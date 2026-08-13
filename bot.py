import random, requests, re, os, time, textwrap
import xml.etree.ElementTree as ET
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build
from auto_music import fetch_music_for_video
print("Starting FINAL BOT - USA ULTRA VIRAL - FULL SEO - FIXED 3 PROBLEMS...")

def get_feeling_emoji(title):
    title_low = title.lower()
    if any(w in title_low for w in ["iphone", "apple", "ios", "ipad"]):
        return random.choice(["📱", "🍎", "🔥"])
    elif any(w in title_low for w in ["samsung", "android", "pixel"]):
        return random.choice(["📱", "🤖", "⚡"])
    elif any(w in title_low for w in ["ai", "chatgpt", "openai", "gemini"]):
        return random.choice(["🤖", "🧠", "🚀"])
    elif any(w in title_low for w in ["tesla", "elon", "car", "ev", "spacex"]):
        return random.choice(["🚗", "⚡", "🚀"])
    elif any(w in title_low for w in ["shock", "viral", "breaking", "trending", "insane"]):
        return random.choice(["😱", "🚨", "💥", "🔥"])
    elif any(w in title_low for w in ["launch", "new", "released", "update"]):
        return random.choice(["✨", "🚀", "🆕"])
    else:
        return random.choice(["🔥", "💥", "⚡", "🚀"])

for f in ["voice.mp3", "final_shorts.mp4"] + [f"clip_{i}.mp4" for i in range(5)]:
    if os.path.exists(f):
        try: os.remove(f)
        except: pass

CHANNEL_LINK = "https://www.youtube.com/@TECH4USA"
OLD_SHORTS = "https://www.youtube.com/@TECH4USA/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
BANNED_WORDS = ["jethalal", "bapuji", "taarak", "ooltah", "chashmah", "tmkoc", "bhabi", "kapil", "bigg boss", "lottery"]

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
        f"american woman with {topic} technology smiling",
        f"{topic} closeup screen New York USA",
        f"{topic} gadget b-roll american background",
        f"USA flag {topic} technology background"
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

def create_progress_bar(duration):
    try:
        bar = ColorClip(size=(1080, 12), color=(255, 0, 0)).set_duration(duration)
        bar = bar.set_position(('center', 'top'))
        return bar
    except:
        return None

def get_trending_topic_triple():
    print("TRIPLE CHECK: Google RSS USA -> YouTube USA")
    final_topic = None
    source = ""
    try:
        r = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=15)
        root = ET.fromstring(r.content)
        items = root.findall('.//item/title')
        for item in items[:15]:
            topic = item.text.strip()
            if any(b in topic.lower() for b in BANNED_WORDS): continue
            if len(topic) > 3:
                final_topic = topic
                source = "google_rss"
                break
    except Exception as e:
        print(f"Google RSS error: {e}")
    if not final_topic:
        try:
            if YOUTUBE_API_KEY:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                yt_req = youtube.videos().list(part='snippet', chart='mostPopular', regionCode='US', maxResults=20).execute()
                for item in yt_req.get('items', []):
                    yt_title = item['snippet']['title']
                    if any(b in yt_title.lower() for b in BANNED_WORDS): continue
                    if 5 < len(yt_title) < 90:
                        final_topic = re.sub(r'[^a-zA-Z0-9 ]', '', yt_title).strip()[:45]
                        source = "youtube"
                        break
        except Exception as e:
            print(f"YouTube error: {e}")
    if not final_topic:
        final_topic = "Tech News USA"
        source = "fallback"
    return final_topic, source

def clean_news_text(raw):
    raw = re.sub('<[^<]+?>', '', raw)
    raw = raw.replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
    raw = re.split(r'\s-\s[A-Z][a-z]+\s*$', raw)[0]
    sentences = [s.strip() for s in re.split(r'\.\s+', raw) if len(s.strip()) > 10]
    if not sentences:
        return raw[:300].strip()
    important_keywords = ["$", "pay", "billion", "million", "lawsuit", "sued", "fine", "%", "price", "launch"]
    important_sent = []
    for s in sentences[1:]:
        if any(k in s.lower() for k in important_keywords):
            important_sent.append(s)
    final_sents = [sentences[0]]
    if important_sent and important_sent[0] not in final_sents:
        final_sents.append(important_sent[0])
    for s in sentences[1:]:
        if s not in final_sents and len(final_sents) < 3:
            final_sents.append(s)
    short = '. '.join(final_sents)[:350]
    return short.strip()

def get_real_news_script(topic):
    real_news_text = ""
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(topic)}+when:1d&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=12)
        root = ET.fromstring(r.content)
        first_item = root.find('.//item')
        if first_item is not None:
            title_news = first_item.find('title').text if first_item.find('title') is not None else topic
            desc = first_item.find('description').text if first_item.find('description') is not None else ""
            raw = f"{title_news}. {desc}"
            real_news_text = clean_news_text(raw)
    except Exception as e:
        print(f"News fetch error: {e}")
    if len(real_news_text) < 30:
        real_news_text = f"{topic} is trending number one in the USA right now with a big update"
    topic_clean = topic.replace("  ", " ").strip()
    templates = [
        f"Hey America, stop scrolling. {real_news_text}. This just happened and it is a game changer for {topic_clean}. You need to see this right now. Hit subscribe for more USA updates.",
        f"What's up USA? {topic_clean} is trending everywhere right now. {real_news_text}. This is major news from today. Everyone in America is talking about this. Let me know what you think.",
        f"Breaking news America. {real_news_text}. This matters to you because it affects everyone in the USA. If you missed this {topic_clean} update, this is huge. Watch till the end for what to do next.",
        f"Did you hear about {topic_clean}? {real_news_text}. This went viral across the USA today. I will explain it in simple words, just real facts for you. Hit that subscribe button for daily updates."
    ]
    final_script = random.choice(templates)
    words = final_script.split()
    if len(words) > 65:
        first_part = ' '.join(words[:45])
        last_part = ' '.join(words[-15:])
        final_script = first_part + " " + last_part
        final_script = ' '.join(final_script.split()[:65]) + "."
    return final_script

def fetch_seo_keywords(topic):
    keywords = []
    try:
        url = f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={requests.utils.quote(topic)}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            import json
            try:
                data = json.loads(r.text)
                if len(data) > 1:
                    for sug in data[1][:7]:
                        if isinstance(sug, list):
                            keywords.append(sug[0])
                        else:
                            keywords.append(str(sug))
            except:
                pass
    except Exception as e:
        print(f"SEO keyword fetch error: {e}")
    suffixes = ["news", "update", "2026", "USA", "today", "leak", "review"]
    for suf in suffixes:
        k = f"{topic} {suf}"
        if k not in keywords:
            keywords.append(k)
    keywords = list(dict.fromkeys([k.strip() for k in keywords if len(k)>3]))[:12]
    print(f"SEO KEYWORDS MILA: {keywords}")
    return keywords

def seo_optimize(topic, script_text):
    keywords = fetch_seo_keywords(topic)
    base_title = topic.replace("#tech","").replace("#shorts","").strip()
    base_title = ' '.join(base_title.split()[:7])
    emoji = get_feeling_emoji(base_title)
    seo_titles = [
        f"{emoji} {base_title} Breaking News USA 2026 {emoji}",
        f"{emoji} {base_title} You Need To Know Today {emoji}",
        f"{emoji} {base_title} Viral in America Right Now {emoji}"
    ]
    final_title = min(seo_titles, key=lambda x: abs(len(x)-58))[:90]
    kw_str = ", ".join(keywords[:5])
    description = f"{final_title}\n\n{script_text}\n\nHello Americans! {topic} is trending number 1 in the USA today.\n\nIn this video:\n- {topic} latest news today\n- Why {topic} is trending in America\n- What you should do about {topic}\n\nRelated Searches: {kw_str}\n\nThis video is based on Google Trends USA and YouTube Trending USA real-time data.\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n\n#tech #shorts #shortsfeed #ytshorts #{topic.replace(' ', '')} #USTrending #GoogleTrendsUSA #USATechNews #ViralUSA #TechNews2026 #BreakingNewsUSA\n"
    tags = [topic, f"{topic} news", f"{topic} USA", f"{topic} today", f"{topic} update 2026", f"{topic} trending USA", f"{topic} breaking news", "USA trending today", "Google Trends USA", "YouTube Trending USA", "US tech news today", "viral tech USA", "tech news 2026", "breaking tech news USA", f"{topic} explained", "shorts", "shorts feed", "ytshorts"]
    for kw in keywords[:5]:
        if kw not in tags and len(tags) < 20:
            tags.append(kw)
    tags = list(dict.fromkeys(tags))[:18]
    return final_title, description, tags

topic_search, script_source = get_trending_topic_triple()
topic_title = get_unique_title(f"{topic_search} You Didn't Know!")
script_text = get_real_news_script(topic_search)
print(f"FINAL TITLE: {topic_title}")
print(f"FINAL SCRIPT: {script_text}")
clean_script_for_voice = script_text.replace("#","").strip()
gTTS(text=clean_script_for_voice, lang='en', tld='us', slow=False).save("voice.mp3")
time.sleep(1)
audio = AudioFileClip("voice.mp3")
try: audio = audio.volumex(1.8)
except: pass
bg_music_path = fetch_music_for_video(topic_search)
if bg_music_path:
    from moviepy.editor import AudioFileClip, CompositeAudioClip
    bg_music = AudioFileClip(bg_music_path).subclip(0, audio.duration)
    bg_music = bg_music.volumex(0.12)
    final_audio = CompositeAudioClip([audio, bg_music])
else:
    final_audio = audio  
max_duration = 34
if final_audio.duration > max_duration:
    try: final_audio = final_audio.subclip(0, max_duration)
    except: final_audio = final_audio.with_end(max_duration)
W, H = 1080, 1920
bg_clip = get_multi_clips(topic_search, final_audio.duration)
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
    draw.rounded_rectangle((50, 1160, W-50, 1230), radius=35, fill=(255, 0, 0, 240))
    draw.text((95, 1175), f'USA VIRAL: {search[:20]}', fill=(255,255,255), font=font_small)
    draw.rectangle((0, 1300, W, H), fill=(0,0,0,190))
    y = 1330
    clean_title_raw = title.replace("#tech","").replace("#shorts","").replace("#viral","").replace("#trending","").strip()
    clean_title_raw = ' '.join(clean_title_raw.split()[:8])
    for line in textwrap.wrap(clean_title_raw, width=28):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=60
        if y>1650: break
    return safe_set_duration(ImageClip(np.array(overlay)), duration)

from upload_youtube import upload_video
final_yt_title, description, tags = seo_optimize(topic_search, script_text)
seo_filename = re.sub(r'[^a-z0-9]+', '-', topic_search.lower()).strip('-')[:40]
seo_filename = f"{seo_filename}-usa-news-2026.mp4"
overlay_clip = create_overlay(final_audio.duration, final_yt_title, topic_search)
caption_clips = create_skyblue_captions(script_text, final_audio.duration)
layers = [bg_clip, overlay_clip, *caption_clips]
progress_bar = create_progress_bar(final_audio.duration)
if progress_bar:
    layers.append(progress_bar)
final = CompositeVideoClip(layers, size=(W,H))
final = safe_set_duration(final, final_audio.duration)
final = safe_set_audio(final, final_audio)
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)
print(f"FINAL SEO DONE - 3 PROBLEMS FIXED")
upload_video(seo_filename, final_yt_title, description, tags)
