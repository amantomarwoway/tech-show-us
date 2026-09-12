# src/video_generator.py - REMAINING PARTS - DETAILED FIXED
# Ye functions ko apne existing video_generator.py me add / replace kar

def make_74k_bottom_text_FINAL(text, total_duration):
    """Bottom black strip with small text - detailed retention"""
    from PIL import Image, ImageDraw, ImageFont
    import os, random

    WIDTH = 1080
    HEIGHT = 200 # BLACK_BOTTOM_STRIP
    viral_text = text.strip()[:80]

    img = Image.new('RGB', (WIDTH, HEIGHT), (0,0,0))
    d = ImageDraw.Draw(img)

    try:
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
    except:
        f = ImageFont.load_default()

    # Center text - bottom hook
    d.text((WIDTH//2, HEIGHT//2), viral_text, font=f, fill=(255,255,255), anchor="mm")

    p = f"temp/bottom_final_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p, quality=95)

    from moviepy.editor import ImageClip
    # Bottom position - 1920-200
    clip = ImageClip(p).set_duration(total_duration).set_position((0, 1920-200))
    return clip

def make_black_rounded_border_FINAL(total_duration):
    """Black rounded border 16px - detailed premium look"""
    from PIL import Image, ImageDraw
    import os, random

    WIDTH, HEIGHT = 1080, 1920
    BORDER = 16
    RADIUS = 38

    # Transparent image with border
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0,0,0,0))
    d = ImageDraw.Draw(img)

    # Outer black rect with rounded corners
    d.rounded_rectangle([0,0,WIDTH,HEIGHT], radius=RADIUS, fill=None, outline=(0,0,0,255), width=BORDER)

    p = f"temp/border_final_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)

    from moviepy.editor import ImageClip
    clip = ImageClip(p).set_duration(total_duration).set_position((0,0))
    return clip

def word_clip_FINAL(word, dur, is_keyword=False, is_first_word=False):
    """Word clip FINAL - 74K style - detailed retention 1.6X punch first words"""
    from PIL import Image, ImageDraw, ImageFont
    import os, random

    word = word.upper().strip()
    if not word:
        word = "SHOCKING"

    # Size based on keyword
    if is_first_word:
        font_size = 92 # 1.6X punch - first 5 words bada
        stroke = 8
        fill = (255, 255, 0) # Yellow for first shocking words
    elif is_keyword:
        font_size = 78 # 1.2X punch - BRUTAL TARIFFS etc
        stroke = 6
        fill = (255, 255, 255)
    else:
        font_size = 62
        stroke = 5
        fill = (255, 255, 255)

    # Black outline + white/yellow fill
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Measure
    dummy = Image.new('RGB', (10,10))
    dmy = ImageDraw.Draw(dummy)
    try:
        bbox = dmy.textbbox((0,0), word, font=font, stroke_width=stroke)
        w = bbox[2]-bbox[0] + 20
        h = bbox[3]-bbox[1] + 20
    except:
        w = len(word)*font_size*0.6 + 20
        h = font_size + 20

    img = Image.new('RGBA', (int(w), int(h)), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.text((w//2, h//2), word, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0,0,0), anchor="mm")

    p = f"temp/txt_{random.randint(1,999999999)}_{word[:5]}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)

    from moviepy.editor import ImageClip
    clip = ImageClip(p).set_duration(dur).set_position(('center',0.65), relative=True)

    # Resize animation - first words me zyada zoom
    if is_first_word:
        clip = clip.resize(lambda t: 1.4 - 0.25*t/dur if t < dur*0.4 else 1.0)
    else:
        clip = clip.resize(lambda t: 1.15 - 0.15*t/dur if t < dur*0.3 else 1.0)

    return clip
