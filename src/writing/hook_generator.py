"""
src/writing/hook_generator.py - Generate hooks for scripts
"""

import random
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

HOOK_TYPES = [
    "breaking",
    "question",
    "consequence",
    "contrarian",
    "what_this_means",
    "timeline",
    "before_after",
    "hidden_detail",
    "global_impact",
    "numbers"
]

def generate_hooks(story, script_data=None):
    """
    Generate 5-10 candidate hooks for a story
    
    Returns list of hooks with scores
    """
    topic = story.get('title', '')
    keywords = story.get('keywords', [])
    
    hooks = []
    
    # 1. Breaking news hook
    hooks.append({
        'type': 'breaking',
        'text': f"Breaking: {topic[:50]}. This just changed everything.",
        'score': 75
    })
    
    # 2. Question hook
    hooks.append({
        'type': 'question',
        'text': f"What if everything you knew about {topic[:40]} was wrong?",
        'score': 70
    })
    
    # 3. Consequence hook
    hooks.append({
        'type': 'consequence',
        'text': f"This decision will affect millions. Here's what it means for you.",
        'score': 80
    })
    
    # 4. What this means hook
    hooks.append({
        'type': 'what_this_means',
        'text': f"{topic[:50]}. Here's what this actually means.",
        'score': 78
    })
    
    # 5. Hidden detail hook
    hooks.append({
        'type': 'hidden_detail',
        'text': f"The part everyone missed about {topic[:40]}.",
        'score': 82
    })
    
    # 6. Global impact hook
    hooks.append({
        'type': 'global_impact',
        'text': f"This isn't just about America. The whole world is watching.",
        'score': 76
    })
    
    # Score and filter
    for hook in hooks:
        hook['score'] = score_hook(hook, story)
    
    hooks.sort(key=lambda x: x['score'], reverse=True)
    
    return hooks[:5]


def score_hook(hook, story):
    """Score a hook for clarity, curiosity, accuracy, etc."""
    score = 50  # Base
    
    text = hook.get('text', '').lower()
    
    # Clarity boost
    if len(text) < 80:
        score += 10
    elif len(text) > 120:
        score -= 10
    
    # Curiosity boost
    curiosity_words = ['secret', 'hidden', 'missed', 'everyone', 'actually']
    if any(w in text for w in curiosity_words):
        score += 15
    
    # Accuracy check - reject clickbait
    if any(w in text for w in ['you won\'t believe', 'shocking truth', 'they don\'t want']):
        score -= 20
    
    # Information gap
    if '?' in text:
        score += 10
    
    return max(0, min(100, score))


def select_best_hook(hooks):
    """Select best hook from candidates"""
    if not hooks:
        return None
    
    # Filter out clickbait
    valid = [h for h in hooks if h['score'] >= 60]
    
    if not valid:
        valid = hooks
    
    # Select highest score
    return max(valid, key=lambda x: x['score'])
