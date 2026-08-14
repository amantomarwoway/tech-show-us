import random, requests, re, os, time, textwrap, datetime, subprocess
import xml.etree.ElementTree as ET
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build

try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(topic): return None

print("Starting FINAL LONG VIDEO BOT - Products + Big Machine + Army + World Trending + Piper TTS + Fast 2.5s - Same Edit as Shorts...")

# ========== 1. NICHE - PRODUCTS + BIG MACHINE + ARMY + WORLD TRENDING - NO AMERICA FIX ==========
TECH_ALLOWED = [
    "iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","macbook","tablet","camera","charger","powerbank",
    "excavator","crane","bulldozer","forklift","tractor","jcb","caterpillar","komatsu","hydraulic","construction","heavy machine","big machine","dump truck","loader",
    "tank","fighter jet","military","army","abrams","f35","f22","drone","helicopter","warship","missile","howitzer","apc","armored","navy","air force","tank",
    "ai","chatgpt","tesla","robot","electric","chip","nvidia","battery","5g","vr","ar"
]
BANNED_NON_TECH = [
    "tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","bapuji","taarak","tmkoc","bhabi","kapil","bigg boss","lottery",
    "football","cricket","basketball","baseball","soccer","wwe","movie","bollywood","hollywood","election","biden","trump","modi","congress"
]
CHANNEL_LINK = "https://www.youtube.com/@TECH4USA"
OLD_VIDEOS = "https://www.youtube.com/@TECH4USA/videos"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# EVERGREEN WORLD - PRODUCTS + BIG MACHINE + ARMY + TECH TREND
EVERGREEN_TOPICS = [
    # Products review
    "CMF Headphones Honest Review After 7 Days - Worth $69?",
    "iPhone 16 Hidden Battery Feature That Saves 2 Days - Tested",
    "Samsung S24 Ultra vs iPhone 15 - Which Camera Wins 2026",
    "Best Earbuds Under $100 World Review 2026",
    # Big Machine
    "Caterpillar D9 Excavator - How This Big Machine Works - Power Test",
    "World Biggest Crane Lifting 10000 Ton - Big Machine Knowledge",
    "Bulldozer vs Excavator - Big Machine Comparison - Which Wins?",
    "JCB Machine Full Review - Hidden Features 99% Dont Know",
    # Army Machine
    "Abrams Tank M1A2 - Army Machine Review - Inside Power - USA",
    "F35 Fighter Jet How This Army Machine Flies - Mach 2 Speed",
    "Military Drone MQ9 Reaper - Army Tech That Protects America",
    "M777 Howitzer Army Machine - How It Fires 30km",
    # World Tech Trend + New Tech
    "AI Tools That Will Replace Jobs in 2026 - World Trending New Tech",
    "Tesla Bot New Update - Future Tech World Trending",
    "ChatGPT New Feature Leaked - Tech World News Today",
    "Secret Google Trick 99 Percent People Dont Know Worldwide"
]

HOOK_EMOTIONS = [
    {"hook": "Paying 99 dollars? I tested 7 days and I am shocked", "emotion": "😲 SHOCK", "type": "Product Review", "color": (255,0,0)},
    {"hook": "This big machine lifts 50 tons like a feather", "emotion": "🤩 POWER", "type": "Big Machine", "color": (255,165,0)},
    {"hook": "Army secrets - this tank survived 5 missile hits", "emotion": "🎖️ BRAVE", "type": "Army Machine", "color": (0,200,255)},
    {"hook": "They hide this feature - 99% dont know", "emotion": "😤 ANGER", "type": "Hidden Feature", "color": (255,0,100)},
    {"hook": "This trick saves 2 hours every week + money", "emotion": "🤑 GREED", "type": "Problem-Solution", "color": (0,255,100)},
    {"hook": "I was in Texas construction site and this saved us", "emotion": "🥺 EMPATHY", "type": "Storytelling", "color": (100,100,255)},
    {"hook": "World trending number 1 - USA to Dubai", "emotion": "🌍 WORLD", "type": "World Trending", "color": (200,200,200)},
    {"hook": "Controversial but true - apps listening to you", "emotion": "🔥 CONTROVERSY", "type": "Tech Truth", "color": (255,50,0)},
    {"hook": "I met a soldier who drove tank from NYC to LA", "emotion": "💪 MOTIVATION", "type": "Army Story", "color": (255,255,0)},
    {"hook": "Best one at the end will blow your mind", "emotion": "🎯 PAYOFF", "type": "Payoff", "color": (0,255,0)},
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
    """Remove links - no www dot com speak"""
    text = re.sub(r'http\S+|www\S+|\.com|\.net|\.org', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^a-zA-Z0-9.,!?$% ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_unique_topic():
    if not os.path.exists("used_long_titles.txt"):
        open("used_long_titles.txt","w").close()
    with open("used_long_titles.txt","r") as f:
        used = f.read().splitlines()
    available = [t for t in EVERGREEN_TOPICS if t not in used]
    if not available:
        available = EVERGREEN_TOPICS
        open("used_long_titles.txt","w").close()
    filtered = [t for t in available if not any(b in t.lower() for b in BANNED_NON_TECH)]
    if not filtered:
        filtered = EVERGREEN_TOPICS
    topic = random.choice(filtered)
    with open("used_long_titles.txt","a") as f:
        f.write(topic+"\n")
    return topic

def fetch_reddit_world():
    """World trending - technology + MachinePorn + TankPorn + gadgets + construction + aviation"""
    for sub in ["technology", "MachinePorn", "TankPorn", "gadgets", "construction", "aviation", "MilitaryPorn"]:
        try:
            r = requests.get(f"https://www.reddit.com/r/{sub}/top/.json?limit=8", headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
            if r.status_code == 200:
                data = r.json()
                for child in data['data']['children']:
                    t = child['data']['title']
                    low = t.lower()
                    if any(b in low for b in BANNED_NON_TECH): continue
                    if any(k in low for k in TECH_ALLOWED):
                        return f"Reddit {sub} trending: {t[:80]}"
        except:
            pass
    return ""

# ========== 2. PIPER TTS - HUMAN EMOTIONAL TEZ HIGH - LONG VIDEO ==========
def text_to_speech_piper_long(text, output_prefix="voice_long"):
    """Long video - split into 3 parts - Piper TTS - 0.9 speed = tez"""
    clean_text = clean_for_tts(text)
    # Remove duplicate sentences
    sentences = []
    seen = set()
    for s in clean_text.split('.'):
        s = s.strip()
        if len(s) > 8 and s.lower() not in seen:
            seen.add(s.lower())
            sentences.append(s)
    clean_text = '. '.join(sentences) + '.'
    
    # Split into 3 chunks for TTS
    words = clean_text.split()
    chunk_size = len(words)//3
    chunks = [
        ' '.join(words[:chunk_size]),
        ' '.join(words[chunk_size:chunk_size*2]),
        ' '.join(words[chunk_size*2:])
    ]
    
    audio_files = []
    model_path = "en_US-lessac-medium.onnx"
    piper_exists = os.path.exists(model_path)
    
    for idx, chunk in enumerate(chunks):
        out_path = f"{output_prefix}_{idx}.wav"
        mp3_path = f"{output_prefix}_{idx}.mp3"
        success = False
        
        if piper_exists:
            try:
                # Escape quotes for shell
                safe_chunk = chunk.replace('"', '').replace('`','').replace('$','')
                cmd = f'echo "{safe_chunk}" | piper --model {model_path} --output_file {out_path} --length_scale 0.9 --sentence_silence 0.15'
                result = subprocess.run(cmd, shell=True, timeout=60, capture_output=True)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                    print(f"✅ Piper long part {idx} success - tez emotional")
                    audio_files.append(out_path)
                    success = True
            except Exception as e:
                print(f"⚠️ Piper long part {idx} failed: {e}")
        
        if not success:
            try:
                from gtts import gTTS
                gTTS(text=chunk, lang='en', tld='us', slow=False).save(mp3_path)
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
                    audio_files.append(mp3_path)
                    print(f"✅ gTTS fallback long part {idx}")
            except Exception as e:
                print(f"❌ TTS part {idx} failed: {e}")
    
    return audio_files

def get_world_trending_long():
    """World trending - Google World + Big Machine + Army"""
    print("WORLD TRENDING LONG CHECK: Google World + Reddit MachinePorn/TankPorn/technology")
    final_topic = None
    source = ""
    
    # 1. Google Trends World
    try:
        r = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=15)
        root = ET.fromstring(r.content)
        items = root.findall('.//item/title')
        random.shuffle(items)
        for item in items[:25]:
            topic = item.text.strip()
            low = topic.lower()
            if any(b in low for b in BANNED_NON_TECH): continue
            if any(t in low for t in TECH_ALLOWED):
                final_topic = topic
                source = "google_world"
                print(f"WORLD TECH LONG: {topic}")
                break
    except Exception as e:
        print(f"Google error: {e}")
    
    # 2. YouTube World Tech
    if not final_topic:
        try:
            if YOUTUBE_API_KEY:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                yt_req = youtube.videos().list(part='snippet', chart='mostPopular', regionCode='US', maxResults=40, videoCategoryId="28").execute()
                for item in yt_req.get('items', []):
                    yt_title = item['snippet']['title']
                    low = yt_title.lower()
                    if any(b in low for b in BANNED_NON_TECH): continue
                    if any(t in low for t in TECH_ALLOWED):
                        final_topic = re.sub(r'[^a-zA-Z0-9 ]', '', yt_title).strip()[:60]
                        source = "youtube_world"
                        break
        except Exception as e:
            print(f"YouTube error: {e}")
    
    # 3. Reddit World - MachinePorn, TankPorn, technology, gadgets, construction
    if not final_topic:
        reddit = fetch_reddit_world()
        if reddit:
            final_topic = reddit.replace("Reddit trending:", "").replace("Reddit", "").strip()[:60]
            source = "reddit_world"
    
    if not final_topic:
        final_topic = get_unique_topic()
        source = "evergreen_world"
    
    print(f"FINAL LONG WORLD TOPIC: {final_topic} from {source}")
    return final_topic

def generate_long_emotional_script(topic):
    """Long - 1300 words - emotional - products + big machine + army + world trending + new tech - no repeat - link free"""
    reddit = fetch_reddit_world()
    real_facts = ""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={requests.utils.quote(topic)}&limit=2&namespace=0&format=json"
        r = requests.get(url, timeout=8)
        if r.status_code==200:
            data = r.json()
            if len(data)>2 and data[2]:
                real_facts = ". ".join(data[2][:2])[:350]
    except:
        pass
    if not real_facts:
        real_facts = f"{topic} is trending worldwide right now. Even TechCrunch and Verge are covering this. This is not just tech, this is power, this is future."

    month_now = datetime.datetime.now().month
    holiday_text = ""
    if month_now == 11: holiday_text = "Black Friday is coming, "
    elif month_now == 9: holiday_text = "Apple Event just happened, "
    elif month_now == 12: holiday_text = "Christmas tech season, "

    topic_low = topic.lower()
    
    # Different script based on niche - emotional connection
    if any(x in topic_low for x in ["excavator","crane","bulldozer","jcb","caterpillar","big machine","construction"]):
        intro = f"Stop scrolling. {holiday_text}Paying millions for this big machine? I spent 7 days on a construction site in Texas with {topic}. This beast changed how I see power. In my opinion, I tested this for real, not AI slop. Some people said AI slop, so I read TechCrunch, Reddit MachinePorn, and talked to operators daily. Human curated big machine knowledge for worldwide audience."
        chapters = [
            f"Chapter 1 - Why {topic} is world trending. {real_facts[:200]}. This big machine can lift 50 tons like a feather. I saw it lift a house foundation in 10 minutes.",
            f"Chapter 2 - Inside power. Hydraulic system 5000 PSI pressure. Engine 600 horsepower. I personally love the roar. My heart beats faster when it starts.",
            f"Chapter 3 - Hidden features 99% operators dont know. Secret button saves 3 hours fuel daily. I discovered this talking to a 30-year operator in Dubai.",
            f"Chapter 4 - Real story. I was stuck in Texas, project delayed. Then {topic} arrived and finished 3 days work in 5 hours. The operator said he drove from NYC to LA for this job.",
            f"Chapter 5 - Comparison bulldozer vs excavator vs crane. Which big machine wins? {topic} vs Caterpillar vs Komatsu. I compared all three. {topic} wins for power, Caterpillar for reliability.",
            f"Chapter 6 - Cost - is it worth millions? I calculated cost per hour. $500 per hour but saves $5000 labor. In my opinion, worth it for big projects.",
            f"Chapter 7 - Future - autonomous big machines 2027. AI will drive this without human. Tesla style. I tested prototype in Nevada. Scary but exciting.",
            f"Chapter 8 - Maintenance secrets. How to keep this beast alive 20 years. Oil change trick, hydraulic filter hack, track tension secret. I learned from manual and real operators.",
            f"Chapter 9 - World biggest - {topic} built Burj Khalifa, Panama Canal, highways. Without big machines, no modern world. This is backbone of civilization.",
            f"Chapter 10 - Final verdict - would I buy this? If I had a construction company, yes. For small jobs, rent. Which big machine is your favorite? Comment below. I reply to every comment.",
        ]
    elif any(x in topic_low for x in ["tank","fighter","army","military","abrams","f35","drone","warship"]):
        intro = f"Army secrets exposed. {holiday_text}This {topic} can destroy everything from 3 miles away. I spent time with US Army veterans who drove this. My hands were shaking when I first sat inside. In my opinion, this is not just machine, this is guardian. Human curated army machine knowledge. Some said AI slop, I met real soldiers, read Reddit TankPorn and MilitaryPorn daily."
        chapters = [
            f"Chapter 1 - Why {topic} is trending worldwide. War in Ukraine, new threats. {real_facts[:200]}. US Army uses this in every war zone. This army machine never lost a battle.",
            f"Chapter 2 - Armor - how strong? Composite armor stops missile direct hit. I saw test video - missile bounced off. The steel is 3 inches thick plus reactive bricks.",
            f"Chapter 3 - Firepower - 120mm gun fires 6 rounds per minute. Range 3 miles accurate. I watched firing and ground shook. The sound gives you goosebumps. You feel power.",
            f"Chapter 4 - Inside cockpit - 4 screens, thermal vision, night vision 5km. I sat inside simulator in Texas base. Soldier who trained me drove this from NYC to LA base. His story - 20 years service.",
            f"Chapter 5 - Speed - 70 mph on sand, 45 mph off-road. Engine 1500 horsepower turbine. Drinks fuel like monster - 1 mile per gallon. But power worth it.",
            f"Chapter 6 - Real war story - {topic} survived 5 direct hits in Ukraine. Crew alive. I talked to veteran on Reddit TankPorn. He said this tank saved his life twice.",
            f"Chapter 7 - Comparison - Abrams vs Russian T90 vs German Leopard. Which army tank wins? I compared armor, gun, speed. Abrams wins for crew safety, Leopard for accuracy.",
            f"Chapter 8 - Cost - 10 million dollars per tank. Worth it? One tank protects 100 soldiers. In my opinion, human life priceless. Army thinks same.",
            f"Chapter 9 - Future - unmanned tanks 2028, AI targeting. F35 already has AI. I saw prototype at airshow. Future war is robots but human heart still needed.",
            f"Chapter 10 - Final - Would this army machine protect America? Yes. This is why America is safe. Which army machine scares you most? Comment. I reply every comment with respect to soldiers.",
        ]
    else:
        # Products review + tech trend + new tech world
        intro = f"Stop scrolling. {holiday_text}Paying 99 dollars for {topic}? I tested this product for 7 days straight and I personally still love it. This is not AI voice only - I used this from NYC to LA flight, 6 hours nonstop. Some people said AI slop, so here is how I actually research - I read TechCrunch, The Verge, Reddit r/technology daily for you. Human curated product review for worldwide audience."
        chapters = [
            f"Chapter 1 - Problem. Your {topic.lower()} is draining money and battery. I made this mistake for years. My old headphones died every 4 hours. Then I found {topic}. Now 40 hours battery.",
            f"Chapter 2 - First impression. Unboxing {topic} - packaging feels premium like $300 product but costs $69. I opened box and heart skipped a beat. Design so clean.",
            f"Chapter 3 - Sound test - I tested bass, treble, mids. Bass hits chest. I played music from NYC to LA flight and never felt tired. Noise cancellation blocks plane engine 100%.",
            f"Chapter 4 - Battery real test. Company says 40 hours. I tested - 38 hours actual with noise cancellation on. Charge 10 min gives 5 hours. I charged once and used whole week Texas trip.",
            f"Chapter 5 - Hidden features 99% dont know. Double tap for transparency mode, triple tap for voice assistant, hold 3 sec for pairing two devices. I found these after 3 days use.",
            f"Chapter 6 - Comparison - {topic} vs AirPods Pro vs Sony WH1000XM5. Which wins? I tested all three. {topic} wins for battery and price, AirPods for iPhone integration, Sony for ANC.",
            f"Chapter 7 - Real world use - Gym, flight, office, walking. Sweat proof? Yes I ran 5 miles. Flight? Perfect. Office? Colleagues cant hear my music. This is versatile.",
            f"Chapter 8 - Durability - I dropped from 5 feet twice. No scratch. Hinge strong. Headband comfortable for 6 hours. My friend said same after 3 months use.",
            f"Chapter 9 - World trending - why {topic} is number 1 worldwide right now? Price $69, features $300. World sees value. In USA, Dubai, India all trending. {reddit} {real_facts[:150]}",
            f"Chapter 10 - Final verdict - Would I buy again? Yes 100%. In my opinion, best under $100. Which gadget would you buy? A) {topic} B) iPhone? Comment. I reply every comment. If you skip you will regret tomorrow.",
        ]
    
    full = intro + " " + " ".join(chapters) + f" Final Thoughts: If this helped, subscribe for human curated tech - products + big machine + army + world trending. I post 4-5 times a week, not monthly. Consistency key. Question - Which would you buy? A) {topic.split()[0]} B) Other? Let me know. And if someone says AI slop, reply - I test real, read real sources, give honest opinion. See you next video. {topic} will change your life."
    
    # Clean - no repeat - link free - 1300 words max
    full = clean_for_tts(full)
    words = full.split()
    # Remove duplicate sentences
    sentences = [s.strip() for s in full.split('.') if len(s.strip()) > 10]
    unique = []
    seen = set()
    for s in sentences:
        low = s.lower()
        if low not in seen:
            seen.add(low)
            unique.append(s)
    full = '. '.join(unique)
    words = full.split()
    if len(words) > 1300:
        full = ' '.join(words[:1300]) + "."
    print(f"Long emotional script - {len(full.split())} words - {len(full.split())//150} min - niche: {topic_low[:30]} - no repeat")
    return full

def create_ctr_thumbnail(topic):
    try:
        W,H=1280,720
        thumb=Image.new('RGB',(W,H),(5,5,25))
        draw=ImageDraw.Draw(thumb)
        for y in range(H):
            r=int(5 + y*0.15); g=int(5 + y*0.1); b=int(25 + y*0.25)
            draw.line([(0,y),(W,y)],fill=(r,g,b))
        try: font_huge=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
        except: font_huge=ImageFont.load_default()
        try: font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 65)
        except: font_big=ImageFont.load_default()
        try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
        except: font_small=ImageFont.load_default()
        
        main_word=topic.split()[0].upper()[:10]
        draw.text((30,30), f"{main_word}?", fill="white", font=font_huge, stroke_width=10, stroke_fill="black")
        # Different for big machine / army
        low = topic.lower()
        if any(x in low for x in ["excavator","crane","bulldozer","big machine"]):
            draw.text((30,160), "POWER!", fill="#FFEB00", font=font_huge, stroke_width=10, stroke_fill="black")
            draw.text((30,300), "99% DON'T KNOW", fill="#00D4FF", font=font_big, stroke_width=6, stroke_fill="black")
        elif any(x in low for x in ["tank","fighter","army"]):
            draw.text((30,160), "ARMY SECRET!", fill="#FF0000", font=font_huge, stroke_width=10, stroke_fill="white")
            draw.text((30,300), "INSIDE POWER", fill="#FFEB00", font=font_big, stroke_width=6, stroke_fill="black")
        else:
            draw.text((30,160), "SECRET!", fill="#FFEB00", font=font_huge, stroke_width=10, stroke_fill="black")
            draw.text((30,300), "99% DON'T KNOW", fill="#00D4FF", font=font_big, stroke_width=6, stroke_fill="black")
        
        draw.polygon([(950,150),(1150,360),(950,570)], fill="#FF0000", outline="white", width=6)
        draw.rounded_rectangle((30,600,600,670), radius=20, fill=(0,200,255))
        draw.text((50,615), "HUMAN-CURATED WORLDWIDE", fill="black", font=font_small)
        draw.rounded_rectangle((30,680,650,710), radius=10, fill=(255,255,255,200))
        draw.text((40,685), "Source: TechCrunch + Verge + Reddit", fill=(0,0,0), font=ImageFont.load_default())
        draw.text((W-150,20), "🔥", fill="white", font=font_huge)
        draw.text((W-60, H-40), "👀", fill=(255,255,255,80), font=font_small)
        thumb.save("thumbnail_long.jpg")
        print("✅ THUMBNAIL LONG - High contrast - CTR")
        return "thumbnail_long.jpg"
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None

def seo_optimize_long(topic, script_text):
    keywords=[]
    try:
        url=f"https://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={requests.utils.quote(topic)}"
        r=requests.get(url, timeout=8)
        if r.status_code==200:
            import json
            try:
                data=json.loads(r.text)
                if len(data)>1:
                    for sug in data[1][:8]:
                        if isinstance(sug, list): keywords.append(sug[0])
                        else: keywords.append(str(sug))
            except: pass
    except: pass

    base= ' '.join(topic.split()[:6])
    low = topic.lower()
    if any(x in low for x in ["excavator","crane","bulldozer","big machine"]):
        emoji="🚜"
        clean_titles=[f"{base} - Big Machine Power Test 2026", f"How {base} Works - Hidden Power", f"{base} vs Caterpillar - Which Wins?"]
    elif any(x in low for x in ["tank","fighter","army","military"]):
        emoji="🎖️"
        clean_titles=[f"{base} - Army Machine Inside Power", f"{base} Military Review - Secret Feature", f"How {base} Protects America - Real Test"]
    else:
        emoji="🔥"
        clean_titles=[f"{base} Honest Review After 7 Days - Worth It?", f"Why {base} Is Trending Worldwide Today", f"{base} Hidden Feature 99% Dont Know"]

    title_a = random.choice(clean_titles)
    title_b = f"{emoji} {random.choice(clean_titles)}"
    final_title = title_b if len(title_b) < 70 else title_a
    final_title = final_title[:90]

    with open("ab_titles_long.txt","w") as f:
        f.write(f"A: {title_a}\nB: {title_b}\nBest upload: 2 PM EST\n")

    kw_str = ", ".join(keywords[:5]) if keywords else "product review, big machine, army machine, world trending"
    month_now = datetime.datetime.now().month
    holiday_text = ""
    if month_now == 11: holiday_text = "Black Friday is coming, "
    elif month_now == 9: holiday_text = "Apple Event just happened, "

    chapters = "\n".join([f"{i}:00 - {HOOK_EMOTIONS[i]['hook']}" for i in range(10)])

    desc = f"""Best {topic} honest review 2026 - worldwide trending explained.
How {topic} works - full breakdown - products + big machine + army machine.

{script_text[:700]}...

🚨 THIS WILL CHANGE HOW YOU SEE {topic.upper()} - Human curated worldwide - products + big machine + army machine knowledge

In this long video (10 chapters):
{chr(10).join([f"✅ Chapter {i+1}: {HOOK_EMOTIONS[i]['hook']} - {HOOK_EMOTIONS[i]['type']}" for i in range(10)])}

TIMESTAMPS (YouTube SEO + Retention - fast paced 2.5s visuals):
00:00 - Intro - Stop scrolling! Shocking
{chapters}
09:30 - Final - Which would you buy? A or B?

Why watch?
- Based on 2026 world research + Reddit MachinePorn + TankPorn + technology + TechCrunch + Verge
- No AI slop - In my opinion, I tested 7 days, real story Texas to Dubai, NYC to LA
- No fluff, only practical - Screen recording style, emotional connection

🔍 Related: {kw_str}

This is evergreen worldwide guide for {topic} - human curated.

If you love products review, big machine knowledge, army machine review, world tech trending, this channel TECH4USA is for you.

Subscribe: {CHANNEL_LINK}
Watch More: {OLD_VIDEOS}

#Tech #ProductReview #BigMachine #ArmyMachine #WorldTrending #USA2026 #{topic.replace(' ','')} #HumanCurated
"""

    def clean_tag(t):
        t = re.sub(r'[<>"\'#]', '', t)
        t = re.sub(r'[^\w\s]', ' ', t)
        t = ' '.join(t.split())
        t = t.strip()[:25]
        return t.lower()

    raw_tags=[topic, f"{topic} review", f"{topic} world", "product review", "big machine", "army machine", "world trending", "honest review", "how it works", "usa tech 2026", "human curated"]
    for kw in keywords[:8]:
        raw_tags.append(kw)
    cleaned=[]; seen=set(); total_len=0
    for t in raw_tags:
        ct=clean_tag(t)
        if len(ct)<2: continue
        if ct in seen: continue
        if total_len + len(ct) + 1 > 400: break
        cleaned.append(ct); seen.add(ct); total_len+=len(ct)+1
        if len(cleaned)>=15: break
    if len(cleaned)<3:
        cleaned=["product review","big machine","army machine","world trending","tech review 2026"]
    tags=cleaned
    print(f"✅ LONG TAGS ({len(tags)}): {tags[:5]} - SAFE")
    print(f"✅ SEO TITLE: {final_title}")
    return final_title, desc, tags, title_a, title_b

def get_long_clips_world_fast(topic, total_duration):
    """
    Long video - same edit as shorts - fast paced - har 2.5-3 sec change
    But for API limit, 20 clips * ~29 sec each with zoom = fast feel
    Different angles for products + big machine + army
    """
    clips=[]
    low = topic.lower()
    if any(x in low for x in ["excavator","crane","bulldozer","big machine","construction","jcb","caterpillar"]):
        queries=[
            f"{topic} big machine closeup side angle 4k",
            f"{topic} excavator action working construction",
            f"{topic} heavy machine operator cabin",
            f"american construction site {topic} power",
            f"{topic} machine hydraulic detail",
            f"{topic} big machine top view",
            f"{topic} machine rotating 360",
            f"caterpillar {topic} lifting",
            f"construction big machine b-roll",
            f"{topic} engine roar"
        ]
    elif any(x in low for x in ["tank","fighter","army","military","abrams","f35"]):
        queries=[
            f"{topic} army tank closeup side angle",
            f"{topic} military machine action",
            f"{topic} fighter jet cockpit",
            f"us army {topic} powerful",
            f"{topic} tank firing",
            f"{topic} military drone flying",
            f"{topic} army vehicle top view",
            f"{topic} tank tracks detail",
            f"military {topic} b-roll 4k",
            f"{topic} army base"
        ]
    else:
        queries=[
            f"{topic} product review closeup side angle",
            f"{topic} gadget in hand",
            f"{topic} product rotating 360",
            f"american hands {topic} unboxing",
            f"{topic} product top view flat lay",
            f"{topic} screen display 45 degree",
            f"{topic} product features macro",
            f"{topic} gadget b-roll",
            f"{topic} technology 4k",
            f"{topic} product lifestyle"
        ]
    
    random.shuffle(queries)
    # For long 580 sec, 20 clips = 29 sec each - with fast zoom pattern interrupt = fast feel
    # Plus first 30 sec we use 12 clips of 2.5 sec for hook (fastest)
    num_clips = 20
    per_clip = total_duration / num_clips
    
    for i in range(num_clips):
        try:
            q=queries[i % len(queries)]
            url=f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=15&orientation=landscape&size=medium"
            headers={"Authorization": PEXELS_API_KEY} if PEXELS_API_KEY else {}
            resp=requests.get(url, headers=headers, timeout=15)
            if resp.status_code!=200: continue
            vids=resp.json().get('videos',[])
            if not vids: continue
            video=random.choice(vids[:5])
            files=sorted(video['video_files'], key=lambda x: x['width'], reverse=True)
            best=next((f for f in files if f['width']>=1280), files[0])
            path=f"clip_long_{i}.mp4"
            r=requests.get(best['link'], stream=True, timeout=60)
            with open(path,"wb") as out:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    out.write(chunk)
            clip=VideoFileClip(path)
            clip=safe_without_audio(clip)
            if clip.duration > per_clip+1:
                start=random.uniform(0, max(0, clip.duration-per_clip-0.5))
                try: clip=clip.subclip(start, start+per_clip)
                except: clip=clip.with_end(per_clip)
            clip=safe_set_duration(clip, per_clip)
            try: clip=clip.resize(width=1920)
            except:
                try: clip=clip.resized(width=1920)
                except: pass
            # Fast zoom - pattern interrupt every 3-5 sec for long - same as shorts style
            try:
                zoom = 1.0 + (0.12 if i%3==0 else 0.06)
                clip=clip.resize(lambda t: zoom + 0.04 * (t / max(per_clip,1)))
            except: pass
            clips.append(clip)
            print(f"LONG CLIP {i+1}/{num_clips}: {q} - {per_clip:.1f}s - fast zoom")
        except Exception as e:
            print(f"Long clip {i} skip: {e}")
            continue
    if not clips:
        fallback = ColorClip(size=(1920,1080), color=(10,10,30))
        fallback = safe_set_duration(fallback, total_duration)
        return fallback
    final_bg=concatenate_videoclips(clips, method="compose")
    final_bg=safe_set_duration(final_bg, total_duration)
    print(f"✅ Long fast bg ready - {len(clips)} clips - same edit as shorts - fast paced")
    return final_bg

def create_long_overlays_same_as_shorts(duration):
    """Same edit as shorts - bottom clean + world trending badge + fast"""
    overlays=[]
    per_hook=duration / 10
    for i, he in enumerate(HOOK_EMOTIONS):
        img=Image.new('RGBA',(1920,1080),(0,0,0,0))
        draw=ImageDraw.Draw(img, 'RGBA')
        try: font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
        except: font_big=ImageFont.load_default()
        try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except: font_small=ImageFont.load_default()
        try: font_badge=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        except: font_badge=ImageFont.load_default()

        draw.rounded_rectangle((20,20,650,70), radius=20, fill=(0,200,255,240))
        draw.text((35,28), "WORLD TRENDING • HUMAN CURATED", fill=(0,0,0), font=font_badge)
        draw.rounded_rectangle((20,80,750,120), radius=12, fill=(255,255,255,200))
        draw.text((30,88), f"Source: World Trends + Reddit MachinePorn TankPorn", fill=(50,50,50), font=font_small)
        draw.rounded_rectangle((30,140,600,200), radius=20, fill=he['color']+(220,))
        draw.text((45,150), f"{he['emotion']} • {he['type']}", fill="white", font=font_small)
        draw.rectangle((0,750,1920,1080), fill=(0,0,0,200))
        y=770
        for line in textwrap.wrap(he['hook'].upper(), width=40):
            draw.text((40, y), line, fill="white", font=font_big, stroke_width=5, stroke_fill="black")
            y+=60
            if y>900: break
        if i >= 5:
            draw.rounded_rectangle((40,950,800,1000), radius=20, fill=(255,235,0,255))
            draw.text((60,960), "Which would YOU buy? A or B? Comment! 👇", fill=(0,0,0), font=font_small)
        if i == 7:
            draw.text((1700,1000), "Did you see that? 👀", fill=(255,255,255,90), font=font_small)
        clip=ImageClip(np.array(img))
        clip=safe_set_duration(clip, per_hook)
        try: clip=clip.set_start(i*per_hook)
        except: clip=clip.with_start(i*per_hook)
        overlays.append(clip)
    return overlays

# ========== MAIN LONG FINAL ==========
evergreen_topic = get_world_trending_long()
full_script = generate_long_emotional_script(evergreen_topic)
print(f"SCRIPT: {len(full_script.split())} words - {len(full_script.split())//150} min")

# Piper TTS Long - 3 parts
audio_files = text_to_speech_piper_long(full_script, "voice_long")
if not audio_files:
    print("❌ No audio - exiting")
    exit(1)

audio_clips=[]
for vp in audio_files:
    if os.path.exists(vp) and os.path.getsize(vp)>1000:
        try:
            audio_clips.append(AudioFileClip(vp))
        except: pass

if not audio_clips:
    print("❌ No audio clips - exit")
    exit(1)

final_audio=concatenate_audioclips(audio_clips)
try: final_audio=final_audio.volumex(1.15)
except: pass

# Music 12% - same as shorts - fast paced - crash proof
bg_music_path = None
try:
    bg_music_path=fetch_music_for_video(evergreen_topic)
except Exception as music_err:
    print(f"⚠️ MUSIC FETCH FAILED - voice only: {music_err}")
    bg_music_path = None

if bg_music_path and os.path.exists(bg_music_path):
    try:
        bg_music=AudioFileClip(bg_music_path).subclip(0, final_audio.duration)
        bg_music=bg_music.volumex(0.12)
        try: bg_music=bg_music.audio_fadein(1).audio_fadeout(1)
        except: pass
        print(f"✅ MUSIC LONG 12% - {bg_music_path}")
        final_audio=CompositeAudioClip([final_audio, bg_music])
    except Exception as e:
        print(f"⚠️ MUSIC MIX FAILED: {e}")
else:
    print("No music - voice only - video still uploads")

max_d=580
if final_audio.duration > max_d:
    try: final_audio=final_audio.subclip(0, max_d)
    except: final_audio=final_audio.with_end(max_d)

print(f"Final Duration: {final_audio.duration} sec - {final_audio.duration/60:.1f} min")

W,H=1920,1080
bg_clip=get_long_clips_world_fast(evergreen_topic, final_audio.duration)
hook_overlays=create_long_overlays_same_as_shorts(final_audio.duration)

def create_progress_bars(duration):
    bars=[]
    try:
        top_bar=ColorClip(size=(1920,12), color=(255,0,0))
        top_bar=safe_set_duration(top_bar, duration)
        try: top_bar=top_bar.set_position(('center','top'))
        except: top_bar=top_bar.with_position(('center','top'))
        bars.append(top_bar)
        for i in range(10):
            seg = ColorClip(size=(192,8), color=(0,200,255) if i%2==0 else (255,235,0))
            seg=safe_set_duration(seg, duration)
            try:
                seg=seg.set_position((i*192, H-8))
                seg=seg.set_start(0)
            except:
                seg=seg.with_position((i*192, H-8))
            bars.append(seg)
    except Exception as e:
        print(f"Progress bar error: {e}")
    return bars

progress_bars=create_progress_bars(final_audio.duration)
final_title, description, tags, title_a, title_b = seo_optimize_long(evergreen_topic, full_script)
thumb=create_ctr_thumbnail(evergreen_topic)
seo_filename=re.sub(r'[^a-z0-9]+','-', evergreen_topic.lower()).strip('-')[:50]
seo_filename=f"{seo_filename}-world-2026-best.mp4"
print(f"✅ SEO FILE: {seo_filename}")

layers=[bg_clip, *hook_overlays, *progress_bars]
final=CompositeVideoClip(layers, size=(W,H))
final=safe_set_duration(final, final_audio.duration)
final=safe_set_audio(final, final_audio)
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)

print(f"🎉 LONG VIDEO FINAL DONE - Products + Big Machine + Army + World Trending + Same Edit as Shorts")
print(f"File: {seo_filename}, Title: {final_title}, Thumb: {thumb}")
print(f"A/B: A={title_a} | B={title_b}")

pinned_comment = f"Which would you buy? A) {evergreen_topic.split()[0]} B) Other? Comment! In my opinion, {evergreen_topic.split()[0]} wins. World trending + Big Machine + Army knowledge. I reply every comment!"
with open("pinned_comment.txt","w") as f:
    f.write(pinned_comment)
community_poll = f"Poll: Best big machine? 1) Excavator 2) Crane 3) Tank? Vote!"
with open("community_poll.txt","w") as f:
    f.write(community_poll)

from upload_youtube import upload_video
try:
    upload_video(seo_filename, final_title, description, tags, thumbnail_path=thumb)
    print("✅ UPLOAD SUCCESS - Long world trending")
except Exception as e:
    print(f"⚠️ Upload failed but file ready: {e}")
    try:
        upload_video(seo_filename, final_title, description, tags)
    except Exception as e2:
        print(f"Second try failed: {e2}")
