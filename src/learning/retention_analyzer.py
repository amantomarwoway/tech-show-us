"""
src/learning/retention_analyzer.py - fixed
- Duration auto-reduce REMOVED
"""

from src.utils.logger import setup_logger
from src.database import get_connection
from src.learning.auto_optimizer import set_config

logger = setup_logger(__name__)


def analyze_retention():
    logger.info("=" * 60)
    logger.info("RETENTION ANALYZER")
    logger.info("=" * 60)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT s.title, MAX(p.views) as views,
                                 MAX(p.avg_percentage_viewed) as retention,
                                 MAX(p.likes) as likes, MAX(p.comments) as comments
                          FROM uploads u
                          JOIN stories s ON s.id = u.story_id
                          LEFT JOIN performance p ON p.video_id = u.video_id
                          WHERE p.views > 0
                            AND u.uploaded_at <= datetime('now', '-1 day')
                          GROUP BY s.id
                          ORDER BY views DESC
                          LIMIT 50''')
        rows = cursor.fetchall()
        conn.close()

        if not rows or len(rows) < 3:
            logger.info(f"Not enough retention data (have {len(rows) or 0})")
            return

        high = [r for r in rows if (r[2] or 0) > 50]
        low = [r for r in rows if (r[2] or 0) < 30 and (r[1] or 0) > 10]

        logger.info(f"High retention: {len(high)}")
        for r in high[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")

        logger.info(f"Low retention: {len(low)}")
        for r in low[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")

        if high:
            common = extract_common_words([r[0] for r in high])
            logger.info(f"Common in high retention: {common[:5]}")
            if common:
                set_config("high_retention_words", common[:10])

    except Exception as e:
        logger.error(f"Retention failed: {e}")


def extract_common_words(titles):
    from collections import Counter
    import re
    stop = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on',
            'at', 'to', 'for', 'of', 'and', 'or', 'but', 'with', 'from'}
    all_words = []
    for title in titles:
        words = re.findall(r'\b[a-z]{4,}\b', title.lower())
        all_words.extend([w for w in words if w not in stop])
    return [w for w, _ in Counter(all_words).most_common(20)]
