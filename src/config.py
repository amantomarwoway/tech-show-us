"""
src/config.py - BROAD TRENDING CONFIG
Niche: Any trending topic (not restricted to news/politics)
"""

import os

GOD_INSTRUCTION = """
TRENDING CONTENT BOT - Any Topic, Only Trending

MISSION: Create viral shorts on ANY trending topic.
- Entertainment, sports, music, movies, gaming, memes, viral moments
- Politics, news (only if trending)
- Tech, AI, science
- Whatever is trending #1 anywhere

CORE RULE: Only TRENDING topics. If it's not trending, skip it.
"""

# ============================================================
# TARGET COUNTRIES (for trending detection)
# ============================================================

ENGLISH_COUNTRIES = ["US", "GB", "CA", "AU", "NZ", "IE"]
ENGLISH_COUNTRIES_HALF = ["US", "GB", "CA", "AU", "NZ", "IE", "IN", "PH", "SG", "ZA"]
TARGET_COUNTRIES = ENGLISH_COUNTRIES + ["IN", "PH", "SG", "ZA", "NG", "KE"]

# ============================================================
# PUBLISH THRESHOLDS (trending-focused)
# ============================================================

PUBLISH_THRESHOLDS = {
    "publish": 70,
    "high_priority": 65,
    "medium": 55,
    "monitor": 45,
    "reject": 0
}

HARD_GATES = {
    "truth_confidence": 70,
    "policy_safety": 85,
    "source_credibility": 60
}

# ============================================================
# STORY SCORING WEIGHTS (trending dominant)
# ============================================================

STORY_SCORE_WEIGHTS = {
    "trend_momentum": 0.40,      # HIGHEST - trending is everything
    "audience_relevance": 0.15,
    "news_importance": 0.05,     # LOW - not news-focused
    "curiosity": 0.20,
    "novelty": 0.10,
    "visual_potential": 0.05,
    "search_potential": 0.03,
    "competition_opportunity": 0.02
}

STORY_TYPE_WEIGHTS = {
    "trending": {
        "trend_momentum": 0.50,
        "audience_relevance": 0.15,
        "news_importance": 0.00,
        "curiosity": 0.20,
        "novelty": 0.10,
        "visual_potential": 0.05,
        "search_potential": 0.00,
        "competition_opportunity": 0.00
    },
    "viral": {
        "trend_momentum": 0.45,
        "audience_relevance": 0.15,
        "news_importance": 0.00,
        "curiosity": 0.25,
        "novelty": 0.10,
        "visual_potential": 0.05,
        "search_potential": 0.00,
        "competition_opportunity": 0.00
    },
    "news": {
        "trend_momentum": 0.35,
        "audience_relevance": 0.20,
        "news_importance": 0.15,
        "curiosity": 0.15,
        "novelty": 0.05,
        "visual_potential": 0.05,
        "search_potential": 0.05,
        "competition_opportunity": 0.00
    }
}

# ============================================================
# VIDEO CONFIG
# ============================================================

VIDEO_CONFIG = {
    "WIDTH": 1080,
    "HEIGHT": 1920,
    "WHITE_BAR_HEIGHT": 210,
    "BLACK_TOP_STRIP": 180,
    "BLACK_BOTTOM_STRIP": 200,
    "BLACK_BORDER": 16,
    "CORNER_RADIUS": 38,
    "CLIP_DENSITY": 0.8,
    "DURATION_MIN": 11,
    "DURATION_MAX": 15,
    "FPS_CHOICES": [29.97, 29.98, 59.94, 59.95],
    "FIRST_WORDS_PUNCH": 1.4,
    "KEYWORD_PUNCH": 1.2,
    "OVERLAP": 0.92,
    "TTS_SPEED": 1.15,
    "WORDS_TARGET": 40
}

# ============================================================
# TTS CONFIG
# ============================================================

TTS_CONFIG = {
    "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
    "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
    "model_path": "models/en_US-ryan-medium.onnx",
    "config_path": "models/en_US-ryan-medium.onnx.json",
    "length_scale": 1.25,
    "noise_scale": 0.6,
    "noise_w_scale": 0.75,
    "speed_choices": [1.0, 1.02, 1.03, 1.11, 1.15],
    "american_filter": "afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=50:release=200,volume=1.2"
}

# ============================================================
# YOUTUBE CONFIG
# ============================================================

YOUTUBE_CONFIG = {
    "category_id": "24",  # Entertainment (broader than News)
    "privacy": "public",
    "comment_bait": "🚨 What do you think? Comment below - Subscribe for more! 🔔",
    "description_hooks": [
        "Wait till end - last part will shock you!",
        "This is what everyone is talking about!",
        "Comment your thoughts below!",
        "Subscribe for more trending content!"
    ],
    "max_tags": 15,
    "max_hashtags": 1
}

# ============================================================
# FACT CHECKER CONFIG (relaxed for trending)
# ============================================================

FACT_CHECKER_CONFIG = {
    "min_score": 2500,
    "high_score": 4000,
    "guaranteed_score": 4500,
    "min_volume": 50,
    "high_volume": 70,
    "pass_count_required": 2,
    "lenient_boost_keywords": ["viral", "trending", "shocking", "breaking"]
}

# ============================================================
# RSS FEEDS (broadened - not just news)
# ============================================================

RSS_FEEDS = [
    # Google News (all categories)
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=trending&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=viral&hl=en-US&gl=US&ceid=US:en",
    
    # Entertainment
    "https://variety.com/feed/",
    "https://www.hollywoodreporter.com/feed/",
    "https://deadline.com/feed/",
    
    # Sports
    "https://www.espn.com/espn/rss/news",
    "https://sports.yahoo.com/rss/",
    
    # Tech
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    
    # Music
    "https://pitchfork.com/feed/feed-news/rss",
    "https://www.rollingstone.com/feed/",
    
    # Gaming
    "https://www.ign.com/rss/articles",
    "https://www.polygon.com/rss/index.xml",
    
    # General
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://feeds.npr.org/1001/rss.xml",
    
    # Viral/Social
    "https://www.buzzfeed.com/index.xml",
    "https://knowyourmeme.com/news/feed"
]

# ============================================================
# TREND CONFIG
# ============================================================

TREND_CONFIG = {
    "geo": "US",
    "timeframe": "now 4-H",
    "min_interest": 30,          # LOWERED - accept more trends
    "breakout_threshold": 3000,   # LOWERED
    "momentum_window": 2,
    "trending_topics_count": 20   # Get more trends
}

# ============================================================
# REDDIT TRENDING SUBREDDITS
# ============================================================

REDDIT_SUBREDDITS = [
    "all",           # r/all - everything trending
    "popular",       # r/popular - top trending
    "trending",
    "entertainment",
    "movies",
    "music",
    "gaming",
    "sports",
    "technology",
    "memes",
    "viral",
    "interestingasfuck",
    "nextfuckinglevel",
    "Damnthatsinteresting"
]

# ============================================================
# GOOGLE NEWS SEARCH QUERIES (broadened)
# ============================================================

GOOGLE_NEWS_QUERIES = [
    "trending",
    "viral",
    "breaking",
    "shocking",
    "everyone talking about",
    "why trending",
    "went viral"
]

# ============================================================
# API KEYS
# ============================================================

def get_api_keys():
    return {
        "gemini": os.getenv("GEMINI_API_KEY", ""),
        "openai": os.getenv("OPENAI_API_KEY", ""),
        "pexels": os.getenv("PEXELS_API_KEY", ""),
        "pixabay": os.getenv("PIXABAY_API_KEY", ""),
        "unsplash": os.getenv("UNSPLASH_API_KEY", ""),
        "giphy": os.getenv("GIPHY_API_KEY", ""),
        "youtube_client_id": os.getenv("YT_CLIENT_ID", ""),
        "youtube_client_secret": os.getenv("YT_CLIENT_SECRET", ""),
        "youtube_refresh_token": os.getenv("YT_REFRESH_TOKEN", "")
    }

# ============================================================
# PATHS
# ============================================================

PATHS = {
    "data": "data",
    "models": "models",
    "output": "output",
    "output_videos": "output/videos",
    "output_thumbnails": "output/thumbnails",
    "temp": "temp",
    "logs": "logs",
    "cache": "data/cache"
}

def ensure_directories():
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

ensure_directories()
