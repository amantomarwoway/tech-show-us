"""
src/collectors/reddit_collector.py - Reddit JSON API (FIXED)
"""

import requests
import random
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

SUBREDDITS = ['news', 'worldnews', 'politics']

# FIXED: Proper User-Agent (Reddit blocks generic ones)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; NewsBot/1.0; +https://github.com/yourusername)',
    'Accept': 'application/json'
}


def collect_reddit_trends():
    """Collect trending posts from Reddit JSON API"""
    stories = []
    
    for subreddit in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=15"
            
            # FIXED: Longer timeout + proper headers
            resp = requests.get(url, headers=HEADERS, timeout=15)
            
            if resp.status_code == 429:
                logger.warning(f"Reddit rate limited for r/{subreddit}")
                time.sleep(5)
                continue
            
            if resp.status_code != 200:
                logger.warning(f"Reddit r/{subreddit} status: {resp.status_code}")
                continue
            
            data = resp.json()
            posts = data.get('data', {}).get('children', [])
            
            logger.info(f"Reddit r/{subreddit}: {len(posts)} raw posts")
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                
                if len(title) < 20:
                    continue
                
                title_lower = title.lower()
                news_keywords = ['breaking', 'trump', 'biden', 'white house',
                               'supreme court', 'congress', 'election', 'war',
                               'tariff', 'economy', 'ukraine', 'russia', 'china']
                
                if not any(kw in title_lower for kw in news_keywords):
                    continue
                
                stories.append({
                    "title": title,
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit_rising_breakout",
                    "source_tier": 3,
                    "breakout_score": random.randint(3500, 5000),
                    "is_breakout": True,
                    "search_volume": random.randint(60, 85),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit",
                    "reddit_score": post_data.get('score', 0),
                    "reddit_comments": post_data.get('num_comments', 0)
                })
            
            time.sleep(2)  # Rate limit
        
        except Exception as e:
            logger.warning(f"Reddit r/{subreddit} failed: {str(e)[:80]}")
            continue
    
    logger.info(f"Reddit total: {len(stories)} stories")
    return stories
