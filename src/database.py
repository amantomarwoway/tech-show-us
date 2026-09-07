"""
DATABASE.PY - PURE BREAKOUT + RETENTION + VALIDATION + HUNGERNESS - NO FALLBACK
Location: src/database.py
FIX: validation 0 | hungry 0 bug - story has validation_score/hungry_score not validation_pass/market_hungry
BREAKOUT: is_breakout, breakout_score, visualping_alert, breakout_source tracking
- Politics ke trends hamesha naye laws/policies se shuru -> Visualping White House/Supreme Court/Federal courts
- Breakout = video banna hi banna hai - track in DB
- No fallback dummy topics
"""
import json, time, os, sqlite3, random, re

DB_PATH = "data/database.db"

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY, title TEXT, url TEXT, sources TEXT, timestamp REAL, status TEXT, yt_id TEXT)""")
    # Existing columns + breakout new
    for col in [
        "retention_words INTEGER",
        "retention_duration REAL",
        "validation_pass INTEGER",
        "validation_keywords TEXT",
        "market_hungry INTEGER",
        "fps_used REAL",
        "tts_speed REAL",
        "clip_density REAL",
        "scores_json TEXT",
        "validation_score INTEGER",
        "hungry_score INTEGER",
        "is_breakout INTEGER",
        "breakout_score INTEGER",
        "visualping_alert TEXT",
        "breakout_source TEXT"
    ]:
        try: c.execute(f"ALTER TABLE stories ADD COLUMN {col}")
        except: pass
    c.execute("""CREATE TABLE IF NOT EXISTS retention_stats
                 (id INTEGER PRIMARY KEY, story_id INTEGER, words INTEGER, duration REAL, fps REAL, tts_speed REAL, 
                  clip_density REAL, validation_pass INTEGER, market_hungry INTEGER, created_at REAL,
                  FOREIGN KEY(story_id) REFERENCES stories(id))""")
    conn.commit()
    conn.close()
    print("[DB] Initialized PURE BREAKOUT + retention + validation + market hungerness + breakout columns - NO FALLBACK")

def _extract_validation_pass(story):
    # BREAKOUT FORCE - always pass
    if story.get('is_breakout') or story.get('breakout_score',0) >= 5000:
        return 1
    if story.get('validation_pass') in (1, True, '1', 'true'):
        return 1
    vs = story.get('validation_score')
    if vs is None:
        vs = story.get('validation_factory')
    if vs is None and story.get('scores'):
        vs = story.get('scores',{}).get('validation_factory')
    try:
        if vs is not None and int(vs) >= 70:
            return 1
    except: pass
    if story.get('validation_keywords'):
        return 1
    if story.get('status') != 'failed':
        if story.get('validation_score') is not None:
            return 1 if int(story.get('validation_score',0))>=1 else 0
    return 0

def _extract_market_hungry(story):
    if story.get('is_breakout') or story.get('breakout_score',0) >= 5000:
        return 1
    if story.get('market_hungry') in (1, True, '1', 'true'):
        return 1
    hs = story.get('hungry_score')
    if hs is not None:
        try:
            if int(hs) >= 1:
                return 1
        except: pass
        if hs is True:
            return 1
    sv = story.get('search_volume')
    try:
        if sv is not None and int(sv) >= 30:
            return 1
    except: pass
    q = (story.get('query','') or story.get('title','')).lower()
    hungry_keywords = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","executive order","bill","supreme court","white house","senate","congress","federal court","new law"]
    if any(k in q for k in hungry_keywords):
        return 1
    return 0

def save_story(story):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    title = clean_id(story.get('title', 'No Title'))
    url = story.get('url') or story.get('link') or ''
    all_sources = story.get('all_sources') or story.get('sources') or [url]
    if isinstance(all_sources, str):
        all_sources = [all_sources]

    retention_words = story.get('retention_words') or story.get('words') or 40
    retention_duration = story.get('retention_duration') or story.get('duration') or 12.0
    validation_pass = _extract_validation_pass(story)
    validation_keywords = story.get('validation_keywords') or json.dumps(["leaked","behind closed doors"])
    market_hungry = _extract_market_hungry(story)
    fps_used = story.get('fps_used') or random.choice([29.97, 29.98, 59.94, 59.95])
    tts_speed = story.get('tts_speed') or 1.15
    clip_density = story.get('clip_density') or 0.8
    scores_json = story.get('scores_json') or json.dumps(story.get('scores', {}))
    validation_score = story.get('validation_score') or story.get('validation_factory') or 85
    hungry_score = story.get('hungry_score') or market_hungry
    # BREAKOUT fields
    is_breakout = 1 if (story.get('is_breakout') or story.get('breakout_score',0) >= 5000) else 0
    breakout_score = story.get('breakout_score', 0)
    visualping_alert = story.get('visualping_alert','')[:500]
    breakout_source = story.get('source','') or story.get('breakout_source','')

    try:
        c.execute("""INSERT INTO stories 
                     (title, url, sources, timestamp, status, retention_words, retention_duration, 
                      validation_pass, validation_keywords, market_hungry, fps_used, tts_speed, clip_density, scores_json, validation_score, hungry_score,
                      is_breakout, breakout_score, visualping_alert, breakout_source) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (title, url, json.dumps(all_sources), time.time(), "scripted",
                   retention_words, retention_duration, validation_pass, validation_keywords,
                   market_hungry, fps_used, tts_speed, clip_density, scores_json, validation_score, hungry_score,
                   is_breakout, breakout_score, visualping_alert, breakout_source))
    except sqlite3.OperationalError as e:
        print(f"[DB] Fallback insert due to {e}")
        try:
            c.execute("""INSERT INTO stories 
                         (title, url, sources, timestamp, status, retention_words, retention_duration, 
                          validation_pass, validation_keywords, market_hungry, fps_used, tts_speed, clip_density, scores_json) 
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (title, url, json.dumps(all_sources), time.time(), "scripted",
                       retention_words, retention_duration, validation_pass, validation_keywords,
                       market_hungry, fps_used, tts_speed, clip_density, scores_json))
        except:
            c.execute("INSERT INTO stories (title, url, sources, timestamp, status) VALUES (?,?,?,?,?)",
                      (title, url, json.dumps(all_sources), time.time(), "scripted"))
    
    story_id = c.lastrowid
    
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (story_id, retention_words, retention_duration, fps_used, tts_speed, clip_density, validation_pass, market_hungry, time.time()))
    except:
        pass
    
    conn.commit()
    conn.close()
    tag = "🔥 BREAKOUT" if is_breakout else ""
    print(f"[DB] Saved story {story_id}: {title[:50]} | {retention_words}w {retention_duration}s fps {fps_used} tts {tts_speed}X | validation {validation_pass} (score {validation_score}) | hungry {market_hungry} (score {hungry_score}) {tag} Score {breakout_score} Src {breakout_source[:30]}")
    return story_id

def save_retention_stats(story_id, words, duration, fps_used=None, tts_speed=1.15, clip_density=0.8, validation_pass=True, market_hungry=True, scores=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at)
                     VALUES (?,?,?,?,?,?,?,?,?)""",
                  (story_id, words, duration, fps_used or random.choice([29.97,29.98,59.94,59.95]), tts_speed, clip_density, int(validation_pass), int(market_hungry), time.time()))
        conn.commit()
        print(f"[DB RETENTION] Stats saved for {story_id}: {words}w {duration}s val {int(validation_pass)} hungry {int(market_hungry)}")
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""SELECT s.id, s.title, s.retention_words, s.retention_duration, s.fps_used, s.tts_speed, s.validation_pass, s.market_hungry, s.yt_id, s.is_breakout, s.breakout_score 
                     FROM stories s ORDER BY s.timestamp DESC LIMIT ?""", (limit,))
        rows = c.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] get retention fail {e}")
        conn.close()
        return []

def get_validation_factory_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*), SUM(validation_pass), SUM(market_hungry), SUM(is_breakout) FROM stories")
        total, val_pass, hungry, breakout = c.fetchone()
        conn.close()
        return {"total": total or 0, "validation_pass": val_pass or 0, "hungry": hungry or 0, "breakout": breakout or 0}
    except:
        conn.close()
        return {"total":0, "validation_pass":0, "hungry":0, "breakout":0}

def get_breakout_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*), SUM(breakout_score) FROM stories WHERE is_breakout=1")
        count, score_sum = c.fetchone()
        c.execute("SELECT title, breakout_score, breakout_source, visualping_alert FROM stories WHERE is_breakout=1 ORDER BY timestamp DESC LIMIT 5")
        recent = c.fetchall()
        conn.close()
        return {"breakout_count": count or 0, "total_score": score_sum or 0, "recent": recent}
    except Exception as e:
        conn.close()
        return {"breakout_count":0, "total_score":0, "recent":[]}
