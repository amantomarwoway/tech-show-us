import os, random, requests, json, time, glob
from pytrends.request import TrendReq
import google.generativeai as genai
from moviepy.editor import *

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("assets", exist_ok=True)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_us_trend():
    pytrends = TrendReq(hl='en-US', tz=360)
    df = pytrends.trending_searches(pn='united_states')
    topic = df[0][0]
    print(f"TRENDING: {topic}")
    return topic

def get_script_and_keywords(topic):
    prompt = f"""
    You are a viral US TikTok scriptwriter.
    Topic: {topic}
    Return ONLY valid JSON:
    {{"script": "30 sec American English script with hook", "visual_keywords": ["keyword1", "keyword2", "keyword3"], "ai_image_prompt": "cinematic photorealistic image prompt for this news, 9:16", "description": "short SEO description", "tags": ["tag1", "tag2"], "hashtags": ["#fyp", "#usa", "#viral", "#breakingnews", "#trending"]}}
    """
    res = model.generate_content(prompt)
    text = res.text.replace("```json","").replace("```","").strip()
    return json.loads(text)

def download_pexels_clip(keyword):
    try:
        headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
        r = requests.get(f"https://api.pexels.com/videos/search?query={keyword}&per_page=1&orientation=portrait&size=medium", headers=headers, timeout=20)
        if r.status_code==200 and r.json()['videos']:
            url = r.json()['videos'][0]['video_files'][0]['link']
            path = f"assets/{keyword.replace(' ','_')}.mp4"
            with open(path, 'wb') as f:
                f.write(requests.get(url, timeout=20).content)
            return path
    except Exception as e:
        print(f"Pexels failed for {keyword}: {e}")
    return None

def download_pollinations_image(prompt):
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=1080&height=1920&model=flux&nologo=true&seed={random.randint(1,9999)}"
        path = f"assets/ai_{int(time.time())}_{random.randint(1,100)}.jpg"
        with open(path, 'wb') as f:
            f.write(requests.get(url, timeout=30).content)
        return path
    except:
        return None

def generate_voice_piper(text):
    wav_path = "assets/voice.wav"
    try:
        from piper import PiperVoice
        voice = PiperVoice.load("piper_model/en_US-amy-medium.onnx")
        with open(wav_path, "wb") as wav_file:
            for chunk in voice.synthesize(text):
                wav_file.write(chunk.audio_int_16_bytes)
        return wav_path
    except Exception as e:
        print(f"Piper error {e}, using espeak fallback")
        os.system(f'espeak-ng -v en-us "{text}" -s 155 --stdout > {wav_path}')
        return wav_path

def make_4k_video(script_data, clips, ai_images, voice_path):
    W, H = 2160, 3840
    audio = AudioFileClip(voice_path)
    duration = audio.duration + 0.8
    all_visuals = [v for v in clips + ai_images if v and os.path.exists(v)]
    if not all_visuals:
        raise Exception("No visuals found")

    random.shuffle(all_visuals)
    time_per_visual = duration / len(all_visuals)

    video_clips = []
    for visual in all_visuals:
        if visual.endswith(".mp4"):
            c = VideoFileClip(visual).subclip(0, time_per_visual).resize((W, H)).set_duration(time_per_visual)
        else:
            c = ImageClip(visual).set_duration(time_per_visual).resize((W, H)).set_position(("center","center"))
        video_clips.append(c)

    final_video = concatenate_videoclips(video_clips, method="compose").set_duration(duration)
    final_video = final_video.set_audio(audio)

    words = script_data['script'].split()
    txt_clips = []
    for i, word in enumerate(words):
        start = (duration / len(words)) * i
        txt = TextClip(word, fontsize=85, color='yellow', font='Arial-Bold', stroke_color='black', stroke_width=6)
        txt = txt.set_position(('center', H*0.72)).set_duration(duration/len(words)).set_start(start)
        txt_clips.append(txt)

    final = CompositeVideoClip([final_video] + txt_clips, size=(W,H))
    output_path = f"{OUTPUT_DIR}/USA_{int(time.time())}_4K.mp4"
    final.write_videofile(output_path, fps=24, codec='libx264', bitrate="8000k", preset="ultrafast", threads=2)
    return output_path

if __name__ == "__main__":
    topic = get_us_trend()
    data = get_script_and_keywords(topic)
    print(json.dumps(data, indent=2))

    clips = []
    for kw in data['visual_keywords']:
        c = download_pexels_clip(kw)
        if c: clips.append(c)
        time.sleep(1)

    ai_images = []
    for _ in range(3):
        img = download_pollinations_image(data['ai_image_prompt'])
        if img: ai_images.append(img)

    voice = generate_voice_piper(data['script'])
    final_path = make_4k_video(data, clips, ai_images, voice)

    with open(f"{OUTPUT_DIR}/meta.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"DONE: {final_path}")
