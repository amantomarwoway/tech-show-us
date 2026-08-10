import textwrap, random
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

scripts = [
    "WAIT Apple is making a foldable iPhone! Leaks say it will have NO CREASE. It will launch in 2026 for 2000 dollars. Would you buy it?",
    "STOP SCROLLING Your phone is listening to you! Go to Settings Privacy and turn off Ads Personalization right now to stop tracking!",
    "This AI trick will blow your mind! Your phone can remove any object from photos in one tap. Just open Google Photos and tap Eraser!"
]

full_text = random.choice(scripts)
sentences = full_text.split('. ')
print(full_text)

bg_colors = [(10,10,25), (90,0,30), (0,70,50), (30,0,90)]

clips = []
for i, sentence in enumerate(sentences):
    if len(sentence.strip()) < 3:
        continue
    tts = gTTS(text=sentence, lang='en', tld='us')
    mp3 = f"v{i}.mp3"
    tts.save(mp3)
    audio = AudioFileClip(mp3)

    W, H = 1080, 1920
    img = Image.new('RGB', (W, H), color=bg_colors[i % len(bg_colors)])
    draw = ImageDraw.Draw(img)
    
    # Safe font
    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
    except:
        pass

    # Hook for first
    if i == 0:
        draw.text((100, 250), "WAIT!!", fill=(255,255,0), font=font)

    wrapped = textwrap.fill(sentence.upper(), width=22)
    draw.multiline_text((80, 700), wrapped, fill=(255,255,255), font=font, spacing=10)

    draw.text((80, 1700), "Tech Operation Theatre", fill=(200,200,200), font=font)

    path = f"b{i}.png"
    img.save(path)

    ic = ImageClip(path).set_duration(audio.duration)
    ic = ic.set_audio(audio)
    clips.append(ic)

final = concatenate_videoclips(clips)
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
