# src/audio_retention.py - MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - RETENTION POWER - DETAILED FIXED
# End tak rokne ki takat - American retention - Automated-Shorts-Generator + VUZA + MuckScraper

def get_tts_retention_filter(first_punch_text="", american_mode=True, hook_data=None):
    """
    TTS retention filter - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE
    1.11X speed + echo for American audience - Hook ke liye 1.13X + bass
    first_punch_text: first 2 shocking words (hook)
    hook_data: dict with hook, retain, reward, muckscraper_source, breakout_score, vuza_offline
    """
    if not american_mode:
        return "atempo=1.0"

    # Base - American retention power
    first = (first_punch_text or "").upper()

    # Hook/Retain/Reward - Automated-Shorts-Generator framework
    hook = ""
    retain = ""
    reward = ""
    muck_source = ""
    breakout_score = 0
    vuza_offline = False

    if isinstance(hook_data, dict):
        hook = hook_data.get('hook','') or hook_data.get('hook_visual','') or first_punch_text or ""
        retain = hook_data.get('retain','') or ""
        reward = hook_data.get('reward','') or ""
        muck_source = hook_data.get('muckscraper_source','') or hook_data.get('source','') or ""
        breakout_score = hook_data.get('breakout_score',0) or hook_data.get('search_potential_score',0)
        vuza_offline = hook_data.get('vuza_offline', False)
        # first_punch_text override with hook if present
        if hook:
            first = hook.upper()[:60]

    # VUZA OFFLINE - 100% FREE - gTTS compatible filter
    if vuza_offline:
        # gTTS voice is softer, need more punch
        if any(w in first for w in ["SHOCKING", "BRUTAL", "BREAKING", "LEAKED", "WHITE HOUSE", "PANIC"]):
            filter_str = "atempo=1.13, aecho=0.8:0.88:8:0.5, bass=g=3:f=100, treble=g=1.5"
            print(f"[RETENTION - VUZA OFFLINE] TTS filter HOOK PUNCH: {filter_str} - first punch: {first[:40]} - 100% FREE")
            return filter_str
        else:
            filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4, bass=g=2:f=100"
            print(f"[RETENTION - VUZA OFFLINE] TTS filter: {filter_str} - first punch: {first[:30]}")
            return filter_str

    # MUCKSCRAPER + HOOK - high breakout = extra speed
    if breakout_score >= 5000 or "muckscraper" in muck_source.lower() or "reuters" in muck_source.lower() or "cnn" in muck_source.lower():
        # High demand news - faster 1.13X for retention
        if any(w in first for w in ["SHOCKING", "BRUTAL", "BREAKING", "LEAKED", "SECRET", "BEHIND"]):
            filter_str = "atempo=1.13, aecho=0.8:0.88:7:0.45, bass=g=2.5:f=100, volume=1.1"
            print(f"[RETENTION - MUCKSCRAPER + HOOK] TTS filter HIGH BREAKOUT {breakout_score}: {filter_str} - first punch: {first[:40]} Source:{muck_source[:20]}")
            return filter_str

    # Default Hook/Retain/Reward logic - Automated-Shorts-Generator
    if any(w in first for w in ["SHOCKING", "BRUTAL", "BREAKING", "LEAKED"]):
        # First word pe extra bass + speed variation - HOOK
        filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4, bass=g=2:f=100"
        print(f"[RETENTION - HOOK/RETAIN/REWARD] TTS filter HOOK: {filter_str} - first punch: {first[:30]} Hook:{hook[:20] if hook else 'N/A'}")
        return filter_str
    else:
        # 1.11X speed - American retention power - end tak rokne ki takat
        filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4"
        print(f"[RETENTION - HOOK/RETAIN/REWARD] TTS filter: {filter_str} - first punch: {first[:30]} - Retain:{retain[:20] if retain else 'N/A'}")
        return filter_str

def get_american_captions_timing(total_duration, word_count, first_words_count=5, hook_data=None):
    """
    Captions timing - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - American retention
    first 5 words ko 1.6X punch (Hook yellow), keywords ko 1.2X punch (Retain), last 2 words slow (Reward)
    overlap 0.92 se fast reading - end tak rokne
    """
    if word_count <= 0:
        word_count = 20

    # Base duration per word - total / words * 0.95
    base_dur = total_duration / max(word_count, 1) * 0.95

    # American limits: 0.28 - 0.38 sec per word - fast - MUCKSCRAPER + VUZA
    base_dur = max(0.28, min(0.38, base_dur))

    # Hook/Retain/Reward - Automated-Shorts-Generator framework
    hook = ""
    vuza_offline = False
    breakout_score = 0
    if isinstance(hook_data, dict):
        hook = hook_data.get('hook','') or ""
        vuza_offline = hook_data.get('vuza_offline', False)
        breakout_score = hook_data.get('breakout_score',0)

    # First 5 words - 1.6X punch - SHOCKING first 2 words - HOOK - Yellow big
    if vuza_offline:
        # VUZA OFFLINE - need more punch for offline colors
        first_dur = base_dur * 1.7
    elif breakout_score >= 5000:
        # MUCKSCRAPER high breakout - extra punch
        first_dur = base_dur * 1.7
    else:
        first_dur = base_dur * 1.6

    # Keywords - BRUTAL, TARIFFS, PANIC etc - 1.2X punch - RETAIN
    keyword_dur = base_dur * 1.2

    # Overlap - 0.92 - words jaldi aayenge, retention badhega - VUZA OFFLINE
    overlap = 0.92
    if vuza_offline:
        overlap = 0.90 # Faster for offline

    # Detailed: last 2 sec me slow down for end hook - REWARD - "Wait till end - last part will shock you"
    reward_extra = 0
    if total_duration > 10:
        reward_extra = 0.2 # Last word extra 0.2s for reward payoff
        print(f"[RETENTION - REWARD] Last word extra {reward_extra}s for end hook")

    print(f"[RETENTION - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE] Captions: base={base_dur:.3f}s first={first_dur:.3f}s (HOOK yellow) keyword={keyword_dur:.3f}s (RETAIN) overlap={overlap} VUZA={vuza_offline} Breakout={breakout_score}")

    return {
        "base_dur": base_dur,
        "first_dur": first_dur,
        "keyword_dur": keyword_dur,
        "overlap": overlap,
        "first_words_count": first_words_count,
        "reward_extra": reward_extra,
        "vuza_offline": vuza_offline,
        "hook": hook
    }

def get_vuza_retention_filter(first_punch_text=""):
    """VUZA OFFLINE - 100% FREE - gTTS compatible - no Piper needed"""
    first = (first_punch_text or "").upper()
    if any(w in first for w in ["SHOCKING", "BRUTAL", "BREAKING", "LEAKED"]):
        filter_str = "atempo=1.13, aecho=0.8:0.88:8:0.5, bass=g=3:f=100"
    else:
        filter_str = "atempo=1.11, aecho=0.8:0.88:6:0.4"
    print(f"[RETENTION - VUZA OFFLINE 100% FREE] Filter: {filter_str} - {first[:30]}")
    return filter_str

def get_retention_hooks(muckscraper_data=None):
    """Retention hooks for detailed video - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA"""
    base_hooks = {
        "shocking_start": ["Shocking Leak", "Brutal Order", "Breaking Secret", "Leaked Behind", "White House Shocker"],
        "middle_hook": ["This changes everything", "This affects you directly", "Wait till end", "Behind closed doors"],
        "end_hook": ["Last part will shock you", "You won't believe what happened next", "Do you think this is fair?"],
        "comment_bait": "Do you think this is fair? Comment below - Should this be allowed?",
        "subscribe_bait": "Subscribe before this gets deleted - more shocking leaks coming!"
    }

    # MuckScraper boost
    if isinstance(muckscraper_data, dict):
        source = muckscraper_data.get('muckscraper_source','') or ""
        grouped = muckscraper_data.get('grouped_topic','') or ""
        if "reuters" in source.lower():
            base_hooks["shocking_start"].insert(0, f"Reuters Live: {grouped[:20] if grouped else 'Breaking'}")
        if "cnn" in source.lower():
            base_hooks["middle_hook"].insert(0, "CNN just confirmed this")

    # VUZA OFFLINE tag
    base_hooks["vuza_tag"] = "Made with VUZA OFFLINE - 100% FREE - No paid API"
    base_hooks["ollama_tag"] = "AI Summary by Ollama - Automated-Shorts-Generator"

    print(f"[RETENTION] Hooks ready - MUCKSCRAPER:{muckscraper_data.get('muckscraper_source','N/A')[:20] if isinstance(muckscraper_data, dict) else 'N/A'} + VUZA OFFLINE")
    return base_hooks

# For main.py compatibility - MUCKSCRAPER + VUZA
def get_tts_filter_for_video(viral_hook="", american=True, script_data=None):
    """Wrapper for old code - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE"""
    if isinstance(script_data, dict):
        return get_tts_retention_filter(viral_hook, american_mode=american, hook_data=script_data)
    elif isinstance(viral_hook, dict):
        # Called with dict as first arg
        return get_tts_retention_filter(viral_hook.get('hook',''), american_mode=american, hook_data=viral_hook)
    else:
        return get_tts_retention_filter(viral_hook, american_mode=american, hook_data=None)

# Extra - Hook/Retain/Reward timing for video_generator
def get_hook_retain_reward_timing(total_duration=13):
    """Automated-Shorts-Generator - 0-3s Hook, 3-10s Retain, 10-15s Reward"""
    return {
        "hook": {"start": 0, "end": 3, "color": (180,30,30), "text": "HOOK - Shocking first 2 words"},
        "retain": {"start": 3, "end": 10, "color": (20,40,90), "text": "RETAIN - Twist + secret"},
        "reward": {"start": 10, "end": total_duration, "color": (30,20,50), "text": "REWARD - Payoff + comment bait"},
        "vuza_offline": True,
        "muckscraper": "live HTML scrape"
    }
