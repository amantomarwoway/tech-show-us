import os, random, requests, time, tempfile, glob, re
from pathlib import Path
from src.config import USER_AGENTS, pro_headers, pro_fetch
OUTPUT_ASSETS=Path("output/assets"); OUTPUT_ASSETS.mkdir(parents=True, exist_ok=True)

def pro_fetch_pexels_force(q):
    for attempt in range(10):
        try:
            time.sleep(random.uniform(0.05,0.2))
            key=os.getenv("PEXELS_API_KEY")
            if not key: raise RuntimeError("PEXELS_API_KEY missing - NO FALLBACK")
            h={"Authorization":key, **pro_headers()}
            url=f"https://api.pexels.com/videos/search?query={q}&per_page=5&orientation=portrait"
            r=requests.get(url, headers=h, timeout=12)
            if r.status_code==200:
                vids=r.json().get('videos',[])
                if vids:
                    link=sorted(vids[0]['video_files'], key=lambda x:x['width'])[-1]['link']
                    tmp=tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    open(tmp,'wb').write(requests.get(link, timeout=15, headers=pro_headers()).content)
                    if os.path.exists(tmp) and os.path.getsize(tmp)>1000:
                        return tmp
            print(f"[ASSET PRO] Pexels {r.status_code} retry {attempt} - FORCE")
            time.sleep((2**attempt)+random.uniform(0,0.5))
        except Exception as e:
            print(f"[ASSET PRO] Pexels fail {e} attempt {attempt} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError(f"Pexels failed for {q} - NO FALLBACK - FORCE")

def pro_fetch_duckduckgo_force(q):
    for attempt in range(10):
        try:
            time.sleep(random.uniform(0.05,0.2))
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                res=list(ddgs.images(q, max_results=2))
                if res:
                    url=res[0].get('image')
                    r=pro_fetch(url, timeout=12, retries=10)
                    p=OUTPUT_ASSETS/f"duck_{re.sub(r'\W+','_',q)[:20]}_{random.randint(1000,9999)}.jpg"
                    p.write_bytes(r.content)
                    if p.stat().st_size>1000:
                        return str(p)
            print(f"[ASSET PRO] DuckDuckGo empty retry {attempt} - FORCE")
        except Exception as e:
            print(f"[ASSET PRO] DuckDuckGo fail {e} attempt {attempt} - FORCE RETRY")
        time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError(f"DuckDuckGo failed for {q} - NO FALLBACK")

def fetch_all_assets(topic, keywords=None, script_visual_segments=None):
    results={"images":[],"videos":[],"segments":[]}
    if not script_visual_segments:
        raise RuntimeError("No script_visual_segments - NO FALLBACK")
    for seg in script_visual_segments[:8]:
        q=seg.get('visual_search_prompt','') or seg.get('segment_text','')
        if not q: raise RuntimeError("Empty visual_search_prompt - NO FALLBACK")
        # Force: Pexels > DuckDuckGo > no fallback
        try:
            path=pro_fetch_pexels_force(q)
        except:
            path=pro_fetch_duckduckgo_force(q)
        if path.endswith(('.jpg','.jpeg','.png')):
            results["images"].append(path)
            results["segments"].append({"type":"image","path":path,"duration":1.0,"prompt":q})
        else:
            results["videos"].append(path)
            results["segments"].append({"type":"video","path":path,"duration":1.8,"prompt":q})
    if not results["segments"]:
        raise RuntimeError("No assets fetched - NO FALLBACK - FORCE")
    print(f"[ASSET PRO] FORCE {len(results['images'])} images 1.0s {len(results['videos'])} videos 1.8s - NO FALLBACK")
    return results

def fetch_all_assets_god(topic="", keywords=None, script_visual_segments=None, *a, **k):
    if isinstance(topic, dict):
        t=topic.get('title',''); segs=topic.get('script_visual_segments')
        if not segs: raise RuntimeError("No segments in dict - NO FALLBACK")
        return fetch_all_assets(t, keywords=keywords, script_visual_segments=segs)
    return fetch_all_assets(topic, keywords=keywords, script_visual_segments=script_visual_segments)
