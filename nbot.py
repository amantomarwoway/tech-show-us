from PIL import Image
if not hasattr(Image, 'ANTIALIAS'): Image.ANTIALIAS = Image.LANCZOS
import os, time, random, re, glob
from pytrends.request import TrendReq
from gnews import GNews
from moviepy.editor import *
import moviepy.video.fx.all as vfx

print("BOT STARTED - FINAL LOCKED")

def get_trend_and_full_news():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.trending_searches(pn='united_states')
        trend = str(df.iloc[0,0])
    except:
        trend = "USA Breaking News"
    print(f"TREND: {trend}")
    try:
        gnews = GNews(language='en', country='US', max_results=5, period='1d')
        news_list = gnews.get_news(trend)
        full_text = " ".join([n.get('title','') + ". " + n.get('description','') for n in news_list[:3]])
        if len(full_text) < 20: raise ValueError("empty")
    except:
        full_text = f"Breaking news in USA about {trend}. Latest reports say {trend} is trending across America today with major developments."
    return trend, full_text

def clean_news(text):
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return ". ".join(text.split('.')[:6])[:800]

def get_clips_google_youtube(trend, need=6):
    for f in glob.glob("yt_*.mp4") + glob.glob("g_*.mp4") + glob.glob("fallback_*.mp4"):
        try: os.remove(f)
        except: pass
    clips = []
    os.system(f'yt-dlp --no-playlist --max-downloads 4 -S "res:720" --download-sections "*0-6" -o "yt_%(id)s.%(ext)s" --merge-output-format mp4 "ytsearch4:{trend} news today" -q --no-warnings')
    clips += glob.glob("yt_*.mp4")
    os.system(f'yt-dlp --no-playlist --max-downloads 2 -S "res:720" --download-sections "*0-6" -o "g_%(id)s.%(ext)s" --merge-output-format mp4 "ytsearch2:{trend} USA breaking" -q --no-warnings')
    clips += glob.glob("g_*.mp4")
    if len(clips) < need:
        for i in range(need - len(clips)):
            ColorClip((1080,1920), color=(random.randint(0,40),random.randint(0,40),random.randint(0,40)), duration=5).write_videofile(f"fallback_{i}.mp4", fps=24, logger=None, codec='libx264', audio=False)
            clips.append(f"fallback_{i}.mp4")
    return clips[:need]

def edit_copyright_safe(video_path):
    try:
        clip = VideoFileClip(video_path)
        clip = clip.subclip(0, min(5, clip.duration))
        w,h = clip.size
        clip = clip.crop(x1=w*0.05, y1=h*0.05, x2=w*0.95, y2=h*0.95)
        clip = clip.resize(height=1920)
        clip = clip.crop(width=1080, height=1920, x_center=clip.w/2, y_center=clip.h/2)
        clip = clip.fx(vfx.speedx, 1.06).fx(vfx.colorx, 1.12)
        return clip
    except:
        return ColorClip((1080,1920), color=(10,10,10), duration=5)

def make_and_upload(trend, clean_news_text, clip_paths):
    is_viral = len(clean_news_text) > 350
    with open("news.txt","w", encoding="utf-8") as f: f.write(clean_news_text)
    os.system('cat news.txt | piper --model en_US-lessac-medium.onnx --output_file voice.wav -q')
    if not os.path.exists("voice.wav"): return
    audio = AudioFileClip("voice.wav")
    edited_clips = [edit_copyright_safe(p) for p in clip_paths]
    if is_viral:
        final_v = concatenate_videoclips(edited_clips*5).subclip(0, audio.duration+1)
    else:
        final_v = concatenate_videoclips(edited_clips, method="compose").subclip(0, 30)
    final_v = final_v.set_audio(audio)
    words = clean_news_text.split()
    per_word = final_v.duration / max(len(words),1)
    txts = [TextClip(w.upper(), fontsize=68, color='white', font='DejaVu-Sans', stroke_color='black', stroke_width=4, method='label').set_position(('center',1350)).set_start(i*per_word).set_duration(per_word) for i,w in enumerate(words)]
    final = CompositeVideoClip([final_v] + txts, size=(1080,1920))
    out = f"final_{int(time.time())}.mp4"
    final.write_videofile(out, fps=24, codec='libx264', audio_codec='aac', threads=2, logger=None)

    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    creds = Credentials(None, refresh_token=os.getenv("YT_REFRESH_TOKEN"), client_id=os.getenv("YT_CLIENT_ID"), client_secret=os.getenv("YT_CLIENT_SECRET"), token_uri="https://oauth2.googleapis.com/token")
    creds.refresh(Request())
    yt = build('youtube','v3', credentials=creds)
    title = f"{trend} - USA Breaking Update! #shorts" if not is_viral else f"{trend} - Full Story | USA News"
    desc = f"{clean_news_text}\n\n#{trend.replace(' ','')} #usanews #breakingnews #usa #shorts #viral"
    req = yt.videos().insert(part="snippet,status", body={"snippet": {"title": title[:95], "description": desc, "tags": [trend, "USA News"], "categoryId": "25"}, "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}, media_body=MediaFileUpload(out, resumable=True))
    print(f"UPLOADED: https://youtu.be/{req.execute()['id']}")

if __name__ == "__main__":
    trend, full_news = get_trend_and_full_news()
    clean = clean_news(full_news)
    clips = get_clips_google_youtube(trend)
    make_and_upload(trend, clean, clips)
