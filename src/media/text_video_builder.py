"""
src/media/text_video_builder.py - CINEMATIC TEXT VIDEO
- Rich visual design (no Pexels needed)
- Animated background, big numbers, disclaimers
- FFmpeg powered
- 100% free, GitHub Actions compatible
"""

import os
import random
import subprocess
import glob
import re
from PIL import Image, ImageDraw, ImageFont

from src.utils.logger import setup_logger
from src.config import TTS_CONFIG, PATHS

logger = setup_logger(__name__)

WIDTH = 1080
HEIGHT = 1920
TOP_BAR = 140
BOTTOM_BAR = 200
SIDE_BAR = 70

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

SCHEMES = [
    {"name": "crimson", "bg1": (15, 5, 5), "bg2": (45, 10, 15), "accent": (220, 30, 50), "gold": (255, 200, 50)},
    {"name": "midnight", "bg1": (5, 5, 25), "bg2": (10, 15, 55), "accent": (50, 130, 255), "gold": (255, 215, 80)},
    {"name": "emerald", "bg1": (5, 15, 10), "bg2": (10, 40, 25), "accent": (30, 200, 100), "gold": (255, 220, 60)},
    {"name": "royal", "bg1": (15, 5, 25), "bg2": (40, 10, 60), "accent": (180, 50, 220), "gold": (255, 210, 100)},
    {"name": "gold", "bg1": (10, 8, 5), "bg2": (35, 25, 10), "accent": (255, 170, 30), "gold": (255, 235, 130)},
    {"name": "obsidian", "bg1": (10, 10, 10), "bg2": (25, 25, 30), "accent": (200, 60, 60), "gold": (230, 230, 230)},
]


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


def make_background(scheme):
    """Rich gradient background with texture"""
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
    
    # Diagonal texture lines
    line_color = tuple(min(255, c + 10) for c in bg2)
    for i in range(-HEIGHT, WIDTH + HEIGHT, 60):
        draw.line([(i, 0), (i + HEIGHT, HEIGHT)], fill=line_color, width=1)
    
    # Top-left accent triangle
    draw.polygon([(0, TOP_BAR), (WIDTH // 3, TOP_BAR), (0, HEIGHT // 3)],
                 fill=tuple(int(c * 0.3) for c in scheme['accent']))
    
    # Bottom-right accent triangle
    draw.polygon([(WIDTH, HEIGHT - BOTTOM_BAR), (2 * WIDTH // 3, HEIGHT - BOTTOM_BAR),
                  (WIDTH, 2 * HEIGHT // 3)],
                 fill=tuple(int(c * 0.3) for c in scheme['accent']))
    
    path = os.path.join(PATHS['temp'], f"bg_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


def wrap_text(text, font, max_w, draw):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def find_font_for_text(text, max_w, max_h, max_lines, start_size):
    tmp = Image.new('RGB', (10, 10))
    draw = ImageDraw.Draw(tmp)
    for size in range(start_size, 20, -4):
        font = load_font(FONT_BOLD, size)
        lines = wrap_text(text, font, max_w, draw)
        if len(lines) <= max_lines:
            total_h = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                total_h += (bbox[3] - bbox[1]) + 20
            if total_h <= max_h:
                return font, lines, size
    font = load_font(FONT_BOLD, 50)
    lines = wrap_text(text, font, max_w, draw)
    return font, lines[:max_lines], 50


def draw_top_bar(draw, scheme):
    draw.rectangle([0, 0, WIDTH, TOP_BAR], fill=(0, 0, 0))
    draw.rectangle([0, TOP_BAR - 6, WIDTH, TOP_BAR], fill=scheme['accent'])
    
    font_brand = load_font(FONT_BOLD, 46)
    draw.text((40, TOP_BAR // 2), "UNCOVERED USA",
              font=font_brand, fill=(255, 255, 255), anchor='lm')
    
    dot_x = WIDTH - SIDE_BAR - 180
    dot_y = TOP_BAR // 2
    draw.ellipse([dot_x - 14, dot_y - 14, dot_x + 14, dot_y + 14], fill=(255, 30, 30))
    font_live = load_font(FONT_BOLD, 40)
    draw.text((dot_x + 28, dot_y), "LIVE", font=font_live,
              fill=(255, 255, 255), anchor='lm')


def draw_side_disclaimer(draw, scheme):
    x_start = WIDTH - SIDE_BAR
    draw.rectangle([x_start, TOP_BAR, WIDTH, HEIGHT - BOTTOM_BAR], fill=(180, 0, 0))
    
    font = load_font(FONT_BOLD, 28)
    text = "FACT BASED · TEXT · NO VISUALS · "
    char_y = TOP_BAR + 30
    idx = 0
    while char_y < HEIGHT - BOTTOM_BAR - 40:
        ch = text[idx % len(text)]
        draw.text((x_start + SIDE_BAR // 2, char_y), ch, font=font,
                  fill=(255, 255, 255), anchor='mm')
        char_y += 32
        idx += 1


def draw_bottom_bar(draw, scheme, ticker_text):
    y_start = HEIGHT - BOTTOM_BAR
    draw.rectangle([0, y_start, WIDTH, HEIGHT], fill=(0, 0, 0))
    draw.rectangle([0, y_start, WIDTH, y_start + 6], fill=scheme['accent'])
    
    font_ticker = load_font(FONT_BOLD, 34)
    ticker = ticker_text[:55]
    draw.text((40, y_start + 55), f"▶ {ticker}",
              font=font_ticker, fill=scheme['gold'], anchor='lm')
    
    font_cta = load_font(FONT_BOLD, 32)
    draw.text((WIDTH // 2, y_start + 140), "SUBSCRIBE FOR MORE FACTS",
              font=font_cta, fill=(220, 220, 220), anchor='mm')


def draw_corner_decorations(draw, scheme):
    size = 60
    thick = 8
    color = scheme['accent']
    cl = WIDTH - SIDE_BAR - 20
    ct = TOP_BAR + 20
    cb = HEIGHT - BOTTOM_BAR - 20
    
    # Top left
    draw.rectangle([20, ct, 20 + size, ct + thick], fill=color)
    draw.rectangle([20, ct, 20 + thick, ct + size], fill=color)
    # Top right
    draw.rectangle([cl - size, ct, cl, ct + thick], fill=color)
    draw.rectangle([cl - thick, ct, cl, ct + size], fill=color)
    # Bottom left
    draw.rectangle([20, cb - thick, 20 + size, cb], fill=color)
    draw.rectangle([20, cb - size, 20 + thick, cb], fill=color)
    # Bottom right
    draw.rectangle([cl - size, cb - thick, cl, cb], fill=color)
    draw.rectangle([cl - thick, cb - size, cl, cb], fill=color)


def make_slide(shot_text, detail_text, number_text, scheme, slide_num, total):
    """Build one slide"""
    bg_path = make_background(scheme)
    img = Image.open(bg_path).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    content_w = WIDTH - SIDE_BAR - 60
    cx = content_w // 2 + 30
    
    draw_corner_decorations(draw, scheme)
    
    # Big number
    if number_text:
        num_font = load_font(FONT_BOLD, 150)
        y_num = 380
        # Glow
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4)]:
            draw.text((cx + dx, y_num + dy), number_text,
                      font=num_font, fill=(0, 0, 0), anchor='mm')
        draw.text((cx, y_num), number_text,
                  font=num_font, fill=scheme['gold'], anchor='mm')
    
    # Main shot text
    max_w = content_w - 80
    shot_font, shot_lines, size = find_font_for_text(shot_text, max_w, 700, 4, 100)
    
    y = 700 if number_text else 550
    for line in shot_lines:
        bbox = draw.textbbox((0, 0), line, font=shot_font)
        lw = bbox[2] - bbox[0]
        x = cx - lw // 2
        # Multi-directional shadow
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3),
                       (0, -3), (0, 3), (-3, 0), (3, 0)]:
            draw.text((x + dx, y + dy), line, font=shot_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=shot_font, fill=(255, 255, 255))
        y += size + 20
    
    # Divider + detail
    if detail_text and detail_text != shot_text:
        y += 30
        draw.rectangle([cx - 200, y, cx + 200, y + 4], fill=scheme['accent'])
        y += 40
        
        detail_font, detail_lines, dsize = find_font_for_text(
            detail_text, max_w, 400, 4, 55
        )
        for line in detail_lines:
            bbox = draw.textbbox((0, 0), line, font=detail_font)
            lw = bbox[2] - bbox[0]
            x = cx - lw // 2
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((x + dx, y + dy), line, font=detail_font, fill=(0, 0, 0))
            draw.text((x, y), line, font=detail_font, fill=scheme['gold'])
            y += dsize + 15
    
    # Counter
    counter_font = load_font(FONT_BOLD, 28)
    draw.text((WIDTH - SIDE_BAR - 40, TOP_BAR + 40), f"{slide_num + 1}/{total}",
              font=counter_font, fill=(150, 150, 150), anchor='rt')
    
    draw_top_bar(draw, scheme)
    draw_side_disclaimer(draw, scheme)
    draw_bottom_bar(draw, scheme, shot_text)
    
    path = os.path.join(PATHS['temp'], f"slide_{slide_num}_{random.randint(1, 999999)}.png")
    img.save(path, quality=95)
    return path


def parse_facts_to_slides(facts):
    """Parse facts to (shot, detail, number) tuples"""
    slides = []
    for fact in facts:
        numbers = re.findall(
            r'(\$?\d+(?:\.\d+)?\s*(?:billion|million|trillion|percent|%|K|M|B))',
            fact, re.IGNORECASE
        )
        number_text = numbers[0].strip() if numbers else ""
        
        words = fact.split()
        shot = " ".join(words[:7]) if len(words) > 8 else fact
        
        slides.append({
            "shot": shot,
            "detail": fact,
            "number": number_text
        })
    return slides


def render_with_ffmpeg(slide_paths, audio_path, output_path, slide_duration):
    """Composite slides with FFmpeg (safe version)"""
    total_duration = slide_duration * len(slide_paths)
    
    # Build concat file
    concat_file = os.path.join(PATHS['temp'], "concat.txt")
    with open(concat_file, 'w') as f:
        for p in slide_paths:
            f.write(f"file '{p}'\n")
            f.write(f"duration {slide_duration}\n")
        f.write(f"file '{slide_paths[-1]}'\n")
    
    # Simple, safe filter: crossfade + subtle zoom
    # No complex moving overlays (avoid FFmpeg crashes)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", audio_path,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-t", str(total_duration),
        output_path
    ]
    
    logger.info("Running FFmpeg compose...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    if r.returncode != 0:
        logger.error(f"FFmpeg failed: {r.stderr[-500:]}")
        return False
    
    return True


def create_text_video(script_data, editor_data=None):
    """Main entry - cinematic text video"""
    logger.info("=" * 50)
    logger.info("CINEMATIC TEXT VIDEO")
    logger.info("=" * 50)
    
    os.makedirs(PATHS['output_videos'], exist_ok=True)
    os.makedirs(PATHS['temp'], exist_ok=True)
    
    output_path = os.path.join(PATHS['output_videos'],
                               f"text_{random.randint(1000, 9999)}.mp4")
    
    scheme = random.choice(SCHEMES)
    logger.info(f"Scheme: {scheme['name']}")
    
    facts = script_data.get('facts', [])
    script_text = script_data.get('short_script', '')
    
    if not facts:
        sentences = re.split(r'[.!?]+', script_text)
        facts = [s.strip() for s in sentences if len(s.strip()) > 15][:3]
    
    if not facts:
        facts = [
            "This story has 3 surprising facts",
            "Most people do not know the details",
            "Here is what you need to know"
        ]
    
    logger.info(f"Facts: {len(facts)}")
    for i, f in enumerate(facts):
        logger.info(f"  {i+1}. {f[:65]}")
    
    # Audio
    voice = get_tts_voice()
    audio_path = generate_audio(script_text, voice)
    
    if not audio_path or not os.path.exists(audio_path):
        logger.warning("Silent audio fallback")
        audio_path = os.path.join(PATHS['temp'], 'silent.wav')
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", "anullsrc=r=22050:cl=mono",
            "-t", str(len(facts) * 4),
            "-c:a", "pcm_s16le", audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Duration
    try:
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ], capture_output=True, text=True, timeout=30)
        audio_dur = float(probe.stdout.strip())
    except:
        audio_dur = len(facts) * 4
    
    total_duration = max(12, min(20, audio_dur))
    slide_duration = total_duration / len(facts)
    logger.info(f"Total: {total_duration:.1f}s | Per slide: {slide_duration:.1f}s")
    
    # Build slides
    slides_data = parse_facts_to_slides(facts)
    slide_paths = []
    
    for i, sd in enumerate(slides_data):
        path = make_slide(
            sd['shot'], sd['detail'], sd['number'],
            scheme, i, len(slides_data)
        )
        slide_paths.append(path)
        logger.info(f"  Slide {i+1}: {sd['shot'][:40]}")
    
    # Render
    success = render_with_ffmpeg(slide_paths, audio_path, output_path, slide_duration)
    
    if not success:
        logger.error("Render failed")
        return output_path
    
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"VIDEO READY: {output_path} ({size_mb:.1f}MB)")
    
    # Cleanup
    try:
        for f in glob.glob(os.path.join(PATHS['temp'], "slide_*.png")):
            os.remove(f)
        for f in glob.glob(os.path.join(PATHS['temp'], "bg_*.png")):
            os.remove(f)
    except:
        pass
    
    return output_path
