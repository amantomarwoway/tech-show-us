"""
src/intelligence/story_ranker.py - Story scoring and ranking
"""

from src.config import STORY_SCORE_WEIGHTS, STORY_TYPE_WEIGHTS, PUBLISH_THRESHOLDS
from src.intelligence.trend_engine import calculate_trend_score
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def classify_story_type(story):
    """Classify story into type for dynamic weighting"""
    title = story.get('title', '').lower()
    
    if any(kw in title for kw in ['breaking', 'just in', 'urgent', 'alert']):
        return 'breaking'
    elif any(kw in title for kw in ['trump', 'biden', 'election', 'congress', 'senate']):
        return 'political'
    elif any(kw in title for kw in ['war', 'china', 'russia', 'ukraine', 'nato', 'un']):
        return 'geopolitical'
    elif any(kw in title for kw in ['apple', 'google', 'ai', 'tech', 'spacex', 'tesla']):
        return 'tech'
    else:
        return 'evergreen'


def rank_stories(stories):
    """
    Rank all stories using multi-factor scoring
    
    STORY_SCORE = 
    25% TREND MOMENTUM
    20% AUDIENCE RELEVANCE
    15% NEWS IMPORTANCE
    15% CURIOSITY
    10% NOVELTY
    5% VISUAL POTENTIAL
    5% SEARCH POTENTIAL
    5% COMPETITION OPPORTUNITY
    """
    ranked = []
    
    for story in stories:
        # Classify type
        story_type = classify_story_type(story)
        story['story_type'] = story_type
        
        # Get appropriate weights
        weights = STORY_TYPE_WEIGHTS.get(story_type, STORY_SCORE_WEIGHTS)
        
        # Calculate individual scores
        scores = {
            'trend_momentum': calculate_trend_score(story),
            'audience_relevance': calculate_audience_relevance(story),
            'news_importance': calculate_news_importance(story),
            'curiosity': calculate_curiosity(story),
            'novelty': calculate_novelty(story),
            'visual_potential': calculate_visual_potential(story),
            'search_potential': calculate_search_potential(story),
            'competition_opportunity': calculate_competition_opportunity(story)
        }
        
        # Weighted sum
        final_score = sum(scores[k] * weights[k] for k in scores)
        
        story['final_score'] = final_score
        story['score_breakdown'] = scores
        
        ranked.append(story)
    
    # Sort by final score
    ranked.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    # Log top stories
    for i, story in enumerate(ranked[:5]):
        logger.info(f"Rank {i+1}: {story['title'][:50]} | Score: {story['final_score']:.1f} | Type: {story.get('story_type', 'unknown')}")
    
    return ranked


def calculate_audience_relevance(story):
    """Calculate global audience relevance (0-100)"""
    title = story.get('title', '').lower()
    score = 50  # Base
    
    # Global relevance boosters
    if any(kw in title for kw in ['world', 'global', 'international', 'un', 'nato']):
        score += 25
    if any(kw in title for kw in ['us', 'usa', 'america', 'white house']):
        score += 20
    if any(kw in title for kw in ['uk', 'britain', 'europe', 'canada', 'australia']):
        score += 15
    if any(kw in title for kw in ['china', 'russia', 'india', 'japan', 'middle east']):
        score += 15
    
    # Population affected
    if any(kw in title for kw in ['millions', 'families', 'everyone', 'americans']):
        score += 10
    
    return min(100, score)


def calculate_news_importance(story):
    """Calculate news importance (0-100)"""
    title = story.get('title', '').lower()
    score = 40
    
    importance_keywords = {
        'war': 30, 'election': 25, 'economy': 25, 'supreme court': 25,
        'white house': 20, 'congress': 20, 'president': 20,
        'tariff': 20, 'trade': 15, 'health': 20, 'climate': 15
    }
    
    for kw, boost in importance_keywords.items():
        if kw in title:
            score += boost
            break
    
    return min(100, score)


def calculate_curiosity(story):
    """Calculate curiosity factor (0-100)"""
    title = story.get('title', '').lower()
    score = 50
    
    curiosity_keywords = ['shocking', 'secret', 'leaked', 'hidden', 'revealed',
                         'exposed', 'behind closed doors', 'nobody knows', 'surprising']
    
    for kw in curiosity_keywords:
        if kw in title:
            score += 15
            break
    
    # Question in title
    if '?' in title:
        score += 10
    
    return min(100, score)


def calculate_novelty(story):
    """Calculate novelty (0-100)"""
    title = story.get('title', '').lower()
    score = 50
    
    novelty_keywords = ['first', 'new', 'unprecedented', 'historic', 'never before']
    
    for kw in novelty_keywords:
        if kw in title:
            score += 20
            break
    
    return min(100, score)


def calculate_visual_potential(story):
    """Calculate visual potential (0-100)"""
    title = story.get('title', '').lower()
    score = 60  # Default - most news has some visuals
    
    # Visual-friendly topics
    if any(kw in title for kw in ['crash', 'explosion', 'protest', 'rally', 'speech']):
        score += 20
    if any(kw in title for kw in ['map', 'chart', 'data', 'numbers']):
        score += 15
    
    return min(100, score)


def calculate_search_potential(story):
    """Calculate search potential (0-100)"""
    search_volume = story.get('search_volume', 50)
    return min(100, search_volume)


def calculate_competition_opportunity(story):
    """Calculate competition opportunity (0-100)"""
    # Higher = less competition = better opportunity
    # This is a simplified version - real implementation would check YouTube
    return 60  # Default


def calculate_publish_score(story):
    """Calculate final publish score (0-100)"""
    return story.get('final_score', 0)
