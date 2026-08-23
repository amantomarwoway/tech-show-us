import os
from google import genai

def generate_script(news_text):
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""
You are a USA tech news anchor for a YouTube Shorts channel.

Write a 40 second YouTube Shorts script for this news in AMERICAN ENGLISH, energetic and professional style.

News: {news_text}

Rules:
- Keep it under 80 words.
- No brackets, no emojis.
- Write in clear American English only, no Hinglish.
- First line must be a catchy TITLE under 15 words.

Return format:
TITLE: <your title>
SCRIPT: <your 40 sec script>
"""
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        raw_text = response.text.strip() if response.text else ""
        print(f"Generated Script: {raw_text}")

        # --- ROOT FIX: String to Dict ---
        title = "USA Tech News"
        script_content = raw_text

        if "TITLE:" in raw_text and "SCRIPT:" in raw_text:
            try:
                title_part = raw_text.split("TITLE:")[1].split("SCRIPT:")[0].strip()
                script_part = raw_text.split("SCRIPT:")[1].strip()
                title = title_part[:95]
                script_content = script_part
            except:
                pass
        elif raw_text:
            # First line as title if no format
            lines = raw_text.split('\n')
            title = lines[0][:95]
            script_content = raw_text

        # Always return DICT, never string - this fixes Line 257 error
        return {
            "title": title,
            "full_script": script_content,
            "description": f"{script_content}\n\n#usanews #technews #shorts",
            "sources": "USA NEWS"
        }

    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Return dict even on error to avoid crash
        return {
            "title": "USA Tech News Update",
            "full_script": str(news_text)[:400] if news_text else "Breaking tech news from USA.",
            "description": "Latest USA Tech News #shorts",
            "sources": "USA NEWS"
        }
