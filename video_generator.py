# video_generator.py - REAL AEROPLANE - RETENTION POWER - DETAILED FIXED
import os, random, requests, tempfile, re, wave, subprocess, glob
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 210
BLACK_TOP_STRIP = 150
CLIP_DENSITY = 0.8 # 0.8 sec fast cuts - retention
DURATION_MIN = 11
DURATION_MAX = 15
FPS_CHOICES = [29.97, 30]

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"

def get_piper_voice():
    """Piper Ryan American voice - size check ke saath"""
    try:
        from piper import PiperVoice
        os.makedirs("models", exist_ok=True)
        mp="models/en_US-ryan-medium.onnx"
        cp="models/en_US-ryan-medium.onnx.json"
        # Size check - khali file nahi
        if not os.path.exists(mp) or os.path.getsize(mp) < 100000:
            print("[PIPER] Downloading Ryan model...")
            r=requests.get(MODEL_URL, timeout=60)
            if r.status_code==200 and len(r.content)>100000:
                open(mp,'wb').write(r.content)
                print(f"[PIPER] Model downloaded {len(r.content)} bytes")
        if not os.path.exists(cp):
            r=requests.get(CONFIG_URL, timeout=60)
            if r.status_code==200: open(cp,'wb').write(r.content)
        voice = PiperVoice.load(mp, cp)
        print("[PIPER] Ryan voice loaded - retention power")
        return voice
    except Exception as e:
        print(f"[PIPER] Fail {e} - using fallback")
        raise

def clean_id(text): return re.sub(r'\s+', ' ', text).strip() if text else ""
def clean_script_no_trim(text): return clean_id(text)

def get_best_free_clips_from_script(script_data, num=20):
    """Pexels se best clips - detailed search"""
    key=os.getenv("PEXELS_API_KEY")
    if not key:
        return [ColorClip(size=(WIDTH,HEIGHT), color=(30,20,40), duration=CLIP_DENSITY) for _ in range(num)]
    try:
        h={"Authorization":key}
        q="shocked man reaction"
        if isinstance(script_data, dict):
            q=script_data.get('viral_hook','') or script_data.get('title','') or "shocked man reaction"
        q=q[:40]
        url=f"https://api.pexels.com/videos/search?query={q}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url,headers=h,timeout=20).json()
        clips=[]
        for v in res.get('videos',[])[:num*2]:
            if len(clips)>=num: break
            try:
                link=sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
                tmp=tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); tmp.close()
                r=requests.get(link, timeout=30)
                if r.status_code!=200: continue
                open(tmp.name,'wb').write(r.content)
                if os.path.getsize(tmp.name) < 50000: os.remove(tmp.name); continue
                vc=VideoFileClip(tmp.name).subclip(0, min(2, VideoFileClip(tmp.name).duration)).resize(height=1920).set_position('center').without_audio()
                clips.append(vc)
            except: continue
        if clips:
            random.shuffle(clips)
            return clips[:num]
    except Exception as e:
        print(f"Pexels error: {e}")
    return [ColorClip(size=(WIDTH,HEIGHT), color=(30,20,40), duration=CLIP_DENSITY) for _ in range(num)]

def make_74k_white_bar_FINAL(text, bar_height=210):
    """White bar with black top - 2 line hook"""
    viral_text = clean_id(text)[:35]
    words = viral_text.split()
    if len(words)>=4:
        mid=(len(words)+1)//2
        lines=[" ".join(words[:mid]), " ".join(words[mid:])]
    else: lines=[viral_text]
    img=Image.new('RGB', (WIDTH, 360), (0,0,0))
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,WIDTH,150], fill=(0,0,0))
    d.rectangle([0,150,WIDTH,360], fill=(255,255,255))
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except: f=ImageFont.load_default()
    if len(lines)==1: d.text((WIDTH//2,255), lines[0], font=f, fill=(0,0,0), anchor="mm")
    else:
        d.text((WIDTH//2,220), lines[0], font=f, fill=(0,0,0), anchor="mm")
        d.text((WIDTH//2,290), lines[1], font=f, fill=(0,0,0), anchor="mm")
    p=f"temp/whitebar_{random.randint(1,999999)}.png"
    os.makedirs("temp", exist_ok=True); img.save(p, quality=95)
    return p, 360

def word_clip_FINAL(word, dur, is_keyword, is_first):
    """Word clip - 1.6X punch for first 5 words, 1.2X for keywords"""
    path=f"temp/txt_{random.randint(1,999999)}.png"
    img=Image.new('RGBA', (800,200), (0,0,0,0))
    d=ImageDraw.Draw(img)
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90 if is_first else 75)
    except: f=ImageFont.load_default()
    # Black border for visibility
    for dx in [-2,0,2]:
        for dy in [-2,0,2]:
            d.text((400+dx,100+dy), word, font=f, fill=(0,0,0), anchor="mm")
    d.text((400,100), word, font=f, fill=(255,255,0) if is_keyword else (255,255,255), anchor="mm")
    img.save(path)
    clip=ImageClip(path).set_duration(dur).set_position(('center',0.65),relative=True)
    # 1.6X punch for first word, 1.2X for keywords
    if is_first:
        clip = clip.resize(lambda t: 1.6 - 0.35*t/dur if t < dur*0.4 else 1.0)
    elif is_keyword:
        clip = clip.resize(lambda t: 1.25 - 0.15*t/dur if t < dur*0.3 else 1.0)
    return clip

def create_video(script_data, story=None, output_path="output/final.mp4"):
    """Create DETAILED video - retention power 1.11X + 1.6X"""
    raw_script=script_data.get('full_script','') or script_data.get('short_script','') if isinstance(script_data, dict) else str(script_data)
    title=script_data.get('title','Breaking News') if isinstance(script_data, dict) else raw_script[:50]
    viral_hook=script_data.get('viral_hook','') or title if isinstance(script_data, dict) else title
    first_punch=script_data.get('first_sentence_punch','') or viral_hook[:60]

    os.makedirs("output",exist_ok=True); os.makedirs("temp",exist_ok=True)
    script_text=clean_script_no_trim(raw_script)[:300]
    if len(script_text.split())>50: script_text=" ".join(script_text.split()[:50])

    # TTS - Piper Ryan with retention filter
    audio_path="temp/voice.wav"
    try:
        voice=get_piper_voice()
        audio_chunks=[]; sr=22050
        try:
            gen=voice.synthesize(script_text)
            for ch in gen: audio_chunks.append(ch); sr=ch.sample_rate
        except: audio_chunks=[]
        if not audio_chunks:
            with wave.open(audio_path,"wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
                wav.writeframes(bytes([0]*22050*4))
        else:
            with wave.open(audio_path,"wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr)
                for ch in audio_chunks: wav.writeframes(ch.audio_int16_bytes)
        # Retention filter - 1.11X speed + echo
        filtered="temp/voice_filtered.wav"
        try:
            cmd=["ffmpeg","-y","-i",audio_path,"-af","atempo=1.11, aecho=0.8:0.88:6:0.4","-c:a","pcm_s16le",filtered]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio=AudioFileClip(filtered)
        except:
            audio=AudioFileClip(audio_path)
    except Exception as e:
        print(f"TTS fail {e} - using silent")
        from moviepy.editor import AudioClip
        import numpy as np
        def make_frame(t): return [0]
        audio=AudioClip(make_frame, duration=12)

    total=getattr(audio,'duration',12)
    if total<11: total=11
    if total>15:
        total=15
        try: audio=audio.subclip(0,15)
        except: pass

    # Best clips - 0.8s density fast cuts
    raw_clips=get_best_free_clips_from_script(script_data, num=int(total/0.8)+2)
    final_clips=[]; t=0
    for c in raw_clips:
        if t>=total: break
        dur=min(0.8, total-t)
        try: final_clips.append(c.subclip(0,dur).set_start(t))
        except: final_clips.append(c.set_start(t).set_duration(dur))
        t+=dur
    if not final_clips: final_clips=[ColorClip((WIDTH,HEIGHT), color=(30,20,40), duration=total)]
    base_video=CompositeVideoClip(final_clips, size=(WIDTH,HEIGHT)).set_duration(total)

    # White bar + captions with retention timing
    white_path,_=make_74k_white_bar_FINAL(viral_hook)
    white_clip=ImageClip(white_path).set_duration(total).set_position((0,0))

    try:
        from src.audio_retention import get_american_captions_timing
        timing=get_american_captions_timing(total, len(script_text.split()), 5)
        base_dur=timing["base_dur"]; first_dur=timing["first_dur"]; keyword_dur=timing["keyword_dur"]; overlap=timing["overlap"]
    except:
        base_dur=total/max(len(script_text.split()),1)*0.95
        base_dur=max(0.28, min(0.38, base_dur))
        first_dur=base_dur*1.6; keyword_dur=base_dur*1.2; overlap=0.92

    words=script_text.split()
    caption_clips=[]; current_time=0
    first_count=min(5, len(words))
    for i,w in enumerate(words):
        is_first=i<first_count
        is_kw=any(k in w.upper() for k in ["BRUTAL","SHOCKING","BREAKING","TRUMP","BIDEN","PANIC","MILLIONS","SECRET","LEAKED","WHITE","HOUSE"]) or is_first
        dur=first_dur if is_first else (keyword_dur if is_kw else base_dur)
        if current_time>=total: break
        if current_time+dur>total: dur=max(0.15, total-current_time)
        wc=word_clip_FINAL(w.upper(), dur, is_kw, is_first).set_start(current_time)
        caption_clips.append(wc)
        current_time+=dur*overlap

    comp=CompositeVideoClip([base_video, white_clip] + caption_clips, size=(WIDTH,HEIGHT)).set_duration(total).set_audio(audio)
    comp.write_videofile(output_path, fps=random.choice(FPS_CHOICES), codec='libx264', audio_codec='aac', preset='ultrafast', threads=2, logger=None)

    # Cleanup temp files - detailed video ke liye jaruri
    try:
        for f in glob.glob("temp/whitebar_*.png") + glob.glob("temp/txt_*.png") + glob.glob("temp/voice*.wav"):
            try: os.remove(f)
            except: pass
    except: pass

    print(f"VIDEO READY {output_path} - {total}s - Retention Power")
    return output_path
