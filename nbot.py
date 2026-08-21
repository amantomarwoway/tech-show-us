import os, random, requests, json, time
from pytrends.request import TrendReq
import google.generativeai as genai
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIG ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets", exist_ok=True)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def get_us_trend():
    print("Fetching Google Trends USA...")
    pytrends = TrendReq(hl='en-US', tz=360)
    df = pytrends.trending_searches(pn='united_states')
    topic = df[0][0] # Top 1 trend
    print(f"Trending Topic Found: {topic}")
    return topic

def get_script_and_keywords(topic):
    prompt = f"""
    You are a viral US TikTok scriptwriter.
    Topic: {topic}
    Task:
    1. Write a 30 sec American English script with a killer hook in first 2 sec.
    2. Give 3 generic Pexels search keywords for visuals (e.g. 'courtroom gavel, american flag')
    3. Give 1 cinematic AI image prompt for Pollinations for this news.
    4. Give a SEO description, 5 tags, 5 hashtags from TikTok Creative Center USA style.

    Return ONLY JSON like this:
    {{"script": "...", "visual_keywords": ["k1", "k2", "k3"], "ai_image_prompt": "...", "description": "...", "tags": ["..."], "hashtags": ["#fyp", "#usa", "..."]}}
    """
    res = model.generate_content(prompt)
    # clean json
    text = res.text.replace("```json","").replace("```","").strip()
    data = json.loads(text)
    return data

def download_pexels_clip(keyword):
    headers = {"Authorization": PEXELS_API_KEY}
    r = requests.get(f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait", headers=headers)
    if r.status_code==200 and r.json()['videos']:
        url = r.json()['videos'][0]['video_files'][0]['link']
        path = f"assets/{keyword.replace(' ','_')}.mp4"
        with open(path, 'wb') as f:
            f.write(requests.get(url).content)
        return path
    return None

def download_pollinations_image(prompt):
    # 100% Free, no key needed
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=2160&height=3840&model=flux&nologo=true"
    path = f"assets/ai_{int(time.time())}.jpg"
    with open(path, 'wb') as f:
        f.write(requests.get(url).content)
    return path

def generate_voice_piper(text):
    # Piper TTS - Free offline. Using en_US-amy-medium
    # For GitHub Action, we use espeak as fallback if piper model not found
    # Install piper voice model locally: https://github.com/rhasspy/piper
    try:
        from piper import PiperVoice
        voice = PiperVoice.load("en_US-amy-medium.onnx")
        wav_path = "assets/voice.wav"
        with open(wav_path, "wb") as wav_file:
            for audio in voice.synthesize(text):
                wav_file.write(audio.audio_int_16_bytes)
        return wav_path
    except:
        # Fallback free TTS for server
        os.system(f'espeak-ng -v en-us "{text}" -s 150 --stdout > assets/voice.wav')
        return "assets/voice.wav"

def make_4k_video(script_data, clips, ai_images, voice_path):
    print("Editing 4K Video...")
    # 4K Portrait - 2160x3840
    W, H = 2160, 3840

    audio = AudioFileClip(voice_path)
    duration = audio.duration + 1

    # Mix clips and images
    video_clips = []
    all_visuals = clips + ai_images
    random.shuffle(all_visuals)

    time_per_visual = duration / len(all_visuals)

    for visual in all_visuals:
        if visual.endswith(".mp4"):
            c = VideoFileClip(visual).subclip(0, time_per_visual).resize((W, H)).set_duration(time_per_visual)
        else:
            c = ImageClip(visual).set_duration(time_per_visual).resize((W, H))
        video_clips.append(c)

    final_video = concatenate_videoclips(video_clips, method="compose").set_duration(duration)
    final_video = final_video.set_audio(audio)

    # Word to word yellow captions - lightly up from low center
    words = script_data['script'].split()
    txt_clips = []
    for i, word in enumerate(words):
        start = (duration / len(words)) * i
        txt = TextClip(word, fontsize=90, color='yellow', font='Arial-Bold', stroke_color='black', stroke_width=4)
        txt = txt.set_position(('center', H*0.75)).set_duration(duration/len(words)).set_start(start)
        txt_clips.append(txt)

    final = CompositeVideoClip([final_video] + txt_clips, size=(W,H))

    output_path = f"{OUTPUT_DIR}/USA_{int(time.time())}_4K.mp4"
    final.write_videofile(output_path, fps=24, codec='libx264', bitrate="8000k", preset="ultrafast")
    return output_path, script_data

# --- MAIN FLOW ---
if __name__ == "__main__":
    topic = get_us_trend()
    script_data = get_script_and_keywords(topic)
    print(json.dumps(script_data, indent=2))

    clips = []
    for kw in script_data['visual_keywords']:
        c = download_pexels_clip(kw)
        if c: clips.append(c)

    ai_images = []
    for _ in range(2): # 2 AI cinematic images
        img = download_pollinations_image(script_data['ai_image_prompt'])
        ai_images.append(img)

    # TODO: Tweet screenshot - Add playwright code to screenshot twitter search for topic
    # For now mixing Pexels + AI is enough for USA audience

    voice = generate_voice_piper(script_data['script'])

    final_path, meta = make_4k_video(script_data, clips, ai_images, voice)

    # Save metadata for upload
    with open(f"{OUTPUT_DIR}/meta.json", "w") as f:
        json.dump(meta, f)

    print(f"VIDEO READY: {final_path}")
    print(f"DESCRIPTION: {meta['description']}")
    print(f"HASHTAGS: {' '.join(meta['hashtags'])}")

    # Upload Logic - Use tiktok_uploader or official API
    # pip install tiktok-uploader
    # from tiktok_uploader.upload import upload_video
    # upload_video(final_path, description=meta['description'] + " " + " ".join(meta['hashtags']))
