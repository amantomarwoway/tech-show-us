"""
src/intelligence/audience_model.py - Global English audience model
"""

from src.config import ENGLISH_COUNTRIES, ENGLISH_COUNTRIES_HALF, TARGET_COUNTRIES
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

AUDIENCE_CLUSTERS = {
    'US': {'weight': 1.0, 'name': 'United States'},
    'UK': {'weight': 0.85, 'name': 'United Kingdom'},
    'CA': {'weight': 0.80, 'name': 'Canada'},
    'AU': {'weight': 0.75, 'name': 'Australia'},
    'NZ': {'weight': 0.70, 'name': 'New Zealand'},
    'IE': {'weight': 0.70, 'name': 'Ireland'},
    'IN': {'weight': 0.65, 'name': 'India'},
    'PH': {'weight': 0.55, 'name': 'Philippines'},
    'SG': {'weight': 0.55, 'name': 'Singapore'},
    'ZA': {'weight': 0.50, 'name': 'South Africa'},
    'NG': {'weight': 0.45, 'name': 'Nigeria'},
    'KE': {'weight': 0.40, 'name': 'Kenya'}
}

def calculate_global_relevance(story):
    """
    Calculate GLOBAL_RELEVANCE_SCORE (0-100)
    
    CONSIDER:
    - population affected
    - economic impact
    - geopolitical importance
    - cultural interest
    - international consequences
    - novelty
    - English-language search demand
    - cross-country discussion
    - ability to understand without local knowledge
    """
    title = story.get('title', '').lower()
    score = 0
    
    # 1. Population affected (0-20)
    if any(kw in title for kw in ['millions', 'billions', 'everyone', 'global']):
        score += 20
    elif any(kw in title for kw in ['thousands', 'families', 'americans']):
        score += 12
    else:
        score += 6
    
    # 2. Economic impact (0-15)
    if any(kw in title for kw in ['economy', 'market', 'trade', 'tariff', 'inflation', 'jobs']):
        score += 15
    else:
        score += 5
    
    # 3. Geopolitical importance (0-20)
    geo_keywords = ['war', 'nato', 'china', 'russia', 'ukraine', 'middle east', 'un', 'sanctions']
    if any(kw in title for kw in geo_keywords):
        score += 20
    else:
        score += 5
    
    # 4. Cultural interest (0-10)
    if any(kw in title for kw in ['election', 'president', 'royal', 'celebrity']):
        score += 10
    else:
        score += 4
    
    # 5. International consequences (0-15)
    if any(kw in title for kw in ['global', 'world', 'international', 'foreign']):
        score += 15
    else:
        score += 5
    
    # 6. Novelty (0-10)
    if any(kw in title for kw in ['first', 'new', 'unprecedented', 'historic']):
        score += 10
    else:
        score += 5
    
    # 7. English search demand (0-10)
    search_volume = story.get('search_volume', 50)
    score += min(10, search_volume / 10)
    
    return min(100, score)


def get_target_countries_for_story(story):
    """Determine which country clusters will care about this story"""
    title = story.get('title', '').lower()
    targets = []
    
    for code, info in AUDIENCE_CLUSTERS.items():
        # Check if story mentions specific country
        country_name = info['name'].lower()
        if country_name in title or code.lower() in title:
            targets.append(code)
    
    # Add default targets
    if not targets:
        targets = ['US', 'GB', 'CA', 'AU']
    
    return targets


def estimate_audience_size(story):
    """Estimate potential audience size"""
    base_relevance = calculate_global_relevance(story)
    
    # Rough estimate: relevance * 100K base
    estimated = base_relevance * 1000
    
    return min(1000000, estimated)
