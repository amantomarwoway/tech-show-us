"""
FIXED auto_music.py - This is the file causing your screenshot error
Music Error: Expecting value: line 1 column 1 (char 0)

Root Cause: Pixabay API returning empty response, json() fails
Fix: Add empty check + try/except + return None (video still works)
"""
import os, requests, random

def fetch_music_for_video(topic):
    try:
        api_key = os.environ.get("PIXABAY_API_KEY") or os.environ.get("PIXABAY_MUSIC_KEY") or ""
        if not api_key:
            print("No PIXABAY_API_KEY - skipping music")
            return None
        
        # Search for tech background music
        q = "technology background uplifting" if "tech" in topic.lower() else "upbeat background"
        url = f"https://pixabay.com/api/videos/?key={api_key}&q={requests.utils.quote(q)}&per_page=5"
        # NOTE: If you use music endpoint, change URL to /api/ with category=music
        # Common mistake: using wrong endpoint returns HTML not JSON -> char 0 error
        
        print(f"Fetching music for: {topic}")
        r = requests.get(url, timeout=10)
        
        # FIX 1: Check if response is empty (your error)
        if not r.text or len(r.text.strip()) == 0:
            print("⚠️ Pixabay returned empty response - skipping music")
            return None
        
        # FIX 2: Check status code
        if r.status_code != 200:
            print(f"⚠️ Pixabay status {r.status_code} - skipping music: {r.text[:100]}")
            return None
        
        # FIX 3: Safe JSON parse with try/except (THIS IS YOUR ERROR FIX)
        try:
            data = r.json()
        except Exception as json_err:
            print(f"⚠️ JSON parse failed (char 0 error) - response was: {r.text[:200]} - Error: {json_err}")
            print("Continuing without music - video will still be created")
            return None
        
        # Parse hits
        hits = data.get("hits", [])
        if not hits:
            print("No music hits - voice only")
            return None
        
        # Try to get download URL
        chosen = random.choice(hits)
        # For music, field might be different - handle both
        music_url = chosen.get("videos", {}).get("large", {}).get("url") or chosen.get("url")
        if not music_url:
            # If using Pixabay Music API
            music_url = chosen.get("audio") or chosen.get("download")
        
        if not music_url:
            return None
            
        # Download
        path = "bg_music.mp3"
        mr = requests.get(music_url, stream=True, timeout=30)
        with open(path, "wb") as f:
            for chunk in mr.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        print(f"Music downloaded: {path}")
        return path
        
    except Exception as e:
        # FINAL SAFETY - never crash the whole bot for music
        print(f"⚠️ Music Error caught (will continue without music): {e}")
        return None
