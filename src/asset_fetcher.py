import os, random, requests, time, tempfile, subprocess, glob, json, re
from pathlib import Path

OUTPUT_ASSETS = Path("output/assets")
OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
]
FPS_CHOICES = [29.97, 30, 59.94, 60]

def pro_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Cache-Control": "no-cache, no-store",
        "Pragma": "no-cache",
        "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "Referer": random.choice(["https://www.google.com/","https://duckduckgo.com/"])
    }

def pro_fetch(url, timeout=15, retries=10):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(0.02,0.25))
            cb = f"{'&' if '?' in url else '?'}cb={random.randint(100000,999999)}&t={int(time.time())}"
            r = requests.get(url+cb, headers=pro_headers(), timeout=timeout)
            if r.status_code in [200,201,202]:
                return r
            time.sleep((2**attempt)+random.uniform(0,0.5))
        except:
            time.sleep((2**attempt)+random.uniform(0,0.3))
    raise RuntimeError(f"PRO FETCH FAILED {url} - NO FALLBACK")

def clean_for_filename(text):
    # NO backslash inside f-string - use this helper
    cleaned = re.sub(r'\W+', '_', text)
    return cleaned[:20]

def get_duckduckgo_image(visual_prompt: str) -> str:
    for attempt in range(10):
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.images(visual_prompt, max_results=3))
                if not results:
                    raise RuntimeError("DuckDuckGo empty")
                random.shuffle(results)
                for res in results[:2]:
                    img_url = res.get('image') or res.get('thumbnail')
                    if not img_url: continue
                    r = pro_fetch(img_url, timeout=15, retries=10)
                    clean_prompt = clean_for_filename(visual_prompt)
                    rand_num = random.randint(1000,9999)
                    path = OUTPUT_ASSETS / f"duck_{clean_prompt}_{rand_num}.jpg"
                    path.write_bytes(r.content)
                    if path.stat().st_size < 5000:
                        path.unlink(missing_ok=True)
                        continue
                    print(f"[ASSET PRO] DuckDuckGo 1.0s: {path} prompt={visual_prompt} - FORCE")
                    return str(path)
        except Exception as e:
            print(f"[ASSET PRO] DuckDuckGo attempt {attempt} fail {e} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.3))
    raise RuntimeError(f"DuckDuckGo failed for {visual_prompt} - NO FALLBACK")

def get_yt_dlp_clip(visual_prompt: str) -> str:
    for attempt in range(10):
        try:
            import yt_dlp
            rand_id = random.randint(1000,9999)
            out_tmpl = str(TEMP_DIR / f"ytdlp_{rand_id}_%(id)s.%(ext)s")
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
            if not files:
                raise RuntimeError("yt-dlp no files")
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            vpath = files[0]
            from moviepy.editor import VideoFileClip
            try:
                vc = VideoFileClip(vpath)
                if vc.duration > 1.8:
                    clean_prompt2 = clean_for_filename(visual_prompt)
                    rand2 = random.randint(1000,9999)
                    final_path = OUTPUT_ASSETS / f"ytdlp_{clean_prompt2}_{rand2}.mp4"
                    vc.close()
                    cmd = ["ffmpeg","-y","-i", vpath, "-t", "1.8", "-c:v","libx264","-c:a","aac", str(final_path)]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(vpath)
                    print(f"[ASSET PRO] yt-dlp 1.8s: {final_path} - FORCE")
                    return str(final_path)
                else:
                    vc.close()
                    os.remove(vpath)
            except:
                if os.path.exists(vpath):
                    final_path = OUTPUT_ASSETS / f"ytdlp_{random.randint(1000,9999)}.mp4"
                    os.rename(vpath, final_path)
                    return str(final_path)
        except Exception as e:
            print(f"[ASSET PRO] yt-dlp attempt {attempt} fail {e} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.3))
    raise RuntimeError(f"yt-dlp failed for {visual_prompt} - NO FALLBACK")

def fetch_all_assets(topic: str, keywords: list = None, script_visual_segments: list = None):
    results = {"music": None, "images": [], "gifs": [], "sfx": [], "videos": [], "segments": []}
    if not script_visual_segments:
        raise RuntimeError("No script_visual_segments - NO FALLBACK")
    used_urls=set()
    for idx, seg in enumerate(script_visual_segments[:8]):
        prompt = seg.get('visual_search_prompt','').strip()
        asset_type = seg.get('asset_type','video').lower()
        if not prompt:
            raise RuntimeError("Empty visual_search_prompt - NO FALLBACK")
        if asset_type == 'image':
            img = get_duckduckgo_image(prompt)
            results["images"].append(img)
            results["segments"].append({"type":"image","path":img,"duration":1.0,"prompt":prompt,"segment_text":seg.get('segment_text','')})
        else:
            clip = get_yt_dlp_clip(prompt)
            results["videos"].append(clip)
            results["segments"].append({"type":"video","path":clip,"duration":1.8,"prompt":prompt,"segment_text":seg.get('segment_text','')})
    if not results["segments"]:
        raise RuntimeError("No assets fetched - NO FALLBACK")
    print(f"[ASSET PRO] FORCE images={len(results['images'])} 1.0s videos={len(results['videos'])} 1.8s - NO FALLBACK")
    return results

def fetch_all_assets_god(topic: str = "", keywords: list = None, script_visual_segments: list = None, *args, **kwargs):
    if isinstance(topic, dict):
        t = topic.get('title','') or topic.get('query','')
        kws = topic.get('tags') or keywords
        segs = topic.get('script_visual_segments') or script_visual_segments
        if not segs:
            raise RuntimeError("No segs in dict - NO FALLBACK")
        return fetch_all_assets(t, keywords=kws, script_visual_segments=segs)
    return fetch_all_assets(topic, keywords=keywords, script_visual_segments=script_visual_segments)
