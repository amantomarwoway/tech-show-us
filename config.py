"""
config.py - FINAL SHORT BOT - Filter A+B+C + Viral Structure
"""

import os

# ========== VERIFICATION ==========
VERIFICATION_THRESHOLD = 0.90

# ========== TRENDING WEIGHTS ==========
WEIGHTS = {
    "recency": 0.35,
    "source_count": 0.30,
    "reliability": 0.20,
    "duplicate_freq": 0.15
}

# ========== SOURCE RELIABILITY ==========
SOURCE_RELIABILITY = {
    "reuters": 1.0,
    "apnews": 1.0,
    "bbc": 0.95,
    "npr": 0.95,
    "nbcnews": 0.9,
    "abcnews": 0.9,
    "cbsnews": 0.9,
    "cnn": 0.85,
    "gov": 1.0,
    "google_trends_usa": 0.95,
    "google_trends": 0.95,
    "filter_a_youtube_breakout": 1.0,
    "filter_b_autocomplete": 0.95,
    "filter_c_bot_friendly": 0.95
}

# ========== RSS FEEDS ==========
RSS_FEEDS = {
    "reuters": "http://feeds.reuters.com/reuters/topNews",
    "apnews": "https://apnews.com/hub/ap-top-news?utm_source=apnews.com&utm_medium=feed",
    "bbc": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
    "npr": "https://feeds.npr.org/1001/rss.xml",
    "nbcnews": "http://feeds.nbcnews.com/nbcnews/public/news",
    "abcnews": "https://abcnews.go.com/abcnews/topstories",
}

# ========== GOOGLE TRENDS - Filter A ==========
GOOGLE_TRENDS_GEO = "US"
GOOGLE_TRENDS_URL = "https://trends.google.com/trending/rss?geo=US"
TREND_LIMIT = 30
GOOGLE_TRENDS_YOUTUBE_GPROP = "youtube"
GOOGLE_TRENDS_TIMEFRAME = "now 7-d"

# ========== YOUTUBE - Filter B + C ==========
YOUTUBE_CATEGORY_ID = "25"
YOUTUBE_PRIVACY = "public"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YOUTUBE_CLIENT = "youtube"
YOUTUBE_DS = "yt"
YOUTUBE_GL = "US"
YOUTUBE_HL = "en"

YOUTUBE_AUTOCOMPLETE_SEEDS = [
    "breaking news usa",
    "why is",
    "what happened today",
    "trump news",
    "weather alert usa"
]

FILTER_C_DAYS = 7
FILTER_C_MIN_FACELESS_RATIO = 0.3
FILTER_C_BOT_FRIENDLY_THRESHOLD = 70

# ========== VIDEO SETTINGS - Shorts 9:16 ==========
VIDEO_W, VIDEO_H = 1080, 1920
MAX_VIDEO_DURATION = 60
TARGET_MINUTES = int(os.getenv("TARGET_MINUTES", "10"))
TARGET_MAX_MINUTES = int(os.getenv("TARGET_MAX_MINUTES", "14"))

# ========== PATHS ==========
DB_PATH = "data/news_history.db"
OUTPUT_DIR = "output"
OUTPUT_LONG_DIR = "output_long"
CLIPS_DIR = "clips"
AUDIO_DIR = "audio"

# ========== API KEYS ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "") or os.getenv("PEXELS_KEY", "")

# ========== SHORTS GATE THRESHOLDS ==========
THRESHOLD = 75
TREND_LIMIT_SHORTS = 30
BOT_FRIENDLY_THRESHOLD = 70

CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Uncovered USA")
LOG_LEVEL = "INFO"

VIRAL_SHORT_STRUCTURE = {
    "hook_0_3s": "Shocking fact, number, FOMO - Stop scroll",
    "context_3_10s": "What, where, who - Specific",
    "conflict_10_25s": "Why, 3 points, why matters + retention words",
    "payoff_25_38s": "Final truth, impact",
    "cta_38_40s": "Comment + subscribe"
}
