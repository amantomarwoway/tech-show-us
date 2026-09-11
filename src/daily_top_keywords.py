"""
daily_top_keywords.py - DYNAMIC TOP 100 + WIRE + 45MIN + 7-DAY VELOCITY + YOUTUBE SEARCH SEO
Location: src/daily_top_keywords.py
UPDATED: Wire Service (Reuters + Google News Wire) 45min filter + mainstream block + search potential + 7-Day Velocity + SEO over Shorts Feed
Old preserved: banned niches, hungry boost, but now with wire first
"""
import feedparser, requests, re, json, random, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_PATH = Path("data/daily_top_100.json")
CACHE_PATH.parent.mkdir(exist_ok=True)

BANNED_NICHES_DAILY = ["ipl","bcci","cricket","bollywood","bhojpuri","tamil movie","recipe","horoscope","lottery"]

HUNGRY_BOOST_KEYWORDS = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","just leaked","secret leak"]
BOLD_CLAIM_BOOST = ["changes everything","you won't believe","shocked","huge","massive"]

REUTERS_FEEDS = [
    "http://feeds.reuters.com/reuters/topNews",
    "http://feeds.reuters.com/reuters/USNews",
]
GOOGLE_NEWS_WIRE_FEEDS = [
    "https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=US+politics+when:1h&hl=en-US&gl=US&ceid=US:en",
]
MAINSTREAM_BLOCK = ["cnn.com","nytimes.com","washingtonpost.com","foxnews.com","msnbc.com","apnews.com"]

US_SEARCH_KEYWORDS = [
    "trump","biden","white house","supreme court","executive order","congress","senate",
    "pentagon","fbi","doj","tariff","ban","election","border","immigration","breaking","leaked","shocking"
]

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_within_45min(entry) -> bool:
    try:
        import time as time_mod
        published = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published = datetime.fromtimestamp(time_mod.mktime(entry.published_parsed), tz=timezone.utc)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            published = datetime.fromtimestamp(time_mod.mktime(entry.updated_parsed), tz=timezone.utc)
        else:
            return True
        now = datetime.now(timezone.utc)
        return (now - published) <= timedelta(minutes=45)
    except:
        return True

def is_mainstream_blocked(url: str) -> bool:
    if not url: return False
    low = url.lower()
    return any(d in low for d in MAINSTREAM_BLOCK)

def score_search_potential(title: str) -> int:
    if not title: return 0
    low = title.lower()
    score = 0
    for kw in US_SEARCH_KEYWORDS:
        if kw in low:
            score += 10
    for qw in ["how","what","why","update","explained"]:
        if qw in low:
            score += 15
    if any(h in low for h in HUNGRY_BOOST_KEYWORDS):
        score += 20
    return score

def is_us_topic(text: str) -> bool:
    if not text: return False
    low = text.lower()
    blocked = ['germany','merz','canada']
    for b in blocked:
        if b in low and not any(k in low for k in ['trump','white house','usa']):
            return False
    return True

def is_7day_search_velocity(title: str) -> bool:
    low = title.lower()
    velocity_triggers = ["how","what","why","update","explained","leaked","secret","breaking","ban","order","decision","ruling"]
    return any(t in low for t in velocity_triggers) and score_search_potential(title) >= 30

def fetch_wire_feed(url: str):
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:15]:
            if not is_within_45min(entry):
                continue
            title = clean_id(getattr(entry, 'title',''))
            if len(title) < 8: continue
            link = getattr(entry, 'link','')
            if is_mainstream_blocked(link): continue
            if not is_us_topic(title): continue
            score = score_search_potential(title)
            if score < 15: continue
            if not is_7day_search_velocity(title): continue
            results.append({"title": title, "url": link, "score": score, "source": "reuters_wire" if "reuters" in url else "google_news_wire"})
        return results
    except:
        return []

def fetch_google_trends_usa_top_30():
    all_wire = []
    all_feeds = REUTERS_FEEDS + GOOGLE_NEWS_WIRE_FEEDS
    try:
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fetch_wire_feed, url): url for url in all_feeds}
            for future in as_completed(futures):
                try:
                    data = future.result()
                    if data: all_wire.extend(data)
                except: continue
    except:
        all_wire = []

    seen = set()
    deduped = []
    for item in all_wire:
        key = item['title'].lower().strip()
        if key not in seen and len(key) > 5:
            seen.add(key)
            deduped.append(item)
    deduped.sort(key=lambda x: x['score'], reverse=True)

    if not deduped:
        url = "https://trends.google.com/trending/rss?geo=US"
        try:
            feed = feedparser.parse(url)
            topics = []
            for i, entry in enumerate(feed.entries[:30]):
                q = clean_id(entry.title.strip())
                if any(b in q.lower() for b in BANNED_NICHES_DAILY):
                    continue
                if len(q) >= 3:
                    score_boost = 0
                    q_low = q.lower()
                    if any(h in q_low for h in HUNGRY_BOOST_KEYWORDS):
                        score_boost = -5
                    topics.append({"keyword": q.lower(), "rank": i+1 + score_boost, "source": "google_trends_fallback", "hungry": any(h in q_low for h in HUNGRY_BOOST_KEYWORDS), "score": score_search_potential(q)})
            topics = sorted(topics, key=lambda x: x["rank"])
            for idx, t in enumerate(topics):
                t["rank"] = idx+1
            return topics
        except Exception as e:
            print(f"[DAILY TOP] Trends fallback fail {e}")
            return []

    topics = []
    for i, item in enumerate(deduped[:30]):
        q = item['title']
        q_low = q.lower()
        topics.append({
            "keyword": q.lower(),
            "rank": i+1,
            "source": item['source'],
            "hungry": any(h in q_low for h in HUNGRY_BOOST_KEYWORDS),
            "score": item['score'],
            "is_weekly_search_trend": True,
            "confidence_score": min(95, 70 + item['score']),
            "url": item['url']
        })
    return topics

def expand_to_100_with_youtube_suggestions(base_keywords):
    expanded = []
    seen = set()
    for item in base_keywords:
        kw = item["keyword"]
        if kw not in seen:
            expanded.append(item)
            seen.add(kw)
        try:
            ua = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            ])
            r = requests.get("https://suggestqueries.google.com/complete/search",
                params={"client": "youtube", "ds": "yt", "q": kw, "hl": "en", "gl": "US"},
                timeout=3, headers={"User-Agent": ua})
            matches = re.findall(r'"([^"]+)"', r.text)
            suggestions = [m.lower() for m in matches[1:] if len(m) > 4][:4]
            for s in suggestions:
                if s not in seen and len(expanded) < 100:
                    if any(b in s for b in BANNED_NICHES_DAILY):
                        continue
                    if not is_us_topic(s):
                        continue
                    if not is_7day_search_velocity(s):
                        if score_search_potential(s) < 20:
                            continue
                    is_hungry = any(h in s for h in HUNGRY_BOOST_KEYWORDS)
                    expanded.append({
                        "keyword": s,
                        "rank": len(expanded)+1,
                        "source": "youtube_search_seo",
                        "parent": kw,
                        "hungry": is_hungry,
                        "is_weekly_search_trend": is_7day_search_velocity(s),
                        "confidence_score": min(95, 60 + score_search_potential(s)),
                        "seo_optimized": True
                    })
                    seen.add(s)
        except:
            pass
        if len(expanded) >= 100:
            break
    
    hungry = [x for x in expanded if x.get("hungry")]
    normal = [x for x in expanded if not x.get("hungry")]
    boosted = []
    h_idx=0
    n_idx=0
    for i in range(100):
        if i<30 and h_idx < len(hungry):
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
    for idx, item in enumerate(boosted[:100]):
        item["rank"] = idx+1
    return boosted[:100]

def get_daily_top_100(force_refresh=False):
    if not force_refresh and CACHE_PATH.exists():
        try:
            data = json.loads(CACHE_PATH.read_text())
            cached_date = data.get("date")
            if cached_date == datetime.now().strftime("%Y-%m-%d") and len(data.get("keywords", [])) >= 50:
                kws = data["keywords"]
                if any("hungry" in k or "is_weekly_search_trend" in k for k in kws[:5]):
                    return kws
        except:
            pass
    base = fetch_google_trends_usa_top_30()
    top_100 = expand_to_100_with_youtube_suggestions(base)
    try:
        CACHE_PATH.write_text(json.dumps({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": top_100,
            "version": "wire_45min_velocity_seo_v2",
            "engine": "reuters_wire + google_news_wire 45min + 7day velocity + youtube search SEO",
            "asset": "duckduckgo 1.0s + yt-dlp 1.8s"
        }, indent=2))
        hungry_count = sum(1 for k in top_100 if k.get("hungry"))
        velocity_count = sum(1 for k in top_100 if k.get("is_weekly_search_trend"))
        print(f"[DAILY TOP] Generated {len(top_100)} keywords, hungry {hungry_count}, velocity {velocity_count} (wire 45min + SEO)")
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
    is_velocity_match=False
    
    for item in top_100:
        kw = item["keyword"]
        rank = item["rank"]
        if kw in query_lower or query_lower in kw:
            if best_rank is None or rank < best_rank:
                best_rank = rank
                matched_kw = kw
                is_hungry_match = item.get("hungry", False)
                is_velocity_match = item.get("is_weekly_search_trend", False)
    
    if best_rank is None:
        if any(h in query_lower for h in HUNGRY_BOOST_KEYWORDS):
            if is_7day_search_velocity(query_lower):
                return 85, f"velocity_hungry_{query_lower[:20]}"
            return 78, f"hungry_kw_match_{query_lower[:20]}"
        if is_7day_search_velocity(query_lower):
            return 80, f"velocity_match_{query_lower[:20]}"
        return 0, None
    
    score = max(75, 95 - (best_rank - 1) * 0.20)
    if best_rank <= 10:
        score = min(98, score + 5)
    elif best_rank <= 25:
        score = min(95, score + 2)
    
    if is_hungry_match:
        score = min(98, score + 5)
    if is_velocity_match:
        score = min(98, score + 7)
        print(f"[DAILY TOP] Velocity + SEO match +7: {query_lower[:40]} matched {matched_kw} rank {best_rank}")
    elif is_hungry_match:
        print(f"[DAILY TOP] Hungry match +5: {query_lower[:40]} matched {matched_kw} rank {best_rank}")
    
    return int(score), matched_kw

def get_hungry_keywords_only():
    top_100 = get_daily_top_100()
    hungry = [k for k in top_100 if k.get("hungry")]
    return hungry

def get_velocity_keywords_only():
    top_100 = get_daily_top_100()
    velocity = [k for k in top_100 if k.get("is_weekly_search_trend") and k.get("confidence_score",0) >= 85]
    return velocity

def is_market_hungry(query: str) -> bool:
    q = query.lower()
    return any(h in q for h in HUNGRY_BOOST_KEYWORDS) and is_7day_search_velocity(q)

def is_7day_search_trend(query: str) -> bool:
    return is_7day_search_velocity(query) and score_search_potential(query) >= 30
