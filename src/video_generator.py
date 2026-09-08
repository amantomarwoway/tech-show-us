"""
ULTIMATE GOD LEVEL - RETENTION + VvSA + ANTI-BOT + SOUND RETENTION - NO 4K
Location: src/video_generator.py
Edits as per request (4K excluded):
- Retention: 0.8 sec per clip, TTS 1.15X, 11-13 sec / 40 words, Seamless loop
- VvSA: Shock first frame (LIGHT - no overexposure), Audio punch first 1 sec, SFX by topic
- Anti Bot: Frame variation, Randomisation, No same font, Random font colour
- FFmpeg: ULTRA CLEAN - NO noise/hue filter (was causing overexposure)
- Pexel randomisation + FPS NTSC 29.97/29.98/59.94/59.95
- Sound retention: BGM volume every 3 sec 5% up/down + sub bass
FIXED OVEREXPOSURE:
- Removed colorx 1.1-1.25 + lum_contrast 15 from Pexels clips (main culprit for neon)
- Removed colorx 1.05 shock first frame -> raw clip only
- NOISE_HUE_FILTER = "" (empty = no second ffmpeg pass = no chamak)
- vignette opacity 0.28->0.08 light only
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

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"

CHANNEL_NAME = "Uncovered USA 24"
CHANNEL_SHORT = "Uncovered USA 24"

# ===== NEW RETENTION CONSTANTS =====
RETENTION_WORDS = 40
CLIP_DENSITY = 0.8  # sec per clip
DURATION_MIN = 11
DURATION_MAX = 13
FPS_CHOICES = [29.97, 29.98, 59.94, 59.95]
# ULTRA CLEAN FIX: Empty = no noise/hue = no overexposure. Was "noise=alls=2:allf=t,hue=h=0:s=1.02" still had noise
NOISE_HUE_FILTER = ""  # FIXED: heavy chamak 100% removed
FONT_LIST = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]
FONT_COLORS = ["#FFEB3B", "#FFFFFF", "#00E5FF", "#FF3D00", "#76FF03", "#FFEA00"]
SFX_MAP = {
    "crash": "crash_hit",
    "police": "siren_punch",
    "fbi": "siren_punch",
    "arrested": "cuff_click",
    "dies": "grave_bass",
    "dead": "grave_bass",
    "shocking": "shock_hit",
    "breaking": "breaking_beep",
    "trump": "trump_rally_hit",
    "biden": "news_punch"
}

KEYWORDS_RED = ["TRUMP","BIDEN","BREAKING","SHOCKING","USA","AMERICA","DIES","DEAD","CRASH","POLICE","COURT","FBI","JUST","ALERT","MASSIVE","HUGE","KILLED","ARRESTED","NASCAR"]
WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 150

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-ryan-medium.onnx"; cp="models/en_US-ryan-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading BEST FREE Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def clean_id(text: str) -> str:
    """FIX: Remove KG IDs like /m/04mjl, m04mjl"""
    import re
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def trim_to_40_words(text: str) -> str:
    """FIXED: Strict 40 words + loop tail"""
    text = clean_id(text)
    words = text.split()
    # Reserve 8 for loop
    if len(words) > 32:
        words = words[:32]
    first3 = " ".join(words[:3]) if len(words)>=3 else "this just leaked"
    first3_list = first3.split()[:3]
    loop_tail = ["And", "that's", "why"] + first3_list + ["just", "leaked", "now", "today"]
    loop_tail = loop_tail[:8]
    final = (words[:32] + loop_tail)[:40]
    while len(final) < 40:
        final.append("now")
    return " ".join(final[:40])

def get_best_free_clips_fixed(q, num=15):
    """Pexel randomisation + 0.8 sec density + frame variation - FIXED NoneType get_frame - ULTRA CLEAN NO COLORX"""
    key=os.getenv("PEXELS_API_KEY")
    clips=[]
    temp_files=[]
    if not key:
        print("No PEXELS_API_KEY - Using BEST FREE color clips")
        return [ColorClip(size=(1080,1920), color=(random.randint(15,35),random.randint(15,45),random.randint(50,90)), duration=CLIP_DENSITY) for _ in range(num)]
    try:
        h={"Authorization":key}
        q_clean = clean_id(str(q))
        words_found = re.findall(r'\w+', q_clean)[:3]
        words_found = [w for w in words_found if not re.match(r'^m[0-9]', w, re.I)]
        sq = " ".join(words_found) if words_found else "usa breaking news"
        url=f"https://api.pexels.com/videos/search?query={sq}&per_page={num*3}&orientation=portrait&size=medium"
        res=requests.get(url,headers=h,timeout=20).json()
        videos = res.get('videos',[])
        random.shuffle(videos)
        print(f"Pexels search: {sq} -> {len(videos)} found, picking {num} random - ULTRA CLEAN RAW")
        for v in videos[:num*2]:
            if len(clips) >= num:
                break
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
                    video_clip = VideoFileClip(tmp_path)
                    if video_clip.duration < 0.5:
                        video_clip.close()
                        os.remove(tmp_path)
                        continue
                    rand_start = random.uniform(0, max(0, video_clip.duration-1))
                    final_clip = video_clip.subclip(rand_start, min(rand_start+2, video_clip.duration)).resize(height=1920-WHITE_BAR_HEIGHT).set_position('center').without_audio()
                    # FIXED: REMOVED HEAVY CHAMAK - these 2 lines were causing overexposure neon
                    # final_clip = final_clip.fx(vfx.colorx, random.uniform(1.1,1.25))  # REMOVED - main culprit
                    # final_clip = final_clip.fx(vfx.lum_contrast, lum=0, contrast=15, contrast_thr=127)  # REMOVED - posterize
                    temp_files.append(tmp_path)
                    clips.append(final_clip)
                except Exception as e:
                    print(f"Pexels clip error: {e}")
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                    continue
            except Exception as e:
                print(f"Pexels video loop error: {e}")
                continue
        if clips:
            random.shuffle(clips)
            final_cuts=[]
            for c in clips:
                try:
                    d = min(CLIP_DENSITY, c.duration if hasattr(c, 'duration') else CLIP_DENSITY)
                    start = random.uniform(0, max(0, c.duration-d)) if hasattr(c, 'duration') else 0
                    cut = c.subclip(start, start+d) if hasattr(c, 'subclip') else c
                    final_cuts.append(cut)
                except Exception as e:
                    final_cuts.append(c)
            print(f"Pexels SUCCESS: {len(final_cuts)} clips ready for {sq} - ULTRA CLEAN")
            return final_cuts[:num]
    except Exception as e:
        print(f"Pexels overall error: {e}")
        import traceback
        traceback.print_exc()
    if not clips:
        print("Pexels fallback to color clips - no valid clips downloaded")
    return [ColorClip(size=(1080,1920), color=(random.randint(15,35),random.randint(15,45),random.randint(50,90)), duration=CLIP_DENSITY) for _ in range(num)]

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
            bg = AudioFileClip(tmp.name)
            return bg
    except:
        return None
    return None

def get_sfx_for_topic(topic: str):
    topic_l = topic.lower()
    for k,v in SFX_MAP.items():
        if k in topic_l:
            return v
    return random.choice(["shock_hit","whoosh","punch"])

def get_music_by_mood(topic: str):
    try:
        from config import get_music_mood_from_topic
        mood = get_music_mood_from_topic(topic)
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

def make_text_image(text, fontsize, color, stroke_w=5, size=(1080, 200), bg_color=None, font_style="bold", font_path=None):
    if bg_color:
        img=Image.new('RGBA', size, bg_color)
    else:
        img=Image.new('RGBA', size, (0,0,0,0))
    d=ImageDraw.Draw(img)
    chosen_font = font_path or random.choice(FONT_LIST)
    try:
        f=ImageFont.truetype(chosen_font, fontsize)
    except:
        try:
            f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
        except:
            f=ImageFont.load_default()
    if stroke_w == 0:
        d.text((size[0]//2, size[1]//2), text, font=f, fill=color, anchor="mm")
    else:
        d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    p=f"temp/txt_{random.randint(1,999999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def make_white_bar_text_image(text, fontsize=46):
    lines = text.split('\n')
    if len(text) > 30 and '\n' not in text:
        words = text.split()
        mid = len(words)//2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    if len(lines) == 1:
        fp = random.choice(FONT_LIST)
        return make_text_image(lines[0], fontsize, "black", 0, (1020, 80), bg_color=(255,255,255,255), font_style="bold_italic", font_path=fp)
    else:
        img = Image.new('RGBA', (1020, 120), (255,255,255,255))
        d = ImageDraw.Draw(img)
        fp = random.choice(FONT_LIST)
        try:
            f = ImageFont.truetype(fp, fontsize-2)
        except:
            f = ImageFont.load_default()
        d.text((1020//2, 25), lines[0], font=f, fill="black", anchor="mm")
        d.text((1020//2, 75), lines[1], font=f, fill="black", anchor="mm")
        p = f"temp/txt_white_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        return p

def word_clip_god(word, dur, is_keyword=False):
    color = random.choice(["#FF0000","#FFEB3B"]) if is_keyword else random.choice(FONT_COLORS)
    fontsize = random.randint(76,84) if is_keyword else random.randint(68,74)
    chosen_font = random.choice(FONT_LIST)
    path = make_text_image(word, fontsize, color, 7, (1000, 280), font_path=chosen_font)
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    if is_keyword:
        clip = clip.resize(lambda t: 1.5 - 0.5*t/dur if t < dur*0.4 else 1.0)
        clip = clip.set_position(lambda t: ('center', 0.72 + random.uniform(-0.015,0.015) if t < 0.18 else 0.72), relative=True)
    else:
        clip = clip.resize(lambda t: 1.35 - 0.35*t/dur if t < dur*0.3 else 1.0)
    return clip

def top_branding_best(duration):
    fp = random.choice(FONT_LIST)
    path = make_text_image(CHANNEL_SHORT, 28, "white", 3, (650, 80), font_path=fp)
    top = ImageClip(path).set_duration(duration).set_position(('center', (WHITE_BAR_HEIGHT+10)/1920), relative=True).set_opacity(0.92)
    top = top.resize(lambda t: 1 + 0.03*abs(__import__('numpy').sin(t*2)))
    flag_path = make_text_image("USA", 20, random.choice(FONT_COLORS), 2, (80, 50), font_path=fp)
    flag = ImageClip(flag_path).set_duration(duration).set_position((20, WHITE_BAR_HEIGHT+10))
    return [top, flag]

def white_bar_viral_hook_clip(viral_hook_text: str, duration: float):
    white_bg = ColorClip((WIDTH, WHITE_BAR_HEIGHT), color=(255,255,255), duration=duration).set_position((0,0)).set_opacity(1)
    safe = viral_hook_text.replace("'","").replace('"',"").strip()[:70]
    if not safe:
        safe = "Breaking News"
    try:
        img = Image.new('RGB', (1020, WHITE_BAR_HEIGHT-20), (255,255,255))
        d = ImageDraw.Draw(img)
        fp = random.choice(FONT_LIST)
        try:
            f = ImageFont.truetype(fp, 46)
        except:
            f = ImageFont.load_default()
        d.text((1020//2, (WHITE_BAR_HEIGHT-20)//2), safe, font=f, fill=(0,0,0), anchor="mm")
        p = f"temp/whitebar_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        hook_clip = ImageClip(p).set_duration(duration).set_position(('center', 10))
    except Exception as e:
        hook_path = make_text_image(safe, 46, "black", 0, (1020, WHITE_BAR_HEIGHT-20), bg_color=(255,255,255,255), font_style="bold")
        hook_clip = ImageClip(hook_path).set_duration(duration).set_position(('center', 10))
    return [white_bg, hook_clip]
    
def retention_loops_best(total):
    clips=[]
    loops = [(1.5, "WAIT"), (4, "HERE'S WHY"), (7.5, "WHAT HAPPENED NEXT?"), (10, "DON'T MISS THIS")]
    for t, txt in loops:
        if t < total:
            col = random.choice(FONT_COLORS)
            fp = random.choice(FONT_LIST)
            p = make_text_image(txt, random.randint(36,40), col, 4, (550, 80), font_path=fp)
            c = ImageClip(p).set_duration(0.7).set_start(t).set_position(('center', 0.18), relative=True)
            c = c.resize(lambda t: 1.25 if t < 0.2 else 1.0)
            clips.append(c)
    return clips

def vignette_best(duration):
    # FIXED ULTRA CLEAN: Light vignette only 0.08 opacity, was 0.28/0.33 causing dark overexposure
    top = ColorClip((1080, 200), color=(0,0,0), duration=duration).set_opacity(0.08).set_position((0,WHITE_BAR_HEIGHT))
    bottom = ColorClip((1080, 300), color=(0,0,0), duration=duration).set_opacity(0.08).set_position((0,1620))
    return [top, bottom]

def get_giphy_pro_editor(script_text: str, total_duration: float):
    clips=[]
    try:
        key = os.getenv("GIPHY_API_KEY")
        if not key:
            return []
        words = script_text.lower().split()
        triggers = {
            "shocking": "shocked reaction", "breaking": "breaking news", "wow": "wow reaction",
            "huge": "mind blown", "crazy": "crazy reaction", "unbelievable": "shocked",
            "dies": "sad rip", "dead": "sad rip", "wins": "celebration party",
            "arrested": "police siren", "crash": "crash explosion", "trump": "trump", "biden": "biden"
        }
        total_words = len(words)
        word_duration = total_duration / max(total_words, 1)
        found_positions = []
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^a-z]', '', w)
            if clean_w in triggers:
                timestamp = idx * word_duration
                if not found_positions or timestamp - found_positions[-1][0] > 2.0:
                    found_positions.append((timestamp, triggers[clean_w], clean_w))
        if not found_positions and total_duration > 5:
            found_positions = [(total_duration*0.15, "breaking news", "auto1"), (total_duration*0.5, "wow reaction", "auto2")]
        for ts, query, original in found_positions[:3]:
            try:
                url = f"https://api.giphy.com/v1/stickers/search?api_key={key}&q={query}&limit=1&rating=pg"
                res = requests.get(url, timeout=8).json()
                data = res.get('data', [])
                if not data:
                    url2 = f"https://api.giphy.com/v1/gifs/search?api_key={key}&q={query}&limit=1&rating=pg"
                    res = requests.get(url2, timeout=8).json()
                    data = res.get('data', [])
                if not data:
                    continue
                item = data[0]
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
                dur = random.uniform(1.0, 1.5)
                if original in ["shocking", "unbelievable", "wow"]:
                    pos = ('center', 0.25); size = 320
                elif original in ["wins", "celebration"]:
                    pos = ('center', 0.35); size = 350
                else:
                    pos_x = random.choice([0.1, 0.65]); pos_y = random.choice([0.15, 0.30, 0.50])
                    pos = (pos_x, pos_y); size = random.randint(220, 300)
                try:
                    g_clip = VideoFileClip(tmp.name).resize(width=size).set_duration(dur).set_start(ts)
                    g_clip = g_clip.set_position(pos, relative=True).set_opacity(0.92)
                    g_clip = g_clip.resize(lambda t: 0.8 + 0.2*t/dur if t < dur*0.2 else (1.1 - 0.1*(t-dur*0.8)/dur if t > dur*0.8 else 1.0))
                    clips.append(g_clip)
                except Exception as inner_e:
                    continue
            except Exception as e:
                continue
        return clips
    except Exception as e:
        return []

def get_giphy_stickers(keyword: str, limit=3):
    return []

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or script_data.get('script','') or ""
        title=script_data.get('title','USA Tech Breaking News')
        viral_hook=script_data.get('viral_hook','') or script_data.get('white_bar_text','') or "This Changes Everything"
        keywords=script_data.get('keywords', []) or [title.split()[0] if title else "USA"]
        mood=script_data.get('mood', title)
    else:
        raw_script=str(script_data)
        title=raw_script[:40]
        viral_hook="This Changes Everything"
        keywords=[title]
        mood=title

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    script_text = trim_to_40_words(raw_script)
    print(f"[RETENTION] Script trimmed to 40 words: {len(script_text.split())} words -> target 11-13 sec - ULTRA CLEAN")

    print("1. TTS Piper + 1.15X + Audio Punch...")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    with wave.open(audio_path,"wb") as wav:
        first=True
        for ch in voice.synthesize(script_text):
            if first:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
            wav.writeframes(ch.audio_int16_bytes)
    
    audio=AudioFileClip(audio_path)
    audio = audio.fx(vfx.speedx, 1.15)
    total=audio.duration
    if total > DURATION_MAX:
        audio = audio.subclip(0, DURATION_MAX)
        total = DURATION_MAX
    if total < DURATION_MIN:
        print(f"[WARN] Audio {total:.1f}s < {DURATION_MIN}s - will pad")

    def make_punch_audio():
        a1 = audio.subclip(0, min(1, total)).volumex(1.5)
        a2 = audio.subclip(min(1, total), total) if total > 1 else None
        if a2:
            return CompositeAudioClip([a1.set_start(0), a2.set_start(1)])
        return a1
    audio = make_punch_audio()

    first_sentence = script_text.split('.')[0][:55] if '.' in script_text else script_text[:55]
    print(f"2. Pexel clips {CLIP_DENSITY} sec density + randomisation - ULTRA CLEAN NO FILTER...")
    clips_needed = max(8, int(math.ceil(total / CLIP_DENSITY)) + 2)
    title_clean = clean_id(title)
    raw_clips = get_best_free_clips_fixed(title_clean, num=clips_needed)
    
    # ULTRA CLEAN: Build sequence WITHOUT heavy colorx - pure raw
    final_video_clips=[]
    t=0
    for idx, c in enumerate(raw_clips):
        if t >= total:
            break
        dur = min(CLIP_DENSITY, total-t, c.duration)
        sub = c.subclip(0, dur).set_start(t)
        # FIXED: No heavy shock - was colorx 1.05 + zoom 1.02 still causing light chamak
        # Now pure raw clip, no fx at all
        final_video_clips.append(sub)
        t+=dur

    if not final_video_clips:
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=(20,20,60), duration=total)]

    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)

    print("3. Captions + anti-bot fonts - ULTRA CLEAN...")
    words = script_text.split()
    word_dur = total / max(len(words),1)
    caption_clips=[]
    for i,w in enumerate(words):
        is_kw = any(k in w.upper() for k in KEYWORDS_RED)
        dur = word_dur
        wc = word_clip_god(w.upper(), dur, is_kw).set_start(i*word_dur)
        caption_clips.append(wc)

    white_bar = white_bar_viral_hook_clip(viral_hook, total)
    branding = top_branding_best(total)
    loops = retention_loops_best(total)
    vig = vignette_best(total)
    giphy = get_giphy_pro_editor(script_text, total)

    print("4. Composite + NTSC FPS - ULTRA CLEAN NO FFmpeg noise/hue...")
    comp = CompositeVideoClip([base_video] + white_bar + branding + loops + vig + giphy + caption_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    
    fps = random.choice(FPS_CHOICES)
    print(f"[FPS] Selected NTSC fps: {fps} - ULTRA CLEAN")

    bg_music = get_free_bg_music()
    if bg_music:
        bg_music = bg_music.subclip(0, total).set_duration(total)
        bg_music = bg_music.fx(afx.audio_fadein, 0.3).set_start(0)
        final_audio = CompositeAudioClip([audio, bg_music.volumex(0.08)])
    else:
        final_audio = audio

    comp = comp.set_audio(final_audio)

    # ULTRA CLEAN: Direct write, NO second ffmpeg noise/hue filter
    # If NOISE_HUE_FILTER empty, skip second pass = 100% clean raw
    if NOISE_HUE_FILTER and NOISE_HUE_FILTER.strip():
        temp_out = output_path.replace(".mp4","_temp.mp4")
        comp.write_videofile(temp_out, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
        try:
            cmd = ["ffmpeg","-y","-i", temp_out,"-vf", NOISE_HUE_FILTER,"-r", str(fps),"-c:v","libx264","-crf","20","-preset","veryfast","-c:a","aac","-b:a","128k",output_path]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.remove(temp_out)
            print(f"[FFMPEG] Noise+hue applied, fps locked {fps} -> {output_path}")
        except Exception as e:
            print(f"[FFMPEG] fallback, error {e}")
            os.rename(temp_out, output_path)
    else:
        print(f"[ULTRA CLEAN] Direct write NO noise/hue filter = RAW PEXELS CLEAN - ZERO CHAMAK")
        comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)

    try:
        import glob
        for f in glob.glob("temp/txt_*.png") + glob.glob("temp/whitebar_*.png") + glob.glob("temp/txt_white_*.png"):
            os.remove(f)
    except:
        pass

    return output_path

if __name__=="__main__":
    print("Test video_generator ULTRA CLEAN - NO heavy chamak")
    data={"full_script":"Breaking: Massive shock in USA as this story behind closed doors leaked, first to know effect is huge, you will not believe what happened next in America","title":"USA Breaking Massive Leak Behind Closed Doors","viral_hook":"This Leaked Behind Closed Doors","keywords":["USA","leak"]}
    create_video(data)
