"""
news_fetcher.py - Wire + Google News fetcher (45 min filter) - EDITED MINIMAL
Bhai ko har baar breakout news hi chahiye - Wire Service se
"""
import time, re, feedparser
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

def is_us_topic(text: str) -> bool:
    if not text: return False
    low = text.lower()
    blocked = ['germany', 'merz', 'canada']
    for b in blocked:
        if b in low and not any(k in low for k in ['trump', 'white house', 'usa']):
            return False
    return True

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

REUTERS_FEEDS = [
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.reuters.com/reuters/USNews",
    "http://feeds.reuters.com/reuters/politicsNews"
]

GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+politics+OR+white+house+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
]

MAINSTREAM_BLOCK = [
    "cnn.com", "nytimes.com", "washingtonpost.com", "foxnews.com",
    "msnbc.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com",
    "apnews.com", "bbc.com", "theguardian.com"
]

US_SEARCH_KEYWORDS = [
    "trump", "biden", "white house", "supreme court", "executive order",
    "congress", "senate", "pentagon", "fbi", "doj", "tariff", "ban",
    "election", "border", "immigration", "breaking", "leaked", "shocking"
]

def is_mainstream_blocked(url: str) -> bool:
    if not url: return False
    low = url.lower()
    return any(d in low for d in MAINSTREAM_BLOCK)

def is_within_45min(entry) -> bool:
    try:
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = datetime.fromtimestamp(time.mktime(entry.updated_parsed), tz=timezone.utc)
        else:
            return True
        now = datetime.now(timezone.utc)
        return (now - published) <= timedelta(minutes=45)
    except:
        return True

def score_search_potential(title: str) -> int:
    if not title: return 0
    low = title.lower()
    score = 0
    for kw in US_SEARCH_KEYWORDS:
        if kw in low:
            score += 10
    for qw in ["how", "what", "why", "update", "explained"]:
        if qw in low:
            score += 15
    return score

def fetch_feed(url: str):
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:10]:
            if not is_within_45min(entry):
                continue
            title = clean_id(getattr(entry, 'title', ''))
            if len(title) < 10: continue
            link = getattr(entry, 'link', '')
            if is_mainstream_blocked(link): continue
            if not is_us_topic(title): continue
            score = score_search_potential(title)
            if score < 10: continue
            results.append({
                "title": title, "query": title, "url": link,
                "source": "reuters_wire" if "reuters" in url else "google_news_wire",
                "published": time.gmtime(), "summary": title,
                "is_breakout": True, "breakout_score": 5000 + score,
                "search_volume": min(95, 60 + score),
                "search_potential_score": score,
                "bot_friendly": True
            })
        return results
    except:
        return []

def fetch_all_news():
    all_news = []
    all_feeds = REUTERS_FEEDS + GOOGLE_NEWS_FEEDS
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(fetch_feed, url): url for url in all_feeds}
        for future in as_completed(futures):
            try:
                data = future.result()
                if data: all_news.extend(data)
            except: continue
    seen = set()
    deduped = []
    for item in all_news:
        key = item['title'].lower().strip()
        if key not in seen and len(key) > 5:
            seen.add(key)
            deduped.append(item)
    deduped.sort(key=lambda x: x.get('search_potential_score', 0), reverse=True)
    us_filtered = [n for n in deduped if is_us_topic(n.get("title","")+" "+n.get("query",""))]
    if us_filtered:
        deduped = us_filtered
    return deduped

def fetch_news(limit_per_feed=15, max_total=60):
    news = fetch_all_news()
    filtered = [n for n in news if n.get('is_breakout')]
    if not filtered and news:
        filtered = news[:1]
    return filtered[:max_total]
