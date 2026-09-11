"""
asset_fetcher.py - GOD LEVEL UNIVERSAL ASSET FETCHER
Instruction: Har cheez kahin se bhi best tarike se use kar
DuckDuckGo 1.0s + yt-dlp 1.8s + Pexels + Pixabay + Unsplash + Giphy - jo best de
"""

import os, random, requests, time, tempfile, subprocess, glob, json, re
from pathlib import Path

try:
    from src.config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION
except:
    from config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION

OUTPUT_ASSETS = Path("output/assets")
OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Mozilla/5.0 (Macintosh)"]

def get_random_headers():
    return {"User-Agent": random.choice(USER_AGENTS), "Accept": "application/json"}

def get_duckduckgo_image(prompt):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.images(prompt, max_results=3))
            if not results: return None
            random.shuffle(results)
            for res in results[:2]:
                url = res.get('image') or res.get('thumbnail')
                if not url: continue
                r = requests.get(url, timeout=12, headers=get_random_headers())
                if r.status_code==200 and len(r.content)>5000:
                    path = OUTPUT_ASSETS / f"duck_{re.sub(r'\W+','_',prompt)[:20]}_{random.randint(1000,9999)}.jpg"
                    path.write_bytes(r.content)
                    print(f"[ASSET GOD] Best DuckDuckGo 1.0s: {prompt}")
                    return str(path)
    except Exception as e:
        print(f"[ASSET] Duck fail {e}")
    return None

def get_yt_dlp_clip(prompt):
    try:
        import yt_dlp
        out_tmpl = str(TEMP_DIR / f"ytdlp_{random.randint(1000,9999)}_%(id)s.%(ext)s")
        ydl_opts = {'format':'best[height<=720][ext=mp4]/best','outtmpl':out_tmpl,'quiet':True,'no_warnings':True,'noplaylist':True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"ytsearch3:{prompt}", download=True)
        files = glob.glob(str(TEMP_DIR / f"ytdlp_*.*"))
        if files:
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            vpath = files[0]
            # cut to 1.8s
            final = OUTPUT_ASSETS / f"ytdlp_{random.randint(1000,9999)}.mp4"
            try:
                subprocess.run(["ffmpeg","-y","-i",vpath,"-t","1.8","-c:v","libx264","-c:a","aac",str(final)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(vpath)
                print(f"[ASSET GOD] Best yt-dlp 1.8s: {prompt}")
                return str(final)
            except:
                return vpath
    except Exception as e:
        print(f"[ASSET] yt-dlp fail {e}")
    return None

def get_pexels_best(prompt, typ="video"):
    key=os.getenv("PEXELS_API_KEY","")
    if not key: return None
    try:
        if typ=="image":
            r=requests.get("https://api.pexels.com/v1/search", headers={"Authorization":key}, params={"query":prompt,"per_page":2}, timeout=10)
            data=r.json()
            if data.get("photos"):
                url=data["photos"][0]["src"]["large"]
                path=OUTPUT_ASSETS / f"pexels_{random.randint(1000,9999)}.jpg"
                path.write_bytes(requests.get(url, timeout=10).content)
                print(f"[ASSET GOD] Best Pexels image: {prompt}")
                return str(path)
        else:
            r=requests.get("https://api.pexels.com/videos/search", headers={"Authorization":key}, params={"query":prompt,"per_page":2,"orientation":"portrait"}, timeout=10)
            data=r.json()
            if data.get("videos"):
                link=data["videos"][0]["video_files"][0]["link"]
                path=OUTPUT_ASSETS / f"pexels_{random.randint(1000,9999)}.mp4"
                path.write_bytes(requests.get(link, timeout=12).content)
                print(f"[ASSET GOD] Best Pexels video: {prompt}")
                return str(path)
    except: pass
    return None

def get_pixabay_best(prompt):
    key=os.getenv("PIXABAY_API_KEY","") or os.getenv("PIXABAY_KEY","")
    if not key: return None
    try:
        r=requests.get("https://pixabay.com/api/videos/", params={"key":key,"q":prompt,"per_page":2}, timeout=10)
        data=r.json()
        if data.get("hits"):
            url=data["hits"][0]["videos"]["medium"]["url"]
            path=OUTPUT_ASSETS / f"pixabay_{random.randint(1000,9999)}.mp4"
            path.write_bytes(requests.get(url, timeout=12).content)
            print(f"[ASSET GOD] Best Pixabay video: {prompt}")
            return str(path)
    except: pass
    return None

def get_unsplash_best(prompt):
    key=os.getenv("UNSPLASH_ACCESS_KEY","")
    if not key: return None
    try:
        r=requests.get("https://api.unsplash.com/search/photos", params={"query":prompt,"per_page":1}, headers={"Authorization":f"Client-ID {key}"}, timeout=10)
        data=r.json()
        if data.get("results"):
            url=data["results"][0]["urls"]["regular"]
            path=OUTPUT_ASSETS / f"unsplash_{random.randint(1000,9999)}.jpg"
            path.write_bytes(requests.get(url, timeout=10).content)
            print(f"[ASSET GOD] Best Unsplash image: {prompt}")
            return str(path)
    except: pass
    return None

def get_giphy_best(prompt):
    key=os.getenv("GIPHY_API_KEY","")
    if not key: return None
    try:
        r=requests.get("https://api.giphy.com/v1/gifs/search", params={"api_key":key,"q":prompt,"limit":2,"rating":"g"}, timeout=10)
        data=r.json()
        if data.get("data"):
            url=data["data"][0]["images"]["original"]["url"]
            path=OUTPUT_ASSETS / f"giphy_{random.randint(1000,9999)}.gif"
            path.write_bytes(requests.get(url, timeout=10).content)
            print(f"[ASSET GOD] Best Giphy gif: {prompt}")
            return str(path)
    except: pass
    return None

def fetch_best_asset(prompt, asset_type="video"):
    """GOD: Try all sources, pick best - kahin se bhi best"""
    print(f"[ASSET GOD] Fetching best {asset_type} for: {prompt} - trying all sources")
    # Try all in parallel best order
    if asset_type=="image":
        for func in [get_duckduckgo_image, get_pexels_best, get_unsplash_best, get_giphy_best]:
            try:
                res=func(prompt, "image") if "pexels" in func.__name__ else func(prompt)
                if res: return res, "image"
            except: continue
    else:
        for func in [get_yt_dlp_clip, get_pexels_best, get_pixabay_best, get_giphy_best]:
            try:
                if func==get_yt_dlp_clip: res=func(prompt)
                elif func==get_giphy_best: res=func(prompt)
                else: res=func(prompt, "video")
                if res: return res, "video"
            except: continue
    return None, None

def fetch_all_assets_god(topic, script_visual_segments=None):
    print(GOD_INSTRUCTION)
    print(f"[ASSET GOD] Fetching all assets for {topic} - best from everywhere")
    results={"images":[],"videos":[],"all":[]}
    if script_visual_segments:
        for seg in script_visual_segments[:8]:
            prompt=seg.get('visual_search_prompt','') or seg.get('segment_text','')
            atype=seg.get('asset_type','video')
            path, typ = fetch_best_asset(prompt, atype)
            if path:
                dur=CLIP_DURATION if typ=="video" else IMAGE_DURATION
                results["all"].append({"path":path,"type":typ,"duration":dur,"prompt":prompt,"segment":seg})
                if typ=="image": results["images"].append(path)
                else: results["videos"].append(path)
    print(f"[ASSET GOD] Done {len(results['all'])} best assets")
    return results

# Backward compatible wrappers
def get_pexels_image(k): p,t=fetch_best_asset(k,"image"); return p
def get_pexels_video_random(k,num=2): 
    res=[]
    for _ in range(num):
        p,t=fetch_best_asset(k,"video")
        if p: res.append(p)
    return res
def get_giphy_gif(k): p,t=fetch_best_asset(k,"image"); return p
def fetch_all_assets(topic, keywords=None, script_visual_segments=None):
    return fetch_all_assets_god(topic, script_visual_segments)
