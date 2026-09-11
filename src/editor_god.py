import os, random, re, json, requests, glob, subprocess, tempfile
from pathlib import Path
try:
    from src.config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION, WIDTH, HEIGHT, FPS_CHOICES
except:
    from config import GOD_INSTRUCTION, IMAGE_DURATION, CLIP_DURATION, WIDTH, HEIGHT, FPS_CHOICES
OUTPUT = Path("output"); OUTPUT.mkdir(exist_ok=True)
TEMP = Path("temp"); TEMP.mkdir(exist_ok=True)
USER_AGENTS=["Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Mozilla/5.0 (Macintosh)"]
def clean_id(t):
    if not t: return ""
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\b[mM][0-9][a-z0-9]+\b','',t); t=re.sub(r'\s+',' ',t).strip(); return t
def call_gemini_or_openai(prompt):
    gem_key=os.getenv("GEMINI_API_KEY","")
    if gem_key:
        try:
            from google import genai
            client=genai.Client(api_key=gem_key)
            for model in ["gemini-2.0-flash","gemini-1.5-flash","gemini-2.0-flash-exp"]:
                try:
                    resp=client.models.generate_content(model=model, contents=prompt)
                    text=getattr(resp,'text',None)
                    if text and len(text)>20: return text
                except: continue
        except: pass
    open_key=os.getenv("OPENAI_API_KEY","")
    if open_key:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=open_key)
            resp=client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.9, max_tokens=1200)
            return resp.choices[0].message.content
        except: pass
    return None
def generate_visual_segments(full_script):
    prompt=f"""Break script into 6-8 segments. Each = 1 sentence. For each give exact visual search prompt like if script says 'Pentagon deployed' prompt='Pentagon building exterior daytime'. Script: {full_script} Return JSON only: [{{"segment_text":"...","asset_type":"video or image","visual_search_prompt":"...","emotion":"...","sound_hint":"..."}}]"""
    raw=call_gemini_or_openai(prompt)
    if raw:
        try:
            m=re.search(r'\[.*\]', raw, re.DOTALL)
            if m:
                data=json.loads(m.group())
                if len(data)>=4: return data[:8]
        except: pass
    sentences=re.split(r'[.!?]+', full_script); sentences=[s.strip() for s in sentences if len(s.strip())>5][:8]
    segs=[]
    for i,s in enumerate(sentences):
        at="video" if i%2==0 else "image"; prompt=s; low=s.lower()
        if "pentagon" in low: prompt="Pentagon building exterior daytime"
        elif "white house" in low: prompt="White House exterior Washington DC"
        elif "supreme court" in low: prompt="Supreme Court building USA"
        elif "trump" in low or "biden" in low: prompt="US Capitol building crowd"
        elif "shocked" in low or "breaking" in low: prompt="shocked reaction face dramatic"
        elif "police" in low or "fbi" in low: prompt="police cars lights night"
        segs.append({"segment_text":s,"asset_type":at,"visual_search_prompt":prompt,"emotion":"tense","sound_hint":"whoosh"})
    return segs
def fetch_best_visual(prompt, asset_type="video"):
    # 1 DuckDuckGo
    if asset_type=="image":
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results=list(ddgs.images(prompt, max_results=3))
                if results:
                    for r in results[:2]:
                        url=r.get('image') or r.get('thumbnail')
                        if not url: continue
                        try:
                            resp=requests.get(url, timeout=12, headers={"User-Agent":random.choice(USER_AGENTS)})
                            if resp.status_code==200 and len(resp.content)>5000:
                                path=TEMP / f"duck_{random.randint(1000,9999)}.jpg"
                                path.write_bytes(resp.content)
                                print(f"[EDITOR_GOD] Best visual DuckDuckGo: {prompt}")
                                return str(path), "image"
                        except: continue
        except: pass
    if asset_type=="video":
        try:
            import yt_dlp
            out_tmpl=str(TEMP / f"ytdlp_{random.randint(1000,9999)}_%(id)s.%(ext)s")
            ydl_opts={'format':'best[height<=720][ext=mp4]/best','outtmpl':out_tmpl,'quiet':True,'no_warnings':True,'noplaylist':True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(f"ytsearch2:{prompt}", download=True)
            files=glob.glob(str(TEMP / f"ytdlp_*.*"))
            if files:
                files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return files[0], "video"
        except: pass
    pex_key=os.getenv("PEXELS_API_KEY","")
    if pex_key:
        try:
            if asset_type=="image":
                r=requests.get("https://api.pexels.com/v1/search", headers={"Authorization":pex_key}, params={"query":prompt,"per_page":3}, timeout=10)
                data=r.json()
                if data.get("photos"):
                    url=data["photos"][0]["src"]["large"]
                    resp=requests.get(url, timeout=10)
                    path=TEMP / f"pexels_{random.randint(1000,9999)}.jpg"
                    path.write_bytes(resp.content)
                    return str(path), "image"
            else:
                r=requests.get("https://api.pexels.com/videos/search", headers={"Authorization":pex_key}, params={"query":prompt,"per_page":2,"orientation":"portrait"}, timeout=10)
                data=r.json()
                if data.get("videos"):
                    link=data["videos"][0]["video_files"][0]["link"]
                    resp=requests.get(link, timeout=15)
                    path=TEMP / f"pexels_{random.randint(1000,9999)}.mp4"
                    path.write_bytes(resp.content)
                    return str(path), "video"
        except: pass
    pix_key=os.getenv("PIXABAY_API_KEY","") or os.getenv("PIXABAY_KEY","")
    if pix_key and asset_type=="video":
        try:
            r=requests.get("https://pixabay.com/api/videos/", params={"key":pix_key,"q":prompt,"per_page":3}, timeout=10)
            data=r.json()
            if data.get("hits"):
                url=data["hits"][0]["videos"]["medium"]["url"]
                resp=requests.get(url, timeout=15)
                path=TEMP / f"pixabay_{random.randint(1000,9999)}.mp4"
                path.write_bytes(resp.content)
                return str(path), "video"
        except: pass
    uns_key=os.getenv("UNSPLASH_ACCESS_KEY","")
    if uns_key and asset_type=="image":
        try:
            r=requests.get("https://api.unsplash.com/search/photos", params={"query":prompt,"per_page":1}, headers={"Authorization":f"Client-ID {uns_key}"}, timeout=10)
            data=r.json()
            if data.get("results"):
                url=data["results"][0]["urls"]["regular"]
                resp=requests.get(url, timeout=10)
                path=TEMP / f"unsplash_{random.randint(1000,9999)}.jpg"
                path.write_bytes(resp.content)
                return str(path), "image"
        except: pass
    return None, None
def editor_god_main(script_data, story_data):
    print(GOD_INSTRUCTION)
    print("[LEG2 EDITOR_GOD] A to Z editing - best visuals from everywhere")
    full_script=script_data.get('full_script','') if isinstance(script_data,dict) else str(script_data)
    full_script=clean_id(full_script)
    if len(full_script.split())>50: full_script=" ".join(full_script.split()[:50])
    segments=script_data.get('script_visual_segments') if isinstance(script_data,dict) else None
    if not segments: segments=generate_visual_segments(full_script)
    assets=[]
    for seg in segments[:8]:
        prompt=seg.get('visual_search_prompt','') or seg.get('segment_text','')
        atype=seg.get('asset_type','video')
        path, typ=fetch_best_visual(prompt, atype)
        if path: assets.append({"path":path,"type":typ,"duration":1.8 if typ=="video" else 1.0,"segment":seg,"prompt":prompt})
    print(f"[LEG2] Collected {len(assets)} best visuals")
    return {"full_script":full_script,"segments":segments,"assets":assets,"title":script_data.get('title','') if isinstance(script_data,dict) else full_script[:60],"seo_title":script_data.get('seo_youtube_title','') if isinstance(script_data,dict) else full_script[:60],"description":story_data.get('description','') if isinstance(story_data,dict) else "","tags":story_data.get('tags',[]) if isinstance(story_data,dict) else [],"hashtags":story_data.get('hashtags',[]) if isinstance(story_data,dict) else []}
