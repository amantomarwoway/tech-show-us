import time, math

try:
    import config
    WEIGHTS = config.WEIGHTS
except:
    # Agar config.py me WEIGHTS nahi hai toh default
    WEIGHTS = {
        'recency': 0.4,
        'source_count': 0.2,
        'reliability': 0.3,
        'duplicate_freq': 0.1
    }

# NEW - Searchable boost lists
US_BOOST = ["usa", "us", "america", "texas", "california", "florida", "new york", "washington", "trump", "biden", "nasa", "fbi", "court", "election", "iphone", "tesla", "ai", "google", "openai"]
SEARCH_BOOST = ["why", "how", "what happened", "explained", "crisis", "breaking", "update", "leak", "ban", "banned", "price", "crash", "launches", "arrested", "just in"]
BORING_REJECT = ["obituary", "dies", "dead", "recipe", "horoscope", "lottery", "crossword"]

def score_and_rank(stories):
    now = time.time()
    for s in stories:
        # --- FIX 1: published ka fallback ---
        try:
            pub = s.get('published')
            if pub is None:
                recency_hours = 0  # agar time nahi hai toh abhi ki news maan le
            elif isinstance(pub, (int, float)):
                recency_hours = (now - pub) / 3600
            else:
                # agar time.struct_time hai toh
                recency_hours = (now - time.mktime(pub)) / 3600
        except:
            recency_hours = 0

        # Recency score: jitni nayi utna high (0-100)
        recency_score = max(0, 100 - recency_hours * 2)

        # Source reliability
        reliability_score = s.get('reliability', 0.7) * 100

        # --- NEW FIX: Google Trends USA ko sabse zyada priority ---
        source = s.get('source', '').lower()
        title = (s.get('title') or '').lower()

        # 1. Boring topics ko 0 kar do - views nahi ayenge
        if any(b in title for b in BORING_REJECT):
            s['trending_score'] = 0
            continue

        base_score = 0

        if "google_trends_usa" in source:
            base_score += 80  # direct trending boost
            # Google trends ka recency hamesha 100
            recency_score = 100
        else:
            base_score += 20

        # 2. US relevance boost (US audience ke liye)
        if any(k in title for k in US_BOOST):
            base_score += 20

        # 3. Searchable intent boost (log YouTube pe ye search karte hain)
        if any(k in title for k in SEARCH_BOOST):
            base_score += 25

        # 4. Ideal title length for search (4-10 words best CTR)
        word_len = len(title.split())
        if 4 <= word_len <= 10:
            base_score += 10

        # Final weighted score
        final = (
            WEIGHTS['recency'] * recency_score +
            WEIGHTS['reliability'] * reliability_score +
            0.5 * base_score  # extra searchable boost
        )

        # Bonus: exact trending query length
        if "google_trends" in source:
            final += 30

        s['trending_score'] = min(100, final)

    # Sort high to low
    ranked = sorted(stories, key=lambda x: x.get('trending_score', 0), reverse=True)

    # Sirf searchable wale rakho (score > 60) - low views wale hatao
    filtered = [r for r in ranked if r.get('trending_score', 0) > 40]

    # Agar filter ke baad kuch nahi bacha toh top 5 de do
    return filtered[:15] if filtered else ranked[:5]
