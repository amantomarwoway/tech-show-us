import random, requests, textwrap, numpy as np, feedparser
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

print("Starting PRO US Bot - Full Features...")

# === 1. KNOWLEDGEABLE + TRENDING (Jo pehle tha wahi) ===
KNOWLEDGE_BANK = [
    {
        "title": "IPHONE BATTERY SECRET",
        "script": "Your iPhone battery is dying fast because of one hidden setting Apple never tells you. Go to Settings, Battery, and turn off Background App Refresh. This one trick will give you two extra hours of battery every single day. Try it now and thank me later.",
        "kw": "iphone"
    },
    {
        "title": "GOOGLE SEARCH HACK",
        "script": "Stop wasting hours on fake Google results. Here is a secret trick that will save you ten hours a month. Just type site colon reddit dot com before your question. You will get real human answers, not sponsored ads. This is the best productivity hack of 2025.",
        "kw": "laptop"
    },
    {
        "title": "ANDROID FAST CHARGE",
        "script": "Ninety percent of Android users have no idea about this hidden super fast charging feature. Just hold your power button and volume up button together for three seconds. Your phone will charge fifty percent faster. Share this with your friends.",
        "kw": "android"
    },
]

# Trending news try karega (agar fail hua to BANK se lega)
try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=Apple+AI+Google+Tech+Tips&hl=en-US&gl=US&ceid=US:en")
    if feed.entries and len(feed.entries[0].title) > 15:
        news_title = feed.entries[0].title
        selected = {
            "title": "BREAKING TECH NEWS",
            "script": f"Breaking tech news for you. {news_title}. This changes everything for tech lovers in America. Here is what it means for you and how you can save money with this update.",
            "kw": "technology"
        }
        print("Using Trending News")
    else:
        selected = random.choice(KNOWLEDGE_BANK)
except:
    selected = random.choice(KNOWLEDGE_BANK)

print(f"Topic: {selected['title']}")
sentences = [s.strip() for s in selected["script"].split('.') if len(s.strip()) > 3]

# === 2. FULL HD VIDEO CREATION ===
clips = []
for i, sentence in enumerate(sentences):
    print(f"Making clip {i+1}/{len(sentences)}: {sentence[:30]}")
    audio_file = f"voice_{i}.mp3"

    # FAST US VOICE (No API, Fixed - No speedx error)
    tts = gTTS(text=sentence, lang='en', tld='us', slow=False)
    tts.save(audio_file)
    audio = AudioFileClip(audio_file) # <-- Error fix yahi hai, speedx hataya

    # HD Image
    W, H = 1080, 1920
    try:
        url = f"https://picsum.photos/{W}/{H}?random={random.randint(1,99999)}"
        resp = requests.get(url, timeout=25)
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img = img.resize((W, H), Image.LANCZOS)
    except Exception as e:
        print(f"Image fail {e}, using solid")
        img = Image.new('RGB', (W, H), (15, 15, 45))

    # Dark overlay for text readability - PRO LOOK
    img = Image.blend(img, Image.new('RGB', (W, H), (0, 0, 0)), 0.45)

    draw = ImageDraw.Draw(img)
    try:
        font_main = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
    except:
        font_main = ImageFont.load_default()
        font_title = ImageFont.load_default()

    # Title at top - Yellow PRO
    draw.text((40, 80), selected["title"], fill=(255, 235, 0), font=font_title, stroke_width=6, stroke_fill="black")

    # Main sentence in center - White with black stroke
    wrapped = textwrap.fill(sentence.upper(), width=22)
    lines = wrapped.split('\n')
    total_h = len(lines) * 80
    y_start = (H - total_h) // 2 + 100

    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_main)
        text_w = bbox[2] - bbox[0]
        x = (W - text_w) // 2
        draw.text((x, y), line, fill="white", font=font_main, stroke_width=8, stroke_fill="black")
        y += 85

    clip = ImageClip(np.array(img)).set_duration(audio.duration).set_audio(audio)
    clips.append(clip)

# === 3. FINAL EXPORT - HD QUALITY (Same as before) ===
final_video = concatenate_videoclips(clips, method="compose")
final_video.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', bitrate="5000k", preset="ultrafast")

print("PRO Video Ready - All Features Kept")
