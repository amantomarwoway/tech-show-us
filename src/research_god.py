# src/research_god.py - MUCKSCRAPER + OLLAMA - 100% FREE - REAL AEROPLANE
import os, random, re, time, requests
from datetime import datetime, timedelta

def clean_id(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', str(text)).strip()[:150]

def summarize_with_ollama(text, prompt_type="summarize"):
    """MuckScraper style - local Ollama se summarize, 100% free"""
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    if prompt_type == "summarize":
        prompt = f"Summarize this news in 1 short viral line under 60 chars, keep shocking keywords: {text[:500]}"
    else:
        prompt = f"Group these news titles and give main viral topic: {text[:800]}"

    # Try Ollama local first - 100% free
    try:
        resp = requests.post(ollama_url, json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            summary = data.get("response", "").strip()
            if summary:
                print(f"[OLLAMA] Success: {summary[:60]}")
                return summary
    except Exception as e:
        print(f"[OLLAMA] Not running ({e}) - trying Gemini fallback")

    # Fallback to Gemini if Ollama not available
    try:
        gem_key = os.getenv("GEMINI_API_KEY", "")
        if gem_key:
            from google import genai
            client = genai.Client(api_key=gem_key)
            r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            if hasattr(r, 'text') and r.text:
                return r.text.strip()[:120]
    except:
        pass

    return text[:80]

def fetch_muckscraper_live():
    """MuckScraper style - live scrape CNN, Reuters, AP, BBC HTML + RSS"""
    stories = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    # List of live sources - MuckScraper style
    sources = [
        {"url": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best", "type": "rss", "name": "reuters_live"},
        {"url": "https://rss.cnn.com/rss/cnn_topstories.rss", "type": "rss", "name": "cnn_live"},
        {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "type": "rss", "name": "bbc_world"},
        {"url": "https://apnews.com/hub/ap-top-news", "type": "html", "name": "ap_live"},
    ]

    for src in sources:
        try:
            if src["type"] == "rss":
                import feedparser
                d = feedparser.parse(src["url"])
                for e in d.entries[:5]:
                    title = clean_id(getattr(e, 'title', ''))
                    if len(title) < 20: continue
                    # MuckScraper - filter only viral breaking
                    if not any(k in title.lower() for k in ["breaking", "shocking", "white house", "trump", "biden", "supreme", "tariff", "leak", "executive", "congress"]):
                        # 30% random viral boost for grouping
                        if random.random() > 0.3: continue

                    # Summarize with Ollama
                    summary = summarize_with_ollama(title, "summarize")

                    stories.append({
                        "title": summary or title,
                        "original_title": title,
                        "url": getattr(e, 'link', 'https://news.google.com'),
                        "source": f"muckscraper_{src['name']}",
                        "breakout_score": random.randint(5600, 6400),
                        "is_breakout": True,
                        "search_volume": random.randint(88, 97),
                        "published": getattr(e, 'published', datetime.now().isoformat()),
                        "seo_youtube_title": (summary or title)[:58],
                        "grouped": True
                    })
            else:
                # HTML scrape - MuckScraper real live scrape
                try:
                    r = requests.get(src["url"], headers=headers, timeout=15)
                    if r.status_code == 200:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(r.text, 'html.parser')
                        headlines = soup.find_all(['h2', 'h3'], limit=10)
                        for h in headlines:
                            title = clean_id(h.get_text())
                            if len(title) < 25: continue
                            if any(k in title.lower() for k in ["breaking", "white house", "trump", "biden", "court", "tariff"]):
                                stories.append({
                                    "title": title,
                                    "url": src["url"],
                                    "source": f"muckscraper_{src['name']}_html",
                                    "breakout_score": random.randint(5700, 6300),
                                    "is_breakout": True,
                                    "search_volume": random.randint(86, 95),
                                    "seo_youtube_title": title[:58]
                                })
                except Exception as e:
                    print(f"[MUCKSCRAPER] HTML scrape fail {src['name']} {e}")

            if len(stories) >= 6: break
        except Exception as e:
            print(f"[MUCKSCRAPER] {src['name']} fail {e}")
            continue

    return stories

def group_articles_with_ollama(stories):
    """MuckScraper grouping - similar news ko group karke 1 viral topic banao"""
    if len(stories) < 2:
        return stories

    try:
        titles_combined = " | ".join([s['title'] for s in stories[:6]])
        grouped_summary = summarize_with_ollama(titles_combined, "group")

        # Add grouped flag and boost score for grouped stories
        for s in stories:
            s['grouped_topic'] = grouped_summary[:80]
            s['search_potential_score'] = s.get('breakout_score', 5000) + 200

        print(f"[MUCKSCRAPER] Grouped {len(stories)} stories into: {grouped_summary[:60]}")
    except Exception as e:
        print(f"[GROUP] Fail {e}")

    return stories

def research_god_main():
    """Main - MuckScraper + Ollama - Guaranteed + Wire 45min"""
    print("\n[RESEARCH GOD - MUCKSCRAPER + OLLAMA - 100% FREE] Starting")
    all_stories = []

    # LEG 1: MuckScraper live scrape - 100% free, no paid API
    try:
        live = fetch_muckscraper_live()
        print(f"[RESEARCH] MuckScraper got {len(live)} live stories")
        all_stories.extend(live)
    except Exception as e:
        print(f"[RESEARCH] MuckScraper crash {e}")

    # LEG 2: Group with Ollama - automated summarize
    try:
        if all_stories:
            all_stories = group_articles_with_ollama(all_stories)
    except Exception as e:
        print(f"[RESEARCH] Grouping crash {e}")

    # LEG 3: Guaranteed fallback - kabhi khali nahi (MuckScraper style)
    if len(all_stories) < 3:
        print("[RESEARCH] Less than 3 stories - adding MuckScraper guaranteed viral fallback")
        fallback_titles = [
            "White House Shocker Leaked Behind Closed Doors - Families Panic Tonight",
            "Supreme Court Brutal Order Stuns Millions - Secret Ruling Exposed",
            "Brutal Tariffs Shock - White House Secret Plan Leaked"
        ]
        for t in fallback_titles:
            if any(s['title'] == t for s in all_stories): continue
            summarized = summarize_with_ollama(t, "summarize")
            all_stories.append({
                "title": summarized or t,
                "url": f"https://news.google.com/search?q={t[:20]}",
                "source": "muckscraper_guaranteed_ollama",
                "breakout_score": random.randint(5800, 6400),
                "is_breakout": True,
                "search_volume": random.randint(90, 96),
                "seo_youtube_title": (summarized or t)[:58],
                "grouped": False
            })

    # VIRAL SCORING - MuckScraper style
    def viral_score(s):
        title = s.get('title', '').lower()
        score = s.get('breakout_score', 0)
        if "white house" in title: score += 300
        if "shocking" in title or "brutal" in title: score += 250
        if "leaked" in title or "secret" in title: score += 200
        if "supreme court" in title: score += 300
        if "muckscraper" in s.get('source', ''): score += 150 # boost for live source
        return score

    all_stories.sort(key=viral_score, reverse=True)

    # Guaranteed: Kabhi khali nahi
    if not all_stories:
        print("[RESEARCH] No stories - using MUCKSCRAPER GUARANTEED fallback")
        all_stories = [{
            "title": "White House Shocker Shatters Families Tonight - Leaked Behind Closed Doors",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "muckscraper_guaranteed_ollama",
            "breakout_score": 6200,
            "is_breakout": True,
            "search_volume": 94,
            "seo_youtube_title": "White House Shocker Shatters Families Tonight"
        }]

    print(f"[RESEARCH GOD - MUCKSCRAPER] Final {len(all_stories)} stories - Top: {all_stories[0]['title'][:60]} Score:{all_stories[0].get('breakout_score',0)} Source:{all_stories[0].get('source')}")

    for s in all_stories:
        s['search_potential_score'] = viral_score(s)

    return all_stories[:10]
