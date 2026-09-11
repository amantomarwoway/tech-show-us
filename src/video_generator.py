import os, random, requests, tempfile, re, wave, subprocess, glob
from pathlib import Path
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont
from piper import PiperVoice

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 210
BLACK_TOP_STRIP = 150
BLACK_BORDER = 16
CLIP_DENSITY = 0.8
DURATION_MAX = 15
FPS_CHOICES = [29.97,30,59.94,60]
NOISE_HUE_FILTER = "noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08"
RETENTION_WORDS = 50

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
def pro_headers(): return {"User-Agent": random.choice(USER_AGENTS),"Cache-Control":"no-cache"}

def pro_fetch_force(url, dest_path, timeout=90, retries=10):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(0.05,0.25))
            cb = f"{'&' if '?' in url else '?'}cb={random.randint(100000,999999)}&t={int(time.time())}"
            print(f"[PIPER PRO FORCE] Downloading {url[:60]} attempt {attempt+1}")
            r = requests.get(url+cb, headers=pro_headers(), timeout=timeout, stream=True)
            if r.status_code==200:
                with open(dest_path,'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk: f.write(chunk)
                if os.path.exists(dest_path) and os.path.getsize(dest_path)>1000:
                    return True
            print(f"[PIPER PRO] Status {r.status_code} retry {attempt} - FORCE")
            time.sleep((2**attempt)+random.uniform(0,0.8))
        except Exception as e:
            print(f"[PIPER PRO] Fail {e} attempt {attempt} - FORCE")
            time.sleep((2**attempt)+random.uniform(0,0.8))
    raise RuntimeError(f"PIPER MODEL DOWNLOAD FAILED after {retries} - NO FALLBACK - {url}")

PIPER_MODELS = {
    "ryan-medium": {"onnx":"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx","json":"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"},
    "amy-medium": {"onnx":"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx","json":"https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"}
}

def get_piper_voice_pro_force():
    os.makedirs("models", exist_ok=True)
    for model_name, urls in PIPER_MODELS.items():
        mp=f"models/en_US-{model_name}.onnx"; cp=f"models/en_US-{model_name}.onnx.json"
        if not os.path.exists(mp) or os.path.getsize(mp)<1000:
            pro_fetch_force(urls['onnx'], mp, timeout=120, retries=10)
        if not os.path.exists(cp) or os.path.getsize(cp)<1000:
            pro_fetch_force(urls['json'], cp, timeout=60, retries=10)
        try:
            voice=PiperVoice.load(mp, cp)
            print(f"[PIPER PRO FORCE] Loaded {model_name} - NO FALLBACK")
            return voice, model_name
        except Exception as e:
            print(f"[PIPER PRO] Load fail {model_name} {e} - FORCE RETRY NEXT MODEL")
            try: os.remove(mp)
            except: pass
            try: os.remove(cp)
            except: pass
            continue
    raise RuntimeError("ALL PIPER MODELS FAILED - NO FALLBACK - FORCE")

def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\s+',' ',t).strip(); return t

def get_best_free_clips_from_script_force(script_data, num=20):
    import glob as glob2
    real = glob2.glob("output/assets/*.jpg") + glob2.glob("output/assets/*.mp4") + glob2.glob("temp/duck_*.jpg") + glob2.glob("temp/ytdlp_*.mp4")
    if not real:
        raise RuntimeError("No real assets found - NO FALLBACK - FORCE")
    clips=[]
    random.shuffle(real)
    for f in real[:num]:
        if f.lower().endswith(('.jpg','.png')):
            clips.append(ImageClip(f, duration=CLIP_DENSITY).resize(height=HEIGHT).set_position('center'))
        else:
            clips.append(VideoFileClip(f).subclip(0,2).resize(height=HEIGHT).set_position('center').without_audio())
    if not clips:
        raise RuntimeError("No clips created from real assets - NO FALLBACK")
    return clips[:num]

def make_74k_white_bar_FINAL(text, bar_height=210):
    viral_text = " ".join(clean_id(text).split()[:8])[:62]
    if not viral_text: raise RuntimeError("Empty white bar text - NO FALLBACK")
    words=viral_text.split()
    lines=[" ".join(words[:len(words)//2]), " ".join(words[len(words)//2:])] if len(words)>=4 else [viral_text]
    total_h=BLACK_TOP_STRIP+WHITE_BAR_HEIGHT
    img=Image.new('RGB', (WIDTH, total_h), (0,0,0))
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,WIDTH,BLACK_TOP_STRIP], fill=(0,0,0))
    d.rectangle([0,BLACK_TOP_STRIP,WIDTH,total_h], fill=(255,255,255))
    try:
        f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
        f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    except:
        f1=f2=ImageFont.load_default()
    if len(lines)==1:
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2), lines[0], font=f1, fill=(0,0,0), anchor="mm")
    else:
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2-32), lines[0], font=f1, fill=(0,0,0), anchor="mm")
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2+32), lines[1], font=f2, fill=(0,0,0), anchor="mm")
    p=f"temp/whitebar_final_{random.randint(1,999999)}.png"
    os.makedirs("temp", exist_ok=True); img.save(p, quality=95)
    return p, total_h

def make_74k_bottom_text_FINAL(text, total):
    if not text: raise RuntimeError("Empty bottom text - NO FALLBACK")
    img=Image.new('RGBA', (WIDTH, 200), (0,0,0,0))
    d=ImageDraw.Draw(img)
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    except: f=ImageFont.load_default()
    d.text((WIDTH//2,100), f"👇 {clean_id(text)[:50]} 👇", font=f, fill="#FFE600", anchor="mm", stroke_width=4, stroke_fill="black")
    p=f"temp/bottom_final_{random.randint(1,999999)}.png"
    img.save(p)
    return ImageClip(p).set_duration(total).set_position((0, HEIGHT-250))

def make_black_rounded_border_FINAL(total):
    img=Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,WIDTH,BLACK_BORDER], fill=(0,0,0))
    d.rectangle([0,HEIGHT-BLACK_BORDER,WIDTH,HEIGHT], fill=(0,0,0))
    d.rectangle([0,0,BLACK_BORDER,HEIGHT], fill=(0,0,0))
    d.rectangle([WIDTH-BLACK_BORDER,0,WIDTH,HEIGHT], fill=(0,0,0))
    p=f"temp/border_final_{random.randint(1,999999)}.png"
    img.save(p)
    return ImageClip(p).set_duration(total)

def word_clip_FINAL(word, dur, is_keyword=False, is_first=False):
    word=clean_id(word)
    if not word: return None
    color="#FFEB3B" if is_keyword else "#FFFFFF"
    fontsize=92 if is_first else (86 if is_keyword else 72)
    stroke=6 if is_first else 4
    path=f"temp/txt_{random.randint(1,999999)}.png"
    img=Image.new('RGBA', (WIDTH, 300), (0,0,0,0))
    d=ImageDraw.Draw(img)
    try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except: font=ImageFont.load_default()
    d.text((WIDTH//2,150), word.upper(), font=font, fill=color, anchor="mm", stroke_width=stroke, stroke_fill="black")
    img.save(path)
    clip=ImageClip(path).set_duration(dur).set_position(('center',0.65),relative=True)
    clip=clip.resize(lambda t: 1.4-0.25*t/dur if is_first and t<dur*0.4 else (1.15-0.15*t/dur if t<dur*0.3 else 1.0))
    return clip

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    raw_script=script_data.get('full_script','') if isinstance(script_data, dict) else str(script_data)
    title=script_data.get('title','Breaking News') if isinstance(script_data, dict) else raw_script[:50]
    viral_hook=script_data.get('viral_hook','') or title
    if not raw_script: raise RuntimeError("Empty script - NO FALLBACK")
    script_text=clean_id(raw_script)
    if len(script_text.split())>50: script_text=" ".join(script_text.split()[:50])
    os.makedirs("output",exist_ok=True); os.makedirs("temp",exist_ok=True)

    # PIPER FORCE - NO GTTS FALLBACK
    voice, model_name = get_piper_voice_pro_force()
    audio_path="temp/voice.wav"
    import wave
    print(f"[PIPER PRO FORCE] Synthesizing {len(script_text.split())} words with {model_name} - NO FALLBACK")
    with wave.open(audio_path,"wb") as wav:
        first=True
        for chunk in voice.synthesize(script_text):
            if first:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(chunk.sample_rate); first=False
                print(f"[PIPER PRO FORCE] Sample rate {chunk.sample_rate}")
            wav.writeframes(chunk.audio_int16_bytes)
    if not os.path.exists(audio_path) or os.path.getsize(audio_path)<1000:
        raise RuntimeError(f"Piper wav failed {audio_path} - NO FALLBACK")

    audio=AudioFileClip(audio_path)
    total=min(max(audio.duration, 11), DURATION_MAX)
    raw_clips=get_best_free_clips_from_script_force(script_data, num=int(total/CLIP_DENSITY)+3)
    final_clips=[]; t=0
    for c in raw_clips:
        if t>=total: break
        dur=min(CLIP_DENSITY, total-t)
        final_clips.append(c.subclip(0,dur).set_start(t)); t+=dur
    base_video=CompositeVideoClip(final_clips, size=(WIDTH,HEIGHT)).set_duration(total)
    whitebar_path,_=make_74k_white_bar_FINAL(viral_hook)
    white_bar=ImageClip(whitebar_path).set_duration(total).set_position((0,0))
    bottom=make_74k_bottom_text_FINAL(viral_hook, total)
    border=make_black_rounded_border_FINAL(total)
    words=script_text.split()
    caption_clips=[]; cur=0
    base_dur=total/max(len(words),1)*0.95
    base_dur=max(0.28, min(0.38, base_dur))
    for i,w in enumerate(words):
        is_first=i<5
        is_kw=any(k in w.upper() for k in ["LEAKED","SECRET","BREAKING","SHOCKING","TRUMP","BIDEN"]) or is_first
        dur=base_dur*1.4 if is_first else (base_dur*1.2 if is_kw else base_dur)
        if cur>=total: break
        if cur+dur>total: dur=max(0.15,total-cur)
        wc=word_clip_FINAL(w.upper(), dur, is_kw, is_first)
        if wc: caption_clips.append(wc.set_start(cur))
        cur+=dur*0.92
    comp=CompositeVideoClip([base_video, white_bar, bottom, border]+caption_clips, size=(WIDTH,HEIGHT)).set_duration(total)
    comp=comp.set_audio(audio)
    fps=random.choice(FPS_CHOICES)
    temp_out=output_path.replace(".mp4","_temp.mp4")
    comp.write_videofile(temp_out, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
    cmd=["ffmpeg","-y","-i", temp_out,"-vf", NOISE_HUE_FILTER,"-r", str(fps),"-c:v","libx264","-crf","20","-preset","veryfast","-c:a","aac","-b:a","128k",output_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try: os.remove(temp_out)
    except: pass
    if not os.path.exists(output_path):
        raise RuntimeError(f"Video not created {output_path} - NO FALLBACK")
    print(f"[RENDER PRO FORCE] {output_path} - PIPER {model_name} - NO FALLBACK - PEAK")
    return output_path
