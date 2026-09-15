"""
src/config.py - GOD LEVEL CONFIG
All settings for the bot
"""

import os

"""
src/config.py - GOD LEVEL CONFIG
"""

import os

# ============================================================
# 🚨 CRITICAL FIX: Pillow 10+ compatibility for MoviePy 1.0.3
# ============================================================
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
if not hasattr(Image, 'BICUBIC'):
    Image.BICUBIC = Image.Resampling.BICUBIC
if not hasattr(Image, 'BILINEAR'):
    Image.BILINEAR = Image.Resampling.BILINEAR
if not hasattr(Image, 'NEAREST'):
    Image.NEAREST = Image.Resampling.NEAREST
# ============================================================

# ... rest of config

# ============================================================
# GOD LEVEL INSTRUCTION
# ============================================================

GOD_INSTRUCTION = """
GOD LEVEL YOUTUBE SHORTS BOT - Zero Cost, Maximum Automation

MISSION: Create high-quality, fact-checked, globally relevant YouTube Shorts
that maximize viewer satisfaction and session watch time.

CORE PRINCIPLES:
1. TRUTH FIRST - Never publish unverified claims
2. GLOBAL AUDIENCE - English-first, not US-only
3. ZERO COST - Use free tiers and open source
4. FAIL SAFE - Every component has fallback
5. LEARN & IMPROVE - Use analytics to get better

PIPELINE (5 LEGS):
Leg 1 - Research God: Multi-source news collection + trend detection
Leg 2 - Editor God: Best visual assets from free sources
Leg 3 - Boss Approval: Quality gate + final approval
Leg 4 - Uploader God: YouTube upload + metadata optimization
Leg 5 - Self Evolution: Learn from performance data

QUALITY GATES (HARD):
- Truth confidence must be >= 85
- Policy safety must be >= 90
- Final score must be >= 70

Never compromise truth for virality.
"""

# ============================================================
# TARGET COUNTRIES
# ============================================================

# Primary English-speaking countries
ENGLISH_COUNTRIES = ["US", "GB", "CA", "AU", "NZ", "IE"]

# English + significant English understanding
ENGLISH_COUNTRIES_HALF = ["US", "GB", "CA", "AU", "NZ", "IE", "IN", "PH", "SG", "ZA"]

# All target countries for global relevance
TARGET_COUNTRIES = ENGLISH_COUNTRIES + ["IN", "PH", "SG", "ZA", "NG", "KE"]

# ============================================================
# PUBLISH THRESHOLDS
# ============================================================

PUBLISH_THRESHOLDS = {
    "publish": 75,          # Publish immediately
    "high_priority": 65,   # High priority
    "medium": 55,          # Publish if resources available
    "monitor": 45,         # Monitor for later
    "reject": 0            # Reject
}

# Hard gates (cannot be overridden by high viral score)
HARD_GATES = {
    "truth_confidence": 85,
    "policy_safety": 90,
    "source_credibility": 70
}

# ============================================================
# STORY SCORING WEIGHTS
# ============================================================

STORY_SCORE_WEIGHTS = {
    "trend_momentum": 0.25,
    "audience_relevance": 0.20,
    "news_importance": 0.15,
    "curiosity": 0.15,
    "novelty": 0.10,
    "visual_potential": 0.05,
    "search_potential": 0.05,
    "competition_opportunity": 0.05
}

# Dynamic weight adjustments by story type
STORY_TYPE_WEIGHTS = {
    "breaking": {
        "trend_momentum": 0.35,
        "audience_relevance": 0.20,
        "news_importance": 0.20,
        "curiosity": 0.10,
        "novelty": 0.05,
        "visual_potential": 0.05,
        "search_potential": 0.05,
        "competition_opportunity": 0.00
    },
    "evergreen": {
        "trend_momentum": 0.10,
        "audience_relevance": 0.25,
        "news_importance": 0.10,
        "curiosity": 0.20,
        "novelty": 0.10,
        "visual_potential": 0.10,
        "search_potential": 0.10,
        "competition_opportunity": 0.05
    },
    "political": {
        "trend_momentum": 0.20,
        "audience_relevance": 0.25,
        "news_importance": 0.20,
        "curiosity": 0.15,
        "novelty": 0.05,
        "visual_potential": 0.05,
        "search_potential": 0.05,
        "competition_opportunity": 0.05
    },
    "geopolitical": {
        "trend_momentum": 0.25,
        "audience_relevance": 0.25,
        "news_importance": 0.20,
        "curiosity": 0.10,
        "novelty": 0.10,
        "visual_potential": 0.05,
        "search_potential": 0.05,
        "competition_opportunity": 0.00
    },
    "tech": {
        "trend_momentum": 0.20,
        "audience_relevance": 0.20,
        "news_importance": 0.10,
        "curiosity": 0.20,
        "novelty": 0.15,
        "visual_potential": 0.05,
        "search_potential": 0.05,
        "competition_opportunity": 0.05
    }
}

# ============================================================
# VIDEO CONFIG
# ============================================================

VIDEO_CONFIG = {
    "WIDTH": 1080,
    "HEIGHT": 1920,
    "WHITE_BAR_HEIGHT": 210,
    "BLACK_TOP_STRIP": 150,
    "BLACK_BOTTOM_STRIP": 200,
    "BLACK_BORDER": 16,
    "CORNER_RADIUS": 38,
    "CLIP_DENSITY": 0.8,        # 0.8s per clip for retention
    "DURATION_MIN": 11,
    "DURATION_MAX": 15,
    "FPS_CHOICES": [29.97, 29.98, 59.94, 59.95],  # NTSC standard
    "FIRST_WORDS_PUNCH": 1.4,   # First 5 words 1.4x longer
    "KEYWORD_PUNCH": 1.2,
    "OVERLAP": 0.92,
    "TTS_SPEED": 1.15,          # 1.15X for retention
    "WORDS_TARGET": 40          # 40 words = 11-13 sec
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
    "category_id": "25",  # News & Politics
    "privacy": "public",
    "comment_bait": "🚨 Do you think this is fair? Comment below - Subscribe before this gets deleted! 🔔",
    "description_hooks": [
        "🚨 Wait till end - last part will shock you!",
        "💥 This affects you directly!",
        "👇 Do you think this is fair? Comment below 👇",
        "🔔 Subscribe for more breaking news!"
    ],
    "max_tags": 15,
    "max_hashtags": 5
}

# ============================================================
# FACT CHECKER CONFIG
# ============================================================

FACT_CHECKER_CONFIG = {
    "min_score": 4000,
    "high_score": 5000,
    "guaranteed_score": 5500,
    "min_volume": 70,
    "high_volume": 80,
    "pass_count_required": 2,  # 2 of 3 pass = video made
    "lenient_boost_keywords": ["white house", "shocking", "brutal", "leaked", "supreme court"]
}

# ============================================================
# SOURCE CONFIG
# ============================================================

# Tier 1: Most authoritative
TIER1_SOURCES = [
    "whitehouse.gov",
    "supremecourt.gov",
    "congress.gov",
    "senate.gov",
    "house.gov",
    "state.gov",
    "defense.gov",
    "justice.gov",
    "treasury.gov",
    "un.org",
    "who.int",
    "worldbank.org",
    "imf.org"
]

# Tier 2: Major news agencies
TIER2_SOURCES = [
    "reuters.com",
    "apnews.com",
    "bbc.com",
    "bbc.co.uk",
    "afp.com",
    "npr.org",
    "pbs.org",
    "cnn.com",
    "nytimes.com",
    "washingtonpost.com",
    "theguardian.com",
    "aljazeera.com"
]

# Tier 3: Specialized/industry
TIER3_SOURCES = [
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "economist.com",
    "nature.com",
    "science.org",
    "techcrunch.com",
    "theverge.com",
    "politico.com",
    "thehill.com"
]

# RSS Feeds (free)
RSS_FEEDS = [
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=white+house+breaking&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=world+news+breaking&hl=en-US&gl=US&ceid=US:en",
    "http://rss.cnn.com/rss/cnn_topstories.rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.bbci.co.uk/news/politics/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
    "https://feeds.npr.org/1001/rss.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml"
]

# ============================================================
# TREND CONFIG
# ============================================================

TREND_CONFIG = {
    "geo": "US",
    "timeframe": "now 4-H",
    "min_interest": 40,
    "breakout_threshold": 5000,
    "momentum_window": 2  # Compare last 2 data points
}

# ============================================================
# GLOBAL RELEVANCE CONFIG
# ============================================================

GLOBAL_RELEVANCE_WEIGHTS = {
    "population_affected": 0.25,
    "economic_impact": 0.20,
    "geopolitical_importance": 0.20,
    "cultural_interest": 0.15,
    "international_consequences": 0.10,
    "english_search_demand": 0.10
}

# ============================================================
# VISUAL CONFIG
# ============================================================

VISUAL_CONFIG = {
    "pexels_api_key": os.getenv("PEXELS_API_KEY", ""),
    "pixabay_api_key": os.getenv("PIXABAY_API_KEY", ""),
    "unsplash_api_key": os.getenv("UNSPLASH_API_KEY", ""),
    "giphy_api_key": os.getenv("GIPHY_API_KEY", ""),
    "preferred_orientation": "portrait",
    "preferred_size": "medium",
    "min_duration": 0.5,
    "max_duration": 2.0,
    "license_check_enabled": True
}

# ============================================================
# LOGGING CONFIG
# ============================================================

LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/bot.log",
    "max_bytes": 10 * 1024 * 1024,  # 10 MB
    "backup_count": 5
}

# ============================================================
# DATABASE CONFIG
# ============================================================

DATABASE_CONFIG = {
    "path": "data/news_bot.db",
    "timeout": 30,
    "check_same_thread": False
}

# ============================================================
# API KEYS (from environment)
# ============================================================

def get_api_keys():
    """Get all API keys from environment"""
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
    """Create all required directories"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

# Auto-create directories on import
ensure_directories()
