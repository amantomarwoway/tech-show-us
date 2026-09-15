"""
src/media/caption_engine.py - Word-level caption timing
"""

import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

KEYWORD_BOOST = ['BREAKING', 'SHOCKING', 'TRUMP', 'BIDEN', 'WHITE', 'HOUSE',
                 'LEAKED', 'SECRET', 'SUPREME', 'COURT', 'USA', 'AMERICA',
                 'WAR', 'CRASH', 'DEAD', 'KILLED', 'ARRESTED', 'FBI']


def generate_caption_timing(script_text, total_duration):
    """
    Generate word-level caption timing
    
    Returns:
        list of {word, start, duration, is_keyword}
    """
    words = script_text.split()
    
    if not words:
        return []
    
    # Base duration per word
    base_dur = total_duration / len(words)
    
    # Adjust: first 5 words longer (pattern interrupt)
    timing = []
    current_time = 0
    
    for i, word in enumerate(words):
        is_keyword = any(k in word.upper() for k in KEYWORD_BOOST)
        is_first = i < 5
        
        if is_first:
            dur = base_dur * 1.4
        elif is_keyword:
            dur = base_dur * 1.2
        else:
            dur = base_dur * 0.95
        
        # Clamp
        dur = max(0.15, min(0.6, dur))
        
        timing.append({
            'word': word,
            'start': current_time,
            'duration': dur,
            'is_keyword': is_keyword,
            'is_first': is_first
        })
        
        current_time += dur * 0.92  # 8% overlap for smooth flow
    
    return timing


def get_caption_style(is_keyword, is_first):
    """Get caption styling"""
    if is_first:
        return {
            'fontsize': 90,
            'color': '#FFFFFF',
            'stroke': 9,
            'effect': 'zoom_in'
        }
    elif is_keyword:
        return {
            'fontsize': 86,
            'color': '#FF0000',
            'stroke': 8,
            'effect': 'pulse'
        }
    else:
        return {
            'fontsize': 78,
            'color': '#FFFFFF',
            'stroke': 7,
            'effect': 'none'
        }
