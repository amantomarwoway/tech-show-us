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

        recency_score = max(0, 1 - (recency_hours / 24))  # 24h me decay

        # --- FIX 2: source_count ka fallback ---
        source_count = s.get('source_count')
        if source_count is None:
            all_src = s.get('all_sources') or s.get('sources') or [s.get('url','')]
            source_count = len(all_src)
        source_score = min(source_count / 3.0, 1.0)

        # --- FIX 3: reliability ka fallback ---
        reliability_score = s.get('reliability', 0.8)  # default 0.8

        # --- FIX 4: all_sources ka fallback ---
        dup_score = len(s.get('all_sources', []) or []) / 5.0

        w = WEIGHTS
        s['trend_score'] = (
            recency_score * w.get('recency', 0.4) +
            source_score * w.get('source_count', 0.2) +
            reliability_score * w.get('reliability', 0.3) +
            dup_score * w.get('duplicate_freq', 0.1)
        )

    return sorted(stories, key=lambda x: x.get('trend_score', 0), reverse=True)
