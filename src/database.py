"""
DATABASE.PY - Wire + Google News 45min + 7-Day Velocity + YouTube Search SEO + DuckDuckGo 1.0s + yt-dlp 1.8s
Location: src/database.py
UPDATED: No breakout/visualping, now wire service + search velocity + SEO tracking
- Wire Service: Reuters + Google News Wire, 45min filter, mainstream block, search potential
- Predictive: 7-Day Search Velocity Filter, is_weekly_search_trend, confidence_score >=85
- SEO: YouTube Search Traffic over Shorts Feed, seo_youtube_title, seo_tags
- Assets: DuckDuckGo 1.0s images + yt-dlp 1.8s clips, visual_segments
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
        "breakout_source TEXT",
        "is_wire INTEGER",
        "wire_source TEXT",
        "fetch_window_minutes INTEGER",
        "search_potential_score INTEGER",
        "is_weekly_search_trend INTEGER",
        "confidence_score INTEGER",
        "seo_youtube_title TEXT",
        "seo_tags TEXT",
        "youtube_search_optimized INTEGER",
        "asset_engine TEXT",
        "image_duration REAL",
        "clip_duration REAL",
        "visual_segments TEXT",
        "is_mainstream_blocked INTEGER",
        "ground_level_first INTEGER"
    ]:
        try: c.execute(f"ALTER TABLE stories ADD COLUMN {col}")
        except: pass
    c.execute("""CREATE TABLE IF NOT EXISTS retention_stats
                 (id INTEGER PRIMARY KEY, story_id INTEGER, words INTEGER, duration REAL, fps REAL, tts_speed REAL, 
                  clip_density REAL, validation_pass INTEGER, market_hungry INTEGER, created_at REAL,
                  FOREIGN KEY(story_id) REFERENCES stories(id))""")
    for col in [
        "is_weekly_search_trend INTEGER",
        "confidence_score INTEGER",
        "seo_youtube_title TEXT"
    ]:
        try: c.execute(f"ALTER TABLE retention_stats ADD COLUMN {col}")
        except: pass
    conn.commit()
    conn.close()
    print("[DB] Initialized Wire + Velocity + SEO + Asset columns")

def _extract_validation_pass(story):
    if story.get('is_weekly_search_trend') and story.get('confidence_score',0) >= 85:
        return 1
    if story.get('validation_pass') in (1, True, '1', 'true'):
        return 1
    vs = story.get('validation_score') or story.get('confidence_score')
    if vs is not None:
        try:
            if int(vs) >= 70:
                return 1
        except: pass
    if story.get('validation_keywords'):
        return 1
    return 0

def _extract_market_hungry(story):
    if story.get('is_weekly_search_trend') and story.get('confidence_score',0) >= 85:
        return 1
    if story.get('market_hungry') in (1, True, '1', 'true'):
        return 1
    hs = story.get('hungry_score')
    if hs is not None:
        try:
            if int(hs) >= 1:
                return 1
        except: pass
    sv = story.get('search_volume') or story.get('search_potential_score')
    try:
        if sv is not None and int(sv) >= 30:
            return 1
    except: pass
    q = (story.get('query','') or story.get('title','') or story.get('seo_youtube_title','')).lower()
    hungry_keywords = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","executive order","bill","supreme court","white house","senate","congress","federal court","new law"]
    if any(k in q for k in hungry_keywords):
        return 1
    return 0

def save_story(story):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    title = clean_id(story.get('seo_youtube_title') or story.get('title', 'No Title'))
    url = story.get('url') or story.get('link') or ''
    all_sources = story.get('all_sources') or story.get('sources') or [url]
    if isinstance(all_sources, str):
        all_sources = [all_sources]

    retention_words = story.get('retention_words') or story.get('words') or 45
    retention_duration = story.get('retention_duration') or story.get('duration') or 13.0
    validation_pass = _extract_validation_pass(story)
    validation_keywords = story.get('validation_keywords') or json.dumps(["leaked","behind closed doors"])
    market_hungry = _extract_market_hungry(story)
    fps_used = story.get('fps_used') or random.choice([29.97, 30, 59.94, 60])
    tts_speed = story.get('tts_speed') or 1.15
    clip_density = story.get('clip_density') or 1.8
    scores_json = story.get('scores_json') or json.dumps(story.get('scores', {}))
    validation_score = story.get('validation_score') or story.get('confidence_score') or 85
    hungry_score = story.get('hungry_score') or market_hungry
    
    is_wire = 1 if ("reuters_wire" in str(story.get('source','')) or "google_news_wire" in str(story.get('source',''))) else 0
    wire_source = story.get('source','')[:100]
    fetch_window = story.get('fetch_window_minutes', 45)
    search_potential = story.get('search_potential_score') or story.get('search_volume', 0)
    is_trend = 1 if story.get('is_weekly_search_trend') else 0
    confidence = story.get('confidence_score', 0)
    seo_title = story.get('seo_youtube_title') or title
    seo_tags = json.dumps(story.get('seo_tags') or story.get('tags_all','').split()[:10])
    yt_search_opt = 1 if story.get('youtube_search_optimized') or story.get('seo_youtube_title') else 1
    asset_engine = story.get('asset_engine') or "duckduckgo + yt-dlp"
    img_dur = story.get('image_duration', 1.0)
    clip_dur = story.get('clip_duration', 1.8)
    visual_seg = json.dumps(story.get('script_visual_segments') or story.get('visual_segments', [])[:8])
    is_mainstream_blocked = 0
    ground_level = 1

    is_breakout = story.get('is_breakout', 0)
    breakout_score = story.get('breakout_score', 0)
    visualping_alert = ""
    breakout_source = ""

    try:
        c.execute("""INSERT INTO stories 
                     (title, url, sources, timestamp, status, retention_words, retention_duration, 
                      validation_pass, validation_keywords, market_hungry, fps_used, tts_speed, clip_density, scores_json, validation_score, hungry_score,
                      is_breakout, breakout_score, visualping_alert, breakout_source,
                      is_wire, wire_source, fetch_window_minutes, search_potential_score, is_weekly_search_trend, confidence_score,
                      seo_youtube_title, seo_tags, youtube_search_optimized, asset_engine, image_duration, clip_duration, visual_segments,
                      is_mainstream_blocked, ground_level_first) 
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (title, url, json.dumps(all_sources), time.time(), "scripted",
                   retention_words, retention_duration, validation_pass, validation_keywords,
                   market_hungry, fps_used, tts_speed, clip_density, scores_json, validation_score, hungry_score,
                   is_breakout, breakout_score, visualping_alert, breakout_source,
                   is_wire, wire_source, fetch_window, search_potential, is_trend, confidence,
                   seo_title, seo_tags, yt_search_opt, asset_engine, img_dur, clip_dur, visual_seg,
                   is_mainstream_blocked, ground_level))
    except sqlite3.OperationalError as e:
        print(f"[DB] Fallback insert due to {e}")
        c.execute("INSERT INTO stories (title, url, sources, timestamp, status) VALUES (?,?,?,?,?)",
                  (title, url, json.dumps(all_sources), time.time(), "scripted"))
    
    story_id = c.lastrowid
    
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at, is_weekly_search_trend, confidence_score, seo_youtube_title)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (story_id, retention_words, retention_duration, fps_used, tts_speed, clip_density, validation_pass, market_hungry, time.time(), is_trend, confidence, seo_title))
    except:
        try:
            c.execute("""INSERT INTO retention_stats 
                         (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at)
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (story_id, retention_words, retention_duration, fps_used, tts_speed, clip_density, validation_pass, market_hungry, time.time()))
        except:
            pass
    
    conn.commit()
    conn.close()
    tag = "🔍 SEARCH_TREND" if is_trend else ""
    print(f"[DB] Saved story {story_id}: {title[:50]} | {retention_words}w {retention_duration}s fps {fps_used} | val {validation_pass} hungry {market_hungry} {tag} Conf {confidence} Wire {wire_source[:20]} SEO {seo_title[:30]}")
    return story_id

def save_retention_stats(story_id, words, duration, fps_used=None, tts_speed=1.15, clip_density=1.8, validation_pass=True, market_hungry=True, scores=None, is_weekly_search_trend=False, confidence_score=85, seo_youtube_title=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""INSERT INTO retention_stats 
                     (story_id, words, duration, fps, tts_speed, clip_density, validation_pass, market_hungry, created_at, is_weekly_search_trend, confidence_score, seo_youtube_title)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (story_id, words, duration, fps_used or random.choice([29.97,30,59.94,60]), tts_speed, clip_density, int(validation_pass), int(market_hungry), time.time(), int(is_weekly_search_trend), int(confidence_score), seo_youtube_title))
        conn.commit()
        print(f"[DB RETENTION] Stats saved for {story_id}: {words}w {duration}s trend {int(is_weekly_search_trend)} conf {confidence_score}")
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
        c.execute("""SELECT s.id, s.title, s.retention_words, s.retention_duration, s.fps_used, s.tts_speed, s.validation_pass, s.market_hungry, s.yt_id, s.is_weekly_search_trend, s.confidence_score, s.seo_youtube_title 
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
        c.execute("SELECT COUNT(*), SUM(validation_pass), SUM(market_hungry), SUM(is_weekly_search_trend), AVG(confidence_score) FROM stories")
        total, val_pass, hungry, trend, avg_conf = c.fetchone()
        conn.close()
        return {"total": total or 0, "validation_pass": val_pass or 0, "hungry": hungry or 0, "search_trend": trend or 0, "avg_confidence": avg_conf or 0}
    except:
        conn.close()
        return {"total":0, "validation_pass":0, "hungry":0, "search_trend":0, "avg_confidence":0}

def get_breakout_stats():
    return get_search_velocity_stats()

def get_search_velocity_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*), SUM(confidence_score), AVG(confidence_score) FROM stories WHERE is_weekly_search_trend=1")
        count, score_sum, avg = c.fetchone()
        c.execute("SELECT title, confidence_score, seo_youtube_title, wire_source FROM stories WHERE is_weekly_search_trend=1 ORDER BY timestamp DESC LIMIT 5")
        recent = c.fetchall()
        conn.close()
        return {"search_trend_count": count or 0, "total_confidence": score_sum or 0, "avg_confidence": avg or 0, "recent": recent}
    except Exception as e:
        conn.close()
        return {"search_trend_count":0, "total_confidence":0, "avg_confidence":0, "recent":[]}

def get_search_seo_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*), SUM(youtube_search_optimized) FROM stories")
        count, seo = c.fetchone()
        conn.close()
        return {"total": count or 0, "seo_optimized": seo or 0}
    except:
        conn.close()
        return {"total":0, "seo_optimized":0}
