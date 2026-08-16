import os,random,re,requests,subprocess,warnings
warnings.filterwarnings("ignore")
from moviepy.editor import *
W,H,T=1080,1920,35
W8,H8=2160,3840
PEX=os.environ.get("PEXELS_API_KEY"); FF="ffmpeg"

def viral():
    base=["Excavator vs Bulldozer Fight","Big Machine Crash","Transformer Machine Transformation","Human to Robot Transformation","Fighter Jet Dogfight","Space Fight Satellite vs Missile","Powerful Gun vs Tank Fight","Ultra Machine Fight","Biggest Excavator Working","Monster Truck vs Bulldozer"]
    open("used_short_titles.txt","a").close(); u=open("used_short_titles.txt").read().lower(); f=[x for x in base if x.lower() not in u] or base; ch=random.choice(f); open("used_short_titles.txt","a").write(ch+"\n"); return ch

def seo(r):
    t=f"{r} in 8K - Real Machine Sound! #shorts"; return t[:95],[r,f"{r} 8K","8K shorts","machine fight"][:10],f"{r} 8K Real Sound #shorts #8K"

def tts(txt):
    fl=[]
    txt_safe=re.sub(r'[^A-Za-z0-9.,!?-]', ' ', txt)
    for i,ch in enumerate([txt_safe[i:i+480] for i in range(0,len(txt_safe),480)][:3]):
        ow=f"v{i}.wav"
        try:
            subprocess.run(f'./piper/piper --model en_US-lessac-medium.onnx --output_file {ow} --length_scale 0.92 < <(echo "{ch}")',shell=True,executable='/bin/bash',timeout=60)
            if os.path.exists(ow) and os.path.getsize(ow)>3000: fl.append(ow)
        except:continue
    if not fl:
        subprocess.run([FF,"-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","30","dummy.wav"],capture_output=True);return ["dummy.wav"]
    try:
        open("list.txt","w").write("\n".join([f"file '{f}'" for f in fl]))
        subprocess.run(f'{FF} -y -f concat -safe 0 -i list.txt -c copy temp.wav',shell=True,capture_output=True,timeout=30)
        subprocess.run(f'{FF} -y -i temp.wav -af loudnorm=I=-14:TP=-1:volume=1.5 final.wav',shell=True,capture_output=True,timeout=30)
        if os.path.exists("final.wav") and os.path.getsize("final.wav")>5000: return ["final.wav"]
    except:pass
    return [fl[0]]

def dl(q):
    o=[]; q_clean=re.sub(r'vs|Fight','',q,flags=re.I).strip()
    try:
        r=requests.get(f"https://api.pexels.com/videos/search?query={requests.utils.quote(q_clean)}&per_page=8&size=medium",headers={"Authorization":PEX} if PEX else {},timeout=15).json()
        for v in r.get('videos',[])[:5]:
            try: b=sorted(v['video_files'],key=lambda x:x['width'])[-1]; p=f"s_{random.randint(10000,99999)}.mp4"; open(p,'wb').write(requests.get(b['link'],timeout=20).content); o.append(p)
            except:continue
    except:pass
    return o

def make_ass(words, dur, path="cap.ass"):
    per=dur/len(words) if words else 1
    header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Word,DejaVu Sans,55,&H0000EBFF,&H000000FF,&H00000000,&HAA000000,-1,0,1,4,1,2,10,10,180,1
[Events]
Format: Layer, Start, End, Style, Text
"""
    lines=[header]
    for i,w in enumerate(words):
        s=i*per; e=s+per
        st=f"{int(s//3600)}:{int((s%3600)//60):02d}:{int(s%60):02d}.{int((s%1)*100):02d}"
        et=f"{int(e//3600)}:{int((e%3600)//60):02d}:{int(e%60):02d}.{int((e%1)*100):02d}"
        lines.append(f"Dialogue: 0,{st},{et},Word,{w.upper()}")
    open(path,"w",encoding="utf-8").write("\n".join(lines))
    return path

def up(vp,ti,de,ta):
    from google.oauth2.credentials import Credentials;from google.auth.transport.requests import Request;from googleapiclient.discovery import build;from googleapiclient.http import MediaFileUpload
    c=Credentials(None,refresh_token=os.environ.get("YT_REFRESH_TOKEN"),client_id=os.environ.get("YT_CLIENT_ID"),client_secret=os.environ.get("YT_CLIENT_SECRET"),token_uri="https://oauth2.googleapis.com/token",scopes=["https://www.googleapis.com/auth/youtube.upload"]);c.refresh(Request());yt=build("youtube","v3",credentials=c)
    b={"snippet":{"title":ti,"description":de,"tags":ta,"categoryId":"28"},"status":{"privacyStatus":"public"}}; m=MediaFileUpload(vp,chunksize=-1,resumable=True); r=yt.videos().insert(part="snippet,status",body=b,media_body=m); res=None
    while res is None: s,res=r.next_chunk()
    print(f"UP https://youtu.be/{res['id']}")

raw=viral(); title,tags,desc=seo(raw)
script=f"This {raw} in 8K with real machine sound is insane! Watch till the end. The {raw} delivers unbelievable 8K power. Its engine roars like a monster. You can hear the real machine sound. No machine can match its force. Who will win this ultra fight? Subscribe for daily 8K fights!"
words=script.split()
af=tts(script); audio=AudioFileClip(af[0])

# === FINAL FIX - DURATION = AUDIO DURATION ===
# pehle max 28 force karta tha, ab audio jitna hai utna hi video
dur = min(T, max(10, audio.duration - 0.1))
print(f"AUDIO {audio.duration} DUR {dur}")
audio = audio.subclip(0, dur)

clips=dl(raw); vc=[]
for p in clips:
    try: cl=VideoFileClip(p); cl=cl.resize(height=H).crop(x_center=cl.w/2, y_center=cl.h/2, width=W, height=H); vc.append(cl)
    except:continue
if not vc: vc=[ColorClip((W,H),color=(20,20,40),duration=dur)]

bg_video=concatenate_videoclips(vc,method="compose").loop(duration=dur).resize((W,H))

try: machine_audio=bg_video.audio.volumex(0.30).set_duration(dur) if bg_video.audio else None
except: machine_audio=None
final_audio=CompositeAudioClip([machine_audio, audio]).set_duration(dur) if machine_audio else audio

no_cap="no_cap.mp4"
CompositeVideoClip([bg_video],size=(W,H)).set_duration(dur).set_audio(final_audio).write_videofile(no_cap,fps=30,codec='libx264',audio_codec='aac',preset='ultrafast',threads=2,bitrate="40000k",logger=None)

ass=make_ass(words,dur)
final_fn='short-8K-'+re.sub(r'[^a-z0-9]+','-',title.lower()).strip('-')[:25]+".mp4"
subprocess.run(f'{FF} -y -i {no_cap} -vf "ass={ass},scale={W8}:{H8}:flags=lanczos" -c:a copy -b:v 80000k {final_fn}',shell=True,timeout=120)

up(final_fn,title,desc,tags)
