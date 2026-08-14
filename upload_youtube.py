from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

def get_youtube_service():
    # GitHub Secrets se login (runner pe token.json nahi hota)
    client_id = os.environ.get("YOUTUBE_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
    
    creds = None
    if refresh_token and client_id and client_secret:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        creds.refresh(Request())
    else:
        # Local pe token.json se login (shorts ke liye)
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
    
    if not creds:
        raise Exception("No credentials - Add token.json or YT_CLIENT_ID secrets")
    
    return build('youtube', 'v3', credentials=creds)

def upload_video(file_path, title, description, tags, thumbnail_path=None):
    # SHORTS KA PURANA CODE + GitHub support
    youtube = get_youtube_service()
    request = youtube.videos().insert(part="snippet,status",body={"snippet": {"title": title[:95], "description": description, "tags": tags[:15], "categoryId": "28"},"status": {"privacyStatus": "public"}},media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))
    response = request.execute()
    
    # LONG KA THUMBNAIL SUPPORT - Shorts me skip hoga
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"✅ Thumbnail uploaded: {thumbnail_path}")
        except Exception as e:
            print(f"⚠️ Thumbnail failed: {e}")
    
    return response
