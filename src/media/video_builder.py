"""
src/media/video_builder.py - ULTIMATE ENGAGEMENT EDITION + 8K UPSCALE
- AI-based best frame selection (entire video analysis)
- Bold white bar with auto emoji (no cut text)
- Top black strip with branding
- Bottom black strip with CTA
- Text-based first frame (0.3s) matching white bar
- 8K upscale before upload
"""

import os
import random
import wave
import subprocess
import tempfile
import glob
import re
import time

# Pillow 10+ compatibility
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
if not hasattr(Image, 'BICUBIC'):
    Image.BICUBIC = Image.Resampling.BICUBIC
if not hasattr(Image, 'BILINEAR'):
    Image.BILINEAR = Image.Resampling.BILINEAR
if not hasattr(Image, 'NEAREST'):
    Image.NEAREST = Image.Resampling.NEAREST

# MoviePy 1.x
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, ColorClip,
        CompositeVideoClip, CompositeAudioClip
    )
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    print("[VIDEO_BUILDER] ✅ MoviePy 1.x loaded")
except ImportError as e:
    print(f"[VIDEO_BUILDER] ❌ MoviePy 1.x REQUIRED: {e}")
    raise

from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = VIDEO_CONFIG['WIDTH']       # 1080
HEIGHT = VIDEO_CONFIG['HEIGHT']     # 1920

# LAYOUT
TOP_BLACK_STRIP = 180
WHITE_BAR_HEIGHT = 200
BOTTOM_BLACK_STRIP = 200

# FONTS
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# 8K Resolution
UPSCALE_WIDTH = 4320
UPSCALE_HEIGHT = 7680


def load_font(path, size):
    """Load font safely"""
    try:
        return ImageFont.truetype(path, size)
    except:
        try:
            return ImageFont.truetype(FONT_BOLD, size)
        except:
            return ImageFont.load_default()


# ============================================================
# TTS
# ============================================================

def get_tts_voice():
    try:
        from piper import PiperVoice
        import requests
        model_path = TTS_CONFIG['model_path']
        config_path = TTS_CONFIG['config_path']
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        if not os.path.exists(model_path) or os.path.getsize(model_path) < 100000:
            logger.info("Downloading Piper TTS...")
            r = requests.get(TTS_CONFIG['model_url'], timeout=120)
            if r.status_code == 200 and len(r.content) > 100000:
                with open(model_path, 'wb') as f:
                    f.write(r.content)
        if not os.path.exists(config_path):
            r = requests.get(TTS_CONFIG['config_url'], timeout=60)
            if r.status_code == 200:
                with open(config_path, 'wb') as f:
                    f.write(r.content)
        voice = PiperVoice.load(model_path, config_path)
        logger.info("✅ TTS voice loaded")
        return voice
    except Exception as e:
        logger.error(f"❌ TTS failed: {e}")
        return None


def generate_audio(script_text, voice):
    audio_path = os.path.join(PATHS['temp'], 'voice.wav')
    os.makedirs(PATHS['temp'], exist_ok=True)
    if not voice:
        return create_silent_audio(audio_path, 12)
    try:
        chunks = []
        sr = 22050
        try:
            gen = voice.synthesize(script_text, length_scale=1.25,
                                   noise_scale=0.6, noise_w_scale=0.75)
        except TypeError:
            gen = voice.synthesize(script_text)
        for c in gen:
            chunks.append(c)
            sr = c.sample_rate
        if not chunks:
            return create_silent_audio(audio_path, 12)
        with wave.open(audio_path, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr)
            for c in chunks:
                wav.writeframes(c.audio_int16_bytes)
        logger.info(f"✅ Audio generated")
        return audio_path
    except Exception as e:
        logger.error(f"❌ Audio failed: {e}")
        return create_silent_audio(audio_path, 12)


def create_silent_audio(path, duration=12):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", str(duration), "-c:a", "pcm_s16le", path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return path
    except:
        return None


# ============================================================
# 🤖 AI BEST FRAME SELECTION
# ============================================================

def analyze_frame_engagement(frame_array):
    """Score frame 0-100"""
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
        score = (
            min(100, contrast * 1.8) * 0.20 +
            max(0, brightness_score) * 0.15 +
            min(100, colorfulness * 2.5) * 0.15 +
            min(100, sharpness * 4) * 0.15 +
            min(100, center_contrast * 1.5) * 0.15 +
            min(100, skin_ratio * 500) * 0.20
        )
        return score
    except:
        return 50


def find_best_moment(video_path, num_samples=20):
    """Find best frame in video"""
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
                frame = vid.get_frame(ts)
                sc = analyze_frame_engagement(frame)
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
# 🎯 SMART TEXT SIZING (NO CUT)
# ============================================================

def wrap_text_to_width(text, font, max_width, draw):
    """Wrap text to fit width"""
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


def find_best_font_size(text, max_width, max_height, max_lines=2, start_size=72):
    """Find font size that fits"""
    temp_img = Image.new('RGB', (10, 10))
    draw = ImageDraw.Draw(temp_img)
    
    for size in range(start_size, 24, -2):
        font = load_font(FONT_BOLD, size)
        lines = wrap_text_to_width(text, font, max_width, draw)
        
        if len(lines) <= max_lines:
            total_h = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                total_h += (bbox[3] - bbox[1]) + 10
            if total_h <= max_height:
                return font, lines, size
    
    font = load_font(FONT_BOLD, 32)
    lines = wrap_text_to_width(text, font, max_width, draw)
    return font, lines[:max_lines], 32


# ============================================================
# 🎨 TOP BLACK STRIP (BRANDING)
# ============================================================

def make_top_black_strip():
    """Top black strip with branding"""
    img = Image.new('RGB', (WIDTH, TOP_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Red accent line at bottom
    draw.rectangle([0, TOP_BLACK_STRIP - 5, WIDTH, TOP_BLACK_STRIP], fill=(220, 30, 30))
    
    # Channel name (left)
    font_ch = load_font(FONT_BOLD, 42)
    draw.text((30, TOP_BLACK_STRIP // 2), "UNCOVERED USA",
              font=font_ch, fill=(255, 255, 255), anchor='lm')
    
    # LIVE dot (right)
    dot_x = WIDTH - 180
    dot_y = TOP_BLACK_STRIP // 2
    draw.ellipse([dot_x - 12, dot_y - 12, dot_x + 12, dot_y + 12], fill=(255, 30, 30))
    
    font_live = load_font(FONT_BOLD, 38)
    draw.text((dot_x + 25, dot_y), "LIVE", font=font_live,
              fill=(255, 255, 255), anchor='lm')
    
    path = os.path.join(PATHS['temp'], f"top_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# 🎨 WHITE BAR (AUTO-FIT TEXT + BOLD + EMOJI)
# ============================================================

def make_white_bar(text, topic=""):
    """
    FINAL white bar:
    - Auto font size (no cut)
    - Bold with thick shadow
    - Emoji at end
    - Red accent bars
    """
    total_h = WHITE_BAR_HEIGHT
    img = Image.new('RGB', (WIDTH, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Gradient
    for y in range(total_h):
        ratio = y / total_h
        shade = int(255 - ratio * 12)
        draw.line([(0, y), (WIDTH, y)], fill=(shade, shade, shade))
    
    # Red accent bars
    draw.rectangle([0, 0, 18, total_h], fill=(220, 30, 30))
    draw.rectangle([WIDTH - 18, 0, WIDTH, total_h], fill=(220, 30, 30))
    
    # Emoji split
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+",
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    text_only = emoji_pattern.sub('', text).strip().upper()
    
    # Auto emoji if missing
    if not emojis:
        tl = topic.lower() if topic else text_only.lower()
        if any(w in tl for w in ['war', 'military', 'strike', 'missile', 'attack']):
            emojis = ["⚔️"]
        elif any(w in tl for w in ['tariff', 'trade', 'economy', 'money']):
            emojis = ["💰"]
        elif any(w in tl for w in ['trump', 'biden', 'congress', 'white house']):
            emojis = ["🏛️"]
        elif any(w in tl for w in ['ai', 'tech', 'robot']):
            emojis = ["🤖"]
        elif any(w in tl for w in ['secret', 'leaked', 'classified']):
            emojis = ["🔒"]
        elif any(w in tl for w in ['crash', 'drop', 'fall']):
            emojis = ["📉"]
        elif any(w in tl for w in ['court', 'law', 'justice']):
            emojis = ["⚖️"]
        elif any(w in tl for w in ['warning', 'danger', 'risk']):
            emojis = ["⚠️"]
        else:
            emojis = ["🚨"]
    
    emoji_char = emojis[0]
    full_text = text_only + " " + emoji_char
    
    max_text_width = WIDTH - 80
    max_text_height = total_h - 40
    
    font, lines, size = find_best_font_size(
        full_text, max_text_width, max_text_height, max_lines=2, start_size=76
    )
    
    logger.info(f"   White bar font: {size}px, {len(lines)} lines")
    
    if len(lines) == 1:
        line = lines[0]
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = (total_h - th) // 2
        
        # Shadow
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(180, 180, 180))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(80, 80, 80))
        draw.text((x, y), line, font=font, fill=(10, 10, 10))
    
    else:
        line_h = max_text_height // 2
        for i, line in enumerate(lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (WIDTH - tw) // 2
            y = 20 + i * line_h
            
            for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
                draw.text((x + dx, y + dy), line, font=font, fill=(180, 180, 180))
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((x + dx, y + dy), line, font=font, fill=(80, 80, 80))
            draw.text((x, y), line, font=font, fill=(10, 10, 10))
    
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# 🎯 FIRST FRAME (Based on White Bar Text) - 0.3 second
# ============================================================

def create_text_based_first_frame(white_bar_text, topic=""):
    """
    Create a first frame that matches the white bar text
    - Large text on dark gradient background
    - Accent color shape
    - Auto emoji
    """
    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Dark gradient background
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(10 + ratio * 30)
        g = int(10 + ratio * 20)
        b = int(40 + ratio * 60)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Big diagonal accent shape (left side)
    draw.polygon(
        [(0, 0), (350, 0), (150, HEIGHT), (0, HEIGHT)],
        fill=(220, 30, 30)
    )
    
    # Text = white bar text
    text = white_bar_text.upper().strip()
    
    # Font auto-size
    temp_img = Image.new('RGB', (10, 10))
    temp_draw = ImageDraw.Draw(temp_img)
    
    font = None
    lines = []
    
    for size in range(150, 40, -5):
        try:
            f = ImageFont.truetype(FONT_BOLD, size)
        except:
            f = ImageFont.load_default()
        
        # Wrap text
        words = text.split()
        test_lines = []
        current = []
        
        for word in words:
            test = " ".join(current + [word])
            bbox = temp_draw.textbbox((0, 0), test, font=f)
            w = bbox[2] - bbox[0]
            if w <= WIDTH - 250:
                current.append(word)
            else:
                if current:
                    test_lines.append(" ".join(current))
                current = [word]
        if current:
            test_lines.append(" ".join(current))
        
        # Check total height
        total_h = len(test_lines) * (size + 20)
        if total_h <= HEIGHT - 600:
            font = f
            lines = test_lines
            break
    
    if not font:
        font = ImageFont.load_default()
        lines = [text[:20]]
    
    # Draw text
    line_height = int(font.size * 1.3) if hasattr(font, 'size') else 120
    total_text_h = len(lines) * line_height
    y_start = (HEIGHT - total_text_h) // 2
    
    for i, line in enumerate(lines[:3]):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2 + 80  # Offset for accent shape
        
        y = y_start + i * line_height
        
        # Thick shadow
        for dx, dy in [(-6, -6), (6, -6), (-6, 6), (6, 6), 
                       (0, -6), (0, 6), (-6, 0), (6, 0)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0))
        
        # Main
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
    
    # Bottom red accent bar
    draw.rectangle([0, HEIGHT - 40, WIDTH, HEIGHT], fill=(220, 30, 30))
    
    path = os.path.join(PATHS['temp'], f"firstframe_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    logger.info(f"   🎯 First frame created")
    return path


# ============================================================
# 🎨 BOTTOM BLACK STRIP
# ============================================================

def make_bottom_black_strip():
    """Bottom strip with CTA"""
    img = Image.new('RGB', (WIDTH, BOTTOM_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Red line at top
    draw.rectangle([0, 0, WIDTH, 5], fill=(220, 30, 30))
    
    # Subscribe text
    font_cta = load_font(FONT_BOLD, 44)
    draw.text((WIDTH // 2, 70), "SUBSCRIBE FOR MORE",
              font=font_cta, fill=(255, 255, 255), anchor='mm')
    
    font_sub = load_font(FONT_BOLD, 32)
    draw.text((WIDTH // 2, 140), "New videos every 6 hours",
              font=font_sub, fill=(180, 180, 180), anchor='mm')
    
    path = os.path.join(PATHS['temp'], f"bottom_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# CAPTIONS
# ============================================================

def make_caption_image(text, fontsize=72, color='#FFFFFF', stroke=7):
    """Caption with thick outline"""
    img = Image.new('RGBA', (WIDTH, 260), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(FONT_BOLD, fontsize)
    
    # Thick black outline
    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3),
                   (-3, 0), (3, 0), (0, -3), (0, 3)]:
        draw.text((WIDTH//2 + dx, 130 + dy), text, font=font,
                  fill='black', anchor='mm')
    
    # Color fill
    draw.text((WIDTH//2, 130), text, font=font,
              fill=color, anchor='mm')
    
    path = os.path.join(PATHS['temp'], f"cap_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


# ============================================================
# GRADIENT FALLBACK
# ============================================================

def create_gradient_visual(text="", index=0):
    colors = [
        ((10, 15, 40), (60, 30, 100)),
        ((20, 10, 10), (100, 40, 30)),
        ((5, 20, 30), (30, 80, 120)),
        ((15, 15, 15), (60, 60, 60)),
        ((30, 20, 5), (120, 80, 20)),
    ]
    c1, c2 = colors[index % len(colors)]
    
    img = Image.new('RGB', (WIDTH, HEIGHT), c1)
    draw = ImageDraw.Draw(img)
    
    for y in range(HEIGHT):
        r = y / HEIGHT
        col = (
            int(c1[0]*(1-r) + c2[0]*r),
            int(c1[1]*(1-r) + c2[1]*r),
            int(c1[2]*(1-r) + c2[2]*r),
        )
        draw.line([(0, y), (WIDTH, y)], fill=col)
    
    if text:
        font = load_font(FONT_BOLD, 100)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = (HEIGHT - th) // 2
        for dx in [-4, 0, 4]:
            for dy in [-4, 0, 4]:
                draw.text((x+dx, y+dy), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    path = os.path.join(PATHS['temp'], f"grad_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


# ============================================================
# 🎬 8K UPSCALE (Before Upload)
# ============================================================

def upscale_to_8k(input_path):
    """
    Upscale video to 8K (7680x4320)
    Uses FFmpeg lanczos for best quality
    """
    try:
        logger.info("=" * 50)
        logger.info("🎬 [8K UPSCALE] Starting...")
        logger.info("=" * 50)
        
        if not os.path.exists(input_path):
            logger.error(f"[8K] File not found: {input_path}")
            return input_path
        
        input_size = os.path.getsize(input_path) / (1024 * 1024)
        logger.info(f"   Input size: {input_size:.1f}MB")
        
        output_8k = input_path.replace('.mp4', '_8k.mp4')
        
        # Get duration
        try:
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", input_path
            ], capture_output=True, text=True, timeout=30)
            duration = float(probe.stdout.strip()) if probe.stdout.strip() else 12
            logger.info(f"   Duration: {duration:.1f}s")
        except:
            duration = 12
        
        start_time = time.time()
        
        # 8K upscale command (lanczos = highest quality)
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-vf", f"scale={UPSCALE_WIDTH}:{UPSCALE_HEIGHT}:flags=lanczos",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_8k
        ]
        
        logger.info(f"   Running FFmpeg 8K upscale...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900  # 15 min max
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0 and os.path.exists(output_8k):
            output_size = os.path.getsize(output_8k) / (1024 * 1024)
            logger.info(f"✅ [8K UPSCALE] Done in {elapsed:.1f}s")
            logger.info(f"   Output size: {output_size:.1f}MB")
            
            # Replace original with 8K
            try:
                os.remove(input_path)
            except:
                pass
            os.rename(output_8k, input_path)
            
            return input_path
        else:
            err = result.stderr[-300:] if result.stderr else 'unknown'
            logger.warning(f"❌ [8K UPSCALE] Failed: {err}")
            # Clean up partial file
            if os.path.exists(output_8k):
                try:
                    os.remove(output_8k)
                except:
                    pass
            return input_path
    
    except subprocess.TimeoutExpired:
        logger.error("❌ [8K UPSCALE] Timeout (15 min)")
        return input_path
    except Exception as e:
        logger.error(f"❌ [8K UPSCALE] Error: {e}")
        return input_path


# ============================================================
# 🎬 MAIN VIDEO CREATION
# ============================================================

def create_video(script_data, editor_data=None):
    logger.info("=" * 50)
    logger.info("🎬 VIDEO CREATION START")
    logger.info("=" * 50)
    
    os.makedirs(PATHS['output_videos'], exist_ok=True)
    os.makedirs(PATHS['temp'], exist_ok=True)
    
    output_path = os.path.join(
        PATHS['output_videos'],
        f"short_{random.randint(1000, 9999)}.mp4"
    )
    
    # ============================================================
    # SCRIPT
    # ============================================================
    
    script_text = (
        script_data.get('full_script', '') or
        script_data.get('short_script', '') or
        "Breaking news update."
    )
    words = script_text.split()[:VIDEO_CONFIG['WORDS_TARGET']]
    script_text = " ".join(words)
    logger.info(f"📝 Script: {len(words)} words")
    
    # ============================================================
    # TTS
    # ============================================================
    
    voice = get_tts_voice()
    audio_path = generate_audio(script_text, voice)
    if not audio_path or not os.path.exists(audio_path):
        audio_path = create_silent_audio(os.path.join(PATHS['temp'], 'silent.wav'), 12)
    
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    speed = VIDEO_CONFIG.get('TTS_SPEED', 1.0)
    if speed != 1.0:
        audio = audio.fx(vfx.speedx, speed)
        total_duration = audio.duration
    total_duration = max(VIDEO_CONFIG['DURATION_MIN'], min(VIDEO_CONFIG['DURATION_MAX'], total_duration))
    logger.info(f"⏱️ Duration: {total_duration:.1f}s")
    
    # ============================================================
    # VISUALS
    # ============================================================
    
    clips_needed = int(total_duration / VIDEO_CONFIG['CLIP_DENSITY']) + 2
    logger.info(f"📊 Clips needed: {clips_needed}")
    
    visual_paths = []
    if editor_data and editor_data.get('visuals'):
        for v in editor_data['visuals']:
            p = v.get('path') if isinstance(v, dict) else None
            if p and os.path.exists(p):
                visual_paths.append(p)
        logger.info(f"Editor: {len(visual_paths)} clips")
    
    if len(visual_paths) < clips_needed:
        try:
            from src.media.asset_finder import find_assets_for_script
            new = find_assets_for_script(script_text, num_clips=clips_needed)
            for a in new:
                p = a.get('path') if isinstance(a, dict) else None
                if p and os.path.exists(p) and p not in visual_paths:
                    visual_paths.append(p)
            logger.info(f"After download: {len(visual_paths)}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
    
    if len(visual_paths) < clips_needed:
        needed = clips_needed - len(visual_paths)
        logger.warning(f"🚨 Generating {needed} fallback")
        script_words = script_text.split()
        for i in range(needed):
            text = script_words[i % len(script_words)].upper() if script_words else ""
            visual_paths.append(create_gradient_visual(text, i))
    
    if not visual_paths:
        for i in range(clips_needed):
            color = (random.randint(20, 50), random.randint(20, 50), random.randint(60, 100))
            visual_paths.append(('color', color))
    
    logger.info(f"✅ FINAL: {len(visual_paths)} clips")
    
    # ============================================================
    # 🤖 AI BEST FRAME SELECTION
    # ============================================================
    
    logger.info("🎯 Finding best moment...")
    best_idx, best_ts, best_sc = 0, 0.0, -1
    
    for idx, vp in enumerate(visual_paths[:6]):
        if isinstance(vp, str) and os.path.exists(vp) and vp.lower().endswith(('.mp4', '.mov', '.webm')):
            ts, sc = find_best_moment(vp, 15)
            if sc > best_sc:
                best_sc = sc
                best_idx = idx
                best_ts = ts
                logger.info(f"   Clip {idx}: {ts:.2f}s (score: {sc:.1f}) ⭐")
    
    if best_idx > 0:
        visual_paths.insert(0, visual_paths.pop(best_idx))
        logger.info(f"🔄 Winner moved to first")
    
    # ============================================================
    # BUILD CLIPS
    # ============================================================
    
    video_clips = []
    current = 0
    idx = 0
    density = VIDEO_CONFIG['CLIP_DENSITY']
    
    while current < total_duration:
        dur = min(density, total_duration - current)
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
                    sub = ColorClip((WIDTH, HEIGHT), color=(20, 20, 50), duration=dur)
            else:
                sub = ColorClip((WIDTH, HEIGHT), color=(20, 20, 50), duration=dur)
            sub = sub.set_start(current)
            video_clips.append(sub)
        except Exception as e:
            logger.warning(f"Clip {idx} failed: {e}")
            video_clips.append(ColorClip((WIDTH, HEIGHT), color=(30, 30, 60), duration=dur).set_start(current))
        
        current += dur
        idx += 1
    
    logger.info(f"🎞️ Compositing {len(video_clips)} clips...")
    
    # LAYOUT
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
    
    # ============================================================
    # OVERLAYS
    # ============================================================
    
    overlays = []
    
    # 1. Top black strip
    overlays.append(ImageClip(make_top_black_strip()).set_duration(total_duration).set_position((0, 0)))
    
    # 2. White bar
    viral_hook = (
        script_data.get('viral_hook', '') or
        script_data.get('title', '')[:40] or
        "BREAKING NEWS"
    )
    topic = script_data.get('title', '') or script_data.get('seo_youtube_title', '')
    logger.info(f"🎨 White bar: '{viral_hook}'")
    
    try:
        wb = make_white_bar(viral_hook, topic)
        overlays.append(ImageClip(wb).set_duration(total_duration).set_position((0, TOP_BLACK_STRIP)))
    except Exception as e:
        logger.warning(f"White bar failed: {e}")
    
    # 3. 🎯 FIRST FRAME (0.3 sec) - Based on White Bar Text
    try:
        first_frame_img = create_text_based_first_frame(viral_hook, topic)
        first_frame_clip = (
            ImageClip(first_frame_img)
            .set_duration(0.3)
            .set_start(0)
            .set_position((0, 0))
        )
        overlays.append(first_frame_clip)
        logger.info("🎯 First frame (0.3s) added")
    except Exception as e:
        logger.warning(f"First frame failed: {e}")
    
    # 4. Bottom strip
    overlays.append(ImageClip(make_bottom_black_strip()).set_duration(total_duration).set_position((0, HEIGHT - BOTTOM_BLACK_STRIP)))
    
    # 5. Captions
    words = script_text.split()
    word_dur = total_duration / max(len(words), 1)
    red_kw = [
        'BREAKING','SHOCKING','TRUMP','BIDEN','WAR','DEAD','KILLED','LEAKED',
        'SECRET','FBI','COURT','RUSSIA','UKRAINE','CHINA','MISSILE','STRIKE',
        'POLAND','NATO','USA','AMERICA','CRISIS','EXPOSED','REVEALED'
    ]
    
    for i, word in enumerate(words):
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
    
    logger.info(f"✅ {len(overlays)} overlays")
    
    # ============================================================
    # FINAL COMPOSITE
    # ============================================================
    
    final = CompositeVideoClip([base] + overlays, size=(WIDTH, HEIGHT)).set_duration(total_duration)
    final = final.set_audio(audio)
    
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    logger.info(f"💾 Writing at {fps} fps...")
    
    temp_out = output_path.replace('.mp4', '_raw.mp4')
    
    final.write_videofile(
        temp_out,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    logger.info(f"✅ Raw written")
    
    # ============================================================
    # FFMPEG FILTER (noise + hue)
    # ============================================================
    
    logger.info("🎨 FFmpeg filters...")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_out,
            "-vf", "noise=alls=5:allf=t,hue=h=2:s=1.08",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(fps),
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            os.remove(temp_out)
            logger.info(f"✅ FFmpeg applied")
        else:
            logger.warning(f"FFmpeg failed")
            os.rename(temp_out, output_path)
    except Exception as e:
        logger.warning(f"FFmpeg error: {e}")
        if os.path.exists(temp_out):
            os.rename(temp_out, output_path)
    
    # ============================================================
    # 🎬 8K UPSCALE (Before Return)
    # ============================================================
    
    logger.info("🎬 16K upscale for upload...")
    output_path = upscale_to_16k(output_path)
    
    # Cleanup
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], '*.mp4')):
            os.remove(f)
    except:
        pass
    
    logger.info("=" * 50)
    logger.info(f"🎉 VIDEO READY (16K): {output_path}")
    logger.info("=" * 50)
    
    return output_path
