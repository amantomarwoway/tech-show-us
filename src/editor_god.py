import os, random, re, json, requests, glob, subprocess, tempfile
from pathlib import Path
try:
    from src.config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION, WIDTH, HEIGHT, FPS_CHOICES, USER_AGENTS, pro_headers, pro_fetch
except:
    from config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION, WIDTH, HEIGHT, FPS_CHOICES
    USER_AGENTS=["Mozilla/5.0"]
    def pro_headers(): return {"User-Agent": random.choice(USER_AGENTS)}
    def pro_fetch(url, timeout=10, retries=10):
        for _ in range(retries):
            try:
                r=requests.get(url, headers=pro_headers(), timeout=timeout)
                if r.status_code==200: return r
            except: pass
        raise RuntimeError(f"Fetch failed {url}")

OUTPUT = Path("output"); OUTPUT.mkdir(exist_ok=True)
TEMP = Path("temp"); TEMP.mkdir(exist_ok=True)

def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I)
    temp = re.sub(r'\b[mM][0-9][a-z0-9]+\b','',t)
    t=re.sub(r'\s+',' ',temp).strip()
    return t

def call_gemini_or_openai_force(prompt):
    for attempt in range(10):
        try:
            gem_key=os.getenv("GEMINI_API_KEY","")
            if not gem_key: raise RuntimeError("GEMINI_API_KEY missing")
            from google import genai
            client=genai.Client(api_key=gem_key)
            for model in ["gemini-2.0-flash","gemini-1.5-flash"]:
                try:
                    resp=client.models.generate_content(model=model, contents=prompt)
                    text=getattr(resp,'text',None)
                    if text and len(text)>20: return text
                except: continue
        except Exception as e:
            print(f"[EDITOR PRO] Gemini attempt {attempt} fail {e} - FORCE RETRY")
            time.sleep((2**attempt)+0.3)
    raise RuntimeError("Gemini failed after 10 - NO FALLBACK")

def generate_visual_segments(full_script):
    prompt=f"Break script into 6-8 segments. Each = 1 sentence. For each give exact visual search prompt like if script says 'Pentagon deployed' prompt='Pentagon building exterior daytime'. Script: {full_script} Return JSON only: [{{'segment_text':'...','asset_type':'video or image','visual_search_prompt':'...'}}]"
    raw=call_gemini_or_openai_force(prompt)
    m=re.search(r'\[.*\]', raw, re.DOTALL)
    if m:
        data=json.loads(m.group())
        if len(data)>=4: return data[:8]
    raise RuntimeError("No visual segments generated - NO FALLBACK")

def fetch_best_visual_force(prompt, asset_type="video"):
    # FIXED: no backslash inside f-string
    safe_name = clean_id(prompt)
    safe_name = re.sub(r'\W+', '_', safe_name)[:20]
    rand_num = random.randint(1000,9999)
    for attempt in range(10):
        try:
            if asset_type=="image":
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results=list(ddgs.images(prompt, max_results=3))
                    if not results: raise RuntimeError("DuckDuckGo empty")
                    for r in results[:2]:
                        url=r.get('image') or r.get('thumbnail')
                        if not url: continue
                        resp=pro_fetch(url, timeout=12, retries=10)
                        path=TEMP / f"duck_{safe_name}_{rand_num}.jpg"
                        path.write_bytes(resp.content)
                        print(f"[EDITOR_GOD PRO] DuckDuckGo: {prompt} - FORCE")
                        return str(path), "image"
            else:
                import yt_dlp
                out_tmpl=str(TEMP / f"ytdlp_{rand_num}_%(id)s.%(ext)s")
                ydl_opts={'format':'best[height<=720][ext=mp4]/best','outtmpl':out_tmpl,'quiet':True,'no_warnings':True,'noplaylist':True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(f"ytsearch2:{prompt}", download=True)
                files=glob.glob(str(TEMP / f"ytdlp_*.*"))
                if not files: raise RuntimeError("yt-dlp no files")
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return files[0], "video"
        except Exception as e:
            print(f"[EDITOR PRO] Visual fetch fail {e} attempt {attempt} - FORCE RETRY")
            time.sleep((2**attempt)+0.3)
    raise RuntimeError(f"Visual fetch failed {prompt} - NO FALLBACK")

def editor_god_main(script_data, story_data):
    print("[LEG2 EDITOR_GOD] A to Z editing - NO FALLBACK - FORCE - PRO HACKER")
    full_script=script_data.get('full_script','') if isinstance(script_data,dict) else str(script_data)
    full_script=clean_id(full_script)
    if len(full_script.split())>50: full_script=" ".join(full_script.split()[:50])
    if not full_script: raise RuntimeError("Empty script - NO FALLBACK")
    segments=script_data.get('script_visual_segments') if isinstance(script_data,dict) else None
    if not segments: segments=generate_visual_segments(full_script)
    assets=[]
    for seg in segments[:8]:
        prompt=seg.get('visual_search_prompt','') or seg.get('segment_text','')
        if not prompt: raise RuntimeError("Empty prompt - NO FALLBACK")
        atype=seg.get('asset_type','video')
        path, typ=fetch_best_visual_force(prompt, atype)
        assets.append({"path":path,"type":typ,"duration":1.8 if typ=="video" else 1.0,"segment":seg,"prompt":prompt})
    print(f"[LEG2 PRO FORCE] Collected {len(assets)} visuals - NO FALLBACK")
    return {"full_script":full_script,"segments":segments,"assets":assets,"title":script_data.get('title','') if isinstance(script_data,dict) else full_script[:60],"seo_title":script_data.get('seo_youtube_title','') if isinstance(script_data,dict) else full_script[:60]}
