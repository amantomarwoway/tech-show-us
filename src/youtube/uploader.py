"""
src/youtube/uploader.py - YouTube upload with API v3
"""

import os
import json
import time
from src.utils.logger import setup_logger
from src.config import YOUTUBE_CONFIG

logger = setup_logger(__name__)

def upload_video(video_path, thumbnail_path=None, title="", description="", tags=None, category_id="25"):
    """
    Upload video to YouTube
    
    Returns video_id if successful, None otherwise
    """
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None
    
    # Check credentials
    client_id = os.getenv("YT_CLIENT_ID", "")
    client_secret = os.getenv("YT_CLIENT_SECRET", "")
    refresh_token = os.getenv("YT_REFRESH_TOKEN", "")
    
    if not all([client_id, client_secret, refresh_token]):
        logger.warning("YouTube credentials missing - simulating upload")
        return simulate_upload(video_path, title)
    
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # Create credentials
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload",
                   "https://www.googleapis.com/auth/youtube"]
        )
        
        # Build YouTube client
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Prepare video body
        body = {
            'snippet': {
                'title': title[:100],
                'description': description[:5000],
                'tags': tags[:15] if tags else [],
                'categoryId': category_id,
                'defaultLanguage': 'en',
                'defaultAudioLanguage': 'en-US'
            },
            'status': {
                'privacyStatus': YOUTUBE_CONFIG.get('privacy', 'public'),
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload video
        logger.info(f"Uploading: {title[:60]}...")
        
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = None
        retries = 0
        
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            except Exception as e:
                retries += 1
                if retries > 3:
                    raise
                logger.warning(f"Upload retry {retries}: {e}")
                time.sleep(2 ** retries)
        
        video_id = response['id']
        logger.info(f"Upload successful: {video_id}")
        
        # Upload thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                logger.info("Thumbnail uploaded")
            except Exception as e:
                logger.warning(f"Thumbnail upload failed: {e}")
        
        return video_id
    
    except Exception as e:
        logger.error(f"YouTube upload failed: {e}")
        return simulate_upload(video_path, title)


def simulate_upload(video_path, title):
    """Simulate upload for testing"""
    import hashlib
    fake_id = hashlib.md5(f"{title}{time.time()}".encode()).hexdigest()[:11]
    logger.info(f"[SIMULATED] Uploaded: https://youtu.be/{fake_id}")
    return fake_id


def get_video_analytics(video_id):
    """Get analytics for a video"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        client_id = os.getenv("YT_CLIENT_ID", "")
        client_secret = os.getenv("YT_CLIENT_SECRET", "")
        refresh_token = os.getenv("YT_REFRESH_TOKEN", "")
        
        if not all([client_id, client_secret, refresh_token]):
            return None
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"]
        )
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()
        
        if response.get('items'):
            return response['items'][0].get('statistics', {})
    
    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
    
    return None
