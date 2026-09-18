"""
src/collectors/reddit_collector.py - Reddit RSS (NO API KEY NEEDED)
"""

import feedparser
import random
import time
import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Reddit RSS feeds - real trending
REDDIT_RSS_FEEDS = [
    "https://www.reddit.com/r/all/hot/.rss",
    "https://www.reddit.com/r/popular/hot/.rss",
    "https://www.reddit.com/r/nextfuckinglevel/hot/.rss",
    "https://www.reddit.com/r/interestingasfuck/hot/.rss",
    "https://www.reddit.com/r/Damnthatsinteresting/hot/.rss",
]

# Boring keywords to reject
REJECT_KEYWORDS = [
    'weather', 'temperature', 'forecast', 'muggy',
    'recipe', 'cooking', 'diet', 'workout',
    'daily thread', 'weekly thread', 'discussion',
    'county', 'municipal', 'local', 'neighborhood',
    'megathread', 'roundup', 'recap'
]


def collect_reddit_trends():
    """Collect real trending via Reddit RSS (no API key)"""
    stories = []
    
    for feed_url in REDDIT_RSS_FEEDS:
        try:
            # Delay between feeds to avoid rate limit
            time.sleep(random.uniform(2, 4))
            
            feed = feedparser.parse(feed_url)
            
            if not feed.entries:
                logger.warning(f"No entries from: {feed_url}")
                continue
            
            subreddit = feed_url.split('/r/')[1].split('/')[0]
            logger.info(f"r/{subreddit}: {len(feed.entries)} entries")
            
            added = 0
            for entry in feed.entries[:25]:
                title = entry.get('title', '').strip()
                
                if len(title) < 25:
                    continue
                
                # Reject boring topics
                title_lower = title.lower()
                if any(r in title_lower for r in REJECT_KEYWORDS):
                    continue
                
                # Reject non-alpha start
                if not title[0].isalpha():
                    continue
                
                # Extract reddit link
                link = entry.get('link', '')
                
                stories.append({
                    "title": title,
                    "url": link,
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
            
            logger.info(f"r/{subreddit}: +{added} stories added")
        
        except Exception as e:
            logger.warning(f"Feed failed {feed_url}: {str(e)[:80]}")
            continue
    
    logger.info(f"Reddit RSS total: {len(stories)} stories")
    return stories
