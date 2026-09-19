"""
src/collectors/reddit_collector.py - Reddit RSS with SPAM filter
"""

import feedparser
import random
import time
import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

FEEDS = [
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

REJECT = ['weather', 'temperature', 'forecast', 'muggy', 'recipe', 'cooking',
          'diet', 'workout', 'daily thread', 'weekly thread', 'discussion',
          'county', 'municipal', 'local', 'neighborhood', 'megathread']

SPAM_KW = ['18+', 'adult', 'xxx', 'porn', 'nude', 'sex', 'casino', 'betting',
           'lottery', 'loan', 'free download', 'torrent', 'crack']


def collect_reddit_trends():
    stories = []
    for feed_url in FEEDS:
        try:
            time.sleep(random.uniform(5, 8))
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                logger.warning(f"No entries: {feed_url[:60]}")
                continue
            
            try:
                sub = feed_url.split('/r/')[1].split('/')[0]
            except:
                sub = "reddit"
            
            logger.info(f"r/{sub}: {len(feed.entries)} entries")
            added = 0
            for entry in feed.entries[:25]:
                title = entry.get('title', '').strip()
                url = entry.get('link', '')
                if len(title) < 25 or not title[0].isalpha():
                    continue
                tl = title.lower()
                if any(k in tl for k in SPAM_KW):
                    continue
                if re.search(r'\[.*?\]', title):
                    continue
                if any(r in tl for r in REJECT):
                    continue
                stories.append({
                    "title": title, "url": url,
                    "source": "reddit_rss_trending", "source_tier": 1,
                    "breakout_score": random.randint(6000, 7000),
                    "is_breakout": True,
                    "search_volume": random.randint(80, 100),
                    "seo_youtube_title": title[:58],
                    "collected_from": "reddit",
                    "subreddit": sub
                })
                added += 1
            logger.info(f"r/{sub}: +{added} stories")
        except Exception as e:
            logger.warning(f"Feed failed: {str(e)[:80]}")
            continue
    logger.info(f"Reddit total: {len(stories)}")
    return stories
