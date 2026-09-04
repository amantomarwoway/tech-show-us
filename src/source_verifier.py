from collections import defaultdict
import config
from datetime import datetime, timezone

def verify_stories(stories):
    grouped = defaultdict(list)
    for s in stories:
        key = s['title'].lower().strip()[:40]
        grouped[key].append(s)

    verified = []
    for key, group in grouped.items():
        if len(group) >= 2:
            sources = list(set([g['source'] for g in group]))
            if len(sources) >= 2:
                merged = group[0].copy()
                merged['all_sources'] = group
                merged['source_count'] = len(sources)
                merged['verification_score'] = min(0.95, 0.7 + len(sources)*0.1)
                verified.append(merged)
        # --- ADD-ON Problem 6 - E+I fix - google_news_us_live ko allow karo ---
        elif group[0]['source'] in ['reuters','apnews','gov', 'google_trends_usa', 'google_trends_usa_current', 'google_trends_official_rss', 'google_trends', 'google_news_us_live', 'google_trends_usa_breakout']:
        # --- END ---
            g = group[0].copy()
            g['all_sources'] = group
            g['source_count'] = 1
            if 'google_trends' in g['source'] or 'google_news_us_live' in g['source']:
                g['verification_score'] = 0.90
                g['single_source'] = False
                g['status'] = 'verified_trending' if 'trends' in g['source'] else 'verified_live_news'
            else:
                g['verification_score'] = 0.85
                g['single_source'] = True
                g['status'] = 'verified_single_official'
            verified.append(g)

    if not verified and stories:
        has_trends = any('google_trends' in s.get('source','') or 'google_news_us_live' in s.get('source','') for s in stories)
        if has_trends:
            for s in stories[:5]:
                g = s.copy()
                g['all_sources'] = [s]
                g['source_count'] = 1
                g['verification_score'] = 0.88
                g['status'] = 'trending_verified'
                g['single_source'] = False
                verified.append(g)

    return verified

def verify_story_single(story):
    result = verify_stories([story])
    if result:
        return {"verification_score": result[0]['verification_score'], "status": "verified", "matched_sources": result[0]['all_sources']}
    return {"verification_score": 0.88 if 'google_trends' in story.get('source','') or 'google_news_us_live' in story.get('source','') else 0.0, "status": "fallback", "matched_sources": [story]}

class SourceVerifier:
    def verify_story(self, story_dict):
        return verify_story_single(story_dict)
    def verify_stories(self, stories):
        return verify_stories(stories)
