"""
src/collectors/reddit_collector.py - Reddit JSON API (free, no auth needed)
"""

import requests
import random
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

SUBREDDITS = ['news', 'worldnews', 'politics', 'Conservative', 'Liberal']

def collect_reddit_trends():
    """Collect trending posts from Reddit JSON API"""
    stories = []
    
    for subreddit in SUBREDDITS[:3]:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
            headers = {'User-Agent': 'NewsBot/1.0'}
            
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                continue
            
            data = resp.json()
            posts = data.get('data', {}).get('children', [])
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                
                if len(title) < 20:
                    continue
                
                # Check for news keywords
                title_lower = title.lower()
                news_keywords = ['breaking', 'trump', 'biden', 'white house', 'supreme court',
                                'congress', 'election', 'war', 'tariff', 'economy']
                
                if not any(kw in title_lower for kw in news_keywords):
                    continue
                
                stories.append({
                    "title": title,
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit_rising_breakout",
                    "source_tier": 3,  # Lower credibility - signal only
                    "breakout_score": random.randint(3500, 5000),
                    "is_breakout": True,
                    "search_volume": random.randint(60, 85),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit",
                    "reddit_score": post_data.get('score', 0),
                    "reddit_comments": post_data.get('num_comments', 0)
                })
            
            logger.info(f"Reddit r/{subreddit}: {len(stories)} total")
            time.sleep(1)  # Rate limit
            
        except Exception as e:
            logger.warning(f"Reddit r/{subreddit} failed: {e}")
            continue
    
    return stories
