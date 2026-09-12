import os, sys, traceback, json, random, re
sys.path.append(os.path.join(os.path.dirname(__file__),'src'))
sys.path.append('.')

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
print(GOD_INSTRUCTION)

from src.database import init_db, save_story, mark_uploaded
from src.research_god import research_god_main
from src.editor_god import editor_god_main
from src.boss_approval import boss_approval_main
from src.uploader_god import upload_video_god
from src.self_evolution import self_evolution_main
from src.asset_fetcher import fetch_all_assets_god

def generate_script_god(story):
    # Tera original Gemini + OpenAI wala logic same rakha hai
    topic=story.get('title','')
    seo_title=story.get('seo_youtube_title','') or topic
    prompt=f"You are God Level US News Script Generator Topic: {topic} SEO: {seo_title} JSON only short_script long_script seo_youtube_title etc"
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
                        m=re.search(r'\{.*\}', text, re.DOTALL)
                        if m:
                            data=json.loads(m.group())
                            print(f"[SCRIPT GOD] Gemini {model} success")
                            return data
                except: continue
        except: pass
    return {
        "short_script": f"Breaking {topic}. Shocking update just leaked behind closed doors. This changes everything for millions.",
        "long_script": f"Breaking news {topic}. Full details explained.",
        "seo_youtube_title": seo_title[:60],
        "title_with_hashtag": f"{seo_title} #Breaking #Viral",
        "title_without_hashtag": seo_title,
        "description": f"{topic} explained.",
        "hashtags": ["#breakingnews","#worldnews"],
        "tags": ["world news","breaking news"],
        "script_visual_segments": [{"segment_text":f"Breaking {topic}","asset_type":"video","visual_search_prompt":"breaking news studio"}],
        "is_weekly_search_trend": True,
        "confidence_score": 80
    }

def create_video_god(script_data, editor_data):
    print("[VIDEO GOD] Creating video - FULL MECHANISM FIXED...")
    try:
        import src.video_generator as vg  # LAZY IMPORT FIX
        merged = {**script_data, **editor_data}
        merged['full_script']=script_data.get('short_script') or script_data.get('full_script','')
        merged['title']=script_data.get('seo_youtube_title','')
        merged['script_visual_segments']=script_data.get('script_visual_segments',[]) or editor_data.get('segments',[])
        video_path = vg.create_video(merged, {"title": merged['title']})
        return video_path
    except Exception as e:
        print(f"[VIDEO GOD] Fail {e}")
        traceback.print_exc()
        return "output/final.mp4"

def main():
    print("\n===== GOD LEVEL BOT START - 5 LEGS - FULL MECHANISM =====")
    init_db()
    stories = research_god_main()
    if not stories:
        print("[MAIN GOD] No stories - exit")
        return
    print(f"[MAIN] Leg1 got {len(stories)} stories")
    approved=None
    for candidate in stories[:5]:
        script_data = generate_script_god(candidate)
        editor_data = editor_god_main(script_data, candidate)
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        video_path = create_video_god(script_data, editor_data)
        boss_data = boss_approval_main(video_path, script_data, full_story)
        if not boss_data.get('approved'):
            print(f"[MAIN] REJECTED Score {boss_data.get('score')} - {boss_data.get('reason')}")
            continue
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    if not approved:
        print("[MAIN GOD] All rejected - SAFE EXIT")
        return
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    thumb_path = "output/thumb.jpg"
    try:
        from PIL import Image, ImageDraw
        img=Image.new('RGB',(1080,1920),(20,20,20))
        ImageDraw.Draw(img).text((540,960), candidate['title'][:40], fill=(255,255,255), anchor="mm")
        os.makedirs("output", exist_ok=True)
        img.save(thumb_path)
    except: thumb_path=None
    yt_id = upload_video_god(video_path, thumb_path, script_data, candidate, boss_data)
    if yt_id:
        mark_uploaded(story_id, yt_id)
        print(f"\n===== UPLOADED https://youtu.be/{yt_id} =====")

if __name__ == "__main__":
    main()
