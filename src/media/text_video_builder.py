"""
src/media/text_video_builder.py - WARRIOR LETTER BATTLE v3
- Top white bar: word formation via letter battle
- NEW: Yellow bottom bar with 26 letters (A-Z) in eternal 13v13 war
- Weapons: guns, bombs, tanks, missiles
- Letters die & revive in endless loop
- Smooth time-based animation (higher FPS per word)
- Full script shown, synced to audio
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

# ============================================================
# YELLOW BATTLE BAR (bottom of Shorts frame)
# ============================================================
YELLOW_BAR_TOP = HEIGHT - 460      # 1460
YELLOW_BAR_BOTTOM = HEIGHT - 240   # 1680
YELLOW_BAR_HEIGHT = YELLOW_BAR_BOTTOM - YELLOW_BAR_TOP
YELLOW_COLOR = (255, 215, 0)
YELLOW_DARK = (200, 160, 0)
RED_TEAM_COLOR = (200, 30, 30)
BLUE_TEAM_COLOR = (30, 80, 200)

# ============================================================
# SMOOTHNESS KNOBS — tune here
# ============================================================
TARGET_FPS = 15               # frames per second of video
MIN_FRAMES_PER_WORD = 4       # fast words still get a few
MAX_FRAMES_PER_WORD = 25      # cap to avoid explosion

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
    except Exception:
        try:
            return ImageFont.truetype(FONT_BOLD, size)
        except Exception:
            return ImageFont.load_default()


def _stable_hash(s):
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h


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
# BACKGROUND & BRANDING
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


def draw_top_branding(img):
    draw = ImageDraw.Draw(img)
    font = load_font(FONT_BOLD, 42)
    draw.text((40, 45), "UNCOVERED USA", font=font, fill=(255, 255, 255), anchor='lm')
    dot_x = WIDTH - 180
    draw.ellipse([dot_x - 12, 33, dot_x + 12, 57], fill=(255, 30, 30))
    font_live = load_font(FONT_BOLD, 36)
    draw.text((dot_x + 24, 45), "LIVE", font=font_live, fill=(255, 255, 255), anchor='lm')


def draw_bottom_cta(img, scheme):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, HEIGHT - 120, WIDTH, HEIGHT], fill=(0, 0, 0))
    draw.rectangle([0, HEIGHT - 128, WIDTH, HEIGHT - 120], fill=scheme['accent'])
    font_cta = load_font(FONT_BOLD, 38)
    draw.text((WIDTH // 2, HEIGHT - 60), "SUBSCRIBE FOR MORE",
              font=font_cta, fill=(220, 220, 220), anchor='mm')


# ============================================================
# WEAPON DRAWING (top bar)
# ============================================================

def draw_weapon(draw, x, y, size, angle_deg, color):
    angle = math.radians(angle_deg)
    end_x = x + int(size * math.cos(angle))
    end_y = y + int(size * math.sin(angle))
    draw.line([(x, y), (end_x, end_y)], fill=(60, 30, 10), width=10)
    weapon_type = random.choice(WEAPON_TYPES)
    if weapon_type == 'sword':
        tip_x = end_x + int(40 * math.cos(angle))
        tip_y = end_y + int(40 * math.sin(angle))
        perp = angle + math.pi / 2
        px = int(15 * math.cos(perp)); py = int(15 * math.sin(perp))
        draw.polygon([(end_x + px, end_y + py), (end_x - px, end_y - py), (tip_x, tip_y)],
                     fill=(200, 210, 220), outline=(100, 110, 120))
    elif weapon_type == 'hammer':
        perp = angle + math.pi / 2
        px = int(30 * math.cos(perp)); py = int(30 * math.sin(perp))
        draw.rectangle([end_x - abs(px), end_y - abs(py), end_x + abs(px), end_y + abs(py)],
                       fill=(80, 80, 90), outline=(40, 40, 50))
    elif weapon_type == 'axe':
        perp = angle + math.pi / 2
        px = int(35 * math.cos(perp)); py = int(35 * math.sin(perp))
        draw.polygon([(end_x, end_y), (end_x + px, end_y + py),
                      (end_x + int(30 * math.cos(angle)), end_y + int(30 * math.sin(angle)))],
                     fill=(190, 190, 200), outline=(90, 90, 100))
    elif weapon_type == 'spear':
        tip_x = end_x + int(60 * math.cos(angle))
        tip_y = end_y + int(60 * math.sin(angle))
        perp = angle + math.pi / 2
        px = int(12 * math.cos(perp)); py = int(12 * math.sin(perp))
        draw.polygon([(end_x + px, end_y + py), (end_x - px, end_y - py), (tip_x, tip_y)],
                     fill=(220, 220, 230), outline=(120, 120, 130))
    else:
        draw.ellipse([end_x - 20, end_y - 20, end_x + 20, end_y + 20],
                     fill=(80, 80, 90), outline=(40, 40, 50))


# ============================================================
# YELLOW BAR — LETTER POSITIONS (13 vs 13)
# ============================================================

def _compute_letter_positions():
    """Return dict char -> {'x','y','side'} for all 26 letters."""
    positions = {}
    spacing = 64
    top_row_y = YELLOW_BAR_TOP + 60
    bot_row_y = YELLOW_BAR_TOP + 155

    left_top = "ABCDEFG"    # 7
    left_bot = "HIJKLM"     # 6
    right_top = "NOPQRST"   # 7
    right_bot = "UVWXYZ"    # 6

    for i, c in enumerate(left_top):
        positions[c] = {'x': 30 + i * spacing, 'y': top_row_y, 'side': 'left'}
    for i, c in enumerate(left_bot):
        positions[c] = {'x': 30 + i * spacing, 'y': bot_row_y, 'side': 'left'}

    # Right side: align end near WIDTH-30
    right_end = WIDTH - 30 - 45   # 45 approx letter width
    right_start = right_end - 6 * spacing
    for i, c in enumerate(right_top):
        positions[c] = {'x': right_start + i * spacing, 'y': top_row_y, 'side': 'right'}
    for i, c in enumerate(right_bot):
        positions[c] = {'x': right_start + i * spacing, 'y': bot_row_y, 'side': 'right'}

    return positions


LETTER_POSITIONS = _compute_letter_positions()


# ============================================================
# YELLOW BAR — BATTLE ANIMATION STATE (time-based)
# ============================================================

def get_letter_anim(char, t):
    """Deterministic animation state for a letter at time t."""
    h = _stable_hash(char)
    rng = random.Random(h)

    cycle_len = 7.0 + rng.random() * 4.0        # 7-11 seconds
    phase = ((t * 0.5) + rng.random() * cycle_len) % cycle_len
    phase = phase / cycle_len                    # 0..1

    # Bob
    bob = math.sin(t * 4 + h * 0.01) * 4

    # Life state
    if phase < 0.62:
        status, prog = 'alive', phase / 0.62
    elif phase < 0.70:
        status, prog = 'dying', (phase - 0.62) / 0.08
    elif phase < 0.84:
        status, prog = 'dead', 1.0
    else:
        status, prog = 'reviving', (phase - 0.84) / 0.16

    # Shooting pulse
    shoot_t = (t * 1.8 + h * 0.03) % 1.0
    shooting = shoot_t < 0.12 and status == 'alive'

    weapon = ['gun', 'bomb', 'tank', 'missile'][h % 4]
    return {
        'status': status,
        'progress': prog,
        'bob': bob,
        'shooting': shooting,
        'weapon': weapon,
    }


# ============================================================
# YELLOW BAR — WEAPONS/PROJECTILES
# ============================================================

def _get_projectiles(t):
    """Return list of currently-flying projectiles."""
    projectiles = []
    slot_len = 0.28
    current_slot = int(t / slot_len)

    for i in range(7):  # track 7 most recent slots
        slot = current_slot - i
        if slot < 0:
            continue
        spawn_t = slot * slot_len
        age = t - spawn_t
        if age > slot_len * 6:
            continue

        rng = random.Random(slot * 7919)
        direction = rng.choice([1, -1])
        start_y = rng.randint(YELLOW_BAR_TOP + 45, YELLOW_BAR_BOTTOM - 55)
        ptype = rng.choice(['bullet', 'missile', 'bomb', 'missile'])

        progress = min(1.0, age / (slot_len * 5))
        if direction == 1:
            x = int(-20 + progress * (WIDTH + 40))
        else:
            x = int(WIDTH + 20 - progress * (WIDTH + 40))

        y = start_y
        if ptype == 'missile':
            y += int(math.sin(age * 30) * 10)

        projectiles.append({'type': ptype, 'x': x, 'y': y,
                            'dir': direction, 'age': age})

    return projectiles


def draw_projectile(draw, p):
    x, y = p['x'], p['y']
    d = p['dir']
    if p['type'] == 'bullet':
        draw.ellipse([x - 4, y - 3, x + 4, y + 3], fill=(255, 240, 120))
        draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 255, 200))
    elif p['type'] == 'missile':
        # Body
        draw.ellipse([x - 8, y - 5, x + 8, y + 5], fill=(200, 60, 60))
        # Flame tail
        tail_x = x - d * 14
        draw.polygon([(x - d * 6, y - 4), (tail_x, y), (x - d * 6, y + 4)],
                     fill=(255, 180, 60))
    else:  # bomb
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], fill=(30, 30, 40))
        draw.ellipse([x - 10, y - 10, x + 10, y + 10], outline=(120, 120, 130), width=2)
        # fuse
        draw.line([(x + 8, y - 8), (x + 14, y - 14)], fill=(255, 200, 100), width=3)


# ============================================================
# YELLOW BAR — MAIN RENDER
# ============================================================

def draw_yellow_bar(img, t):
    """Draw the yellow 26-letter battle bar at time t."""
    draw = ImageDraw.Draw(img)

    # Background
    draw.rectangle([0, YELLOW_BAR_TOP, WIDTH, YELLOW_BAR_BOTTOM], fill=YELLOW_COLOR)
    draw.rectangle([0, YELLOW_BAR_TOP, WIDTH, YELLOW_BAR_TOP + 6], fill=(0, 0, 0))
    draw.rectangle([0, YELLOW_BAR_BOTTOM - 6, WIDTH, YELLOW_BAR_BOTTOM], fill=(0, 0, 0))

    # Diagonal yellow stripes for texture
    stripe_color = (255, 235, 90)
    for i in range(-YELLOW_BAR_HEIGHT, WIDTH + YELLOW_BAR_HEIGHT, 120):
        draw.line([(i, YELLOW_BAR_TOP), (i + YELLOW_BAR_HEIGHT, YELLOW_BAR_BOTTOM)],
                  fill=stripe_color, width=2)

    # Title tag
    font_tag = load_font(FONT_BOLD, 22)
    tag_w = 340
    tag_x = (WIDTH - tag_w) // 2
    draw.rectangle([tag_x, YELLOW_BAR_TOP + 8, tag_x + tag_w, YELLOW_BAR_TOP + 38],
                   fill=(20, 20, 20))
    draw.text((WIDTH // 2, YELLOW_BAR_TOP + 23),
              "LIVE LETTER BATTLE  13v13",
              font=font_tag, fill=(255, 215, 0), anchor='mm')

    # VS in middle
    font_vs = load_font(FONT_BOLD, 34)
    draw.text((WIDTH // 2, YELLOW_BAR_TOP + YELLOW_BAR_HEIGHT // 2 + 10), "VS",
              font=font_vs, fill=(180, 20, 20), anchor='mm')

    # Projectiles behind letters
    for p in _get_projectiles(t):
        draw_projectile(draw, p)

    # Letters
    for char, pos in LETTER_POSITIONS.items():
        anim = get_letter_anim(char, t)
        _draw_battle_letter(draw, char, pos, anim)

    # Explosions (deterministic per time)
    for i in range(3):
        slot = int(t / 1.2) + i
        rng = random.Random(slot * 3301)
        if rng.random() < 0.35:
            ex = rng.randint(60, WIDTH - 60)
            ey = rng.randint(YELLOW_BAR_TOP + 50, YELLOW_BAR_BOTTOM - 50)
            age = (t - slot * 1.2) / 0.6
            if 0 <= age <= 1:
                r = int(8 + 40 * age)
                a = int(255 * (1 - age))
                # star burst
                for k in range(6):
                    ang = k * math.pi / 3 + age * 2
                    exr = ex + int(r * math.cos(ang))
                    eyr = ey + int(r * math.sin(ang))
                    draw.ellipse([exr - 5, eyr - 5, exr + 5, eyr + 5],
                                 fill=(255, 200, 60))
                draw.ellipse([ex - r // 2, ey - r // 2, ex + r // 2, ey + r // 2],
                             fill=(255, 240, 120))


def _draw_battle_letter(draw, char, pos, anim):
    x, y = pos['x'], pos['y']
    side = pos['side']
    base_color = RED_TEAM_COLOR if side == 'left' else BLUE_TEAM_COLOR

    status = anim['status']
    prog = anim['progress']
    bob = anim['bob']

    # Size and color depending on life state
    if status == 'dying':
        size = int(48 - 30 * prog)
        color = tuple(int(c * (1 - 0.5 * prog)) for c in base_color)
        y_off = int(prog * 22)
    elif status == 'dead':
        size = 16
        color = (90, 90, 90)
        y_off = 22
    elif status == 'reviving':
        size = int(16 + 32 * prog)
        color = tuple(int(c * (0.35 + 0.65 * prog)) for c in base_color)
        y_off = int(22 * (1 - prog))
    else:
        size = 48
        color = base_color
        y_off = 0

    cx = x + int(bob)
    cy = y + y_off

    # Muzzle flash direction
    muzzle_dir = 1 if side == 'left' else -1

    # Draw weapon muzzle if shooting
    if anim['shooting']:
        mx = cx + muzzle_dir * 26
        draw.ellipse([mx - 12, cy - 12, mx + 12, cy + 12], fill=(255, 255, 120))
        draw.ellipse([mx - 6, cy - 6, mx + 6, cy + 6], fill=(255, 255, 255))

    # Letter with outline
    font = load_font(FONT_BOLD, size)
    for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, -3), (0, 3), (-3, 0), (3, 0)]:
        draw.text((cx + dx, cy + dy), char, font=font, fill=(0, 0, 0), anchor='mm')
    draw.text((cx, cy), char, font=font, fill=color, anchor='mm')

    # Skull for dead
    if status == 'dead':
        draw.ellipse([cx - 8, cy - 6, cx + 8, cy + 6], fill=(230, 230, 230))
        draw.ellipse([cx - 4, cy - 3, cx - 1, cy], fill=(0, 0, 0))
        draw.ellipse([cx + 1, cy - 3, cx + 4, cy], fill=(0, 0, 0))


# ============================================================
# TOP BAR FRAMES (word formation)
# ============================================================

def frame_fight(word, scheme, letters_scattered):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    font_hdr = load_font(FONT_BOLD_ITALIC, 40)
    draw.text((WIDTH // 2, 220), "BATTLE BEGINS",
              font=font_hdr, fill=(180, 180, 190), anchor='mm')

    for item in letters_scattered:
        char = item['char']; x = item['x']; y = item['y']
        size = item['size']; color = item['color']; wa = item['weapon_angle']
        draw_weapon(draw, x + 30, y + 30, size * 0.9, wa, (150, 150, 160))
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

    draw_top_branding(img)
    draw_bottom_cta(img, scheme)
    path = os.path.join(PATHS['temp'], f"f1_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_clash(word, scheme, letters_scattered):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    cx = WIDTH // 2
    cy = 210
    for _ in range(40):
        sx = cx + random.randint(-200, 200)
        sy = cy + random.randint(-80, 80)
        sz = random.randint(3, 8)
        color = random.choice([(255, 220, 100), (255, 150, 50), (255, 255, 200)])
        draw.ellipse([sx - sz, sy - sz, sx + sz, sy + sz], fill=color)

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
    draw.text((WIDTH // 2, 220), "CLASH! CLASH!",
              font=font_hdr, fill=(255, 100, 100), anchor='mm')
    draw_top_branding(img)
    draw_bottom_cta(img, scheme)
    path = os.path.join(PATHS['temp'], f"f2_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


def frame_forming(word, scheme, shine_phase=0.0):
    img = Image.new('RGB', (WIDTH, HEIGHT), (10, 5, 15))
    draw_dark_background(img, scheme)
    draw_white_bar(img, scheme)
    draw = ImageDraw.Draw(img)
    clean_word = word.strip()[:14]
    size = 110
    if len(clean_word) > 8: size = 90
    if len(clean_word) > 11: size = 75
    font = load_font(FONT_BOLD, size)
    temp = Image.new('RGB', (10, 10))
    td = ImageDraw.Draw(temp)
    bbox = td.textbbox((0, 0), clean_word, font=font)
    tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
    x = (WIDTH - tw) // 2
    y = (WHITE_BAR_BOTTOM // 2) + 20 - th // 2
    for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (0, -4), (0, 4), (-4, 0), (4, 0)]:
        draw.text((x + dx, y + dy), clean_word, font=font, fill=(60, 60, 70))
    draw.text((x, y), clean_word, font=font, fill=(5, 5, 10))

    # Moving shine
    shine_x = int(x + (tw + 80) * shine_phase) - 40
    if x <= shine_x <= x + tw:
        draw.rectangle([shine_x, y - 10, shine_x + 25, y + th + 10],
                       fill=None, outline=(255, 255, 255), width=3)

    draw.rectangle([x - 20, y + th + 20, x + tw + 20, y + th + 28], fill=scheme['accent'])
    font_tag = load_font(FONT_BOLD, 32)
    draw.text((WIDTH // 2, WHITE_BAR_BOTTOM - 40), "VICTORY",
              font=font_tag, fill=(200, 100, 50), anchor='mm')
    draw_top_branding(img)
    draw_bottom_cta(img, scheme)
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
        sz = random.randint(4, 14)
        color = random.choice([(255, 200, 60), (255, 130, 30), (255, 255, 200),
                               (255, 80, 80), (200, 200, 200)])
        draw.ellipse([px - sz, py - sz, px + sz, py + sz], fill=color)
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
    draw_top_branding(img)
    draw_bottom_cta(img, scheme)
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
    size = 170
    if len(clean_word) > 8: size = 140
    if len(clean_word) > 11: size = 110
    letters_data = []
    total_w = 0
    gap = 8
    for char in clean_word:
        if char == ' ':
            letters_data.append((' ', 40, None)); total_w += 40; continue
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
            current_x += w; continue
        font, color = data
        y_off = random.randint(-25, 25)
        for dx, dy in [(-8, -8), (8, -8), (-8, 8), (8, 8), (0, -8), (0, 8), (-8, 0), (8, 0)]:
            draw.text((current_x + dx, y_base + y_off + dy), char, font=font, fill=(0, 0, 0))
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, -3), (0, 3), (-3, 0), (3, 0)]:
            draw.text((current_x + dx, y_base + y_off + dy), char, font=font, fill=(0, 0, 0))
        draw.text((current_x, y_base + y_off), char, font=font, fill=color)
        current_x += w + gap
    draw_top_branding(img)
    draw_bottom_cta(img, scheme)
    path = os.path.join(PATHS['temp'], f"f5_{random.randint(1,999999)}.png")
    img.save(path, quality=92)
    return path


# ============================================================
# SCRIPT SPLIT + TIMING
# ============================================================

def split_script_into_words(script_text):
    words = script_text.split()
    result = []
    i = 0
    while i < len(words):
        word = words[i].strip()
        if not word:
            i += 1; continue
        if re.match(r'^\$?\d+(\.\d+)?$', word.replace(',', '')) and i + 1 < len(words):
            nxt = words[i + 1].lower().strip('.,!?')
            if nxt in ['billion', 'million', 'trillion', 'thousand', 'percent',
                       '%', 'dollars', 'years', 'days']:
                result.append(f"{word} {words[i+1]}")
                i += 2; continue
        result.append(word)
        i += 1
    return result


def calculate_word_timings(words, total_duration):
    if not words:
        return []
    weights = [max(len(w), 4) for w in words]
    total_weight = sum(weights)
    timings = [(w / total_weight) * total_duration for w in weights]
    drift = total_duration - sum(timings)
    timings[-1] += drift
    return timings


def get_frames_per_word(word_time):
    n = int(word_time * TARGET_FPS)
    return max(MIN_FRAMES_PER_WORD, min(MAX_FRAMES_PER_WORD, n))


def get_frame_sequence(word_time, frames_per_word):
    """
    Return list of (frame_type, duration_seconds) for a word.
    Higher frames_per_word → smoother transitions.
    """
    # Target proportions
    proportions = [
        ("fight", 0.10),
        ("clash", 0.10),
        ("form",  0.46),
        ("expl",  0.14),
        ("final", 0.20),
    ]
    frames = []
    for ftype, prop in proportions:
        n = max(1, int(round(frames_per_word * prop)))
        for _ in range(n):
            frames.append(ftype)
    # Trim / pad to match frames_per_word
    if len(frames) > frames_per_word:
        frames = frames[:frames_per_word]
    while len(frames) < frames_per_word:
        frames.append("form")
    # Duration per frame
    dur = word_time / len(frames)
    return [(ft, dur) for ft in frames]


# ============================================================
# BUILD VIDEO (with yellow bar overlay)
# ============================================================

def build_video(frame_paths, frame_durations, audio_path, output_path, cumulative_times):
    """
    Concatenate frames + audio via FFmpeg.
    frames: list of PNG paths (already have yellow bar drawn)
    cumulative_times: list of start times for each frame (unused for FFmpeg but kept for reference)
    """
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
        "-vf", f"fps=30,scale={WIDTH}:{HEIGHT},format=yuv420p",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-t", str(total_duration),
        abs_output,
    ]

    logger.info(f"FFmpeg: {len(frame_paths)} frames, {total_duration:.1f}s total")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=2400)
    if r.returncode != 0:
        logger.error(f"FFmpeg failed: {r.stderr[-500:]}")
        return False
    return True


# ============================================================
# MAIN
# ============================================================

def create_text_video(script_data, editor_data=None):
    logger.info("=" * 50)
    logger.info("WARRIOR LETTER BATTLE v3")
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
    except Exception:
        audio_dur = 12

    total_duration = max(8.0, min(59.0, audio_dur))
    logger.info(f"Final video: {total_duration:.2f}s (audio: {audio_dur:.2f}s)")

    words = split_script_into_words(script_text)
    logger.info(f"Total words: {len(words)}")
    if not words:
        words = ["Breaking", "News"]

    word_timings = calculate_word_timings(words, total_duration)

    all_frames = []
    all_durations = []
    cumulative_times = []
    cumulative = 0.0

    for i, word in enumerate(words):
        word_time = word_timings[i]
        n_frames = get_frames_per_word(word_time)
        frame_seq = get_frame_sequence(word_time, n_frames)

        logger.info(f"Word {i+1}/{len(words)}: '{word}' ({word_time:.2f}s, {n_frames} frames)")

        # Precompute scatter once per word
        clean_word = word.strip()[:14]
        scatter_base = []
        for ch in clean_word:
            if ch == ' ':
                continue
            scatter_base.append({
                'char': ch,
                'bx': random.randint(50, WIDTH - 150),
                'by': random.randint(80, WHITE_BAR_BOTTOM - 120),
                'size': random.randint(70, 100),
                'color': random.choice(WARRIOR_COLORS),
                'wa': random.uniform(-60, 60),
            })

        for j, (ftype, dur) in enumerate(frame_seq):
            t = cumulative  # time of this frame
            phase = j / max(1, len(frame_seq) - 1)

            # Build scattered list with slight variation
            letters_scattered = []
            for s in scatter_base:
                letters_scattered.append({
                    'char': s['char'],
                    'x': s['bx'] + int(math.sin(phase * 6.28 + j) * 12),
                    'y': s['by'] + int(math.cos(phase * 6.28 + j) * 8),
                    'size': s['size'],
                    'color': s['color'],
                    'weapon_angle': s['wa'] + phase * 40,
                })

            try:
                if ftype == 'fight':
                    fp = frame_fight(word, scheme, letters_scattered)
                elif ftype == 'clash':
                    fp = frame_clash(word, scheme, letters_scattered)
                elif ftype == 'form':
                    fp = frame_forming(word, scheme, shine_phase=phase)
                elif ftype == 'expl':
                    fp = frame_explosion(word, scheme, progress=phase)
                else:  # final
                    fp = frame_final(word, scheme)

                # *** Overlay yellow battle bar on this frame ***
                img = Image.open(fp).convert('RGB')
                draw_yellow_bar(img, t)
                img.save(fp, quality=92)

                all_frames.append(fp)
                all_durations.append(dur)
                cumulative_times.append(t)
                cumulative += dur

            except Exception as e:
                logger.warning(f"Frame fail ({ftype} for '{word}'): {e}")

    if not all_frames:
        logger.error("No frames generated")
        return output_path

    logger.info(f"Total frames: {len(all_frames)} across {len(words)} words")

    success = build_video(all_frames, all_durations, audio_path, output_path, cumulative_times)
    if not success:
        logger.error("Video build failed")
        return output_path

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"VIDEO READY: {output_path} ({size_mb:.1f}MB)")

    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "f[0-9]_*.png")):
            os.remove(f)
    except Exception:
        pass

    return output_path
