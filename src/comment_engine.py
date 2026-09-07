"""
comment_engine.py - FIXED
- First 10 comments fetch + witty provocative reply (10 limit)
- FIX 12: invalid_scope: Bad Request comment fetch fail -> handle force-ssl scope fallback + graceful skip
"""
import os, time, random, traceback

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

def _get_youtube_client(scopes=None):
    """FIX: try force-ssl, fallback to youtube scope if invalid_scope"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    CLIENT_ID=os.getenv("YT_CLIENT_ID")
    CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
    REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("[COMMENTS] Secrets missing, skip")
        return None
    if scopes is None:
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
    try:
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                          client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=scopes)
        youtube=build("youtube","v3",credentials=creds)
        return youtube
    except Exception as e:
        err_str=str(e).lower()
        if "invalid_scope" in err_str or "bad request" in err_str:
            print(f"[COMMENTS] invalid_scope with {scopes}, trying fallback youtube scope")
            try:
                # Fallback: use youtube scope (covers comments if token has it)
                fallback_scopes=["https://www.googleapis.com/auth/youtube"]
                creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                                  client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=fallback_scopes)
                youtube=build("youtube","v3",credentials=creds)
                return youtube
            except Exception as e2:
                print(f"[COMMENTS] Fallback also fail {e2} - OAuth token needs re-consent with youtube scope, skipping comment engine")
                return None
        else:
            print(f"[COMMENTS] Client build fail {e}")
            return None

def fetch_first_10_comments(video_id):
    """Fetch first 10 comments - FIXED invalid_scope"""
    try:
        youtube=_get_youtube_client(scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
        if youtube is None:
            # Try readonly fallback for fetch only
            youtube=_get_youtube_client(scopes=["https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube"])
            if youtube is None:
                print(f"[COMMENTS] No client for fetch {video_id}, skip")
                return []
        resp=youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=10, order="relevance").execute()
        comments=[]
        for item in resp.get('items',[]):
            try:
                snippet=item['snippet']['topLevelComment']['snippet']
                comments.append({
                    "comment_id": item['snippet']['topLevelComment']['id'],
                    "text": snippet['textDisplay'],
                    "author": snippet['authorDisplayName']
                })
            except:
                continue
        print(f"[COMMENTS] Fetched {len(comments)} for {video_id}")
        return comments
    except Exception as e:
        err=str(e).lower()
        if "invalid_scope" in err or "insufficient" in err or "forbidden" in err or "bad request" in err:
            print(f"[COMMENTS] Fetch fail invalid_scope/forbidden {video_id} - token missing youtube.force-ssl scope, needs re-consent. Skipping: {e}")
        else:
            print(f"[COMMENTS] Fetch fail {video_id} {e}")
        return []

def reply_witty_provocative(video_id, comment_id=None):
    """Witty provocative reply (10 limit per video) - FIXED invalid_scope"""
    try:
        youtube=_get_youtube_client(scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
        if youtube is None:
            print(f"[COMMENTS] No client for reply {video_id}, skip - needs OAuth re-consent with youtube.force-ssl")
            return 0
        
        if comment_id:
            reply_text=random.choice(WITTY_REPLIES) + " " + random.choice(PROVOCATIVE_QUESTIONS)
            try:
                youtube.comments().insert(part="snippet", body={
                    "snippet": {"parentId": comment_id, "textOriginal": reply_text}
                }).execute()
                print(f"[COMMENTS] Replied to {comment_id}: {reply_text[:60]}")
                return 1
            except Exception as e:
                err=str(e).lower()
                if "invalid_scope" in err or "forbidden" in err or "bad request" in err:
                    print(f"[COMMENTS] Reply invalid_scope - token lacks comment scope, skip: {e}")
                    return 0
                raise

        else:
            comments=fetch_first_10_comments(video_id)
            if not comments:
                print(f"[COMMENTS] No comments to reply for {video_id}")
                return 0
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
                    time.sleep(random.uniform(3,6))
                except Exception as e:
                    err=str(e).lower()
                    if "invalid_scope" in err or "forbidden" in err or "quota" in err:
                        print(f"[COMMENTS] Reply fail {err[:100]} - stopping")
                        break
                    print(f"[COMMENTS] Reply fail {e}")
                    continue
            return count
    except Exception as e:
        err=str(e).lower()
        if "invalid_scope" in err or "bad request" in err:
            print(f"[COMMENTS] Reply fail invalid_scope {video_id} - OAuth token needs re-consent with https://www.googleapis.com/auth/youtube.force-ssl scope. Go to Google Cloud Console > OAuth consent > re-generate refresh token with youtube.force-ssl scope. Skipping gracefully.")
            return 0
        print(f"[COMMENTS] Reply fail {e}")
        traceback.print_exc()
        return 0

def run_comment_engine_for_latest(limit_videos=3):
    try:
        import sqlite3
        db_path="data/database.db"
        if not os.path.exists(db_path):
            print("[COMMENTS] DB not found, skip")
            return
        conn=sqlite3.connect(db_path)
        c=conn.cursor()
        c.execute("SELECT yt_id FROM stories WHERE yt_id IS NOT NULL AND yt_id != '' ORDER BY timestamp DESC LIMIT ?", (limit_videos,))
        rows=c.fetchall()
        conn.close()
        for (yt_id,) in rows:
            if not yt_id:
                continue
            reply_witty_provocative(yt_id)
            time.sleep(10)
    except Exception as e:
        print(f"[COMMENTS] Run fail {e}")

if __name__=="__main__":
    run_comment_engine_for_latest()
