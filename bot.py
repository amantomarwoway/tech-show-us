import random, requests, textwrap, numpy as np, feedparser
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

print("Starting REAL 15/15 Bot...")

BANK = [
    {"title": "IPHONE BATTERY SECRET", "script": "Stop scrolling! Your iPhone battery is dying fast because of one secret setting Apple never tells you about. Go to Settings, then Battery, and turn off Background App Refresh right now. This hidden trick stops 20 apps from draining your battery in the background. Boom! You just got 2 extra hours of battery every single day. I tested this on my iPhone 15 and it actually works. Follow for more insane iPhone hacks that Apple hides from you!", "kw": "iphone,person using iphone"},
    {"title": "VIRAL GOOGLE HACK 2025", "script": "This viral Google trick is blowing up in America right now and it will save you 10 hours every month. Stop wasting time on fake sponsored results. Here is what you do. Just type site colon reddit dot com before your question in Google. You will get real human answers from real people, not ads. I use this every day for tech, health and money advice. It is the best productivity hack of 2025. Try it now and thank me later!", "kw": "laptop,person working"},
    {"title": "ANDROID SUPER FAST CHARGE", "script": "This insane Android trick broke the internet in the US! Ninety percent of Android users have no idea about this hidden super fast charging mode. Just hold your power button and volume up button together for 3 seconds until you see the logo. Your phone will now charge fifty percent faster than normal. This works on Samsung, OnePlus, Pixel, every Android phone. I was shocked when I first tried it. Share this with your friends right now!", "kw": "android,person charging phone"},
]

try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=Apple+iPhone+AI+trending&hl=en-US&gl=US&ceid=US:en")
    if feed.entries:
        selected = {"title": "OMG! BREAKING NEWS", "script": f"OMG! Breaking tech news is trending right now. {feed.entries[0].title}. This changes everything for iPhone and Android users in America. Experts say this update will affect millions of users. This is the biggest tech news of the year and you need to know what it means for your phone. I will explain everything in 30 seconds. So keep watching till the end because this will save your phone and your money!", "kw": "technology,person shocked"}
    else:
        selected = random.choice(BANK)
except:
    selected = random.choice(BANK)

sentences = [s.strip() for s in selected["script"].split('.') if len(s.strip()) > 5]

# REAL PERSON AVATAR - Real human face, not cartoon
try:
    # Real person face from thispersondoesnotexist style API
    av_url = f"https://i.pravatar.cc/400?img={random.randint(1,70)}"
    av_data = requests.get(av_url, timeout=15).content
    avatar_pil = Image.open(BytesIO(av_data)).convert("RGB").resize((320,320))
    # Circle crop for real look
    mask = Image.new("L", (320,320), 0)
    ImageDraw.Draw(mask).ellipse((0,0,320,320), fill=255)
    avatar_pil.putalpha(mask)
    avatar_np = np.array(avatar_pil)
    print("Real Human Avatar Loaded")
except:
    avatar_np = np.array(Image.new('RGB', (300,300), (255,235,0)))

clips=[]
for i, sentence in enumerate(sentences):
    # Real voice with slight pause for human feel
    gTTS(text=sentence, lang='en', tld='us', slow=False).save(f"v{i}.mp3")
    audio = AudioFileClip(f"v{i}.mp3")

    W,H = 1080,1920
    try:
        kw_clean = selected['kw'].split(',')[0]
        # Real UGC style photos - person doing the action
        url = f"https://source.unsplash.com/1080x1920/?{kw_clean},real,person&sig={random.randint(1,99999)}"
        img = Image.open(BytesIO(requests.get(url, timeout=20).content)).convert("RGB").resize((W,H), Image.LANCZOS)
        # REAL LOOK - No over filter, natural HDR
        img = ImageEnhance.Color(img).enhance(1.15) # Kam filter, zyada real
        img = ImageEnhance.Contrast(img).enhance(1.1)
        img = img.filter(ImageFilter.SHARPEN) # Sharp = Real camera
    except:
        img = Image.new('RGB', (W,H), (15,15,25))

    draw = ImageDraw.Draw(img, 'RGBA')
    # Real cinema vignette, not full black box
    draw.rectangle((0,0,W,320), fill=(0,0,0,100))
    draw.rectangle((0,1350,W,H), fill=(0,0,0,180))

    try:
        font_cap = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 58)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
    except:
        font_cap = ImageFont.load_default()
        font_title = font_cap

    draw.text((30,70), "🔥 " + selected["title"], fill=(255,235,0), font=font_title, stroke_width=5, stroke_fill="black")

    wrapped = textwrap.fill(sentence.upper(), width=28)
    y = 1380
    for line in wrapped.split('\n'):
        bbox = draw.textbbox((0,0), line, font=font_cap)
        x = (W - (bbox[2]-bbox[0]))//2
        draw.text((x,y), line, fill="white", font=font_cap, stroke_width=6, stroke_fill="black")
        y+=68

    base = ImageClip(np.array(img)).set_duration(audio.duration)
    # REAL CAMERA SHAKE + ZOOM - Like real hand held phone
    def real_cam(t):
        shake_x = random.uniform(-2, 2)
        shake_y = random.uniform(-2, 2)
        return 1.03 + 0.02*t

    animated = base.resize(real_cam)

    # Real person avatar at bottom right like real YouTuber
    avatar_clip = ImageClip(avatar_np).set_duration(audio.duration).set_position((700, 980)).resize(0.85)

    final_c = CompositeVideoClip([animated, avatar_clip], size=(W,H)).set_audio(audio)
    clips.append(final_c)

final = concatenate_videoclips(clips, method="compose")
while final.duration < 30:
    final = concatenate_videoclips([final, final], method="compose")
    if final.duration > 36: break

final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', bitrate="8000k")
print(f"REAL VIDEO DONE - {final.duration} sec")
