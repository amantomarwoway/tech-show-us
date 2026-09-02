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
    if GENAI_NEW:
        try:
            client=genai.Client(api_key=api_key)
            response=client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return response.text.strip() if response.text else ""
        except Exception as e:
            err=str(e)
            if "404" in err or "NOT_FOUND" in err or "not found" in err.lower() or "v1beta" in err.lower():
                try:
                    import google.generativeai as genai_old
                    genai_old.configure(api_key=api_key)
                    model=genai_old.GenerativeModel('gemini-1.5-flash')
                    response=model.generate_content(prompt)
                    return response.text.strip() if response.text else ""
                except Exception as e2:
                    if "404" in str(e2):
                        model=genai_old.GenerativeModel('gemini-1.5-flash-latest')
                        response=model.generate_content(prompt)
                        return response.text.strip() if response.text else ""
                    raise e2
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                raise
            try:
                import google.generativeai as genai_old
                genai_old.configure(api_key=api_key)
                model=genai_old.GenerativeModel('gemini-1.5-flash')
                response=model.generate_content(prompt)
                return response.text.strip() if response.text else ""
            except:
                raise e
    else:
        import google.generativeai as genai_old
        genai_old.configure(api_key=api_key)
        try:
            model=genai_old.GenerativeModel('gemini-1.5-flash')
            response=model.generate_content(prompt)
            return response.text.strip() if response.text else ""
        except Exception as e:
            if "404" in str(e):
                model=genai_old.GenerativeModel('gemini-1.5-flash-latest')
                response=model.generate_content(prompt)
                return response.text.strip() if response.text else ""
            raise

# Google se functions
def get_google_searchable_title(topic: str) -> str:
    try:
        from live_viral_hashtag import get_google_searchable_title as google_title_fn
        return google_title_fn(topic)
    except Exception as e:
        print(f"Google title import fail: {e}")
    # Fallback direct Google
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
    # Fallback
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


def get_google_structured_script(topic: str) -> dict:
    """GOOGLE DIRECT - Proper structured script for full sound - no Gemini"""
    try:
        # Google se topic details lao
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        import re as re2
        matches = re2.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m)>5][:5]
        google_context = " ".join(suggestions) if suggestions else topic
        
        # Structured script Google prompt - proper 4 segments
        # Using Google search data to build proper script
        hook = f"Stop scrolling folks. {topic.title()} just shocked America - this is huge."
        news = f"Here's what happened in {topic} - {google_context[:100]}. This is breaking right now."
        context = f"Wait, here's the crazy part - why America is talking about {topic}. This changes everything for USA, and you need to know why."
        cta = f"What do y'all think about {topic}? Comment below and let me know."
        
        full = f"{hook} {news} {context} {cta}"
        # Ensure 85-95 words for proper structure
        words = full.split()
        if len(words) < 80:
            full += f" This is massive news for {topic} and USA is reacting."
        
        return {
            "hook": hook,
            "news": news,
            "context": context,
            "cta": cta,
            "full": full[:600]
        }
    except Exception as e:
        print(f"[GOOGLE SCRIPT] Fail: {e}")
        return {
            "hook": f"Stop scrolling. {topic.title()} just happened.",
            "news": f"Breaking in {topic} right now.",
            "context": f"Here's why USA cares about {topic}.",
            "cta": f"What do you think? Comment below.",
            "full": f"Stop scrolling folks. Breaking in {topic} - this just happened and it's huge. Here's why America is talking about it. What do y'all think? Comment below."
        }


def get_yt_suggestions(q):
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":q,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        return [m for m in matches[1:] if len(m)>5][:5]
    except:
        return []

def generate_viral_hook_from_script(script_text: str, topic: str) -> str:
    """White bar 5-6 words full sentence mirror"""
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
        why=news_input.get('why_searching','') or news_input.get('format_test','')
    else:
        topic=str(news_input)
        search_vol=70
        why=""
    topic=topic.strip()[:200]
    if len(topic)<3:
        topic="USA Breaking News"
    yt_sug=get_yt_suggestions(topic)
    google_struct = get_google_structured_script(topic)  # GOOGLE PROPER STRUCTURED SCRIPT

    # TITLE GOOGLE SE AAYEGA - NOT GEMINI FIXED 9-11 WORDS
    google_title = get_google_searchable_title(topic)
    
    # HASHTAGS GOOGLE SE
    topic_hashtags = get_topic_hashtags_from_google(topic)
    world_viral = get_world_viral_hashtag()
    all_hashtags_list = topic_hashtags + [world_viral]
    all_hashtags_str = ", ".join(all_hashtags_list)
    topic_hashtags_str = ", ".join(topic_hashtags)

    prompt=f"""
You are VIRAL USA YouTube Shorts Expert for American audience.
TOPIC: {topic}
GOOGLE SEARCHABLE TITLE (already from Google, use as base but make it viral): {google_title}
Search Vol: {search_vol} | Why: {why}
YT Related: {yt_sug}

RULES FOR TITLE - GOOGLE SEARCHABLE VIRAL:
- Use Google title as base: {google_title} but make it more viral and searchable
- Keep it searchable (what people actually search on YouTube)
- No "breaking news today"
- Example: If Google gives "white house state ballroom" make it "White House State Ballroom $200M Makeover Shocks America"
- Keep searchable keywords from Google title

RULES FOR SCRIPT (USA AUDIENCE):
- Structure:
  [0:00-0:03 HOOK] Stop scrolling line + shocking fact
  [0:03-0:15 NEWS] What happened - American slang folks, y'all, gonna
  [0:15-0:30 CONTEXT] Why USA cares - retention "wait, here's crazy part"
  [0:30-0:40 CTA] Comment question
- 85-95 words, American English

RULES FOR DESCRIPTION (YouTube Algorithm):
- 3 paras: Hook, What happened, Why USA matters
- No hashtags in description body (hashtags separate)

RULES FOR WHITE BAR:
- 5-6 words full sentence mirror of topic
- Example: "White House Ballroom $200M Makeover"

RETURN EXACTLY:
TITLE: <final viral searchable title based on Google title>
WHITE_BAR: <5-6 words full sentence mirror>
SCRIPT:
[0:00-0:03 HOOK] Visual: <v> | Audio: <a>
[0:03-0:15 THE NEWS] Visual: <v> | Audio: <a>
[0:15-0:30 CONTEXT] Visual: <v> | Audio: <a>
[0:30-0:40 CTA] Visual: <v> | Audio: <a>
FULL_VOICEOVER: <85-95 words>
DESCRIPTION:
<description 3 paras USA algorithm>
"""

    try:
        raw=call_gemini(prompt)
    except Exception as e:
        err=str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower() or "404" in err or "NOT_FOUND" in err or "No module" in err or "generativeai" in err.lower():
            print(f"[GEMINI FALLBACK] {topic} - {err[:80]}")
            # TITLE GOOGLE SE HI
            fb_title = google_title
            if len(fb_title.split()) < 4:
                fb_title = f"{topic.title()} Shocks America"
            # Script - GOOGLE STRUCTURED (proper structure + full sound)
            g_struct = get_google_structured_script(topic)
            fb_script = g_struct["full"]
            # White bar 5-6 words
            fb_white = " ".join(topic.split()[:6]).title()[:50]
            # Description
            fb_desc = f"{topic.title()} just made a massive move that has America talking.\n\nWhat happened in {topic[:50]} is shocking everyone right now.\n\nHere's why it matters for USA - this changes everything."
            desc_with_tags = f"{fb_desc}\n\n{' '.join(topic_hashtags)} {world_viral}"
            return {
                "title":fb_title,
                "title_options":[fb_title],
                "full_script":fb_script,
                "raw_script_structured":fb_script,
                "script_segments":{},
                "visual_instructions":{"music":"tense dramatic news","captions":"bold","pacing":"fast"},
                "description":desc_with_tags,
                "tags_primary":topic_hashtags_str,
                "tags_secondary":world_viral,
                "tags_shorts":all_hashtags_str,
                "tags_all":all_hashtags_str,
                "tags_topic":topic_hashtags_str,
                "viral_hashtag":world_viral,
                "sources":"Google Searchable",
                "viral_check":{"words":len(fb_script.split()),"has_segments":0},
                "viral_hook":fb_white,
                "white_bar_text":fb_white,
                "mood":"tense"
            }
        raise e

    selected=""
    full_vo=""
    segments={}
    description=""
    white_bar_parsed=""
    
    try:
        if "TITLE:" in raw:
            after_title = raw.split("TITLE:")[1]
            for delim in ["WHITE_BAR:", "SCRIPT:", "FULL_VOICEOVER:", "DESCRIPTION:"]:
                if delim in after_title:
                    after_title = after_title.split(delim)[0]
                    break
            selected = after_title.strip().splitlines()[0].strip()[:95]
            if "breaking news today" in selected.lower():
                selected = google_title  # Use Google title if bakwaas
        
        if "WHITE_BAR:" in raw:
            wb_part = raw.split("WHITE_BAR:")[1]
            for delim in ["SCRIPT:", "FULL_VOICEOVER:", "DESCRIPTION:"]:
                if delim in wb_part:
                    wb_part = wb_part.split(delim)[0]
                    break
            white_bar_parsed = wb_part.strip().splitlines()[0].strip()[:60]
            wb_words = white_bar_parsed.split()
            if len(wb_words) > 6:
                white_bar_parsed = " ".join(wb_words[:6])
        
        if "SCRIPT:" in raw:
            sb=raw.split("SCRIPT:")[1].split("FULL_VOICEOVER:")[0] if "FULL_VOICEOVER:" in raw else raw.split("SCRIPT:")[1].split("DESCRIPTION:")[0]
            for marker,key in [("0:00-0:03","hook_0_3"),("0:03-0:15","news_3_15"),("0:15-0:30","context_15_30"),("0:30-0:40","cta_30_40")]:
                if marker in sb:
                    part=sb.split(marker)[1]
                    for nm in ["0:00-0:03","0:03-0:15","0:15-0:30","0:30-0:40","0:30-0:45"]:
                        if nm!=marker and nm in part:
                            part=part.split(nm)[0]
                    segments[key]=part.strip()[:400]
        
        if "FULL_VOICEOVER:" in raw:
            fv=raw.split("FULL_VOICEOVER:")[1].split("DESCRIPTION:")[0].strip()
            full_vo=fv[:600]
        
        if "DESCRIPTION:" in raw:
            description=raw.split("DESCRIPTION:")[1].strip()[:1200]
    
    except Exception as e:
        print(f"Parse error {e}")

    clean_tts=re.sub(r'\[.*?\]','',full_vo)
    clean_tts=re.sub(r'Visual:.*?\|','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'Audio:\s*','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'\s+',' ',clean_tts).strip()
    
    # SOUND FIX: No cut to 95 words - keep full script for proper audio
    if len(clean_tts.split())>120:
        clean_tts=" ".join(clean_tts.split()[:110])  # was 95, now 110 for full sound
    if len(clean_tts)<20:
        tmp=" ".join(segments.values())
        tmp=re.sub(r'Visual:.*?\|','',tmp, flags=re.I)
        tmp=re.sub(r'Audio:\s*','',tmp, flags=re.I)
        tmp=re.sub(r'\[.*?\]','',tmp)
        clean_tts=re.sub(r'\s+',' ',tmp).strip()[:500]
        if len(clean_tts)<20:
            clean_tts = f"Stop scrolling folks. Breaking in {topic} - this just happened. Here's why America is talking about it. What do y'all think? Comment below."

    if not selected or len(selected)<10 or "breaking news today" in selected.lower():
        selected = google_title

    if not description:
        description=f"{topic.title()} just made a massive move that has America talking.\n\nWhat happened is shocking everyone right now.\n\nHere's why it matters for USA."

    if white_bar_parsed and 5 <= len(white_bar_parsed.split()) <= 6:
        white_bar_text = white_bar_parsed.title()
    else:
        topic_words = topic.split()
        if len(topic_words) >= 5:
            white_bar_text = " ".join(topic_words[:6]).title()
        else:
            white_bar_text = f"{topic.title()} Shocks America"
        white_bar_text = white_bar_text[:50]

    desc_with_tags = f"{description}\n\n{' '.join(topic_hashtags)} {world_viral}"

    return {
        "title":selected,
        "title_options":[selected],
        "full_script":clean_tts,
        "raw_script_structured":raw,
        "script_segments":segments,
        "visual_instructions":{"music":"tense dramatic news","captions":"bold","pacing":"fast"},
        "description":desc_with_tags,
        "tags_primary":topic_hashtags_str,
        "tags_secondary":world_viral,
        "tags_shorts":all_hashtags_str,
        "tags_all":all_hashtags_str,
        "tags_topic":topic_hashtags_str,
        "viral_hashtag":world_viral,
        "sources":f"Google Searchable Vol {search_vol}",
        "viral_check":{"words":len(clean_tts.split()),"has_segments":len(segments)},
        "viral_hook": white_bar_text,
        "white_bar_text": white_bar_text,
        "mood": "tense"
    }
