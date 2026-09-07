"""
Shorts Gate - RETENTION + VALIDATION FACTORY GATE
Location: src/shorts_gate.py
Edits:
- Retention filter: 40 words lock (35-45) mandatory for 11-13 sec
- Validation Factory gate: behind closed doors, leaked, first to know, bold claim mandatory
- Twist-only check
- Anti-bot + existing logic preserved
- Threshold 70 + Bot friendly 60 preserved
"""
import re, time, requests, random
from typing import Dict, List
from datetime import datetime, timezone
THRESHOLD=70
BOT_FRIENDLY_THRESHOLD=60
TREND_LIMIT=30

# --- NEW RETENTION + VALIDATION CONSTANTS ---
RETENTION_WORDS_TARGET = 40
RETENTION_WORDS_MIN = 35
RETENTION_WORDS_MAX = 45
VALIDATION_MANDATORY_KEYWORDS = ["behind closed doors", "leaked", "secret", "inside"]
VALIDATION_FIRST_TO_KNOW = ["first to know", "first"]
BOLD_CLAIMS_LIST = ["this changes everything","you won't believe","shocked everyone","this is huge","nobody saw this coming","game changer","secret","changes everything"]

BANNED_NICHES = ["ipl","bcci","cricket","csk","mi vs","bollywood","bhojpuri","tamil movie","recipe","cooking","horoscope","astrology","lottery","crossword","obituary"]
def is_banned_niche(query: str) -> bool:
    q = query.lower()
    return any(b in q for b in BANNED_NICHES)

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
        # Anti-bot: random UA
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            "Mozilla/5.0 (X11; Linux x86_64)"
        ])
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":query,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":ua})
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
    accept=["signs","returns","announces","deal","contract","trade","injury","breaking","official","just in","signed","76ers","lakers","nba","nfl","exhibit 10","training camp","leaked","secret","behind closed doors"]
    if any(a in q for a in accept): score+=15
    if topic.get("search_volume",0)>=40: score+=10
    if "rising" in topic.get("growth","") or "breakout" in topic.get("growth",""): score+=5
    return min(95,score)

# ===== NEW VALIDATION FACTORY SCORES =====
def score_retention_filter(script):
    """RETENTION: 40 words lock for 11-13 sec"""
    if not script:
        return 0
    wc = len(script.split())
    if RETENTION_WORDS_MIN <= wc <= RETENTION_WORDS_MAX:
        return 95
    if 30 <= wc <= 50:
        return 80
    if 25 <= wc <= 60:
        return 65
    return 40

def score_validation_factory(script):
    """VALIDATION FACTORY: behind closed doors, leaked, first to know, bold claim"""
    if not script:
        return 0
    low = script.lower()
    score=50
    
    # Mandatory leak angle
    if any(k in low for k in ["behind closed doors", "leaked", "secret leak", "inside sources"]):
        score+=20
    elif "leak" in low or "secret" in low:
        score+=10
    
    # First to know effect
    if "first to know" in low:
        score+=15
    elif "first" in low and "know" in low:
        score+=10
    
    # Bold confident daave
    bold_found = sum(1 for b in BOLD_CLAIMS_LIST if b in low)
    if bold_found >=2:
        score+=15
    elif bold_found >=1:
        score+=10
    
    # Twist-only check
    if "but here's the crazy part" in low or "but here's" in low or "crazy part" in low:
        score+=5
    
    return min(100, score)

def score_hook_quality(script):
    """Loop Viral Hook + leak angle bonus"""
    if not script: return 75
    first = " ".join(script.strip().split()[:25])
    first_lower = first.lower()
    score = 70
    if len(first.split()) >= 5:
        score += 10
    viral_words = ["breaking","shocking","just","found","huge","massive","secret","hidden","insane","crazy","this","officially","just in","alert","leaked","behind closed doors"]
    if any(w in first_lower for w in viral_words):
        score += 15
    if "?" in first or "!" in first:
        score += 5
    # Bonus for secret leak in hook
    if "leaked" in first_lower or "secret" in first_lower:
        score += 5
    return max(0, min(100, score))

def score_script_quality(script):
    """Loop Viral Quality + 40 words bonus"""
    if not script: return 75
    words = script.split()
    wc = len(words)
    sc = script.count('.') + script.count('!') + script.count('?')
    if sc < 2:
        sc = 2
    score = 75
    # NEW: 40 words perfect for 11-13 sec retention
    if RETENTION_WORDS_MIN <= wc <= RETENTION_WORDS_MAX:
        score += 20
    elif 85 <= wc <= 110:
        score += 10
    elif 70 <= wc <= 120:
        score += 5
    else:
        score += 2
    lower = script.lower()
    if lower.count("you") >= 1:
        score += 5
    if "[" not in script and "]" not in script:
        score += 5
    first_words = [w.lower() for w in words[:3]]
    last_words = [w.lower() for w in words[-10:]]
    if any(fw in " ".join(last_words) for fw in first_words if len(fw) > 2):
        score += 10
    else:
        score += 3
    return max(0, min(100, score))

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
        # NEW: Retention + Validation Factory gate
        scores["retention_filter"]=score_retention_filter(script)
        scores["validation_factory"]=score_validation_factory(script)
        words = script.split()
        first3 = " ".join(words[:3]).lower()
        last10 = " ".join(words[-10:]).lower()
        is_loop = any(w in last10 for w in first3.split() if len(w)>2)
        scores["tacko_structure"]=90 if is_loop else 85
    else:
        scores["hook_quality"]=0; scores["script_quality"]=0; scores["retention_filter"]=0; scores["validation_factory"]=0
    fails=[]
    for k,v in scores.items():
        if v==0: continue
        if k=="bot_friendly": thresh=BOT_FRIENDLY_THRESHOLD
        elif k=="hook_quality": thresh=50
        elif k=="script_quality": thresh=60
        elif k=="tacko_structure": thresh=60
        elif k=="retention_filter": thresh=75  # NEW: 40 words mandatory
        elif k=="validation_factory": thresh=70  # NEW: leak + first to know mandatory
        elif k in ["filter_a","filter_b"]: thresh=60
        else: thresh=THRESHOLD
        if v<thresh: fails.append(f"{k}={v} (<{thresh})")
    if fails: return False, scores, f"FAIL: {', '.join(fails)}"
    avg=sum([v for v in scores.values() if v>0])/max(1,len([v for v in scores.values() if v>0]))
    return True, scores, f"APPROVE: avg={avg:.1f}"

def gate_loop_for_shorts(topics, generate_script_fn):
    topics_limited = topics[:3]
    print(f"[GATE FINAL FAST + RETENTION + VALIDATION FACTORY] Gate on {len(topics_limited)} topics - Filter A/B/C + Bot + Retention 40w + Validation leak/secret")
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
                fallback_text = f"{q} just leaked behind closed doors and changes everything. You won't believe this. First to know effect is huge. Wait till end. And that's why {q[:20]} just leaked"
                return topic, {"title": q[:60], "full_script": fallback_text, "viral_hook": "Breaking Update Leaked", "white_bar_text": "Secret Leaked Behind Doors"}, scores_6
            print(f"  SKIP script gen failed: {e}")
            continue
        approve_all, scores_all, reason_all=evaluate_topic(topic, script=script_text)
        if not approve_all:
            print(f"  SKIP post-script: {reason_all} | {scores_all}")
            # Debug validation
            if "retention_filter" in scores_all and scores_all["retention_filter"]<75:
                print(f"    -> RETENTION FAIL: {len(script_text.split())} words, need 35-45")
            if "validation_factory" in scores_all and scores_all["validation_factory"]<70:
                print(f"    -> VALIDATION FAIL: need leaked/behind closed doors + first to know + bold claim")
            continue
        print(f"  APPROVE: {q} | {scores_all} | {reason_all}")
        return topic, script_result if isinstance(script_result, dict) else script_text, scores_all
    print("[GATE] All topics FAILED - Retention/Validation")
    return None, None, None
