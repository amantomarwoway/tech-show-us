import random, requests, textwrap, numpy as np, feedparser
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# --- TRENDING + EVERGREEN LOGIC ---
print("Checking topic...")
TRENDING_TOPIC = None
KEYWORD = "technology"
SCRIPT_TEXT = ""

try:
    rss = "https://news.google.com/rss/search?q=tech+AI+iPhone&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(rss)
    if feed.entries:
        TRENDING_TOPIC = feed.entries[0].title
        KEYWORD = "iphone" if "iPhone" in TRENDING_TOPIC or "Apple" in TRENDING_TOPIC else "AI" if "AI" in TRENDING_TOPIC else "technology"
        SCRIPT_TEXT = f"BREAKING! {TRENDING_TOPIC}. This is huge update. Follow for more tech news!"
        print(f"TRENDING: {TRENDING_TOPIC}")
except:
    pass

if not TRENDING_TOPIC:
    evergreen = [
        {"text": "Apple is making a foldable iPhone with NO CREASE! It will cost 2000 dollars and launch in 2026.", "kw": "iphone"},
        {"text": "Turn off this setting to stop Google tracking your phone. Go to Settings Privacy now.", "kw": "mobile phone"},
    ]
    pick = random.choice(evergreen)
    SCRIPT_TEXT = pick["text"]
    KEYWORD = pick["kw"]
    print(f"EVERGREEN: {SCRIPT_TEXT}")

sentences = [s.strip() for s in SCRIPT_TEXT.split('.') if len(s.strip())>2]
HIGHLIGHTS = ["BREAKING","APPLE","IPHONE","2000","DOLLARS","NO CREASE","2026","GOOGLE","AI"]

# Avatar download
HAS_AVATAR=False
try:
    r=requests.get("https://api.dicebear.com/7.x/avataaars/png?seed=TechOp&backgroundColor=b6e3f4", timeout=10)
    open("avatar.png","wb").write(r.content)
    HAS_AVATAR=True
except:
    pass

clips=[]
for i, sentence in enumerate(sentences):
    tts = gTTS(text=sentence, lang='en', tld='us')
    tts.save(f"v{i}.mp3")
    audio = AudioFileClip(f"v{i}.mp3")

    W,H=1080,1920
    # Related image
    try:
        url = f"https://loremflickr.com/{W}/{H}/{KEYWORD}?lock={random.randint(1,9999)}"
        resp = requests.get(url, timeout=25)
        img = Image.open(BytesIO(resp.content)).convert("RGB").resize((W,H))
    except:
        img = Image.new('RGB', (W,H), (15,15,45))

    img = Image.blend(img, Image.new('RGB', (W,H), (0,0,0)), 0.45)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        font_s = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    except:
        font=ImageFont.load_default()
        font_s=font

    # Caption professional - niche centre se thoda up
    wrapped = textwrap.fill(sentence.upper(), width=18)
    y = 1080
    for line in wrapped.split('\n'):
        words=line.split()
        line_w=sum([draw.textbbox((0,0), w+" ", font=font)[2] for w in words])
        x=(W-line_w)//2
        for w in words:
            col=(255,230,0) if any(h in w for h in HIGHLIGHTS) else (255,255,255)
            draw.text((x,y), w+" ", fill=col, font=font, stroke_width=7, stroke_fill="black")
            x+=draw.textbbox((0,0), w+" ", font=font)[2]
        y+=85

    if TRENDING_TOPIC and i==0:
        draw.text((40,140), "🔥 TRENDING", fill=(255,60,60), font=font_s, stroke_width=4, stroke_fill="black")

    draw.text((30,1850), "Tech Operation Theatre", fill="white", font=font_s, stroke_width=3, stroke_fill="black")

    base = ImageClip(np.array(img)).set_duration(audio.duration)

    if HAS_AVATAR:
        try:
            av = Image.open("avatar.png").convert("RGBA").resize((300,300))
            mask = Image.new('L', (300,300), 0)
            ImageDraw.Draw(mask).ellipse([0,0,300,300], fill=255)
            av.putalpha(mask)
            a_clip = ImageClip(np.array(av)).set_duration(audio.duration).set_position((720, 1450))
            comp = CompositeVideoClip([base, a_clip]).set_audio(audio)
            clips.append(comp)
            continue
        except:
            pass
    clips.append(base.set_audio(audio))

final = concatenate_videoclips(clips, method="compose")
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac', threads=1, preset='ultrafast')
print("Video Done")
