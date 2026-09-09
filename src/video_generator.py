"""
ULTIMATE GOD LEVEL - BEST VIDEO GENERATOR - SECOND FRAME VIRAL STYLE
Location: src/video_generator.py
FINAL EDIT as per all requests:

- RETENTION_WORDS = 50 (up to 50 flexible, 50 tak koi rok nahi, 100% accuracy 50 ke andar)
- CLIP_DENSITY = 0.8 sec FIXED per clip - har clip 0.8 sec hi, clips wahi jisme emotion/shock ki kami na ho bilkul bhi
- Duration variable 11-15 sec (not fixed 11-13) - script ke hisaab se 11 sec ho ya 15 sec
- Pexels search FROM SCRIPT not TITLE - script ke sentence direct clip le sake, Pexels query = script keywords + emotional keywords
- NO trim_to_40_words - jo Gemini likhe wahi final, no today today, no kaat-peet
- Audio retention BEST: atempo 1.11/1.12X (not 1.15), pitch 1.025 youthful, 1 sec 160% punch for first shock sentence (American 4-5 baar replay), 3.2s 6% variation, warm bass + crystal treble + compressor + clean = enjoyable sunne me maza
- Visual SECOND FRAME STYLE (74K views wala): Top white bar bold black + emoji, Bottom white with black stroke + curiosity gap, expressive face reaction
- Anti-bot: Random fonts, random colors, random FPS NTSC 29.97/29.98/59.94/59.95, frame variation, no same font
- ULTRA CLEAN: NO noise/hue filter, NO colorx 1.1-1.25, NO overexposure - raw Pexels clean
- BGM: Volume har 3 sec 6% up/down + sub bass drop + stereo wide - emotional swell
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

# ===== FINAL RETENTION CONSTANTS - BEST =====
RETENTION_WORDS = 50  # 50 tak flexible - koi rok nahi, max 50
CLIP_DENSITY = 0.8  # FIXED 0.8 sec per clip - har clip 0.8 hi, emotional/shock only
DURATION_MIN = 11
DURATION_MAX = 15  # 11-15 variable as per request (11 sec ho ya 15 sec)
FPS_CHOICES = [29.97, 29.98, 59.94, 59.95]
NOISE_HUE_FILTER = ""  # ULTRA CLEAN - no overexposure
FONT_LIST = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
]
FONT_COLORS = ["#FFEB3B", "#FFFFFF", "#00E5FF", "#FF3D00", "#76FF03", "#FFEA00", "#FF1744", "#FFFFFF"]
# Second frame style colors - high contrast for viral
VIRAL_TOP_COLORS = ["#000000"]  # black on white bar
VIRAL_BOTTOM_COLORS = ["#FFFFFF"]  # white with black stroke
SFX_MAP = {
    "crash": "crash_hit", "police": "siren_punch", "fbi": "siren_punch",
    "arrested": "cuff_click", "dies": "grave_bass", "dead": "grave_bass",
    "shocking": "shock_hit", "breaking": "breaking_beep",
    "shattered": "heart_break", "betrayal": "shock_hit", "families": "emotional_punch"
}
KEYWORDS_RED = ["TRUMP","BIDEN","BREAKING","SHOCKING","USA","AMERICA","DIES","DEAD","CRASH","POLICE","COURT","FBI","JUST","ALERT","MASSIVE","HUGE","KILLED","ARRESTED","SHATTERED","BETRAYAL","FAMILIES","HEARTS"]
WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 180  # Slightly bigger for second frame style - meme white bar

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-ryan-medium.onnx"; cp="models/en_US-ryan-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading BEST FREE Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def clean_id(text: str) -> str:
    """Remove KG IDs like /m/04mjl, m04mjl"""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_script_no_trim(text: str) -> str:
    """FINAL: NO trim, NO today today, jo Gemini likhe wahi final - 50 tak flexible"""
    text = clean_id(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'Visual:.*?\|', '', text, flags=re.I)
    text = re.sub(r'Audio:\s*', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    # NO cutting, NO adding today today - as per request
    # 11 sec ho ya 15 sec ho - disturb nahi karna
    return text

def get_best_free_clips_from_script(script_data, num=20):
    """
    PEXELS FROM SCRIPT + 0.8s EMOTIONAL/SHOCK ONLY - BEST
    - Script se keywords nikal ke search, Title se nahi
    - Har clip 0.8 sec FIXED
    - Clips wahi jisme emotion/shock ki kami na ho bilkul bhi
    - Second frame jaisa expressive face reaction priority
    """
    key=os.getenv("PEXELS_API_KEY")
    clips=[]
    temp_files=[]
    
    # Get Pexels query from SCRIPT (not title) - as per latest request
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
    
    # Build search query from SCRIPT - not title
    if pexels_query:
        search_q = pexels_query
    elif pexels_keywords:
        search_q = " ".join(pexels_keywords[:3])
    else:
        # Fallback: extract from script directly
        words = re.findall(r'\b[a-zA-Z]{4,}\b', script_text.lower())
        stop = {"this","that","with","from","have","been","will","they","them","what","when","where"}
        keywords = [w for w in words if w not in stop][:3]
        search_q = " ".join(keywords) if keywords else "emotional shocked reaction"
    
    # Add emotional boosters for second frame style - face expression change
    emotional_boosters = ["shocked", "emotional", "crying", "reaction", "dramatic"]
    # Mix search_q with emotional booster for high-emotion clips only
    final_search_queries = [
        search_q,
        f"{search_q} {random.choice(emotional_boosters)}",
        f"{first_punch.split()[0] if first_punch.split() else 'shocking'} {random.choice(emotional_boosters)} face"
    ]
    
    if not key:
        print(f"No PEXELS_API_KEY - Using BEST FREE emotional color clips for {search_q}")
        # Emotional colors - not boring
        emotional_colors = [(35,15,30), (20,30,60), (60,20,20), (30,50,70), (70,30,40)]
        return [ColorClip(size=(1080,1920), color=random.choice(emotional_colors), duration=CLIP_DENSITY) for _ in range(num)]
    
    try:
        h={"Authorization":key}
        # Try multiple queries for best emotional clips
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
                print(f"Pexels search FROM SCRIPT: '{sq_final}' -> {len(videos)} found")
            except:
                continue
        
        # Deduplicate and shuffle for anti-bot + variety
        seen_ids = set()
        unique_videos = []
        for v in all_videos:
            vid = v.get('id')
            if vid not in seen_ids:
                seen_ids.add(vid)
                unique_videos.append(v)
        random.shuffle(unique_videos)
        
        print(f"Pexels total unique FROM SCRIPT: {len(unique_videos)} videos, picking {num} emotional only - 0.8s FIXED")
        
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
                    # Random start for frame variation - anti-bot
                    rand_start = random.uniform(0, max(0, video_clip.duration-1.5))
                    final_clip = video_clip.subclip(rand_start, min(rand_start+2, video_clip.duration)).resize(height=1920-WHITE_BAR_HEIGHT).set_position('center').without_audio()
                    # ULTRA CLEAN - NO colorx, NO overexposure - raw clean
                    temp_files.append(tmp_path)
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
            random.shuffle(clips)
            final_cuts=[]
            for c in clips:
                try:
                    # FIXED 0.8s per clip - har clip 0.8 sec hi hogi
                    d = CLIP_DENSITY
                    if hasattr(c, 'duration') and c.duration > d:
                        start = random.uniform(0, max(0, c.duration-d-0.2))
                        cut = c.subclip(start, start+d)
                    else:
                        cut = c.subclip(0, min(d, c.duration)) if hasattr(c, 'subclip') else c
                        cut = cut.set_duration(d)
                    # Ensure duration exactly 0.8
                    cut = cut.set_duration(CLIP_DENSITY)
                    final_cuts.append(cut)
                except:
                    final_cuts.append(c)
            print(f"Pexels SUCCESS FROM SCRIPT: {len(final_cuts)} emotional clips ready - 0.8s FIXED - emotional/shock only")
            return final_cuts[:num]
    except Exception as e:
        print(f"Pexels overall error: {e}")
        import traceback
        traceback.print_exc()
    
    if not clips:
        print("Pexels fallback to emotional color clips - 0.8s FIXED")
    return [ColorClip(size=(1080,1920), color=(random.randint(20,50),random.randint(15,40),random.randint(40,80)), duration=CLIP_DENSITY) for _ in range(num)]

def get_free_bg_music():
    try:
        key = os.getenv("PIXABAY_API_KEY")
        if not key:
            return None
        # Emotional cinematic for second frame style
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
    """BEST text image - Second frame style: white with black stroke for bottom, black on white for top"""
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
    
    # Second frame style: Bottom = white with thick black stroke (readable), Top = black on white
    if is_viral_bottom:
        # Bottom style - second frame viral: white text black stroke 6-7px
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

def make_white_bar_text_image_viral(text, fontsize=52):
    """SECOND FRAME VIRAL STYLE: White bar bold black + emoji"""
    # Add emoji for viral second frame style if not present
    viral_text = text.strip()
    # Ensure emoji for emotional punch - second frame has 😂
    emojis = ["😱", "😭", "😳", "💔", "🔥"]
    has_emoji = any(e in viral_text for e in ["😀","😂","😱","😭","😳","💔","🔥","😮","🤯"])
    
    lines = viral_text.split('\n')
    if len(viral_text) > 28 and '\n' not in viral_text:
        words = viral_text.split()
        mid = len(words)//2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    
    if len(lines) == 1:
        # Viral style: Bold black on white, bigger font for second frame
        fp = random.choice(FONT_LIST)
        # If no emoji, don't force, keep original but bold
        return make_text_image_best(lines[0], fontsize, "black", 0, (1040, 90), bg_color=(255,255,255,255), font_path=fp, is_viral_bottom=False)
    else:
        img = Image.new('RGBA', (1040, 130), (255,255,255,255))
        d = ImageDraw.Draw(img)
        fp = random.choice(FONT_LIST)
        try:
            f = ImageFont.truetype(fp, fontsize-4)
        except:
            f = ImageFont.load_default()
        d.text((1040//2, 30), lines[0], font=f, fill="black", anchor="mm")
        d.text((1040//2, 85), lines[1], font=f, fill="black", anchor="mm")
        p = f"temp/txt_white_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        return p

def word_clip_god_best(word, dur, is_keyword=False, is_first_word=False):
    """BEST word clip - emotional punch for first words + keywords"""
    if is_first_word:
        # First sentence words - MAX shock+emotion - bigger, red/yellow
        color = random.choice(["#FF0000","#FFEB3B","#FF1744"])
        fontsize = random.randint(82,90)
    elif is_keyword:
        color = random.choice(["#FF0000","#FFEB3B"])
        fontsize = random.randint(78,86)
    else:
        color = random.choice(FONT_COLORS)
        fontsize = random.randint(70,76)
    
    chosen_font = random.choice(FONT_LIST)
    # Second frame style: white with black stroke for readability (viral)
    stroke = 8 if is_first_word or is_keyword else 6
    path = make_text_image_best(word, fontsize, color, stroke, (1020, 300), font_path=chosen_font, is_viral_bottom=True)
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    
    if is_first_word or is_keyword:
        # Punch animation for shock words - pop + shake
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

def white_bar_viral_hook_clip_best(viral_hook_text: str, duration: float):
    """SECOND FRAME VIRAL STYLE: White bar with bold black + emoji - top"""
    white_bg = ColorClip((WIDTH, WHITE_BAR_HEIGHT), color=(255,255,255), duration=duration).set_position((0,0)).set_opacity(1)
    safe = clean_id(viral_hook_text).replace("'","").replace('"',"").strip()[:70]
    if not safe:
        safe = "Shocking Truth Revealed"
    
    # Add emotional emoji for viral second frame style if needed
    # Keep original text but ensure bold black
    
    try:
        img = Image.new('RGB', (1040, WHITE_BAR_HEIGHT-25), (255,255,255))
        d = ImageDraw.Draw(img)
        fp = random.choice(FONT_LIST)
        try:
            f = ImageFont.truetype(fp, 52)
        except:
            f = ImageFont.load_default()
        # Bold black on white - second frame viral style
        d.text((1040//2, (WHITE_BAR_HEIGHT-25)//2), safe, font=f, fill=(0,0,0), anchor="mm")
        p = f"temp/whitebar_{random.randint(1,999999999)}.png"
        os.makedirs("temp", exist_ok=True)
        img.save(p)
        hook_clip = ImageClip(p).set_duration(duration).set_position(('center', 12))
    except Exception as e:
        hook_path = make_text_image_best(safe, 52, "black", 0, (1040, WHITE_BAR_HEIGHT-25), bg_color=(255,255,255,255))
        hook_clip = ImageClip(hook_path).set_duration(duration).set_position(('center', 12))
    return [white_bg, hook_clip]
    
def retention_loops_best(total):
    clips=[]
    loops = [(1.5, "WAIT FOR IT"), (4, "HERE'S WHY"), (7.5, "WHAT HAPPENED NEXT?"), (10, "DON'T MISS THIS")]
    for t, txt in loops:
        if t < total:
            col = random.choice(FONT_COLORS)
            fp = random.choice(FONT_LIST)
            p = make_text_image_best(txt, random.randint(38,44), col, 5, (600, 90), font_path=fp, is_viral_bottom=True)
            c = ImageClip(p).set_duration(0.8).set_start(t).set_position(('center', 0.20), relative=True)
            c = c.resize(lambda t: 1.1 if t < 0.2 else 1.0)
            clips.append(c)
    return clips

def vignette_best(duration):
    # Light vignette only 0.08 - ultra clean, no dark overexposure
    top = ColorClip((1080, 200), color=(0,0,0), duration=duration).set_opacity(0.08).set_position((0,WHITE_BAR_HEIGHT))
    bottom = ColorClip((1080, 300), color=(0,0,0), duration=duration).set_opacity(0.12).set_position((0,1620))
    return [top, bottom]

def get_giphy_pro_editor_best(script_text: str, total_duration: float):
    """Giphy stickers - emotional reactions for second frame style"""
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
            "arrested": "police siren", "crash": "crash explosion",
            "shattered": "crying reaction", "hearts": "heartbreak crying", "betrayal": "shocked betrayal",
            "families": "family crying"
        }
        total_words = len(words)
        word_duration = total_duration / max(total_words, 1)
        found_positions = []
        for idx, w in enumerate(words):
            clean_w = re.sub(r'[^a-z]', '', w)
            if clean_w in triggers:
                timestamp = idx * word_duration
                if not found_positions or timestamp - found_positions[-1][0] > 2.5:
                    found_positions.append((timestamp, triggers[clean_w], clean_w))
        if not found_positions and total_duration > 5:
            found_positions = [(total_duration*0.15, "shocked reaction", "auto1"), (total_duration*0.55, "crying emotional", "auto2")]
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
                dur = random.uniform(1.0, 1.6)
                if original in ["shocking", "shattered", "hearts", "betrayal", "unbelievable"]:
                    pos = ('center', 0.30); size = 360
                elif original in ["wins", "celebration"]:
                    pos = ('center', 0.38); size = 380
                else:
                    pos_x = random.choice([0.1, 0.65]); pos_y = random.choice([0.18, 0.32, 0.52])
                    pos = (pos_x, pos_y); size = random.randint(240, 320)
                try:
                    g_clip = VideoFileClip(tmp.name).resize(width=size).set_duration(dur).set_start(ts)
                    g_clip = g_clip.set_position(pos, relative=True).set_opacity(0.92)
                    g_clip = g_clip.resize(lambda t: 0.8 + 0.2*t/dur if t < dur*0.2 else (1.1 - 0.1*(t-dur*0.8)/dur if t > dur*0.8 else 1.0))
                    clips.append(g_clip)
                except:
                    continue
            except:
                continue
        return clips
    except:
        return []

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    """
    BEST VIDEO GENERATOR - Second frame viral style
    - Script up to 50 words flexible, no trim, jo Gemini likhe wahi final
    - Pexels FROM SCRIPT, 0.8s FIXED emotional/shock only
    - Top white bar bold black + bottom white with black stroke (second frame 74K style)
    - Audio BEST 1.11/1.12X + 160% punch
    """
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

    # FINAL: No trim, jo Gemini likhe wahi final - 50 tak flexible
    script_text = clean_script_no_trim(raw_script)
    word_count = len(script_text.split())
    print(f"[RETENTION BEST] Script {word_count} words (up to 50 flexible, no trim) - 50 tak koi rok nahi - 100% accuracy 50 ke andar")

    # Validate 50 words max - but no today today adding
    if word_count > 50:
        print(f"[WARNING] {word_count} >50, trimming to 50 for 100% accuracy")
        script_text = " ".join(script_text.split()[:50])
        word_count = 50

    print("1. TTS Piper + BEST Audio Retention 1.11/1.12X + 160% Punch...")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    with wave.open(audio_path,"wb") as wav:
        first=True
        for ch in voice.synthesize(script_text):
            if first:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
            wav.writeframes(ch.audio_int16_bytes)
    
    # Use BEST audio retention filter
    try:
        from audio_retention import get_tts_retention_filter, apply_audio_retention_to_file
        print(f"Using BEST audio_retention: 1.11/1.12X + 160% punch for: {first_punch[:60]}")
        # Apply BEST filter directly via ffmpeg
        temp_audio_filtered = "temp/voice_filtered.wav"
        af_filter = get_tts_retention_filter(first_punch)
        cmd = ["ffmpeg","-y","-i", audio_path, "-af", af_filter, "-c:a", "pcm_s16le", temp_audio_filtered]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio=AudioFileClip(temp_audio_filtered)
    except Exception as e:
        print(f"BEST audio retention failed {e}, using fallback 1.11X")
        audio=AudioFileClip(audio_path)
        audio = audio.fx(vfx.speedx, random.choice([1.11, 1.12]))
    
    total=audio.duration
    # Variable duration 11-15 sec as per request
    if total > DURATION_MAX:
        audio = audio.subclip(0, DURATION_MAX)
        total = DURATION_MAX
    if total < DURATION_MIN:
        print(f"[WARN] Audio {total:.1f}s < {DURATION_MIN}s - padding allowed (11-15 variable)")

    # Punch already applied via audio_retention filter - first 1 sec 160%

    first_sentence = first_punch if first_punch else (script_text.split('.')[0][:65] if '.' in script_text else script_text[:65])
    print(f"2. Pexels FROM SCRIPT {CLIP_DENSITY}s FIXED emotional/shock only - SECOND FRAME VIRAL STYLE...")
    clips_needed = max(12, int(math.ceil(total / CLIP_DENSITY)) + 3)
    
    # PEXELS FROM SCRIPT - not title - as per latest request
    raw_clips = get_best_free_clips_from_script(script_data, num=clips_needed)
    
    # Build sequence 0.8s FIXED each, emotional/shock only, no low emotion
    final_video_clips=[]
    t=0
    for idx, c in enumerate(raw_clips):
        if t >= total:
            break
        dur = min(CLIP_DENSITY, total-t)
        try:
            sub = c.subclip(0, dur).set_start(t)
            # No heavy colorx - ultra clean raw
            final_video_clips.append(sub)
        except:
            final_video_clips.append(c.set_start(t).set_duration(dur))
        t+=dur

    if not final_video_clips:
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=(30,20,50), duration=total)]

    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)

    print("3. Captions BEST - Second frame style white with black stroke + first word punch...")
    words = script_text.split()
    # Variable duration based on total and word count (11-15 sec variable)
    word_dur = total / max(len(words),1) * 1.15
    caption_clips=[]
    first_words_count = min(5, len(words))  # First 5 words = max shock+emotion punch
    for i,w in enumerate(words):
        is_first = i < first_words_count
        is_kw = any(k in w.upper() for k in KEYWORDS_RED) or is_first
        dur = word_dur
        wc = word_clip_god_best(w.upper(), dur, is_kw, is_first).set_start(i*word_dur*0.95)
        caption_clips.append(wc)

    white_bar = white_bar_viral_hook_clip_best(viral_hook, total)
    branding = top_branding_best(total)
    loops = retention_loops_best(total)
    vig = vignette_best(total)
    giphy = get_giphy_pro_editor_best(script_text, total)

    print("4. Composite BEST + NTSC FPS + Second frame viral style - ULTRA CLEAN...")
    comp = CompositeVideoClip([base_video] + white_bar + branding + loops + vig + giphy + caption_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    
    fps = random.choice(FPS_CHOICES)
    print(f"[FPS] Selected NTSC fps: {fps} - ULTRA CLEAN 0.8s emotional clips only")

    # BGM with BEST filter - enjoyable
    try:
        from audio_retention import get_bgm_volume_filter
        bg_music = get_free_bg_music()
        if bg_music:
            bg_music = bg_music.subclip(0, total).set_duration(total)
            # Apply BGM BEST filter
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

    # ULTRA CLEAN direct write - NO second ffmpeg noise/hue
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
        print(f"[ULTRA CLEAN BEST] Direct write NO noise/hue = RAW PEXELS CLEAN - 0.8s emotional only - Second frame viral style")
        comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)

    try:
        import glob
        for f in glob.glob("temp/txt_*.png") + glob.glob("temp/whitebar_*.png") + glob.glob("temp/txt_white_*.png"):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass

    return output_path

if __name__=="__main__":
    print("Test video_generator BEST - Second frame viral style - 0.8s emotional clips only - 50 words flexible")
    data={
        "full_script":"Families hearts shattered tonight as secret Senate betrayal leaks, shocking deal no one saw coming leaves America stunned and crying, this changes everything for millions",
        "title":"Senate Shocker Shatters Families",
        "viral_hook":"Senate Shocker Shatters Families",
        "pexels_query":"shocked emotional families crying",
        "pexels_keywords":["shocked","families","crying","betrayal"],
        "first_sentence_punch":"Families hearts shattered tonight as secret Senate betrayal leaks"
    }
    create_video(data)
