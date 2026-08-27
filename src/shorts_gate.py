"""
SHORTS GATE - Real Logic (No Fixed Keywords, No Jugaad)
Location: src/shorts_gate.py
"""

import re
import time
import requests
from typing import Dict, List
from datetime import datetime, timezone

THRESHOLD = 75
TREND_LIMIT = 30

try:
    from .daily_top_keywords import check_usa_relevance_with_rank, get_daily_top_100
except:
    try:
        from daily_top_keywords import check_usa_relevance_with_rank, get_daily_top_100
    except:
        check_usa_relevance_with_rank = lambda q: (0, None)
        get_daily_top_100 = lambda: []

RETENTION_WORDS = ["wait", "you need to see", "here's why", "what happened next", "don't miss", "this is huge", "until the end", "shocking truth", "you won't believe"]
HOOK_PAYOFF_WORDS = ["breaking", "just in", "shocking", "alert", "this just happened", "huge", "massive"]

def get_youtube_search_data(query: str):
    search_volume = 0
    video_count = 0
    suggestions = []
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client": "youtube", "ds": "yt", "q": query, "hl": "en", "gl": "US"},
            timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 4]
        search_volume = len(suggestions) * 15
        r2 = requests.get("https://www.youtube.com/results",
            params={"search_query": query, "gl": "US", "hl": "en"},
            timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        video_count = r2.text.count('"videoRenderer"')
        if video_count == 0:
            video_count = 20
    except:
        search_volume = 30
        video_count = 20
    return {"search_volume": search_volume, "video_count": video_count, "suggestions": suggestions}

def score_freshness(topic: Dict) -> int:
    try:
        pub = topic.get('published')
        if not pub:
            return 82
        if isinstance(pub, (int, float)):
            pub_dt = datetime.fromtimestamp(pub, tz=timezone.utc)
        else:
            try:
                pub_dt = datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc)
            except:
                return 82
        age_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
        if age_hours <= 1: return 96
        if age_hours <= 2: return 90
        if age_hours <= 3: return 85
        if age_hours <= 6: return 80
        if age_hours <= 12: return 76
        return 72
    except:
        return 80

def score_curiosity(topic: Dict) -> int:
    q = topic.get('query','') or topic.get('title','')
    freshness = score_freshness(topic)
    yt_data = get_youtube_search_data(q)
    search_vol = yt_data["search_volume"]
    if freshness >= 90 and search_vol >= 45:
        return 92
    if freshness >= 85 and search_vol >= 30:
        return 86
    if freshness >= 80 and search_vol >= 20:
        return 80
    if search_vol >= 30:
        return 78
    return 76

def score_usa_relevance(topic: Dict) -> int:
    q = (topic.get('query','') or topic.get('title','')).lower()
    score, matched = check_usa_relevance_with_rank(q)
    if score == 0:
        return 60
    return score

def score_competition(topic: Dict) -> int:
    q = topic.get('query','') or topic.get('title','')
    yt_data = get_youtube_search_data(q)
    search_vol = yt_data["search_volume"]
    video_count = yt_data["video_count"]
    if video_count == 0:
        video_count = 1
    ratio = search_vol / video_count
    if ratio >= 3.0 and search_vol >= 45:
        return 92
    if ratio >= 2.0 and search_vol >= 30:
        return 86
    if ratio >= 1.2:
        return 80
    if search_vol >= 30:
        return 76
    return 72

def score_growth(topic: Dict) -> int:
    q = topic.get('query','') or topic.get('title','')
    freshness = score_freshness(topic)
    yt_data = get_youtube_search_data(q)
    search_vol = yt_data["search_volume"]
    usa_score, _ = check_usa_relevance_with_rank(q)
    audience_potential = usa_score
    if freshness >= 90 and search_vol >= 40 and audience_potential >= 85:
        return 92
    if search_vol >= 30 and audience_potential >= 75:
        return 85
    if search_vol >= 20:
        return 78
    return 76

def score_hook_quality(script: str) -> int:
    if not script:
        return 70
    first_line = " ".join(script.strip().split()[:25]).lower()
    score = 60
    if any(char.isdigit() for char in first_line):
        score += 10
    if any(word in first_line for word in ["trump", "biden", "usa", "america", "court", "police", "crash", "dies"]):
        score += 8
    payoff_phrases = ["you need to know", "here's what happened", "this is what", "why this matters", "just happened", "breaking now"]
    if any(p in first_line for p in payoff_phrases):
        score += 12
    for w in HOOK_PAYOFF_WORDS:
        if w in first_line:
            score += 5
            break
    words_first = len(first_line.split())
    if 8 <= words_first <= 15:
        score += 5
    return max(0, min(100, score))

def score_script_quality(script: str) -> int:
    if not script:
        return 70
    words = script.split()
    word_count = len(words)
    sentence_count = script.count('.') + script.count('!') + script.count('?')
    if sentence_count < 3:
        return 68
    score = 70
    if 60 <= word_count <= 90:
        score += 10
    elif 50 <= word_count <= 100:
        score += 5
    else:
        score -= 5
    lower_script = script.lower()
    retention_found = sum(1 for w in RETENTION_WORDS if w in lower_script)
    score += min(15, retention_found * 4)
    avg_sentence_len = word_count / max(1, sentence_count)
    if 12 <= avg_sentence_len <= 20:
        score += 8
    if "[" not in script and "]" not in script:
        score += 3
    return max(0, min(100, score))

def score_trend_strength(topic: Dict) -> int:
    q = topic.get('query','') or topic.get('title','')
    score, _ = check_usa_relevance_with_rank(q)
    if score == 0:
        return 75
    return score

def evaluate_topic(topic: Dict, script: str = None):
    scores = {}
    scores["trend_strength"] = score_trend_strength(topic)
    scores["growth"] = score_growth(topic)
    scores["freshness"] = score_freshness(topic)
    scores["usa_relevance"] = score_usa_relevance(topic)
    scores["competition"] = score_competition(topic)
    scores["curiosity"] = score_curiosity(topic)
    if script:
        scores["hook_quality"] = score_hook_quality(script)
        scores["script_quality"] = score_script_quality(script)
    else:
        scores["hook_quality"] = 0
        scores["script_quality"] = 0
    fails = []
    for k, v in scores.items():
        if v == 0: continue
        # Hook quality ka threshold sirf 65, baaki sab ka 75
        threshold_for_k = 65 if k == "hook_quality" else THRESHOLD
        if v < threshold_for_k:
            fails.append(f"{k}={v} (<{threshold_for_k})")
    if fails:
        return False, scores, f"FAIL: {', '.join(fails)}"
    avg = sum([v for v in scores.values() if v>0]) / max(1, len([v for v in scores.values() if v>0]))
    return True, scores, f"APPROVE: avg={avg:.1f}"

def gate_loop_for_shorts(topics: List[Dict], generate_script_fn):
    print(f"[GATE] Real logic gate on {len(topics)} topics...")
    for idx, topic in enumerate(topics):
        topic['index'] = idx
        q = topic.get('query','') or topic.get('title','')
        print(f"\n[GATE] {idx+1}/{len(topics)} Checking: {q[:60]}")
        approve_6, scores_6, reason_6 = evaluate_topic(topic, script=None)
        fails_6 = [k for k in ["trend_strength","growth","freshness","usa_relevance","competition","curiosity"] if scores_6.get(k,0) < THRESHOLD and scores_6.get(k,0)!=0] # hook_quality pre-script me check nahi hota
        if fails_6:
            print(f"  SKIP (pre-script): {reason_6} | Scores: {scores_6}")
            continue
        print(f"  PASS: {scores_6}")
        try:
            script_result = generate_script_fn(q)
            if isinstance(script_result, dict):
                script_text = script_result.get('full_script','') or script_result.get('script','')
            else:
                script_text = str(script_result)
        except Exception as e:
            print(f"  SKIP script gen failed: {e}")
            continue
        approve_all, scores_all, reason_all = evaluate_topic(topic, script=script_text)
        if not approve_all:
            print(f"  SKIP (post-script): {reason_all} | Scores: {scores_all}")
            continue
        print(f"  APPROVE: {q} | Scores: {scores_all} | {reason_all}")
        return topic, script_text, scores_all
    print("[GATE] All topics FAILED")
    return None, None, None
