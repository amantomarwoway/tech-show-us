from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os, time

def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
    creds = None
    if refresh_token and client_id and client_secret:
        try:
            print(f"Using Secrets - {client_id[:10]}...")
            creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret, scopes=["https://www.googleapis.com/auth/youtube.upload"])
            creds.refresh(Request())
            print("Credentials refreshed")
        except Exception as e:
            print(f"Secrets refresh failed: {e}")
            creds = None
    if not creds and os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
        except Exception as e:
            print(f"token.json failed: {e}")
            creds = None
    if not creds:
        raise Exception("No credentials - Add YT secrets or token.json")
    return build('youtube', 'v3', credentials=creds)

def upload_video(file_path, title, description, tags, thumbnail_path=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    file_size = os.path.getsize(file_path)
    print(f"File: {file_path} - {file_size/(1024*1024):.2f} MB - Title: {title[:50]}")
    if file_size < 1000:
        raise Exception(f"Video file corrupt: {file_size} bytes")
    youtube = get_youtube_service()
    clean_tags = []
    for t in (tags[:15] if tags else []):
        t = str(t).strip()[:25].lower()
        if len(t) >= 2:
            clean_tags.append(t)
    if len(clean_tags) < 3:
        clean_tags = ["product review", "big machine", "army machine", "world trending", "tech review 2026 4k"]
    final_title = title[:95].strip()
    print(f"Uploading 4K - Category 28 - Tags: {clean_tags[:3]}")
    max_retries = 3
    response = None
    for attempt in range(max_retries):
        try:
            chunk_size = 10 * 1024 * 1024
            if file_size < 50 * 1024 * 1024:
                chunk_size = -1
            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {"title": final_title, "description": description[:4900], "tags": clean_tags, "categoryId": "28"},
                    "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
                },
                media_body=MediaFileUpload(file_path, chunksize=chunk_size, resumable=True, mimetype='video/mp4')
            )
            print(f"Upload attempt {attempt+1}/{max_retries} - {file_size/(1024*1024):.1f} MB")
            response = request.execute()
            if response and 'id' in response:
                video_id = response['id']
                print(f"UPLOAD SUCCESS - Video ID: {video_id} - https://youtu.be/{video_id}")
                break
        except Exception as e:
            print(f"Upload attempt {attempt+1} failed: {e}")
            time.sleep(10)
            if attempt == max_retries - 1:
                raise
    if not response or 'id' not in response:
        raise Exception("Upload failed - no video ID")
    video_id = response['id']
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            print(f"Uploading thumbnail: {thumbnail_path}")
            youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')).execute()
            print("Thumbnail uploaded")
        except Exception as e:
            print(f"Thumbnail upload failed (non-critical): {e}")
    else:
        print(f"Thumbnail not found: {thumbnail_path} - skipping OK for shorts")
    print(f"FINAL SUCCESS 4K - https://youtu.be/{video_id}")
    return response
