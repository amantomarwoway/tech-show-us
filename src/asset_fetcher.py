"""
Asset Fetcher - Pexels, Pixabay, Giphy se music/image/gif laane ke liye
Simple version
"""
import os
import requests
from pathlib import Path

# ===== CONFIG =====
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_KEY = os.getenv("PIXABAY_API_KEY", "") or os.getenv("PIXABAY_KEY", "")
GIPHY_KEY = os.getenv("GIPHY_API_KEY", "")

OUTPUT_ASSETS = Path("output/assets")
OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)

# ===== MUSIC MOOD MAP - Topic ke hisab se =====
MUSIC_MOOD_MAP = {
    "breaking": "tense dramatic",
    "shocking": "tense dramatic",
    "crash": "dark cinematic",
    "dies": "sad piano",
    "happy": "uplifting happy",
    "wins": "celebration uplifting",
    "heroic": "epic uplifting",
    "default": "news background"
}

# ===== SFX MAP - Action sound =====
SFX_MAP = {
    "breaking": "whoosh.mp3",
    "shocking": "boom.mp3",
    "just in": "alert.mp3",
    "signed": "cash.mp3",
    "wins": "crowd_cheer.mp3",
    "dies": "sad_violin.mp3"
}

def get_mood_from_topic(topic: str) -> str:
    topic = topic.lower()
    for key, mood in MUSIC_MOOD_MAP.items():
        if key in topic:
            return mood
    return MUSIC_MOOD_MAP["default"]

def get_music(mood: str) -> str:
    """Pixabay se music fetch"""
    if not PIXABAY_KEY:
        print("[ASSET] PIXABAY_KEY missing")
        return None
    try:
        # Pixabay music API
        url = f"https://pixabay.com/api/videos/?key={PIXABAY_KEY}&q={mood}&category=music"
        # Actually pixabay music: https://pixabay.com/api/?key=...&q=...
        # Simple: use search
        r = requests.get("https://pixabay.com/api/", params={
            "key": PIXABAY_KEY,
            "q": mood,
            "category": "music",
            "per_page": 3
        }, timeout=10)
        data = r.json()
        if data.get("hits"):
            # Pixabay free music link nahi deta direct, isliye demo me first hit ka preview use
            # Real me tumhe pixabay.com/music/ se download karna padega
            print(f"[ASSET] Music found for mood: {mood}")
            return f"pixabay_music_{mood}.mp3"  # placeholder path
    except Exception as e:
        print(f"[ASSET] Music error: {e}")
    return None

def get_pexels_image(keyword: str) -> str:
    """Pexels se image"""
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get("https://api.pexels.com/v1/search",
                         headers={"Authorization": PEXELS_KEY},
                         params={"query": keyword, "per_page": 1},
                         timeout=10)
        data = r.json()
        if data.get("photos"):
            url = data["photos"][0]["src"]["large"]
            # download
            img_data = requests.get(url, timeout=10).content
            path = OUTPUT_ASSETS / f"{keyword.replace(' ', '_')}.jpg"
            path.write_bytes(img_data)
            print(f"[ASSET] Image saved: {path}")
            return str(path)
    except Exception as e:
        print(f"[ASSET] Image error {keyword}: {e}")
    return None

def get_giphy_gif(keyword: str) -> str:
    """Giphy se gif"""
    if not GIPHY_KEY:
        print("[ASSET] GIPHY_KEY missing")
        return None
    try:
        r = requests.get("https://api.giphy.com/v1/gifs/search",
                         params={"api_key": GIPHY_KEY, "q": keyword, "limit": 1, "rating": "g"},
                         timeout=10)
        data = r.json()
        if data.get("data"):
            gif_url = data["data"][0]["images"]["original"]["url"]
            gif_data = requests.get(gif_url, timeout=15).content
            path = OUTPUT_ASSETS / f"{keyword.replace(' ', '_')}.gif"
            path.write_bytes(gif_data)
            print(f"[ASSET] GIF saved: {path}")
            return str(path)
    except Exception as e:
        print(f"[ASSET] GIF error {keyword}: {e}")
    return None

def get_sfx_for_word(script_word: str) -> str:
    """Script ke word se SFX"""
    word = script_word.lower()
    for key, sfx_file in SFX_MAP.items():
        if key in word:
            sfx_path = Path(f"assets/sounds/{sfx_file}")
            if sfx_path.exists():
                return str(sfx_path)
            else:
                print(f"[ASSET] SFX not found locally: {sfx_path}, need to download")
                return None
    return None

def fetch_all_assets(topic: str, keywords: list):
    """Main function - sab assets ek saath"""
    results = {"music": None, "images": [], "gifs": [], "sfx": []}
    mood = get_mood_from_topic(topic)
    results["music"] = get_music(mood)
    for kw in keywords[:3]:
        img = get_pexels_image(kw)
        if img:
            results["images"].append(img)
        gif = get_giphy_gif(kw)
        if gif:
            results["gifs"].append(gif)
    print(f"[ASSET] Done: {results}")
    return results

def add_asset_at_last(main_video: str, asset_path: str, final_output: str):
    """Asset ko last me same as it is jodna - 1 sec ke liye"""
    import subprocess
    # asset ko 1 sec ka video banao aur concat
    cmd = [
        "ffmpeg", "-y",
        "-i", main_video,
        "-loop", "1", "-t", "1", "-i", asset_path,
        "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0[v]",
        "-map", "[v]", "-map", "0:a",
        final_output
    ]
    subprocess.run(cmd)
    print(f"[ASSET] Last me joda: {final_output}")
    return final_output

if __name__ == "__main__":
    fetch_all_assets("Tacko Fall signs 76ers", ["76ers logo", "Tacko Fall", "celebration"])
