"""
src/intelligence/audience_activity.py - Detect if audience is active NOW
"""

import time
import random
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def is_audience_active(story):
    """
    Check if topic's audience is active RIGHT NOW
    
    Returns:
        (is_active: bool, activity_score: 0-100, reason: str)
    """
    title = story.get('title', '')
    source = story.get('source', '')
    
    logger.info(f"🔍 Checking audience activity for: {title[:60]}")
    
    signals = []
    
    # ============================================================
    # SIGNAL 1: Google Trends Last Hour
    # ============================================================
    trends_score = check_google_trends_spike(title)
    signals.append(('trends', trends_score))
    logger.info(f"   📊 Google Trends spike: {trends_score}/100")
    
    # ============================================================
    # SIGNAL 2: Reddit Post Freshness
    # ============================================================
    reddit_score = check_reddit_freshness(story)
    signals.append(('reddit', reddit_score))
    logger.info(f"   🔥 Reddit freshness: {reddit_score}/100")
    
    # ============================================================
    # SIGNAL 3: News Freshness
    # ============================================================
    news_score = check_news_freshness(story)
    signals.append(('news', news_score))
    logger.info(f"   📰 News freshness: {news_score}/100")
    
    # ============================================================
    # AGGREGATE
    # ============================================================
    
    # Weights: trends 50%, reddit 30%, news 20%
    weighted_score = (
        trends_score * 0.50 +
        reddit_score * 0.30 +
        news_score * 0.20
    )
    
    # Count active signals (score >= 50)
    active_signals = sum(1 for _, score in signals if score >= 50)
    
    logger.info(f"   🎯 Weighted activity: {weighted_score:.1f}/100 ({active_signals}/3 signals active)")
    
    # Rule: at least 2 signals active OR weighted score >= 60
    if active_signals >= 2 or weighted_score >= 60:
        return True, weighted_score, f"Active ({active_signals}/3 signals)"
    else:
        return False, weighted_score, f"Low activity ({active_signals}/3 signals)"


def check_google_trends_spike(title):
    """
    Check Google Trends interest over last 1 hour
    Returns: 0-100 activity score
    """
    try:
        from pytrends.request import TrendReq
        
        # Extract 2-3 keywords for query
        words = [w for w in title.split() if len(w) > 4][:3]
        if not words:
            return 30  # Neutral
        
        query = " ".join(words)
        
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
        except TypeError:
            pytrends = TrendReq(hl='en-US', tz=360)
        
        pytrends.build_payload([query], timeframe='now 1-H', geo='US')
        time.sleep(1)
        
        # Get interest over time
        data = pytrends.interest_over_time()
        
        if data.empty or query not in data.columns:
            return 30
        
        # Get last value
        values = data[query].tolist()
        
        if not values:
            return 30
        
        current = values[-1]
        
        # Scoring:
        # 80+ = very active
        # 50-79 = active
        # 20-49 = moderate
        # 0-19 = inactive
        
        if current >= 80:
            return 100
        elif current >= 50:
            return 80
        elif current >= 20:
            return 50
        elif current >= 5:
            return 30
        else:
            return 10
    
    except Exception as e:
        logger.warning(f"   Trends check failed: {str(e)[:80]}")
        return 40  # Neutral if fails


def check_reddit_freshness(story):
    """
    Check if Reddit source is recent (posted in last 2 hours)
    Returns: 0-100 activity score
    """
    source = story.get('source', '')
    
    if 'reddit' not in source.lower():
        return 40  # Not from reddit, neutral
    
    # Check if we have reddit timestamp info
    reddit_score = story.get('reddit_score', 0)
    reddit_comments = story.get('reddit_comments', 0)
    
    if reddit_score == 0:
        return 40
    
    # If we have high score, assume recent
    # Reddit RSS doesn't give timestamp, so we estimate
    
    if reddit_score >= 5000:
        return 100
    elif reddit_score >= 2000:
        return 80
    elif reddit_score >= 1000:
        return 60
    else:
        return 30


def check_news_freshness(story):
    """
    Check if news source is recent
    Returns: 0-100 activity score
    """
    source = story.get('source', '')
    url = story.get('url', '')
    
    # Check if from Reddit
    if 'reddit' in source.lower():
        return 40
    
    # Check if from Google News Trending (always fresh)
    if 'trending' in source.lower() or 'breakout' in source.lower():
        return 80
    
    # Check if from RSS (varies)
    # For now, give neutral
    return 50


def get_best_upload_time(story):
    """
    Get recommended upload time based on topic
    Returns: (best_hour_utc, reason)
    """
    title = story.get('title', '').lower()
    
    # Detect topic region
    if any(w in title for w in ['trump', 'biden', 'congress', 'white house', 'usa', 'america']):
        return 23, "US politics - peak US evening (6 PM EST)"
    elif any(w in title for w in ['taylor swift', 'beyonce', 'netflix', 'movie']):
        return 2, "Entertainment - peak US late evening (9 PM EST)"
    elif any(w in title for w in ['sport', 'nba', 'nfl', 'football', 'soccer']):
        return 23, "Sports - peak US evening (6 PM EST)"
    elif any(w in title for w in ['ai', 'tech', 'apple', 'google']):
        return 19, "Tech - peak US afternoon (2 PM EST)"
    else:
        return 23, "Default - peak US evening (6 PM EST)"
