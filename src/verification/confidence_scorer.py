"""
src/verification/confidence_scorer.py - Final confidence scoring
"""

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def calculate_final_confidence(story, verification_data, fact_check_result):
    """
    Calculate final confidence score (0-100)
    
    Hard gates:
    - Truth confidence >= 85
    - Policy safety >= 90
    """
    confidence = 50
    
    # Source credibility (0-25)
    source_score = verification_data.get('source_credibility', 50)
    confidence += (source_score / 100) * 25
    
    # Corroboration (0-15)
    if verification_data.get('corroborated'):
        confidence += 15
    elif verification_data.get('corroboration_count', 0) >= 1:
        confidence += 8
    
    # Fact check (0-20)
    if fact_check_result.get('passed'):
        confidence += 20
    
    # Trend strength (0-10)
    breakout_score = story.get('breakout_score', 0)
    confidence += min(10, breakout_score / 600)
    
    # Freshness (0-10)
    confidence += 8  # Default for recent stories
    
    # Penalties
    if not verification_data.get('corroborated'):
        confidence -= 10
    
    if story.get('source_tier', 4) == 4:
        confidence -= 15
    
    return max(0, min(100, confidence))


def check_hard_gates(confidence_data):
    """
    Check if hard gates pass
    
    TRUTH_CONFIDENCE >= 85
    POLICY_SAFETY >= 90
    """
    from src.config import HARD_GATES
    
    truth = confidence_data.get('truth_confidence', 0)
    policy = confidence_data.get('policy_safety', 0)
    
    if truth < HARD_GATES['truth_confidence']:
        return False, f"Truth confidence too low: {truth}"
    
    if policy < HARD_GATES['policy_safety']:
        return False, f"Policy safety too low: {policy}"
    
    return True, "All hard gates passed"
