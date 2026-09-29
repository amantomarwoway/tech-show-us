"""
SQLite persistence for used words + uploaded video tracking.
Committed back to git after every run for permanent dedup (see main.py).
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

from src.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS used_words (
    word TEXT PRIMARY KEY,
    long_video_id TEXT,
    short_id_1 TEXT,
    short_id_2 TEXT,
    title TEXT,
    uploaded_at TEXT,
    ctr_long REAL,
    ctr_short1 REAL,
    ctr_short2 REAL,
    thumbnail_version INTEGER DEFAULT 1,
    script TEXT
);
"""

# Columns added after the initial release. SQLite's CREATE TABLE IF NOT
# EXISTS won't retroactively add these to a database file created by an
# older version of this schema, so _migrate() ALTERs them in individually,
# skipping any that already exist. Add future schema changes here rather
# than editing SCHEMA above, or existing words.db files silently keep
# missing the new columns.
_MIGRATION_COLUMNS = {
    "ctr_attempts_long": "INTEGER DEFAULT 0",
    "ctr_attempts_short1": "INTEGER DEFAULT 0",
    "ctr_attempts_short2": "INTEGER DEFAULT 0",
    "last_ctr_attempt_long": "TEXT",
    "last_ctr_attempt_short1": "TEXT",
    "last_ctr_attempt_short2": "TEXT",
}


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(used_words)")}
    for col, decl in _MIGRATION_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE used_words ADD COLUMN {col} {decl}")


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(SCHEMA)
        _migrate(conn)


def is_word_used(word: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM used_words WHERE word = ? COLLATE NOCASE", (word,)
        ).fetchone()
        return row is not None


def get_all_used_words() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT word FROM used_words").fetchall()
        return [r["word"] for r in rows]


def mark_word_used(
    word: str,
    long_video_id: str,
    short_id_1: Optional[str],
    short_id_2: Optional[str],
    title: str,
    script: dict,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO used_words
                (word, long_video_id, short_id_1, short_id_2, title, uploaded_at, script)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(word) DO UPDATE SET
                long_video_id=excluded.long_video_id,
                short_id_1=excluded.short_id_1,
                short_id_2=excluded.short_id_2,
                title=excluded.title,
                uploaded_at=excluded.uploaded_at,
                script=excluded.script
            """,
            (
                word,
                long_video_id,
                short_id_1,
                short_id_2,
                title,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(script, ensure_ascii=False),
            ),
        )


def update_ctr(word: str, *, ctr_long=None, ctr_short1=None, ctr_short2=None) -> None:
    fields, values = [], []
    if ctr_long is not None:
        fields.append("ctr_long = ?")
        values.append(ctr_long)
    if ctr_short1 is not None:
        fields.append("ctr_short1 = ?")
        values.append(ctr_short1)
    if ctr_short2 is not None:
        fields.append("ctr_short2 = ?")
        values.append(ctr_short2)
    if not fields:
        return
    values.append(word)
    with get_conn() as conn:
        conn.execute(f"UPDATE used_words SET {', '.join(fields)} WHERE word = ?", values)


def increment_thumb_version(word: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT thumbnail_version FROM used_words WHERE word = ?", (word,)
        ).fetchone()
        new_version = (row["thumbnail_version"] if row else 1) + 1
        conn.execute(
            "UPDATE used_words SET thumbnail_version = ? WHERE word = ?",
            (new_version, word),
        )
        return new_version


_CTR_FIELD_COLUMNS = {
    "long": ("ctr_attempts_long", "last_ctr_attempt_long"),
    "short1": ("ctr_attempts_short1", "last_ctr_attempt_short1"),
    "short2": ("ctr_attempts_short2", "last_ctr_attempt_short2"),
}


def record_ctr_attempt(word: str, field: str) -> None:
    """Call this AFTER a successful CTR regeneration (title/thumbnail
    update actually pushed to YouTube) — it's what CTR_MAX_ATTEMPTS and
    CTR_COOLDOWN_DAYS in ctr_optimizer.py check against, so a call here
    that isn't backed by a real update would let a video dodge the
    attempt cap."""
    if field not in _CTR_FIELD_COLUMNS:
        raise ValueError(f"Unknown CTR field: {field}")
    attempts_col, last_attempt_col = _CTR_FIELD_COLUMNS[field]
    with get_conn() as conn:
        conn.execute(
            f"UPDATE used_words SET {attempts_col} = COALESCE({attempts_col}, 0) + 1, "
            f"{last_attempt_col} = ? WHERE word = ?",
            (datetime.now(timezone.utc).isoformat(), word),
        )


def get_videos_needing_ctr_check(min_age_hours: int = 48) -> list[sqlite3.Row]:
    """Return rows for videos uploaded more than `min_age_hours` ago."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM used_words WHERE uploaded_at IS NOT NULL"
        ).fetchall()
    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        try:
            uploaded = datetime.fromisoformat(r["uploaded_at"])
        except (TypeError, ValueError):
            continue
        age_hours = (now - uploaded).total_seconds() / 3600
        if age_hours >= min_age_hours:
            out.append(r)
    return out
