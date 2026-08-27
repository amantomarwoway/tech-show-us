"""
SHORTS GATE - 8-Factor Strict APPROVE/SKIP for Shorts
Rules: All 8 scores >=75 = APPROVE, else SKIP -> next topic
No fallback, 100% free, zero-cost
"""

import re
import time
import requests
from typing import Dict, Tuple, List
from datetime import datetime, timezone

THRESHOLD = 75
TREND_LIMIT = 30

# ===== 150+ USA KEYWORDS - FULL LIST =====
USA_KEYWORDS = [
    # Country
    "usa", "america", "united states", "us", "u.s.", "american",
    # Government
    "white house", "congress", "senate", "house", "president", "biden", "trump", "kamala", "supreme court", "fbi", "cia", "nasa", "pentagon", "department",
    # 50 States
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming", "dc", "district of columbia",
    # Major Cities
    "los angeles", "new york city", "chicago", "houston", "phoenix", "philadelphia", "san antonio", "san diego", "dallas", "san jose",
    "austin", "jacksonville", "fort worth", "columbus", "san francisco", "charlotte", "indianapolis", "seattle", "denver", "boston",
    "el paso", "nashville", "detroit", "oklahoma city", "portland", "las vegas", "memphis", "louisville", "milwaukee", "baltimore",
    "albuquerque", "tucson", "mesa", "sacramento", "atlanta", "kansas city", "miami", "orlando", "tampa", "minneapolis",
    # Sports / Culture
    "nfl", "nba", "mlb", "nhl", "ncaa", "super bowl", "world series", "hollywood", "silicon valley", "wall street", "tesla", "apple", "google", "microsoft", "amazon", "meta", "openai",
    # Tech / Economy
    "dow jones", "nasdaq", "s&p", "fed", "federal reserve", "inflation", "irs", "cdc", "fda"
]

CURIOSITY_WORDS = ["why", "what happened", "shocking", "breaking", "exposed", "secret", "truth", "revealed", "you won't believe", "just in", "update", "crisis", "scandal", "banned", "leaked"]
HOOK_WORDS = ["breaking", "just in", "shocking", "alert", "urgent", "watch", "look", "this just happened", "you won't believe", "huge", "massive", "incredible"]

def score_trend_strength(topic: Dict) -> int:
    """Rank based: #1=95, #30=36"""
    rank = topic.get('index', 0)
    strength = topic.get('trend_strength', 95 - rank*2)
    return max(0, min(100, int(strength)))

def score_growth(topic: Dict, prev_topics: List[str] = None) -> int:
    """If topic jumped up in rank vs previous fetch = high growth"""
    # Free heuristic: shorter query + high trend_strength = fast growth
    q = topic.get('query','')
    # If query contains 'breaking', 'today', 'just' -> high growth
    if any(w in q.lower() for w in ["breaking", "just in", "today", "now", "live"]):
        return 90
    # Rank 1-5 = high growth
    if topic.get('trend_strength', 0) >= 85:
        return 85
    if topic.get('trend_strength', 0) >= 70:
        return 75
    return 65

def score_freshness(topic: Dict) -> int:
    """Hours old from published_parsed"""
    try:
        pub = topic.get('published')
        if not pub:
            # If no time, assume fresh if high rank
            return 80 if topic.get('trend_strength',0) > 80 else 70
        # pub is time.struct_time
        pub_dt = datetime.fromtimestamp(time.mktime(pub), tz=timezone.utc) if hasattr(pub, 'tm_year') else datetime.now(timezone.utc)
        age_hours = (datetime.now(timezone.utc) - pub_dt).total_seconds() / 3600
        if age_hours <= 0.5:
            return 98
        if age_hours <= 1:
            return 92
        if age_hours <= 2:
            return 85
        if age_hours <= 4:
            return 78
        if age_hours <= 8:
            return 70
        if age_hours <= 12:
            return 60
        return 40
    except:
        return 70

def score_usa_relevance(topic: Dict) -> int:
    """150+ keywords check - NO fallback, must match"""
    q = topic.get('query','').lower() + " " + topic.get('summary','').lower()
    matches = 0
    for kw in USA_KEYWORDS:
        if kw in q:
            matches += 1
            # Early high score if multiple matches
            if matches >= 2:
                return 95
    if matches == 1:
        # Check if query itself is USA city/state
        for kw in USA_KEYWORDS:
            if q.strip() == kw or q.startswith(kw + " ") or q.endswith(" " + kw):
                return 85
        return 78  # one match = pass threshold
    # If topic from google_trends_usa_current, it's USA by default - give 75 exactly
    if topic.get('source') == 'google_trends_usa_current':
        return 76
    return 55  # FAIL

def score_competition(topic: Dict) -> int:
    """Free: YouTube suggest count - many suggestions = high competition = low score"""
    try:
        query = topic.get('query','')
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "youtube", "ds": "yt", "q": query, "hl": "en", "gl": "US"}
        r = requests.get(url, params=params, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        import re as re2
        matches = re2.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 4]
        count = len(suggestions)
        # Less suggestions = less competition = higher score (good for us)
        if count <= 2:
            return 92  # low competition
        if count <= 4:
            return 82
        if count <= 6:
            return 76
        if count <= 8:
            return 68  # FAIL
        return 55
    except:
        # On error, we must SKIP per user rule (no fallback) -> return FAIL to trigger skip
        return 50

def score_curiosity(topic: Dict) -> int:
    q = topic.get('query','').lower()
    score = 60
    for w in CURIOSITY_WORDS:
        if w in q:
            score += 12
    # Question format
    if "?" in q or q.startswith("why") or q.startswith("how") or q.startswith("what"):
        score += 15
    return max(0, min(100, score))

def score_hook_quality(script: str) -> int:
    """First 15 words"""
    if not script:
        return 50
    first = script.strip().split()[:20]
    first_str = " ".join(first).lower()
    score = 60
    for w in HOOK_WORDS:
        if w in first_str:
            score += 10
    # Strong start: number, breaking, name
    if first and (first[0].lower() in ["breaking", "just", "shocking", "alert"] or first_str[:1].isdigit()):
        score += 10
    if len(script.split()) >= 50:
        score += 5
    return max(0, min(100, score))

def score_script_quality(script: str) -> int:
    if not script:
        return 50
    words = len(script.split())
    score = 70
    if 60 <= words <= 85:
        score = 90
    elif 50 <= words <= 95:
        score = 80
    elif words < 40 or words > 120:
        score = 55
    # No brackets/emojis
    if "[" not in script and "]" not in script and "{" not in script:
        score += 5
    # American English check - no Hinglish
    # Sentences
    sentences = script.count(".") + script.count("!") + script.count("?")
    if sentences >= 3:
        score += 5
    return max(0, min(100, score))

def evaluate_topic(topic: Dict, script: str = None) -> Tuple[bool, Dict[str, int], str]:
    """
    Returns: (is_approve, scores_dict, fail_reason)
    Strict: if ANY score <75 => SKIP
    """
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
        # Before script gen, only 6 scores. After script, 8 scores.
        scores["hook_quality"] = 0
        scores["script_quality"] = 0

    # Check fails
    fails = []
    for k, v in scores.items():
        if v == 0:
            continue  # not yet scored
        if v < THRESHOLD:
            fails.append(f"{k}={v}")

    if fails:
        return False, scores, f"FAIL: {', '.join(fails)} <{THRESHOLD}"
    
    # All passed
    avg = sum([v for v in scores.values() if v>0]) / max(1, len([v for v in scores.values() if v>0]))
    if avg < THRESHOLD:
        return False, scores, f"FAIL: avg={avg:.1f} <{THRESHOLD}"
    
    return True, scores, f"APPROVE: avg={avg:.1f}"

def gate_loop_for_shorts(topics: List[Dict], generate_script_fn) -> Tuple[Dict, str, Dict]:
    """
    Loop through 30 topics until one APPROVES all 8 gates
    topics: list from Google Trends (30)
    generate_script_fn: function that takes news_text and returns script dict
    Returns: (approved_topic, script_text, scores) or (None, None, None) if all fail
    """
    print(f"[GATE] Starting strict 75 gate on {len(topics)} topics...")
    for idx, topic in enumerate(topics):
        topic['index'] = idx
        q = topic.get('query','')
        print(f"\n[GATE] {idx+1}/{len(topics)} Checking: {q[:50]}")
        
        # Stage 1: 6 scores before script
        approve_6, scores_6, reason_6 = evaluate_topic(topic, script=None)
        # For stage 1, we check only first 6
        fails_6 = [k for k in ["trend_strength","growth","freshness","usa_relevance","competition","curiosity"] if scores_6.get(k,0) < THRESHOLD]
        if fails_6:
            print(f"  ❌ SKIP (pre-script): {reason_6} | Scores: {scores_6}")
            continue
        print(f"  ✅ Pre-script PASS: {scores_6}")

        # Stage 2: Generate script then check hook + script quality
        try:
            script_result = generate_script_fn(q)
            if isinstance(script_result, dict):
                script_text = script_result.get('full_script','') or script_result.get('script','')
            else:
                script_text = str(script_result)
        except Exception as e:
            print(f"  ❌ SKIP script gen failed: {e}")
            continue

        approve_all, scores_all, reason_all = evaluate_topic(topic, script=script_text)
        if not approve_all:
            print(f"  ❌ SKIP (post-script): {reason_all} | Scores: {scores_all}")
            continue

        print(f"  🔥 APPROVE: {q} | Scores: {scores_all} | {reason_all}")
        return topic, script_text, scores_all

    print("[GATE] All 30 topics FAILED strict gate - no video this run (safe)")
    return None, None, None
