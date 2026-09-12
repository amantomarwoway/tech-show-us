# src/editor_god.py - REAL AEROPLANE - DETAILED FIXED - Best visuals kahin se bhi
import os, requests, random, re

def clean_query(text):
    if not text: return "shocked man reaction"
    text = re.sub(r'\s+', ' ', text).strip()
    words = [w for w in text.split() if len(w)>2][:4]
    return " ".join(words) if words else "shocked man reaction"

def fetch_pexels_visuals(query, num=5):
    """Pexels best visuals - portrait"""
    clips=[]
    key=os.getenv("PEXELS_API_KEY")
    if not key: return []
    try:
        h={"Authorization": key}
        q=clean_query(query)
        url=f"https://api.pexels.com/videos/search?query={q}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url, headers=h, timeout=15).json()
        for v in res.get('videos',[])[:num]:
            try:
                link=sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
                clips.append({"type":"video", "url": link, "query": q, "source": "pexels"})
            except: continue
        print(f"[EDITOR GOD] Pexels got {len(clips)} for '{q}'")
    except Exception as e:
        print(f"[EDITOR] Pexels fail {e}")
    return clips

def fetch_pixabay_fallback(query, num=3):
    """Pixabay fallback - free images if Pexels fail"""
    clips=[]
    try:
        # Pixabay API optional - if key not present, use DuckDuckGo style search prompt
        key=os.getenv("PIXABAY_API_KEY")
        if not key:
            # Return search prompts for video_generator to use DuckDuckGo + yt-dlp
            return [{"type":"prompt", "visual_search_prompt": clean_query(query), "source":"duckduckgo"}]

        url=f"https://pixabay.com/api/videos/?key={key}&q={clean_query(query)}&per_page={num}"
        res=requests.get(url, timeout=10).json()
        for hit in res.get('hits',[])[:num]:
            try:
                link=hit['videos']['medium']['url']
                clips.append({"type":"video", "url": link, "query": query, "source": "pixabay"})
            except: continue
    except: pass
    return clips

def editor_god_main(script_data, candidate):
    """
    Editor God - Best visuals har jagah se
    script_data: from generate_script_god with script_visual_segments
    candidate: story with title, seo_youtube_title
    Returns: {"segments": [...], "pexels_query": "...", "visuals": [...]}
    """
    print("\n[EDITOR GOD - DETAILED] Starting - Best visuals DuckDuckGo + Pexels + Pixabay + yt-dlp")

    title=candidate.get('title','') or script_data.get('seo_youtube_title','')
    seo_title=script_data.get('seo_youtube_title','') or title

    # Visual segments from script - detailed
    script_segments=script_data.get('script_visual_segments',[]) or []

    # Build pexels query - best from title
    # Example: "White House Shocker" -> "white house shocking"
    pexels_query=seo_title[:40]
    if not pexels_query:
        pexels_query=title[:40]

    # Clean for search
    pexels_query=clean_query(pexels_query)

    # If script has visual_search_prompt, use best one
    best_prompt=""
    if script_segments:
        # Pick first with visual_search_prompt
        for seg in script_segments:
            vp=seg.get('visual_search_prompt','')
            if vp and len(vp)>5:
                best_prompt=vp
                break

    if not best_prompt:
        best_prompt=pexels_query

    print(f"[EDITOR GOD] Title: {title[:60]}")
    print(f"[EDITOR GOD] Pexels query: {pexels_query}")
    print(f"[EDITOR GOD] Best visual prompt: {best_prompt}")

    # Fetch best visuals - Pexels first, then Pixabay, then DuckDuckGo prompts
    all_visuals=[]

    # Pexels - portrait 9:16
    pexels_visuals=fetch_pexels_visuals(best_prompt, num=8)
    all_visuals.extend(pexels_visuals)

    # If Pexels gave less than 5, try Pixabay fallback
    if len(all_visuals) < 5:
        pixabay_visuals=fetch_pixabay_fallback(best_prompt, num=5)
        all_visuals.extend(pixabay_visuals)

    # Detailed: Always include search prompts for video_generator's DuckDuckGo + yt-dlp best
    # video_generator will use these prompts to fetch free clips
    search_prompts=[]
    if script_segments:
        for seg in script_segments[:8]:
            prompt=seg.get('visual_search_prompt','') or seg.get('segment_text','')[:30]
            if prompt:
                search_prompts.append(clean_query(prompt))
    else:
        # From title
        words=title.split()[:6]
        search_prompts.append(" ".join(words))

    # Final editor data - detailed
    editor_data={
        "segments": script_segments,
        "pexels_query": pexels_query,
        "best_visual_prompt": best_prompt,
        "visuals": all_visuals,
        "search_prompts": search_prompts,
        "title": seo_title,
        "viral_hook": script_data.get('viral_hook','') or seo_title,
        "first_sentence_punch": script_data.get('first_sentence_punch','') or seo_title[:60]
    }

    print(f"[EDITOR GOD] Final: {len(all_visuals)} visuals + {len(search_prompts)} search prompts - detailed ready")

    return editor_data
