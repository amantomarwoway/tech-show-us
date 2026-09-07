"""
comment_engine.py - First 10 comments fetch + witty provocative reply (10 limit)
"""
import os, time, random
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

WITTY_REPLIES = [
    "First to know effect 🔥 What do y'all think - is this leaked true?",
    "Behind closed doors secret is out - you won't believe what's next 👀",
    "This changes everything for USA. Agree or not? Comment below 👇",
    "Inside sources just revealed this - shocking truth exposed!",
    "You saw it here first - before mainstream media. Thoughts?",
    "Leaked docs don't lie. What's your take on this?",
    "Nobody saw this coming - game changer moment.",
    "Secret deal just exposed. How big is this for America?",
    "Breaking behind closed doors - your opinion matters, drop it!",
    "Just leaked and already viral. Should we trust this?",
]

PROVOCATIVE_QUESTIONS = [
    "Do you think this was planned behind closed doors?",
    "Is this the biggest leak this month? Yes or No?",
    "Who benefits from this secret leak?",
    "Should this have stayed secret? What do you think?",
    "First to know - will this change your vote?",
]

def fetch_first_10_comments(video_id):
    """Fetch first 10 comments"""
    try:
        CLIENT_ID=os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                          client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                          scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
        youtube=build("youtube","v3",credentials=creds)
        resp=youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=10, order="relevance").execute()
        comments=[]
        for item in resp.get('items',[]):
            snippet=item['snippet']['topLevelComment']['snippet']
            comments.append({
                "comment_id": item['snippet']['topLevelComment']['id'],
                "text": snippet['textDisplay'],
                "author": snippet['authorDisplayName']
            })
        print(f"[COMMENTS] Fetched {len(comments)} for {video_id}")
        return comments
    except Exception as e:
        print(f"[COMMENTS] Fetch fail {video_id} {e}")
        return []

def reply_witty_provocative(video_id, comment_id=None):
    """Witty provocative reply (10 limit per video)"""
    try:
        CLIENT_ID=os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                          client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                          scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
        youtube=build("youtube","v3",credentials=creds)
        
        if comment_id:
            # Reply to specific comment
            reply_text=random.choice(WITTY_REPLIES) + " " + random.choice(PROVOCATIVE_QUESTIONS)
            youtube.comments().insert(part="snippet", body={
                "snippet": {"parentId": comment_id, "textOriginal": reply_text}
            }).execute()
            print(f"[COMMENTS] Replied to {comment_id}: {reply_text[:60]}")
            return True
        else:
            # Auto reply to first 10 comments - 10 limit
            comments=fetch_first_10_comments(video_id)
            count=0
            for com in comments[:10]:
                if count>=10:
                    break
                try:
                    reply_text=random.choice(WITTY_REPLIES)
                    youtube.comments().insert(part="snippet", body={
                        "snippet": {"parentId": com['comment_id'], "textOriginal": reply_text}
                    }).execute()
                    print(f"[COMMENTS] Reply {count+1}/10 to {com['author']}: {reply_text[:50]}")
                    count+=1
                    time.sleep(random.uniform(3,6))  # anti-spam delay
                except Exception as e:
                    print(f"[COMMENTS] Reply fail {e}")
                    continue
            return count
    except Exception as e:
        print(f"[COMMENTS] Reply fail {e}")
        return 0

def run_comment_engine_for_latest(limit_videos=3):
    """Run for latest 3 videos"""
    try:
        import sqlite3
        conn=sqlite3.connect("data/database.db")
        c=conn.cursor()
        c.execute("SELECT yt_id FROM stories WHERE yt_id IS NOT NULL ORDER BY timestamp DESC LIMIT ?", (limit_videos,))
        rows=c.fetchall()
        conn.close()
        for (yt_id,) in rows:
            reply_witty_provocative(yt_id)
            time.sleep(10)
    except Exception as e:
        print(f"[COMMENTS] Run fail {e}")

if __name__=="__main__":
    run_comment_engine_for_latest()
