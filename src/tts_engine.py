"""
ULTIMATE GOD LEVEL - TTS RETENTION + VvSA + SOUND RETENTION
Location: src/tts_engine.py
Edits:
- Pacing 1.10X speed
- Pitch slightly up (energetic)
- Audio punch first 1 sec 150% volume
- Sound retention: BGM volume every 3 sec 5% up/down + sub bass drop
- VvSA: first frame audio shock
"""

import os, wave, subprocess, tempfile, math, random
from pathlib import Path

# Retention constants
TTS_SPEED = 1.10
PUNCH_VOLUME = 1.5  # first 1 sec 150%
PITCH_SEMITONES = 1.2  # slight pitch up for energy
VOL_MODULATION_EVERY_SEC = 3  # har 3 sec
VOL_MODULATION_PERCENT = 0.05  # 5%

def apply_ffmpeg_retention_filters(input_path, output_path):
    """
    FFmpeg filters for retention:
    - atempo 1.10 (pacing)
    - asetrate + pitch up
    - volume punch first 1 sec
    - volume modulation every 3 sec 5%
    - bass boost / sub drop
    """
    # Build complex filter
    # 1. Speed 1.15x
    # 2. Pitch up slightly via asetrate (22050 -> 22050*1.02)
    # 3. Volume automation: first 1 sec *1.5, then every 3 sec 5% sin modulation + bass
    # Using ffmpeg volume expressions
    try:
        # volume filter with timeline: first 1 sec 1.5, rest 1 + 0.05*sin(t/3*PI)
        # bass = low freq boost with bass filter
        vf = (
            f"atempo={TTS_SPEED},"
            f"asetrate=22050*1.02,aresample=22050,"
            f"volume='if(lt(t,1),{PUNCH_VOLUME},1+{VOL_MODULATION_PERCENT}*sin(2*PI*t/{VOL_MODULATION_EVERY_SEC}))',"
            f"bass=g=3:f=100"
        )
        cmd = [
            "ffmpeg","-y",
            "-i", input_path,
            "-af", vf,
            "-c:a","pcm_s16le",
            output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[TTS RETENTION] Applied: speed {TTS_SPEED}X + pitch up + punch {PUNCH_VOLUME} + vol mod every {VOL_MODULATION_EVERY_SEC}s + bass")
        return True
    except Exception as e:
        print(f"[TTS FFmpeg fail] {e}, using moviepy fallback")
        return False

def apply_moviepy_fallback(input_path, output_path):
    """Fallback if ffmpeg not available - using moviepy"""
    try:
        from moviepy.editor import AudioFileClip, CompositeAudioClip
        import moviepy.audio.fx.all as afx
        
        audio = AudioFileClip(input_path)
        # 1.15X speed
        audio = audio.fx(afx.audio_fadein, 0.05).fx(afx.audio_fadeout, 0.05)
        try:
            from moviepy.audio.fx.speedx import speedx
            audio = audio.fx(speedx, TTS_SPEED)
        except:
            pass
        
        # Audio punch first 1 sec
        def vol_func(t):
            if t < 1:
                return PUNCH_VOLUME
            # har 3 sec 5% up/down
            mod = VOL_MODULATION_PERCENT * math.sin(2*math.pi*t/VOL_MODULATION_EVERY_SEC)
            return 1.0 + mod
        
        # Moviepy volumex with function not stable, use simple split
        if audio.duration > 1:
            a1 = audio.subclip(0,1).volumex(PUNCH_VOLUME)
            a2 = audio.subclip(1, audio.duration)
            # Apply 5% modulation to a2 via iterative clips every 3 sec
            clips=[]
            t=0
            while t < a2.duration:
                seg_dur = min(3, a2.duration - t)
                seg = a2.subclip(t, t+seg_dur)
                # alternate 5% up/down
                factor = 1.05 if int(t/3) % 2 == 0 else 0.95
                seg = seg.volumex(factor)
                clips.append(seg.set_start(t))
                t+=seg_dur
            # Composite
            if clips:
                rest = CompositeAudioClip(clips)
                final = CompositeAudioClip([a1, rest.set_start(1)])
                final.write_audiofile(output_path, fps=22050, logger=None)
                return True
            else:
                audio = CompositeAudioClip([a1, a2.set_start(1)])
        
        audio.write_audiofile(output_path, fps=22050, logger=None)
        return True
    except Exception as e:
        print(f"[MoviePy fallback fail] {e}")
        return False

def generate_voice(text, out_path="output/voice.wav"):
    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    temp_raw = "temp/voice_raw.wav"
    
    # Step 1: Generate raw TTS - BOY VOICE RYAN MEDIUM
    try:
        from piper import PiperVoice
        model_path = "models/en_US-ryan-medium.onnx"
        # Try multiple possible paths - BOY VOICE ONLY
        for p in [model_path, "piper_model/en_US-ryan-medium.onnx", "models/en_US-ryan-medium.onnx"]:
            if os.path.exists(p):
                model_path = p
                break
        voice = PiperVoice.load(model_path)
        with wave.open(temp_raw, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            first=True
            for chunk in voice.synthesize(text):
                if first:
                    # Try to get sample rate from chunk if available
                    try:
                        wf.setframerate(chunk.sample_rate)
                    except:
                        wf.setframerate(22050)
                    first=False
                # piper returns audio_int16_bytes or audio_int16?
                data = getattr(chunk, 'audio_int16_bytes', None) or getattr(chunk, 'audio_int_16_bytes', None) or getattr(chunk, 'audio_int16', None)
                if data is None:
                    # fallback: chunk may be bytes directly
                    data = bytes(chunk) if isinstance(chunk, (bytes, bytearray)) else chunk.audio_int16_bytes
                wf.writeframes(data)
        print(f"[TTS BOY VOICE] Raw generated: {temp_raw} - RYAN MEDIUM")
    except Exception as e:
        print(f"Piper fail {e}, using espeak-ng fallback - BOY VOICE")
        # espeak with faster rate 165 ~ 1.10x of normal 135 - boy pitch 50
        safe_text = text.replace('"','').replace("'","")[:500]
        os.system(f'espeak-ng -v en-us+m3 "{safe_text}" -s 165 -p 45 --stdout > {temp_raw}')
    
    # Step 2: Apply retention filters (VvSA + Sound retention)
    success = apply_ffmpeg_retention_filters(temp_raw, out_path)
    if not success:
        success = apply_moviepy_fallback(temp_raw, out_path)
    
    if not success:
        # If both fail, just copy raw to out
        import shutil
        shutil.copy(temp_raw, out_path)
        print(f"[TTS] Fallback copy raw to {out_path}")
    
    # Cleanup
    try:
        if os.path.exists(temp_raw):
            os.remove(temp_raw)
    except:
        pass
    
    print(f"[TTS FINAL BOY] {out_path} - Speed {TTS_SPEED}X, Punch {PUNCH_VOLUME} first 1s, Vol mod every {VOL_MODULATION_EVERY_SEC}s {int(VOL_MODULATION_PERCENT*100)}% + bass drop - RYAN MEDIUM BOY")
    return out_path

# Backward compat function for video_generator.py that expects generate_voice
def generate_voice_with_retention(text, out_path="output/voice.wav"):
    return generate_voice(text, out_path)

if __name__=="__main__":
    test_text = "This just leaked behind closed doors and changes everything. You won't believe what happened next."
    generate_voice(test_text)
