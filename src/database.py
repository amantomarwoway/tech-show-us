"""
DATABASE.PY - RETENTION + VALIDATION FACTORY + MARKET HUNGERNESS TRACKING
Location: src/database.py
Edits: Added columns for retention metrics, validation factory, market hungerness - no delete
"""
import json, time, os, sqlite3, random

DB_PATH = "data/database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Original table
    c.execute("""CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY, title TEXT, url TEXT, sources TEXT, timestamp REAL, status TEXT, yt_id TEXT)""")
    
    # NEW: Retention + Validation Factory columns - try add if not exists
    try:
        c.execute("ALTER TABLE stories ADD COLUMN retention_words INTEGER")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN retention_duration REAL")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN validation_pass INTEGER")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN validation_keywords TEXT")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN market_hungry INTEGER")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN fps_used REAL")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN tts_speed REAL")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN clip_density REAL")
    except: pass
    try:
        c.execute("ALTER TABLE stories ADD COLUMN scores_json TEXT")
    except: pass
    
    # NEW: Retention performance table
    c.execute("""CREATE TABLE IF NOT EXISTS retention_stats
                 (id INTEGER PRIMARY KEY, story_id INTEGER, words INTEGER, duration REAL, fps REAL, tts_speed REAL, 
                  clip_density REAL, validation_pass INTEGER, market_hungry INTEGER, created_at REAL,
                  FOREIGN KEY(story_id) REFERENCES stories(id))""")
    
    conn.commit()
    conn.close()
    print("[DB] Initialized with retention + validation factory + market hungerness columns")

def save_story(story):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    title = story.get('title', 'No Title')
    url = story.get('url') or story.get('link') or ''
    all_sources = story.get('all_sources') or story.get('sources') or [url]
    if isinstance(all_sources, str):
        all_sources = [all_sources]

    # NEW: Extract retention + validation data if present in story dict
    retention_words = story.get('retention_words') or story.get('words') or 40
    retention_duration = story.get('retention_duration') or story.get('duration') or 12.0
    validation_pass = 1 if story.get('validation_pass') else 0
    validation_keywords = story.get('validation_keywords') or json.dumps(["leaked","behind closed doors"])
    market_hungry = 1 if story.get('market_hungry') else 0
    fps_used = story.get('fps_used') or random.choice([29.97, 29.98, 59.94, 59.95])
    tts_speed = story.get('tts_speed') or 1.15
    clip_density = story.get('clip_density') or 0.8
    scores_json = story.get('scores_json') or json.dumps(story.get('scores', {}))

    try:
        c.execute("""INSERT INTO stories 
                     (title, url, sources, timestamp, status, retention_words, retention_duration, 
                      validation_pass, validation_keywords, market_hungry, fps_used, tts_speed, clip_density, scores_json) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (title, url, json.dumps(all_sources), time.time(), "scripted",
                   retention_words, retention_duration, validation_pass, validation_keywords,
                   market_hungry, fps_used, tts_speed, clip_density, scores_json))
    except sqlite3.OperationalError as e:
        # Fallback if columns not exist yet (old DB)
        print(f"[DB] Fallback insert due to {e}")
        c.execute("INSERT INTO stories (title, url, sources, timestamp, status) VALUES (?,?,?,?,?)",
                  (title, url, json.dumps(all_sources), time.time(), "scripted"))
    
    story_id = c.lastrowid
    
    # Also insert into retention_stats
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (story_id, retention_words, retention_duration, fps_used, tts_speed, clip_density, validation_pass, market_hungry, time.time()))
    except:
        pass
    
    conn.commit()
    conn.close()
    print(f"[DB] Saved story {story_id}: {title[:50]} | retention {retention_words}w {retention_duration}s fps {fps_used} tts {tts_speed}X clip {clip_density}s | validation {validation_pass} | hungry {market_hungry}")
    return story_id

def save_retention_stats(story_id, words, duration, fps_used=None, tts_speed=1.15, clip_density=0.8, validation_pass=True, market_hungry=True, scores=None):
    """NEW: Explicit retention stats saver"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (story_id, words, duration, fps_used or random.choice([29.97,29.98,59.94,59.95]), tts_speed, clip_density, int(validation_pass), int(market_hungry), time.time()))
        conn.commit()
        print(f"[DB RETENTION] Stats saved for {story_id}: {words}w {duration}s")
    except Exception as e:
        print(f"[DB RETENTION] Fail {e}")
    conn.close()

def mark_uploaded(story_id, yt_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE stories SET status='uploaded', yt_id=? WHERE id=?", (yt_id, story_id))
    conn.commit()
    conn.close()
    print(f"[DB] Marked uploaded {story_id} -> {yt_id}")

def get_retention_performance(limit=20):
    """NEW: Get retention performance for analysis"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""SELECT s.id, s.title, s.retention_words, s.retention_duration, s.fps_used, s.tts_speed, s.validation_pass, s.market_hungry, s.yt_id 
                     FROM stories s ORDER BY s.timestamp DESC LIMIT ?""", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] get retention fail {e}")
        conn.close()
        return []

def get_validation_factory_stats():
    """NEW: Validation factory pass/fail stats"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*), SUM(validation_pass), SUM(market_hungry) FROM stories")
        total, val_pass, hungry = c.fetchone()
        conn.close()
        return {"total": total or 0, "validation_pass": val_pass or 0, "hungry": hungry or 0}
    except:
        conn.close()
        return {"total":0, "validation_pass":0, "hungry":0}
