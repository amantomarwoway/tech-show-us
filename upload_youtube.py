import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(video_path, title="Tech Shorts #Auto"):
    CLIENT_ID = os.environ['YT_CLIENT_ID']
    CLIENT_SECRET = os.environ['YT_CLIENT_SECRET']
    REFRESH_TOKEN = os.environ['YT_REFRESH_TOKEN']

    creds = Credentials(None, refresh_token=REFRESH_TOKEN, token_uri='https://oauth2.googleapis.com/token', client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=['https://www.googleapis.com/auth/youtube.upload'])
    creds.refresh(Request())
    youtube = build('youtube', 'v3', credentials=creds)

    print(f"Uploading {video_path}...")
    req = youtube.videos().insert(
        part="snippet,status",
        body={"snippet":{"title":title,"description":"#shorts #tech","categoryId":"28"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}},
        media_body=MediaFileUpload(video_path, resumable=True)
    )
    res = req.execute()
    print("SUCCESS:", f"https://youtu.be/{res['id']}")
    return res

# Test ke liye
if __name__ == "__main__":
    upload_video("final_video.mp4")
