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
        client=genai.Client(api_key=api_key)
        response=client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        return response.text.strip() if response.text else ""
    else:
        import google.generativeai as genai_old
        genai_old.configure(api_key=api_key)
        model=genai_old.GenerativeModel('gemini-2.0-flash')
        response=model.generate_content(prompt)
        return response.text.strip() if response.text else ""

def get_yt_suggestions(q):
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search", params={"client":"youtube","ds":"yt","q":q,"hl":"en","gl":"US"}, timeout=4, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        return [m for m in matches[1:] if len(m)>5][:5]
    except:
        return []

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

TOPIC (this video only): {topic}
Search Vol: {search_vol} | Why: {why}
YT Related: {yt_sug}

MUST follow Tacko Fall structure:

[0:00-0:03 HOOK] Visual: Fast-paced high-energy clips + dramatic headline | Audio: Excited Punchy: "{topic} is officially BACK... well, almost!" + number/name/FOMO
[0:03-0:15 THE NEWS] Visual: Recent footage overseas/training, then team/logo | Audio: Just signed deal, Exhibit 10 contract, team name
[0:15-0:30 CONTEXT] Visual: Quick highlights legendary time | Audio: Haven't seen since 2022, dominating overseas, fighting for roster spot
[0:30-0:45 CTA] Visual: Close-up smiling, split screen question Text: "Will he make final roster?" | Audio: Has size but does he have speed? Drop thoughts, Hit follow

ALSO: Music trending heavy-bass hip-hop, Captions bold colorful keywords, Pacing fast first 3 sec most important

4 Titles: 1. Short clickable emoji 2. Keyword rich SEO 3. Engaging question 4. High search volume
SEO Description: first 3 lines main keywords, para1 main, para2 context, para3 question + LIKE COMMENT SUBSCRIBE
Tags: Primary 7, Secondary 7, Shorts 8 hashtags

RETURN:
TITLE_OPTIONS:
1. <t1>
2. <t2>
3. <t3>
4. <t4>

SELECTED_TITLE: <best>

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
    raw=call_gemini(prompt)
    title_options=[]
    selected=topic[:60]
    full_vo=""
    segments={}
    music="Trending heavy-bass hip-hop, energetic, 100 BPM"
    captions=f"{topic.split()[0]}, bold colorful"
    pacing="Fast and punchy, first 3 sec most important"
    description=""
    tp=""; ts=""; th=""
    try:
        if "TITLE_OPTIONS:" in raw:
            block=raw.split("TITLE_OPTIONS:")[1].split("SELECTED_TITLE:")[0]
            for line in block.split("\n"):
                line=line.strip()
                if not line: continue
                if line[0].isdigit():
                    clean=re.sub(r'^\d+\.\s*','',line).strip()
                    if len(clean)>10:
                        title_options.append(clean[:95])
        if "SELECTED_TITLE:" in raw:
            sel=raw.split("SELECTED_TITLE:")[1].split("SCRIPT:")[0].strip().split("\n")[0]
            selected=sel.strip()[:95]
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
    return {"title":selected,"title_options":title_options,"full_script":clean_tts,"raw_script_structured":raw,"script_segments":segments,"visual_instructions":{"music":music,"captions":captions,"pacing":pacing},"description":f"{description}\n\n#usanews #breakingnews #shorts {th}","tags_primary":tp,"tags_secondary":ts,"tags_shorts":th,"tags_all":f"{tp}, {ts}, {th}","sources":f"Filter A+B+C Tacko Style Vol {search_vol}","viral_check":{"words":len(clean_tts.split()),"has_segments":len(segments)==4}}
