# UPDATED JULY 2025 - GEMINI 3.6 FLASH LATEST + CHATGPT FALLBACK gpt-4o-mini - NO SAFE EXIT - NO FORCE PASS
# UPDATED FOR: Wire + Google News 45min + 7-Day Velocity + DuckDuckGo 1.0s + yt-dlp 1.8s + YouTube Search SEO
"""
CONFIG.PY - FIXED AS PER LATEST 15 FILES - RETENTION + VALIDATION FACTORY + MARKET HUNGERNESS + VvSA + SOUND RETENTION
Location: src/config.py
FIXED: https, Gemini 3.6 Flash July, ChatGPT fallback, US only, no overexposure, no safe exit
UPDATED: Reuters Wire + Google News Wire 45min filter, mainstream legacy block, search velocity, SEO over Shorts Feed
"""
import os, random

VERIFICATION_THRESHOLD=0.90
WEIGHTS={"recency":0.35,"source_count":0.30,"reliability":0.20,"duplicate_freq":0.15}

# --- FIXED: Wire + Google News trusted + US ONLY + Mainstream Block ---
SOURCE_RELIABILITY={
    "reuters":1.0,
    "reuters_wire":1.0,
    "google_news_wire":0.95,
    "apnews":1.0,
    "bbc":0.95,
    "npr":0.95,
    "nbcnews":0.9,
    "abcnews":0.9,
    "cbsnews":0.9,
    "cnn":0.85,
    "gov":1.0,
    "duckduckgo_image":0.90,
    "yt_dlp_video":0.90,
    "youtube_search":0.90,
}

# ===== NEW RETENTION CONSTANTS - FIXED NO OVEREXPOSURE + NEW ASSET TIMING =====
RETENTION_CONFIG = {
    "WORDS_TARGET": 45,
    "WORDS_MIN": 40,
    "WORDS_MAX": 50,
    "DURATION_TARGET": 13,
    "DURATION_MIN": 11,
    "DURATION_MAX": 15,
    "CLIP_DENSITY": 1.8,  # video clip 1.8s
    "IMAGE_DURATION": 1.0,  # image 1.0s
    "VIDEO_DURATION": 1.8,  # clip 1.8s
    "TTS_SPEED": 1.15,
    "TTS_PITCH_SEMITONES": 1.2,
    "FPS_CHOICES": [29.97, 30, 59.94, 60],
    "NOISE_HUE_FILTER": "",
    "FPS": 30,
    "AUDIO_PUNCH_FIRST_SEC": 1.5,
    "VOL_MOD_EVERY_SEC": 3,
    "VOL_MOD_PERCENT": 0.05,
    "BASS_BOOST": "bass=g=3:f=100"
}

# ===== WIRE SERVICE & ADVANCED INDEX ENGINE - 45 MIN FILTER =====
WIRE_SERVICE_CONFIG = {
    "enabled": True,
    "fetch_window_minutes": 45,
    "reuters_feeds": [
        "http://feeds.reuters.com/reuters/topNews",
        "http://feeds.reuters.com/reuters/USNews",
        "http://feeds.reuters.com/reuters/politicsNews"
    ],
    "google_news_feeds": [
        "https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=US+politics+OR+white+house+when:1h&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
    ],
    "mainstream_block": [
        "cnn.com", "nytimes.com", "washingtonpost.com", "foxnews.com",
        "msnbc.com", "abcnews.go.com", "cbsnews.com", "nbcnews.com",
        "apnews.com", "bbc.com", "theguardian.com"
    ],
    "us_search_keywords": [
        "trump", "biden", "white house", "supreme court", "executive order",
        "congress", "senate", "pentagon", "fbi", "doj", "tariff", "ban",
        "election", "border", "immigration", "breaking", "leaked", "shocking"
    ],
    "ground_level_first": True,
    "max_search_potential": True
}

# ===== 7-DAY SEARCH VELOCITY FILTER =====
SEARCH_VELOCITY_CONFIG = {
    "enabled": True,
    "filter_name": "7-Day Search Velocity Filter",
    "rule": "Only select stories that an average American will actively type into Google or YouTube to search for explanations, updates, or follow-ups over next 7 days. Reject generic news.",
    "confidence_threshold": 85,
    "is_weekly_search_trend_required": True,
    "reject_generic": True
}

# ===== YOUTUBE SEARCH SEO RULES =====
YOUTUBE_SEARCH_SEO_CONFIG = {
    "enabled": True,
    "focus": "YouTube Search Traffic over Shorts Feed",
    "title_rules": "Highly targeted, high-intent search titles, include year/breaking, under 60 chars",
    "tags_rules": "8-10 high-intent SEO tags, American search behavior",
    "optimize_for": "Search Traffic, not Feed",
    "high_ctr_required": True
}

# Validation Factory - NO FORCE PASS
VALIDATION_FACTORY_CONFIG = {
    "MANDATORY_KEYWORDS": ["behind closed doors", "leaked", "secret", "inside sources"],
    "FIRST_TO_KNOW": ["first to know"],
    "BOLD_CLAIMS": ["this changes everything","you won't believe","shocked everyone","this is huge","nobody saw this coming","game changer"],
    "TWIST_ONLY": True,
    "SECRET_LEAK_ANGLE_MANDATORY": True,
    "NO_FORCE_PASS": True
}

# Market Hungerness - US ONLY
MARKET_HUNGERNESS_CONFIG = {
    "enabled": True,
    "vol_threshold_hungry": 60,
    "vol_threshold_medium": 45,
    "vol_threshold_low": 30,
    "hungry_keywords": ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","just leaked"],
    "freshness_threshold_hours": 1,
    "us_only": True,
    "blocked_countries": ["germany", "canada", "german", "merz"]
}

# Asset Gathering - DuckDuckGo + yt-dlp (Pexels replaced)
ASSET_GATHERING_CONFIG = {
    "engine": "duckduckgo + yt-dlp",
    "image_duration": 1.0,
    "clip_duration": 1.8,
    "search_type": "exact visual search as per script_visual_segments",
    "visual_search_prompt_required": True,
    "asset_types": ["video", "image"],
    "youtube_search_seo_focus": True,
    "shorts_feed_focus": False,
    "per_page_choices": [3,5],
    "orientation": "portrait",
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    ],
    "delay_min": 0.1,
    "delay_max": 0.3
}

# Legacy Pexels config kept for fallback compatibility but disabled
PEXELS_RANDOM_CONFIG = {
    "enabled": False,
    "per_page_choices": [5,8,12],
    "random_suffixes": ["", " 4k", " cinematic", " news", " usa"],
    "orientation_choices": ["portrait","landscape",""],
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ],
    "delay_min": 0.1,
    "delay_max": 0.4
}

# VvSA + Fonts + Colours + Frame Variation
VvSA_CONFIG = {
    "FONT_LIST": ["Anton", "BebasNeue", "Oswald", "Montserrat-ExtraBold", "Impact"],
    "COLOR_LIST": ["#FF3B30", "#FFD60A", "#30D158", "#0A84FF", "#FF2D55", "#FFFFFF"],
    "SHOCK_FIRST_FRAME_DURATION": 0.3,
    "SHOCK_ZOOM": 1.3,
    "GLITCH_EVERY_SEC": 3,
    "FRAME_VARIATION_ENABLED": True
}

# FIXED: Wire Service + Google Index + 45 min
RSS_FEEDS={
    "reuters_wire": "http://feeds.reuters.com/reuters/topNews",
    "reuters_us": "http://feeds.reuters.com/reuters/USNews",
    "google_news_wire": "https://news.google.com/rss/search?q=breaking+news+US+when:1h&hl=en-US&gl=US&ceid=US:en"
}
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
MAX_VIDEO_DURATION=15
TARGET_MINUTES=int(os.getenv("TARGET_MINUTES","10"))
TARGET_MAX_MINUTES=int(os.getenv("TARGET_MAX_MINUTES","14"))
DB_PATH="data/news_history.db"
OUTPUT_DIR="output"
OUTPUT_LONG_DIR="output_long"
CLIPS_DIR="clips"
AUDIO_DIR="audio"

# GEMINI 3.6 FLASH JULY 2025 + CHATGPT FALLBACK - NEW
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","")
GEMINI_MODELS_36_FLASH=[
    "gemini-3.6-flash",
    "gemini-3.6-flash-latest",
    "gemini-3.6-flash-exp",
    "gemini-2.5-flash",
    "gemini-2.5-flash-latest",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest"
]
CHATGPT_FALLBACK_MODELS=[
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-3.5-turbo",
    "gpt-4-turbo"
]
GEMINI_CONFIG={
    "temperature":0.9,
    "max_tokens":800,
    "models":GEMINI_MODELS_36_FLASH,
    "fallback":CHATGPT_FALLBACK_MODELS,
    "no_force_pass":True
}

PEXELS_API_KEY=os.getenv("PEXELS_API_KEY","") or os.getenv("PEXELS_KEY","")
THRESHOLD=70
TREND_LIMIT_SHORTS=30
BOT_FRIENDLY_THRESHOLD=60
CHANNEL_NAME=os.getenv("CHANNEL_NAME","Uncovered USA")
LOG_LEVEL="INFO"

# US LOCK - News & Politics
try:
    from youtube_metadata_lock import YOUTUBE_METADATA_LOCK
    YOUTUBE_CATEGORY_ID = YOUTUBE_METADATA_LOCK["categoryId"]
    YOUTUBE_PRIVACY = YOUTUBE_METADATA_LOCK["privacyStatus"]
    print(f"[CONFIG Problem 6] US LOCK Loaded: {YOUTUBE_METADATA_LOCK}")
except:
    YOUTUBE_METADATA_LOCK = {"categoryId":"25","privacyStatus":"public","defaultLanguage":"en","defaultAudioLanguage":"en-US"}

PEXELS_KEY = PEXELS_API_KEY
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY","") or os.getenv("PIXABAY_KEY","")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY","")

# UPDATED MUSIC_MOOD_MAP
MUSIC_MOOD_MAP = {
    "breaking": "tense dramatic news",
    "shocking": "tense dramatic suspense shock",
    "crash": "dark cinematic grave tense",
    "dies": "sad piano emotional grave dark",
    "death": "sad piano emotional grave",
    "killed": "sad dramatic grave",
    "arrest": "tense crime thriller police",
    "court": "serious dramatic tense",
    "trump": "epic dramatic news",
    "biden": "serious news background",
    "election": "tense political drama",
    "happy": "uplifting happy inspirational",
    "wins": "celebration uplifting victory",
    "heroic": "epic uplifting heroic",
    "rescue": "uplifting hopeful",
    "leaked": "mystery tension secret leaked",
    "secret": "mystery tension secret leaked",
    "behind closed doors": "mystery tension secret behind doors",
    "exposed": "tense reveal shock",
    "revealed": "mystery tension reveal",
    "default": "news background corporate tense"
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
    "explosion": "explosion.mp3",
    "leaked": "secret_reveal.mp3",
    "secret": "secret_reveal.mp3",
    "behind": "mystery_hit.mp3",
    "exposed": "shock_hit.mp3",
    "revealed": "reveal_punch.mp3"
}

def get_music_mood_from_topic(topic: str) -> str:
    topic_l = str(topic).lower()
    keys = list(MUSIC_MOOD_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key!= "default" and key in topic_l:
            return MUSIC_MOOD_MAP[key]
    return MUSIC_MOOD_MAP["default"]

def get_sfx_for_script(script_text: str):
    txt = str(script_text).lower()
    keys = list(SFX_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key in txt:
            return SFX_MAP[key]
    return None

def get_random_fps():
    return random.choice(RETENTION_CONFIG["FPS_CHOICES"])

def get_random_font():
    return random.choice(VvSA_CONFIG["FONT_LIST"])

def get_random_color():
    return random.choice(VvSA_CONFIG["COLOR_LIST"])

CAPTION_STYLE = {
    "font": "DejaVuSans-Bold",
    "font_size": 72,
    "primary_color": "white",
    "highlight_color": "#FFE600",
    "stroke_color": "black",
    "stroke_width": 4,
    "bottom_margin": 140,
    "random_fonts": VvSA_CONFIG["FONT_LIST"],
    "random_colors": VvSA_CONFIG["COLOR_LIST"]
}
OUTRO_CONFIG = {
    "channel": "UNCOVERED USA 24",
    "cta": "LIKE SHARE SUBSCRIBE COMMENT NOW",
    "duration": 1
}

def check_retention_words(text: str) -> bool:
    wc = len(text.split())
    return RETENTION_CONFIG["WORDS_MIN"] <= wc <= RETENTION_CONFIG["WORDS_MAX"]

def check_validation_factory(text: str) -> bool:
    low = text.lower()
    has_leak = any(k in low for k in ["leak","behind closed doors","secret","inside"])
    has_first = "first to know" in low or ("first" in low and "know" in low)
    has_bold = any(b in low for b in VALIDATION_FACTORY_CONFIG["BOLD_CLAIMS"])
    return has_leak and has_bold

def is_us_topic_config(text: str) -> bool:
    if not text: return False
    low = text.lower()
    blocked = ["germany", "merz", "canada", "canadian", "german"]
    for b in blocked:
        if b in low and not any(k in low for k in ["trump", "white house", "usa", "america", "supreme court"]):
            return False
    return True


# ===== GOD LEVEL COMPATIBILITY ALIASES - For research_god.py =====
# Expose WIRE_SERVICE_CONFIG as top-level lists expected by research_god
REUTERS_FEEDS = WIRE_SERVICE_CONFIG.get("reuters_feeds", [])
GOOGLE_NEWS_WIRE = WIRE_SERVICE_CONFIG.get("google_news_feeds", [])
MAINSTREAM_BLOCK = WIRE_SERVICE_CONFIG.get("mainstream_block", [])
FETCH_WINDOW_MINUTES = WIRE_SERVICE_CONFIG.get("fetch_window_minutes", 45)
US_SEARCH_TRIGGERS = WIRE_SERVICE_CONFIG.get("us_search_keywords", [])
WORLD_VIRAL_TAGS = ["breakingnews","worldnews","viralnews","usanews","globalupdate","newsupdate","trending","explained","breaking news US","world news today","news explained"]
ENGLISH_COUNTRIES = ["USA","UK","Canada","Australia","India","Philippines","South Africa","New Zealand","Ireland","Singapore"]
GOD_INSTRUCTION = "HAR LEG HAR CHEEZ KAHIN SE BHI BEST TARIKE SE USE KARE - Editor aur sabhi legs"
