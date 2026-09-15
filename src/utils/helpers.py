"""
src/utils/helpers.py - Common utilities
"""

import re
import hashlib
from datetime import datetime


def clean_text(text):
    """Clean text for processing"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def clean_id(text):
    """Remove Google Knowledge Graph IDs"""
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def text_hash(text):
    """Generate hash for text"""
    return hashlib.md5(text.encode()).hexdigest()


def safe_filename(text, max_len=50):
    """Convert text to safe filename"""
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text[:max_len]


def time_ago(timestamp_str):
    """Human-readable time ago"""
    try:
        from dateutil import parser
        dt = parser.parse(timestamp_str)
        diff = datetime.now() - dt.replace(tzinfo=None)
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{int(seconds/60)}m ago"
        elif seconds < 86400:
            return f"{int(seconds/3600)}h ago"
        else:
            return f"{int(seconds/86400)}d ago"
    except:
        return "recently"


def truncate(text, max_len=100, suffix="..."):
    """Truncate text"""
    if not text or len(text) <= max_len:
        return text
    return text[:max_len - len(suffix)].rsplit(' ', 1)[0] + suffix
