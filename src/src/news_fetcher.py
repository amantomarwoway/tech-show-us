import feedparser, time
from datetime import datetime, timezone
import config

def fetch_all_news():
    all_news = []
    for source, url in config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                all_news.append({
                    "title": entry.title,
                    "url": entry.link,
                    "source": source,
                    "published": entry.get("published_parsed", time.gmtime()),
                    "summary": entry.get("summary","")[:500],
                    "reliability": config.SOURCE_RELIABILITY.get(source, 0.7)
                })
        except Exception as e:
            print(f"RSS fail {source}: {e}")
    return all_news
