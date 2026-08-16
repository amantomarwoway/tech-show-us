import random, requests, re, os, time, textwrap, subprocess, xml.etree.ElementTree as ET, gc, warnings
warnings.filterwarnings("ignore")
try: import imageio_ffmpeg; os.environ['IMAGEIO_FFMPEG_EXE']=imageio_ffmpeg.get_ffmpeg_exe(); FFMPEG=imageio_ffmpeg.get_ffmpeg_exe()
except: FFMPEG="ffmpeg"
try: from moviepy.editor import *
except: from moviepy import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W,H,T=3840,2160,240
PEXELS=os.environ.get("PEXELS_API_KEY")
BANNED=["tyrod","taylor","mariners","yankees","oreo","brad pitt","pushpa","jethalal","tmkoc","bhabi","kapil","bigg boss","football","cricket","movie","election","biden","trump","modi"]
TECH=["iphone","apple","samsung","pixel","phone","headphone","earbuds","watch","laptop","gadget","airpods","excavator","crane","bulldozer","jcb","caterpillar","construction","tank","fighter","robot","tesla","humanoid","ai","processor","chip","gpu"]
GIRL_Q=["beautiful american woman emotional talking","american girl shocked facial expression close up","beautiful blonde woman crying happy","american woman explaining with hand gestures"]

def sd(c,d):
    try: return c.set_duration(d)
    except: return c.with_duration(d) if hasattr(c,'with_duration') else c
def sa(c,a):
    try: return c.set_audio(a)
    except: return c.with_audio(a) if hasattr(c,'with_audio') else c
def sna(c):
    try: return c.without_audio()
    except: return c.with_audio(None)
def sr(c,w=W):
    try: return c.resize(width=w)
    except: return c.resized(width=w) if hasattr(c,'resized') else c
def clean(t): return re.sub(r'\s+',' ',re.sub(r'[^a-zA-Z0-9.,!?$% ]',' ',re.sub(r'http\S+|www\S+|\.com','',t,flags=re.I))).strip()

def fix(p):
    f=p.replace(".mp4","_f.mp4")
    try:
        subprocess.run([FFMPEG,"-y","-err_detect","ignore_err","-fflags","+discardcorrupt","-i",p,"-c:v","libx264","-pix_fmt","yuv420p","-vf","scale=1280:720:force_original_aspect_ratio=decrease","-c:a","aac","-movflags","+faststart",f],timeout=30,capture_output=True)
        if os.path.exists(f) and os.path.getsize(f)>50000: os.remove(p); os.rename(f,p)
        else:
            try: os.remove(f)
            except: pass
    except: pass
    return p

def safe_clip(path,d=5):
    for _ in range(3):
        try:
            if not os.path.exists(path) or os.path.getsize(path)<50000: raise Exception()
            cl=VideoFileClip(path,verbose=False)
            if cl.reader is None: cl.close(); raise Exception()
            cl.get_frame(0); return cl
        except: fix(path); time.sleep(0.5)
    return sd(ColorClip(size=(W,H),color=(15,15,35)),d)

def get_trends():
    c=[]
    try:
        from pytrends.request import TrendReq
        tr=TrendReq(hl='en-US',tz=360).trending_searches(pn='united_states')[0].tolist()
        c+=[t for t in tr if not any(b in t.lower() for b in BANNED) and len(t)<100 and (any(k in t.lower() for k in TECH) or len(t.split())<=5)]
    except: pass
    try:
        k=os.environ.get("YOUTUBE_API_KEY","") or os.environ.get("YT_CLIENT_ID","")
        if k:
            d=requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=US&videoCategoryId=28&maxResults=25&key={k}",timeout=15).json()
            c+=[i['snippet']['title'][:60] for i in d.get('items',[]) if 10<len(i['snippet']['title'])<90 and not any(b in i['snippet']['title'].lower() for b in BANNED)]
    except: pass
    try:
        for sub in ["technology","gadgets"]:
            d=requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=25",headers={"User-Agent":"Mozilla/5.0"},timeout=15).json()
            for p in d['data']['children']:
                t=re.sub(r'\s+',' ',re.sub(r'[^a-zA-Z0-9 ]',' ',p['data']['title'])).strip()
                if 10<len(t)<90 and any(k in t.lower() for k in TECH) and not any(b in t.lower() for b in BANNED): c.append(t[:60])
    except: pass
    try:
        for url in ["https://news.google.com/rss/search?q=technology+gadget+review+2026&hl=en-US&gl=US&ceid=US:en","https://news.google.com/rss/search?q=iphone+samsung+tesla+robot+tech&hl=en-US&gl=US&ceid=US:en"]:
            r=requests.get(url,timeout=15); root=ET.fromstring(r.content)
            for it in root.findall('.//item/title')[:15]:
                t=it.text.split(' - ')[0]
                if 10<len(t)<90 and any(k in t.lower() for k in TECH) and not any(b in t.lower() for b in BANNED): c.append(t[:60])
    except: pass
    c=list(set([x for x in c if len(x)>10]))
    if not c: return random.choice(["iPhone 16 Pro Max Review","Tesla Bot 2026","Caterpillar D9 Bulldozer Power"])
    f="used_long_titles.txt"; open(f,"a").close(); used=[l.lower() for l in open(f).read().splitlines()]
    fresh=[x for x in c if x.lower() not in used] or c
    ch=random.choice(fresh); open(f,"a").write(ch+"\n"); print(f"🎯 {ch}"); return ch

def gen_script(t):
    m=t.replace(" - "," ").strip()
    s=f"""Oh my god guys! You will not believe what happened when I tested {m} for 7 days! I am literally shaking right now because what I found shocked me completely! When I first saw {m}, I thought wow this looks amazing, 99,000 dollars, 600 horsepower, big machine, but is it really worth that much money? I still remember day one, I was so nervous, my hands were shaking when I started {m} for the first time. The sound was so loud, like a beast roaring, 600 horsepower engine, oh my god! My heart was racing so fast. On day two, I saw how this beast lifts 50 tons like it is nothing! I literally screamed with excitement! Day three was most emotional day, I was working in Texas, hot sun, but {m} did not stop. It worked 5 hours non stop and completed 3 days work! I started crying tears of joy. But wait, there is hidden secret that nobody tells you about {m}. 99 percent miss this hidden feature. Secret fuel saving mode saves 30 percent fuel! Now let me be honest, I love {m} but 3 things broke my heart. First, price too high, 99,000 dollars. Second, maintenance expensive. Third, need special training. But after 7 days, final verdict is this. If you have big projects, if you want to save time, if you want to feel power, then {m} is for you. So tell me in comments, would you buy {m} for 99,000 dollars? If this 4 minute emotional review touched your heart, please subscribe!"""
    full=clean(s); sens=[x.strip() for x in full.split('.') if len(x.strip())>25]
    if len(sens)>8: cs=len(sens)//8; sens=[". ".join(sens[i*cs:(i*cs+cs if i<7 else len(sens))]) for i in range(8)]
    return full,sens[:8],m

def tts(txt):
    wds=txt.split(); cs=max(1,len(wds)//4); chs=[' '.join(wds[:cs]),' '.join(wds[cs:cs*2]),' '.join(wds[cs*2:cs*3]),' '.join(wds[cs*3:])]
    chs=[c for c in chs if len(c)>20]; files=[]; model="en_US-lessac-medium.onnx"; has=os.path.exists(model)
    for i,c in enumerate(chs):
        ow=f"voice_{i}.wav"; om=f"voice_{i}.mp3"; ok=False
        if has:
            try:
                subprocess.run(f'echo "{c.replace(chr(34),"").replace(chr(96),"")}" | piper --model {model} --output_file {ow} --length_scale 0.92',shell=True,timeout=80,capture_output=True)
                if os.path.exists(ow) and os.path.getsize(ow)>2000: files.append(ow); ok=True
            except: pass
        if not ok:
            try: from gtts import gTTS; gTTS(text=c[:4000],lang='en',tld='us').save(om); files.append(om)
            except: pass
    return files

def dl(q,pre):
    out=[]
    try:
        r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=15&orientation=landscape&size=medium",headers={"Authorization":PEXELS} if PEXELS else {},timeout=15)
        if r.status_code!=200: return []
        vs=r.json().get('videos',[]); random.shuffle(vs)
        for v in vs[:5]:
            try:
                fs=sorted(v['video_files'],key=lambda x:x['width'],reverse=True); cand=[f for f in fs if 720<=f['width']<=1280]
                if not cand: continue
                best=random.choice(cand[:2]); p=f"{pre}_{random.randint(1000,9999)}.mp4"
                open(p,"wb").write(requests.get(best['link'],stream=True,timeout=90).content)
                if os.path.getsize(p)<80000: os.remove(p); continue
                out.append(fix(p))
                if len(out)>=2: break
            except: continue
    except: pass
    return out

def make_vid(sents,dur,topic,g,b):
    final=[]; per=max(28.0,min(dur/len(sents) if sents else 30,32.0)); allc=g+b or g
    for i,sent in enumerate(sents[:8]):
        try:
            p=allc[i%len(allc)] if allc else None; gc=safe_clip(p,per) if p and os.path.exists(p) else sd(ColorClip(size=(W,H),color=(25,10,40)),per)
            gc=sna(gc)
            if gc.duration<per:
                try: gc=gc.loop(duration=per)
                except: gc=sd(gc,per)
            try: gc=gc.subclip(0,per)
            except: pass
            gc=sd(sr(gc,W),per)
            try: gc=gc.crop(x_center=gc.w/2,y_center=gc.h*0.42,width=W,height=H)
            except: pass
            img=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(img,'RGBA')
            try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.022)); fs=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",int(W*0.016))
            except: fb=fs=ImageFont.load_default()
            if i==0: dr.rounded_rectangle((30,30,950,90),radius=15,fill=(255,0,80,230)); dr.text((50,40),"TRENDING NOW - EMOTIONAL - 4K - 4 SOURCES",fill="white",font=fs)
            else: emos=["SHOCKED! 😱","AMAZING! 🤩","SO HAPPY! 😭","WOW! 🙌","EMOTIONAL! ❤️","UNBELIEVABLE! 😲","LOVE IT! 🥰","FINAL! 💖"]; dr.rounded_rectangle((30,30,750,80),radius=12,fill=(0,200,255,220)); dr.text((40,38),f"{emos[i%len(emos)]} - {topic[:20].upper()}",fill="black",font=fs)
            dr.rectangle((0,int(H*0.70),W,H),fill=(0,0,0,200)); y=int(H*0.73)
            for line in textwrap.wrap(sent,width=50)[:4]: dr.text((40,y),line.upper(),fill="white",font=fb,stroke_width=4,stroke_fill="black"); y+=int(H*0.05)
            txt=ImageClip(np.array(img)); txt=sd(txt,per); comp=CompositeVideoClip([gc,txt],size=(W,H)); comp=sd(comp,per)
            tmp=f"temp_{i}.mp4"; comp.write_videofile(tmp,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None,verbose=False); final.append(tmp)
            try: comp.close(); gc.close()
            except: pass
        except Exception as e: print(f"Seg {i} {e}"); continue
    if not final: return sd(ColorClip(size=(W,H),color=(25,10,40)),dur),[]
    cl=[safe_clip(f,per) for f in final]; fv=concatenate_videoclips(cl,method="compose"); fv=sd(fv,T); return fv,final

if __name__=="__main__":
    top=get_trends(); full,sents,main=gen_script(top)
    afs=tts(full)
    if not afs: exit(1)
    acl=[AudioFileClip(p) for p in afs if os.path.exists(p) and os.path.getsize(p)>1000]
    if not acl: exit(1)
    fa=concatenate_audioclips(acl); fa=fa.subclip(0,T) if fa.duration>T else fa; fa=sd(fa,T)
    g=[]; [g.extend(dl(q,"emotional_girl")) for q in GIRL_Q if len(g)<8]
    b=dl(f"{main.split()[0]} cinematic bokeh","creative_bg")
    allc=g+b; vc,tm=make_vid(sents,fa.duration,main,g,b) if len(allc)>=2 else (sd(ColorClip(size=(W,H),color=(25,10,40)),fa.duration),[])
    fv=sd(sa(sd(vc,T),fa),T); fn=re.sub(r'[^a-z0-9]+','-',main.lower()).strip('-')[:40]+"-emotional-single-4min-4k.mp4"
    fv.write_videofile(fn,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="8000k",logger=None)
    for x in tm+allc:
        try: os.remove(x)
        except: pass
    print(f"✅ DONE {fn}")
    try: from upload_youtube import upload_video; upload_video(fn,f"{main} Made Me Cry! Emotional 4 Minute Story!",f"{full[:500]}",[main.lower(),"emotional","viral"])
    except Exception as e: print(f"Upload {e}")
