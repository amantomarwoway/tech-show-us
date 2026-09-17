"""
src/collectors/reddit_collector.py - Old Reddit JSON (no API key)
Browser-like headers to avoid 403
"""

import requests
import random
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Multiple realistic browser user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0',
]

# Subreddits for real trending
SUBREDDITS = ['all', 'popular', 'nextfuckinglevel', 'interestingasfuck', 'Damnthatsinteresting']


def collect_reddit_trends():
    """Collect trending posts from Reddit using old.reddit.com JSON"""
    stories = []
    
    for subreddit in SUBREDDITS:
        try:
            # Use old.reddit.com JSON endpoint
            url = f"https://old.reddit.com/r/{subreddit}/hot.json?limit=25&raw_json=1"
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': f'https://old.reddit.com/r/{subreddit}/',
                'X-Requested-With': 'XMLHttpRequest',
                'DNT': '1',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(2.5, 5.0))
            
            resp = requests.get(url, headers=headers, timeout=25)
            
            if resp.status_code == 403:
                logger.warning(f"r/{subreddit}: 403 Forbidden (IP blocked)")
                continue
            
            if resp.status_code == 429:
                logger.warning(f"r/{subreddit}: 429 Rate limited - waiting 15s")
                time.sleep(15)
                continue
            
            if resp.status_code != 200:
                logger.warning(f"r/{subreddit}: HTTP {resp.status_code}")
                continue
            
            try:
                data = resp.json()
            except:
                logger.warning(f"r/{subreddit}: Invalid JSON")
                continue
            
            posts = data.get('data', {}).get('children', [])
            logger.info(f"r/{subreddit}: {len(posts)} posts fetched")
            
            added = 0
            for post in posts:
                post_data = post.get('data', {})
                
                title = post_data.get('title', '').strip()
                score = post_data.get('score', 0)
                num_comments = post_data.get('num_comments', 0)
                over_18 = post_data.get('over_18', False)
                stickied = post_data.get('stickied', False)
                is_video = post_data.get('is_video', False)
                domain = post_data.get('domain', '')
                post_hint = post_data.get('post_hint', '')
                
                # Filters
                if len(title) < 20:
                    continue
                if score < 500:  # Real trending only
                    continue
                if over_18:  # Skip NSFW
                    continue
                if stickied:  # Skip pinned announcements
                    continue
                if not title[0].isalpha():  # Skip non-text titles
                    continue
                if domain in ['i.redd.it', 'v.redd.it', 'imgur.com'] and not title:
                    continue
                
                # Calculate trending score
                trending_score = score + (num_comments * 2)
                breakout_score = min(6500, 3000 + trending_score // 10)
                
                stories.append({
                    "title": title,
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "source": "reddit_rising_breakout",
                    "source_tier": 2,
                    "breakout_score": breakout_score,
                    "is_breakout": score > 2000,
                    "search_volume": min(95, 50 + score // 200),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit",
                    "reddit_score": score,
                    "reddit_comments": num_comments,
                    "subreddit": subreddit
                })
                added += 1
            
            logger.info(f"r/{subreddit}: +{added} stories")
        
        except Exception as e:
            logger.warning(f"r/{subreddit} failed: {str(e)[:100]}")
            continue
    
    logger.info(f"Reddit total: {len(stories)} stories")
    return stories


# ============================================================
# LEGACY COMPATIBILITY
# ============================================================

def collect_reddit_trends_legacy():
    """Same as collect_reddit_trends - kept for compatibility"""
    return collect_reddit_trends()
