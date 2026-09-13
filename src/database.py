# src/database.py - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - DETAILED FIXED
import os, sqlite3, json
from datetime import datetime

DB_PATH = "data/god_bot.db"

def init_db():
    """Init DB - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - with migration"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Stories table - detailed + MuckScraper + Hook/Retain/Reward + VUZA
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

    # Migration - add new columns for MuckScraper + Hook/Retain/Reward + VUZA if not exists
    existing_cols = []
    try:
        c.execute("PRAGMA table_info(stories)")
        existing_cols = [row[1] for row in c.fetchall()]
    except:
        existing_cols = []

    new_columns = {
        "hook": "TEXT",
        "retain": "TEXT",
        "reward": "TEXT",
        "original_title": "TEXT",
        "grouped_topic": "TEXT",
        "muckscraper_source": "TEXT",
        "search_potential_score": "INTEGER DEFAULT 0",
        "vuza_offline": "BOOLEAN DEFAULT 0",
        "hook_visual": "TEXT",
        "retain_visual": "TEXT",
        "reward_visual": "TEXT",
        "ollama_summary": "TEXT",
        "video_path": "TEXT"
    }

    for col, col_type in new_columns.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE stories ADD COLUMN {col} {col_type}")
                print(f"[DB] Migration added column {col}")
            except Exception as e:
                print(f"[DB] Migration fail {col} {e}")

    # Evolution table - MuckScraper + VUZA learning
    c.execute('''CREATE TABLE IF NOT EXISTS evolution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        learned TEXT,
        score INTEGER,
        source TEXT,
        hook TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # MuckScraper stats table - for grouping
    c.execute('''CREATE TABLE IF NOT EXISTS muckscraper_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grouped_topic TEXT,
        titles TEXT,
        count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()
    print(f"[DB] Initialized {DB_PATH} - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - detailed mode")

def save_story(story):
    """Save story - anti-duplicate by URL + title - MuckScraper + Hook/Retain/Reward + VUZA"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        url = story.get('url','') or story.get('title','')[:100]
        title = story.get('title','')

        # Check duplicate - MuckScraper style - URL + title both
        c.execute("SELECT id FROM stories WHERE url=?", (url,))
        existing = c.fetchone()
        if existing:
            print(f"[DB] Duplicate skip URL {url[:50]}")
            conn.close()
            return existing[0]

        # Also check title similarity for MuckScraper - same news different URL
        if title:
            c.execute("SELECT id FROM stories WHERE title=? LIMIT 1", (title,))
            existing_title = c.fetchone()
            if existing_title:
                print(f"[DB] Duplicate skip TITLE {title[:50]}")
                conn.close()
                return existing_title[0]

        # Hook/Retain/Reward - Automated-Shorts-Generator
        hook = story.get('hook','')
        retain = story.get('retain','')
        reward = story.get('reward','')

        c.execute('''INSERT OR IGNORE INTO stories
            (title, url, source, breakout_score, is_breakout, search_volume,
             seo_youtube_title, short_script, long_script, description, hashtags, tags,
             script_visual_segments, confidence_score, uploaded,
             hook, retain, reward, original_title, grouped_topic, muckscraper_source,
             search_potential_score, vuza_offline, hook_visual, retain_visual, reward_visual,
             ollama_summary, video_path)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                title,
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
                story.get('confidence_score',80),
                # New fields - MuckScraper + Hook/Retain/Reward + VUZA
                hook,
                retain,
                reward,
                story.get('original_title',''),
                story.get('grouped_topic','') or story.get('grouped',''),
                story.get('muckscraper_source','') or story.get('source',''),
                story.get('search_potential_score',0) or story.get('breakout_score',0),
                1 if story.get('vuza_offline') or story.get('offline') else 0,
                story.get('hook_visual','') or hook,
                story.get('retain_visual','') or retain,
                story.get('reward_visual','') or reward,
                story.get('ollama_summary','') or story.get('grouped_topic',''),
                story.get('video_path','') or story.get('output_path','')
            ))
        conn.commit()
        sid = c.lastrowid or 1

        # Save MuckScraper group if exists
        grouped = story.get('grouped_topic','')
        if grouped:
            try:
                c.execute("INSERT INTO muckscraper_groups (grouped_topic, titles, count) VALUES (?,?,?)",
                          (grouped, json.dumps([title]), 1))
                conn.commit()
            except:
                pass

        conn.close()
        print(f"[DB] Saved id={sid} {title[:50]} Score={story.get('breakout_score',0)} Hook={hook[:20]} Source={story.get('source','')} VUZA={story.get('vuza_offline', False)}")
        return sid
    except Exception as e:
        print(f"[DB] Save fail {e}")
        import traceback; traceback.print_exc()
        return 1

def mark_uploaded(story_id, youtube_id):
    """Mark uploaded - for self evolution - MuckScraper + VUZA"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE stories SET uploaded=1, youtube_id=? WHERE id=?", (youtube_id, story_id))
        conn.commit()
        conn.close()
        print(f"[DB] Marked uploaded {story_id} -> {youtube_id} - MUCKSCRAPER + VUZA")
    except Exception as e:
        print(f"[DB] Mark fail {e}")

def get_recent_stories(limit=10):
    """Get recent for evolution - MuckScraper + Hook/Retain/Reward"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT title, breakout_score, uploaded, hook, source, vuza_offline FROM stories ORDER BY id DESC LIMIT?", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Get recent fail {e}")
        return []

def get_muckscraper_stats(limit=5):
    """Get MuckScraper stats - grouping + VUZA"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT grouped
