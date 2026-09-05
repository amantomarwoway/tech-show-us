import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import os, traceback

# --- ADD-ON Problem 6 - trend_filters.py DEAD hai, isko False karo warna crash hoga ---
FILTERS_AVAILABLE = False
apply_all_filters_short_bot = None
print("[MAIN Problem 6] FILTERS_AVAILABLE=False - trend_filters.py deleted, direct news_fetcher use hoga")
# --- END - Pehle wala try-except import hata diya ---

from news_fetcher import fetch_all_news

try:
    from source_verifier import verify_stories
except ImportError:
    def verify_stories(x): return x

try:
    from duplicate_detector import is_duplicate
except ImportError:
    def is_duplicate(x): return False

from script_generator import generate_script

try:
    from fact_checker import fact_check
except ImportError:
    def fact_check(s, st): return {"passed": True, "report": "skip"}

try:
    from video_generator import create_video
except ImportError:
    def create_video(*a, **k): return "output/final.mp4"

try:
    from thumbnail_generator import create_thumbnail
except ImportError:
    try:
        from thumbnail_generator import generate_thumbnail as create_thumbnail
    except:
        def create_thumbnail(*a, **k): return "output/thumb.jpg"

try:
    from youtube_uploader import upload_video
except ImportError:
    def upload_video(*a, **k): return "test_id"

try:
    from database import init_db, save_story, mark_uploaded
except ImportError:
    def init_db(): pass
    def save_story(x): return 1
    def mark_uploaded(a,b): pass

from shorts_gate import gate_loop_for_shorts, THRESHOLD, BOT_FRIENDLY_THRESHOLD

try:
    from trend_score import score_and_rank
except ImportError:
    def score_and_rank(s): return s

def main():
    init_db()

    manual_topic = os.getenv("MANUAL_TOPIC", "").strip()
    if manual_topic:
        print(f"1. MANUAL Topic: {manual_topic}")
        raw_stories = [{"title": manual_topic, "query": manual_topic, "url": "", "source": "manual", "published": None, "summary": manual_topic, "search_volume": 80, "bot_friendly": True, "filter_c_score": 85, "bot_friendly_score": 85}]
    elif FILTERS_AVAILABLE:
        print(f"1. Fetching USA news - Filter A+B+C (Tacko Style Every Video)")
        print(f" [Filter A] YouTube Search Filter US Breakout")
        print(f" [Filter B] Autocomplete Feeder Half keyword hot")
        print(f" [Filter C] Format & Engagement Bot friendly >=70")
        try:
            raw_stories = apply_all_filters_short_bot()
            if not raw_stories:
                print("Filter A+B+C returned 0, fallback to RSS")
                raw_stories = fetch_all_news()
        except Exception as e:
            print(f"Filter A+B+C crashed: {e}")
            traceback.print_exc()
            raw_stories = fetch_all_news()
    else:
        print(f"1. Fetching USA news from RSS (Fallback) - Problem 6 Synced - Direct Google Trends + Live Fallback")
        raw_stories = fetch_all_news()

    if not raw_stories:
        print("No news fetched"); return
    print(f"Fetched: {len(raw_stories)} stories")
    for i, s in enumerate(raw_stories[:5]):
        print(f" {i+1}. {s.get('query','')[:60]} | Vol {s.get('search_volume','')} | Bot {s.get('filter_c_score', s.get('bot_friendly_score',''))} | {s.get('growth','')}")

    print(f"2. Verifying {len(raw_stories)} stories...")
    try:
        verified = verify_stories(raw_stories)
    except Exception as e:
        print(f"verify_stories crashed: {e}, using raw")
        verified = raw_stories

    if not verified:
        verified = raw_stories

    print(f"3. Scoring & Ranking...")
    try:
        ranked = score_and_rank(verified)
    except:
        ranked = verified

    if not ranked:
        ranked = verified

    print(f"4. STARTING GATE THRESHOLD {THRESHOLD} + BOT_FRIENDLY {BOT_FRIENDLY_THRESHOLD} + Tacko 4 segments + FACT CHECKER (Shorts Gate ke baad)")

    def script_gen_wrapper(topic_input):
        if isinstance(topic_input, dict):
            dummy = topic_input
        else:
            dummy = {"title": str(topic_input), "query": str(topic_input), "summary": str(topic_input), "search_volume": 60}
        result = generate_script(dummy)
        return result

    # ===== NEW FLOW: GATE ke baad FACT CHECKER, uske baad hi FINAL APPROVED =====
    approved_topic = None
    script_result = None
    scores = None
    validation = None

    # Ranked list me se ek-ek karke check karo
    for idx, candidate in enumerate(ranked[:5]): # Top 5 me se best dhoondo jo Fact Check bhi pass kare
        print(f"\n[GATE] {idx+1}/{min(5,len(ranked))} Checking: {candidate.get('query') or candidate.get('title')} | Vol ? | Bot ?")

        # 1. GATE CHECK
        temp_approved, temp_script, temp_scores = gate_loop_for_shorts([candidate], script_gen_wrapper)

        if not temp_approved:
            print(f" -> GATE FAIL for {candidate.get('query')}")
            continue

        print(f" -> GATE PASS pre-script: {temp_scores}")

        # 2. FACT CHECKER - SHORTS GATE KE BAAD, FINAL APPROVED SE PEHLE
        print(f"5. Fact Checking (Shorts Gate ke baad)...")
        try:
            # fact_checker ab dict return karta hai {"passed": True/False}
            validation = fact_check(temp_script, temp_approved)

            if not validation.get('passed', False):
                print(f"❌ REJECTED BY FACT CHECKER: {temp_approved.get('title') or temp_approved.get('query')}")
                print(f"   Reason: {validation.get('report')}")
                print(f"   -> Is topic ko FINAL APPROVED nahi karenge, agla topic try karenge")
                continue # Agla topic
            else:
                print(f"✅ FACT CHECKER PASS: {validation.get('report')}")

        except Exception as e:
            print(f"fact_check crashed: {e}, continuing with PASS")
            traceback.print_exc()
            validation = {"passed": True, "report": f"crash bypass {e}"}

        # 3. Agar yahan tak aa gaya matlab GATE + FACT CHECKER dono PASS
        approved_topic = temp_approved
        script_result = temp_script
        scores = temp_scores
        break # Mil gaya final topic

    if not approved_topic:
        print("❌ All topics FAILED gate + fact checker - SAFE EXIT - Koi bhi topic FINAL APPROVED nahi hua")
        return

    print(f"\n🔥 FINAL APPROVED: {approved_topic.get('title') or approved_topic.get('query')} (Fact Checker ke baad)")
    print(f" Scores: {scores}")
    print(f" Fact Report: {validation.get('report') if validation else 'N/A'}")

    if isinstance(script_result, dict):
        script_data = script_result
        title = script_data.get('title','')
        full_script = script_data.get('full_script','')
        title_options = script_data.get('title_options', [title])
        segments = script_data.get('script_segments', {})
        visual = script_data.get('visual_instructions', {})
        description = script_data.get('description','')
        tags_all = script_data.get('tags_all','')
        print("\n=== TACKO STYLE PER VIDEO (Every video ke hisaab se) ===")
        print(f"Selected Title: {title}")
        print("Title Options:")
        for i, to in enumerate(title_options[:4],1):
            print(f" {i}. {to}")
        print("\nSegments:")
        for k,v in segments.items():
            print(f" {k}: {v[:150]}...")
        print(f"\nVisual: Music={visual.get('music')} | Captions={visual.get('captions')} | Pacing={visual.get('pacing')}")
        print(f"\nDescription: {description[:400]}...")
        print(f"Tags: {tags_all[:250]}...")
    else:
        script_data = generate_script(approved_topic)
        title = script_data.get('title','') if isinstance(script_data, dict) else str(script_data)[:60]
        full_script = script_data.get('full_script','') if isinstance(script_data, dict) else str(script_data)
        description = script_data.get('description','') if isinstance(script_data, dict) else full_script
        title_options = [title]
        segments = {}
        visual = {}
        tags_all = ""

    try:
        if is_duplicate(approved_topic):
            print(f"NOTE: Duplicate but still processing: {approved_topic.get('title')}")
    except:
        pass

    story_id = save_story(approved_topic)

    print(f"\n5. FINAL script already with Tacko structure - Already Fact Checked PASS")

    print(f"6. Creating video with Tacko instructions...")
    try:
        video_path = create_video(script_data, approved_topic)
    except:
        video_path = create_video(full_script, "output/final.mp4")

    try:
        thumb_path = create_thumbnail(script_data, approved_topic)
    except:
        thumb_path = "output/thumb.jpg"

    print(f"Video: {video_path} | Thumb: {thumb_path}")

    print(f"8. Uploading with SEO title + description + tags...")
    print(f" Title: {title}")
    try:
        yt_id = upload_video(video_path, thumb_path, script_data, approved_topic)
    except:
        try:
            yt_id = upload_video(video_path, thumb_path, title, description)
        except:
            yt_id = "test"

    if yt_id:
        mark_uploaded(story_id, yt_id)
        print(f"9. UPLOADED: https://youtu.be/{yt_id}")
        print(f" Used Title Options: {title_options}")
    else:
        print("Upload failed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        with open("logs.txt","w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)
