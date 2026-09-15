"""
src/safety/policy_filter.py - YouTube policy safety filter
"""

import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# High-risk keywords that require extra verification
HIGH_RISK_KEYWORDS = [
    'election fraud', 'stolen election', 'rigged',
    'vaccine death', 'cure cancer', 'miracle cure',
    'secret cure', 'they don\'t want you to know',
    'wake up', 'plandemic', 'conspiracy',
    'deep state', 'new world order'
]

# Misinformation patterns
MISINFO_PATTERNS = [
    r'doctors?\s+hate',
    r'government\s+hiding',
    r'they\s+don\'t\s+want',
    r'secret\s+cure',
    r'100%\s+proven'
]

def check_policy_compliance(script_data, story):
    """
    Check if content complies with YouTube policies
    
    Returns dict with passed status and risk level
    """
    result = {
        'passed': True,
        'risk_level': 'low',
        'issues': []
    }
    
    script = script_data.get('short_script', '') or script_data.get('full_script', '')
    title = story.get('title', '')
    
    text = f"{title} {script}".lower()
    
    # Check high-risk keywords
    for kw in HIGH_RISK_KEYWORDS:
        if kw in text:
            result['issues'].append(f"High-risk keyword: {kw}")
            result['risk_level'] = 'high'
    
    # Check misinformation patterns
    for pattern in MISINFO_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            result['issues'].append(f"Misinfo pattern: {pattern}")
            result['risk_level'] = 'high'
    
    # Check for unsupported claims
    unsupported_patterns = [
        r'everyone\s+knows',
        r'it\'s\s+obvious',
        r'they\s+all\s+know',
        r'no\s+one\s+is\s+talking\s+about'
    ]
    
    for pattern in unsupported_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result['issues'].append(f"Unsupported claim: {pattern}")
            result['risk_level'] = 'medium'
    
    # Determine pass/fail
    if result['risk_level'] == 'high':
        result['passed'] = False
    elif result['risk_level'] == 'medium' and len(result['issues']) > 2:
        result['passed'] = False
    
    return result


def run_quality_gate(script_data, story):
    """
    Run full quality gate before publishing
    
    Returns dict with passed status
    """
    result = {
        'passed': True,
        'reason': '',
        'checks': {}
    }
    
    # 1. Policy compliance
    policy = check_policy_compliance(script_data, story)
    result['checks']['policy'] = policy
    
    if not policy['passed']:
        result['passed'] = False
        result['reason'] = f"Policy issues: {policy['issues']}"
        return result
    
    # 2. Truth confidence (from fact checker)
    # This is checked separately in main pipeline
    
    # 3. Script quality
    script = script_data.get('short_script', '') or script_data.get('full_script', '')
    
    if len(script.split()) < 20:
        result['passed'] = False
        result['reason'] = "Script too short"
        return result
    
    if len(script.split()) > 60:
        result['passed'] = False
        result['reason'] = "Script too long"
        return result
    
    # 4. Title check
    title = script_data.get('seo_youtube_title', '') or story.get('title', '')
    
    if len(title) > 100:
        result['passed'] = False
        result['reason'] = "Title too long"
        return result
    
    if title.isupper() and len(title) > 30:
        result['passed'] = False
        result['reason'] = "Title is ALL CAPS"
        return result
    
    logger.info(f"Quality gate passed: {result['checks']}")
    return result


def check_defamation_risk(text):
    """Check for potential defamation"""
    # Simplified check
    risky_phrases = [
        'is a criminal', 'is corrupt', 'is a liar', 'is a fraud',
        'committed a crime', 'is guilty of'
    ]
    
    text_lower = text.lower()
    
    for phrase in risky_phrases:
        if phrase in text_lower:
            # Check if attributed
            attributed = ['accused', 'alleged', 'according to', 'claims', 'reports say']
            if not any(attr in text_lower for attr in attributed):
                return True
    
    return False
