"""
src/media/video_builder.py - BULLETPROOF video creation
"""

import os
import random
import wave
import subprocess
import tempfile
import glob

# 🚨 CRITICAL FIX: Pillow 10+ compatibility for MoviePy 1.0.3
from PIL import Image
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

# ... rest of code
"""
src/media/video_builder.py - BULLETPROOF video creation
MoviePy 1.0.3 ONLY - Script-based visuals + guaranteed output
"""

import os
import random
import wave
import subprocess
import tempfile
import glob

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

from PIL import Image, ImageDraw, ImageFont
from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = VIDEO_CONFIG['WIDTH']
HEIGHT = VIDEO_CONFIG['HEIGHT']


# ============================================================
# TTS
# ============================================================

def get_tts_voice():
    """Load Piper TTS voice"""
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
                logger.info(f"Model downloaded: {len(r.content)} bytes")
        
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
    """Generate audio from script"""
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
        
        logger.info(f"✅ Audio generated: {audio_path}")
        return audio_path
    
    except Exception as e:
        logger.error(f"❌ Audio gen failed: {e}")
        return create_silent_audio(audio_path, duration=12)


def create_silent_audio(path, duration=12):
    """Create silent audio fallback"""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", str(duration), "-c:a", "pcm_s16le", path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return path
    except:
        return None


# ============================================================
# GENERATED VISUALS (Fallback)
# ============================================================

def create_gradient_image(path, color1, color2, text=""):
    """Create gradient background with optional text"""
    img = Image.new('RGB', (WIDTH, HEIGHT), color1)
    draw = ImageDraw.Draw(img)
    
    # Vertical gradient
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    # Optional text
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
        
        # Outline
        for dx in [-4, 0, 4]:
            for dy in [-4, 0, 4]:
                draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    img.save(path)
    return path


def create_generated_visuals(script_text, num=15):
    """Generate gradient visuals when Pexels fails"""
    logger.info(f"🎨 Generating {num} gradient visuals")
    
    visuals = []
    words = script_text.split()
    
    # Cinematic colors
    color_pairs = [
        ((10, 15, 40), (60, 30, 100)),   # Purple/blue
        ((20, 10, 10), (100, 40, 30)),   # Red/brown
        ((5, 20, 30), (30, 80, 120)),    # Blue
        ((15, 15, 15), (60, 60, 60)),    # Gray
        ((30, 20, 5), (120, 80, 20)),    # Gold
    ]
    
    for i in range(num):
        color1, color2 = random.choice(color_pairs)
        
        # Keyword from script
        if i < len(words):
            text = words[i].upper()
        elif words:
            text = random.choice(words).upper()
        else:
            text = ""
        
        path = os.path.join(PATHS['temp'], f"grad_{random.randint(1, 999999)}.png")
        create_gradient_image(path, color1, color2, text)
        visuals.append(path)
    
    return visuals


# ============================================================
# TEXT RENDERING
# ============================================================

def make_text_image(text, fontsize=70, color='white', stroke=6):
    """Create text image with outline"""
    img = Image.new('RGBA', (WIDTH, 300), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize
        )
    except:
        font = ImageFont.load_default()
    
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


def make_white_bar(text):
    """Create viral hook white bar"""
    img = Image.new('RGB', (WIDTH, 210), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # White section
    draw.rectangle([0, 60, WIDTH, 210], fill=(255, 255, 255))
    
    words = text.split()[:8]
    if len(words) >= 4:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [" ".join(words)]
    
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf", 46
        )
    except:
        font = ImageFont.load_default()
    
    if len(lines) == 1:
        draw.text((WIDTH // 2, 135), lines[0], font=font, fill=(0, 0, 0), anchor='mm')
    else:
        draw.text((WIDTH // 2, 105), lines[0], font=font, fill=(0, 0, 0), anchor='mm')
        draw.text((WIDTH // 2, 165), lines[1], font=font, fill=(0, 0, 0), anchor='mm')
    
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# VIDEO CREATION (MAIN)
# ============================================================

def create_video(script_data, editor_data=None):
    """BULLETPROOF video creation"""
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
    # GET SCRIPT
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
    # 2. GET VISUALS - SCRIPT BASED
    # ============================================================
    
    clips_needed = int(total_duration / VIDEO_CONFIG['CLIP_DENSITY']) + 2
    logger.info(f"📊 Clips needed: {clips_needed}")
    
    visual_paths = []
    
    # 2a. Get from editor_data
    if editor_data and editor_data.get('visuals'):
        for v in editor_data['visuals']:
            path = v.get('path') if isinstance(v, dict) else None
            if path and os.path.exists(path):
                visual_paths.append(path)
        logger.info(f"Editor provided: {len(visual_paths)} clips")
    
    # 2b. Download more if needed (script-based)
    if len(visual_paths) < clips_needed:
        logger.info(f"⚠️ Only {len(visual_paths)} clips - downloading from script...")
        
        try:
            from src.media.asset_finder import find_assets_for_script
            new_assets = find_assets_for_script(script_text, num_clips=clips_needed)
            
            for a in new_assets:
                path = a.get('path') if isinstance(a, dict) else None
                if path and os.path.exists(path) and path not in visual_paths:
                    visual_paths.append(path)
            
            logger.info(f"After download: {len(visual_paths)} clips")
        except Exception as e:
            logger.error(f"Script download failed: {e}")
    
    # 2c. Generate fallback gradient images
    if len(visual_paths) < clips_needed:
        logger.warning(f"🚨 Still {len(visual_paths)}/{clips_needed} - generating fallback")
        try:
            needed = clips_needed - len(visual_paths)
            generated = create_generated_visuals(script_text, num=needed)
            visual_paths.extend(generated)
            logger.info(f"Generated {len(generated)} gradient visuals")
        except Exception as e:
            logger.error(f"Fallback failed: {e}")
    
    # 2d. Final safety - color clips
    if not visual_paths:
        logger.error("❌ No visuals - using color clips")
        for i in range(clips_needed):
            color = (random.randint(20, 50), random.randint(20, 50), random.randint(60, 100))
            visual_paths.append(('color', color))
    
    logger.info(f"✅ FINAL: {len(visual_paths)} visual assets")
    
    # ============================================================
    # 3. BUILD VIDEO CLIPS
    # ============================================================
    
    video_clips = []
    current_time = 0
    clip_idx = 0
    clip_density = VIDEO_CONFIG['CLIP_DENSITY']
    
    while current_time < total_duration:
        clip_duration = min(clip_density, total_duration - current_time)
        
        asset = visual_paths[clip_idx % len(visual_paths)]
        
        try:
            # Tuple = color clip
            if isinstance(asset, tuple) and asset[0] == 'color':
                sub = ColorClip((WIDTH, HEIGHT), color=asset[1], duration=clip_duration)
            
            # String = file path
            elif isinstance(asset, str) and os.path.exists(asset):
                ext = asset.lower()
                
                if ext.endswith(('.mp4', '.mov', '.webm', '.avi')):
                    # Video file
                    vid = VideoFileClip(asset, audio=False)
                    vid = vid.resize(height=HEIGHT)
                    
                    if vid.w > WIDTH:
                        vid = vid.crop(x_center=vid.w / 2, width=WIDTH)
                    elif vid.w < WIDTH:
                        vid = vid.resize(width=WIDTH)
                    
                    max_start = max(0, vid.duration - clip_duration)
                    start = random.uniform(0, max_start) if max_start > 0 else 0
                    
                    sub = vid.subclip(start, min(start + clip_duration, vid.duration))
                    sub = sub.set_duration(clip_duration)
                
                elif ext.endswith(('.png', '.jpg', '.jpeg')):
                    # Image file
                    sub = ImageClip(asset).set_duration(clip_duration)
                    sub = sub.resize(height=HEIGHT)
                    
                    if sub.w > WIDTH:
                        sub = sub.crop(x_center=sub.w / 2, width=WIDTH)
                    elif sub.w < WIDTH:
                        sub = sub.resize(width=WIDTH)
                    
                    # Subtle zoom effect
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
    # 4. BASE COMPOSITE
    # ============================================================
    
    base = CompositeVideoClip(
        video_clips,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    # ============================================================
    # 5. OVERLAYS
    # ============================================================
    
    overlays = []
    
    # White bar viral hook
    viral_hook = (
        script_data.get('viral_hook', '') or
        script_data.get('title', '')[:60] or
        "Breaking News"
    )
    
    try:
        whitebar_path = make_white_bar(viral_hook[:70])
        whitebar = ImageClip(whitebar_path).set_duration(total_duration).set_position((0, 0))
        overlays.append(whitebar)
    except Exception as e:
        logger.warning(f"White bar failed: {e}")
    
    # Word captions
    words = script_text.split()
    word_dur = total_duration / max(len(words), 1)
    
    keywords_red = [
        'BREAKING', 'SHOCKING', 'TRUMP', 'BIDEN', 'WAR', 'DEAD',
        'KILLED', 'LEAKED', 'SECRET', 'FBI', 'COURT', 'RUSSIA',
        'UKRAINE', 'CHINA', 'MISSILE', 'STRIKE', 'POLAND', 'NATO',
        'USA', 'AMERICA', 'EMERGENCY', 'CRISIS'
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
            cap = cap.set_position(('center', 0.72), relative=True)
            
            if is_kw:
                cap = cap.resize(lambda t: 1.3 - 0.3 * min(1, t / word_dur))
            
            overlays.append(cap)
        except:
            continue
    
    logger.info(f"✅ {len(overlays)} overlays ready")
    
    # ============================================================
    # 6. FINAL COMPOSITE
    # ============================================================
    
    final = CompositeVideoClip(
        [base] + overlays,
        size=(WIDTH, HEIGHT)
    ).set_duration(total_duration)
    
    final = final.set_audio(audio)
    
    # ============================================================
    # 7. WRITE RAW VIDEO
    # ============================================================
    
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    logger.info(f"💾 Writing video at {fps} fps...")
    
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
    
    logger.info(f"✅ Raw video written: {temp_output}")
    
    # ============================================================
    # 8. FFMPEG FILTER (noise + hue for dedup)
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
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            os.remove(temp_output)
            logger.info(f"✅ FFmpeg applied: {output_path}")
        else:
            logger.warning(f"FFmpeg failed: {result.stderr[-200:]}")
            os.rename(temp_output, output_path)
    
    except Exception as e:
        logger.warning(f"FFmpeg error: {e}")
        if os.path.exists(temp_output):
            os.rename(temp_output, output_path)
    
    # ============================================================
    # 9. CLEANUP
    # ============================================================
    
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "*.png")):
            try:
                os.remove(f)
            except:
                pass
        for f in glob.glob(os.path.join(PATHS['temp'], "*.mp4")):
            try:
                os.remove(f)
            except:
                pass
    except:
        pass
    
    logger.info("=" * 50)
    logger.info(f"🎉 VIDEO READY: {output_path}")
    logger.info("=" * 50)
    
    return output_path
