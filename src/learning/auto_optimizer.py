"""
src/learning/auto_optimizer.py - v3
- Duration auto-adjust REMOVED
- 24h+ data window
- Fixed hook classifier (6 patterns)
"""

import json
from datetime import datetime
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)


DEFAULT_AUTONOMOUS_CONFIG = {
    "clip_density": 0.8,
    "tts_speed": 1.15,
    "hook_style": "statement",
    "title_pattern": "reason",
    "emotion_style": "auto",
    "voice_style": "ryan",
    "bar_color": "green",
    "best_hours_utc": [13, 17, 20, 23, 2],
    "upload_frequency": 5,
    "min_trending_score": 5000,
    "min_viral_score": 65,
    "total_videos_analyzed": 0,
    "best_performing_topic": "",
    "best_performing_hook": "",
    "best_performing_title": "",
    "avg_views": 0,
    "avg_retention": 0,
    "last_updated": datetime.now().isoformat(),
    "version": 3,
}


def init_autonomous_config():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS autonomous_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        config_key TEXT UNIQUE,
        config_value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS performance_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_type TEXT, pattern_value TEXT,
        avg_views REAL, avg_retention REAL, sample_count INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ab_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_name TEXT, variant_a TEXT, variant_b TEXT,
        a_views INTEGER DEFAULT 0, b_views INTEGER DEFAULT 0,
        a_count INTEGER DEFAULT 0, b_count INTEGER DEFAULT 0,
        winner TEXT, status TEXT DEFAULT 'running',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    for key, value in DEFAULT_AUTONOMOUS_CONFIG.items():
        cursor.execute('INSERT OR IGNORE INTO autonomous_config (config_key, config_value) VALUES (?, ?)',
                       (key, json.dumps(value)))
    conn.commit()
    conn.close()
    logger.info("Autonomous config initialized")


def get_config(key, default=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT config_value FROM autonomous_config WHERE config_key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return default if default is not None else DEFAULT_AUTONOMOUS_CONFIG.get(key)
    except Exception:
        return default if default is not None else DEFAULT_AUTONOMOUS_CONFIG.get(key)


def set_config(key, value):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO autonomous_config (config_key, config_value, updated_at)
                          VALUES (?, ?, CURRENT_TIMESTAMP)''', (key, json.dumps(value)))
        conn.commit()
        conn.close()
        logger.info(f"Config updated: {key} = {value}")
    except Exception as e:
        logger.error(f"Config write failed {key}: {e}")


def get_all_config():
    config = dict(DEFAULT_AUTONOMOUS_CONFIG)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT config_key, config_value FROM autonomous_config')
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            try:
                config[row[0]] = json.loads(row[1])
            except Exception:
                pass
    except Exception:
        pass
    return config


def _classify_hook(title):
    tl = (title or "").lower().strip()
    if not tl:
        return "other"
    if '?' in title:
        return "question"
    if any(ch.isdigit() for ch in title[:20]):
        return "number"
    if any(w in tl for w in ['nobody', 'shocking', 'insane', 'crazy',
                             'unbelievable', 'secret', 'revealed', 'exposed',
                             'truth', 'banned', 'deleted', 'removed']):
        return "shock"
    if any(w in tl for w in ['reason', 'why', 'how', 'what happened',
                             'behind', 'until', 'before', 'after']):
        return "mystery"
    if any(w in tl for w in ['broke', 'won', 'lost', 'smashed', 'beat',
                             'hit', 'changed', 'saved', 'destroyed']):
        return "statement"
    return "other"


def analyze_and_optimize():
    logger.info("=" * 60)
    logger.info("AUTO-OPTIMIZER v3")
    logger.info("=" * 60)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT s.id, s.title, s.canonical_topic,
                                 MAX(p.views) AS views,
                                 MAX(p.likes) AS likes,
                                 MAX(p.comments) AS comments,
                                 MAX(p.avg_percentage_viewed) AS retention,
                                 u.uploaded_at
                          FROM uploads u
                          JOIN stories s ON s.id = u.story_id
                          LEFT JOIN performance p ON p.video_id = u.video_id
                          WHERE u.uploaded_at <= datetime('now', '-1 day')
                          GROUP BY s.id
                          ORDER BY views DESC
                          LIMIT 100''')
        rows = cursor.fetchall()
        conn.close()

        if not rows or len(rows) < 5:
            logger.info(f"Not enough mature data (have {len(rows) or 0})")
            return

        videos = [{'id': r[0], 'title': r[1] or '', 'topic': r[2] or '',
                   'views': r[3] or 0, 'likes': r[4] or 0,
                   'comments': r[5] or 0, 'retention': r[6] or 0} for r in rows]

        avg_views = sum(v['views'] for v in videos) / len(videos)
        avg_retention = sum(v['retention'] for v in videos) / len(videos)

        logger.info(f"Analyzed {len(videos)} mature videos (24h+)")
        logger.info(f"   Avg views: {avg_views:.0f}")
        logger.info(f"   Avg retention: {avg_retention:.1f}%")
        logger.info(f"   Best: {videos[0]['views']} views")

        if videos[0]['views'] > 500:
            set_config("best_performing_topic", videos[0]['topic'])
            set_config("best_performing_title", videos[0]['title'])
            logger.info(f"   Best topic: {videos[0]['topic'][:60]}")

        set_config("avg_views", int(avg_views))
        set_config("avg_retention", round(avg_retention, 1))
        set_config("total_videos_analyzed", len(videos))
        set_config("last_updated", datetime.now().isoformat())

        # Hook classifier
        style_perf = {}
        for v in videos:
            style = _classify_hook(v['title'])
            style_perf.setdefault(style, []).append(v['views'])

        best_style = None
        best_avg = 0
        for style, views_list in style_perf.items():
            avg = sum(views_list) / len(views_list)
            logger.info(f"   Hook '{style}': {avg:.0f} views ({len(views_list)} vids)")
            if avg > best_avg and len(views_list) >= 3:
                best_avg = avg
                best_style = style

        if best_style:
            current = get_config("hook_style", "statement")
            if best_style != current:
                set_config("hook_style", best_style)
                logger.info(f"   Hook updated: {current} -> {best_style}")

        # Title pattern
        patterns = {'reason': 'the reason', 'truth': 'the truth about',
                    'nobody': 'nobody', 'broke': 'broke the internet',
                    'really': 'what really happened', 'bigger': 'bigger than'}
        pattern_perf = {}
        for v in videos:
            tl = v['title'].lower()
            for pname, ptext in patterns.items():
                if ptext in tl:
                    pattern_perf.setdefault(pname, []).append(v['views'])

        best_pat = None
        best_pat_avg = 0
        for pname, views_list in pattern_perf.items():
            if len(views_list) < 2:
                continue
            avg = sum(views_list) / len(views_list)
            if avg > best_pat_avg:
                best_pat_avg = avg
                best_pat = pname

        if best_pat:
            current = get_config("title_pattern", "reason")
            if best_pat != current:
                set_config("title_pattern", best_pat)
                logger.info(f"   Title pattern: {current} -> {best_pat}")

        logger.info("=" * 60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Auto-optimizer failed: {e}")


def create_ab_test(test_name, variant_a, variant_b):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO ab_tests (test_name, variant_a, variant_b)
                          VALUES (?, ?, ?)''',
                       (test_name, json.dumps(variant_a), json.dumps(variant_b)))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"A/B test failed: {e}")


def get_active_ab_test(test_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''SELECT id, variant_a, variant_b, a_views, b_views, a_count, b_count
                          FROM ab_tests WHERE test_name = ? AND status = 'running'
                          ORDER BY id DESC LIMIT 1''', (test_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'id': row[0], 'variant_a': json.loads(row[1]), 'variant_b': json.loads(row[2]),
                    'a_views': row[3], 'b_views': row[4], 'a_count': row[5], 'b_count': row[6]}
    except Exception:
        pass
    return None


def record_ab_result(test_id, variant, views):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if variant == 'a':
            cursor.execute('UPDATE ab_tests SET a_views = a_views + ?, a_count = a_count + 1 WHERE id = ?', (views, test_id))
        else:
            cursor.execute('UPDATE ab_tests SET b_views = b_views + ?, b_count = b_count + 1 WHERE id = ?', (views, test_id))
        conn.commit()
        conn.close()
    except Exception:
        pass
