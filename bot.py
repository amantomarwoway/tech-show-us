import random, requests, feedparser, re, os, time, textwrap
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np

print("Starting FINAL ALL-IN-ONE Bot...")

if os.path.exists("bg_video.mp4"):
    os.remove("bg_video.mp4")

CHANNEL_LINK = "https://www.youtube.com/@techoperationtheatre"
CHANNEL_NAME = "Tech Operation Theatre"
OLD_SHORTS = "https://www.youtube.com/@techoperationtheatre/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

BANNED_WORDS = ["jethalal", "bapuji", "taarak", "ooltah", "chashmah", "tmkoc", "bhabi", "kapil", "bigg boss"]

def get_pexels_video(query):
    try:
        if not PEXELS_API_KEY: return None
        # Bright studio add kiya lighting ke liye
        full_q = query + " bright studio light professional"
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(full_q)}&per_page=10&orientation=portrait&size=medium"
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
        print(f"VIDEO MILA: {query}")
        return "bg_video.mp4"
    except Exception as e:
        print(f"Pexels Error {e}")
        return None

def get_human_face_clip(query):
    try:
        # YAHAN RELATED FIX KIYA - query topic se related hai
        face_queries = [
            f"american man explaining {query} technology bright",
            f"tech youtuber talking {query} studio light",
            f"man with {query} bright professional"
        ]
        for q in face_queries:
            vid = get_pexels_video(q)
            if vid:
                return vid, False

        # AI fallback bhi related
        ai_url = f"https://loremflickr.com/1080/1920/american,man,{query.replace(' ',',')},tech,bright,studio?lock={random.randint(1,99999)}"
        img_path = f"/tmp/face_{int(time.time())}.jpg"
        r = requests.get(ai_url, timeout=30)
        if r.status_code == 200:
            with open(img_path, 'wb') as f: f.write(r.content)
            im = Image.open(img_path)
            im = ImageEnhance.Brightness(im).enhance(1.5)
            im = ImageEnhance.Color(im).enhance(1.3)
            im.save(img_path)
            return img_path, True
        return None, False
    except: return None, False

def create_skyblue_captions(full_text, audio_duration):
    words = full_text.split()
    clips = []
    per_word = audio_duration / max(len(words),1)
    for i, word in enumerate(words):
        img = Image.new('RGBA', (1080, 200), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        except: font = ImageFont.load_default()
        text = word.upper()
        bbox = draw.textbbox((0,0), text, font=font)
        w = bbox[2]-bbox[0]
        x = (1080 - w)//2
        draw.text((x, 30), text, fill="black", font=font, stroke_width=14, stroke_fill="black")
        draw.text((x, 30), text, fill="#00D4FF", font=font)
        clip = ImageClip(np.array(img)).set_duration(per_word).set_start(i * per_word)
        clip = clip.set_position(('center', 0.75), relative=True)
        clips.append(clip)
    return clips

BIG_CREATORS = [
    {"id": "UC6-F5tO8uklgE9Zy8IvbdFw", "name": "Marques Brownlee"},
    {"id": "UCBJycsmduvYEL83R_U4JriQ", "name": "Mrwhosetheboss"},
    {"id": "UCsTcErHg8oDvUnTzoqsYeNw", "name": "Unbox Therapy"},
]
BACKUP_TOPICS = [
    {"query": "iphone technology", "title": "Secret iPhone setting you should turn on", "search": "iphone secret trick"},
    {"query": "android technology", "title": "Secret Android setting you should turn on", "search": "android secret"},
]

def get_viral_from_big_creator():
    random.shuffle(BIG_CREATORS)
    for creator in BIG_CREATORS:
        try:
            feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={creator['id']}")
            if not feed.entries: continue
            for entry in feed.entries[:6]:
                title = entry.title
                if any(b in title.lower() for b in BANNED_WORDS):
                    continue
                if 10 < len(title) < 100:
                    kw = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower()
                    return {"original_title": title, "original_desc": entry.get('summary',''), "original_link": entry.link, "creator_name": creator['name'], "pexels_query": ' '.join(kw.split()[:3]), "search": kw[:30]}
        except: continue
    return None

viral = get_viral_from_big_creator()
if viral:
    topic_title = viral["original_title"]; topic_search = viral["search"]; pexels_q = viral["pexels_query"]
    cloned_desc = viral["original_desc"]
else:
    fb = random.choice(BACKUP_TOPICS)
    topic_title = fb["title"]; topic_search = fb["search"]; pexels_q = fb["query"]
    cloned_desc = ""

# SCRIPT - TERI DEMAND
script_text = f"Hello friends, {topic_title}. {cloned_desc[:100]} This viral technology is trending in USA right now. {topic_search} is something everyone is searching. Here is the secret trick you must know. So subscribe my channel for more."

print(f"SCRIPT: {script_text}")

gTTS(text=script_text, lang='en', tld='com', slow=False).save("voice.mp3")
time.sleep(1)
audio = AudioFileClip("voice.mp3")
TARGET = 30
if audio.duration < TARGET:
    audio = concatenate_audioclips([audio]* (int(TARGET//audio.duration)+2)).subclip(0, TARGET)
    audio.write_audiofile("voice_30.mp3")
    audio = AudioFileClip("voice_30.mp3")
else:
    audio = audio.subclip(0, TARGET)

# SOUND TEZ - BINA FX KE ERROR FREE
audio = audio.volumex(1.8)

W, H = 1080, 1920
bg_path, is_image = get_human_face_clip(pexels_q or topic_search)

if not bg_path:
    bg_path = get_pexels_video(pexels_q)

if bg_path and os.path.exists(bg_path):
    if is_image:
        bg_clip = ImageClip(bg_path).set_duration(audio.duration).resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
    else:
        bg_clip = VideoFileClip(bg_path).without_audio().resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
        bg_clip = bg_clip.loop(duration=audio.duration) if bg_clip.duration < audio.duration else bg_clip.subclip(0, audio.duration)
else:
    bg_clip = ImageClip(np.array(Image.new("RGB", (W,H), (10,10,40)))).set_duration(audio.duration)

def create_overlay(duration, title, search):
    overlay = Image.new('RGBA', (W,H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    try: font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except: font_big = ImageFont.load_default()
    try: font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except: font_small = ImageFont.load_default()
    draw.rounded_rectangle((50, 1160, W-50, 1230), radius=35, fill=(255,255,255,240))
    draw.text((95, 1175), f'Search "{search[:25]}"', fill=(60,60,60), font=font_small)
    draw.rectangle((0, 1300, W, H), fill=(0,0,0,190))
    y = 1330
    for line in textwrap.wrap(title + " #tech #shorts", width=28):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=60
        if y>1650: break
    return ImageClip(np.array(overlay)).set_duration(duration)

overlay_clip = create_overlay(audio.duration, topic_title, topic_search)
caption_clips = create_skyblue_captions(script_text, audio.duration)
final = CompositeVideoClip([bg_clip, overlay_clip, *caption_clips], size=(W,H)).set_duration(audio.duration).set_audio(audio)
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', threads=2)

from upload_youtube import upload_video
upload_video("final_shorts.mp4", f"{topic_title} 🔥"[:95], f"{topic_title}\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n#tech #shorts", [topic_search, "tech"])
