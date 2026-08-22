import time, math
import config

def score_and_rank(stories):
    now = time.time()
    for s in stories:
        recency_hours = (now - time.mktime(s['published'])) / 3600
        recency_score = max(0, 1 - (recency_hours/24)) # 24h me decay
        source_score = s['source_count'] / 3.0
        reliability_score = s['reliability']
        dup_score = len(s.get('all_sources',[])) / 5.0

        w = config.WEIGHTS
        s['trend_score'] = (recency_score * w['recency'] +
                            source_score * w['source_count'] +
                            reliability_score * w['reliability'] +
                            dup_score * w['duplicate_freq'])

    return sorted(stories, key=lambda x: x['trend_score'], reverse=True)
