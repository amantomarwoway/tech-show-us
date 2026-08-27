import feedparser, time

def fetch_all_news():
    all_news = []
    feed_url = "https://trends.google.com/trending/rss?geo=US"
    try:
        print(f"Fetching PURE Google Trends USA (30 topics): {feed_url}")
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print("ERROR: Google Trends returned 0 entries")
            return []
        for entry in feed.entries[:30]:
            q = entry.title.strip()
            if len(q) < 3:
                continue
            all_news.append({"title": q, "url": entry.link, "source": "google_trends_usa", "published": entry.get("published_parsed", time.gmtime()), "summary": q, "reliability": 0.95, "query": q})
        print(f"SUCCESS: Got {len(all_news)} PURE Google Trends USA topics (30)")
    except Exception as e:
        print(f"Google Trends failed: {e}")
        return []
    return all_news

def fetch_news(limit_per_feed=15, max_total=60):
    return fetch_all_news()
