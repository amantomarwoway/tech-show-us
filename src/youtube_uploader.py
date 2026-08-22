import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(video_path, thumb_path, script_data, story):
    try:
        creds = Credentials(
            None,
            refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("YOUTUBE_CLIENT_ID"),
            client_secret=os.getenv("YOUTUBE_CLIENT_SECRET"),
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )
        youtube = build('youtube','v3', credentials=creds)

        title = script_data['title_candidates'][0][:95] # YouTube limit
        desc = f"""{script_data['description']}

What happened: {script_data['what_happened']}
Why it matters: {script_data['why_matters']}

Sources:
{chr(10).join([s['url'] for s in story['all_sources']])}

Disclaimer: This is an original news summary based on publicly available reporting from {script_data['sources']}. Not affiliated with any news network. Date: {story['published']}

#USANews #NewsExplainer
"""

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": desc, "tags": ["USA News","Breaking News"], "categoryId": "25"},
                "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
            },
            media_body=MediaFileUpload(video_path)
        )
        response = request.execute()
        yt_id = response['id']

        # Thumbnail
        if os.path.exists(thumb_path):
            youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumb_path)).execute()

        return yt_id
    except Exception as e:
        print(f"YouTube upload fail: {e}")
        return None
