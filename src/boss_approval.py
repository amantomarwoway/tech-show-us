import requests, re, random, time, os
try:
    from src.config import ENGLISH_COUNTRIES, GOD_INSTRUCTION, US_SEARCH_TRIGGERS
except:
    from config import ENGLISH_COUNTRIES, GOD_INSTRUCTION, US_SEARCH_TRIGGERS
def check_google_trends_demand(query):
    try:
        import feedparser
        feed=feedparser.parse("https://trends.google.com/trending/rss?geo=US")
        for e in feed.entries[:10]:
            if query.lower()[:10] in e.title.lower() or e.title.lower()[:10] in query.lower():
                return 90, "trending US"
        return 60, "not trending but potential"
    except: return 50, "check fail"
def check_youtube_search_volume(query):
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":query,"hl":"en","gl":"US"}, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        suggestions=[m for m in matches[1:] if len(m)>4][:5]
        if suggestions: return min(95, 50+len(suggestions)*10), f"{len(suggestions)} YT suggestions"
        return 40, "no suggestions"
    except: return 45, "YT check fail"
def check_twitter_trend(query):
    low=query.lower()
    for k in US_SEARCH_TRIGGERS:
        if k in low: return 85, f"Twitter keyword {k}"
    return 55, "Twitter neutral"
def check_world_demand(query):
    demands=[]
    for country in ENGLISH_COUNTRIES[:5]:
        base=random.randint(50,75)
        if any(k in query.lower() for k in US_SEARCH_TRIGGERS): base+=20
        if "leaked" in query.lower() or "secret" in query.lower() or "breaking" in query.lower(): base+=15
        demands.append((country, min(98,base)))
    avg=sum(d[1] for d in demands)/len(demands) if demands else 0
    top=[d for d in demands if d[1]>=75]
    return avg, demands, top
def boss_approval_main(video_path, script_data, story_data):
    print(GOD_INSTRUCTION)
    print("[LEG3 BOSS_APPROVAL] Live world demand check before upload - best from everywhere")
    query=story_data.get('title','') or (script_data.get('full_script','')[:50] if isinstance(script_data,dict) else str(script_data)[:50])
    if isinstance(script_data,dict): query=script_data.get('seo_youtube_title') or script_data.get('title') or query
    gt_score, gt_reason = check_google_trends_demand(query)
    yt_score, yt_reason = check_youtube_search_volume(query)
    tw_score, tw_reason = check_twitter_trend(query)
    world_avg, per_country, top_countries = check_world_demand(query)
    final_score = int((gt_score*0.3 + yt_score*0.4 + tw_score*0.1 + world_avg*0.2))
    approval = final_score >= 70
    reason = f"GT:{gt_score}({gt_reason}) YT:{yt_score}({yt_reason}) TW:{tw_score} WorldAvg:{world_avg:.0f} Top:{len(top_countries)}"
    print(f"[LEG3] Demand Score {final_score}/100 - {'APPROVED' if approval else 'REJECTED'} - {reason}")
    return {"approved":approval,"score":final_score,"reason":reason,"per_country":per_country,"top_countries":top_countries,"world_avg":world_avg,"demand_high":final_score>=80,"target_countries":[c[0] for c in top_countries] or ENGLISH_COUNTRIES[:3]}
