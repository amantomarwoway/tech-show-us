import sqlite3, os, json, time, random
from src.config import DB_PATH, USER_AGENTS, pro_headers, pro_fetch
def init_db():
    os.makedirs("data",exist_ok=True)
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS stories (id INTEGER PRIMARY KEY, title TEXT, url TEXT, timestamp REAL, status TEXT, yt_id TEXT, confidence_score INTEGER, search_potential_score INTEGER, seo_youtube_title TEXT, views INTEGER DEFAULT 0, retention REAL DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS evolution_log (id INTEGER PRIMARY KEY, timestamp REAL, old_config TEXT, new_config TEXT, improvement REAL)")
    conn.commit(); conn.close()
    print("[DB PRO] Initialized - NO FALLBACK - FORCE")
def save_story(story):
    conn=sqlite3.connect(DB_PATH); c=conn.cursor()
    c.execute("INSERT INTO stories (title,url,timestamp,status,confidence_score,search_potential_score,seo_youtube_title) VALUES (?,?,?,?,?,?,?)",(story.get('seo_youtube_title') or story.get('title',''), story.get('url',''), time.time(), "scripted", story.get('confidence_score',85), story.get('search_potential_score',80), story.get('seo_youtube_title','')))
    sid=c.lastrowid; conn.commit(); conn.close(); return sid
def mark_uploaded(sid, ytid):
    conn=sqlite3.connect(DB_PATH); c=conn.cursor(); c.execute("UPDATE stories SET status='uploaded', yt_id=? WHERE id=?",(ytid,sid)); conn.commit(); conn.close()
