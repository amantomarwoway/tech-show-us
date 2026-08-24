import feedparser, time
from datetime import datetime, timezone
import config

# NEW - Google Trends USA
try:
    from pytrends.request import TrendReq
    HAS_TRENDS = True
except ImportError:
    HAS_TRENDS = False

def fetch_all_news():
    all_news = []

    # --- 1. GOOGLE TRENDS USA (PRIORITY - SEARCHABLE TOPICS) ---
    if HAS_TRENDS:
        try:
            print("Fetching Google Trends USA...")
            pytrends = TrendReq(hl='en-US', tz=240, timeout=(10, 25))
            # pn = united_states = USA only
            df = pytrends.trending_searches(pn='united_states')
            for i, row in df.head(15).iterrows():
                q = str(row[0]).strip()
                if len(q) < 4:
                    continue
                # Skip boring
                if any(b in q.lower() for b in ["obituary", "dies", "horoscope"]):
                    continue
                all_news.append({
                    "title": q,
                    "url": f"https://trends.google.com/trends/explore?geo=US&q={q}",
                    "source": "google_trends_usa",
                    "published": time.gmtime(),
                    "summary": q,
                    "reliability": 0.95  # Highest for trending
                })
            print(f"Got {len(all_news)} from Google Trends USA")
        except Exception as e:
            print(f"Google Trends failed: {e} -> using RSS")
    
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
