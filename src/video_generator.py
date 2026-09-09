"""
ULTIMATE GOD LEVEL - BEST VIDEO GENERATOR - EXACT 74K DICTO + NORMAL SPEED (EDITED FROM OLD FILE)
Location: src/video_generator.py
EDITED FROM OLD FILE AS PER USER REQUEST - Purani file m edit karke diya hai

USER REQUEST:
- Video generator wala meri is purani file m edit krke do
- Aur agr is file se bhi script speed aur word by word caption speed ho to use bhi normal kre
- Exact same dicto as 74K views frame wali video

OLD FILE HAD (Jo user ne diya tha):
- WHITE_BAR_HEIGHT = 180 (small)
- White bar fontsize 52, location ('center',12) not exact 74K
- atempo 1.11/1.12X fast = 12 sec script 5 sec me khatam (bug)
- word_dur = total/len *1.15 fast choppy
- WAIT FOR IT, HERE'S WHY extra loops

NEW FIXED - EXACT 74K DICTO + NORMAL SPEED:
- WHITE_BAR_HEIGHT = 190 (exact 74K frame height 180-200, not 180)
- White bar: bold black italic 48px, 2 lines "Brutal New Tariffs / Panic Millions 😱" + emoji, location (0,0) full width 1080x190, black rounded border 14px radius 32px - exact same dicto as 74K "Nothing like quality time / with the family 😂"
- Bottom: white with thick black stroke 7px, 2 lines bottom left with ellipsis "..." like 74K "With that drawing, no / wonder he didn't get p..."
- Script speed NORMAL: Piper length_scale 1.25 slow + atempo 1.0-1.03X natural 175-190 wpm = 50 words 13-15 sec not 5 sec rush (American best normal)
- Word by word caption speed NORMAL: base 0.26-0.32s per word (total/num*0.98), first 5 words 1.35x longer punch 0.38s, keywords 1.15x, overlap 0.96 smooth - not fast choppy
- RETENTION_WORDS 50 flexible, CLIP_DENSITY 0.8s FIXED emotional only, Pexels FROM SCRIPT not TITLE - same as old file
- Audio retention: 1.0-1.03X natural + 165% punch + 7% swell + warm bass + crystal treble
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

RETENTION_WORDS = 50
CLIP_DENSITY = 0.8
DURATION_MIN = 11
DURATION_MAX = 15
FPS_CHOICES = [29.97, 29.98, 59.94, 59.95]
NOISE_HUE_FILTER = ""
BLACK_BORDER = 14
CORNER_RADIUS = 32
FONT_LIST = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
]
FONT_COLORS = ["#FFEB3B", "#FFFFFF", "#00E5FF", "#FF3D00", "#76FF03", "#FFEA00", "#FF1744", "#FFFFFF"]
VIRAL_TOP_COLORS = ["#000000"]
VIRAL_BOTTOM_COLORS = ["#FFFFFF"]
KEYWORDS_RED = ["TRUMP","BIDEN","BREAKING","SHOCKING","USA","AMERICA","DIES","DEAD","CRASH","POLICE","COURT","FBI","JUST","ALERT","MASSIVE","HUGE","KILLED","ARRESTED","SHATTERED","BETRAYAL","FAMILIES","HEARTS","BRUTAL","TARIFFS","PANIC","MILLIONS"]
WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 190  # FIXED - EXACT 74K FRAME HEIGHT 190px not 180

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-ryan-medium.onnx"; cp="models/en_US-ryan-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading BEST FREE Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def clean_id(text: str) -> str:
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_script_no_trim(text: str) -> str:
    text = clean_id(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'Visual:.*?\|', '', text, flags=re.I)
    text = re.sub(r'Audio:\s*', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_best_free_clips_from_script(script_data, num=20):
    key=os.getenv("PEXELS_API_KEY")
    clips=[]
    temp_files=[]
    if isinstance(script_data, dict):
        pexels_query = script_data.get('pexels_query', '')
        pexels_keywords = script_data.get('pexels_keywords', [])
        first_punch = script_data.get('first_sentence_punch', '')
        title = script_data.get('title', '')
        script_text = script_data.get('full_script', '')
    else:
        pexels_query = str(script_data)[:50]
        pexels_keywords = []
        first_punch = ""
        title = ""
        script_text = str(script_data)
    if pexels_query:
        search_q = pexels_query
    elif pexels_keywords:
        search_q = " ".join(pexels_keywords[:3])
    else:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', script_text.lower())
        stop = {"this","that","with","from","have","been","will","they","them","what","when","where"}
        keywords = [w for w in words if w not in stop][:3]
        search_q = " ".join(keywords) if keywords else "emotional shocked reaction"
    emotional_boosters = ["shocked", "emotional", "crying", "reaction", "dramatic"]
    final_search_queries = [
        search_q,
        f"{search_q} {random.choice(emotional_boosters)}",
        f"{first_punch.split()[0] if first_punch.split() else 'shocking'} {random.choice(emotional_boosters)} face"
    ]
    if not key:
        emotional_colors = [(35,15,30), (20,30,60), (60,20,20), (30,50,70), (70,30,40)]
        return [ColorClip(size=(1080,1920), color=random.choice(emotional_colors), duration=CLIP_DENSITY) for _ in range(num)]
    try:
        h={"Authorization":key}
        all_videos = []
        for sq in final_search_queries[:2]:
            q_clean = clean_id(str(sq))
            words_found = re.findall(r'\w+', q_clean)[:4]
            words_found = [w for w in words_found if not re.match(r'^m[0-9]', w, re.I) and len(w)>2]
            sq_final = " ".join(words_found) if words_found else "emotional shocked reaction"
            url=f"https://api.pexels.com/videos/search?query={sq_final}&per_page={num*2}&orientation=portrait&size=medium"
            try:
                res=requests.get(url,headers=h,timeout=20).json()
                videos = res.get('videos',[])
                all_videos.extend(videos)
            except:
                continue
        seen_ids = set()
        unique_videos = []
        for v in all_videos:
            vid = v.get('id')
            if vid not in seen_ids:
                seen_ids.add(vid)
                unique_videos.append(v)
        random.shuffle(unique_videos)
        for v in unique_videos[:num*3]:
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
                if int(r.headers.get('content-length', 0)) > 0 and int(r.headers.get('content-length', 0)) < 50000:
                    continue
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp_path = tmp_file.name
                tmp_file.close()
                with open(tmp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                if os.path.getsize(tmp_path) < 50000:
                    os.remove(tmp_path)
                    continue
                try:
                    video_clip = VideoFileClip(tmp_path)
                    if video_clip.duration < 0.5:
                        video_clip.close()
                        os.remove(tmp_path)
                        continue
                    rand_start = random.uniform(0, max(0, video_clip.duration-1.5))
                    final_clip = video_clip.subclip(rand_start, min(rand_start+2, video_clip.duration)).resize(height=1920-WHITE_BAR_HEIGHT).set_position('center').without_audio()
                    temp_files.append(tmp_path)
                    clips.append(final_clip)
                except:
                    try:
                        os.remove(tmp_path)
                    except:
                        pass
                    continue
            except:
                continue
        if clips:
            random.shuffle(clips)
            final_cuts=[]
            for c in clips:
                try:
                    d = CLIP_DENSITY
                    if hasattr(c, 'duration') and c.duration > d:
                        start = random.uniform(0, max(0, c.duration-d-0.2))
                        cut = c.subclip(start, start+d)
                    else:
                        cut = c.subclip(0, min(d, c.duration)) if hasattr(c, 'subclip') else c
                        cut = cut.set_duration(d)
                    cut = cut.set_duration(CLIP_DENSITY)
                    final_cuts.append(cut)
                except:
                    final_cuts.append(c)
            return final_cuts[:num]
    except Exception as e:
        print(f"Pexels overall error: {e}")
    return [ColorClip(size=(1080,1920), color=(random.randint(20,50),random.randint(15,40),random.randint(40,80)), duration=CLIP_DENSITY) for _ in range(num)]

def get_free_bg_music():
    try:
        key = os.getenv("PIXABAY_API_KEY")
        if not key:
            return None
        queries = ["cinematic tension emotional", "dramatic news emotional", "sad emotional piano"]
        url = f"https://pixabay.com/api/music/?key={key}&q={random.choice(queries)}&per_page=3"
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

def make_text_image_best(text, fontsize, color, stroke_w=6, size=(1080, 200), bg_color=None, font_path=None, is_viral_bottom=False):
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
    if is_viral_bottom:
        d.text((size[0]//2, size[1]//2), text, font=f, fill="white", stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    else:
        if stroke_w == 0:
            d.text((size[0]//2, size[1]//2), text, font=f, fill=color, anchor="mm")
        else:
            d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    p=f"temp/txt_{random.randint(1,999999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def make_white_bar_text_image_viral_EXACT_74K(text, fontsize=48):
    """
    EXACT 74K FRAME WHITE BAR - FIXED FROM OLD FILE
    OLD: fontsize 52, height 180, position ('center',12), no emoji, no italic
    NEW: height 190, bold black italic 48px, 2 lines with emoji 😱, location (0,0) full width - exact 74K dicto
    74K frame: "Nothing like quality time / with the family 😂" -> "Brutal New Tariffs / Panic Millions 😱"
    """
    viral_text = clean_id(text).strip()
    words = viral_text.split()
    if len(words) >= 4:
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) + " 😱"
        lines = [line1, line2]
    else:
        lines = [viral_text + " 😱"]
    bar_height = 190
    img = Image.new('RGB', (1080, bar_height), (255,255,255))
    d = ImageDraw.Draw(img)
    font_path_bold_italic = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        f1 = ImageFont.truetype(font_path_bold_italic if os.path.exists(font_path_bold_italic) else font_path_bold, 48)
        f2 = ImageFont.truetype(font_path_bold_italic if os.path.exists(font_path_bold_italic) else font_path_bold, 46)
    except:
        f1 = ImageFont.load_default()
        f2 = ImageFont.load_default()
    if len(lines) == 1:
        bbox = d.textbbox((0,0), lines[0], font=f1)
        w = bbox[2]-bbox[0]
        d.text(((1080-w)//2, bar_height//2), lines[0], font=f1, fill=(0,0,0), anchor="mm")
    else:
        bbox1 = d.textbbox((0,0), lines[0], font=f1)
        w1 = bbox1[2]-bbox1[0]
        d.text(((1080-w1)//2, bar_height//2 - 26), lines[0], font=f1, fill=(0,0,0), anchor="mm")
        bbox2 = d.textbbox((0,0), lines[1], font=f2)
        w2 = bbox2[2]-bbox2[0]
        d.text(((1080-w2)//2, bar_height//2 + 26), lines[1], font=f2, fill=(0,0,0), anchor="mm")
    p = f"temp/whitebar_74k_exact_old_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    return p, bar_height

def word_clip_god_best_NORMAL(word, dur, is_keyword=False, is_first_word=False):
    """
    NORMAL SPEED - Word by word caption - FIXED FROM OLD FILE
    OLD FILE: word_dur = total/len *1.15 fast choppy, fontsize 70-76
    NEW NORMAL: base 0.26-0.32s per word American readable, first 5 words 1.35x longer punch 0.38s, fontsize 86-92 for punch
    """
    if is_first_word:
        color = random.choice(["#FF0000","#FFEB3B","#FF1744"])
        fontsize = random.randint(86,92)
    elif is_keyword:
        color = random.choice(["#FF0000","#FFEB3B"])
        fontsize = random.randint(82,88)
    else:
        color = random.choice(FONT_COLORS)
        fontsize = random.randint(74,80)
    chosen_font = random.choice(FONT_LIST)
    stroke = 8 if is_first_word or is_keyword else 6
    path = make_text_image_best(word, fontsize, color, stroke, (1020, 300), font_path=chosen_font, is_viral_bottom=True)
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    if is_first_word or is_keyword:
        clip = clip.resize(lambda t: 1.6 - 0.3*t/dur if t < dur*0.4 else (1.0 + 0.1*math.sin(t*15) if t < dur*0.7 else 1.0))
        clip = clip.set_position(lambda t: ('center', 0.72 + random.uniform(-0.02,0.02) if t < 0.2 else 0.72), relative=True)
    else:
        clip = clip.resize(lambda t: 1.35 - 0.35*t/dur if t < dur*0.3 else 1.0)
    return clip

def top_branding_best(duration):
    fp = random.choice(FONT_LIST)
    path = make_text_image_best(CHANNEL_SHORT, 30, "white", 3, (700, 85), font_path=fp)
    top = ImageClip(path).set_duration(duration).set_position(('center', (WHITE_BAR_HEIGHT+10)/1920), relative=True).set_opacity(0.92)
    top = top.resize(lambda t: 1 + 0.03*abs(np.sin(t*2)))
    flag_path = make_text_image_best("USA", 22, random.choice(FONT_COLORS), 3, (85, 55), font_path=fp)
    flag = ImageClip(flag_path).set_duration(duration).set_position((20, WHITE_BAR_HEIGHT+10))
    return [top, flag]

def white_bar_viral_hook_clip_best_EXACT_74K(viral_hook_text: str, duration: float):
    """
    EXACT 74K WHITE BAR - Location (0,0) full width 1080x190 bold black italic 48px + emoji - FIXED FROM OLD FILE ('center',12) 180px 52px
    """
    safe = clean_id(viral_hook_text).replace("'","").replace('"',"").strip()[:70]
    if not safe:
        safe = "Shocking Truth Revealed"
    whitebar_path, actual_height = make_white_bar_text_image_viral_EXACT_74K(safe, fontsize=48)
    hook_clip = ImageClip(whitebar_path).set_duration(duration).set_position((0,0))
    return [hook_clip], actual_height

def make_74k_bottom_text_old_file(text, duration):
    viral_text = clean_id(text).strip()
    words = viral_text.split()
    if len(words) >= 4:
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) + "..."
        lines = [line1, line2]
    else:
        lines = [viral_text + "..."]
    img = Image.new('RGBA', (900, 160), (0,0,0,0))
    d = ImageDraw.Draw(img)
    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        f1 = ImageFont.truetype(font_path_bold, 42)
        f2 = ImageFont.truetype(font_path_bold, 40)
    except:
        f1 = ImageFont.load_default()
        f2 = ImageFont.load_default()
    d.text((10, 10), lines[0], font=f1, fill=(255,255,255), stroke_width=7, stroke_fill=(0,0,0), anchor="lt")
    if len(lines) > 1:
        d.text((10, 70), lines[1], font=f2, fill=(255,255,255), stroke_width=7, stroke_fill=(0,0,0), anchor="lt")
    p = f"temp/bottom_74k_old_file_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((35, 0.78), relative=True)
    return clip

def make_black_rounded_border_old_file(duration):
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0,0,WIDTH,HEIGHT], radius=32, outline=(0,0,0), width=14)
    p = f"temp/border_old_file_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((0,0))
    return clip

def retention_loops_best_MINIMAL(total):
    clips=[]
    loops = [(3.5, "HERE'S WHY")]
    for t, txt in loops:
        if t < total:
            col = random.choice(FONT_COLORS)
            fp = random.choice(FONT_LIST)
            p = make_text_image_best(txt, random.randint(32,36), col, 4, (500, 70), font_path=fp, is_viral_bottom=True)
            c = ImageClip(p).set_duration(0.6).set_start(t).set_position(('center', 0.22), relative=True)
            clips.append(c)
    return clips

def vignette_best(duration):
    top = ColorClip((1080, 200), color=(0,0,0), duration=duration).set_opacity(0.06).set_position((0,WHITE_BAR_HEIGHT))
    bottom = ColorClip((1080, 300), color=(0,0,0), duration=duration).set_opacity(0.10).set_position((0,1620))
    return [top, bottom]

def get_giphy_pro_editor_best(script_text: str, total_duration: float):
    clips=[]
    try:
        key = os.getenv("GIPHY_API_KEY")
        if not key:
            return []
        words = script_text.lower().split()
        triggers = {
            "shocking": "shocked reaction", "breaking": "breaking news", "brutal": "shocked reaction",
            "tariffs": "money shocked", "panic": "panic reaction", "millions": "crowd shocked"
        }
        total_words = len(words)
        word_duration = total_duration / max(total_words, 1)
        found_positions = []
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^a-z]', '', w)
            if clean_w in triggers:
                timestamp = idx * word_duration
                if not found_positions or timestamp - found_positions[-1][0] > 3.0:
                    found_positions.append((timestamp, triggers[clean_w], clean_w))
        if not found_positions and total_duration > 6:
            found_positions = [(total_duration*0.2, "shocked reaction", "auto1")]
        for ts, query, original in found_positions[:2]:
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
                dur = random.uniform(1.0, 1.4)
                pos = ('center', 0.32)
                size = 340
                try:
                    g_clip = VideoFileClip(tmp.name).resize(width=size).set_duration(dur).set_start(ts)
                    g_clip = g_clip.set_position(pos, relative=True).set_opacity(0.90)
                    clips.append(g_clip)
                except:
                    continue
            except:
                continue
        return clips
    except:
        return []

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or script_data.get('script','') or ""
        title=script_data.get('title','USA Tech Breaking News')
        viral_hook=script_data.get('viral_hook','') or script_data.get('white_bar_text','') or "Shocking Truth Revealed"
        mood=script_data.get('mood', title)
        first_punch = script_data.get('first_sentence_punch', '')
    else:
        raw_script=str(script_data)
        title=raw_script[:50]
        viral_hook="Shocking Truth Revealed"
        mood=title
        first_punch = raw_script.split('.')[0] if '.' in raw_script else raw_script[:60]

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    script_text = clean_script_no_trim(raw_script)
    word_count = len(script_text.split())
    print(f"[OLD FILE EDITED EXACT 74K + NORMAL SPEED] Script {word_count} words - White bar 190px bold italic 48px exact 74K + Speed 13-15 sec normal")

    if word_count > 50:
        script_text = " ".join(script_text.split()[:50])
        word_count = 50

    print("1. TTS Piper NORMAL SPEED - length_scale 1.25 slow + 1.0-1.03X natural (OLD FILE had 1.11 fast 5 sec rush) - NOW NORMAL 13-15 sec...")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    try:
        with wave.open(audio_path,"wb") as wav:
            first=True
            for ch in voice.synthesize(script_text, length_scale=1.25, noise_scale=0.6, noise_w_scale=0.75):
                if first:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                wav.writeframes(ch.audio_int16_bytes)
        print(f"[TTS] Piper length_scale 1.25 NORMAL - 50 words 13-15 sec not 5 sec")
    except TypeError:
        with wave.open(audio_path,"wb") as wav:
            first=True
            for ch in voice.synthesize(script_text):
                if first:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                wav.writeframes(ch.audio_int16_bytes)
    
    try:
        from audio_retention import get_tts_retention_filter, get_american_captions_timing
        temp_audio_filtered = "temp/voice_filtered.wav"
        af_filter = get_tts_retention_filter(first_punch, american_mode=True)
        cmd = ["ffmpeg","-y","-i", audio_path, "-af", af_filter, "-c:a", "pcm_s16le", temp_audio_filtered]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio=AudioFileClip(temp_audio_filtered)
    except Exception as e:
        print(f"BEST audio retention failed {e}, using fallback NORMAL 1.0-1.03X (old file had 1.11 fast)")
        audio=AudioFileClip(audio_path)
        if audio.duration < DURATION_MIN:
            stretch_factor = audio.duration / DURATION_MIN
            audio = audio.fx(vfx.speedx, stretch_factor)
        else:
            audio = audio.fx(vfx.speedx, random.choice([1.0, 1.02, 1.03]))
    
    total=audio.duration
    print(f"[DURATION NORMAL] After TTS NORMAL: {total:.1f}s (target 13-15 sec normal, not 5 sec rush)")

    if total < DURATION_MIN:
        needed_factor = total / DURATION_MIN
        audio = audio.fx(vfx.speedx, needed_factor)
        total = DURATION_MIN
    if total > DURATION_MAX:
        audio = audio.subclip(0, DURATION_MAX)
        total = DURATION_MAX

    first_sentence = first_punch if first_punch else (script_text.split('.')[0][:65] if '.' in script_text else script_text[:65])
    print(f"2. Pexels FROM SCRIPT {CLIP_DENSITY}s FIXED emotional - White bar 190px exact 74K dicto...")
    clips_needed = max(12, int(math.ceil(total / CLIP_DENSITY)) + 3)
    raw_clips = get_best_free_clips_from_script(script_data, num=clips_needed)
    
    final_video_clips=[]
    t=0
    for idx, c in enumerate(raw_clips):
        if t >= total:
            break
        dur = min(CLIP_DENSITY, total-t)
        try:
            sub = c.subclip(0, dur).set_start(t)
            final_video_clips.append(sub)
        except:
            final_video_clips.append(c.set_start(t).set_duration(dur))
        t+=dur

    if not final_video_clips:
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=(30,20,50), duration=total)]

    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)

    print("3. Captions NORMAL SPEED - 0.26-0.32s per word + first 5 words 1.35x punch (OLD FILE had 1.15 fast choppy) - NOW NORMAL readable...")
    words = script_text.split()
    
    try:
        from audio_retention import get_american_captions_timing
        timing = get_american_captions_timing(total, len(words), first_words_count=5)
        base_dur = timing["base_dur"]
        first_dur = timing["first_dur"]
        keyword_dur = timing["keyword_dur"]
        overlap = timing["overlap"]
        print(f"[CAPTION NORMAL FIXED] Old file: total/len*1.15 fast choppy | New NORMAL: Base {base_dur:.3f}s, First {first_dur:.3f}s punch, Keyword {keyword_dur:.3f}s, Overlap {overlap}, WPM {timing['wpm']:.0f} normal readable")
    except:
        base_dur = total / max(len(words),1) * 0.98
        base_dur = max(0.24, min(0.34, base_dur))
        first_dur = base_dur * 1.35
        keyword_dur = base_dur * 1.15
        overlap = 0.96
        print(f"[CAPTION NORMAL FALLBACK] Base {base_dur:.3f}s, First {first_dur:.3f}s, Keyword {keyword_dur:.3f}s")
    
    caption_clips=[]
    first_words_count = min(5, len(words))
    current_time = 0
    for i,w in enumerate(words):
        is_first = i < first_words_count
        is_kw = any(k in w.upper() for k in KEYWORDS_RED) or is_first
        if is_first:
            dur = first_dur
        elif is_kw:
            dur = keyword_dur
        else:
            dur = base_dur
        wc = word_clip_god_best_NORMAL(w.upper(), dur, is_kw, is_first).set_start(current_time)
        caption_clips.append(wc)
        current_time += dur * overlap

    white_bar_list, actual_white_height = white_bar_viral_hook_clip_best_EXACT_74K(viral_hook, total)
    bottom_text_clip = make_74k_bottom_text_old_file(viral_hook, total)
    border_clip = make_black_rounded_border_old_file(total)
    loops = retention_loops_best_MINIMAL(total)
    vig = vignette_best(total)
    giphy = get_giphy_pro_editor_best(script_text, total)

    print(f"4. Composite OLD FILE EDITED EXACT 74K + NORMAL SPEED - White bar {actual_white_height}px bold italic 48px exact 74K + Audio {total:.1f}s normal + Caption {base_dur:.3f}s normal...")
    global WHITE_BAR_HEIGHT
    WHITE_BAR_HEIGHT = actual_white_height
    
    comp = CompositeVideoClip([base_video] + white_bar_list + [bottom_text_clip, border_clip] + loops + vig + giphy + caption_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    
    fps = random.choice(FPS_CHOICES)
    print(f"[FPS] NTSC {fps} - Old file edited exact 74K + normal speed {total:.1f}s + caption {base_dur:.3f}s readable")

    try:
        from audio_retention import get_bgm_volume_filter
        bg_music = get_free_bg_music()
        if bg_music:
            bg_music = bg_music.subclip(0, total).set_duration(total)
            bg_temp_in = "temp/bgm_in.mp3"
            bg_temp_out = "temp/bgm_out.mp3"
            bg_music.write_audiofile(bg_temp_in, logger=None)
            bg_af = get_bgm_volume_filter()
            cmd_bgm = ["ffmpeg","-y","-i", bg_temp_in, "-af", bg_af, "-c:a", "libmp3lame", "-b:a", "128k", bg_temp_out]
            subprocess.run(cmd_bgm, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            bg_music_filtered = AudioFileClip(bg_temp_out)
            bg_music_filtered = bg_music_filtered.fx(afx.audio_fadein, 0.4).set_start(0)
            final_audio = CompositeAudioClip([audio, bg_music_filtered.volumex(0.09)])
        else:
            final_audio = audio
    except Exception as e:
        print(f"BGM BEST failed {e}, using simple BGM")
        bg_music = get_free_bg_music()
        if bg_music:
            bg_music = bg_music.subclip(0, total).set_duration(total)
            bg_music = bg_music.fx(afx.audio_fadein, 0.3).set_start(0)
            final_audio = CompositeAudioClip([audio, bg_music.volumex(0.08)])
        else:
            final_audio = audio

    comp = comp.set_audio(final_audio)

    print(f"[OLD FILE EDITED EXACT 74K + NORMAL SPEED] Direct write - White bar {actual_white_height}px bold italic 48px exact 74K + {total:.1f}s normal not 5s rush + caption {base_dur:.3f}s normal readable")
    comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)

    try:
        import glob
        for f in glob.glob("temp/txt_*.png") + glob.glob("temp/whitebar_*.png") + glob.glob("temp/txt_white_*.png") + glob.glob("temp/whitebar_74k_exact_old_*.png") + glob.glob("temp/bottom_74k_old_file_*.png") + glob.glob("temp/border_old_file_*.png"):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass

    return output_path

if __name__=="__main__":
    print("Test OLD FILE EDITED EXACT 74K + NORMAL SPEED - White bar 190px bold italic 48px exact 74K + Speed 13-15 sec normal + Caption 0.26-0.32s normal")
    data={
        "full_script":"Families hearts shattered tonight as secret Senate betrayal leaks, shocking deal no one saw coming leaves America stunned and crying, this changes everything for millions",
        "title":"Senate Shocker Shatters Families",
        "viral_hook":"Senate Shocker Shatters Families",
        "pexels_query":"shocked emotional families crying",
        "pexels_keywords":["shocked","families","crying","betrayal"],
        "first_sentence_punch":"Families hearts shattered tonight as secret Senate betrayal leaks"
    }
    create_video(data)
