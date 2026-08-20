from PIL import Image
if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS
import os, time, re, glob, requests
from pytrends.request import TrendReq
from gnews import GNews
from moviepy.editor import *

print("BOT STARTED - FINAL 4K CLEAN")

def get_trend_and_news():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.trending_searches(pn='united_states')
        trend = str(df.iloc[0,0])
    except: 
        trend = "USA Breaking News"
    try:
        gnews = GNews(language='en', country='US', max_results=3, period='1d')
        news_list = gnews.get_news(trend)
        full_text = " ".join([n.get('title','') + ". " + n.get('description','') for n in news_list[:3]])
    except:
        full_text = f"Breaking news in USA about {trend}. Latest update on {trend}."
    return trend, full_text

def clean_news(text):
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', ' ', text)
    return ". ".join(text.split('.')[:6])[:800]

def get_4k_related_clips(trend, need=6):
    for f in glob.glob("img_*.jpg") + glob.glob("clip_*.mp4"):
        try: os.remove(f)
        except: pass
    clips = []
    headers = {"Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"}
    try:
        r = requests.get(f"https://api.unsplash.com/search/photos?query={trend}&orientation=portrait&per_page={need}&order_by=relevant&content_filter=high", headers=headers, timeout=15)
        if r.status_code == 200:
            for i, p in enumerate(r.json().get('results',[])[:need]):
                url = p['urls']['raw'] + "&w=2160&h=3840&fit=crop&q=95"
                data = requests.get(url, timeout=20).content
                open(f"img_{i}.jpg","wb").write(data)
                print(f"4K Downloaded {i}: {trend}")
    except Exception as e: 
        print(f"Unsplash error: {e}")

    for i in range(need):
        if os.path.exists(f"img_{i}.jpg"):
            try:
                img_clip = ImageClip(f"img_{i}.jpg", duration=5).resize(height=3840).crop(width=2160, height=3840, x_center=1080, y_center=1920)
                img_clip = img_clip.resize(lambda t: 1 + 0.05*t) # clean slow zoom
                img_clip.write_videofile(f"clip_{i}.mp4", fps=30, codec='libx264', logger=None, ffmpeg_params=['-crf','16'])
                clips.append(f"clip_{i}.mp4")
            except: pass
    print(f"Total 4K Clips: {len(clips)}")
    return clips

def make_final(trend, clean_text, clip_paths):
    # SOUND PERFECT
    with open("news.txt","w", encoding="utf-8") as f: f.write(clean_text)
    os.system('cat news.txt | piper --model en_US-lessac-medium.onnx --output_file voice.wav')
    if not os.path.exists("voice.wav") or os.path.getsize("voice.wav") < 1000:
        print("Voice failed")
        return
    audio = AudioFileClip("voice.wav").fx(afx.volumex, 2.5).fx(afx.audio_normalize)

    edited = [VideoFileClip(p).subclip(0,5) for p in clip_paths]
    final_v = concatenate_videoclips(edited*3, method="compose").subclip(0, audio.duration + 0.3)
    final_v = final_v.set_audio(audio)

    words = clean_text.split()
    per = final_v.duration / max(len(words),1)
    # YELLOW MEDIUM CAPTION - JAISA TUNE BOLA
    txts = [TextClip(w.upper(), fontsize=72, color='yellow', font='DejaVu-Sans', stroke_color='black', stroke_width=4, method='label').set_position(('center', 3000)).set_start(i*per).set_duration(per) for i,w in enumerate(words)]

    final = CompositeVideoClip([final_v] + txts, size=(2160,3840))
    out = f"final_{int(time.time())}.mp4"
    final.write_videofile(out, fps=30, codec='libx264', audio_codec='aac', audio_bitrate='192k', logger=None, ffmpeg_params=['-crf','18'])

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=os.getenv("YT_REFRESH_TOKEN"), client_id=os.getenv("YT_CLIENT_ID"), client_secret=os.getenv("YT_CLIENT_SECRET"), token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    yt = build('youtube','v3', credentials=creds)
    title = f"{trend} - USA Breaking Update! #shorts"
    # Unsplash credit add kiya - terms ke liye
    desc = f"{clean_text}\n\nPhoto by Unsplash\n\n#{trend.replace(' ','')} #usanews #breakingnews"
    req = yt.videos().insert(part="snippet,status", body={"snippet": {"title": title[:95], "description": desc, "tags": [trend, "USA News"], "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(out, resumable=True))
    print(f"UPLOADED 4K: https://youtu.be/{req.execute()['id']}")
    open("last_trend.txt","w").write(trend)

if __name__ == "__main__":
    trend, full_news = get_trend_and_news()
    last = open("last_trend.txt").read() if os.path.exists("last_trend.txt") else ""
    if trend.strip() == last.strip() and last != "":
        print(f"Same trend {trend}, skip")
        exit(0)
    clean = clean_news(full_news)
    clips = get_4k_related_clips(trend, 6)
    if len(clips) == 0:
        print("No images - check UNSPLASH_ACCESS_KEY")
        exit(1)
    make_final(trend, clean, clips)
