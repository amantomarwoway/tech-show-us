"""
src/media/text_video_builder.py - WARRIOR LETTER-BY-LETTER VISUAL
- Each letter = its own unique visual (color, size, rotation, font)
- Letters arranged like warrior formation
- Word-by-word display
- Trending topic focused
"""

import os
import random
import subprocess
import glob
import re
import math
from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import setup_logger
from src.config import TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = 1080
HEIGHT = 1920

# Multiple fonts = warrior variety
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTS = [FONT_BOLD, FONT_BOLD_ITALIC, FONT_REGULAR]

# Warrior color palette (aggressive + bold)
WARRIOR_COLORS = [
    (255, 30, 30),     # Blood red
    (255, 200, 0),     # Gold
    (0, 220, 255),     # Electric cyan
    (255, 100, 200),   # Hot pink
    (100, 255, 100),   # Neon green
    (255, 130, 0),     # Orange fire
    (180, 80, 255),    # Electric purple
    (255, 255, 255),   # Pure white
    (255, 240, 80),    # Bright yellow
    (50, 255, 180),    # Teal
    (220, 40, 40),     # Dark red
    (255, 170, 20),    # Amber
]

# Background schemes (dark, cinematic)
BG_SCHEMES = [
    {"bg1": (5, 0, 10), "bg2": (25, 5, 35), "accent": (220, 30, 80)},
    {"bg1": (0, 5, 20), "bg2": (8, 20, 55), "accent": (50, 130, 255)},
    {"bg1": (0, 10, 5), "bg2": (5, 30, 18), "accent": (30, 200, 100)},
    {"bg1": (10, 0, 0), "bg2": (35, 5, 10), "accent": (255, 60, 60)},
    {"bg1": (12, 8, 0), "bg2": (40, 25, 5), "accent": (255, 170, 30)},
    {"bg1": (2, 2, 2), "bg2": (18, 18, 22), "accent": (200, 200, 200)},
]

# Words that get FULL WARRIOR treatment
WARRIOR_WORDS = ['breaking', 'shocking', 'secret', 'leaked', 'exposed',
                 'billion', 'million', 'trillion', 'dead', 'died', 'killed',
                 'arrested', 'war', 'crisis', 'massive', 'huge', 'never',
                 'first', 'record', 'warning', 'danger', 'viral', 'trending',
                 'everyone', 'nobody', 'why', 'how', 'what', 'real', 'truth']


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        try:
            return ImageFont.truetype(FONT_BOLD, size)
        except:
            return ImageFont.load_default()


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


def generate_audio(text, voice):
    import wave
    ap = os.path.join(PATHS['temp'], 'voice.wav')
    os.makedirs(PATHS['temp'], exist_ok=True)
    if not voice:
        return None
    try:
        chunks = []
        sr = 22050
        try:
            gen = voice.synthesize(text, length_scale=1.0, noise_scale=0.6, noise_w_scale=0.75)
        except TypeError:
            gen = voice.synthesize(text)
        for c in gen:
            chunks.append(c)
            sr = c.sample_rate
        if not chunks:
            return None
        with wave.open(ap, 'wb') as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sr)
            for c in chunks:
                wav.writeframes(c.audio_int16_bytes)
        return ap
    except Exception as e:
        logger.error(f"Audio: {e}")
        return None


# ============================================================
# BACKGROUND
# ============================================================

def make_background(scheme):
    """Cinematic dark background with radial glow"""
    img = Image.new('RGB', (WIDTH, HEIGHT), scheme['bg1'])
    draw = ImageDraw.Draw(img)
    bg1, bg2 = scheme['bg1'], scheme['bg2']

    # Vertical gradient
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        r = int(bg1[0] * (1 - ratio) + bg2[0] * ratio)
        g = int(bg1[1] * (1 - ratio) + bg2[1] * ratio)
        b = int(bg1[2] * (1 - ratio) + bg2[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # Diagonal slashes (warrior armor pattern)
    slash_color = tuple(min(255, c + 12) for c in bg2)
    for i in range(-HEIGHT, WIDTH + HEIGHT, 90):
        draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=slash_color, width=2)

    # Center radial glow
    cx, cy = WIDTH // 2, HEIGHT // 2
    for radius in range(700, 0, -40):
        alpha = int(18 * (1 - radius / 700))
        color = (min(255, bg2[0] + alpha),
                 min(255, bg2[1] + alpha),
                 min(255, bg2[2] + alpha))
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     outline=color, width=30)

    # Vignette
    for i in range(100):
        draw.rectangle([0, 0, WIDTH, i], fill=(0, 0, 0))
        draw.rectangle([0, i, i, HEIGHT], fill=(0, 0, 0))
        draw.rectangle([WIDTH - i, 0, WIDTH, HEIGHT], fill=(0, 0, 0))
        draw.rectangle([0, HEIGHT - i, WIDTH, HEIGHT], fill=(0, 0, 0))

    path = os.path.join(PATHS['temp'], f"bg_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


# ============================================================
# LETTER RENDERER (WARRIOR)
# ============================================================

def render_letter_warrior(char, base_size, force_color=None):
    """
    Render ONE letter as a warrior visual.
    Each letter gets:
    - Random font
    - Random color from palette
    - Random rotation (-15 to +15)
    - Random size variation (±25%)
    - Multi-layer shadow
    - Glow effect
    """
    if not char or char == ' ':
        return None, 0, 0

    # Random font per letter
    font_path = random.choice(FONTS)

    # Size variation
    size_variation = random.uniform(0.85, 1.25)
    font_size = int(base_size * size_variation)

    # Random color
    if force_color:
        color = force_color
    else:
        color = random.choice(WARRIOR_COLORS)

    # Random rotation
    rotation = random.uniform(-15, 15)

    font = load_font(font_path, font_size)

    # Measure letter
    temp = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp)
    bbox = td.textbbox((0, 0), char, font=font)
    text_w = bbox[2] - bbox[0] + 40
    text_h = bbox[3] - bbox[1] + 40

    # Canvas with padding for rotation
    pad = 100
    canvas = Image.new('RGBA', (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
    cd = ImageDraw.Draw(canvas)

    base_x = pad
    base_y = pad

    # Multi-layer shadow (warrior depth)
    for dx, dy in [(-8, -8), (8, -8), (-8, 8), (8, 8),
                   (0, -8), (0, 8), (-8, 0), (8, 0),
                   (-5, -5), (5, -5), (-5, 5), (5, 5)]:
        cd.text((base_x + dx, base_y + dy), char,
                font=font, fill=(0, 0, 0, 220))

    # Outline stroke
    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3),
                   (0, -3), (0, 3), (-3, 0), (3, 0),
                   (-2, -2), (2, -2), (-2, 2), (2, 2)]:
        cd.text((base_x + dx, base_y + dy), char,
                font=font, fill=(0, 0, 0, 255))

    # Main letter
    cd.text((base_x, base_y), char, font=font, fill=color + (255,))

    # Rotate
    canvas = canvas.rotate(rotation, resample=Image.BICUBIC, expand=True)

    return canvas, color, font_size


def render_word_warrior(word, scheme, is_emphasis=False):
    """
    Render one word as a WARRIOR SQUAD.
    Each letter is a warrior with unique style, but they stand together.
    """
    bg = make_background(scheme)
    img = Image.open(bg).convert('RGBA')
    draw = ImageDraw.Draw(img)

    clean_word = word.strip()
    if not clean_word:
        clean_word = word

    # Base size (bigger for emphasis)
    if is_emphasis:
        base_size = random.randint(200, 260)
    else:
        base_size = random.randint(130, 180)

    # Render each letter
    letter_imgs = []
    max_letter_h = 0

    for char in clean_word:
        if char == ' ':
            letter_imgs.append(None)
            continue

        letter_img, color, size = render_letter_warrior(char, base_size)
        if letter_img:
            letter_imgs.append({
                'img': letter_img,
                'color': color,
                'size': size,
                'rotation': random.uniform(-15, 15)
            })
            max_letter_h = max(max_letter_h, letter_img.height)

    if not letter_imgs:
        return None

    # Calculate total width (letters stand shoulder to shoulder)
    gap = random.randint(2, 10)  # Random gaps between warriors
    total_w = 0
    for item in letter_imgs:
        if item:
            total_w += item['img'].width + gap

    # Scale if too wide
    max_w = WIDTH - 80
    if total_w > max_w:
        scale = max_w / total_w
        # Re-render letters smaller... simple: just reduce alpha
        # Skip scaling for now, adjust later

    # Center position with slight random offset
    x_start = (WIDTH - total_w) // 2 + random.randint(-20, 20)
    y_center = HEIGHT // 2 + random.randint(-40, 40) - max_letter_h // 2

    # Paste each letter
    current_x = x_start
    for item in letter_imgs:
        if not item:
            current_x += base_size // 3
            continue

        # Random vertical offset per letter (warrior stance variation)
        y_offset = random.randint(-30, 30)

        letter_img = item['img']
        paste_y = y_center + y_offset

        # Paste letter (with alpha)
        img.paste(letter_img,
                  (current_x, paste_y),
                  letter_img)

        # Add glow behind letter
        glow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        glow_cx = current_x + letter_img.width // 2
        glow_cy = paste_y + letter_img.height // 2
        color = item['color']

        for r in range(250, 0, -25):
            alpha = int(40 * (1 - r / 250))
            gd.ellipse([glow_cx - r, glow_cy - r, glow_cx + r, glow_cy + r],
                       fill=color + (alpha,))

        img = Image.alpha_composite(img, glow)

        current_x += letter_img.width + gap

    # Re-draw on the composited image
    draw = ImageDraw.Draw(img)

    # Top branding bar
    draw.rectangle([0, 0, WIDTH, 120], fill=(0, 0, 0, 230))
    draw.rectangle([0, 120, WIDTH, 128], fill=scheme['accent'] + (255,))

    font_brand = load_font(FONT_BOLD, 46)
    draw.text((40, 60), "UNCOVERED USA",
              font=font_brand, fill=(255, 255, 255, 255), anchor='lm')

    dot_x = WIDTH - 180
    draw.ellipse([dot_x - 14, 46, dot_x + 14, 74], fill=(255, 30, 30, 255))
    font_live = load_font(FONT_BOLD, 40)
    draw.text((dot_x + 28, 60), "LIVE",
              font=font_live, fill=(255, 255, 255, 255), anchor='lm')

    # Bottom bar
    draw.rectangle([0, HEIGHT - 160, WIDTH, HEIGHT], fill=(0, 0, 0, 230))
    draw.rectangle([0, HEIGHT - 168, WIDTH, HEIGHT - 160], fill=scheme['accent'] + (255,))

    font_cta = load_font(FONT_BOLD, 38)
    draw.text((WIDTH // 2, HEIGHT - 80), "SUBSCRIBE FOR MORE",
              font=font_cta, fill=(220, 220, 220, 255), anchor='mm')

    path = os.path.join(PATHS['temp'], f"ww_{random.randint(1, 999999)}.png")
    img.convert('RGB').save(path, quality=95)
    return path


# ============================================================
# SPLIT SCRIPT INTO WORDS
# ============================================================

def split_script_into_words(script_text):
    """Split into words, keep numbers together"""
    words = script_text.split()
    result = []
    i = 0
    while i < len(words):
        word = words[i].strip()
        if not word:
            i += 1
            continue

        # Number + unit combo
        if re.match(r'^\$?\d+(\.\d+)?$', word.replace(',', '')) and i + 1 < len(words):
            nxt = words[i + 1].lower().strip('.,!?')
            if nxt in ['billion', 'million', 'trillion', 'thousand', 'percent', '%',
                       'dollars', 'years', 'days']:
                result.append(f"{word} {words[i+1]}")
                i += 2
                continue

        result.append(word)
        i += 1
    return result


# ============================================================
# FFMPEG: BUILD VIDEO FROM WORD IMAGES
# ============================================================

def build_video_from_word_images(word_images, audio_path, output_path, word_duration):
    total_duration = word_duration * len(word_images)

    concat_file = os.path.join(PATHS['temp'], "word_concat.txt")
    with open(concat_file, 'w') as f:
        for p in word_images:
            abs_path = os.path.abspath(p)
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {word_duration}\n")
        f.write(f"file '{os.path.abspath(word_images[-1])}'\n")

    abs_audio = os.path.abspath(audio_path)
    abs_output = os.path.abspath(output_path)
    abs_concat = os.path.abspath(concat_file)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", abs_concat,
        "-i", abs_audio,
        "-vf", f"fps=30,scale={WIDTH}:{HEIGHT}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-t", str(total_duration),
        abs_output
    ]

    logger.info(f"FFmpeg: {len(word_images)} words @ {word_duration:.2f}s each")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if r.returncode != 0:
        logger.error(f"FFmpeg failed: {r.stderr[-400:]}")
        return False
    return True


# ============================================================
# MAIN
# ============================================================

def create_text_video(script_data, editor_data=None):
    logger.info("=" * 50)
    logger.info("WARRIOR LETTER-BY-LETTER VISUAL")
    logger.info("=" * 50)

    os.makedirs(PATHS['output_videos'], exist_ok=True)
    os.makedirs(PATHS['temp'], exist_ok=True)

    output_path = os.path.join(PATHS['output_videos'],
                               f"ww_{random.randint(1000, 9999)}.mp4")

    scheme = random.choice(BG_SCHEMES)
    logger.info(f"Scheme accent: {scheme['accent']}")

    script_text = script_data.get('short_script', '')
    if not script_text:
        facts = script_data.get('facts', [])
        script_text = " ".join(facts) if facts else "Breaking news everyone needs to know"

    logger.info(f"Script: {script_text[:100]}")

    voice = get_tts_voice()
    audio_path = generate_audio(script_text, voice)

    if not audio_path or not os.path.exists(audio_path):
        logger.warning("Silent audio")
        audio_path = os.path.join(PATHS['temp'], 'silent.wav')
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "anullsrc=r=22050:cl=mono",
            "-t", "15", "-c:a", "pcm_s16le", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ], capture_output=True, text=True, timeout=30)
        audio_dur = float(probe.stdout.strip())
    except:
        audio_dur = 12

    total_duration = max(10, min(18, audio_dur))
    logger.info(f"Audio: {audio_dur:.2f}s | Video: {total_duration:.2f}s")

    words = split_script_into_words(script_text)
    logger.info(f"Words: {len(words)}")

    if not words:
        words = ["Breaking", "News", "Update"]

    word_duration = total_duration / len(words)
    logger.info(f"Per word: {word_duration:.2f}s")

    word_images = []
    for i, word in enumerate(words):
        clean = re.sub(r'[^\w]', '', word.lower())
        is_emphasis = clean in WARRIOR_WORDS or bool(re.search(r'\d', word))

        try:
            path = render_word_warrior(word, scheme, is_emphasis)
            if path:
                word_images.append(path)
                logger.info(f"  [{i+1}/{len(words)}] '{word}'")
        except Exception as e:
            logger.warning(f"Word render failed for '{word}': {e}")
            continue

    if not word_images:
        logger.error("No word images generated")
        return output_path

    success = build_video_from_word_images(word_images, audio_path, output_path, word_duration)

    if not success:
        logger.error("Video build failed")
        return output_path

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"VIDEO READY: {output_path} ({size_mb:.1f}MB)")

    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "ww_*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], "bg_*.png")):
            os.remove(f)
    except:
        pass

    return output_path
