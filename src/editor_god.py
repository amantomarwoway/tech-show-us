import os, random, time, re, glob
from pathlib import Path
from src.config import USER_AGENTS, pro_headers, pro_fetch, RETENTION_CONFIG
from src.asset_fetcher import fetch_all_assets

def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\s+',' ',t).strip(); return t

def editor_god_main(cand):
    print("[EDITOR GOD] Frame-by-frame exact visual, 1.0s image + 1.8s clip, 10+ sound layers - NO FALLBACK - FORCE")
    from src.script_generator import generate_script_final
    script_data=generate_script_final(cand) # Force, no fallback
    topic=cand.get('title','')
    segments=script_data.get('script_visual_segments',[])
    if not segments:
        raise RuntimeError("No visual segments - NO FALLBACK")
    assets=fetch_all_assets(topic, script_data.get('seo_tags'), segments) # Force fetch, no color fallback
    if not assets.get('segments'):
        raise RuntimeError("No assets fetched - NO FALLBACK - FORCE")
    merged={**cand, **script_data, **assets}
    merged['full_script']=script_data.get('full_script','') or script_data.get('short_script','')
    merged['title']=script_data.get('seo_youtube_title','')
    from src.video_generator import create_video
    video_path=create_video(merged, cand) # Force Piper TTS, no gTTS fallback
    if not os.path.exists(video_path):
        raise RuntimeError(f"Video not created {video_path} - NO FALLBACK")
    return {"video_path":video_path, "segments":segments, "assets":assets, "full_script":merged['full_script'], "seo_youtube_title":merged['title'], "description":script_data.get('description',''), "tags_all":script_data.get('tags_all',''), "confidence_score":script_data.get('confidence_score',85), "is_weekly_search_trend":script_data.get('is_weekly_search_trend',True)}
