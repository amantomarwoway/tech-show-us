import re

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_us_topic(text: str) -> bool:
    if not text: return False
    low = text.lower()
    blocked = ['germany', 'merz', 'canada']
    for b in blocked:
        if b in low and not any(k in low for k in ['trump', 'white house', 'usa']):
            return False
    return True

def get_all_breakouts_any_topic():
    try:
        from news_fetcher import fetch_all_news
    except ImportError:
        try:
            from src.news_fetcher import fetch_all_news
        except:
            return []
    return fetch_all_news()
