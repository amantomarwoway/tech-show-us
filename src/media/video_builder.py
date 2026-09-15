"""
src/media/video_builder.py - FINAL PRODUCTION VERSION
- Auto-shrink white bar text (no cut)
- Bold with thick stroke
- Emoji via native rendering + fallback
- Top black strip with branding
- Bottom black strip clean
- AI best frame selection
"""

import os
import random
import wave
import subprocess
import tempfile
import glob
import re

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
    print("[VIDEO_BUILDER] MoviePy 1.x loaded")
except ImportError as e:
    print(f"[VIDEO_BUILDER] MoviePy 1.x REQUIRED: {e}")
    raise

from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = VIDEO_CONFIG['WIDTH']       # 1080
HEIGHT = VIDEO_CONFIG['HEIGHT']     # 1920

# LAYOUT (fixed, exact)
TOP_BLACK_STRIP = 180
WHITE_BAR_HEIGHT = 200
BOTTOM_BLACK_STRIP = 200

# FONTS
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"


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
            r = requests.get(TTS_CONFIG['model_url'], timeout=120)
            if r.status_code == 200:
                with open(model_path, 'wb') as f:
                    f.write(r.content)
        if not os.path.exists(config_path):
            r = requests.get(TTS_CONFIG['config_url'], timeout=60)
            if r.status_code == 200:
                with open(config_path, 'wb') as f:
                    f.write(r.content)
        return PiperVoice.load(model_path, config_path)
    except Exception as e:
        logger.error(f"TTS failed: {e}")
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
        return audio_path
    except Exception as e:
        logger.error(f"Audio failed: {e}")
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
    """Score frame 0-100 for engagement"""
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
    """Find font size that fits text"""
    temp_img = Image.new('RGB', (10, 10))
    draw = ImageDraw.Draw(temp_img)
    
    for size in range(start_size, 24, -2):
        font = load_font(FONT_BOLD, size)
        lines = wrap_text_to_width(text, font, max_width, draw)
        
        if len(lines) <= max_lines:
            # Check height
            total_h = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                total_h += (bbox[3] - bbox[1]) + 10
            
            if total_h <= max_height:
                return font, lines, size
    
    # Fallback: smallest size
    font = load_font(FONT_BOLD, 32)
    lines = wrap_text_to_width(text, font, max_width, draw)
    return font, lines[:max_lines], 32


# ============================================================
# 🎨 TOP BLACK STRIP (BRANDING)
# ============================================================

def make_top_black_strip():
    """Top black strip with channel branding"""
    img = Image.new('RGB', (WIDTH, TOP_BLACK_STRIP), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Red accent line at bottom
    draw.rectangle([0, TOP_BLACK_STRIP - 5, WIDTH, TOP_BLACK_STRIP], fill=(220, 30, 30))
    
    # Channel name (left side)
    font_ch = load_font(FONT_BOLD, 42)
    draw.text((30, TOP_BLACK_STRIP // 2), "UNCOVERED USA", 
              font=font_ch, fill=(255, 255, 255), anchor='lm')
    
    # LIVE dot (right side)
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

def render_emoji_manually(draw, text, x, y, size=70):
    """
    Manually draw emoji as fallback (colored circle if font fails)
    """
    try:
        emoji_font = ImageFont.truetype(FONT_EMOJI, size)
        draw.text((x, y), text, font=emoji_font, embedded_color=True, anchor='mm')
        return True
    except:
        return False


def make_white_bar(text, topic=""):
    """
    FINAL white bar:
    - Auto font size (no cut)
    - Max 2 lines
    - Bold + thick shadow
    - Emoji at end
    - Red accent bars left + right
    """
    total_h = WHITE_BAR_HEIGHT
    img = Image.new('RGB', (WIDTH, total_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Gradient white
    for y in range(total_h):
        ratio = y / total_h
        shade = int(255 - ratio * 12)
        draw.line([(0, y), (WIDTH, y)], fill=(shade, shade, shade))
    
    # Red accent bars
    draw.rectangle([0, 0, 18, total_h], fill=(220, 30, 30))
    draw.rectangle([WIDTH - 18, 0, WIDTH, total_h], fill=(220, 30, 30))
    
    # Separate emoji from text
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+",
        flags=re.UNICODE
    )
    emojis = emoji_pattern.findall(text)
    text_only = emoji_pattern.sub('', text).strip().upper()
    
    # Auto-add emoji if missing
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
    
    # Add emoji to text
    full_text = text_only + " " + emoji_char
    
    # Max width for text
    max_text_width = WIDTH - 60  # Padding
    max_text_height = total_h - 40
    
    # Find best font size (auto-fit)
    font, lines, size = find_best_font_size(
        full_text, max_text_width, max_text_height, max_lines=2, start_size=76
    )
    
    logger.info(f"   White bar font: {size}px, {len(lines)} lines")
    
    # Draw text centered
    if len(lines) == 1:
        line = lines[0]
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (WIDTH - tw) // 2
        y = (total_h - th) // 2
        
        # THICK shadow (4 directions)
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(180, 180, 180))
        # Outline
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(80, 80, 80))
        # Main
        draw.text((x, y), line, font=font, fill=(10, 10, 10))
    
    else:
        # Two lines
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
    draw.text((WIDTH // 2, 140), "🔔 New videos every 6 hours", 
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
    
    # Black outline (thick)
    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (-3, 0), (3, 0), (0, -3), (0, 3)]:
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
# 🎬 MAIN
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
    
    script_text = (
        script_data.get('full_script', '') or
        script_data.get('short_script', '') or
        "Breaking news update."
    )
    words = script_text.split()[:VIDEO_CONFIG['WORDS_TARGET']]
    script_text = " ".join(words)
    logger.info(f"📝 Script: {len(words)} words")
    
    # TTS
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
    
    # VISUALS
    clips_needed = int(total_duration / VIDEO_CONFIG['CLIP_DENSITY']) + 2
    
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
        except Exception as e:
            logger.error(f"Download failed: {e}")
    
    if len(visual_paths) < clips_needed:
        needed = clips_needed - len(visual_paths)
        for i in range(needed):
            visual_paths.append(create_gradient_visual(script_text.split()[i % len(script_text.split())].upper() if script_text.split() else "", i))
    
    logger.info(f"✅ FINAL: {len(visual_paths)} clips")
    
    # 🎯 AI BEST FRAME SELECTION
    logger.info("🎯 Finding best frame...")
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
        logger.info(f"🔄 Winner clip {best_idx} moved to first")
    
    # BUILD CLIPS
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
    
    # LAYOUT: video area between strips
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
    
    # OVERLAYS
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
    
    # 3. Bottom strip
    overlays.append(ImageClip(make_bottom_black_strip()).set_duration(total_duration).set_position((0, HEIGHT - BOTTOM_BLACK_STRIP)))
    
    # 4. Captions
    words = script_text.split()
    word_dur = total_duration / max(len(words), 1)
    red_kw = ['BREAKING','SHOCKING','TRUMP','BIDEN','WAR','DEAD','KILLED','LEAKED','SECRET','FBI','COURT','RUSSIA','UKRAINE','CHINA','MISSILE','STRIKE','POLAND','NATO','USA','AMERICA','CRISIS','EXPOSED']
    
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
    
    final = CompositeVideoClip([base] + overlays, size=(WIDTH, HEIGHT)).set_duration(total_duration)
    final = final.set_audio(audio)
    
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    temp_out = output_path.replace('.mp4', '_raw.mp4')
    
    final.write_videofile(temp_out, fps=fps, codec='libx264', audio_codec='aac',
                          preset='ultrafast', threads=4, logger=None)
    
    try:
        cmd = ["ffmpeg", "-y", "-i", temp_out,
               "-vf", "noise=alls=5:allf=t,hue=h=2:s=1.08",
               "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
               "-c:a", "aac", "-b:a", "128k", "-r", str(fps), output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            os.remove(temp_out)
        else:
            os.rename(temp_out, output_path)
    except:
        if os.path.exists(temp_out):
            os.rename(temp_out, output_path)
    
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], '*.mp4')):
            os.remove(f)
    except:
        pass
    
    logger.info(f"🎉 VIDEO READY: {output_path}")
    return output_path
