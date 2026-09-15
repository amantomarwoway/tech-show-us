"""
src/media/video_builder.py - Video creation (MoviePy 1.0.3)
"""

import os
import random
import wave
import subprocess
import sys

# FIX: MoviePy 1.x import
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, ColorClip,
        CompositeVideoClip, CompositeAudioClip
    )
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    MOVIEPY_OK = True
except ImportError as e:
    print(f"[VIDEO_BUILDER] MoviePy 1.x required: {e}")
    MOVIEPY_OK = False

from PIL import Image, ImageDraw, ImageFont
from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

# ... rest of the code (same as before)
"""
src/media/video_builder.py - Video creation with MoviePy + FFmpeg
"""

import os
import random
import wave
import math
import subprocess
import tempfile
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from src.utils.logger import setup_logger
from src.config import VIDEO_CONFIG, TTS_CONFIG, PATHS

logger = setup_logger(__name__)

# ============================================================
# TTS
# ============================================================

def get_tts_voice():
    """Load Piper TTS voice"""
    try:
        from piper import PiperVoice
        
        model_path = TTS_CONFIG['model_path']
        config_path = TTS_CONFIG['config_path']
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        if not os.path.exists(model_path) or os.path.getsize(model_path) < 100000:
            logger.info("Downloading Piper TTS model...")
            import requests
            r = requests.get(TTS_CONFIG['model_url'], timeout=60)
            if r.status_code == 200 and len(r.content) > 100000:
                with open(model_path, 'wb') as f:
                    f.write(r.content)
        
        if not os.path.exists(config_path):
            import requests
            r = requests.get(TTS_CONFIG['config_url'], timeout=60)
            if r.status_code == 200:
                with open(config_path, 'wb') as f:
                    f.write(r.content)
        
        voice = PiperVoice.load(model_path, config_path)
        logger.info("TTS voice loaded")
        return voice
    
    except Exception as e:
        logger.error(f"TTS load failed: {e}")
        return None


def generate_audio(script_text, voice):
    """Generate audio from script using Piper TTS"""
    audio_path = os.path.join(PATHS['temp'], 'voice.wav')
    
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
            raise ValueError("No audio generated")
        
        with wave.open(audio_path, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for chunk in audio_chunks:
                wav.writeframes(chunk.audio_int16_bytes)
        
        logger.info(f"Audio generated: {audio_path}")
        return audio_path
    
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        return None


# ============================================================
# TEXT RENDERING
# ============================================================

def make_text_image(text, fontsize=60, color='white', stroke=5, size=(1080, 200)):
    """Create text image"""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to load font
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    
    font = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, fontsize)
            break
        except:
            continue
    
    if not font:
        font = ImageFont.load_default()
    
    # Draw text centered
    draw.text((size[0]//2, size[1]//2), text, font=font, fill=color,
              stroke_width=stroke, stroke_fill='black', anchor='mm')
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"txt_{random.randint(1, 999999)}.png")
    img.save(path)
    
    return path


def make_white_bar(text, width=1080, height=210):
    """Create white bar with black text (viral hook style)"""
    # Create black top strip + white bar
    img = Image.new('RGB', (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # White bar
    draw.rectangle([0, 60, width, height], fill=(255, 255, 255))
    
    # Text
    words = text.split()[:8]
    if len(words) >= 4:
        mid = (len(words) + 1) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    else:
        lines = [" ".join(words)]
    
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    try:
        font = ImageFont.truetype(font_path, 48)
    except:
        font = ImageFont.load_default()
    
    if len(lines) == 1:
        draw.text((width//2, 60 + (height-60)//2), lines[0], font=font, 
                  fill=(0, 0, 0), anchor='mm')
    else:
        draw.text((width//2, 60 + (height-60)//2 - 28), lines[0], font=font, 
                  fill=(0, 0, 0), anchor='mm')
        draw.text((width//2, 60 + (height-60)//2 + 28), lines[1], font=font, 
                  fill=(0, 0, 0), anchor='mm')
    
    os.makedirs(PATHS['temp'], exist_ok=True)
    path = os.path.join(PATHS['temp'], f"whitebar_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    
    return path


# ============================================================
# VIDEO CREATION
# ============================================================

def create_video(script_data, editor_data=None):
    """
    Main video creation function
    
    Returns path to created video
    """
    logger.info("Creating video...")
    
    os.makedirs(PATHS['output_videos'], exist_ok=True)
    output_path = os.path.join(PATHS['output_videos'], 
                               f"short_{random.randint(1000, 9999)}.mp4")
    
    # Get script
    script_text = script_data.get('full_script', '') or script_data.get('short_script', '')
    
    if not script_text:
        script_text = "Breaking news. This is a developing story."
    
    # Trim to 40 words
    words = script_text.split()[:VIDEO_CONFIG['WORDS_TARGET']]
    script_text = " ".join(words)
    
    logger.info(f"Script: {len(words)} words")
    
    # 1. Generate TTS
    voice = get_tts_voice()
    
    if voice:
        audio_path = generate_audio(script_text, voice)
    else:
        # Create silent audio
        audio_path = os.path.join(PATHS['temp'], 'silent.wav')
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", "12", "-c:a", "pcm_s16le", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not audio_path or not os.path.exists(audio_path):
        logger.error("No audio - using silent")
        audio_path = os.path.join(PATHS['temp'], 'silent.wav')
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", "12", "-c:a", "pcm_s16le", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Load audio
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration
    
    # Apply speed
    speed = VIDEO_CONFIG['TTS_SPEED']
    if speed != 1.0:
        audio = audio.fx(vfx.speedx, speed)
        total_duration = audio.duration
    
    # Clamp duration
    total_duration = max(VIDEO_CONFIG['DURATION_MIN'], 
                        min(VIDEO_CONFIG['DURATION_MAX'], total_duration))
    
    # 2. Get visual assets
    assets = editor_data.get('visuals', []) if editor_data else []
    
    if not assets:
        # Create color clips
        assets = []
        for i in range(15):
            assets.append({
                'type': 'color',
                'color': (random.randint(20, 40), random.randint(20, 40), random.randint(40, 80)),
                'duration': VIDEO_CONFIG['CLIP_DENSITY']
            })
    
    # 3. Build video clips
    video_clips = []
    current_time = 0
    clip_idx = 0
    
    while current_time < total_duration:
        clip_duration = min(VIDEO_CONFIG['CLIP_DENSITY'], total_duration - current_time)
        
        if clip_idx < len(assets):
            asset = assets[clip_idx]
        else:
            asset = {'type': 'color', 'color': (30, 30, 60)}
        
        try:
            if asset.get('type') == 'video' and asset.get('path'):
                if os.path.exists(asset['path']):
                    clip = VideoFileClip(asset['path'], audio=False)
                    clip = clip.resize(height=VIDEO_CONFIG['HEIGHT'])
                    clip = clip.subclip(0, min(clip_duration, clip.duration))
                else:
                    clip = ColorClip((VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']),
                                    color=asset.get('color', (30, 30, 60)),
                                    duration=clip_duration)
            else:
                clip = ColorClip((VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']),
                                color=asset.get('color', (30, 30, 60)),
                                duration=clip_duration)
        except:
            clip = ColorClip((VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']),
                            color=(30, 30, 60),
                            duration=clip_duration)
        
        clip = clip.set_start(current_time)
        video_clips.append(clip)
        
        current_time += clip_duration
        clip_idx += 1
    
    if not video_clips:
        video_clips = [ColorClip((VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']),
                                 color=(30, 30, 60),
                                 duration=total_duration)]
    
    # Composite base video
    base_video = CompositeVideoClip(video_clips, 
                                     size=(VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']))
    base_video = base_video.set_duration(total_duration)
    
    # 4. Add overlays
    overlays = []
    
    # White bar (viral hook)
    viral_hook = script_data.get('viral_hook', '') or script_data.get('title', 'Breaking News')
    whitebar_path = make_white_bar(viral_hook[:60])
    whitebar_clip = ImageClip(whitebar_path).set_duration(total_duration).set_position((0, 0))
    overlays.append(whitebar_clip)
    
    # Word captions
    caption_clips = create_captions(script_text, total_duration)
    overlays.extend(caption_clips)
    
    # Composite everything
    final = CompositeVideoClip([base_video] + overlays,
                                size=(VIDEO_CONFIG['WIDTH'], VIDEO_CONFIG['HEIGHT']))
    final = final.set_duration(total_duration)
    final = final.set_audio(audio)
    
    # 5. Write video
    fps = random.choice(VIDEO_CONFIG['FPS_CHOICES'])
    
    logger.info(f"Writing video: {fps} fps, {total_duration:.1f}s")
    
    final.write_videofile(
        output_path,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    # 6. Apply FFmpeg noise/hue filter
    try:
        temp_output = output_path.replace('.mp4', '_temp.mp4')
        
        subprocess.run([
            "ffmpeg", "-y", "-i", output_path,
            "-vf", "noise=alls=5:allf=t,hue=h=2:s=1.08",
            "-c:v", "libx264", "-crf", "20", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "128k",
            temp_output
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        os.replace(temp_output, output_path)
        logger.info("FFmpeg noise/hue applied")
    
    except Exception as e:
        logger.warning(f"FFmpeg filter failed: {e}")
    
    # Cleanup
    cleanup_temp_files()
    
    logger.info(f"Video created: {output_path}")
    return output_path


def create_captions(script_text, total_duration):
    """Create word captions"""
    words = script_text.split()
    
    if not words:
        return []
    
    word_duration = total_duration / len(words)
    captions = []
    
    keywords = ['BREAKING', 'SHOCKING', 'TRUMP', 'BIDEN', 'WHITE', 'HOUSE',
                'LEAKED', 'SECRET', 'SUPREME', 'COURT', 'USA', 'AMERICA']
    
    for i, word in enumerate(words):
        start_time = i * word_duration
        dur = word_duration * 1.2
        
        is_keyword = any(k in word.upper() for k in keywords)
        
        fontsize = 80 if is_keyword else 70
        color = '#FF0000' if is_keyword else '#FFFFFF'
        
        path = make_text_image(word.upper(), fontsize, color, 6, (1000, 200))
        
        clip = ImageClip(path).set_duration(dur).set_start(start_time)
        clip = clip.set_position(('center', 0.72), relative=True)
        
        if is_keyword:
            clip = clip.resize(lambda t: 1.2 - 0.2 * t / dur if t < dur * 0.3 else 1.0)
        
        captions.append(clip)
    
    return captions


def cleanup_temp_files():
    """Remove temporary files"""
    try:
        import glob
        patterns = [
            os.path.join(PATHS['temp'], "txt_*.png"),
            os.path.join(PATHS['temp'], "whitebar_*.png"),
            os.path.join(PATHS['temp'], "*.mp4")
        ]
        
        for pattern in patterns:
            for f in glob.glob(pattern):
                try:
                    os.remove(f)
                except:
                    pass
    
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")
