"""
src/config.py - AUTONOMOUS BOT CONFIG v4
- Duration capped at 20s (memory safety for GitHub Actions)
- Faster TTS speed
"""

import os

GOD_INSTRUCTION = """
AUTONOMOUS YOUTUBE SHORTS BOT
Goal: MAXIMIZE views + engagement + subscribers
Method: Learn from data, self-optimize, self-repair
"""

ENGLISH_COUNTRIES = ["US", "GB", "CA", "AU", "NZ", "IE"]
ENGLISH_COUNTRIES_HALF = ["US", "GB", "CA", "AU", "NZ", "IE", "IN", "PH", "SG", "ZA"]
TARGET_COUNTRIES = ENGLISH_COUNTRIES + ["IN", "PH", "SG", "ZA", "NG", "KE"]

PUBLISH_THRESHOLDS = {
    "publish": 65, "high_priority": 60, "medium": 50, "monitor": 40, "reject": 0
}

HARD_GATES = {"truth_confidence": 65, "policy_safety": 85, "source_credibility": 55}

STORY_SCORE_WEIGHTS = {
    "trend_momentum": 0.35, "audience_relevance": 0.15, "news_importance": 0.05,
    "curiosity": 0.20, "novelty": 0.10, "visual_potential": 0.05,
    "search_potential": 0.05, "competition_opportunity": 0.05
}

STORY_TYPE_WEIGHTS = {
    "trending": {"trend_momentum": 0.45, "audience_relevance": 0.15, "news_importance": 0.00, "curiosity": 0.25, "novelty": 0.05, "visual_potential": 0.05, "search_potential": 0.05, "competition_opportunity": 0.00},
    "viral": {"trend_momentum": 0.40, "audience_relevance": 0.15, "news_importance": 0.00, "curiosity": 0.30, "novelty": 0.05, "visual_potential": 0.05, "search_potential": 0.05, "competition_opportunity": 0.00},
    "news": {"trend_momentum": 0.35, "audience_relevance": 0.20, "news_importance": 0.15, "curiosity": 0.15, "novelty": 0.05, "visual_potential": 0.05, "search_potential": 0.05, "competition_opportunity": 0.00}
}

# ✅ FIXED: Duration capped at 20s for memory safety
VIDEO_CONFIG = {
    "WIDTH": 1080, "HEIGHT": 1920, "WHITE_BAR_HEIGHT": 210,
    "BLACK_TOP_STRIP": 180, "BLACK_BOTTOM_STRIP": 200,
    "BLACK_BORDER": 16, "CORNER_RADIUS": 38,
    "CLIP_DENSITY": 0.8,
    "DURATION_MIN": 12, "DURATION_MAX": 20,   # ← Capped at 20s
    "FPS_CHOICES": [29.97, 29.98, 59.94, 59.95],
    "FIRST_WORDS_PUNCH": 1.4, "KEYWORD_PUNCH": 1.2, "OVERLAP": 0.92,
    "TTS_SPEED": 1.15, "WORDS_TARGET": 50     # ← 80 → 50 words
}

# ✅ FIXED: Faster TTS speeds for shorter audio
TTS_CONFIG = {
    "model_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
    "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
    "model_path": "models/en_US-ryan-medium.onnx",
    "config_path": "models/en_US-ryan-medium.onnx.json",
    "length_scale": 1.0, "noise_scale": 0.6, "noise_w_scale": 0.75,
    "speed_choices": [1.15, 1.2, 1.25],        # ← Faster speeds
    "american_filter": "afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=50:release=200,volume=1.2"
}

YOUTUBE_CONFIG = {
    "category_id": "24", "privacy": "public",
    "comment_bait": "What do you think? Comment below!",
    "description_hooks": ["Wait till end!", "This is what everyone is talking about!"],
    "max_tags": 15, "max_hashtags": 3
}

FACT_CHECKER_CONFIG = {
    "min_score": 2500, "high_score": 4000, "guaranteed_score": 4500,
    "min_volume": 50, "high_volume": 70, "pass_count_required": 2,
    "lenient_boost_keywords": ["viral", "trending", "shocking", "breaking"]
}

RSS_FEEDS = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=trending&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=viral&hl=en-US&gl=US&ceid=US:en",
    "https://variety.com/feed/", "https://www.hollywoodreporter.com/feed/",
    "https://deadline.com/feed/", "https://www.espn.com/espn/rss/news",
    "https://sports.yahoo.com/rss/", "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml", "https://www.wired.com/feed/rss",
    "https://pitchfork.com/feed/feed-news/rss", "https://www.rollingstone.com/feed/",
    "https://www.ign.com/rss/articles", "https://www.polygon.com/rss/index.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://feeds.npr.org/1001/rss.xml", "https://www.buzzfeed.com/index.xml",
    "https://knowyourmeme.com/news/feed"
]

TREND_CONFIG = {
    "geo": "US", "timeframe": "now 4-H", "min_interest": 30,
    "breakout_threshold": 3000, "momentum_window": 2, "trending_topics_count": 20
}

REDDIT_SUBREDDITS = ["all", "popular", "trending", "entertainment", "movies", "music", "gaming", "sports", "technology", "memes", "viral"]

GOOGLE_NEWS_QUERIES = ["trending", "viral", "breaking", "shocking", "everyone talking about", "why trending", "went viral"]

LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/bot.log", "max_bytes": 10 * 1024 * 1024, "backup_count": 5
}

DATABASE_CONFIG = {
    "path": "data/news_bot.db", "timeout": 30, "check_same_thread": False
}

TIER1_SOURCES = ["whitehouse.gov", "supremecourt.gov", "congress.gov", "senate.gov", "un.org", "who.int"]
TIER2_SOURCES = ["reuters.com", "apnews.com", "bbc.com", "npr.org", "cnn.com", "nytimes.com", "theguardian.com"]
TIER3_SOURCES = ["bloomberg.com", "wsj.com", "ft.com", "techcrunch.com", "theverge.com"]

VISUAL_CONFIG = {
    "pexels_api_key": os.getenv("PEXELS_API_KEY", ""),
    "pixabay_api_key": os.getenv("PIXABAY_API_KEY", ""),
    "unsplash_api_key": os.getenv("UNSPLASH_API_KEY", ""),
    "giphy_api_key": os.getenv("GIPHY_API_KEY", ""),
    "preferred_orientation": "portrait", "preferred_size": "medium",
    "min_duration": 0.5, "max_duration": 2.0, "license_check_enabled": True
}

GLOBAL_RELEVANCE_WEIGHTS = {
    "population_affected": 0.25, "economic_impact": 0.20, "geopolitical_importance": 0.20,
    "cultural_interest": 0.15, "international_consequences": 0.10, "english_search_demand": 0.10
}

VIRAL_KEYWORDS = ["breaking", "shocking", "leaked", "secret", "exposed", "revealed", "viral", "trending", "everyone", "massive", "huge", "just happened"]

TOP_REAL_SOURCES = ["google_trends_breakout", "google_trends_trending_now", "google_news_us_live", "guaranteed_google_news", "reddit_rising_breakout", "cnn_breaking"]

AUTONOMOUS_MODE = True

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

PATHS = {
    "data": "data", "models": "models", "output": "output",
    "output_videos": "output/videos", "output_thumbnails": "output/thumbnails",
    "temp": "temp", "logs": "logs", "cache": "data/cache"
}

def ensure_directories():
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

ensure_directories()

def get_env(key, default=""):
    return os.getenv(key, default)
