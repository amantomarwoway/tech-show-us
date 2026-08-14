import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET, gc
# BOTH SOLUTION 1+2: Pillow 9.5.0 + MoviePy 2.1.2 - fixes ANTIALIAS + reader None
try:
    import imageio_ffmpeg
    os.environ['IMAGEIO_FFMPEG_EXE'] = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"✅ Bundled FFmpeg: {os.environ['IMAGEIO_FFMPEG_EXE']}")
except:
    print("Using system FFmpeg")

from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np

print("FINAL CLIP-ONLY 4K - SOLUTION 1+2 BOTH - Pillow 9.5.0 + MoviePy 2.1.2 + No Double Open")

QUALITY=os.environ.get("QUALITY","4K")
W,H=3840,2160
MAX_DURATION=380

PEXELS_API_KEY=os.environ.get("PEXELS_API_KEY")
VIRAL_TOPICS=["Caterpillar D9 Bulldozer","CMF Headphones by Nothing","Abrams M1A2 Tank","iPhone 16 Pro Max","F35 Fighter Jet","JCB 3CX Excavator","Samsung S24 Ultra","MQ9 Reaper Drone","Tesla Bot 2026","Liebherr Crane"]
USA_GIRL_QUERIES=["beautiful american woman talking camera","american girl explaining shocking","beautiful blonde woman surprised face","american woman tech review talking"]
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

def generate_viral_script(topic):
    main=topic.replace(" - "," ").strip()
    hook=f"Stop! Don't buy or use {main} before watching this video! I tested {main} for 7 days and what I found will shock you."
    chapters=[f"What is {main}? {main} trending 2026.",f"How {main} works? 600 HP hydraulic.",f"Power shocked me. 600 HP 6 sports cars.",f"Inside secrets. 4 screens GPS thermal.",f"Real test Texas. 3 days work 5 hours.",f"Hidden feature 99 percent miss. Saves 30 percent fuel.",f"Final verdict. Should you buy {main}? Comment."]
    full=hook+" ".join(chapters)
    full=clean_tts(full)
    return full, full.split('.'), main

def tts_piper(script):
    clean=clean_tts(script)
    words=clean.split()
    chunk_size=max(1,len(words)//3)
    chunks=[' '.join(words[:chunk_size]),' '.join(words[chunk_size:chunk_size*2]),' '.join(words[chunk_size*2:])]
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
                cmd=f'echo "{safe}" | piper --model {model} --output_file {out_wav} --length_scale 0.88 --sentence_silence 0.2'
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

def download_pexels_clip_both_fix(query, prefix):
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
                print(f"✅ CLIP DOWNLOADED BOTH FIX: {path} - {best['width']}p")
                out.append(path)
                if len(out)>=2: break
            except: continue
    except Exception as e:
        print(f"Download error {query}: {e}")
    return out

def get_girl_clips_both():
    clips=[]
    for q in USA_GIRL_QUERIES[:3]:
        found=download_pexels_clip_both_fix(q,"girl")
        clips.extend(found)
        if len(clips)>=6: break
        time.sleep(0.5);gc.collect()
    return clips

def get_broll_both(topic):
    clips=[]
    queries=["excavator working","bulldozer construction"] if "bulldozer" in topic.lower() else ["military tank","army vehicle"] if "tank" in topic.lower() else [f"{topic.split()[0]} product"]
    for q in queries[:2]:
        found=download_pexels_clip_both_fix(q,"broll")
        clips.extend(found)
        if len(clips)>=4: break
        time.sleep(0.5);gc.collect()
    return clips

def create_video_both_fix(sentences, total_duration, topic_main, clip_paths):
    final_files=[]
    per_sentence=total_duration/len(sentences) if sentences else 5
    per_sentence=max(3.0,min(per_sentence,6.0))
    print(f"Creating BOTH FIX CLIP-ONLY 4K - {len(sentences)} segments")
    for i,sent in enumerate(sentences[:8]):
        try:
            path=clip_paths[i % len(clip_paths)] if clip_paths else None
            if not path or not os.path.exists(path):
                gc_clip=ColorClip(size=(W,H),color=(15,15,35))
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
                    print(f"✅ Segment {i} clip OK - {path}")
                except Exception as e:
                    print(f"Segment {i} clip error {path}: {e}")
                    gc_clip=ColorClip(size=(W,H),color=(15,15,35))
                    gc_clip=safe_duration(gc_clip,per_sentence)
            img=Image.new('RGBA',(W,H),(0,0,0,0))
            draw=ImageDraw.Draw(img,'RGBA')
            try: font_bold=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.022))
            except: font_bold=ImageFont.load_default()
            try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.016))
            except: font_small=ImageFont.load_default()
            if i==0:
                draw.rounded_rectangle((30,30,900,90),radius=15,fill=(255,0,80,230))
                draw.text((50,40),"DON'T BUY BEFORE WATCHING! 4K CLIP",fill="white",font=font_small)
            else:
                draw.rounded_rectangle((30,30,700,80),radius=12,fill=(0,200,255,220))
                draw.text((40,38),f"{topic_main[:35].upper()} - PART {i+1}",fill="black",font=font_small)
            draw.rectangle((0,int(H*0.72),W,H),fill=(0,0,0,190))
            wrapped=textwrap.wrap(sent,width=55)
            y=int(H*0.75)
            for line in wrapped[:3]:
                draw.text((40,y),line.upper(),fill="white",font=font_bold,stroke_width=4,stroke_fill="black")
                y+=int(H*0.05)
            txt_clip=ImageClip(np.array(img))
            txt_clip=safe_duration(txt_clip,per_sentence)
            comp=CompositeVideoClip([gc_clip,txt_clip],size=(W,H))
            comp=safe_duration(comp,per_sentence)
            temp_file=f"temp_seg_{i}_clip.mp4"
            comp.write_videofile(temp_file,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None,verbose=False)
            final_files.append(temp_file)
            try: comp.close(); gc_clip.close()
            except: pass
            gc.collect()
        except Exception as e:
            print(f"Segment {i} error: {e}");gc.collect();continue
    if not final_files:
        fallback=ColorClip(size=(W,H),color=(10,10,30))
        fallback=safe_duration(fallback,total_duration)
        return fallback,[]
    clips=[]
    for f in final_files:
        try:
            c=VideoFileClip(f)
            clips.append(c)
        except: continue
    if not clips:
        fallback=ColorClip(size=(W,H),color=(10,10,30))
        fallback=safe_duration(fallback,total_duration)
        return fallback,final_files
    final_video=concatenate_videoclips(clips,method="compose")
    final_video=safe_duration(final_video,total_duration)
    for c in clips:
        try: c.close()
        except: pass
    gc.collect()
    return final_video,final_files

if __name__=="__main__":
    trending_topic=get_trending()
    full_script,sentences,topic_main=generate_viral_script(trending_topic)
    print(f"Topic: {topic_main} - BOTH FIX")
    audio_files=tts_piper(full_script)
    if not audio_files: exit(1)
    audio_clips=[AudioFileClip(p) for p in audio_files if os.path.exists(p) and os.path.getsize(p)>1000]
    if not audio_clips: exit(1)
    final_audio=concatenate_audioclips(audio_clips)
    if final_audio.duration>MAX_DURATION:
        try: final_audio=final_audio.subclip(0,MAX_DURATION)
        except: final_audio=final_audio.with_end(MAX_DURATION)
    print(f"Audio {final_audio.duration/60:.1f} min - Fetching clips BOTH FIX")
    girl_clips=get_girl_clips_both()
    broll_clips=get_broll_both(topic_main)
    all_clips=girl_clips + broll_clips
    if not all_clips:
        video_clip=ColorClip(size=(W,H),color=(15,15,35))
        video_clip=safe_duration(video_clip,final_audio.duration)
        temp_files=[]
    else:
        video_clip,temp_files=create_video_both_fix(sentences,final_audio.duration,topic_main,all_clips)
    final_video=safe_duration(video_clip,final_audio.duration)
    final_video=safe_audio(final_video,final_audio)
    seo_name=re.sub(r'[^a-z0-9]+','-',topic_main.lower()).strip('-')[:40]
    filename=f"{seo_name}-usa-girl-4k-both-fix.mp4"
    print(f"Writing BOTH FIX 4K {filename} {W}x{H}")
    final_video.write_videofile(filename,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None)
    for tf in temp_files:
        try: os.remove(tf)
        except: pass
    for p in all_clips:
        try: os.remove(p)
        except: pass
    gc.collect()
    print(f"✅ BOTH FIX 4K DONE - {filename}")
    try:
        from upload_youtube import upload_video
        upload_video(filename,f"I Tested {topic_main} For 7 Days - 4K CLIP Truth!",f"4K BOTH FIX - {full_script[:500]}",[topic_main.lower(),"4k","viral"])
    except Exception as e:
        print(f"Upload fail: {e}")
