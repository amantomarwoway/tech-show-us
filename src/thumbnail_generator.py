from PIL import Image, ImageDraw, ImageFont
import textwrap, os
import config

def create_thumbnail(script_data, story):
    W, H = 1280, 720
    img = Image.new('RGB', (W,H), color=(15,15,40))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except: font = ImageFont.load_default()

    # --- FIX ---
    if isinstance(story, dict):
        story_title = story.get('title', 'Breaking News')
    else:
        story_title = str(story)[:100]

    if isinstance(script_data, dict):
        sources = script_data.get('sources', 'USA NEWS')
    else:
        sources = 'USA NEWS'

    title = "\n".join(textwrap.wrap(story_title[:70], width=20))
    draw.text((50,150), title, font=font, fill=(255,255,255))
    draw.text((50,600), f"{sources} | USA NEWS", fill=(255,255,0))

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = f"{config.OUTPUT_DIR}/thumb.jpg"
    img.save(path)
    return path
