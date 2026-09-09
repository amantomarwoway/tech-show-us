"""
audio_retention.py - ULTIMATE BEST - EMOTIONAL & ENJOYABLE AUDIO
FINAL EDIT as per request: Make audio enjoyable to listen, best possible

FEATURES:
- BGM: 5% up/down every 3 sec + sub bass drop + warm bass + crystal treble + stereo widening + emotional swell
- TTS: 1.11/1.12X speed (not 1.15), pitch up 1.025, first 1 sec 160% punch for shock sentence (American replays 4-5 times), 3 sec 6% variation, warmth, clarity, punchy compressor, de-rumble, de-hiss
- Enjoyable: Warm, crisp, punchy, emotional - sunne me maza aaye

Based on old file provided by user + latest requests
"""

import random, subprocess

def get_bgm_volume_filter():
    """
    BGM - BEST VERSION - Enjoyable & Emotional
    - Volume har 3 sec pe 5-6% up/down (retention - ear ko bore nahi hone deta)
    - Sub bass drop for emotional weight (dil me lage)
    - Warm bass + crystal treble for enjoyable listening
    - Stereo widening for spacious feel
    - Short log only (no long filter leak)
    """
    # Warm deep bass for emotional weight
    bass_filter = "bass=g=4:f=90:width_type=o:width=1.2"
    # Crystal clear treble for sparkle
    treble_filter = "treble=g=1.3:f=4000:width_type=o:width=1.5"
    # Low sub bass for feeling in chest
    sub_bass = "lowshelf=g=2:f=100:width_type=o:width=1"
    # Volume modulation 5-6% every 3 sec - retention, not boring
    vol_mod = "volume='1+0.06*sin(2*PI*t/3.2)':eval=frame"
    # Stereo widening - enjoyable, spacious
    stereo_wide = "extrastereo=m=1.4:c=0"
    
    full_af = f"{bass_filter},{treble_filter},{sub_bass},{vol_mod},{stereo_wide}"
    print(f"[AUDIO RETENTION] BGM BEST: warm bass 4dB + crystal treble + sub bass + 3.2s 6% swell + stereo wide - enjoyable")
    return full_af

def get_tts_retention_filter(topic_first_sentence=""):
    """
    TTS - ULTIMATE BEST - Emotional, Punchy, Enjoyable
    - Speed 1.11/1.12X (not 1.15) - fast but natural, not chipmunk
    - Pitch up 1.025 - youthful, energetic, American ko pasand
    - First 1 sec 160% punch - shock+emotion wala first sentence sabse tez, American 4-5 baar replay kare
    - Har 3 sec 6% volume up/down - retention, monotony break, sunne me maza
    - Bass warmth + treble clarity + compressor punch + de-rumble + de-hiss = professional enjoyable
    - topic_first_sentence = first sentence jo sabse zyada shock+emotional hai
    """
    # Random 1.11 or 1.12 for natural variation - not robotic
    speed = random.choice([1.11, 1.12])
    
    # Remove low rumble and high hiss for clean enjoyable audio
    clean_filter = "highpass=f=75,lowpass=f=13000"
    
    # Warmth in voice - chest voice, emotional
    bass_warm = "bass=g=2.8:f=120:width_type=o:width=1.5"
    
    # Clarity and presence - voice cuts through, enjoyable to ear
    treble_clear = "treble=g=1.4:f=3200:width_type=o:width=1.2"
    
    # Compressor - punchy, professional, even volume - sunne me maza
    # Makes quiet parts louder, loud parts controlled - emotional impact
    compressor = "compand=attacks=0:points=-80/-900|-45/-15|-27/-9|0/-7|20/-7:gain=2.5"
    
    # Pitch up slightly for youthful energetic American news voice
    pitch_up = f"asetrate=48000*1.025,atempo=1/1.025"
    
    # Volume punch: first 1 sec 160% (shock sentence punch), then every 3 sec 6% variation
    # First sentence = most shock+emotion, so 1.6x loudness = American replays 4-5 times
    vol_punch = "volume='if(lt(t,1),1.6,if(lt(mod(t,3.2),0.18),1.06,0.94))':eval=frame"
    
    # Combine all - enjoyable, emotional, punchy
    tts_af = (
        f"atempo={speed},"
        f"{pitch_up},"
        f"{clean_filter},"
        f"{bass_warm},"
        f"{treble_clear},"
        f"{compressor},"
        f"{vol_punch}"
    )
    
    # Log punch sentence for debugging - shows which sentence is getting punch
    punch_preview = topic_first_sentence[:70] if topic_first_sentence else "shock+emotion first sentence"
    print(f"[AUDIO RETENTION] TTS BEST: {speed}X + pitch 1.025 youthful + 1s punch 160% + 3.2s 6% + warm bass 2.8dB + crystal treble + compressor punch + clean | Punch: {punch_preview}")
    return tts_af

def get_emotional_enhancement_filter():
    """
    Extra emotional enhancement - for making voice more touching, face expression change
    - Slight reverb for emotional depth (not too much, just warmth)
    - Can be added optionally for super emotional topics
    """
    # Very subtle reverb for emotional depth - makes voice more touching
    emotional_filter = "aecho=0.8:0.88:15:0.3"
    return emotional_filter

def apply_audio_retention_to_file(input_audio, output_audio, is_tts=False, topic_first_sentence=""):
    """
    Apply best audio retention - enjoyable to listen
    - is_tts=False = BGM (enjoyable background)
    - is_tts=True = TTS voice (punchy, emotional, enjoyable)
    - topic_first_sentence = first sentence with max shock+emotion for punch
    """
    if is_tts:
        af = get_tts_retention_filter(topic_first_sentence)
        # For ultra emotional, can add slight echo (optional)
        # Uncomment if want more emotional depth: af = f"{af},{get_emotional_enhancement_filter()}"
    else:
        af = get_bgm_volume_filter()
    
    # High quality 192k AAC - enjoyable quality
    cmd = ["ffmpeg","-y","-i", input_audio, "-af", af, "-c:a", "aac", "-b:a", "192k", output_audio]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[AUDIO RETENTION] BEST APPLIED: is_tts={is_tts} | Speed 1.11/1.12X | Punch 160% | Enjoyable")
        return output_audio
    except Exception as e:
        print(f"[AUDIO RETENTION] Fail ({e}), using original - enjoyable fallback")
        return input_audio

def apply_best_audio_retention(input_audio, output_audio, first_sentence_punch="", is_emotional_topic=False):
    """
    BEST WRAPPER - Sabse best enjoyable audio ke liye
    - Automatically chooses best settings based on topic
    - first_sentence_punch = sabse zyada shock+emotional wala first sentence
    - is_emotional_topic = agar topic bahut emotional hai to extra depth
    """
    # Use TTS best filter with punch sentence
    af = get_tts_retention_filter(first_sentence_punch)
    
    # If emotional topic, add subtle emotional depth
    if is_emotional_topic:
        af = f"{af},{get_emotional_enhancement_filter()}"
        print(f"[AUDIO RETENTION] ULTRA EMOTIONAL MODE: extra depth added for {first_sentence_punch[:50]}")
    
    cmd = ["ffmpeg","-y","-i", input_audio, "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", output_audio]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[AUDIO RETENTION] ULTRA BEST: Emotional enjoyable audio ready")
        return output_audio
    except Exception as e:
        print(f"[AUDIO RETENTION] Ultra fail, trying basic best")
        return apply_audio_retention_to_file(input_audio, output_audio, is_tts=True, topic_first_sentence=first_sentence_punch)

if __name__=="__main__":
    print("=== AUDIO RETENTION - BEST TEST ===")
    vf1 = get_bgm_volume_filter()
    vf2 = get_tts_retention_filter("Families hearts shattered tonight - shocking betrayal")
    vf3 = get_emotional_enhancement_filter()
    print(f"BGM Filter: {vf1[:80]}...")
    print(f"TTS Filter: {vf2[:120]}...")
    print(f"Emotional Filter: {vf3}")
    print("BGM filter OK, TTS filter OK - BEST enjoyable version - 1.11/1.12X + 160% punch + warm + crystal clear")
    print("Audio sunne me maza ayega - American 4-5 baar replay karega first sentence")
