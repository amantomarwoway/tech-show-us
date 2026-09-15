"""
src/learning/ab_tester.py - A/B testing for hooks and titles
"""

import random
import json
from datetime import datetime
from src.utils.logger import setup_logger
from src.database import get_connection

logger = setup_logger(__name__)

def create_ab_test(story, variants):
    """
    Create A/B test for a story
    
    variants: dict with hook_a, hook_b, title_a, title_b
    """
    test_id = f"test_{int(datetime.now().timestamp())}"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ab_tests (
            id TEXT PRIMARY KEY,
            story_id INTEGER,
            variant_a TEXT,
            variant_b TEXT,
            variant_a_views INTEGER DEFAULT 0,
            variant_b_views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        INSERT INTO ab_tests (id, story_id, variant_a, variant_b)
        VALUES (?, ?, ?, ?)
    ''', (test_id, story.get('id', 0),
          json.dumps(variants.get('a', {})),
          json.dumps(variants.get('b', {}))))
    
    conn.commit()
    conn.close()
    
    logger.info(f"A/B test created: {test_id}")
    return test_id


def select_variant(test_id):
    """Randomly select variant A or B"""
    return random.choice(['a', 'b'])


def record_result(test_id, variant, views):
    """Record A/B test result"""
    conn = get_connection()
    cursor = conn.cursor()
    
    column = 'variant_a_views' if variant == 'a' else 'variant_b_views'
    
    cursor.execute(f'''
        UPDATE ab_tests SET {column} = {column} + ?
        WHERE id = ?
    ''', (views, test_id))
    
    conn.commit()
    conn.close()


def get_winning_variant(test_id):
    """Get winning variant based on views"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM ab_tests WHERE id = ?', (test_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    row = dict(row)
    views_a = row['variant_a_views']
    views_b = row['variant_b_views']
    
    if views_a > views_b * 1.2:
        return 'a'
    elif views_b > views_a * 1.2:
        return 'b'
    else:
        return 'tie'
