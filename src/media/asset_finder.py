"""
src/media/asset_finder.py - STRONG SCRIPT-BASED VISUAL FINDER
Multiple strategies for max relevance
"""

import os
import re
import random
import requests
import tempfile
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Comprehensive visual mapping
VISUAL_MAP = {
    # Politics
    'trump': 'trump rally',
    'biden': 'white house',
    'congress': 'capitol building',
    'senate': 'senate chamber',
    'supreme court': 'supreme court building',
    'white house': 'white house exterior',
    'election': 'voting ballot',
    'vote': 'voting hands',
    'president': 'presidential podium',
    'democrat': 'capitol building',
    'republican': 'capitol building',
    
    # Military/Conflict
    'russia': 'russian military parade',
    'russian': 'russian military',
    'ukraine': 'ukraine city street',
    'missile': 'missile launch',
    'strike': 'explosion smoke',
    'war': 'soldiers marching',
    'military': 'military tanks',
    'attack': 'emergency response',
    'poland': 'poland city',
    'nato': 'nato flag',
    'army': 'army soldiers',
    'troops': 'soldiers',
    'weapons': 'weapons military',
    'kyiv': 'kyiv city',
    
    # Economy
    'tariff': 'shipping containers port',
    'trade': 'cargo ship',
    'economy': 'stock market chart',
    'market': 'trading floor',
    'inflation': 'grocery store',
    'jobs': 'factory workers',
    'federal reserve': 'federal reserve',
    'dollar': 'dollar bills',
    'money': 'money cash',
    'cost': 'expensive price tag',
    'price': 'shopping prices',
    'stocks': 'stock market screen',
    'million': 'wealth money',
    'billion': 'city skyline',
    
    # General news
    'fire': 'fire flames emergency',
    'crash': 'car accident',
    'police': 'police lights night',
    'court': 'courtroom gavel',
    'protest': 'protest crowd',
    'rally': 'political rally',
    'breaking': 'breaking news studio',
    'urgent': 'emergency alert',
    'crisis': 'emergency response',
    'leak': 'classified documents',
    'leaked': 'documents papers',
    'secret': 'hidden mystery',
    'scandal': 'press conference',
    'warning': 'warning sign',
    'danger': 'danger alert',
    'alert': 'emergency alert',
    'disaster': 'natural disaster',
    'flood': 'flood water',
    'storm': 'storm clouds',
    'earthquake': 'earthquake damage',
    
    # Tech
    'ai': 'artificial intelligence',
    'artificial': 'AI robot',
    'tech': 'technology computer',
    'apple': 'apple store iphone',
    'google': 'google office',
    'tesla': 'electric car',
    'spacex': 'rocket launch',
    'space': 'space rocket',
    'nasa': 'nasa rocket',
    'launch': 'rocket launch',
    'satellite': 'satellite space',
    'robot': 'robot technology',
    'cyber': 'cyber security',
    'hack': 'hacker computer',
    
    # Health
    'covid': 'hospital medical',
    'vaccine': 'vaccine injection',
    'health': 'hospital corridor',
    'disease': 'medical research',
    'doctor': 'doctor hospital',
    'hospital': 'hospital building',
    
    # Climate
    'climate': 'climate change glacier',
    'warming': 'melting ice',
    'hurricane': 'hurricane damage',
    'wildfire': 'forest fire',
    
    # Society
    'family': 'family walking',
    'children': 'children playing',
    'school': 'school classroom',
    'student': 'students studying',
    'workers': 'construction workers',
    'immigration': 'airport travelers',
    'border': 'border fence',
    
    # Person emotions
    'shock': 'shocked person',
    'angry': 'angry man',
    'sad': 'sad person',
    'happy': 'happy person',
    'fear': 'scared person',
    'panic': 'panic crowd',
    'cry': 'crying person',
    'worried': 'worried person',
}

# Stop words
STOP_WORDS = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to',
    'for', 'of', 'and', 'or', 'but', 'with', 'from', 'by', 'as', 'says',
    'said', 'will', 'has', 'have', 'had', 'be', 'been', 'being', 'this',
    'that', 'these', 'those', 'new', 'breaking', 'news', 'just',
    'according', 'reports', 'officials', 'confirmed', 'situation', 'developing',
    'what', 'happens', 'next', 'still', 'more', 'information', 'available',
    'here', 'know', 'so', 'far', 'we', 'you', 'they', 'it', 'he', 'she',
    'than', 'then', 'their', 'there', 'these', 'about', 'after', 'also'
}


def extract_key_entities(text):
    """Extract key entities from text - 3 words MAX per query"""
    text_lower = text.lower()
    
    # 1. Find mapped queries (MOST SPECIFIC)
    mapped = []
    for key, query in VISUAL_MAP.items():
        if key in text_lower:
            mapped.append(query)
    
    # 2. Extract top keywords
    words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    keywords = [w for w in words if w not in STOP_WORDS]
    
    return mapped, keywords


def download_clip(video_url, timeout=30):
    """Download clip"""
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
    except:
        return None


def search_pexels_videos(query, key, num=3):
    """Search Pexels videos"""
    try:
        url = (
            f"https://api.pexels.com/videos/search"
            f"?query={requests.utils.quote(query)}"
            f"&per_page={num * 3}"
            f"&orientation=portrait"
            f"&size=medium"
        )
        
        resp = requests.get(url, headers={"Authorization": key}, timeout=20)
        
        if resp.status_code != 200:
            logger.warning(f"   Pexels videos status {resp.status_code}")
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
            except:
                continue
        
        return downloaded
    except Exception as e:
        logger.warning(f"   Pexels video failed: {e}")
        return []


def find_assets_for_script(script_text, num_clips=16):
    """
    STRONG script-based visual finder
    - Splits script into sentences
    - Extracts keywords per sentence
    - 3 search strategies
    """
    key = os.getenv("PEXELS_API_KEY", "").strip()
    
    if not key:
        logger.warning("⚠️ PEXELS_API_KEY missing")
        return []
    
    logger.info(f"🎬 Script-based visual finder (need {num_clips} clips)")
    
    # ============================================================
    # SPLIT SCRIPT INTO SENTENCES
    # ============================================================
    
    sentences = re.split(r'[.!?]+', script_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 8]
    
    if not sentences:
        sentences = [script_text]
    
    logger.info(f"📝 Script split into {len(sentences)} sentences")
    
    # ============================================================
    # BUILD QUERIES PER SENTENCE
    # ============================================================
    
    all_queries = []
    
    for sent in sentences:
        # Get mapped queries + keywords
        mapped, keywords = extract_key_entities(sent)
        
        # Priority 1: Mapped queries (most specific)
        if mapped:
            all_queries.append(mapped[0])
        
        # Priority 2: Top 2 keywords combined
        if len(keywords) >= 2:
            all_queries.append(" ".join(keywords[:2]))
        elif keywords:
            all_queries.append(keywords[0])
    
    # Deduplicate while keeping order
    seen = set()
    unique_queries = []
    for q in all_queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)
    
    logger.info(f"🔍 {len(unique_queries)} unique queries")
    logger.info(f"   Sample: {unique_queries[:5]}")
    
    # ============================================================
    # SEARCH PEXELS FOR EACH QUERY
    # ============================================================
    
    all_clips = []
    seen_paths = set()
    
    for i, query in enumerate(unique_queries):
        if len(all_clips) >= num_clips:
            break
        
        logger.info(f"🔍 [{i+1}/{len(unique_queries)}] '{query}'")
        
        # Get 2-3 clips per query
        clips = search_pexels_videos(query, key, num=2)
        
        for clip in clips:
            if clip not in seen_paths:
                all_clips.append(clip)
                seen_paths.add(clip)
        
        logger.info(f"   → {len(clips)} clips (total: {len(all_clips)})")
    
    # ============================================================
    # FALLBACK: generic news queries
    # ============================================================
    
    if len(all_clips) < num_clips:
        logger.warning(f"⚠️ Only {len(all_clips)}/{num_clips} - using fallbacks")
        
        fallback_queries = [
            "breaking news studio",
            "world map digital",
            "city skyline night",
            "government building",
            "flag waving",
            "news anchor desk",
            "camera crew filming",
            "newspaper printing",
            "emergency lights",
            "data screen"
        ]
        
        random.shuffle(fallback_queries)
        
        for fq in fallback_queries:
            if len(all_clips) >= num_clips:
                break
            
            clips = search_pexels_videos(fq, key, num=2)
            for clip in clips:
                if clip not in seen_paths:
                    all_clips.append(clip)
                    seen_paths.add(clip)
    
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


def find_assets_for_segments(segments, story):
    """Legacy wrapper"""
    script = (
        story.get('short_script', '') or
        story.get('full_script', '') or
        story.get('title', '')
    )
    return find_assets_for_script(script, num_clips=16) if script else []


def find_background_music(mood='news'):
    """Find background music"""
    music_dir = "assets/music"
    if os.path.exists(music_dir):
        files = [f for f in os.listdir(music_dir)
                if f.endswith(('.mp3', '.wav'))]
        if files:
            return os.path.join(music_dir, random.choice(files))
    return None
