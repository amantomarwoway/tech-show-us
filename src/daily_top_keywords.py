"""
daily_top_keywords.py - Dynamic Top 100 USA Searchable Keywords
Roz Google Trends USA + YouTube se rank-wise nikalta hai
Fixed list nahi hai - daily alag rank
"""

import feedparser
import requests
import re
import json
from datetime import datetime
from pathlib import Path

CACHE_PATH = Path("data/daily_top_100.json")
CACHE_PATH.parent.mkdir(exist_ok=True)

# --- ADD-ON C+K ---
BANNED_NICHES_DAILY = ["ipl","bcci","cricket","bollywood","bhojpuri","tamil movie","recipe","horoscope","lottery"]
# --- END ---

def fetch_google_trends_usa_top_30():
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        feed = feedparser.parse(url)
        topics = []
        for i, entry in enumerate(feed.entries[:30]):
            q = entry.title.strip()
            # --- ADD-ON C+K - BANNED FILTER ---
            if any(b in q.lower() for b in BANNED_NICHES_DAILY):
                continue
            # --- END ---
            if len(q) >= 3:
                topics.append({"keyword": q.lower(), "rank": i+1, "source": "google_trends"})
        return topics
    except:
        return []

def expand_to_100_with_youtube_suggestions(base_keywords):
    expanded = []
    seen = set()
    for item in base_keywords:
        kw = item["keyword"]
        if kw not in seen:
            expanded.append(item)
            seen.add(kw)
        try:
            r = requests.get("https://suggestqueries.google.com/complete/search",
                params={"client": "youtube", "ds": "yt", "q": kw, "hl": "en", "gl": "US"},
                timeout=3, headers={"User-Agent": "Mozilla/5.0"})
            matches = re.findall(r'"([^"]+)"', r.text)
            suggestions = [m.lower() for m in matches[1:] if len(m) > 4][:3]
            for s in suggestions:
                if s not in seen and len(expanded) < 100:
                    # --- ADD-ON C+K ---
                    if any(b in s for b in BANNED_NICHES_DAILY):
                        continue
                    # --- END ---
                    expanded.append({"keyword": s, "rank": len(expanded)+1, "source": "youtube_suggest", "parent": kw})
                    seen.add(s)
        except:
            pass
        if len(expanded) >= 100:
            break
    return expanded[:100]

def get_daily_top_100(force_refresh=False):
    if not force_refresh and CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            cached_date = data.get("date")
            if cached_date == datetime.now().strftime("%Y-%m-%d") and len(data.get("keywords", [])) >= 50:
                return data["keywords"]
        except:
            pass
    base = fetch_google_trends_usa_top_30()
    top_100 = expand_to_100_with_youtube_suggestions(base)
    try:
        CACHE_PATH.write_text(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),"keywords": top_100}, indent=2))
    except:
        pass
    return top_100

def check_usa_relevance_with_rank(query):
    query_lower = query.lower()
    # --- ADD-ON C+K - INSTANT BANNED REJECT ---
    if any(b in query_lower for b in BANNED_NICHES_DAILY):
        return 0, None
    # --- END ---
    top_100 = get_daily_top_100()
    best_rank = None
    matched_kw = None
    for item in top_100:
        kw = item["keyword"]
        rank = item["rank"]
        if kw in query_lower or query_lower in kw:
            if best_rank is None or rank < best_rank:
                best_rank = rank
                matched_kw = kw
    if best_rank is None:
        return 0, None
    # C+K - Threshold 75 strict
    score = max(75, 95 - (best_rank - 1) * 0.20)
    if best_rank <= 10:
        score = min(98, score + 5)
    elif best_rank <= 25:
        score = min(95, score + 2)
    return int(score), matched_kw
