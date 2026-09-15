"""
src/verification/source_verifier.py - Source credibility scoring
"""

import re
from urllib.parse import urlparse
from src.config import TIER1_SOURCES, TIER2_SOURCES, TIER3_SOURCES
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def get_source_tier(url):
    """Determine source tier (1-4)"""
    if not url:
        return 4
    
    domain = urlparse(url).netloc.lower()
    domain = domain.replace('www.', '')
    
    if any(t in domain for t in TIER1_SOURCES):
        return 1
    if any(t in domain for t in TIER2_SOURCES):
        return 2
    if any(t in domain for t in TIER3_SOURCES):
        return 3
    
    return 4


def calculate_source_credibility(url, source_name=""):
    """
    Calculate source credibility score (0-100)
    
    SOURCE_SCORE = authority + directness + corroboration + recency 
                 - anonymous_risk - contradiction_risk
    """
    score = 50  # Base
    
    tier = get_source_tier(url)
    
    # Tier-based scoring
    tier_scores = {1: 40, 2: 30, 3: 15, 4: 0}
    score += tier_scores.get(tier, 0)
    
    # Directness (official source = higher)
    domain = urlparse(url).netloc.lower() if url else ""
    if any(x in domain for x in ['gov', 'official', 'press']):
        score += 15
    
    # Historical reliability
    if 'reuters' in domain or 'apnews' in domain:
        score += 10
    
    # Anonymous source risk
    source_lower = source_name.lower()
    if 'anonymous' in source_lower or 'unnamed' in source_lower:
        score -= 20
    
    return max(0, min(100, score))


def cross_verify(story, all_stories):
    """
    Cross-verify story with other sources
    
    Returns:
        dict with corroboration status
    """
    title = story.get('title', '').lower()
    title_keywords = set(re.findall(r'\w+', title)) - {'the', 'a', 'an', 'is', 'in', 'on', 'at'}
    
    corroborating = []
    
    for other in all_stories:
        if other is story:
            continue
        
        other_title = other.get('title', '').lower()
        other_keywords = set(re.findall(r'\w+', other_title)) - {'the', 'a', 'an', 'is', 'in', 'on', 'at'}
        
        # Calculate overlap
        overlap = len(title_keywords & other_keywords)
        total = len(title_keywords | other_keywords)
        
        if total > 0 and overlap / total > 0.4:
            corroborating.append(other)
    
    return {
        'corroborated': len(corroborating) >= 2,
        'corroboration_count': len(corroborating),
        'sources': [c.get('source', '') for c in corroborating]
    }


def handle_breaking_news(story):
    """
    Special handling for breaking news
    
    Breaking news requires:
    1. Original/official source
    2. Independent confirmation
    3. Confidence estimate
    """
    result = {
        'status': 'developing',
        'confidence': 50,
        'recommendation': 'wait_for_confirmation'
    }
    
    source_tier = get_source_tier(story.get('url', ''))
    breakout_score = story.get('breakout_score', 0)
    
    # Tier 1 + high score = high confidence
    if source_tier == 1 and breakout_score > 5500:
        result['status'] = 'confirmed'
        result['confidence'] = 90
        result['recommendation'] = 'publish_with_attribution'
    elif source_tier <= 2 and breakout_score > 5000:
        result['status'] = 'likely'
        result['confidence'] = 75
        result['recommendation'] = 'publish_with_caution'
    else:
        result['recommendation'] = 'wait'
    
    return result
