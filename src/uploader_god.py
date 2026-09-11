import os, random, time, requests, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src.config import USER_AGENTS, pro_headers, pro_fetch, ENGLISH_COUNTRIES
from src.youtube_uploader import upload_video

def pro_translate_gemini_force(text, country):
    for attempt in range(10):
        try:
            time.sleep(random.uniform(0.05,0.3))
            import os
            api_key=os.getenv("GEMINI_API_KEY")
            if not api_key: raise RuntimeError("GEMINI_API_KEY missing - NO FALLBACK")
            from google import genai
            client=genai.Client(api_key=api_key)
            prompt=f"Translate and localize for {country} audience, high CTR under 60 chars: {text}. Return only translated title."
            resp=client.models.generate_content(model="gemini-2.0-flash", contents=prompt+f" cb={random.randint(1000,9999)}")
            t=getattr(resp,'text','')
            if t: return t.strip()[:95]
        except Exception as e:
            print(f"[UPLOADER PRO] Translate fail {e} attempt {attempt} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError(f"Translate failed for {country} - NO FALLBACK")

def generate_thumbnail_per_country_force(title, country):
    for attempt in range(10):
        try:
            img=Image.new('RGB',(1080,1920),(random.randint(10,30),random.randint(10,30),random.randint(40,80)))
            d=ImageDraw.Draw(img)
            try: f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            except: f=ImageFont.load_default()
            d.text((540,800), f"{country.upper()}", font=f, fill="#FFEB3B", anchor="mm")
            d.text((540,960), title[:40], font=f, fill="white", anchor="mm")
            os.makedirs("output", exist_ok=True)
            p=f"output/thumb_{country}_{random.randint(1000,9999)}.jpg"
            img.save(p)
            if os.path.exists(p): return p
        except Exception as e:
            print(f"[UPLOADER PRO] Thumb fail {e} attempt {attempt} - FORCE")
            time.sleep((2**attempt)+random.uniform(0,0.3))
    raise RuntimeError(f"Thumbnail failed for {country} - NO FALLBACK")

def uploader_god_main(video_path, editor_data, cand, boss_data):
    print("[UPLOADER GOD] Per country title/thumb/dubbing - NO FALLBACK - FORCE - PRO HACKER")
    yt_ids=[]
    countries=boss_data.get('target_countries', ENGLISH_COUNTRIES[:5])[:5]
    if not countries:
        raise RuntimeError("No target countries - NO FALLBACK")
    for country in countries:
        title_local=pro_translate_gemini_force(editor_data.get('seo_youtube_title','') or cand.get('title',''), country)
        desc_local=editor_data.get('description','')[:200]
        thumb=generate_thumbnail_per_country_force(title_local, country)
        final_video=video_path
        for attempt in range(10):
            try:
                yt_id=upload_video(final_video, thumb, {"title":title_local,"description":desc_local,"tags_all":editor_data.get('tags_all','')}, cand)
                if yt_id:
                    yt_ids.append({"country":country,"yt_id":yt_id,"title":title_local})
                    print(f"[UPLOADER GOD PRO] Uploaded {country}: https://youtu.be/{yt_id} - FORCE")
                    break
                else:
                    raise RuntimeError(f"Upload returned None for {country}")
            except Exception as e:
                print(f"[UPLOADER GOD PRO] Upload fail {country} attempt {attempt} {e} - FORCE RETRY")
                time.sleep((2**attempt)+random.uniform(0,1))
                if attempt==9:
                    raise RuntimeError(f"Upload failed for {country} after 10 attempts - NO FALLBACK")
    if not yt_ids:
        raise RuntimeError("All uploads failed - NO FALLBACK")
    return yt_ids
