import os, json, google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_script(story):
    sources_text = ", ".join([s['source'] for s in story['all_sources']])
    prompt = f"""
    You are a factual USA news explainer. DO NOT invent facts.
    Story: {story['title']} - {story['summary']}
    Sources: {sources_text}
    Create JSON ONLY:
    {{"hook": "1 sentence hook", "what_happened": "verified facts only, with date", "why_matters": "context", "what_we_know": "confirmed vs developing", "full_script": "60 sec script: HOOK, WHAT HAPPENED, WHY IT MATTERS, SOURCES. Mention sources.", "title_candidates": ["title1","title2","title3"], "description": "factual description"}}
    """
    try:
        res = model.generate_content(prompt)
        txt = res.text.replace("```json","").replace("```","").strip()
        data = json.loads(txt)
        data['sources'] = sources_text
        data['story'] = story
        return data
    except Exception as e:
        print(f"Script gen fail: {e}"); return None
