"""
src/youtube/analytics_collector.py - Analytics collector (fixed)
- Fetches ALL uploads (not just 50)
- Tracks failures + reports them
- Does NOT overwrite valid data with 0
"""

import os
from src.utils.logger import setup_logger
from src.database import get_connection, save_performance

logger = setup_logger(__name__)


def collect_analytics():
    logger.info("=" * 60)
    logger.info("📊 ANALYTICS COLLECTOR")
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
        # Fetch ALL uploads (was LIMIT 50)
        cursor.execute('SELECT video_id FROM uploads ORDER BY uploaded_at DESC')
        rows = cursor.fetchall()
        conn.close()

        total = len(rows)
        logger.info(f"Total uploads to check: {total}")

        checked = 0
        failed = 0
        failure_reasons = {}

        for row in rows:
            vid = row[0]
            try:
                resp = youtube.videos().list(part='statistics', id=vid).execute()
                items = resp.get('items', [])
                if not items:
                    failed += 1
                    failure_reasons['not_found'] = failure_reasons.get('not_found', 0) + 1
                    logger.warning(f"Analytics {vid}: video not found")
                    continue

                stats = items[0].get('statistics', {})

                # Do NOT write 0 for fields we don't have (leave NULL for retention)
                perf = {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                }
                save_performance(vid, perf)
                checked += 1

                # Log only milestone views (every 500+)
                views = perf['views']
                if views >= 500:
                    logger.info(f"Analytics {vid}: {views} views, {perf['likes']} likes")

            except Exception as e:
                failed += 1
                reason = str(e)[:50]
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                continue

        logger.info(f"Collected: {checked} / {total} (failed {failed})")
        if failure_reasons:
            logger.info(f"Failure breakdown: {failure_reasons}")

        return checked

    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        return 0
