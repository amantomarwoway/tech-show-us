import random, requests, textwrap, numpy as np, feedparser, re, os, time
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

print("Starting VIRAL CLONE Bot...")

CHANNEL_LINK = "https://www.youtube.com/@amantomarwoway"
CHANNEL_NAME = "Aman Tomar Wow Way"
OLD_SHORTS = "https://www.youtube.com/@amantomarwoway/shorts"

# --- BADE CREATORS JINKI VIDEO CLONE KARNI HAI ---
BIG_CREATORS = [
    "UCBJycsmduvYEL83R_U4JriQ", # MKBHD
    "UCMiJRAwDNSNzuYeN2uWa0pA", # Mrwhosetheboss
    "UCXuqSBlHAE6Xw-yeJA0Tunw", # Linus Tech Tips
    "UCsTcErHg8oDvUnTzoqsYeNw", # Unbox Therapy
    "UC3S0BHgGj0CVo72N3mU3M5A", # ThioJoe - US Tech
]

def get_viral_from_big_creator():
    print("Bade creators ki viral video dhoond raha hu...")
    all_videos = []
    for channel_id in BIG_CREATORS:
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:3]:
                all_videos.append(entry)
        except: pass

    if not all_videos:
        return None

    viral = random.choice(all_videos)
    print(f"VIRAL FOUND: {viral.title} from {viral.author}")
    return viral

def get_own_news_fallback():
    try:
        feed = feedparser.parse("https://techcrunch.com/feed/")
        return feed.entries[0]
    except:
        return None

# --- STEP 1: VIRAL CLONE YA OWN NEWS ---
viral_video = get_viral_from_big_creator()

if viral_video:
    original_title = viral_video.title
    original_desc = viral_video.get('summary','')[:300]
    original_author = viral_video.get('author','Big Creator')
    viral_title = f"{original_title} | FIRST TIME IN USA 🇺🇸"
    if len(viral_title) > 95: viral_title = original_title[:92]
    viral_desc = f"""{original_title}

{original_desc}

This topic is currently VIRAL on YouTube by {original_author}. Full breakdown in this Shorts.

🔥 This is trending in USA right now and first time explained for American audience.

👉 Watch More Viral US Tech Shorts: {OLD_SHORTS}
👉 Subscribe to {CHANNEL_NAME}: {CHANNEL_LINK}

Credit: Inspired by {original_author} viral video - {viral_video.link}

#viral #trending #usanews #firsttimeinamerica #usatech #{re.sub('[^a-zA-Z0-9]','',original_title.split()[0].lower())}

Original Topic: {original_title}
"""
    viral_tags = [original_title.split()[0].lower(), "viral shorts", "first time in america", "usa tech news", "trending usa", original_author.lower()] + re.findall(r'\b\w+\b', original_title.lower())[:8]
    script_source_title = original_title
else:
    news = get_own_news_fallback()
    viral_title = f"FIRST TIME IN AMERICA: {news.title[:50]}! 🤯"
    viral_desc = f"{news.title}\n\nSubscribe: {CHANNEL_LINK}"
    viral_tags = ["usa news", "first time in america"]
    script_source_title = news.title
    original_author = "US News"

print(f"FINAL TITLE: {viral_title}")

# --- SCRIPT FOR VOICE ---
script = f"Breaking! {script_source_title}. This video is viral on YouTube right now by {original_author}. Everyone in America is talking about this. I will explain this first time in America for you. Subscribe to {CHANNEL_NAME} for more viral updates."

# --- NEW: ROBUST IMAGE FETCH WITH RETRY ---
def fetch_image_bytes(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            print(f"Fetching image attempt {attempt+1}: {url[:80]}...")
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 5000:
                return resp.content
            else:
                print(f"Bad status {resp.status_code} or small content, retrying...")
        except Exception as e:
            print(f"Image fetch failed attempt {attempt+1}: {e}")
        sleep_time = (attempt+1)*5
        print(f"Waiting {sleep_time}s before retry...")
        time.sleep(sleep_time)
    print("All retries failed for image, using fallback color")
    return None

# --- VIDEO GENERATION - TOP CREATOR STYLE ---
def get_clip(sentence, duration, idx):
    prompt = requests.utils.quote(f"{sentence}, viral tech, usa, cinematic, vibrant, HDR, 8k, colorful")
    url = f"https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1920&nologo=true&seed={random.randint(1,999999)}"
    img_bytes = fetch_image_bytes(url, max_retries=5)
    if img_bytes is None:
        # Fallback solid image
        img = Image.new("RGB", (1080,1920), (20,20,40))
    else:
        try:
            img = Image.open(BytesIO(img_bytes)).convert("RGB").resize((1080,1920))
        except:
            img = Image.new("RGB", (1080,1920), (20,20,40))
    img = ImageEnhance.Color(img).enhance(2.0)
    img = ImageEnhance.Contrast(img).enhance(1.4)
    clip = ImageClip(np.array(img)).set_duration(duration)
    clip = clip.resize(lambda t: 1 + 0.15 * t / duration)
    return clip.set_position(('center','center'))

sentences = [s.strip() for s in script.split('.') if len(s.strip()) > 3]

try:
    av_data = fetch_image_bytes(f"https://randomuser.me/api/portraits/men/{random.randint(10,70)}.jpg", max_retries=3)
    if av_data:
        avatar_pil = Image.open(BytesIO(av_data)).convert("RGBA").resize((280,280))
    else:
        raise Exception("no avatar")
    mask = Image.new("L", (280,280), 0)
    ImageDraw.Draw(mask).ellipse((0,0,280,280), fill=255)
    avatar_pil.putalpha(mask)
    avatar_np = np.array(avatar_pil)
except:
    avatar_np = np.array(Image.new('RGB', (280,280), (255,235,0)))

clips=[]
idx=0
for i, sentence in enumerate(sentences):
    gTTS(text=sentence, lang='en', tld='us', slow=False).save(f"v{i}.mp3")
    audio = AudioFileClip(f"v{i}.mp3")
    words = sentence.split()
    chunk_duration = audio.duration / len(words) if words else 0.5
    for w_idx, word in enumerate(words):
        bg_clip = get_clip(sentence, chunk_duration, idx); idx+=1
        W,H = 1080,1920
        text_img = Image.new('RGBA', (W,H), (0,0,0,0))
        draw = ImageDraw.Draw(text_img, 'RGBA')
        if i==0 and w_idx<2:
            draw.rectangle((0,0,W,300), fill=(255,0,0,220))
            try: font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
            except: font_big = ImageFont.load_default()
            draw.text((40,90), "🔥 VIRAL IN USA!", fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        draw.rectangle((0,1350,W,H), fill=(0,0,0,190))
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 78)
        except: font = ImageFont.load_default()
        y=1450
        full_line = " ".join(words[max(0,w_idx-2):w_idx+3])
        for line in textwrap.fill(full_line.upper(), width=16).split('\n'):
            bbox = draw.textbbox((0,0), line, font=font)
            x = (W - (bbox[2]-bbox[0]))//2
            color = (255,235,0) if word.upper() in line else (255,255,255)
            draw.text((x,y), line, fill=color, font=font, stroke_width=8, stroke_fill="black")
            y+=95
            break
        text_clip = ImageClip(np.array(text_img)).set_duration(chunk_duration)
        avatar_clip = ImageClip(avatar_np).set_duration(chunk_duration).set_position((750, 1050))
        final_c = CompositeVideoClip([bg_clip, text_clip, avatar_clip], size=(W,H))
        clips.append(final_c)

all_audio = [AudioFileClip(f"v{j}.mp3") for j in range(len(sentences))]
full_audio = concatenate_audioclips(all_audio)
final_video = concatenate_videoclips(clips, method="compose").set_duration(full_audio.duration).set_audio(full_audio)
final = final_video
while final.duration < 32:
    final = concatenate_videoclips([final, final_video], method="compose")
    if final.duration > 36: break
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac')
print(f"DONE {final.duration}s")

from upload_youtube import upload_video
upload_video("final_shorts.mp4", viral_title, viral_desc, viral_tags[:15])
