# src/editor_god.py - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - DETAILED FIXED
import os, random, re

def clean_query(text):
    if not text: return "shocked man reaction white house"
    text = re.sub(r'\s+', ' ', str(text)).strip()
    words = [w for w in text.split() if len(w)>2][:5]
    return " ".join(words) if words else "shocked man reaction white house"

def fetch_pexels_visuals(query, num=5):
    """Pexels best visuals - portrait - optional - VUZA offline fallback"""
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        print(f"[EDITOR GOD] No PEXELS_API_KEY - VUZA offline mode for '{query}'")
        return [] # video_generator will use offline ColorClip - VUZA
    try:
        import requests
        h={"Authorization": key}
        q=clean_query(query)
        url=f"https://api.pexels.com/videos/search?query={q}&per_page={num}&orientation=portrait&size=medium"
        res=requests.get(url, headers=h, timeout=15).json()
        clips=[]
        for v in res.get('videos',[])[:num]:
            try:
                link=sorted(v['video_files'], key=lambda x: x['width'])[-1]['link']
                clips.append({"type":"video", "url": link, "query": q, "source": "pexels_vuza"})
            except: continue
        print(f"[EDITOR GOD] Pexels got {len(clips)} for '{q}' - VUZA")
        return clips
    except Exception as e:
        print(f"[EDITOR] Pexels fail {e} - VUZA offline fallback")
        return []

def fetch_vuza_offline_visuals(query_list):
    """VUZA / Open Montage offline visuals - 100% FREE - no API key needed"""
    offline=[]
    base_vuza = [
        "shocked man reaction white house breaking",
        "pentagon building exterior daytime secret",
        "family watching news shocked panic millions",
        "supreme court building exterior",
        "congress meeting behind closed doors leaked"
    ]

    for q in query_list[:4]:
        cq = clean_query(q)
        offline.append({
            "type": "prompt",
            "visual_search_prompt": cq,
            "source": "vuza_offline",
            "offline": True,
            "color": random.choice([(30,20,40), (40,20,30), (20,30,40)])
        })

    # Fill with base if less
    for bp in base_vuza:
        if len(offline) >= 6: break
        if not any(bp in o['visual_search_prompt'] for o in offline):
            offline.append({
                "type": "prompt",
                "visual_search_prompt": bp,
                "source": "vuza_offline",
                "offline": True
            })

    print(f"[EDITOR GOD] VUZA offline {len(offline)} visuals ready - 100% FREE")
    return offline

def fetch_pixabay_fallback(query, num=3):
    """Pixabay fallback - VUZA offline style"""
    key=os.getenv("PIXABAY_API_KEY")
    if not key:
        # Return VUZA offline prompt instead of empty
        return [{
            "type":"prompt",
            "visual_search_prompt": clean_query(query),
            "source":"vuza_offline",
            "offline": True
        }]
    try:
        import requests
        url=f"https://pixabay.com/api/videos/?key={key}&q={clean_query(query)}&per_page={num}"
        res=requests.get(url, timeout=10).json()
        clips=[]
        for hit in res.get('hits',[])[:num]:
            try:
                link=hit['videos']['medium']['url']
                clips.append({"type":"video", "url": link, "query": query, "source": "pixabay_vuza"})
            except: continue
        return clips
    except:
        return [{
            "type":"prompt",
            "visual_search_prompt": clean_query(query),
            "source":"vuza_offline",
            "offline": True
        }]

def editor_god_main(script_data, candidate):
    """
    Editor God - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - Best visuals har jagah se
    script_data: from generate_script_god with hook, retain, reward, script_visual_segments
    candidate: story with title, seo_youtube_title, muckscraper_source, grouped_topic
    Returns: {"segments": [...], "pexels_query": "...", "visuals": [...], "hook_visual": ..., "vuza_offline": True}
    """
    print("\n[EDITOR GOD - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - DETAILED] Starting - Best visuals VUZA offline + Pexels optional")

    title = candidate.get('title','') or script_data.get('seo_youtube_title','') if isinstance(script_data, dict) else ""
    seo_title = script_data.get('seo_youtube_title','') or title if isinstance(script_data, dict) else title

    # Hook/Retain/Reward - Automated-Shorts-Generator - Shashwat623 framework
    hook = script_data.get('hook','') if isinstance(script_data, dict) else ""
    retain = script_data.get('retain','') if isinstance(script_data, dict) else ""
    reward = script_data.get('reward','') if isinstance(script_data, dict) else ""
    short_script = script_data.get('short_script','') if isinstance(script_data, dict) else ""

    # MuckScraper - grouped topic + source
    grouped_topic = candidate.get('grouped_topic','') or candidate.get('grouped','') or script_data.get('grouped_topic','') if isinstance(script_data, dict) else ""
    muckscraper_source = candidate.get('source','') or candidate.get('muckscraper_source','') or ""

    # Visual segments from script - detailed + Hook/Retain/Reward
    script_segments = script_data.get('script_visual_segments',[]) if isinstance(script_data, dict) else []

    # Build pexels query - best from title + hook
    pexels_query = seo_title[:40] or title[:40]
    pexels_query = clean_query(pexels_query)

    # Best visual prompts - priority Hook/Retain/Reward
    best_prompt = ""
    hook_visual = retain_visual = reward_visual = ""

    if hook:
        hook_visual = clean_query(hook)
        best_prompt = hook_visual
        print(f"[EDITOR GOD] HOOK visual: {hook_visual}")

    if retain and not best_prompt:
        retain_visual = clean_query(retain)
        best_prompt = retain_visual
    elif retain:
        retain_visual = clean_query(retain)

    if reward:
        reward_visual = clean_query(reward)

    if not best_prompt:
        if script_segments:
            for seg in script_segments:
                vp = seg.get('visual_search_prompt','')
                if vp and len(vp)>5:
                    best_prompt = clean_query(vp)
                    break
        if not best_prompt:
            best_prompt = pexels_query

    # Ensure hook/retain/reward visuals have fallback
    if not hook_visual: hook_visual = best_prompt or "shocked man reaction white house breaking"
    if not retain_visual: retain_visual = clean_query(retain) if retain else "pentagon building secret meeting"
    if not reward_visual: reward_visual = clean_query(reward) if reward else "family panic watching news"

    print(f"[EDITOR GOD] Title: {title[:60]}")
    print(f"[EDITOR GOD] MuckScraper source: {muckscraper_source} Grouped: {grouped_topic[:40] if grouped_topic else 'N/A'}")
    print(f"[EDITOR GOD] Pexels query: {pexels_query}")
    print(f"[EDITOR GOD] Hook: {hook_visual} | Retain: {retain_visual} | Reward: {reward_visual}")

    # Fetch best visuals - Pexels first (if key), then VUZA offline - 100% FREE
    all_visuals = []

    # Pexels - portrait 9:16 - optional - VUZA offline fallback
    for q in [hook_visual, retain_visual, reward_visual][:2]:
        pexels_visuals = fetch_pexels_visuals(q, num=4)
        all_visuals.extend(pexels_visuals)

    # VUZA offline visuals - ALWAYS available - 100% FREE - Open Montage style
    vuza_queries = [hook_visual, retain_visual, reward_visual, best_prompt, pexels_query]
    vuza_visuals = fetch_vuza_offline_visuals(vuza_queries)
    all_visuals.extend(vuza_visuals)

    # If still less than 5, try Pixabay fallback
    if len([v for v in all_visuals if not v.get('offline')]) < 3:
        pixabay_visuals = fetch_pixabay_fallback(best_prompt, num=3)
        all_visuals.extend(pixabay_visuals)

    # Search prompts for video_generator's DuckDuckGo + yt-dlp best - VUZA offline
    search_prompts = []
    # Priority Hook/Retain/Reward
    if hook_visual: search_prompts.append(hook_visual)
    if retain_visual: search_prompts.append(retain_visual)
    if reward_visual: search_prompts.append(reward_visual)

    if script_segments:
        for seg in script_segments[:6]:
            prompt = seg.get('visual_search_prompt','') or seg.get('segment_text','')[:40]
            if prompt:
                cq = clean_query(prompt)
                if cq not in search_prompts:
                    search_prompts.append(cq)
    else:
        if title:
            words = title.split()[:6]
            sp = " ".join(words)
            if clean_query(sp) not in search_prompts:
                search_prompts.append(clean_query(sp))

    # Ensure at least 3 prompts
    if len(search_prompts) < 3:
        search_prompts.extend(["shocked man reaction white house", "pentagon building secret", "family panic news"])

    # Final editor data - detailed - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE
    editor_data = {
        "segments": script_segments,
        "pexels_query": pexels_query,
        "best_visual_prompt": best_prompt,
        "hook_visual": hook_visual,
        "retain_visual": retain_visual,
        "reward_visual": reward_visual,
        "visuals": all_visuals,
        "search_prompts": search_prompts[:6],
        "title": seo_title,
        "viral_hook": script_data.get('viral_hook','') or hook or seo_title if isinstance(script_data, dict) else seo_title,
        "first_sentence_punch": script_data.get('first_sentence_punch','') or hook or seo_title[:60] if isinstance(script_data, dict) else seo_title[:60],
        "hook": hook,
        "retain": retain,
        "reward": reward,
        "short_script": short_script,
        "grouped_topic": grouped_topic,
        "muckscraper_source": muckscraper_source,
        "vuza_offline": True,
        "offline_visuals": [v for v in all_visuals if v.get('offline')],
        "vuza_queries": vuza_queries
    }

    print(f"[EDITOR GOD - VUZA OFFLINE] Final: {len(all_visuals)} visuals ({len([v for v in all_visuals if v.get('offline')])} offline) + {len(search_prompts)} search prompts - HOOK/RETAIN/REWARD ready - MUCKSCRAPER {muckscraper_source}")

    return editor_data
