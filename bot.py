import textwrap, random, requests
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# PRO VIRAL SCRIPTS
data = [
    ("iphone", "WAIT! Apple is making a foldable iPhone with NO CREASE! Leaks say it will cost 2000 dollars and launch in 2026. Screen will be bigger than iPad mini. Would you buy it? Follow for more!"),
    ("android", "STOP! Your phone is spying on you! This one setting stops Google tracking. Go to Settings, Privacy, Turn off Ads Personalization NOW! Follow for more tech secrets!"),
    ("ai", "This AI trick is INSANE! Remove any person from your photo in one tap. Open Google Photos, tap Tools, Magic Eraser and BOOM! No Photoshop needed! Follow for more!")
]

keyword, full_text = random.choice(data)
sentences = full_text.split('. ')
print(f"Making: {full_text}")

clips = []
for i, sentence in enumerate(sentences):
    if len(sentence.strip()) < 2:
        continue

    tts = gTTS(text=sentence, lang='en', tld='us')
    mp3 = f"v{i}.mp3"
    tts.save(mp3)
    audio = AudioFileClip(mp3)

    # DOWNLOAD REAL IMAGE
    try:
        url = f"https://picsum.photos/seed/{keyword}{i}{random.randint(1,9999)}/1080/1920"
        r = requests.get(url, timeout=15)
        img = Image.open(BytesIO(r.content)).convert("RGB")
        img = img.resize((1080, 1920))
    except:
        img = Image.new('RGB', (1080, 1920), (15,15,30))

    # DARK OVERLAY for text visibility
    dark = Image.new('RGB', (1080, 1920), (0,0,0))
    img = Image.blend(img, dark, 0.55)

    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    except:
        font_big = ImageFont.load_default()
        font_small = font_big

    # HOOK
    if i == 0:
        draw.text((80, 180), "WAIT!!", fill=(255, 235, 59), font=font_big)
    
    # MAIN TEXT
    wrapped = textwrap.fill(sentence.upper(), width=20)
    draw.multiline_text((80, 650), wrapped, fill=(255,255,255), font=font_big, spacing=15)

    # WATERMARK & PROGRESS BAR
    draw.text((80, 1780), "Tech Operation Theatre", fill=(255,255,255), font=font_small)
    # Progress bar
    progress_w = int((i+1)/len(sentences) * 1080)
    draw.rectangle([0, 1900, progress_w, 1920], fill=(255,235,59))

    path = f"bg{i}.png"
    img.save(path)

    # ZOOM EFFECT - professional
    img_clip = ImageClip(path).set_duration(audio.duration).set_audio(audio)
    img_clip = img_clip.resize(lambda t: 1 + 0.03*t)
    clips.append(img_clip)

final = concatenate_videoclips(clips)
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
print("PROFESSIONAL VIDEO DONE!")
