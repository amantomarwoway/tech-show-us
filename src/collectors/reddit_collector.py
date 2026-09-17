"""
src/collectors/reddit_collector.py - BROAD REDDIT TRENDING
Fetches from r/all, r/popular and topic-specific subs
"""

import requests
import random
import time
from src.utils.logger import setup_logger
from src.config import REDDIT_SUBREDDITS

logger = setup_logger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def collect_reddit_trends():
    """Collect trending posts from Reddit"""
    stories = []
    
    # Focus on r/all, r/popular, and 3-4 topic subs
    priority_subs = ['all', 'popular', 'nextfuckinglevel', 'interestingasfuck', 'viral']
    
    for subreddit in priority_subs:
        try:
            url = f"https://old.reddit.com/r/{subreddit}/hot.json?limit=15"
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            resp = requests.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 429:
                logger.warning(f"Reddit rate limited for r/{subreddit}")
                time.sleep(5)
                continue
            
            if resp.status_code != 200:
                logger.warning(f"Reddit r/{subreddit}: {resp.status_code}")
                continue
            
            data = resp.json()
            posts = data.get('data', {}).get('children', [])
            
            logger.info(f"Reddit r/{subreddit}: {len(posts)} posts")
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '').strip()
                score = post_data.get('score', 0)
                
                if len(title) < 20:
                    continue
                
                # Only high upvote posts (real trending)
                if score < 500:
                    continue
                
                # Skip NSFW
                if post_data.get('over_18', False):
                    continue
                
                # Skip non-English
                if not title[0].isalpha():
                    continue
                
                stories.append({
                    "title": title,
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit_rising_breakout",
                    "source_tier": 2,
                    "breakout_score": min(6500, 3000 + score // 10),
                    "is_breakout": score > 2000,
                    "search_volume": min(95, 50 + score // 200),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit",
                    "reddit_score": score,
                    "subreddit": subreddit
                })
            
            time.sleep(3)
        
        except Exception as e:
            logger.warning(f"Reddit r/{subreddit} failed: {str(e)[:80]}")
            continue
    
    logger.info(f"Reddit total: {len(stories)} stories")
    return stories
