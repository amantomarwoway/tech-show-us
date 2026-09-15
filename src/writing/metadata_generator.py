"""
src/writing/metadata_generator.py - Title/description/hashtag generation
"""

import random
from src.utils.logger import setup_logger
from src.config import YOUTUBE_CONFIG

logger = setup_logger(__name__)

def generate_all_metadata(script_data, story):
    """Generate all YouTube metadata"""
    return {
        "title": generate_title(script_data, story),
        "description": generate_description(script_data, story),
        "tags": generate_tags(script_data, story),
        "hashtags": generate_hashtags(script_data, story)
    }


def generate_title(script_data, story):
    """
    Generate 5 title variations and select best
    """
    topic = story.get('title', '')
    seo_title = script_data.get('seo_youtube_title', '') or topic
    
    titles = [
        # A: News-first
        seo_title[:95],
        
        # B: Curiosity-first
        f"The part everyone missed about {topic[:50]}",
        
        # C: Consequence-first
        f"This changes everything: {topic[:50]}",
        
        # D: Search-first
        f"{topic[:60]} explained",
        
        # E: Global impact
        f"Global impact: {topic[:50]}"
    ]
    
    # Filter valid titles
    valid = [t for t in titles if 20 <= len(t) <= 100]
    
    if not valid:
        valid = [seo_title[:95]]
    
    # Select based on predicted performance
    selected = select_best_title(valid, story)
    
    return selected


def select_best_title(titles, story):
    """Select best title based on heuristics"""
    scores = []
    
    for title in titles:
        score = 50
        
        # Length optimization (40-70 chars best)
        if 40 <= len(title) <= 70:
            score += 20
        elif 30 <= len(title) <= 80:
            score += 10
        
        # Curiosity words
        if any(w in title.lower() for w in ['secret', 'hidden', 'missed', 'actually']):
            score += 15
        
        # Numbers
        if any(c.isdigit() for c in title):
            score += 5
        
        # No ALL CAPS
        if title.isupper():
            score -= 20
        
        # No excessive emojis
        if title.count('!') > 2:
            score -= 10
        
        scores.append((title, score))
    
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[0][0]


def generate_description(script_data, story):
    """Generate YouTube description"""
    topic = story.get('title', '')
    script = script_data.get('short_script', '') or script_data.get('full_script', '')
    
    # Get hooks
    hooks = YOUTUBE_CONFIG.get('description_hooks', [])
    hook = random.choice(hooks) if hooks else "Subscribe for more!"
    
    description = f"""{hook}

{topic}

{script[:200]}...

Stay informed. Subscribe for more breaking news.

#BreakingNews #WorldNews #USNews
"""
    
    return description[:5000]  # YouTube limit


def generate_tags(script_data, story):
    """Generate YouTube tags"""
    base_tags = [
        "breaking news", "world news", "us news", "news today",
        "politics", "white house", "trump", "biden"
    ]
    
    # Add topic-specific tags
    topic_tags = script_data.get('tags', [])
    
    # Combine and limit
    all_tags = base_tags + topic_tags
    unique_tags = list(dict.fromkeys(all_tags))  # Remove duplicates
    
    return unique_tags[:15]  # YouTube recommends max 15


def generate_hashtags(script_data, story):
    """Generate hashtags (3-5 max)"""
    base = ["#BreakingNews", "#WorldNews", "#USNews"]
    
    topic_hashtags = script_data.get('hashtags', [])
    
    # Combine
    all_hashtags = base + topic_hashtags
    
    # Limit to 5
    return all_hashtags[:5]
