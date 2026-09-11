import os, re, random, time, requests, json
from src.config import USER_AGENTS, pro_headers, pro_fetch

def clean_topic_for_id(t):
    t=re.sub(r'/m/[a-z0-9]+','',t,flags=re.I); t=re.sub(r'\s+',' ',t).strip(); return t[:200]

def call_gemini_pro_force(prompt):
    for attempt in range(10):
        try:
            time.sleep(random.uniform(0.05,0.3))
            api_key=os.getenv("GEMINI_API_KEY")
            if not api_key: raise RuntimeError("GEMINI_API_KEY missing - NO FALLBACK")
            from google import genai
            client=genai.Client(api_key=api_key)
            for model in ["gemini-2.0-flash","gemini-1.5-flash"]:
                try:
                    resp=client.models.generate_content(model=model, contents=prompt+f" cb={random.randint(1000,9999)}")
                    text=getattr(resp,'text','')
                    if text and '{' in text: return text.strip()
                except Exception as e:
                    print(f"[SCRIPT PRO] Gemini {model} fail {e} - FORCE RETRY")
                    continue
        except Exception as e:
            print(f"[SCRIPT PRO] Attempt {attempt} fail {e} - FORCE RETRY")
            time.sleep((2**attempt)+random.uniform(0,0.5))
    raise RuntimeError("Gemini failed after 10 attempts - NO FALLBACK - FORCE")

def generate_script_final(news_input):
    if isinstance(news_input, dict): topic=news_input.get('title','')
    else: topic=str(news_input)
    topic=clean_topic_for_id(topic)
    if not topic: raise RuntimeError("Empty topic - NO FALLBACK")
    prompt=f"""Predict next 7 days search for: {topic}. Return JSON ONLY: {{"seo_youtube_title":"under 60 chars high CTR","seo_tags":["k1"],"full_script":"40-50 words 11-15 sec first sentence max shock","is_weekly_search_trend":true,"confidence_score":90,"script_visual_segments":[{{"segment_text":"...","asset_type":"video","visual_search_prompt":"Pentagon building exterior daytime"}}]}}"""
    raw=call_gemini_pro_force(prompt)
    m=re.search(r'\{.*\}', raw, re.DOTALL)
    if not m: raise RuntimeError(f"No JSON in Gemini response {raw[:100]} - NO FALLBACK")
    data=json.loads(m.group())
    if not data.get('seo_youtube_title') or not data.get('full_script'):
        raise RuntimeError(f"Incomplete JSON {data} - NO FALLBACK")
    data["title"]=data.get("seo_youtube_title", topic[:60])
    data["full_script"]=data.get("full_script","")[:500]
    data["description"]=data.get("full_script","")+" #breakingnews #worldnews"
    data["tags_all"]=" ".join(data.get("seo_tags",[]))
    data["viral_hook"]=data["title"][:50]
    data["white_bar_text"]=data["title"][:50]
    data["pexels_query"]=data.get("script_visual_segments",[{}])[0].get("visual_search_prompt","") if data.get("script_visual_segments") else topic[:30]
    return data
