"""
YOUTUBE UPLOADER - 4K UPSCALE AT UPLOAD TIME - NO HEAVY CHAMAK, ONLY 4K SCALE
FIXED: heavy chamak removed, only 4K scale, ID leak removed, no disable
Location: src/youtube_uploader.py
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
    """
    FIXED: 4K upscale ONLY scale, NO unsharp/heavy chamak
    User asked: chamak hata dena sirf 4k rehne dena
    """
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
        # FIXED: Only lanczos scale, NO unsharp filter - heavy chamak removed
        cmd = ["ffmpeg","-y","-i", input_path,"-vf","scale=2160:3840:flags=lanczos:sws_dither=none","-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",output_path]
        print(f"[4K UPSCALE] 1080->2160x3840 scale only (no heavy chamak) - as requested")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        size_mb = os.path.getsize(output_path)/(1024*1024)
        print(f"[4K UPSCALE] Done {size_mb:.1f}MB 4K")
        return output_path
    except Exception as e:
        print(f"[4K UPSCALE] fail {e}, using original")
        return input_path

def get_random_metadata_variations(topic=""):
    base_tags = ["USA News","Breaking News","US News Today","Breaking USA","News Today"]
    leak_tags = ["Leaked","Secret Leaked","Behind Closed Doors","Exposed","Just Leaked"]
    tags = random.sample(base_tags, 3) + random.sample(leak_tags, 2)
    random.shuffle(tags)
    tags = [clean_id(t) for t in tags if clean_id(t)]
    return tags[:5]

def upload_video(video_path, thumb_path, script_data, story):
    print(f"--- Checking video file: {video_path} ---")
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)
    print(f"[UPLOAD] 1080 -> 4K scale only (heavy chamak removed)")
    try:
        upscaled_path = upscale_to_4k_at_upload(video_path)
        final_upload_path = upscaled_path
    except:
        final_upload_path = video_path
    CLIENT_ID = os.getenv("YT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("CRITICAL: Secrets missing!"); sys.exit(1)
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=["https://www.googleapis.com/auth/youtube.upload"])
        youtube = build("youtube", "v3", credentials=creds)
        title_raw = script_data.get('title','USA News') if isinstance(script_data, dict) else str(script_data)[:95]
        title_raw = clean_id(title_raw)
        if isinstance(story, dict):
            q = (story.get('query','') or story.get('title','')).lower()
            if 'tom cruise' not in q and 'tom' not in q:
                title_raw = re.sub(r'tom\s*cruise', '', title_raw, flags=re.I)
                title_raw = re.sub(r'#tomcruise', '', title_raw, flags=re.I)
        title = title_raw[:95].strip() or "USA Breaking News Leaked Behind Closed Doors"
        desc_raw = script_data.get('description','') if isinstance(script_data, dict) else ''
        desc_raw = clean_id(desc_raw)
        desc = f"{desc_raw} \n\n#Shorts #Viral #Leaked #Secret #BehindClosedDoors \n\nDisclaimer: Original summary based on public reporting."[:4800]
        topic_for_tags = story.get('query','') if isinstance(story, dict) else ""
        tags = get_random_metadata_variations(topic_for_tags)
        if isinstance(script_data, dict) and script_data.get('tags_all'):
            extra = [clean_id(t.strip('# ')) for t in script_data.get('tags_all','').split(',')[:10]]
            extra = [t for t in extra if t and len(t)>2 and not re.match(r'^m[0-9]', t, re.I) and '/m/' not in t.lower()]
            if 'tom' not in topic_for_tags.lower():
                extra = [t for t in extra if 'tomcruise' not in t.lower()]
            tags = list(dict.fromkeys(tags + extra))[:15]
        print(f"--- YouTube Insert (4K no heavy chamak) ---\n Title: {title}\n Tags: {tags}")
        request = youtube.videos().insert(part="snippet,status", body={"snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(final_upload_path, resumable=True, chunksize=-1, mimetype="video/*"))
        response = request.execute()
        yt_id = response['id']
        print(f"VIDEO UPLOADED (4K no heavy chamak): https://youtu.be/{yt_id}")
        try:
            if thumb_path and os.path.exists(thumb_path):
                youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
        except: pass
        return yt_id
    except Exception as e:
        print(f"UPLOAD FAILED {e}"); traceback.print_exc(); sys.exit(1)
