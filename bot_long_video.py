import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET, gc
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(t): return None

FAST_MODE=False
LOW_RAM=True
QUALITY=os.environ.get("QUALITY","4K")
W,H=3840,2160
if QUALITY!="4K":
    W,H=1280,720
MAX_DURATION=380
print(f"FINAL BOT 4K - W={W}x{H}")

PEXELS_API_KEY=os.environ.get("PEXELS_API_KEY")
TECH_ALLOWED=["iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","excavator","crane","bulldozer","jcb","caterpillar","construction","tank","fighter","military","abrams","f35","drone","ai","tesla","robot"]
BANNED=["tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","tmkoc","bhabi","kapil","bigg boss","football","cricket","movie","election","biden","trump","modi"]
VIRAL_TOPICS=["Caterpillar D9 Bulldozer","CMF Headphones by Nothing","Abrams M1A2 Tank","iPhone 16 Pro Max","F35 Fighter Jet","JCB 3CX Excavator","Samsung S24 Ultra","MQ9 Reaper Drone","Tesla Bot 2026","Liebherr Crane"]
USA_GIRL_QUERIES=["beautiful american woman talking camera","american girl explaining shocking","beautiful blonde woman surprised face","american woman tech review talking","beautiful american girl pointing","american woman serious explaining"]

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
    fact=f"{main} is trending worldwide right now in 2026."
    hook=f"Stop! Don't buy or use {main} before watching this video! I tested {main} for 7 days and what I found will shock you."
    chapters=[f"What is {main}? {fact}",f"How {main} works? {main} works on a 600 horsepower engine.",f"Power that shocked me. 600 horsepower, same as 6 sports cars.",f"Inside cabin secrets. 4 screens, GPS, thermal cameras.",f"Real test Texas site. Work pending for 3 days, {main} finished in 5 hours.",f"Hidden feature 99 percent miss. Secret button saves 30 percent fuel.",f"Final verdict. Should you buy {main}? Comment what you think."]
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
def download_pexels_video(query,prefix,count=1):
    out=[]
    try:
        url=f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=5&orientation=landscape&size=large"
        headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
        r=requests.get(url,headers=headers,timeout=15)
        if r.status_code!=200: return []
        for v in r.json().get('videos',[])[:count]:
            try:
                files=sorted(v['video_files'],key=lambda x:x['width'],reverse=True)
                best=next((f for f in files if f['width']>=1920),files[0])
                path=f"{prefix}_{random.randint(1000,9999)}.mp4"
                resp=requests.get(best['link'],stream=True,timeout=60)
                with open(path,"wb") as f:
                    for chunk in resp.iter_content(chunk_size=512*1024): f.write(chunk)
                if os.path.exists(path) and os.path.getsize(path)>30000: out.append(path)
            except: continue
    except: pass
    return out
def download_pexels_image(query):
    try:
        url=f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=3&orientation=landscape"
        headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
        r=requests.get(url,headers=headers,timeout=10)
        if r.status_code!=200: return None
        photos=r.json().get('photos',[])
        if not photos: return None
        img_url=photos[0]['src']['large2x']
        path=f"thumb_img_{random.randint(1000,9999)}.jpg"
        resp=requests.get(img_url,timeout=20)
        with open(path,"wb") as f: f.write(resp.content)
        if os.path.exists(path): return path
    except: return None
def get_girl_clips():
    clips=[]
    for q in USA_GIRL_QUERIES[:3]:
        clips.extend(download_pexels_video(q,"girl",1))
        if len(clips)>=4: break
        time.sleep(0.5);gc.collect()
    return clips
def get_broll(topic):
    clips=[]
    simple=["bulldozer","excavator"] if "bulldozer" in topic.lower() else ["military tank","fighter jet"] if "tank" in topic.lower() else ["headphones","iphone"]
    for q in simple[:2]:
        clips.extend(download_pexels_video(q,"broll",1))
        if len(clips)>=4: break
        time.sleep(0.5);gc.collect()
    return clips
def create_viral_video_LOW_RAM(girl_paths,broll_paths,sentences,total_duration,topic_main):
    final_files=[]
    per_sentence=total_duration/len(sentences) if sentences else 5
    per_sentence=max(2.5,min(per_sentence,5))
    for i,sent in enumerate(sentences[:8]):
        try:
            girl_path=girl_paths[i%len(girl_paths)] if girl_paths else None
            if girl_path and os.path.exists(girl_path):
                try:
                    gc_clip=VideoFileClip(girl_path)
                    gc_clip=safe_no_audio(gc_clip)
                    if gc_clip.duration<per_sentence: gc_clip=gc_clip.loop(duration=per_sentence)
                    try: gc_clip=gc_clip.subclip(0,per_sentence)
                    except: gc_clip=gc_clip.with_end(per_sentence)
                    gc_clip=safe_duration(gc_clip,per_sentence)
                    gc_clip=safe_resize(gc_clip,W)
                    try: gc_clip=gc_clip.crop(x_center=gc_clip.w/2,y_center=gc_clip.h*0.42,width=W,height=H)
                    except: pass
                except:
                    gc_clip=ColorClip(size=(W,H),color=(15,15,35))
                    gc_clip=safe_duration(gc_clip,per_sentence)
            else:
                gc_clip=ColorClip(size=(W,H),color=(15,15,35))
                gc_clip=safe_duration(gc_clip,per_sentence)
            try:
                img=Image.new('RGBA',(W,H),(0,0,0,0))
                draw=ImageDraw.Draw(img,'RGBA')
                try: font_bold=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.02))
                except: font_bold=ImageFont.load_default()
                try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.015))
                except: font_small=ImageFont.load_default()
                if i==0:
                    draw.rounded_rectangle((10,10,700,45),radius=10,fill=(255,0,80,230))
                    draw.text((15,15),"DON'T BUY BEFORE WATCHING!",fill="white",font=font_small)
                else:
                    draw.rounded_rectangle((10,10,500,40),radius=8,fill=(0,200,255,220))
                    draw.text((15,12),f"{topic_main[:30].upper()} - {i+1}",fill="black",font=font_small)
                draw.rectangle((0,int(H*0.75),W,H),fill=(0,0,0,190))
                wrapped=textwrap.wrap(sent,width=60)
                y=int(H*0.78)
                for line in wrapped[:2]:
                    draw.text((15,y),line.upper(),fill="white",font=font_bold,stroke_width=3,stroke_fill="black")
                    y+=int(H*0.04)
                txt_clip=ImageClip(np.array(img))
                txt_clip=safe_duration(txt_clip,per_sentence)
                comp=CompositeVideoClip([gc_clip,txt_clip],size=(W,H))
                comp=safe_duration(comp,per_sentence)
            except:
                comp=gc_clip
            temp_file=f"temp_seg_{i}.mp4"
            comp.write_videofile(temp_file,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=1,bitrate="8000k",logger=None,verbose=False)
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
    clips=[VideoFileClip(f) for f in final_files]
    final_video=concatenate_videoclips(clips,method="compose")
    final_video=safe_duration(final_video,total_duration)
    for c in clips:
        try: c.close()
        except: pass
    gc.collect()
    return final_video,final_files
def create_thumb_tech_burner_style(topic):
    try:
        TW,TH=1280,720
        thumb=Image.new('RGB',(TW,TH),(240,240,240))
        draw=ImageDraw.Draw(thumb)
        girl_img_path=download_pexels_image("beautiful american woman pointing")
        product_img_path=download_pexels_image(topic.split()[0])
        try:
            if product_img_path and os.path.exists(product_img_path):
                prod_img=Image.open(product_img_path).convert("RGBA")
                prod_img=prod_img.resize((500,500))
                thumb.paste(prod_img,(30,100),prod_img if prod_img.mode=='RGBA' else None)
        except: pass
        try:
            if girl_img_path and os.path.exists(girl_img_path):
                girl_img=Image.open(girl_img_path).convert("RGBA")
                girl_img=girl_img.resize((600,600))
                thumb.paste(girl_img,(650,50),girl_img if girl_img.mode=='RGBA' else None)
        except: pass
        thumb.save("thumbnail_long.jpg",quality=95)
        return "thumbnail_long.jpg"
    except: return None

if __name__=="__main__":
    trending_topic=get_trending()
    full_script,sentences,topic_main=generate_viral_script(trending_topic)
    audio_files=tts_piper(full_script)
    if not audio_files: exit(1)
    audio_clips=[AudioFileClip(p) for p in audio_files if os.path.exists(p)]
    final_audio=concatenate_audioclips(audio_clips)
    if final_audio.duration>MAX_DURATION:
        try: final_audio=final_audio.subclip(0,MAX_DURATION)
        except: final_audio=final_audio.with_end(MAX_DURATION)
    girl_clips=get_girl_clips()
    broll_clips=get_broll(topic_main)
    if not girl_clips:
        video_clip=ColorClip(size=(W,H),color=(15,15,35))
        video_clip=safe_duration(video_clip,final_audio.duration)
        temp_files=[]
    else:
        video_clip,temp_files=create_viral_video_LOW_RAM(girl_clips,broll_clips,sentences,final_audio.duration,topic_main)
    final_video=safe_duration(video_clip,final_audio.duration)
    final_video=safe_audio(final_video,final_audio)
    seo_name=re.sub(r'[^a-z0-9]+','-',topic_main.lower()).strip('-')[:40]
    filename=f"{seo_name}-usa-girl-4k-viral.mp4"
    print(f"Writing 4K {filename} {W}x{H} bitrate 8000k")
    final_video.write_videofile(filename,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None)
    for tf in temp_files:
        try: os.remove(tf)
        except: pass
    gc.collect()
    try:
        from upload_youtube import upload_video
        upload_video(filename,f"I Tested {topic_main} For 7 Days - 4K SHOCKING Truth!",f"4K - {full_script[:400]}",[topic_main.lower(),"4k","viral"],thumbnail_path=create_thumb_tech_burner_style(topic_main))
    except Exception as e:
        print(f"Upload fail: {e}")
