import os, random, requests, tempfile, re, wave, math, subprocess, struct
from pathlib import Path
try:
    from moviepy.editor import *
    MOVIEPY_AVAILABLE=True
except:
    MOVIEPY_AVAILABLE=False
try:
    from piper import PiperVoice
    PIPER_AVAILABLE=True
except:
    PiperVoice=None
    PIPER_AVAILABLE=False
try:
    from gtts import gTTS
    GTTS_AVAILABLE=True
except:
    GTTS_AVAILABLE=False
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"
RETENTION_WORDS = 40
CLIP_DENSITY = 0.8
DURATION_MAX = 13
FPS_CHOICES = [29.97, 30, 59.94, 60]
NOISE_HUE_FILTER = "noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08"
WIDTH, HEIGHT = 1080, 1920
def get_piper_voice():
    if not PIPER_AVAILABLE: return None
    try:
        os.makedirs("models", exist_ok=True)
        mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
        if not os.path.exists(mp):
            open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
            open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
        return PiperVoice.load(mp, cp)
    except: return None
def trim_to_40_words(t):
    w=t.split()
    return " ".join(w[:RETENTION_WORDS])
def get_best_free_clips_fixed(q, num=15):
    try:
        from moviepy.editor import ColorClip
    except: return []
    return [ColorClip((1080,1920),color=(random.randint(15,35),random.randint(15,45),random.randint(50,90)),duration=CLIP_DENSITY) for _ in range(num)]
def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or script_data.get('script','') or ""
    else:
        raw_script=str(script_data)
    os.makedirs("output",exist_ok=True); os.makedirs("temp",exist_ok=True)
    script_text = trim_to_40_words(raw_script)
    print(f"[RETENTION] {len(script_text.split())} words")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    try:
        if voice:
            with wave.open(audio_path,"wb") as wav:
                first=True
                for ch in voice.synthesize(script_text):
                    if first:
                        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                    wav.writeframes(ch.audio_int16_bytes)
        else:
            if GTTS_AVAILABLE:
                tts_path="temp/voice.mp3"
                gTTS(text=script_text, lang='en', slow=False).save(tts_path)
                subprocess.run(["ffmpeg","-y","-i", tts_path, audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                raise Exception("no tts")
    except Exception as e:
        print(f"[TTS] silent fallback {e}")
        with wave.open(audio_path,"wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(24000)
            wav.writeframes(struct.pack('<h', 0) * 24000 * 12)
    if not MOVIEPY_AVAILABLE:
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"color=c=0x1a1a3c:s=1080x1920:d=12","-i",audio_path,"-shortest",output_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    from moviepy.editor import AudioFileClip, CompositeVideoClip, ColorClip
    try:
        audio=AudioFileClip(audio_path)
        total=min(audio.duration, DURATION_MAX)
    except:
        total=12.0; audio=None
    clips_needed = max(8, int(math.ceil(total / CLIP_DENSITY)) + 2)
    raw_clips = get_best_free_clips_fixed("", num=clips_needed)
    final_video_clips=[]
    t=0
    for c in raw_clips:
        if t >= total: break
        try:
            dur = min(CLIP_DENSITY, total-t, c.duration)
            sub = c.subclip(0, dur).set_start(t)
            final_video_clips.append(sub); t+=dur
        except: continue
    if not final_video_clips:
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=(20,20,60), duration=total)]
    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    comp = CompositeVideoClip([base_video], size=(WIDTH, HEIGHT)).set_duration(total)
    fps = random.choice(FPS_CHOICES)
    if audio: comp = comp.set_audio(audio)
    temp_out = output_path.replace(".mp4","_temp.mp4")
    try:
        comp.write_videofile(temp_out, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
    except:
        pass
    try:
        cmd = ["ffmpeg","-y","-i", temp_out,"-vf", NOISE_HUE_FILTER,"-r", str(fps),"-c:v","libx264","-crf","20","-preset","veryfast","-c:a","aac","-b:a","128k",output_path]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try: os.remove(temp_out)
        except: pass
    except:
        try: os.rename(temp_out, output_path)
        except: pass
    return output_path
