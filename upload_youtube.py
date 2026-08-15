from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os, time

def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
    creds = None
    if refresh_token and client_id and client_secret:
        try:
            print(f"✅ Using Secrets - {client_id[:15]}...")
            creds = Credentials(None, refresh_token=refresh_token, token_uri="https://oauth2.googleapis.com/token", client_id=client_id, client_secret=client_secret, scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"])
            creds.refresh(Request())
            print("✅ Credentials refreshed - PERMANENT")
            return build('youtube', 'v3', credentials=creds)
        except Exception as e:
            print(f"❌ Secrets refresh failed: {e}")
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return build('youtube', 'v3', credentials=creds)
        except Exception as e:
            print(f"token.json failed: {e}")
    print(f"DEBUG CLIENT_ID:{bool(client_id)} SECRET:{bool(client_secret)} REFRESH:{bool(refresh_token)}")
    raise Exception("No credentials - Add 3 YT secrets in GitHub")

def upload_video(file_path, title, description, tags, thumbnail_path=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    file_size = os.path.getsize(file_path)
    print(f"File: {file_path} - {file_size/(1024*1024):.2f} MB - Title: {title[:50]}")
    if file_size < 1000:
        raise Exception(f"Video corrupt: {file_size} bytes")
    youtube = get_youtube_service()
    clean_tags = [str(t).strip()[:25].lower() for t in (tags[:15] if tags else []) if len(str(t).strip())>=2]
    if len(clean_tags) < 3:
        clean_tags = ["product review", "tech review 2026 4k", "world trending"]
    final_title = title[:95].strip()
    print(f"Uploading - {final_title}")
    response = None
    for attempt in range(3):
        try:
            chunk_size = -1 if file_size < 50*1024*1024 else 10*1024*1024
            request = youtube.videos().insert(
                part="snippet,status",
                body={"snippet": {"title": final_title, "description": description[:4900], "tags": clean_tags, "categoryId": "28"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}},
                media_body=MediaFileUpload(file_path, chunksize=chunk_size, resumable=True, mimetype='video/mp4')
            )
            response = request.execute()
            if response and 'id' in response:
                print(f"✅ SUCCESS https://youtu.be/{response['id']}")
                break
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(10)
            if attempt == 2: raise
    if not response or 'id' not in response:
        raise Exception("Upload failed")
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(videoId=response['id'], media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')).execute()
        except: pass
    return response
