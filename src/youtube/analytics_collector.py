"""
src/youtube/analytics_collector.py - fixed
- Fetches ALL uploads, tracks failures gracefully
- Reports valid vs dead IDs
"""

import os
from src.utils.logger import setup_logger
from src.database import get_connection, save_performance

logger = setup_logger(__name__)


def collect_analytics():
    logger.info("=" * 60)
    logger.info("ANALYTICS COLLECTOR")
    logger.info("=" * 60)

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
        cursor.execute('SELECT video_id FROM uploads ORDER BY uploaded_at DESC')
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        logger.info(f"Total uploads to check: {total}")

        checked = 0
        dead = 0
        dead_ids = []

        for row in rows:
            vid = row[0]
            try:
                resp = youtube.videos().list(part='statistics', id=vid).execute()
                items = resp.get('items', [])
                if not items:
                    dead += 1
                    dead_ids.append(vid)
                    continue

                stats = items[0].get('statistics', {})
                perf = {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                }
                save_performance(vid, perf)
                checked += 1

            except Exception as e:
                dead += 1
                logger.debug(f"Analytics {vid}: {str(e)[:60]}")
                continue

        logger.info(f"Collected: {checked} valid, {dead} dead IDs")

        # Clean dead IDs from database
        if dead_ids:
            try:
                conn = get_connection()
                cur = conn.cursor()
                placeholders = ','.join('?' * len(dead_ids))
                cur.execute(f'DELETE FROM uploads WHERE video_id IN ({placeholders})', dead_ids)
                deleted = cur.rowcount
                conn.commit()
                conn.close()
                logger.info(f"Cleaned {deleted} dead video IDs from database")
            except Exception as e:
                logger.warning(f"DB cleanup failed: {e}")

        return checked

    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        return 0
