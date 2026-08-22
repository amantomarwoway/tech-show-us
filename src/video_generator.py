import os
from moviepy.editor import *
from tts_engine import generate_voice
import config

def create_video(script_data, story):
    W, H = config.VIDEO_W, config.VIDEO_H
    voice_path = generate_voice(script_data['full_script'])
    audio = AudioFileClip(voice_path)
    duration = min(audio.duration + 0.5, config.MAX_VIDEO_DURATION)

    # Simple text-based video - 100% copyright safe, fast
    bg = ColorClip(size=(W,H), color=(10,10,30), duration=duration)

    # Title text
    title_clip = TextClip(story['title'][:60], fontsize=55, color='white', font='Arial-Bold', method='caption', size=(W-100, None))
    title_clip = title_clip.set_position(('center', H*0.2)).set_duration(duration)

    # Source attribution
    src_clip = TextClip(f"Sources: {script_data['sources']} | {story['published']}", fontsize=30, color='lightgray', method='caption', size=(W-80, None))
    src_clip = src_clip.set_position(('center', H*0.9)).set_duration(duration)

    # Developing label if needed
    clips = [bg, title_clip, src_clip]
    if story.get('single_source'):
        dev = TextClip("DEVELOPING STORY - Single Source", fontsize=40, color='yellow', bg_color='red')
        dev = dev.set_position(('center', 50)).set_duration(duration)
        clips.append(dev)

    final = CompositeVideoClip(clips, size=(W,H)).set_audio(audio)
    out_path = f"{config.OUTPUT_DIR}/news_{int(audio.duration)}.mp4"
    final.write_videofile(out_path, fps=24, codec='libx264', preset='ultrafast', threads=2, bitrate="3000k")
    return out_path
