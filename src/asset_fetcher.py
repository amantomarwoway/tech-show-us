# src/asset_fetcher.py - VUZA / OPEN MONTAGE - 100% FREE OFFLINE - DETAILED FIXED
import os, random, re

def clean_q(text):
    if not text: return "shocked man reaction white house"
    text = re.sub(r'\s+', ' ', str(text)).strip()
    words = [w for w in text.split() if len(w)>2][:5]
    return " ".join(words) if words else "shocked man reaction white house"

def fetch_pexels_best(query, num=8):
    """Pexels best - optional - VUZA offline fallback"""
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        print(f"[ASSET GOD] No PEXELS_API_KEY - VUZA offline mode for '{query}'")
        return [] # video_generator will use offline ColorClip

    try:
        import requests, tempfile
        h = {"Authorization": key}
        q = clean_q(query)
        url = f"https://api.pexels.com/videos/search?query={q}&per_page={num}&orientation=portrait&size=medium"
        res = requests.get(url, headers=h, timeout=15).json()
        clips = []
        for v in res.get('videos', [])[:num]:
            try:
                files = sorted(v['video_files'], key=lambda x: x['width'])
                link = files[-1]['link']
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                path = tmp.name; tmp.close()
                r = requests.get(link, timeout=20, stream=True)
                if r.status_code!= 200: continue
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        if chunk: f.write(chunk)
                if os.path.getsize(path) < 50000:
                    os.remove(path); continue
                clips.append({"path": path, "query": q, "source": "pexels_vuza"})
            except: continue
        print(f"[ASSET GOD] Pexels got {len(clips)} for '{q}' - VUZA")
        return clips
    except Exception as e:
        print(f"[ASSET] Pexels fail {e} - VUZA offline fallback")
        return []

def fetch_duckduckgo_prompts(query_list):
    """DuckDuckGo search prompts - 100% FREE - no API key - VUZA + yt-dlp fallback"""
    prompts = []
    for q in query_list[:6]:
        cq = clean_q(q)
        # Make viral for retention
        if "white house" not in cq.lower() and "shocking" not in cq.lower():
            cq = f"{cq} shocking reaction"
        if cq not in prompts:
            prompts.append(cq)

    # Add Hook/Retain/Reward prompts if available
    print(f"[ASSET GOD] DuckDuckGo VUZA prompts (100% FREE): {prompts}")
    return prompts

def fetch_vuza_offline_prompts(query_list):
    """VUZA / Open Montage offline prompts - 100% FREE - no API needed"""
    offline = []
    base_prompts = [
        "shocked man reaction white house breaking",
        "pentagon building exterior daytime",
        "family watching news shocked panic",
        "supreme court building exterior",
        "congress meeting behind closed doors"
    ]

    for q in query_list[:3]:
        offline.append({
            "visual_search_prompt": clean_q(q),
            "source": "vuza_offline",
            "offline": True,
            "color": random.choice([(30,20,40), (40,20,30), (20,30,40)])
        })

    # Fill with base if less
    for bp in base_prompts:
        if len(offline) >= 5: break
        if not any(bp in o['visual_search_prompt'] for o in offline):
            offline.append({"visual_search_prompt": bp, "source": "vuza_offline", "offline": True})

    print(f"[ASSET GOD] VUZA offline {len(offline)} prompts ready - 100% FREE")
    return offline

def fetch_all_assets_god(script_data, candidate=None, visual_segments=None):
    """
    Fetch all assets god - VUZA OFFLINE - 100% FREE - best tarike se kahin se bhi
    script_data: dict with hook, retain, reward, seo_youtube_title, script_visual_segments
    Returns dict for editor_god / video_generator
    """
    print("\n[ASSET FETCHER GOD - VUZA OFFLINE - 100% FREE] Fetching best visuals")

    title = ""
    hook = retain = reward = ""
    if isinstance(candidate, dict):
        title = candidate.get('title','')

    if isinstance(script_data, dict):
        title = script_data.get('seo_youtube_title','') or script_data.get('title','') or title
        hook = script_data.get('hook','')
        retain = script_data.get('retain','')
        reward = script_data.get('reward','')

    if not title:
        title = "White House Shocker Shatters Families Tonight - Leaked"

    # Visual segments - Hook/Retain/Reward support - Automated-Shorts-Generator
    segments = visual_segments or (script_data.get('script_visual_segments',[]) if isinstance(script_data, dict) else [])

    best_prompts = []
    # Priority: Hook, Retain, Reward - Shashwat623 framework
    if hook: best_prompts.append(clean_q(hook))
    if retain: best_prompts.append(clean_q(retain))
    if reward: best_prompts.append(clean_q(reward))

    if segments:
        for seg in segments[:6]:
            vp = seg.get('visual_search_prompt','') or seg.get('segment_text','')[:40]
            if vp and clean_q(vp) not in best_prompts:
                best_prompts.append(clean_q(vp))
    else:
        if clean_q(title) not in best_prompts:
            best_prompts.append(clean_q(title))

    # Ensure at least 3 prompts
    if len(best_prompts) < 3:
        best_prompts.extend(["shocked man reaction white house", "pentagon building secret", "family panic news"])

    # Fetch - try Pexels if key, else VUZA offline
    all_assets = []
    # Try Pexels for first 2 prompts if key exists - else skip
    for prompt in best_prompts[:2]:
        assets = fetch_pexels_best(prompt, num=3)
        all_assets.extend(assets)

    # VUZA offline prompts - always available - 100% FREE
    vuza_offline = fetch_vuza_offline_prompts(best_prompts)
    all_assets.extend(vuza_offline)

    # DuckDuckGo prompts for yt-dlp - 100% FREE
    dd_prompts = fetch_duckduckgo_prompts(best_prompts)

    final = {
        "assets": all_assets,
        "search_prompts": dd_prompts,
        "pexels_query": clean_q(title),
        "best_visual_prompt": best_prompts[0] if best_prompts else clean_q(title),
        "segments": segments,
        "hook_visual": clean_q(hook) if hook else best_prompts[0],
        "retain_visual": clean_q(retain) if retain else best_prompts[1] if len(best_prompts)>1 else best_prompts[0],
        "reward_visual": clean_q(reward) if reward else best_prompts[2] if len(best_prompts)>2 else best_prompts[0],
        "vuza_offline": True, # Flag for video_generator to use offline mode
        "offline_assets": vuza_offline
    }

    print(f"[ASSET FETCHER GOD - VUZA] Final {len(all_assets)} assets ({len(vuza_offline)} offline) + {len(dd_prompts)} prompts - 100% FREE ready")

    return final

# For backward compatibility
def fetch_all_assets(query, num=5):
    return fetch_pexels_best(query, num)
