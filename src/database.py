import json, time, os, sqlite3

DB_PATH = "data/database.db"

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS stories
                 (id INTEGER PRIMARY KEY, title TEXT, url TEXT, sources TEXT, timestamp REAL, status TEXT, yt_id TEXT)""")
    conn.commit()
    conn.close()

def save_story(story):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # FIX:.get use kar rahe hain, direct ['all_sources'] nahi
    title = story.get('title', 'No Title')
    url = story.get('url') or story.get('link') or ''
    all_sources = story.get('all_sources') or story.get('sources') or [url]
    if isinstance(all_sources, str):
        all_sources = [all_sources]

    c.execute("INSERT INTO stories (title, url, sources, timestamp, status) VALUES (?,?,?,?,?)",
              (title, url, json.dumps(all_sources), time.time(), "scripted"))
    story_id = c.lastrowid
    conn.commit()
    conn.close()
    return story_id

def mark_uploaded(story_id, yt_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE stories SET status='uploaded', yt_id=? WHERE id=?", (yt_id, story_id))
    conn.commit()
    conn.close()
