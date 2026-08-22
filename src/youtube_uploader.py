import os
import sys
import traceback
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(video_path, thumb_path, script_data, story):
    print(f"--- Checking video file: {video_path} ---")
    if not os.path.exists(video_path):
        print(f"CRITICAL: video file not found!")
        raise FileNotFoundError(video_path)

    # Secrets check
    cid = os.getenv("YOUTUBE_CLIENT_ID")
    csecret = os.getenv("YOUTUBE_CLIENT_SECRET")
    rtoken = os.getenv("YOUTUBE_REFRESH_TOKEN")
    print(f"Secrets present? CID:{bool(cid)} CSECRET:{bool(csecret)} RTOKEN:{bool(rtoken)}")
    
    if not all([cid, csecret, rtoken]):
        print("CRITICAL: YouTube Secrets missing in GitHub Actions!")
        sys.exit(1)

    try:
        creds = Credentials(
            None,
            refresh_token=rtoken,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cid,
            client_secret=csecret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build("youtube", "v3", credentials=creds)

        title = script_data.get('title','USA News')[:95]
        desc = f"{script_data.get('description','')} \n\nDisclaimer: This is an original news summary based on publicly available reporting. #USANews #NewsExplainer"

        print("--- Starting YouTube Insert ---")
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": desc, "tags": ["USA News","Breaking News"], "categoryId": "25"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(video_path, resumable=True, chunksize=-1, mimetype="video/*")
        )
        response = request.execute()
        yt_id = response['id']
        print(f"VIDEO UPLOADED: https://youtu.be/{yt_id}")

        # Thumbnail - fail hua toh video toh upload ho chuka hai
        try:
            if thumb_path and os.path.exists(thumb_path):
                youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")).execute()
                print("Thumbnail uploaded")
        except Exception as thumb_e:
            print(f"Thumbnail fail (ignore): {thumb_e}")

        return yt_id

    except Exception as e:
        print(f"!!! YOUTUBE UPLOAD FAILED !!! {e}")
        traceback.print_exc()
        sys.exit(1)  # Ab green tick nahi, seedha red fail hoga aur error dikhega
