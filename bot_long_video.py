import os,random,re,requests,subprocess,warnings
warnings.filterwarnings("ignore")
from moviepy.editor import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np
W,H,T=1280,720,240; PEX=os.environ.get("PEXELS_API_KEY"); FF="ffmpeg"

def viral():
 c=[];base=["Rocks vs Excavators","F-35 vs J-20","AIRCRAFT SPEED COMPARISON","Excavator vs Bulldozer","Tesla Bot vs Human","Satellite vs Missile"]
 c=base;open("used_long_titles.txt","a").close();u=open("used_long_titles.txt").read().lower();fr=[x for x in c if x.lower() not in u] or c;ch=random.choice(fr);open("used_long_titles.txt","a").write(ch+"\n");return ch

def seo(l,r):
 title=f"{l} vs {r} - Ultimate Power Comparison 2025";tags=[f"{l} vs {r}",f"{l} power",f"{r} power","who will win"][:12]
 desc=f"{title}\n\n1. Power of {l}\n2. Power of {r}\n3. Final verdict\n\nThanks! Subscribe! Comment how did you like video?\n";return title,tags,desc

def tts_pro(txt):
 files=[]; chunks=[txt[i:i+600] for i in range(0,len(txt),600)][:5]
 for i,ch in enumerate(chunks):
  ow=f"v{i}.wav"; ch=ch.replace('"','').replace("'",'')
  subprocess.run(f'echo "{ch}" |./piper/piper --model en_US-lessac-medium.onnx --output_file {ow} --length_scale 0.86',shell=True,timeout=60)
  if os.path.exists(ow) and os.path.getsize(ow)>3000: files.append(ow)
 if files:
  concat="|".join(files); subprocess.run(f'{FF} -y -i "concat:{concat}" -af loudnorm=I=-16:TP=-1.5:LRA=11,highpass=f=75,volume=1.3 final.wav',shell=True,capture_output=True)
  if os.path.exists("final.wav"): return ["final.wav"]
  return files
 subprocess.run([FF,"-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","60","dummy.wav"],capture_output=True);return ["dummy.wav"]

def dl(q):
 out=[]
 try:
  r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=6&size=medium",headers={"Authorization":PEX} if PEX else {},timeout=15).json()
  for v in r.get('videos',[])[:5]:
   try:best=sorted(v['video_files'],key=lambda x:x['width'])[-1];p=f"c_{random.randint(1000,9999)}.mp4";open(p,'wb').write(requests.get(best['link'],timeout=20).content);out.append(p)
   except:continue
 except:pass
 return out

def thumb_pro(l,r):
    bg="bg.jpg"; query=f"{l} {r}"
    try:
        res=requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape",headers={"Authorization":PEX} if PEX else {},timeout=10).json()
        url=res['photos'][0]['src']['large2x']; open(bg,'wb').write(requests.get(url,timeout=12).content)
        img=Image.open(bg).convert("RGB").resize((1280,720), Image.LANCZOS)
    except: img=Image.new('RGB',(1280,720),(18,28,58))
    overlay=Image.new('RGBA',(1280,720),(0,0,0,75)); img=Image.alpha_composite(img.convert('RGBA'),overlay).convert('RGB'); d=ImageDraw.Draw(img)
    try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",86)
    except: fb=ImageFont.load_default()
    main=f"{l.upper()} vs {r.upper()}"; sub="SPEED COMPARISON" if any(x in (l+r).lower() for x in ["aircraft","f-35","jet","speed"]) else "POWER COMPARISON"; full_text=f"{main}\n{sub}"
    for off in [(5,5)]: d.text((640+off[0], 170+off[1]), full_text, fill="black", font=fb, anchor="mm", align="center")
    d.text((640,170), full_text, fill="white", font=fb, anchor="mm", align="center", stroke_width=7, stroke_fill="black")
    img.save("thumb.jpg","JPEG",quality=98); return "thumb.jpg"

def upload(vp,title,desc,tags,tp):
 from google.oauth2.credentials import Credentials;from google.auth.transport.requests import Request;from googleapiclient.discovery import build;from googleapiclient.http import MediaFileUpload
 creds=Credentials(None,refresh_token=os.environ.get("YT_REFRESH_TOKEN"),client_id=os.environ.get("YT_CLIENT_ID"),client_secret=os.environ.get("YT_CLIENT_SECRET"),token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/youtube.upload"]);creds.refresh(Request());yt=build("youtube","v3",credentials=creds)
 body={"snippet":{"title":title[:95],"description":desc,"tags":tags,"categoryId":"28"},"status":{"privacyStatus":"public"}};media=MediaFileUpload(vp,chunksize=-1,resumable=True);req=yt.videos().insert(part="snippet,status",body=body,media_body=media);resp=None
 while resp is None:status,resp=req.next_chunk()
 vid=resp["id"];
 try:yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(tp,mimetype="image/jpeg")).execute()
 except:pass
 print(f"UPLOADED https://youtu.be/{vid}")

raw=viral(); a,b=[x.strip() for x in re.split(r'\s+vs\s+',raw,flags=re.I)][:2] if "vs" in raw.lower() else (raw,"Rival")
title,tags,desc=seo(a,b)
script=f"In this video you will discover three insane things. First the real power of {a}. Second the hidden feature of {b} that ninety nine percent people miss. And third the final verdict who will win. Let's start. The {a} is an absolute beast. It delivers extreme force and its speed is shocking. Now the {b}. This machine is built for war. It strikes with incredible velocity. Now the ultimate showdown {a} versus {b}. Only one can survive. Thank you so much for watching. Please subscribe and let me know in the comments how did you like the video."
words=script.split()
af=tts_pro(script); audio=AudioFileClip(af[0]).subclip(0,T)
clips=dl(f"{a} {b}")+dl(a)
vclips=[]
for p in clips:
 try:vclips.append(VideoFileClip(p).resize((W,H)).without_audio())
 except:pass
if not vclips: vclips=[ColorClip((W,H),color=(20,20,40),duration=5)]
bg_video=concatenate_videoclips(vclips,method="compose").loop(duration=audio.duration).resize((W,H))
per=audio.duration/len(words); txts=[]
for i,w in enumerate(words):
 cimg=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(cimg,'RGBA')
 try:fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",54)
 except:fnt=ImageFont.load_default()
 dr.rectangle((0,590,W,720),fill=(0,0,0,150)); dr.text((W//2,645),w.upper(),fill="#FFEB00",font=fnt,anchor="mm",stroke_width=5,stroke_fill="black")
 txts.append(ImageClip(np.array(cimg)).set_start(i*per).set_duration(per))

final=CompositeVideoClip([bg_video]+txts,size=(W,H)).set_duration(audio.duration).set_audio(audio)

# FIX - SAFE FILENAME (ye error fix karta hai)
safe_title=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
if not safe_title or safe_title[0].isdigit() or safe_title.startswith('-'): safe_title='vid-'+safe_title
fn=safe_title[:38]+".mp4"

final.write_videofile(fn,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="5000k",logger=None)
th=thumb_pro(a,b)
upload(fn,title,desc,tags,th)
