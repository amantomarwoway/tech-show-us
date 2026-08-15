import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET, gc
try:
    import imageio_ffmpeg
    os.environ['IMAGEIO_FFMPEG_EXE'] = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except:
    FFMPEG = "ffmpeg"

try:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, concatenate_audioclips
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, concatenate_audioclips

from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("🔥 SINGLE TOPIC EMOTIONAL - 4 MIN EXACT - Girl Expressions + Hand Movements")

W,H=3840,2160
MAX_DURATION=240
TARGET_DURATION=240  # Exact 4 minute

PEXELS_API_KEY=os.environ.get("PEXELS_API_KEY")
VIRAL_TOPICS=["Caterpillar D9 Bulldozer","CMF Headphones by Nothing","Abrams M1A2 Tank","iPhone 16 Pro Max","F35 Fighter Jet","JCB 3CX Excavator","Samsung S24 Ultra","MQ9 Reaper Drone","Tesla Bot 2026","Liebherr Crane"]

# EMOTIONAL GIRL QUERIES - facial expressions + hand movements
USA_GIRL_EMOTIONAL=[
    "beautiful american woman emotional talking with hands",
    "american girl shocked surprised facial expression close up",
    "beautiful blonde woman crying happy emotional hands moving",
    "american woman explaining with hand gestures expressive",
    "beautiful american girl excited face talking camera"
]

BANNED=["tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","tmkoc","bhabi","kapil","bigg boss","football","cricket","movie","election","biden","trump","modi"]
TECH_ALLOWED=["iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","excavator","crane","bulldozer","jcb","caterpillar","construction","tank","fighter","military","abrams","f35","drone","ai","tesla","robot"]

def safe_duration(c,d):
    try: return c.set_duration(d)
    except: return c.with_duration(d)
def safe_audio(c,a):
    try: return c.set_audio(a)
    except: return c.with_audio(a)
def safe_no_audio(c):
    try: return c.without_audio()
    except: return c.with_audio(None)
def safe_resize(clip,width=W):
    try: return clip.resize(width=width)
    except:
        try: return clip.resized(width=width)
        except: return clip
def clean_tts(t):
    t=re.sub(r'http\S+|www\S+|\.com','',t,flags=re.IGNORECASE)
    t=re.sub(r'[^a-zA-Z0-9.,!?$% ]',' ',t)
    t=re.sub(r'\s+',' ',t).strip()
    return t

def fix_video_with_ffmpeg(input_path):
    fixed_path = input_path.replace(".mp4", "_fixed.mp4")
    try:
        cmd = [FFMPEG, "-y", "-i", input_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-vf", "scale=1280:720:force_original_aspect_ratio=decrease", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", fixed_path]
        subprocess.run(cmd, timeout=30, capture_output=True)
        if os.path.exists(fixed_path) and os.path.getsize(fixed_path) > 50000:
            try: os.remove(input_path)
            except: pass
            os.rename(fixed_path, input_path)
        else:
            try: os.remove(fixed_path)
            except: pass
    except: pass
    return input_path

def safe_VideoFileClip(path, per_sentence=5):
    for attempt in range(3):
        try:
            clip = VideoFileClip(path)
            if clip.reader is None: raise Exception("Reader None")
            clip.get_frame(0)
            return clip
        except:
            if attempt < 2:
                fix_video_with_ffmpeg(path)
                time.sleep(1)
            else:
                return safe_duration(ColorClip(size=(W,H), color=(15,15,35)), per_sentence)
    return safe_duration(ColorClip(size=(W,H), color=(15,15,35)), per_sentence)

def get_topic():
    if not os.path.exists("used_long_titles.txt"): open("used_long_titles.txt","w").close()
    with open("used_long_titles.txt","r") as f: used=f.read().splitlines()
    available=[t for t in VIRAL_TOPICS if t not in used]
    if not available:
        available=VIRAL_TOPICS
        open("used_long_titles.txt","w").close()
    topic=random.choice(available)
    with open("used_long_titles.txt","a") as f: f.write(topic+"\n")
    return topic

def get_trending():
    try:
        r=requests.get("https://trends.google.com/trending/rss?geo=US",timeout=10)
        root=ET.fromstring(r.content)
        for item in root.findall('.//item/title')[:15]:
            t=item.text.strip()
            low=t.lower()
            if any(b in low for b in BANNED): continue
            if any(k in low for k in TECH_ALLOWED):
                return t[:60]
    except: pass
    return get_topic()

def generate_emotional_single_script(topic):
    """SINGLE TOPIC - NO CHAPTERS - Full emotional - 4 min - 550 words"""
    main=topic.replace(" - "," ").strip()
    
    # Single emotional story - no chapter numbers - pure emotion + facial expressions
    script = f"""
    Oh my god guys! You will not believe what happened when I tested {main} for 7 days! I am literally shaking right now because what I found shocked me completely! 
    When I first saw {main}, I thought wow this looks amazing, 99,000 dollars, 600 horsepower, big machine, but is it really worth that much money? I had so many doubts in my heart.
    I still remember day one, I was so nervous, my hands were shaking when I started {main} for the first time. The sound was so loud, like a beast roaring, 600 horsepower engine, oh my god! My heart was beating so fast! 
    But then something magical happened. On day two, I saw how this beast lifts 50 tons like it's nothing! I literally screamed with excitement, my eyes were wide open, I could not believe what I was seeing! 50 tons! Can you imagine? My hands automatically went up in shock!
    Day three was the most emotional day for me. I was working in Texas, hot sun, sweat on my face, but {main} did not stop. It worked for 5 hours non stop and completed 3 days of work! I started crying with happiness because I saved so much time and money. My facial expression was pure joy!
    But wait, there is a hidden secret that nobody tells you about {main}. 99 percent of people miss this hidden feature. There is a secret fuel saving mode that saves 30 percent fuel! When I found it, my jaw dropped, I was like oh my god why nobody told me this before! My hands were moving everywhere explaining this!
    Now let me be honest with you guys, with full emotions. I love {main} but there are 3 things that broke my heart. First, the price is too high, 99,000 dollars is a lot of money, my heart sank when I saw the price tag. Second, maintenance is so expensive, it hurts my pocket. Third, you need special training, I was so frustrated at first.
    But after 7 days, my final emotional verdict is this. If you have big construction projects, if you want to save time, if you want to feel that power in your hands, then {main} is for you. I am so emotional right now saying this, but this machine changed my life! My face shows pure excitement!
    So tell me in comments, would you buy {main} for 99,000 dollars? I am waiting for your comments with my heart full of emotions! If this 4 minute emotional review touched your heart, please subscribe! I put my full heart into this 4 minute video!
    """
    
    full=clean_tts(script)
    # For emotional flow, split into 8 emotional parts (not chapters) - each 30 sec
    sentences = [s.strip() for s in full.split('.') if len(s.strip()) > 25]
    # Ensure we have 8 parts for 4 min - 30 sec each
    if len(sentences) > 8:
        # Combine to make 8 emotional segments
        combined=[]
        chunk_size=len(sentences)//8
        for i in range(8):
            start=i*chunk_size
            end=start+chunk_size if i<7 else len(sentences)
            combined.append(". ".join(sentences[start:end]))
        sentences=combined
    return full, sentences[:8], main

def tts_piper_4min_emotional(script):
    clean=clean_tts(script)
    words=clean.split()
    chunk_size=max(1,len(words)//4)
    chunks=[' '.join(words[:chunk_size]),' '.join(words[chunk_size:chunk_size*2]),' '.join(words[chunk_size*2:chunk_size*3]),' '.join(words[chunk_size*3:])]
    chunks=[c for c in chunks if len(c.strip())>20]
    files=[]
    model="en_US-lessac-medium.onnx"
    has_piper=os.path.exists(model)
    for idx,chunk in enumerate(chunks):
        out_wav=f"voice_{idx}.wav"
        out_mp3=f"voice_{idx}.mp3"
        ok=False
        if has_piper:
            try:
                safe=chunk.replace('"','').replace('`','').replace('$','')
                # Emotional - slightly slower and expressive
                cmd=f'echo "{safe}" | piper --model {model} --output_file {out_wav} --length_scale 0.92 --sentence_silence 0.25'
                subprocess.run(cmd,shell=True,timeout=80,capture_output=True)
                if os.path.exists(out_wav) and os.path.getsize(out_wav)>2000:
                    files.append(out_wav);ok=True
            except: pass
        if not ok:
            try:
                from gtts import gTTS
                gTTS(text=chunk[:4000],lang='en',tld='us',slow=False).save(out_mp3)
                if os.path.exists(out_mp3): files.append(out_mp3)
            except: pass
        gc.collect()
    return files

def download_pexels_emotional(query, prefix):
    out=[]
    try:
        url=f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=15&orientation=landscape&size=medium"
        headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
        r=requests.get(url,headers=headers,timeout=15)
        if r.status_code!=200: return []
        videos=r.json().get('videos',[])
        random.shuffle(videos)
        for v in videos[:5]:
            try:
                files=sorted(v['video_files'],key=lambda x:x['width'],reverse=True)
                candidates=[f for f in files if 720 <= f['width'] <= 1280]
                if not candidates: continue
                best=random.choice(candidates[:2])
                path=f"{prefix}_{random.randint(1000,9999)}.mp4"
                resp=requests.get(best['link'],stream=True,timeout=90)
                with open(path,"wb") as f:
                    for chunk in resp.iter_content(chunk_size=512*1024): f.write(chunk)
                if not os.path.exists(path) or os.path.getsize(path)<80000:
                    try: os.remove(path)
                    except: pass
                    continue
                path = fix_video_with_ffmpeg(path)
                out.append(path)
                if len(out)>=2: break
            except: continue
    except: pass
    return out

def get_emotional_girl_clips():
    clips=[]
    for q in USA_GIRL_EMOTIONAL[:4]:
        found=download_pexels_emotional(q,"emotional_girl")
        clips.extend(found)
        if len(clips)>=8: break
        time.sleep(0.5);gc.collect()
    return clips

def get_creative_background_clips(topic):
    # Creative background - bokeh, neon, abstract
    queries=[f"{topic.split()[0]} cinematic bokeh", "creative neon background 4k", "abstract technology background"]
    clips=[]
    for q in queries[:2]:
        found=download_pexels_emotional(q,"creative_bg")
        clips.extend(found)
        if len(clips)>=4: break
        time.sleep(0.5);gc.collect()
    return clips

def create_video_emotional_single(sentences, total_duration, topic_main, girl_clips, bg_clips):
    final_files=[]
    per_sentence=total_duration/len(sentences) if sentences else 30
    per_sentence=max(28.0,min(per_sentence,32.0))  # 28-32 sec each for 4 min
    print(f"Creating EMOTIONAL SINGLE TOPIC - {len(sentences)} x {per_sentence:.1f} sec = {total_duration} sec")
    
    # Creative background - mix girl + creative bokeh
    all_clips = girl_clips + bg_clips
    if not all_clips:
        all_clips = girl_clips
    
    for i,sent in enumerate(sentences[:8]):
        try:
            path=all_clips[i % len(all_clips)] if all_clips else None
            if not path or not os.path.exists(path):
                gc_clip=ColorClip(size=(W,H),color=(25,10,40))  # Creative purple background
                gc_clip=safe_duration(gc_clip,per_sentence)
            else:
                try:
                    gc_clip=VideoFileClip(path)
                    gc_clip=safe_no_audio(gc_clip)
                    if gc_clip.duration<per_sentence:
                        try: gc_clip=gc_clip.loop(duration=per_sentence)
                        except: gc_clip=safe_duration(gc_clip,per_sentence)
                    try: gc_clip=gc_clip.subclip(0,per_sentence)
                    except: gc_clip=gc_clip.with_end(per_sentence)
                    gc_clip=safe_duration(gc_clip,per_sentence)
                    gc_clip=safe_resize(gc_clip,W)
                    try: gc_clip=gc_clip.crop(x_center=gc_clip.w/2,y_center=gc_clip.h*0.42,width=W,height=H)
                    except: pass
                except:
                    gc_clip=ColorClip(size=(W,H),color=(25,10,40))
                    gc_clip=safe_duration(gc_clip,per_sentence)
            
            # Creative overlay - emotional style
            img=Image.new('RGBA',(W,H),(0,0,0,0))
            draw=ImageDraw.Draw(img,'RGBA')
            try: font_bold=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.022))
            except: font_bold=ImageFont.load_default()
            try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.016))
            except: font_small=ImageFont.load_default()
            
            # Emotional top badge
            if i==0:
                draw.rounded_rectangle((30,30,950,90),radius=15,fill=(255,0,80,230))
                draw.text((50,40),"OH MY GOD! EMOTIONAL REVIEW - 4K - FULL HEART",fill="white",font=font_small)
            else:
                # Show emotions - shocked, happy, etc.
                emotions=["SHOCKED! 😱", "AMAZING! 🤩", "SO HAPPY! 😭", "WOW! 🙌", "EMOTIONAL! ❤️", "UNBELIEVABLE! 😲", "LOVE IT! 🥰", "FINAL! 💖"]
                draw.rounded_rectangle((30,30,750,80),radius=12,fill=(0,200,255,220))
                draw.text((40,38),f"{emotions[i % len(emotions)]} - {topic_main[:20].upper()}",fill="black",font=font_small)
            
            # Bottom text area - creative gradient style
            draw.rectangle((0,int(H*0.70),W,H),fill=(0,0,0,200))
            # Add creative side glow
            draw.rectangle((0,int(H*0.70),15,H),fill=(255,0,80,180))
            
            wrapped=textwrap.wrap(sent,width=50)
            y=int(H*0.73)
            for line in wrapped[:4]:  # 4 lines for emotional depth
                draw.text((40,y),line.upper(),fill="white",font=font_bold,stroke_width=4,stroke_fill="black")
                y+=int(H*0.05)
            
            txt_clip=ImageClip(np.array(img))
            txt_clip=safe_duration(txt_clip,per_sentence)
            comp=CompositeVideoClip([gc_clip,txt_clip],size=(W,H))
            comp=safe_duration(comp,per_sentence)
            temp_file=f"temp_emotional_{i}.mp4"
            comp.write_videofile(temp_file,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None,verbose=False)
            final_files.append(temp_file)
            try: comp.close(); gc_clip.close()
            except: pass
            gc.collect()
        except Exception as e:
            print(f"Segment {i} error: {e}");gc.collect();continue
    
    if not final_files:
        fallback=ColorClip(size=(W,H),color=(25,10,40))
        fallback=safe_duration(fallback,total_duration)
        return fallback,[]
    
    clips=[]
    for f in final_files:
        try:
            c=VideoFileClip(f)
            clips.append(c)
        except: continue
    
    final_video=concatenate_videoclips(clips,method="compose")
    final_video=safe_duration(final_video,TARGET_DURATION)
    for c in clips:
        try: c.close()
        except: pass
    gc.collect()
    return final_video,final_files

if __name__=="__main__":
    trending_topic=get_trending()
    full_script,sentences,topic_main=generate_emotional_single_script(trending_topic)
    print(f"Topic: {topic_main} - EMOTIONAL SINGLE - 4 MIN - {len(sentences)} parts")
    print(f"Script preview: {full_script[:200]}...")
    
    audio_files=tts_piper_4min_emotional(full_script)
    if not audio_files: exit(1)
    audio_clips=[AudioFileClip(p) for p in audio_files if os.path.exists(p) and os.path.getsize(p)>1000]
    if not audio_clips: exit(1)
    final_audio=concatenate_audioclips(audio_clips)
    
    # Force exact 240 sec
    if final_audio.duration > TARGET_DURATION:
        try: final_audio=final_audio.subclip(0,TARGET_DURATION)
        except: final_audio=final_audio.with_end(TARGET_DURATION)
    final_audio=safe_duration(final_audio,TARGET_DURATION)
    
    print(f"Audio exact 4 min: {final_audio.duration} sec - Fetching emotional girl clips")
    girl_clips=get_emotional_girl_clips()
    bg_clips=get_creative_background_clips(topic_main)
    print(f"Girl clips: {len(girl_clips)}, BG clips: {len(bg_clips)}")
    
    all_clips = girl_clips + bg_clips
    if len(all_clips) < 2:
        video_clip=ColorClip(size=(W,H),color=(25,10,40))
        video_clip=safe_duration(video_clip,final_audio.duration)
        temp_files=[]
    else:
        video_clip,temp_files=create_video_emotional_single(sentences,final_audio.duration,topic_main,girl_clips,bg_clips)
    
    final_video=safe_duration(video_clip,TARGET_DURATION)
    final_video=safe_audio(final_video,final_audio)
    final_video=safe_duration(final_video,TARGET_DURATION)
    
    seo_name=re.sub(r'[^a-z0-9]+','-',topic_main.lower()).strip('-')[:40]
    filename=f"{seo_name}-emotional-single-4min-4k.mp4"
    print(f"Writing EMOTIONAL SINGLE 4 MINUTE {filename} - {TARGET_DURATION} sec")
    final_video.write_videofile(filename,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None)
    
    for tf in temp_files:
        try: os.remove(tf)
        except: pass
    for p in all_clips:
        try: os.remove(p)
        except: pass
    gc.collect()
    print(f"✅ EMOTIONAL SINGLE 4 MINUTE DONE - {filename} - NO CHAPTERS - FULL EMOTIONS!")
    try:
        from upload_youtube import upload_video
        upload_video(filename,f"{topic_main} Made Me Cry! My Emotional 4 Minute Story!",f"Single topic emotional review with facial expressions and hand movements - {full_script[:500]}",[topic_main.lower(),"emotional","4 minute","girl reaction","viral"])
    except Exception as e:
        print(f"Upload fail: {e}")
