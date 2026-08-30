"""
src_long/long_video_engine_v2.py - Human Body Video Builder - 16:9 Long
100% FREE SOURCES - Fixed corrupt download

Haddiya = Chapters + Timeline
Maans = B-roll + Voice + Pacing
Nase = Captions + Retention + Zoom
Khaal = Branding + Outro + Polish + Algorithm
"""

import os, random, requests, tempfile, re, wave
from moviepy.editor import *
from piper import PiperVoice
from PIL import Image, ImageDraw, ImageFont
import PIL.Image
import numpy as np

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
if not hasattr(PIL.Image, 'BICUBIC'):
    PIL.Image.BICUBIC = PIL.Image.Resampling.BICUBIC

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

CHANNEL = "Uncovered USA 24"
KEYWORDS_RED = ["TRUMP","BIDEN","BREAKING","SHOCKING","USA","AMERICA","DIES","DEAD","CRASH","POLICE","COURT","FBI","MASSIVE","HUGE","KILLED"]

def get_piper():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
    if not os.path.exists(mp):
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def get_clips_fixed(query: str, num=14):
    """FIXED - No corrupt, 16:9 landscape, 100% FREE"""
    key=os.getenv("PEXELS_API_KEY")
    if not key:
        return [ColorClip((1920,1080),color=(random.randint(10,30),random.randint(20,40),random.randint(50,90)),duration=3) for _ in range(num)]
    try:
        h={"Authorization":key}
        sq=" ".join(re.findall(r'\w+',str(query))[:3]) or "usa news"
        url=f"https://api.pexels.com/videos/search?query={sq}&per_page={num}&orientation=landscape&size=medium"
        res=requests.get(url,headers=h,timeout=20).json()
        clips=[]
        for v in res.get('videos',[])[:num]:
            try:
                link = sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
                r = requests.get(link, timeout=30, stream=True)
                if r.status_code!=200: continue
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                path = tmp.name; tmp.close()
                with open(path,'wb') as f:
                    for chunk in r.iter_content(8192):
                        if chunk: f.write(chunk)
                if os.path.getsize(path) < 50000:
                    os.remove(path); continue
                try:
                    test=VideoFileClip(path)
                    test.get_frame(0); test.close()
                    clips.append(VideoFileClip(path).resize((1920,1080)).without_audio())
                except:
                    try: os.remove(path)
                    except: pass
            except: continue
        if clips: return clips
    except Exception as e:
        print(f"Pexels long error: {e}")
    return [ColorClip((1920,1080),color=(random.randint(10,30),random.randint(20,40),random.randint(50,90)),duration=3) for _ in range(num)]

def txt_img(text, fontsize, color, stroke=4, size=(800,150), bg=None):
    if bg: img=Image.new('RGBA', size, bg)
    else: img=Image.new('RGBA', size, (0,0,0,0))
    d=ImageDraw.Draw(img)
    try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except: f=ImageFont.load_default()
    d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke, stroke_fill="black", anchor="mm")
    p=f"temp/long_{random.randint(1,999999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def build_long_video(audio_path: str, script: str, query: str, chapters: list, output_path: str):
    print("[HUMAN STRUCTURE] Building LONG video - American audience")
    audio=AudioFileClip(audio_path)
    total=audio.duration
    print(f"Full story duration: {total:.1f}s - no cut")
    
    stocks=get_clips_fixed(query, 15)
    final_clips=[]
    left=total
    i=0
    while left>0.1:
        c=stocks[i%len(stocks)]
        dur=min(random.uniform(2.5,4.0), c.duration-0.2, left)
        if dur<0.5: dur=left
        start=0 if c.duration<=dur else random.uniform(0,c.duration-dur)
        clip=c.subclip(start,start+dur).set_duration(dur)
        if i%2==0: clip=clip.resize(lambda t: 1+0.02*t)
        else: clip=clip.resize(lambda t: 1.05-0.02*t)
        final_clips.append(clip)
        left-=dur; i+=1
        if i>120: break
    video=concatenate_videoclips(final_clips, method="compose").set_duration(total).resize((1920,1080))
    
    # NASE: Captions American style - bigger, slower
    words=script.split()
    wd=total/max(len(words),1)
    caps=[]
    for idx,w in enumerate(words):
        clean=re.sub(r'[^\w\']','',w).upper()
        if not clean: continue
        is_kw=any(k in clean for k in KEYWORDS_RED)
        color="#FF0000" if is_kw else "#FFFFFF"
        fontsize=62 if is_kw else 54
        path=txt_img(clean, fontsize, color, 5, (900,120))
        clip=ImageClip(path).set_duration(wd*2.5).set_start(idx*wd).set_position(('center',0.82), relative=True)
        if is_kw: clip=clip.resize(lambda t: 1.15 if t<0.2 else 1.0)
        caps.append(clip)
        if len(caps)>300: break
    
    # Retention every 90 sec
    retention=[]
    loops=[(30,"WAIT FOR THIS"),(90,"HERE'S WHY THIS MATTERS"),(180,"WHAT HAPPENED NEXT IS SHOCKING"),(270,"DON'T MISS THE TRUTH"),(360,"THIS IS HUGE FOR AMERICA")]
    for t,txt in loops:
        if t<total:
            col="#FF0000" if "WAIT" in txt or "HUGE" in txt else "#FFEB3B"
            p=txt_img(txt, 40, col, 4, (700,80))
            c=ImageClip(p).set_duration(2.5).set_start(t).set_position(('center',0.18), relative=True)
            retention.append(c)
    
    # KHAAL + HADDIYA: Branding + Chapters
    top_path=txt_img("UNCOVERED USA 24", 32, "white", 3, (500,60))
    top=ImageClip(top_path).set_duration(total).set_position((20,20)).set_opacity(0.9)
    prog_bg=ColorClip((1920,6), color=(80,80,80), duration=total).set_position((0,1074))
    prog=ColorClip((1920,6), color=(255,0,0), duration=total).set_position((0,1074))
    
    chapter_clips=[]
    for chap in chapters[:5]:
        if "0:00" in chap or "Hook" in chap:
            p=txt_img(chap, 28, "#FFEB3B", 3, (600,50))
            c=ImageClip(p).set_duration(3).set_start(1).set_position((20,80))
            chapter_clips.append(c)
    
    main=CompositeVideoClip([video, prog_bg, prog, top] + chapter_clips + retention + caps[:80]).set_duration(total).set_audio(audio)
    
    # Intro 3 sec + Outro 5 sec
    intro_bg=ColorClip((1920,1080), color=(10,25,49), duration=3)
    intro_txt=ImageClip(txt_img("UNCOVERED USA 24", 80, "white", 6, (1000,150))).set_duration(3).set_position('center')
    intro_sub=ImageClip(txt_img("AMERICA'S BREAKING NEWS", 36, "#FFEB3B", 3, (800,80))).set_duration(3).set_position(('center',0.65), relative=True)
    intro=CompositeVideoClip([intro_bg,intro_txt,intro_sub]).set_duration(3)
    
    outro_bg=ColorClip((1920,1080), color=(10,25,49), duration=5)
    outro_clips=[outro_bg]
    items=[(0.3,"LIKE","#FF0000",(300,500)),(0.6,"SHARE","#FFEB3B",(700,500)),(0.9,"SUBSCRIBE","#FF0000",(1100,500)),(1.2,"COMMENT NOW","#FFEB3B",(500,650))]
    for st,txt,col,pos in items:
        p=txt_img(txt, 60, col, 5, (400,100))
        c=ImageClip(p).set_duration(5-st).set_start(st).set_position(pos)
        c=c.resize(lambda t: 1.3 if t<0.15 else 1.0)
        outro_clips.append(c)
    thanks=ImageClip(txt_img("Thanks for Watching - Uncovered USA 24", 38, "white", 3, (1000,80))).set_duration(5).set_start(2).set_position(('center',0.85), relative=True)
    outro_clips.append(thanks)
    outro=CompositeVideoClip(outro_clips).set_duration(5)
    
    full=concatenate_videoclips([intro, main, outro], method="compose")
    full.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac', threads=2, preset='ultrafast')
    print(f"LONG VIDEO READY (Human Body): {output_path}")
    return output_path
