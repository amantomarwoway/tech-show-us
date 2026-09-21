"""
src/learning/retention_analyzer.py - Retention analysis (fixed)
- Duration auto-reduce REMOVED
- Only learns common words from high-retention videos
"""

from src.utils.logger import setup_logger
from src.database import get_connection
from src.learning.auto_optimizer import set_config

logger = setup_logger(__name__)


def analyze_retention():
    logger.info("=" * 60)
    logger.info("📊 RETENTION ANALYZER")
    logger.info("=" * 60)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Only videos 24h+ old, dedupe by story
        cursor.execute('''
            SELECT s.title, MAX(p.views) as views,
                   MAX(p.avg_percentage_viewed) as retention,
                   MAX(p.likes) as likes, MAX(p.comments) as comments
            FROM uploads u
            JOIN stories s ON s.id = u.story_id
            LEFT JOIN performance p ON p.video_id = u.video_id
            WHERE p.views > 0
              AND u.uploaded_at <= datetime('now', '-1 day')
            GROUP BY s.id
            ORDER BY views DESC
            LIMIT 50
        ''')

        rows = cursor.fetchall()
        conn.close()

        if not rows or len(rows) < 3:
            logger.info(f"Not enough retention data (have {len(rows) or 0}, need 3+)")
            return

        high_retention = [r for r in rows if (r[2] or 0) > 50]
        low_retention = [r for r in rows if (r[2] or 0) < 30 and (r[1] or 0) > 10]

        logger.info(f"📈 High retention videos: {len(high_retention)}")
        for r in high_retention[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")

        logger.info(f"📉 Low retention videos: {len(low_retention)}")
        for r in low_retention[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")

        if high_retention:
            common_words = extract_common_words([r[0] for r in high_retention])
            logger.info(f"🎯 Common words in high retention: {common_words[:5]}")
            if common_words:
                set_config("high_retention_words", common_words[:10])

        # Duration auto-reduce REMOVED — main.py controls duration now

    except Exception as e:
        logger.error(f"Retention analysis failed: {e}")


def extract_common_words(titles):
    from collections import Counter
    import re

    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on',
                  'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'from'}

    all_words = []
    for title in titles:
        words = re.findall(r'\b[a-z]{4,}\b', title.lower())
        all_words.extend([w for w in words if w not in stop_words])

    counter = Counter(all_words)
    return [w for w, _ in counter.most_common(20)]
