import random, requests, re, os, time, textwrap, subprocess
import xml.etree.ElementTree as ET
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build

# Try auto_music safely
try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(topic): return None

print("Starting FINAL SHORTS BOT - Products + Big Machine + Army + World Trending + Piper TTS + Fast 2.5s...")

# ========== 1. NICHE - PRODUCTS + BIG MACHINE + ARMY + TECH TREND - WORLD ==========
TECH_ALLOWED = [
    # Products review
    "iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","tech","airpods","macbook","tablet","camera","charger",
    # Big Machine
    "excavator","crane","bulldozer","forklift","tractor","jcb","caterpillar","komatsu","hydraulic","construction","heavy machine","big machine","dump truck",
    # Army Machine
    "tank","fighter jet","military","army","abrams","f35","f22","drone","helicopter","warship","missile","howitzer","apc","armored","navy","air force",
    # Tech trend
    "ai","chatgpt","tesla","robot","drone","5g","chip","nvidia","battery","electric","autonomous"
]
BANNED_NON_TECH = [
    "tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","bapuji","taarak","tmkoc","bhabi","kapil","bigg boss","lottery",
    "football","cricket","basketball","baseball","soccer","wwe","movie","bollywood","hollywood","election","biden","trump","modi"
]
CHANNEL_LINK = "https://www.youtube.com/@TECH4USA"
OLD_SHORTS = "https://www.youtube.com/@TECH4USA/shorts"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

EVERGREEN_FALLBACK = [
    # Products review
    "CMF Headphones Review 40 Hour Battery Test",
    "iPhone 16 Hidden Feature That Saves Battery 2 Days",
    "Samsung S24 Ultra vs iPhone 15 Camera Test",
    # Big Machine
    "Caterpillar Excavator D9 - How This Big Machine Works",
    "World Biggest Crane 10000 Ton Lifting Power",
    "Bulldozer vs Excavator Which Machine Wins",
    # Army Machine
    "Abrams Tank M1A2 - Army Machine Review Inside Power",
    "F35 Fighter Jet - How This Army Machine Flies",
    "Military Drone MQ9 Reaper - Army Tech Explained",
    # Tech Trend
    "AI Tool Saving 5 Hours A Day World Trending"
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

def clean_for_tts(text):
    """Remove links to prevent www dot com speaking - TTS clean"""
    text = re.sub(r'http\S+|www\S+|\.com|\.net|\.org', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^a-zA-Z0-9.,!?$% ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_unique_title(title):
    try:
        if not os.path.exists("used_titles.txt"):
            open("used_titles.txt","w").close()
        with open("used_titles.txt","r") as f:
            used = f.read().splitlines()
        if title in used:
            title = f"{title} Review {random.randint(1,99)}"
        with open("used_titles.txt","a") as f:
            f.write(title+"\n")
        return title[:90]
    except:
        return title[:90]

# ========== 2. PIPER TTS - HUMAN EMOTIONAL TEZ HIGH ==========
def text_to_speech_piper(text, output_path="voice.wav"):
    """Piper TTS - offline human emotional - 1.1x speed fast"""
    clean_text = clean_for_tts(text)
    # Remove repeat sentences - ensure unique
    sentences = []
    seen = set()
    for s in clean_text.split('.'):
        s = s.strip()
        if len(s) > 5 and s.lower() not in seen:
            seen.add(s.lower())
            sentences.append(s)
    clean_text = '. '.join(sentences) + '.'
    
    # Try Piper TTS first - 100% offline, no char 0 error
    try:
        model_path = "en_US-lessac-medium.onnx"
        if os.path.exists(model_path):
            # Piper command - fast + emotional
            cmd = f'echo "{clean_text}" | piper --model {model_path} --output_file {output_path} --length_scale 0.9 --sentence_silence 0.1'
            # length_scale 0.9 = 10% faster - tez voice
            result = subprocess.run(cmd, shell=True, timeout=30, capture_output=True, text=True)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print(f"✅ Piper TTS success - {output_path} - human emotional tez")
                return output_path
        print("Piper model not found, trying gTTS fallback")
    except Exception as e:
        print(f"⚠️ Piper failed: {e} - using gTTS fallback")
    
    # Fallback gTTS - but cleaned
    try:
        from gtts import gTTS
        gTTS(text=clean_text, lang='en', tld='us', slow=False).save("voice.mp3")
        # Convert mp3 to wav path for uniform handling - actually keep mp3
        return "voice.mp3"
    except Exception as e:
        print(f"❌ TTS failed: {e}")
        return None

# ========== 3. FAST PACED VISUALS - HAR 2-2.5 SEC CHANGE - DIFFERENT ANGLES ==========
def get_fast_paced_clips(topic, total_duration):
    """
    Har 2-2.5 sec me visual change - different angles
    Products: side angle, bottom angle, rotating 360, top flat lay, grip angle, 45 degree
    Big Machine / Army: closeup, wide, cockpit, tracks, engine, action
    """
    clips = []
    topic_low = topic.lower()
    
    # Detect niche for query
    if any(x in topic_low for x in ["excavator","crane","bulldozer","jcb","caterpillar","dump","construction","big machine"]):
        queries = [
            f"{topic} big machine closeup side angle 4k",
            f"{topic} excavator action working",
            f"{topic} heavy machine top view flat lay",
            f"{topic} construction machine operator cabin",
            f"{topic} machine tracks hydraulic detail",
            f"{topic} big machine rotating 360",
            f"american construction site {topic}",
            f"{topic} machine power lifting"
        ]
    elif any(x in topic_low for x in ["tank","fighter","military","army","abrams","f35","drone","warship","missile"]):
        queries = [
            f"{topic} army tank closeup side angle",
            f"{topic} military machine action firing",
            f"{topic} fighter jet cockpit inside",
            f"{topic} army vehicle top view",
            f"{topic} tank tracks detail bottom angle",
            f"{topic} military drone flying 4k",
            f"{topic} army machine rotating 360",
            f"us army {topic} powerful"
        ]
    else:
        # Products review
        queries = [
            f"{topic} product review closeup side angle",
            f"{topic} gadget in hand bottom angle",
            f"{topic} product rotating 360 degree",
            f"{topic} back panel top view flat lay",
            f"{topic} product screen display 45 degree",
            f"{topic} hand holding grip angle",
            f"{topic} unboxing american hands",
            f"{topic} product features detail macro"
        ]
    
    random.shuffle(queries)
    # Fast paced: 8 clips for 20 sec = 2.5 sec each
    num_clips = 8
    per_clip = total_duration / num_clips
    
    for i in range(num_clips):
        try:
            q = queries[i % len(queries)]
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=15&orientation=portrait&size=medium"
            headers = {"Authorization": PEXELS_API_KEY} if PEXELS_API_KEY else {}
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                continue
            vids = resp.json().get('videos', [])
            if not vids:
                continue
            video = random.choice(vids[:5])  # Top 5 for quality
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
                try:
                    clip = clip.subclip(start, start+per_clip)
                except:
                    clip = clip.with_end(per_clip)
            clip = safe_set_duration(clip, per_clip)
            # Pattern interrupt - zoom every clip different - fast paced
            try:
                clip = clip.resize(height=1920)
            except:
                try:
                    clip = clip.resized(height=1920)
                except:
                    pass
            # Fast zoom - 0.08 for shorts
            zoom_factor = 1.0 + (0.12 if i % 2 == 0 else 0.06) * (1)
            try:
                clip = clip.resize(lambda t: zoom_factor + 0.08 * (t / max(per_clip,1)))
            except:
                pass
            clips.append(clip)
            print(f"✅ Clip {i+1}/{num_clips} - {q} - {per_clip:.1f}s - different angle")
        except Exception as e:
            print(f"Clip {i} skip: {e}")
            continue
    
    if not clips:
        # Fallback color + pattern
        print("No pexels clips - using gradient fallback")
        return None
    
    final_bg = concatenate_videoclips(clips, method="compose")
    final_bg = safe_set_duration(final_bg, total_duration)
    print(f"✅ Fast paced bg ready - {len(clips)} clips - har {per_clip:.1f}s change")
    return final_bg

# ========== 4. CAPTIONS - BOTTOM CLEAN - REFERENCE VIDEO STYLE ==========
def create_bottom_clean_captions(full_text, audio_duration):
    """
    Bottom clean captions - white text, black semi-transparent bg, 2 lines max
    Reference video style - fast paced
    """
    clean_text = clean_for_tts(full_text)
    # Split into fast phrases - 2-2.5 sec per phrase
    words = clean_text.split()
    # Group words into 4-5 word phrases for bottom captions
    phrases = []
    for i in range(0, len(words), 5):
        phrase = ' '.join(words[i:i+5])
        if phrase:
            phrases.append(phrase)
    
    clips = []
    per_phrase = audio_duration / max(len(phrases),1)
    
    for i, phrase in enumerate(phrases):
        # Bottom clean box - reference style
        W, H = 1080, 1920
        img = Image.new('RGBA', (W, 320), (0,0,0,0))
        draw = ImageDraw.Draw(img, 'RGBA')
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        except:
            font = ImageFont.load_default()
        
        # Black semi-transparent bg - bottom
        draw.rectangle((0, 0, W, 320), fill=(0,0,0,180))
        
        # White text - clean - 2 lines max
        lines = textwrap.wrap(phrase.upper(), width=28)
        y = 30
        for line in lines[:2]:  # Max 2 lines
            bbox = draw.textbbox((0,0), line, font=font)
            w = bbox[2]-bbox[0]
            x = (W - w)//2
            # White with black stroke - clean
            draw.text((x, y), line, fill="white", font=font, stroke_width=6, stroke_fill="black")
            y += 70
        
        clip = ImageClip(np.array(img))
        clip = safe_set_duration(clip, per_phrase)
        try:
            clip = clip.set_start(i * per_phrase)
        except:
            clip = clip.with_start(i * per_phrase)
        # Bottom position
        try:
            clip = clip.set_position(('center', 0.78), relative=True)
        except:
            clip = clip.with_position(('center', 0.78), relative=True)
        clips.append(clip)
    
    return clips

def create_progress_bar(duration):
    try:
        bar = ColorClip(size=(1080, 10), color=(255, 0, 0)).set_duration(duration)
        try:
            bar = bar.set_position(('center','top'))
        except:
            bar = bar.with_position(('center','top'))
        return bar
    except:
        return None

# ========== 5. TRENDING - WORLD WIDE - TECH ONLY - PRODUCTS + BIG MACHINE + ARMY ==========
def get_trending_world_tech():
    print("WORLD TRENDING CHECK: Google World + YouTube World + Reddit technology + MachinePorn + TankPorn")
    final_topic = None
    source = ""
    
    # 1. Google Trends World - RSS
    try:
        r = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=15)  # US still biggest tech market but world topics included
        root = ET.fromstring(r.content)
        items = root.findall('.//item/title')
        random.shuffle(items)
        for item in items[:25]:
            topic = item.text.strip()
            low = topic.lower()
            if any(b in low for b in BANNED_NON_TECH):
                continue
            if any(t in low for t in TECH_ALLOWED):
                if len(topic) > 3:
                    final_topic = topic
                    source = "google_world_tech"
                    print(f"WORLD TECH FROM GOOGLE: {topic}")
                    break
    except Exception as e:
        print(f"Google RSS error: {e}")
    
    # 2. YouTube World Trending Tech
    if not final_topic:
        try:
            if YOUTUBE_API_KEY:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                yt_req = youtube.videos().list(part='snippet', chart='mostPopular', regionCode='US', maxResults=40, videoCategoryId="28").execute()
                for item in yt_req.get('items', []):
                    yt_title = item['snippet']['title']
                    low = yt_title.lower()
                    if any(b in low for b in BANNED_NON_TECH):
                        continue
                    if any(t in low for t in TECH_ALLOWED):
                        if 5 < len(yt_title) < 90:
                            final_topic = re.sub(r'[^a-zA-Z0-9 ]', '', yt_title).strip()[:60]
                            source = "youtube_world_tech"
                            print(f"YOUTUBE WORLD TECH: {yt_title}")
                            break
        except Exception as e:
            print(f"YouTube error: {e}")
    
    # 3. Reddit - multiple subs: technology, MachinePorn, TankPorn, aviation, gadgets
    if not final_topic:
        for sub in ["technology", "MachinePorn", "TankPorn", "gadgets", "aviation", "construction"]:
            try:
                r = requests.get(f"https://www.reddit.com/r/{sub}/top/.json?limit=10", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for child in data['data']['children']:
                        t = child['data']['title']
                        low = t.lower()
                        if any(b in low for b in BANNED_NON_TECH):
                            continue
                        if any(k in low for k in TECH_ALLOWED):
                            final_topic = t[:60]
                            source = f"reddit_{sub}"
                            print(f"REDDIT {sub}: {t}")
                            break
                if final_topic:
                    break
            except Exception as e:
                print(f"Reddit {sub} error: {e}")
                continue
    
    # 4. Fallback evergreen - products + big machine + army
    if not final_topic:
        final_topic = random.choice(EVERGREEN_FALLBACK)
        source = "evergreen_world"
    
    print(f"FINAL WORLD TOPIC: {final_topic} from {source}")
    return final_topic, source

def clean_news_text(raw):
    raw = re.sub('<[^<]+?>', '', raw)
    raw = raw.replace("&apos;", "'").replace("&quot;", '"').replace("&amp;", "&")
    raw = re.split(r'\s-\s[A-Z][a-z]+\s*$', raw)[0]
    sentences = [s.strip() for s in re.split(r'\.\s+', raw) if len(s.strip()) > 10]
    # Remove duplicate sentences - no repeat
    unique = []
    seen = set()
    for s in sentences:
        low = s.lower()
        if low not in seen:
            seen.add(low)
            unique.append(s)
    if not unique:
        return raw[:300].strip()
    return '. '.join(unique[:2])[:350].strip()

# ========== 6. EMOTIONAL SCRIPT - PRODUCTS + BIG MACHINE + ARMY - NO REPEAT ==========
def get_emotional_script(topic):
    """
    Emotional connection se bharpoor - products review + big machine + army
    No sentence repeat - link free
    """
    real_news_text = ""
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(topic)}+tech+when:1d&hl=en-US&gl=US&ceid=US:en"
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

    if len(real_news_text) < 20:
        real_news_text = f"{topic} is trending worldwide right now"

    topic_low = topic.lower()
    
    # Emotional templates - different for each niche - NO REPEAT
    if any(x in topic_low for x in ["excavator","crane","bulldozer","jcb","caterpillar","construction","big machine","dump"]):
        templates = [
            f"Paying thousands for this big machine? I tested {topic} for 7 days and I am shocked. {real_news_text}. This beast lifts 50 tons like a feather. I personally love the hydraulic power. Most people dont know this secret feature saves 3 hours daily. Would you drive this? Comment A for yes B for no.",
            f"This big machine changed my life. {topic} can dig 20 feet in 10 seconds. {real_news_text}. I was on a construction site in Texas and this saved our project. The engine roars like a lion. 99 percent operators miss this trick. Which big machine is your favorite? Comment below.",
            f"Worlds biggest {topic} just revealed. {real_news_text}. I compared it with normal machines and the power difference is insane. This machine built the tallest tower in Dubai. My heart beats faster when I hear its engine. Is this worth millions? Tell me.",
        ]
    elif any(x in topic_low for x in ["tank","fighter","military","army","abrams","f35","drone","warship","missile"]):
        templates = [
            f"Army secrets exposed. This {topic} can destroy a building from 3 miles away. {real_news_text}. I personally still love this army machine. US Army uses this in every war zone. The armor is so strong even missiles bounce off. 99 percent people never saw inside. Want to see cockpit? Comment yes.",
            f"Paying 10 million dollars for this army machine? {topic} just entered service. {real_news_text}. This tank survived 5 direct hits in Ukraine war. I met a soldier who drove this from NYC to LA training base. His story gave me goosebumps. The speed is 70 miles per hour on sand. Is this invincible? Comment your opinion.",
            f"Worlds most dangerous {topic} leaked. {real_news_text}. This fighter jet goes Mach 2 and enemies cant even see it. I tested the simulator and my hands were shaking. This army machine protects America every day. The technology inside is from 2030. Which army machine scares you most? Tell me.",
        ]
    else:
        # Products review + tech trend - CMF style
        templates = [
            f"Paying 99 dollars for this? I tested {topic} for 7 days and I personally still love it. {real_news_text}. Battery lasts 40 hours straight. I traveled from NYC to LA and never charged. The bass hits so hard my chest vibrates. Secret feature double tap for noise cancellation. Worth it? Comment A for yes B for no.",
            f"This product changed my life. {topic} has a hidden feature 99 percent dont know. {real_news_text}. I made this mistake for years and wasted money. Now my phone battery lasts 2 days with one setting. My friends in Texas all switched after seeing this. Which gadget would you buy? Comment below.",
            f"World trending {topic} just launched worldwide. {real_news_text}. I compared it with iPhone and Samsung and this wins for price. The design feels like 1000 dollar product but costs 69. I unboxed it and my heart skipped a beat. The display is so bright you can see in direct sun. Would you buy this? Tell me.",
            f"Stop scrolling. {topic} is number one trending in the world right now. {real_news_text}. In my opinion this is the best product of 2026. I used it 30 days nonstop and here is my honest review. It saves me 2 hours every week. The build quality is insane for this price. Which color would you pick? Comment.",
        ]
    
    final_script = random.choice(templates)
    # Clean + ensure no repeat + 65-70 words for 20 sec - fast paced
    final_script = clean_for_tts(final_script)
    words = final_script.split()
    # Remove duplicate words phrases - ensure unique sentences
    sentences = [s.strip() for s in final_script.split('.') if len(s.strip()) > 5]
    unique_sentences = []
    seen_sent = set()
    for s in sentences:
        low = s.lower()
        if low not in seen_sent:
            seen_sent.add(low)
            unique_sentences.append(s)
    final_script = '. '.join(unique_sentences)
    # Cap to 65-70 words - no repeat, fast
    final_words = final_script.split()
    if len(final_words) > 70:
        final_words = final_words[:68]
        final_script = ' '.join(final_words) + '.'
    
    print(f"Emotional script - {len(final_script.split())} words - no repeat - niche: {topic_low[:30]}")
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
        print(f"SEO keyword error: {e}")
    suffixes = ["review 2026", "world trending", "big machine", "army machine", "honest review", "how it works"]
    for suf in suffixes:
        k = f"{topic} {suf}"
        if k not in keywords:
            keywords.append(k)
    keywords = list(dict.fromkeys([k.strip() for k in keywords if len(k)>3]))[:12]
    return keywords

def seo_optimize(topic, script_text):
    keywords = fetch_seo_keywords(topic)
    base_title = topic.replace("#tech","").replace("#shorts","").strip()
    base_title = ' '.join(base_title.split()[:6])
    
    # Clean title - 1 emoji only - products + big machine + army
    topic_low = topic.lower()
    if any(x in topic_low for x in ["excavator","crane","bulldozer","big machine"]):
        emoji = "🚜"
        templates = [f"{base_title} - Big Machine Power Test", f"Why {base_title} Is Changing Construction", f"{base_title} Honest Review - Worth It?"]
    elif any(x in topic_low for x in ["tank","fighter","army","military"]):
        emoji = "🎖️"
        templates = [f"{base_title} - Army Machine Inside Power", f"{base_title} Military Review - Secret Feature", f"How {base_title} Protects America"]
    else:
        emoji = "🔥"
        templates = [f"{base_title} Review - 7 Days Tested", f"{base_title} - Hidden Feature 99% Dont Know", f"{base_title} Worth $99? Honest Test"]
    
    title_a = random.choice(templates)
    title_b = f"{emoji} {random.choice(templates)}"
    final_title = title_b if len(title_b) < 65 else title_a
    final_title = final_title[:65]
    
    with open("ab_titles.txt","w") as f:
        f.write(f"A: {title_a}\nB: {title_b}\n")
    
    kw_str = ", ".join(keywords[:5])
    description = f"{base_title} honest review worldwide trending.\nHow {topic} works - full breakdown fast paced.\n\n{script_text}\n\nHello world! I tested {topic} for 7 days. {topic} is trending worldwide - Products + Big Machine + Army Machine knowledge.\n\nIn this Shorts:\n- Honest review after 7 days test\n- Hidden features 99% dont know\n- Is it worth your money?\n\nRelated: {kw_str}\n\nBased on Google World Trends + YouTube World + Reddit r/technology + MachinePorn + TankPorn real data. Human curated worldwide.\n\nWatch More: {OLD_SHORTS}\nSubscribe: {CHANNEL_LINK}\n\n#Shorts #Tech #{topic.replace(' ', '')} #ProductReview #BigMachine #ArmyMachine #WorldTrending\n"
    
    def clean_tag(t):
        t = re.sub(r'[<>"\'#]', '', t)
        t = re.sub(r'[^\w\s]', ' ', t)
        t = ' '.join(t.split()).strip()[:25]
        return t.lower()

    raw_tags = [topic, f"{topic} review", f"{topic} world trending", "product review", "big machine", "army machine", "world tech", "honest review"]
    for kw in keywords[:5]:
        raw_tags.append(kw)
    cleaned = []
    seen = set()
    total_len = 0
    for t in raw_tags:
        ct = clean_tag(t)
        if len(ct) < 2: continue
        if ct in seen: continue
        if len(ct) > 25: continue
        if total_len + len(ct) + 1 > 400:
            break
        cleaned.append(ct)
        seen.add(ct)
        total_len += len(ct) + 1
        if len(cleaned) >= 12:
            break
    if len(cleaned) < 3:
        cleaned = ["product review", "big machine", "army machine", "world trending", "tech review 2026"]
    tags = cleaned
    print(f"✅ TAGS: {tags}")
    return final_title, description, tags, title_a, title_b

# ========== MAIN ==========
topic_search, script_source = get_trending_world_tech()
topic_title = get_unique_title(topic_search)
script_text = get_emotional_script(topic_search)

print(f"FINAL TOPIC: {topic_title}")
print(f"FINAL SCRIPT: {script_text}")

# Piper TTS - human emotional tez high
voice_path = text_to_speech_piper(script_text, "voice.wav")
if not voice_path or not os.path.exists(voice_path):
    print("❌ TTS failed - exit")
    exit(1)

time.sleep(0.5)
audio = AudioFileClip(voice_path)
try:
    audio = audio.volumex(1.15)  # High volume - emotional
except:
    pass

# Music 12% - fast paced - crash proof
bg_music_path = None
try:
    bg_music_path = fetch_music_for_video(topic_search)
except Exception as music_err:
    print(f"⚠️ Music fetch failed - voice only: {music_err}")
    bg_music_path = None

final_audio = audio
if bg_music_path and os.path.exists(bg_music_path):
    try:
        bg_music = AudioFileClip(bg_music_path).subclip(0, audio.duration)
        bg_music = bg_music.volumex(0.12)  # 12% for shorts
        try:
            bg_music = bg_music.audio_fadein(0.5).audio_fadeout(0.5)
        except:
            pass
        print(f"✅ Music at 12% - {bg_music_path}")
        final_audio = CompositeAudioClip([audio, bg_music])
    except Exception as e:
        print(f"⚠️ Music mix failed - voice only: {e}")
        final_audio = audio

max_duration = 20  # Fast 20 sec for retention
if final_audio.duration > max_duration:
    try:
        final_audio = final_audio.subclip(0, max_duration)
    except:
        final_audio = final_audio.with_end(max_duration)

W, H = 1080, 1920
bg_clip = get_fast_paced_clips(topic_search, final_audio.duration)
if not bg_clip:
    bg_clip = ColorClip(size=(W,H), color=(10,10,30))
    bg_clip = safe_set_duration(bg_clip, final_audio.duration)

# Overlays - human curated + world trending badge
def create_overlay(duration, title, search):
    overlay = Image.new('RGBA', (W,H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay, 'RGBA')
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font_big = ImageFont.load_default()
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except:
        font_small = ImageFont.load_default()
    try:
        font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_badge = ImageFont.load_default()
    
    # World trending badge
    draw.rounded_rectangle((20, 20, 650, 70), radius=20, fill=(0, 200, 255, 240))
    draw.text((35, 28), "WORLD TRENDING • HUMAN CURATED • USA", fill=(0,0,0), font=font_badge)
    draw.rounded_rectangle((20, 80, 600, 120), radius=12, fill=(255,255,255,200))
    draw.text((30, 88), f"Source: World Trends + Reddit MachinePorn", fill=(50,50,50), font=font_small)
    
    # Title bottom
    draw.rectangle((0, 1250, W, H), fill=(0,0,0,210))
    y = 1280
    clean_title_raw = title.replace("#tech","").replace("#shorts","").strip()
    clean_title_raw = ' '.join(clean_title_raw.split()[:7])
    for line in textwrap.wrap(clean_title_raw, width=26):
        draw.text((35, y), line.upper(), fill="white", font=font_big, stroke_width=5, stroke_fill="black")
        y+=58
        if y>1480:
            break
    draw.rounded_rectangle((30, 1510, W-30, 1580), radius=25, fill=(255,235,0,255))
    draw.text((60, 1525), "A for YES B for NO? Comment! 👇", fill=(0,0,0), font=font_small)
    return safe_set_duration(ImageClip(np.array(overlay)), duration)

from upload_youtube import upload_video
final_yt_title, description, tags, title_a, title_b = seo_optimize(topic_search, script_text)
seo_filename = re.sub(r'[^a-z0-9]+', '-', topic_search.lower()).strip('-')[:40]
seo_filename = f"{seo_filename}-world-trending-2026.mp4"

overlay_clip = create_overlay(final_audio.duration, final_yt_title, topic_search)
caption_clips = create_bottom_clean_captions(script_text, final_audio.duration)
layers = [bg_clip, overlay_clip, *caption_clips]
progress_bar = create_progress_bar(final_audio.duration)
if progress_bar:
    layers.append(progress_bar)

final = CompositeVideoClip(layers, size=(W,H))
final = safe_set_duration(final, final_audio.duration)
final = safe_set_audio(final, final_audio)
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)

print(f"✅ SHORTS FINAL DONE - Products + Big Machine + Army + World Trending")
print(f"File: {seo_filename}, Title: {final_yt_title}")
print(f"A/B: A={title_a} | B={title_b}")
print(f"Fast paced: har 2.5 sec visual change - different angles")
print(f"Piper TTS: human emotional tez - no repeat - link free")

pinned_comment = f"Which one would you buy? A) {topic_search} B) Other? Comment below! In my opinion, {topic_search} wins. What do you think? #World Trending"
with open("pinned_comment.txt","w") as f:
    f.write(pinned_comment)

upload_video(seo_filename, final_yt_title, description, tags)
