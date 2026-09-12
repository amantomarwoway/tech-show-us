# src/audio_retention.py - REAL AEROPLANE - RETENTION POWER - DETAILED FIXED
# End tak rokne ki takat - American retention

def get_tts_retention_filter(first_punch_text="", american_mode=True):
    """
    TTS retention filter - 1.11X speed + echo for American audience
    first_punch_text: first 2 shocking words
    """
    if not american_mode:
        return "atempo=1.0"

    # 1.11X speed - American retention power - end tak rokne ki takat
    # aecho - halka echo se voice heavy lagega
    # Detailed: 1.11X se video 11 sec se 13 sec tak stretch, retention badhega
    filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4"

    # Agar first punch me SHOCKING/BRUTAL hai to extra punch
    first = (first_punch_text or "").upper()
    if any(w in first for w in ["SHOCKING", "BRUTAL", "BREAKING", "LEAKED"]):
        # First word pe extra bass + speed variation
        filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4, bass=g=2:f=100"

    print(f"[RETENTION] TTS filter: {filter_str} - first punch: {first_punch_text[:30]}")
    return filter_str

def get_american_captions_timing(total_duration, word_count, first_words_count=5):
    """
    Captions timing - American retention
    first 5 words ko 1.6X punch, keywords ko 1.2X punch
    overlap 0.92 se fast reading - end tak rokne
    """
    if word_count <= 0:
        word_count = 20

    # Base duration per word - total / words * 0.95
    base_dur = total_duration / max(word_count, 1) * 0.95

    # American limits: 0.28 - 0.38 sec per word - fast
    base_dur = max(0.28, min(0.38, base_dur))

    # First 5 words - 1.6X punch - SHOCKING first 2 words
    first_dur = base_dur * 1.6

    # Keywords - BRUTAL, TARIFFS, PANIC etc - 1.2X punch
    keyword_dur = base_dur * 1.2

    # Overlap - 0.92 - words jaldi aayenge, retention badhega
    overlap = 0.92

    # Detailed: last 2 sec me slow down for end hook
    # "Wait till end - last part will shock you"
    if total_duration > 10:
        # Last word extra time
        pass

    print(f"[RETENTION] Captions: base={base_dur:.3f}s first={first_dur:.3f}s keyword={keyword_dur:.3f}s overlap={overlap}")

    return {
        "base_dur": base_dur,
        "first_dur": first_dur,
        "keyword_dur": keyword_dur,
        "overlap": overlap,
        "first_words_count": first_words_count
    }

def get_retention_hooks():
    """Retention hooks for detailed video"""
    return {
        "shocking_start": ["Shocking Leak", "Brutal Order", "Breaking Secret", "Leaked Behind"],
        "middle_hook": ["This changes everything", "This affects you directly", "Wait till end"],
        "end_hook": ["Last part will shock you", "You won't believe what happened next", "Do you think this is fair?"],
        "comment_bait": "Do you think this is fair? Comment below",
        "subscribe_bait": "Subscribe before this gets deleted"
    }

# For main.py compatibility
def get_tts_filter_for_video(viral_hook="", american=True):
    """Wrapper for old code"""
    return get_tts_retention_filter(viral_hook, american_mode=american)
