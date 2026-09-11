import feedparser, requests, re, json, random, time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import USER_AGENTS, pro_headers, pro_fetch, FETCH_WINDOW_MINUTES, US_SEARCH_TRIGGERS, WORLD_VIRAL_TAGS, ENGLISH_COUNTRIES, GOD_INSTRUCTION

def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\s+',' ',t).strip(); return t

def pro_fetch_wire_force(url):
    r=pro_fetch(url, timeout=12, retries=10) # NO FALLBACK, force 10 retries
    feed=feedparser.parse(r.content)
    res=[]
    for e in feed.entries[:10]:
        title=clean_id(getattr(e,'title',''))
        if len(title)<8: continue
        res.append({"title":title,"query":title,"url":getattr(e,'link',''),"source":"wire","search_potential_score":random.randint(70,95),"is_weekly_search_trend":True,"confidence_score":random.randint(85,98)})
    if not res:
        raise RuntimeError(f"No stories from {url} - NO FALLBACK")
    return res

def fetch_reddit_free_force():
    out=[]
    for url in ["https://www.reddit.com/r/worldnews/hot.json?limit=10","https://www.reddit.com/r/news/hot.json?limit=10"]:
        r=pro_fetch(url, timeout=12, retries=10)
        data=r.json()
        for child in data.get('data',{}).get('children',[])[:5]:
            t=clean_id(child['data'].get('title',''))
            if len(t)>10:
                out.append({"title":t,"query":t,"url":"https://reddit.com"+child['data'].get('permalink',''),"source":"reddit_free","search_potential_score":85,"is_weekly_search_trend":True,"confidence_score":88})
    if not out:
        raise RuntimeError("Reddit empty - NO FALLBACK")
    return out

def fetch_youtube_free_force():
    import yt_dlp
    ydl_opts={'quiet':True,'extract_flat':True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info=ydl.extract_info("ytsearch5:breaking news USA today", download=False)
        out=[]
        for e in info.get('entries',[])[:5]:
            t=clean_id(e.get('title',''))
            out.append({"title":t,"query":t,"url":f"https://youtube.com/watch?v={e.get('id','')}","source":"youtube_free","search_potential_score":90,"is_weekly_search_trend":True,"confidence_score":90})
        if not out:
            raise RuntimeError("YouTube empty - NO FALLBACK")
        return out

def predict_7day_search_ai_force(topic):
    prompt=f"Predict next 7 days search for {topic}. Return JSON with seo_youtube_title under 60 chars high CTR, title_with_hashtag, description with hashtags, hashtags, tags, target_countries."
    for attempt in range(10):
        try:
            time.sleep(random.uniform(0.05,0.3))
            import os
            api_key=os.getenv("GEMINI_API_KEY")
            if not api_key: raise RuntimeError("GEMINI_API_KEY missing - NO FALLBACK")
            from google import genai
            client=genai.Client(api_key=api_key)
            resp=client.models.generate_content(model="gemini-2.0-flash", contents=prompt+f" cb={random.randint(1000,9999)}")
            text=getattr(resp,'text','')
            m=re.search(r'\{.*\}',text,re.DOTALL)
            if m: return json.loads(m.group())
        except Exception as e:
            print(f"[RESEARCH PRO] Gemini attempt {attempt} fail {e} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError("Gemini failed after 10 attempts - NO FALLBACK")

def research_god_main():
    print("[RESEARCH GOD] 45 sec scan - NO FALLBACK - FORCE - PRO HACKER")
    all_news=[]
    feeds=["https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en","http://feeds.reuters.com/reuters/topNews"]
    start=time.time()
    with ThreadPoolExecutor(max_workers=10) as ex:
        futs={ex.submit(pro_fetch_wire_force, url):url for url in feeds}
        futs.update({ex.submit(fetch_reddit_free_force):"reddit", ex.submit(fetch_youtube_free_force):"youtube"})
        for f in as_completed(futs):
            if time.time()-start>45: break
            d=f.result() # No fallback, will raise if fails
            all_news.extend(d)
    seen=set(); dedup=[]
    for it in all_news:
        k=it['title'].lower()
        if k not in seen:
            seen.add(k); dedup.append(it)
    dedup.sort(key=lambda x:x.get('search_potential_score',0), reverse=True)
    enriched=[]
    for s in dedup[:10]:
        seo=predict_7day_search_ai_force(s['title'])
        s.update(seo); enriched.append(s)
    if not enriched:
        raise RuntimeError("No enriched stories - NO FALLBACK")
    print(f"[RESEARCH GOD] Found {len(enriched)} FORCE")
    return enriched
