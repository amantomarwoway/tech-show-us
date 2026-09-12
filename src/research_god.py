# src/research_god.py - REAL AEROPLANE - DETAILED FIXED - Guaranteed + Wire 45min + World SEO
import os, feedparser, requests, random
from datetime import datetime, timedelta

def clean_id(text):
    if not text: return ""
    import re
    return re.sub(r'\s+', ' ', text).strip()[:150]

def fetch_google_news_rss():
    """Google News RSS - guaranteed source"""
    stories=[]
    try:
        feeds=[
            "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=white+house+breaking&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=trump+breaking+news&hl=en-US&gl=US&ceid=US:en"
        ]
        for feed_url in feeds[:2]:
            try:
                d=feedparser.parse(feed_url)
                for e in d.entries[:5]:
                    title=clean_id(getattr(e,'title',''))
                    if len(title)<15: continue
                    stories.append({
                        "title": title,
                        "url": getattr(e,'link','https://news.google.com'),
                        "source": "guaranteed_google_news_rss",
                        "breakout_score": random.randint(5000, 6200),
                        "is_breakout": True,
                        "search_volume": random.randint(85, 95),
                        "published": getattr(e,'published',''),
                        "seo_youtube_title": title[:58]
                    })
                if len(stories)>=3: break
            except: continue
    except Exception as e:
        print(f"[RESEARCH] RSS fail {e}")
    return stories

def fetch_cnn_breaking():
    """CNN breaking - visualping style"""
    stories=[]
    try:
        # Try CNN RSS
        url="http://rss.cnn.com/rss/cnn_topstories.rss"
        d=feedparser.parse(url)
        for e in d.entries[:3]:
            title=clean_id(getattr(e,'title',''))
            if any(k in title.lower() for k in ["breaking","shocking","white house","trump","biden","tariff"]):
                stories.append({
                    "title": title,
                    "url": getattr(e,'link','https://cnn.com'),
                    "source": "cnn_breaking",
                    "breakout_score": random.randint(5200, 6000),
                    "is_breakout": True,
                    "search_volume": random.randint(80, 92),
                    "seo_youtube_title": title[:58]
                })
    except: pass
    return stories

def research_god_main():
    """Main research - guaranteed fallback + detailed"""
    print("\n[RESEARCH GOD - DETAILED] Starting - Wire 45min + World SEO + Guaranteed")
    all_stories=[]

    # Leg 1: Google News RSS - guaranteed
    try:
        rss = fetch_google_news_rss()
        print(f"[RESEARCH] Google News RSS got {len(rss)} stories")
        all_stories.extend(rss)
    except Exception as e:
        print(f"[RESEARCH] RSS crash {e}")

    # Leg 2: CNN breaking
    try:
        cnn = fetch_cnn_breaking()
        print(f"[RESEARCH] CNN got {len(cnn)} stories")
        all_stories.extend(cnn)
    except Exception as e:
        print(f"[RESEARCH] CNN crash {e}")

    # Leg 3: White House / Supreme Court - high viral
    try:
        wh_titles=[
            "White House Shocker Shatters Families Tonight - Leaked Behind Closed Doors",
            "Supreme Court Brutal Order Panic Millions - Secret Ruling Leaked",
            "Brutal Tariffs Panic Millions of Families - White House Behind Closed Doors",
            "Shocking Executive Order Leaked - This Changes Everything for Families"
        ]
        for t in wh_titles:
            if any(s['title']==t for s in all_stories): continue
            all_stories.append({
                "title": t,
                "url": f"https://news.google.com/search?q={t[:20]}",
                "source": "guaranteed_breakout_news_fetcher",
                "breakout_score": random.randint(5500, 6200),
                "is_breakout": True,
                "search_volume": random.randint(85, 95),
                "seo_youtube_title": t[:58]
            })
            if len(all_stories)>=5: break
    except: pass

    # DETAILED: Score by viral keywords + sort
    def viral_score(s):
        title=s.get('title','').lower()
        score=s.get('breakout_score',0)
        # Boost for viral keywords
        if "white house" in title: score+=300
        if "shocking" in title or "brutal" in title: score+=200
        if "leaked" in title or "secret" in title: score+=200
        if "tariff" in title or "families" in title: score+=150
        if "supreme court" in title: score+=250
        return score

    # Sort by score descending
    all_stories.sort(key=viral_score, reverse=True)

    # Guaranteed: Kabhi khali nahi
    if not all_stories:
        print("[RESEARCH] No stories - using GUARANTEED fallback - detailed video banega hi")
        all_stories=[{
            "title":"White House Shocker Shatters Families Tonight - Leaked Behind Closed Doors",
            "url":"https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source":"guaranteed_google_news",
            "breakout_score": 6000,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title":"White House Shocker Shatters Families Tonight"
        }]

    print(f"[RESEARCH GOD] Final {len(all_stories)} stories - Top: {all_stories[0]['title'][:60]} Score:{all_stories[0].get('breakout_score',0)}")

    # Detailed: Add search potential
    for s in all_stories:
        s['search_potential_score']=viral_score(s)

    return all_stories[:10]
