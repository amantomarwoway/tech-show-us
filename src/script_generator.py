"""
src/script_generator.py - FINAL SHORT BOT - Viral Structure + Filter A/B/C + Gemini 3.6

Short Viral Video Script Structure (40 sec):
0-3s HOOK (Shocking fact, number, FOMO)
3-10s CONTEXT (What, where, who)
10-25s CONFLICT/DEEP (Why, 3 points, why matters)
25-38s PAYOFF (Final truth, impact)
38-40s CTA (Comment, subscribe)

Retention: Every 2 sentences word like "wait", "here's why" etc
"""

import os
import requests
import re

try:
    from google import genai
    GENAI_NEW = True
except ImportError:
    try:
        import google.generativeai as genai_old
        GENAI_NEW = False
        genai = None
    except ImportError:
        genai = None
        genai_old = None
        GENAI_NEW = None

def call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY missing")
    if GENAI_NEW:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip() if response.text else ""
    else:
        import google.generativeai as genai_old
        genai_old.configure(api_key=api_key)
        model = genai_old.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else ""

def get_searchable_title(topic):
    """YouTube Search Filter - Searchable title"""
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
                         params={"client": "youtube", "ds": "yt", "q": topic, "hl": "en", "gl": "US"},
                         timeout=4, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 5][:2]
        if suggestions:
            return suggestions[0].title()
    except:
        pass
    clean_topic = str(topic).strip()
    if len(clean_topic) < 3:
        clean_topic = "USA Breaking News"
    return f"{clean_topic} Today".title()[:95]

def generate_script(news_input):
    """
    FINAL SHORT BOT - Viral Structure + Gemini 3.6
    Filter A/B/C info also used in prompt for better hook
    """
    try:
        if isinstance(news_input, dict):
            news_text = news_input.get('query','') or news_input.get('title','') or news_input.get('summary','') or str(news_input.get('query',''))
            why = news_input.get('why_searching','') or news_input.get('format_test','')
            bot_friendly = news_input.get('bot_friendly', True)
            search_vol = news_input.get('search_volume', 50)
            growth = news_input.get('growth','rising')
        else:
            news_text = str(news_input)
            why = ""
            bot_friendly = True
            search_vol = 50
            growth = "rising"
        
        news_text = news_text.strip()
        if len(news_text) < 3:
            news_text = "Breaking news from USA"
        
        # VIRAL SHORT STRUCTURE PROMPT - Gemini 3.6
        prompt = f"""
You are VIRAL USA YouTube Shorts writer (40 sec, 9:16, American audience ONLY, faceless AI voice).

TRENDING TOPIC (Bot Friendly Rising Trend):
Keyword: {news_text}
Search Volume: {search_vol} | Growth: {growth} | Why Searching: {why} | Bot Friendly: {bot_friendly}
Filter Info: This topic passed Filter A (YouTube Search Breakout), Filter B (Autocomplete Hot), Filter C (Faceless Friendly, Rising Trend)

VIRAL SHORT SCRIPT STRUCTURE - MUST FOLLOW (YouTube Shorts Algorithm):

[0-3s HOOK - Stop Scroll]:
- First 3 seconds MUST have: Number/Name/Shocking Fact + Keyword "{news_text}" + FOMO
- Example: "Trump just announced $5B move that changes Texas forever, you need to know this"
- Must create curiosity gap, use "breaking", "shocking", "just in", "alert"
- NO generic "USA news" start

[3-10s CONTEXT - What/Where/Who]:
- What happened, where (US city/state like Texas, Florida, California), who (names), when (today)
- 1-2 sentences, facts, specific
- Example: "This happened in Texas today, affecting 3 million Americans..."

[10-25s CONFLICT/DEEP - Why/3 Points]:
- Why it happened, 3 key points, why it matters to Americans
- Add retention words: "wait", "here's why", "what happened next", "don't miss"
- Example: "Here's why this matters to you. First... Second... Wait, here's the shocking part..."
- American triggers: wallet, safety, family, politics

[25-38s PAYOFF - Final Truth + Impact]:
- Final truth, impact on Americans, what happens next
- Must make viewer stay till end
- Example: "This is huge for America, your family needs to know this truth..."

[38-40s CTA - Comment + Subscribe]:
- Comment question + subscribe
- Example: "Comment below what you think, subscribe for more USA breaking news"

STRICT RULES:
- 65-85 words ONLY, 5-6 sentences total (40 sec at 150wpm)
- EVERY sentence must have value, no filler
- Every 2 sentences add retention word: "wait", "here's why", "what happened next", "don't miss", "this is huge"
- American English only, energetic, specific numbers
- No brackets [], no emojis
- Faceless friendly: No "I", no "we", just facts
- YouTube algorithm: Title under 60 chars, description with #usa #breakingnews #shorts

RETURN FORMAT (STRICT):

TITLE: <12-15 words viral American, number/name, SEO, under 60 chars, searchable, e.g., "Trump's $5B Shocking Move Changes Texas Forever">
SCRIPT:
[0-3s HOOK] <25 words hook with number/name/FOMO>
[3-10s CONTEXT] <15 words context>
[10-25s CONFLICT] <25 words with retention>
[25-38s PAYOFF] <15 words payoff>
[38-40s CTA] <5 words CTA>
"""

        raw_text = call_gemini(prompt)
        
        title = news_text[:60]
        script_content = raw_text
        
        # Parse TITLE and SCRIPT
        if "TITLE:" in raw_text and "SCRIPT:" in raw_text:
            try:
                title_part = raw_text.split("TITLE:")[1].split("SCRIPT:")[0]
                script_part = raw_text.split("SCRIPT:")[1].strip()
                title = title_part.strip().split("\n")[0].strip()[:95]
                script_content = script_part
            except:
                pass
        elif "SCRIPT:" in raw_text:
            script_content = raw_text.split("SCRIPT:")[1].strip()
        
        # Clean script: Remove [0-3s] markers for TTS but keep for structure check
        clean_for_tts = re.sub(r'\[\d+-\d+s[^\]]*\]', '', script_content).strip()
        clean_for_tts = re.sub(r'\s+', ' ', clean_for_tts)
        
        # Ensure 65-85 words
        words = clean_for_tts.split()
        if len(words) > 90:
            clean_for_tts = " ".join(words[:85])
        
        final_title = get_searchable_title(title if len(title) > 5 else news_text)
        
        # Check viral structure
        has_hook = any(x in clean_for_tts.lower()[:100] for x in ["breaking", "shocking", "just", "trump", "biden", "$", "million"])
        has_retention = any(x in clean_for_tts.lower() for x in ["wait", "here's why", "what happened next", "don't miss", "this is huge"])
        
        return {
            "title": final_title,
            "full_script": clean_for_tts,
            "raw_script_structured": script_content,  # With [0-3s] markers for debugging
            "description": f"{clean_for_tts}\n\n#{news_text.split()[0]} #usanews #breakingnews #shorts #americanews\nWhy trending: {why}",
            "sources": f"Filter A+B+C Bot Friendly Rising Trend - Vol {search_vol} - {growth}",
            "viral_check": {"has_hook": has_hook, "has_retention": has_retention, "words": len(words)},
            "filters": {"why": why, "bot_friendly": bot_friendly, "search_volume": search_vol}
        }
    except Exception as e:
        print(f"GEMINI SHORT ERROR: {e}")
        safe_text = str(news_input)[:300] if not isinstance(news_input, dict) else news_input.get('query','Breaking USA News')[:300]
        # Fallback viral structure
        fallback_script = f"Breaking: {safe_text} just happened in Texas, affecting 3 million Americans. Wait, here's why this matters to you. This changes everything for American families. This is huge for America. Comment below what you think."
        return {
            "title": f"{safe_text[:50]} Breaking Today".title(),
            "full_script": fallback_script,
            "raw_script_structured": fallback_script,
            "description": f"{fallback_script} #usanews #shorts",
            "sources": "Fallback viral",
            "viral_check": {"has_hook": True, "has_retention": True, "words": len(fallback_script.split())},
            "filters": {}
        }
