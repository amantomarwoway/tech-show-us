"""
Config - sab yahi se control hoga
Full version with all required fields
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
    "google_trends": 0.95
}

# ========== RSS FEEDS - 100% Free & Legal ==========
RSS_FEEDS = {
    "reuters": "http://feeds.reuters.com/reuters/topNews",
    "apnews": "https://apnews.com/hub/ap-top-news?utm_source=apnews.com&utm_medium=feed",
    "bbc": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
    "npr": "https://feeds.npr.org/1001/rss.xml",
    "nbcnews": "http://feeds.nbcnews.com/nbcnews/public/news",
    "abcnews": "https://abcnews.go.com/abcnews/topstories",
}

# ========== GOOGLE TRENDS ==========
GOOGLE_TRENDS_GEO = "US"
GOOGLE_TRENDS_URL = "https://trends.google.com/trending/rss?geo=US"
TREND_LIMIT = 30

# ========== DAILY TOP 100 KEYWORDS ==========
DAILY_KEYWORDS_PATH = "data/daily_top_100.json"
TOP_KEYWORDS_COUNT = 100

# ========== YOUTUBE ==========
YOUTUBE_CATEGORY_ID = "25"  # News & Politics
YOUTUBE_PRIVACY = "public"  # public / private / unlisted
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
YT_CLIENT = "youtube"
YOUTUBE_DS = "yt"
YOUTUBE_GL = "US"
YOUTUBE_HL = "en"

# ========== VIDEO SETTINGS ==========
VIDEO_W, VIDEO_H = 1080, 1920  # Shorts format
MAX_VIDEO_DURATION = 60
TARGET_MINUTES = int(os.getenv("TARGET_MINUTES", "10"))
TARGET_MAX_MINUTES = int(os.getenv("TARGET_MAX_MINUTES", "14"))

# ========== PATHS ==========
DB_PATH = "data/news_history.db"
OUTPUT_DIR = "output"
OUTPUT_LONG_DIR = "output_long"
CLIPS_DIR = "clips"
AUDIO_DIR = "audio"

# ========== API KEYS (from env) ==========
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "") or os.getenv("PEXELS_KEY", "")

# ========== SHORTS GATE THRESHOLDS ==========
THRESHOLD = 75
TREND_LIMIT_SHORTS = 30

# ========== LONG VIDEO ==========
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Uncovered USA 24")

# ========== LOGGING ==========
LOG_LEVEL = "INFO"
