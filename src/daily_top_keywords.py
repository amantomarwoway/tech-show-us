"""
daily_top_keywords.py - DYNAMIC TOP 100 + MARKET HUNGERNESS + VALIDATION FACTORY BOOST
Location: src/daily_top_keywords.py
Edits: Market hungerness + secret leak boost + retention searchable - old preserved
"""
import feedparser, requests, re, json, random
from datetime import datetime
from pathlib import Path

CACHE_PATH = Path("data/daily_top_100.json")
CACHE_PATH.parent.mkdir(exist_ok=True)

BANNED_NICHES_DAILY = ["ipl","bcci","cricket","bollywood","bhojpuri","tamil movie","recipe","horoscope","lottery"]

# NEW: Market hungerness + validation factory boost keywords
HUNGRY_BOOST_KEYWORDS = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","just leaked","secret leak"]
BOLD_CLAIM_BOOST = ["changes everything","you won't believe","shocked","huge","massive"]

def fetch_google_trends_usa_top_30():
    url = "https://trends.google.com/trending/rss?geo=US"
    try:
        feed = feedparser.parse(url)
        topics = []
        for i, entry in enumerate(feed.entries[:30]):
            q = entry.title.strip()
            if any(b in q.lower() for b in BANNED_NICHES_DAILY):
                continue
            if len(q) >= 3:
                # NEW: Hungry boost scoring
                score_boost = 0
                q_low = q.lower()
                if any(h in q_low for h in HUNGRY_BOOST_KEYWORDS):
                    score_boost = -5  # rank up (lower rank number = better)
                topics.append({"keyword": q.lower(), "rank": i+1 + score_boost, "source": "google_trends", "hungry": any(h in q_low for h in HUNGRY_BOOST_KEYWORDS)})
        # Sort by boosted rank
        topics = sorted(topics, key=lambda x: x["rank"])
        # Re-rank 1..30
        for idx, t in enumerate(topics):
            t["rank"] = idx+1
        return topics
    except Exception as e:
        print(f"[DAILY TOP] Trends fail {e}")
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
            # Anti-bot random UA
            ua = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            ])
            r = requests.get("https://suggestqueries.google.com/complete/search",
                params={"client": "youtube", "ds": "yt", "q": kw, "hl": "en", "gl": "US"},
                timeout=3, headers={"User-Agent": ua})
            matches = re.findall(r'"([^"]+)"', r.text)
            suggestions = [m.lower() for m in matches[1:] if len(m) > 4][:4] # 3 se 4 kiya for retention
            for s in suggestions:
                if s not in seen and len(expanded) < 100:
                    if any(b in s for b in BANNED_NICHES_DAILY):
                        continue
                    # NEW: Prioritize hungry keywords in expansion
                    is_hungry = any(h in s for h in HUNGRY_BOOST_KEYWORDS)
                    # Add with hungry flag
                    expanded.append({"keyword": s, "rank": len(expanded)+1, "source": "youtube_suggest", "parent": kw, "hungry": is_hungry})
                    seen.add(s)
        except:
            pass
        if len(expanded) >= 100:
            break
    
    # NEW: Re-sort to bring hungry keywords higher
    # Separate hungry and normal, then interleave with hungry priority
    hungry = [x for x in expanded if x.get("hungry")]
    normal = [x for x in expanded if not x.get("hungry")]
    # Boosted list: hungry first 30% ranks
    boosted = []
    h_idx=0
    n_idx=0
    for i in range(100):
        if i<30 and h_idx < len(hungry): # first 30 ranks hungry priority
            boosted.append(hungry[h_idx])
            h_idx+=1
        elif n_idx < len(normal):
            boosted.append(normal[n_idx])
            n_idx+=1
        elif h_idx < len(hungry):
            boosted.append(hungry[h_idx])
            h_idx+=1
        if len(boosted)>=100:
            break
    # Re-assign ranks
    for idx, item in enumerate(boosted[:100]):
        item["rank"] = idx+1
    return boosted[:100]

def get_daily_top_100(force_refresh=False):
    if not force_refresh and CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            cached_date = data.get("date")
            if cached_date == datetime.now().strftime("%Y-%m-%d") and len(data.get("keywords", [])) >= 50:
                # Check if hungry boost exists, if not force refresh for new logic
                kws = data["keywords"]
                if any("hungry" in k for k in kws[:5]):
                    return kws
                else:
                    print("[DAILY TOP] Cache old logic, refreshing with hungry boost")
        except:
            pass
    base = fetch_google_trends_usa_top_30()
    top_100 = expand_to_100_with_youtube_suggestions(base)
    try:
        CACHE_PATH.write_text(json.dumps({"date": datetime.now().strftime("%Y-%m-%d"),"keywords": top_100, "version": "retention_hungry_v1"}, indent=2))
        hungry_count = sum(1 for k in top_100 if k.get("hungry"))
        print(f"[DAILY TOP] Generated {len(top_100)} keywords, hungry {hungry_count} (leaked/secret/breaking)")
    except Exception as e:
        print(f"[DAILY TOP] Cache write fail {e}")
        pass
    return top_100

def check_usa_relevance_with_rank(query):
    query_lower = query.lower()
    if any(b in query_lower for b in BANNED_NICHES_DAILY):
        return 0, None
    
    top_100 = get_daily_top_100()
    best_rank = None
    matched_kw = None
    is_hungry_match=False
    
    for item in top_100:
        kw = item["keyword"]
        rank = item["rank"]
        if kw in query_lower or query_lower in kw:
            if best_rank is None or rank < best_rank:
                best_rank = rank
                matched_kw = kw
                is_hungry_match = item.get("hungry", False)
    
    if best_rank is None:
        # NEW: Even if not in top 100, if query has hungry keywords, give medium score for market hungerness
        if any(h in query_lower for h in HUNGRY_BOOST_KEYWORDS):
            return 78, f"hungry_kw_match_{query_lower[:20]}"
        return 0, None
    
    # Score with hungry boost
    score = max(75, 95 - (best_rank - 1) * 0.20)
    if best_rank <= 10:
        score = min(98, score + 5)
    elif best_rank <= 25:
        score = min(95, score + 2)
    
    # Hungry boost +5
    if is_hungry_match:
        score = min(98, score + 5)
        print(f"[DAILY TOP] Hungry match +5: {query_lower[:40]} matched {matched_kw} rank {best_rank}")
    
    return int(score), matched_kw

def get_hungry_keywords_only():
    """NEW: Get only hungry keywords for market hungerness"""
    top_100 = get_daily_top_100()
    hungry = [k for k in top_100 if k.get("hungry")]
    return hungry

def is_market_hungry(query: str) -> bool:
    """NEW: Market hungerness check"""
    q = query.lower()
    return any(h in q for h in HUNGRY_BOOST_KEYWORDS)
