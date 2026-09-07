"""
reupload_manager.py - Smart Re-uploader - 24hr <2.5k views = delete + pexel random + new title + re-upload
"""
import os, time, json, sqlite3, random, subprocess
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = "data/database.db"

def check_reupload_candidates():
    """24hr <2.5k views = reupload candidate"""
    try:
        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()
        cutoff=time.time() - 24*3600
        c.execute("SELECT id, title, yt_id, timestamp FROM stories WHERE status='uploaded' AND timestamp < ? ORDER BY timestamp DESC", (cutoff,))
        rows=c.fetchall()
        conn.close()
    except Exception as e:
        print(f"[REUPLOAD] DB fail {e}")
        return []
    
    candidates=[]
    try:
        from analytics_monitor import fetch_youtube_analytics
        for story_id, title, yt_id, ts in rows[-10:]:  # last 10 old
            try:
                stats=fetch_youtube_analytics(yt_id)
                views=stats.get('views',0) if isinstance(stats, dict) else stats[0].get('views',0) if stats else 0
                age_hr=(time.time()-ts)/3600
                if age_hr>=24 and views<2500:
                    print(f"[REUPLOAD] Candidate: {yt_id} views {views} age {age_hr:.1f}h <2.5k")
                    candidates.append({"story_id": story_id, "yt_id": yt_id, "title": title, "views": views, "age_hr": age_hr})
            except Exception as e:
                print(f"[REUPLOAD] stats fail for {yt_id} {e}")
                continue
            time.sleep(0.4)
    except:
        pass
    return candidates

def smart_reupload_process(candidate):
    """delete + pexel random + new title + re-upload"""
    yt_id=candidate['yt_id']
    old_title=candidate['title']
    print(f"[REUPLOAD] Starting smart reupload for {yt_id} - {old_title[:40]}")
    
    try:
        # 1. Delete old video
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        CLIENT_ID=os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
            print("[REUPLOAD] Secrets missing, mock delete")
        else:
            creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                              client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                              scopes=["https://www.googleapis.com/auth/youtube"])
            youtube=build("youtube","v3",credentials=creds)
            youtube.videos().delete(id=yt_id).execute()
            print(f"[REUPLOAD] Deleted old video {yt_id}")
    except Exception as e:
        print(f"[REUPLOAD] Delete fail (maybe already deleted) {e}")
    
    # 2. Pexel random + new title
    try:
        from title_changer import get_new_trending_title
        new_title=get_new_trending_title(old_title)
    except:
        new_title=f"{old_title.split('Leaked')[0].strip()} Leaked {random.choice(['Exposed','Behind Closed Doors','Secret'])}"
    
    print(f"[REUPLOAD] New title: {new_title}")
    
    # 3. Re-create video with pexel random logic
    try:
        # Call main generation with MANUAL_TOPIC
        os.environ["MANUAL_TOPIC"]=new_title
        os.environ["PEXELS_RANDOM"]="1"
        # Import and run main's video creation part only
        from script_generator import generate_script
        from video_generator import create_video
        from thumbnail_generator import create_thumbnail
        from youtube_uploader import upload_video
        from database import save_story, mark_uploaded
        
        story_dict={"title": new_title, "query": new_title, "url": "", "source": "reupload", "search_volume": 80}
        script_data=generate_script(story_dict)
        video_path=create_video(script_data, story_dict)
        thumb_path=create_thumbnail(script_data, story_dict)
        new_yt_id=upload_video(video_path, thumb_path, script_data, story_dict)
        story_id=save_story(story_dict)
        mark_uploaded(story_id, new_yt_id)
        print(f"[REUPLOAD] Re-uploaded: https://youtu.be/{new_yt_id} old views {candidate['views']}")
        return new_yt_id
    except Exception as e:
        print(f"[REUPLOAD] Re-create fail {e}")
        import traceback; traceback.print_exc()
        return None

def run_reupload_check():
    cands=check_reupload_candidates()
    for cand in cands:
        smart_reupload_process(cand)
        time.sleep(5)  # gap between reuploads

if __name__=="__main__":
    run_reupload_check()
