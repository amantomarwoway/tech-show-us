import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET, gc
try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except:
    pass
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from googleapiclient.discovery import build
try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(topic): return None

QUALITY = os.environ.get("QUALITY","4K")
W, H = 2160, 3840
if QUALITY!= "4K":
    W, H = 1080, 1920
print(f"SHORTS BOT 4K - 4 TRENDING SOURCES - W={W}x{H}")

BANNED=["tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","tmkoc","bhabi","kapil","bigg boss","football","cricket","movie","election","biden","trump","modi"]
TECH_ALLOWED=["iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","excavator","crane","bulldozer","jcb","caterpillar","construction","tank","fighter","military","abrams","f35","drone","ai","tesla","robot","technology","tech"]
PEXELS_API_KEY=os.environ.get("PEXELS_API_KEY")

def safe_set_duration(clip,d):
    try: return clip.set_duration(d)
    except: return clip.with_duration(d)
def clean_for_tts(text):
    text=re.sub(r'http\S+|www\S+|\.com','',text,flags=re.IGNORECASE)
    text=re.sub(r'[^a-zA-Z0-9.,!?$% ]',' ',text)
    text=re.sub(r'\s+',' ',text).strip()
    return text
def get_unique_title(title):
    try:
        if not os.path.exists("used_titles.txt"): open("used_titles.txt","w").close()
        with open("used_titles.txt","r") as f: used=f.read().splitlines()
        if title in used: title=f"{title} Review {random.randint(1,99)}"
        with open("used_titles.txt","a") as f: f.write(title+"\n")
        return title[:90]
    except: return title[:90]
def text_to_speech_piper(text, output_path="voice.wav"):
    clean_text=clean_for_tts(text)
    try:
        model_path="en_US-lessac-medium.onnx"
        if os.path.exists(model_path):
            cmd=f'echo "{clean_text.replace(chr(34),"")}" | piper --model {model_path} --output_file {output_path} --length_scale 0.9 --sentence_silence 0.1'
            subprocess.run(cmd,shell=True,timeout=30,capture_output=True)
            if os.path.exists(output_path) and os.path.getsize(output_path)>1000:
                return output_path
    except: pass
    try:
        from gtts import gTTS
        gTTS(text=clean_text, lang='en', tld='us', slow=False).save("voice.mp3")
        return "voice.mp3"
    except: return None

# === 4 TRENDING SOURCES - SHORTS ===
def get_from_google_trends_pytrends():
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        trending = pytrends.trending_searches(pn='united_states')
        all_trends = trending[0].tolist()
        filtered=[t for t in all_trends if not any(b in t.lower() for b in BANNED) and len(t)<90]
        if filtered:
            print(f"✅ Shorts Source1 pytrends: {len(filtered)} found")
            return filtered
    except Exception as e:
        print(f"Shorts Source1 fail: {e}")
    return []

def get_from_youtube_trending():
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY") or os.environ.get("YOUTUBE_CLIENT_ID") or ""
        if not api_key:
            return []
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=US&videoCategoryId=28&maxResults=25&key={api_key}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            candidates=[item['snippet']['title'][:60] for item in data.get('items', []) if not any(b in item['snippet']['title'].lower() for b in BANNED)]
            if candidates:
                print(f"✅ Shorts Source2 YouTube: {len(candidates)} found")
                return candidates
    except Exception as e:
        print(f"Shorts Source2 fail: {e}")
    return []

def get_from_reddit():
    try:
        candidates=[]
        for sub in ["technology", "gadgets"]:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=25"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                for post in data['data']['children']:
                    title = post['data']['title']
                    if 10 < len(title) < 90 and not any(b in title.lower() for b in BANNED):
                        title = re.sub(r'[^a-zA-Z0-9 ]', ' ', title)
                        candidates.append(title[:60].strip())
        if candidates:
            print(f"✅ Shorts Source3 Reddit: {len(candidates)} found")
            return candidates
    except Exception as e:
        print(f"Shorts Source3 fail: {e}")
    return []

def get_from_google_news():
    try:
        urls = [
            "https://news.google.com/rss/search?q=technology+gadget+review&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=iphone+samsung+pixel+tech&hl=en-US&gl=US&ceid=US:en"
        ]
        candidates=[]
        for url in urls:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall('.//item/title')[:15]:
                    t = item.text.strip().split(' - ')[0]
                    if 10 < len(t) < 90 and not any(b in t.lower() for b in BANNED):
                        candidates.append(t[:60])
        if candidates:
            print(f"✅ Shorts Source4 Google News: {len(candidates)} found")
            return candidates
    except Exception as e:
        print(f"Shorts Source4 fail: {e}")
    return []

def get_trending_world_tech():
    print("🔍 SHORTS - Fetching from 4 TRENDING SOURCES...")
    all_candidates=[]
    all_candidates.extend(get_from_google_trends_pytrends())
    all_candidates.extend(get_from_youtube_trending())
    all_candidates.extend(get_from_reddit())
    all_candidates.extend(get_from_google_news())
    all_candidates = list(set([c.strip() for c in all_candidates if c.strip() and len(c.strip())>10]))
    print(f"🔥 SHORTS Total candidates from 4 sources: {len(all_candidates)}")
    if not all_candidates:
        emergency=["iPhone 16 Pro Max Review 4K","Samsung S24 Ultra Test 4K","Tesla Bot 2026 Review 4K"]
        chosen=random.choice(emergency)
        return chosen, "emergency_4_trending"
    used_file="used_titles.txt"
    if not os.path.exists(used_file):
        open(used_file,"w").close()
    with open(used_file,"r") as f:
        used=[line.strip().lower() for line in f.read().splitlines() if line.strip()]
    fresh=[c for c in all_candidates if c.lower() not in used]
    if not fresh:
        open(used_file,"w").close()
        fresh=all_candidates
    chosen=random.choice(fresh)
    print(f"🎯 SHORTS FINAL TRENDING (4 sources): {chosen}")
    return chosen, "4_trending_combined"

def get_emotional_script(topic):
    templates=[
        f"Oh my god! Paying 99 dollars for {topic}? I tested {topic} for 7 days in 4K and my face was shocked! Battery 40 hours! Beast lifts 50 tons! My hands shaking with excitement! Would you buy? Comment! Trending now from 4 sources!",
        f"Stop! {topic} made me cry! 7 days test in 4K ultra HD! 40 hours battery! 50 tons power! My facial expression says everything! My hands moving with joy! Comment A yes B no! Trending!",
        f"Guys I am shaking! {topic} is insane! Tested 7 days! 4K ultra HD! 40 hours! 50 tons! My shocked face! My excited hands! Would you pay 99 dollars? Comment now! Trending source!"
    ]
    return clean_for_tts(random.choice(templates))

def get_fast_paced_clips(topic, total_duration):
    clips=[];queries=[f"{topic} product review 4k",f"{topic} big machine 4k",f"{topic} army machine 4k",f"american {topic} 4k"]
    random.shuffle(queries)
    num_clips=8;per_clip=total_duration/num_clips
    for i in range(num_clips):
        try:
            q=queries[i%len(queries)]
            url=f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=10&orientation=portrait&size=large"
            headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
            resp=requests.get(url,headers=headers,timeout=15)
            if resp.status_code!=200: continue
            vids=resp.json().get('videos',[])
            if not vids: continue
            video=random.choice(vids[:3])
            files=sorted(video['video_files'],key=lambda x:x['width'],reverse=True)
            best=next((f for f in files if f['width']>=1080),files[0])
            path=f"clip_{i}.mp4"
            r=requests.get(best['link'],stream=True,timeout=60)
            with open(path,"wb") as out:
                for chunk in r.iter_content(chunk_size=1024*1024): out.write(chunk)
            clip=VideoFileClip(path)
            try: clip=clip.without_audio()
            except: clip=clip.with_audio(None)
            if clip.duration>per_clip+1:
                start=random.uniform(0,max(0,clip.duration-per_clip-0.5))
                try: clip=clip.subclip(start,start+per_clip)
                except: clip=clip.with_end(per_clip)
            clip=safe_set_duration(clip,per_clip)
            try: clip=clip.resize(height=H)
            except:
                try: clip=clip.resized(height=H)
                except: pass
            clips.append(clip)
        except: continue
    if not clips: return None
    final_bg=concatenate_videoclips(clips,method="compose")
    final_bg=safe_set_duration(final_bg,total_duration)
    return final_bg

def seo_optimize(topic, script_text):
    base_title=topic[:60]
    final_title=f"{base_title} 4K Review - Trending Now"[:65]
    description=f"{base_title} honest review 4K ultra HD from 4 trending sources.\n\n{script_text}\n\nShot in 4K.\n\n#Shorts #4K #Trending"
    tags=[topic.lower(),"4k review","trending now","product review","world trending","tech review 2026 4k"]
    return final_title,description,tags,final_title,final_title

topic_search,src=get_trending_world_tech()
topic_title=get_unique_title(topic_search)
script_text=get_emotional_script(topic_search)
voice_path=text_to_speech_piper(script_text,"voice.wav")
if not voice_path: exit(1)
audio=AudioFileClip(voice_path)
max_duration=20
if audio.duration>max_duration:
    try: audio=audio.subclip(0,max_duration)
    except: audio=audio.with_end(max_duration)
bg_clip=get_fast_paced_clips(topic_search,audio.duration)
if not bg_clip:
    bg_clip=ColorClip(size=(W,H),color=(10,10,30))
    bg_clip=safe_set_duration(bg_clip,audio.duration)
def create_overlay(duration,title,search):
    overlay=Image.new('RGBA',(W,H),(0,0,0,0))
    draw=ImageDraw.Draw(overlay,'RGBA')
    try: font_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.045))
    except: font_big=ImageFont.load_default()
    try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",int(W*0.02))
    except: font_small=ImageFont.load_default()
    draw.rounded_rectangle((20,20,750,70),radius=20,fill=(0,200,255,240))
    draw.text((35,28),"TRENDING NOW • 4K • 4 SOURCES COMBINED",fill=(0,0,0),font=font_small)
    draw.rectangle((0,int(H*0.7),W,H),fill=(0,0,0,210))
    y=int(H*0.72)
    for line in textwrap.wrap(title[:60],width=26):
        draw.text((35,y),line.upper(),fill="white",font=font_big,stroke_width=5,stroke_fill="black")
        y+=int(H*0.04)
        if y>int(H*0.85): break
    return safe_set_duration(ImageClip(np.array(overlay)),duration)

from upload_youtube import upload_video
final_yt_title,description,tags,title_a,title_b=seo_optimize(topic_search,script_text)
seo_filename=re.sub(r'[^a-z0-9]+','-',topic_search.lower()).strip('-')[:40]
seo_filename=f"{seo_filename}-4k-world-2026.mp4"
overlay_clip=create_overlay(audio.duration,final_yt_title,topic_search)
final=CompositeVideoClip([bg_clip,overlay_clip],size=(W,H))
final=safe_set_duration(final,audio.duration)
try: final=final.set_audio(audio)
except: final=final.with_audio(audio)
print(f"Writing 4K {seo_filename} {W}x{H} - 4 TRENDING SOURCES")
final.write_videofile(seo_filename, fps=30, codec='libx264', audio_codec='aac', threads=2, bitrate="12000k", logger=None)
print(f"SHORTS 4K DONE - {seo_filename} - 4 TRENDING SOURCES COMBINED")
upload_video(seo_filename,final_yt_title,description,tags)
