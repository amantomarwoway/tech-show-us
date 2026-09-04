import feedparser, time
from datetime import datetime, timezone

# --- ADD-ON E+I START ---
# E = 60 min live cutoff, I = No news fail -> Google News US Live fallback
import requests

def get_live_news_60min_filter(news_list):
    """Problem E - Sirf 60 min ke andar ki news pass karo"""
    fresh = []
    now = datetime.now(timezone.utc)
    for n in news_list:
        pub = n.get('published')
        try:
            if isinstance(pub, time.struct_time):
                pub_dt = datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc)
            elif isinstance(pub, (int,float)):
                pub_dt = datetime.fromtimestamp(pub, tz=timezone.utc)
            else:
                # Trends ka time nahi hota toh fresh maano
                fresh.append(n)
                continue
            age_min = (now - pub_dt).total_seconds() / 60
            if age_min <= 60: # 60 min live cutoff
                fresh.append(n)
        except:
            fresh.append(n)
    return fresh

def fetch_google_news_us_live_fallback():
    """Problem I - Agar Trends fail ho ya 0 news ho toh Google News US Live se lao"""
    fallback_news = []
    try:
        # Google News US RSS - Live
        rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        print(f"Fetching FALLBACK Google News US Live: {rss_url}")
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:15]:
            q = entry.title.strip()
            if len(q) < 3:
                continue
            fallback_news.append({
                "title": q,
                "url": entry.link,
                "source": "google_news_us_live", # Ye source verifier me allow karna hai - Problem 6
                "published": entry.get("published_parsed", time.gmtime()),
                "summary": q,
                "reliability": 0.90,
                "query": q
            })
        print(f"FALLBACK SUCCESS: Got {len(fallback_news)} Google News US Live topics")
    except Exception as e:
        print(f"Fallback Google News US Live failed: {e}")
    return fallback_news
# --- ADD-ON E+I END ---

def fetch_all_news():
    all_news = []
    feed_url = "https://trends.google.com/trending/rss?geo=US"
    try:
        print(f"Fetching PURE Google Trends USA (30 topics): {feed_url}")
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            print("ERROR: Google Trends returned 0 entries")
            # --- ADD-ON I ---
            return fetch_google_news_us_live_fallback()
            # --- END ---
        for entry in feed.entries[:30]:
            q = entry.title.strip()
            if len(q) < 3:
                continue
            all_news.append({"title": q, "url": entry.link, "source": "google_trends_usa", "published": entry.get("published_parsed", time.gmtime()), "summary": q, "reliability": 0.95, "query": q})
        print(f"SUCCESS: Got {len(all_news)} PURE Google Trends USA topics (30)")

        # --- ADD-ON E - 60 min filter (Trends ke liye bypass, par Google News ke liye strict) ---
        # Trends ke paas exact time nahi hota, isliye filter ke baad bhi list rakho
        # Ye filter asli kaam tab karega jab source google_news_us_live hoga
        # --- END ---

    except Exception as e:
        print(f"Google Trends failed: {e}")
        # --- ADD-ON I - Trends fail hone par bot fail nahi hoga, fallback chalega ---
        return fetch_google_news_us_live_fallback()
        # --- END ---

    # --- ADD-ON I - Agar list khali hai toh fallback ---
    if not all_news:
        return fetch_google_news_us_live_fallback()
    # --- END ---

    return all_news

def fetch_news(limit_per_feed=15, max_total=60):
    news = fetch_all_news()
    # --- ADD-ON E - Final 60 min live check for google_news_us_live source ---
    filtered = []
    for n in news:
        if n.get('source') == 'google_news_us_live':
            fresh = get_live_news_60min_filter([n])
            filtered.extend(fresh)
        else:
            filtered.append(n)
    # Agar 60 min filter ke baad bhi khali ho gaya toh fallback se 1-2 fresh de do taki bot fail na ho
    if not filtered:
        print("[E+I] All news filtered as old, using fallback fresh")
        return fetch_google_news_us_live_fallback()[:5]
    return filtered
