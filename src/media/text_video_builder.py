"""
src/media/text_video_builder.py - WARRIOR LETTER BATTLE v2
- Extended white bar (top)
- Letters fight with weapons to form words
- Word drops with explosion
- Final warrior display
- FULL script shown (no word cap) — synced to audio
- Adaptive frames: fast words get fewer frames, slow words get full battle
- Optimized for 45-55s long-form Shorts
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
WHITE_BAR_TOP = 0
WHITE_BAR_BOTTOM = 420
MAIN_TOP = 420
MAIN_HEIGHT = HEIGHT - MAIN_TOP

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTS = [FONT_BOLD, FONT_BOLD_ITALIC, FONT_REGULAR]

WARRIOR_COLORS = [
    (255, 30, 30), (255, 200, 0), (0, 220, 255),
    (255, 100, 200), (100, 255, 100), (255, 130, 0),
    (180, 80, 255), (255, 255, 255), (255, 240, 80),
    (50, 255, 180), (220, 40, 40), (255, 170, 20),
]

BG_SCHEMES = [
    {"bg1": (5, 0, 10), "bg2": (25, 5, 35), "accent": (220, 30, 80)},
    {"bg1": (0, 5, 20), "bg2": (8, 20, 55), "accent": (50, 130, 255)},
    {"bg1": (0, 10, 5), "bg2": (5, 30, 18), "accent": (30, 200, 100)},
    {"bg1": (10, 0, 0), "bg2": (35, 5, 10), "accent": (255, 60, 60)},
    {"bg1": (12, 8, 0), "bg2": (40, 25, 5), "accent": (255, 170, 30)},
    {"bg1": (2, 2, 2), "bg2": (18, 18, 22), "accent": (200, 200, 200)},
]

WEAPON_TYPES = ['sword', 'hammer', 'axe', 'spear', 'mace']


# ============================================================
# HELPERS
# ============================================================

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

def draw_dark_background(img, scheme):
    draw = ImageDraw.Draw(img)
    bg1, bg2 = scheme['bg1'], scheme['bg2']
    for y in range(MAIN_TOP, HEIGHT):
        ratio = (y - MAIN_TOP) / MAIN_HEIGHT
        r = int(bg1[0] * (1 - ratio) + bg2[0] * ratio)
        g = int(bg1[1] * (1 - ratio) + bg2[1] * ratio)
        b = int(bg1[2] * (1 - ratio) + bg2[2] * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    slash_color = tuple(min(255, c + 10) for c in bg2)
    for i in range(-HEIGHT, WIDTH + HEIGHT, 90):
        draw.line([(i, MAIN_TOP), (i + HEIGHT, HEIGHT)], fill=slash_color, width=1)


def draw_white_bar(img, scheme):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, WHITE_BAR_TOP, WIDTH, WHITE_BAR_BOTTOM], fill=(248, 248, 252))
    draw.rectangle([0, WHITE_BAR_BOTTOM, WIDTH, WHITE_BAR_BOTTOM + 8], fill=scheme['accent'])
    draw.rectangle([0, 0, WIDTH, 90], fill=(0, 0, 0))


def draw_branding(img, scheme):
    draw = ImageDraw.Draw(img)
    font = load_font(FONT_BOLD, 42)
    draw.text((40, 45), "UNCOVERED USA", font=font, fill=(255, 255, 255), anchor='lm')
    dot_x = WIDTH - 180
    draw.ellipse([dot_x - 12, 33, dot_x + 12, 57], fill=(255, 30, 30))
    font_live = load_font(FONT_BOLD, 36)
    draw.text((dot_x + 24, 45), "LIVE", font=font_live, fill=(255, 255, 255), anchor='lm')
    draw.rectangle([0, HEIGHT - 120, WIDTH, HEIGHT], fill=(0, 0, 0, 220))
    draw.rectangle([0, HEIGHT - 128, WIDTH, HEIGHT - 120], fill=scheme['accent'])
    font_cta = load_font(FONT_BOLD, 38)
    draw.text((WIDTH // 2, HEIGHT - 60), "SUBSCRIBE FOR MORE",
              font=font_cta, fill=(220, 220, 220), anchor='mm')


# ============================================================
# WEAPON DRAWING
# ============================================================

def draw_weapon(draw, x, y, size, angle_deg, color):
    angle = math.radians(angle_deg)
    length = size
    end_x = x + int(length * math.cos(angle))
    end_y = y + int(length * math.sin(angle))
    draw.line([(x, y), (end_x, end_y)], fill=(60, 30, 10), width=10)

    weapon_type = random.choice(WEAPON_TYPES)
    if weapon_type == 'sword':
        tip_x = end_x + int(40 * math.cos(angle))
        tip_y = end_y + int(40 * math.sin(angle))
        perp = angle + math.pi / 2
        px = int(15 * math.cos(perp))
        py = int(15 * math.sin(perp))
        draw.polygon([(end_x + px, end_y + py), (end_x - px, end_y - py), (tip_x, tip_y)],
                     fill=(200, 210, 220), outline=(100, 110, 120))
    elif weapon_type == 'hammer':
        perp = angle + math.pi / 2
        px = int(30 * math.cos(perp))
        py = int(30 * math.sin(perp))
        draw.rectangle([end_x - abs(px), end_y - abs(py), end_x + abs(px), end_y + abs(py)],
                       fill=(80, 80, 90), outline=(40, 40, 50))
    elif weapon_type == 'axe':
        perp = angle + math.pi / 2
        px = int(35 * math.cos(perp))
        py = int(35 * math.sin(perp))
        draw.polygon([(end_x, end_y), (end_x + px, end_y + py),
                      (end_x + int(30 * math.cos(angle)), end_y + int(30 * math.sin(angle)))],
                     fill=(190, 190, 200), outline=(90, 90, 100))
    elif weapon_type == 'spear':
        tip_x = end_x + int(60 * math.cos(angle))
        tip_y = end_y + int(60 * math.sin(angle))
        perp = angle + math.pi / 2
        px = int(12 * math.cos(perp))
        py = int(12 * math.sin(perp))
        draw.polygon([(end_x + px, end_y + py), (end_x - px, end_y - py), (tip_x, tip_y)],
                     fill=(220, 220, 230), outline=(120, 120, 130))
    else:
        draw.ellipse([end_x - 20, end_y - 20, end_x + 20, end_y + 20],
                     fill=(80, 80, 90), outline=(40, 40, 50))


# ============================================================
# FRAMES
# ============================================================

def frame_fight(word, scheme, letters_scattered):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    font_hdr = load_font(FONT_BOLD_ITALIC, 40)
    draw.text((WIDTH // 2, 220), "⚔  BATTLE BEGINS  ⚔",
              font=font_hdr, fill=(180, 180, 190), anchor='mm')

    for item in letters_scattered:
        char = item['char']
        x = item['x']; y = item['y']; size = item['size']
        color = item['color']; weapon_angle = item['weapon_angle']
        draw_weapon(draw, x + 30, y + 30, size * 0.9, weapon_angle, (150, 150, 160))
        font = load_font(random.choice(FONTS), size)
        for dx, dy in [(-5, -5), (5, -5), (-5, 5), (5, 5)]:
            draw.text((x + dx, y + dy), char, font=font, fill=(0, 0, 0))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), char, font=font, fill=(0, 0, 0))
        draw.text((x, y), char, font=font, fill=color)

    for _ in range(20):
        sx = random.randint(50, WIDTH - 50)
        sy = random.randint(100, WHITE_BAR_BOTTOM - 50)
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 220, 100))

    draw_branding(img, scheme)
    path = os.path.join(PATHS['temp'], f"f1_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_clash(word, scheme, letters_scattered):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    center_x = WIDTH // 2
    center_y = 210
    for _ in range(40):
        sx = center_x + random.randint(-200, 200)
        sy = center_y + random.randint(-80, 80)
        size = random.randint(3, 8)
        color = random.choice([(255, 220, 100), (255, 150, 50), (255, 255, 200)])
        draw.ellipse([sx - size, sy - size, sx + size, sy + size], fill=color)

    for item in letters_scattered:
        char = item['char']
        x = item['x'] + random.randint(-50, 50)
        y = item['y'] + random.randint(-40, 40)
        size = item['size']; color = item['color']
        draw_weapon(draw, x + 40, y + 30, size * 0.9, item['weapon_angle'] + 45, (200, 200, 210))
        font = load_font(random.choice(FONTS), size)
        for dx, dy in [(-5, -5), (5, -5), (-5, 5), (5, 5)]:
            draw.text((x + dx, y + dy), char, font=font, fill=(0, 0, 0))
        draw.text((x, y), char, font=font, fill=color)

    font_hdr = load_font(FONT_BOLD_ITALIC, 44)
    draw.text((WIDTH // 2, 220), "⚔ CLASH! CLASH! ⚔",
              font=font_hdr, fill=(255, 100, 100), anchor='mm')
    draw_branding(img, scheme)
    path = os.path.join(PATHS['temp'], f"f2_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_forming(word, scheme):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    clean_word = word.strip()[:14]
    size = 110
    if len(clean_word) > 8:
        size = 90
    if len(clean_word) > 11:
        size = 75
    font = load_font(FONT_BOLD, size)
    temp = Image.new('RGB', (10, 10))
    td = ImageDraw.Draw(temp)
    bbox = td.textbbox((0, 0), clean_word, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = (WHITE_BAR_BOTTOM // 2) + 20 - th // 2
    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, -4), (0, 4), (-4, 0), (4, 0)]:
        draw.text((x + dx, y + dy), clean_word, font=font, fill=(60, 60, 70))
    draw.text((x, y), clean_word, font=font, fill=(5, 5, 10))
    draw.rectangle([x - 20, y + th + 20, x + tw + 20, y + th + 28], fill=scheme['accent'])
    font_tag = load_font(FONT_BOLD, 32)
    draw.text((WIDTH // 2, WHITE_BAR_BOTTOM - 40), "★ VICTORY ★",
              font=font_tag, fill=(200, 100, 50), anchor='mm')
    draw_branding(img, scheme)
    path = os.path.join(PATHS['temp'], f"f3_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_explosion(word, scheme, progress=0.5):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    clean_word = word.strip()[:14]
    font = load_font(FONT_BOLD, 90)
    temp = Image.new('RGB', (10, 10))
    td = ImageDraw.Draw(temp)
    bbox = td.textbbox((0, 0), clean_word, font=font)
    tw = bbox[2] - bbox[0]
    x = (WIDTH - tw) // 2
    y = (WHITE_BAR_BOTTOM // 2) + 20 - 40
    draw.text((x, y), clean_word, font=font, fill=(150, 150, 150))
    cx = WIDTH // 2
    cy = WHITE_BAR_BOTTOM + 30
    for _ in range(60):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(30, 350 * progress)
        px = cx + int(dist * math.cos(angle))
        py = cy + int(dist * math.sin(angle))
        size = random.randint(4, 14)
        color = random.choice([(255, 200, 60), (255, 130, 30), (255, 255, 200),
                               (255, 80, 80), (200, 200, 200)])
        draw.ellipse([px - size, py - size, px + size, py + size], fill=color)
    draw.ellipse([cx - 80, cy - 80, cx + 80, cy + 80], fill=(255, 220, 80))
    draw.ellipse([cx - 40, cy - 40, cx + 40, cy + 40], fill=(255, 255, 255))
    word_y = WHITE_BAR_BOTTOM + 100 + int(300 * progress)
    if word_y < HEIGHT - 200:
        font_w = load_font(FONT_BOLD, 110)
        temp2 = Image.new('RGB', (10, 10))
        td2 = ImageDraw.Draw(temp2)
        bbox2 = td2.textbbox((0, 0), clean_word, font=font_w)
        tw2 = bbox2[2] - bbox2[0]
        x2 = (WIDTH - tw2) // 2
        for dx, dy in [(-5, -5), (5, -5), (-5, 5), (5, 5)]:
            draw.text((x2 + dx, word_y + dy), clean_word, font=font_w, fill=(0, 0, 0))
        draw.text((x2, word_y), clean_word, font=font_w, fill=random.choice(WARRIOR_COLORS))
    draw_branding(img, scheme)
    path = os.path.join(PATHS['temp'], f"f4_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_final(word, scheme):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    clean_word = word.strip()[:14]
    font_sm = load_font(FONT_BOLD, 60)
    temp = Image.new('RGB', (10, 10))
    td = ImageDraw.Draw(temp)
    bbox = td.textbbox((0, 0), clean_word, font=font_sm)
    tw = bbox[2] - bbox[0]
    x = (WIDTH - tw) // 2
    y = (WHITE_BAR_BOTTOM // 2) + 20 - 30
    draw.text((x, y), clean_word, font=font_sm, fill=(120, 120, 130))
    display_word = clean_word
    size = 170
    if len(display_word) > 8:
        size = 140
    if len(display_word) > 11:
        size = 110
    letters_data = []
    total_w = 0
    gap = 8
    for char in display_word:
        if char == ' ':
            letters_data.append((' ', 40, None))
            total_w += 40
            continue
        font = load_font(random.choice(FONTS), size)
        td2 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
        bb = td2.textbbox((0, 0), char, font=font)
        w = bb[2] - bb[0] + 20
        color = random.choice(WARRIOR_COLORS)
        letters_data.append((char, w, (font, color)))
        total_w += w + gap
    x_start = (WIDTH - total_w) // 2
    y_base = MAIN_TOP + (MAIN_HEIGHT // 2) - size // 2
    current_x = x_start
    for char, w, data in letters_data:
        if char == ' ':
            current_x += w
            continue
        font, color = data
        y_off = random.randint(-25, 25)
        for dx, dy in [(-8, -8), (8, -8), (-8, 8), (8, 8), (0, -8), (0, 8), (-8, 0), (8, 0)]:
            draw.text((current_x + dx, y_base + y_off + dy), char, font=font, fill=(0, 0, 0))
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, -3), (0, 3), (-3, 0), (3, 0)]:
            draw.text((current_x + dx, y_base + y_off + dy), char, font=font, fill=(0, 0, 0))
        draw.text((current_x, y_base + y_off), char, font=font, fill=color)
        current_x += w + gap
    draw_branding(img, scheme)
    path = os.path.join(PATHS['temp'], f"f5_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


# ============================================================
# SCRIPT SPLIT + TIMING
# ============================================================

def split_script_into_words(script_text):
    """Split script into displayable word units (keeps numbers+units together)."""
    words = script_text.split()
    result = []
    i = 0
    while i < len(words):
        word = words[i].strip()
        if not word:
            i += 1
            continue
        if re.match(r'^\$?\d+(\.\d+)?$', word.replace(',', '')) and i + 1 < len(words):
            nxt = words[i + 1].lower().strip('.,!?')
            if nxt in ['billion', 'million', 'trillion', 'thousand', 'percent',
                       '%', 'dollars', 'years', 'days']:
                result.append(f"{word} {words[i+1]}")
                i += 2
                continue
        result.append(word)
        i += 1
    return result


def calculate_word_timings(words, total_duration):
    """
    Distribute total_duration across words proportionally to character length.
    Longer words get slightly more time; short words get a floor.
    Guarantees sum == total_duration (no drift).
    """
    if not words:
        return []

    weights = [max(len(w), 4) for w in words]
    total_weight = sum(weights)
    timings = [(w / total_weight) * total_duration for w in weights]

    # Fix float drift so the sum exactly equals total_duration
    drift = total_duration - sum(timings)
    timings[-1] += drift
    return timings


def get_frame_plan(word_time):
    """
    Adaptive frame plan based on available time for the word.
    Returns list of (frame_name, weight) — weights sum to 1.0.
    Fast words get fewer frames; slow words get the full battle.
    """
    if word_time < 0.35:
        # Ultra fast — single frame, just the formed word
        return [("form", 1.0)]
    elif word_time < 0.60:
        # Fast — form + quick explosion
        return [("form", 0.75), ("expl", 0.25)]
    elif word_time < 1.00:
        # Medium — quick battle + form
        return [("fight", 0.20), ("form", 0.65), ("expl", 0.15)]
    else:
        # Slow — full 5-frame warrior battle
        return [
            ("fight", 0.10),
            ("clash", 0.10),
            ("form", 0.46),
            ("expl", 0.14),
            ("final", 0.20),
        ]


FRAME_BUILDERS = {
    "fight": lambda w, s, ls: frame_fight(w, s, ls),
    "clash": lambda w, s, ls: frame_clash(w, s, ls),
    "form":  lambda w, s, ls: frame_forming(w, s),
    "expl":  lambda w, s, ls: frame_explosion(w, s, 0.5),
    "final": lambda w, s, ls: frame_final(w, s),
}


# ============================================================
# BUILD VIDEO
# ============================================================

def build_video(frame_paths, frame_durations, audio_path, output_path):
    total_duration = sum(frame_durations)
    concat_file = os.path.join(PATHS['temp'], "seq_concat.txt")
    with open(concat_file, 'w') as f:
        for path, dur in zip(frame_paths, frame_durations):
            abs_path = os.path.abspath(path)
            f.write(f"file '{abs_path}'\n")
            f.write(f"duration {dur}\n")
        f.write(f"file '{os.path.abspath(frame_paths[-1])}'\n")

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

    logger.info(f"FFmpeg: {len(frame_paths)} frames, {total_duration:.1f}s total")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        logger.error(f"FFmpeg failed: {r.stderr[-400:]}")
        return False
    return True


# ============================================================
# MAIN
# ============================================================

def create_text_video(script_data, editor_data=None):
    logger.info("=" * 50)
    logger.info("WARRIOR LETTER BATTLE VIDEO")
    logger.info("=" * 50)

    os.makedirs(PATHS['output_videos'], exist_ok=True)
    os.makedirs(PATHS['temp'], exist_ok=True)

    output_path = os.path.join(PATHS['output_videos'],
                               f"battle_{random.randint(1000, 9999)}.mp4")

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

    # Video duration = audio duration, capped at 59s (Shorts max)
    total_duration = max(8.0, min(59.0, audio_dur))
    logger.info(f"Final video duration: {total_duration:.2f}s (audio: {audio_dur:.2f}s)")

    words = split_script_into_words(script_text)
    logger.info(f"Total words: {len(words)}")

    if not words:
        words = ["Breaking", "News"]

    # No word cap — show every word, synced to audio
    word_timings = calculate_word_timings(words, total_duration)

    logger.info("Word timing plan (first 12):")
    for w, t in zip(words[:12], word_timings[:12]):
        logger.info(f"  '{w}' -> {t:.2f}s")
    if len(words) > 12:
        logger.info(f"  ... and {len(words)-12} more words")

    all_frames = []
    all_durations = []

    for i, word in enumerate(words):
        word_time = word_timings[i]
        plan = get_frame_plan(word_time)
        plan_names = [p[0] for p in plan]

        logger.info(f"Word {i+1}/{len(words)}: '{word}' ({word_time:.2f}s) → {plan_names}")

        # Scattered letters for fight scenes
        letters_scattered = []
        clean_word = word.strip()[:14]
        for j, char in enumerate(clean_word):
            if char == ' ':
                continue
            letters_scattered.append({
                'char': char,
                'x': random.randint(50, WIDTH - 150),
                'y': random.randint(80, WHITE_BAR_BOTTOM - 120),
                'size': random.randint(70, 100),
                'color': random.choice(WARRIOR_COLORS),
                'weapon_angle': random.uniform(-60, 60)
            })

        for frame_name, weight in plan:
            try:
                builder = FRAME_BUILDERS.get(frame_name)
                if not builder:
                    continue
                frame_path = builder(word, scheme, letters_scattered)
                all_frames.append(frame_path)
                all_durations.append(word_time * weight)
            except Exception as e:
                logger.warning(f"{frame_name} fail for '{word}': {e}")

    if not all_frames:
        logger.error("No frames generated")
        return output_path

    logger.info(f"Total frames: {len(all_frames)} across {len(words)} words")
    success = build_video(all_frames, all_durations, audio_path, output_path)

    if not success:
        logger.error("Video build failed")
        return output_path

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"VIDEO READY: {output_path} ({size_mb:.1f}MB)")

    # Cleanup temp frames
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "f[0-9]_*.png")):
            os.remove(f)
    except:
        pass

    return output_path
