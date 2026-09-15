"""
src/intelligence/competition_analyzer.py - Competition analysis
"""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def analyze_competition(story):
    """
    Analyze competition for a topic
    
    Returns:
        dict with competition metrics and recommended angle
    """
    title = story.get('title', '')
    
    # Simplified analysis
    # Real implementation would check YouTube search
    
    result = {
        'competition_level': 'medium',
        'competition_score': 60,  # Higher = more competition
        'recommended_angle': find_under_served_angle(story),
        'saturation': 0.5
    }
    
    return result


def find_under_served_angle(story):
    """
    Find under-served angle for a competitive topic
    
    Instead of "Trump announces X", try:
    - "What this actually changes"
    - "Why this matters globally"
    - "The part everyone missed"
    """
    title = story.get('title', '').lower()
    
    angles = [
        "What this actually changes",
        "Why this matters for ordinary people",
        "The part everyone missed",
        "What happens next",
        "Global impact explained"
    ]
    
    # Pick based on topic
    if 'trump' in title or 'biden' in title:
        return "What this actually changes for everyday Americans"
    elif 'tariff' in title or 'trade' in title:
        return "Why this matters for prices and jobs"
    elif 'war' in title or 'conflict' in title:
        return "What this means for global stability"
    elif 'election' in title:
        return "What this means for the future"
    else:
        return angles[0]


def calculate_competition_opportunity(story):
    """
    Calculate competition opportunity score (0-100)
    Higher = better opportunity (less competition or good angle)
    """
    competition = analyze_competition(story)
    
    # Invert competition score
    opportunity = 100 - competition['competition_score']
    
    # Boost if we have a good angle
    if competition['recommended_angle']:
        opportunity += 10
    
    return min(100, opportunity)
