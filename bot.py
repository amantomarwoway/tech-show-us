import random, requests, feedparser, re, os, time, textwrap
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_audioclips, TextClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("Starting VIRAL CLONER FACE 30s Bot...")

CHANNEL_LINK = "https://www.youtube.com/@techoperationtheatre"
CHANNEL_NAME = "Tech Operation Theatre"
OLD_SHORTS = "https://www.youtube.com/@techoperationtheatre/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def get_ai_clip(query):
    try:
        if not query: query = "technology"
        clean_query = query.strip().replace(' ', ',')
        url = f"https://loremflickr.com/1080/1920/{clean_query}?lock={random.randint(1,999999)}"
        img_path = f"/tmp/clip_{int(time.time())}.jpg"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(img_path, 'wb') as f:
                f.write(r.content)
            print(f"AI Clip Mil Gaya: {query}")
            return img_path
        return None
    except Exception as e:
        print(f"Clip Error: {e}")
        return None

# --- NAYA ADD KIYA: HUMAN FACE WALA ---
def get_human_face_clip(query):
    try:
        # Face wale queries
        face_queries = [
            f"{query} man face talking",
            f"{query} person face speaking portrait",
            f"tech man face talking"
        ]
        for q in face_queries:
            vid = get_pexels_video(q)
            if vid:
                print(f"FACE VIDEO MIL GAYA: {q}")
                return vid, False
        # Fallback AI Face
        print("AI FACE use ho raha hai")
        ai_url = f"https://loremflickr.com/1080/1920/man,face,portrait,tech?lock={random.randint(1,999999)}"
        img_path = f"/tmp/face_{int(time.time())}.jpg"
        r = requests.get(ai_url, timeout=30)
        if r.status_code == 200:
            with open(img_path, 'wb') as f:
                f.write(r.content)
            return img_path, True
        return None, False
    except:
        return None, False

def create_skyblue_captions(full_text, audio_duration):
    try:
        if not full_text: return []
        words = full_text.split()
        if not words: return []
        clips = []
        per_word = audio_duration / max(len(words), 1)
        for i, word in enumerate(words):
            txt = TextClip(word.upper(), fontsize=58, color='#00D4FF', font='Arial-Bold', stroke_color='black', stroke_width=3, method='label').set_duration(per_word).set_start(i * per_word)
            txt = txt.set_position(('center', 0.78), relative=True)
            clips.append(txt)
        return clips
    except Exception as e:
        print(f"Caption Error: {e}")
        return []

BIG_CREATORS = [
    {"id": "UC6-F5tO8uklgE9Zy8IvbdFw", "name": "Marques Brownlee", "handle": "@MKBHD"},
    {"id": "UCBJycsmduvYEL83R_U4JriQ", "name": "Mrwhosetheboss", "handle": "@Mrwhosetheboss"},
    {"id": "UCsTcErHg8oDvUnTzoqsYeNw", "name": "Unbox Therapy", "handle": "@UnboxTherapy"},
    {"id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Linus Tech Tips", "handle": "@LinusTechTips"},
    {"id": "UCW5OrZ_CJ6GdY4Slc8Rbjyg", "name": "Tech Burner", "handle": "@TechBurner"},
    {"id": "UCqwUrSlWBP7mTfbArq8F9hg", "name": "Gadgets 360", "handle": "@Gadgets360"},
]
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
    print("Big creators ki viral shorts check kar raha hu...")
    random.shuffle(BIG_CREATORS)
    for creator in BIG_CREATORS[:3]:
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={creator['id']}"
            feed = feedparser.parse(feed_url)
            if not feed.entries: continue
            latest = feed.entries[0]
            title = latest.title
            description = latest.get('summary', '') or latest.get('description', '')
            link = latest.link
            if len(title) < 100 and len(title) > 10:
                print(f"VIRAL FOUND from {creator['name']}: {title}")
                keywords = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower()
                pexels_query = ' '.join(keywords.split()[:4])
                return {"original_title": title, "original_desc": description, "original_link": link, "creator_name": creator['name'], "pexels_query": pexels_query, "search": keywords[:30]}
        except: continue
    return None

def get_pexels_video(query):
    print(f"Pexels search: {query}")
    try:
        if not PEXELS_API_KEY: return None
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=5&orientation=portrait&size=medium"
        headers = {"Authorization": PEXELS_API_KEY}
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code!= 200: return None
        videos = resp.json().get('videos', [])
        if not videos: return None
        video = random.choice(videos)
        files = sorted(video['video_files'], key=lambda x: x['width'], reverse=True)
        best = next((f for f in files if f['width'] >= 720), files[0])
        r = requests.get(best['link'], stream=True, timeout=60)
        with open("bg_video.mp4", "wb") as out:
            for chunk in r.iter_content(chunk_size=1024*1024): out.write(chunk)
        return "bg_video.mp4"
    except: return None

viral = get_viral_from_big_creator()
if viral:
    topic_title = viral["original_title"]; topic_search = viral["search"]; pexels_q = viral["pexels_query"]
    cloned_desc = viral["original_desc"]; cloned_link = viral["original_link"]
else:
    fallback = random.choice(BACKUP_TOPICS)
    topic_title = fallback["title"]; topic_search = fallback["search"]; pexels_q = fallback["query"]
    cloned_desc = ""; cloned_link = ""

# --- 30 SEC VOICE ---
if viral:
    script_text = f"{topic_title}. {cloned_desc[:150]} This viral technology is trending in USA right now. {topic_search} is something everyone is searching. Here is the secret trick you must know to make it work. This will save your time and money. Subscribe for more viral tech shorts."
else:
    script_text = f"{topic_title}. This is a secret trick about {topic_search}. Most people don't know this hidden feature. If you enable this one setting, your device will become twice as fast. This is trending in USA and going viral. Let me show you how it works step by step. Subscribe to {CHANNEL_NAME} for more."

gTTS(text=script_text, lang='en', tld='us', slow=False).save("voice.mp3")
time.sleep(1)
audio = AudioFileClip("voice.mp3")
TARGET = 30
if audio.duration < TARGET:
    loop_times = int(TARGET // audio.duration) + 2
    audio = concatenate_audioclips([audio]*loop_times).subclip(0, TARGET)
    audio.write_audiofile("voice_30.mp3")
    audio = AudioFileClip("voice_30.mp3")
else:
    audio = audio.subclip(0, TARGET)
safe_duration = audio.duration
W, H = 1080, 1920

# --- YAHAN EDIT KIYA HAI - AB FACE WALA LAYEGA ---
bg_path, is_image = get_human_face_clip(pexels_q or topic_search)

# Agar face wala bhi fail ho gaya to purana wala logic
if not bg_path:
    print("Face nahi mila, Normal video try kar raha hu")
    temp_path = get_pexels_video(pexels_q or topic_search)
    if temp_path:
        bg_path = temp_path
        is_image = False
    else:
        ai_path = get_ai_clip(pexels_q or topic_search)
        bg_path = ai_path
        is_image = True

if bg_path and os.path.exists(bg_path):
    if is_image:
        bg_clip = ImageClip(bg_path).set_duration(safe_duration).resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.05*t)
    else:
        bg_clip = VideoFileClip(bg_path).without_audio().resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
        bg_clip = bg_clip.loop(duration=safe_duration) if bg_clip.duration < safe_duration else bg_clip.subclip(0, safe_duration)
else:
    img = Image.new("RGB", (W,H), (10,10,40))
    bg_clip = ImageClip(np.array(img)).set_duration(safe_duration)

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

overlay_clip = create_overlay(safe_duration, topic_title, topic_search)
caption_clips = create_skyblue_captions(script_text, safe_duration)
final = CompositeVideoClip([bg_clip, overlay_clip, *caption_clips], size=(W,H)).set_duration(safe_duration).set_audio(audio)
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', threads=2)
print(f"DONE {final.duration}s")

from upload_youtube import upload_video
if viral:
    final_title = f"{viral['original_title']} 🔥"
    final_desc = f"""{viral['original_title']}\n\n{cloned_desc[:300]}\n\nThis is similar to video by {viral['creator_name']} - {cloned_link}\n\n👉 Watch More: {OLD_SHORTS}\n👉 Subscribe: {CHANNEL_LINK}\n\nOriginal Inspiration: {viral['creator_name']} {viral['original_link']}\n\n#viral #tech #shorts #trending #firsttimeinusa #{topic_search.replace(' ','')} #{viral['creator_name'].replace(' ','')}\n\nCredit: Pexels Stock\n"""
    final_tags = [topic_search, viral['creator_name'], "tech shorts", "viral tech", "first time in usa", "cloned viral", "trending"]
else:
    final_title = f"{topic_title} 🔥 | First Time in USA"
    final_desc = f"{topic_title}\n\nSearch: {topic_search}\n\n👉 Watch More: {OLD_SHORTS}\n👉 Subscribe: {CHANNEL_LINK}\n\n#tech #shorts #viral"
    final_tags = [topic_search, "tech tips", "viral"]
upload_video("final_shorts.mp4", final_title[:95], final_desc, final_tags[:15])
print(f"Uploaded CLONED VIRAL 30s: {final_title}")
