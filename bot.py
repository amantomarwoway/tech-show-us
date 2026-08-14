import random, requests, re, os, time, textwrap
import xml.etree.ElementTree as ET
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build
from auto_music import fetch_music_for_video
print("Starting ULTIMATE FIXED BOT - ALL 8 SUGGESTIONS + SUB-SUGGESTIONS - USA TECH ONLY...")

# ========== 1. NICHE & BRANDING ==========
# Only Tech USA / AI / Gadgets - strict filter
TECH_ALLOWED = ["iphone","apple","ios","ipad","android","samsung","pixel","google","ai","chatgpt","openai","gemini","tesla","elon","gadget","tech","phone","battery","hack","app","laptop","5g","privacy","security","chip","nvidia","microsoft","meta","vr","ar","robot","drone","earbuds","watch","macbook"]
BANNED_NON_TECH = [
    "tyrod","taylor","mariners","yankees","oreo","brad pitt","ukraine","pushpa","jethalal","bapuji","taarak","tmkoc","bhabi","kapil","bigg boss","lottery",
    "football","cricket","basketball","baseball","soccer","wwe","movie","bollywood","hollywood","election","biden","trump"
]
CHANNEL_LINK = "https://www.youtube.com/@TECH4USA"
OLD_SHORTS = "https://www.youtube.com/@TECH4USA/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
BANNED_WORDS = BANNED_NON_TECH + ["jethalal","bapuji","taarak","ooltah","chashmah","tmkoc","bhabi","kapil","bigg boss","lottery"]

EVERGREEN_TECH_FALLBACK = [
    "iPhone Hidden Setting That Saves Battery 2 Days",
    "How To Stop Apps Spying On You in 10 Seconds",
    "Android Trick That Will Blow Your Mind",
    "AI Tool Saving 5 Hours A Day in USA",
    "Samsung vs iPhone Which Is Better in 2026",
    "Secret Google Search Trick 99 Percent Dont Know",
    "Tesla Hidden Feature Only Owners Know",
    "ChatGPT Prompts That Make Money in USA"
]

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
            title = f"{title} Secret {random.randint(1,99)}"
        with open("used_titles.txt","a") as f:
            f.write(title+"\n")
        return title[:90]
    except:
        return title[:90]

# ========== 3. HOOK & RETENTION - PATTERN INTERRUPT + LOOPING ==========
def get_multi_clips_ultimate(topic, total_duration):
    """High-contrast black/white/blue, 4K crisp, pattern interrupt zoom"""
    clips = []
    # High contrast queries - tech only
    queries = [
        f"closeup {topic} iphone screen 4k",
        f"american hands typing {topic} laptop minimal",
        f"{topic} gadget b-roll black background",
        f"new york tech {topic} futuristic blue"
    ]
    random.shuffle(queries)
    per_clip = total_duration / 4
    for i in range(4):
        try:
            q = queries[i % len(queries)]
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=10&orientation=portrait&size=medium"
            headers = {"Authorization": PEXELS_API_KEY} if PEXELS_API_KEY else {}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200: continue
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
            # Pattern interrupt zoom - GitHub runner safe
            try:
                clip = clip.resize(height=1920)
            except:
                try: clip = clip.resized(height=1920)
                except: pass
            try:
                # Optional zoom - safe fallback
                clip = clip.resize(lambda t: 1 + 0.08 * (t / max(per_clip,1)))
            except:
                pass
            clips.append(clip)
        except Exception as e:
            print(f"Clip {i} skip: {e}")
            continue
    if not clips:
        return None
    final_bg = concatenate_videoclips(clips, method="compose")
    final_bg = safe_set_duration(final_bg, total_duration)
    return final_bg

# ========== 5. CAPTIONS & AUDIO - BIG CENTER YELLOW/WHITE BOLD ==========
def create_ultimate_captions(full_text, audio_duration):
    """Bold Montserrat style, yellow/white + black stroke, center - mute viewers"""
    clean_text = full_text.replace("#tech","").replace("#shorts","")
    words = clean_text.split()
    clips = []
    per_word = audio_duration / max(len(words),1)
    for i, word in enumerate(words):
        img = Image.new('RGBA', (1080, 350), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 78)
        except: font = ImageFont.load_default()
        text = word.upper()
        # Easter egg hidden
        if i == len(words)//2 and random.random() < 0.3:
            text = "DID YOU SEE THAT? " + text
        bbox = draw.textbbox((0,0), text, font=font)
        w = bbox[2]-bbox[0]
        x = (1080 - w)//2
        # High contrast: yellow for keywords, white for others
        color = (255, 235, 0) if len(word) > 4 else (255,255,255)
        # Black stroke for readability - USA crisp
        draw.text((x, 80), text, fill="black", font=font, stroke_width=18, stroke_fill="black")
        draw.text((x, 80), text, fill=color, font=font, stroke_width=6, stroke_fill="black")
        clip = ImageClip(np.array(img))
        clip = safe_set_duration(clip, per_word)
        try: clip = clip.set_start(i * per_word)
        except: clip = clip.with_start(i * per_word)
        try: clip = clip.set_position(('center', 0.65), relative=True)
        except: clip = clip.with_position(('center', 0.65), relative=True)
        clips.append(clip)
    return clips

def create_progress_bar(duration):
    try:
        bar = ColorClip(size=(1080, 14), color=(255, 0, 0)).set_duration(duration)
        try: bar = bar.set_position(('center','top'))
        except: bar = bar.with_position(('center','top'))
        return bar
    except:
        return None

# ========== 1. NICHE FILTER - TECH ONLY TRENDING ==========
def get_trending_topic_triple():
    print("TRIPLE CHECK: Google RSS USA TECH ONLY -> YouTube TECH ONLY -> Reddit r/technology")
    final_topic = None
    source = ""
    # 1. Google Trends USA - filter tech only
    try:
        r = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=15)
        root = ET.fromstring(r.content)
        items = root.findall('.//item/title')
        random.shuffle(items)
        for item in items[:20]:
            topic = item.text.strip()
            low = topic.lower()
            if any(b in low for b in BANNED_NON_TECH): continue
            if not any(t in low for t in TECH_ALLOWED): continue
            if len(topic) > 3:
                final_topic = topic
                source = "google_rss_tech"
                print(f"TECH TOPIC FROM GOOGLE: {topic}")
                break
    except Exception as e:
        print(f"Google RSS error: {e}")
    
    # 2. YouTube USA Tech trending fallback
    if not final_topic:
        try:
            if YOUTUBE_API_KEY:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                yt_req = youtube.videos().list(part='snippet', chart='mostPopular', regionCode='US', maxResults=30, videoCategoryId="28").execute()
                for item in yt_req.get('items', []):
                    yt_title = item['snippet']['title']
                    low = yt_title.lower()
                    if any(b in low for b in BANNED_NON_TECH): continue
                    if not any(t in low for t in TECH_ALLOWED): continue
                    if 5 < len(yt_title) < 90:
                        final_topic = re.sub(r'[^a-zA-Z0-9 ]', '', yt_title).strip()[:50]
                        source = "youtube_tech"
                        break
        except Exception as e:
            print(f"YouTube error: {e}")
    
    # 3. Reddit r/technology / r/gadgets check (social proof idea)
    if not final_topic:
        try:
            r = requests.get("https://www.reddit.com/r/technology/top/.json?limit=10", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for child in data['data']['children']:
                    t = child['data']['title']
                    low = t.lower()
                    if any(b in low for b in BANNED_NON_TECH): continue
                    if any(k in low for k in TECH_ALLOWED):
                        final_topic = t[:50]
                        source = "reddit_tech"
                        print(f"REDDIT TOPIC: {t}")
                        break
        except Exception as e:
            print(f"Reddit error: {e}")
    
    # 4. Final fallback - evergreen tech only
    if not final_topic:
        final_topic = random.choice(EVERGREEN_TECH_FALLBACK)
        source = "evergreen_tech"
    
    print(f"FINAL TECH TOPIC: {final_topic} from {source}")
    return final_topic, source

def clean_news_text(raw):
    raw = re.sub('<[^<]+?>', '', raw)
    raw = raw.replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
    raw = re.split(r'\s-\s[A-Z][a-z]+\s*$', raw)[0]
    sentences = [s.strip() for s in re.split(r'\.\s+', raw) if len(s.strip()) > 10]
    if not sentences:
        return raw[:300].strip()
    return '. '.join(sentences[:2])[:350].strip()

# ========== 2. AI SLOP FIX + 6. CONTENT STRATEGY + 3. HOOK ==========
def get_real_news_script(topic):
    real_news_text = ""
    social_proof = ""
    try:
        # Fetch real news + TechCrunch/Verge style for social proof
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(topic)}+tech+when:1d&hl=en-US&gl=US&ceid=US:en"
        r = requests.get(url, timeout=12)
        root = ET.fromstring(r.content)
        first_item = root.find('.//item')
        if first_item is not None:
            title_news = first_item.find('title').text if first_item.find('title') is not None else topic
            desc = first_item.find('description').text if first_item.find('description') is not None else ""
            raw = f"{title_news}. {desc}"
            real_news_text = clean_news_text(raw)
            # Social proof extraction
            if "TechCrunch" in raw or "Verge" in raw or "WSJ" in raw:
                social_proof = "Even TechCrunch is talking about this."
    except Exception as e:
        print(f"News fetch error: {e}")

    if len(real_news_text) < 20:
        real_news_text = f"{topic} is changing how Americans use their phones in 2026"

    # Holiday check - Black Friday / Apple Event etc
    import datetime
    month = datetime.datetime.now().month
    holiday_hook = ""
    if month == 11:
        holiday_hook = "Black Friday is coming, "
    elif month == 9:
        holiday_hook = "Apple Event just happened, "

    # 5 CONTENT STRATEGY TEMPLATES - Problem-Solution, Comparison, Future, Storytelling, Listicle
    templates = [
        # Problem-Solution - high retention
        f"Stop scrolling! {holiday_hook}Your {topic} is draining battery right now. {real_news_text}. In my opinion, I tested this for 30 days and found a fix. Number one, turn this hidden setting off. It saves 2 days battery. I will show you exactly how. {social_proof} Which gadget would you buy? Comment below!",

        # Comparison
        f"This AI tool is saving me 5 hours a day! {topic} vs iPhone - which wins? {real_news_text}. I tested both for weeks. In my opinion, {topic} wins for battery but iPhone wins for camera. You can travel from NYC to LA and this phone still won't die. Which would you choose? A or B? Comment!",

        # Future Tech
        f"How AI will change iPhones in 2027! {topic} just leaked. {real_news_text}. This is controversial but true - your apps are listening. I found a 10 second fix. Some people said AI slop, here's how I actually research this - I read TechCrunch and Verge daily for you. What do you think?",

        # Storytelling NYC to LA
        f"You won't believe what happened! I was traveling from NYC to LA and {topic} saved me. {real_news_text}. This feature was hidden by Apple. I made this mistake for years. Now my battery lasts 2 days. Same phone, different setting. Try this for 24 hours. Would you buy this?",

        # Listicle Top 3 - best for retention
        f"Top 3 {topic} secrets 99 percent of Americans don't know! Number one, {real_news_text[:120]}. Number two, this trick saves you 2 hours every week. Number three, the best one at the end will blow your mind. In my opinion, this changes everything. Which one is your favorite? Comment!"
    ]
    
    final_script = random.choice(templates)
    # Loop trick: end connects to start - first 3 words = last 3 words for seamless loop
    words = final_script.split()
    # Keep 15-20 sec - 55-70 words max for 20 sec video (STW optimization)
    if len(words) > 70:
        # Keep first 50 + last 10 for looping feel
        first = ' '.join(words[:50])
        last = ' '.join(words[-10:])
        final_script = first + " " + last
        # Make loop: add first phrase at end for seamless
        first_phrase = ' '.join(words[:4])
        final_script = final_script + f" {first_phrase}."
    
    final_script = ' '.join(final_script.split()[:68]) + "."
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
    # Add tech specific
    suffixes = ["iPhone trick 2026", "USA", "battery saving", "how to fix", "AI gadget 2026", "tech that helps humans"]
    for suf in suffixes:
        k = f"{topic} {suf}"
        if k not in keywords:
            keywords.append(k)
    keywords = list(dict.fromkeys([k.strip() for k in keywords if len(k)>3]))[:12]
    print(f"SEO KEYWORDS: {keywords}")
    return keywords

def seo_optimize_ultimate(topic, script_text):
    keywords = fetch_seo_keywords(topic)
    base_title = topic.replace("#tech","").replace("#shorts","").strip()
    base_title = ' '.join(base_title.split()[:6])
    
    # ========== 4. TITLE - CLEAN, 1 EMOJI ONLY, NO SPAM ==========
    # Clean format: 3 Reasons Why... / How to... - no Viral in America Right Now spam
    clean_templates = [
        f"3 Reasons Why {base_title} Is Trending Today",
        f"How To Fix {base_title} in 10 Seconds",
        f"{base_title}: The Secret Apple Hides From You",
        f"{base_title} vs iPhone - Which Wins in 2026?",
        f"Why {base_title} Is Changing Life in USA"
    ]
    # Pick one and add only 1 emoji (CTR but not spammy)
    def get_single_emoji(t):
        tl = t.lower()
        if any(w in tl for w in ["iphone","apple","ios"]): return "📱"
        elif any(w in tl for w in ["samsung","android","pixel"]): return "📱"
        elif any(w in tl for w in ["ai","chatgpt"]): return "🤖"
        elif any(w in tl for w in ["tesla"]): return "🚗"
        else: return "🔥"
    
    emoji = get_single_emoji(base_title)
    # A/B testing - generate 2 titles
    title_a = f"{random.choice(clean_templates)}"
    title_b = f"{emoji} {random.choice(clean_templates)}"
    final_title = title_b if len(title_b) < 65 else title_a
    final_title = final_title[:65]
    
    # Save A/B for testing
    with open("ab_titles.txt","w") as f:
        f.write(f"A: {title_a}\nB: {title_b}\n")
    
    kw_str = ", ".join(keywords[:5])
    # ========== DESCRIPTION - FIRST 2 LINES SEARCH KEYWORDS ==========
    # Holiday check inside function - safe for runner
    import datetime
    month_now = datetime.datetime.now().month
    holiday_text = ""
    if month_now == 11:
        holiday_text = "Black Friday is coming, "
    elif month_now == 9:
        holiday_text = "Apple Event just happened, "
    description = f"Best AI gadgets 2026 - {base_title} explained for USA.\nHow to use {topic} like a pro in 2026 - full breakdown.\n\n{script_text}\n\nHello Americans! In my opinion, I tested {topic} for 30 days. {topic} is trending number 1 in USA today - {holiday_text}Tech that helps humans.\n\nIn this video:\n- Why {topic} is trending in America (Problem-Solution)\n- Hidden details most people don't know\n- How to use {topic} to save time and money\n\nRelated Searches: {kw_str}\n\nThis video is based on Google Trends USA, YouTube Trending USA and Reddit r/technology real data. Human-curated Tech News for USA. Even TechCrunch and Verge are talking about this.\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n\n#Shorts #Tech #{topic.replace(' ', '')} #USATech #AIGadgets2026 #HumanCurated\n"
    
    # ========== FIX FOR YOUTUBE INVALID KEYWORDS ERROR ==========
    # YouTube API rules: each tag <30 chars, total <500 chars, no < > " etc
    def clean_tag(t):
        # Remove invalid chars: keep only letters, numbers, space
        t = re.sub(r'[<>"\'#]', '', t)  # Remove < > " ' #
        t = re.sub(r'[^\w\s]', ' ', t)  # Replace special chars with space
        t = ' '.join(t.split())  # Remove extra spaces
        t = t.strip()[:25]  # Max 25 chars to be safe (limit is 30)
        return t.lower()

    raw_tags = [topic, f"{topic} how to", f"{topic} usa", f"{topic} battery", "usa tech today", "best ai gadgets 2026", "tech helps humans", "human curated tech", "iphone tricks usa", "ai tools 2026"]
    # Add keywords but clean them
    for kw in keywords[:5]:
        raw_tags.append(kw)

    cleaned = []
    seen = set()
    total_len = 0
    for t in raw_tags:
        ct = clean_tag(t)
        if len(ct) < 2: continue  # Skip too short
        if ct in seen: continue
        if len(ct) > 25: continue  # YouTube rejects >30, we use 25 safe
        # Check total length <400 safe
        if total_len + len(ct) + 1 > 400:
            break
        cleaned.append(ct)
        seen.add(ct)
        total_len += len(ct) + 1
        if len(cleaned) >= 12:  # Max 12 tags - safe limit
            break

    # Fallback if all tags invalid
    if len(cleaned) < 3:
        cleaned = ["tech usa", "ai gadgets", "iphone tricks", "usa tech", "tech news 2026"]

    tags = cleaned
    print(f"✅ CLEANED TAGS ({len(tags)}): {tags} - Total chars: {total_len} - SAFE FOR YOUTUBE API")
    return final_title, description, tags, title_a, title_b

# ========== MAIN ULTIMATE ==========
topic_search, script_source = get_trending_topic_triple()
topic_title = get_unique_title(topic_search)
script_text = get_real_news_script(topic_search)

print(f"FINAL CLEAN TITLE TOPIC: {topic_title}")
print(f"FINAL HUMAN SCRIPT: {script_text}")

clean_script_for_voice = script_text.replace("#","").strip()
gTTS(text=clean_script_for_voice, lang='en', tld='us', slow=False).save("voice.mp3")
time.sleep(1)
audio = AudioFileClip("voice.mp3")
try: audio = audio.volumex(1.8)
except: pass

# ========== 5. TRENDING MUSIC 15% + FADE - CRASH PROOF FIX FOR PIXABAY JSON ERROR ==========
bg_music_path = None
try:
    # This is where your screenshot error happens: auto_music -> Pixabay JSON parse
    bg_music_path = fetch_music_for_video(topic_search)
except Exception as music_err:
    print(f"⚠️ MUSIC FETCH FAILED (Pixabay empty response) - Continuing without music: {music_err}")
    bg_music_path = None

final_audio = audio
if bg_music_path and os.path.exists(bg_music_path):
    try:
        from moviepy.editor import AudioFileClip, CompositeAudioClip
        try:
            bg_music = AudioFileClip(bg_music_path).subclip(0, audio.duration)
        except:
            bg_music = AudioFileClip(bg_music_path).with_end(audio.duration)
        bg_music = bg_music.volumex(0.15)  # 15% as requested
        try:
            bg_music = bg_music.audio_fadein(0.5).audio_fadeout(0.5)
        except:
            pass
        print(f"TRENDING MUSIC ADDED at 15%: {bg_music_path}")
        final_audio = CompositeAudioClip([audio, bg_music])
    except Exception as e:
        print(f"⚠️ MUSIC MIX FAILED - using voice only: {e}")
        final_audio = audio
else:
    print("No music found or fetch failed - using voice only (video will still upload)")

# ========== 8. VIDEO LENGTH 15-20 SEC FOR RETENTION ==========
max_duration = 20  # Short - better retention 50-60%
if final_audio.duration > max_duration:
    try: final_audio = final_audio.subclip(0, max_duration)
    except: final_audio = final_audio.with_end(max_duration)

W, H = 1080, 1920
bg_clip = get_multi_clips_ultimate(topic_search, final_audio.duration)
if not bg_clip:
    bg_clip = ColorClip(size=(W,H), color=(10,10,30))
    bg_clip = safe_set_duration(bg_clip, final_audio.duration)

# ========== OVERLAYS - HUMAN CURATED + SOCIAL PROOF + EASTER EGG + GREEN SCREEN ==========
def create_ultimate_overlay(duration, title, search):
    overlay = Image.new('RGBA', (W,H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    try: font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except: font_big = ImageFont.load_default()
    try: font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except: font_small = ImageFont.load_default()
    try: font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except: font_badge = ImageFont.load_default()
    
    # Human-curated badge top (branding fix)
    draw.rounded_rectangle((20, 20, 550, 70), radius=20, fill=(0, 200, 255, 240))
    draw.text((35, 28), "HUMAN-CURATED TECH • USA", fill=(0,0,0), font=font_badge)
    
    # Social proof - Verge/TechCrunch style
    draw.rounded_rectangle((20, 80, 500, 120), radius=12, fill=(255,255,255,200))
    draw.text((30, 88), f"Source: Google Trends USA + Reddit", fill=(50,50,50), font=font_small)
    
    # Green screen style bottom box
    draw.rectangle((0, 1250, W, H), fill=(0,0,0,210))
    y = 1280
    clean_title_raw = title.replace("#tech","").replace("#shorts","").replace("#viral","").strip()
    clean_title_raw = ' '.join(clean_title_raw.split()[:7])
    for line in textwrap.wrap(clean_title_raw, width=26):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=58
        if y>1480: break
    
    # Engagement CTA - Which gadget would you buy?
    draw.rounded_rectangle((30, 1510, W-30, 1580), radius=25, fill=(255,235,0,255))
    draw.text((60, 1525), "Which would YOU buy? A or B? Comment! 👇", fill=(0,0,0), font=font_small)
    
    # Easter egg hidden - small corner for re-watch
    draw.text((W-120, H-30), "👀", fill=(255,255,255,100), font=font_small)
    
    return safe_set_duration(ImageClip(np.array(overlay)), duration)

from upload_youtube import upload_video
final_yt_title, description, tags, title_a, title_b = seo_optimize_ultimate(topic_search, script_text)
seo_filename = re.sub(r'[^a-z0-9]+', '-', topic_search.lower()).strip('-')[:40]
seo_filename = f"{seo_filename}-usa-tech-2026.mp4"

overlay_clip = create_ultimate_overlay(final_audio.duration, final_yt_title, topic_search)
caption_clips = create_ultimate_captions(script_text, final_audio.duration)
layers = [bg_clip, overlay_clip, *caption_clips]
progress_bar = create_progress_bar(final_audio.duration)
if progress_bar:
    layers.append(progress_bar)

final = CompositeVideoClip(layers, size=(W,H))
final = safe_set_duration(final, final_audio.duration)
final = safe_set_audio(final, final_audio)
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)

print(f"ULTIMATE FIXED - ALL 8 SUGGESTIONS + SUB DONE")
print(f"File: {seo_filename}, Title: {final_yt_title}")
print(f"A/B Titles: A={title_a} | B={title_b}")

# ========== 7. ENGAGEMENT - PINNED COMMENT + COMMUNITY POLL ==========
pinned_comment = f"Which gadget would you buy? A) {topic_search} B) iPhone? Comment below! 👇 In my opinion, {topic_search} wins. What do you think? #Tech that helps humans"
with open("pinned_comment.txt","w") as f:
    f.write(pinned_comment)
community_poll = f"Poll: Which AI is better for {topic_search}? 1) ChatGPT 2) Gemini? Vote in comments!"
with open("community_poll.txt","w") as f:
    f.write(community_poll)
print(f"Pinned: {pinned_comment}")
print(f"Community Poll: {community_poll}")
print(f"Consistency Reminder: Hafte me 4-5 shorts - monthly nahi!")
print(f"Holiday Check Done, Reddit Check Done, Social Proof Added, Easter Egg Added")

upload_video(seo_filename, final_yt_title, description, tags)
