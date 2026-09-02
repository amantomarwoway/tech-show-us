import os
VERIFICATION_THRESHOLD=0.90
WEIGHTS={"recency":0.35,"source_count":0.30,"reliability":0.20,"duplicate_freq":0.15}
SOURCE_RELIABILITY={"reuters":1.0,"apnews":1.0,"bbc":0.95,"npr":0.95,"nbcnews":0.9,"abcnews":0.9,"cbsnews":0.9,"cnn":0.85,"gov":1.0,"google_trends_usa":0.95,"youtube_search":0.90}
RSS_FEEDS={"reuters":"http://feeds.reuters.com/reuters/topNews"}
GOOGLE_TRENDS_GEO="US"
GOOGLE_TRENDS_URL="https://trends.google.com/trending/rss?geo=US"
TREND_LIMIT=30
TREND_FILTER_A={"enabled":True,"gprop":"youtube","geo":"US","breakout_threshold":5000}
TREND_FILTER_B={"enabled":True,"half_keyword":True}
TREND_FILTER_C={"enabled":True,"bot_friendly_threshold":70}
TACKO_STYLE={"enabled":True,"segments":{"hook_0_3":{"duration":3},"news_3_15":{"duration":12},"context_15_30":{"duration":15},"cta_30_45":{"duration":15}},"titles":{"count":4}}
DAILY_KEYWORDS_PATH="data/daily_top_100.json"
TOP_KEYWORDS_COUNT=100
YOUTUBE_CATEGORY_ID="25"
YOUTUBE_PRIVACY="public"
YOUTUBE_API_KEY=os.getenv("YOUTUBE_API_KEY","")
YOUTUBE_CLIENT="youtube"
YOUTUBE_DS="yt"
YOUTUBE_GL="US"
YOUTUBE_HL="en"
VIDEO_W,VIDEO_H=1080,1920
MAX_VIDEO_DURATION=60
TARGET_MINUTES=int(os.getenv("TARGET_MINUTES","10"))
TARGET_MAX_MINUTES=int(os.getenv("TARGET_MAX_MINUTES","14"))
DB_PATH="data/news_history.db"
OUTPUT_DIR="output"
OUTPUT_LONG_DIR="output_long"
CLIPS_DIR="clips"
AUDIO_DIR="audio"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
PEXELS_API_KEY=os.getenv("PEXELS_API_KEY","") or os.getenv("PEXELS_KEY","")
THRESHOLD=75
TREND_LIMIT_SHORTS=30
BOT_FRIENDLY_THRESHOLD=70
CHANNEL_NAME=os.getenv("CHANNEL_NAME","Uncovered USA")
LOG_LEVEL="INFO"

# ===== ADD-ON: MUSIC MOOD MAP + SFX MAP (OLD CODE DELETE NAHI KIYA, SIRF ADD KIYA) =====
PEXELS_KEY = PEXELS_API_KEY
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY","") or os.getenv("PIXABAY_KEY","")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY","")

MUSIC_MOOD_MAP = {
    "breaking": "tense dramatic news",
    "shocking": "tense dramatic suspense",
    "crash": "dark cinematic tense",
    "dies": "sad piano emotional",
    "death": "sad piano emotional",
    "killed": "sad dramatic",
    "arrest": "tense crime thriller",
    "court": "serious dramatic",
    "trump": "epic dramatic news",
    "biden": "serious news background",
    "election": "tense political drama",
    "happy": "uplifting happy inspirational",
    "wins": "celebration uplifting victory",
    "heroic": "epic uplifting heroic",
    "rescue": "uplifting hopeful",
    "default": "news background corporate"
}

SFX_MAP = {
    "breaking": "whoosh.mp3",
    "shocking": "boom.mp3",
    "just in": "alert.mp3",
    "alert": "alert.mp3",
    "signed": "cash.mp3",
    "wins": "crowd_cheer.mp3",
    "win": "crowd_cheer.mp3",
    "dies": "sad_violin.mp3",
    "crash": "crash.mp3",
    "explosion": "explosion.mp3"
}

def get_music_mood_from_topic(topic: str) -> str:
    """ADD-ON: mood se music decide karna - topic ke hisab se"""
    topic_l = str(topic).lower()
    for key, mood in MUSIC_MOOD_MAP.items():
        if key != "default" and key in topic_l:
            return mood
    return MUSIC_MOOD_MAP["default"]

def get_sfx_for_script(script_text: str):
    """ADD-ON: script se SFX decide"""
    txt = str(script_text).lower()
    for key, sfx_file in SFX_MAP.items():
        if key in txt:
            return sfx_file
    return None

# OUTRO + CAPTION CONFIG ADD-ON
CAPTION_STYLE = {
    "font": "DejaVuSans-Bold",
    "font_size": 72,
    "primary_color": "white",
    "highlight_color": "#FFE600",
    "stroke_color": "black",
    "stroke_width": 4,
    "bottom_margin": 140
}
OUTRO_CONFIG = {
    "channel": "UNCOVERED USA 24",
    "cta": "LIKE SHARE SUBSCRIBE COMMENT NOW",
    "duration": 2
}
