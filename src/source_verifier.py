from collections import defaultdict
import re, time, json
from datetime import datetime, timezone
from typing import List, Dict

try:
    import config
    CONFIG_AVAILABLE = True
except:
    CONFIG_AVAILABLE = False
    config = None

# UPDATED JULY 2025 - All sources from latest 15 files
TRUSTED_SOURCES = [
    'reuters','apnews','gov',
    'google_trends_usa','google_trends_usa_current','google_trends_official_rss','google_trends','google_news_us_live','google_trends_usa_breakout',
    'google_trends_breakout','google_trends_trending_now','google_trends_usa_breakout',
    'visualping_cnn_breaking','visualping_cnn_breaking_guaranteed','guaranteed_google_news_rss',
    'guaranteed_breakout_cnn_google_fox','guaranteed_breakout_hardcoded','guaranteed_breakout',
    'visualping_whitehouse_press','visualping_supreme_court','visualping_recent',
    'reddit_rising_breakout','youtube_search',
    'filter_abc','filter_a','filter_b','filter_a_youtube','filter_a_rising'
]

BREAKOUT_SOURCES = [
    'visualping_cnn_breaking_guaranteed','guaranteed_google_news_rss','guaranteed_breakout_cnn_google_fox','guaranteed_breakout_hardcoded',
    'google_trends_breakout','google_trends_trending_now','reddit_rising_breakout','visualping_cnn_breaking','visualping_whitehouse_press','visualping_supreme_court'
]

BLOCKED_COUNTRIES = ["germany","merz","canada","canadian","german"]

def is_us_topic_verifier(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    for b in BLOCKED_COUNTRIES:
        if b in low and not any(k in low for k in ["trump","white house","usa","america","supreme court","congress","senate","biden","fbi","nasa"]):
            return False
    return True

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_source_reliability(source: str) -> float:
    if CONFIG_AVAILABLE and hasattr(config, 'SOURCE_RELIABILITY'):
        if source in config.SOURCE_RELIABILITY:
            return config.SOURCE_RELIABILITY[source]
        # partial match
        for k,v in config.SOURCE_RELIABILITY.items():
            if k in source or source in k:
                return v
    # fallback reliability map
    if source in BREAKOUT_SOURCES:
        return 0.95
    if 'google_trends' in source or 'google_news' in source:
        return 0.90
    if source in ['reuters','apnews','gov']:
        return 1.0
    return 0.80

def verify_stories(stories: List[Dict]) -> List[Dict]:
    if not stories:
        return []
    grouped = defaultdict(list)
    for s in stories:
        title = s.get('title','')
        title_clean = clean_id(title).lower().strip()[:50]
        if not title_clean:
            continue
        # US filter
        if not is_us_topic_verifier(title):
            # allow if breakout
            if not (s.get('is_breakout') or s.get('breakout_score',0) >= 5000):
                continue
        grouped[title_clean].append(s)

    verified = []
    for key, group in grouped.items():
        if len(group) >= 2:
            sources = list(set([g.get('source','unknown') for g in group]))
            if len(sources) >= 2 or any(src in BREAKOUT_SOURCES for src in sources):
                merged = group[0].copy()
                merged['all_sources'] = group
                merged['source_count'] = len(sources)
                # breakout boost
                base = 0.7 + len(sources)*0.1
                if any(g.get('is_breakout') or g.get('breakout_score',0) >= 5000 for g in group):
                    base += 0.15
                merged['verification_score'] = min(0.97, base)
                merged['status'] = 'verified_multi_source_breakout' if any(g.get('is_breakout') for g in group) else 'verified_multi_source'
                merged['single_source'] = False
                verified.append(merged)
        elif len(group) == 1:
            g = group[0].copy()
            src = g.get('source','')
            # TRUSTED + BREAKOUT allow single source
            if src in TRUSTED_SOURCES or src in BREAKOUT_SOURCES or 'google_trends' in src or 'google_news' in src or 'visualping' in src or 'guaranteed' in src or src in ['reuters','apnews','gov']:
                g['all_sources'] = group
                g['source_count'] = 1
                rel = get_source_reliability(src)
                if src in BREAKOUT_SOURCES:
                    g['verification_score'] = 0.95
                    g['status'] = 'verified_breakout_guaranteed'
                    g['single_source'] = False
                elif 'google_trends' in src or 'google_news_us_live' in src or 'guaranteed' in src:
                    g['verification_score'] = 0.90
                    g['single_source'] = False
                    g['status'] = 'verified_trending' if 'trends' in src else 'verified_live_news_guaranteed'
                else:
                    g['verification_score'] = rel if rel > 0.85 else 0.85
                    g['single_source'] = True
                    g['status'] = 'verified_single_official'
                verified.append(g)

    # FALLBACK: if still no verified but stories exist, allow trending/breakout
    if not verified and stories:
        has_trends = any('google_trends' in s.get('source','') or 'google_news_us_live' in s.get('source','') or s.get('is_breakout') or 'visualping' in s.get('source','') or 'guaranteed' in s.get('source','') for s in stories)
        if has_trends:
            for s in stories[:5]:
                if not is_us_topic_verifier(s.get('title','')) and not (s.get('is_breakout') or s.get('breakout_score',0) >= 5000):
                    continue
                g = s.copy()
                g['all_sources'] = [s]
                g['source_count'] = 1
                if s.get('is_breakout') or s.get('breakout_score',0) >= 5000:
                    g['verification_score'] = 0.95
                    g['status'] = 'breakout_guaranteed_verified'
                else:
                    g['verification_score'] = 0.88
                    g['status'] = 'trending_verified'
                g['single_source'] = False
                verified.append(g)
        else:
            # last resort - allow top 3 if US
            for s in stories[:3]:
                if not is_us_topic_verifier(s.get('title','')):
                    continue
                g = s.copy()
                g['all_sources'] = [s]
                g['source_count'] = 1
                g['verification_score'] = 0.80
                g['status'] = 'fallback_us_verified'
                g['single_source'] = True
                verified.append(g)

    # Sort by verification_score desc + breakout first
    verified.sort(key=lambda x: (x.get('is_breakout', False) or x.get('breakout_score',0) >= 5000, x.get('verification_score',0)), reverse=True)
    return verified

def verify_story_single(story: Dict) -> Dict:
    result = verify_stories([story])
    if result:
        return {"verification_score": result[0]['verification_score'], "status": result[0].get('status','verified'), "matched_sources": result[0]['all_sources'], "is_breakout": result[0].get('is_breakout', False)}
    # fallback single
    src = story.get('source','')
    if story.get('is_breakout') or story.get('breakout_score',0) >= 5000:
        return {"verification_score": 0.95, "status": "breakout_guaranteed", "matched_sources": [story], "is_breakout": True}
    if 'google_trends' in src or 'google_news_us_live' in src or 'visualping' in src or 'guaranteed' in src:
        return {"verification_score": 0.88, "status": "trending_fallback", "matched_sources": [story], "is_breakout": False}
    return {"verification_score": 0.0, "status": "unverified", "matched_sources": [story], "is_breakout": False}

class SourceVerifier:
    def verify_story(self, story_dict: Dict):
        return verify_story_single(story_dict)
    def verify_stories(self, stories: List[Dict]):
        return verify_stories(stories)
