"""
src/learning/auto_optimizer.py - AUTONOMOUS BRAIN
Duration capped at 20s (safe for GitHub Actions)
"""

import json
import random
from datetime import datetime, timedelta
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)


DEFAULT_AUTONOMOUS_CONFIG = {
    "video_duration": 18,           # ✅ Default 18s (safe)
    "clip_density": 0.8,
    "tts_speed": 1.15,
    "words_target": 50,
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
    "version": 2
}


def init_autonomous_config():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE,
            config_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT,
            pattern_value TEXT,
            avg_views REAL,
            avg_retention REAL,
            sample_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            variant_a TEXT,
            variant_b TEXT,
            a_views INTEGER DEFAULT 0,
            b_views INTEGER DEFAULT 0,
            a_count INTEGER DEFAULT 0,
            b_count INTEGER DEFAULT 0,
            winner TEXT,
            status TEXT DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    for key, value in DEFAULT_AUTONOMOUS_CONFIG.items():
        cursor.execute('''
            INSERT OR IGNORE INTO autonomous_config (config_key, config_value)
            VALUES (?, ?)
        ''', (key, json.dumps(value)))
    
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
    except Exception as e:
        logger.warning(f"Config read failed {key}: {e}")
        return default if default is not None else DEFAULT_AUTONOMOUS_CONFIG.get(key)


def set_config(key, value):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO autonomous_config (config_key, config_value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value)))
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
            except:
                pass
    except:
        pass
    return config


def analyze_and_optimize():
    logger.info("=" * 60)
    logger.info("AUTO-OPTIMIZER - Learning from performance")
    logger.info("=" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.id, s.title, s.canonical_topic,
                   p.views, p.likes, p.comments, p.avg_percentage_viewed,
                   u.uploaded_at
            FROM uploads u
            JOIN stories s ON s.id = u.story_id
            LEFT JOIN performance p ON p.video_id = u.video_id
            ORDER BY u.uploaded_at DESC
            LIMIT 50
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows or len(rows) < 5:
            logger.info("Not enough data yet (need 5+)")
            return
        
        videos = []
        for row in rows:
            videos.append({
                'id': row[0], 'title': row[1], 'topic': row[2],
                'views': row[3] or 0, 'likes': row[4] or 0,
                'comments': row[5] or 0, 'retention': row[6] or 0,
            })
        
        videos.sort(key=lambda x: x['views'], reverse=True)
        
        total_views = sum(v['views'] for v in videos)
        avg_views = total_views / len(videos) if videos else 0
        avg_retention = sum(v['retention'] for v in videos) / len(videos) if videos else 0
        
        logger.info(f"Analyzed {len(videos)} videos")
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
        
        # ============================================================
        # DURATION OPTIMIZATION (capped 12-20s)
        # ============================================================
        top_10 = videos[:10]
        top_avg = sum(v['views'] for v in top_10) / len(top_10) if top_10 else 0
        
        if top_avg > avg_views * 1.5:
            logger.info(f"   Top 10 avg: {top_avg:.0f} ({(top_avg/avg_views):.1f}x)")
            
            # If low retention → shorter
            if avg_retention < 40:
                current = get_config("video_duration", 18)
                new_duration = max(12, current - 2)     # ← Cap min 12
                if new_duration != current:
                    set_config("video_duration", new_duration)
                    logger.info(f"   Duration reduced: {current}s -> {new_duration}s")
            
            # If high retention → slightly longer (max 20)
            elif avg_retention > 70:
                current = get_config("video_duration", 18)
                new_duration = min(20, current + 2)     # ← Cap max 20
                if new_duration != current:
                    set_config("video_duration", new_duration)
                    logger.info(f"   Duration increased: {current}s -> {new_duration}s")
        
        # ============================================================
        # HOOK STYLE
        # ============================================================
        style_perf = {}
        for v in videos:
            title = v['title'].lower()
            if '?' in title:
                style = 'question'
            elif any(w in title for w in ['reason', 'truth', 'nobody', 'broke']):
                style = 'statement'
            else:
                style = 'other'
            if style not in style_perf:
                style_perf[style] = []
            style_perf[style].append(v['views'])
        
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
        
        # ============================================================
        # TITLE PATTERN
        # ============================================================
        patterns = {
            'reason': 'the reason', 'truth': 'the truth about',
            'nobody': 'nobody', 'broke': 'broke the internet',
            'really': 'what really happened', 'bigger': 'bigger than'
        }
        
        pattern_perf = {}
        for v in videos:
            tl = v['title'].lower()
            for pname, ptext in patterns.items():
                if ptext in tl:
                    if pname not in pattern_perf:
                        pattern_perf[pname] = []
                    pattern_perf[pname].append(v['views'])
        
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
        
        # ============================================================
        # CLIP DENSITY
        # ============================================================
        if avg_retention < 50:
            current = get_config("clip_density", 0.8)
            new_density = max(0.5, current - 0.1)
            if new_density != current:
                set_config("clip_density", round(new_density, 2))
                logger.info(f"   Clip density: {current}s -> {new_density}s")
        
        logger.info("=" * 60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Auto-optimizer failed: {e}")


def create_ab_test(test_name, variant_a, variant_b):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ab_tests (test_name, variant_a, variant_b)
            VALUES (?, ?, ?)
        ''', (test_name, json.dumps(variant_a), json.dumps(variant_b)))
        conn.commit()
        conn.close()
        logger.info(f"A/B test created: {test_name}")
    except Exception as e:
        logger.warning(f"A/B test failed: {e}")


def get_active_ab_test(test_name):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, variant_a, variant_b, a_views, b_views, a_count, b_count
            FROM ab_tests WHERE test_name = ? AND status = 'running'
            ORDER BY id DESC LIMIT 1
        ''', (test_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0], 'variant_a': json.loads(row[1]), 'variant_b': json.loads(row[2]),
                'a_views': row[3], 'b_views': row[4], 'a_count': row[5], 'b_count': row[6]
            }
    except:
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
        
        cursor.execute('SELECT a_count, b_count, a_views, b_views FROM ab_tests WHERE id = ?', (test_id,))
        row = cursor.fetchone()
        
        if row and row[0] >= 5 and row[1] >= 5:
            a_avg = row[2] / row[0]
            b_avg = row[3] / row[1]
            winner = 'a' if a_avg > b_avg * 1.2 else ('b' if b_avg > a_avg * 1.2 else 'tie')
            cursor.execute('UPDATE ab_tests SET winner = ?, status = "done" WHERE id = ?', (winner, test_id))
            logger.info(f"A/B test done: Winner = {winner} (A:{a_avg:.0f} B:{b_avg:.0f})")
        
        conn.commit()
        conn.close()
    except:
        pass
