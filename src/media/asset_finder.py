"""
src/media/asset_finder.py - Find free visual assets
"""

import os
import random
import requests
import tempfile
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def find_assets_for_segments(segments, story):
    """Find visual assets for each script segment"""
    assets = []
    
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    
    for segment in segments:
        search_query = segment.get('visual_search_prompt', '')
        
        if not search_query:
            search_query = story.get('title', 'breaking news')[:50]
        
        # Try Pexels
        if pexels_key:
            asset = search_pexels(search_query)
            if asset:
                assets.append(asset)
                continue
        
        # Fallback to color clip
        assets.append({
            'type': 'color',
            'color': (random.randint(20, 40), random.randint(20, 40), random.randint(40, 80)),
            'duration': 0.8
        })
    
    return assets


def search_pexels(query, num=5):
    """Search Pexels for videos"""
    key = os.getenv("PEXELS_API_KEY", "")
    
    if not key:
        return None
    
    try:
        headers = {"Authorization": key}
        
        # Clean query
        words = [w for w in query.split() if len(w) > 2][:3]
        clean_query = " ".join(words) if words else "breaking news"
        
        url = f"https://api.pexels.com/videos/search?query={clean_query}&per_page={num*3}&orientation=portrait&size=medium"
        
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        videos = data.get('videos', [])
        
        if not videos:
            return None
        
        # Random selection
        random.shuffle(videos)
        
        for video in videos[:num]:
            try:
                files = sorted(video['video_files'], key=lambda x: x['width'])
                if not files:
                    continue
                
                link = files[-1]['link']
                
                # Download to temp
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tmp_path = tmp.name
                tmp.close()
                
                r = requests.get(link, timeout=30, stream=True)
                if r.status_code != 200:
                    continue
                
                with open(tmp_path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                
                if os.path.getsize(tmp_path) < 50000:
                    os.remove(tmp_path)
                    continue
                
                return {
                    'type': 'video',
                    'path': tmp_path,
                    'url': link,
                    'source': 'pexels',
                    'license': 'Pexels License',
                    'duration': 2.0
                }
            
            except Exception as e:
                logger.warning(f"Pexels clip failed: {e}")
                continue
    
    except Exception as e:
        logger.warning(f"Pexels search failed: {e}")
    
    return None


def find_background_music(mood='news'):
    """Find background music (free)"""
    # Check for local music files first
    music_dir = "assets/music"
    
    if os.path.exists(music_dir):
        files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav'))]
        if files:
            return os.path.join(music_dir, random.choice(files))
    
    # Try Pixabay
    pixabay_key = os.getenv("PIXABAY_API_KEY", "")
    
    if pixabay_key:
        try:
            url = f"https://pixabay.com/api/music/?key={pixabay_key}&q=cinematic+tension&per_page=3"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get('hits', [])
                
                if hits:
                    music_url = hits[0].get('download')
                    if music_url:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                        r = requests.get(music_url, timeout=20)
                        tmp.write(r.content)
                        tmp.close()
                        return tmp.name
        
        except Exception as e:
            logger.warning(f"Music search failed: {e}")
    
    return None
