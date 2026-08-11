from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
def upload_video(file_path, title, description, tags):
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/youtube.upload'])
    youtube = build('youtube', 'v3', credentials=creds)
    request = youtube.videos().insert(part="snippet,status",body={"snippet": {"title": title[:95], "description": description, "tags": tags[:15], "categoryId": "28"},"status": {"privacyStatus": "public"}},media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True))
    return request.execute()
