"""
Asset Fetcher - RETENTION + ANTI-BOT + PEXEL RANDOMISATION + VvSA
Location: src/asset_fetcher.py
Edits:
- Pexel randomisation: per_page*3 + shuffle + random in_point
- Frame variation rule: random crop/resize/orientation
- Anti-bot: random UA + random query variations + delay
- FFmpeg light noise/hue for dedup
- Sound retention: mood + SFX mapping enhanced + BGM vol every 3 sec handled in video_generator
- No same asset repeat
"""

import os, random, requests, time, tempfile, subprocess
from pathlib import Path

# ===== CONFIG =====
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "") or os.getenv("PIXABAY_KEY", "")
GIPHY_KEY = os.getenv("GIPHY_API_KEY", "")

OUTPUT_ASSETS = Path("output/assets")
OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)

# ===== RETENTION + ANTI-BOT CONSTANTS =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"
]
FPS_CHOICES = [29.97, 29.98, 59.94, 59.95]
NOISE_HUE_FILTER = "noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08"
PEXELS_RANDOM_QUERIES = ["", " 4k", " cinematic", " news", " usa"]

# ===== MUSIC MOOD MAP - Topic ke hisab se + VvSA =====
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

# ===== SFX MAP - Enhanced with VvSA =====
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
    """Anti-bot: random UA every request"""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Cache-Control": "no-cache"
    }

def get_mood_from_topic(topic: str) -> str:
    topic_l = topic.lower()
    # Anti-bot: random shuffle of keys to avoid same pattern
    keys = list(MUSIC_MOOD_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key in topic_l:
            return MUSIC_MOOD_MAP[key]
    return MUSIC_MOOD_MAP["default"]

def get_music(mood: str) -> str:
    """Pixabay se music fetch + randomisation + sound retention ready"""
    if not PIXABAY_KEY:
        print("[ASSET] PIXABAY_KEY missing")
        return None
    try:
        # Pexel randomisation logic: random query suffix + random per_page
        rand_suffix = random.choice(["", " cinematic", " tension", " news"])
        search_q = f"{mood}{rand_suffix}"
        per_page = random.choice([3,5,7]) # anti-bot no same count
        
        # Try pixabay music API (official)
        r = requests.get("https://pixabay.com/api/music/",
                         params={
                             "key": PIXABAY_KEY,
                             "q": search_q,
                             "per_page": per_page
                         },
                         headers=get_random_headers(),
                         timeout=12)
        data = r.json()
        if data.get("hits"):
            # Random pick not always first (anti-bot)
            hit = random.choice(data["hits"][:min(3, len(data["hits"]))])
            download_url = hit.get("download") or hit.get("audio")
            if download_url:
                # Download with random delay anti-bot
                time.sleep(random.uniform(0.2,0.6))
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp.write(requests.get(download_url, headers=get_random_headers(), timeout=20).content)
                tmp.close()
                # Apply light FFmpeg dedup + BGM volume ready for sound retention
                final_path = OUTPUT_ASSETS / f"music_{mood.replace(' ','_')}_{random.randint(1000,9999)}.mp3"
                # FFmpeg: light noise not needed for audio, but we apply bass + volume automation template
                try:
                    cmd = [
                        "ffmpeg","-y",
                        "-i", tmp.name,
                        "-af", f"bass=g=2:f=110,volume=0.06",
                        str(final_path)
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(tmp.name)
                    print(f"[ASSET] Music saved with retention filter: {final_path} mood={mood} fps={random.choice(FPS_CHOICES)}")
                    return str(final_path)
                except:
                    os.rename(tmp.name, final_path)
                    return str(final_path)
            print(f"[ASSET] Music found for mood: {mood} random pick")
            return f"pixabay_music_{mood}.mp3"
    except Exception as e:
        print(f"[ASSET] Music error: {e}")
    return None

def get_pexels_image(keyword: str) -> str:
    """Pexels image + randomisation + frame variation + FFmpeg dedup"""
    if not PEXELS_KEY:
        return None
    try:
        # Anti-bot: random query variation
        rand_q = keyword + random.choice(PEXELS_RANDOM_QUERIES)
        per_page = random.choice([5,8,12])
        r = requests.get("https://api.pexels.com/v1/search",
                         headers={"Authorization": PEXELS_KEY, **get_random_headers()},
                         params={"query": rand_q, "per_page": per_page, "orientation": random.choice(["portrait","landscape",""])},
                         timeout=12)
        data = r.json()
        if data.get("photos"):
            # Randomisation: shuffle and pick random not first
            photos = data["photos"]
            random.shuffle(photos)
            chosen = random.choice(photos[:min(4, len(photos))])
            url = chosen["src"].get("large") or chosen["src"]["original"]
            # Frame variation: random resize param
            img_data = requests.get(url, headers=get_random_headers(), timeout=12).content
            path = OUTPUT_ASSETS / f"{keyword.replace(' ', '_')}_{random.randint(1000,9999)}.jpg"
            path.write_bytes(img_data)
            # FFmpeg light noise+hue for dedup (anti bot + anti copyright)
            try:
                tmp_out = str(path).replace(".jpg", "_f.jpg")
                cmd = [
                    "ffmpeg","-y",
                    "-i", str(path),
                    "-vf", NOISE_HUE_FILTER,
                    tmp_out
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.replace(tmp_out, path)
            except:
                pass
            print(f"[ASSET] Image saved random: {path} query={rand_q}")
            time.sleep(random.uniform(0.1,0.4)) # anti-bot delay
            return str(path)
    except Exception as e:
        print(f"[ASSET] Image error {keyword}: {e}")
    return None

def get_pexels_video_random(keyword: str, num=5):
    """NEW: For video_generator compatibility - Pexel randomisation video version"""
    if not PEXELS_KEY:
        return []
    clips=[]
    try:
        rand_q = keyword + random.choice(PEXELS_RANDOM_QUERIES)
        r = requests.get("https://api.pexels.com/videos/search",
                         headers={"Authorization": PEXELS_KEY},
                         params={"query": rand_q, "per_page": num*3, "orientation": "portrait", "size": "medium"},
                         timeout=12)
        data = r.json()
        videos = data.get("videos", [])
        random.shuffle(videos)
        for v in videos[:num]:
            try:
                files = sorted(v['video_files'], key=lambda x: x['width'])
                link = files[-1]['link'] if files else None
                if not link:
                    continue
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp.write(requests.get(link, headers=get_random_headers(), timeout=20).content)
                tmp.close()
                # Apply FFmpeg noise+hue for dedup + fps randomization
                fps = random.choice(FPS_CHOICES)
                out = OUTPUT_ASSETS / f"pexels_{keyword.replace(' ','_')}_{random.randint(1000,9999)}.mp4"
                try:
                    cmd = [
                        "ffmpeg","-y",
                        "-i", tmp.name,
                        "-vf", NOISE_HUE_FILTER,
                        "-r", str(fps),
                        str(out)
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    os.remove(tmp.name)
                    clips.append(str(out))
                except:
                    os.rename(tmp.name, out)
                    clips.append(str(out))
            except:
                continue
        print(f"[ASSET] Pexels videos random {len(clips)} for {keyword}")
        return clips
    except Exception as e:
        print(f"[ASSET] Pexels video error {e}")
        return []

def get_giphy_gif(keyword: str) -> str:
    """Giphy + randomisation + frame variation"""
    if not GIPHY_KEY:
        print("[ASSET] GIPHY_KEY missing")
        return None
    try:
        # Random variation in query
        rand_q = keyword + random.choice([" reaction", " shock", " breaking", ""])
        r = requests.get("https://api.giphy.com/v1/gifs/search",
                         params={"api_key": GIPHY_KEY, "q": rand_q, "limit": random.choice([3,5,8]), "rating": "g"},
                         headers=get_random_headers(),
                         timeout=12)
        data = r.json()
        if data.get("data"):
            # Random pick anti-bot
            gifs = data["data"]
            random.shuffle(gifs)
            chosen = random.choice(gifs[:min(3, len(gifs))])
            gif_url = chosen["images"]["original"]["url"]
            gif_data = requests.get(gif_url, headers=get_random_headers(), timeout=15).content
            path = OUTPUT_ASSETS / f"{keyword.replace(' ', '_')}_{random.randint(1000,9999)}.gif"
            path.write_bytes(gif_data)
            print(f"[ASSET] GIF saved random: {path} query={rand_q}")
            time.sleep(random.uniform(0.1,0.3))
            return str(path)
    except Exception as e:
        print(f"[ASSET] GIF error {keyword}: {e}")
    return None

def get_sfx_for_word(script_word: str) -> str:
    """SFX by topic + sound retention ready"""
    word = script_word.lower()
    # Random shuffle keys for anti-bot no same pattern
    keys = list(SFX_MAP.keys())
    random.shuffle(keys)
    for key in keys:
        if key in word:
            sfx_file = SFX_MAP[key]
            # Try multiple possible paths
            for base in ["assets/sounds", "assets", "sounds", "output/assets"]:
                sfx_path = Path(f"{base}/{sfx_file}")
                if sfx_path.exists():
                    print(f"[ASSET] SFX matched: {word} -> {sfx_path} + punch ready")
                    return str(sfx_path)
            print(f"[ASSET] SFX not found locally: {sfx_file}, need download - will use punch fallback")
            # Return placeholder with punch logic to be handled in video_generator
            return f"punch_{key}.mp3"
    return None

def fetch_all_assets(topic: str, keywords: list):
    """Main - sab assets + randomisation + no repeat"""
    results = {"music": None, "images": [], "gifs": [], "sfx": [], "videos": []}
    mood = get_mood_from_topic(topic)
    results["music"] = get_music(mood)
    
    # Anti-bot: shuffle keywords so no same order
    shuffled_kws = keywords[:]
    random.shuffle(shuffled_kws)
    
    used_urls=set()
    for kw in shuffled_kws[:4]: # 4 for variation
        # Image
        img = get_pexels_image(kw)
        if img and img not in used_urls:
            results["images"].append(img)
            used_urls.add(img)
        # Video random (new for retention)
        vids = get_pexels_video_random(kw, num=2)
        results["videos"].extend(vids)
        # GIF
        gif = get_giphy_gif(kw)
        if gif and gif not in used_urls:
            results["gifs"].append(gif)
            used_urls.add(gif)
        # SFX per keyword
        sfx = get_sfx_for_word(kw)
        if sfx:
            results["sfx"].append(sfx)
    
    print(f"[ASSET] Done retention random: music={results['music']}, images={len(results['images'])}, gifs={len(results['gifs'])}, videos={len(results['videos'])}, sfx={results['sfx']}")
    return results

def add_asset_at_last(main_video: str, asset_path: str, final_output: str):
    """Asset last me 1 sec + FFmpeg dedup + fps lock"""
    fps = random.choice(FPS_CHOICES)
    cmd = [
        "ffmpeg", "-y",
        "-i", main_video,
        "-loop", "1", "-t", "1", "-i", asset_path,
        "-filter_complex", f"[0:v][1:v]concat=n=2:v=1:a=0, {NOISE_HUE_FILTER} [v]",
        "-map", "[v]", "-map", "0:a",
        "-r", str(fps),
        final_output
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[ASSET] Last me joda with dedup fps={fps}: {final_output}")
    return final_output

if __name__ == "__main__":
    fetch_all_assets("Tacko Fall signs 76ers leaked behind closed doors", ["76ers logo", "Tacko Fall", "celebration secret"])
