import random, requests, textwrap, numpy as np, feedparser
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

print("Starting FINAL PRO MAX Bot - 10/10 Fixed...")

# === CONTENT - Knowledgeable + Trending ===
BANK = [
    {"title": "IPHONE BATTERY SECRET", "script": "Your iPhone battery is dying fast because of one hidden setting Apple never tells you. Go to Settings, Battery, and turn off Background App Refresh. This one trick will give you two extra hours of battery every single day.", "kw": "iphone"},
    {"title": "GOOGLE SEARCH HACK", "script": "Stop wasting hours on fake Google results. Just type site colon reddit dot com before your question. You will get real human answers, not sponsored ads. This saves ten hours a month.", "kw": "laptop"},
    {"title": "ANDROID FAST CHARGE", "script": "Ninety percent of Android users don't know this hidden super fast charging feature. Hold power and volume up together for three seconds. Your phone will charge fifty percent faster.", "kw": "android"},
]

try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=Apple+AI+Google+Tech&hl=en-US&gl=US&ceid=US:en")
    if feed.entries and len(feed.entries[0].title) > 20:
        selected = {"title": "BREAKING TECH NEWS", "script": f"Breaking tech news. {feed.entries[0].title}. This changes everything for tech lovers in America.", "kw": "technology"}
        print("Using Trending")
    else:
        selected = random.choice(BANK)
except:
    selected = random.choice(BANK)

sentences = [s.strip() for s in selected["script"].split('.') if len(s.strip()) > 3]
print(f"Topic: {selected['title']}")

# Avatar
def create_avatar():
    size = 250
    img = Image.new('RGB', (size, size), (255,235,0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0,0,size,size), fill=(255,235,0), outline="black", width=10)
    draw.ellipse((60,60,100,100), fill="black")
    draw.ellipse((150,60,190,100), fill="black")
    draw.arc((60,120,190,210), 20, 160, fill="black", width=10)
    return np.array(img)

avatar_np = create_avatar()

clips=[]
for i, sentence in enumerate(sentences):
    # Fast US Voice - No API
    gTTS(text=sentence, lang='en', tld='us', slow=False).save(f"v{i}.mp3")
    audio = AudioFileClip(f"v{i}.mp3")

    W,H = 1080,1920
    # Script Related Photo
    try:
        url = f"https://loremflickr.com/{W}/{H}/{selected['kw']}?lock={random.randint(1,99999)}"
        img = Image.open(BytesIO(requests.get(url, timeout=20).content)).convert("RGB").resize((W,H))
    except:
        img = Image.new('RGB', (W,H), (20,20,50))

    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 1380, W, H), fill=(0,0,0))

    try:
        font_cap = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
    except:
        font_cap = ImageFont.load_default()
        font_title = font_cap

    draw.text((40,70), selected["title"], fill=(255,235,0), font=font_title, stroke_width=4, stroke_fill="black")

    # Caption at bottom
    wrapped = textwrap.fill(sentence.upper(), width=28)
    y = 1420
    for line in wrapped.split('\n'):
        bbox = draw.textbbox((0,0), line, font=font_cap)
        x = (W - (bbox[2]-bbox[0]))//2
        draw.text((x,y), line, fill="white", font=font_cap, stroke_width=5, stroke_fill="black")
        y+=65

    base = ImageClip(np.array(img)).set_duration(audio.duration)
    animated = base.resize(lambda t: 1 + 0.03*t) # Animation
    avatar_clip = ImageClip(avatar_np).set_duration(audio.duration).set_position((400, 1100)).resize(0.8)

    final_c = CompositeVideoClip([animated, avatar_clip]).set_audio(audio)
    clips.append(final_c)

final = concatenate_videoclips(clips, method="compose")
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
print("FINAL DONE - All 10 Fixed")
