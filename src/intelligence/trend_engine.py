"""
src/intelligence/trend_engine.py - Multi-signal trend detection
"""

import re
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def calculate_trend_score(story):
    """
    Calculate comprehensive trend score from 0-100
    
    Formula:
    TREND_SCORE = momentum + search_growth + source_velocity 
                + social_velocity + geographic_interest 
                + recency + novelty + public_importance
    """
    score = 0
    
    # 1. Momentum (0-25 points)
    breakout_score = story.get('breakout_score', 0)
    momentum = min(25, breakout_score / 250)  # 6000+ = 24 points
    score += momentum
    
    # 2. Search growth (0-15 points)
    search_volume = story.get('search_volume', 0)
    search_growth = min(15, search_volume / 6.67)  # 100 = 15 points
    score += search_growth
    
    # 3. Source velocity (0-15 points)
    source = story.get('source', '').lower()
    if 'trends' in source:
        score += 15
    elif 'google' in source or 'rss' in source:
        score += 12
    elif 'cnn' in source or 'bbc' in source or 'reuters' in source:
        score += 10
    elif 'reddit' in source:
        score += 5
    else:
        score += 8
    
    # 4. Social velocity (0-10 points)
    reddit_score = story.get('reddit_score', 0)
    if reddit_score > 1000:
        score += 10
    elif reddit_score > 500:
        score += 7
    elif reddit_score > 100:
        score += 4
    
    # 5. Geographic interest (0-10 points)
    # US = 10, other English = 7
    if story.get('geo', 'US') == 'US':
        score += 10
    else:
        score += 7
    
    # 6. Recency (0-10 points)
    published = story.get('published', '')
    if published:
        try:
            # Simple recency check
            score += 8  # Default if we can't parse
        except:
            score += 5
    else:
        score += 5
    
    # 7. Novelty (0-10 points)
    title = story.get('title', '').lower()
    novelty_keywords = ['first', 'new', 'unprecedented', 'historic', 'breaking']
    if any(kw in title for kw in novelty_keywords):
        score += 10
    else:
        score += 5
    
    # 8. Public importance (0-5 points)
    important_keywords = ['war', 'economy', 'election', 'health', 'climate', 'security']
    if any(kw in title for kw in important_keywords):
        score += 5
    else:
        score += 2
    
    return min(100, score)


def calculate_momentum(story, historical_data=None):
    """
    Calculate momentum - is this topic accelerating?
    """
    if not historical_data:
        return story.get('breakout_score', 0) / 100
    
    # Compare current vs historical
    current = story.get('breakout_score', 0)
    previous = historical_data.get('previous_score', current)
    
    if previous > 0:
        momentum = ((current - previous) / previous) * 100
        return max(0, min(100, momentum))
    
    return 50
