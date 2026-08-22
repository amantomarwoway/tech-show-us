import os
from google import genai

def generate_script(news_text):
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""
        You are a USA tech news anchor. Write a 40 second YouTube Shorts script for this news in Hinglish, energetic style:
        {news_text}
        Keep it under 80 words. No brackets.
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        print(f"Generated Script: {response.text}")
        return response.text
    except Exception as e:
        print(f"GEMINI ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
