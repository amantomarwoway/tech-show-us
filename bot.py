import random, requests, feedparser, re, os, time, textwrap
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pytrends.request import TrendReq
import snscrape.modules.twitter as sntwitter
from googleapiclient.discovery import build

print("Starting FINAL MULTI-ACTIVITY BOT - TITLE WITHOUT HASHTAG...")

for f in ["voice.mp3", "voice_30.mp3", "final_shorts.mp4"] + [f"clip_{i}.mp4" for i in range(5)]:
    if os.path.exists(f):
        try: os.remove(f)
        except: pass

CHANNEL_LINK = "https://www.youtube.com/@techoperationtheatre"
OLD_SHORTS = "https://www.youtube.com/@techoperationtheatre/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
BANNED_WORDS = ["jethalal", "bapuji", "taarak", "ooltah", "chashmah", "tmkoc", "bhabi", "kapil", "bigg boss"]

def safe_set_duration(clip, d):
    try: return clip.set_duration(d)
    except: return clip.with_duration(d)
def safe_set_audio(clip, a):
    try: return clip.set_audio(a)
    except: return clip.with_audio(a)
def safe_without_audio(clip):
    try: return clip.without_audio()
    except: return clip.with_audio(None)

def get_unique_title(title):
    try:
        if not os.path.exists("used_titles.txt"):
            open("used_titles.txt","w").close()
        with open("used_titles.txt","r") as f:
            used = f.read().splitlines()
        if title in used:
            title = f"{title} {random.choice(['Pro Trick','Secret','2026','Viral'])} {random.randint(1,99)}"
        with open("used_titles.txt","a") as f:
            f.write(title+"\n")
        return title[:90]
    except:
        return title[:90]

def get_multi_clips(topic, total_duration):
    clips = []
    activities = [
        f"american man using {topic} phone smiling",
        f"{topic} closeup screen technology",
        f"american man typing {topic} laptop",
        f"{topic} gadget b-roll technology background"
    ]
    random.shuffle(activities)
    per_clip = total_duration / 4
    for i in range(4):
        try:
            q = activities[i % len(activities)]
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=10&orientation=portrait&size=medium"
            headers = {"Authorization": PEXELS_API_KEY} if PEXELS_API_KEY else {}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code!= 200: continue
            vids = resp.json().get('videos', [])
            if not vids: continue
            video = random.choice(vids)
            files = sorted(video['video_files'], key=lambda x: x['width'], reverse=True)
            best = next((f for f in files if f['width'] >= 720), files[0])
            path = f"clip_{i}.mp4"
            r = requests.get(best['link'], stream=True, timeout=60)
            with open(path, "wb") as out:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    out.write(chunk)
            clip = VideoFileClip(path)
            clip = safe_without_audio(clip)
            if clip.duration > per_clip + 1:
                start = random.uniform(0, max(0, clip.duration - per_clip - 0.5))
                try: clip = clip.subclip(start, start+per_clip)
                except: clip = clip.with_end(per_clip)
            clip = safe_set_duration(clip, per_clip)
            try: clip = clip.resize(height=1920)
            except:
                try: clip = clip.resized(height=1920)
                except: pass
            clips.append(clip)
            print(f"CLIP {i+1} MILA: {q}")
        except Exception as e:
            print(f"Clip {i} skip: {e}")
            continue
    if not clips:
        return None
    final_bg = concatenate_videoclips(clips, method="compose")
    final_bg = safe_set_duration(final_bg, total_duration)
    return final_bg

def create_skyblue_captions(full_text, audio_duration):
    clean_text = full_text.replace("#tech","").replace("#shorts","")
    words = clean_text.split()
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
        clip = ImageClip(np.array(img))
        clip = safe_set_duration(clip, per_word)
        try: clip = clip.set_start(i * per_word)
        except: clip = clip.with_start(i * per_word)
        try: clip = clip.set_position(('center', 0.75), relative=True)
        except: clip = clip.with_position(('center', 0.75), relative=True)
        clips.append(clip)
    return clips

# ================= TRIPLE CHECK FINAL FIX =================
def get_trending_topic_triple():
    print("TRIPLE CHECK: Google (High Prob) -> YouTube (High Prob) -> Twitter (Backup)")
    final_topic = None
    source = ""

    # 1. GOOGLE TRENDS - 50-90% probability wale (USA trending)
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        trending_df = pytrends.trending_searches(pn='united_states')
        google_topics = trending_df[0].tolist()[:10]
        tech_keywords = ['iphone', 'android', 'ai', 'tech', 'nasa', 'space', 'google', 'chatgpt', 'phone', 'laptop', 'gadget', 'apple', 'samsung', 'tesla']
        for topic in google_topics:
            if any(k in topic.lower() for k in tech_keywords):
                if any(b in topic.lower() for b in BANNED_WORDS): continue
                final_topic = topic
                source = "google"
                print(f"GOOGLE SE FINAL: {topic}")
                break
    except Exception as e:
        print(f"Google error: {e}")

    # 2. YOUTUBE TRENDING - Agar Google fail
    if not final_topic:
        try:
            if YOUTUBE_API_KEY:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                yt_req = youtube.videos().list(part='snippet', chart='mostPopular', regionCode='US', videoCategoryId='28', maxResults=15).execute()
                for item in yt_req.get('items', []):
                    yt_title = item['snippet']['title']
                    if any(b in yt_title.lower() for b in BANNED_WORDS): continue
                    if 10 < len(yt_title) < 80:
                        final_topic = re.sub(r'[^a-zA-Z0-9 ]', '', yt_title).strip()[:40]
                        source = "youtube"
                        print(f"YOUTUBE SE FINAL: {yt_title}")
                        break
        except Exception as e:
            print(f"YouTube error: {e}")

    # 3. TWITTER BACKUP - Sirf tab jab dono fail
    if not final_topic:
        try:
            print("Twitter Backup use...")
            query = "tech AI NASA min_faves:2000 lang:en"
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                if len(tweet.content) > 20:
                    final_topic = tweet.content.split('\n')[0][:50]
                    source = "twitter"
                    print(f"TWITTER SE FINAL: {final_topic}")
                    break
                break
        except:
            pass

    if not final_topic:
        final_topic = "Secret iPhone Setting"
        source = "fallback"
    return final_topic, source

# --- MAIN START ---
topic_search, script_source = get_trending_topic_triple()

# Title - Clickbait
topic_title = get_unique_title(f"{topic_search} You Didn't Know!")

# Script - ALAG SE BANEGA, TITLE NAHI PADHEGA - Jo log sunna pasand karte hain
if script_source == "google":
    script_text = f"This {topic_search} is exploding in the United States right now. Everyone is searching for it. Here is what you need to know before it goes viral everywhere. This will save you a lot of time."
elif script_source == "youtube":
    script_text = f"YouTube is going crazy over {topic_search}. This tech trend is number one in America right now. I checked every video. Here is the real truth you must know."
else: # twitter backup
    script_text = f"Twitter cannot stop talking about {topic_search}. This tech secret just leaked and it is viral. Here is what is really happening."

print(f"FINAL TITLE: {topic_title}")
print(f"FINAL SCRIPT: {script_text} | Source: {script_source}")

# VOICE FIX - PURE AMERICAN SMOOTH
clean_script_for_voice = script_text.replace("#","").strip()
# American accent ke liye tld='com' hi use hota hai
gTTS(text=clean_script_for_voice, lang='en', tld='com', slow=False).save("voice.mp3")

time.sleep(1)
audio = AudioFileClip("voice.mp3")
TARGET = 30
if audio.duration < TARGET:
    audio = concatenate_audioclips([audio]* (int(TARGET//audio.duration)+2)).subclip(0, TARGET)
    audio.write_audiofile("voice_30.mp3", logger=None)
    audio = AudioFileClip("voice_30.mp3")
else:
    try: audio = audio.subclip(0, TARGET)
    except: audio = audio.with_end(TARGET)
try: audio = audio.volumex(1.8)
except: pass

W, H = 1080, 1920
bg_clip = get_multi_clips(topic_search, audio.duration)
if not bg_clip:
    bg_clip = ImageClip(np.array(Image.new("RGB", (W,H), (10,10,40))))
    bg_clip = safe_set_duration(bg_clip, audio.duration)

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
    clean_title = title.replace("#tech","").replace("#shorts","").replace("#viral","").replace("#","")
    for line in textwrap.wrap(clean_title, width=28):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=60
        if y>1650: break
    return safe_set_duration(ImageClip(np.array(overlay)), duration)

overlay_clip = create_overlay(audio.duration, topic_title, topic_search)
caption_clips = create_skyblue_captions(script_text, audio.duration)
final = CompositeVideoClip([bg_clip, overlay_clip, *caption_clips], size=(W,H))
final = safe_set_duration(final, audio.duration)
final = safe_set_audio(final, audio)
final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)

from upload_youtube import upload_video
upload_video("final_shorts.mp4", f"{topic_title}"[:95], f"{topic_title}\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n#tech #shorts", [topic_search, "tech"])
