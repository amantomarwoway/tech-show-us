"""
main.py - GOD LEVEL MAIN - 5 LEGS ORCHESTRATOR
Flow: Leg1 Research God (Wire 45min + World SEO) -> Leg2 Editor God (Best visuals from everywhere) -> Leg3 Boss Approval (Live world demand) -> Leg4 Uploader God -> Leg5 Self Evolution
Instruction: Har leg har cheez kahin se bhi best tarike se use kare
"""

import os, sys, time, traceback, json, random
sys.path.append(os.path.join(os.path.dirname(__file__),'src'))
sys.path.append('.')

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
print(GOD_INSTRUCTION)

# Import all 5 legs
try:
    from src.research_god import research_god_main
    from src.editor_god import editor_god_main
    from src.boss_approval import boss_approval_main
    from src.uploader_god import upload_video_god
    from src.self_evolution import self_evolution_main
    from src.asset_fetcher import fetch_all_assets_god
    from src.database import init_db, save_story, mark_uploaded
    GOD_AVAILABLE=True
    print("[MAIN GOD] All 5 legs loaded - GOD LEVEL")
except Exception as e:
    print(f"[MAIN GOD] Import fail {e} - trying fallback")
    traceback.print_exc()
    GOD_AVAILABLE=False

def generate_script_god(story):
    """Generate script using best AI - Gemini > OpenAI > HF"""
    topic=story.get('title','')
    seo_title=story.get('seo_youtube_title','') or topic
    # Build prompt
    prompt=f"""
You are God Level US + World News Script Generator for YouTube Shorts + Long.

Topic: {topic}
SEO Title: {seo_title}
URL: {story.get('url','')}
Target Countries: {ENGLISH_COUNTRIES}

Task:
1. Write 40-50 words script, 11-15 sec for shorts, emotional + shocking first sentence, TTS friendly.
2. Also write 180-240 words long version for 3-4 min video.
3. Visual Context: Break shorts script into 6-8 segments, each with visual_search_prompt exact like "Pentagon building exterior daytime" for script "Pentagon deployed".
4. World SEO: Title with/without hashtag, description with hashtags, tags for English + half English countries.

JSON only:
{{
  "short_script": "40-50 words",
  "long_script": "180-240 words",
  "seo_youtube_title": "under 60 chars high CTR",
  "title_with_hashtag": "title #Breaking #Viral",
  "title_without_hashtag": "title",
  "description": "SEO description with hashtags",
  "hashtags": ["#breakingnews","#worldnews"],
  "tags": ["world news","breaking news",...],
  "script_visual_segments": [
    {{"segment_text":"...","asset_type":"video","visual_search_prompt":"..."}}
  ],
  "is_weekly_search_trend": true,
  "confidence_score": 90
}}
"""
    # Try best AI
    gem_key=os.getenv("GEMINI_API_KEY","")
    if gem_key:
        try:
            from google import genai
            client=genai.Client(api_key=gem_key)
            for model in ["gemini-2.0-flash","gemini-1.5-flash"]:
                try:
                    resp=client.models.generate_content(model=model, contents=prompt)
                    text=getattr(resp,'text','')
                    if text:
                        # Parse JSON
                        import re
                        m=re.search(r'\{.*\}', text, re.DOTALL)
                        if m:
                            data=json.loads(m.group())
                            print(f"[SCRIPT GOD] Gemini {model} success")
                            return data
                except: continue
        except: pass
    open_key=os.getenv("OPENAI_API_KEY","")
    if open_key:
        try:
            from openai import OpenAI
            client=OpenAI(api_key=open_key)
            resp=client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.9, max_tokens=1500)
            text=resp.choices[0].message.content
            import re
            m=re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                data=json.loads(m.group())
                print("[SCRIPT GOD] OpenAI success")
                return data
        except: pass
    # Fallback
    return {
        "short_script": f"Breaking {topic}. Shocking update just leaked behind closed doors. This changes everything for millions.",
        "long_script": f"Breaking news {topic}. Full details explained. This is world breaking news. What happened, why it matters, what next.",
        "seo_youtube_title": seo_title[:60],
        "title_with_hashtag": f"{seo_title} #Breaking #Viral",
        "title_without_hashtag": seo_title,
        "description": f"{topic} explained. {' '.join(story.get('hashtags',[]))}",
        "hashtags": story.get('hashtags',["#breakingnews"]),
        "tags": story.get('tags',["breaking news"]),
        "script_visual_segments": [{"segment_text":f"Breaking {topic}","asset_type":"video","visual_search_prompt":"breaking news studio"}],
        "is_weekly_search_trend": True,
        "confidence_score": 80
    }

def create_video_god(script_data, editor_data):
    """Create video using editor god assets - Best from everywhere"""
    print("[VIDEO GOD] Creating video from editor god best assets...")
    try:
        # Use existing video_generator but with god assets
        from src.video_generator import create_video as old_create
        # Merge
        merged = {**script_data, **editor_data}
        merged['full_script']=script_data.get('short_script') or script_data.get('full_script','')
        merged['title']=script_data.get('seo_youtube_title','')
        merged['script_visual_segments']=script_data.get('script_visual_segments',[]) or editor_data.get('segments',[])
        # Call old generator which already uses DuckDuckGo + yt-dlp best
        video_path = old_create(merged, {"title": merged['title']})
        return video_path
    except Exception as e:
        print(f"[VIDEO GOD] Fail {e} - using fallback")
        traceback.print_exc()
        return "output/final.mp4"

def main():
    print("\n===== GOD LEVEL BOT START - 5 LEGS =====")
    print(GOD_INSTRUCTION)
    init_db()
    
    # LEG 1: RESEARCH GOD
    print("\n--- LEG 1: RESEARCH GOD ---")
    stories = research_god_main()
    if not stories:
        print("[MAIN GOD] No stories - exit")
        return
    print(f"[MAIN] Leg1 got {len(stories)} stories")
    
    approved=None
    for candidate in stories[:5]:
        print(f"\nChecking candidate: {candidate['title'][:60]} Score:{candidate.get('search_potential_score',0)}")
        # Generate script
        script_data = generate_script_god(candidate)
        if script_data.get('confidence_score',0) < 75 and not script_data.get('is_weekly_search_trend'):
            print(f"Skipped low confidence {script_data.get('confidence_score')}")
            continue
        
        # LEG 2: EDITOR GOD
        print("\n--- LEG 2: EDITOR GOD ---")
        editor_data = editor_god_main(script_data, candidate)
        
        # Merge for video
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        
        # Create video
        video_path = create_video_god(script_data, editor_data)
        
        # LEG 3: BOSS APPROVAL - Live world demand check
        print("\n--- LEG 3: BOSS APPROVAL ---")
        boss_data = boss_approval_main(video_path, script_data, full_story)
        
        if not boss_data.get('approved'):
            print(f"[MAIN] REJECTED by Boss Score {boss_data.get('score')} - {boss_data.get('reason')} - Trying next candidate")
            continue
        
        print(f"[MAIN] APPROVED by Boss Score {boss_data.get('score')} - High demand in {boss_data.get('target_countries')}")
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    if not approved:
        print("[MAIN GOD] All candidates rejected by Boss - SAFE EXIT")
        return
    
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    # LEG 4: UPLOADER GOD
    print("\n--- LEG 4: UPLOADER GOD ---")
    thumb_path = "output/thumb.jpg"
    # Create simple thumb if not exists
    try:
        from PIL import Image, ImageDraw, ImageFont
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
    
    # LEG 5: SELF EVOLUTION
    print("\n--- LEG 5: SELF EVOLUTION ---")
    try:
        evo = self_evolution_main()
        print(f"[MAIN] Evolution: {evo}")
    except Exception as e:
        print(f"[MAIN] Evolution fail {e}")
    
    print("\n===== GOD LEVEL BOT DONE - 5 LEGS COMPLETE =====")

if __name__ == "__main__":
    main()
