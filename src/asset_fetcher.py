"""
Asset Fetcher - Wire + 45min + 7-Day Velocity + DuckDuckGo 1.0s + yt-dlp 1.8s + YouTube Search SEO
Location: src/asset_fetcher.py
UPDATED: Pexels replaced with DuckDuckGo Search + yt-dlp ytsearch, exact visual as per script_visual_segments
- Image: 1.0 sec screen
- Clip: 1.8 sec screen
- Search: exact prompt like "Pentagon building exterior daytime" for script line "Pentagon deployed..."
- SEO: YouTube Search Traffic over Shorts Feed
- Wire: Reuters + Google News Wire 45min filter, mainstream block
"""

import os, random, requests, time, tempfile, subprocess, glob, json, re
from pathlib import Path

OUTPUT_ASSETS = Path("output/assets")
OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]
FPS_CHOICES = [29.97, 30, 59.94, 60]

MUSIC_MOOD_MAP = {
    "breaking": "tense dramatic news",
    "shocking": "tense dramatic shock",
    "crash": "dark cinematic grave",
    "dies": "sad piano grave dark",
    "dead": "sad piano grave dark",
    "police": "tense siren dramatic",
    "fbi": "tense investigation",
    "arrested": "tense dramatic",
    "happy": "uplifting happy celebration",
    "wins": "celebration uplifting victory",
    "heroic": "epic uplifting heroic",
    "leaked": "mystery tension secret",
    "secret": "mystery tension secret",
    "behind closed doors": "mystery tension secret",
    "default": "news background corporate tense"
}

SFX_MAP = {
    "breaking": "whoosh.mp3",
    "shocking": "boom.mp3",
    "just in": "alert.mp3",
    "signed": "cash.mp3",
    "wins": "crowd_cheer.mp3",
    "dies": "sad_violin.mp3",
    "dead": "sad_violin.mp3",
    "leaked": "secret_reveal.mp3",
    "secret": "secret_reveal.mp3",
    "behind": "mystery_hit.mp3",
    "crash": "crash_hit.mp3",
    "police": "siren_punch.mp3",
    "fbi": "siren_punch.mp3",
    "arrested": "cuff_click.mp3",
    "trump": "trump_hit.mp3",
    "biden": "news_punch.mp3"
}

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Cache-Control": "no-cache"
    }

def get_mood_from_topic(topic: str) -> str:
    topic_l = topic.lower()
    keys = list(MUSIC_MOOD_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key in topic_l:
            return MUSIC_MOOD_MAP[key]
    return MUSIC_MOOD_MAP["default"]

def get_music(mood: str) -> str:
    PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "") or os.getenv("PIXABAY_KEY", "")
    if not PIXABAY_KEY:
        return None
    try:
        rand_suffix = random.choice(["", " cinematic", " tension", " news"])
        search_q = f"{mood}{rand_suffix}"
        per_page = random.choice([3,5,7])
        r = requests.get("https://pixabay.com/api/music/",
                         params={"key": PIXABAY_KEY, "q": search_q, "per_page": per_page},
                         headers=get_random_headers(), timeout=12)
        data = r.json()
        if data.get("hits"):
            hit = random.choice(data["hits"][:min(3, len(data["hits"]))])
            download_url = hit.get("download") or hit.get("audio")
            if download_url:
                time.sleep(random.uniform(0.2,0.6))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp.write(requests.get(download_url, headers=get_random_headers(), timeout=20).content)
                tmp.close()
                final_path = OUTPUT_ASSETS / f"music_{mood.replace(' ','_')}_{random.randint(1000,9999)}.mp3"
                try:
                    cmd = ["ffmpeg","-y","-i", tmp.name, "-af", f"bass=g=2:f=110,volume=0.06", str(final_path)]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(tmp.name)
                    return str(final_path)
                except:
                    os.rename(tmp.name, final_path)
                    return str(final_path)
    except Exception as e:
        print(f"[ASSET] Music error: {e}")
    return None

def get_duckduckgo_image(visual_prompt: str) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(visual_prompt, max_results=3))
            if not results:
                return None
            random.shuffle(results)
            for res in results[:2]:
                img_url = res.get('image') or res.get('thumbnail')
                if not img_url: continue
                try:
                    r = requests.get(img_url, timeout=15, headers=get_random_headers())
                    if r.status_code != 200: continue
                    clean_prompt = re.sub(r'\W+', '_', visual_prompt)[:30]
                    path = OUTPUT_ASSETS / f"duck_{clean_prompt}_{random.randint(1000,9999)}.jpg"
                    path.write_bytes(r.content)
                    if path.stat().st_size < 5000:
                        path.unlink(missing_ok=True)
                        continue
                    print(f"[ASSET] DuckDuckGo image 1.0s: {path} prompt={visual_prompt}")
                    time.sleep(random.uniform(0.1,0.3))
                    return str(path)
                except:
                    continue
    except Exception as e:
        print(f"[ASSET] DuckDuckGo image error {visual_prompt}: {e}")
    return None

def get_yt_dlp_clip(visual_prompt: str) -> str:
    try:
        import yt_dlp
        out_tmpl = str(TEMP_DIR / f"ytdlp_{random.randint(1000,9999)}_%(id)s.%(ext)s")
        ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[height<=720]/best',
            'outtmpl': out_tmpl,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }
        query = f"ytsearch3:{visual_prompt}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(query, download=True)
        files = glob.glob(str(TEMP_DIR / f"ytdlp_*.*"))
        if files:
            # pick newest
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            vpath = files[0]
            # verify duration >=0.5
            try:
                from moviepy.editor import VideoFileClip
                vc = VideoFileClip(vpath)
                if vc.duration >= 0.5:
                    clean_prompt2 = re.sub(r'\W+', '_', visual_prompt)[:30]
                    final_path = OUTPUT_ASSETS / f"ytdlp_{clean_prompt2}_{random.randint(1000,9999)}.mp4"
                    # cut to 1.8s
                    vc.close()
                    # ffmpeg cut 1.8s
                    cmd = ["ffmpeg","-y","-i", vpath, "-t", "1.8", "-c:v","libx264","-c:a","aac", str(final_path)]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(vpath)
                    print(f"[ASSET] yt-dlp clip 1.8s: {final_path} prompt={visual_prompt}")
                    return str(final_path)
                else:
                    vc.close()
                    os.remove(vpath)
            except:
                # if moviepy fails, just return raw
                if os.path.exists(vpath):
                    final_path = OUTPUT_ASSETS / f"ytdlp_{random.randint(1000,9999)}.mp4"
                    os.rename(vpath, final_path)
                    return str(final_path)
    except Exception as e:
        print(f"[ASSET] yt-dlp error {visual_prompt}: {e}")
    return None

def get_sfx_for_word(script_word: str) -> str:
    word = script_word.lower()
    keys = list(SFX_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key in word:
            sfx_file = SFX_MAP[key]
            for base in ["assets/sounds", "assets", "sounds", "output/assets"]:
                sfx_path = Path(f"{base}/{sfx_file}")
                if sfx_path.exists():
                    return str(sfx_path)
            return f"punch_{key}.mp3"
    return None

def fetch_all_assets(topic: str, keywords: list = None, script_visual_segments: list = None):
    results = {"music": None, "images": [], "gifs": [], "sfx": [], "videos": [], "segments": []}
    mood = get_mood_from_topic(topic)
    results["music"] = get_music(mood)
    
    used_urls=set()
    
    # NEW: If script_visual_segments provided (YouTube Search SEO + exact visual), use it directly
    if script_visual_segments:
        for idx, seg in enumerate(script_visual_segments[:8]):
            prompt = seg.get('visual_search_prompt','').strip()
            asset_type = seg.get('asset_type','video').lower()
            if not prompt: continue
            if asset_type == 'image':
                img = get_duckduckgo_image(prompt)
                if img and img not in used_urls:
                    results["images"].append(img)
                    results["segments"].append({"type":"image","path":img,"duration":1.0,"prompt":prompt,"segment_text":seg.get('segment_text','')})
                    used_urls.add(img)
            else:
                clip = get_yt_dlp_clip(prompt)
                if clip and clip not in used_urls:
                    results["videos"].append(clip)
                    results["segments"].append({"type":"video","path":clip,"duration":1.8,"prompt":prompt,"segment_text":seg.get('segment_text','')})
                    used_urls.add(clip)
            # SFX per segment
            sfx = get_sfx_for_word(seg.get('segment_text',''))
            if sfx:
                results["sfx"].append(sfx)
        print(f"[ASSET] Done visual_segments: images={len(results['images'])} 1.0s, videos={len(results['videos'])} 1.8s, sfx={results['sfx']}")
        return results
    
    # Fallback: old keywords mode (DuckDuckGo + yt-dlp)
    if keywords:
        shuffled_kws = keywords[:]
        random.shuffle(shuffled_kws)
        for kw in shuffled_kws[:4]:
            img = get_duckduckgo_image(kw)
            if img and img not in used_urls:
                results["images"].append(img)
                used_urls.add(img)
            clip = get_yt_dlp_clip(kw)
            if clip and clip not in used_urls:
                results["videos"].append(clip)
                used_urls.add(clip)
            sfx = get_sfx_for_word(kw)
            if sfx:
                results["sfx"].append(sfx)
    
    print(f"[ASSET] Done fallback: music={results['music']}, images={len(results['images'])} 1.0s, videos={len(results['videos'])} 1.8s, sfx={results['sfx']}")
    return results

def add_asset_at_last(main_video: str, asset_path: str, final_output: str):
    fps = random.choice(FPS_CHOICES)
    # image 1.0s / video 1.8s handling
    dur = 1.0 if asset_path.lower().endswith(('.jpg','.jpeg','.png')) else 1.8
    if asset_path.lower().endswith(('.jpg','.jpeg','.png')):
        cmd = [
            "ffmpeg", "-y",
            "-i", main_video,
            "-loop", "1", "-t", str(dur), "-i", asset_path,
            "-filter_complex", f"[0:v][1:v]concat=n=2:v=1:a=0 [v]",
            "-map", "[v]", "-map", "0:a",
            "-r", str(fps),
            final_output
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", main_video,
            "-i", asset_path,
            "-filter_complex", f"[0:v][1:v]concat=n=2:v=1:a=0 [v]",
            "-map", "[v]", "-map", "0:a",
            "-r", str(fps),
            final_output
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[ASSET] Last me joda {dur}s fps={fps}: {final_output}")
    return final_output

if __name__ == "__main__":
    # Test with visual segments
    test_segments = [
        {"segment_text": "Pentagon deployed cyber units", "asset_type": "video", "visual_search_prompt": "Pentagon building exterior daytime"},
        {"segment_text": "Shocking decision leaked", "asset_type": "image", "visual_search_prompt": "shocked man reaction office"},
    ]
    fetch_all_assets("White House executive order", script_visual_segments=test_segments)
