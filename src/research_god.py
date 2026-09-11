import feedparser, requests, re, json, random, time
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
try:
    from src.config import REUTERS_FEEDS, GOOGLE_NEWS_WIRE, MAINSTREAM_BLOCK, FETCH_WINDOW_MINUTES, US_SEARCH_TRIGGERS, WORLD_VIRAL_TAGS, ENGLISH_COUNTRIES, GOD_INSTRUCTION
except:
    from config import REUTERS_FEEDS, GOOGLE_NEWS_WIRE, MAINSTREAM_BLOCK, FETCH_WINDOW_MINUTES, US_SEARCH_TRIGGERS, WORLD_VIRAL_TAGS, ENGLISH_COUNTRIES, GOD_INSTRUCTION
BANNED = ["ipl","bcci","cricket","bollywood","bhojpuri","recipe","horoscope"]
def clean_id(t):
    if not t: return ""
    t = re.sub(r'/m/[a-z0-9]+','',t,flags=re.I)
    t = re.sub(r'\b[mM][0-9][a-z0-9]+\b','',t)
    t = re.sub(r'\s+',' ',t).strip()
    return t
def within_45min(entry):
    try:
        import time as tm
        pub=None
        if hasattr(entry,'published_parsed') and entry.published_parsed:
            pub=datetime.fromtimestamp(tm.mktime(entry.published_parsed), tz=timezone.utc)
        elif hasattr(entry,'updated_parsed') and entry.updated_parsed:
            pub=datetime.fromtimestamp(tm.mktime(entry.updated_parsed), tz=timezone.utc)
        else: return True
        return (datetime.now(timezone.utc)-pub) <= timedelta(minutes=FETCH_WINDOW_MINUTES)
    except: return True
def is_blocked(url):
    if not url: return False
    return any(d in url.lower() for d in MAINSTREAM_BLOCK)
def search_potential(title):
    low=title.lower(); score=0
    for kw in US_SEARCH_TRIGGERS:
        if kw in low: score+=12
    for qw in ["how","what","why","update","explained","ban","order","ruling","leaked","secret"]:
        if qw in low: score+=15
    return score
def is_7day_velocity(title):
    return search_potential(title) >= 30
def fetch_feed(url):
    try:
        feed=feedparser.parse(url); res=[]
        for e in feed.entries[:12]:
            if not within_45min(e): continue
            title=clean_id(getattr(e,'title',''))
            if len(title)<8 or any(b in title.lower() for b in BANNED): continue
            link=getattr(e,'link','')
            if is_blocked(link): continue
            score=search_potential(title)
            if score<10: continue
            res.append({"title":title,"query":title,"url":link,"source":"reuters_wire" if "reuters" in url else "google_news_wire","published":time.gmtime(),"summary":title,"search_potential_score":score,"is_weekly_search_trend":True,"confidence_score":min(98,60+score),"is_wire":True})
        return res
    except: return []
def fetch_all_wire():
    all_news=[]; feeds=REUTERS_FEEDS+GOOGLE_NEWS_WIRE
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs={ex.submit(fetch_feed,url):url for url in feeds}
        for f in as_completed(futs):
            try:
                d=f.result()
                if d: all_news.extend(d)
            except: continue
    seen=set(); dedup=[]
    for it in all_news:
        k=it['title'].lower().strip()
        if k not in seen and len(k)>5:
            seen.add(k); dedup.append(it)
    dedup.sort(key=lambda x:x.get('search_potential_score',0),reverse=True)
    return dedup[:20]
def get_world_seo_pack(topic, url=""):
    base=clean_id(topic)[:80]
    title_with_hashtag = f"{base} #Breaking #Viral"
    title_without = base
    hashtags = ["#breakingnews","#worldnews","#viralnews","#USANews","#globalupdate","#newsupdate","#trending","#explained"]
    low=base.lower()
    if "trump" in low: hashtags+=["#trump","#whitehouse"]
    if "supreme" in low: hashtags+=["#supremecourt"]
    if "leaked" in low: hashtags+=["#leaked","#secret"]
    description = f"{base} - Full update explained. Breaking world news for {', '.join(ENGLISH_COUNTRIES[:5])} audience.\n\nWhat happened? Why it matters? Next 7 days search trend.\n\n{' '.join(hashtags)}\n\n#shorts #news #world"
    tags = WORLD_VIRAL_TAGS + [w.strip('#') for w in hashtags[:10]] + ["breaking news US","world news today","news explained","global news","viral news US","English news"]
    tags = list(dict.fromkeys(tags))[:15]
    return {"seo_youtube_title":base[:60],"title_with_hashtag":title_with_hashtag[:95],"title_without_hashtag":title_without[:60],"hashtags":hashtags,"description":description,"tags":tags,"target_countries":ENGLISH_COUNTRIES,"is_world_viral":True}
def research_god_main():
    print(GOD_INSTRUCTION)
    print("[LEG1 RESEARCH_GOD] Fetching Wire 45min + Velocity + World SEO - Best from everywhere")
    stories=fetch_all_wire()
    if not stories:
        try:
            feed=feedparser.parse("https://trends.google.com/trending/rss?geo=US")
            for e in feed.entries[:5]:
                t=clean_id(e.title)
                if len(t)>5:
                    stories.append({"title":t,"query":t,"url":"","source":"google_trends_fallback","search_potential_score":50,"is_weekly_search_trend":True,"confidence_score":75})
        except: pass
    # FINAL FALLBACK - Never return empty - World breaking news backup
    if not stories:
        print("[LEG1] Wire empty, using WORLD VIRAL FALLBACK - never empty")
        fallback_topics = [
            "White House Executive Order Leaked Behind Closed Doors",
            "Supreme Court Shocking Ruling Changes Everything USA",
            "Pentagon Secret Deal Exposed World Reacts",
            "Breaking US Economy Update Leaked Inside Sources",
            "Trump White House Breaking News Just Leaked"
        ]
        import random
        for topic in random.sample(fallback_topics, 3):
            stories.append({"title":topic,"query":topic,"url":"","source":"world_viral_fallback","search_potential_score":80,"is_weekly_search_trend":True,"confidence_score":85})

    enriched=[]
    for s in stories:
        seo=get_world_seo_pack(s['title'], s.get('url',''))
        s.update(seo); enriched.append(s)
    print(f"[LEG1] Found {len(enriched)} stories with world SEO")
    return enriched
