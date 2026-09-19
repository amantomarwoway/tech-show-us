"""
src/learning/retention_analyzer.py - Deep retention analysis
"""

from src.utils.logger import setup_logger
from src.database import get_connection
from src.learning.auto_optimizer import get_config, set_config

logger = setup_logger(__name__)


def analyze_retention():
    """
    Deep analysis of retention data
    Identifies best/worst performing patterns
    """
    logger.info("=" * 60)
    logger.info("📊 RETENTION ANALYZER")
    logger.info("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get recent videos with retention
        cursor.execute('''
            SELECT s.title, p.views, p.avg_percentage_viewed, p.likes, p.comments
            FROM uploads u
            JOIN stories s ON s.id = u.story_id
            LEFT JOIN performance p ON p.video_id = u.video_id
            WHERE p.views > 0
            ORDER BY u.uploaded_at DESC
            LIMIT 30
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows or len(rows) < 3:
            logger.info("Not enough retention data")
            return
        
        # Analyze retention patterns
        high_retention = [r for r in rows if (r[2] or 0) > 50]
        low_retention = [r for r in rows if (r[2] or 0) < 30 and (r[1] or 0) > 10]
        
        logger.info(f"📈 High retention videos: {len(high_retention)}")
        for r in high_retention[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")
        
        logger.info(f"📉 Low retention videos: {len(low_retention)}")
        for r in low_retention[:5]:
            logger.info(f"   {r[2]:.0f}% | {r[1]} views | {r[0][:50]}")
        
        # Learn from high retention titles
        if high_retention:
            common_words = extract_common_words([r[0] for r in high_retention])
            logger.info(f"🎯 Common words in high retention: {common_words[:5]}")
            
            if common_words:
                set_config("high_retention_words", common_words[:10])
        
        # If low retention is high, suggest shorter videos
        if len(low_retention) > len(high_retention):
            logger.info("⚠️ More low retention than high - reducing duration")
            current = get_config("video_duration", 30)
            new = max(15, current - 5)
            set_config("video_duration", new)
        
    except Exception as e:
        logger.error(f"Retention analysis failed: {e}")


def extract_common_words(titles):
    """Extract common words from titles"""
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
