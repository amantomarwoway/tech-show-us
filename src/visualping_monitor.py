"""
src/visualping_monitor.py - NEW - Tera Visualping Idea - PURE BREAKOUT
White House press release page: whitehouse.gov/presidential-actions/
Supreme Court: supremecourt.gov/opinions/
Federal court dockets: courtlistener.com
CNN Breaking RSS: rss.cnn.com/rss/cnn_brk.rss
Logic: Har 60 sec pe page ka hash compare — hash badla matlab naya executive order/law aaya = seconds me breakout alert
- Politics ke trends hamesha naye laws/policies se shuru hote hain
- Jaise hi website par text badlega (naya executive order), seconds me screenshot alert -> raw data before CNN/Fox
- Dataminr/Reddit style tezi detection
- Breakout = video banna hi banna hai, koi fallback nahi
Location: src/visualping_monitor.py
"""
import hashlib, json, re, time, random
from pathlib import Path
from datetime import datetime, timezone
import requests

HASH_FILE = Path("data/visualping_hashes.json")
CACHE_FILE = Path("data/visualping_cache.json")
HASH_FILE.parent.mkdir(parents=True, exist_ok=True)

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Sources to monitor - as per user request
VISUALPING_SOURCES = [
    ("whitehouse_press", "https://www.whitehouse.gov/presidential-actions/", "White House Press Release - Executive Orders - New Laws/Policies"),
    ("whitehouse_briefing", "https://www.whitehouse.gov/briefing-room/", "White House Briefing Room - New Policies - Politics start"),
    ("supreme_court_slip", "https://www.supremecourt.gov/opinions/slipopinion/24", "Supreme Court - Slip Opinions - New Announcements"),
    ("supreme_court_recent", "https://www.supremecourt.gov/opinions/recentdecisions", "Supreme Court - Recent Decisions - Raw data"),
    ("courtlistener", "https://www.courtlistener.com/?type=r&q=&order_by=dateFiled+desc", "Federal Court Dockets - New Filings - CourtListener"),
    ("cnn_breaking", "http://rss.cnn.com/rss/cnn_brk.rss", "CNN Breaking RSS - Breaking before mainstream"),
    ("whitehouse_news", "https://www.whitehouse.gov/news/", "White House News - Latest Presidential Actions"),
]

def load_prev_hashes():
    if HASH_FILE.exists():
        try:
            return json.loads(HASH_FILE.read_text())
        except:
            return {}
    return {}

def save_hashes(hashes):
    try:
        HASH_FILE.write_text(json.dumps(hashes, indent=2))
    except Exception as e:
        print(f"[VISUALPING] Save hash fail {e}")

def extract_title_from_html(html, url):
    """Extract best title from HTML"""
    try:
        m = re.search(r'<title>(.*?)</title>', html, re.I|re.S)
        title = clean_id(m.group(1)[:150] if m else "")
        # Try extract executive order / bill / opinion specifics
        patterns = [
            r'Executive Order[^<\n]{0,120}',
            r'Executive Order\s+\d+',
            r'Presidential Action[^<]{0,80}',
            r'New (Bill|Law|Policy|Executive Order)[^<\n]{0,100}',
            r'Supreme Court[^<\n]{0,120}',
            r'Slip Opinion[^<]{0,80}',
            r'BREAKING[:\s]+[^<\n]{0,100}'
        ]
        for pat in patterns:
            m2 = re.search(pat, html, re.I)
            if m2:
                extracted = clean_id(m2.group(0)[:130])
                if len(extracted) > 10:
                    return extracted
        return title or f"Breaking from {url.split('/')[2]}"
    except:
        return f"Breaking Alert"

def get_visualping_breakouts():
    """
    Core Visualping logic: Har 60 sec pe page ka hash compare
    Hash badla matlab naya executive order/law aaya = seconds me breakout alert
    """
    breakouts = []
    prev_hashes = load_prev_hashes()
    new_hashes = {}
    
    print(f"[VISUALPING] Monitoring {len(VISUALPING_SOURCES)} sources - Hash compare every 60 sec - NO FALLBACK")
    
    for name, url, desc in VISUALPING_SOURCES:
        try:
            if "rss.cnn.com" in url or url.endswith(".rss"):
                # CNN Breaking RSS
                try:
                    import feedparser
                    feed = feedparser.parse(url)
                    if feed.entries:
                        latest_title = clean_id(feed.entries[0].title)
                        latest_link = feed.entries[0].link
                        h = hashlib.md5(latest_title.encode()).hexdigest()
                        new_hashes[name] = h
                        
                        # If hash changed = new breaking news = seconds alert
                        if prev_hashes.get(name) and prev_hashes[name] != h:
                            if len(latest_title) < 5:
                                continue
                            if re.match(r'^m[0-9]', latest_title, re.I):
                                continue
                            print(f"🔥 [VISUALPING BREAKOUT] {name} CHANGED -> {latest_title[:80]} - {desc}")
                            breakouts.append({
                                "title": latest_title,
                                "query": latest_title,
                                "url": latest_link,
                                "source": f"visualping_{name}",
                                "published": time.gmtime(),
                                "summary": latest_title,
                                "is_breakout": True,
                                "breakout_score": 6000,
                                "search_volume": 95,
                                "bot_friendly": True,
                                "filter_c_score": 95,
                                "bot_friendly_score": 95,
                                "freshness_score": 98,
                                "reliability": 0.97,
                                "visualping_alert": f"VISUALPING: Text changed on {desc} - {url} - Seconds alert - Raw data before CNN/Fox - {latest_title[:60]}",
                                "visualping_desc": desc
                            })
                        elif not prev_hashes.get(name):
                            # First time save hash, don't alert
                            print(f"[VISUALPING] First hash saved for {name}: {latest_title[:50]}")
                        else:
                            print(f"[VISUALPING] No change {name}")
                    else:
                        print(f"[VISUALPING] No entries {name}")
                except Exception as e:
                    print(f"[VISUALPING] RSS {name} fail {e}")
                    continue
            else:
                # HTML pages: White House, Supreme Court, CourtListener
                try:
                    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, timeout=10)
                    if r.status_code != 200:
                        print(f"[VISUALPING] {name} status {r.status_code}")
                        continue
                    
                    # Use first 8000 chars for hash - sensitive to text change
                    snippet = r.text[:8000]
                    # Remove dynamic timestamps to avoid false alerts
                    snippet_clean = re.sub(r'\d{1,2}:\d{2}.*?(AM|PM)', '', snippet)
                    snippet_clean = re.sub(r'\d{4}-\d{2}-\d{2}', '', snippet_clean)
                    h = hashlib.md5(snippet_clean.encode()).hexdigest()
                    new_hashes[name] = h
                    
                    if prev_hashes.get(name) and prev_hashes[name] != h:
                        title = extract_title_from_html(r.text, url)
                        title_clean = clean_id(title)
                        if len(title_clean) < 5:
                            title_clean = f"Breaking {desc.split(' - ')[0]}"
                        if re.match(r'^m[0-9]', title_clean, re.I):
                            continue
                        
                        print(f"🔥🔥🔥 [VISUALPING BREAKOUT] {name} HTML CHANGED - {desc} - {title_clean[:80]} - New Executive Order / Law / Policy!")
                        breakouts.append({
                            "title": title_clean,
                            "query": title_clean,
                            "url": url,
                            "source": f"visualping_{name}",
                            "published": time.gmtime(),
                            "summary": title_clean,
                            "is_breakout": True,
                            "breakout_score": 6500,
                            "search_volume": 95,
                            "bot_friendly": True,
                            "filter_c_score": 95,
                            "bot_friendly_score": 95,
                            "freshness_score": 98,
                            "reliability": 0.98,
                            "visualping_alert": f"VISUALPING: Text changed on {desc} - New Executive Order / Law / Policy detected - Seconds alert - Raw data before mainstream media - {title_clean[:70]}",
                            "visualping_desc": desc,
                            "visualping_url": url
                        })
                    elif not prev_hashes.get(name):
                        print(f"[VISUALPING] First hash saved for {name}")
                    else:
                        print(f"[VISUALPING] No change {name} - hash same")
                        
                except Exception as e:
                    print(f"[VISUALPING] {name} HTML fail {e}")
                    continue
                    
        except Exception as e:
            print(f"[VISUALPING] {name} overall fail {e}")
            continue
    
    # Save new hashes
    # Merge with prev to keep all
    merged = {**prev_hashes, **new_hashes}
    save_hashes(merged)
    
    # Dataminr / Reddit style - agar koi khabar achanak tezi pakad rahi hai
    try:
        print("[VISUALPING] Checking Reddit rising - Dataminr style tezi detection")
        r = requests.get("https://www.reddit.com/r/all/rising/.json?limit=12", headers={"User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)"}, timeout=7)
        if r.status_code == 200:
            data = r.json()
            for child in data.get('data',{}).get('children',[])[:6]:
                try:
                    cdata = child['data']
                    title = clean_id(cdata.get('title',''))
                    if len(title) < 8: continue
                    if re.match(r'^m[0-9]', title, re.I): continue
                    score = cdata.get('score',0)
                    upvote_ratio = cdata.get('upvote_ratio',0)
                    # Tezi pakad rahi hai = high score in rising
                    if score > 350 and upvote_ratio > 0.7:
                        print(f"🔥 [DATAMINR/REDDIT BREAKOUT] Rising spike {score} upvote {upvote_ratio} -> {title[:70]}")
                        breakouts.append({
                            "title": title,
                            "query": title,
                            "url": f"https://reddit.com{cdata.get('permalink','')}",
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
                            "visualping_alert": f"Dataminr/Reddit spike: {score} points in rising, upvote {upvote_ratio} - tezi pakad rahi hai - {title[:50]}"
                        })
                except:
                    continue
    except Exception as e:
        print(f"[VISUALPING] reddit fail {e}")
    
    # Cache
    try:
        CACHE_FILE.write_text(json.dumps({"last": datetime.now(timezone.utc).isoformat(), "breakouts": breakouts[:20]}, indent=2))
    except:
        pass
    
    print(f"[VISUALPING ENGINE] Total BREAKOUT: {len(breakouts)} - NO FALLBACK - Video banna hi banna hai if breakout found")
    return breakouts

def monitor_loop(interval_seconds=60):
    """Continuous monitoring - Har 60 sec pe hash compare"""
    print(f"🔥 [VISUALPING MONITOR] Starting continuous loop every {interval_seconds} sec - NO FALLBACK")
    print(f"   Monitoring: {[s[0] for s in VISUALPING_SOURCES]}")
    while True:
        try:
            print(f"\n[VISUALPING] {datetime.now(timezone.utc).isoformat()} - Checking all sources...")
            brk = get_visualping_breakouts()
            if brk:
                print(f"🔥🔥🔥 {len(brk)} BREAKOUT DETECTED - VIDEO BANEGA HI BANEGA 🔥🔥🔥")
                for b in brk:
                    print(f"   -> {b['query'][:70]} | Score {b['breakout_score']} | {b['source']}")
                # Here main.py will pick these and create video
                # Could also trigger webhook / notification
            else:
                print(f"[VISUALPING] No breakout this cycle - waiting {interval_seconds} sec")
            time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("[VISUALPING] Stopped by user")
            break
        except Exception as e:
            print(f"[VISUALPING] Loop error {e}, retry in {interval_seconds}s")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    print("=== Testing visualping_monitor.py - PURE VISUALPING BREAKOUT ===")
    brk = get_visualping_breakouts()
    for i,b in enumerate(brk[:5]):
        print(f"{i+1}. {b['query'][:70]} | {b['source']} | Score {b['breakout_score']} | Alert {b['visualping_alert'][:80]}")
    if not brk:
        print("No breakout right now - first run saved hashes - next run will detect changes - NO FALLBACK")
        print("Run monitor_loop() for continuous 60 sec check")
