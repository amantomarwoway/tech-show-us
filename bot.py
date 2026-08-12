import random, requests, feedparser, re, os, time, textwrap
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_audioclips
import moviepy.video.fx.all as vfx
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np

print("Starting FINAL VIRAL CLONER - All Fixed Bot...")

if os.path.exists("bg_video.mp4"):
    os.remove("bg_video.mp4")

CHANNEL_LINK = "https://www.youtube.com/@techoperationtheatre"
CHANNEL_NAME = "Tech Operation Theatre"
OLD_SHORTS = "https://www.youtube.com/@techoperationtheatre/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

BANNED_WORDS = ["jethalal", "bapuji", "taarak", "ooltah", "chashmah", "tmkoc", "bhabi", "kapil", "bigg boss", "anupama"]

# Pexels pehle define kiya taki error na aaye
def get_pexels_video(query):
    print(f"Pexels search: {query}")
    try:
        if not PEXELS_API_KEY: return None
        url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=8&orientation=portrait&size=medium"
        headers = {"Authorization": PEXELS_API_KEY}
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code!= 200: return None
        videos = resp.json().get('videos', [])
        if not videos: return None
        # Bright wala video chun lo
        video = random.choice(videos)
        files = sorted(video['video_files'], key=lambda x: x['width'], reverse=True)
        best = next((f for f in files if f['width'] >= 720), files[0])
        r = requests.get(best['link'], stream=True, timeout=60)
        with open("bg_video.mp4", "wb") as out:
            for chunk in r.iter_content(chunk_size=1024*1024): out.write(chunk)
        return "bg_video.mp4"
    except Exception as e:
        print(f"Pexels Error: {e}")
        return None

def get_ai_clip(query):
    try:
        if not query: query = "usa technology bright studio"
        clean_query = f"bright,studio,{query.strip().replace(' ', ',')}"
        url = f"https://loremflickr.com/1080/1920/{clean_query}?lock={random.randint(1,999999)}"
        img_path = f"/tmp/clip_{int(time.time())}.jpg"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(img_path, 'wb') as f: f.write(r.content)
            # Brightness badhao
            im = Image.open(img_path)
            enhancer = ImageEnhance.Brightness(im)
            im = enhancer.enhance(1.3)
            enhancer2 = ImageEnhance.Color(im)
            im = enhancer2.enhance(1.2)
            im.save(img_path)
            return img_path
        return None
    except: return None

def get_human_face_clip(query):
    try:
        # SCRIPT SE RELATED FACE - Ye fix hai
        # Agar topic iphone hai to iphone wala banda ayega
        face_queries = [
            f"{query} with man tech youtuber studio bright light",
            f"american man explaining {query} bright studio",
            f"tech man talking {query} professional lighting"
        ]
        for q in face_queries:
            vid = get_pexels_video(q)
            if vid:
                print(f"RELATED FACE MIL GAYA: {q}")
                return vid, False
        print("AI RELATED FACE")
        ai_url = f"https://loremflickr.com/1080/1920/american,man,{query.replace(' ',',')},tech,bright?lock={random.randint(1,999999)}"
        img_path = f"/tmp/face_{int(time.time())}.jpg"
        r = requests.get(ai_url, timeout=30)
        if r.status_code == 200:
            with open(img_path, 'wb') as f: f.write(r.content)
            im = Image.open(img_path)
            im = ImageEnhance.Brightness(im).enhance(1.4)
            im = ImageEnhance.Color(im).enhance(1.3)
            im.save(img_path)
            return img_path, True
        return None, False
    except: return None, False

# FIXED CAPTION - WORD TO WORD SKY BLUE - PIL WALA 100% WORKING
def create_skyblue_captions(full_text, audio_duration):
    try:
        words = full_text.split()
        if not words: return []
        clips = []
        per_word = audio_duration / len(words)
        for i, word in enumerate(words):
            img = Image.new('RGBA', (1080, 180), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 62)
            except: font = ImageFont.load_default()
            text = word.upper()
            bbox = draw.textbbox((0,0), text, font=font)
            w = bbox[2]-bbox[0]
            x = (1080 - w)//2
            draw.text((x, 20), text, fill="black", font=font, stroke_width=12, stroke_fill="black")
            draw.text((x, 20), text, fill="#00D4FF", font=font)
            clip = ImageClip(np.array(img)).set_duration(per_word).set_start(i * per_word)
            clip = clip.set_position(('center', 0.78), relative=True)
            clips.append(clip)
        print(f"Caption Words: {len(clips)} Word to Word OK")
        return clips
    except Exception as e:
        print(f"Caption Error: {e}")
        return []

BIG_CREATORS = [
    {"id": "UC6-F5tO8uklgE9Zy8IvbdFw", "name": "Marques Brownlee"},
    {"id": "UCBJycsmduvYEL83R_U4JriQ", "name": "Mrwhosetheboss"},
    {"id": "UCsTcErHg8oDvUnTzoqsYeNw", "name": "Unbox Therapy"},
    {"id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Linus Tech Tips"},
]
BACKUP_TOPICS = [
    {"query": "iphone 16 technology", "title": "Secret iPhone setting you should turn on", "search": "iphone secret trick"},
    {"query": "android secret setting", "title": "Secret Android setting you should turn on", "search": "android secret setting"},
    {"query": "tesla technology", "title": "Tesla's new feature is mind blowing", "search": "tesla new feature"},
]

def get_viral_from_big_creator():
    random.shuffle(BIG_CREATORS)
    for creator in BIG_CREATORS[:3]:
        try:
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={creator['id']}"
            feed = feedparser.parse(feed_url)
            if not feed.entries: continue
            for entry in feed.entries[:6]:
                title = entry.title
                if any(b in title.lower() for b in BANNED_WORDS):
                    print(f"SKIPPED: {title}")
                    continue
                if len(title) < 100 and len(title) > 10:
                    keywords = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower()
                    pexels_query = ' '.join(keywords.split()[:4])
                    return {"original_title": title, "original_desc": entry.get('summary',''), "original_link": entry.link, "creator_name": creator['name'], "pexels_query": pexels_query, "search": keywords[:30]}
        except: continue
    return None

viral = get_viral_from_big_creator()
if viral:
    topic_title = viral["original_title"]; topic_search = viral["search"]; pexels_q = viral["pexels_query"]
    cloned_desc = viral["original_desc"]; cloned_link = viral["original_link"]
else:
    fallback = random.choice(BACKUP_TOPICS)
    topic_title = fallback["title"]; topic_search = fallback["search"]; pexels_q = fallback["query"]
    cloned_desc = ""; cloned_link = ""

# --- FINAL SCRIPT FIX ---
if viral:
    script_text = f"Hello friends, {topic_title}. {cloned_desc[:120]} This viral technology is trending in USA right now. {topic_search} is something everyone is searching. Here is the secret trick you must know. So subscribe my channel for more."
else:
    script_text = f"Hello friends, {topic_title}. This is a secret trick about {topic_search}. Most people don't know this hidden feature. If you enable this one setting, your device will become twice as fast. This is trending in USA. So subscribe my channel for more."

print(f"SCRIPT: {script_text}")

# --- SOUND NUKILA TEZ CLEAR FIX ---
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

# Tez aur clear
audio = audio.fx(vfx.audio_fadein, 0.1).fx(vfx.audio_fadeout, 0.2).volumex(1.6)
safe_duration = audio.duration
W, H = 1080, 1920

bg_path, is_image = get_human_face_clip(pexels_q or topic_search)
if not bg_path:
    temp_path = get_pexels_video(pexels_q or topic_search)
    if temp_path: bg_path, is_image = temp_path, False
    else: bg_path, is_image = get_ai_clip(pexels_q or topic_search), True

if bg_path and os.path.exists(bg_path):
    if is_image:
        bg_clip = ImageClip(bg_path).set_duration(safe_duration).resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
        bg_clip = bg_clip.resize(lambda t: 1 + 0.03*t)
    else:
        bg_clip = VideoFileClip(bg_path).without_audio().resize(height=H)
        if bg_clip.w > W: bg_clip = bg_clip.crop(x1=(bg_clip.w-W)//2, x2=(bg_clip.w-W)//2 + W, y1=0, y2=H)
        bg_clip = bg_clip.loop(duration=safe_duration) if bg_clip.duration < safe_duration else bg_clip.subclip(0, safe_duration)
        # LIGHTING FIX - Bright + Color
        bg_clip = bg_clip.fx(vfx.colorx, 1.25).fx(vfx.lum_contrast, lum=10, contrast=0.2)
else:
    img = Image.new("RGB", (W,H), (10,10,40))
    bg_clip = ImageClip(np.array(img)).set_duration(safe_duration)

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
    for line in textwrap.wrap(title + " #tech #shorts #viral", width=28):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=60
        if y>1650: break
    draw.text((35, 1700), f"@{CHANNEL_NAME} • Subscribe", fill=(200,200,200), font=font_small)
    return ImageClip(np.array(overlay)).set_duration(duration)

overlay_clip = create_overlay(safe_duration, topic_title, topic_search)
caption_clips = create_skyblue_captions(script_text, safe_duration)
final = CompositeVideoClip([bg_clip, overlay_clip, *caption_clips], size=(W,H)).set_duration(safe_duration).set_audio(audio)
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', threads=2)
print(f"DONE {final.duration}s BRIGHT + RELATED FACE + TEZ SOUND")

from upload_youtube import upload_video
final_title = f"{topic_title} 🔥" if viral else f"{topic_title} 🔥 | First Time in USA"
final_desc = f"{topic_title}\n\nSearch: {topic_search}\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n\n#tech #shorts #viral"
final_tags = [topic_search, "tech shorts", "viral"]
upload_video("final_shorts.mp4", final_title[:95], final_desc, final_tags[:15])
