"""
src/media/video_builder.py - ULTIMATE ENGAGEMENT EDITION
- AI-based best frame selection (entire video analysis)
- Bold white bar with auto emoji
- Top black strip 200px + Bottom black strip 200px
"""

import os
import random
import wave
import subprocess
import tempfile
import glob
import re

# 🚨 CRITICAL FIX: Pillow 10+ compatibility for MoviePy 1.0.3
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS
if not hasattr(Image, 'BICUBIC'):
    Image.BICUBIC = Image.Resampling.BICUBIC
if not hasattr(Image, 'BILINEAR'):
    Image.BILINEAR = Image.Resampling.BILINEAR
if not hasattr(Image, 'NEAREST'):
    Image.NEAREST = Image.Resampling.NEAREST

# HARD CHECK: MoviePy 1.x
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

WIDTH = VIDEO_CONFIG['WIDTH']
HEIGHT = VIDEO_CONFIG['HEIGHT']

# NEW LAYOUT
TOP_BLACK_STRIP = 200
WHITE_BAR_HEIGHT = 210
BOTTOM_BLACK_STRIP = 200


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
        return create_silent_audio(audio_path, duration=12)
    
    try:
        audio_chunks = []
        sample_rate = 22050
        
        try:
            gen = voice.synthesize(script_text, length_scale=1.25,
                                   noise_scale=0.6, noise_w_scale=0.75)
        except TypeError:
            gen = voice.synthesize(script_text)
        
        for chunk in gen:
            audio_chunks.append(chunk)
            sample_rate = chunk.sample_rate
        
        if not audio_chunks:
            return create_silent_audio(audio_path, duration=12)
        
        with wave.open(audio_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for chunk in audio_chunks:
                wav.writeframes(chunk.audio_int16_bytes)
        
        logger.info(f"✅ Audio generated")
        return audio_path
    except Exception as e:
        logger.error(f"❌ Audio failed: {e}")
        return create_silent_audio(audio_path, duration=12)


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
# 🎯 AI-BASED BEST FRAME SELECTION
# ============================================================

def analyze_frame_engagement(frame_array):
    """
    Score a single frame for engagement (0-100)
    Higher = better for CTR
    """
    try:
        import numpy as np
        
        img = Image.fromarray(frame_array)
        gray = img.convert('L')
        
        # 1. Contrast (std dev of grayscale)
        stat = ImageStat.Stat(gray)
        contrast = stat.stddev[0]
        
        # 2. Brightness (optimal 120-180)
        brightness = stat.mean[0]
        brightness_score = 100 - abs(brightness - 150) * 1.5
        
        # 3. Colorfulness (saturation variance)
        hsv = img.convert('HSV')
        hsv_stat = ImageStat.Stat(hsv)
        colorfulness = hsv_stat.stddev[1]
        
        # 4. Edge density (sharpness)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        sharpness = edge_stat.mean[0]
        
        # 5. Center-weighted interest (subjects usually centered)
        w, h = img.size
        center = img.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
        center_stat = ImageStat.Stat(center.convert('L'))
        center_contrast = center_stat.stddev[0]
        
        # 6. Face detection (skin tone heuristic)
        np_arr = np.array(center.convert('RGB'))
        r, g, b = np_arr[:, :, 0], np_arr[:, :, 1], np_arr[:, :, 2]
        skin_mask = (
            (r > 95) & (g > 40) & (b > 20) &
            (r > g) & (r > b) & (abs(r.astype(int) - g.astype(int)) > 15)
        )
        skin_ratio = skin_mask.sum() / max(1, skin_mask.size)
        
        # Weighted score
        score = (
            min(100, contrast * 1.8) * 0.20 +          # Contrast
            max(0, brightness_score) * 0.15 +           # Brightness
            min(100, colorfulness * 2.5) * 0.15 +       # Color
            min(100, sharpness * 4) * 0.15 +            # Sharpness
            min(100, center_contrast * 1.5) * 0.15 +    # Center
            min(100, skin_ratio * 500) * 0.20           # Face
        )
        
        return score
    except Exception as e:
        return 50


def find_best_moment_across_video(video_path, num_samples=30):
    """
    Analyze entire video, find single most engaging moment
    Returns: (best_timestamp, best_score, all_scores)
    """
    try:
        vid = VideoFileClip(video_path, audio=False)
        duration = vid.duration
        
        if duration < 0.5:
            vid.close()
            return 0.0, 50, []
        
        timestamps = [i * duration / num_samples for i in range(num_samples)]
        
        scores = []
        best_score = -1
        best_timestamp = 0
        
        for ts in timestamps:
            try:
                frame = vid.get_frame(ts)
                score = analyze_frame_engagement(frame)
                scores.append((ts, score))
                
                if score > best_score:
                    best_score = score
                    best_timestamp = ts
            except:
                continue
        
        vid.close()
        
        logger.info(f"🎯 Analyzed {len(scores)} frames")
        logger.info(f"🎯 Best: {best_timestamp:.2f}s (score: {best_score:.1f})")
        
        # Log top 3
        sorted_moments = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
        for ts, sc in sorted_moments:
            logger.info(f"   → {ts:.2f}s: {sc:.1f}")
        
        return best_timestamp, best_score, scores
    
    except Exception as e:
        logger.warning(f"Analysis failed: {e}")
        return 0.0, 50, []


def find_best_frame_from_video(video_path, num_samples=30):
    """Wrapper"""
    ts, score, _ = find_best_moment_across_video(video_path, num_samples)
    return ts, score


# ============================================================
# 🎨 BOLD WHITE BAR WITH AUTO EMOJI
# ============================================================

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"   # Symbols & Pictographs
    "\U0001F600-\U0001F64F"   # Emoticons
    "\U0001F680-\U0001F6FF"   # Transport
    "\U0001F700-\U0001F77F"   # Alchemical
    "\U0001F780-\U0001F7FF"   # Geometric
    "\U0001F800-\U0001F8FF"   # Supplemental Arrows
    "\U0001F900-\U0001F9FF"   # Supplemental Symbols
    "\U0001FA00-\U0001FA6F"   # Chess
    "\U0001FA70-\U0001FAFF"   # Symbols Extended
    "\U00002600-\U000026FF"   # Misc Symbols
    "\U00002700-\U000027BF"   # Dingbats
    "\U0001F1E0-\U0001F1FF"   # Flags
    "]+", flags=re.UNICODE
)


def auto_select_emoji(topic):
    """Auto-select best emoji based on topic"""
    t = topic.lower()
    
    if any(w in t for w in ['war', 'military', 'strike', 'missile', 'attack', 'invasion']):
        return "⚔️"
    if any(w in t for w in ['tariff', 'trade', 'economy', 'money', 'dollar', 'cost', 'price']):
        return "💰"
    if any(w in t for w in ['trump', 'biden', 'congress', 'senate', 'white house', 'president']):
        return "🏛️"
    if any(w in t for w in ['ai', 'tech', 'robot', 'artificial', 'chatgpt', 'google', 'apple']):
        return "🤖"
    if any(w in t for w in ['secret', 'leaked', 'classified', 'hidden', 'exposed']):
        return "🔒"
    if any(w in t for w in ['crash', 'drop', 'fall', 'plunge', 'slump']):
        return "📉"
    if any(w in t for w in ['rise', 'surge', 'grow', 'soar', 'jump']):
        return "📈"
    if any(w in t for w in ['court', 'law', 'justice', 'supreme']):
        return "⚖️"
    if any(w in t for w in ['ban', 'blocked', 'banned', 'refused']):
        return "🚫"
    if any(w in t for w in ['global', 'world', 'international']):
        return "🌍"
    if any(w in t for w in ['warning', 'danger', 'risk', 'threat']):
        return "⚠️"
    if any(w in t for w in ['win', 'victory', 'triumph']):
        return "🏆"
    if any(w in t for w in ['watch', 'look', 'see', 'view']):
        return "👀"
    
    return "🚨"


def make_engaging_white_bar(text, topic=""):
    """
    ULTRA BOLD white bar with emoji
    - Maximum font weight
    - Auto emoji
    - Strong accent colors
    """
    total_height = TOP_BLACK_STRIP + WHITE_BAR_HEIGHT
    
    img = Image.new('RGB', (WIDTH, total_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Random accent color
    accents = [
        (255, 215, 0),    # Gold
        (255, 30, 30),    # Red
        (0, 200, 255),    # Cyan
        (50, 255, 100),   # Green
        (255, 80, 200),   # Pink
        (255, 130, 0),    # Orange
        (200, 0, 255),    # Purple
    ]
    accent_color = random.choice(accents)
    
    # White bar gradient
    for y in range(WHITE_BAR_HEIGHT):
        ratio = y / WHITE_BAR_HEIGHT
        r = int(255 - ratio * 15)
        g = int(255 - ratio * 15)
        b = int(255 - ratio * 15)
        draw.line(
            [(0, TOP_BLACK_STRIP + y), (WIDTH, TOP_BLACK_STRIP + y)],
            fill=(r, g, b)
        )
    
    # Thick accent bars (25px)
    draw.rectangle(
        [0, TOP_BLACK_STRIP, 25, TOP_BLACK_STRIP + WHITE_BAR_HEIGHT],
        fill=accent_color
    )
    draw.rectangle(
        [WIDTH - 25, TOP_BLACK_STRIP, WIDTH, TOP_BLACK_STRIP + WHITE_BAR_HEIGHT],
        fill=accent_color
    )
    
    # ============================================================
    # EMOJI HANDLING
    # ============================================================
    
    # Check if emoji exists
    if not EMOJI_PATTERN.search(text):
        # Auto-add emoji
        emoji = auto_select_emoji(topic or text)
        text = text.strip() + " " + emoji
        logger.info(f"   Auto-emoji added: {emoji}")
    
    # Split text without removing emoji
    text_clean = text.strip()
    
    # ============================================================
    # SPLIT INTO LINES (keep emoji)
    # ============================================================
    
    # Remove emoji temporarily to count words
    text_no_emoji = EMOJI_PATTERN.sub('', text_clean).strip()
    emojis_found = EMOJI_PATTERN.findall(text_clean)
    
    words = text_no_emoji.split()
    
    if len(words) >= 4:
        mid = (len(words) + 1) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        
        # Add emoji to second line
        if emojis_found:
            line2 = line2 + " " + "".join(emojis_found)
        
        lines = [line1, line2]
    elif len(words) >= 2:
        lines = [text_no_emoji + " " + "".join(emojis_found) if emojis_found else text_no_emoji]
    else:
        lines = [text_clean]
    
    # ============================================================
    # FONT LOADING
    # ============================================================
    
    bold_font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    def load_font(paths, size):
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
        return ImageFont.load_default()
    
    text_color = (5, 5, 5)
    
    # ============================================================
    # RENDER
    # ============================================================
    
    if len(lines) == 1:
        # Single line - BIG font
        font = load_font(bold_font_paths, 76)
        
        bbox = draw.textbbox((0, 0), lines[0], font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = TOP_BLACK_STRIP + (WHITE_BAR_HEIGHT - th) // 2
        
        # Strong shadow (4 directions)
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
            draw.text((x + dx, y + dy), lines[0], font=font, fill=(140, 140, 140))
        
        # Main
        draw.text((x, y), lines[0], font=font, fill=text_color)
    
    else:
        # Two lines
        font = load_font(bold_font_paths, 58)
        
        for i, line in enumerate(lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (WIDTH - tw) // 2
            y = TOP_BLACK_STRIP + 30 + i * 82
            
            # Strong shadow
            for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
                draw.text((x + dx, y + dy), line, font=font, fill=(140, 140, 140))
            
            # Main
            draw.text((x, y), line, font=font, fill=text_color)
    
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# BOTTOM BLACK STRIP
# ============================================================

def make_bottom_black_strip():
    """Create bottom black strip"""
    img = Image.new('RGB', (WIDTH, BOTTOM_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    path = os.path.join(PATHS['temp'], f"bottom_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# CAPTION TEXT IMAGE
# ============================================================

def make_text_image(text, fontsize=70, color='white', stroke=6):
    img = Image.new('RGBA', (WIDTH, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize
        )
    except:
        font = ImageFont.load_default()
    
    # Shadow
    draw.text(
        (WIDTH // 2 + 3, 153), text,
        font=font, fill=(0, 0, 0, 180),
        stroke_width=stroke + 2, stroke_fill='black',
        anchor='mm'
    )
    
    # Main
    draw.text(
        (WIDTH // 2, 150), text,
        font=font, fill=color,
        stroke_width=stroke, stroke_fill='black',
        anchor='mm'
    )
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"txt_{random.randint(1, 999999)}.png")
    img.save(path)
    return path


# ============================================================
# GRADIENT FALLBACK
# ============================================================

def create_gradient_image(path, color1, color2, text=""):
    img = Image.new('RGB', (WIDTH, HEIGHT), color1)
    draw = ImageDraw.Draw(img)
    
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    if text:
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90
            )
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = (HEIGHT - th) // 2
        
        for dx in [-4, 0, 4]:
            for dy in [-4, 0, 4]:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    img.save(path)
    return path


def create_generated_visuals(script_text, num=15):
    logger.info(f"🎨 Generating {num} gradient visuals")
    visuals = []
    words = script_text.split()
    
    color_pairs = [
        ((10, 15, 40), (60, 30, 100)),
        ((20, 10, 10), (100, 40, 30)),
        ((5, 20, 30), (30, 80, 120)),
        ((15, 15, 15), (60, 60, 60)),
        ((30, 20, 5), (120, 80, 20)),
    ]
    
    for i in range(num):
        color1, color2 = random.choice(color_pairs)
        text = words[i].upper() if i < len(words) else ""
        path = os.path.join(PATHS['temp'], f"grad_{random.randint(1, 999999)}.png")
        create_gradient_image(path, color1, color2, text)
        visuals.append(path)
    
    return visuals


# ============================================================
# MAIN VIDEO CREATION
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
    
    # SCRIPT
    script_text = (
        script_data.get('full_script', '') or
        script_data.get('short_script', '') or
        "Breaking news update. This is a developing story."
    )
    
    words = script_text.split()[:VIDEO_CONFIG['WORDS_TARGET']]
    script_text = " ".join(words)
    logger.info(f"📝 Script: {len(words)} words")
    
    # TTS
    voice = get_tts_voice()
    audio_path = generate_audio(script_text, voice)
    
    if not audio_path or not os.path.exists(audio_path):
        audio_path = create_silent_audio(
            os.path.join(PATHS['temp'], 'silent.wav'), 12
        )
    
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    
    speed = VIDEO_CONFIG.get('TTS_SPEED', 1.0)
    if speed != 1.0:
        audio = audio.fx(vfx.speedx, speed)
        total_duration = audio.duration
    
    total_duration = max(
        VIDEO_CONFIG['DURATION_MIN'],
        min(VIDEO_CONFIG['DURATION_MAX'], total_duration)
    )
    
    logger.info(f"⏱️ Duration: {total_duration:.1f}s")
    
    # VISUALS
    clips_needed = int(total_duration / VIDEO_CONFIG['CLIP_DENSITY']) + 2
    logger.info(f"📊 Clips needed: {clips_needed}")
    
    visual_paths = []
    
    if editor_data and editor_data.get('visuals'):
        for v in editor_data['visuals']:
            path = v.get('path') if isinstance(v, dict) else None
            if path and os.path.exists(path):
                visual_paths.append(path)
        logger.info(f"Editor provided: {len(visual_paths)} clips")
    
    if len(visual_paths) < clips_needed:
        logger.info(f"⚠️ Downloading more...")
        try:
            from src.media.asset_finder import find_assets_for_script
            new_assets = find_assets_for_script(script_text, num_clips=clips_needed)
            for a in new_assets:
                path = a.get('path') if isinstance(a, dict) else None
                if path and os.path.exists(path) and path not in visual_paths:
                    visual_paths.append(path)
            logger.info(f"After download: {len(visual_paths)}")
        except Exception as e:
            logger.error(f"Download failed: {e}")
    
    if len(visual_paths) < clips_needed:
        logger.warning(f"🚨 Generating fallback")
        try:
            needed = clips_needed - len(visual_paths)
            generated = create_generated_visuals(script_text, num=needed)
            visual_paths.extend(generated)
        except Exception as e:
            logger.error(f"Fallback failed: {e}")
    
    if not visual_paths:
        for i in range(clips_needed):
            color = (random.randint(20, 50), random.randint(20, 50), random.randint(60, 100))
            visual_paths.append(('color', color))
    
    logger.info(f"✅ FINAL: {len(visual_paths)} visual assets")
    
    # ============================================================
    # 🎯 AI-BASED BEST MOMENT SELECTION (ENTIRE VIDEO ANALYSIS)
    # ============================================================
    
    logger.info("🎯 Analyzing all clips for BEST moment...")
    
    best_clip_idx = 0
    best_timestamp = 0.0
    best_score = -1
    
    # Analyze first 8 clips (max)
    for idx, vp in enumerate(visual_paths[:8]):
        if isinstance(vp, str) and os.path.exists(vp):
            if vp.lower().endswith(('.mp4', '.mov', '.webm', '.avi')):
                try:
                    ts, score, _ = find_best_moment_across_video(vp, num_samples=15)
                    
                    if score > best_score:
                        best_score = score
                        best_clip_idx = idx
                        best_timestamp = ts
                        logger.info(f"   Clip {idx}: {ts:.2f}s (score: {score:.1f}) ⭐")
                except Exception as e:
                    logger.warning(f"   Clip {idx} failed: {e}")
                    continue
    
    logger.info(f"🏆 WINNER: Clip {best_clip_idx} at {best_timestamp:.2f}s (score: {best_score:.1f})")
    
    # Reorder: winner clip goes first
    if best_clip_idx > 0:
        winning = visual_paths.pop(best_clip_idx)
        visual_paths.insert(0, winning)
        logger.info(f"🔄 Winner moved to first position")
    
    best_start_time = best_timestamp
    
    # ============================================================
    # BUILD CLIPS
    # ============================================================
    
    video_clips = []
    current_time = 0
    clip_idx = 0
    clip_density = VIDEO_CONFIG['CLIP_DENSITY']
    
    while current_time < total_duration:
        clip_duration = min(clip_density, total_duration - current_time)
        asset = visual_paths[clip_idx % len(visual_paths)]
        
        try:
            if isinstance(asset, tuple) and asset[0] == 'color':
                sub = ColorClip((WIDTH, HEIGHT), color=asset[1], duration=clip_duration)
            
            elif isinstance(asset, str) and os.path.exists(asset):
                ext = asset.lower()
                
                if ext.endswith(('.mp4', '.mov', '.webm', '.avi')):
                    vid = VideoFileClip(asset, audio=False)
                    vid = vid.resize(height=HEIGHT)
                    
                    if vid.w > WIDTH:
                        vid = vid.crop(x_center=vid.w / 2, width=WIDTH)
                    elif vid.w < WIDTH:
                        vid = vid.resize(width=WIDTH)
                    
                    # 🎯 First clip uses best moment timestamp
                    if clip_idx == 0 and best_start_time > 0:
                        start = best_start_time
                        logger.info(f"🎬 First frame at {start:.2f}s (highest engagement)")
                    else:
                        max_start = max(0, vid.duration - clip_duration)
                        start = random.uniform(0, max_start) if max_start > 0 else 0
                    
                    end_time = min(start + clip_duration, vid.duration)
                    sub = vid.subclip(start, end_time)
                    sub = sub.set_duration(clip_duration)
                
                elif ext.endswith(('.png', '.jpg', '.jpeg')):
                    sub = ImageClip(asset).set_duration(clip_duration)
                    sub = sub.resize(height=HEIGHT)
                    if sub.w > WIDTH:
                        sub = sub.crop(x_center=sub.w / 2, width=WIDTH)
                    elif sub.w < WIDTH:
                        sub = sub.resize(width=WIDTH)
                    sub = sub.resize(lambda t: 1.0 + 0.05 * t / clip_duration)
                
                else:
                    sub = ColorClip((WIDTH, HEIGHT), color=(20, 20, 50), duration=clip_duration)
            
            else:
                sub = ColorClip((WIDTH, HEIGHT), color=(20, 20, 50), duration=clip_duration)
            
            sub = sub.set_start(current_time)
            video_clips.append(sub)
        
        except Exception as e:
            logger.warning(f"Clip {clip_idx} failed: {e}")
            fallback = ColorClip(
                (WIDTH, HEIGHT),
                color=(random.randint(20, 50), random.randint(20, 50), random.randint(60, 100)),
                duration=clip_duration
            ).set_start(current_time)
            video_clips.append(fallback)
        
        current_time += clip_duration
        clip_idx += 1
    
    logger.info(f"🎞️ Compositing {len(video_clips)} clips...")
    
    # ============================================================
    # BASE COMPOSITE WITH LAYOUT
    # ============================================================
    
    video_area_top = TOP_BLACK_STRIP + WHITE_BAR_HEIGHT
    video_area_height = HEIGHT - video_area_top - BOTTOM_BLACK_STRIP
    
    adjusted_clips = []
    for clip in video_clips:
        try:
            clip_resized = clip.resize(height=video_area_height)
            
            if clip_resized.w > WIDTH:
                clip_resized = clip_resized.crop(x_center=clip_resized.w / 2, width=WIDTH)
            elif clip_resized.w < WIDTH:
                clip_resized = clip_resized.resize(width=WIDTH)
            
            clip_resized = clip_resized.set_position((0, video_area_top))
            adjusted_clips.append(clip_resized)
        except Exception as e:
            adjusted_clips.append(clip)
    
    base = CompositeVideoClip(
        adjusted_clips,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    # ============================================================
    # OVERLAYS
    # ============================================================
    
    overlays = []
    
    # White bar
    viral_hook = (
        script_data.get('viral_hook', '') or
        script_data.get('title', '')[:40] or
        "BREAKING NEWS"
    )
    
    topic_for_emoji = script_data.get('title', '') or script_data.get('seo_youtube_title', '')
    
    logger.info(f"🎨 White bar: '{viral_hook}'")
    
    try:
        whitebar_path = make_engaging_white_bar(viral_hook, topic_for_emoji)
        whitebar = ImageClip(whitebar_path).set_duration(total_duration).set_position((0, 0))
        overlays.append(whitebar)
    except Exception as e:
        logger.warning(f"White bar failed: {e}")
    
    # Bottom strip
    try:
        bottom_path = make_bottom_black_strip()
        bottom_strip = ImageClip(bottom_path).set_duration(total_duration).set_position((0, HEIGHT - BOTTOM_BLACK_STRIP))
        overlays.append(bottom_strip)
    except Exception as e:
        logger.warning(f"Bottom strip failed: {e}")
    
    # Captions
    words = script_text.split()
    word_dur = total_duration / max(len(words), 1)
    
    keywords_red = [
        'BREAKING', 'SHOCKING', 'TRUMP', 'BIDEN', 'WAR', 'DEAD',
        'KILLED', 'LEAKED', 'SECRET', 'FBI', 'COURT', 'RUSSIA',
        'UKRAINE', 'CHINA', 'MISSILE', 'STRIKE', 'POLAND', 'NATO',
        'USA', 'AMERICA', 'EMERGENCY', 'CRISIS', 'EXPOSED', 'REVEALED'
    ]
    
    for i, word in enumerate(words):
        start = i * word_dur
        if start >= total_duration:
            break
        
        is_kw = any(k in word.upper() for k in keywords_red)
        color = '#FF0000' if is_kw else '#FFFFFF'
        fontsize = 80 if is_kw else 70
        
        try:
            path = make_text_image(word.upper(), fontsize, color, 7)
            cap = ImageClip(path).set_duration(word_dur * 1.2).set_start(start)
            cap = cap.set_position(('center', 0.78), relative=True)
            
            if is_kw:
                cap = cap.resize(lambda t: 1.3 - 0.3 * min(1, t / word_dur))
            
            overlays.append(cap)
        except:
            continue
    
    logger.info(f"✅ {len(overlays)} overlays")
    
    # FINAL
    final = CompositeVideoClip(
        [base] + overlays,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    final = final.set_audio(audio)
    
    # WRITE
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    logger.info(f"💾 Writing at {fps} fps...")
    
    temp_output = output_path.replace('.mp4', '_raw.mp4')
    
    final.write_videofile(
        temp_output,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    logger.info(f"✅ Raw written")
    
    # FFMPEG FILTER
    logger.info("🎨 FFmpeg filters...")
    
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", temp_output,
            "-vf", "noise=alls=5:allf=t,hue=h=2:s=1.08",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            "-r", str(fps),
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            os.remove(temp_output)
            logger.info(f"✅ FFmpeg applied")
        else:
            logger.warning(f"FFmpeg failed")
            os.rename(temp_output, output_path)
    
    except Exception as e:
        logger.warning(f"FFmpeg error: {e}")
        if os.path.exists(temp_output):
            os.rename(temp_output, output_path)
    
    # Cleanup
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], '*.mp4')):
            os.remove(f)
    except:
        pass
    
    logger.info("=" * 50)
    logger.info(f"🎉 VIDEO READY")
    logger.info("=" * 50)
    
    return output_path
