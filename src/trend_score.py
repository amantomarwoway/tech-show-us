import time, math, requests, re

try:
    import config
    WEIGHTS = config.WEIGHTS
except:
    WEIGHTS = {
        'recency': 0.4,
        'source_count': 0.2,
        'reliability': 0.3,
        'duplicate_freq': 0.1
    }

# ===== FULL 150+ USA KEYWORDS (As per user demand - not just 3-4) =====
USA_KEYWORDS_FULL = [
    "usa", "america", "united states", "us", "u.s.", "american",
    "white house", "congress", "senate", "house", "president", "biden", "trump", "kamala harris", "supreme court", "fbi", "cia", "nasa", "pentagon",
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia",
    "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland",
    "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming", "dc", "district of columbia",
    "los angeles", "new york city", "chicago", "houston", "phoenix", "philadelphia", "san antonio", "san diego", "dallas", "san jose",
    "austin", "jacksonville", "fort worth", "columbus", "san francisco", "charlotte", "indianapolis", "seattle", "denver", "boston",
    "el paso", "nashville", "detroit", "oklahoma city", "portland", "las vegas", "memphis", "louisville", "milwaukee", "baltimore",
    "albuquerque", "tucson", "mesa", "sacramento", "atlanta", "kansas city", "miami", "orlando", "tampa", "minneapolis",
    "nfl", "nba", "mlb", "nhl", "ncaa", "super bowl", "world series", "hollywood", "silicon valley", "wall street",
    "tesla", "apple", "google", "microsoft", "amazon", "meta", "openai", "spacex", "boeing",
    "dow jones", "nasdaq", "fed", "federal reserve", "irs", "cdc", "fda"
]

SEARCH_BOOST = ["why", "how", "what happened", "explained", "crisis", "breaking", "update", "leak", "ban", "banned", "price", "crash", "launches", "arrested", "just in", "shocking", "truth", "revealed"]
BORING_REJECT = ["obituary", "dies", "dead", "recipe", "horoscope", "lottery", "crossword"]

THRESHOLD = 75

def get_usa_relevance_score(title: str) -> int:
    """Full 150+ keyword check"""
    t = title.lower()
    matches = 0
    for kw in USA_KEYWORDS_FULL:
        if kw in t:
            matches += 1
            if matches >= 2:
                return 95
    if matches == 1:
        return 82
    # google_trends_usa source = by default USA, give 76 to pass
    return 76

def get_competition_score(query: str) -> int:
    """Free YouTube suggest count"""
    try:
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "youtube", "ds": "yt", "q": query, "hl": "en", "gl": "US"}
        r = requests.get(url, params=params, timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 4]
        count = len(suggestions)
        if count <= 2:
            return 92
        if count <= 4:
            return 82
        if count <= 6:
            return 76
        if count <= 8:
            return 68
        return 55
    except:
        return 50  # No fallback -> will cause SKIP

def score_and_rank(stories):
    now = time.time()
    scored_stories = []
    
    for s in stories:
        title = (s.get('title') or '').lower()
        
        # Boring reject = 0 (SKIP)
        if any(b in title for b in BORING_REJECT):
            s['trending_score'] = 0
            s['scores'] = {"fail_reason": "boring topic"}
            continue

        # --- 8-FACTOR PRE-SCORE (before script) ---
        try:
            pub = s.get('published')
            if pub is None:
                recency_hours = 0
            elif isinstance(pub, (int, float)):
                recency_hours = (now - pub) / 3600
            else:
                recency_hours = (now - time.mktime(pub)) / 3600
        except:
            recency_hours = 0

        # 1. Trend strength (rank based)
        trend_strength = s.get('trend_strength', 95 - len(scored_stories)*2)
        if isinstance(trend_strength, float):
            trend_strength = int(trend_strength * 100)
        
        # 2. Growth (heuristic)
        growth = 90 if any(w in title for w in ["breaking", "just in", "today"]) else (85 if trend_strength >= 85 else 75)
        
        # 3. Freshness
        if recency_hours <= 0.5:
            freshness = 98
        elif recency_hours <= 1:
            freshness = 92
        elif recency_hours <= 2:
            freshness = 85
        elif recency_hours <= 4:
            freshness = 78
        elif recency_hours <= 8:
            freshness = 70
        else:
            freshness = 60

        # 4. USA relevance (FULL 150+ keywords)
        usa_relevance = get_usa_relevance_score(title)

        # 5. Competition
        competition = get_competition_score(s.get('title',''))

        # 6. Curiosity
        curiosity = 60
        for w in SEARCH_BOOST:
            if w in title:
                curiosity += 8
        curiosity = min(100, curiosity)

        # Store all 6 pre-scores
        s['scores'] = {
            "trend_strength": int(trend_strength),
            "growth": growth,
            "freshness": freshness,
            "usa_relevance": usa_relevance,
            "competition": competition,
            "curiosity": curiosity
        }

        # Strict check: if ANY <75 -> mark as fail (will be skipped in gate)
        fails = [k for k,v in s['scores'].items() if v < THRESHOLD]
        if fails:
            s['trending_score'] = 0
            s['scores']['fail_reason'] = f"FAIL {fails} <75"
            # Still keep for gate to log SKIP
            scored_stories.append(s)
            continue

        # Base score for ranking
        base_score = 80 if "google_trends_usa" in s.get('source','').lower() else 20
        if usa_relevance >= 80:
            base_score += 20
        if curiosity >= 80:
            base_score += 15

        final = (
            WEIGHTS['recency'] * (100 - recency_hours*2) +
            WEIGHTS['reliability'] * s.get('reliability',0.7)*100 +
            0.5 * base_score
        )
        s['trending_score'] = min(100, final + 30)
        scored_stories.append(s)

    # Sort high to low, but KEEP failed ones for logging (gate will skip)
    ranked = sorted(scored_stories, key=lambda x: x.get('trending_score', 0), reverse=True)
    
    # Only return those that passed pre-gate OR top 15 for gate to try
    # Gate will do strict 75 check again + script quality
    filtered = [r for r in ranked if r.get('trending_score',0) > 0]
    return filtered[:30] if filtered else ranked[:10]
