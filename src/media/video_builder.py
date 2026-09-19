"""
src/media/video_builder.py - AUTONOMOUS VIDEO BUILDER v6 (Memory Safe)
- Duration capped at 20s
- Clips capped at 40 (GitHub Actions memory limit)
- 8K only if video < 18s, else 4K fallback
- Fast cuts first 5s (0.5s), then learned density
- Audio cut fix
"""

import os
import random
import wave
import subprocess
import tempfile
import glob
import re
import time

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
if not hasattr(Image, 'BICUBIC'):
    Image.BICUBIC = Image.Resampling.BICUBIC
if not hasattr(Image, 'BILINEAR'):
    Image.BILINEAR = Image.Resampling.BILINEAR
if not hasattr(Image, 'NEAREST'):
    Image.NEAREST = Image.Resampling.NEAREST

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, ColorClip,
        CompositeVideoClip, CompositeAudioClip
    )
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    print("[VIDEO_BUILDER] MoviePy 1.x loaded")
except ImportError as e:
    print(f"[VIDEO_BUILDER] MoviePy 1.x REQUIRED: {e}")
    raise

from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = VIDEO_CONFIG['WIDTH']
HEIGHT = VIDEO_CONFIG['HEIGHT']

TOP_BLACK_STRIP = 180
WHITE_BAR_HEIGHT = 210
BOTTOM_BLACK_STRIP = 200

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"

GREEN_ACCENT = (34, 139, 34)
RED_ACCENT = (220, 30, 30)
BLUE_ACCENT = (30, 100, 220)

UPSCALE_WIDTH = 4320
UPSCALE_HEIGHT = 7680

FAST_CUT_DURATION = 0.5
FAST_CUT_UNTIL = 5.0
MAX_CLIPS = 40           # ✅ Hard cap for memory
MAX_DURATION = 20        # ✅ Hard cap for duration


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        try:
            return ImageFont.truetype(FONT_BOLD, size)
        except:
            return ImageFont.load_default()


def get_learned_params():
    try:
        from src.learning.auto_optimizer import get_config
        return {
            "duration": get_config("video_duration", 18),
            "clip_density": get_config("clip_density", 0.8),
            "tts_speed": get_config("tts_speed", 1.15),
            "words_target": get_config("words_target", 50),
            "bar_color": get_config("bar_color", "green"),
        }
    except:
        return {"duration": 18, "clip_density": 0.8, "tts_speed": 1.15, "words_target": 50, "bar_color": "green"}


def get_accent_color():
    params = get_learned_params()
    colors = {"green": GREEN_ACCENT, "red": RED_ACCENT, "blue": BLUE_ACCENT}
    return colors.get(params.get("bar_color", "green"), GREEN_ACCENT)


# ============================================================
# EMOTION
# ============================================================

def detect_emotion_from_text(text):
    if not text:
        return ('neutral', 'serious man portrait')
    t = text.lower()
    
    women_kw = ['woman', 'women', 'girl', 'she', 'her', 'wife', 'lady',
                'jennifer', 'taylor', 'beyonce', 'selena', 'ariana',
                'kardashian', 'meghan', 'kate', 'melania', 'kamala',
                'actress', 'female', 'mom', 'mother', 'daughter', 'sister',
                'lopez', 'jlo', 'madonna', 'rihanna', 'zendaya']
    is_woman = any(kw in t for kw in women_kw)
    
    if is_woman:
        if any(w in t for w in ['shock', 'shocking', 'stun', 'surprise']):
            return ('shock', 'shocked woman face')
        if any(w in t for w in ['crash', 'crisis', 'disaster', 'panic']):
            return ('fear', 'worried woman stressed')
        if any(w in t for w in ['angry', 'outrage', 'furious']):
            return ('anger', 'angry woman face')
        if any(w in t for w in ['sad', 'tragic', 'cry']):
            return ('sad', 'sad woman portrait')
        if any(w in t for w in ['happy', 'win', 'victory']):
            return ('happy', 'happy woman portrait')
        if any(w in t for w in ['mugshot', 'arrested', 'police']):
            return ('serious', 'woman portrait serious')
        if any(w in t for w in ['glamour', 'celebrity', 'red carpet']):
            return ('curious', 'glamorous woman portrait')
        if any(w in t for w in ['hack', 'cyber', 'leak']):
            return ('serious', 'female hacker portrait')
        return ('neutral', 'woman portrait')
    
    kid_kw = ['kid', 'child', 'boy', 'girl', '7-year', 'young', 'baby', 'teen']
    if any(kw in t for kw in kid_kw):
        return ('happy', 'happy child playing')
    
    if any(w in t for w in ['hack', 'cyber', 'leak', 'security']):
        return ('serious', 'hacker hoodie portrait')
    
    if any(w in t for w in ['shock', 'shocking', 'stun', 'surprise']):
        return ('shock', 'shocked man face')
    if any(w in t for w in ['crash', 'crisis', 'disaster', 'panic']):
        return ('fear', 'worried man stressed')
    if any(w in t for w in ['angry', 'outrage', 'furious', 'fight']):
        return ('anger', 'angry man shouting')
    if any(w in t for w in ['sad', 'tragic', 'death']):
        return ('sad', 'sad man portrait')
    if any(w in t for w in ['war', 'military', 'attack', 'missile']):
        return ('serious', 'serious man portrait')
    if any(w in t for w in ['cost', 'money', 'tariff', 'economy']):
        return ('concerned', 'concerned businessman')
    if any(w in t for w in ['trump', 'biden', 'president', 'congress']):
        return ('serious', 'politician serious portrait')
    if any(w in t for w in ['ai', 'tech', 'robot']):
        return ('curious', 'thinking man portrait')
    if any(w in t for w in ['warning', 'danger', 'alert']):
        return ('alert', 'surprised man portrait')
    if any(w in t for w in ['win', 'victory', 'success']):
        return ('happy', 'happy man portrait')
    if any(w in t for w in ['secret', 'leaked', 'exposed']):
        return ('surprise', 'surprised man portrait')
    if any(w in t for w in ['court', 'law', 'justice']):
        return ('serious', 'serious lawyer portrait')
    
    return ('neutral', 'serious man portrait')


def fetch_human_emotion_image(query):
    import requests
    key = os.getenv("PEXELS_API_KEY", "").strip()
    if not key:
        return None
    try:
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=10&orientation=portrait"
        resp = requests.get(url, headers={"Authorization": key}, timeout=15)
        if resp.status_code != 200:
            return None
        photos = resp.json().get('photos', [])
        if not photos:
            return None
        logger.info(f"   Found {len(photos)} photos for '{query}'")
        random.shuffle(photos)
        for photo in photos[:3]:
            try:
                img_url = (photo.get('src', {}).get('large2x') or
                           photo.get('src', {}).get('large') or
                           photo.get('src', {}).get('portrait'))
                if not img_url:
                    continue
                r = requests.get(img_url, timeout=20)
                if r.status_code != 200:
                    continue
                tmp_path = os.path.join(PATHS['temp'], f"emotion_{random.randint(1,999999)}.jpg")
                with open(tmp_path, 'wb') as f:
                    f.write(r.content)
                img = Image.open(tmp_path).convert('RGB')
                img_ratio = img.width / img.height
                target_ratio = WIDTH / HEIGHT
                if img_ratio > target_ratio:
                    new_h = HEIGHT
                    new_w = int(HEIGHT * img_ratio)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    left = (new_w - WIDTH) // 2
                    img = img.crop((left, 0, left + WIDTH, HEIGHT))
                else:
                    new_w = WIDTH
                    new_h = int(WIDTH / img_ratio)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    top = (new_h - HEIGHT) // 2
                    img = img.crop((0, top, WIDTH, top + HEIGHT))
                try:
                    os.remove(tmp_path)
                except:
                    pass
                return img
            except:
                continue
        return None
    except:
        return None


# ============================================================
# TTS
# ============================================================

def get_tts_voice():
    try:
        from piper import PiperVoice
        import requests
        mp = TTS_CONFIG['model_path']
        cp = TTS_CONFIG['config_path']
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        if not os.path.exists(mp) or os.path.getsize(mp) < 100000:
            r = requests.get(TTS_CONFIG['model_url'], timeout=120)
            if r.status_code == 200 and len(r.content) > 100000:
                with open(mp, 'wb') as f:
                    f.write(r.content)
        if not os.path.exists(cp):
            r = requests.get(TTS_CONFIG['config_url'], timeout=60)
            if r.status_code == 200:
                with open(cp, 'wb') as f:
                    f.write(r.content)
        return PiperVoice.load(mp, cp)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return None


def generate_audio(script_text, voice):
    ap = os.path.join(PATHS['temp'], 'voice.wav')
    os.makedirs(PATHS['temp'], exist_ok=True)
    if not voice:
        return create_silent_audio(ap, 20)
    try:
        chunks = []
        sr = 22050
        try:
            gen = voice.synthesize(script_text, length_scale=1.0,
                                   noise_scale=0.6, noise_w_scale=0.75)
        except TypeError:
            gen = voice.synthesize(script_text)
        for c in gen:
            chunks.append(c)
            sr = c.sample_rate
        if not chunks:
            return create_silent_audio(ap, 20)
        with wave.open(ap, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr)
            for c in chunks:
                wav.writeframes(c.audio_int16_bytes)
        logger.info("Audio generated")
        return ap
    except Exception as e:
        logger.error(f"Audio failed: {e}")
        return create_silent_audio(ap, 20)


def create_silent_audio(path, duration=20):
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                        "-t", str(duration), "-c:a", "pcm_s16le", path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return path
    except:
        return None


# ============================================================
# BEST FRAME
# ============================================================

def analyze_frame_engagement(frame_array):
    try:
        import numpy as np
        img = Image.fromarray(frame_array)
        gray = img.convert('L')
        stat = ImageStat.Stat(gray)
        contrast = stat.stddev[0]
        brightness = stat.mean[0]
        brightness_score = 100 - abs(brightness - 150) * 1.5
        hsv = img.convert('HSV')
        colorfulness = ImageStat.Stat(hsv).stddev[1]
        edges = gray.filter(ImageFilter.FIND_EDGES)
        sharpness = ImageStat.Stat(edges).mean[0]
        w, h = img.size
        center = img.crop((w//4, h//4, 3*w//4, 3*h//4))
        center_contrast = ImageStat.Stat(center.convert('L')).stddev[0]
        np_arr = np.array(center.convert('RGB'))
        r, g, b = np_arr[:,:,0], np_arr[:,:,1], np_arr[:,:,2]
        skin = (r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b) & (abs(r.astype(int)-g.astype(int)) > 15)
        skin_ratio = skin.sum() / max(1, skin.size)
        return (min(100, contrast * 1.8) * 0.20 +
                max(0, brightness_score) * 0.15 +
                min(100, colorfulness * 2.5) * 0.15 +
                min(100, sharpness * 4) * 0.15 +
                min(100, center_contrast * 1.5) * 0.15 +
                min(100, skin_ratio * 500) * 0.20)
    except:
        return 50


def find_best_moment(video_path, num_samples=15):
    try:
        vid = VideoFileClip(video_path, audio=False)
        dur = vid.duration
        if dur < 0.5:
            vid.close()
            return 0.0, 50
        best_ts, best_sc = 0, -1
        for i in range(num_samples):
            ts = i * dur / num_samples
            try:
                sc = analyze_frame_engagement(vid.get_frame(ts))
                if sc > best_sc:
                    best_sc = sc
                    best_ts = ts
            except:
                continue
        vid.close()
        return best_ts, best_sc
    except:
        return 0.0, 50


# ============================================================
# TEXT RENDERING
# ============================================================

def wrap_text_to_width(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def find_best_font_size(text, max_width, max_height, max_lines=3, start_size=62):
    tmp = Image.new('RGB', (10, 10))
    draw = ImageDraw.Draw(tmp)
    for size in range(start_size, 20, -2):
        try:
            font = ImageFont.truetype(FONT_BOLD_ITALIC, size)
        except:
            font = ImageFont.load_default()
        lines = wrap_text_to_width(text, font, max_width, draw)
        if len(lines) <= max_lines:
            total_h = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                total_h += (bbox[3] - bbox[1]) + 8
            if total_h <= max_height:
                return font, lines, size
    try:
        font = ImageFont.truetype(FONT_BOLD_ITALIC, 24)
    except:
        font = ImageFont.load_default()
    lines = wrap_text_to_width(text, font, max_width, draw)
    return font, lines[:max_lines], 24


def make_white_bar(text):
    accent = get_accent_color()
    total_h = WHITE_BAR_HEIGHT
    img = Image.new('RGB', (WIDTH, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y in range(total_h):
        ratio = y / total_h
        shade = int(255 - ratio * 12)
        draw.line([(0, y), (WIDTH, y)], fill=(shade, shade, shade))
    draw.rectangle([0, 0, 18, total_h], fill=accent)
    draw.rectangle([WIDTH - 18, 0, WIDTH, total_h], fill=accent)
    
    text_only = text.strip().upper().rstrip('?').strip()
    if not text_only:
        text_only = "NOBODY SAW THIS COMING"
    
    font, lines, size = find_best_font_size(text_only, WIDTH - 100, total_h - 30, 3, 62)
    logger.info(f"   White bar: {size}px, {len(lines)} lines")
    
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
    
    total_text_h = sum(line_heights) + (len(lines) - 1) * 8
    y_start = (total_h - total_text_h) // 2
    cy = y_start
    for i, line in enumerate(lines[:3]):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        for dx, dy in [(-2, -2), (2, 2)]:
            draw.text((x + dx, cy + dy), line, font=font, fill=(150, 150, 150))
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            draw.text((x + dx, cy + dy), line, font=font, fill=(40, 40, 40))
        draw.text((x, cy), line, font=font, fill=(5, 5, 5))
        cy += line_heights[i] + 8
    
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1,999999)}.png")
    img.save(path, quality=95)
    return path


def create_text_based_first_frame(white_bar_text, topic=""):
    accent = get_accent_color()
    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    emotion, query = detect_emotion_from_text(topic or white_bar_text)
    logger.info(f"   Emotion: {emotion} | Query: '{query}'")
    
    emotion_img = fetch_human_emotion_image(query)
    if emotion_img:
        img = emotion_img.copy()
        overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 160))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay).convert('RGB')
        draw = ImageDraw.Draw(img)
    else:
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(10 + ratio * 30)
            g = int(10 + ratio * 20)
            b = int(40 + ratio * 60)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    shape = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shape)
    sd.polygon([(0, 0), (350, 0), (150, HEIGHT), (0, HEIGHT)],
               fill=(accent[0], accent[1], accent[2], 200))
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, shape).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    text = white_bar_text.strip().upper().rstrip('?').strip()
    if not text:
        text = "NOBODY SAW THIS COMING"
    
    def load_italic(paths, size):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
        return ImageFont.load_default()
    
    italic_fonts = [FONT_BOLD_ITALIC, FONT_BOLD]
    font = None
    lines = []
    max_w = WIDTH - 250
    for size in range(100, 40, -5):
        f = load_italic(italic_fonts, size)
        words = text.split()
        test_lines = []
        current = []
        for word in words:
            test = " ".join(current + [word])
            bbox = draw.textbbox((0, 0), test, font=f)
            w = bbox[2] - bbox[0]
            if w <= max_w:
                current.append(word)
            else:
                if current:
                    test_lines.append(" ".join(current))
                current = [word]
        if current:
            test_lines.append(" ".join(current))
        total_h = len(test_lines) * (size + 20)
        if len(test_lines) <= 3 and total_h <= HEIGHT - 500:
            font = f
            lines = test_lines
            break
    if not font:
        font = load_italic(italic_fonts, 60)
        lines = [text]
    
    line_height = int(font.size * 1.3) if hasattr(font, 'size') else 120
    total_text_h = len(lines) * line_height
    y_start = (HEIGHT - total_text_h) // 2
    for i, line in enumerate(lines[:3]):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2 + 80
        y = y_start + i * line_height
        for dx, dy in [(-5, -5), (5, -5), (-5, 5), (5, 5),
                       (0, -5), (0, 5), (-5, 0), (5, 0)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
    
    draw.rectangle([0, HEIGHT - 40, WIDTH, HEIGHT], fill=accent)
    
    path = os.path.join(PATHS['temp'], f"firstframe_{random.randint(1,999999)}.png")
    img.save(path, quality=95)
    return path


def make_top_strip():
    accent = get_accent_color()
    img = Image.new('RGB', (WIDTH, TOP_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, TOP_BLACK_STRIP - 5, WIDTH, TOP_BLACK_STRIP], fill=accent)
    path = os.path.join(PATHS['temp'], f"top_{random.randint(1,999999)}.png")
    img.save(path, quality=95)
    return path


def make_bottom_strip():
    accent = get_accent_color()
    img = Image.new('RGB', (WIDTH, BOTTOM_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, WIDTH, 5], fill=accent)
    font_cta = load_font(FONT_BOLD, 44)
    draw.text((WIDTH // 2, 70), "SUBSCRIBE FOR MORE",
              font=font_cta, fill=(255, 255, 255), anchor='mm')
    font_sub = load_font(FONT_BOLD, 32)
    draw.text((WIDTH // 2, 140), "New videos daily",
              font=font_sub, fill=(180, 180, 180), anchor='mm')
    path = os.path.join(PATHS['temp'], f"bottom_{random.randint(1,999999)}.png")
    img.save(path, quality=95)
    return path


def make_caption_image(text, fontsize=72, color='#FFFFFF', stroke=7):
    img = Image.new('RGBA', (WIDTH, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(FONT_BOLD, fontsize)
    for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3),(-3,0),(3,0),(0,-3),(0,3)]:
        draw.text((WIDTH//2 + dx, 130 + dy), text, font=font, fill='black', anchor='mm')
    draw.text((WIDTH//2, 130), text, font=font, fill=color, anchor='mm')
    path = os.path.join(PATHS['temp'], f"cap_{random.randint(1,999999)}.png")
    img.save(path)
    return path


def create_gradient_visual(text="", index=0):
    colors = [((10,15,40),(60,30,100)), ((20,10,10),(100,40,30)), ((5,20,30),(30,80,120))]
    c1, c2 = colors[index % len(colors)]
    img = Image.new('RGB', (WIDTH, HEIGHT), c1)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        r = y / HEIGHT
        col = (int(c1[0]*(1-r)+c2[0]*r), int(c1[1]*(1-r)+c2[1]*r), int(c1[2]*(1-r)+c2[2]*r))
        draw.line([(0, y), (WIDTH, y)], fill=col)
    if text:
        font = load_font(FONT_BOLD, 100)
        bbox = draw.textbbox((0,0), text, font=font)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        x = (WIDTH-tw)//2
        y = (HEIGHT-th)//2
        for dx in [-4,0,4]:
            for dy in [-4,0,4]:
                draw.text((x+dx,y+dy), text, font=font, fill=(0,0,0))
        draw.text((x,y), text, font=font, fill=(255,255,255))
    path = os.path.join(PATHS['temp'], f"grad_{random.randint(1,999999)}.png")
    img.save(path)
    return path


# ============================================================
# UPSCALE (8K if short, 4K if long)
# ============================================================

def upscale_to_8k(input_path):
    try:
        # ✅ Check duration - skip 8K if > 18s
        try:
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", input_path
            ], capture_output=True, text=True, timeout=30)
            video_duration = float(probe.stdout.strip()) if probe.stdout.strip() else 20
        except:
            video_duration = 20
        
        if video_duration > 18:
            logger.warning(f"Video {video_duration:.1f}s > 18s - using 4K (memory safe)")
            return upscale_to_4k(input_path)
        
        logger.info("=" * 50)
        logger.info("[8K UPSCALE] Starting...")
        logger.info("=" * 50)
        if not os.path.exists(input_path):
            return input_path
        input_size = os.path.getsize(input_path) / (1024 * 1024)
        logger.info(f"   Input: {input_size:.1f}MB")
        output_8k = input_path.replace('.mp4', '_8k.mp4')
        start = time.time()
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-vf", f"scale={UPSCALE_WIDTH}:{UPSCALE_HEIGHT}:flags=lanczos:force_original_aspect_ratio=decrease",
               "-c:v", "libx264", "-preset", "ultrafast", "-tune", "fastdecode",
               "-crf", "25", "-pix_fmt", "yuv420p", "-threads", "2",
               "-x264-params", "ref=1:bframes=0:me=dia:subme=0:trellis=0:weightp=0",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_8k]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1500)
        elapsed = time.time() - start
        if r.returncode == 0 and os.path.exists(output_8k):
            size = os.path.getsize(output_8k) / (1024 * 1024)
            logger.info(f"[8K] Done in {elapsed:.1f}s | {size:.1f}MB")
            try:
                os.remove(input_path)
            except:
                pass
            os.rename(output_8k, input_path)
            return input_path
        else:
            logger.warning("[8K] Failed - trying 4K")
            if os.path.exists(output_8k):
                try:
                    os.remove(output_8k)
                except:
                    pass
            return upscale_to_4k(input_path)
    except Exception as e:
        logger.error(f"[8K] Error: {e}")
        return upscale_to_4k(input_path)


def upscale_to_4k(input_path):
    """4K fallback for long videos or 8K failure"""
    try:
        logger.info("[4K UPSCALE] Starting...")
        if not os.path.exists(input_path):
            return input_path
        output_4k = input_path.replace('.mp4', '_4k.mp4')
        start = time.time()
        cmd = ["ffmpeg", "-y", "-i", input_path,
               "-vf", "scale=2160:3840:flags=lanczos",
               "-c:v", "libx264", "-preset", "ultrafast", "-tune", "fastdecode",
               "-crf", "23", "-pix_fmt", "yuv420p", "-threads", "2",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_4k]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        elapsed = time.time() - start
        if r.returncode == 0 and os.path.exists(output_4k):
            size = os.path.getsize(output_4k) / (1024 * 1024)
            logger.info(f"[4K] Done in {elapsed:.1f}s | {size:.1f}MB")
            try:
                os.remove(input_path)
            except:
                pass
            os.rename(output_4k, input_path)
            return input_path
        else:
            logger.warning("[4K] Failed - keeping original")
            if os.path.exists(output_4k):
                try:
                    os.remove(output_4k)
                except:
                    pass
            return input_path
    except Exception as e:
        logger.error(f"[4K] Error: {e}")
        return input_path


# ============================================================
# MAIN CREATE
# ============================================================

def create_video(script_data, editor_data=None):
    logger.info("=" * 50)
    logger.info("VIDEO CREATION START")
    logger.info("=" * 50)
    
    os.makedirs(PATHS['output_videos'], exist_ok=True)
    os.makedirs(PATHS['temp'], exist_ok=True)
    
    output_path = os.path.join(PATHS['output_videos'], f"short_{random.randint(1000,9999)}.mp4")
    
    params = get_learned_params()
    target_duration = min(params['duration'], MAX_DURATION)
    clip_density = params['clip_density']
    tts_speed = params['tts_speed']
    
    logger.info(f"Learned: duration={target_duration}s, density={clip_density}s, speed={tts_speed}x")
    
    script_text = (script_data.get('full_script', '') or
                   script_data.get('short_script', '') or
                   "Trending content update.")
    words = script_text.split()
    script_text = " ".join(words[:params['words_target']])
    logger.info(f"Script: {len(script_text.split())} words")
    
    visual_queries = script_data.get('visual_queries', [])
    
    voice = get_tts_voice()
    audio_path = generate_audio(script_text, voice)
    if not audio_path or not os.path.exists(audio_path):
        audio_path = create_silent_audio(os.path.join(PATHS['temp'], 'silent.wav'), target_duration)
    
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    logger.info(f"Audio original: {audio_duration:.2f}s")
    
    if tts_speed != 1.0:
        audio = audio.fx(vfx.speedx, tts_speed)
        audio_duration = audio.duration
        logger.info(f"Audio after {tts_speed}x: {audio_duration:.2f}s")
    
    duration_max = target_duration
    duration_min = max(12, target_duration - 6)
    
    if audio_duration > duration_max:
        audio = audio.subclip(0, duration_max)
        total_duration = duration_max
        logger.info(f"Audio clipped to {duration_max}s")
    elif audio_duration < duration_min:
        total_duration = duration_min
        logger.info(f"Audio padded to {duration_min}s")
    else:
        total_duration = audio_duration
    
    logger.info(f"Final duration: {total_duration:.2f}s")
    
    # Clips calculation with CAP
    first_5_clips = int(FAST_CUT_UNTIL / FAST_CUT_DURATION)
    remaining = max(0, total_duration - FAST_CUT_UNTIL)
    remaining_clips = int(remaining / clip_density) + 2
    clips_needed = first_5_clips + remaining_clips
    
    # ✅ HARD CAP 40
    if clips_needed > MAX_CLIPS:
        logger.warning(f"Clips capped: {clips_needed} -> {MAX_CLIPS}")
        clips_needed = MAX_CLIPS
    
    logger.info(f"Clips needed: {clips_needed}")
    
    visual_paths = []
    if editor_data and editor_data.get('visuals'):
        for v in editor_data['visuals']:
            p = v.get('path') if isinstance(v, dict) else None
            if p and os.path.exists(p):
                visual_paths.append(p)
                if len(visual_paths) >= MAX_CLIPS:
                    break
    
    if len(visual_paths) < clips_needed:
        try:
            from src.media.asset_finder import find_assets_for_script
            need = min(clips_needed - len(visual_paths), MAX_CLIPS)
            new = find_assets_for_script(script_text, num_clips=need, visual_queries=visual_queries)
            for a in new:
                p = a.get('path') if isinstance(a, dict) else None
                if p and os.path.exists(p) and p not in visual_paths:
                    visual_paths.append(p)
                    if len(visual_paths) >= MAX_CLIPS:
                        break
        except Exception as e:
            logger.error(f"Download failed: {e}")
    
    if len(visual_paths) < clips_needed:
        needed = clips_needed - len(visual_paths)
        for i in range(needed):
            visual_paths.append(create_gradient_visual("", i))
            if len(visual_paths) >= MAX_CLIPS:
                break
    
    if not visual_paths:
        for i in range(min(clips_needed, MAX_CLIPS)):
            visual_paths.append(('color', (random.randint(20,50), random.randint(20,50), random.randint(60,100))))
    
    # Hard cap final
    visual_paths = visual_paths[:MAX_CLIPS]
    logger.info(f"Final clips: {len(visual_paths)}")
    
    # Best frame
    best_idx, best_ts, best_sc = 0, 0.0, -1
    for idx, vp in enumerate(visual_paths[:5]):
        if isinstance(vp, str) and os.path.exists(vp) and vp.lower().endswith(('.mp4', '.mov', '.webm')):
            ts, sc = find_best_moment(vp, 12)
            if sc > best_sc:
                best_sc = sc
                best_idx = idx
                best_ts = ts
    
    if best_idx > 0:
        visual_paths.insert(0, visual_paths.pop(best_idx))
    
    # Build clips
    video_clips = []
    current = 0
    idx = 0
    while current < total_duration:
        if current < FAST_CUT_UNTIL:
            dur = min(FAST_CUT_DURATION, FAST_CUT_UNTIL - current, total_duration - current)
        else:
            dur = min(clip_density, total_duration - current)
        if dur <= 0:
            break
        asset = visual_paths[idx % len(visual_paths)]
        try:
            if isinstance(asset, tuple) and asset[0] == 'color':
                sub = ColorClip((WIDTH, HEIGHT), color=asset[1], duration=dur)
            elif isinstance(asset, str) and os.path.exists(asset):
                ext = asset.lower()
                if ext.endswith(('.mp4', '.mov', '.webm', '.avi')):
                    vid = VideoFileClip(asset, audio=False)
                    vid = vid.resize(height=HEIGHT)
                    if vid.w > WIDTH:
                        vid = vid.crop(x_center=vid.w/2, width=WIDTH)
                    elif vid.w < WIDTH:
                        vid = vid.resize(width=WIDTH)
                    if idx == 0 and best_ts > 0:
                        start = best_ts
                    else:
                        mx = max(0, vid.duration - dur)
                        start = random.uniform(0, mx) if mx > 0 else 0
                    end = min(start + dur, vid.duration)
                    sub = vid.subclip(start, end).set_duration(dur)
                elif ext.endswith(('.png', '.jpg', '.jpeg')):
                    sub = ImageClip(asset).set_duration(dur).resize(height=HEIGHT)
                    if sub.w > WIDTH:
                        sub = sub.crop(x_center=sub.w/2, width=WIDTH)
                    elif sub.w < WIDTH:
                        sub = sub.resize(width=WIDTH)
                    sub = sub.resize(lambda t: 1.0 + 0.05*t/dur)
                else:
                    sub = ColorClip((WIDTH, HEIGHT), color=(20,20,50), duration=dur)
            else:
                sub = ColorClip((WIDTH, HEIGHT), color=(20,20,50), duration=dur)
            sub = sub.set_start(current)
            video_clips.append(sub)
        except Exception as e:
            video_clips.append(ColorClip((WIDTH, HEIGHT), color=(30,30,60), duration=dur).set_start(current))
        current += dur
        idx += 1
    
    logger.info(f"Compositing {len(video_clips)} clips")
    
    video_top = TOP_BLACK_STRIP + WHITE_BAR_HEIGHT
    video_h = HEIGHT - video_top - BOTTOM_BLACK_STRIP
    
    adjusted = []
    for clip in video_clips:
        try:
            r = clip.resize(height=video_h)
            if r.w > WIDTH:
                r = r.crop(x_center=r.w/2, width=WIDTH)
            elif r.w < WIDTH:
                r = r.resize(width=WIDTH)
            r = r.set_position((0, video_top))
            adjusted.append(r)
        except:
            adjusted.append(clip)
    
    base = CompositeVideoClip(adjusted, size=(WIDTH, HEIGHT)).set_duration(total_duration)
    
    overlays = []
    overlays.append(ImageClip(make_top_strip()).set_duration(total_duration).set_position((0, 0)))
    
    viral_hook = (script_data.get('viral_hook', '') or
                  script_data.get('title', '')[:60] or
                  "NOBODY SAW THIS COMING")
    topic = script_data.get('title', '') or script_data.get('seo_youtube_title', '')
    logger.info(f"White bar: '{viral_hook}'")
    
    try:
        wb = make_white_bar(viral_hook)
        overlays.append(ImageClip(wb).set_duration(total_duration).set_position((0, TOP_BLACK_STRIP)))
    except Exception as e:
        logger.warning(f"White bar failed: {e}")
    
    overlays.append(ImageClip(make_bottom_strip()).set_duration(total_duration).set_position((0, HEIGHT - BOTTOM_BLACK_STRIP)))
    
    words_list = script_text.split()
    word_dur = total_duration / max(len(words_list), 1)
    red_kw = ['BREAKING','SHOCKING','TRUMP','BIDEN','WAR','DEAD','KILLED','LEAKED',
              'SECRET','FBI','COURT','RUSSIA','UKRAINE','CHINA','MISSILE','STRIKE',
              'USA','AMERICA','CRISIS','EXPOSED','REVEALED','VIRAL']
    
    for i, word in enumerate(words_list):
        st = i * word_dur
        if st >= total_duration:
            break
        is_kw = any(k in word.upper() for k in red_kw)
        color = '#FF0000' if is_kw else '#FFFFFF'
        fs = 78 if is_kw else 68
        try:
            p = make_caption_image(word.upper(), fs, color, 7)
            cap = ImageClip(p).set_duration(word_dur * 1.2).set_start(st)
            cap = cap.set_position(('center', 0.82), relative=True)
            if is_kw:
                cap = cap.resize(lambda t: 1.25 - 0.25*min(1, t/word_dur))
            overlays.append(cap)
        except:
            continue
    
    try:
        ff = create_text_based_first_frame(viral_hook, topic)
        ff_clip = (ImageClip(ff).set_duration(1.0).set_start(0)
                   .resize(lambda t: 1.0 + 0.15*t).set_position('center'))
        overlays.append(ff_clip)
        logger.info("First frame added")
    except Exception as e:
        logger.warning(f"First frame failed: {e}")
    
    logger.info(f"{len(overlays)} overlays")
    
    final = CompositeVideoClip([base] + overlays, size=(WIDTH, HEIGHT)).set_duration(total_duration)
    final = final.set_audio(audio)
    
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    logger.info(f"Writing at {fps} fps")
    
    temp_out = output_path.replace('.mp4', '_raw.mp4')
    final.write_videofile(temp_out, fps=fps, codec='libx264', audio_codec='aac',
                          preset='ultrafast', threads=4, logger=None)
    
    try:
        cmd = ["ffmpeg", "-y", "-i", temp_out,
               "-vf", "noise=alls=5:allf=t,hue=h=2:s=1.08",
               "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
               "-c:a", "aac", "-b:a", "128k", "-r", str(fps), output_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            os.remove(temp_out)
        else:
            os.rename(temp_out, output_path)
    except:
        if os.path.exists(temp_out):
            os.rename(temp_out, output_path)
    
    # Upscale (8K if short, 4K if long)
    output_path = upscale_to_8k(output_path)
    
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], '*.mp4')):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], '*.jpg')):
            os.remove(f)
    except:
        pass
    
    logger.info("=" * 50)
    logger.info(f"VIDEO READY: {output_path}")
    logger.info("=" * 50)
    
    return output_path
