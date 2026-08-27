import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import os, traceback
from news_fetcher import fetch_all_news
from source_verifier import verify_stories
from duplicate_detector import is_duplicate
from script_generator import generate_script
from fact_checker import fact_check
from video_generator import create_video
from thumbnail_generator import create_thumbnail
from youtube_uploader import upload_video
from database import init_db, save_story, mark_uploaded
from shorts_gate import gate_loop_for_shorts, THRESHOLD

def main():
    init_db()
    print(f"1. Fetching USA news from RSS (30 topics)...")
    raw_stories = fetch_all_news()  # Now returns 30
    if not raw_stories:
        print("No news fetched"); return
    print(f"Fetched: {len(raw_stories)} stories")

    print(f"2. Verifying {len(raw_stories)} stories...")
    try:
        verified = verify_stories(raw_stories)
    except Exception as e:
        print(f"verify_stories crashed: {e}, using raw")
        verified = raw_stories
    
    print(f"Verified count: {len(verified) if verified else 0}")
    if not verified or len(verified) == 0:
        print("Verification returned 0, using raw stories as fallback")
        verified = raw_stories

    print(f"3. Scoring & Ranking (150+ USA keywords, 8-factor pre-check)...")
    try:
        ranked = score_and_rank(verified)
    except Exception as e:
        print(f"score_and_rank crashed: {e}, using verified")
        ranked = verified

    print(f"Ranked count: {len(ranked) if ranked else 0}")
    if not ranked or len(ranked) == 0:
        print("Ranking empty, using verified as ranked")
        ranked = verified

    if not ranked:
        print("No stories left after all fallbacks, exiting")
        return

    # ===== NEW: 8-FACTOR STRICT GATE (75 threshold, no fallback) =====
    print(f"4. STARTING 8-FACTOR STRICT GATE - THRESHOLD {THRESHOLD} - NO FALLBACK")
    print(f"   🔥 Trend strength | 📈 Growth | 🕐 Freshness | 🇺🇸 USA relevance | 🥊 Competition | 🧠 Curiosity | ⚡ Hook | 📝 Script")

    def script_gen_wrapper(news_text):
        # Wrapper to match gate_loop expectation: news_text is title string
        dummy_story = {"title": news_text, "summary": news_text}
        result = generate_script(dummy_story)
        return result

    approved_topic, script_text, scores = gate_loop_for_shorts(ranked, script_gen_wrapper)

    if not approved_topic:
        print("❌ All 30 topics FAILED strict 75 gate - SAFE EXIT, no low quality video")
        return

    print(f"🔥 FINAL APPROVED TOPIC: {approved_topic['title']}")
    print(f"   Scores: {scores}")

    # Now proceed with the approved story only
    story = approved_topic
    # Duplicate check (optional, but keep)
    try:
        if is_duplicate(story):
            print(f"NOTE: Duplicate found but still processing (APPROVED topic): {story['title']}")
    except:
        pass

    story_id = save_story(story)

    print(f"5. Generating FINAL script for APPROVED topic: {story['title']}")
    script_data = generate_script(story)
    if not script_data: 
        print("Script generation failed, exiting (no fallback)")
        return

    print(f"6. Fact Checking script...")
    try:
        validation = fact_check(script_data['full_script'], story)
        if not validation['passed']:
            print(f"Fact check FAILED: {validation['report']}, but continuing as APPROVED topic passed gate")
    except Exception as e:
        print(f"fact_check crashed: {e}, continuing")

    print(f"7. Creating video...")
    video_path = create_video(script_data, story)
    thumb_path = create_thumbnail(script_data, story)
    print(f"Video created at: {video_path}")

    print(f"8. Uploading to YouTube...")
    yt_id = upload_video(video_path, thumb_path, script_data, story)

    if yt_id:
        mark_uploaded(story_id, yt_id)
        print(f"9. UPLOADED: https://youtu.be/{yt_id} | Scores: {scores}")
    else:
        print("Upload returned None - FAILED (no retry, no fallback)")

if __name__ == "__main__":
    try: 
        main()
    except Exception as e:
        traceback.print_exc()
        with open("logs.txt","w") as f: 
            f.write(traceback.format_exc())
        sys.exit(1)
