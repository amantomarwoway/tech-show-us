# src/database.py - REAL AEROPLANE - DETAILED FIXED - SQLite with anti-duplicate
import os, sqlite3, json
from datetime import datetime

DB_PATH = "data/god_bot.db"

def init_db():
    """Init DB - data folder + tables"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Stories table - detailed
    c.execute('''CREATE TABLE IF NOT EXISTS stories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT UNIQUE,
        source TEXT,
        breakout_score INTEGER,
        is_breakout BOOLEAN,
        search_volume INTEGER,
        seo_youtube_title TEXT,
        short_script TEXT,
        long_script TEXT,
        description TEXT,
        hashtags TEXT,
        tags TEXT,
        script_visual_segments TEXT,
        confidence_score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        uploaded BOOLEAN DEFAULT 0,
        youtube_id TEXT
    )''')
    # Evolution table
    c.execute('''CREATE TABLE IF NOT EXISTS evolution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        learned TEXT,
        score INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
    print(f"[DB] Initialized {DB_PATH} - detailed mode")

def save_story(story):
    """Save story - anti-duplicate by URL"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        url = story.get('url','') or story.get('title','')[:100]
        # Check duplicate
        c.execute("SELECT id FROM stories WHERE url=?", (url,))
        existing = c.fetchone()
        if existing:
            print(f"[DB] Duplicate skip {url[:40]}")
            conn.close()
            return existing[0]

        c.execute('''INSERT OR IGNORE INTO stories
            (title, url, source, breakout_score, is_breakout, search_volume,
             seo_youtube_title, short_script, long_script, description, hashtags, tags,
             script_visual_segments, confidence_score, uploaded)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0)''',
            (
                story.get('title',''),
                url,
                story.get('source',''),
                story.get('breakout_score',0),
                story.get('is_breakout', False),
                story.get('search_volume',0),
                story.get('seo_youtube_title',''),
                story.get('short_script',''),
                story.get('long_script',''),
                story.get('description',''),
                json.dumps(story.get('hashtags',[])),
                json.dumps(story.get('tags',[])),
                json.dumps(story.get('script_visual_segments',[])),
                story.get('confidence_score',80)
            ))
        conn.commit()
        sid = c.lastrowid or 1
        conn.close()
        print(f"[DB] Saved story id={sid} {story.get('title','')[:50]} Score={story.get('breakout_score',0)}")
        return sid
    except Exception as e:
        print(f"[DB] Save fail {e}")
        return 1

def mark_uploaded(story_id, youtube_id):
    """Mark uploaded - for self evolution"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE stories SET uploaded=1, youtube_id=? WHERE id=?", (youtube_id, story_id))
        conn.commit()
        conn.close()
        print(f"[DB] Marked uploaded {story_id} -> {youtube_id}")
    except Exception as e:
        print(f"[DB] Mark fail {e}")

def get_recent_stories(limit=10):
    """Get recent for evolution"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT title, breakout_score, uploaded FROM stories ORDER BY id DESC LIMIT?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except:
        return []
