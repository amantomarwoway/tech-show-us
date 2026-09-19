"""
src/intelligence/topic_scorer.py - Smart topic scoring
"""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


VIRAL_KEYWORDS = {
    'celebrity': 30, 'taylor swift': 40, 'musk': 40, 'trump': 35, 'biden': 30,
    'mrbeast': 40, 'ronaldo': 35, 'messi': 35, 'kanye': 30, 'drake': 30,
    'beyonce': 35, 'kardashian': 30, 'breaking': 25, 'shocking': 25,
    'leaked': 30, 'exposed': 25, 'viral': 30, 'trending': 25,
    'war': 30, 'crash': 25, 'dead': 25, 'killed': 30, 'arrested': 25,
    'record': 20, 'historic': 25, 'never': 15, 'first': 15,
    'netflix': 25, 'nba': 25, 'nfl': 25, 'world cup': 30,
    'ai': 25, 'apple': 25, 'tesla': 25, 'spacex': 25,
}

NEGATIVE_KEYWORDS = {
    'recipe': -40, 'cooking': -40, 'diet': -40, 'skincare': -40, 'botox': -40,
    'beauty': -35, 'makeup': -35, 'workout': -35, 'garden': -40,
    'weather': -50, 'temperature': -50, 'forecast': -50,
    'county': -30, 'municipal': -30, 'local': -30,
    'pokemon cards': -35, 'fall lovers': -35, 'autumn': -30,
    'discussion': -40, 'megathread': -50, 'weekly': -40, 'daily': -40,
}


def score_topic(title):
    if not title:
        return 0
    tl = title.lower()
    score = 50
    for kw, boost in VIRAL_KEYWORDS.items():
        if kw in tl:
            score += boost
    for kw, penalty in NEGATIVE_KEYWORDS.items():
        if kw in tl:
            score += penalty
    return max(0, min(100, score))


def rank_stories(stories):
    ranked = []
    for s in stories:
        title = s.get('title', '')
        viral_score = score_topic(title)
        breakout = s.get('breakout_score', 0)
        source_boost = 20 if 'reddit' in s.get('source', '').lower() else 0
        
        final = (viral_score * 0.5 + (breakout / 100) * 0.3 + source_boost)
        s['final_score'] = final
        s['viral_score'] = viral_score
        ranked.append(s)
    
    ranked.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    for i, s in enumerate(ranked[:5]):
        logger.info(f"Rank {i+1}: {s.get('title', '')[:55]} | Score: {s.get('final_score', 0):.1f} | Viral: {s.get('viral_score', 0)}")
    
    return ranked
