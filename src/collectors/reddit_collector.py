"""
src/collectors/reddit_collector.py - Reddit RSS (multiple subs + delay)
"""

import feedparser
import random
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

REDDIT_RSS_FEEDS = [
    "https://www.reddit.com/r/all/hot/.rss",
    "https://www.reddit.com/r/all/top/.rss?t=day",
    "https://www.reddit.com/r/worldnews/hot/.rss",
    "https://www.reddit.com/r/news/hot/.rss",
    "https://www.reddit.com/r/entertainment/hot/.rss",
    "https://www.reddit.com/r/movies/hot/.rss",
    "https://www.reddit.com/r/sports/hot/.rss",
    "https://www.reddit.com/r/music/hot/.rss",
    "https://www.reddit.com/r/technology/hot/.rss",
]

REJECT_KEYWORDS = [
    'weather', 'temperature', 'forecast', 'muggy',
    'recipe', 'cooking', 'diet', 'workout',
    'daily thread', 'weekly thread', 'discussion',
    'county', 'municipal', 'local', 'neighborhood',
    'megathread', 'roundup', 'recap'
]


def collect_reddit_trends():
    """Collect real trending via Reddit RSS"""
    stories = []
    
    for feed_url in REDDIT_RSS_FEEDS:
        try:
            # Longer delay (Reddit RSS is rate-limited)
            time.sleep(random.uniform(5, 8))
            
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries: {feed_url[:60]}")
                continue
            
            # Extract subreddit name
            try:
                subreddit = feed_url.split('/r/')[1].split('/')[0]
            except:
                subreddit = "reddit"
            
            logger.info(f"r/{subreddit}: {len(feed.entries)} entries")
            
            added = 0
            for entry in feed.entries[:25]:
                title = entry.get('title', '').strip()
                
                if len(title) < 25:
                    continue
                
                if not title[0].isalpha():
                    continue
                
                title_lower = title.lower()
                if any(r in title_lower for r in REJECT_KEYWORDS):
                    continue
                
                stories.append({
                    "title": title,
                    "url": entry.get('link', ''),
                    "source": "reddit_rss_trending",
                    "source_tier": 1,
                    "breakout_score": random.randint(6000, 7000),
                    "is_breakout": True,
                    "search_volume": random.randint(80, 100),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit_rss",
                    "subreddit": subreddit
                })
                added += 1
            
            logger.info(f"r/{subreddit}: +{added} stories")
        
        except Exception as e:
            logger.warning(f"Feed failed: {str(e)[:80]}")
            continue
    
    logger.info(f"Reddit RSS total: {len(stories)} stories")
    return stories
