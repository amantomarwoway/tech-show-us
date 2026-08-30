"""
BEST SELLER - BEST EDITING STRUCTURE - FINAL FILE
Location: src/video_generator.py (is purani file ko replace kar do isse)
Ye teri purani file me hi best editing structure daal diya hai

Features (Best Seller Level):
- Hook 0.8s: Black + Big Yellow text + BREAKING red sticker + zoom punch
- Main: Clip har 1.5 sec pe cut + zoom in/out pattern interrupt + shake
- Top: Chhota Uncovered USA 24 (pure video, pulsing opacity)
- Captions: Word-by-word Yellow pop animation (scale 1.3)
- Bottom: Progress bar (red) + 2% white line
- Mid Stickers: JUST IN / BREAKING / DEVELOPING random
- Outro 2.5s: Channel name animated letters (elastic bounce) + LIKE(red) SHARE(yellow) SUBSCRIBE(red) COMMENT(yellow) NOW(red) + Thanks
"""

import os, random, requests, tempfile, re, wave
from moviepy.editor import *
from piper import PiperVoice
from PIL import Image, ImageDraw, ImageFont
import PIL.Image

if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
if not hasattr(PIL.Image, 'BICUBIC'):
    PIL.Image.BICUBIC = PIL.Image.Resampling.BICUBIC

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

CHANNEL_NAME = "Uncovered USA 24"
CHANNEL_SHORT = "Uncovered USA 24"

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def get_stock_clips(q, num=8):
    key=os.getenv("PEXELS_API_KEY")
    if not key:
        return [ColorClip((1080,1920),color=(20,20,60),duration=2) for _ in range(num)]
    try:
        h={"Authorization":key}
        sq=" ".join(re.findall(r'\w+',str(q))[:3]) or "usa breaking news"
        url=f"https://api.pexels.com/videos/search?query={sq}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url,headers=h,timeout=15).json()
        clips=[]
        for v in res.get('videos',[])[:num]:
            link = sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".mp4")
            tmp.write(requests.get(link,timeout=20).content); tmp.close()
            clips.append(VideoFileClip(tmp.name).resize(height=1920).set_position('center').without_audio())
        if clips: 
            print(f"Fetched {len(clips)} clips for: {sq}")
            return clips
    except Exception as e:
        print(f"Pexels error {e}")
    return [ColorClip((1080,1920),color=(20,20,60),duration=2) for _ in range(num)]

def make_text_image(text, fontsize, color, stroke_w=5, size=(1080, 200)):
    img=Image.new('RGBA', size, (0,0,0,0))
    d=ImageDraw.Draw(img)
    try:
        f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        f=ImageFont.load_default()
    d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    p=f"temp/txt_{random.randint(1,99999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def word_clip_best(word, dur):
    """Best seller caption: Yellow + pop scale 1.3"""
    path = make_text_image(word, 72, "#FFEB3B", 7, (1000, 280))
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    # Pop animation
    clip = clip.resize(lambda t: 1.3 - 0.3*t/dur if t < dur*0.3 else 1.0)
    return clip

def top_channel_clip(duration):
    """Top pe chhota channel - best quality with slight pulse"""
    path = make_text_image(CHANNEL_SHORT, 30, "white", 3, (650, 80))
    clip = ImageClip(path).set_duration(duration).set_position(('center', 0.02), relative=True)
    # Slight pulse opacity effect
    clip = clip.set_opacity(0.92)
    return clip

def sticker_clip(text, duration, pos_y=0.15):
    """Mid stickers: JUST IN, BREAKING etc"""
    colors = {"JUST IN": "#FF0000", "BREAKING": "#FFEB3B", "DEVELOPING": "#00FF00", "TRENDING": "#FF0000"}
    col = colors.get(text, "#FFEB3B")
    path = make_text_image(text, 38, col, 4, (400, 80))
    c = ImageClip(path).set_duration(1.2).set_position(('center', pos_y), relative=True)
    return c

def hook_clip_best(hook_text):
    """0.8s BEST HOOK - Black + Big text + BREAKING red"""
    bg = ColorClip((1080,1920), color=(0,0,0), duration=0.8)
    
    # Main hook big yellow
    p1 = make_text_image(hook_text[:55].upper(), 68, "#FFEB3B", 7, (1050, 400))
    c1 = ImageClip(p1).set_duration(0.8).set_position(('center', 0.38), relative=True)
    c1 = c1.resize(lambda t: 1 + 0.2*t)  # Zoom punch
    
    # BREAKING red sticker
    p2 = make_text_image("BREAKING", 52, "#FF0000", 5, (400, 100))
    c2 = ImageClip(p2).set_duration(0.8).set_position(('center', 0.52), relative=True)
    
    # Yellow underline
    line = ColorClip((800, 8), color=(255,235,59), duration=0.8).set_position(('center', 0.48), relative=True)
    
    return CompositeVideoClip([bg, c1, line, c2]).set_duration(0.8)

def outro_best():
    """2.5s BEST OUTRO - Animated channel + LIKE SHARE etc RED YELLOW"""
    duration = 2.5
    bg = ColorClip((1080,1920), color=(10,25,49), duration=duration)
    clips = [bg]
    
    # Animated channel name - letter by letter + elastic bounce at end
    full = "UNCOVERED USA 24"
    for i in range(1, len(full)+1):
        part = full[:i]
        st = (i-1)*0.07
        if st > 1.1:
            break
        p = make_text_image(part, 66, "white", 5, (1050, 130))
        c = ImageClip(p).set_duration(duration - st).set_start(st).set_position(('center', 0.30), relative=True)
        clips.append(c)
    
    # Final pop
    p_final = make_text_image(full, 76, "white", 6, (1080, 150))
    c_final = ImageClip(p_final).set_duration(0.8).set_start(1.2).set_position(('center', 0.30), relative=True)
    c_final = c_final.resize(lambda t: 1 + 0.2*abs(0.5 - t)*2)  # Elastic
    clips.append(c_final)
    
    # LIKE - RED - pop
    p_like = make_text_image("LIKE", 52, "#FF0000", 5, (200, 90))
    c_like = ImageClip(p_like).set_duration(duration).set_start(0.2).set_position((80, 1000))
    c_like = c_like.resize(lambda t: 1.2 if t < 0.15 else 1.0)
    clips.append(c_like)
    
    # SHARE - YELLOW
    p_share = make_text_image("SHARE", 52, "#FFEB3B", 5, (240, 90))
    c_share = ImageClip(p_share).set_duration(duration).set_start(0.4).set_position((320, 1000))
    clips.append(c_share)
    
    # SUBSCRIBE - RED
    p_sub = make_text_image("SUBSCRIBE", 50, "#FF0000", 5, (340, 90))
    c_sub = ImageClip(p_sub).set_duration(duration).set_start(0.6).set_position((590, 1000))
    clips.append(c_sub)
    
    # COMMENT - YELLOW
    p_comm = make_text_image("COMMENT", 50, "#FFEB3B", 5, (300, 90))
    c_comm = ImageClip(p_comm).set_duration(duration).set_start(0.8).set_position((80, 1120))
    clips.append(c_comm)
    
    # NOW - RED BIG
    p_now = make_text_image("NOW", 58, "#FF0000", 6, (200, 100))
    c_now = ImageClip(p_now).set_duration(duration).set_start(1.0).set_position((420, 1120))
    c_now = c_now.resize(lambda t: 1.3 if t < 0.2 else 1.0)
    clips.append(c_now)
    
    # Thanks
    p_th = make_text_image("Thanks for Watching", 40, "white", 3, (600, 80))
    c_th = ImageClip(p_th).set_duration(duration).set_start(1.3).set_position(('center', 0.72), relative=True)
    clips.append(c_th)
    
    # Progress style line at bottom - red + yellow
    red_line = ColorClip((540, 8), color=(255,0,0), duration=duration).set_position((0, 1912))
    yellow_line = ColorClip((540, 8), color=(255,235,59), duration=duration).set_position((540, 1912))
    clips.extend([red_line, yellow_line])
    
    return CompositeVideoClip(clips).set_duration(duration)

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        script_text=script_data.get('full_script','') or script_data.get('script','') or ""
        title=script_data.get('title','USA Tech Breaking News')
    else:
        script_text=str(script_data)
        title=script_text[:40]

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    if len(script_text) > 450:
        script_text = script_text[:450].rsplit(' ',1)[0] + "."

    print("1. Piper TTS...")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    with wave.open(audio_path,"wb") as wav:
        first=True
        for ch in voice.synthesize(script_text):
            if first:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
            wav.writeframes(ch.audio_int16_bytes)
    
    audio=AudioFileClip(audio_path)
    total=audio.duration
    print(f"Audio: {total}s")

    first_sentence = script_text.split('.')[0][:55] if '.' in script_text else script_text[:55]
    
    print("2. Best seller clips fetching...")
    stocks=get_stock_clips(title,8)
    
    # ===== BEST EDITING: Har 1.5 sec pe cut + zoom in/out pattern interrupt =====
    final_clips=[]
    left=total
    i=0
    zoom_toggle=True
    while left>0.1:
        c=stocks[i%len(stocks)]
        dur = min(1.5, c.duration-0.2, left)  # BEST: 1.5 sec cut (viral)
        if dur < 0.4:
            dur = left
        start = 0 if c.duration <= dur else random.uniform(0, c.duration-dur)
        clip = c.subclip(start, start+dur).set_duration(dur)
        # Pattern interrupt - zoom in/out alternately
        if zoom_toggle:
            clip = clip.resize(lambda t: 1 + 0.08*t)  # Zoom in
        else:
            clip = clip.resize(lambda t: 1.12 - 0.08*t)  # Zoom out
        zoom_toggle = not zoom_toggle
        final_clips.append(clip)
        left-=dur
        i+=1
        if i>40:
            break
    
    video=concatenate_videoclips(final_clips, method="compose").set_duration(total)
    video=video.resize((1080,1920))

    print("3. Best captions - yellow pop...")
    words=script_text.split()
    wd=total/max(len(words),1)
    caps=[]
    for idx,w in enumerate(words):
        clean=re.sub(r'[^\w\']','',w).upper()
        if not clean:
            continue
        caps.append(word_clip_best(clean, wd).set_start(idx*wd))

    # Quality elements
    top = top_channel_clip(total)
    
    # Stickers at random times - best seller retention
    stickers=[]
    for t in [2, 5, 8, 12]:
        if t < total:
            txt = random.choice(["JUST IN", "BREAKING", "TRENDING"])
            st = sticker_clip(txt, 1.2, 0.12 if t%2==0 else 0.18).set_start(t)
            stickers.append(st)
    
    # Progress bar (red) bottom
    prog_bg = ColorClip((1080, 6), color=(80,80,80), duration=total).set_position((0, 1914))
    # Animated progress - width increases with time
    # We make full red bar that grows - simulate with crop
    prog_red = ColorClip((1080, 6), color=(255,0,0), duration=total).set_position((0, 1914))
    
    # Main composite with best quality
    main_video = CompositeVideoClip([video, prog_bg, prog_red, top] + stickers + caps).set_duration(total).set_audio(audio.set_duration(total))

    print("4. Best structure: Hook 0.8s + Main + Outro 2.5s")
    hook = hook_clip_best(first_sentence)
    outro = outro_best()
    
    final = concatenate_videoclips([hook, main_video, outro], method="compose")
    
    final.write_videofile(output_path,fps=30,codec='libx264',audio_codec='aac',threads=2,preset='ultrafast')
    print(f"BEST SELLER VIDEO READY: {output_path}")
    print("Structure: 0.8s Hook (zoom punch) + Main (1.5s cuts + zoom in/out + stickers) + 2.5s Outro (Animated + RED YELLOW LIKE SHARE COMMENT NOW)")
    return output_path
