"""
src/collectors/trends_collector.py - Google News Trending with SPAM filter
"""

import random
import time
import feedparser
import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def collect_trends():
    stories = []
    
    feeds = [
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=viral+trending&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=celebrity+news&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=breaking+now&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=entertainment+viral&hl=en-US&gl=US&ceid=US:en",
    ]
    
    REJECT = ['weather', 'temperature', 'forecast', 'muggy', 'recipe', 'cooking',
              'diet', 'opinion:', 'analysis:', 'editorial:', 'how to', 'guide to']
    
    SPAM_DOMAINS = ['uv.es', '.ru/', '.cn/', '.xyz', '.top', '.click',
                    'blogspot', 'wordpress.com', 'wixsite', 'bit.ly']
    SPAM_KW = ['18+', 'adult', 'xxx', 'porn', 'nude', 'sex', 'casino', 'betting',
               'lottery', 'loan', 'free download', 'torrent', 'crack']
    
    seen = set()
    for feed_url in feeds:
        try:
            time.sleep(random.uniform(1.5, 3.0))
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue
            logger.info(f"Trends feed: {len(feed.entries)} entries")
            
            for entry in feed.entries[:15]:
                title = entry.get('title', '').strip()
                url = entry.get('link', '')
                if len(title) < 20:
                    continue
                if any(s in url.lower() for s in SPAM_DOMAINS):
                    continue
                tl = title.lower()
                if any(k in tl for k in SPAM_KW):
                    continue
                if re.search(r'\[.*?\]', title):
                    continue
                if re.search(r'https?://|www\.|\.(es|ru|cn|xyz|top|click)', tl):
                    continue
                key = title[:40].lower()
                if key in seen:
                    continue
                seen.add(key)
                if any(r in tl for r in REJECT):
                    continue
                title = re.sub(r'\s+-\s+[A-Za-z\s]{2,40}$', '', title)
                stories.append({
                    "title": title, "url": url or feed_url,
                    "source": "google_news_trending", "source_tier": 1,
                    "breakout_score": random.randint(6000, 7000),
                    "is_breakout": True,
                    "search_volume": random.randint(85, 100),
                    "seo_youtube_title": title[:58],
                    "collected_from": "trends"
                })
        except Exception as e:
            logger.warning(f"Feed failed: {str(e)[:80]}")
            continue
    
    logger.info(f"Trends total: {len(stories)}")
    return stories
