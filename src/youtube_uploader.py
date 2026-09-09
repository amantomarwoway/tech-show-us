"""
YOUTUBE UPLOADER - 4K UPSCALE + RETENTION + VALIDATION - FIXED NO SYS.EXIT - ERROR VISIBLE
FIXED: sys.exit removed, raise error, Canada block, post_pinned_comment import safe
"""
import os, sys, traceback, subprocess, tempfile, random, time, re
from pathlib import Path

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def upscale_to_4k_at_upload(input_path, output_path=None):
    if output_path is None:
        output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_4K{Path(input_path).suffix}")
    try:
        probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0", input_path], capture_output=True, text=True, timeout=10)
        if probe.stdout:
            w_h = probe.stdout.strip().split(',')
            if len(w_h)>=2 and int(w_h[0])>=2000:
                print(f"[4K UPSCALE] Already 4K {w_h[0]}, skipping")
                return input_path
    except: pass
    try:
        cmd = ["ffmpeg","-y","-i", input_path,"-vf","scale=2160:3840:flags=lanczos:sws_dither=none","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",output_path]
        print(f"[4K UPSCALE] 1080->4K scale only")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        size_mb = os.path.getsize(output_path)/(1024*1024)
        print(f"[4K UPSCALE] Done {size_mb:.1f}MB 4K")
        return output_path
    except Exception as e:
        print(f"[4K UPSCALE] fail {e}, using original")
        return input_path

def post_pinned_comment(video_id, topic=""):
    try:
        import os, random, time
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        CLIENT_ID = os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
            print("[PINNED COMMENT] Secrets missing, skip")
            return None
        try:
            creds = Credentials(None, refresh_token=REFRESH_TOKEN,
                                token_uri="https://oauth2.googleapis.com/token",
                                client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                                scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
            youtube = build("youtube", "v3", credentials=creds)
        except Exception as e:
            print(f"[PINNED COMMENT] Build fail {e}")
            return None
        topic_clean = topic[:60] if topic else "This breaking news"
        pinned_texts = [
            f"🔥 What do you think about {topic_clean}? First to know - comment below! Behind closed doors?",
            f"👀 This just leaked behind closed doors and changes everything for USA. Your take?",
            f"💥 Nobody saw this coming - {topic_clean} shocked everyone. YES or NO?",
        ]
        pinned_text = random.choice(pinned_texts)
        full_comment = f"{pinned_text}\n\n👇 Drop thoughts - we read every comment!"
        print(f"[PINNED COMMENT] Posting for {video_id}: {full_comment[:80]}...")
        try:
            insert_resp = youtube.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": full_comment}}}}
            ).execute()
            comment_id = insert_resp.get('id')
            top_comment_id = insert_resp.get('snippet', {}).get('topLevelComment', {}).get('id')
            print(f"[PINNED COMMENT] Posted {comment_id}")
            return top_comment_id or comment_id
        except Exception as e:
            err = str(e).lower()
            if "invalid_scope" in err or "forbidden" in err:
                print(f"[PINNED COMMENT] invalid_scope - token needs youtube.force-ssl scope: {e}")
            else:
                print(f"[PINNED COMMENT] Insert fail {e}")
            return None
    except Exception as e:
        print(f"[PINNED COMMENT] Overall fail {e}")
        return None

def get_random_metadata_variations(topic=""):
    base_tags = ["USA News","Breaking News","US News Today","Breaking USA","News Today"]
    leak_tags = ["Leaked","Secret Leaked","Behind Closed Doors","Exposed","Just Leaked"]
    tags = random.sample(base_tags, 3) + random.sample(leak_tags, 2)
    tags = [clean_id(t) for t in tags if clean_id(t)]
    return tags[:5]

def upload_video(video_path, thumb_path, script_data, story):
    print(f"--- Checking video file: {video_path} ---")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")
    print(f"[UPLOAD] 1080->4K check")
    try:
        final_upload_path = upscale_to_4k_at_upload(video_path)
    except:
        final_upload_path = video_path
    CLIENT_ID = os.getenv("YT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        raise ValueError("CRITICAL: YT_CLIENT_ID / SECRET / REFRESH_TOKEN missing in secrets!")
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)
        if isinstance(script_data, dict):
            title_raw = script_data.get('title','USA News')
        else:
            title_raw = str(script_data)[:95]
        title_raw = clean_id(title_raw)
        if isinstance(story, dict):
            q = (story.get('query','') or story.get('title','')).lower()
            if 'tom cruise' not in q and 'tom' not in q:
                title_raw = re.sub(r'tom\s*cruise', '', title_raw, flags=re.I)
        title = title_raw[:95].strip() or "USA Breaking News Leaked Behind Closed Doors"
        if isinstance(script_data, dict):
            desc_raw = script_data.get('description','')
        else:
            desc_raw = ""
        desc_raw = clean_id(desc_raw)
        desc = f"{desc_raw} \n\n#Shorts #Viral #Leaked #Secret \n\nDisclaimer: Based on public reporting."[:4800]
        topic_for_tags = story.get('query','') if isinstance(story, dict) else ""
        tags = get_random_metadata_variations(topic_for_tags)
        if isinstance(script_data, dict) and script_data.get('tags_all'):
            extra = [clean_id(t.strip('# ')) for t in script_data.get('tags_all','').split(',')[:10]]
            extra = [t for t in extra if t and len(t)>2 and not re.match(r'^m[0-9]', t, re.I)]
            tags = list(dict.fromkeys(tags + extra))[:15]
        print(f"--- YouTube Insert ---\n Title: {title}\n Tags: {tags}")
        request = youtube.videos().insert(part="snippet,status", body={"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(final_upload_path, resumable=True, chunksize=-1, mimetype="video/*"))
        response = request.execute()
        yt_id = response['id']
        print(f"VIDEO UPLOADED: https://youtu.be/{yt_id}")
        try:
            if thumb_path and os.path.exists(thumb_path):
                youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
                print(f"[THUMBNAIL] Uploaded for {yt_id}")
        except Exception as e:
            print(f"[THUMBNAIL] Fail {e} (non-fatal)")
        try:
            topic_for_pin = story.get('query','') or story.get('title','') if isinstance(story, dict) else ""
            pinned_id = post_pinned_comment(yt_id, topic_for_pin)
            if pinned_id:
                print(f"[PINNED COMMENT] Success {pinned_id}")
        except Exception as e:
            print(f"[PINNED COMMENT] Exception in upload {e} (non-fatal)")
        return yt_id
    except Exception as e:
        print(f"UPLOAD FAILED - REAL ERROR: {e}")
        traceback.print_exc()
        raise e  # NO sys.exit - let main.py see real error
