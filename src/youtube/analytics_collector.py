"""
src/youtube/analytics_collector.py - Collect video analytics
"""

import os
from src.utils.logger import setup_logger
from src.database import get_connection, save_performance

logger = setup_logger(__name__)


def collect_analytics():
    """Collect analytics for recent uploads"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        client_id = os.getenv("YT_CLIENT_ID", "")
        client_secret = os.getenv("YT_CLIENT_SECRET", "")
        refresh_token = os.getenv("YT_REFRESH_TOKEN", "")
        
        if not all([client_id, client_secret, refresh_token]):
            logger.warning("Missing YouTube credentials")
            return 0
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"]
        )
        
        youtube = build('youtube', 'v3', credentials=creds)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT video_id FROM uploads
            ORDER BY uploaded_at DESC
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        checked = 0
        
        for row in rows:
            video_id = row[0]
            
            try:
                response = youtube.videos().list(
                    part='statistics',
                    id=video_id
                ).execute()
                
                items = response.get('items', [])
                
                if not items:
                    continue
                
                stats = items[0].get('statistics', {})
                
                performance_data = {
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
                
                save_performance(video_id, performance_data)
                checked += 1
                
                logger.info(f"Analytics {video_id}: {performance_data['views']} views")
            
            except Exception as e:
                logger.warning(f"Analytics {video_id} failed: {e}")
                continue
        
        logger.info(f"Analytics collected: {checked} videos")
        return checked
    
    except Exception as e:
        logger.error(f"Analytics collector failed: {e}")
        return 0
