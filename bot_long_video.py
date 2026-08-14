import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, ColorClip, CompositeAudioClip, concatenate_audioclips
from PIL import Image, ImageDraw, ImageFont
import numpy as np
try:
    from auto_music import fetch_music_for_video
except:
    def fetch_music_for_video(t): return None

# === FIXED CONFIG - USA BEST TIME + FAST MODE + PIPER ===
FAST_MODE = os.environ.get("FAST_MODE") == "true"
MAX_DURATION = 400 if FAST_MODE else 520
print(f"🔥 VIRAL BOT - PIPER USA GIRL + TECH BURNER THUMBNAIL - FAST_MODE={FAST_MODE} - MAX {MAX_DURATION/60:.1f} min")

PEXELS_API_KEY=os.environ.get("PEXELS_API_KEY")
CHANNEL_LINK="https://www.youtube.com/@TECH4USA"
TECH_ALLOWED=["iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","excavator","crane","bulldozer","jcb","caterpillar","construction","tank","fighter","military","abrams","f35","drone","ai","tesla","robot"]
BANNED=["tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","tmkoc","bhabi","kapil","bigg boss","football","cricket","movie","election","biden","trump","modi"]
VIRAL_TOPICS=["Caterpillar D9 Bulldozer","CMF Headphones by Nothing","Abrams M1A2 Tank","iPhone 16 Pro Max","F35 Fighter Jet","JCB 3CX Excavator","Samsung S24 Ultra","MQ9 Reaper Drone","Tesla Bot 2026","Liebherr Crane"]
USA_GIRL_QUERIES=["beautiful american woman talking camera","american girl explaining shocking","beautiful blonde woman surprised face","american woman tech review talking","beautiful american girl pointing","american woman serious explaining","beautiful brunette woman happy","american girl vlogger closeup"]

def safe_duration(c,d):
    try: return c.set_duration(d)
    except: return c.with_duration(d)
def safe_audio(c,a):
    try: return c.set_audio(a)
    except: return c.with_audio(a)
def safe_no_audio(c):
    try: return c.without_audio()
    except: return c.with_audio(None)
def clean_tts(t):
    t=re.sub(r'http\S+|www\S+|\.com','',t,flags=re.IGNORECASE)
    t=re.sub(r'[^a-zA-Z0-9.,!?$% ]',' ',t)
    t=re.sub(r'\s+',' ',t).strip()
    return t
def get_topic():
    if not os.path.exists("used_long_titles.txt"): open("used_long_titles.txt","w").close()
    with open("used_long_titles.txt","r") as f: used=f.read().splitlines()
    available=[t for t in VIRAL_TOPICS if t.split()[0] not in ' '.join(used)]
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
                print(f"TRENDING: {t}")
                return t[:60]
    except: pass
    return get_topic()
def generate_viral_script(topic):
    main=topic.replace(" - "," ").strip()
    print(f"Generating VIRAL script for: {main}")
    fact=f"{main} is trending worldwide right now in 2026."
    try:
        url=f"https://en.wikipedia.org/w/api.php?action=opensearch&search={requests.utils.quote(main.split()[0])}&limit=1&format=json"
        r=requests.get(url,timeout=8)
        if r.status_code==200:
            d=r.json()
            if len(d)>2 and d[2] and len(d[2][0])>20:
                fact=d[2][0][:180]
    except: pass
    hook=f"Stop! Don't buy or use {main} before watching this video! I tested {main} for 7 days and what I found will shock you. This is the truth nobody tells you about {main}. Watch till end."
    chapters=[f"What is {main}? {fact} Many people ask what is {main}. In simple words, {main} is a powerful machine built for extreme work that humans cannot do alone. I will explain everything.",f"How {main} works? {main} works on a 600 horsepower engine and hydraulic system with 5000 PSI pressure. When operator pushes joystick, hydraulic oil flows and {main} moves. It is like super human muscle.",f"Power that shocked me. When I first started {main}, ground was shaking. This is 600 horsepower, same as 6 sports cars. It can push 50 tons, lift 20 tons, work 20 hours nonstop. Real beast.",f"Inside cabin secrets. Inside {main} cabin, there are 4 screens, GPS, thermal cameras, air seat. Operator controls everything with 2 joysticks. I sat inside in Texas, feels like spaceship.",f"Real test - Texas site. I took {main} to real construction site in Texas. Work pending for 3 days, {main} finished in 5 hours. Dug 10 feet, moved 30 tons mud. Operator drives {main} from New York to Los Angeles.",f"Hidden feature 99 percent miss. Secret button in {main} saves 30 percent fuel. Auto leveling, night lights that make night like day. Manual does not tell, real operators know this trick.",f"{main} vs others. I compared {main} with similar machines. If bulldozer, it wins in pushing. Excavator wins in digging. Crane wins in height. So if you need raw power, {main} is number one.",f"Price - Is {main} worth it? {main} costs 500 thousand to 1 million dollars. Sounds high, but does work of 50 workers. 50 workers cost 2500 dollars per hour, {main} costs 500 dollars. Saves millions yearly.",f"Future of {main}. By 2027, {main} will be autonomous. No driver. AI will drive, GPS will control, sensors avoid obstacles. Tesla and Caterpillar testing self driving {main} in Nevada desert. Future is here.",f"Final verdict. Should you buy {main}? If you are big company, army, or love power machines, yes. If small contractor, rent it. In my opinion, {main} is best in world. Comment what you think about {main}. I reply to all."]
    full=hook+" ".join(chapters)
    full=clean_tts(full)
    sents=[];seen=set()
    for s in full.split('.'):
        s=s.strip()
        if len(s)>20 and s.lower() not in seen:
            seen.add(s.lower());sents.append(s)
    full='. '.join(sents)+'.'
    words=full.split()
    max_words = 900 if FAST_MODE else 1100
    if len(words)>max_words:
        full=' '.join(words[:max_words])+'.'
        sents=full.split('.')[:10 if FAST_MODE else 12]
    print(f"Viral script ready - {len(words)} words - {len(sents)} sentences - FAST={FAST_MODE}")
    return full,sents,main

def tts_piper(script):
    clean=clean_tts(script)
    words=clean.split()
    chunk_size=len(words)//3
    chunks=[' '.join(words[:chunk_size]),' '.join(words[chunk_size:chunk_size*2]),' '.join(words[chunk_size*2:])]
    chunks=[c for c in chunks if len(c.strip())>20]
    files=[]
    model="en_US-lessac-medium.onnx"
    model_json=model+".json"
    has_piper=os.path.exists(model) and os.path.exists(model_json)
    print(f"TTS Check - Piper model exists: {has_piper}")
    for idx,chunk in enumerate(chunks):
        out_wav=f"voice_{idx}.wav"
        out_mp3=f"voice_{idx}.mp3"
        ok=False
        if has_piper:
            try:
                safe=chunk.replace('"','').replace('`','').replace('$','').replace('&',' and ')
                cmd=f'echo "{safe}" | piper --model {model} --output_file {out_wav} --length_scale 0.88 --sentence_silence 0.2'
                result=subprocess.run(cmd,shell=True,timeout=90,capture_output=True,text=True)
                if os.path.exists(out_wav) and os.path.getsize(out_wav)>2000:
                    files.append(out_wav);ok=True;print(f"✅ Piper {idx} ok")
            except Exception as e: print(f"Piper fail {idx}: {e}")
        if not ok:
            try:
                from gtts import gTTS
                gTTS(text=chunk[:4000],lang='en',tld='us',slow=False).save(out_mp3)
                if os.path.exists(out_mp3) and os.path.getsize(out_mp3)>1000: files.append(out_mp3)
            except: pass
    return files

def download_pexels_video(query,prefix,count=2):
    out=[]
    try:
        url=f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=8&orientation=landscape&size=medium"
        headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
        r=requests.get(url,headers=headers,timeout=15)
        if r.status_code!=200: return []
        for v in r.json().get('videos',[])[:count]:
            try:
                files=sorted(v['video_files'],key=lambda x:x['width'],reverse=True)
                best=next((f for f in files if f['width']>=1280),files[0])
                path=f"{prefix}_{random.randint(1000,9999)}.mp4"
                resp=requests.get(best['link'],stream=True,timeout=60)
                with open(path,"wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024*1024): f.write(chunk)
                if os.path.exists(path) and os.path.getsize(path)>40000: out.append(path)
            except: continue
    except: pass
    return out

def download_pexels_image(query):
    try:
        url=f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=5&orientation=landscape"
        headers={"Authorization":PEXELS_API_KEY} if PEXELS_API_KEY else {}
        r=requests.get(url,headers=headers,timeout=10)
        if r.status_code!=200: return None
        photos=r.json().get('photos',[])
        if not photos: return None
        img_url=photos[0]['src']['large']
        path=f"thumb_img_{random.randint(1000,9999)}.jpg"
        resp=requests.get(img_url,timeout=20)
        with open(path,"wb") as f: f.write(resp.content)
        if os.path.exists(path): return path
    except: return None

def get_girl_clips():
    clips=[];random.shuffle(USA_GIRL_QUERIES)
    target = 6 if FAST_MODE else 8
    per_query = 1 if FAST_MODE else 2
    for q in USA_GIRL_QUERIES[:4 if FAST_MODE else 5]:
        clips.extend(download_pexels_video(q,"girl",per_query))
        if len(clips)>=target: break
        time.sleep(0.5 if FAST_MODE else 0.8)
    return clips

def get_broll(topic):
    clips=[];simple=[]
    if any(w in topic.lower() for w in ["bulldozer","excavator","crane","jcb","caterpillar"]): simple=["bulldozer","excavator","construction machine"]
    elif any(w in topic.lower() for w in ["tank","fighter","drone","military","abrams","f35"]): simple=["military tank","fighter jet","army"]
    else: simple=["headphones","iphone","technology"]
    target = 6 if FAST_MODE else 10
    per_query = 1 if FAST_MODE else 2
    for q in simple[:3 if FAST_MODE else 5]:
        clips.extend(download_pexels_video(q,"broll",per_query))
        if len(clips)>=target: break
        time.sleep(0.5 if FAST_MODE else 0.8)
    return clips

def create_viral_video(girl_paths,broll_paths,sentences,total_duration,topic_main):
    final_segments=[];per_sentence=total_duration/len(sentences) if sentences else total_duration/10
    if per_sentence<2.5: per_sentence=2.5
    if per_sentence>8: per_sentence=6
    for i,sent in enumerate(sentences):
        try:
            girl_path=girl_paths[i%len(girl_paths)] if girl_paths else None
            broll_path=broll_paths[i%len(broll_paths)] if broll_paths else None
            if girl_path and os.path.exists(girl_path):
                try:
                    gc=VideoFileClip(girl_path);gc=safe_no_audio(gc)
                    if gc.duration<per_sentence: gc=concatenate_videoclips([gc]* (int(per_sentence//gc.duration)+1))
                    st=random.uniform(0,max(0,gc.duration-per_sentence-0.1))
                    try: gc=gc.subclip(st,st+per_sentence)
                    except: gc=gc.with_end(per_sentence)
                    gc=safe_duration(gc,per_sentence)
                    try: gc=gc.resize(width=1920)
                    except:
                        try: gc=gc.resized(width=1920)
                        except: pass
                    try: gc=gc.crop(x_center=gc.w/2,y_center=gc.h*0.42,width=1920,height=1080)
                    except: pass
                except:
                    gc=ColorClip(size=(1920,1080),color=(15,15,35));gc=safe_duration(gc,per_sentence)
            else:
                gc=ColorClip(size=(1920,1080),color=(15,15,35));gc=safe_duration(gc,per_sentence)
            if broll_path and os.path.exists(broll_path):
                try:
                    bc=VideoFileClip(broll_path);bc=safe_no_audio(bc)
                    if bc.duration<per_sentence: bc=concatenate_videoclips([bc]* (int(per_sentence//bc.duration)+1))
                    st=random.uniform(0,max(0,bc.duration-per_sentence-0.1))
                    try: bc=bc.subclip(st,st+per_sentence)
                    except: bc=bc.with_end(per_sentence)
                    bc=safe_duration(bc,per_sentence)
                    try: bc=bc.resize(width=700)
                    except:
                        try: bc=bc.resized(width=700)
                        except: pass
                    try: bc=bc.set_position((1920-720,1080-450))
                    except: bc=bc.with_position((1920-720,1080-450))
                    comp=CompositeVideoClip([gc,bc],size=(1920,1080));comp=safe_duration(comp,per_sentence)
                except: comp=gc
            else: comp=gc
            try:
                img=Image.new('RGBA',(1920,1080),(0,0,0,0));draw=ImageDraw.Draw(img,'RGBA')
                try: font_bold=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",48)
                except: font_bold=ImageFont.load_default()
                try: font_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",30)
                except: font_small=ImageFont.load_default()
                if i==0:
                    draw.rounded_rectangle((20,20,1100,75),radius=15,fill=(255,0,80,230))
                    draw.text((30,28),"🚨 VIRAL - DON'T BUY BEFORE WATCHING!",fill="white",font=font_small)
                else:
                    draw.rounded_rectangle((20,20,800,65),radius=12,fill=(0,200,255,220))
                    draw.text((30,25),f"{topic_main[:40].upper()} - CHAPTER {i+1}",fill="black",font=font_small)
                draw.rectangle((0,800,1920,1080),fill=(0,0,0,190))
                wrapped=textwrap.wrap(sent,width=50);y=820
                for line in wrapped[:3]:
                    draw.text((40,y),line.upper(),fill="white",font=font_bold,stroke_width=5,stroke_fill="black");y+=60
                if broll_path:
                    draw.rounded_rectangle((1920-720,1080-470,1920-20,1080-430),radius=10,fill=(255,235,0,230))
                    draw.text((1920-700,1080-465),f"👉 {topic_main.split()[0].upper()} IN ACTION",fill="black",font=font_small)
                txt_clip=ImageClip(np.array(img));txt_clip=safe_duration(txt_clip,per_sentence)
                comp=CompositeVideoClip([comp,txt_clip],size=(1920,1080));comp=safe_duration(comp,per_sentence)
            except: pass
            final_segments.append(comp)
        except: continue
    if not final_segments:
        fallback=ColorClip(size=(1920,1080),color=(10,10,30));fallback=safe_duration(fallback,total_duration);return fallback
    final_video=concatenate_videoclips(final_segments,method="compose");final_video=safe_duration(final_video,total_duration)
    return final_video

def create_thumb_tech_burner_style(topic):
    try:
        W,H=1280,720;thumb=Image.new('RGB',(W,H),(240,240,240));draw=ImageDraw.Draw(thumb)
        product_query=topic.split()[0]
        if "bulldozer" in topic.lower() or "excavator" in topic.lower() or "crane" in topic.lower(): product_query="bulldozer construction machine"
        elif "tank" in topic.lower() or "fighter" in topic.lower(): product_query="military tank"
        elif "headphone" in topic.lower(): product_query="headphones"
        elif "iphone" in topic.lower() or "samsung" in topic.lower(): product_query="iphone smartphone"
        girl_img_path=download_pexels_image("beautiful american woman orange shirt smiling pointing")
        if not girl_img_path: girl_img_path=download_pexels_image("american girl pointing smiling")
        product_img_path=download_pexels_image(product_query)
        try:
            if product_img_path and os.path.exists(product_img_path):
                prod_img=Image.open(product_img_path).convert("RGBA");prod_img=prod_img.resize((520,520));thumb.paste(prod_img,(30,100),prod_img if prod_img.mode=='RGBA' else None)
            else: draw.rounded_rectangle((40,100,540,600),radius=20,fill=(20,20,20))
        except: draw.rounded_rectangle((40,100,540,600),radius=20,fill=(20,20,20))
        try:
            if girl_img_path and os.path.exists(girl_img_path):
                girl_img=Image.open(girl_img_path).convert("RGBA");girl_img=girl_img.resize((650,650));thumb.paste(girl_img,(630,30),girl_img if girl_img.mode=='RGBA' else None)
        except: pass
        try:
            draw.line([(380,250),(520,170)],fill="black",width=8);draw.polygon([(520,170),(500,150),(540,140)],fill="black")
            draw.ellipse((490,80,630,180),fill="white",outline="black",width=3);draw.rectangle((550,100,570,160),fill=(0,100,255));draw.rectangle((490,120,630,140),fill=(0,100,255))
        except: pass
        try:
            font_logo_big=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",36)
            font_logo_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",22)
        except:
            font_logo_big=ImageFont.load_default();font_logo_small=ImageFont.load_default()
        draw.rounded_rectangle((10,10,200,65),radius=8,fill=(0,0,0));draw.text((15,12),"TECH",fill="#00D4FF",font=font_logo_big,stroke_width=2,stroke_fill="black");draw.text((15,38),"4 USA",fill="#FF3300",font=font_logo_small,stroke_width=2,stroke_fill="white")
        for p in [girl_img_path,product_img_path]:
            try:
                if p and os.path.exists(p): os.remove(p)
            except: pass
        thumb.save("thumbnail_long.jpg",quality=95);print("✅ TECH BURNER STYLE THUMBNAIL READY");return "thumbnail_long.jpg"
    except Exception as e:
        print(f"Thumb fail: {e}")
        try:
            W,H=1280,720;thumb=Image.new('RGB',(W,H),(240,240,240));draw=ImageDraw.Draw(thumb)
            try: font_huge=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",85)
            except: font_huge=ImageFont.load_default()
            draw.text((30,20),f"{topic.split()[0].upper()}",fill="black",font=font_huge,stroke_width=6,stroke_fill="white");draw.text((30,120),f"{topic.split()[-1].upper()}?!",fill="#FF3300",font=font_huge,stroke_width=6,stroke_fill="white");thumb.save("thumbnail_long.jpg");return "thumbnail_long.jpg"
        except: return None

def seo_viral(topic,script):
    title1=f"I Tested {topic} For 7 Days - SHOCKING Truth!";title2=f"{topic} - Don't Buy Before Watching This! USA Girl Review";final_title=title1[:90] if len(topic)<30 else title2[:90]
    desc=f"STOP! Don't buy {topic} before watching this!\n\nBeautiful American girl explains {topic}.\n\n{script[:700]}...\n\nSubscribe: {CHANNEL_LINK}\n"
    tags=[topic.lower(),f"{topic.lower()} review","usa girl explains","don't buy",f"{topic.lower()} worth it","tech review 2026","viral tech"];return final_title,desc,tags

if __name__=="__main__":
    trending_topic=get_trending();full_script,sentences,topic_main=generate_viral_script(trending_topic);audio_files=tts_piper(full_script)
    if not audio_files: print("❌ No audio");exit(1)
    audio_clips=[]
    for p in audio_files:
        if os.path.exists(p) and os.path.getsize(p)>2000:
            try: audio_clips.append(AudioFileClip(p))
            except: pass
    if not audio_clips: print("❌ Audio empty");exit(1)
    final_audio=concatenate_audioclips(audio_clips)
    try: final_audio=final_audio.volumex(1.18)
    except: pass
    try:
        music_path=fetch_music_for_video(topic_main)
        if music_path and os.path.exists(music_path):
            bg=AudioFileClip(music_path).subclip(0,final_audio.duration);bg=bg.volumex(0.10);final_audio=CompositeAudioClip([final_audio,bg])
    except: pass
    if final_audio.duration>MAX_DURATION:
        try: final_audio=final_audio.subclip(0,MAX_DURATION)
        except: final_audio=final_audio.with_end(MAX_DURATION)
    print(f"Audio duration: {final_audio.duration/60:.2f} min - Topic: {topic_main} - FAST={FAST_MODE}")
    print("Downloading USA girl clips...");girl_clips=get_girl_clips();print(f"Girl clips: {len(girl_clips)}")
    print(f"Downloading B-roll for {topic_main}...");broll_clips=get_broll(topic_main);print(f"B-roll clips: {len(broll_clips)}")
    if not girl_clips and not broll_clips:
        print("⚠️ No Pexels clips - fallback");video_clip=ColorClip(size=(1920,1080),color=(15,15,35));video_clip=safe_duration(video_clip,final_audio.duration)
    else: video_clip=create_viral_video(girl_clips,broll_clips,sentences,final_audio.duration,topic_main)
    final_title,description,tags=seo_viral(topic_main,full_script);thumb=create_thumb_tech_burner_style(topic_main)
    seo_name=re.sub(r'[^a-z0-9]+','-',topic_main.lower()).strip('-')[:50];filename=f"{seo_name}-usa-girl-viral-review.mp4"
    final_video=safe_duration(video_clip,final_audio.duration);final_video=safe_audio(final_video,final_audio)
    print(f"Writing {filename}... FAST={FAST_MODE}")
    if FAST_MODE:
        final_video.write_videofile(filename, fps=24, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
    else:
        final_video.write_videofile(filename, fps=24, codec='libx264', audio_codec='aac', threads=2, logger=None)
    print(f"✅ DONE: {topic_main} - {filename}")
    try:
        from upload_youtube import upload_video
        upload_video(filename,final_title,description,tags,thumbnail_path=thumb)
        print("🚀 Upload success!")
    except Exception as e:
        print(f"Upload fail: {e}")
        try:
            from upload_youtube import upload_video
            upload_video(filename,final_title,description,tags)
        except Exception as e2: print(f"Second upload fail: {e2}")
