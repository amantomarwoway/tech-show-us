"""
Central configuration for the HEY DARKY story bot.

Everything tunable lives here; secrets are NEVER stored in the repo — they are
read from environment variables (GitHub Actions secrets) at call time.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (all created on import so no module ever has to mkdir)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
TEMP_DIR = ROOT_DIR / "temp"
SCENES_DIR = TEMP_DIR / "scenes"
LOG_DIR = ROOT_DIR / "logs"
ASSETS_DIR = ROOT_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"   # optional: your own CC0/royalty-free tracks (fallback)
SFX_DIR = ASSETS_DIR / "sfx"       # optional: your own CC0/royalty-free effects (fallback)
LUT_DIR = ASSETS_DIR / "luts"      # optional: a .cube colour grade
AUDIO_CACHE_DIR = ROOT_DIR / "audio_cache"
for _d in (DATA_DIR, OUTPUT_DIR, TEMP_DIR, SCENES_DIR, LOG_DIR, MUSIC_DIR, SFX_DIR, LUT_DIR, AUDIO_CACHE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "words.db"   # committed back to git by the workflows

# ---------------------------------------------------------------------------
# Safety switch
# ---------------------------------------------------------------------------
# "1" (default): everything is uploaded PRIVATE / unpublished and Instagram is
# skipped, so you can review the first runs. "0": fully automatic public
# publishing. Set via the repo VARIABLE REVIEW_MODE (see the workflow).
REVIEW_MODE = os.getenv("REVIEW_MODE", "1") != "0"

# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------
FPS = 30
CRF = 20                      # final quality (lower = better/larger)
CLIP_PRESET = "veryfast"      # per-beat Ken Burns clips (re-encoded once more at the end)
FINAL_PRESET = "medium"       # the single final caption/LUT pass
LONG_WIDTH, LONG_HEIGHT = 1920, 1080
SHORT_WIDTH, SHORT_HEIGHT = 1080, 1920
SHORT_MIN_SEC, SHORT_MAX_SEC = 20, 35
DEFAULT_LUT = LUT_DIR / "cinematic.cube"   # applied only if the file exists
REQUEST_TIMEOUT_SEC = 30

# ---------------------------------------------------------------------------
# Gemini (story writing)
# ---------------------------------------------------------------------------
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
GEMINI_PRIMARY_MODEL = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-3.6-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.7-flash")
# A full 15-20 minute story as JSON is ~10k tokens; the API default output cap can be far lower
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "32768"))

# ---------------------------------------------------------------------------
# Voice-over (Edge TTS primary, Piper offline fallback) + word alignment
# ---------------------------------------------------------------------------
EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-ChristopherNeural")
TTS_CHUNK_CHAR_LIMIT = 2500
PIPER_FALLBACK_MODEL = "en_US-lessac-medium"
PIPER_MODEL_DIR = DATA_DIR / "piper"
_PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
PIPER_MODEL_URL = f"{_PIPER_BASE}/{PIPER_FALLBACK_MODEL}.onnx"
PIPER_CONFIG_URL = f"{_PIPER_BASE}/{PIPER_FALLBACK_MODEL}.onnx.json"
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "tiny.en")

# ---------------------------------------------------------------------------
# Images (Pollinations -> Pexels -> Pixabay)
# ---------------------------------------------------------------------------
POLLINATIONS_API_KEY_ENV = "POLLINATIONS_API_KEY"
POLLINATIONS_BASE = "https://gen.pollinations.ai/image/"
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "flux")
POLLINATIONS_TIMEOUT_SEC = 90
PEXELS_API_KEY_ENV = "PEXELS_API_KEY"
PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
PIXABAY_API_KEY_ENV = "PIXABAY_API_KEY"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/"
PIXABAY_SLEEP_SEC = 0.6       # polite spacing between Pixabay calls
POLLINATIONS_SLEEP_SEC = 1.0

# ---------------------------------------------------------------------------
# YouTube
# ---------------------------------------------------------------------------
YT_CLIENT_ID_ENV = "YT_CLIENT_ID"
YT_CLIENT_SECRET_ENV = "YT_CLIENT_SECRET"
YT_REFRESH_TOKEN_ENV = "YT_REFRESH_TOKEN"
YT_TOKEN_URI = "https://oauth2.googleapis.com/token"
YT_UPLOAD_CHUNK_BYTES = 8 * 1024 * 1024
YT_MAX_DESC_HASHTAGS = 5
YT_TITLE_LIMIT = 100

# ---------------------------------------------------------------------------
# Channel identity
# ---------------------------------------------------------------------------
CHANNEL_NAME = os.getenv("CHANNEL_NAME", "Hey Darky")
STORY_LANGUAGE = "en"  # every title/description/tag/caption and the narration are English-only
STORY_CHANNEL_HASHTAGS = ("#HeyDarky", "#Horror", "#Mystery", "#Thriller", "#Suspense", "#CrimeStory")
STORY_GENRES = ("crime", "thriller", "suspense", "mystery", "horror")
STORY_GENRE_HASHTAGS = {
    "horror": ("#HorrorStories", "#ScaryStories"),
    "crime": ("#CrimeStory", "#CrimeFiction"),
    "thriller": ("#ThrillerStory", "#Thriller"),
    "suspense": ("#Suspense", "#SuspenseStory"),
    "mystery": ("#MysteryStory", "#Mystery"),
}
STORY_RESEARCH_QUERIES = {
    "crime": "fictional crime story narration",
    "thriller": "thriller story narration",
    "suspense": "suspense story narration",
    "mystery": "mystery story narration",
    "horror": "scary horror story narration",
}

# ---------------------------------------------------------------------------
# Story writing
# ---------------------------------------------------------------------------
STORY_MIN_MINUTES, STORY_MAX_MINUTES = 15, 20
STORY_MIN_WORDS = STORY_MIN_MINUTES * 130     # ~130 words per minute of narration
STORY_MAX_WORDS = STORY_MAX_MINUTES * 130
STORY_MIN_SCENES, STORY_MAX_SCENES = 24, 45
STORY_MIN_CHARACTERS, STORY_MAX_CHARACTERS = 2, 5
STORY_MAX_BGM_KEYWORDS = 6    # distinct music moods per story (keeps API hits low)
STORY_MAX_PAUSE_SEC = 4.0     # longest dramatic pause the writer may request

# The recurring fictional town + cast ("Anthology Brand": one continuous world).
STORY_UNIVERSE_TOWN = os.getenv("STORY_UNIVERSE_TOWN", "Blackwood Pines, Oregon")
STORY_RECURRING_CHARACTERS = (
    {"name": "Detective Sarah Miller", "gender": "female",
     "note": "recurring investigator — sharp, guarded, carries old unsolved cases personally"},
    {"name": "Sheriff Tom Garrett", "gender": "male",
     "note": "recurring local law enforcement — weary, knows the town's secrets, slow to trust outsiders"},
)
STORY_RECURRING_CHARACTER_RATE = 0.4   # ~40% of stories feature one of them

# Content pillars (the recurring categories a story falls into; the bot learns
# from real analytics which ones this audience prefers).
STORY_PILLARS = (
    "unsolved_mystery",
    "locked_room",
    "psychological_thriller",
    "detective_mystery",
    "twist_crime",
)
STORY_PILLAR_LABELS = {
    "unsolved_mystery": "Unsolved-style fictional mystery",
    "locked_room": "Locked-room crime",
    "psychological_thriller": "Psychological thriller",
    "detective_mystery": "Detective mystery",
    "twist_crime": "Unexpected-twist crime story",
}
STORY_LOCALE_NOTE = (
    "Setting: small-town or rural America (Pacific Northwest / New England "
    "/ Midwest flavor). Use Western character names (e.g. John, Sarah, "
    "Detective Miller, Sheriff Tom). Use American terminology: a police "
    "station is a 'precinct', the local police chief is 'Sheriff', a small "
    "porch/balcony is a 'porch' or 'deck'. Use American English idioms "
    "throughout, not British/Indian/international English phrasing."
)
# Western-culture visuals: appended to EVERY image prompt (kept at the END so the
# Pexels/Pixabay fallbacks, which search on the first few words, are unaffected).
STORY_VISUAL_STYLE_SUFFIX = (
    ", set in the United States: authentic Western (American) people, clothing, "
    "homes, cars, objects and everyday life, American small-town and suburban "
    "architecture and landscapes, cinematic dark moody lighting, photorealistic, "
    "no text, no watermark"
)

# ---------------------------------------------------------------------------
# Character voices (verified Edge TTS neural voices)
# ---------------------------------------------------------------------------
STORY_NARRATOR_VOICE = "en-US-ChristopherNeural"   # "Reliable, Authority"
# Slightly slower + lower for an ominous narrator read. `rate` does most of the
# work; some edge-tts versions give `pitch` little effect.
STORY_NARRATOR_RATE = os.getenv("STORY_NARRATOR_RATE", "-8%")
STORY_NARRATOR_PITCH = os.getenv("STORY_NARRATOR_PITCH", "-5Hz")
STORY_MALE_VOICES = (
    "en-US-GuyNeural", "en-US-EricNeural", "en-US-RogerNeural",
    "en-US-AndrewNeural", "en-US-BrianNeural",
)
STORY_FEMALE_VOICES = (
    "en-US-JennyNeural", "en-US-AriaNeural", "en-US-MichelleNeural",
    "en-US-AnaNeural", "en-US-EmmaNeural",
)

# ---------------------------------------------------------------------------
# Audio layering (src/audio_fetcher.py + src/audio_mixer.py)
# ---------------------------------------------------------------------------
# VERIFIED: Pixabay's official API only searches IMAGES and VIDEOS (no music
# endpoint), so music AND sound effects both come from Freesound (CC0 only),
# with local assets/ and a synthesized ambient drone as fallbacks.
FREESOUND_SEARCH_URL = "https://freesound.org/apiv2/search/"
FREESOUND_API_KEY_ENV = "FREESOUND_API_KEY"
AUDIO_REQUEST_MIN_GAP_SEC = 2.0   # strict spacing between ANY two Freesound requests
AUDIO_429_COOLDOWN_SEC = 60       # linear backoff: 60s, 120s, ... on HTTP 429
AUDIO_MAX_RETRIES = 3
FREESOUND_LICENSE_FILTER = 'license:"Creative Commons 0"'
FREESOUND_BGM_DURATION_FILTER = "duration:[60 TO 600]"
FREESOUND_SFX_DURATION_FILTER = "duration:[0.5 TO 10.0]"
# dB relative to the voice-over (the 0 dB reference); assets are peak-normalized first.
STORY_BGM_DB = -22.0
STORY_BGM_PAUSE_DB = -12.0
STORY_PAUSE_MIN_SEC = 2.0
STORY_AMBIENT_DB = -26.0
STORY_ACTION_DB = -8.0
STORY_BGM_CROSSFADE_SEC = 1.0

# ---------------------------------------------------------------------------
# Cadence + publishing (YouTube / Facebook / Instagram)
# ---------------------------------------------------------------------------
STORY_YT_CATEGORY = "24"            # Entertainment (fiction)
STORY_LONG_EVERY_DAYS = 2           # one 15-20 min story every 2 days
STORY_SHORTS_PER_STORY = 2          # => exactly one Short per day
STORY_SHORT_QUEUE_DELAY_HOURS = 20  # Short #2 waits ~a day in the publish queue
FB_PAGE_ID_ENV = "FB_PAGE_ID"
FB_ACCESS_TOKEN_ENV = "FB_ACCESS_TOKEN"
IG_USER_ID_ENV = "IG_USER_ID"
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v23.0")
# Facebook is the ONLY platform here with an official organic-audience control
# (Page-post `targeting` / `feed_targeting`). English-locale keys are resolved
# live from Meta's adlocale search. YouTube / Instagram have no such API.
FB_TARGET_LOCALE_QUERY = "English"
FB_HARD_TARGETING = os.getenv("FB_HARD_TARGETING", "1") != "0"
FB_TARGET_COUNTRIES = tuple(
    c.strip().upper() for c in os.getenv("FB_TARGET_COUNTRIES", "").split(",") if c.strip()
)  # empty = worldwide English-locale audience
FB_MAX_HASHTAGS = 5
IG_MAX_HASHTAGS = 8
IG_CAPTION_LIMIT = 2200
