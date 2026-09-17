"""
src/intelligence/story_ranker.py - TRENDING-FOCUSED RANKER
Accepts ANY topic - only TRENDING matters
"""

from src.config import STORY_SCORE_WEIGHTS, STORY_TYPE_WEIGHTS
from src.intelligence.trend_engine import calculate_trend_score
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def classify_story_type(story):
    """Classify: trending, viral, or news"""
    title = story.get('title', '').lower()
    source = story.get('source', '').lower()
    
    # Google Trends or Reddit = trending
    if 'trends' in source or 'reddit' in source:
        return 'trending'
    
    # High breakout = viral
    if story.get('is_breakout') and story.get('breakout_score', 0) > 5000:
        return 'viral'
    
    # Default: news
    return 'news'


def rank_stories(stories):
    """Rank all stories - TRENDING wins"""
    ranked = []
    
    for story in stories:
        story_type = classify_story_type(story)
        story['story_type'] = story_type
        
        weights = STORY_TYPE_WEIGHTS.get(story_type, STORY_SCORE_WEIGHTS)
        
        scores = {
            'trend_momentum': calculate_trend_score(story),
            'audience_relevance': calculate_audience_relevance(story),
            'news_importance': calculate_news_importance(story),
            'curiosity': calculate_curiosity(story),
            'novelty': calculate_novelty(story),
            'visual_potential': calculate_visual_potential(story),
            'search_potential': story.get('search_volume', 50),
            'competition_opportunity': 60
        }
        
        final_score = sum(scores[k] * weights[k] for k in scores)
        
        story['final_score'] = final_score
        story['score_breakdown'] = scores
        
        ranked.append(story)
    
    ranked.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    for i, story in enumerate(ranked[:5]):
        logger.info(f"Rank {i+1}: {story['title'][:50]} | Score: {story['final_score']:.1f} | Type: {story['story_type']}")
    
    return ranked


def calculate_audience_relevance(story):
    """Global audience relevance (0-100)"""
    title = story.get('title', '').lower()
    score = 50
    
    # Universal appeal topics
    if any(kw in title for kw in ['world', 'global', 'everyone', 'people', 'viral']):
        score += 20
    if any(kw in title for kw in ['trending', 'shocking', 'wow', 'amazing']):
        score += 15
    if any(kw in title for kw in ['us', 'usa', 'america', 'trump', 'biden']):
        score += 15
    if any(kw in title for kw in ['uk', 'britain', 'canada', 'australia']):
        score += 10
    
    return min(100, score)


def calculate_news_importance(story):
    """Low weight for trending stories"""
    return 50  # Neutral


def calculate_curiosity(story):
    """Curiosity factor (0-100)"""
    title = story.get('title', '').lower()
    score = 55
    
    # Curiosity triggers
    if any(kw in title for kw in ['shocking', 'secret', 'leaked', 'why', 'how', 'what']):
        score += 20
    if '?' in title:
        score += 15
    if any(kw in title for kw in ['viral', 'trending', 'everyone']):
        score += 15
    
    return min(100, score)


def calculate_novelty(story):
    """Novelty (0-100)"""
    title = story.get('title', '').lower()
    score = 60
    
    if any(kw in title for kw in ['first', 'new', 'unprecedented', 'just']):
        score += 20
    
    return min(100, score)


def calculate_visual_potential(story):
    """Visual potential (0-100)"""
    title = story.get('title', '').lower()
    score = 65
    
    # Visual-friendly
    if any(kw in title for kw in ['video', 'photo', 'watch', 'look', 'viral']):
        score += 20
    if any(kw in title for kw in ['dance', 'sport', 'game', 'movie', 'music']):
        score += 15
    
    return min(100, score)


def calculate_publish_score(story):
    return story.get('final_score', 0)
