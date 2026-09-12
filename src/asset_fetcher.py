# src/asset_fetcher.py - REAL AEROPLANE - DETAILED FIXED - Har jagah se best visuals
import os, requests, random, re, tempfile

def clean_q(text):
    if not text: return "shocked man reaction"
    text = re.sub(r'\s+', ' ', text).strip()
    words = [w for w in text.split() if len(w)>2][:4]
    return " ".join(words) if words else "shocked man reaction"

def fetch_pexels_best(query, num=8):
    """Pexels portrait best - detailed"""
    clips=[]
    key=os.getenv("PEXELS_API_KEY")
    if not key: return []
    try:
        h={"Authorization": key}
        q=clean_q(query)
        url=f"https://api.pexels.com/videos/search?query={q}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url, headers=h, timeout=15).json()
        for v in res.get('videos',[])[:num]:
            try:
                files=sorted(v['video_files'], key=lambda x: x['width'])
                link=files[-1]['link']
                # Download to temp
                r=requests.get(link, timeout=20, stream=True)
                if r.status_code!=200: continue
                tmp=tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                path=tmp.name; tmp.close()
                with open(path,'wb') as f:
                    for chunk in r.iter_content(8192):
                        if chunk: f.write(chunk)
                if os.path.getsize(path)<50000:
                    os.remove(path); continue
                clips.append({"path": path, "query": q, "source": "pexels"})
            except: continue
        print(f"[ASSET GOD] Pexels got {len(clips)} for '{q}'")
    except Exception as e:
        print(f"[ASSET] Pexels fail {e}")
    return clips

def fetch_duckduckgo_prompts(query_list):
    """DuckDuckGo search prompts - for yt-dlp fallback - detailed"""
    # video_generator already uses DuckDuckGo + yt-dlp
    # This just returns search prompts
    prompts=[]
    for q in query_list[:5]:
        cq=clean_q(q)
        if cq not in prompts:
            prompts.append(cq)
    print(f"[ASSET GOD] DuckDuckGo prompts: {prompts}")
    return prompts

def fetch_pixabay_best(query, num=3):
    """Pixabay fallback"""
    clips=[]
    key=os.getenv("PIXABAY_API_KEY")
    if not key:
        return [{"visual_search_prompt": clean_q(query), "source":"duckduckgo"}]
    try:
        url=f"https://pixabay.com/api/videos/?key={key}&q={clean_q(query)}&per_page={num}"
        res=requests.get(url, timeout=10).json()
        for hit in res.get('hits',[])[:num]:
            try:
                link=hit['videos']['medium']['url']
                clips.append({"url": link, "query": query, "source": "pixabay"})
            except: continue
    except: pass
    return clips

def fetch_all_assets_god(script_data, candidate=None, visual_segments=None):
    """
    Fetch all assets god - best tarike se kahin se bhi
    script_data: dict with seo_youtube_title, script_visual_segments
    Returns dict for editor_god / video_generator
    """
    print("\n[ASSET FETCHER GOD - DETAILED] Fetching best visuals from everywhere")

    title=""
    if isinstance(candidate, dict):
        title=candidate.get('title','')
    if isinstance(script_data, dict):
        title=script_data.get('seo_youtube_title','') or title

    if not title:
        title="White House Shocker Shatters Families Tonight"

    # Visual segments
    segments=visual_segments or (script_data.get('script_visual_segments',[]) if isinstance(script_data, dict) else [])

    best_prompts=[]
    if segments:
        for seg in segments[:6]:
            vp=seg.get('visual_search_prompt','') or seg.get('segment_text','')[:30]
            if vp:
                best_prompts.append(clean_q(vp))
    else:
        best_prompts=[clean_q(title)]

    # Fetch
    all_assets=[]
    # Pexels best
    for prompt in best_prompts[:2]:
        assets=fetch_pexels_best(prompt, num=4)
        all_assets.extend(assets)

    # Pixabay if less than 5
    if len(all_assets)<5:
        for prompt in best_prompts[:2]:
            pix=fetch_pixabay_best(prompt, num=3)
            all_assets.extend(pix)

    # DuckDuckGo prompts for yt-dlp
    dd_prompts=fetch_duckduckgo_prompts(best_prompts)

    final={
        "assets": all_assets,
        "search_prompts": dd_prompts,
        "pexels_query": clean_q(title),
        "best_visual_prompt": best_prompts[0] if best_prompts else clean_q(title),
        "segments": segments
    }

    print(f"[ASSET FETCHER GOD] Final {len(all_assets)} assets + {len(dd_prompts)} prompts - detailed ready")

    return final

# For backward compatibility
def fetch_all_assets(query, num=5):
    return fetch_pexels_best(query, num)
