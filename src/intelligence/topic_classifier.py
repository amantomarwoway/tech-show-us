"""
src/intelligence/topic_classifier.py - Classify story types
"""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

TOPIC_CATEGORIES = {
    'politics': ['trump', 'biden', 'election', 'congress', 'senate', 'white house',
                 'supreme court', 'democrat', 'republican', 'vote', 'president'],
    'geopolitics': ['war', 'china', 'russia', 'ukraine', 'nato', 'un', 'sanctions',
                    'middle east', 'israel', 'iran', 'north korea'],
    'economy': ['economy', 'market', 'stock', 'inflation', 'tariff', 'trade',
                'federal reserve', 'interest rate', 'jobs', 'gdp'],
    'tech': ['apple', 'google', 'meta', 'tesla', 'ai', 'spacex', 'microsoft',
             'amazon', 'tiktok', 'chatgpt'],
    'health': ['health', 'covid', 'vaccine', 'fda', 'cdc', 'who', 'disease'],
    'climate': ['climate', 'global warming', 'environment', 'carbon', 'emissions'],
    'breaking': ['breaking', 'just in', 'urgent', 'alert', 'developing']
}


def classify_topic(story):
    """
    Classify story into one or more categories
    
    Returns:
        dict with primary_category, all_categories, confidence
    """
    title = story.get('title', '').lower()
    
    matched = []
    
    for category, keywords in TOPIC_CATEGORIES.items():
        for kw in keywords:
            if kw in title:
                matched.append(category)
                break
    
    if not matched:
        matched = ['general']
    
    return {
        'primary_category': matched[0],
        'all_categories': matched,
        'confidence': 80 if len(matched) > 0 else 50
    }


def get_category_weights(category):
    """Get scoring weights for a category"""
    from src.config import STORY_TYPE_WEIGHTS
    
    category_map = {
        'breaking': 'breaking',
        'politics': 'political',
        'geopolitics': 'geopolitical',
        'tech': 'tech',
        'economy': 'evergreen',
        'health': 'evergreen',
        'climate': 'evergreen',
        'general': 'evergreen'
    }
    
    story_type = category_map.get(category, 'evergreen')
    return STORY_TYPE_WEIGHTS.get(story_type, STORY_TYPE_WEIGHTS['evergreen'])
