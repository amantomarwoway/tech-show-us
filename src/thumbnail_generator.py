from PIL import Image, ImageDraw, ImageFont
import textwrap, os
import config

def create_thumbnail(script_data, story):
    W, H = 1280, 720
    img = Image.new('RGB', (W,H), color=(15,15,40))
    draw = ImageDraw.Draw(img)
    try: font = ImageFont.truetype("DejaVuSans-Bold.ttf", 70)
    except: font = ImageFont.load_default()

    title = "\n".join(textwrap.wrap(story['title'][:70], width=20))
    draw.text((50,150), title, font=font, fill=(255,255,255))
    draw.text((50,600), f"{script_data['sources']} | USA NEWS", fill=(255,255,0))

    path = f"{config.OUTPUT_DIR}/thumb.jpg"
    img.save(path)
    return path
