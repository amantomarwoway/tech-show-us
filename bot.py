import os,random,re,requests,subprocess,warnings
warnings.filterwarnings("ignore")
from moviepy.editor import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np
W,H,T=2160,3840,35; PEX=os.environ.get("PEXELS_API_KEY"); FF="ffmpeg"

def viral():
    base=["Excavator vs Bulldozer Fight","Big Machine Crash","Transformer Machine Transformation","Human to Robot Transformation","Fighter Jet Dogfight F-35 vs SU-57","Space Fight Satellite vs Missile","Powerful Gun vs Tank Fight","Ultra Machine Fight","Biggest Excavator Working","Monster Truck vs Bulldozer","Robot Transformation","Aeroplane Mid Air Fight","Gadgets Fight","Most Powerful Machine","Machine vs Human"]
    open("used_short_titles.txt","a").close(); u=open("used_short_titles.txt").read().lower(); f=[x for x in base if x.lower() not in u] or base; ch=random.choice(f); open("used_short_titles.txt","a").write(ch+"\n"); return ch

def seo(r):
    t=f"{r} in 8K Ultra HD - Insane Power! #shorts"; t=t[:95] if len(t)>95 else t
    tags=[r,f"{r} 8K","8K shorts","machine fight 8K","big machine crash","transformation 8K","fighter jet fight","ultra fight","powerful machine 8K","8K video"][:12]
    d=f"{r} in 8K Ultra HD 🔥\n\n#shorts #8K #machinefight #bigmachine #transformation\n\n{r} is insane in 8K!\nSubscribe for daily 8K fights!"
    return t,tags,d

def tts(txt):
    fl=[]
    for i,ch in enumerate([txt[i:i+500] for i in range(0,len(txt),500)][:3]):
        ow=f"v{i}.wav"; ch=ch.replace('"','')
        subprocess.run(f'echo "{ch}" |./piper/piper --model en_US-lessac-medium.onnx --output_file {ow} --length_scale 0.92',shell=True,timeout=60)
        if os.path.exists(ow) and os.path.getsize(ow)>2000: fl.append(ow)
    if not fl: subprocess.run([FF,"-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","30","dummy.wav"],capture_output=True);return ["dummy.wav"]
    open("list.txt","w").write("\n".join([f"file '{f}'" for f in fl])); subprocess.run(f'{FF} -y -f concat -safe 0 -i list.txt -af loudnorm=I=-14:TP=-1:volume=1.4 final.wav',shell=True,capture_output=True)
    return ["final.wav"] if os.path.exists("final.wav") else fl

def dl(q):
    o=[]
    try:
        r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=8&size=large",headers={"Authorization":PEX} if PEX else {},timeout=15).json()
        for v in r.get('videos',[])[:5]:
            try: b=sorted(v['video_files'],key=lambda x:x['width'])[-1]; p=f"s_{random.randint(1000,9999)}.mp4"; open(p,'wb').write(requests.get(b['link'],timeout=20).content); o.append(p)
            except:continue
    except:pass
    return o

def up(vp,ti,de,ta):
    from google.oauth2.credentials import Credentials;from google.auth.transport.requests import Request;from googleapiclient.discovery import build;from googleapiclient.http import MediaFileUpload
    c=Credentials(None,refresh_token=os.environ.get("YT_REFRESH_TOKEN"),client_id=os.environ.get("YT_CLIENT_ID"),client_secret=os.environ.get("YT_CLIENT_SECRET"),token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/youtube.upload"]);c.refresh(Request());yt=build("youtube","v3",credentials=c)
    b={"snippet":{"title":ti,"description":de,"tags":ta,"categoryId":"28"},"status":{"privacyStatus":"public"}}; m=MediaFileUpload(vp,chunksize=-1,resumable=True); r=yt.videos().insert(part="snippet,status",body=b,media_body=m); res=None
    while res is None: s,res=r.next_chunk()
    print(f"8K UP https://youtu.be/{res['id']}")

raw=viral(); title,tags,desc=seo(raw)
script=f"This {raw} in 8K Ultra HD is insane! Watch till the end. The {raw} delivers unbelievable 8K power. Its engine roars like a monster. No machine can match its force. It crushes everything in 8K. The speed is shocking. The power is unreal. This is the most powerful machine fight ever in 8K. Who will win this ultra 8K fight? The result will blow your mind in 8K. Subscribe for daily 8K machine fights!"
words=script.split(); af=tts(script); audio=AudioFileClip(af[0]); dur=min(T, max(28, audio.duration - 0.15)); audio=audio.subclip(0,dur)
clips=dl(raw)+dl(raw.split(" vs ")[0] if " vs " in raw else raw)
vc=[]
for p in clips:
    try: cl=VideoFileClip(p).without_audio(); cl=cl.resize(height=H).crop(x_center=cl.w/2, y_center=cl.h/2, width=W, height=H); vc.append(cl)
    except:pass
if not vc: vc=[ColorClip((W,H),color=(20,20,40),duration=5)]
bg=concatenate_videoclips(vc,method="compose").loop(duration=dur).resize((W,H))
per=dur/len(words); caps=[]
for i,w in enumerate(words):
    img=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(img,'RGBA')
    try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",160)
    except: fnt=ImageFont.load_default()
    d.rectangle((0,H//2-150,W,H//2+150),fill=(0,0,0,170)); d.text((W//2,H//2),w.upper(),fill="#FFEB00",font=fnt,anchor="mm",stroke_width=14,stroke_fill="black")
    caps.append(ImageClip(np.array(img)).set_start(i*per).set_duration(per))
final=CompositeVideoClip([bg]+caps,size=(W,H)).set_duration(dur).set_audio(audio)
fn='short-8K-'+re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')[:25]+".mp4"
final.write_videofile(fn,fps=30,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="80000k",logger=None)
up(fn,title,desc,tags)
