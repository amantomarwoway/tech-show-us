"""
SQLite database (data/words.db — committed back to git by the workflows).

  series          one row per multi-part story: planned length, status, the weekly slot it owns,
                  its YouTube playlist, and its "bible" (characters + voices + looks, rolling recap,
                  open plot threads) so every new part continues the same story.
  story_videos    every video (long episode or short) with the REAL performance numbers from YouTube
                  Analytics, the series/part it belongs to and when it goes public.
  schedule_slots  the weekly long-episode slots (US Eastern local time) — seeded from config and
                  swapped by the bot when a slot underperforms; slot_history remembers every slot
                  ever used so the explorer never flips back to an old one.
  publish_queue   posts waiting for their moment (Instagram cannot be scheduled by API, so its posts
                  wait here until due); stores per-platform results so a retry never double-posts.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from statistics import mean, median

from src.config import DB_PATH, LONG_SLOTS_DEFAULT

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
    genre TEXT,
    series_id INTEGER,
    part_no INTEGER,
    slot_index INTEGER,
    publish_at TEXT                  -- when it goes (or went) public, ISO UTC
);
"""
SERIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    genre TEXT,
    pillar TEXT,
    status TEXT DEFAULT 'active',    -- active | finished
    planned_parts INTEGER,
    parts_done INTEGER DEFAULT 0,    -- parts produced (published or scheduled)
    slot_index INTEGER,
    playlist_id TEXT,
    bible TEXT,
    created_at TEXT,
    finished_at TEXT
);
"""
SLOTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule_slots (
    slot_index INTEGER PRIMARY KEY,
    weekday INTEGER,
    hour_local INTEGER,              -- hour in config.SLOT_TIMEZONE (US Eastern)
    minute INTEGER DEFAULT 0
);
"""
HISTORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS slot_history (
    weekday INTEGER,
    hour_local INTEGER,
    minute INTEGER DEFAULT 0,
    first_used_at TEXT,
    PRIMARY KEY (weekday, hour_local, minute)
);
"""
PLAYLISTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS playlists (
    key TEXT PRIMARY KEY,            -- e.g. 'genre:horror', 'all-episodes'
    playlist_id TEXT
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
# Columns added to story_videos after its first version, applied in place to an existing database.
_STORY_MIGRATION_COLUMNS = {
    "kind": "TEXT DEFAULT 'long'",
    "parent_video_id": "TEXT",
    "genre": "TEXT",
    "series_id": "INTEGER",
    "part_no": "INTEGER",
    "slot_index": "INTEGER",
    "publish_at": "TEXT",
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    with get_conn() as conn:
        for schema in (STORY_SCHEMA, SERIES_SCHEMA, SLOTS_SCHEMA, HISTORY_SCHEMA, PLAYLISTS_SCHEMA, QUEUE_SCHEMA):
            conn.execute(schema)
        _migrate_story(conn)
        if not conn.execute("SELECT 1 FROM schedule_slots LIMIT 1").fetchone():
            for idx, (weekday, hour, minute) in enumerate(LONG_SLOTS_DEFAULT):
                conn.execute("INSERT INTO schedule_slots VALUES (?, ?, ?, ?)", (idx, weekday, hour, minute))
                conn.execute("INSERT OR IGNORE INTO slot_history VALUES (?, ?, ?, ?)", (weekday, hour, minute, _now_iso()))


# ---------------------------------------------------------------------------
# schedule slots
# ---------------------------------------------------------------------------
def get_slots() -> list[dict]:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM schedule_slots ORDER BY slot_index")]


def set_slot(slot_index: int, weekday: int, hour_local: int, minute: int = 0) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE schedule_slots SET weekday=?, hour_local=?, minute=? WHERE slot_index=?",
                     (weekday, hour_local, minute, slot_index))
        conn.execute("INSERT OR IGNORE INTO slot_history VALUES (?, ?, ?, ?)", (weekday, hour_local, minute, _now_iso()))


def get_slot_history() -> set[tuple[int, int, int]]:
    """Every (weekday, hour, minute) the channel has ever used as a long-episode slot."""
    with get_conn() as conn:
        return {(r["weekday"], r["hour_local"], r["minute"]) for r in conn.execute("SELECT * FROM slot_history")}


# ---------------------------------------------------------------------------
# channel-wide playlists (a video should sit in 3-4 playlists: its series, its genre, all episodes)
# ---------------------------------------------------------------------------
def get_playlist(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT playlist_id FROM playlists WHERE key = ?", (key,)).fetchone()
    return row["playlist_id"] if row else None


def set_playlist(key: str, playlist_id: str) -> None:
    with get_conn() as conn:
        conn.execute("INSERT INTO playlists (key, playlist_id) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET playlist_id=excluded.playlist_id",
                     (key, playlist_id))


# ---------------------------------------------------------------------------
# series
# ---------------------------------------------------------------------------
def _series_row(row) -> dict | None:
    if row is None:
        return None
    d = dict(row)
    d["bible"] = json.loads(d["bible"]) if d.get("bible") else {}
    return d


def create_series(title: str, genre: str, pillar: str, planned_parts: int, slot_index: int, bible: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO series (title, genre, pillar, status, planned_parts, parts_done, slot_index, bible, created_at) "
            "VALUES (?, ?, ?, 'active', ?, 0, ?, ?, ?)",
            (title, genre, pillar, planned_parts, slot_index, json.dumps(bible), _now_iso()),
        )
        return cur.lastrowid


def get_series(series_id: int) -> dict | None:
    with get_conn() as conn:
        return _series_row(conn.execute("SELECT * FROM series WHERE id = ?", (series_id,)).fetchone())


def get_active_series() -> list[dict]:
    with get_conn() as conn:
        return [_series_row(r) for r in conn.execute("SELECT * FROM series WHERE status = 'active' ORDER BY id")]


def series_for_slot(slot_index: int) -> dict | None:
    with get_conn() as conn:
        return _series_row(conn.execute(
            "SELECT * FROM series WHERE status = 'active' AND slot_index = ? ORDER BY id DESC LIMIT 1", (slot_index,)).fetchone())


def update_series(series_id: int, **fields) -> None:
    """Allowed: title, planned_parts, parts_done, status, playlist_id, bible (dict), finished_at."""
    allowed = {"title", "planned_parts", "parts_done", "status", "playlist_id", "bible", "finished_at"}
    bad = set(fields) - allowed
    if bad:
        raise ValueError(f"Unknown series fields: {sorted(bad)}")
    if "bible" in fields:
        fields["bible"] = json.dumps(fields["bible"])
    if not fields:
        return
    with get_conn() as conn:
        conn.execute(f"UPDATE series SET {', '.join(f'{k} = ?' for k in fields)} WHERE id = ?",
                     [*fields.values(), series_id])


def episodes_for_series(series_id: int) -> list[dict]:
    """Long videos of a series in part order."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM story_videos WHERE series_id = ? AND COALESCE(kind,'long') = 'long' ORDER BY part_no", (series_id,))]


# ---------------------------------------------------------------------------
# story_videos
# ---------------------------------------------------------------------------
def record_story_upload(
    video_id: str, title: str, pillar: str, recurring_character_used: str = "",
    *, kind: str = "long", parent_video_id: str | None = None, genre: str | None = None,
    series_id: int | None = None, part_no: int | None = None, slot_index: int | None = None,
    publish_at: str | None = None,
) -> None:
    """Call once per uploaded video (long or short). The analytics sync later fills in real
    retention/CTR; pattern_analytics learns from the LONG ones; the series planner reads them."""
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO story_videos
                (video_id, title, pillar, recurring_character_used, uploaded_at, kind, parent_video_id, genre,
                 series_id, part_no, slot_index, publish_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title=excluded.title, pillar=excluded.pillar,
                recurring_character_used=excluded.recurring_character_used,
                uploaded_at=excluded.uploaded_at, kind=excluded.kind,
                parent_video_id=excluded.parent_video_id, genre=excluded.genre,
                series_id=excluded.series_id, part_no=excluded.part_no,
                slot_index=excluded.slot_index, publish_at=excluded.publish_at
            """,
            (video_id, title, pillar, recurring_character_used, _now_iso(), kind, parent_video_id, genre,
             series_id, part_no, slot_index, publish_at),
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
    """{pillar: {"count", "avg_retention", "avg_ctr"}} over LONG videos that have real data."""
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


def channel_baseline(exclude_series_id: int | None = None, now: datetime | None = None) -> dict:
    """The yardstick a story is judged against: over every LONG video with real data (optionally leaving out
    one series, so a story is never compared with itself) -> {"n", "retention" (mean), "views_per_day" (median)}.
    Views are turned into views PER DAY of age (an episode's views are a 28-day window, so a 3-day-old part and a
    month-old part are only comparable per day). Both values are None when there is no data."""
    now = now or datetime.now(timezone.utc)
    sql = ("SELECT avg_view_percentage AS r, views AS v, publish_at, uploaded_at FROM story_videos "
           "WHERE avg_view_percentage IS NOT NULL AND COALESCE(kind, 'long') = 'long'")
    args: list = []
    if exclude_series_id is not None:
        sql += " AND (series_id IS NULL OR series_id != ?)"
        args.append(exclude_series_id)
    with get_conn() as conn:
        rows = conn.execute(sql, args).fetchall()
    if not rows:
        return {"n": 0, "retention": None, "views_per_day": None}
    rates = []
    for r in rows:
        if r["v"] is None:
            continue
        try:
            age_days = (now - datetime.fromisoformat(r["publish_at"] or r["uploaded_at"])).total_seconds() / 86400
        except (TypeError, ValueError):
            continue
        rates.append(r["v"] / min(max(age_days, 1.0), 28.0))
    return {"n": len(rows), "retention": mean(r["r"] for r in rows), "views_per_day": median(rates) if rates else None}


def slot_stats() -> dict:
    """{slot_index: {"n", "avg_views", "avg_retention"}} over LONG episodes that have data."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT slot_index, views, avg_view_percentage AS r FROM story_videos "
            "WHERE slot_index IS NOT NULL AND avg_view_percentage IS NOT NULL AND COALESCE(kind,'long')='long'").fetchall()
    out: dict[int, dict] = {}
    for r in rows:
        s = out.setdefault(r["slot_index"], {"views": [], "ret": []})
        if r["views"] is not None:
            s["views"].append(r["views"])
        s["ret"].append(r["r"])
    return {i: {"n": len(s["ret"]), "avg_views": mean(s["views"]) if s["views"] else 0.0, "avg_retention": mean(s["ret"])}
            for i, s in out.items()}


def slot_taken(kind: str, when: datetime, tolerance_minutes: int = 2) -> bool:
    """True if a video of this kind is already scheduled/published at that exact slot time."""
    lo = (when - timedelta(minutes=tolerance_minutes)).isoformat()
    hi = (when + timedelta(minutes=tolerance_minutes)).isoformat()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM story_videos WHERE COALESCE(kind,'long') = ? AND publish_at >= ? AND publish_at <= ? LIMIT 1",
            (kind, lo, hi)).fetchone()
    return row is not None


def get_story_videos_for_stats(min_age_hours: float = 48, max_age_days: int = 90) -> list[sqlite3.Row]:
    """Videos old enough for stable numbers. Age counts from when the video went PUBLIC
    (publish_at) when it was scheduled, else from the upload."""
    now = datetime.now(timezone.utc)
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM story_videos WHERE uploaded_at IS NOT NULL").fetchall()
    out = []
    for r in rows:
        try:
            ref = datetime.fromisoformat(r["publish_at"] or r["uploaded_at"])
        except (TypeError, ValueError):
            continue
        age_h = (now - ref).total_seconds() / 3600
        if min_age_hours <= age_h <= max_age_days * 24:
            out.append(r)
    return out


# ---------------------------------------------------------------------------
# publish_queue
# ---------------------------------------------------------------------------
def enqueue_publish(due_at_iso: str, file_path: str, payload: dict, result: dict | None = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO publish_queue (created_at, due_at, file_path, payload, status, result) VALUES (?, ?, ?, ?, 'pending', ?)",
            (_now_iso(), due_at_iso, file_path, json.dumps(payload), json.dumps(result) if result else None),
        )
        return cur.lastrowid


def get_due_publish_items(now_iso: str | None = None, max_attempts: int = 3) -> list[dict]:
    now_iso = now_iso or _now_iso()
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
