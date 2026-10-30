"""
SQLite database (data/words.db — committed back to git by the workflows).

  story_videos   every published video (long + short) with the REAL performance
                 numbers pulled from YouTube Analytics; the bot's learning data.
  publish_queue  Shorts waiting for their day (file path + per-platform text +
                 per-platform results, so a retry never double-posts).
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from src.config import DB_PATH

STORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS story_videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    pillar TEXT,
    recurring_character_used TEXT,
    uploaded_at TEXT,
    avg_view_percentage REAL,
    ctr REAL,
    views INTEGER,
    kind TEXT DEFAULT 'long',        -- 'long' or 'short'
    parent_video_id TEXT,            -- a Short's long video
    genre TEXT
);
"""

QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS publish_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT,
    due_at TEXT,
    file_path TEXT,
    payload TEXT,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    result TEXT
);
"""

# Columns added to story_videos after its first version — applied in place to an
# existing database (CREATE TABLE IF NOT EXISTS never alters a table).
_STORY_MIGRATION_COLUMNS = {
    "kind": "TEXT DEFAULT 'long'",
    "parent_video_id": "TEXT",
    "genre": "TEXT",
}


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate_story(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(story_videos)")}
    for col, decl in _STORY_MIGRATION_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE story_videos ADD COLUMN {col} {decl}")


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(STORY_SCHEMA)
        conn.execute(QUEUE_SCHEMA)
        _migrate_story(conn)


# ---------------------------------------------------------------------------
# story_videos
# ---------------------------------------------------------------------------
def record_story_upload(
    video_id: str, title: str, pillar: str, recurring_character_used: str = "",
    *, kind: str = "long", parent_video_id: str | None = None, genre: str | None = None,
) -> None:
    """Call once per uploaded video (long or short). The analytics sync later fills
    in real retention/CTR; pattern_analytics learns from the LONG ones."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO story_videos
                (video_id, title, pillar, recurring_character_used, uploaded_at, kind, parent_video_id, genre)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title=excluded.title, pillar=excluded.pillar,
                recurring_character_used=excluded.recurring_character_used,
                uploaded_at=excluded.uploaded_at, kind=excluded.kind,
                parent_video_id=excluded.parent_video_id, genre=excluded.genre
            """,
            (video_id, title, pillar, recurring_character_used,
             datetime.now(timezone.utc).isoformat(), kind, parent_video_id, genre),
        )


def update_story_performance(
    video_id: str, *, avg_view_percentage: float | None = None,
    ctr: float | None = None, views: int | None = None,
) -> None:
    fields, values = [], []
    for column, value in (("avg_view_percentage", avg_view_percentage), ("ctr", ctr), ("views", views)):
        if value is not None:
            fields.append(f"{column} = ?")
            values.append(value)
    if not fields:
        return
    values.append(video_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE story_videos SET {', '.join(fields)} WHERE video_id = ?", values)


def get_pillar_stats() -> dict:
    """{pillar: {"count", "avg_retention", "avg_ctr"}} over LONG videos that have
    real performance data (a Short's retention isn't comparable, and a video
    without stats yet must not drag a pillar toward zero)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT pillar, avg_view_percentage, ctr FROM story_videos "
            "WHERE avg_view_percentage IS NOT NULL AND COALESCE(kind, 'long') = 'long'"
        ).fetchall()
    stats: dict[str, dict] = {}
    for row in rows:
        s = stats.setdefault(row["pillar"], {"count": 0, "_ret": 0.0, "_ctr": 0.0, "_ctr_n": 0})
        s["count"] += 1
        s["_ret"] += row["avg_view_percentage"]
        if row["ctr"] is not None:
            s["_ctr"] += row["ctr"]
            s["_ctr_n"] += 1
    for s in stats.values():
        s["avg_retention"] = s.pop("_ret") / s["count"]
        s["avg_ctr"] = (s["_ctr"] / s["_ctr_n"]) if s["_ctr_n"] else None
        del s["_ctr"], s["_ctr_n"]
    return stats


def last_story_long_upload() -> datetime | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(uploaded_at) AS t FROM story_videos WHERE COALESCE(kind, 'long') = 'long'"
        ).fetchone()
    if not row or not row["t"]:
        return None
    try:
        return datetime.fromisoformat(row["t"])
    except ValueError:
        return None


def should_build_long_today(every_days: int, now: datetime | None = None,
                            slack_hours: float = 6.0) -> bool:
    """True if no long story was uploaded within the last `every_days` days (minus
    slack, so a run starting a few hours earlier than the previous one still counts
    as due). Driven by what was ACTUALLY uploaded, not calendar parity — a failed
    day is retried the next day automatically."""
    now = now or datetime.now(timezone.utc)
    last = last_story_long_upload()
    if last is None:
        return True
    return (now - last).total_seconds() >= every_days * 86400 - slack_hours * 3600


def get_story_videos_for_stats(min_age_hours: float = 48, max_age_days: int = 90) -> list[sqlite3.Row]:
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM story_videos WHERE uploaded_at IS NOT NULL").fetchall()
    out = []
    for r in rows:
        try:
            age_h = (now - datetime.fromisoformat(r["uploaded_at"])).total_seconds() / 3600
        except (TypeError, ValueError):
            continue
        if min_age_hours <= age_h <= max_age_days * 24:
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# publish_queue
# ---------------------------------------------------------------------------
def enqueue_publish(due_at_iso: str, file_path: str, payload: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO publish_queue (created_at, due_at, file_path, payload, status) VALUES (?, ?, ?, ?, 'pending')",
            (datetime.now(timezone.utc).isoformat(), due_at_iso, file_path, json.dumps(payload)),
        )
        return cur.lastrowid


def get_due_publish_items(now_iso: str | None = None, max_attempts: int = 3) -> list[dict]:
    now_iso = now_iso or datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM publish_queue WHERE status = 'pending' AND due_at <= ? AND attempts < ? ORDER BY due_at",
            (now_iso, max_attempts),
        ).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["payload"] = json.loads(d["payload"]) if d.get("payload") else {}
        items.append(d)
    return items


def mark_publish_item(item_id: int, status: str, result: dict | None = None) -> None:
    """status: 'done' | 'failed' | 'pending' (a pending retry still counts the attempt)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE publish_queue SET status = ?, attempts = attempts + 1, result = ? WHERE id = ?",
            (status, json.dumps(result) if result is not None else None, item_id),
        )
