import random
def get_tts_retention_filter(first_punch, american_mode=True):
    # GOD: Best sound retention - punch first sentence
    speed = 1.15 if american_mode else 1.0
    # Bass boost + volume for retention
    return f"atempo={speed},bass=g=2:f=110,volume=1.2"
def get_american_captions_timing(total, word_count, first_count=5):
    base = total / max(word_count,1) * 0.95
    base = max(0.28, min(0.38, base))
    return {"base_dur":base,"first_dur":base*1.4,"keyword_dur":base*1.2,"overlap":0.92}
