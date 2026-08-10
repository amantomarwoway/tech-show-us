import textwrap
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip
from PIL import Image, ImageDraw, ImageFont
import random

# US Tech Topics - roz random pick hoga
topics = [
    "Apple is secretly testing a foldable iPhone for 2026!",
    "This AI feature will make your Android phone 10 times faster!",
    "Elon Musk just revealed a new Tesla phone feature!",
    "Your phone is tracking you even in airplane mode, here's how to stop it!",
    "Google's new AI can edit your photos like magic!"
]
text = random.choice(topics)
print(f"Topic: {text}")

# 1. Voice
tts = gTTS(text=text, lang='en', tld='com')
tts.save("voice.mp3")

# 2. Image - PIL se (ImageMagick error nahi ayega)
W, H = 1080, 1920
img = Image.new('RGB', (W, H), color=(5, 5, 15))
draw = ImageDraw.Draw(img)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
except:
    font = ImageFont.load_default()

wrapped = textwrap.fill(text, width=22)
bbox = draw.multiline_textbbox((0,0), wrapped, font=font)
tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]

draw.multiline_text(
    ((W-tw)//2, (H-th)//2),
    wrapped,
    font=font,
    fill=(255,255,255),
    align="center",
    spacing=15
)
img.save("bg.png")

# 3. Video
audio = AudioFileClip("voice.mp3")
clip = ImageClip("bg.png").set_duration(audio.duration + 0.6).set_audio(audio)
clip.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
print("Done! Video ready.")
