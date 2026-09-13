# src/config.py - MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - RETENTION POWER

GOD_INSTRUCTION = """
GOD LEVEL BOT - MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - 100% FREE
Instruction: Har leg har cheez kahin se bhi best tarike se use kare - bina kisi paid API ke

- Research: MuckScraper live HTML scrape + Ollama local summarize + grouping - 100% free, no Google News API
- Editor: VUZA / Open Montage offline - ColorClip + local assets, Pexels optional fallback, no paid key needed
- Script: Automated-Shorts-Generator Hook/Retain/Reward framework - Ollama first, then Gemini
- Fact Checker: MuckScraper sources + Ollama local fact check + pytrends fallback - 2 of 3 PASS = video banegi
- Boss Approval: Live world demand - MuckScraper viral score
- Uploader: World viral upload with comment + subscribe bait
- Self Evolution: Khud seekhe retention power

RETENTION POWER RULES:
1. First 2 words SHOCKING BRUTAL - Hook 0-3s pattern interrupt
2. 0.8s clip density - fast cuts American audience - VUZA style
3. 1.11X speed + echo + 1.6X punch first 5 words - retention
4. Wait till end hook + This affects you + Comment bait - Reward
5. End tak rokne ki takat - detailed video 11-15 sec - Hook/Retain/Reward
6. 100% FREE OFFLINE - Ollama + VUZA - no Pexels/Pixabay key needed
"""

ENGLISH_COUNTRIES = ["US", "GB", "CA", "AU", "NZ"]

# ===== MUCKSCRAPER CONFIG - Live news scrape + Ollama grouping - 100% FREE =====
MUCKSCRAPER_SOURCES = [
    {"name": "reuters_live", "url": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best", "type": "rss"},
    {"name": "cnn_live", "url": "https://rss.cnn.com/rss/cnn_topstories.rss", "type": "rss"},
    {"name": "bbc_world", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "type": "rss"},
    {"name": "ap_live", "url": "https://apnews.com/hub/ap-top-news", "type": "html"},
    {"name": "google_news_us", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "type": "rss"},
]

OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_URL = "http://localhost:11434/api/generate"

# MuckScraper + Ollama sources - fact_checker.py ke liye
TOP_REAL_SOURCES_MUCKSCRAPER = [
    "muckscraper_reuters_live",
    "muckscraper_cnn_live",
    "muckscraper_bbc_world",
    "muckscraper_ap_live",
    "muckscraper_guaranteed_ollama",
    "muckscraper_reuters_live_html",
    "muckscraper_cnn_live_html",
    "guaranteed_google_news",
    "guaranteed_google_news_rss",
    "guaranteed_breakout_news_fetcher",
    "google_trends_breakout",
    "cnn_breaking",
]

# ===== AUTOMATED-SHORTS-GENERATOR CONFIG - Hook/Retain/Reward framework =====
SHORTS_FRAMEWORK = {
    "HOOK": {
        "duration": "0-3s",
        "rule": "Pattern interrupt, shocking question, viral keywords - SHOCKING, BRUTAL, LEAKED",
        "example": "Breaking White House shocker leaked!"
    },
    "RETAIN": {
        "duration": "3-10s",
        "rule": "Context + twist + curiosity gap, keep viewers, behind closed doors",
        "example": "Behind closed doors, secret order changes everything for families"
    },
    "REWARD": {
        "duration": "10-15s",
        "rule": "Payoff + CTA, emotional punch, affects you, comment bait",
        "example": "This impacts millions tonight. Comment your opinion below"
    }
}

# ===== VUZA / OPEN MONTAGE CONFIG - 100% FREE OFFLINE - No paid API =====
VIDEO_ENGINE = "VUZA_OFFLINE" # VUZA / Open Montage - pure text-to-video offline, no Pexels key needed
ASSET_ENGINE = "VUZA_OFFLINE"
TTS_ENGINE = "PIPER_GTTS_DUAL" # Piper first, gTTS fallback - both free

VUZA_SETTINGS = {
    "offline_mode": True, # 100% free offline - no Pexels/Pixabay/Unsplash/Giphy key needed
    "use_pexels_if_key": True, # If PEXELS_API_KEY exists, use it + offline fallback
    "color_clips_fallback": True, # Always works - ColorClip
    "retention_density": 0.8,
    "retention_speed": 1.11,
    "first_word_punch": 1.6,
}

# World SEO targets - kept for compatibility
WORLD_SEO_TARGETS = {
    "US": 40,
    "GB": 15,
    "CA": 15,
    "AU": 10,
    "IN": 20
}

# Retention hooks for detailed video - Hook/Retain/Reward style
RETENTION_HOOKS = [
    "Wait till end - last part will shock you", # Reward
    "This affects you directly", # Reward
    "This changes everything for millions", # Retain
    "You won't believe what happened next", # Retain
    "Behind closed doors leaked", # Hook
    "Shocking leak behind closed doors", # Hook
    "Brutal order panic millions", # Hook
]

COMMENT_BAITS = [
    "Do you think this is fair? Comment below",
    "Should this be allowed? Comment your opinion",
    "Is this right or wrong? Comment now",
    "What would you do? Comment below"
]

SUBSCRIBE_BAITS = [
    "Subscribe before this gets deleted",
    "Subscribe for real breaking news",
    "Follow before they hide this",
    "Subscribe - more shocking leaks coming"
]

# Viral keywords for detailed search - MuckScraper + Hook/Retain/Reward
VIRAL_KEYWORDS = [
    "breaking", "shocking", "leaked", "secret", "behind closed doors",
    "executive order", "white house", "supreme court", "trump", "biden",
    "tariff", "trade war", "ban", "panic", "families",
    "brutal", "shatter", "exposed", "revealed", "stuns"
]

# Video settings for detailed - VUZA offline
VIDEO_SETTINGS = {
    "width": 1080,
    "height": 1920,
    "clip_density": 0.8,
    "duration_min": 11,
    "duration_max": 15,
    "fps": [29.97, 30],
    "retention_speed": 1.11,
    "first_word_punch": 1.6,
    "keyword_punch": 1.25,
    "offline_mode": True,
    "vuza_engine": "VUZA_OFFLINE"
}
