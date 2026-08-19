import os, requests, time, traceback
from pytrends.request import TrendReq
from huggingface_hub import InferenceClient
from gradio_client import Client
from moviepy.editor import *

# --- Secrets from YML ---
HF_TOKEN = os.getenv("HF_TOKEN")
hf_client = InferenceClient(token=HF_TOKEN)

def get_wan_client():
    try:
        return Client("kijai/WanVideo", verbose=False)
    except Exception as e:
        print(f"Wan Client Error: {e}")
        return None

wan_client = get_wan_client()

# 1. Script from USA Trends Only
def get_usa_trending_script():
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        df = pytrends.trending_searches(pn='united_states')
        trend = str(df[0][0])
    except Exception as e:
        print(f"Trends fail, using backup: {e}")
        trend = "USA Breaking News"

    base = f"{trend} is trending in USA right now. People across America are shocked. Experts are calling this huge. Social media is reacting. This could change everything. Everyone is talking about it. What do you think about {trend}"
    lines = [s.strip() for s in base.split('.') if s.strip()][:7]
    while len(lines) < 7:
        lines.append(lines[-1])
    return trend, lines

# 2. HF Image + Wan 2.1 Video (7 images -> 7 videos)
def generate_clip(line, idx):
    img_path = f"img_{idx}.jpg"
    clip_path = f"clip_{idx}.mp4"

    print(f"[{idx+1}/7] HF Image: {line[:50]}")
    for _ in range(2):
        try:
            image = hf_client.text_to_image(
                prompt=f"{line}, cinematic photorealistic 4k, usa",
                model="black-forest-labs/FLUX.1-dev"
            )
            image.save(img_path)
            break
        except Exception as e:
            print(f"HF Retry: {e}")
            time.sleep(5)

    print(f"[{idx+1}/7] Wan 2.1 Video Converting")
    video_made = False
    if wan_client:
        try:
            result = wan_client.predict(img_path, f"{line}, smooth motion, camera pan", 5, 16, api_name="/generate")
            video_url = result[0] if isinstance(result, (list, tuple)) else result
            if isinstance(video_url, dict):
                video_url = video_url.get('video') or video_url.get('url') or list(video_url.values())[0]
            r = requests.get(video_url, timeout=250)
            with open(clip_path, 'wb') as f:
                f.write(r.content)
            video_made = True
        except Exception as e:
            print(f"Wan fail, fallback used: {e}")

    if not video_made:
        print("Fallback Image->Video")
        clip = ImageClip(img_path, duration=5).resize((1080, 1920))
        clip.write_videofile(clip_path, fps=24, codec='libx264', logger=None, audio=False)

    return clip_path

# 3. Piper TTS + Yellow Caption + Final Short
def create_final_short(clips, lines, trend):
    full_text = ". ".join(lines)
    print("Generating Piper American Voice...")
    os.system(f'echo "{full_text}" | piper --model./en_US-lessac-medium.onnx --output_file voice.wav')

    video_clips = [VideoFileClip(c).resize((1080, 1920)).set_duration(5) for c in clips if os.path.exists(c)]
    final_video = concatenate_videoclips(video_clips, method="compose")

    if os.path.exists("voice.wav"):
        try:
            audio = AudioFileClip("voice.wav")
            final_video = final_video.set_audio(audio).set_duration(min(final_video.duration, audio.duration))
        except Exception as e:
            print(f"Audio attach fail: {e}")

    # Yellow word-to-word caption - niche center se thoda upar
    txt_clips = []
    for i, line in enumerate(lines):
        txt = TextClip(line, fontsize=60, color='yellow', font='DejaVu-Sans-Bold',
                       stroke_color='black', stroke_width=3, method='caption',
                       size=(900, None), align='center')
        txt = txt.set_position(('center', 1350)).set_start(i*5).set_duration(5)
        txt_clips.append(txt)

    final = CompositeVideoClip([final_video] + txt_clips, size=(1080, 1920))
    output = f"short_{int(time.time())}.mp4"
    final.write_videofile(output, fps=24, codec='libx264', threads=2, logger=None)
    return output

# 4. YouTube Upload
def upload_youtube(video_path, trend):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    print(f"Uploading to YouTube: {trend}")
    creds = Credentials(None, refresh_token=os.getenv("YT_REFRESH_TOKEN"),
                        client_id=os.getenv("YT_CLIENT_ID"),
                        client_secret=os.getenv("YT_CLIENT_SECRET"),
                        token_uri="https://oauth2.googleapis.com/token")
    youtube = build('youtube', 'v3', credentials=creds)
    title = f"{trend} Trending in USA! #shorts"
    req = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {"title": title[:95], "description": f"{trend} is trending in USA today. #usa #trending #shorts", "categoryId": "25"},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}
        },
        media_body=MediaFileUpload(video_path, resumable=True)
    )
    res = req.execute()
    print(f"UPLOADED: https://youtu.be/{res['id']}")

if __name__ == "__main__":
    trend, lines = get_usa_trending_script()
    print(f"Trend: {trend}")
    all_clips = [generate_clip(line, i) for i, line in enumerate(lines)]
    final_path = create_final_short(all_clips, lines, trend)
    upload_youtube(final_path, trend)
    print("DONE - 1 Short Complete")
