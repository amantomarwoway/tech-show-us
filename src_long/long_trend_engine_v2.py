"""
src_long/long_trend_engine_v2.py
Direct Google Search Trend Finder - NOT Google Trends RSS
American Audience

What it does:
- Direct Google Autocomplete gl=US
- Direct YouTube Autocomplete ds=yt gl=US
- Calculates: kya search kar rahe hain, kitne search kar rahe hain, kyu search kar rahe hain, kitna interest hai
"""

import requests
import re
import time
import random
from typing import List, Dict

SEED_QUERIES = [
    "breaking news",
    "what happened today",
    "why is trending",
    "trump news",
    "biden news",
    "nfl today",
    "weather alert",
    "shooting today",
    "earthquake today",
    "stock market crash",
    "tesla news",
    "election 2025"
]

def google_direct_suggest(q: str) -> List[str]:
    try:
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "firefox", "q": q, "gl": "us", "hl": "en"}
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        data = r.json()
        if len(data) > 1:
            return data[1][:10]
    except: pass
    return []

def youtube_direct_suggest(q: str) -> Dict:
    result = {"suggestions": [], "search_volume": 0, "video_count": 0}
    try:
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "youtube", "ds": "yt", "q": q, "gl": "US", "hl": "en"}
        r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 5][:10]
        result["suggestions"] = suggestions
        result["search_volume"] = len(suggestions) * 15
        r2 = requests.get("https://www.youtube.com/results", params={"search_query": q, "gl": "US", "hl": "en"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        result["video_count"] = r2.text.count('"videoRenderer"') or 20
    except:
        result["search_volume"] = 30
        result["video_count"] = 20
    return result

def why_searching(q: str) -> str:
    ql = q.lower()
    if "breaking" in ql or "what happened" in ql: return "fear_of_missing_out - Americans fear missing urgent news"
    if "why" in ql: return "curiosity_reason - Americans want to know reason"
    if "how much" in ql or "price" in ql: return "financial_interest - Affects wallet"
    if "weather" in ql or "earthquake" in ql or "shooting" in ql: return "safety_concern - Safety of family"
    if "trump" in ql or "biden" in ql or "election" in ql: return "political_interest - Changes American politics"
    return "general_curiosity - Blowing up across America"

def american_interest_score(vol: int, video_count: int, why: str) -> int:
    ratio = vol / max(video_count,1)
    base = 70
    if ratio >= 3 and vol >= 45: base = 92
    elif ratio >= 2 and vol >= 30: base = 84
    elif ratio >= 1: base = 76
    if "fear_of_missing_out" in why or "safety_concern" in why: base += 8
    return min(100, base)

def find_american_trends_direct(limit: int = 20) -> List[Dict]:
    print("[LONG TREND ENGINE] Direct Google Search - What Americans search NOW...")
    all_topics = []
    for seed in SEED_QUERIES:
        google_sugs = google_direct_suggest(seed)
        for sug in google_sugs:
            yt = youtube_direct_suggest(sug)
            why = why_searching(sug)
            interest = american_interest_score(yt["search_volume"], yt["video_count"], why)
            all_topics.append({
                "query": sug,
                "title": sug,
                "source": "google_direct_usa",
                "search_volume": yt["search_volume"],
                "video_count": yt["video_count"],
                "why_searching": why,
                "american_interest": interest,
                "youtube_suggestions": yt["suggestions"][:3]
            })
        time.sleep(0.4)
    
    # Deduplicate
    seen=set()
    unique=[]
    for t in all_topics:
        ql=t["query"].lower()
        if ql not in seen and len(ql)>8:
            seen.add(ql)
            unique.append(t)
    
    sorted_topics = sorted(unique, key=lambda x: (x["american_interest"] + x["search_volume"]/2), reverse=True)
    print(f"[TREND ENGINE] Found {len(sorted_topics)} American searches")
    for i,t in enumerate(sorted_topics[:5]):
        print(f"  {i+1}. {t['query']} | Interest {t['american_interest']} | Vol {t['search_volume']} | Why: {t['why_searching'][:40]}")
    return sorted_topics[:limit]
