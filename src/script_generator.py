"""
ULTIMATE GOD LEVEL - FINAL EDIT - 50 WORDS FLEXIBLE - 0.8s EMOTIONAL CLIPS ONLY
Location: src/script_generator.py
FINAL FLOW as per latest request:
Topic (any) -> Title 4-5 words shock+emotional both mandatory no fixed words -> Script UP TO 50 WORDS flexible (50 tak koi rok nahi, Gemini ko bolna hai 50 ke andar hi 100% accuracy) -> Pexels from SCRIPT (not title) -> Video 0.8s clips ONLY emotional/shock, no low-emotion clips

- RETENTION_WORDS = 50 (up to 50 flexible, no rok)
- NO trim_to_40_words - jo Gemini likhe wahi final, 11-15 sec variable
- validate_script_factory -> 50 words tak PASS
- atempo 1.11 and 1.12X (in audio_retention.py)
- Punch: first sentence max shock+emotion
- Pexels from SCRIPT, 0.8s clip ONLY emotional/shock
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

RETENTION_WORDS = 50  # 50 tak flexible - koi rok nahi, max 50

def clean_topic_for_id(topic: str) -> str:
    cleaned = re.sub(r'/m/[a-z0-9]+', '', topic, flags=re.I)
    cleaned = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:200] if cleaned else topic[:200]

def validate_script_factory(script_text: str, topic: str, topic_dict=None) -> bool:
    """FINAL: 50 words tak flexible - koi rok nahi, 50 ke andar PASS"""
    wc = len(script_text.split())
    if wc <= 50:
        print(f"[VALIDATION PASS] {wc} words <=50 - flexible PASS")
        return True
    else:
        print(f"[VALIDATION FAIL] {wc} words >50 - FAIL")
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
    raise RuntimeError("All Gemini 3.6 Flash + ChatGPT fallback failed - NO FALLBACK")

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

def extract_pexels_keywords_from_script(script_text: str, topic: str):
    """
    PEXELS FROM SCRIPT + 0.8s EMOTIONAL/SHOCK CLIPS ONLY
    - Script ke sentence direct clip le sake
    - Har clip 0.8 sec fix, sirf emotional/shock wali clips
    """
    sentences = re.split(r'[.!?]', script_text)
    first_sentence = sentences[0] if sentences else script_text[:100]
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', script_text.lower())
    stop_words = {"this","that","with","from","have","been","will","they","them","what","when","where","which","about","could","would","should"}
    keywords = [w for w in words if w not in stop_words][:6]
    
    first_words = re.findall(r'\b[a-zA-Z]{4,}\b', first_sentence.lower())
    first_keywords = [w for w in first_words if w not in stop_words][:3]
    
    all_keywords = first_keywords + keywords + [topic.split()[0] if topic.split() else "breaking"]
    
    seen = set()
    unique_keywords = []
    for k in all_keywords:
        if k not in seen and len(k) > 3:
            seen.add(k)
            unique_keywords.append(k)
        if len(unique_keywords) >= 4:
            break
    
    pexels_query = " ".join(unique_keywords[:3])
    
    # Emotional/shock keywords for Pexels filtering
    emotional_boosters = ["shocked", "crying", "emotional", "breaking", "dramatic", "intense", "reaction"]
    
    return {
        "pexels_query": pexels_query,
        "first_sentence": first_sentence,
        "keywords": unique_keywords,
        "emotional_keywords": emotional_boosters,
        "clip_duration": 0.8,
        "clip_filter": "emotional_shock_only",
        "script_based": True
    }

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
    else:
        topic=str(news_input)
        search_vol=70
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
        breakout_context = f"BREAKOUT ALERT: Score {breakout_score} from {breakout_source} - {visualping_alert}"

    prompt=f"""
You are VIRAL USA YouTube Shorts script writer - EMOTIONAL RETENTION GOD. {breakout_context}

TOPIC: {topic}
GOOGLE TITLE: {google_title}
YT Related: {yt_sug}
Search Vol: {search_vol}

MANDATORY RULES - 100% ACCURACY - 50 WORDS KE ANDAR:

FLOW: Topic -> Title -> Script -> Pexels (from SCRIPT, 0.8s emotional/shock clips only)
1. TOPIC ayega - kaisa bhi aaye
2. Chahe TOPIC kaisa bhi ho, usko SHOCK + EMOTIONAL tarike se dikhana hai - aise ki sunne wale ke face expression change ho jaye
3. TITLE: 4-5 words, SHOCK + EMOTION dono mandatory, topic related, NO FIXED WORDS
4. SCRIPT: 50 WORDS TAK FLEXIBLE - 50 tak koi rok nahi, lekin 100% ACCURACY ke sath 50 words ke andar hi honi chaiye. Kabhi bhi 50 se zyada nahi. Jo Gemini likhe wahi final - extra mat jodo, kaato mat, today today mat jodo. Script chahe 11 sec me khatam ho, 13 sec me, 15 sec me - disturb mat karna. Sabse important: SHURU KA SENTENCE me sabse zyada SHOCK + EMOTION hona chaiye taki American banda 4-5 baar wahi sune laut kar. Emotional retention punch.
5. Pexels: SCRIPT se keywords nikal ke clip lega (TITLE se nahi), har clip 0.8 second ki hi hogi, aur sirf wahi clips add karni hai jisme emotion aur shockness ki kami na ho bilkul bhi - low emotion clips bilkul nahi

TITLE RULES - NO FIXED WORDS:
- EXACTLY 4-5 words ONLY
- SHOCK + EMOTIONAL both mandatory
- Topic related
- NO FIXED WORDS

SCRIPT RULES - 50 WORDS TAK FLEXIBLE 100% ACCURACY:
- MAX 50 WORDS - 50 tak koi rok nahi, lekin 100% accuracy ke sath 50 ke andar hi honi chaiye, 50 se zyada kabhi nahi
- NO trimming, NO extra adding - jo likha wahi final
- First sentence = MOST SHOCK + EMOTION - punch that makes American replay 4-5 times
- Full script emotional, face expression change
- Simple USA English, TTS friendly
- Pexels: 0.8s clips, emotional/shock only, no low-emotion clips

RETURN EXACTLY:
TITLE: <4-5 words shock+emotion both topic related no fixed words>
WHITE_BAR: <same as TITLE 4-5 words>
SCRIPT: <UP TO 50 WORDS - 50 ke andar 100% accuracy, first sentence max shock+emotion, emotional retention>
DESCRIPTION:
Para1: Hook line with max emotion
Para2: WHAT HAPPENED 1 line about {topic}
Para3: WHY IT MATTERS 1 line for USA emotional impact
"""

    raw=""
    try:
        raw=call_gemini(prompt)
    except Exception as e:
        print(f"[GEMINI ERROR - NO FALLBACK] {topic} - {e}")
        raise RuntimeError(f"Gemini failed - NO FALLBACK: {e}")

    selected=""; full_vo=""; description=""; white_bar_parsed=""
    try:
        if "TITLE:" in raw:
            after_title = raw.split("TITLE:")[1]
            for delim in ["WHITE_BAR:", "SCRIPT:", "DESCRIPTION:"]:
                if delim in after_title:
                    after_title = after_title.split(delim)[0]
                    break
            selected = after_title.strip().splitlines()[0].strip()[:95]
            selected = clean_topic_for_id(selected)
            if len(selected.split()) > 5:
                selected = " ".join(selected.split()[:5])
        if "WHITE_BAR:" in raw:
            wb_part = raw.split("WHITE_BAR:")[1]
            for delim in ["SCRIPT:", "DESCRIPTION:"]:
                if delim in wb_part:
                    wb_part = wb_part.split(delim)[0]
                    break
            white_bar_parsed = wb_part.strip().splitlines()[0].strip()[:60]
            white_bar_parsed = clean_topic_for_id(white_bar_parsed)
            if len(white_bar_parsed.split()) > 5:
                white_bar_parsed = " ".join(white_bar_parsed.split()[:5])
        if "SCRIPT:" in raw:
            full_vo=raw.split("SCRIPT:")[1].split("DESCRIPTION:")[0].strip()[:800]
        if "DESCRIPTION:" in raw:
            description=raw.split("DESCRIPTION:")[1].strip()[:1200]
    except Exception as e:
        raise RuntimeError(f"Parse failed - NO FALLBACK: {e}")

    clean_tts=re.sub(r'\[.*?\]','',full_vo)
    clean_tts=re.sub(r'Visual:.*?\|','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'Audio:\s*','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'\s+',' ',clean_tts).strip()
    clean_tts=clean_topic_for_id(clean_tts)
    
    if len(clean_tts.split()) < 5:
        raise RuntimeError(f"Script too short - NO FALLBACK: {clean_tts}")

    # Validate 50 tak flexible
    if len(clean_tts.split()) > 50:
        print(f"[WARNING] Script {len(clean_tts.split())} words >50, trimming to 50 for 100% accuracy")
        clean_tts = " ".join(clean_tts.split()[:50])

    if not selected or len(selected.split()) < 4:
        raise RuntimeError(f"Title not 4-5 words - NO FALLBACK: {selected}")

    if not description:
        description=f"{topic.title()} is making headlines today. WHAT HAPPENED: Latest updates on {topic.title()} are drawing attention. WHY IT MATTERS: This could have wide emotional impact."

    if white_bar_parsed and 4 <= len(white_bar_parsed.split()) <= 5:
        white_bar_text = white_bar_parsed.title()
    else:
        white_bar_text = selected.title()
    white_bar_text = clean_topic_for_id(white_bar_text)
    if len(white_bar_text.split()) > 5:
        white_bar_text = " ".join(white_bar_text.split()[:5])

    pexels_data = extract_pexels_keywords_from_script(clean_tts, topic)

    desc_with_tags = f"{description}\n\n{' '.join(topic_hashtags)} {world_viral}"
    return {
        "title":selected,
        "title_options":[selected],
        "full_script":clean_tts,
        "raw_script_structured":raw,
        "script_segments":{},
        "visual_instructions":{
            "music":"tense dramatic news",
            "captions":"bold",
            "pacing":"fast",
            "pexels_query": pexels_data["pexels_query"],
            "pexels_keywords": pexels_data["keywords"],
            "emotional_keywords": pexels_data["emotional_keywords"],
            "clip_duration": 0.8,
            "clip_filter": "emotional_shock_only - no low emotion clips",
            "first_sentence_punch": pexels_data["first_sentence"],
            "pexels_from_script": True
        },
        "description":desc_with_tags,
        "tags_primary":topic_hashtags_str,
        "tags_secondary":world_viral,
        "tags_shorts":all_hashtags_str,
        "tags_all":all_hashtags_str,
        "tags_topic":topic_hashtags_str,
        "viral_hashtag":world_viral,
        "sources":f"Vol {search_vol} Pexels from SCRIPT 0.8s emotional: {pexels_data['pexels_query']}",
        "viral_check":{"words":len(clean_tts.split())},
        "viral_hook": white_bar_text,
        "white_bar_text": white_bar_text,
        "mood": "emotional",
        "pexels_query": pexels_data["pexels_query"],
        "pexels_keywords": pexels_data["keywords"],
        "first_sentence_punch": pexels_data["first_sentence"],
        "clip_duration": 0.8,
        "clip_filter": "emotional_shock_only"
    }
