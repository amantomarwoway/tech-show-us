import os
import random
import requests
import tempfile
import re
import wave
from moviepy.editor import *
from piper import PiperVoice

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
    api_key = os.getenv("PEXELS_API_KEY")
    clips = []
    if not api_key:
        print("No PEXELS_API_KEY - using color clips")
        return [ColorClip(size=(1080,1920), color=(20,20,40), duration=2) for _ in range(num)]
    try:
        headers = {"Authorization": api_key}
        search_q = " ".join(re.findall(r'\w+', str(query))[:2]) or ["technology"]
        url = f"https://api.pexels.com/videos/search?query={search_q}&per_page={num}&orientation=portrait"
        res = requests.get(url, headers=headers, timeout=15).json()
        for v in res.get('videos', [])[:num]:
            files = [f for f in v['video_files'] if f['height']>=720]
            if not files: continue
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            r = requests.get(files[0]['link'], timeout=20)
            tmp.write(r.content)
            tmp.close()
            clips.append(VideoFileClip(tmp.name).resize(height=1920).without_audio())
    except Exception as e:
        print(f"Pexels error: {e}")
    if not clips:
        clips = [ColorClip(size=(1080,1920), color=(20,20,40), duration=2) for _ in range(num)]
    return clips

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    # FIX: script_text defined first
    if isinstance(script_data, dict):
        script_text = script_data.get('full_script', '') or script_data.get('script','')
        title = script_data.get('title','USA News')
    else:
        script_text = str(script_data)
        title = script_text[:50]

    os.makedirs("output", exist_ok=True)
    os.makedirs("temp", exist_ok=True)

    # 1. PIPER TTS FIXED
    print("1. Generating Piper TTS American...")
    voice = get_piper_voice()
    audio_path = "temp/voice.wav"

    with wave.open(audio_path, "wb") as wav_file:
        first = True
        for chunk in voice.synthesize(script_text):
            if first:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(chunk.sample_rate)
                first = False
            wav_file.writeframes(chunk.audio_int16_bytes)

    audio = AudioFileClip(audio_path)
    total_duration = audio.duration + 0.5
    print(f"Audio duration: {total_duration}")

    # 2. MANY CLIPS
    print("2. Fetching many clips...")
    stock_clips = get_stock_clips(title or script_text, num=6)

    final_clips = []
    time_left = total_duration
    idx = 0
    while time_left > 0:
        clip = stock_clips[idx % len(stock_clips)]
        cut_dur = min(random.uniform(1.0, 2.0), time_left, clip.duration-0.1)
        if cut_dur <= 0: cut_dur = 0.5
        sub = clip.subclip(0, cut_dur).set_duration(cut_dur)
        final_clips.append(sub)
        time_left -= cut_dur
        idx += 1

    video = concatenate_videoclips(final_clips).set_duration(total_duration)

    # 3. WORD BY WORD CAPTION - low centre
    print("3. Creating captions...")
    words = script_text.split()
    word_duration = total_duration / max(len(words), 1)
    caption_clips = []
    for i, word in enumerate(words):
        clean = re.sub(r'[^\w\']', '', word).upper()
        if not clean: continue
        txt = TextClip(clean, fontsize=65, color='white', font='Arial-Bold', stroke_color='black', stroke_width=4)
        txt = txt.set_start(i*word_duration).set_duration(word_duration).set_position(('center', 0.78), relative=True)
        caption_clips.append(txt)

    final = CompositeVideoClip([video] + caption_clips).set_audio(audio).set_duration(total_duration)
    final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    print(f"Moviepy - video ready {output_path}")
    return output_path
