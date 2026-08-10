import random, requests, textwrap, asyncio, numpy as np, feedparser, edge_tts
from io import BytesIO
from moviepy.editor import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

print("Finding valuable topic...")

# --- 100% VALUE CONTENT ---
KNOWLEDGE_BANK = [
    {"title": "iPhone Battery Secret", "text": "Your iPhone battery is dying fast because of this one setting. Go to Settings, Battery, turn off Background App Refresh. Your battery will last 2 hours more daily.", "kw": "iphone"},
    {"title": "Hidden Google Trick", "text": "This Google hidden trick will save you 10 hours a month. Type site colon reddit dot com before any search to get real answers, not ads.", "kw": "laptop"},
    {"title": "Apple Foldable Leaked", "text": "Apple's first foldable iPhone will have zero crease and cost 2000 dollars. Samsung paid 10 million for this technology but Apple made it better.", "kw": "iphone"},
]

# Try trending for value
try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=tech+tips+AI+Apple&hl=en-US&gl=US&ceid=US:en")
    if feed.entries and random.random() > 0.5:
        topic = feed.entries[0].title
        selected = {"title": topic, "text": f"Breaking tech news! {topic}. Here is what it means for you and how you can use it to save money.", "kw": "technology"}
    else:
        selected = random.choice(KNOWLEDGE_BANK)
except:
    selected = random.choice(KNOWLEDGE_BANK)

SCRIPT_TEXT = selected["text"]
KEYWORD = selected["kw"]
sentences = [s.strip() for s in SCRIPT_TEXT.split('.') if len(s.strip())>2]

# --- NATIVE AMERICAN VOICE (FAST & NATURAL) ---
async def make_voice(text, file):
    # en-US-GuyNeural = Real American Male voice, fast and confident
    await edge_tts.Communicate(text, "en-US-GuyNeural", rate="+20%").save(file)

clips=[]
for i, sentence in enumerate(sentences):
    asyncio.run(make_voice(sentence, f"v{i}.mp3"))
    audio = AudioFileClip(f"v{i}.mp3")

    W,H=1080,1920
    try:
        url=f"https://loremflickr.com/{W}/{H}/{KEYWORD}?lock={random.randint(1,9999)}"
        img=Image.open(BytesIO(requests.get(url, timeout=20).content)).convert("RGB").resize((W,H))
    except:
        img=Image.new('RGB',(W,H),(10,10,40))
    img=Image.blend(img, Image.new('RGB',(W,H),(0,0,0)), 0.5)
    draw=ImageDraw.Draw(img)
    try:
        font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
    except:
        font=ImageFont.load_default()

    wrapped=textwrap.fill(sentence.upper(), width=20)
    y=1050
    for line in wrapped.split('\n'):
        bbox=draw.textbbox((0,0), line, font=font)
        draw.text(((W-(bbox[2]-bbox[0]))//2, y), line, fill="white", font=font, stroke_width=8, stroke_fill="black")
        y+=80

    draw.text((40,80), selected["title"].upper(), fill=(255,230,0), font=font, stroke_width=5, stroke_fill="black")
    clip=ImageClip(np.array(img)).set_duration(audio.duration).set_audio(audio)
    clips.append(clip)

final=concatenate_videoclips(clips, method="compose")
final.write_videofile("final_shorts.mp4", fps=24, codec='libx264', audio_codec='aac')
print("Native US Video Done")
