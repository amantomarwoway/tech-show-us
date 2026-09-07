"""
CONFIG.PY - RETENTION + VALIDATION FACTORY + MARKET HUNGERNESS + VvSA + SOUND RETENTION
Location: src/config.py or config.py
Edits: All new retention constants added, old preserved
"""
import os, random
VERIFICATION_THRESHOLD=0.90
WEIGHTS={"recency":0.35,"source_count":0.30,"reliability":0.20,"duplicate_freq":0.15}

# --- ADD-ON Problem 6 + E+I START - google_news_us_live ko trusted banao ---
SOURCE_RELIABILITY={"reuters":1.0,"apnews":1.0,"bbc":0.95,"npr":0.95,"nbcnews":0.9,"abcnews":0.9,"cbsnews":0.9,"cnn":0.85,"gov":1.0,"google_trends_usa":0.95,"google_news_us_live":0.90,"youtube_search":0.90}
# --- END ---

# ===== NEW RETENTION CONSTANTS - SABSE MAIN =====
RETENTION_CONFIG = {
    "WORDS_TARGET": 40,
    "WORDS_MIN": 35,
    "WORDS_MAX": 45,
    "DURATION_TARGET": 12,  # 11-13 sec
    "DURATION_MIN": 11,
    "DURATION_MAX": 13,
    "CLIP_DENSITY": 0.8,  # har 0.8 sec pe naya clip - fast pacing
    "TTS_SPEED": 1.15,
    "TTS_PITCH_SEMITONES": 1.2,
    "FPS_CHOICES": [29.97, 29.98, 59.94, 59.95],  # NTSC for YT avoid
    "NOISE_HUE_FILTER": "noise=alls=5:allf=t:allf=t:allp=7,hue=h=2:s=1.08",
    "FPS": 30,
    "AUDIO_PUNCH_FIRST_SEC": 1.5,  # 150%
    "VOL_MOD_EVERY_SEC": 3,
    "VOL_MOD_PERCENT": 0.05,
    "BASS_BOOST": "bass=g=3:f=100"
}

# Validation Factory
VALIDATION_FACTORY_CONFIG = {
    "MANDATORY_KEYWORDS": ["behind closed doors", "leaked", "secret", "inside sources"],
    "FIRST_TO_KNOW": ["first to know"],
    "BOLD_CLAIMS": ["this changes everything","you won't believe","shocked everyone","this is huge","nobody saw this coming","game changer"],
    "TWIST_ONLY": True,
    "SECRET_LEAK_ANGLE_MANDATORY": True
}

# Market Hungerness
MARKET_HUNGERNESS_CONFIG = {
    "enabled": True,
    "vol_threshold_hungry": 60,
    "vol_threshold_medium": 45,
    "vol_threshold_low": 30,
    "hungry_keywords": ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","just leaked"],
    "freshness_threshold_hours": 6
}

# Pexel Randomisation + Anti-bot
PEXELS_RANDOM_CONFIG = {
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
YOUTUBE_CATEGORY_ID="25" # US LOCK - News & Politics
YOUTUBE_PRIVACY="public"
YOUTUBE_API_KEY=os.getenv("YOUTUBE_API_KEY","")
YOUTUBE_CLIENT="youtube"
YOUTUBE_DS="yt"
YOUTUBE_GL="US"
YOUTUBE_HL="en"
VIDEO_W,VIDEO_H=1080,1920
MAX_VIDEO_DURATION=15  # CHANGED: 60 se 15 kiya - retention 11-13 sec lock
TARGET_MINUTES=int(os.getenv("TARGET_MINUTES","10"))
TARGET_MAX_MINUTES=int(os.getenv("TARGET_MAX_MINUTES","14"))
DB_PATH="data/news_history.db"
OUTPUT_DIR="output"
OUTPUT_LONG_DIR="output_long"
CLIPS_DIR="clips"
AUDIO_DIR="audio"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
PEXELS_API_KEY=os.getenv("PEXELS_API_KEY","") or os.getenv("PEXELS_KEY","")
THRESHOLD=70  # 75 se 70 kiya
TREND_LIMIT_SHORTS=30
BOT_FRIENDLY_THRESHOLD=60  # 70 se 60
CHANNEL_NAME=os.getenv("CHANNEL_NAME","Uncovered USA")
LOG_LEVEL="INFO"

# --- ADD-ON: Problem 6 - US Metadata Lock import (1 line sync) ---
try:
    from youtube_metadata_lock import YOUTUBE_METADATA_LOCK
    YOUTUBE_CATEGORY_ID = YOUTUBE_METADATA_LOCK["categoryId"]
    YOUTUBE_PRIVACY = YOUTUBE_METADATA_LOCK["privacyStatus"]
    print(f"[CONFIG Problem 6] US LOCK Loaded: {YOUTUBE_METADATA_LOCK}")
except:
    # Fallback agar file abhi tak create nahi hui
    YOUTUBE_METADATA_LOCK = {"categoryId":"25","privacyStatus":"public","defaultLanguage":"en","defaultAudioLanguage":"en-US"}
# --- END ---

PEXELS_KEY = PEXELS_API_KEY
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY","") or os.getenv("PIXABAY_KEY","")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY","")

# UPDATED MUSIC_MOOD_MAP with leak/secret
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
    # Random shuffle for anti-bot no same pattern
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
    "duration": 1  # CHANGED: 2 se 1 kiya - retention
}

# NEW: Retention check helper
def check_retention_words(text: str) -> bool:
    wc = len(text.split())
    return RETENTION_CONFIG["WORDS_MIN"] <= wc <= RETENTION_CONFIG["WORDS_MAX"]

def check_validation_factory(text: str) -> bool:
    low = text.lower()
    has_leak = any(k in low for k in ["leak","behind closed doors","secret","inside"])
    has_first = "first to know" in low or ("first" in low and "know" in low)
    has_bold = any(b in low for b in VALIDATION_FACTORY_CONFIG["BOLD_CLAIMS"])
    return has_leak and has_bold
