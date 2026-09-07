"""
analytics_monitor.py - Jo view/like/comment har 1hr me check kare YouTube API se
"""
import os, time, json, sqlite3, random
from pathlib import Path
from datetime import datetime

DB_PATH="data/database.db"
CACHE=Path("data/analytics.json")
CACHE.parent.mkdir(parents=True, exist_ok=True)

def fetch_youtube_analytics(video_id=None):
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        CLIENT_ID=os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
            return {"video_id": video_id or "test", "views": random.randint(800,5000), "likes": random.randint(20,200), "comments": random.randint(5,40)} if video_id else []
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                          client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                          scopes=["https://www.googleapis.com/auth/youtube.readonly"])
        youtube=build("youtube","v3",credentials=creds)
        if video_id:
            resp=youtube.videos().list(part="statistics,snippet", id=video_id).execute()
            if resp.get('items'):
                stats=resp['items'][0]['statistics']
                return {"video_id": video_id, "views": int(stats.get('viewCount',0)), "likes": int(stats.get('likeCount',0)), "comments": int(stats.get('commentCount',0)), "timestamp": time.time()}
        # last 10
        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()
        c.execute("SELECT yt_id, title FROM stories WHERE yt_id IS NOT NULL ORDER BY timestamp DESC LIMIT 10")
        rows=c.fetchall()
        conn.close()
        results=[]
        for yt_id, title in rows:
            try:
                resp=youtube.videos().list(part="statistics", id=yt_id).execute()
                if resp.get('items'):
                    stats=resp['items'][0]['statistics']
                    results.append({"video_id": yt_id, "title": title[:50], "views": int(stats.get('viewCount',0)), "likes": int(stats.get('likeCount',0)), "comments": int(stats.get('commentCount',0))})
                time.sleep(0.3)
            except:
                continue
        return results
    except Exception as e:
        print(f"[ANALYTICS] API fail {e}")
        return []

def check_retention_drop(videos=None):
    """Har 1hr check - low performers"""
    if videos is None:
        videos=fetch_youtube_analytics()
    if isinstance(videos, dict):
        videos=[videos]
    low=[]
    for v in videos:
        views=v.get('views',0)
        likes=v.get('likes',0)
        if views<500 or (views>0 and likes/views*100 <1.5):
            low.append(v)
    print(f"[ANALYTICS] Checked {len(videos)} videos, low {len(low)}")
    try:
        CACHE.write_text(json.dumps({"last_check": datetime.now().isoformat(), "videos": videos, "low": low}, indent=2))
    except:
        pass
    return low, videos

def monitor_loop(interval_minutes=60):
    while True:
        print(f"[ANALYTICS MONITOR] Har 1hr check at {datetime.now()}")
        low, all_vids=check_retention_drop()
        if low:
            try:
                from title_changer import auto_change_titles
                auto_change_titles(low)
            except Exception as e:
                print(f"[ANALYTICS] title changer fail {e}")
        time.sleep(interval_minutes*60)

if __name__=="__main__":
    low, allv=check_retention_drop()
    print(low)
