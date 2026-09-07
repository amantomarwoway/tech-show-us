"""
news_fetcher.py - PURE BREAKOUT ONLY - NO FALLBACK
- Politics ke trends hamesha naye laws ya policies se shuru hote hain
- Visualping: US White House press release page, Federal court dockets, Supreme Court announcement pages monitor
- Jaise hi website par text badlega (naya executive order), seconds me screenshot alert -> raw data before CNN/Fox
- Google Trends par "Breakout" political terms monitor
- Dataminr/Reddit par tezi pakad rahi news -> background "What is Bill X / Who is Politician Y" ready
- Breakout = video banna hi banna hai, koi fallback nahi
"""
import feedparser, time, random, re, hashlib, json
from datetime import datetime, timezone
import requests
from pathlib import Path

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

CACHE_FILE = Path("data/breakout_cache.json")
HASH_FILE = Path("data/visualping_hashes.json")
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

def get_breakouts_from_pytrends():
    """Google Trends par Breakout political terms ko monitor karein - +5000% spike"""
    breakouts = []
    try:
        from pytrends.request import TrendReq
        print("[BREAKOUT] Checking pytrends BREAKOUT for USA - Politics laws/policies se start + Any Topic...")
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        seeds = ["executive order", "supreme court", "white house", "breaking news", "usa bill", "senate vote", "congress", "federal court", "new law"]
        random.shuffle(seeds)
        for seed in seeds[:4]:
            try:
                pytrends.build_payload([seed], timeframe='now 1-d', geo='US')
                related = pytrends.related_queries()
                if seed in related and related[seed].get('rising') is not None:
                    rising = related[seed]['rising']
                    for _, row in rising.iterrows():
                        q = str(row['query'])
                        val = str(row['value'])
                        if 'breakout' in val.lower():
                            q_clean = clean_id(q)
                            if len(q_clean) < 3: continue
                            if re.match(r'^m[0-9]', q_clean, re.I): continue
                            breakouts.append({
                                "title": q_clean,
                                "query": q_clean,
                                "url": f"https://trends.google.com/trends?q={q_clean}",
                                "source": "google_trends_breakout",
                                "published": time.gmtime(),
                                "summary": q_clean,
                                "is_breakout": True,
                                "breakout_score": 5000,
                                "breakout_seed": seed,
                                "search_volume": 95,
                                "bot_friendly": True,
                                "filter_c_score": 95,
                                "bot_friendly_score": 95,
                                "freshness_score": 95,
                                "reliability": 0.98,
                                "visualping_alert": f"Google Trends BREAKOUT +5000% (seed={seed}) - New law/policy"
                            })
                            print(f"[BREAKOUT FOUND] {q_clean} -> BREAKOUT +5000% seed={seed}")
                time.sleep(1.2)
            except Exception as e:
                print(f"[BREAKOUT] seed {seed} fail {e}")
                continue
        print(f"[BREAKOUT] pytrends found {len(breakouts)} BREAKOUT topics")
    except Exception as e:
        print(f"[BREAKOUT] pytrends fail {e}")
    return breakouts

def get_visualping_breakouts():
    """
    Visualping: Is AI tool ki madad se aap US White House press release page, 
    Federal court dockets, ya Supreme Court ke main announcement pages ko monitor par laga sakte hain.
    Jaise hi website par koi text badlega (jaise koi naya executive order), 
    yeh aapko seconds mein screenshot alert bhej dega. Mainstream media tak khabar chapne se pehle raw data.
    """
    breakouts = []
    sources = [
        ("whitehouse_press", "https://www.whitehouse.gov/presidential-actions/", "White House Press Release - Executive Orders"),
        ("whitehouse_briefing", "https://www.whitehouse.gov/briefing-room/", "White House Briefing Room - New Policies"),
        ("supreme_court", "https://www.supremecourt.gov/opinions/slipopinion/24", "Supreme Court - Slip Opinions / Announcements"),
        ("supreme_court_recent", "https://www.supremecourt.gov/opinions/recentdecisions", "Supreme Court - Recent Decisions"),
        ("courtlistener", "https://www.courtlistener.com/?type=r&q=&order_by=dateFiled+desc", "Federal Court Dockets - New Filings"),
        ("cnn_breaking", "http://rss.cnn.com/rss/cnn_brk.rss", "CNN Breaking RSS - Breaking before mainstream"),
    ]
    prev_hashes = {}
    if HASH_FILE.exists():
        try:
            prev_hashes = json.loads(HASH_FILE.read_text())
        except:
            prev_hashes = {}
    new_hashes = {}
    for name, url, desc in sources:
        try:
            if "rss" in url:
                feed = feedparser.parse(url)
                if feed.entries:
                    latest = feed.entries[0].title
                    h = hashlib.md5(latest.encode()).hexdigest()
                    new_hashes[name] = h
                    if prev_hashes.get(name) and prev_hashes[name] != h:
                        q_clean = clean_id(latest)
                        if len(q_clean) < 5: continue
                        breakouts.append({
                            "title": q_clean,
                            "query": q_clean,
                            "url": feed.entries[0].link,
                            "source": f"visualping_{name}",
                            "published": time.gmtime(),
                            "summary": q_clean,
                            "is_breakout": True,
                            "breakout_score": 6000,
                            "search_volume": 95,
                            "bot_friendly": True,
                            "filter_c_score": 95,
                            "bot_friendly_score": 95,
                            "freshness_score": 98,
                            "reliability": 0.97,
                            "visualping_alert": f"VISUALPING: Text changed on {desc} - {url} - Seconds alert - Raw data before mainstream"
                        })
                        print(f"[VISUALPING BREAKOUT] {name} changed -> {q_clean[:70]} - {desc}")
            else:
                r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
                if r.status_code == 200:
                    # Use first 5000 chars hash for change detection
                    snippet = r.text[:5000]
                    h = hashlib.md5(snippet.encode()).hexdigest()
                    new_hashes[name] = h
                    if prev_hashes.get(name) and prev_hashes[name] != h:
                        import re as re2
                        m = re2.search(r'<title>(.*?)</title>', r.text, re2.I|re2.S)
                        title = clean_id(m.group(1)[:150] if m else f"Breaking from {desc}")
                        # Try extract executive order / opinion
                        m2 = re2.search(r'Executive Order[^<]{0,120}|New (Bill|Law|Policy)[^<]{0,100}|Supreme Court[^<]{0,120}', r.text, re2.I)
                        if m2:
                            title = clean_id(m2.group(0)[:130])
                        breakouts.append({
                            "title": title,
                            "query": title,
                            "url": url,
                            "source": f"visualping_{name}",
                            "published": time.gmtime(),
                            "summary": title,
                            "is_breakout": True,
                            "breakout_score": 6500,
                            "search_volume": 95,
                            "bot_friendly": True,
                            "filter_c_score": 95,
                            "bot_friendly_score": 95,
                            "freshness_score": 98,
                            "reliability": 0.98,
                            "visualping_alert": f"VISUALPING: Text changed on {desc} - New Executive Order / Law / Policy - Seconds alert"
                        })
                        print(f"[VISUALPING BREAKOUT] {name} HTML changed - {desc} - {title[:70]}")
        except Exception as e:
            print(f"[VISUALPING] {name} fail {e}")
    try:
        HASH_FILE.write_text(json.dumps(new_hashes, indent=2))
    except:
        pass

    # Dataminr / Reddit style - agar koi khabar achanak tezi pakad rahi hai
    try:
        r = requests.get("https://www.reddit.com/r/all/rising/.json?limit=10", headers={"User-Agent":"Mozilla/5.0"}, timeout=6)
        if r.status_code == 200:
            data = r.json()
            for child in data.get('data',{}).get('children',[])[:5]:
                title = clean_id(child['data'].get('title',''))
                if len(title) < 8: continue
                score = child['data'].get('score',0)
                if score > 400:
                    breakouts.append({
                        "title": title,
                        "query": title,
                        "url": f"https://reddit.com{child['data'].get('permalink','')}",
                        "source": "reddit_rising_breakout",
                        "published": time.gmtime(),
                        "summary": title,
                        "is_breakout": True,
                        "breakout_score": 5500,
                        "search_volume": 85,
                        "bot_friendly": True,
                        "filter_c_score": 85,
                        "bot_friendly_score": 85,
                        "freshness_score": 90,
                        "reliability": 0.90,
                        "visualping_alert": f"Dataminr/Reddit spike: {score} points in rising - tezi pakad rahi hai"
                    })
                    print(f"[DATAMINR/REDDIT BREAKOUT] Rising spike {score} -> {title[:60]}")
    except Exception as e:
        print(f"[VISUALPING] reddit fail {e}")

    print(f"[VISUALPING ENGINE] Total breakout: {len(breakouts)}")
    return breakouts

def get_all_breakouts_any_topic():
    """Main entry - ONLY breakout ANY topic - No fallback - Visualping + Google Trends BREAKOUT"""
    all_breakouts = []
    try:
        all_breakouts.extend(get_breakouts_from_pytrends())
    except Exception as e:
        print(f"[BREAKOUT] pytrends wrapper fail {e}")
    try:
        all_breakouts.extend(get_visualping_breakouts())
    except Exception as e:
        print(f"[BREAKOUT] visualping wrapper fail {e}")
    # Deduplicate
    seen = set()
    deduped = []
    for b in all_breakouts:
        q = b['query'].lower()
        if q not in seen:
            seen.add(q)
            deduped.append(b)
    print(f"[BREAKOUT ENGINE FINAL] Total ANY-TOPIC breakouts: {len(deduped)} - NO FALLBACK - Only breakout = video banna hi banna hai")
    try:
        CACHE_FILE.write_text(json.dumps({"last": datetime.now(timezone.utc).isoformat(), "breakouts": deduped[:30]}, indent=2))
    except:
        pass
    return deduped

def fetch_all_news():
    """PURE BREAKOUT ONLY - NO FALLBACK - Jo karne ko bola h vo hi"""
    print(f"🔥 [NEWS_FETCHER] PURE BREAKOUT MODE - NO FALLBACK - Only Visualping + Google Trends BREAKOUT + Reddit Rising")
    print(f"   Politics trends hamesha naye laws ya policies se shuru hote hain -> White House / Supreme Court / Federal courts monitor")
    
    all_news = get_all_breakouts_any_topic()
    
    if all_news:
        print(f"🔥🔥🔥 BREAKOUT FOUND {len(all_news)} - ANY TOPIC (News+Politics) - VIDEO BANEGA HI BANEGA - NO FALLBACK 🔥🔥🔥")
        for i, b in enumerate(all_news[:5]):
            print(f"   BREAKOUT {i+1}: {b.get('query')[:75]} | Score {b.get('breakout_score')} | {b.get('source')} | {b.get('visualping_alert','')[:80]}")
    else:
        print(f"[BREAKOUT ENGINE] No breakout right now - Returning empty - Main.py will safe exit - NO FALLBACK DUMMY")
    
    return all_news

def fetch_news(limit_per_feed=15, max_total=60):
    news = fetch_all_news()
    # Breakouts ko top pe rakho - already breakout only
    breakout_filtered = [n for n in news if n.get('is_breakout')]
    print(f"[NEWS_FETCHER FINAL] Returning {len(breakout_filtered[:max_total])} BREAKOUT topics (NO FALLBACK) - Politics laws/policies + Any topic")
    return breakout_filtered[:max_total]
