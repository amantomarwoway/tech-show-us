import os, random, time, requests
from src.config import USER_AGENTS, pro_headers, pro_fetch, WORLD_50_COUNTRIES

def check_live_demand_50_countries_force(topic):
    scores={}
    bearer=os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer:
        raise RuntimeError("TWITTER_BEARER_TOKEN missing - NO FALLBACK")
    for country in WORLD_50_COUNTRIES[:50]:
        demand=0
        for attempt in range(10):
            try:
                time.sleep(random.uniform(0.05,0.2))
                url=f"https://api.twitter.com/2/tweets/search/recent?query={topic} lang:en&max_results=10"
                h={"Authorization":f"Bearer {bearer}", **pro_headers()}
                r=requests.get(url+f"&cb={random.randint(1000,9999)}", headers=h, timeout=10)
                if r.status_code==200:
                    count=len(r.json().get('data',[]))
                    demand=min(99, 70+count*3)
                    break
                else:
                    print(f"[BOSS PRO] Twitter {r.status_code} retry {attempt} - FORCE")
                    time.sleep((2**attempt)+random.uniform(0,0.5))
            except Exception as e:
                print(f"[BOSS PRO] Twitter fail {e} attempt {attempt} - FORCE RETRY")
                time.sleep((2**attempt)+random.uniform(0,0.5))
        if demand==0:
            raise RuntimeError(f"Twitter demand 0 for {country} - NO FALLBACK - FORCE")
        scores[country]=min(99, demand)
    avg=sum(scores.values())/len(scores)
    return avg, scores

def calculate_ctr_score_force(title):
    ctr=70
    if any(k in title.lower() for k in ["leaked","secret","behind closed doors","shocking","breaking","exposed"]): ctr+=15
    if len(title)<=60: ctr+=10
    ctr+=random.randint(0,10)
    return min(99, ctr)

def boss_approval_main(video_path, editor_data, cand):
    print("[BOSS GOD] 2 min before upload - 50+ countries - NO FALLBACK - FORCE")
    topic=cand.get('title','') or editor_data.get('seo_youtube_title','')
    avg_demand, country_scores = check_live_demand_50_countries_force(topic)
    ctr = calculate_ctr_score_force(editor_data.get('seo_youtube_title','') or topic)
    final = (avg_demand*0.6 + ctr*0.4)
    print(f"[BOSS PRO] Demand {avg_demand:.1f} CTR {ctr} Final {final:.1f} - NO FALLBACK")
    if final < 90:
        try:
            if video_path and os.path.exists(video_path): os.remove(video_path)
        except: pass
        return {"approved":False, "score":final, "reason":f"Low demand {avg_demand:.1f} CTR {ctr}", "country_scores":country_scores}
    return {"approved":True, "score":final, "target_countries":list(country_scores.keys())[:10], "country_scores":country_scores, "ctr":ctr, "demand":avg_demand}
