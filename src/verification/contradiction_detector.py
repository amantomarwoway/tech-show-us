"""
src/verification/contradiction_detector.py - Cross-source contradiction detection
"""

import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def detect_contradictions(story, related_stories):
    """
    Detect contradictions between sources
    
    Returns:
        dict with contradiction status
    """
    result = {
        'has_contradiction': False,
        'contradictions': [],
        'severity': 'none'
    }
    
    if not related_stories:
        return result
    
    title = story.get('title', '').lower()
    
    # Check for negation patterns
    for other in related_stories:
        other_title = other.get('title', '').lower()
        
        # Look for denial words
        denial_words = ['denies', 'denied', 'false', 'not true', 'refutes', 'rejects']
        
        for word in denial_words:
            if word in other_title and any(kw in other_title for kw in title.split()[:3]):
                result['has_contradiction'] = True
                result['contradictions'].append({
                    'source': other.get('source', ''),
                    'title': other_title,
                    'type': 'denial'
                })
                result['severity'] = 'high'
    
    return result


def check_date_consistency(story):
    """Check if dates in story are consistent"""
    title = story.get('title', '')
    
    # Extract years
    years = re.findall(r'\b(20\d{2})\b', title)
    
    if years:
        from datetime import datetime
        current_year = datetime.now().year
        
        for year in years:
            year_int = int(year)
            if year_int < current_year - 5 or year_int > current_year + 1:
                return False, f"Suspicious year: {year}"
    
    return True, "Dates OK"


def check_location_consistency(story):
    """Check if location mentions are consistent"""
    title = story.get('title', '').lower()
    
    locations = ['usa', 'uk', 'china', 'russia', 'europe', 'india', 'japan']
    mentioned = [loc for loc in locations if loc in title]
    
    # Multiple conflicting locations
    if len(mentioned) > 3:
        return False, f"Too many locations: {mentioned}"
    
    return True, "Locations OK"
