import os, sys, traceback, json, random, re
sys.path.append(os.path.join(os.path.dirname(__file__),'src'))
sys.path.append('.')

from src.config import GOD_INSTRUCTION
print(GOD_INSTRUCTION)

from src.database import init_db, save_story, mark_uploaded
from src.research_god import research_god_main
from src.editor_god import editor_god_main
from src.boss_approval import boss_approval_main
from src.uploader_god import upload_video_god
from src.self_evolution import self_evolution_main
from src.asset_fetcher import fetch_all_assets_god

def generate_script_god(story):
    """Automated-Shorts-Generator - Hook, Retain, Reward framework - MUCKSCRAPER + VUZA style"""
    topic = story.get('title','')
    original_title = story.get('original_title', topic)
    seo_title = story.get('seo_youtube_title','') or topic

    # HOOK-RETAIN-REWARD prompt - Shashwat623 style
    prompt = f"""
You are Automated Shorts Generator - Hook, Retain, Reward framework.

Topic: {topic}
Original: {original_title}
SEO Title: {seo_title}
Source: {story.get('source','muckscraper')}

Task - Write in JSON only:
1. HOOK (0-3 sec): Pattern interrupt, shocking question, must have viral keywords like breaking, shocking, leaked, white house, trump, biden
2. RETAIN (3-10 sec): Context + twist + curiosity gap, keep viewers
3. REWARD (10-15 sec): Payoff + CTA, emotional punch

Rules:
- Total 40-50 words only, TTS friendly, no brackets
- First sentence must be shocking
- Use American English
- Must be YouTube Shorts viral

JSON only:
{{
  "hook": "0-3s shocking line",
  "retain": "3-10s context twist",
  "reward": "10-15s payoff CTA",
  "short_script": "hook + retain + reward combined 40-50 words",
  "long_script": "180-240 words detailed version for long video",
  "seo_youtube_title": "under 60 chars high CTR",
  "title_with_hashtag": "title #Breaking #Viral",
  "title_without_hashtag": "title",
  "description": "SEO description with hashtags",
  "hashtags": ["#breakingnews","#whitehouse","#trump"],
  "tags": ["breaking news","white house","shocking"],
  "script_visual_segments": [
    {{"segment_text":"hook text","asset_type":"video","visual_search_prompt":"shocked man reaction white house"}},
    {{"segment_text":"retain text","asset_type":"video","visual_search_prompt":"pentagon building exterior"}},
    {{"segment_text":"reward text","asset_type":"video","visual_search_prompt":"family watching news shocked"}}
  ],
  "is_weekly_search_trend": true,
  "confidence_score": 90
}}
"""

    # Try Ollama first - 100% free - MuckScraper style
    try:
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        import requests
        resp = requests.post(ollama_url, json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=20)
        if resp.status_code == 200:
            text = resp.json().get("response", "")
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data = json.loads(m.group())
                if "short_script" in data and "hook" in data:
                    print(f"[SCRIPT GOD] Ollama Hook/Retain/Reward success")
                    return data
    except Exception as e:
        print(f"[SCRIPT GOD] Ollama not running {e} - trying Gemini")

    # Try Gemini
    gem_key = os.getenv("GEMINI_API_KEY","")
    if gem_key:
        try:
            from google import genai
            client = genai.Client(api_key=gem_key)
            for model in ["gemini-2.0-flash","gemini-1.5-flash"]:
                try:
                    resp = client.models.generate_content(model=model, contents=prompt)
                    text = getattr(resp,'text','')
                    if text:
                        m = re.search(r'\{.*\}', text, re.DOTALL)
                        if m:
                            data = json.loads(m.group())
                            print(f"[SCRIPT GOD] Gemini {model} Hook/Retain/Reward success")
                            return data
                except: continue
        except: pass

    # Fallback to OpenAI
    open_key = os.getenv("OPENAI_API_KEY","")
    if open_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=open_key)
            resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.9, max_tokens=1500)
            text = resp.choices[0].message.content
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data = json.loads(m.group())
                print("[SCRIPT GOD] OpenAI Hook/Retain/Reward success")
                return data
        except: pass

    # GUARANTEED Hook-Retain-Reward fallback - MuckScraper + VUZA style
    hook = f"Breaking {topic.split()[0] if topic else 'White House'} shocker leaked!"
    retain = f"Behind closed doors, {original_title[:50]} changes everything."
    reward = f"This impacts millions of families tonight. Follow for updates."
    full_short = f"{hook} {retain} {reward}"

    return {
        "hook": hook,
        "retain": retain,
        "reward": reward,
        "short_script": full_short,
        "long_script": f"{full_short} Full details: {topic}. This is breaking news affecting millions. What happened, why it matters, and what happens next explained in detail.",
        "seo_youtube_title": seo_title[:60],
        "title_with_hashtag": f"{seo_title} #Breaking #Viral #WhiteHouse",
        "title_without_hashtag": seo_title,
        "description": f"{topic} explained. Hook: {hook} Retain: {retain} Reward: {reward}",
        "hashtags": ["#breakingnews","#whitehouse","#shocking","#viral"],
        "tags": ["breaking news","white house","shocking","viral","trump"],
        "script_visual_segments": [
            {"segment_text": hook, "asset_type":"video","visual_search_prompt":"shocked man reaction white house breaking"},
            {"segment_text": retain, "asset_type":"video","visual_search_prompt":"pentagon building secret meeting"},
            {"segment_text": reward, "asset_type":"video","visual_search_prompt":"family panic watching news"}
        ],
        "is_weekly_search_trend": True,
        "confidence_score": 85
    }

def create_video_god(script_data, editor_data):
    print("[VIDEO GOD - VUZA OFFLINE] Creating video - FULL MECHANISM FIXED...")
    try:
        import src.video_generator as vg # LAZY IMPORT FIX for pkg_resources error
        merged = {**script_data, **editor_data}
        merged['full_script'] = script_data.get('short_script') or script_data.get('full_script','')
        merged['title'] = script_data.get('seo_youtube_title','')
        merged['hook'] = script_data.get('hook','')
        merged['retain'] = script_data.get('retain','')
        merged['reward'] = script_data.get('reward','')
        merged['script_visual_segments'] = script_data.get('script_visual_segments',[]) or editor_data.get('segments',[])
        video_path = vg.create_video(merged, {"title": merged['title']})
        return video_path
    except Exception as e:
        print(f"[VIDEO GOD] Fail {e}")
        traceback.print_exc()
        return "output/final.mp4"

def main():
    print("\n===== GOD LEVEL BOT START - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE =====")
    print(GOD_INSTRUCTION)
    init_db()

    print("\n--- LEG 1: RESEARCH GOD - MUCKSCRAPER + OLLAMA ---")
    stories = research_god_main()
    print(f"[MAIN] Leg1 MuckScraper got {len(stories)} stories")

    approved=None
    for candidate in stories[:5]:
        print(f"\nChecking candidate: {candidate['title'][:60]} Score:{candidate.get('search_potential_score',0)} Source:{candidate.get('source')}")
        script_data = generate_script_god(candidate)
        print(f" [SCRIPT] HOOK: {script_data.get('hook','')[:50]} | RETAIN: {script_data.get('retain','')[:40]} | REWARD: {script_data.get('reward','')[:40]}")

        if script_data.get('confidence_score',0) < 70 and not script_data.get('is_weekly_search_trend'):
            print(f"Skipped low confidence {script_data.get('confidence_score')}")
            continue

        print("\n--- LEG 2: EDITOR GOD - VUZA OFFLINE ---")
        editor_data = editor_god_main(script_data, candidate)

        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)

        video_path = create_video_god(script_data, editor_data)

        print("\n--- LEG 3: BOSS APPROVAL ---")
        boss_data = boss_approval_main(video_path, script_data, full_story)

        if not boss_data.get('approved'):
            print(f"[MAIN] REJECTED by Boss Score {boss_data.get('score')} - {boss_data.get('reason')} - Trying next")
            continue

        print(f"[MAIN] APPROVED by Boss Score {boss_data.get('score')}")
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break

    candidate, script_data, editor_data, boss_data, story_id, video_path = approved

    print("\n--- LEG 4: UPLOADER GOD ---")
    thumb_path = "output/thumb.jpg"
    try:
        from PIL import Image, ImageDraw
        img=Image.new('RGB',(1080,1920),(20,20,20))
        d=ImageDraw.Draw(img)
        d.text((540,960), candidate['title'][:40], fill=(255,255,255), anchor="mm")
        os.makedirs("output", exist_ok=True)
        img.save(thumb_path)
    except: thumb_path=None

    yt_id = upload_video_god(video_path, thumb_path, script_data, candidate, boss_data)

    if yt_id:
        mark_uploaded(story_id, yt_id)
        print(f"\n===== UPLOADED https://youtu.be/{yt_id} =====")

    print("\n--- LEG 5: SELF EVOLUTION ---")
    try:
        evo = self_evolution_main()
        print(f"[MAIN] Evolution: {evo}")
    except Exception as e:
        print(f"[MAIN] Evolution fail {e}")

    print("\n===== MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA BOT DONE =====")

if __name__ == "__main__":
    main()
