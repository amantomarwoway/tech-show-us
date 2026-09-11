import os, random, time, requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 Version/17.2 Mobile/15E148 Safari/604.1"
]
def pro_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Referer": random.choice(["https://www.google.com/","https://www.bing.com/","https://duckduckgo.com/","https://huggingface.co/"]),
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Real-IP": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(1,254)}.{random.randint(1,254)}",
        "DNT": "1"
    }
def pro_fetch(url, timeout=15, retries=10):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(0.02,0.25))
            cb = f"{'&' if '?' in url else '?'}cb={random.randint(100000,999999)}&t={int(time.time())}&r={random.randint(1000,9999)}&v={random.randint(1,999)}&hack={random.randint(10000,99999)}"
            r = requests.get(url+cb, headers=pro_headers(), timeout=timeout)
            if r.status_code in [200,201,202]: return r
            print(f"[PRO HACKER] {r.status_code} for {url[:50]} attempt {attempt+1} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,1))
        except Exception as e:
            print(f"[PRO HACKER] fail {e} attempt {attempt+1} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0.3,1.2))
    raise RuntimeError(f"PRO FETCH FAILED after {retries} attempts - NO FALLBACK - {url}")

RETENTION_CONFIG = {"WORDS_TARGET":45,"WORDS_MIN":40,"WORDS_MAX":50,"DURATION_TARGET":13,"DURATION_MIN":11,"DURATION_MAX":15,"CLIP_DENSITY":1.8,"IMAGE_DURATION":1.0,"VIDEO_DURATION":1.8,"TTS_SPEED":1.15,"FPS_CHOICES":[29.97,30,59.94,60],"NOISE_HUE_FILTER":"noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08","AUDIO_PUNCH_FIRST_SEC":1.6}
WIRE_SERVICE_CONFIG = {"fetch_window_minutes":45,"reuters_feeds":["http://feeds.reuters.com/reuters/topNews","http://feeds.reuters.com/reuters/USNews"],"google_news_feeds":["https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en"]}
SEARCH_VELOCITY_CONFIG = {"confidence_threshold":85}
DB_PATH="data/news_history.db"
OUTPUT_DIR="output"
ENGLISH_COUNTRIES=["USA","UK","Canada","Australia","India","Philippines","South Africa"]
WORLD_50_COUNTRIES=["USA","UK","India","Canada","Australia","Germany","France","Brazil","Japan","Mexico","Italy","Spain","South Africa","Philippines","Indonesia","Turkey","Saudi Arabia","UAE","Singapore","Malaysia","Thailand","Vietnam","Nigeria","Kenya","Argentina","Chile","Colombia","Peru","Netherlands","Sweden","Norway","Denmark","Poland","Ukraine","Pakistan","Bangladesh","New Zealand","Ireland","Israel","Egypt","Greece","Portugal","Belgium","Switzerland","Austria","Czech Republic","Romania","Hungary","Finland"]
GOD_INSTRUCTION="HAR LEG HAR CHEEZ KAHIN SE BHI BEST TARIKE SE USE KARE - NO FALLBACK - FORCE WORK - PRO HACKER PEAK"
REUTERS_FEEDS=WIRE_SERVICE_CONFIG["reuters_feeds"]
GOOGLE_NEWS_WIRE=WIRE_SERVICE_CONFIG["google_news_feeds"]
FETCH_WINDOW_MINUTES=45
US_SEARCH_TRIGGERS=["trump","biden","white house","supreme court","pentagon","fbi","breaking","leaked","secret","behind closed doors"]
WORLD_VIRAL_TAGS=["breakingnews","worldnews","viralnews","usanews"]
IMAGE_DURATION=1.0
CLIP_DURATION=1.8
WIDTH=1080
HEIGHT=1920
FPS_CHOICES=[29.97,30,59.94,60]
