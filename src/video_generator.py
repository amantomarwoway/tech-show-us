import os
import random
import requests
import tempfile
from moviepy.editor import *
from piper import PiperVoice
import re

# Download Piper model once - American English
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

def get_piper_voice():
    os.makedirs("models", exist_ok=True)
    model_path = "models/en_US-amy-medium.onnx"
    config_path = "models/en_US-amy-medium.onnx.json"
    if not os.path.exists(model_path):
        print("Downloading Piper model...")
        r = requests.get(MODEL_URL)
        open(model_path, 'wb').write(r.content)
        r = requests.get(CONFIG_URL)
        open(config_path, 'wb').write(r.content)
    return PiperVoice.load(model_path, config_path)

def get_stock_clips(query, num=6):
    """Fetch many clips from Pexels"""
    api_key = os.getenv("PEXELS_API_KEY")
    clips = []
    if not api_key:
        # Fallback: create color clips if no key
        print("No PEXELS_API_KEY - using color clips")
        return [ColorClip(size=(1080,1920), color=(random.randint(0,50), random.randint(0,50), random.randint(50,150)), duration=2) for _ in range(num)]

    try:
        headers = {"Authorization": api_key}
        # Clean query for search
        search_q = " ".join(re.findall(r'\w+', query)[:3]) or ["technology", "usa", "news"]
        url = f"https://api.pexels.com/videos/search?query={search_q}&per_page={num}&orientation=portrait"
        res = requests.get(url, headers=headers, timeout=10).json()
        for v in res.get('videos', [])[:num]:
            # Get smallest portrait video file
            files = sorted([f for f in v['video_files'] if f['height']>=720], key=lambda x: x['width'])
            if files:
                # Download file
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                r = requests.get(files[0]['link'], timeout=20)
                tmp.write(r.content)
                tmp.close()
                clips.append(VideoFileClip(tmp.name).resize((1080,1920)).without_audio())
        print(f"Got {len(clips)} stock clips")
    except Exception as e:
        print(f"Pexels error: {e}")

    if not clips:
        clips = [ColorClip(size=(1080,1920), color=(20,20,40), duration=2) for _ in range(num)]
    return clips

def create_video(script_data, output_path="output/news_32.mp4"):
    # Handle dict
    if isinstance(script_data, dict):
        script_text = script_data.get('full_script', '')
        title = script_data.get('title','')
    else:
        script_text = str(script_data)
        title = script_text[:50]

    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    # 1. PIPER TTS - American English
    print("1. Generating Piper TTS American...")
    voice = get_piper_voice()
    audio_path = "temp/voice.wav"
    with open(audio_path, "wb") as wav_file:
        # Piper writes wav directly
        voice.synthesize_wav(script_text, wav_file)

    audio = AudioFileClip(audio_path)
    total_duration = audio.duration + 0.5
    print(f"Audio duration: {total_duration}")

    # 2. MANY MANY CLIPS - Professional editing
    print("2. Fetching many clips...")
    stock_clips = get_stock_clips(title or script_text, num=6)

    # Cut clips to fit total duration, fast cuts every 1.5 sec
    final_clips = []
    time_left = total_duration
    idx = 0
    while time_left > 0:
        clip = stock_clips[idx % len(stock_clips)]
        cut_dur = min(random.uniform(1.0, 2.0), time_left, clip.duration)
        sub = clip.subclip(0, cut_dur).set_duration(cut_dur)
        # Add zoom effect for pro look
        sub = sub.resize(lambda t: 1 + 0.1*t)
        final_clips.append(sub)
        time_left -= cut_dur
        idx += 1

    video = concatenate_videoclips(final_clips).set_duration(total_duration)

    # 3. WORD BY WORD CAPTION - low centre, a bit up
    print("3. Creating word by word captions...")
    words = script_text.split()
    word_duration = total_duration / max(len(words), 1)

    caption_clips = []
    for i, word in enumerate(words):
        start = i * word_duration
        # Clean word
        clean_word = re.sub(r'[^\w\s\']', '', word).upper()
        if not clean_word:
            continue
        txt = TextClip(clean_word, fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=3)
        txt = txt.set_start(start).set_duration(word_duration).set_pos(('center', 0.75), relative=True) # low centre, a bit up from lowest
        caption_clips.append(txt)

    # Composite
    final = CompositeVideoClip([video] + caption_clips).set_audio(audio).set_duration(total_duration)
    final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    print(f"Moviepy - video ready {output_path}")
    print(f"Video created at: {output_path}")

    # Cleanup
    for c in stock_clips:
        try: c.close()
        except: pass

    return output_path
