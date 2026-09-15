"""
src/collectors/trends_collector.py - Google Trends (FIXED for urllib3 2.x)
"""

import random
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_trends():
    """Collect trending topics from Google Trends"""
    stories = []
    
    try:
        from pytrends.request import TrendReq
        
        # Safe init
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10, retries=1, backoff_factor=0.5)
        except TypeError:
            try:
                pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
            except TypeError:
                pytrends = TrendReq(hl='en-US', tz=360)
        
        # FIXED: Use related_queries instead of trending_searches
        # (trending_searches is broken in pytrends 4.9.2 with urllib3 2.x)
        
        for keyword in ["breaking news", "world news", "trump"]:
            try:
                pytrends.build_payload([keyword], timeframe='now 1-H', geo='US')
                time.sleep(1)
                
                related = pytrends.related_queries()
                
                if keyword in related:
                    rising = related[keyword].get('rising')
                    if rising is not None and not rising.empty:
                        for _, row in rising.head(5).iterrows():
                            query = str(row.get('query', ''))
                            value = row.get('value', 0)
                            
                            if len(query) < 3:
                                continue
                            
                            stories.append({
                                "title": f"{query} - Trending Now",
                                "url": f"https://trends.google.com/trends/explore?q={query}&geo=US",
                                "source": "google_trends_trending_now",
                                "source_tier": 2,
                                "breakout_score": 5000 if value == 'Breakout' else min(6500, 4000 + int(value) * 20),
                                "is_breakout": True,
                                "search_volume": min(100, 70 + int(value) // 20) if value != 'Breakout' else 95,
                                "seo_youtube_title": query[:58],
                                "collected_from": "trends_related"
                            })
                
                logger.info(f"Trends '{keyword}': {len(stories)} total")
            
            except Exception as e:
                logger.warning(f"Trends query '{keyword}' failed: {str(e)[:80]}")
                continue
        
    except Exception as e:
        logger.error(f"Trends collector failed: {e}")
    
    return stories


def get_trending_searches(geo="US"):
    """Fallback: get trending searches (may fail on newer urllib3)"""
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
        trending = pytrends.trending_searches(pn='united_states')
        
        if trending is not None and not trending.empty:
            return [str(row[0]) for _, row in trending.head(20).iterrows()]
    
    except Exception as e:
        logger.debug(f"Trending searches unavailable: {e}")
    
    return []
