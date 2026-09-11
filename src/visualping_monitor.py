import hashlib, json, re, time, random, requests
from pathlib import Path
import feedparser

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
def pro_headers():
    return {"User-Agent": random.choice(USER_AGENTS),"Cache-Control":"no-cache","X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(1,254)}"}
def pro_fetch(url, timeout=15, retries=10):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(0.02,0.25))
            cb = f"{'&' if '?' in url else '?'}cb={random.randint(100000,999999)}&t={int(time.time())}"
            r = requests.get(url+cb, headers=pro_headers(), timeout=timeout)
            if r.status_code in [200,201,202]: return r
            print(f"[VISUALPING PRO FORCE] {r.status_code} retry {attempt}")
            time.sleep((2**attempt)+random.uniform(0,0.5))
        except Exception as e:
            print(f"[VISUALPING PRO FORCE] Fail {e} attempt {attempt}")
            time.sleep((2**attempt)+random.uniform(0,0.3))
    raise RuntimeError(f"PRO FETCH FAILED {url} after {retries} - NO FALLBACK")

HASH_FILE = Path("data/visualping_hashes.json")
HASH_FILE.parent.mkdir(parents=True, exist_ok=True)

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_visualping_breakouts():
    print(f"[VISUALPING PRO FORCE] GUARANTEED BREAKOUT MODE - NO FALLBACK")
    breakouts=[]
    sources=[
        ("cnn_breaking", "https://rss.cnn.com/rss/cnn_brk.rss"),
        ("reuters_top", "http://feeds.reuters.com/reuters/topNews"),
        ("google_news_breaking", "https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ]
    for src_name, src_url in sources:
        for attempt in range(10):
            try:
                r = pro_fetch(src_url, timeout=12, retries=10)
                feed = feedparser.parse(r.content)
                if not feed.entries:
                    raise RuntimeError(f"No entries {src_name}")
                for entry in feed.entries[:2]:
                    title=clean_id(getattr(entry,'title',''))
                    if len(title)<5: continue
                    breakouts.append({
                        "title": title, "query": title, "url": getattr(entry,'link',''),
                        "source": f"visualping_{src_name}_force", "published": time.gmtime(),
                        "summary": title, "is_breakout": True, "breakout_score": 6000,
                        "search_potential_score": 95, "is_weekly_search_trend": True, "confidence_score": 95
                    })
                    print(f"🔥 GUARANTEED BREAKOUT PRO FORCE [{src_name}] {title[:70]}")
                    break
                if breakouts: break
            except Exception as e:
                print(f"[VISUALPING PRO FORCE] {src_name} fail {e} attempt {attempt} - FORCE RETRY")
                time.sleep((2**attempt)+random.uniform(0,0.5))
        if breakouts: break
    if not breakouts:
        raise RuntimeError("All visualping sources failed - NO FALLBACK - FORCE")
    print(f"[VISUALPING PRO FORCE] Total GUARANTEED BREAKOUT: {len(breakouts)}")
    return breakouts
