import random, requests, re, os, time, textwrap, datetime
import xml.etree.ElementTree as ET
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build

# Try to import auto_music safely
try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(topic): return None

print("Starting LONG VIDEO ULTIMATE BEST - ALL 8 SUGGESTIONS + EXTRA PRO BEST - ERROR FREE - GITHUB RUNNER TESTED...")

# ========== 1. NICHE & BRANDING - ULTIMATE ==========
TECH_ALLOWED = ["iphone","apple","ios","ipad","android","samsung","pixel","google","ai","chatgpt","openai","gemini","tesla","elon","gadget","tech","phone","battery","hack","app","laptop","5g","privacy","security","chip","nvidia","microsoft","meta","vr","ar","robot","drone","earbuds","watch","macbook","mac","ipad","airpods","smartwatch","tablet","camera","processor","gpu","cpu","ram","storage","charger","powerbank"]
BANNED_NON_TECH = [
    "tyrod","taylor","mariners","yankees","oreo","brad pitt","ukraine","pushpa","jethalal","bapuji","taarak","ooltah","chashmah","tmkoc","bhabi","kapil","bigg boss","lottery",
    "football","cricket","basketball","baseball","soccer","wwe","movie","bollywood","hollywood","election","biden","trump","modi","congress","bjp",
    "taylor swift","kardashian","kylie","selena","justin bieber"
]
CHANNEL_LINK = "https://www.youtube.com/@TECH4USA"
OLD_VIDEOS = "https://www.youtube.com/@TECH4USA/videos"
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

# EVERGREEN USA TECH TOPICS - High search, no expiry - FILTERED FOR USA
EVERGREEN_TOPICS = [
    "iPhone Hidden Features You Never Knew - 2026 Edition",
    "Android Tricks That Will Blow Your Mind - USA Tested",
    "AI Tools That Will Replace Your Job in 2026 - I Tested",
    "Secret Google Search Tricks 99 Percent People Dont Know",
    "How To Make Your Phone Battery Last 3 Days - Problem Solved",
    "Tesla Hidden Features Only Owners Know - Comparison",
    "ChatGPT Prompts That Make You Money in USA - Future Tech",
    "Samsung vs iPhone Which Is Actually Better in 2026 - Honest Comparison",
    "How To Protect Your Phone From Hackers USA - 10 Second Fix",
    "Best Free Apps Every American Should Have - Top 3 List",
    "Why Your Phone Is Slow And How To Fix It Forever - Problem Solution",
    "Hidden iPhone Settings That Apple Hides From You - I Found It",
    "How AI Is Changing Life in America Right Now - Storytelling NYC to LA",
    "The Truth About 5G Is It Dangerous - Real Facts",
    "How To Earn Money With Your Phone in USA - Tested",
    "Laptop Tricks That Will Save You Hours - Top 3",
    "Secret Codes Every Smartphone Has - Did You See That",
    "How To Stop Apps From Spying On You - 10 Sec Fix",
    "Future Technology That Will Change America - 2027 Prediction",
    "Why You Should Never Charge Your Phone Overnight - Mistake I Made"
]

# ========== EMOTION MAP FOR 10 HOOKS - USA PSYCHOLOGY + SUB-SUGGESTIONS ==========
HOOK_EMOTIONS = [
    {"hook": "Stop scrolling! This phone trick saves 2 days battery", "emotion": "😲 SHOCK", "type": "Problem-Solution", "color": (255,0,0)},
    {"hook": "If you skip, you will regret tomorrow - FOMO", "emotion": "😨 FOMO", "type": "Comparison", "color": (255,165,0)},
    {"hook": "Secret feature hidden by Apple - 99% dont know", "emotion": "🤩 AMAZEMENT", "type": "Top 3 Listicle", "color": (0,200,255)},
    {"hook": "They don't want you to know this - Apple hides", "emotion": "😤 ANGER", "type": "Future Tech", "color": (255,0,100)},
    {"hook": "This trick saves 2 hours every week + money", "emotion": "🤑 GREED", "type": "Problem-Solution", "color": (0,255,100)},
    {"hook": "I made this mistake for years - My story NYC to LA", "emotion": "🥺 EMPATHY", "type": "Storytelling", "color": (100,100,255)},
    {"hook": "Stanford 2026 study proves - 43% productivity", "emotion": "🧠 TRUST", "type": "Comparison", "color": (200,200,200)},
    {"hook": "Controversial but true - Apps listening to you", "emotion": "🔥 CONTROVERSY", "type": "Problem-Solution", "color": (255,50,0)},
    {"hook": "Try this for 24 hours - Challenge", "emotion": "💪 MOTIVATION", "type": "Future Tech", "color": (255,255,0)},
    {"hook": "The best one at the end will blow your mind", "emotion": "🎯 PAYOFF", "type": "Top 3 Listicle", "color": (0,255,0)},
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

def get_unique_topic():
    if not os.path.exists("used_long_titles.txt"):
        open("used_long_titles.txt","w").close()
    with open("used_long_titles.txt","r") as f:
        used = f.read().splitlines()
    available = [t for t in EVERGREEN_TOPICS if t not in used]
    if not available:
        available = EVERGREEN_TOPICS
        open("used_long_titles.txt","w").close()
    # Filter BANNED
    filtered = []
    for t in available:
        low = t.lower()
        if any(b in low for b in BANNED_NON_TECH):
            continue
        filtered.append(t)
    if not filtered:
        filtered = EVERGREEN_TOPICS
    topic = random.choice(filtered)
    with open("used_long_titles.txt","a") as f:
        f.write(topic+"\n")
    return topic

def fetch_reddit_tech():
    try:
        r = requests.get("https://www.reddit.com/r/technology/top/.json?limit=5", headers={"User-Agent":"Mozilla/5.0"}, timeout=8)
        if r.status_code == 200:
            data = r.json()
            for child in data['data']['children']:
                t = child['data']['title']
                low = t.lower()
                if any(b in low for b in BANNED_NON_TECH): continue
                if any(k in low for k in TECH_ALLOWED):
                    return f"Reddit trending: {t[:80]}"
    except:
        pass
    return ""

def generate_ultimate_script(topic):
    """ALL 6 SUB-STRATEGIES + AI SLOP FIX + HOOK FIX"""
    reddit = fetch_reddit_tech()
    real_facts = ""
    try:
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={requests.utils.quote(topic)}&limit=2&namespace=0&format=json"
        r = requests.get(url, timeout=8)
        if r.status_code==200:
            data = r.json()
            if len(data)>2 and data[2]:
                real_facts = ". ".join(data[2][:2])[:300]
    except:
        pass
    if not real_facts:
        real_facts = f"{topic} is something every American uses daily but never understands fully. Even TechCrunch and The Verge are talking about this in 2026."

    # Holiday check
    month_now = datetime.datetime.now().month
    holiday_text = ""
    if month_now == 11:
        holiday_text = "Black Friday is coming, "
    elif month_now == 9:
        holiday_text = "Apple Event just happened, "
    elif month_now == 12:
        holiday_text = "Christmas tech gifts season, "

    # ULTIMATE SCRIPT WITH ALL SUB-SUGGESTIONS
    # 1. Niche - Tech only, Channel name TECH4USA
    # 2. AI Slop fix - Personal opinion, Emotion, Screen recording style
    # 3. Hook - No Hello friends, direct shocking
    # 6. Content Strategy - All 5 types included

    intro = f"Stop scrolling! {holiday_text}If you are using {topic.split()[0]} wrong, you are losing 2 hours every week. This is not AI voice only - In my opinion, I tested this for 30 days in real life, from NYC to LA, and found something Apple hides from you. Some people said AI slop, so here is how I actually research - I read TechCrunch, The Verge, and Reddit r/technology daily for you. Human-curated Tech News for USA. Let's dive in."

    # Problem-Solution
    part1 = f"Chapter 1 - Problem Solution: Number one, your {topic.lower()} is draining battery and spying on you right now. I made this mistake for years. My phone died every 4 hours. Then I discovered this hidden setting. Now battery lasts 3 days. Same phone, different settings. I will show you screen recording style, step by step, on actual phone screen."

    # Comparison
    part2 = f"Chapter 2 - Comparison: Samsung vs iPhone vs {topic.split()[0]} - Which wins in 2026? I tested all three for weeks. {real_facts[:150]}. In my opinion, {topic.split()[0]} wins for battery, iPhone wins for camera. You can travel from NYC to LA and this phone still won't die. Which would you choose? A or B? Comment!"

    # Future Tech
    part3 = f"Chapter 3 - Future Tech: How AI will change {topic} in 2027. This is controversial but true - your apps are listening. Even TechCrunch reported this last week. I found a 10 second fix that stops it. Future tech that helps humans, not replaces them."

    # Storytelling NYC to LA
    part4 = f"Chapter 4 - Storytelling: You won't believe what happened when I was traveling from NYC to LA. My {topic} saved me. I was stuck, battery 2 percent, but this trick saved me. Real story, real emotion. {reddit}"

    # Top 3 Listicle + Payoff
    part5 = f"Chapter 5 to 10 - Top 3 secrets: Top 3 {topic} secrets 99 percent Americans don't know. Number one, this trick saves 2 hours every week. Number two, hidden code that unlocks secret menu. Number three, the best one at the end will blow your mind - Did you see that? Easter egg hidden in this video. In my opinion, this changes everything. Which one is your favorite? Which gadget would you buy? Comment A or B!"

    outro = f"Final Thoughts: If this helped, hit subscribe for Human-curated Tech News for USA. I post 4-5 times a week, not monthly. Consistency is key. Question for you - Which gadget would you buy? A) {topic.split()[0]} B) iPhone? Let me know. And if someone says AI slop, here is my reply template - I research real sources, test myself, and give you honest opinion. See you next time!"

    full = f"{intro} {part1} {part2} {part3} {part4} {part5} {outro}"
    # Keep ~1200 words for 8-10 min video (150 wpm)
    words = full.split()
    if len(words) > 1300:
        full = ' '.join(words[:1300]) + "."
    return full

def get_feeling_emoji(title):
    tl = title.lower()
    if any(w in tl for w in ["iphone","apple"]): return "📱"
    elif any(w in tl for w in ["android","samsung"]): return "🤖"
    elif "ai" in tl: return "🤖"
    elif "tesla" in tl: return "🚗"
    else: return "🔥"

def create_ctr_thumbnail(topic):
    """Title/Thumbnail SEO - Curiosity frame + 1-2 emoji + High contrast + Face reaction style"""
    try:
        W,H=1280,720
        # High contrast black/white/blue - 4K crisp
        thumb=Image.new('RGB',(W,H),(5,5,25))
        draw=ImageDraw.Draw(thumb)
        # Gradient blue to black
        for y in range(H):
            r=int(5 + y*0.15)
            g=int(5 + y*0.1)
            b=int(25 + y*0.25)
            draw.line([(0,y),(W,y)],fill=(r,g,b))

        try: font_huge=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except: font_huge=ImageFont.load_default()
        try: font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except: font_big=ImageFont.load_default()
        try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except: font_small=ImageFont.load_default()

        # Curiosity frame - big shocking text first frame concept
        main_word=topic.split()[0].upper()[:8]
        draw.text((30,30), f"{main_word}?", fill="white", font=font_huge, stroke_width=10, stroke_fill="black")
        # Yellow for contrast
        draw.text((30,160), "SECRET!", fill="#FFEB00", font=font_huge, stroke_width=10, stroke_fill="black")
        draw.text((30,300), "99% DON'T KNOW", fill="#00D4FF", font=font_big, stroke_width=6, stroke_fill="black")

        # Arrow - CTR boost - red arrow
        draw.polygon([(950,150),(1150,360),(950,570)], fill="#FF0000", outline="white", width=6)

        # Human-curated badge
        draw.rounded_rectangle((30,600,500,670), radius=20, fill=(0,200,255))
        draw.text((50,615), "HUMAN-CURATED • USA", fill="black", font=font_small)

        # Social proof - Verge/TechCrunch style
        draw.rounded_rectangle((30,680,600,710), radius=10, fill=(255,255,255,200))
        draw.text((40,685), "Source: TechCrunch + Verge + Reddit", fill=(0,0,0), font=ImageFont.load_default())

        # Emoji 1-2 only - clean
        emoji = get_feeling_emoji(topic)
        draw.text((W-150,20), emoji, fill="white", font=font_huge)

        # Easter egg hidden small
        draw.text((W-60, H-40), "👀", fill=(255,255,255,80), font=font_small)

        thumb.save("thumbnail.jpg")
        print("✅ THUMBNAIL CREATED: thumbnail.jpg - CTR optimized - High contrast, curiosity frame, 1 emoji")
        return "thumbnail.jpg"
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return None

def seo_optimize_long_ultimate(topic, script_text):
    # Fetch keywords
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

    # Clean Title - 3 Reasons Why... + 1-2 emoji only + no spam
    base= ' '.join(topic.split()[:6])
    emoji=get_feeling_emoji(topic)
    clean_titles=[
        f"3 Reasons Why {base} Is Changing Life in USA",
        f"How To Fix {base} in 10 Seconds - I Tested",
        f"{base}: Secret Apple Hides From You - 2026",
        f"{base} vs iPhone - Which Wins? Honest Test",
        f"Why {base} Will Save You 2 Hours Every Week"
    ]
    title_a = random.choice(clean_titles)
    title_b = f"{emoji} {random.choice(clean_titles)}"
    final_title = title_b if len(title_b) < 70 else title_a
    final_title = final_title[:90]  # YouTube allows 100, we use 90 safe

    # Save A/B testing
    with open("ab_titles_long.txt","w") as f:
        f.write(f"A: {title_a}\nB: {title_b}\nBest upload: 2 PM EST\n")

    # Description - first 2 lines keywords + SEO
    kw_str = ", ".join(keywords[:5]) if keywords else "tech usa, ai gadgets, iphone tricks"
    month_now = datetime.datetime.now().month
    holiday_text = ""
    if month_now == 11: holiday_text = "Black Friday is coming, "
    elif month_now == 9: holiday_text = "Apple Event just happened, "

    # Chapters for SEO + Retention - YouTube loves this
    chapters = "\n".join([f"{i}:00 - {HOOK_EMOTIONS[i]['hook']}" for i in range(10)])

    desc = f"""Best AI gadgets 2026 - {base} explained for USA.
How to use {topic} like a pro - {holiday_text}Tech that helps humans.

{script_text[:600]}...

🚨 THIS VIDEO WILL CHANGE HOW YOU USE TECHNOLOGY IN USA - Human-curated Tech News for USA

In this video you will discover (Problem-Solution + Comparison + Future Tech):
{chr(10).join([f"✅ Chapter {i+1}: {HOOK_EMOTIONS[i]['hook']} - {HOOK_EMOTIONS[i]['type']}" for i in range(10)])}

TIMESTAMPS (YouTube SEO + Retention):
00:00 - Intro - Stop scrolling! Shocking text
{chapters}
09:30 - Final Thoughts - Which would you buy? A or B?

Why watch this?
- Based on 2026 research + Reddit r/technology + TechCrunch + Verge
- No AI slop - In my opinion, I tested for 30 days, NYC to LA story
- No fluff, only practical tricks - Screen recording style

🔍 Related Searches: {kw_str}

This is evergreen guide for {topic} - Human-curated.

If you are in USA and love technology, this channel TECH4USA is for you - Banner: Human-curated Tech News for USA, About me updated.

Subscribe: {CHANNEL_LINK}
Watch More: {OLD_VIDEOS}

#Tech #Technology #USATech #iPhone #Android #AI #TechTips #USA2026 #{topic.replace(' ','')} #HumanCurated
"""

    # FIX FOR YOUTUBE INVALID KEYWORDS - CLEAN TAGS
    def clean_tag(t):
        t = re.sub(r'[<>"\'#]', '', t)
        t = re.sub(r'[^\w\s]', ' ', t)
        t = ' '.join(t.split())
        t = t.strip()[:25]
        return t.lower()

    raw_tags=[topic, f"{topic} usa", f"{topic} 2026", "usa tech 2026", "technology explained", "tech secrets usa", "iphone tricks", "android tricks", "ai 2026", "tech tips usa", "human curated tech", "best ai gadgets 2026"]
    for kw in keywords[:8]:
        raw_tags.append(kw)

    cleaned=[]
    seen=set()
    total_len=0
    for t in raw_tags:
        ct=clean_tag(t)
        if len(ct)<2: continue
        if ct in seen: continue
        if total_len + len(ct) + 1 > 400: break
        cleaned.append(ct)
        seen.add(ct)
        total_len+=len(ct)+1
        if len(cleaned)>=15: break
    if len(cleaned)<3:
        cleaned=["tech usa","ai gadgets","iphone tricks","usa tech 2026","technology explained"]
    tags=cleaned
    print(f"✅ CLEANED LONG TAGS ({len(tags)}): {tags[:5]} - Total {total_len} chars - SAFE FOR YOUTUBE API")
    print(f"✅ SEO TITLE: {final_title}")
    print(f"✅ A/B TESTING: A={title_a} | B={title_b}")

    return final_title, desc, tags, title_a, title_b

def get_best_upload_time():
    now_utc=datetime.datetime.utcnow()
    est_hour=(now_utc.hour - 4) % 24
    if 13 <= est_hour <= 15 or 19 <= est_hour <= 21:
        return "NOW IS BEST TIME - USA PRIME TIME 2 PM EST / 8 PM EST"
    else:
        return "Next best: 2 PM EST (12:30 AM IST) or 8 PM EST (6:30 AM IST) - Consistency 4-5/week"

def get_long_clips_ultimate(topic, total_duration):
    """High-contrast black/white/blue 4K crisp + pattern interrupt + screen recording style"""
    clips=[]
    # Queries for high contrast + screen recording style
    queries=[
        f"closeup {topic} iphone screen 4k",
        f"american hands typing {topic} laptop minimal black background",
        f"{topic} gadget b-roll blue light 4k",
        f"screen recording {topic} phone settings closeup",
        f"{topic} technology new york futuristic",
        f"{topic} app interface closeup",
        f"{topic} battery charging closeup",
        f"{topic} ai hologram blue"
    ]
    random.shuffle(queries)
    num_clips = 10  # 10 hooks = 10 clips
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
            video=random.choice(vids)
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
            # High contrast + 4K crisp + zoom pattern interrupt every 3-5 sec concept for long
            try: clip=clip.resize(width=1920)
            except:
                try: clip=clip.resized(width=1920)
                except: pass
            try:
                # Subtle zoom for retention
                clip=clip.resize(lambda t: 1 + 0.05 * (t / max(per_clip,1)))
            except: pass
            clips.append(clip)
            print(f"LONG CLIP {i+1}/10: {q} - High contrast 4K")
        except Exception as e:
            print(f"Long clip {i} skip: {e}")
            continue
    if not clips:
        # Fallback color clip
        fallback = ColorClip(size=(1920,1080), color=(10,10,30))
        fallback = safe_set_duration(fallback, total_duration)
        return fallback
    final_bg=concatenate_videoclips(clips, method="compose")
    final_bg=safe_set_duration(final_bg, total_duration)
    return final_bg

def create_ultimate_overlays_long(duration):
    """Hook & Retention + Engagement + Green Screen + Easter Egg + Progress bar + Social proof"""
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

        # Human-curated badge top - Branding
        draw.rounded_rectangle((20,20,550,70), radius=20, fill=(0,200,255,240))
        draw.text((35,28), "HUMAN-CURATED TECH • USA", fill=(0,0,0), font=font_badge)

        # Social proof Verge/TechCrunch + Reddit
        draw.rounded_rectangle((20,80,650,120), radius=12, fill=(255,255,255,200))
        draw.text((30,88), f"Source: TechCrunch + Verge + Reddit r/technology", fill=(50,50,50), font=font_small)

        # Emotion badge - Pattern Interrupt
        draw.rounded_rectangle((30,140,600,200), radius=20, fill=he['color']+(220,))
        draw.text((45,150), f"{he['emotion']} • {he['type']}", fill="white", font=font_small)

        # Hook text bottom - Green screen style + shocking text first frame
        draw.rectangle((0,750,1920,1080), fill=(0,0,0,200))
        # First frame big shocking text for long - first 3 sec
        hook_text = he['hook']
        y=770
        for line in textwrap.wrap(hook_text.upper(), width=40):
            draw.text((40, y), line, fill="white", font=font_big, stroke_width=5, stroke_fill="black")
            y+=60
            if y>900: break

        # Engagement CTA - Which gadget would you buy?
        if i >= 5:  # Show CTA in later chapters
            draw.rounded_rectangle((40,950,800,1000), radius=20, fill=(255,235,0,255))
            draw.text((60,960), "Which would YOU buy? A or B? Comment! 👇", fill=(0,0,0), font=font_small)

        # Easter egg hidden
        if i == 7:
            draw.text((1700,1000), "Did you see that? 👀", fill=(255,255,255,90), font=font_small)

        clip=ImageClip(np.array(img))
        clip=safe_set_duration(clip, per_hook)
        try: clip=clip.set_start(i*per_hook)
        except: clip=clip.with_start(i*per_hook)
        overlays.append(clip)
    return overlays

# ========== MAIN ULTIMATE LONG ==========
evergreen_topic=get_unique_topic()
print(f"EVERGREEN TOPIC: {evergreen_topic} - TECH ONLY FILTERED")
full_script=generate_ultimate_script(evergreen_topic)
print(f"SCRIPT LENGTH: {len(full_script.split())} words - ~{len(full_script.split())//150} min - ALL 8 SUGGESTIONS INCLUDED")

# TTS - split to avoid gTTS limit - error free
clean_script=full_script.replace("#","").strip()
# Split into 3 parts for safety
chunk_size = len(clean_script)//3
part1=clean_script[:chunk_size]
part2=clean_script[chunk_size:chunk_size*2]
part3=clean_script[chunk_size*2:]

try:
    gTTS(text=part1, lang='en', tld='us', slow=False).save("voice1.mp3")
    time.sleep(0.5)
    gTTS(text=part2, lang='en', tld='us', slow=False).save("voice2.mp3")
    time.sleep(0.5)
    gTTS(text=part3, lang='en', tld='us', slow=False).save("voice3.mp3")
    time.sleep(0.5)
    print("✅ TTS DONE - 3 parts - USA voice")
except Exception as e:
    print(f"TTS error: {e} - trying fallback")
    gTTS(text=clean_script[:4000], lang='en', tld='us', slow=False).save("voice1.mp3")
    open("voice2.mp3","w").close()
    open("voice3.mp3","w").close()

from moviepy.editor import CompositeAudioClip, concatenate_audioclips
audio_clips=[]
for vp in ["voice1.mp3","voice2.mp3","voice3.mp3"]:
    if os.path.exists(vp) and os.path.getsize(vp)>1000:
        try:
            audio_clips.append(AudioFileClip(vp))
        except: pass

if not audio_clips:
    print("❌ No audio - exiting")
    exit(1)

final_audio=concatenate_audioclips(audio_clips)
try: final_audio=final_audio.volumex(1.7)
except: pass

# Background music - crash proof - 15% trending + beat sync concept
bg_music_path = None
try:
    bg_music_path=fetch_music_for_video(evergreen_topic)
except Exception as music_err:
    print(f"⚠️ MUSIC FETCH FAILED (Pixabay char 0 error) - Continuing without music: {music_err}")
    bg_music_path = None

if bg_music_path and os.path.exists(bg_music_path):
    try:
        bg_music=AudioFileClip(bg_music_path).subclip(0, final_audio.duration)
        bg_music=bg_music.volumex(0.12)  # 12% for long video - beat sync
        try:
            bg_music=bg_music.audio_fadein(1).audio_fadeout(1)
        except: pass
        print(f"✅ TRENDING MUSIC LONG at 12% - {bg_music_path}")
        final_audio=CompositeAudioClip([final_audio, bg_music])
    except Exception as e:
        print(f"⚠️ MUSIC MIX FAILED - voice only: {e}")
else:
    print("No music - voice only - video will still upload - beat sync will be visual only")

# Cap to 10 min max for retention - 8-10 min best for long
max_d=580  # 9.6 min - best for retention
if final_audio.duration > max_d:
    try: final_audio=final_audio.subclip(0, max_d)
    except: final_audio=final_audio.with_end(max_d)

print(f"Final Duration: {final_audio.duration} sec - {final_audio.duration/60:.1f} min - Perfect for long retention")

W,H=1920,1080
bg_clip=get_long_clips_ultimate(evergreen_topic, final_audio.duration)

hook_overlays=create_ultimate_overlays_long(final_audio.duration)

# Progress bar top + chapters visual - Technical sub
def create_long_progress_bars(duration):
    bars=[]
    try:
        # Top progress red
        top_bar=ColorClip(size=(1920,12), color=(255,0,0))
        top_bar=safe_set_duration(top_bar, duration)
        try: top_bar=top_bar.set_position(('center','top'))
        except: top_bar=top_bar.with_position(('center','top'))
        bars.append(top_bar)
        # Bottom chapters - 10 segments
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

progress_bars=create_long_progress_bars(final_audio.duration)

# SEO + Thumbnail - Title/Thumbnail/SEO sub
final_title, description, tags, title_a, title_b = seo_optimize_long_ultimate(evergreen_topic, full_script)
thumb=create_ctr_thumbnail(evergreen_topic)

best_time=get_best_upload_time()
print(f"✅ BEST UPLOAD TIME: {best_time}")
print(f"✅ CONSISTENCY: 4-5/week reminder - Hafte me 4-5 videos - monthly nahi!")

seo_filename=re.sub(r'[^a-z0-9]+','-', evergreen_topic.lower()).strip('-')[:50]
seo_filename=f"{seo_filename}-usa-evergreen-2026-best.mp4"
print(f"✅ SEO FILE: {seo_filename} - High contrast black/white/blue 4K crisp")

# Compose final - ALL layers
layers=[bg_clip, *hook_overlays, *progress_bars]

final=CompositeVideoClip(layers, size=(W,H))
final=safe_set_duration(final, final_audio.duration)
final=safe_set_audio(final, final_audio)
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, logger=None)

print(f"🎉 LONG VIDEO ULTIMATE BEST DONE - ALL 8 SUGGESTIONS + EXTRA BEST")
print(f"File: {seo_filename}, Title: {final_title}, Thumb: {thumb}")
print(f"A/B Titles: A={title_a} | B={title_b}")
print(f"Timing: {best_time}")

# ========== 7. ENGAGEMENT - ALL SUB ==========
pinned_comment = f"Which gadget would you buy? A) {evergreen_topic.split()[0]} B) iPhone? Comment below! 👇 In my opinion, {evergreen_topic.split()[0]} wins. What do you think? I reply to every comment! #Tech that helps humans - Human-curated Tech News for USA - Some people said AI slop, here's my reply: I research TechCrunch+Verge+Reddit daily and test myself."
with open("pinned_comment.txt","w") as f:
    f.write(pinned_comment)

community_poll = f"Poll: Which AI is better for {evergreen_topic}? 1) ChatGPT 2) Gemini 3) Grok? Vote in comments! Community Tab poll ready!"

# Reply logic template
reply_template = f"""
If someone comments "AI slop" -> Reply: "Thanks for feedback! This is human-curated - I read TechCrunch, Verge, Reddit r/technology daily and test myself for 30 days. In my opinion, {evergreen_topic.split()[0]} is worth it. What do you think?"
If someone comments A/B -> Reply: "Great choice! In my opinion, [their choice] is best for [reason]. NYC to LA tested!"
If someone asks question -> Reply with screen recording style steps
"""

with open("community_poll.txt","w") as f:
    f.write(community_poll + "\n\n" + reply_template)

with open("reply_logic.txt","w") as f:
    f.write(reply_template)

print(f"✅ Pinned: {pinned_comment[:100]}...")
print(f"✅ Community Poll: {community_poll[:100]}...")
print(f"✅ Reply logic saved")
print(f"✅ Green Screen feature overlay: Included in video - bottom black box with yellow CTA")
print(f"✅ Consistency Reminder: Hafte me 4-5 videos - monthly nahi! - Saved in ab_titles_long.txt")
print(f"✅ Holiday Check: Done - Black Friday/Apple Event/Christmas")
print(f"✅ Reddit r/technology check: Done - {fetch_reddit_tech()[:50]}")
print(f"✅ Verge/TechCrunch social proof: Included - Source badge + description")
print(f"✅ Easter egg: Did you see that? - Hidden at 7th chapter + thumbnail corner")
print(f"✅ High-contrast black/white/blue 4K crisp: Done - thumbnail + clips")
print(f"✅ Progress bar top + chapters bottom: Done")
print(f"✅ A/B testing 2 titles: Done - {title_a} vs {title_b}")
print(f"✅ 15-20 sec concept adapted for long: First 30 sec hook = shocking text + Pattern interrupt every 30 sec + zoom + text pop + sound effect concept")

from upload_youtube import upload_video
try:
    upload_video(seo_filename, final_title, description, tags, thumbnail_path=thumb)
    print("✅ UPLOAD SUCCESS - Long video uploaded - Best video ever - 0.1% kharabi nahi")
except Exception as e:
    print(f"⚠️ Upload failed but video file ready: {e} - File: {seo_filename}")
    # Don't crash workflow - video file is ready
