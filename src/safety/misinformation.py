"""
src/safety/misinformation.py - Misinformation detection
"""

import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Common misinformation patterns
MISINFO_INDICATORS = [
    {
        'pattern': r'doctors?\s+(are\s+)?hiding',
        'risk': 'high',
        'reason': 'Medical conspiracy'
    },
    {
        'pattern': r'government\s+(is\s+)?hiding',
        'risk': 'high',
        'reason': 'Government conspiracy'
    },
    {
        'pattern': r'they\s+don\'?t\s+want\s+you\s+to\s+know',
        'risk': 'high',
        'reason': 'Conspiracy phrasing'
    },
    {
        'pattern': r'secret\s+cure',
        'risk': 'high',
        'reason': 'Fake cure'
    },
    {
        'pattern': r'100%\s+proven',
        'risk': 'medium',
        'reason': 'Absolute claim'
    },
    {
        'pattern': r'miracle\s+(cure|drug|treatment)',
        'risk': 'high',
        'reason': 'Miracle cure claim'
    },
    {
        'pattern': r'wake\s+up\s+(people|sheeple)',
        'risk': 'high',
        'reason': 'Conspiracy language'
    },
    {
        'pattern': r'plandemic',
        'risk': 'high',
        'reason': 'COVID misinformation'
    },
    {
        'pattern': r'stolen\s+election',
        'risk': 'high',
        'reason': 'Election misinformation'
    },
    {
        'pattern': r'election\s+fraud',
        'risk': 'medium',
        'reason': 'Requires verification'
    }
]

def detect_misinformation(text):
    """
    Detect potential misinformation in text
    
    Returns:
        dict with risk_level and detected_issues
    """
    result = {
        'risk_level': 'low',
        'issues': [],
        'score': 0
    }
    
    text_lower = text.lower()
    
    for indicator in MISINFO_INDICATORS:
        if re.search(indicator['pattern'], text_lower, re.IGNORECASE):
            result['issues'].append(indicator['reason'])
            
            if indicator['risk'] == 'high':
                result['risk_level'] = 'high'
                result['score'] += 30
            elif indicator['risk'] == 'medium':
                if result['risk_level'] != 'high':
                    result['risk_level'] = 'medium'
                result['score'] += 15
    
    result['score'] = min(100, result['score'])
    
    return result


def require_attribution(text):
    """Check if sensitive claims have proper attribution"""
    sensitive_patterns = [
        r'\b(is|are|was|were)\s+(a\s+)?(criminal|corrupt|fraud|liar)',
        r'\bcommitted\s+(a\s+)?crime',
        r'\bis\s+guilty',
        r'\bdid\s+something\s+illegal'
    ]
    
    text_lower = text.lower()
    
    attribution_phrases = [
        'accused', 'alleged', 'according to', 'claims', 'reports say',
        'officials say', 'sources say', 'reportedly', 'allegedly'
    ]
    
    for pattern in sensitive_patterns:
        if re.search(pattern, text_lower):
            if not any(phrase in text_lower for phrase in attribution_phrases):
                return False  # Missing attribution
    
    return True
