import os
from google import genai

def get_searchable_title(topic):
    """100% block-proof - YouTube block hone pe bhi searchable title dega"""
    import requests, re
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
                         params={"client": "youtube", "ds": "yt", "q": topic, "hl": "en", "gl": "US"},
                         timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 5][:2]
        if suggestions:
            return suggestions[0].title()
    except:
        pass
    # FIX: No more hardcoded tech news
    clean_topic = str(topic).strip()
    if len(clean_topic) < 3:
        clean_topic = "USA Breaking News"
    return f"{clean_topic} Today".title()[:95]

def generate_script(news_input):
    try:
        # FIX: Handle dict or string properly
        if isinstance(news_input, dict):
            news_text = news_input.get('title','') or news_input.get('summary','') or str(news_input.get('query',''))
        else:
            news_text = str(news_input)
        
        news_text = news_text.strip()
        if len(news_text) < 3:
            news_text = "Breaking news from USA"

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # FIX: Removed "tech news anchor" - now general USA news anchor
        prompt = f"""
You are a USA breaking news anchor for a YouTube Shorts channel covering ALL categories - politics, sports, entertainment, business, weather, crime, and tech.

Write a 40 second YouTube Shorts script for this TRENDING TOPIC.

TRENDING TOPIC: {news_text}

Rules:
- Keep it under 80 words.
- No brackets, no emojis.
- Write in clear American English only, no Hinglish.
- First line must be a catchy TITLE under 15 words BASED ON THE TOPIC, not generic "USA Tech News".
- Do NOT add "tech" word unless topic is actually about technology.
- Be specific to the given topic.
- Energetic and professional style.

Return format:
TITLE: <your specific title based on topic>
SCRIPT: <your 40 sec script specific to topic>
"""
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        raw_text = response.text.strip() if response.text else ""
        print(f"Generated Script: {raw_text}")

        title = news_text[:90]  # Default to actual topic
        script_content = raw_text

        if "TITLE:" in raw_text and "SCRIPT:" in raw_text:
            try:
                title_part = raw_text.split("TITLE:")[1].split("SCRIPT:")[0]
                script_part = raw_text.split("SCRIPT:")[1].strip()
                title = title_part.strip()[:95]
                script_content = script_part
            except:
                pass
        elif raw_text:
            lines = raw_text.split('\n')
            if lines:
                title = lines[0][:95]
                script_content = raw_text

        # FIX: Use actual topic, not hardcoded tech news
        final_title = get_searchable_title(title if len(title) > 5 else news_text)

        return {
            "title": final_title,
            "full_script": script_content,
            "description": f"{script_content}\n\n#{news_text.split()[0]} #usanews #breakingnews #shorts",
            "sources": "USA NEWS - Google Trends"
        }

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        import traceback
        traceback.print_exc()
        # FIX: No tech news fallback
        safe_text = str(news_input)[:400] if not isinstance(news_input, dict) else news_input.get('title','Breaking USA News')[:400]
        return {
            "title": f"{safe_text[:60]} Breaking News Today".title(),
            "full_script": safe_text,
            "description": f"{safe_text} #usanews #shorts",
            "sources": "USA NEWS"
        }
