import os, random, requests, tempfile, re, wave
from moviepy.editor import *
from piper import PiperVoice
from PIL import Image, ImageDraw, ImageFont
import PIL.Image

# FIX FOR PILLOW 10+
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-amy-medium.onnx"; cp="models/en_US-amy-medium.onnx.json"
    if not os.path.exists(mp):
        print("Downloading Piper model...")
        open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
        open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
    return PiperVoice.load(mp, cp)

def get_stock_clips(q, num=6):
    key=os.getenv("PEXELS_API_KEY")
    if not key:
        return [ColorClip((1080,1920),color=(20,20,60),duration=2) for _ in range(num)]
    try:
        h={"Authorization":key}
        # q is title, search related clips
        sq=" ".join(re.findall(r'\w+',str(q))[:3]) or "technology news"
        url=f"https://api.pexels.com/videos/search?query={sq}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url,headers=h,timeout=15).json()
        clips=[]
        for v in res.get('videos',[])[:num]:
            link = sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
            tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".mp4")
            tmp.write(requests.get(link,timeout=20).content); tmp.close()
            clips.append(VideoFileClip(tmp.name).resize(height=1920).set_position('center').without_audio())
        if clips: 
            print(f"Fetched {len(clips)} clips related to: {sq}")
            return clips
    except Exception as e:
        print(f"Pexels error {e}")
    return [ColorClip((1080,1920),color=(20,20,60),duration=2) for _ in range(num)]

def word_clip(word, dur):
    # PERFECT VIRAL CAPTION - Yellow, medium size, slightly above bottom centre
    img=Image.new('RGBA',(1080,300),(0,0,0,0))
    d=ImageDraw.Draw(img)
    try:
        # medium size = 70
        f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",70)
    except:
        f=ImageFont.load_default()
    # Yellow colour #FFEB3B with thick black stroke for visibility
    d.text((540,150),word,font=f,fill="#FFEB3B",stroke_width=7,stroke_fill="black",anchor="mm")
    p=f"temp/c_{random.randint(1,9999999)}.png"
    os.makedirs("temp",exist_ok=True)
    img.save(p)
    # thoda upar - 0.72 is perfect for Shorts (niche centre se thoda upar)
    return ImageClip(p).set_duration(dur).set_position(('center',0.72),relative=True)

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    if isinstance(script_data, dict):
        script_text=script_data.get('full_script','') or script_data.get('script','') or ""
        title=script_data.get('title','USA Tech Breaking News')
    else:
        script_text=str(script_data)
        title=script_text[:40]

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)

    print("1. Generating Piper TTS American...")
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    with wave.open(audio_path,"wb") as wav:
        first=True
        for ch in voice.synthesize(script_text):
            if first:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(ch.sample_rate); first=False
            wav.writeframes(ch.audio_int16_bytes)
    audio=AudioFileClip(audio_path)
    total=audio.duration+0.3
    # SHORT VIDEO - max 32 sec for YouTube Shorts
    if total > 32:
        total = 32
        audio = audio.subclip(0,32)
    print(f"Audio duration: {total} - SHORT VIDEO")

    print("2. Fetching many clips related to script...")
    stocks=get_stock_clips(title,6)
    final_clips=[]
    left=total
    i=0
    while left>0.1:
        c=stocks[i%len(stocks)]
        max_d = min(1.8, c.duration-0.2, left)
        if max_d < 0.5: max_d = left
        dur = max_d
        start = 0 if c.duration <= dur else random.uniform(0, c.duration-dur)
        final_clips.append(c.subclip(start, start+dur).set_duration(dur))
        left-=dur
        i+=1
    video=concatenate_videoclips(final_clips, method="compose").set_duration(total)
    video=video.resize((1080,1920))

    print("3. Creating captions - yellow, medium, word by word...")
    words=script_text.split()
    wd=total/max(len(words),1)
    caps=[]
    for idx,w in enumerate(words):
        clean=re.sub(r'[^\w\']','',w).upper()
        if not clean:
            continue
        caps.append(word_clip(clean,wd).set_start(idx*wd))

    final=CompositeVideoClip([video]+caps).set_audio(audio).set_duration(total)
    final.write_videofile(output_path,fps=24,codec='libx264',audio_codec='aac',threads=2,preset='ultrafast')
    print(f"PERFECT VIDEO READY: {output_path}")
    return output_path
