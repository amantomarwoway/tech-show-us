"""
YOUTUBE UPLOADER - 4K UPSCALE AT UPLOAD TIME + RETENTION + VALIDATION
Location: src/youtube_uploader.py
Edits:
- 4K Upscale at upload time only (1080->4K) for chamak, bot impact zero during generation
- Retention metadata preserved
- All original secrets + upload flow preserved
"""
import os, sys, traceback, subprocess, tempfile, random, time
from pathlib import Path

def upscale_to_4k_at_upload(input_path, output_path=None):
    """
    4K Upscale logic - ONLY at upload time, not during generation
    1080x1920 -> 2160x3840 (portrait 4K)
    Uses FFmpeg with high quality upscale for chamak
    Bot impact zero - generation was 1080, upload is 4K
    """
    if output_path is None:
        output_path = str(Path(input_path).parent / f"{Path(input_path).stem}_4K{Path(input_path).suffix}")
    
    # Check if already 4K
    try:
        probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0", input_path],
                               capture_output=True, text=True)
        if probe.stdout:
            w_h = probe.stdout.strip().split(',')
            if len(w_h)>=2:
                w=int(w_h[0])
                if w>=2000: # already 4K
                    print(f"[4K UPSCALE] Already 4K {w}, skipping upscale")
                    return input_path
    except:
        pass

    # FFmpeg upscale to 4K with high quality + light sharpening for chamak
    # zscale for quality, unsharp for chamak, keep NTSC fps as is
    try:
        # Portrait 4K: 2160x3840, but keep aspect, upscale from 1080x1920
        cmd = [
            "ffmpeg","-y",
            "-i", input_path,
            "-vf", "scale=2160:3840:flags=lanczos:sws_dither=none,unsharp=5:5:0.8:3:3:0.4",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",  # high quality for 4K chamak
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        print(f"[4K UPSCALE] Starting: {input_path} -> {output_path} (1080->4K chamak)")
        start = time.time()
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elapsed = time.time() - start
        size_mb = os.path.getsize(output_path)/(1024*1024)
        print(f"[4K UPSCALE] Done in {elapsed:.1f}s, size {size_mb:.1f}MB, 1080->2160x3840")
        return output_path
    except Exception as e:
        print(f"[4K UPSCALE] FFmpeg fail {e}, using original 1080")
        return input_path

def get_random_metadata_variations():
    """VvSA: random tags variation for anti-bot"""
    base_tags = ["USA News","Breaking News","US News Today","Breaking USA","News Today"]
    leak_tags = ["Leaked","Secret Leaked","Behind Closed Doors","Exposed","Just Leaked"]
    # Random 3 from base + 2 from leak for validation factory SEO
    tags = random.sample(base_tags, 3) + random.sample(leak_tags, 2)
    random.shuffle(tags)
    return tags

def upload_video(video_path, thumb_path, script_data, story):
    print(f"--- Checking video file: {video_path} ---")
    if not os.path.exists(video_path):
        print(f"CRITICAL: video file not found!")
        raise FileNotFoundError(video_path)

    # ===== 4K UPSCALE AT UPLOAD TIME - CHAMAK =====
    print(f"[UPLOAD] Original generation was 1080x1920 (retention + anti-bot), now upscaling to 4K for chamak at upload time")
    try:
        upscaled_path = upscale_to_4k_at_upload(video_path)
        final_upload_path = upscaled_path
        if upscaled_path != video_path:
            print(f"[UPLOAD] Using 4K upscaled: {final_upload_path}")
        else:
            print(f"[UPLOAD] Using original 1080 (upscale skipped)")
    except Exception as e:
        print(f"[4K UPSCALE] Error {e}, using original")
        final_upload_path = video_path

    # Secrets check
    CLIENT_ID = os.getenv("YT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")
    print(f"Secrets present? CID:{bool(CLIENT_ID)} CSECRET:{bool(CLIENT_SECRET)} RTOKEN:{bool(REFRESH_TOKEN)}")
    
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("CRITICAL: YouTube Secrets missing in GitHub Actions!")
        sys.exit(1)

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build("youtube", "v3", credentials=creds)

        # Title + Description with validation factory SEO
        title_raw = script_data.get('title','USA News') if isinstance(script_data, dict) else str(script_data)[:95]
        title = title_raw[:95]
        
        desc_raw = script_data.get('description','') if isinstance(script_data, dict) else ''
        # Add retention + validation disclaimer
        retention_note = "\n\n#Shorts #Viral #Leaked #Secret #BehindClosedDoors"
        disclaimer = "\n\nDisclaimer: This is an original news summary based on publicly available reporting. All claims are sourced. First to know effect."
        desc = f"{desc_raw} {retention_note} {disclaimer}"
        desc = desc[:4800] # YT limit 5000

        # Tags with anti-bot randomisation + leak tags
        tags = get_random_metadata_variations()
        if isinstance(script_data, dict) and script_data.get('tags_all'):
            extra_tags = [t.strip('# ') for t in script_data.get('tags_all','').split(',')[:5]]
            tags = list(set(tags + extra_tags))[:15]
        
        print(f"--- Starting YouTube Insert (4K) ---")
        print(f" Title: {title}")
        print(f" Tags: {tags}")
        print(f" File: {final_upload_path} (4K upscaled for chamak)")
        
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": "25"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(final_upload_path, resumable=True, chunksize=-1, mimetype="video/*")
        )
        response = request.execute()
        yt_id = response['id']
        print(f"VIDEO UPLOADED (4K CHAMAK): https://youtu.be/{yt_id}")

        # Thumbnail - fail hua toh video toh upload ho chuka hai
        try:
            if thumb_path and os.path.exists(thumb_path):
                youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
                print("Thumbnail uploaded")
        except Exception as thumb_e:
            print(f"Thumbnail fail (ignore): {thumb_e}")

        # Cleanup 4K temp file if created
        try:
            if final_upload_path != video_path and os.path.exists(final_upload_path):
                # Keep for logs, but can delete if too large
                print(f"[4K] Keeping upscaled file for record: {final_upload_path}")
                # os.remove(final_upload_path) # uncomment if want to save space
        except:
            pass

        return yt_id

    except Exception as e:
        print(f"!!! YOUTUBE UPLOAD FAILED !!! {e}")
        traceback.print_exc()
        sys.exit(1)
