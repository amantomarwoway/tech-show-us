"""
Central configuration for WordsThatSpeaks bot.
No secrets live here — only structure, defaults and tunables.
All API keys / tokens are read from environment variables at call sites.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
LOGS_DIR = ROOT_DIR / "logs"
TEMP_DIR = ROOT_DIR / "temp"
SCENES_DIR = TEMP_DIR / "scenes"
ASSETS_DIR = ROOT_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
LUTS_DIR = ASSETS_DIR / "luts"
SFX_DIR = ASSETS_DIR / "sfx"
DB_PATH = DATA_DIR / "words.db"

for d in (DATA_DIR, OUTPUT_DIR, LOGS_DIR, TEMP_DIR, SCENES_DIR, MUSIC_DIR, LUTS_DIR, SFX_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# LLM models
# ---------------------------------------------------------------------------
# NOTE: verify these are still live in Google AI Studio before relying on them —
# model naming/availability changes over time and this list can go stale.
GEMINI_PRIMARY_MODEL = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.7-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SEMANTIC_DEDUP_THRESHOLD = 0.85

# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------
LONG_WIDTH, LONG_HEIGHT = 1920, 1080
SHORT_WIDTH, SHORT_HEIGHT = 1080, 1920
FPS = 30
CRF = 18
TEXT_WRAP_WIDTH_PCT = 0.80
LONG_MIN_WORDS, LONG_MAX_WORDS = 750, 1300
LONG_MIN_SCENES, LONG_MAX_SCENES = 6, 10
SHORT_MIN_SEC, SHORT_MAX_SEC = 20, 35
DEFAULT_LUT = LUTS_DIR / "teal_orange.cube"

# ---------------------------------------------------------------------------
# Colors / branding
# ---------------------------------------------------------------------------
COLOR_BG = "#0a0a1a"
COLOR_GOLD = "#FFD700"
FONT_BOLD = "DejaVuSans-Bold"
FONT_REGULAR = "DejaVuSans"

# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-GuyNeural")
PIPER_FALLBACK_MODEL = "en_US-ryan-medium"
PIPER_MODEL_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/"
    "en_US-ryan-medium.onnx"
)
PIPER_CONFIG_URL = PIPER_MODEL_URL + ".json"
PIPER_MODEL_DIR = DATA_DIR / "piper"
TTS_CHUNK_CHAR_LIMIT = 3000

# ---------------------------------------------------------------------------
# Whisper alignment
# ---------------------------------------------------------------------------
WHISPER_MODEL_SIZE = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ---------------------------------------------------------------------------
# Visual generation
# ---------------------------------------------------------------------------
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/"
POLLINATIONS_SLEEP_SEC = 1.0
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PIXABAY_IMAGE_URL = "https://pixabay.com/api/"
PIXABAY_MUSIC_URL = "https://pixabay.com/api/music/"

# ---------------------------------------------------------------------------
# YouTube / scheduling
# ---------------------------------------------------------------------------
YT_CATEGORY_EDUCATION = "27"
YT_HASHTAG_CAP = 15
SHORT_PUBLISH_DELAY_HOURS = [24, 48]  # relative to the parent long's publish slot

# Fixed weekly publish slots (UTC). Python weekday(): Mon=0 ... Sun=6.
# Tue=1 and Fri=4 at 01:00 UTC. The bot RUNS earlier (see run-bot.yml cron) and
# schedules the upload with publishAt, so the public time never drifts with
# however long the build happened to take.
PUBLISH_WEEKDAYS = (1, 4)
PUBLISH_HOUR_UTC = 1
MIN_LEAD_TIME_HOURS = 1  # never schedule a slot closer than this to "now"

# REVIEW_MODE=1 (default): everything is uploaded PRIVATE with no schedule so a
# human can check it in YouTube Studio and publish manually. Set the GitHub
# repo variable REVIEW_MODE=0 once you trust the output.
REVIEW_MODE = os.getenv("REVIEW_MODE", "1") != "0"

# ---------------------------------------------------------------------------
# CTR dynamic-optimization thresholds
# ---------------------------------------------------------------------------
LONG_CTR_MIN = 0.04           # 4%
LONG_AVG_VIEW_PCT_MIN = 0.30  # 30% of video length
SHORT_CTR_MIN = 0.06          # 6%
SHORT_AVG_VIEW_PCT_MIN = 0.25 # 25%
CTR_CHECK_MIN_AGE_HOURS = 48
CTR_MAX_AGE_DAYS = 28        # stop touching videos older than this
CTR_COOLDOWN_DAYS = 7        # min gap between two optimizations of same video
CTR_MAX_ATTEMPTS = 2         # hard cap per video, avoids endless title churn
CTR_MIN_VIEWS = 100          # below this, watch-time stats are just noise

# ---------------------------------------------------------------------------
# Word pool safety net (used only if Gemini word-picking repeatedly fails)
# ---------------------------------------------------------------------------
RESERVE_WORDS = [
    "ego", "envy", "grit", "hubris", "solitude", "nostalgia", "shame",
    "courage", "denial", "resilience", "wanderlust", "melancholy",
    "authenticity", "vulnerability", "ambition", "forgiveness", "doubt",
    "integrity", "curiosity", "obsession",
]

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
MAX_RECENT_WORDS_FOR_PROMPT = 200
REQUEST_TIMEOUT_SEC = 30
