import feedparser, time

# PURE GOOGLE TRENDS USA ONLY - NO RSS FALLBACK

def fetch_all_news():
    all_news = []

    # Google Trends ka OFFICIAL feed - ye news RSS nahi, Google Trends hi hai
    # Bas format RSS hai, data 100% Google Trends USA ka hai
    feed_url = "https://trends.google.com/trending/rss?geo=US"

    try:
        print(f"Fetching PURE Google Trends USA: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            print("ERROR: Google Trends returned 0 entries")
            return []  # empty return, no fallback

        for entry in feed.entries[:20]:
            q = entry.title.strip()
            if len(q) < 3:
                continue
                
            all_news.append({
                "title": q,
                "url": entry.link,
                "source": "google_trends_usa",
                "published": entry.get("published_parsed", time.gmtime()),
                "summary": q,
                "reliability": 0.95
            })
        
        print(f"✅ SUCCESS: Got {len(all_news)} PURE Google Trends USA topics")
        for i, item in enumerate(all_news[:5]):
            print(f"{i+1}. {item['title']}")
            
    except Exception as e:
        print(f"❌ Google Trends failed: {e}")
        return []

    return all_news
