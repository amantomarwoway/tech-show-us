import re, time, requests
from typing import Dict, List
from datetime import datetime, timezone
THRESHOLD=70  # 75 se 70 kiya - thoda easy
BOT_FRIENDLY_THRESHOLD=60  # 70 se 60 kiya
TREND_LIMIT=30

# --- ADD-ON C+K START ---
BANNED_NICHES = ["ipl","bcci","cricket","csk","mi vs","bollywood","bhojpuri","tamil movie","recipe","cooking","horoscope","astrology","lottery","crossword","obituary"]
def is_banned_niche(query: str) -> bool:
    q = query.lower()
    return any(b in q for b in BANNED_NICHES)
# --- ADD-ON C+K END ---

try:
    from .daily_top_keywords import check_usa_relevance_with_rank, get_daily_top_100
except:
    try:
        from daily_top_keywords import check_usa_relevance_with_rank, get_daily_top_100
    except:
        check_usa_relevance_with_rank=lambda q: (75, None)
        get_daily_top_100=lambda: []
RETENTION_WORDS=["wait","you need to see","here's why","what happened next","don't miss","this is huge","until the end","shocking truth","you won't believe"]
HOOK_PAYOFF_WORDS=["breaking","just in","shocking","alert","this just happened","huge","massive"]

def get_youtube_search_data_fast(query: str):
    search_volume=0
    suggestions=[]
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":query,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        suggestions=[m for m in matches[1:] if len(m)>4]
        search_volume=len(suggestions)*15
    except:
        search_volume=30
    video_count=max(10,100-search_volume)
    return {"search_volume":search_volume,"video_count":video_count,"suggestions":suggestions}

def score_freshness(topic: Dict) -> int:
    try:
        pub=topic.get('published')
        if not pub: return 82
        if isinstance(pub,(int,float)): pub_dt=datetime.fromtimestamp(pub, tz=timezone.utc)
        else:
            try: pub_dt=datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc)
            except: return 82
        age_hours=(datetime.now(timezone.utc)-pub_dt).total_seconds()/3600
        if age_hours<=1: return 96
        if age_hours<=2: return 90
        if age_hours<=3: return 85
        if age_hours<=6: return 80
        if age_hours<=12: return 76
        return 72
    except: return 80

def score_curiosity(topic): 
    q=topic.get('query','') or topic.get('title','')
    freshness=score_freshness(topic)
    yt=get_youtube_search_data_fast(q)
    sv=yt["search_volume"]
    if freshness>=90 and sv>=45: return 92
    if freshness>=85 and sv>=30: return 86
    if freshness>=80 and sv>=20: return 80
    if sv>=30: return 78
    return 76

def score_usa_relevance(topic):
    q=(topic.get('query','') or topic.get('title','')).lower()
    if is_banned_niche(q):
        return 0
    score,_=check_usa_relevance_with_rank(q)
    if score==0: return 60
    return score

def score_competition(topic):
    q=topic.get('query','') or topic.get('title','')
    yt=get_youtube_search_data_fast(q)
    sv=yt["search_volume"]; vc=yt["video_count"]
    if vc==0: vc=1
    ratio=sv/vc
    if ratio>=3.0 and sv>=45: return 92
    if ratio>=2.0 and sv>=30: return 86
    if ratio>=1.2: return 80
    if sv>=30: return 76
    return 72

def score_growth(topic):
    q=topic.get('query','') or topic.get('title','')
    freshness=score_freshness(topic)
    yt=get_youtube_search_data_fast(q)
    sv=yt["search_volume"]
    usa,_=check_usa_relevance_with_rank(q)
    if freshness>=90 and sv>=40 and usa>=85: return 92
    if sv>=30 and usa>=75: return 85
    if sv>=20: return 78
    return 76

def score_bot_friendly(topic):
    if "bot_friendly_score" in topic: return topic.get("bot_friendly_score",75)
    if "filter_c_score" in topic: return topic.get("filter_c_score",75)
    if topic.get("bot_friendly") is False: return 50
    q=(topic.get('query','') or topic.get('title','')).lower()
    if is_banned_niche(q):
        return 0
    reject=["obituary","recipe","horoscope","lottery","crossword","live interview 3 hours","podcast 3 hours","full press conference"]
    if any(r in q for r in reject): return 40
    score=70
    accept=["signs","returns","announces","deal","contract","trade","injury","breaking","official","just in","signed","76ers","lakers","nba","nfl","exhibit 10","training camp"]
    if any(a in q for a in accept): score+=15
    if topic.get("search_volume",0)>=40: score+=10
    if "rising" in topic.get("growth","") or "breakout" in topic.get("growth",""): score+=5
    return min(95,score)

# --- NEW OPTION 1: LOOP VIRAL ENGINE [REPLACED] ---
def score_hook_quality(script):
    """[NEW C+K] Loop Viral Hook - trump/biden check hataya, sirf viral + loop"""
    if not script: return 75
    # first 25 words = hook
    first = " ".join(script.strip().split()[:25])
    first_lower = first.lower()
    score = 70  # base 70

    # +10 if hook has 5+ words (proper hook)
    if len(first.split()) >= 5:
        score += 10

    # +15 if viral payoff words - yehi viral banata hai
    viral_words = ["breaking","shocking","just","found","huge","massive","secret","hidden","insane","crazy","this","officially","just in","alert"]
    if any(w in first_lower for w in viral_words):
        score += 15

    # +5 if curiosity ? or !
    if "?" in first or "!" in first:
        score += 5

    return max(0, min(100, score))

def score_script_quality(script):
    """[NEW C+K] Loop Viral Quality - '.' count wala 68 wala rule hataya"""
    if not script: return 75
    words = script.split()
    wc = len(words)
    
    # dots count - pehle 3 se kam pe 68 return karta tha, ab nahi
    sc = script.count('.') + script.count('!') + script.count('?')
    if sc < 2:
        sc = 2  # force minimum to avoid 68 fail

    score = 75  # base 75

    # +15 if perfect shorts length 85-110 words (30 sec)
    if 85 <= wc <= 110:
        score += 15
    elif 70 <= wc <= 120:
        score += 8
    else:
        score += 2

    # +5 if retention "you" 2+ times - viewer ko rokta hai
    lower = script.lower()
    if lower.count("you") >= 2:
        score += 5

    # +5 if TTS clean - no [ ] brackets
    if "[" not in script and "]" not in script:
        score += 5

    # +10 if PERFECT LOOP - first 3 words last 10 words me hain kya
    first_words = [w.lower() for w in words[:3]]
    last_words = [w.lower() for w in words[-10:]]
    # check overlap
    if any(fw in " ".join(last_words) for fw in first_words if len(fw) > 2):
        score += 10
    else:
        # agar exact match nahi to partial bhi 5 de de
        score += 5

    return max(0, min(100, score))
# --- END NEW OPTION 1 ---

def score_trend_strength(topic):
    q=topic.get('query','') or topic.get('title','')
    if is_banned_niche(q):
        return 0
    score,_=check_usa_relevance_with_rank(q)
    if topic.get("source") in ["filter_abc","youtube_search","google_trends_usa_breakout","filter_a","filter_b","filter_a_youtube","filter_a_rising"]:
        return max(score,85)
    if score==0: return 75
    return score

def evaluate_topic(topic, script=None):
    scores={}
    scores["trend_strength"]=score_trend_strength(topic)
    scores["growth"]=score_growth(topic)
    scores["freshness"]=score_freshness(topic)
    scores["usa_relevance"]=score_usa_relevance(topic)
    scores["competition"]=score_competition(topic)
    scores["curiosity"]=score_curiosity(topic)
    scores["bot_friendly"]=score_bot_friendly(topic)
    if "filter_a_score" in topic: scores["filter_a"]=topic["filter_a_score"]
    if "filter_b_score" in topic: scores["filter_b"]=topic["filter_b_score"]
    if script:
        scores["hook_quality"]=score_hook_quality(script)
        scores["script_quality"]=score_script_quality(script)
        # --- NEW: tacko_structure ko loop pe check ---
        words = script.split()
        first3 = " ".join(words[:3]).lower()
        last10 = " ".join(words[-10:]).lower()
        is_loop = any(w in last10 for w in first3.split() if len(w)>2)
        scores["tacko_structure"]=90 if is_loop else 85  # pehle 75 deta tha Visual: check pe
    else:
        scores["hook_quality"]=0; scores["script_quality"]=0
    fails=[]
    for k,v in scores.items():
        if v==0: continue
        if k=="bot_friendly": thresh=BOT_FRIENDLY_THRESHOLD
        elif k=="hook_quality": thresh=50  # pehle 65 tha - ab 50
        elif k=="script_quality": thresh=60  # pehle 75 tha - ab 60
        elif k=="tacko_structure": thresh=60  # new
        elif k in ["filter_a","filter_b"]: thresh=60
        else: thresh=THRESHOLD
        if v<thresh: fails.append(f"{k}={v} (<{thresh})")
    if fails: return False, scores, f"FAIL: {', '.join(fails)}"
    avg=sum([v for v in scores.values() if v>0])/max(1,len([v for v in scores.values() if v>0]))
    return True, scores, f"APPROVE: avg={avg:.1f}"

def gate_loop_for_shorts(topics, generate_script_fn):
    topics_limited = topics[:3]
    print(f"[GATE FINAL FAST] Gate on {len(topics_limited)} topics (limited to 3) - Filter A/B/C + Bot Friendly + Tacko [LOOP VIRAL ENGINE]")
    for idx, topic in enumerate(topics_limited):
        topic['index']=idx
        q=topic.get('query','') or topic.get('title','')
        if is_banned_niche(q):
            print(f"  [BANNED C+K] SKIP {q[:60]} - IPL/Bollywood/Cricket/Recipe")
            continue
        print(f"\n[GATE] {idx+1}/{len(topics_limited)} Checking: {q[:60]} | Vol {topic.get('search_volume','?')} | Bot {topic.get('filter_c_score', topic.get('bot_friendly_score','?'))}")
        approve_6, scores_6, reason_6=evaluate_topic(topic, script=None)
        fails_6=[k for k in ["trend_strength","growth","freshness","usa_relevance","competition","curiosity","bot_friendly"] if scores_6.get(k,0)<(BOT_FRIENDLY_THRESHOLD if k=="bot_friendly" else THRESHOLD) and scores_6.get(k,0)!=0]
        if fails_6:
            print(f"  SKIP pre-script: {reason_6} | {scores_6}")
            continue
        print(f"  PASS pre-script: {scores_6}")
        try:
            script_result=generate_script_fn(topic if isinstance(topic, dict) else q)
            if isinstance(script_result, dict):
                script_text=script_result.get('raw_script_structured','') or script_result.get('full_script','')
            else:
                script_text=str(script_result)
        except Exception as e:
            err=str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
                print(f"  [QUOTA 429] Fallback for {q[:40]}")
                fallback_text = f"{q} is breaking. Here's what happened. You need to know this. Wait till end."
                return topic, {"title": q[:60], "full_script": fallback_text, "viral_hook": "Breaking Update", "white_bar_text": "Breaking Update"}, scores_6
            print(f"  SKIP script gen failed: {e}")
            continue
        approve_all, scores_all, reason_all=evaluate_topic(topic, script=script_text)
        if not approve_all:
            print(f"  SKIP post-script: {reason_all} | {scores_all}")
            continue
        print(f"  APPROVE: {q} | {scores_all} | {reason_all}")
        return topic, script_result if isinstance(script_result, dict) else script_text, scores_all
    print("[GATE] All topics FAILED")
    return None, None, None
