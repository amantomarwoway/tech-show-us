"""
src/media/video_builder.py - ULTIMATE ENGAGEMENT EDITION
- Best frame selection (CTR boost)
- Engaging white bar with gradient + accent
- Top black strip 200px + Bottom black strip 200px
- Title/hook quality boost
"""

import os
import random
import wave
import subprocess
import tempfile
import glob

# 🚨 CRITICAL FIX: Pillow 10+ compatibility for MoviePy 1.0.3
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
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

# NEW: Strip dimensions
TOP_BLACK_STRIP = 200      # was 150, now 200 (50px increase)
BOTTOM_BLACK_STRIP = 200   # NEW
WHITE_BAR_HEIGHT = 210


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
            logger.info("Downloading Piper TTS model...")
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
        logger.error(f"❌ TTS load failed: {e}")
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
# 🎯 BEST FRAME SELECTION (CTR BOOST)
# ============================================================

def score_frame(img_array):
    """
    Score a frame for engagement (0-100)
    Higher = better first frame
    """
    try:
        from PIL import ImageStat
        import numpy as np
        
        img = Image.fromarray(img_array)
        
        # 1. Contrast score (higher = better)
        stat = ImageStat.Stat(img.convert('L'))
        contrast = stat.stddev[0]
        
        # 2. Colorfulness (higher = more engaging)
        hsv = img.convert('HSV')
        hsv_stat = ImageStat.Stat(hsv)
        colorfulness = hsv_stat.stddev[1]  # Saturation stddev
        
        # 3. Brightness (optimal 100-180)
        brightness = stat.mean[0]
        brightness_score = 100 - abs(brightness - 140)
        
        # 4. Sharpness (edge detection)
        edges = img.convert('L').filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edges)
        sharpness = edge_stat.mean[0]
        
        # Weighted score
        total = (
            min(100, contrast * 1.5) * 0.3 +
            min(100, colorfulness * 2) * 0.3 +
            max(0, brightness_score) * 0.2 +
            min(100, sharpness * 3) * 0.2
        )
        
        return total
    except Exception as e:
        return 50


def find_best_frame_from_video(video_path, num_samples=10):
    """
    Sample frames from video and return timestamp of best frame
    Returns: (timestamp, score)
    """
    try:
        import numpy as np
        from moviepy.editor import VideoFileClip
        
        vid = VideoFileClip(video_path, audio=False)
        duration = vid.duration
        
        if duration < 0.5:
            vid.close()
            return 0.0, 50
        
        # Sample frames evenly
        timestamps = [i * duration / num_samples for i in range(num_samples)]
        
        best_score = -1
        best_timestamp = 0
        
        for ts in timestamps:
            try:
                frame = vid.get_frame(ts)
                score = score_frame(frame)
                
                if score > best_score:
                    best_score = score
                    best_timestamp = ts
            except:
                continue
        
        vid.close()
        logger.info(f"🎯 Best frame at {best_timestamp:.2f}s (score: {best_score:.1f})")
        return best_timestamp, best_score
    
    except Exception as e:
        logger.warning(f"Best frame failed: {e}")
        return 0.0, 50


def find_best_thumbnail_frame(video_clips):
    """
    Find best frame across all clips for thumbnail
    """
    best_score = -1
    best_clip = None
    best_time = 0
    
    for clip in video_clips[:5]:  # Check first 5 clips
        try:
            if hasattr(clip, 'duration') and clip.duration > 0.3:
                # Sample 3 frames per clip
                for i in range(3):
                    ts = i * clip.duration / 3
                    try:
                        frame = clip.get_frame(ts)
                        score = score_frame(frame)
                        if score > best_score:
                            best_score = score
                            best_clip = clip
                            best_time = ts
                    except:
                        continue
        except:
            continue
    
    return best_clip, best_time, best_score


# ============================================================
# 🎨 ENGAGING WHITE BAR (GRADIENT + ACCENT)
# ============================================================

def extract_engaging_hook(script_data, story):
    """
    Extract engaging hook text for white bar
    Priority: viral_hook > script first sentence > title
    """
    hook = (
        script_data.get('viral_hook', '').strip() or
        script_data.get('hook', '').strip()
    )
    
    # If no hook, extract from script
    if not hook:
        script = script_data.get('short_script', '') or script_data.get('full_script', '')
        if script:
            # First sentence
            import re
            sentences = re.split(r'[.!?]+', script)
            if sentences:
                hook = sentences[0].strip()
    
    # Fallback to title
    if not hook:
        hook = story.get('title', '') or script_data.get('title', 'BREAKING NEWS')
    
    # Clean
    hook = hook.replace('"', '').replace("'", '').strip()
    
    # Limit to 8 words
    words = hook.split()
    if len(words) > 8:
        words = words[:8]
        hook = " ".join(words)
    
    return hook.upper()


def make_engaging_white_bar(text, accent_color=None):
    """
    Create ENGAGING white bar with:
    - Gradient background
    - Bold italic text
    - Accent color bar on left
    - Slight shadow
    """
    # Total height = top black strip + white bar
    total_height = TOP_BLACK_STRIP + WHITE_BAR_HEIGHT
    
    img = Image.new('RGB', (WIDTH, total_height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Random accent color
    if not accent_color:
        accents = [
            (255, 215, 0),    # Gold
            (255, 50, 50),    # Red
            (0, 200, 255),    # Cyan
            (50, 255, 100),   # Green
            (255, 100, 200),  # Pink
            (255, 130, 0),    # Orange
        ]
        accent_color = random.choice(accents)
    
    # Draw white bar with subtle gradient
    for y in range(WHITE_BAR_HEIGHT):
        ratio = y / WHITE_BAR_HEIGHT
        # Gradient from pure white to slightly gray
        r = int(255 - ratio * 20)
        g = int(255 - ratio * 20)
        b = int(255 - ratio * 20)
        draw.line(
            [(0, TOP_BLACK_STRIP + y), (WIDTH, TOP_BLACK_STRIP + y)],
            fill=(r, g, b)
        )
    
    # Accent color bar (left side)
    draw.rectangle(
        [0, TOP_BLACK_STRIP, 20, TOP_BLACK_STRIP + WHITE_BAR_HEIGHT],
        fill=accent_color
    )
    
    # Accent bar (right side)
    draw.rectangle(
        [WIDTH - 20, TOP_BLACK_STRIP, WIDTH, TOP_BLACK_STRIP + WHITE_BAR_HEIGHT],
        fill=accent_color
    )
    
    # Text - split into lines
    words = text.split()
    if len(words) >= 6:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    elif len(words) >= 3:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [text]
    
    # Font - use bold italic
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
    try:
        if len(lines) == 1:
            font = ImageFont.truetype(font_path, 68)
        else:
            font = ImageFont.truetype(font_path, 56)
    except:
        font = ImageFont.load_default()
    
    # Draw text with accent color
    text_color = (10, 10, 10)
    
    if len(lines) == 1:
        # Single line - center
        bbox = draw.textbbox((0, 0), lines[0], font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = TOP_BLACK_STRIP + (WHITE_BAR_HEIGHT - th) // 2
        
        # Shadow
        draw.text((x + 2, y + 2), lines[0], font=font, fill=(150, 150, 150))
        draw.text((x, y), lines[0], font=font, fill=text_color)
    
    else:
        # Two lines
        for i, line in enumerate(lines[:2]):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            x = (WIDTH - tw) // 2
            y = TOP_BLACK_STRIP + 30 + i * 85
            
            # Shadow
            draw.text((x + 2, y + 2), line, font=font, fill=(150, 150, 150))
            draw.text((x, y), line, font=font, fill=text_color)
    
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# 🎨 BOTTOM BLACK STRIP (NEW)
# ============================================================

def make_bottom_black_strip():
    """Create bottom black strip 200px"""
    img = Image.new('RGB', (WIDTH, BOTTOM_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Add channel branding text
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
        )
    except:
        font = ImageFont.load_default()
    
    # Channel name (optional - can be removed)
    # draw.text((WIDTH // 2, BOTTOM_BLACK_STRIP // 2), 
    #           "@YourChannel", font=font, fill=(100, 100, 100), anchor='mm')
    
    path = os.path.join(PATHS['temp'], f"bottom_strip_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# TEXT IMAGE (Captions)
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
    
    # Shadow first
    draw.text(
        (WIDTH // 2 + 3, 153), text,
        font=font, fill=(0, 0, 0, 180),
        stroke_width=stroke + 2, stroke_fill='black',
        anchor='mm'
    )
    
    # Main text
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
# GENERATED VISUALS (Fallback)
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
        "Breaking news update. This is a developing story."
    )
    
    words = script_text.split()[:VIDEO_CONFIG['WORDS_TARGET']]
    script_text = " ".join(words)
    logger.info(f"📝 Script: {len(words)} words")
    
    # ============================================================
    # 1. TTS
    # ============================================================
    
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
    
    # ============================================================
    # 2. VISUALS
    # ============================================================
    
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
        logger.info(f"⚠️ Only {len(visual_paths)} - downloading more...")
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
    # 3. BUILD CLIPS (Best Frame as First)
    # ============================================================
    
    # First find best frame from first clip for CTR boost
    first_clip_path = None
    for vp in visual_paths:
        if isinstance(vp, str) and os.path.exists(vp):
            if vp.lower().endswith(('.mp4', '.mov', '.webm', '.avi')):
                first_clip_path = vp
                break
    
    best_start_time = 0.0
    
    if first_clip_path:
        logger.info(f"🎯 Finding best first frame...")
        best_start_time, score = find_best_frame_from_video(first_clip_path, num_samples=10)
        logger.info(f"✅ Using frame at {best_start_time:.2f}s for CTR")
    
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
                    
                    # 🎯 FOR FIRST CLIP: Use best frame start time
                    if clip_idx == 0 and best_start_time > 0:
                        start = best_start_time
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
    # 4. BASE COMPOSITE (with top & bottom black strips)
    # ============================================================
    
    # Position video between top and bottom strips
    video_area_top = TOP_BLACK_STRIP + WHITE_BAR_HEIGHT
    video_area_height = HEIGHT - video_area_top - BOTTOM_BLACK_STRIP
    
    # Resize clips to fit video area
    adjusted_clips = []
    for clip in video_clips:
        try:
            # Scale to fit video area
            clip_resized = clip.resize(height=video_area_height)
            
            if clip_resized.w > WIDTH:
                clip_resized = clip_resized.crop(x_center=clip_resized.w / 2, width=WIDTH)
            elif clip_resized.w < WIDTH:
                clip_resized = clip_resized.resize(width=WIDTH)
            
            # Position in video area
            clip_resized = clip_resized.set_position((0, video_area_top))
            adjusted_clips.append(clip_resized)
        except Exception as e:
            logger.warning(f"Resize failed: {e}")
            adjusted_clips.append(clip)
    
    base = CompositeVideoClip(
        adjusted_clips,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    # ============================================================
    # 5. OVERLAYS
    # ============================================================
    
    overlays = []
    
    # 🎯 ENGAGING WHITE BAR
    viral_hook = extract_engaging_hook(script_data, script_data)
    logger.info(f"🎨 White bar text: '{viral_hook}'")
    
    try:
        whitebar_path = make_engaging_white_bar(viral_hook)
        whitebar = ImageClip(whitebar_path).set_duration(total_duration).set_position((0, 0))
        overlays.append(whitebar)
    except Exception as e:
        logger.warning(f"White bar failed: {e}")
    
    # 🎯 BOTTOM BLACK STRIP
    try:
        bottom_path = make_bottom_black_strip()
        bottom_strip = ImageClip(bottom_path).set_duration(total_duration).set_position((0, HEIGHT - BOTTOM_BLACK_STRIP))
        overlays.append(bottom_strip)
    except Exception as e:
        logger.warning(f"Bottom strip failed: {e}")
    
    # Captions (position adjusted for new layout)
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
            # Caption position - 75% down (in video area)
            cap = cap.set_position(('center', 0.78), relative=True)
            
            if is_kw:
                cap = cap.resize(lambda t: 1.3 - 0.3 * min(1, t / word_dur))
            
            overlays.append(cap)
        except:
            continue
    
    logger.info(f"✅ {len(overlays)} overlays")
    
    # ============================================================
    # 6. FINAL
    # ============================================================
    
    final = CompositeVideoClip(
        [base] + overlays,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    final = final.set_audio(audio)
    
    # ============================================================
    # 7. WRITE
    # ============================================================
    
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
    
    # ============================================================
    # 8. FFMPEG FILTER
    # ============================================================
    
    logger.info("🎨 Applying FFmpeg filters...")
    
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
        for f in glob.glob(os.path.join(PATHS['temp'], "*.mp4")):
            os.remove(f)
    except:
        pass
    
    logger.info("=" * 50)
    logger.info(f"🎉 VIDEO READY")
    logger.info("=" * 50)
    
    return output_path
