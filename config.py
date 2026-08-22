# Config - sab yahi se control hoga
VERIFICATION_THRESHOLD = 0.90

# Trending Weights - configurable
WEIGHTS = {
    "recency": 0.35,
    "source_count": 0.30,
    "reliability": 0.20,
    "duplicate_freq": 0.15
}

# Source Reliability Score
SOURCE_RELIABILITY = {
    "reuters": 1.0,
    "apnews": 1.0,
    "bbc": 0.95,
    "npr": 0.95,
    "nbcnews": 0.9,
    "abcnews": 0.9,
    "cbsnews": 0.9,
    "cnn": 0.85,
    "gov": 1.0
}

# RSS Feeds - 100% Free & Legal, No Scraping
RSS_FEEDS = {
    "reuters": "http://feeds.reuters.com/reuters/topNews",
    "apnews": "https://apnews.com/hub/ap-top-news?utm_source=apnews.com&utm_medium=feed",
    "bbc": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
    "npr": "https://feeds.npr.org/1001/rss.xml",
    "nbcnews": "http://feeds.nbcnews.com/nbcnews/public/news",
    "abcnews": "https://abcnews.go.com/abcnews/topstories",
}

# YouTube
YOUTUBE_CATEGORY_ID = "25" # News & Politics
YOUTUBE_PRIVACY = "public" # public / private / unlisted

# Video
VIDEO_W, VIDEO_H = 1080, 1920 # Shorts format - fast rendering
MAX_VIDEO_DURATION = 60

# Paths
DB_PATH = "data/news_history.db"
OUTPUT_DIR = "output"
