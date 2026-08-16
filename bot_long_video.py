import os,random,re,requests,subprocess,warnings
warnings.filterwarnings("ignore")
from moviepy.editor import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np
W,H,T=1280,720,240; PEX=os.environ.get("PEXELS_API_KEY"); FF="ffmpeg"

def viral():
 base=["Rocks vs Excavators","F-35 vs J-20","AIRCRAFT SPEED COMPARISON","Excavator vs Bulldozer","Tesla Bot vs Human","Satellite vs Missile","iPhone 16 vs Samsung S24","Tank vs Missile"]
 c=base;open("used_long_titles.txt","a").close();u=open("used_long_titles.txt").read().lower();fr=[x for x in c if x.lower() not in u] or c;ch=random.choice(fr);open("used_long_titles.txt","a").write(ch+"\n");return ch

def seo(l,r):
 title=f"{l} vs {r} - Ultimate Power & Speed Comparison 2025";tags=[f"{l} vs {r}",f"{l} power",f"{r} power","who will win","power comparison","speed comparison"][:12]
 desc=f"{title}\n\nDiscover power of {l} and {r}\n\nThanks! Subscribe!\n";return title,tags,desc

def tts_pro(txt):
 files=[]
 # 10 chunks = 4 min voice
 chunks=[txt[i:i+600] for i in range(0,len(txt),600)][:10]
 for i,ch in enumerate(chunks):
  ow=f"v{i}.wav"; ch=ch.replace('"','').replace("'",'').replace('\n',' ')
  subprocess.run(f'echo "{ch}" |./piper/piper --model en_US-lessac-medium.onnx --output_file {ow} --length_scale 0.88 --noise_scale 0.6',shell=True,timeout=90)
  if os.path.exists(ow) and os.path.getsize(ow)>3000: files.append(ow)
 if not files:
  subprocess.run([FF,"-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","60","dummy.wav"],capture_output=True);return ["dummy.wav"]
 open("list.txt","w").write("\n".join([f"file '{f}'" for f in files]))
 subprocess.run(f'{FF} -y -f concat -safe 0 -i list.txt -af loudnorm=I=-16:TP=-1.5:LRA=11,highpass=f=75,volume=1.3 final.wav',shell=True,capture_output=True)
 return ["final.wav"] if os.path.exists("final.wav") else files

def dl(q):
 out=[]
 try:
  r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=8&size=medium",headers={"Authorization":PEX} if PEX else {},timeout=15).json()
  for v in r.get('videos',[])[:6]:
   try:best=sorted(v['video_files'],key=lambda x:x['width'])[-1];p=f"c_{random.randint(1000,9999)}.mp4";open(p,'wb').write(requests.get(best['link'],timeout=20).content);out.append(p)
   except:continue
 except:pass
 return out

def thumb_pro(l,r):
    bg="bg.jpg"; query=f"{l} {r} jet" if any(x in (l+r).lower() for x in ["f-35","jet","aircraft","speed"]) else f"{l} {r} machine"
    try:
        res=requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape",headers={"Authorization":PEX} if PEX else {},timeout=10).json()
        url=res['photos'][0]['src']['large2x']; open(bg,'wb').write(requests.get(url,timeout=12).content)
        img=Image.open(bg).convert("RGB").resize((1280,720), Image.LANCZOS)
    except: img=Image.new('RGB',(1280,720),(18,28,58))
    overlay=Image.new('RGBA',(1280,720),(0,0,0,75)); img=Image.alpha_composite(img.convert('RGBA'),overlay).convert('RGB'); d=ImageDraw.Draw(img)
    try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",86)
    except: fb=ImageFont.load_default()
    main=f"{l.upper()} vs {r.upper()}"; sub="SPEED COMPARISON" if any(x in (l+r).lower() for x in ["aircraft","f-35","jet","speed"]) else "POWER COMPARISON"; full_text=f"{main}\n{sub}"
    d.text((640,170), full_text, fill="white", font=fb, anchor="mm", align="center", stroke_width=7, stroke_fill="black")
    img.save("thumb.jpg","JPEG",quality=98); return "thumb.jpg"

def upload(vp,title,desc,tags,tp):
 from google.oauth2.credentials import Credentials;from google.auth.transport.requests import Request;from googleapiclient.discovery import build;from googleapiclient.http import MediaFileUpload
 creds=Credentials(None,refresh_token=os.environ.get("YT_REFRESH_TOKEN"),client_id=os.environ.get("YT_CLIENT_ID"),client_secret=os.environ.get("YT_CLIENT_SECRET"),token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/youtube.upload"]);creds.refresh(Request());yt=build("youtube","v3",credentials=creds)
 body={"snippet":{"title":title[:95],"description":desc,"tags":tags,"categoryId":"28"},"status":{"privacyStatus":"public"}};media=MediaFileUpload(vp,chunksize=-1,resumable=True);req=yt.videos().insert(part="snippet,status",body=body,media_body=media);resp=None
 while resp is None:status,resp=req.next_chunk()
 vid=resp["id"]; yt.thumbnails().set(videoId=vid,media_body=MediaFileUpload(tp,mimetype="image/jpeg")).execute(); print(f"UPLOADED https://youtu.be/{vid}")

raw=viral(); a,b=[x.strip() for x in re.split(r'\s+vs\s+',raw,flags=re.I)][:2] if "vs" in raw.lower() else (raw,"Rival")
title,tags,desc=seo(a,b)

# 4 MINUTE LONG SCRIPT - 700 WORDS
script=f"""In this video you will discover three insane things about {a} versus {b}. First the real top speed and power of {a}. Second the hidden feature of {b} that ninety nine percent people miss. And third the final verdict who will win this ultimate showdown.

Let's start with number one, the power of {a}. The {a} is an absolute beast. It is engineered for extreme performance. It delivers incredible force and its engine produces a thunderous sound. When it moves, the ground shakes. Its design is aerodynamic and built for domination. Experts say its top speed can cross limits that normal machines cannot even imagine. Its fuel efficiency and power ratio is unmatched. The technology inside {a} is from the future. Many people think they know about {a}, but the real power is hidden. It has a secret mode that activates only in extreme conditions. That mode makes it ten times more powerful.

Now number two, the power of {b}. The {b} is built for war. It strikes with incredible velocity and precision. Its build quality is solid like a tank. It can operate in the toughest conditions. Whether it is desert, snow, or rain, the {b} never stops. Its engine is more powerful than ten normal engines combined. The sound of {b} is so loud that you can hear it from miles away. It is a true monster on the battlefield. The {b} has been tested in real world battles and it has never failed. Its armor is unbreakable and its speed is unbelievable. People fear the {b} because of its raw power.

Now the most awaited part, the ultimate showdown, {a} versus {b}. Imagine both machines are standing face to face. On the left side, the {a} roars with full power. On the right side, the {b} fires up its engine. The crowd is silent. The atmosphere is tense. The fight begins. The {a} attacks first with its incredible speed. It moves so fast that you cannot even see it. But the {b} defends and counter attacks with double force. Both machines collide. Sparks fly everywhere. Smoke fills the air. The ground trembles. This is not just a fight, this is a war of titans. Only one can survive this epic battle.

Who do you think will win? The {a} with its speed and agility, or the {b} with its raw power and strength? Comment your winner below.

In my honest final verdict, both machines are powerful, but if we talk about pure power, real world domination, and future technology, the winner is shocking. The result will blow your mind.

Thank you so much for watching this ultimate comparison of {a} versus {b}. If you enjoyed this video, please subscribe to our channel, like this video, and let me know in the comments how did you like the video and who is your winner, {a} or {b}. See you in the next epic battle.
"""

words=script.split(); print(f"TOTAL WORDS {len(words)} - TARGET 4 MIN")
af=tts_pro(script)
audio=AudioFileClip(af[0]); dur=max(1, audio.duration - 0.2); audio=audio.subclip(0, dur)
print(f"AUDIO DURATION {dur:.1f} sec = {dur/60:.1f} min")

clips=dl(f"{a} {b}")+dl(a)+dl(b)
vclips=[]
for p in clips:
 try:vclips.append(VideoFileClip(p).resize((W,H)).without_audio())
 except:pass
if not vclips: vclips=[ColorClip((W,H),color=(20,20,40),duration=5)]
bg_video=concatenate_videoclips(vclips,method="compose").loop(duration=dur).resize((W,H))

per=dur/len(words); txts=[]
for i,w in enumerate(words):
 cimg=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(cimg,'RGBA')
 try:fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",54)
 except:fnt=ImageFont.load_default()
 dr.rectangle((0,590,W,720),fill=(0,0,0,150)); dr.text((W//2,645),w.upper(),fill="#FFEB00",font=fnt,anchor="mm",stroke_width=5,stroke_fill="black")
 txts.append(ImageClip(np.array(cimg)).set_start(i*per).set_duration(per))

final=CompositeVideoClip([bg_video]+txts,size=(W,H)).set_duration(dur).set_audio(audio)
safe_title=re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')
if not safe_title: safe_title='video'
fn='vid-'+safe_title[:35]+".mp4"
final.write_videofile(fn,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="5000k",logger=None)
th=thumb_pro(a,b)
upload(fn,title,desc,tags,th)
