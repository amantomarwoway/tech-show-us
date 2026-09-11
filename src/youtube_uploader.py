import os, sys, traceback, subprocess, tempfile, random, time, re, requests
from pathlib import Path

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
def pro_headers():
    return {"User-Agent": random.choice(USER_AGENTS),"Cache-Control":"no-cache","X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(1,254)}"}

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def upscale_to_4k_at_upload_force(input_path, output_path=None):
    if output_path is None:
        output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_4K{Path(input_path).suffix}")
    for attempt in range(10):
        try:
            cmd = ["ffmpeg","-y","-i", input_path,"-vf","scale=2160:3840:flags=lanczos","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",output_path]
            print(f"[4K PRO FORCE] Attempt {attempt+1}")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
            if os.path.exists(output_path) and os.path.getsize(output_path)>1000:
                return output_path
        except Exception as e:
            print(f"[4K PRO] Fail {e} attempt {attempt} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError(f"8K upscale failed after 10 attempts - NO FALLBACK")

def post_pinned_comment_force(video_id, topic=""):
    for attempt in range(10):
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            CLIENT_ID = os.getenv("YT_CLIENT_ID")
            CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
            REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
            if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
                raise RuntimeError("YT secrets missing - NO FALLBACK")
            creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
            youtube = build("youtube", "v3", credentials=creds)
            pinned_texts = [f"🔥 What do you think about {topic[:60]}? Behind closed doors secret out?"]
            full_comment = f"{random.choice(pinned_texts)}\n\n👇 Drop thoughts! cb={random.randint(1000,9999)}"
            insert_resp = youtube.commentThreads().insert(part="snippet", body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": full_comment}}}}).execute()
            return insert_resp.get('id')
        except Exception as e:
            print(f"[PINNED PRO] Fail {e} attempt {attempt} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError(f"Pinned comment failed after 10 - NO FALLBACK")

def upload_video(video_path, thumb_path, script_data, story):
    print(f"--- Checking video file: {video_path} - PRO FORCE NO FALLBACK ---")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path} - NO FALLBACK")
    final_upload_path = upscale_to_4k_at_upload_force(video_path)
    CLIENT_ID = os.getenv("YT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise ValueError("CRITICAL: YT secrets missing - NO FALLBACK")
    for attempt in range(10):
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=["https://www.googleapis.com/auth/youtube.upload"])
            youtube = build("youtube", "v3", credentials=creds)
            title_raw = clean_id(script_data.get('title','USA News') if isinstance(script_data, dict) else str(script_data)[:95])
            title = title_raw[:95].strip() or "USA Breaking News Leaked Behind Closed Doors 2025"
            desc_raw = clean_id(script_data.get('description','') if isinstance(script_data, dict) else "")
            desc = f"{desc_raw}\n\n#Shorts #Viral #Leaked #Secret\n\nDisclaimer: Based on public reporting. cb={random.randint(1000,9999)}"[:4800]
            tags = ["USA News","Breaking News","Leaked","Secret Leaked","Behind Closed Doors"][:15]
            print(f"--- YouTube Insert PRO FORCE Attempt {attempt+1} ---\n Title: {title}")
            request = youtube.videos().insert(part="snippet,status", body={"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "25"}, "status": {"privacyStatus": "public"}}, media_body=MediaFileUpload(final_upload_path, resumable=True, chunksize=-1, mimetype="video/*"))
            response = request.execute()
            yt_id = response['id']
            print(f"VIDEO UPLOADED FORCE: https://youtu.be/{yt_id}")
            if thumb_path and os.path.exists(thumb_path):
                youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
            post_pinned_comment_force(yt_id, story.get('title','') if isinstance(story, dict) else "")
            return yt_id
        except Exception as e:
            print(f"UPLOAD FAILED FORCE Attempt {attempt+1}: {e} - FORCE RETRY")
            traceback.print_exc()
            if attempt==9:
                raise e
            time.sleep((2**attempt)+random.uniform(0,1))
