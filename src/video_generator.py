"""
ULTIMATE GOD LEVEL - BEST VIDEO GENERATOR - EXACT 74K DICTO + NORMAL SPEED + SAFE PIPER FIX
Location: src/video_generator.py
FIXES APPLIED FOR ERROR IN SCREENSHOT:
- Error 1: TypeError: PiperVoice.synthesize() got unexpected keyword 'length_scale' -> Fixed: try with length_scale, fallback without
- Error 2: wave.Error: # channels not specified -> Fixed: safe wave writing with header check + silent fallback
- Error 3: main.py calling create_video(full_script, "output/final.mp4") wrong args -> Fixed in main.py

PLUS:
- WHITE_BAR_HEIGHT = 190 exact 74K dicto (not 180)
- White bar bold black italic 48px 2 lines with emoji 😱 location (0,0) full width - exact 74K
- Script speed NORMAL 1.0-1.03X 13-15 sec not 5 sec rush
- Caption speed NORMAL 0.26-0.32s per word
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
WHITE_BAR_HEIGHT = 190
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
                    final_clip = video_clip.subclip(rand_start, min(rand_start+2, video_clip.duration)).resize(height=1920-WHITE_BAR_HEIGHT).set_position('center').without_audio()
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
        print(f"Pexels error: {e}")
    return [ColorClip(size=(1080,1920), color=(random.randint(20,50),random.randint(15,40),random.randint(40,80)), duration=CLIP_DENSITY) for _ in range(num)]

def make_white_bar_text_image_viral_EXACT_74K(text, fontsize=48):
    viral_text = clean_id(text).strip()
    words = viral_text.split()
    if len(words) >= 4:
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:]) + " \U0001f631"
        lines = [line1, line2]
    else:
        lines = [viral_text + " \U0001f631"]
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
    p = f"temp/whitebar_74k_exact_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    return p, bar_height

def make_74k_bottom_text_exact(text, duration):
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
    p = f"temp/bottom_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((35, 0.78), relative=True)
    return clip

def make_black_rounded_border(duration):
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0,0,WIDTH,HEIGHT], radius=32, outline=(0,0,0), width=14)
    p = f"temp/border_74k_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(duration).set_position((0,0))
    return clip

def make_text_image_best(text, fontsize, color, stroke_w=6, size=(1080, 200), bg_color=None, font_path=None, is_viral_bottom=False):
    if bg_color:
        img=Image.new('RGBA', size, bg_color)
    else:
        img=Image.new('RGBA', size, (0,0,0,0))
    d=ImageDraw.Draw(img)
    chosen_font = font_path or random.choice(["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
    try:
        f=ImageFont.truetype(chosen_font, fontsize)
    except:
        f=ImageFont.load_default()
    if is_viral_bottom:
        d.text((size[0]//2, size[1]//2), text, font=f, fill="white", stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    else:
        d.text((size[0]//2, size[1]//2), text, font=f, fill=color, stroke_width=stroke_w, stroke_fill="black", anchor="mm")
    p=f"temp/txt_{random.randint(1,999999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    return p

def word_clip_god_best_american_normal(word, dur, is_keyword=False, is_first_word=False):
    if is_first_word:
        color = "#FF0000"
        fontsize = 88
    elif is_keyword:
        color = "#FFEB3B"
        fontsize = 84
    else:
        color = "#FFFFFF"
        fontsize = 76
    path = make_text_image_best(word, fontsize, color, 7, (1020, 300), is_viral_bottom=True)
    clip = ImageClip(path).set_duration(dur).set_position(('center',0.72),relative=True)
    return clip

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    # Handle both dict and string input - FIXED for main.py calling issue
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or ""
        title=script_data.get('title','Brutal New Tariffs Panic Millions')
        viral_hook=script_data.get('viral_hook','') or title
        first_punch = script_data.get('first_sentence_punch','')
    elif isinstance(script_data, str):
        # If main.py passes full_script as string and output_path as second arg incorrectly
        if story and isinstance(story, str) and story.endswith('.mp4'):
            # story is actually output_path from wrong call
            output_path = story
            raw_script = script_data
            title = raw_script[:50]
            viral_hook = title
            first_punch = raw_script[:60]
        else:
            raw_script=str(script_data)
            title=raw_script[:50]
            viral_hook=title
            first_punch = raw_script[:60]
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

    print(f"[74K EXACT FIXED] Creating exact 74K frame dicto copy for: {viral_hook}")

    # ===== SAFE PIPER TTS - FIXED FOR OLD PIPER VERSION =====
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    os.makedirs("temp", exist_ok=True)
    
    # SAFE SYNTHESIS - handles both new and old Piper versions
    audio_chunks = []
    sample_rate = 22050
    
    try:
        print("[TTS] Trying new Piper API with length_scale...")
        gen = voice.synthesize(script_text, length_scale=1.25, noise_scale=0.6, noise_w_scale=0.75)
        for ch in gen:
            audio_chunks.append(ch)
            sample_rate = ch.sample_rate
        print(f"[TTS] New API success, got {len(audio_chunks)} chunks")
    except TypeError as e:
        if 'length_scale' in str(e) or 'unexpected keyword' in str(e):
            print(f"[TTS FIX] Old Piper version detected (no length_scale), using fallback: {e}")
            try:
                gen = voice.synthesize(script_text)
                for ch in gen:
                    audio_chunks.append(ch)
                    sample_rate = ch.sample_rate
                print(f"[TTS FIX] Fallback success, got {len(audio_chunks)} chunks")
            except Exception as e2:
                print(f"[TTS] Fallback synthesis failed: {e2}")
                audio_chunks = []
        else:
            print(f"[TTS] TypeError: {e}")
            audio_chunks = []
    except Exception as e:
        print(f"[TTS] Error: {e}, trying fallback without length_scale")
        try:
            gen = voice.synthesize(script_text)
            for ch in gen:
                audio_chunks.append(ch)
                sample_rate = ch.sample_rate
        except Exception as e2:
            print(f"[TTS] Fallback failed: {e2}")
            audio_chunks = []
    
    # SAFE WAVE WRITING - prevents "channels not specified" error
    try:
        if not audio_chunks:
            print("[TTS FIX] No audio chunks, creating 2 sec silent fallback")
            with wave.open(audio_path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)
                wav.writeframes(bytes([0]*22050*2*2))
        else:
            with wave.open(audio_path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                for ch in audio_chunks:
                    wav.writeframes(ch.audio_int16_bytes)
            print(f"[TTS FIX] Wrote {len(audio_chunks)} chunks to {audio_path}")
    except Exception as e:
        print(f"[TTS FIX] Wave write failed {e}, creating silent with ffmpeg")
        try:
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","2","-c:a","pcm_s16le",audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    
    try:
        from audio_retention import get_tts_retention_filter
        temp_audio_filtered = "temp/voice_filtered.wav"
        af_filter = get_tts_retention_filter(first_punch, american_mode=True)
        cmd = ["ffmpeg","-y","-i", audio_path, "-af", af_filter, "-c:a", "pcm_s16le", temp_audio_filtered]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio=AudioFileClip(temp_audio_filtered)
    except Exception as e:
        print(f"[TTS] Retention filter failed {e}, using raw audio")
        audio=AudioFileClip(audio_path)
        audio = audio.fx(vfx.speedx, random.choice([1.0, 1.02, 1.03]))
    
    total=audio.duration
    if total < DURATION_MIN:
        audio = audio.fx(vfx.speedx, total / DURATION_MIN)
        total = DURATION_MIN
    if total > DURATION_MAX:
        audio = audio.subclip(0, DURATION_MAX)
        total = DURATION_MAX

    print(f"2. Pexels 0.8s emotional clips only - exact 74K middle video...")
    clips_needed = max(14, int(total / CLIP_DENSITY) + 3)
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

    print(f"3. Creating exact 74K frame dicto - white bar 190px + bottom text...")
    
    whitebar_path, actual_white_height = make_white_bar_text_image_viral_EXACT_74K(viral_hook, bar_height=190)
    white_bar_clip = ImageClip(whitebar_path).set_duration(total).set_position((0,0))
    bottom_text_clip = make_74k_bottom_text_exact(viral_hook, total)
    border_clip = make_black_rounded_border(total)

    # Caption timing NORMAL
    try:
        from audio_retention import get_american_captions_timing
        timing = get_american_captions_timing(total, len(script_text.split()), first_words_count=5)
        base_dur = timing["base_dur"]
        first_dur = timing["first_dur"]
        keyword_dur = timing["keyword_dur"]
        overlap = timing["overlap"]
    except:
        base_dur = total / max(len(script_text.split()),1) * 0.98
        base_dur = max(0.24, min(0.34, base_dur))
        first_dur = base_dur * 1.35
        keyword_dur = base_dur * 1.15
        overlap = 0.96
    
    words = script_text.split()
    caption_clips=[]
    first_words_count = min(5, len(words))
    current_time = 0
    for i,w in enumerate(words):
        is_first = i < first_words_count
        is_kw = any(k in w.upper() for k in KEYWORDS_RED) or is_first
        dur = first_dur if is_first else (keyword_dur if is_kw else base_dur)
        wc = word_clip_god_best_american_normal(w.upper(), dur, is_kw, is_first).set_start(current_time)
        caption_clips.append(wc)
        current_time += dur * overlap

    print(f"4. Composite exact 74K dicto copy - white bar {actual_white_height}px + bottom text + border...")
    
    comp = CompositeVideoClip([base_video, white_bar_clip, bottom_text_clip, border_clip] + caption_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    
    fps = random.choice(FPS_CHOICES)
    comp = comp.set_audio(audio)
    comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)

    try:
        import glob
        for f in glob.glob("temp/whitebar_74k_*.png") + glob.glob("temp/bottom_74k_*.png") + glob.glob("temp/border_74k_*.png") + glob.glob("temp/txt_*.png"):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass

    return output_path

if __name__=="__main__":
    data={
        "full_script":"Brutal new tariffs panic millions as families hearts shattered tonight, shocking betrayal leaves America stunned",
        "title":"Brutal New Tariffs Panic Millions",
        "viral_hook":"Brutal New Tariffs Panic Millions",
        "pexels_query":"shocked man panic",
        "first_sentence_punch":"Brutal new tariffs panic millions"
    }
    create_video(data)
