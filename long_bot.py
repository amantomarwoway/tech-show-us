"""
long_bot.py - NEW LONG BOT - Fully Structured - Human Body + American Audience
Separate from shorts bot - shorts ko kuch fark nahi padega

Human Body Structure:
- Haddiya (Skeleton): Trend Engine + Chapters
- Maans (Muscle): Script + B-roll + Voice
- Nase (Nerves): Captions + Retention
- Khaal (Skin): Branding + Outro + YouTube Algorithm

Trend: Direct Google Search (NOT Google Trends RSS)
- Kya search kar rahe hain, kitne search kar rahe hain, kyu search kar rahe hain, kitna interest hai

Workflow: 
1. Find what Americans search NOW directly on Google
2. Generate viral script (full story, 900-1300 words, no cut)
3. Piper TTS
4. Pexels clips (fixed, no corrupt)
5. Build long video with human structure (16:9, 6-9 min)
6. Thumbnail + Title/Desc/Tags + Upload

100% FREE SOURCES, Viral Structure
"""

import os
import sys
import wave
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import random

# Add src_long to path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src_long"))

# Import new long engines (separate from shorts)
from long_trend_engine_v2 import find_american_trends_direct
from long_script_engine_v2 import generate_long_script_american
from long_video_engine_v2 import get_piper, build_long_video
from long_config import OUTPUT_LONG_DIR, CHANNEL_NAME

# Optional: existing DB for duplicate check (don't affect shorts)
try:
    sys.path.insert(0, str(ROOT / "src"))
    from database import get_recent
except:
    get_recent = lambda x: []

def tts_long_full(script: str, out_dir: Path) -> Path:
    """Piper TTS for long - chunked"""
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = get_piper()
    audio_path = out_dir / "voice_long.wav"
    with wave.open(str(audio_path), "wb") as wav:
        first=True
        # Chunk script into 400 char pieces for stability
        chunks = [script[i:i+400] for i in range(0, len(script), 400)]
        for chunk in chunks:
            for ch in voice.synthesize(chunk):
                if first:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(ch.sample_rate)
                    first=False
                wav.writeframes(ch.audio_int16_bytes)
    return audio_path

def main():
    print("=== LONG BOT V2 - HUMAN BODY STRUCTURE - AMERICAN AUDIENCE ===")
    
    # Check manual override
    manual_topic = os.getenv("MANUAL_TOPIC", "").strip()
    manual_title = os.getenv("MANUAL_TITLE", "").strip()
    
    # 1. HADDIYA - Find Trend Direct from Google (NOT Google Trends RSS)
    if manual_topic:
        print(f"Manual topic: {manual_topic}")
        trends = [{
            "query": manual_topic,
            "title": manual_topic,
            "source": "manual",
            "search_volume": 80,
            "video_count": 20,
            "why_searching": "manual - user wants this",
            "american_interest": 90,
            "youtube_suggestions": []
        }]
    else:
        trends = find_american_trends_direct(limit=20)
    
    # Filter duplicates (using shorts DB but don't affect shorts)
    try:
        recent = get_recent(50)
        recent_titles = [r.get('title','').lower() for r in recent]
    except:
        recent_titles = []
    
    selected = None
    for t in trends:
        q = t["query"].lower()
        if any(q in rt or rt in q for rt in recent_titles):
            print(f"Skipping duplicate: {t['query']}")
            continue
        if t["american_interest"] >= 75 and t["search_volume"] >= 30:
            selected = t
            break
    
    if not selected:
        selected = trends[0] if trends else {"query": "USA Breaking News Today", "why_searching": "general_curiosity", "american_interest": 80, "youtube_suggestions": []}
    
    print(f"SELECTED (Direct Google USA): {selected['query']} | Interest {selected['american_interest']} | Why: {selected['why_searching']}")
    
    # 2. MAANS - Generate Full Script (Human Body)
    script_data = generate_long_script_american(selected, min_words=900, max_words=1300)
    title = manual_title if manual_title else script_data["title"]
    script = script_data["script"]
    chapters = script_data["chapters"]
    description = script_data["description"]
    tags = script_data["tags"]
    
    print(f"Title: {title}")
    print(f"Words: {script_data['word_count']} (Full story, no cut)")
    print(f"Chapters: {chapters}")
    
    # 3. MAANS - TTS
    work_dir = Path(OUTPUT_LONG_DIR) / datetime.now().strftime("%Y%m%d_%H%M")
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = work_dir / "audio"
    audio_path = tts_long_full(script, audio_dir)
    print(f"Audio ready: {audio_path}")
    
    # 4. KHAAL + MAANS + NASE + HADDIYA - Build Video
    final_video = work_dir / "final_long.mp4"
    build_long_video(str(audio_path), script, selected["query"], chapters, str(final_video))
    
    # 5. Thumbnail (simple free)
    try:
        from PIL import Image, ImageDraw, ImageFont
        thumb_path = work_dir / "thumbnail.jpg"
        img = Image.new('RGB', (1280,720), color=(10,25,49))
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except: font = ImageFont.load_default()
        # Wrap title
        words = title.split()
        lines=[]
        cur=""
        for w in words:
            if len(cur+" "+w)<28:
                cur+=" "+w
            else:
                lines.append(cur.strip()); cur=w
        if cur: lines.append(cur.strip())
        y=180
        for line in lines[:3]:
            draw.text((60,y), line, font=font, fill=(255,255,255))
            y+=70
        draw.text((60,y+20), "UNCOVERED USA 24", font=font, fill=(255,230,0))
        img.save(thumb_path)
        print(f"Thumbnail: {thumb_path}")
    except Exception as e:
        print(f"Thumbnail error: {e}")
        thumb_path = work_dir / "thumbnail.jpg"
    
    # 6. Description with chapters + American SEO
    full_desc = f"{description}\n\n"
    if chapters:
        full_desc += "CHAPTERS:\n" + "\n".join(chapters) + "\n\n"
    full_desc += f"Why Americans Searching: {selected['why_searching']}\n"
    full_desc += f"American Interest Score: {selected['american_interest']}/100\n"
    full_desc += f"Search Volume: {selected['search_volume']}\n\n"
    full_desc += f"{CHANNEL_NAME} is original summary based on publicly available reporting. Not affiliated with CNN, BBC, Reuters.\n"
    full_desc += f"Date: {datetime.now().isoformat()}\n"
    full_desc += "#usanews #breakingnews #americannews"
    
    print("\n=== LONG BOT V2 DONE ===")
    print(f"Video: {final_video}")
    print(f"Title: {title}")
    print(f"Description: {full_desc[:200]}...")
    print(f"Tags: {tags}")
    print("\nHuman Body Structure:")
    print("Haddiya (Skeleton): Trend + Chapters")
    print("Maans (Muscle): Script + B-roll + Voice")
    print("Nase (Nerves): Captions + Retention")
    print("Khaal (Skin): Branding + Outro + Algorithm")
    print("\nAmerican Audience: Designed for USA, FOMO, numbers, fast")
    print("Trend Method: Direct Google Search (kya, kitne, kyu, kitna interest)")
    print("Length: Full story, no cut, 900-1300 words, 6-9 min")
    
    # Upload logic would go here (reuse existing youtube_uploader if available)
    # For now, just save metadata
    meta_path = work_dir / "metadata.json"
    import json
    with open(meta_path, 'w') as f:
        json.dump({"title": title, "description": full_desc, "tags": tags, "query": selected["query"], "chapters": chapters}, f, indent=2)
    
    return str(final_video)

if __name__ == "__main__":
    main()
