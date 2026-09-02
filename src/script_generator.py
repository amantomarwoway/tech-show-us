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

def get_yt_suggestions(q):
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":q,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        return [m for m in matches[1:] if len(m)>5][:5]
    except:
        return []

def generate_viral_hook_from_script(script_text: str, topic: str) -> str:
    try:
        clean = re.sub(r'\[.*?\]','', script_text)
        clean = re.sub(r'Visual:.*?\|','', clean, flags=re.I)
        clean = re.sub(r'Audio:\s*','', clean, flags=re.I)
        words = clean.split()
        triggers = ["shocking","unbelievable","justifiable","outburst","betrayal","arrested","breaking","dies","wins","lost","everything","changes"]
        for t in triggers:
            if t in clean.lower():
                idx = clean.lower().find(t)
                snippet = clean[max(0,idx-20):idx+30]
                sw = snippet.split()[:5]
                if len(sw) >= 3:
                    return " ".join(sw[:5]).title()[:35]
        if words:
            return " ".join(words[:5]).title()[:35]
        return " ".join(topic.split()[:5]).title()[:35]
    except:
        return "This Changes Everything"

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
    prompt=f"""
You are VIRAL USA YouTube Shorts Expert. Create EVERYTHING for ONE video.
TOPIC: {topic}
Search Vol: {search_vol} | Why: {why}
YT Related: {yt_sug}
MUST follow Tacko Fall structure:
[0:00-0:03 HOOK] Visual: Fast clips + dramatic headline | Audio: Excited Punchy
[0:03-0:15 THE NEWS] Visual: Recent footage | Audio: Just signed deal
[0:15-0:30 CONTEXT] Visual: Highlights | Audio: Haven't seen since 2022
[0:30-0:45 CTA] Visual: Close-up question | Audio: Drop thoughts, Hit follow
RETURN:
TITLE_OPTIONS:
1. <t1>
2. <t2>
3. <t3>
4. <t4>
SELECTED_TITLE: <best>
VIRAL_HOOK: <4-5 words CTR hook for white bar>
SCRIPT:
[0:00-0:03 HOOK] Visual: <v> | Audio: <a>
[0:03-0:15 THE NEWS] Visual: <v> | Audio: <a>
[0:15-0:30 CONTEXT] Visual: <v> | Audio: <a>
[0:30-0:45 CTA] Visual: <v> | Audio: <a>
FULL_VOICEOVER: <75-95 words>
VISUAL_INSTRUCTIONS:
Music: <music>
Captions: <captions>
Pacing: <pacing>
DESCRIPTION:
<desc>
TAGS_PRIMARY: <p>
TAGS_SECONDARY: <s>
TAGS_SHORTS: <h>
"""
    try:
        raw=call_gemini(prompt)
    except Exception as e:
        err=str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower() or "404" in err or "NOT_FOUND" in err:
            print(f"[GEMINI FALLBACK] Fallback for: {topic}")
            fb_title = f"{topic[:50]} Breaking News Today"
            fb_script = f"{topic} is officially back. You need to see this. Here's why this matters. This just happened and it's huge. Wait till the end."
            fb_hook = generate_viral_hook_from_script(fb_script, topic)
            return {"title":fb_title,"title_options":[fb_title],"full_script":fb_script,"raw_script_structured":fb_script,"script_segments":{},"visual_instructions":{"music":"news","captions":"breaking","pacing":"fast"},"description":f"{fb_script} #usanews #shorts","tags_primary":"","tags_secondary":"","tags_shorts":"","tags_all":"","sources":"Fallback","viral_check":{"words":len(fb_script.split()),"has_segments":0},"viral_hook":fb_hook,"white_bar_text":fb_hook,"mood":"breaking news"}
        raise e

    title_options=[]
    selected=topic[:60]
    full_vo=""
    segments={}
    music="Trending heavy-bass hip-hop, energetic, 100 BPM"
    captions=f"{topic.split()[0]}, bold colorful"
    pacing="Fast and punchy"
    description=""
    tp=""
    ts=""
    th=""
    viral_hook_parsed=""
    try:
        if "TITLE_OPTIONS:" in raw:
            block=raw.split("TITLE_OPTIONS:")[1].split("SELECTED_TITLE:")[0]
            for line in block.splitlines():
                line=line.strip()
                if not line:
                    continue
                if line[0].isdigit():
                    clean=re.sub(r'^\d+\.\s*','',line).strip()
                    if len(clean)>10:
                        title_options.append(clean[:95])
        if "SELECTED_TITLE:" in raw:
            sel=raw.split("SELECTED_TITLE:")[1].split("VIRAL_HOOK:")[0] if "VIRAL_HOOK:" in raw else raw.split("SELECTED_TITLE:")[1].split("SCRIPT:")[0]
            selected=sel.strip().splitlines()[0][:95]
        if "VIRAL_HOOK:" in raw:
            vh=raw.split("VIRAL_HOOK:")[1].split("SCRIPT:")[0].strip().splitlines()[0]
            viral_hook_parsed=vh.strip()[:50]
        if "SCRIPT:" in raw:
            sb=raw.split("SCRIPT:")[1].split("FULL_VOICEOVER:")[0] if "FULL_VOICEOVER:" in raw else raw.split("SCRIPT:")[1].split("VISUAL_INSTRUCTIONS:")[0]
            for marker,key in [("0:00-0:03","hook_0_3"),("0:03-0:15","news_3_15"),("0:15-0:30","context_15_30"),("0:30-0:45","cta_30_45")]:
                if marker in sb:
                    part=sb.split(marker)[1]
                    for nm in ["0:00-0:03","0:03-0:15","0:15-0:30","0:30-0:45"]:
                        if nm!=marker and nm in part:
                            part=part.split(nm)[0]
                    segments[key]=part.strip()[:400]
        if "FULL_VOICEOVER:" in raw:
            fv=raw.split("FULL_VOICEOVER:")[1].split("VISUAL_INSTRUCTIONS:")[0].strip()
            full_vo=fv[:600]
        if "VISUAL_INSTRUCTIONS:" in raw:
            vi=raw.split("VISUAL_INSTRUCTIONS:")[1].split("DESCRIPTION:")[0]
            if "Music:" in vi:
                music=vi.split("Music:")[1].split("\n")[0].strip()[:150]
            if "Captions:" in vi:
                captions=vi.split("Captions:")[1].split("\n")[0].strip()[:200]
            if "Pacing:" in vi:
                pacing=vi.split("Pacing:")[1].split("\n")[0].strip()[:200]
        if "DESCRIPTION:" in raw:
            description=raw.split("DESCRIPTION:")[1].split("TAGS_PRIMARY:")[0].strip()[:1200]
        if "TAGS_PRIMARY:" in raw:
            tp=raw.split("TAGS_PRIMARY:")[1].split("TAGS_SECONDARY:")[0].strip()[:400]
        if "TAGS_SECONDARY:" in raw:
            ts=raw.split("TAGS_SECONDARY:")[1].split("TAGS_SHORTS:")[0].strip()[:400]
        if "TAGS_SHORTS:" in raw:
            th=raw.split("TAGS_SHORTS:")[1].strip()[:400]
    except Exception as e:
        print(f"Parse error {e}")
    clean_tts=re.sub(r'\[.*?\]','',full_vo)
    clean_tts=re.sub(r'Visual:.*?\|','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'Audio:\s*','',clean_tts, flags=re.I)
    clean_tts=re.sub(r'\s+',' ',clean_tts).strip()
    if len(clean_tts.split())>100:
        clean_tts=" ".join(clean_tts.split()[:95])
    if len(clean_tts)<20:
        tmp=" ".join(segments.values())
        tmp=re.sub(r'Visual:.*?\|','',tmp, flags=re.I)
        tmp=re.sub(r'Audio:\s*','',tmp, flags=re.I)
        tmp=re.sub(r'\[.*?\]','',tmp)
        clean_tts=re.sub(r'\s+',' ',tmp).strip()[:500]
    if not title_options:
        title_options=[f"{topic[:30]} is FINALLY Back! 🤯", f"{topic[:40]} Just Signed! Breaking!", f"{topic[:35]} - Will It Work? Comment!", f"{topic[:40]} Returns After Years! (USA Deal)"]
    if not selected or len(selected)<10:
        selected=title_options[0]
    if not description:
        description=f"{clean_tts}\n\nWhat do you think about {topic}? Drop predictions below!\n\nLIKE COMMENT SUBSCRIBE for more breaking USA news!"
    if viral_hook_parsed and 2 <= len(viral_hook_parsed.split()) <= 6:
        viral_hook = viral_hook_parsed
    else:
        viral_hook = generate_viral_hook_from_script(clean_tts, topic)
    white_bar_text = viral_hook
    return {"title":selected,"title_options":title_options,"full_script":clean_tts,"raw_script_structured":raw,"script_segments":segments,"visual_instructions":{"music":music,"captions":captions,"pacing":pacing},"description":f"{description}\n\n#usanews #breakingnews #shorts {th}","tags_primary":tp,"tags_secondary":ts,"tags_shorts":th,"tags_all":f"{tp}, {ts}, {th}","sources":f"Filter A+B+C Tacko Style Vol {search_vol}","viral_check":{"words":len(clean_tts.split()),"has_segments":len(segments)==4},"viral_hook": viral_hook,"white_bar_text": white_bar_text,"mood": music}
