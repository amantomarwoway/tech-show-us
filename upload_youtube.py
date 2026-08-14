from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import os

def upload_video(file_path, title, description, tags, thumbnail_path=None):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
    youtube = build('youtube', 'v3', credentials=creds)
    request = youtube.videos().insert(part="snippet,status",body={"snippet": {"title": title[:95], "description": description, "tags": tags[:15], "categoryId": "28"},"status": {"privacyStatus": "public"}},media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))
    response = request.execute()
    
    # LONG VIDEO - Thumbnail support (shorts me skip hoga)
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=response['id'],
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print(f"✅ Thumbnail uploaded: {thumbnail_path}")
        except Exception as e:
            print(f"⚠️ Thumbnail upload failed but video uploaded: {e}")
    
    return response
