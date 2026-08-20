from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

import os, requests, time, torch
from pytrends.request import TrendReq
from diffusers import StableDiffusionPipeline
from gradio_client import Client
from moviepy.editor import *

print("Loading FREE Local SD Model - 100% Related")
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32, safety_checker=None)
pipe.to("cpu")

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
    lines = [
        f"{trend} is trending in USA right now and shocking everyone",
        f"Breaking update on {trend} in America has left people speechless",
        f"Experts are saying this {trend} news could change everything in USA",
        f"Social media is going crazy over {trend} across United States",
        f"This {trend} story is breaking the internet in America right now",
        f"What is your honest opinion on {trend} in USA comment below"
    ]
    return lines

# 100% RELATED IMAGE - Har image script ki line se banegi
def make_images(lines, trend):
    paths = []
    for i, line in enumerate(lines):
        print(f"Image {i+1}/6 Related to: {line}")

        # YEHI MAIN CHANGE HAI - Trend + Line dono prompt me
        prompt = f"ultra photorealistic news photo directly related to '{trend}', scene showing {line}, detailed face, USA news background, cinematic, 8k, highly detailed, real photo"

        negative = "cartoon, anime, blurry, low quality, text, watermark"

        image = pipe(prompt, negative_prompt=negative, num_inference_steps=25, guidance_scale=8.5).images[0]
        p = f"img_{i}.jpg"
        image.save(p)
        paths.append(p)
    return paths

def make_videos(img_paths, lines):
    vids = []
    for i, (img_path, line) in enumerate(zip(img_paths, lines)):
        out = f"clip_{i}.mp4"
        success = False
        if wan_client:
            try:
                result = wan_client.predict(img_path, f"{line}, smooth motion, {line}", 5, 16, api_name="/generate")
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
    description = f"{trend} trending in USA!\n\n{full_text}\n\n#shorts #usa #trending #viral #breakingnews #usatrending #shortsfeed"
    tags = [trend, "usa trending", "breaking news", "viral shorts", trend+" news"]
    req = yt.videos().insert(part="snippet,status", body={"snippet": {"title": title[:95], "description": description, "tags": tags, "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(out, resumable=True))
    res = req.execute()
    print(f"UPLOADED: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    trend = get_usa_trend()
    lines = make_script(trend)
    imgs = make_images(lines, trend) # Trend pass kiya for 100% related
    vids = make_videos(imgs, lines)
    edit_and_upload(vids, lines, trend)
