"""
ULTIMATE GOD LEVEL - EXACT 74K FRAME DICTO COPY - SAME AS 74K VIEWS FRAME
Location: src/video_generator.py
USER REQUEST: Aisa hi chaiye jo is image m 74k views wali video ka frame hai same dicto vaise hi ana chaiye meri video m

74K FRAME ANALYSIS (Right side):
- Top white bar: Full width 1080, height 180-200, white background, bold black italic text, 2 lines "Nothing like quality time / with the family 😂" centered, emoji, black rounded top border
- Middle: Video clip full, no USA label, no WAIT FOR IT, no branding, just raw emotional clip
- Bottom: White text with thick black stroke 7px, 2 lines "With that drawing, no / wonder he didn't get p..." bottom left, 38-42px, ellipsis, black rounded bottom
- Black border: 12px thick, rounded corners 35px radius
- Bottom left: "74K views" white small text inside black border
- No extra loops, no channel name, no USA

NEW CODE: Exact dicto same as 74K frame - for "Brutal New Tariffs Panic Millions"
- Top white bar 190px, bold black italic 48px, 2 lines "Brutal New Tariffs / Panic Millions 😱"
- Middle raw clip 0.8s emotional only, no overlays
- Bottom white black stroke 42px, 2 lines "Brutal New Tariffs / Panic Millions..." bottom left like 74K
- Black rounded border 14px
- No WAIT FOR IT, no HERE'S WHY, no USA, no channel branding - exact 74K clean
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

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 190  # Exact 74K frame height - 190px
BLACK_BORDER = 14
CORNER_RADIUS = 32
CLIP_DENSITY = 0.8
DURATION_MIN = 11
DURATION_MAX = 15
FPS_CHOICES = [29.97, 29.98, 59.94, 59.95]
NOISE_HUE_FILTER = ""

FONT_LIST = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
]
FONT_COLORS = ["#FFFFFF"]
KEYWORDS_RED = ["BRUTAL","TARIFFS","PANIC","MILLIONS","SHOCKING","BREAKING","TRUMP","BIDEN"]

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-ryan-medium.onnx"; cp="models/en_US-ryan-medium.onnx.json"
    if not os.path.exists(mp):
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
    if isinstance(script_data, dict):
        pexels_query = script_data.get('pexels_query', '')
        pexels_keywords = script_data.get('pexels_keywords', [])
        first_punch = script_data.get('first_sentence_punch', '')
        script_text = script_data.get('full_script', '')
    else:
        pexels_query = str(script_data)[:50]
        pexels_keywords = []
        first_punch = ""
        script_text = str(script_data)
    
    if pexels_query:
        search_q = pexels_query
    elif pexels_keywords:
        search_q = " ".join(pexels_keywords[:3])
    else:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', script_text.lower())
        stop = {"this","that","with","from","have","been","will","they","them"}
        keywords = [w for w in words if w not in stop][:3]
        search_q = " ".join(keywords) if keywords else "shocked man reaction"
    
    final_search_queries = [search_q, f"{search_q} shocked reaction"]
    
    if not key:
        emotional_colors = [(25,15,25), (20,25,45), (45,20,20)]
        return [ColorClip(size=(1080,1920), color=random.choice(emotional_colors), duration=CLIP_DENSITY) for _ in range(num)]
    
    try:
        h={"Authorization":key}
        all_videos = []
        for sq in final_search_queries[:2]:
            q_clean = clean_id(str(sq))
            words_found = re.findall(r'\w+', q_clean)[:4]
            words_found = [w for w in words_found if not re.match(r'^m[0-9]', w, re.I) and len(w)>2]
            sq_final = " ".join(words_found) if words_found else "shocked man reaction"
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
                    final_clip = video_clip.subclip(rand_start, min(rand_start+2, video_clip.duration)).resize(height=1920).set_position('center').without_audio()
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
                    final_cuts.append(cut)
                except:
                    final_cuts.append(c)
            return final_cuts[:num]
    except Exception as e:
        print(f"Pexels error: {e}")
    
    return [ColorClip(size=(1080,1920), color=(random.randint(20,50),random.randint(15,40),random.randint(40,80)), duration=CLIP_DENSITY) for _ in range(num)]

def make_74k_white_bar_exact(text, bar_height=190):
    """
    EXACT 74K FRAME WHITE BAR - Same dicto
    - Height 190px (74K frame height)
    - Bold black italic, 2 lines, centered, emoji
    - White background, black rounded top border
    - Font: Bold italic black 48px first line, 46px second line + emoji
    """
    viral_text = clean_id(text).strip()
    # 74K style: 2 lines always for 4-5 words title
    words = viral_text.split()
    if len(words) >= 4:
        # Split into 2 balanced lines like 74K: "Brutal New Tariffs / Panic Millions 😱"
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) + " 😱"  # Add emoji like 74K frame 😂
        lines = [line1, line2]
    else:
        lines = [viral_text + " 😱"]
    
    bar_height = 190 if len(lines)==1 else 190  # 74K frame height 190 for 2 lines also
    
    img = Image.new('RGB', (1080, bar_height), (255,255,255))
    d = ImageDraw.Draw(img)
    
    # Use bold oblique for italic bold like 74K frame
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
        # 2 lines centered like 74K: first line top, second line bottom with emoji
        bbox1 = d.textbbox((0,0), lines[0], font=f1)
        w1 = bbox1[2]-bbox1[0]
        d.text(((1080-w1)//2, bar_height//2 - 24), lines[0], font=f1, fill=(0,0,0), anchor="mm")
        bbox2 = d.textbbox((0,0), lines[1], font=f2)
        w2 = bbox2[2]-bbox2[0]
        d.text(((1080-w2)//2, bar_height//2 + 26), lines[1], font=f2, fill=(0,0,0), anchor="mm")
    
    p = f"temp/whitebar_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    return p, bar_height

def make_74k_bottom_text_exact(text, duration):
    """
    EXACT 74K FRAME BOTTOM TEXT - Same dicto
    - White with thick black stroke 7px
    - 2 lines bottom left, 38-42px, with ellipsis "..."
    - Location: bottom left, like "With that drawing, no / wonder he didn't get p..."
    - For "Brutal New Tariffs Panic Millions" -> "Brutal New Tariffs / Panic Millions..."
    """
    viral_text = clean_id(text).strip()
    words = viral_text.split()
    if len(words) >= 4:
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) + "..."  # Ellipsis like 74K
        lines = [line1, line2]
    else:
        lines = [viral_text + "..."]
    
    # Bottom text image - white with black stroke
    img = Image.new('RGBA', (900, 160), (0,0,0,0))
    d = ImageDraw.Draw(img)
    font_path_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        f1 = ImageFont.truetype(font_path_bold, 42)
        f2 = ImageFont.truetype(font_path_bold, 40)
    except:
        f1 = ImageFont.load_default()
        f2 = ImageFont.load_default()
    
    # First line
    d.text((10, 10), lines[0], font=f1, fill=(255,255,255), stroke_width=7, stroke_fill=(0,0,0), anchor="lt")
    # Second line
    if len(lines) > 1:
        d.text((10, 70), lines[1], font=f2, fill=(255,255,255), stroke_width=7, stroke_fill=(0,0,0), anchor="lt")
    
    p = f"temp/bottom_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    
    # Position: bottom left like 74K frame (x=35, y=bottom-180)
    clip = ImageClip(p).set_duration(duration).set_position((35, 0.78), relative=True)
    return clip

def make_74k_views_counter(duration):
    """74K frame bottom left '74K views' small white text"""
    img = Image.new('RGBA', (250, 60), (0,0,0,0))
    d = ImageDraw.Draw(img)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        f = ImageFont.truetype(font_path, 32)
    except:
        f = ImageFont.load_default()
    d.text((10, 10), "74K views", font=f, fill=(255,255,255), anchor="lt")
    p = f"temp/views_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((35, 0.90), relative=True)
    return clip

def make_black_rounded_border(duration):
    """Black rounded border 14px like 74K frame"""
    # Create border image with rounded corners
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    d = ImageDraw.Draw(img)
    # Outer rounded rectangle black border
    d.rounded_rectangle([0,0,WIDTH,HEIGHT], radius=32, outline=(0,0,0), width=14)
    p = f"temp/border_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((0,0))
    return clip

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    """
    EXACT 74K FRAME DICTO COPY - Same as 74K views frame
    """
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or ""
        title=script_data.get('title','Brutal New Tariffs Panic Millions')
        viral_hook=script_data.get('viral_hook','') or title
        first_punch = script_data.get('first_sentence_punch','')
    else:
        raw_script=str(script_data)
        title=raw_script[:50]
        viral_hook=title
        first_punch = raw_script[:60]

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    script_text = clean_script_no_trim(raw_script)
    if len(script_text.split()) > 50:
        script_text = " ".join(script_text.split()[:50])

    print(f"[74K EXACT] Creating exact 74K frame dicto copy for: {viral_hook}")

    # TTS - American best 1.0-1.03X 13-15 sec
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    try:
        with wave.open(audio_path,"wb") as wav:
            first=True
            for ch in voice.synthesize(script_text, length_scale=1.25, noise_scale=0.6, noise_w_scale=0.75):
                if first:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                wav.writeframes(ch.audio_int16_bytes)
    except:
        with wave.open(audio_path,"wb") as wav:
            first=True
            for ch in voice.synthesize(script_text):
                if first:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
                wav.writeframes(ch.audio_int16_bytes)
    
    try:
        from audio_retention import get_tts_retention_filter
        temp_audio_filtered = "temp/voice_filtered.wav"
        af_filter = get_tts_retention_filter(first_punch, american_mode=True)
        cmd = ["ffmpeg","-y","-i", audio_path, "-af", af_filter, "-c:a", "pcm_s16le", temp_audio_filtered]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio=AudioFileClip(temp_audio_filtered)
    except:
        audio=AudioFileClip(audio_path)
        audio = audio.fx(vfx.speedx, random.choice([1.0, 1.02, 1.03]))
    
    total=audio.duration
    if total < DURATION_MIN:
        audio = audio.fx(vfx.speedx, total / DURATION_MIN)
        total = DURATION_MIN
    if total > DURATION_MAX:
        audio = audio.subclip(0, DURATION_MAX)
        total = DURATION_MAX

    print(f"2. Pexels 0.8s emotional clips only - exact 74K middle video no overlays...")
    clips_needed = max(14, int(math.ceil(total / CLIP_DENSITY)) + 3)
    raw_clips = get_best_free_clips_from_script(script_data, num=clips_needed)
    
    final_video_clips=[]
    t=0
    for c in raw_clips:
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
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=(30,20,40), duration=total)]

    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)

    print(f"3. Creating exact 74K frame dicto - white bar 190px bold italic black + bottom white black stroke...")
    
    # Exact 74K white bar
    whitebar_path, actual_white_height = make_74k_white_bar_exact(viral_hook, bar_height=190)
    white_bar_clip = ImageClip(whitebar_path).set_duration(total).set_position((0,0))
    
    # Exact 74K bottom text
    bottom_text_clip = make_74k_bottom_text_exact(viral_hook, total)
    
    # Exact 74K views counter
    views_clip = make_74k_views_counter(total)
    
    # Black rounded border
    border_clip = make_black_rounded_border(total)

    print(f"4. Composite exact 74K dicto copy - white bar {actual_white_height}px + bottom text + border...")
    
    comp = CompositeVideoClip([base_video, white_bar_clip, bottom_text_clip, views_clip, border_clip], size=(WIDTH, HEIGHT)).set_duration(total)
    
    fps = random.choice(FPS_CHOICES)
    comp = comp.set_audio(audio)
    comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)

    try:
        import glob
        for f in glob.glob("temp/whitebar_74k_*.png") + glob.glob("temp/bottom_74k_*.png") + glob.glob("temp/views_74k_*.png") + glob.glob("temp/border_74k_*.png"):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass

    return output_path

if __name__=="__main__":
    print("Test exact 74K frame dicto copy")
    data={
        "full_script":"Brutal new tariffs panic millions as families hearts shattered tonight, shocking betrayal leaves America stunned",
        "title":"Brutal New Tariffs Panic Millions",
        "viral_hook":"Brutal New Tariffs Panic Millions",
        "pexels_query":"shocked man panic",
        "first_sentence_punch":"Brutal new tariffs panic millions"
    }
    create_video(data)
