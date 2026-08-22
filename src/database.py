import sqlite3, time, json
import config

def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS history
    (id INTEGER PRIMARY KEY, title TEXT, url TEXT, sources TEXT, first_seen REAL, status TEXT, youtube_id TEXT)""")
    conn.commit()

def save_story(story):
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO history (title, url, sources, first_seen, status) VALUES (?,?,?,?,?)",
                (story['title'], story['url'], json.dumps(story['all_sources']), time.time(), "scripted"))
    conn.commit()
    return cur.lastrowid

def mark_uploaded(story_id, yt_id):
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute("UPDATE history SET status='uploaded', youtube_id=? WHERE id=?", (yt_id, story_id))
    conn.commit()
