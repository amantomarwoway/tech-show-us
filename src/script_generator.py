import os, requests, re

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

def call_gemini(prompt):
    api_key=os.getenv("GEMINI_API_KEY","")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing")

    models_to_try_new = ["gemini-3.6-flash"]
    models_to_try_old = ["gemini-3.6-flash"]

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version='v1'))
        for model_name in models_to_try_new:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                text = getattr(response, 'text', None)
                if text:
                    return text.strip()
                if hasattr(response, 'candidates') and response.candidates:
                    return response.candidates[0].content.parts[0].text.strip()
            except Exception as inner:
                print(f"[GEMINI TRY] {model_name} failed: {str(inner)[:120]}")
                continue
    except Exception as e:
        print(f"[GEMINI NEW SDK] total fail: {e}")

    try:
        import google.generativeai as genai_old
        genai_old.configure(api_key=api_key)
        for old_model in models_to_try_old:
            try:
                model = genai_old.GenerativeModel(old_model)
                response = model.generate_content(prompt)
                if response.text:
                    return response.text.strip()
            except Exception as inner2:
                print(f"[GEMINI OLD TRY] {old_model} failed: {str(inner2)[:120]}")
                continue
    except Exception as e:
        print(f"[GEMINI OLD SDK] total fail: {e}")

    raise RuntimeError("All Gemini models failed")

def get_google_searchable_title(topic: str) -> str:
    try:
        from live_viral_hashtag import get_google_searchable_title as google_title_fn
        return google_title_fn(topic)
    except Exception as e:
        print(f"Google title import fail: {e}")
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"}, timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        suggestions=[m for m in matches[1:] if len(m)>5]
        if suggestions:
            return suggestions[0][:95].title()
    except:
        pass
    return topic.title()[:95]

def get_topic_hashtags_from_google(topic: str):
    try:
        from live_viral_hashtag import get_topic_hashtags_from_google as topic_tags_fn
        return topic_tags_fn(topic)
    except Exception as e:
        print(f"Google topic hashtags fail: {e}")
    words=re.findall(r'\w+', topic.lower())[:4]
    tags=[]
    for w in words:
        if len(w)>2:
            tags.append(f"#{w}")
    while len(tags)<4:
        tags.append("#usa")
    return tags[:4]

def get_world_viral_hashtag():
    try:
        from live_viral_hashtag import get_world_viral_hashtag as world_fn
        return world_fn()
    except Exception as e:
        print(f"World viral fail: {e}")
    return "#breakingnews"

def get_yt_suggestions(q):
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":q,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        return [m for m in matches[1:] if len(m)>5][:5]
    except:
        return []

def generate_viral_hook_from_script(script_text: str, topic: str) -> str:
    try:
        words=topic.split()
        if len(words)>=5:
            return " ".join(words[:6]).title()[:50]
        return " ".join(script_text.split()[:6]).title()[:50]
    except:
        return " ".join(topic.split()[:6]).title()

def generate_script(news_input):
    if isinstance(news_input, dict):
        topic=news_input.get('query','') or news_input.get('title','') or news_input.get('summary','')
        search_vol=news_input.get('search_volume',70)
    else:
        topic=str(news_input)
        search_vol=70
    topic=topic.strip()[:200]
    if len(topic)<3:
        topic="USA Breaking News"

    yt_sug=get_yt_suggestions(topic)
    google_title = get_google_searchable_title(topic)
    topic_hashtags = get_topic_hashtags_from_google(topic)
    world_viral = get_world_viral_hashtag()
    all_hashtags_list = topic_hashtags + [world_viral]
    all_hashtags_str = ", ".join(all_hashtags_list)
    topic_hashtags_str = ", ".join(topic_hashtags)

    # --- PURE LOOP SCRIPT PROMPT - NO FIXED WHITE HOUSE ---
    prompt=f"""
You are VIRAL USA YouTube Shorts script writer. You write PERFECT LOOP scripts like this example:

Example: "Scientists just found something on the moon that changes everything. For decades, we thought it was just a dead rock. But recent scans revealed deep, hidden underground tunnels. They aren't just empty caves—they are perfectly insulated from radiation and freezing space temperatures. This means future humans won't live in surface domes; we're moving underground. But here's the crazy part... some researchers believe these tunnels could already hold ancient ice, meaning water is already there waiting for us. And that's why scientists just found something on the moon..."

NOW WRITE FOR:
TOPIC: {topic}
GOOGLE TITLE: {google_title}
YT Related: {yt_sug}
Search Vol: {search_vol}

RULES - FOLLOW EXACTLY:
- 90-100 words ONLY - count it
- STRUCTURE: Hook (1 line curiosity) -> Body (For decades/For years, we thought... But now/recent... They aren't just... This means... But here's the crazy part...) -> Loop (last line connects back to first line word-to-word)
- The LAST sentence MUST be incomplete and loop back to FIRST sentence, so video loops seamlessly. Example: First line "Scientists just found something..." Last line "And that's why scientists just found..."
- No fixed phrase like White House, no political angle unless topic is politics
- No labels like WHAT HAPPENED, WHY IT MATTERS, HOOK, BODY, no timestamps
- No Visual: Audio: tags
- TTS friendly, simple USA English, storytelling
- Topic se related hi likho, generic mat likho

RETURN EXACTLY THIS FORMAT:
TITLE: <final viral searchable title based on Google title - 60-90 chars>
WHITE_BAR: <5-6 words full sentence, Title ka mirror, like "Secret Tunnels Found On Moon">
SCRIPT: <your 90-100 words loop script here>
DESCRIPTION:
Para1: Hook line - 1 line
Para2: WHAT HAPPENED 2 lines about {topic}
Para3: WHY IT MATTERS 2 lines for USA
"""

    try:
        raw=call_gemini(prompt)
    except Exception as e:
        err=str(e)
        print(f"[GEMINI ERROR] {topic} - {err[:200]}")
        # Fallback - ALSO PURE LOOP, NO WHITE HOUSE
        fb_title = google_title
        fb_white = " ".join(topic.split()[:6]).title()[:50]
        fb_script = f"{topic} just shocked everyone and nobody saw this coming. For years we thought this was impossible, but recent events revealed something huge. They aren't just making headlines, they are changing the entire game. This means everything we knew about {topic} is about to change forever. But here's the crazy part, this is already happening right now and it's bigger than anyone thought. And that's why {topic} just shocked..."
        fb_desc = f"{topic.title()} just shocked everyone.\n\nWHAT HAPPENED: {topic.title()} is making massive moves right now that no one expected.\n\nWHY IT MATTERS: This changes everything for the future."
        desc_with_tags = f"{fb_desc}\n\n{' '.join(topic_hashtags)} {world_viral}"
        return {
            "title":fb_title,"title_options":[fb_title],"full_script":fb_script,"raw_script_structured":fb_script,"script_segments":{},"visual_instructions":{"music":"tense dramatic news","captions":"bold","pacing":"fast"},"description":desc_with_tags,"tags_primary":topic_hashtags_str,"tags_secondary":world_viral,"tags_shorts":all_hashtags_str,"tags_all":all_hashtags_str,"tags_topic":topic_hashtags_str,"viral_hashtag":world_viral,"sources":"Google Searchable","viral_check":{"words":len(fb_script.split()),"has_segments":0},"viral_hook":fb_white,"white_bar_text":fb_white,"mood":"tense"
        }

    selected=""; full_vo=""; description=""; white_bar_parsed=""
    try:
        if "TITLE:" in raw:
            after_title = raw.split("TITLE:")[1]
            for delim in ["WHITE_BAR:", "SCRIPT:", "DESCRIPTION:"]:
                if delim in after_title:
                    after_title = after_title.split(delim)[0]
                    break
            selected = after_title.strip().splitlines()[0].strip()[:95]
        if "WHITE_BAR:" in raw:
            wb_part = raw.split("WHITE_BAR:")[1]
            for delim in ["SCRIPT:", "DESCRIPTION:"]:
                if delim in wb_part:
                    wb_part = wb_part.split(delim)[0]
                    break
            white_bar_parsed = wb_part.strip().splitlines()[0].strip()[:60]
        if "SCRIPT:" in raw:
            fv=raw.split("SCRIPT:")[1].split("DESCRIPTION:")[0].strip()
            full_vo=fv[:700]
        if "DESCRIPTION:" in raw:
            description=raw.split("DESCRIPTION:")[1].strip()[:1200]
    except Exception as e:
        print(f"Parse error {e}")

    clean_tts=re.sub(r'\[.*?\]','',full_vo)
    clean_tts=re.sub(r'Visual:.*?\|','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'Audio:\s*','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'\s+',' ',clean_tts).strip()
    if len(clean_tts.split())>115:
        clean_tts=" ".join(clean_tts.split()[:102])
    if len(clean_tts)<20:
        clean_tts = f"{topic} just shocked everyone and nobody expected this. For years we thought this was impossible, but now it's real. This changes everything. But here's the crazy part, it's already happening. And that's why {topic} just..."

    if not selected or len(selected)<10:
        selected = google_title
    if not description:
        description=f"{topic.title()} is making massive moves that has America talking.\n\nWHAT HAPPENED: What happened in {topic[:50]} is shocking everyone right now.\n\nWHY IT MATTERS: Here's why it matters."
    if white_bar_parsed and 5 <= len(white_bar_parsed.split()) <= 6:
        white_bar_text = white_bar_parsed.title()
    else:
        white_bar_text = " ".join(topic.split()[:6]).title()[:50]

    desc_with_tags = f"{description}\n\n{' '.join(topic_hashtags)} {world_viral}"
    return {
        "title":selected,"title_options":[selected],"full_script":clean_tts,"raw_script_structured":raw,"script_segments":{},"visual_instructions":{"music":"tense dramatic news","captions":"bold","pacing":"fast"},"description":desc_with_tags,"tags_primary":topic_hashtags_str,"tags_secondary":world_viral,"tags_shorts":all_hashtags_str,"tags_all":all_hashtags_str,"tags_topic":topic_hashtags_str,"viral_hashtag":world_viral,"sources":f"Google Searchable Vol {search_vol}","viral_check":{"words":len(clean_tts.split()),"has_segments":0},"viral_hook": white_bar_text,"white_bar_text": white_bar_text,"mood": "tense"
    }
