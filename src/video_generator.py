import os
from moviepy.editor import *
from tts_engine import generate_voice
import config
from PIL import Image, ImageDraw, ImageFont

def create_text_image(text, width, fontsize=50, color='white'):
    # PIL se text ki image banao - ImageMagick ki zarurat nahi
    img = Image.new('RGBA', (width, 200), (0,0,0,0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Word wrap
    words = text.split()
    lines = []
    line = ""
    for w in words:
        if len(line + " " + w) * (fontsize*0.6) < width:
            line += " " + w
        else:
            lines.append(line)
            line = w
    lines.append(line)
    
    y = 10
    for l in lines:
        draw.text((10, y), l.strip(), font=font, fill=color)
        y += fontsize + 10
    
    img_path = f"/tmp/text_{abs(hash(text))}.png"
    img.crop((0,0,width,y)).save(img_path)
    return img_path

def create_video(script_data, story):
    W, H = config.VIDEO_W, config.VIDEO_H

    if isinstance(script_data, dict):
        full_script = script_data.get('full_script') or script_data.get('script') or str(script_data)
        sources = script_data.get('sources', 'Verified Sources')
    else:
        full_script = str(script_data)
        sources = 'Verified Sources'

    if isinstance(story, dict):
        title = story.get('title', 'Breaking News')
        published = story.get('published', '')
        single_source = story.get('single_source', False)
    else:
        title = str(story)[:100]
        published = ''
        single_source = False

    voice_path = generate_voice(full_script)
    audio = AudioFileClip(voice_path)
    duration = min(audio.duration + 0.5, config.MAX_VIDEO_DURATION)

    bg = ColorClip(size=(W,H), color=(10,10,30), duration=duration)

    # PIL se title image banao
    title_img_path = create_text_image(title[:80], W-100, fontsize=55, color='white')
    title_clip = ImageClip(title_img_path).set_position(('center', H*0.2)).set_duration(duration)

    src_img_path = create_text_image(f"Sources: {sources} | {published}", W-80, fontsize=25, color='lightgray')
    src_clip = ImageClip(src_img_path).set_position(('center', H*0.9)).set_duration(duration)

    clips = [bg, title_clip, src_clip]
    if single_source:
        dev_img_path = create_text_image("DEVELOPING STORY - Single Source", 600, fontsize=40, color='yellow')
        dev = ImageClip(dev_img_path).set_position(('center', 50)).set_duration(duration)
        clips.append(dev)

    final = CompositeVideoClip(clips, size=(W,H)).set_audio(audio)
    out_path = f"{config.OUTPUT_DIR}/news_{int(audio.duration)}.mp4"
    final.write_videofile(out_path, fps=24, codec='libx264', preset='ultrafast', threads=2, bitrate="3000k")
    return out_path
