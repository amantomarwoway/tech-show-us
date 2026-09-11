import os, random, requests, tempfile, re, wave, math, subprocess, struct, glob
from pathlib import Path
from moviepy.editor import *
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

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

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 210
BLACK_TOP_STRIP = 150
BLACK_BOTTOM_STRIP = 200
BLACK_BORDER = 16
CLIP_DENSITY = 0.8
DURATION_MIN = 11
DURATION_MAX = 15
FPS_CHOICES = [29.97, 30, 59.94, 60]
NOISE_HUE_FILTER = "noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08"

FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"]
def pro_headers():
    return {"User-Agent": random.choice(USER_AGENTS),"Cache-Control":"no-cache","Pragma":"no-cache","Referer":random.choice(["https://www.google.com/","https://news.google.com/"])}

def get_piper_voice():
    if not PIPER_AVAILABLE: return None
    try:
        os.makedirs("models", exist_ok=True)
        mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
        if not os.path.exists(mp):
            open(mp,'wb').write(requests.get(MODEL_URL, timeout=60, headers=pro_headers()).content)
            open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60, headers=pro_headers()).content)
        return PiperVoice.load(mp, cp)
    except: return None

def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\b[mM][0-9][a-z0-9]+\b','',t); t=re.sub(r'\s+',' ',t).strip(); return t

def get_best_free_clips_from_script(script_data, num=20):
    # PRO HACKER - REAL assets first, not color
    import glob as glob2
    real_files = glob2.glob("temp/duck_*.jpg") + glob2.glob("temp/ytdlp_*.mp4") + glob2.glob("output/assets/*.jpg") + glob2.glob("output/assets/*.mp4")
    if real_files:
        clips=[]
        random.shuffle(real_files)
        for f in real_files[:num]:
            try:
                if f.lower().endswith(('.jpg','.jpeg','.png')):
                    clips.append(ImageClip(f, duration=CLIP_DENSITY).resize(height=HEIGHT).set_position('center'))
                else:
                    clips.append(VideoFileClip(f).subclip(0, min(CLIP_DENSITY,2)).resize(height=HEIGHT).set_position('center').without_audio())
            except: continue
        if clips:
            print(f"[VISUALS] {len(clips)} REAL assets from DuckDuckGo+yt-dlp - subs/views ke liye")
            return clips[:num]
    # Pexels fallback with pro headers
    key=os.getenv("PEXELS_API_KEY")
    if key:
        try:
            q=script_data.get('pexels_query','') if isinstance(script_data, dict) else str(script_data)[:50]
            q=clean_id(q)[:30] or "shocked man reaction"
            h={"Authorization":key, **pro_headers()}
            url=f"https://api.pexels.com/videos/search?query={q}&per_page={num*2}&orientation=portrait&size=medium"
            res=requests.get(url,headers=h,timeout=20).json()
            videos=res.get('videos',[])
            clips=[]
            for v in videos[:num]:
                try:
                    link=sorted(v['video_files'], key=lambda x:x['width'])[-1]['link']
                    tmp=tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    open(tmp,'wb').write(requests.get(link, timeout=30, headers=pro_headers()).content)
                    clip=VideoFileClip(tmp).subclip(0,2).resize(height=1920).set_position('center').without_audio()
                    clips.append(clip)
                except: continue
            if clips: return clips[:num]
        except Exception as e:
            print(f"Pexels fail {e}")
    return [ColorClip(size=(WIDTH,HEIGHT), color=(30,20,40), duration=CLIP_DENSITY) for _ in range(num)]

def make_74k_white_bar_FINAL(text, bar_height=210):
    viral_text = " ".join(clean_id(text).split()[:8])[:62]
    words=viral_text.split()
    if len(words)>=4:
        mid=(len(words)+1)//2
        lines=[" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines=[viral_text]
    total_h=BLACK_TOP_STRIP+WHITE_BAR_HEIGHT
    img=Image.new('RGB', (WIDTH, total_h), (0,0,0))
    d=ImageDraw.Draw(img)
    d.rectangle([0,0,WIDTH,BLACK_TOP_STRIP], fill=(0,0,0))
    d.rectangle([0,BLACK_TOP_STRIP,WIDTH,total_h], fill=(255,255,255))
    try:
        f1=ImageFont.truetype(FONT_BOLD_ITALIC, 58)
        f2=ImageFont.truetype(FONT_BOLD_ITALIC, 56)
    except:
        f1=ImageFont.load_default(); f2=ImageFont.load_default()
    if len(lines)==1:
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2), lines[0], font=f1, fill=(0,0,0), anchor="mm")
    else:
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2-32), lines[0], font=f1, fill=(0,0,0), anchor="mm")
        d.text((WIDTH//2, BLACK_TOP_STRIP+WHITE_BAR_HEIGHT//2+32), lines[1], font=f2, fill=(0,0,0), anchor="mm")
    p=f"temp/whitebar_final_{random.randint(1,999999)}.png"
    os.makedirs("temp", exist_ok=True); img.save(p, quality=95)
    return p, total_h

def make_74k_bottom_text_FINAL(text, total):
    try:
        img=Image.new('RGBA', (WIDTH, 200), (0,0,0,0))
        d=ImageDraw.Draw(img)
        f=ImageFont.truetype(FONT_BOLD, 42) if os.path.exists(FONT_BOLD) else ImageFont.load_default()
        d.text((WIDTH//2, 100), f"👇 {clean_id(text)[:50]} 👇", font=f, fill="#FFE600", anchor="mm", stroke_width=4, stroke_fill="black")
        p=f"temp/bottom_final_{random.randint(1,999999)}.png"
        img.save(p)
        return ImageClip(p).set_duration(total).set_position((0, HEIGHT-250))
    except:
        return ColorClip((WIDTH,200), color=(0,0,0), duration=total).set_position((0, HEIGHT-250))

def make_black_rounded_border_FINAL(total):
    try:
        img=Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
        d=ImageDraw.Draw(img)
        d.rectangle([0,0,WIDTH,BLACK_BORDER], fill=(0,0,0))
        d.rectangle([0,HEIGHT-BLACK_BORDER,WIDTH,HEIGHT], fill=(0,0,0))
        d.rectangle([0,0,BLACK_BORDER,HEIGHT], fill=(0,0,0))
        d.rectangle([WIDTH-BLACK_BORDER,0,WIDTH,HEIGHT], fill=(0,0,0))
        p=f"temp/border_final_{random.randint(1,999999)}.png"
        img.save(p)
        return ImageClip(p).set_duration(total).set_position((0,0))
    except:
        return ColorClip((WIDTH,HEIGHT), color=(0,0,0,0), duration=total)

def word_clip_FINAL(word, dur, is_keyword=False, is_first_word=False):
    word=clean_id(word)
    if not word: return None
    color="#FFEB3B" if is_keyword else "#FFFFFF"
    fontsize=92 if is_first_word else (86 if is_keyword else 72)
    stroke=6 if is_first_word else 4
    path=f"temp/txt_{random.randint(1,999999)}.png"
    try:
        img=Image.new('RGBA', (WIDTH, 300), (0,0,0,0))
        d=ImageDraw.Draw(img)
        font=ImageFont.truetype(FONT_BOLD, fontsize) if os.path.exists(FONT_BOLD) else ImageFont.load_default()
        d.text((WIDTH//2,150), word.upper(), font=font, fill=color, anchor="mm", stroke_width=stroke, stroke_fill="black")
        img.save(path)
    except: return None
    clip=ImageClip(path).set_duration(dur).set_position(('center',0.65),relative=True)
    if is_first_word:
        clip=clip.resize(lambda t: 1.4-0.25*t/dur if t<dur*0.4 else 1.0)
    else:
        clip=clip.resize(lambda t: 1.15-0.15*t/dur if t<dur*0.3 else 1.0)
    return clip

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or script_data.get('short_script','') or ""
        title=script_data.get('title','Brutal New Tariffs Panic Millions')
        viral_hook=script_data.get('viral_hook','') or script_data.get('seo_youtube_title','') or title
    else:
        raw_script=str(script_data); title=raw_script[:50]; viral_hook=title
    os.makedirs("output",exist_ok=True); os.makedirs("temp",exist_ok=True)
    script_text=clean_id(raw_script)
    if len(script_text.split())>50:
        script_text=" ".join(script_text.split()[:50])
    print(f"[TITLE] {title}")
    print(f"[SCRIPT] {script_text[:80]}... ({len(script_text.split())} words)")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    gtts_done=False
    if not voice:
        try:
            from gtts import gTTS
            tmp_mp3="temp/voice.mp3"
            gTTS(text=script_text, lang='en', slow=False).save(tmp_mp3)
            subprocess.run(["ffmpeg","-y","-i", tmp_mp3, audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            gtts_done=True
        except: pass
    if not gtts_done:
        try:
            import wave
            if voice:
                with wave.open(audio_path,"wb") as wav:
                    first=True
                    for ch in voice.synthesize(script_text):
                        if first:
                            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                        wav.writeframes(ch.audio_int16_bytes)
            else:
                raise Exception("no voice")
        except:
            import wave, struct
            with wave.open(audio_path,"wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(24000)
                wav.writeframes(struct.pack('<h',0)*24000*12)
    audio=AudioFileClip(audio_path)
    total=audio.duration
    if total<11: audio=audio.fx(vfx.speedx, total/11); total=11
    if total>15: audio=audio.subclip(0,15); total=15
    clips_needed=max(8, int(total/CLIP_DENSITY)+2)
    raw_clips=get_best_free_clips_from_script(script_data, num=clips_needed)
    final_clips=[]; t=0
    for c in raw_clips:
        if t>=total: break
        dur=min(CLIP_DENSITY, total-t)
        try: final_clips.append(c.subclip(0,dur).set_start(t))
        except: final_clips.append(c.set_start(t).set_duration(dur))
        t+=dur
    base_video=CompositeVideoClip(final_clips, size=(WIDTH,HEIGHT)).set_duration(total)
    whitebar_path,_=make_74k_white_bar_FINAL(viral_hook)
    white_bar_clip=ImageClip(whitebar_path).set_duration(total).set_position((0,0))
    bottom_text_clip=make_74k_bottom_text_FINAL(viral_hook, total)
    border_clip=make_black_rounded_border_FINAL(total)
    words=script_text.split()
    caption_clips=[]; current_time=0
    first_words_count=min(5, len(words))
    base_dur=total/max(len(words),1)*0.95
    base_dur=max(0.28, min(0.38, base_dur))
    first_dur=base_dur*1.4; keyword_dur=base_dur*1.2; overlap=0.92
    for i,w in enumerate(words):
        is_first=i<first_words_count
        is_kw=any(k in w.upper() for k in ["BRUTAL","TARIFFS","PANIC","MILLIONS","SHOCKING","BREAKING","TRUMP","BIDEN","LEAKED","SECRET"]) or is_first
        dur=first_dur if is_first else (keyword_dur if is_kw else base_dur)
        if current_time>=total: break
        if current_time+dur>total: dur=max(0.15, total-current_time)
        wc=word_clip_FINAL(w.upper(), dur, is_kw, is_first)
        if wc: caption_clips.append(wc.set_start(current_time))
        current_time+=dur*overlap
    comp=CompositeVideoClip([base_video, white_bar_clip, bottom_text_clip, border_clip]+caption_clips, size=(WIDTH,HEIGHT)).set_duration(total)
    fps=random.choice(FPS_CHOICES)
    comp=comp.set_audio(audio)
    print(f"[RENDER] FPS {fps} + {len(caption_clips)} captions + REAL visuals -> {output_path}")
    comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
    return output_path
