import sqlite3, hashlib
import config

def is_duplicate(story):
    try:
        conn = sqlite3.connect(config.DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT title, url FROM history")
        for title, url in cur.fetchall():
            if story['url'] == url: return True
            if story['title'].lower()[:30] in title.lower(): return True
        return False
    except: return False
