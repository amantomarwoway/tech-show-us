"""
src_long/long_script_engine_v2.py - Human Body Structure Script
"""

import os
import re
from google import genai

def generate_long_script_american(trend: dict, min_words: int = 900, max_words: int = 1300) -> dict:
    query = trend.get("query", "USA Breaking News")
    why = trend.get("why_searching", "general_curiosity")
    interest = trend.get("american_interest", 80)
    
    trigger_map = {
        "fear_of_missing_out": "Americans are freaking out, you need to know this now",
        "safety_concern": "This affects your safety and family",
        "political_interest": "This changes everything in American politics",
        "financial_interest": "This hits your wallet directly",
        "curiosity_reason": "Here's why everyone is searching this",
        "general_curiosity": "This is blowing up across America"
    }
    # Extract key from why string
    why_key = why.split(" - ")[0] if " - " in why else why
    trigger_line = trigger_map.get(why_key, trigger_map["general_curiosity"])
    
    prompt = f"""
You are viral USA long-form news writer (6-9 min). American audience ONLY.

TREND (Direct Google USA Search): {query}
WHY: {why} -> {trigger_line}
INTEREST: {interest}/100
YT Suggestions: {trend.get('youtube_suggestions', [])}

HUMAN BODY STRUCTURE (MUST FOLLOW):

HADDIYA - Skeleton - Chapters:
0:00-0:30 HOOK - 25 words, number/name/shock + FOMO, must include keyword
0:30-2:00 CONTEXT - What happened, where, when, who (facts)
2:00-4:30 DEEP DIVE - 3 key points, why, evidence
4:30-6:30 IMPACT - How it affects Americans, reactions, what next
6:30-8:00 PAYOFF + CTA - Final truth, subscribe

MAANS - Muscle:
{min_words}-{max_words} words EXACT, full story, no cut, every sentence value
American English, specific numbers, cities, names, 8-10 paragraphs

NASE - Nerves:
Every 90 sec retention: "wait", "here's why this matters", "what happened next will shock you", "don't miss this part"
Emotion: shocking, huge, massive, breaking

KHAAL - Skin:
First 25 words must have keyword {query} + number/name
Last para CTA: comment, subscribe, watch next
No brackets, no emojis

RETURN FORMAT:

TITLE: <15 words viral American, number/name, SEO>
CHAPTERS:
0:00 - Hook: <line>
0:30 - Context: <line>
2:00 - Deep Dive: <line>
4:30 - Impact: <line>
6:30 - Payoff: <line>
SCRIPT:
<Full {min_words}-{max_words} word script>
DESCRIPTION:
<2 line SEO with #usa #breakingnews>
TAGS:
<10 tags comma separated>
"""

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        raw = response.text.strip() if response.text else ""
        
        title = query.title() + " Breaking News Today"
        chapters = []
        script = raw
        description = f"{query} breaking news. {trigger_line}"
        tags = ["usa news", "breaking news", "american news"]
        
        if "TITLE:" in raw:
            try: title = raw.split("TITLE:")[1].split("CHAPTERS:")[0].strip()[:95]
            except: pass
        if "CHAPTERS:" in raw and "SCRIPT:" in raw:
            try:
                chap_text = raw.split("CHAPTERS:")[1].split("SCRIPT:")[0].strip()
                for line in chap_text.split("\n"):
                    if "-" in line and ":" in line:
                        chapters.append(line.strip())
            except: pass
        if "SCRIPT:" in raw:
            try:
                script_part = raw.split("SCRIPT:")[1]
                if "DESCRIPTION:" in script_part:
                    script = script_part.split("DESCRIPTION:")[0].strip()
                    desc_part = script_part.split("DESCRIPTION:")[1]
                    if "TAGS:" in desc_part:
                        description = desc_part.split("TAGS:")[0].strip()
                        tags_text = desc_part.split("TAGS:")[1].strip()
                        tags = [t.strip() for t in tags_text.split(",")][:12]
                    else:
                        description = desc_part.strip()
                else:
                    script = script_part.strip()
            except:
                script = raw
        
        if len(script.split()) > max_words:
            script = " ".join(script.split()[:max_words])
        
        return {
            "title": title,
            "chapters": chapters,
            "script": script,
            "description": description,
            "tags": tags,
            "query": query,
            "word_count": len(script.split()),
            "why": why,
            "interest": interest
        }
    except Exception as e:
        print(f"GEMINI LONG ERROR: {e}")
        fallback = f"{query}. {trigger_line}. This is happening right now in America. Here's what you need to know. The details are shocking and affect millions of Americans. Stay tuned till the end for the full truth."
        return {
            "title": f"{query.title()} Breaking Today",
            "chapters": ["0:00 Hook", "0:30 Context", "2:00 Deep Dive", "4:30 Impact", "6:30 Payoff"],
            "script": (fallback + " ") * 60,
            "description": fallback,
            "tags": ["usa news", "breaking news"],
            "query": query,
            "word_count": len(fallback.split()) * 60,
            "why": why,
            "interest": interest
        }
