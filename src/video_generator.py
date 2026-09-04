"""
ULTIMATE GOD LEVEL - FIXED - 100% FREE SOURCES - FINAL - EDITED GOOGLE TITLE + HASHTAGS + WORLD VIRAL
Location: src/video_generator.py
Edits:
- White bar height DOUBLE 180px (thumbnail pe saaf dikhegi)
- Font bold 65, 5-6 words full sentence mirror of topic
- Title Google se searchable viral
- 4 hashtag topic related Google se
- 5th hashtag world No.1 viral Google se any niche
"""

import os, random, requests, tempfile, re, wave, math, subprocess
from pathlib import Path
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

CHANNEL_NAME = "Uncovered USA 24"
CHANNEL_SHORT = "Uncovered USA 24"
KEYWORDS_RED = ["TRUMP","BIDEN","BREAKING","SHOCKING","USA","AMERICA","DIES","DEAD","CRASH","POLICE","COURT","FBI","JUST","ALERT","MASSIVE","HUGE","KILLED","ARRESTED","NASCAR"]

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 150  # CLEAN LIKE SECOND IMAGE - pure white, perfect position (was 180 grey)

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading BEST FREE Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def get_best_free_clips_fixed(q, num=8):
    key=os.getenv("PEXELS_API_KEY")
    clips=[]
    if not key:
        print("No PEXELS_API_KEY - Using BEST FREE color clips")
        return [ColorClip((1080,1920),color=(random.randint(15,35),random.randint(15,45),random.randint(50,90)),duration=2) for _ in range(num)]
    try:
        h={"Authorization":key}
        sq=" ".join(re.findall(r'\w+',str(q))[:3]) or "usa breaking news"
        url=f"https://api.pexels.com/videos/search?query={sq}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url,headers=h,timeout=20).json()
        print(f"Pexels search: {sq} -> {len(res.get('videos',[]))} found")
        for v in res.get('videos',[])[:num]:
            try:
                video_files = sorted(v['video_files'], key=lambda x: x['width'])
                link = video_files[-1]['link'] if video_files else None
                if not link:
                    continue
                r = requests.get(link, timeout=30, stream=True)
                if r.status_code != 200:
                    continue
                content_length = int(r.headers.get('content-length', 0))
                if content_length > 0 and content_length < 50000:
                    continue
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp_path = tmp_file.name
                tmp_file.close()
                with open(tmp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                size = os.path.getsize(tmp_path)
                if size < 50000:
                    os.remove(tmp_path)
                    continue
                try:
                    test_clip = VideoFileClip(tmp_path)
                    test_clip.get_frame(0)
                    test_clip.close()
                    final_clip = VideoFileClip(tmp_path).resize(height=1920-WHITE_BAR_HEIGHT).set_position('center').without_audio()
                    clips.append(final_clip)
                except Exception as e:
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                    continue
            except Exception as e:
                continue
        if clips:
            return clips
    except Exception as e:
        print(f"Pexels overall error: {e}")
    return [ColorClip((1080,1920),color=(random.randint(15,35),random.randint(15,45),random.randint(50,90)),duration=2) for _ in range(num)]

def get_free_bg_music():
    try:
        key = os.getenv("PIXABAY_API_KEY")
        if not key:
            return None
        url = f"https://pixabay.com/api/music/?key={key}&q=cinematic+tension&per_page=3"
        res = requests.get(url, timeout=10).json()
        if res.get('hits'):
            music_url = res['hits'][0].get('download')
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(requests.get(music_url, timeout=20).content); tmp.close()
            bg = AudioFileClip(tmp.name).volumex(0.06)
            return bg
    except:
        return None
    return None

def get_music_by_mood(topic: str):
    try:
        from config import get_music_mood_from_topic
        mood = get_music_mood_from_topic(topic)
        print(f"[MUSIC MOOD] Topic: {topic} -> Mood: {mood}")
        return mood
    except:
        topic_l = str(topic).lower()
        if "breaking" in topic_l or "shocking" in topic_l:
            return "tense dramatic news"
        if "dies" in topic_l or "death" in topic_l:
            return "sad piano emotional"
        if "wins" in topic_l:
            return "celebration uplifting victory"
        return "news background corporate"

def make_text_image(text, fontsize, color, stroke_w=5, size=(1080, 200), bg_color=None, font_style="bold"):
    # font_style: bold, bold_italic, regular
    if bg_color:
        img=Image.new('RGBA', size, bg_color)
    else:
        img=Image.new('RGBA', size, (0,0,0,0))
    d=ImageDraw.Draw(img)
    try:
        if font_style == "bold_italic":
            # Try bold oblique for second image like italic clean
            try:
                f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", fontsize)
            except:
                f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
        elif font_style == "bold":
            f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
        else:
            f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    except:
        f=ImageFont.load_default()
    # For pure white bar - no stroke (stroke_w=0) for clean look like second image
    if stroke_w == 0:
        d.text((size[0]//2, size[1]//2), text, font=f, fill=color, anchor="mm")
    else:
        d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    p=f"temp/txt_{random.randint(1,999999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def make_white_bar_text_image(text, fontsize=46):
    """SECOND IMAGE LIKE - pure white bar, perfect black bold italic, 2 line support, clean"""
    # Handle 2 lines like second image "As a kid, this completely\nflew over head"
    lines = text.split('\n')
    if len(text) > 30 and '\n' not in text:
        # Auto split into 2 lines for clean look like second image
        words = text.split()
        mid = len(words)//2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    
    # Create image for 1 or 2 lines
    if len(lines) == 1:
        return make_text_image(lines[0], fontsize, "black", 0, (1020, 80), bg_color=(255,255,255,255), font_style="bold_italic")
    else:
        # For 2 lines - create bigger image like second image
        img = Image.new('RGBA', (1020, 120), (255,255,255,255))
        d = ImageDraw.Draw(img)
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", fontsize-2)
        except:
            try:
                f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize-2)
            except:
                f = ImageFont.load_default()
        # Draw 2 lines centered
        d.text((1020//2, 25), lines[0], font=f, fill="black", anchor="mm")
        d.text((1020//2, 75), lines[1], font=f, fill="black", anchor="mm")
        p = f"temp/txt_white_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        return p


def word_clip_god(word, dur, is_keyword=False):
    color = "#FF0000" if is_keyword else "#FFEB3B"
    fontsize = 80 if is_keyword else 70
    path = make_text_image(word, fontsize, color, 7, (1000, 280))
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    if is_keyword:
        clip = clip.resize(lambda t: 1.5 - 0.5*t/dur if t < dur*0.4 else 1.0)
        clip = clip.set_position(lambda t: ('center', 0.72 + random.uniform(-0.015,0.015) if t < 0.18 else 0.72), relative=True)
    else:
        clip = clip.resize(lambda t: 1.35 - 0.35*t/dur if t < dur*0.3 else 1.0)
    return clip

def top_branding_best(duration):
    # FIX: Don't overlap white bar - start below white bar to keep white pure like second image
    path = make_text_image(CHANNEL_SHORT, 28, "white", 3, (650, 80))
    # Position below white bar, not at 0.02 which overlaps white and makes grey
    top = ImageClip(path).set_duration(duration).set_position(('center', (WHITE_BAR_HEIGHT+10)/1920), relative=True).set_opacity(0.92)
    top = top.resize(lambda t: 1 + 0.03*abs(np.sin(t*2)))
    flag_path = make_text_image("USA", 20, "#FFEB3B", 2, (80, 50))
    # Flag also below white bar
    flag = ImageClip(flag_path).set_duration(duration).set_position((20, WHITE_BAR_HEIGHT+10))
    return [top, flag]

# ===== FIXED: SECOND IMAGE LIKE - PURE WHITE #FFFFFF, CLEAN BOLD, NO GREY =====
def white_bar_viral_hook_clip(viral_hook_text: str, duration: float):
    """SECOND IMAGE LIKE: Pure white bar #FFFFFF, no grey, perfect black bold font"""
    # PURE SOLID WHITE - opacity 1, no transparent
    white_bg = ColorClip((WIDTH, WHITE_BAR_HEIGHT), color=(255,255,255), duration=duration).set_position((0,0)).set_opacity(1)
    
    # Clean text - if only 1 word like "Rockies", use it but make it bold black clean
    safe = viral_hook_text.replace("'","").replace('"',"").strip()[:70]
    if not safe:
        safe = "Breaking News"
    
    # For second image like clean look - use white bar text image with solid white bg
    # Font 42 bold italic, NO STROKE (stroke 0) - pure black like second image
    try:
        # Create solid white image with black text - like second image "As a kid, this completely flew over head"
        img = Image.new('RGB', (1020, WHITE_BAR_HEIGHT-20), (255,255,255))
        d = ImageDraw.Draw(img)
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        except:
            f = ImageFont.load_default()
        # Center text - pure black, no stroke
        d.text((1020//2, (WHITE_BAR_HEIGHT-20)//2), safe, font=f, fill=(0,0,0), anchor="mm")
        p = f"temp/whitebar_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        hook_clip = ImageClip(p).set_duration(duration).set_position(('center', 10))
    except Exception as e:
        # Fallback to old method but with solid white
        hook_path = make_text_image(safe, 46, "black", 0, (1020, WHITE_BAR_HEIGHT-20), bg_color=(255,255,255,255), font_style="bold")
        hook_clip = ImageClip(hook_path).set_duration(duration).set_position(('center', 10))
    
    return [white_bg, hook_clip]
    
def retention_loops_best(total):
    clips=[]
    loops = [(2, "WAIT"), (5, "HERE'S WHY"), (9, "WHAT HAPPENED NEXT?"), (14, "DON'T MISS THIS"), (19, "THIS IS HUGE")]
    for t, txt in loops:
        if t < total:
            col = "#FF0000" if "WAIT" in txt or "HUGE" in txt else "#FFEB3B"
            p = make_text_image(txt, 38, col, 4, (550, 80))
            c = ImageClip(p).set_duration(0.9).set_start(t).set_position(('center', 0.18), relative=True)
            c = c.resize(lambda t: 1.25 if t < 0.2 else 1.0)
            clips.append(c)
    return clips

def vignette_best(duration):
    # FIX: Grey hatane ke liye top vignette white bar ke neeche se start, white bar pe nahi
    top = ColorClip((1080, 200), color=(0,0,0), duration=duration).set_opacity(0.25).set_position((0,WHITE_BAR_HEIGHT))
    bottom = ColorClip((1080, 300), color=(0,0,0), duration=duration).set_opacity(0.3).set_position((0,1620))
    return [top, bottom]

def get_giphy_pro_editor(script_text: str, total_duration: float):
    """
    PRO EDITOR GIPHY - Bot khud decide karega kaha lagana hai, ffmpeg style
    Jaise pro editor lagata hai - emotion, keyword, timing ke hisaab se
    """
    clips=[]
    try:
        key = os.getenv("GIPHY_API_KEY")
        if not key:
            print("[GIPHY PRO] No API key - skip")
            return []
        
        # Script se keywords nikalo jaha giphy lagna chahiye
        words = script_text.lower().split()
        # Emotional triggers jaha pro editor giphy lagata hai
        triggers = {
            "shocking": "shocked reaction",
            "breaking": "breaking news",
            "wow": "wow reaction",
            "huge": "mind blown",
            "crazy": "crazy reaction",
            "unbelievable": "shocked",
            "dies": "sad rip",
            "dead": "sad rip",
            "wins": "celebration party",
            "arrested": "police siren",
            "crash": "crash explosion",
            "trump": "trump",
            "biden": "biden"
        }
        
        # Bot decides positions based on script timing - ffmpeg pro style
        total_words = len(words)
        word_duration = total_duration / max(total_words, 1)
        
        found_positions = []
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^a-z]', '', w)
            if clean_w in triggers:
                timestamp = idx * word_duration
                # Avoid overlapping - min 2 sec gap
                if not found_positions or timestamp - found_positions[-1][0] > 2.0:
                    found_positions.append((timestamp, triggers[clean_w], clean_w))
        
        # If no triggers, use 2-3 emotional points automatically (pro editor auto adds)
        if not found_positions and total_duration > 5:
            found_positions = [
                (total_duration*0.15, "breaking news", "auto1"),
                (total_duration*0.5, "wow reaction", "auto2"),
                (total_duration*0.8, "subscribe", "auto3")
            ]
        
        print(f"[GIPHY PRO] Bot decided {len(found_positions)} positions: {found_positions}")
        
        for ts, query, original in found_positions[:4]:  # Max 4 - pro editor doesn't spam
            try:
                # Search giphy with transparent stickers
                url = f"https://api.giphy.com/v1/stickers/search?api_key={key}&q={query}&limit=1&rating=pg"
                res = requests.get(url, timeout=8).json()
                data = res.get('data', [])
                if not data:
                    # Fallback to gifs
                    url2 = f"https://api.giphy.com/v1/gifs/search?api_key={key}&q={query}&limit=1&rating=pg"
                    res = requests.get(url2, timeout=8).json()
                    data = res.get('data', [])
                if not data:
                    continue
                item = data[0]
                # Try to get transparent gif
                images = item.get('images', {})
                gif_url = None
                for pref in ['original', 'downsized_large', 'fixed_height']:
                    if pref in images and 'url' in images[pref]:
                        gif_url = images[pref]['url']
                        break
                if not gif_url:
                    continue
                
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".gif")
                g_data = requests.get(gif_url, timeout=12).content
                if len(g_data) < 5000:
                    continue
                tmp.write(g_data); tmp.close()
                
                # PRO EDITOR FFMPEG STYLE: Resize, position based on context, fade, bounce
                # Duration 1.2-1.8 sec only (pro doesn't keep long)
                dur = random.uniform(1.2, 1.8)
                # Position logic: shocking top, celebration center, breaking top-right
                if original in ["shocking", "unbelievable", "wow"]:
                    pos = ('center', 0.25)
                    size = 320
                elif original in ["wins", "celebration"]:
                    pos = ('center', 0.35)
                    size = 350
                elif original in ["dies", "dead"]:
                    pos = (0.65, 0.4)
                    size = 280
                else:
                    # Random pro positions - not overlapping captions (0.72)
                    pos_x = random.choice([0.1, 0.65])
                    pos_y = random.choice([0.15, 0.30, 0.50])
                    pos = (pos_x, pos_y) if isinstance(pos_x, float) else (pos_x, pos_y)
                    size = random.randint(220, 300)
                
                try:
                    g_clip = VideoFileClip(tmp.name).resize(width=size).set_duration(dur).set_start(ts)
                    # FFMPEG style effects: fade in/out + slight pop
                    g_clip = g_clip.set_position(pos, relative=True).set_opacity(0.92)
                    # Pop animation like pro editor
                    g_clip = g_clip.resize(lambda t: 0.8 + 0.2*t/dur if t < dur*0.2 else (1.1 - 0.1*(t-dur*0.8)/dur if t > dur*0.8 else 1.0))
                    clips.append(g_clip)
                    print(f"[GIPHY PRO] Added '{query}' at {ts:.1f}s pos {pos}")
                except Exception as inner_e:
                    print(f"[GIPHY PRO] Clip fail {inner_e}")
                    continue
            except Exception as e:
                print(f"[GIPHY PRO] Search fail {query}: {e}")
                continue
        
        print(f"[GIPHY PRO] Total {len(clips)} pro stickers added via ffmpeg logic")
        return clips
    except Exception as e:
        print(f"[GIPHY PRO] Error: {e}")
        return []

# Backward compat
def get_giphy_stickers(keyword: str, limit=3):
    # Old call redirects to pro with dummy timing - but we use pro editor now
    return []

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        script_text=script_data.get('full_script','') or script_data.get('script','') or ""
        title=script_data.get('title','USA Tech Breaking News')
        viral_hook=script_data.get('viral_hook','') or script_data.get('white_bar_text','') or "This Changes Everything"
        keywords=script_data.get('keywords', []) or [title.split()[0] if title else "USA"]
        mood=script_data.get('mood', title)
    else:
        script_text=str(script_data)
        title=script_text[:40]
        viral_hook="This Changes Everything"
        keywords=[title]
        mood=title

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    # SOUND CUT FIX: No truncation - full script sound (was 450 char cut)
    # script_text kept full for proper audio

    print("1. BEST FREE TTS: Piper...")
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
    first_sentence = script_text.split('.')[0][:55] if '.' in script_text else script_text[:55]
    
    music_mood = get_music_by_mood(mood if mood else title)
    print(f"Music mood decided: {music_mood}")
    
    print("2. BEST FREE Clips FIXED...")
    stocks=get_best_free_clips_fixed(title,8)
    final_clips=[]
    left=total
    i=0
    zoom=True
    while left>0.1:
        c=stocks[i%len(stocks)]
        dur = min(1.5, c.duration-0.2, left)
        if dur < 0.4: dur = left
        start = 0 if c.duration <= dur else random.uniform(0, c.duration-dur)
        clip = c.subclip(start, start+dur).set_duration(dur)
        if zoom:
            clip = clip.resize(lambda t: 1 + 0.08*t).rotate(lambda t: 0.25*t)
        else:
            clip = clip.resize(lambda t: 1.12 - 0.08*t).rotate(lambda t: -0.25*t)
        zoom = not zoom
        if i>0:
            flash = ColorClip((1080,1920), color=(255,255,255), duration=0.06).set_opacity(0.4)
            clip = CompositeVideoClip([clip, flash.set_start(dur-0.06)]).set_duration(dur)
        final_clips.append(clip)
        left-=dur
        i+=1
        if i>40: break
    
    # SECOND BOX EXACT SIZE FIX: height = 1920 - WHITE_BAR_HEIGHT (1740) - jitna box banaya utna hi
    VIDEO_HEIGHT = 1920 - WHITE_BAR_HEIGHT
    video=concatenate_videoclips(final_clips, method="compose").set_duration(total).resize((1080, VIDEO_HEIGHT))

    print("3. GOD LEVEL Captions + WHITE BAR DOUBLE 180 BOLD 5-6 WORDS...")
    words=script_text.split()
    wd=total/max(len(words),1)
    caps=[]
    for idx,w in enumerate(words):
        clean=re.sub(r'[^\w\']','',w).upper()
        if not clean: continue
        is_kw = any(k in clean for k in KEYWORDS_RED)
        caps.append(word_clip_god(clean, wd, is_kw).set_start(idx*wd))

    top_elems = top_branding_best(total)
    retention = retention_loops_best(total)
    vignette = vignette_best(total)
    
    # EDITED WHITE BAR - DOUBLE HEIGHT 180 + BOLD 65 + 5-6 WORDS MIRROR
    white_bar_clips = white_bar_viral_hook_clip(viral_hook, total)
    # Video ko neeche shift - 180px ke liye (thumbnail pe saaf dikhega)
    video_shifted = video.set_position((0, WHITE_BAR_HEIGHT))
    
    prog_bg = ColorClip((1080, 8), color=(80,80,80), duration=total).set_position((0,1912))
    prog_red = ColorClip((1080, 8), color=(255,0,0), duration=total).set_position((0,1912))
    line_2p = ColorClip((1080, 4), color=(255,255,255), duration=total).set_opacity(0.02).set_position((0,1908))
    
    bg_music = get_free_bg_music()
    if bg_music:
        bg_loop = bg_music.loop(duration=total).volumex(0.06)
        final_audio = CompositeAudioClip([audio, bg_loop]).set_duration(total)
    else:
        final_audio = audio.set_duration(total)
    
    # GIPHY PRO EDITOR - Bot decides where to place via ffmpeg logic, not 2 fixed
    try:
        giphy_clips = get_giphy_pro_editor(script_text, total)
    except Exception as ge:
        print(f"[GIPHY PRO] Failed: {ge}")
        giphy_clips = []
    # FIX: White bar sabse upar (last layer) - pure white rahega, vignette/branding usko grey nahi karega - second image jaisa
    main_video = CompositeVideoClip([video_shifted] + vignette + [prog_bg, prog_red, line_2p] + top_elems + retention + caps + giphy_clips + white_bar_clips).set_duration(total).set_audio(final_audio)

    final.write_videofile(output_path,fps=30,codec='libx264',audio_codec='aac',threads=2,preset='ultrafast')
    print(f"READY WHITE BAR DOUBLE {WHITE_BAR_HEIGHT}px BOLD 65 5-6 WORDS MIRROR={viral_hook}: {output_path}")
    return output_path
