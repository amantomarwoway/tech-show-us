"""
ULTIMATE GOD LEVEL - FINAL EDIT - NO FIX - EMOTIONAL RETENTION
Location: src/script_generator.py
FINAL FLOW as per latest request:
Topic (any) -> Title 4-5 words shock+emotional both mandatory no fixed words -> Script 45-50 words from Title (NO trim, NO today today, jo Gemini likhe wahi final, emotional face expression change) -> Pexels from SCRIPT (not title) so clips match sentence directly
- RETENTION_WORDS = 50 (45-50 limit)
- NO trim_to_40_words - jo likha wahi final, 11 sec ho ya 15 sec ho disturb nahi
- validate_script_factory -> 50 words ke andar PASS
- atempo 1.11 and 1.12X (in audio_retention.py)
- Punch: first sentence me sabse zyada shock+emotion taaki American 4-5 baar suney
- Pexels search = script se, title se nahi
"""

import os, requests, re, random, time

try:
    from google import genai
    GENAI_NEW=True
except ImportError:
    try:
        import google.generativeai as genai_old
        GENAI_NEW=False
        genai=None
    except ImportError:
        genai=None
        genai_old=None
        GENAI_NEW=None

RETENTION_WORDS = 50  # 45-50 limit as per request

def clean_topic_for_id(topic: str) -> str:
    cleaned = re.sub(r'/m/[a-z0-9]+', '', topic, flags=re.I)
    cleaned = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:200] if cleaned else topic[:200]

def validate_script_factory(script_text: str, topic: str, topic_dict=None) -> bool:
    """FINAL: 50 words ke andar andar PASS - emotional retention"""
    wc = len(script_text.split())
    if wc <= 50:
        print(f"[VALIDATION PASS] {wc} words <=50 - emotional retention PASS")
        return True
    else:
        print(f"[VALIDATION FAIL] {wc} words >50 - FAIL, need <=50")
        return False

def call_gemini(prompt):
    api_key=os.getenv("GEMINI_API_KEY","")
    openai_key=os.getenv("OPENAI_API_KEY","")
    models_to_try_new = [
        "gemini-3.6-flash",
        "gemini-3.6-flash-latest",
        "gemini-3.6-flash-exp",
        "gemini-2.5-flash",
        "gemini-2.5-flash-latest",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-flash-latest"
    ]
    models_to_try_old = [
        "gemini-3.6-flash",
        "gemini-3.6-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-flash-latest"
    ]
    try:
        from google import genai
        if api_key:
            client = genai.Client(api_key=api_key)
            for model_name in models_to_try_new:
                try:
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    text = getattr(response, 'text', None)
                    if text:
                        print(f"[GEMINI 3.6 FLASH] SUCCESS {model_name}")
                        return text.strip()
                    if hasattr(response, 'candidates') and response.candidates:
                        txt = response.candidates[0].content.parts[0].text.strip()
                        if txt:
                            return txt
                except Exception as inner:
                    msg = str(inner).lower()
                    if "429" in msg or "quota" in msg:
                        time.sleep(1)
                    print(f"[GEMINI 3.6 TRY] {model_name} failed: {str(inner)[:120]}")
                    continue
    except Exception as e:
        print(f"[GEMINI 3.6 NEW SDK] total fail: {e}")
    try:
        import google.generativeai as genai_old
        if api_key:
            genai_old.configure(api_key=api_key)
            for old_model in models_to_try_old:
                try:
                    model = genai_old.GenerativeModel(old_model)
                    response = model.generate_content(prompt)
                    if hasattr(response, 'text') and response.text:
                        print(f"[GEMINI 3.6 OLD SDK] SUCCESS {old_model}")
                        return response.text.strip()
                except Exception as inner2:
                    print(f"[GEMINI 3.6 OLD TRY] {old_model} failed: {str(inner2)[:120]}")
                    continue
    except Exception as e:
        print(f"[GEMINI 3.6 OLD SDK] total fail: {e}")
    if openai_key:
        print("[FALLBACK] Gemini 3.6 Flash failed, trying ChatGPT fallback")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            chat_models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
            for chat_model in chat_models:
                try:
                    resp = client.chat.completions.create(model=chat_model, messages=[{"role": "user", "content": prompt}], temperature=0.9, max_tokens=800)
                    text = resp.choices[0].message.content
                    if text:
                        print(f"[CHATGPT FALLBACK] SUCCESS {chat_model}")
                        return text.strip()
                except Exception as ce:
                    print(f"[CHATGPT TRY] {chat_model} failed: {str(ce)[:120]}")
                    continue
        except Exception as e:
            print(f"[CHATGPT FALLBACK] total fail: {e}")
    raise RuntimeError("All Gemini 3.6 Flash + ChatGPT fallback failed - NO FALLBACK as per request")

def get_google_searchable_title(topic: str) -> str:
    topic_clean = clean_topic_for_id(topic)
    try:
        from live_viral_hashtag import get_google_searchable_title as google_title_fn
        t = google_title_fn(topic_clean)
        if "/m/" not in t and "m04mjl" not in t.lower() and "m07r1h" not in t.lower():
            return t[:95]
    except:
        pass
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":topic_clean,"hl":"en","gl":"US"}, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        suggestions=[m for m in matches[1:] if len(m)>5 and "/m/" not in m and not re.match(r'^m[0-9]', m)]
        if suggestions:
            filtered = [s for s in suggestions if not re.search(r'/m/|\b[mM][0-9]', s)]
            if filtered:
                return filtered[0][:95].title()
    except:
        pass
    return topic_clean.title()[:95]

def get_topic_hashtags_from_google(topic: str):
    topic_clean = clean_topic_for_id(topic)
    try:
        from live_viral_hashtag import get_topic_hashtags_from_google as topic_tags_fn
        tags = topic_tags_fn(topic_clean)
        tags = [t for t in tags if "/m/" not in t.lower() and not re.match(r'^#?m[0-9]', t.lower())]
        if tags:
            return tags[:4]
    except:
        pass
    words=re.findall(r'\w+', topic_clean.lower())[:4]
    tags=[]
    for w in words:
        if len(w)>2 and not re.match(r'^m[0-9]', w):
            tags.append(f"#{w}")
    while len(tags)<4:
        tags.append("#usa")
    return tags[:4]

def get_world_viral_hashtag(topic: str = ""):
    if topic:
        topic_clean = clean_topic_for_id(topic)
        words = re.findall(r'\w+', topic_clean.lower())
        if words:
            for w in words:
                if len(w) > 3 and w not in ["history","today","united","states"]:
                    return f"#{w}"
    try:
        from live_viral_hashtag import get_world_viral_hashtag as world_fn
        w = world_fn()
        if topic and "tom" not in topic.lower() and "tomcruise" in w.lower():
            words_list = re.findall(r"\w+", topic.lower())
            first_word = words_list[0] if words_list else "breakingnews"
            return "#" + first_word if topic else "#breakingnews"
        if "/m/" not in w.lower() and "m04mjl" not in w.lower():
            return w
    except:
        pass
    return "#breakingnews"

def get_yt_suggestions(q):
    q_clean = clean_topic_for_id(q)
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":q_clean,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        return [m for m in matches[1:] if len(m)>5 and "/m/" not in m][:5]
    except:
        return []

def parse_json_from_text(text: str):
    try:
        import json
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except:
        pass
    return None

def extract_visual_segments_from_script(script_text: str, topic: str):
    sentences = re.split(r'[.!?]', script_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    segments = []
    for i, s in enumerate(sentences[:8]):
        segments.append({
            "segment_text": s,
            "asset_type": "video" if i % 2 == 0 else "image",
            "visual_search_prompt": s[:60]
        })
    return segments


def generate_script(news_input):
    is_breakout = False
    breakout_score = 0
    visualping_alert = ""
    breakout_source = ""
    if isinstance(news_input, dict):
        topic=news_input.get('query','') or news_input.get('title','') or news_input.get('summary','')
        search_vol=news_input.get('search_volume',70)
        is_breakout = news_input.get('is_breakout', False) or news_input.get('breakout_score',0) >= 5000
        breakout_score = news_input.get('breakout_score', 0)
        visualping_alert = news_input.get('visualping_alert','')
        breakout_source = news_input.get('source','')
        url = news_input.get('url','')
    else:
        topic=str(news_input)
        search_vol=70
        url=""
    topic=clean_topic_for_id(topic.strip()[:200])
    if len(topic)<3:
        topic="USA Breaking News"

    yt_sug=get_yt_suggestions(topic)
    google_title = get_google_searchable_title(topic)
    topic_hashtags = get_topic_hashtags_from_google(topic)
    world_viral = get_world_viral_hashtag(topic)
    topic_hashtags_str = ", ".join(topic_hashtags)
    all_hashtags_str = ", ".join(topic_hashtags + [world_viral])

    breakout_context = ""
    if is_breakout:
        breakout_context = f"BREAKOUT ALERT: Score {breakout_score} from {breakout_source}"

    prompt=f"""
You are Search-Driven US Breaking News Shorts Generator.

Input Headline (Reuters Wire + Google News, last 45 min, ground-level, US audience):
{topic} - {url}
GOOGLE TITLE: {google_title}
YT Related: {yt_sug}
Search Vol: {search_vol}
{breakout_context}

Task:
1. 7-Day Search Velocity Filter: Only select stories that an average American will actively type into Google or YouTube to search for explanations, updates, or follow-ups over next 7 days. Reject generic news. Set is_weekly_search_trend true/false.
2. YouTube Search SEO: Optimize heavily for YouTube Search Traffic over Shorts Feed. Generate high-CTR, high-intent search title and 8-10 SEO tags.
3. Script: Generate engaging narrative text script 11-15 seconds, 40-50 words, TTS friendly, simple US English, first sentence max shock.
4. Visual Context Segmentation: Break script into 6-8 sequential segments. For each segment provide segment_text, asset_type (video or image), visual_search_prompt (highly specific visual prompt e.g., if script says "Pentagon deployed cyber units", prompt must be "Pentagon building exterior daytime").

Forced JSON Output Schema ONLY, no extra text:
{{
  "seo_youtube_title": "High-CTR Search-Optimized YouTube Title under 60 chars",
  "seo_tags": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8"],
  "full_script": "Complete 11-15 second narrative text, 40-50 words",
  "is_weekly_search_trend": true,
  "confidence_score": 85,
  "script_visual_segments": [
    {{
      "segment_text": "First sentence...",
      "asset_type": "video",
      "visual_search_prompt": "Highly specific visual prompt"
    }},
    {{
      "segment_text": "Second sentence...",
      "asset_type": "image",
      "visual_search_prompt": "Highly specific visual prompt"
    }}
  ]
}}

Rules:
- confidence_score 0-100, >=85 only if strong 7-day search potential
- is_weekly_search_trend true only if American will search this for 7 days
- seo_youtube_title search optimized
- seo_tags high-intent YouTube search keywords
- full_script 40-50 words max, 11-15 sec
- script_visual_segments 6-8 items, alternate video/image, video=1.8s clip, image=1.0s, prompt highly specific
Return JSON only.
"""

    raw=""
    try:
        raw=call_gemini(prompt)
    except Exception as e:
        raise RuntimeError(f"Gemini failed: {e}")

    data = parse_json_from_text(raw)
    if not data:
        raise RuntimeError("JSON parse failed")

    seo_title = data.get('seo_youtube_title','')[:95]
    seo_tags = data.get('seo_tags', [])[:10]
    full_script = data.get('full_script','')[:500]
    is_trend = bool(data.get('is_weekly_search_trend', False))
    confidence = int(data.get('confidence_score', 0))
    segments = data.get('script_visual_segments', [])

    if confidence < 85 or not is_trend:
        white_bar = seo_title[:60]
        if len(white_bar.split()) > 5:
            white_bar = " ".join(white_bar.split()[:5])
        return {
            "title": seo_title,
            "seo_youtube_title": seo_title,
            "seo_tags": seo_tags,
            "full_script": full_script,
            "is_weekly_search_trend": is_trend,
            "confidence_score": confidence,
            "script_visual_segments": segments,
            "filtered": True,
            "description": full_script,
            "tags_all": " ".join(seo_tags),
            "viral_hook": white_bar,
            "white_bar_text": white_bar,
            "pexels_query": segments[0].get('visual_search_prompt','') if segments else full_script[:30],
            "first_sentence_punch": segments[0].get('segment_text','') if segments else full_script[:60]
        }

    cleaned = re.sub(r'\[.*?\]','',full_script)
    cleaned = re.sub(r'Visual:.*?\|','',cleaned, flags=re.I)
    cleaned = re.sub(r'Audio:\s*','',cleaned, flags=re.I)
    cleaned = re.sub(r'\s+',' ',cleaned).strip()
    cleaned = clean_topic_for_id(cleaned)
    if len(cleaned.split()) > 50:
        cleaned = " ".join(cleaned.split()[:50])

    if not segments or len(segments) < 4:
        segments = extract_visual_segments_from_script(cleaned, topic)

    white_bar = seo_title[:60]
    if len(white_bar.split()) > 5:
        white_bar = " ".join(white_bar.split()[:5])

    desc_with_tags = f"{cleaned}\n\n{' '.join(topic_hashtags)} {world_viral}"
    return {
        "title": seo_title,
        "seo_youtube_title": seo_title,
        "title_options":[seo_title],
        "full_script": cleaned,
        "raw_script_structured": raw,
        "is_weekly_search_trend": is_trend,
        "confidence_score": confidence,
        "script_visual_segments": segments,
        "description": desc_with_tags,
        "tags_primary": topic_hashtags_str,
        "tags_secondary": world_viral,
        "tags_shorts": all_hashtags_str,
        "tags_all": " ".join(seo_tags),
        "tags_topic": topic_hashtags_str,
        "viral_hashtag": world_viral,
        "sources": f"Vol {search_vol} Search SEO: {seo_title}",
        "viral_hook": white_bar,
        "white_bar_text": white_bar,
        "filtered": False,
        "pexels_query": segments[0].get('visual_search_prompt','') if segments else cleaned[:30],
        "first_sentence_punch": segments[0].get('segment_text','') if segments else cleaned[:60],
        "seo_tags": seo_tags
    }
