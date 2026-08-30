"""
src_long/long_config.py - LONG BOT CONFIG - Separate from shorts config.py
American Audience Design, Human Body Structure
"""

import os

CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Uncovered USA 24")
TARGET_MINUTES = int(os.getenv("TARGET_MINUTES", "7"))  # 6-9 min sweet spot for American long
TARGET_MAX_MINUTES = int(os.getenv("TARGET_MAX_MINUTES", "9"))

# Video format for long - 16:9 (not 9:16 like shorts)
VIDEO_W, VIDEO_H = 1920, 1080

# Human Body Structure Weights
HUMAN_STRUCTURE = {
    "haddiya_skeleton": 0.25,  # Chapter structure
    "maans_muscle": 0.30,      # B-roll + Voice
    "nase_nerves": 0.25,       # Retention + Captions
    "khaal_skin": 0.20         # Branding + Polish
}

# American Audience Triggers
AMERICAN_TRIGGERS = ["breaking", "shocking", "just in", "alert", "huge", "massive", "trump", "biden", "usa", "america"]

# Paths
OUTPUT_LONG_DIR = "output_long"
CLIPS_DIR = "clips_long"
AUDIO_DIR = "audio_long"
TEMP_DIR = "temp/long"

# API Keys (same env as shorts, but separate config)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "") or os.getenv("PEXELS_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# YouTube
YOUTUBE_CATEGORY_ID = "25"  # News & Politics
YOUTUBE_PRIVACY = "public"

# Thumbnail
THUMBNAIL_W, THUMBNAIL_H = 1280, 720
