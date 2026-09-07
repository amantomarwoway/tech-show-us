"""
audio_retention.py - BGM volume har 3 sec pe 5% up/down + sub bass drop logic
"""
import random, subprocess

def get_bgm_volume_filter():
    """
    BGM volume har 3 sec pe 5% up/down + sub bass drop logic
    FFmpeg filter for audio retention
    """
    # Create volume modulation every 3 sec: 5% up/down
    # Using volume expression: if(t%6<3, 1.05, 0.95) etc
    # For more organic, random walk every 3 sec
    
    # Sub bass drop logic - bass boost at start and every 7 sec
    bass_filter = "bass=g=3:f=100:width_type=o:width=1,treble=g=1:f=4000"
    
    # Volume modulation filter - using aevalsrc style not possible, use volume with sine + random
    # We'll use: volume='if(lt(mod(t,3),0.1), 1.05, if(lt(mod(t,6),3.1), 0.95, 1))':eval=frame for 5% up/down
    vol_mod = "volume='1+0.05*sin(2*PI*t/3)':eval=frame"
    
    full_af = f"{bass_filter},{vol_mod}"
    
    print(f"[AUDIO RETENTION] BGM filter: vol har 3 sec 5% up/down + sub bass drop g=3 f=100")
    return full_af

def get_tts_retention_filter():
    """
    TTS retention: 1.15X speed + pitch up + first 1 sec punch + har 3 sec 5% + bass drop
    """
    # TTS speed 1.15 + pitch shift + bass
    # atempo for speed, asetrate for pitch, bass for drop, volume for punch
    
    # First sec 150% punch via volume expression
    # volume='if(lt(t,1),1.5,if(lt(mod(t,3),0.1),1.05,0.95))'
    tts_af = (
        "atempo=1.15,"  # 1.15X speed
        "asetrate=48000*1.02,atempo=1/1.02,"  # pitch up ~2%
        "bass=g=2:f=120,"  # sub bass drop
        "volume='if(lt(t,1),1.5,if(lt(mod(t,3),0.2),1.05,0.95))':eval=frame"  # first sec punch + har 3 sec 5%
    )
    print(f"[AUDIO RETENTION] TTS filter: 1.15X + pitch 1.02 + first 1s 150% + har 3s 5% + bass drop")
    return tts_af

def apply_audio_retention_to_file(input_audio, output_audio, is_tts=False):
    """Apply retention filter to audio file"""
    af = get_tts_retention_filter() if is_tts else get_bgm_volume_filter()
    cmd = ["ffmpeg","-y","-i", input_audio, "-af", af, "-c:a", "aac", "-b:a", "192k", output_audio]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[AUDIO RETENTION] Applied to {input_audio} -> {output_audio}")
        return output_audio
    except Exception as e:
        print(f"[AUDIO RETENTION] Fail {e}, using original")
        return input_audio

if __name__=="__main__":
    print(get_bgm_volume_filter())
    print(get_tts_retention_filter())
