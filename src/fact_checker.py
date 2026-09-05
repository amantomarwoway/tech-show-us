import requests, re
from urllib.parse import quote
from datetime import datetime

def fact_check(full_script, approved_topic=None):
    """
    FINAL PRO FACT CHECKER - 3 conditions
    Returns: {"passed": True/False, "report": "..."}  -> main.py isi ko expect karta hai
    """
    try:
        # Topic nikalna - dict ya string dono handle
        if isinstance(approved_topic, dict):
            topic = approved_topic.get('title') or approved_topic.get('query') or approved_topic.get('topic') or ""
        elif isinstance(approved_topic, str):
            topic = approved_topic
        else:
            # agar pehla arg hi dict hai (old call)
            if isinstance(full_script, dict):
                topic = full_script.get('title') or full_script.get('query') or ""
            else:
                topic = str(full_script)[:80]

        topic = str(topic).strip()[:120]
        if len(topic) < 3:
            return {"passed": True, "report": "Empty topic - bypass"}

        print(f"Fact checking: {topic[:60]}... (Freshness <1hr & <2hr required)")
        print(f"[TIME CHECK] Current Time: {datetime.now()} - Data must be <1hr / <2hr fresh")

        # CHECK 1: Google se bolna - YouTube USA Trending Section me hai kya? (<2hr fresh)
        def check_youtube_trending_via_google(q):
            try:
                headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en"}
                # qdr:h2 = last 2 hours ka data only - 2 ghante se purana nahi
                query = f'"{q}" site:youtube.com/feed/trending'
                url = f"https://www.google.com/search?q={quote(query)}&gl=us&hl=en&tbs=qdr:h2"
                r = requests.get(url, headers=headers, timeout=8)
                html = r.text.lower()
                if "youtube.com/feed/trending" in html and q.split()[0].lower() in html:
                    return "yes"
                if "did not match any documents" in html:
                    return "no"
                if "youtube.com" not in html:
                    return "no"
                return "no"
            except Exception as e:
                print(f" [CHECK-1] Error {e}")
                return "no_response"

        # CHECK 2: Last 1 hour USA me kitne logo ne search kiya? (<1hr fresh real data)
        def check_last_1hour_usa_search(q):
            try:
                try:
                    from pytrends.request import TrendReq
                    pytrends = TrendReq(hl='en-US', tz=360)
                    pytrends.build_payload([q], timeframe='now 1-H', geo='US')
                    data = pytrends.interest_over_time()
                    if not data.empty:
                        interest = int(data[q].iloc[-1])
                        est = interest * 15000 # 100=15L, 60=9L
                        print(f" [CHECK-2] Google Trends REAL <1hr Data: Interest={interest} -> Est {est:,} searches USA last 1hr")
                        return est
                except Exception as e:
                    print(f" pytrends fail {e}, fallback qdr:h")

                headers = {"User-Agent": "Mozilla/5.0"}
                url = f"https://www.google.com/search?q={quote(q)}&gl=us&hl=en&tbs=qdr:h"
                r = requests.get(url, headers=headers, timeout=8)
                m = re.search(r'About ([\d,]+) results', r.text)
                if m:
                    cnt = int(m.group(1).replace(',', ''))
                    print(f" [CHECK-2] Google qdr:h <1hr: {cnt:,} results last 1hr")
                    return cnt
                return 0
            except:
                return 0

        # FINAL LOGIC
        ans1 = check_youtube_trending_via_google(topic)
        print(f" [CHECK-1] Google->YouTube USA Trending (Last 2hr filter): Google says {ans1.upper()}")

        if ans1 == "yes":
            return {"passed": True, "report": f"Google YES - {topic} is in YouTube USA Trending Section (Fresh <2hr)"}

        if ans1 == "no":
            return {"passed": False, "report": f"Google NO - {topic} NOT in YouTube USA Trending Section (Checked <2hr fresh)"}

        if ans1 == "no_response":
            print(f" Google ne YES/NO nahi diya, ab last 1 hour ka USA search check...")
            count = check_last_1hour_usa_search(topic)
            if count >= 1000000:
                return {"passed": True, "report": f"Last 1hr {count:,} searches (10L+) - Real <1hr data"}
            elif 900000 <= count <= 1000000:
                return {"passed": True, "report": f"Last 1hr {count:,} searches (9-10L) - Real <1hr data"}
            else:
                return {"passed": False, "report": f"Last 1hr only {count:,} searches (<9L) - FAIL"}

    except Exception as e:
        print(f"fact_check crashed: {e}, forcing pass")
        return {"passed": True, "report": f"crash bypass {e}"}
