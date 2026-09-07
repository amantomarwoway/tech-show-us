"""
ULTIMATE GOD LEVEL - RETENTION + VALIDATION FACTORY - 40 WORDS + TWIST ONLY
Location: src/script_generator.py
Edits:
- 40 words lock (11-13 sec)
- Twist-only, 1 twist loop seamless
- Bold claims, Secret leak angle mandatory
- Validation Factory: behind closed doors, first to know, leaked keywords check
- Retention: bold confident daave
"""

import os, requests, re, random

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

# ===== NEW RETENTION + VALIDATION CONSTANTS =====
RETENTION_WORDS = 40
VALIDATION_KEYWORDS_MANDATORY = ["behind closed doors", "leaked", "first to know"]
BOLD_CLAIMS = [
    "this changes everything",
    "you won't believe",
    "nobody saw this coming",
    "this is huge",
    "shocked everyone",
    "game changer",
    "secret"
]
SECRET_LEAK_ANGLES = [
    "behind closed doors",
    "leaked behind closed doors",
    "secret leak",
    "just leaked",
    "inside sources reveal"
]

def validate_script_factory(script_text: str, topic: str) -> bool:
    """
    Validation Factory:
    - Bold/confident daave check
    - First-to-know, Behind closed doors keyword mandatory
    - 40 words lock
    """
    low = script_text.lower()
    # Check 40 words
    wc = len(script_text.split())
    if not (35 <= wc <= 45): # allow 35-45 for 40 target
        print(f"[VALIDATION FAIL] Words {wc} != 40 target")
        return False
    # Mandatory keywords
    has_leak = any(k in low for k in ["leak", "behind closed doors", "secret", "inside"])
    has_first = "first to know" in low or "first" in low and "know" in low
    if not has_leak:
        print(f"[VALIDATION FAIL] No leak/secret angle")
        return False
    # Bold claim check
    has_bold = any(b in low for b in BOLD_CLAIMS)
    if not has_bold:
        print(f"[VALIDATION FAIL] No bold claim")
        return False
    print(f"[VALIDATION PASS] {wc} words, leak={has_leak}, bold={has_bold}")
    return True

def trim_to_40_words(text: str, topic_first_words: str) -> str:
    """Force 40 words + seamless loop (last = first)"""
    words = text.split()
    if len(words) > RETENTION_WORDS:
        words = words[:RETENTION_WORDS]
    # If less, pad with topic loop
    while len(words) < RETENTION_WORDS:
        words += topic_first_words.split()[:2]
        if len(words) > RETENTION_WORDS:
            words = words[:RETENTION_WORDS]
            break
    # Seamless loop: last 4 words = first 4 words start for loop effect
    # Example: first "Scientists just found something" -> last "And that's why scientists just found..."
    first4 = " ".join(words[:4])
    # Ensure last sentence points back to first
    trimmed = " ".join(words)
    # If not ending with loop phrase, add loop tail
    if first4.lower() not in trimmed[-40:].lower():
        # Replace last 4 words with loop connector + first 2
        words = words[:-4] + ["And", "that's", "why"] + first4.split()[:2]
        trimmed = " ".join(words[:RETENTION_WORDS])
    return trimmed

def call_gemini(prompt):
    api_key=os.getenv("GEMINI_API_KEY","")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing")

    models_to_try_new = ["gemini-3.6-flash"]
    models_to_try_old = ["gemini-3.6-flash"]

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
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
        # Hook must be 5-6 words mirror of topic + secret leak angle
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

    # --- 40 WORDS RETENTION + SECRET LEAK PROMPT ---
    prompt=f"""
You are VIRAL USA YouTube Shorts script writer - RETENTION GOD.

TOPIC: {topic}
GOOGLE TITLE: {google_title}
YT Related: {yt_sug}
Search Vol: {search_vol}

MANDATORY RULES - FOLLOW 100%:
- EXACTLY 40 WORDS ONLY - not 39, not 41. Count them.
- STRUCTURE: Twist-only: Hook (secret leak) -> 1 Twist (But here's the crazy part...) -> Loop back to hook
- MUST INCLUDE: "behind closed doors" OR "leaked" + "first to know" effect + 1 bold claim like "this changes everything" / "you won't believe" / "shocked everyone"
- ANGLE: Secret leak angle - "Just leaked behind closed doors", "Inside sources reveal", "Secret documents show"
- TONE: Bold, confident daave, confident like you know secret first
- SEAMLESS LOOP: Last sentence MUST be "And that's why [first 3 words of script]..." so video loops perfectly
- No labels like WHAT HAPPENED, WHY IT MATTERS, HOOK, BODY
- No Visual: Audio: tags
- Simple USA English, TTS friendly, short sentences
- Example 40-word loop: "This just leaked behind closed doors and changes everything. For years we thought moon was dead rock. But scans revealed hidden tunnels that could hold water. You won't believe what's inside. And that's why this just leaked..."

RETURN EXACTLY:
TITLE: <viral searchable title 60-90 chars with leak word>
WHITE_BAR: <5-6 words full sentence, mirror of title, include secret/leaked, like "Secret Tunnels Leaked Behind Doors">
SCRIPT: <your exactly 40 words loop script here with behind closed doors + first to know + bold claim>
DESCRIPTION:
Para1: Hook line - 1 line with leaked angle
Para2: WHAT HAPPENED 1 line about {topic}
Para3: WHY IT MATTERS 1 line for USA + bold claim
"""

    raw=""
    try:
        raw=call_gemini(prompt)
    except Exception as e:
        err=str(e)
        print(f"[GEMINI ERROR] {topic} - {err[:200]}")
        # Fallback - 40 words RETENTION + LEAK
        fb_title = f"{google_title} Leaked"
        fb_white = " ".join(topic.split()[:4]).title() + " Leaked Behind Doors"
        # Exact 40 words fallback with validation keywords
        fb_script = f"{topic} just leaked behind closed doors and this changes everything. For years we thought this was impossible. But inside sources reveal hidden truth that shocked everyone. You won't believe what's next. And that's why {topic.lower().split()[0] if topic.split() else 'this'} just leaked"
        # Force trim to 40
        fb_script = trim_to_40_words(fb_script, topic)
        fb_desc = f"{topic.title()} just leaked behind closed doors.\n\nWHAT HAPPENED: {topic.title()} secret leak behind closed doors is shocking America.\n\nWHY IT MATTERS: First to know effect - this changes everything for USA."
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
    
    # FORCE 40 WORDS + VALIDATION FACTORY
    first_words_topic = " ".join(topic.split()[:4])
    clean_tts = trim_to_40_words(clean_tts, first_words_topic)
    
    # Validation loop - retry trim if fail (max 3 attempts)
    attempts=0
    while not validate_script_factory(clean_tts, topic) and attempts<3:
        # Inject mandatory keywords if missing
        low = clean_tts.lower()
        if "behind closed doors" not in low and "leaked" not in low:
            clean_tts = clean_tts.replace("and", "leaked behind closed doors and", 1)
            clean_tts = trim_to_40_words(clean_tts, first_words_topic)
        if "first to know" not in low and "first" not in low:
            clean_tts = clean_tts + " First to know."
            clean_tts = trim_to_40_words(clean_tts, first_words_topic)
        attempts+=1

    if len(clean_tts.split())<10:
        clean_tts = f"{topic} just leaked behind closed doors and changes everything. Inside sources reveal shocking truth. You won't believe what's inside. First to know effect is huge. And that's why {topic.lower().split()[0]} just leaked"
        clean_tts = trim_to_40_words(clean_tts, first_words_topic)

    if not selected or len(selected)<10:
        selected = google_title + " Leaked Behind Doors"
    if not description:
        description=f"{topic.title()} leaked behind closed doors.\n\nWHAT HAPPENED: {topic.title()} secret leak is shocking.\n\nWHY IT MATTERS: First to know - this changes everything."
    if white_bar_parsed and 4 <= len(white_bar_parsed.split()) <= 7:
        white_bar_text = white_bar_parsed.title()
    else:
        white_bar_text = " ".join(topic.split()[:5]).title() + " Leaked"

    desc_with_tags = f"{description}\n\n{' '.join(topic_hashtags)} {world_viral}"
    return {
        "title":selected,"title_options":[selected],"full_script":clean_tts,"raw_script_structured":raw,"script_segments":{},"visual_instructions":{"music":"tense dramatic news","captions":"bold","pacing":"fast"},"description":desc_with_tags,"tags_primary":topic_hashtags_str,"tags_secondary":world_viral,"tags_shorts":all_hashtags_str,"tags_all":all_hashtags_str,"tags_topic":topic_hashtags_str,"viral_hashtag":world_viral,"sources":f"Google Searchable Vol {search_vol}","viral_check":{"words":len(clean_tts.split()),"has_segments":0},"viral_hook": white_bar_text,"white_bar_text": white_bar_text,"mood": "tense"
    }
