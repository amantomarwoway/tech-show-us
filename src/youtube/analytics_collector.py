"""
src/youtube/analytics_collector.py - Enhanced analytics
"""

import os
from src.utils.logger import setup_logger
from src.database import get_connection, save_performance

logger = setup_logger(__name__)


def collect_analytics():
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        cid = os.getenv("YT_CLIENT_ID", "")
        csec = os.getenv("YT_CLIENT_SECRET", "")
        rt = os.getenv("YT_REFRESH_TOKEN", "")
        
        if not all([cid, csec, rt]):
            logger.warning("Missing YT credentials")
            return 0
        
        creds = Credentials(
            token=None, refresh_token=rt,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cid, client_secret=csec,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"]
        )
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT video_id FROM uploads ORDER BY uploaded_at DESC LIMIT 50''')
        rows = cursor.fetchall()
        conn.close()
        
        checked = 0
        for row in rows:
            vid = row[0]
            try:
                resp = youtube.videos().list(part='statistics', id=vid).execute()
                items = resp.get('items', [])
                if not items:
                    continue
                stats = items[0].get('statistics', {})
                
                perf = {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'shares': 0,
                    'avg_view_duration': 0,
                    'avg_percentage_viewed': 0,
                    'subscribers_gained': 0,
                    'retention_score': 0,
                    'engagement_score': 0
                }
                save_performance(vid, perf)
                checked += 1
                logger.info(f"Analytics {vid}: {perf['views']} views, {perf['likes']} likes")
            except Exception as e:
                logger.warning(f"Analytics {vid}: {e}")
                continue
        
        logger.info(f"Collected: {checked} videos")
        return checked
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        return 0
