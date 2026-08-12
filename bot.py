import random, requests, feedparser, re, os, time, textwrap
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("Starting VIRAL CLONER + MIX TECH Bot...")

CHANNEL_LINK = "https://www.youtube.com/@amantomarwoway"
CHANNEL_NAME = "Aman Tomar Wow Way"
OLD_SHORTS = "https://www.youtube.com/@amantomarwoway/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

# --- BIG CREATORS LIST - INKI VIRAL SHORTS CLONE HOGI ---
BIG_CREATORS = [
    # Channel ID : Name (Tech / Innovation niche ke bade creators)
    {"id": "UC6-F5tO8uklgE9Zy8IvbdFw", "name": "Marques Brownlee", "handle": "@MKBHD"}, # MKBHD
    {"id": "UCBJycsmduvYEL83R_U4JriQ", "name": "Mrwhosetheboss", "handle": "@Mrwhosetheboss"},
    {"id": "UCsTcErHg8oDvUnTzoqsYeNw", "name": "Unbox Therapy", "handle": "@UnboxTherapy"},
    {"id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Linus Tech Tips", "handle": "@LinusTechTips"},
    {"id": "UCW5OrZ_CJ6GdY4Slc8Rbjyg", "name": "Tech Burner", "handle": "@TechBurner"},
    {"id": "UCqwUrSlWBP7mTfbArq8F9hg", "name": "Gadgets 360", "handle": "@Gadgets360"},
]

# --- BACKUP 50 MIX TOPICS (Agar cloning fail ho to) ---
BACKUP_TOPICS = [
    {"query": "smartphone close up tech", "title": "Secret Android setting you should turn on", "search": "android secret setting"},
    {"query": "iphone screen technology", "title": "iPhone hidden feature nobody knows", "search": "iphone secret trick"},
    {"query": "laptop keyboard technology", "title": "Secret laptop setting that boosts speed 2x", "search": "laptop speed setting"},
    {"query": "windows 11 laptop screen", "title": "Hidden Windows 11 feature you missed", "search": "windows 11 secret"},
    {"query": "luxury van seat rotation", "title": "Revolutionary car seat technology from China", "search": "adjustable car seat"},
    {"query": "electric car tesla interior", "title": "Tesla's new feature is mind blowing", "search": "tesla new feature"},
    {"query": "robot technology future", "title": "This robot can do everything", "search": "future robot tech"},
    {"query": "ai artificial intelligence chip", "title": "New AI chip changes everything", "search": "ai chip technology"},
]

def get_viral_from_big_creator():
    """Bade creator ki latest viral video nikalta hai"""
    print("Big creators ki viral shorts check kar raha hu...")
    random.shuffle(BIG_CREATORS)
    for creator in BIG_CREATORS[:3]: # 3 creators try karega
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={creator['id']}"
            feed = feedparser.parse(feed_url)
            if not feed.entries: continue
            # Latest video jo Short hai (title chhota hota hai shorts ka)
            latest = feed.entries[0]
            title = latest.title
            description = latest.get('summary', '') or latest.get('description', '')
            link = latest.link
            
            # Check if title looks viral (short title = likely short)
            if len(title) < 100 and len(title) > 10:
                print(f"VIRAL FOUND from {creator['name']}: {title}")
                # Extract keywords for Pexels search
                keywords = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower()
                # Pexels query = first 3 words
                pexels_query = ' '.join(keywords.split()[:4])
                return {
                    "original_title": title,
                    "original_desc": description,
                    "original_link": link,
                    "creator_name": creator['name'],
                    "pexels_query": pexels_query,
                    "search": keywords[:30]
                }
        except Exception as e:
            print(f"Error fetching {creator['name']}: {e}")
            continue
    print("No viral found, using backup topic")
    return None

def get_pexels_video(query):
    print(f"Pexels search: {query}")
    try:
        if not PEXELS_API_KEY:
            print("No API key")
            return None
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=5&orientation=portrait&size=medium"
        headers = {"Authorization": PEXELS_API_KEY}
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"Pexels Error {resp.status_code}")
            return None
        videos = resp.json().get('videos', [])
        if not videos: return None
        video = random.choice(videos)
        files = sorted(video['video_files'], key=lambda x: x['width'], reverse=True)
        best = next((f for f in files if f['width'] >= 720), files[0])
        r = requests.get(best['link'], stream=True, timeout=60)
        with open("bg_video.mp4", "wb") as out:
            for chunk in r.iter_content(chunk_size=1024*1024):
                out.write(chunk)
        return "bg_video.mp4"
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- STEP 1: TRY VIRAL CLONING ---
viral = get_viral_from_big_creator()

if viral:
    # Cloned topic
    topic_title = viral["original_title"]
    topic_search = viral["search"]
    pexels_q = viral["pexels_query"]
    cloned_desc = viral["original_desc"]
    cloned_link = viral["original_link"]
    print(f"CLONING MODE: {topic_title}")
else:
    # Fallback to backup
    fallback = random.choice(BACKUP_TOPICS)
    topic_title = fallback["title"]
    topic_search = fallback["search"]
    pexels_q = fallback["query"]
    cloned_desc = ""
    cloned_link = ""
    print(f"BACKUP MODE: {topic_title}")

bg_path = get_pexels_video(pexels_q or topic_search)
if not bg_path:
    bg_path = get_pexels_video(topic_search)

# --- Voice ---
script_text = f"{topic_title}. This viral technology is trending now. {topic_search}. Secret trick you must know. Subscribe."
gTTS(text=script_text, lang='en', tld='us', slow=False).save("voice.mp3")
audio = AudioFileClip("voice.mp3")

W, H = 1080, 1920
if bg_path and os.path.exists(bg_path):
    bg_clip = VideoFileClip(bg_path).without_audio()
    bg_clip = bg_clip.resize(height=H)
    if bg_clip.w > W:
        bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
    if bg_clip.duration < audio.duration:
        bg_clip = bg_clip.loop(duration=audio.duration)
    else:
        bg_clip = bg_clip.subclip(0, audio.duration)
else:
    img = Image.new("RGB", (W,H), (10,10,40))
    bg_clip = ImageClip(np.array(img)).set_duration(audio.duration)

def create_overlay(duration, title, search):
    overlay = Image.new('RGBA', (W,H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    try: font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except: font_big = ImageFont.load_default()
    try: font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except: font_small = ImageFont.load_default()

    draw.rounded_rectangle((50, 1160, W-50, 1230), radius=35, fill=(255,255,255,240))
    draw.text((95, 1175), f'Search "{search[:25]}"', fill=(60,60,60), font=font_small)
    draw.rectangle((0, 1300, W, H), fill=(0,0,0,190))
    y = 1330
    for line in textwrap.wrap(title + " #tech #shorts #viral", width=28):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=62
        if y>1650: break
    draw.text((35, 1700), f"@{CHANNEL_NAME} • Subscribe", fill=(200,200,200), font=font_small)
    return ImageClip(np.array(overlay)).set_duration(duration)

overlay_clip = create_overlay(audio.duration, topic_title, topic_search)
final = CompositeVideoClip([bg_clip, overlay_clip], size=(W,H)).set_audio(audio)
if final.duration < 25:
    final = final.loop(duration=26)
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac')
print(f"DONE {final.duration}s")

# --- UPLOAD WITH CLONED DESCRIPTION + TAGS ---
from upload_youtube import upload_video

if viral:
    # Same title as viral creator + twist
    final_title = f"{viral['original_title']} 🔥"
    # Same description pattern + your links
    final_desc = f"""{viral['original_title']}

{cloned_desc[:300]}

This is similar to video by {viral['creator_name']} - {cloned_link}

👉 Watch More: {OLD_SHORTS}
👉 Subscribe: {CHANNEL_LINK}

Original Inspiration: {viral['creator_name']} {viral['original_link']}

#viral #tech #shorts #trending #firsttimeinusa #{topic_search.replace(' ','')} #{viral['creator_name'].replace(' ','')}

Credit: Pexels Stock
"""
    final_tags = [topic_search, viral['creator_name'], "tech shorts", "viral tech", "first time in usa", "cloned viral", "trending"]
else:
    final_title = f"{topic_title} 🔥 | First Time in USA"
    final_desc = f"{topic_title}\n\nSearch: {topic_search}\n\n👉 Watch More: {OLD_SHORTS}\n👉 Subscribe: {CHANNEL_LINK}\n\n#tech #shorts #viral"
    final_tags = [topic_search, "tech tips", "viral"]

upload_video("final_shorts.mp4", final_title[:95], final_desc, final_tags[:15])
print(f"Uploaded CLONED VIRAL: {final_title}")
