"""
src/media/asset_finder.py - SCRIPT-BASED visual finder
Har script sentence se specific query nikalti hai
"""

import os
import re
import random
import requests
import tempfile
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Stop words to filter
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to',
    'for', 'of', 'and', 'or', 'but', 'with', 'from', 'by', 'as', 'says',
    'said', 'will', 'has', 'have', 'had', 'be', 'been', 'being', 'this',
    'that', 'these', 'those', 'new', 'breaking', 'news', 'just', 'in',
    'according', 'reports', 'officials', 'confirmed', 'situation', 'developing',
    'what', 'happens', 'next', 'still', 'more', 'information', 'available',
    'here', 'know', 'so', 'far', 'we', 'you', 'they', 'it', 'he', 'she'
}

# Visual keyword mapping (topic → visual search)
VISUAL_MAP = {
    # Politics
    'trump': 'trump rally podium',
    'biden': 'white house exterior',
    'congress': 'capitol building',
    'senate': 'senate chamber',
    'supreme court': 'supreme court building',
    'white house': 'white house exterior',
    'election': 'voting ballot box',
    'vote': 'voting hands',
    'president': 'presidential podium',
    
    # Military/Conflict
    'russia': 'russian military',
    'ukraine': 'ukraine city',
    'missile': 'missile launch',
    'strike': 'explosion smoke',
    'war': 'soldiers marching',
    'military': 'military tanks',
    'attack': 'emergency response',
    'poland': 'poland border',
    'nato': 'nato flag',
    
    # Economy
    'tariff': 'shipping containers',
    'trade': 'cargo ship port',
    'economy': 'stock market chart',
    'market': 'trading floor',
    'inflation': 'grocery prices',
    'jobs': 'workers factory',
    'federal reserve': 'federal reserve building',
    
    # General news
    'fire': 'fire emergency',
    'crash': 'car accident',
    'police': 'police lights',
    'court': 'courtroom justice',
    'protest': 'protest crowd',
    'rally': 'political rally',
    'breaking': 'breaking news studio',
    'urgent': 'emergency alert',
    'crisis': 'emergency response',
    'leak': 'classified documents',
    'secret': 'hidden files',
    'scandal': 'press conference',
    
    # Tech
    'ai': 'artificial intelligence',
    'tech': 'technology data',
    'apple': 'apple store',
    'google': 'google office',
    'tesla': 'electric car',
    'spacex': 'rocket launch',
    
    # Health
    'covid': 'hospital medical',
    'vaccine': 'vaccine injection',
    'health': 'hospital corridor',
    'disease': 'medical research',
    
    # Climate
    'climate': 'climate change',
    'warming': 'melting ice',
    'storm': 'storm clouds',
    'hurricane': 'hurricane damage',
    'flood': 'flood water'
}


def extract_visual_keywords(text):
    """
    Extract visual keywords from a script sentence
    Returns list of search queries
    """
    text_lower = text.lower()
    
    # 1. Check for mapped keywords (most specific)
    matched_queries = []
    for key, visual in VISUAL_MAP.items():
        if key in text_lower:
            matched_queries.append(visual)
    
    if matched_queries:
        return matched_queries[:2]  # Max 2 per sentence
    
    # 2. Extract regular keywords
    words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    keywords = [w for w in words if w not in STOP_WORDS]
    
    if not keywords:
        return []
    
    # Return top 2 keywords as combined query
    return [" ".join(keywords[:2])]


def segment_script(script_text, num_segments=8):
    """
    Split script into segments for visual mapping
    """
    # Split by sentences
    sentences = re.split(r'[.!?]+', script_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if not sentences:
        return [script_text]
    
    # If too few sentences, split by words
    if len(sentences) < num_segments:
        words = script_text.split()
        chunk_size = max(3, len(words) // num_segments)
        
        sentences = []
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                sentences.append(chunk)
    
    return sentences[:num_segments]


def download_clip(video_url, timeout=30):
    """Download single clip"""
    try:
        r = requests.get(video_url, timeout=timeout, stream=True)
        if r.status_code != 200:
            return None
        
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tmp_path = tmp.name
        tmp.close()
        
        with open(tmp_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        
        if os.path.getsize(tmp_path) < 50000:
            os.remove(tmp_path)
            return None
        
        return tmp_path
    
    except Exception as e:
        logger.debug(f"Download failed: {e}")
        return None


def search_pexels(query, key, num=2):
    """Search Pexels for a specific query"""
    try:
        url = (
            f"https://api.pexels.com/videos/search"
            f"?query={requests.utils.quote(query)}"
            f"&per_page={num * 2}"
            f"&orientation=portrait&size=medium"
        )
        
        resp = requests.get(
            url,
            headers={"Authorization": key},
            timeout=20
        )
        
        if resp.status_code != 200:
            return []
        
        videos = resp.json().get('videos', [])
        
        if not videos:
            return []
        
        random.shuffle(videos)
        
        downloaded = []
        for v in videos:
            if len(downloaded) >= num:
                break
            
            try:
                files = sorted(v.get('video_files', []),
                             key=lambda x: x.get('width', 0))
                if not files:
                    continue
                
                link = files[-1].get('link')
                if not link:
                    continue
                
                path = download_clip(link)
                if path:
                    downloaded.append(path)
            
            except Exception as e:
                continue
        
        return downloaded
    
    except Exception as e:
        logger.debug(f"Search failed: {e}")
        return []


def find_assets_for_script(script_text, num_clips=16):
    """
    MAIN FUNCTION - Script-based visual finder
    
    Strategy:
    1. Split script into segments
    2. Extract visual keywords per segment
    3. Search Pexels for each keyword
    4. Guarantee minimum clips with fallbacks
    """
    key = os.getenv("PEXELS_API_KEY", "").strip()
    
    if not key:
        logger.warning("⚠️ PEXELS_API_KEY missing")
        return []
    
    logger.info(f"🎬 Script-based visual finder (need {num_clips} clips)")
    
    # 1. Segment script
    segments = segment_script(script_text, num_segments=num_clips)
    logger.info(f"📝 Script segmented into {len(segments)} parts")
    
    # 2. Extract keywords per segment
    segment_queries = []
    for seg in segments:
        queries = extract_visual_keywords(seg)
        if queries:
            segment_queries.append(queries[0])  # Top query per segment
        else:
            segment_queries.append("breaking news studio")  # Default
    
    logger.info(f"🔍 Queries: {segment_queries[:5]}...")
    
    # 3. Search Pexels for each query
    all_clips = []
    seen_paths = set()
    
    for i, query in enumerate(segment_queries):
        if len(all_clips) >= num_clips:
            break
        
        logger.info(f"🔍 [{i+1}/{len(segment_queries)}] Query: '{query}'")
        
        clips = search_pexels(query, key, num=2)
        
        for clip in clips:
            if clip not in seen_paths:
                all_clips.append(clip)
                seen_paths.add(clip)
        
        logger.info(f"   → {len(clips)} clips (total: {len(all_clips)})")
    
    # 4. Fallback - if not enough, use generic queries
    if len(all_clips) < num_clips:
        logger.warning(f"⚠️ Only {len(all_clips)} clips - using fallback queries")
        
        fallback_queries = [
            "breaking news studio",
            "world map digital",
            "city skyline night",
            "government building",
            "flag waving",
            "data screen",
            "newspaper printing",
            "camera crew",
            "news anchor desk",
            "emergency lights"
        ]
        
        random.shuffle(fallback_queries)
        
        for query in fallback_queries:
            if len(all_clips) >= num_clips:
                break
            
            clips = search_pexels(query, key, num=3)
            for clip in clips:
                if clip not in seen_paths:
                    all_clips.append(clip)
                    seen_paths.add(clip)
            
            logger.info(f"Fallback '{query}': {len(clips)} (total: {len(all_clips)})")
    
    logger.info(f"🎯 FINAL: {len(all_clips)} clips for {num_clips} needed")
    
    # Convert to asset dicts
    assets = []
    for path in all_clips:
        assets.append({
            'type': 'video',
            'path': path,
            'source': 'pexels',
            'license': 'Pexels License'
        })
    
    return assets


# ============================================================
# LEGACY COMPATIBILITY (for existing code)
# ============================================================

def find_assets_for_segments(segments, story):
    """
    Legacy wrapper - redirects to script-based finder
    """
    # Get script from story
    script = (
        story.get('short_script', '') or
        story.get('full_script', '') or
        story.get('title', '')
    )
    
    if not script:
        return []
    
    return find_assets_for_script(script, num_clips=16)


def find_background_music(mood='news'):
    """Find background music"""
    music_dir = "assets/music"
    if os.path.exists(music_dir):
        files = [f for f in os.listdir(music_dir)
                if f.endswith(('.mp3', '.wav'))]
        if files:
            return os.path.join(music_dir, random.choice(files))
    return None
