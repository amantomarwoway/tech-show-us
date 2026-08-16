import os,random,re,requests,subprocess,textwrap,warnings,sys
warnings.filterwarnings("ignore")
print("BOT START",flush=True)
try: import imageio_ffmpeg; os.environ['IMAGEIO_FFMPEG_EXE']=imageio_ffmpeg.get_ffmpeg_exe(); FF="ffmpeg"
except: FF="ffmpeg"
from moviepy.editor import *; from PIL import Image,ImageDraw,ImageFont; import numpy as np
W,H,T=1280,720,240; PEX=os.environ.get("PEXELS_API_KEY")

def fix(p):
 f=p.replace(".mp4","_f.mp4")
 try: subprocess.run([FF,"-y","-i",p,"-vf","scale=1280:720:force_original_aspect_ratio=decrease","-r","24","-c:v","libx264","-c:a","aac","-t","12",f],timeout=20,capture_output=True); os.remove(p); os.rename(f,p)
 except: pass
 return p
def safe(p,d=6):
 try: return VideoFileClip(p,verbose=False).subclip(0,d).resize((W,H)).without_audio().set_duration(d)
 except: fix(p); return ColorClip((W,H),color=(15,15,35),duration=d)

def viral():
 c=[]
 try:
  k=os.environ.get("YOUTUBE_API_KEY")
  for rg in ["US","GB","IN","DE","JP"]:
   try: j=requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode={rg}&videoCategoryId=28&maxResults=5&key={k}",timeout=10).json(); c+=[i['snippet']['title'][:70] for i in j.get('items',[])]
   except: pass
 except: pass
 try:
  for s in ["technology","gadgets","MachinePorn","space"]:
   try: j=requests.get(f"https://www.reddit.com/r/{s}/hot.json?limit=6",headers={"User-Agent":"Mozilla/5.0"},timeout=10).json(); c+=[p['data']['title'][:70] for p in j['data']['children']]
   except: pass
  import xml.etree.ElementTree as ET; r=requests.get("https://news.google.com/rss/search?q=tesla+iphone+fighter+excavator+satellite+missile+vs&hl=en-US&gl=US&ceid=US:en",timeout=10); root=ET.fromstring(r.content); c+=[x.text.split(" - ")[0][:70] for x in root.findall('.//item/title')[:12]]
 except: pass
 base=["Rocks vs Excavators","F-35 vs J-20","Satellite vs Missile","Excavator vs Bulldozer","Tesla Bot vs Human","Starship vs Falcon 9"]
 c=c+base; c=list(set([x for x in c if 10<len(x)<80])); f="used_long_titles.txt"; open(f,"a").close(); u=open(f).read().lower(); fr=[x for x in c if x.lower() not in u] or c; ch=random.choice(fr); open(f,"a").write(ch+"\n"); print(f"WORLDWIDE:{ch}",flush=True); return ch

def seo_pack(raw,l,r):
 yr="2025"
 titles=[f"{l} vs {r} - Who Will Win? Full Power Comparison {yr}",f"{l} vs {r} Ultimate Fight {yr} - Shocking Result!",f"{l} vs {r} Real Power Test - You Won't Believe Who Wins!"]
 title=random.choice(titles)
 tags=[f"{l} vs {r}",f"{l} vs {r} {yr}",f"{l} power",f"{r} power",f"{l} vs {r} who will win","ultimate showdown","power comparison","full comparison","real test","who will win",f"{l} {yr}",f"{r} {yr}","vs fight","machine fight","tech battle"][:15]
 desc=f"""{title}

In this video you will get 3 powerful things:
1. Real power of {l}
2. Hidden feature 99% miss
3. Final verdict - {l} vs {r} who wins?

We start with {l} extreme test, then {r} brutal power, then ultimate showdown {l} versus {r}.

00:00 What you will get
00:30 Let's Start - {l}
02:00 {r} Power
04:00 Ultimate VS Fight
05:30 Final Verdict

Thank you for watching! Please subscribe.
Let me know in comments how did you like video?

#{l.replace(' ','')} #{r.replace(' ','')} #vsfight #whowillwin #{yr} #tech

Subscribe: https://www.youtube.com/@YOUR_CHANNEL
"""
 return title,tags,desc

def tts(txt):
 files=[]
 for i,p in enumerate([txt[i:i+800] for i in range(0,len(txt),800)][:5]):
  ow=f"v{i}.wav"
  try: subprocess.run(f'echo "{p.replace(chr(34),"")}" |./piper/piper --model en_US-lessac-medium.onnx --output_file {ow} --length_scale 0.88',shell=True,timeout=40); files.append(ow)
  except: pass
 return files

def dl(q,pre):
 out=[]
 try:
  r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q)}&per_page=6&size=medium",headers={"Authorization":PEX} if PEX else {},timeout=12).json()
  for v in r.get('videos',[])[:4]:
   try: best=sorted(v['video_files'],key=lambda x:x['width'])[0]; p=f"{pre}_{random.randint(1000,9999)}.mp4"; open(p,'wb').write(requests.get(best['link'],timeout=20).content); out.append(fix(p))
   except: continue
 except: pass
 return out

def thumb(l,r):
 img=Image.new('RGB',(1280,720),(0,0,0)); d=ImageDraw.Draw(img)
 try: fb=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",85); fm=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",38)
 except: fb=fm=ImageFont.load_default()
 d.rectangle((0,0,640,720),fill=(200,20,20)); d.text((20,20),l.upper()[:18],fill="white",font=fm,stroke_width=3,stroke_fill="black"); d.text((20,80),"POWER",fill="yellow",font=fb,stroke_width=4,stroke_fill="black")
 d.rectangle((640,0,1280,720),fill=(20,50,200)); d.text((660,20),r.upper()[:18],fill="white",font=fm,stroke_width=3,stroke_fill="black"); d.text((660,80),"FIGHT",fill="yellow",font=fb,stroke_width=4,stroke_fill="black")
 d.ellipse((520,240,760,480),fill=(255,230,0),outline="red",width=10); d.text((560,300),"VS",fill="red",font=fb,stroke_width=5,stroke_fill="white")
 d.rectangle((0,600,1280,720),fill=(0,0,0)); d.text((20,620),"ULTIMATE SHOWDOWN - WHO WILL WIN?",fill="white",font=fm)
 img.save("thumb_fight.jpg","JPEG",quality=95); return "thumb_fight.jpg"

if __name__=="__main__":
 raw=viral()
 if "vs" in raw.lower(): a,b=[x.strip() for x in re.split(r'\s+vs\s+',raw,flags=re.I)][:2]
 else: a,b=raw,"Ultimate Rival"
 title,tags,desc=seo_pack(raw,a,b)
 full=f"""In this video you will get three things. Number one, the real power of {a} versus {b}. Number two, the hidden feature that ninety nine percent of people miss. Number three, my honest final verdict. Let's start. First, the power of {a}. This beast delivers extreme force and dominates the battlefield. The sound is insane and the performance is shocking. Second, the power of {b}. This machine is built for war and shows no mercy. It strikes with speed and precision. Finally, the ultimate showdown {a} versus {b}. Both machines collide and only one will survive. This fight will blow your mind. Thank you so much for watching. If you enjoyed this fight, please subscribe to our channel. Let me know in the comments how did you like the video."""
 sents=[x.strip() for x in full.split(".") if len(x.strip())>8]
 af=tts(full); acl=[AudioFileClip(p) for p in af if os.path.exists(p)]; audio=concatenate_audioclips(acl).subclip(0,T)
 clips=dl(a,"L")+dl(b,"R")+dl("explosion fight","F"); print(f"CLIPS {len(clips)}",flush=True)
 per=audio.duration/len(sents); v=[]
 for i,s in enumerate(sents):
  base=safe(clips[i%len(clips)],per) if clips else ColorClip((W,H),color=(20,10,30),duration=per)
  try: base=base.loop(duration=per).resize((W,H)).without_audio().set_duration(per)
  except: base=ColorClip((W,H),color=(20,10,30),duration=per).set_duration(per)
  cimg=Image.new('RGBA',(W,H),(0,0,0,0)); dr=ImageDraw.Draw(cimg,'RGBA')
  try: fnt=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
  except: fnt=ImageFont.load_default()
  dr.rectangle((0,520,W,H),fill=(0,0,0,180))
  for j,l in enumerate(textwrap.wrap(s.upper(),45)[:3]): dr.text((30,530+j*45),l,fill="white",font=fnt,stroke_width=3,stroke_fill="black")
  txt=ImageClip(np.array(cimg)).set_duration(per); v.append(CompositeVideoClip([base,txt],size=(W,H)).set_duration(per))
 final_vid=concatenate_videoclips(v).set_duration(audio.duration).set_audio(audio)
 fn=re.sub(r'[^a-z0-9]+','-',title.lower())[:40]+"-4k.mp4"
 final_vid.write_videofile(fn,fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="4000k",logger=None)
 th=thumb(a,b); print(f"DONE {fn}",flush=True)
 try:
  from upload_youtube import upload_video
  upload_video(fn,title,desc,tags,thumb_path=th)
 except Exception as e: print(f"UPLOAD {e}\nTITLE:{title}\nTAGS:{tags}\n{desc[:400]}")
