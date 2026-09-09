"""
audio_retention.py - FIXED
- BGM volume har 3 sec pe 5% up/down + sub bass drop logic preserved
- FIX: atempo=1.15,asetrate=... pura long filter log leak band, only short log
- No disable
"""
# UPDATED JULY 2025 - GEMINI 3.6 FLASH LATEST + CHATGPT FALLBACK gpt-4o-mini - NO SAFE EXIT - NO FORCE PASS

import random, subprocess

def get_bgm_volume_filter():
    """
    BGM volume har 3 sec pe 5% up/down + sub bass drop logic
    """
    bass_filter = "bass=g=3:f=100:width_type=o:width=1,treble=g=1:f=4000"
    vol_mod = "volume='1+0.05*sin(2*PI*t/3)':eval=frame"
    full_af = f"{bass_filter},{vol_mod}"
    # FIX: long filter log leak band - only short log
    print(f"[AUDIO RETENTION] BGM: vol 3s 5% + sub bass")
    return full_af

def get_tts_retention_filter():
    """
    TTS retention: 1.15X speed + pitch up + first 1 sec punch + har 3 sec 5% + bass drop
    """
    tts_af = (
        "atempo=1.15,"
        "asetrate=48000*1.02,atempo=1/1.02,"
        "bass=g=2:f=120,"
        "volume='if(lt(t,1),1.5,if(lt(mod(t,3),0.2),1.05,0.95))':eval=frame"
    )
    # FIX: long filter log leak band - only short log, no full atempo/asetrate print
    print(f"[AUDIO RETENTION] TTS: 1.15X + pitch 1.02 + 1s punch 150% + 3s 5% + bass")
    return tts_af

def apply_audio_retention_to_file(input_audio, output_audio, is_tts=False):
    af = get_tts_retention_filter() if is_tts else get_bgm_volume_filter()
    cmd = ["ffmpeg","-y","-i", input_audio, "-af", af, "-c:a", "aac", "-b:a", "192k", output_audio]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[AUDIO RETENTION] Applied {is_tts}")
        return output_audio
    except Exception as e:
        print(f"[AUDIO RETENTION] Fail, using original")
        return input_audio

if __name__=="__main__":
    vf1 = get_bgm_volume_filter()
    vf2 = get_tts_retention_filter()
    print("BGM filter OK, TTS filter OK - short logs only")
