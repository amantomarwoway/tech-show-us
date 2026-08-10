import textwrap, random, os
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont

# 1. VI AL SCRIPTS WITH HOOK
viral_scripts = [
    "WAIT! Apple is making a foldable iPhone! Yes, leaks say it will have NO CREASE. It will launch in 2026 for 2000 dollars. The screen will be bigger than iPad mini. Would you buy it?",
    "STOP SCROLLING! Your phone is listening to you! This hidden setting in Android stops Google from tracking you. Go to Settings, Privacy, and turn off Ads Personalization right now!",
    "This AI trick will blow your mind! Your phone can now remove any object from photos in one tap. Just open Google Photos, tap Eraser, and magic! No Photoshop needed!"
]

full_text = random.choice(viral_scripts)
sentences = full_text.split('. ')
print(f"Script: {full_text}")

# Colors for every 2 sec change
bg_colors = [(10,10,25), (90,0,30), (0,70,50), (30,0,90), (80,50,0)]

clips = []
audio_clips = []
start = 0

for i, sentence in enumerate(sentences):
    if not sentence.strip():
        continue

    # Voice for this sentence
    tts = gTTS(text=sentence, lang='en', tld='us')
    temp_mp3 = f"voice_{i}.mp3"
    tts.save(temp_mp3)
    audio = AudioFileClip(temp_mp3)
    audio_clips.append(audio)

    # Image for this sentence - changes every time
    W, H = 1080, 1920
    color = bg_colors[i % len(bg_colors)]
    img = Image.new('RGB', (W, H), color=color)
    draw = ImageDraw.Draw(img)

    # Border glow
    draw.rectangle([40, 40, W-40, H-40], outline=(255,255,255), width=4)

    # Font
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big

    # If first sentence -> Add HOOK
    if i == 0:
        draw.text((W//2, 300), "WAIT!! 😳", font=font_big, fill=(255,255,0), anchor="mm")

    wrapped = textwrap.fill(sentence.upper(), width=20)
    bbox = draw.multiline_textbbox((0,0), wrapped, font=font_big)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    draw.multiline_text(((W-tw)//2, (H-th)//2), wrapped, font=font_big, fill=(255,255,255), align="center", spacing=12, stroke_width=2, stroke_fill=(0,0,0))

    draw.text((W//2, H-150), "Tech Operation Theatre", font=font_small, fill=(255,255,255), anchor="mm")

    img_path = f"bg_{i}.png"
    img.save(img_path)

    # Create clip with ZOOM animation
    img_clip = ImageClip(img_path).set_duration(audio.duration)
    img_clip = img_clip.resize(lambda t: 1 + 0.05*t) # Zoom effect
    img_clip = img_clip.set_audio(audio)
    img_clip = img_clip.set_start(start)
    clips.append(img_clip)
    start += audio.duration

# Final video - concatenate all small clips
final = CompositeVideoClip(clips, size=(1080,1920))
final = final.set_duration(start)
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
print("PRO Video Ready!")
