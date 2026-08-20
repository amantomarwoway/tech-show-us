# FIX 1: Pillow ANTIALIAS Error Fix
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import os, requests, time
from pytrends.request import TrendReq
from huggingface_hub import InferenceClient
from gradio_client import Client
from moviepy.editor import *

HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(token=HF_TOKEN)

# FIX 2: Wan 2.1 Repo Not Found Fix
def get_wan_client():
    try:
        return Client("Wan-AI/Wan2.1-I2V-14B-720P")
    except:
        return None
wan_client = get_wan_client()

def get_usa_trend():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.trending_searches(pn='united_states')
        trend = str(df[0][0])
    except:
        trend = "USA Breaking News"
    print(f"TREND: {trend}")
    return trend

def make_script(trend):
    prompt = f"Write a 30 second, 6 sentence viral YouTube Shorts script about '{trend}' trending in USA. American style. Each sentence new line."
    try:
        text = hf_client.text_generation(prompt, model="mistralai/Mistral-7B-Instruct-v0.2", max_new_tokens=200)
    except:
        text = f"{trend} is trending in USA right now. Everyone in America is shocked. Experts say this could change everything. Social media is going crazy. People can't believe it. What do you think about {trend}"
    lines = [s.strip() for s in text.replace('\n','. ').split('.') if len(s.strip())>10][:6]
    while len(lines) < 6:
        lines.append(f"What is your opinion on {trend} in USA")
    return lines

# FIX 3: 100% FREE IMAGE MODEL - NO PAID FLUX DEV
def make_images(lines):
    paths = []
    for i, line in enumerate(lines):
        print(f"Image {i+1}/6 FREE Model")
        try:
            # Ye model hamesha FREE hai
            img = hf_client.text_to_image(
                prompt=f"{line}, cinematic photorealistic USA, highly detailed",
                model="runwayml/stable-diffusion-v1-5"
            )
        except Exception as e:
            print(f"SD 1.5 fail {e}, trying SDXL Free")
            img = hf_client.text_to_image(
                prompt=f"{line}, cinematic USA",
                model="stabilityai/stable-diffusion-xl-base-1.0"
            )
        p = f"img_{i}.jpg"
        img.save(p)
        paths.append(p)
    return paths

def make_videos(img_paths, lines):
    vids = []
    for i, (img_path, line) in enumerate(zip(img_paths, lines)):
        out = f"clip_{i}.mp4"
        success = False
        if wan_client:
            try:
                result = wan_client.predict(img_path, f"{line}, smooth motion", 5, 16, api_name="/generate")
                url = result[0] if isinstance(result, (list,tuple)) else result
                if isinstance(url, dict): url = url.get('video') or list(url.values())[0]
                r = requests.get(url, timeout=200)
                with open(out, 'wb') as f: f.write(r.content)
                success = True
            except:
                print("Wan down, using fallback")
        if not success:
            clip = ImageClip(img_path, duration=5).resize((1080,1920))
            clip.write_videofile(out, fps=24, codec='libx264', logger=None)
        vids.append(out)
    return vids

def edit_and_upload(video_paths, lines, trend):
    full_text = ". ".join(lines)
    os.system(f'echo "{full_text}" | piper --model./en_US-lessac-medium.onnx --output_file voice.wav')
    clips = [VideoFileClip(v).resize((1080,1920)).set_duration(5) for v in video_paths]
    final_v = concatenate_videoclips(clips, method="compose")
    if os.path.exists("voice.wav"):
        final_v = final_v.set_audio(AudioFileClip("voice.wav")).set_duration(30)
    txts = []
    for i, line in enumerate(lines):
        t = TextClip(line, fontsize=65, color='yellow', font='DejaVu-Sans-Bold', stroke_color='black', stroke_width=3, method='caption', size=(900,None), align='center')
        t = t.set_position(('center', 1350)).set_start(i*5).set_duration(5)
        txts.append(t)
    final = CompositeVideoClip([final_v] + txts, size=(1080,1920))
    out = f"short_{int(time.time())}.mp4"
    final.write_videofile(out, fps=24, codec='libx264', threads=2, logger=None)

    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=os.getenv("YT_REFRESH_TOKEN"), client_id=os.getenv("YT_CLIENT_ID"), client_secret=os.getenv("YT_CLIENT_SECRET"), token_uri="https://oauth2.googleapis.com/token")
    yt = build('youtube','v3', credentials=creds)
    title = f"{trend} Just Broke The Internet in USA! #shorts"
    description = f"{trend} is trending in USA!\n\n{full_text}\n\n#shorts #usa #trending #news #viral #usatrending"
    tags = [trend, "usa trending", "breaking news", "viral shorts"]
    req = yt.videos().insert(part="snippet,status", body={"snippet": {"title": title[:95], "description": description, "tags": tags, "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(out, resumable=True))
    res = req.execute()
    print(f"UPLOADED: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    trend = get_usa_trend()
    lines = make_script(trend)
    imgs = make_images(lines)
    vids = make_videos(imgs, lines)
    edit_and_upload(vids, lines, trend)
