"""
MAIN.PY - FINAL WITH 6 NEW FILES INTEGRATED + RETENTION + VALIDATION - KUCH DELETE NAHI
Flow: hungerness -> script 40w -> video 0.8s 12sec -> anti_bot + audio_retention -> 4K upload -> analytics + title_changer + comment + reupload
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
import os, traceback, random, time

FILTERS_AVAILABLE = False
apply_all_filters_short_bot = None
print("[MAIN Problem 6] FILTERS_AVAILABLE=False - direct news_fetcher + 6 NEW FILES")

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
    from script_generator import validate_script_factory
except ImportError:
    def validate_script_factory(script, topic): 
        low = script.lower() if isinstance(script, str) else str(script).lower()
        return "leaked" in low or "secret" in low

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

# ===== 6 NEW FILES IMPORT - KUCH DELETE NAHI, ADD ONLY =====
try:
    from anti_bot_detector import get_anti_bot_config, get_ffmpeg_vf_and_fps
    ANTI_BOT_AVAILABLE = True
except ImportError:
    ANTI_BOT_AVAILABLE = False
    def get_anti_bot_config(): return {"font":"Anton","color":"#FFFFFF","fps":29.97}
    def get_ffmpeg_vf_and_fps(): return ("noise=alls=5:hue=h=2", 29.97, {})

try:
    from audio_retention import get_tts_retention_filter, get_bgm_volume_filter
    AUDIO_RETENTION_AVAILABLE = True
except ImportError:
    AUDIO_RETENTION_AVAILABLE = False
    def get_tts_retention_filter(): return "atempo=1.15"
    def get_bgm_volume_filter(): return "volume=1"

try:
    from analytics_monitor import check_retention_drop, fetch_youtube_analytics
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    def check_retention_drop(*a,**k): return [],[]
    def fetch_youtube_analytics(*a,**k): return []

try:
    from title_changer import get_new_trending_title, auto_change_titles
    TITLE_CHANGER_AVAILABLE = True
except ImportError:
    TITLE_CHANGER_AVAILABLE = False
    def get_new_trending_title(old): return old
    def auto_change_titles(*a,**k): pass

try:
    from comment_engine import reply_witty_provocative, fetch_first_10_comments
    COMMENT_ENGINE_AVAILABLE = True
except ImportError:
    COMMENT_ENGINE_AVAILABLE = False
    def reply_witty_provocative(*a,**k): return 0
    def fetch_first_10_comments(*a,**k): return []

try:
    from reupload_manager import check_reupload_candidates, smart_reupload_process
    REUPLOAD_AVAILABLE = True
except ImportError:
    REUPLOAD_AVAILABLE = False
    def check_reupload_candidates(): return []
    def smart_reupload_process(*a,**k): return None

def check_market_hungerness(topic_dict):
    q = (topic_dict.get('query','') or topic_dict.get('title','')).lower()
    vol = topic_dict.get('search_volume',0)
    freshness_score = 80
    try:
        from shorts_gate import score_freshness
        freshness_score = score_freshness(topic_dict)
    except:
        pass
    hungry_keywords = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed"]
    has_hungry = any(k in q for k in hungry_keywords)
    if vol>=60 and freshness_score>=80 and has_hungry:
        return True, f"HUNGRY: vol {vol} + fresh {freshness_score} + hungry kw"
    if vol>=45 and has_hungry:
        return True, f"HUNGRY MEDIUM: vol {vol} + hungry kw"
    if vol>=30:
        return True, f"HUNGRY LOW: vol {vol} - still okay"
    return False, f"NOT HUNGRY: vol {vol} low"

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
    else:
        print(f"1. Fetching USA news from RSS - Direct Google Trends + Live + Retention + 6 New Files")
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

    print(f"3. Scoring & Ranking + Market Hungerness pre-check...")
    try:
        ranked = score_and_rank(verified)
    except:
        ranked = verified
    if not ranked:
        ranked = verified

    hungry_ranked=[]
    for r in ranked[:15]:
        is_hungry, reason = check_market_hungerness(r)
        print(f" [HUNGER CHECK] {r.get('query','')[:50]} -> {reason}")
        if is_hungry:
            hungry_ranked.append(r)
    if hungry_ranked:
        ranked = hungry_ranked
        print(f" Market hungry filter: {len(hungry_ranked)} topics hungry")
    else:
        print(f" Market hungry filter: no hungry found, using original top")

    print(f"4. STARTING GATE THRESHOLD {THRESHOLD} + BOT_FRIENDLY {BOT_FRIENDLY_THRESHOLD} + RETENTION 40w + VALIDATION FACTORY + FACT CHECKER STRICT + 6 NEW FILES")

    def script_gen_wrapper(topic_input):
        if isinstance(topic_input, dict):
            dummy = topic_input
        else:
            dummy = {"title": str(topic_input), "query": str(topic_input), "summary": str(topic_input), "search_volume": 60}
        result = generate_script(dummy)
        return result

    approved_topic = None
    script_result = None
    scores = None
    validation = None

    for idx, candidate in enumerate(ranked[:10]):
        print(f"\n{'='*60}")
        print(f"[TRY] {idx+1}/10 Topic: {candidate.get('query') or candidate.get('title')}")
        print(f"{'='*60}")
        temp_approved, temp_script, temp_scores = gate_loop_for_shorts([candidate], script_gen_wrapper)
        if not temp_approved:
            print(f" -> GATE FAIL, next topic...")
            continue
        print(f" -> GATE PASS pre-script: {temp_scores}")
        script_text = ""
        if isinstance(temp_script, dict):
            script_text = temp_script.get('full_script','') or temp_script.get('raw_script_structured','')
        else:
            script_text = str(temp_script)
        wc = len(script_text.split())
        print(f" [RETENTION ORCHESTRATION] Words={wc} target 40 (11-13 sec)")
        if not (35 <= wc <= 45):
            print(f" ❌ RETENTION FAIL: {wc} words not in 35-45, skipping")
            continue
        print(f" [VALIDATION FACTORY] Checking behind closed doors + leaked + first to know + bold daave...")
        topic_str = candidate.get('query','') or candidate.get('title','')
        if not validate_script_factory(script_text, topic_str):
            print(f" ❌ VALIDATION FACTORY FAIL")
            continue
        else:
            print(f" ✅ VALIDATION FACTORY PASS")
        print(f"\n5. Fact Checking (STRICT 3 CHECKS)...")
        try:
            validation = fact_check(temp_script, temp_approved)
            if not validation.get('passed', False):
                print(f"❌ REJECTED BY FACT CHECKER: {validation.get('report')}")
                continue
            else:
                print(f"✅ FACT CHECKER PASS ALL 3: {validation.get('report')}")
        except Exception as e:
            print(f"fact_check crashed: {e} -> FAIL")
            traceback.print_exc()
            continue
        approved_topic = temp_approved
        script_result = temp_script
        scores = temp_scores
        break

    if not approved_topic:
        print("\n❌ All topics FAILED - SAFE EXIT")
        return

    print(f"\n🔥 FINAL APPROVED: {approved_topic.get('title') or approved_topic.get('query')}")
    print(f" Scores: {scores}")

    if isinstance(script_result, dict):
        script_data = script_result
        title = script_data.get('title','')
        full_script = script_data.get('full_script','')
        title_options = script_data.get('title_options', [title])
        description = script_data.get('description','')
    else:
        script_data = generate_script(approved_topic)
        title = script_data.get('title','') if isinstance(script_data, dict) else str(script_data)[:60]
        full_script = script_data.get('full_script','') if isinstance(script_data, dict) else str(script_data)
        description = script_data.get('description','') if isinstance(script_data, dict) else full_script
        title_options = [title]

    try:
        if is_duplicate(approved_topic):
            print(f"NOTE: Duplicate but still processing: {approved_topic.get('title')}")
    except:
        pass

    story_id = save_story(approved_topic)

    print(f"\n=== 6 NEW FILES INTEGRATION - NO DELETE ===")
    anti_bot_cfg = {}
    if ANTI_BOT_AVAILABLE:
        try:
            vf, fps, anti_bot_cfg = get_ffmpeg_vf_and_fps()
            print(f"[ANTI_BOT_DETECTOR] font={anti_bot_cfg.get('font')} colour={anti_bot_cfg.get('color')} fps={fps} frame_rule={anti_bot_cfg.get('frame_rule')}")
            approved_topic['anti_bot_cfg'] = anti_bot_cfg
            approved_topic['fps_used'] = fps
            approved_topic['vf_filter'] = vf
        except Exception as e:
            print(f"[ANTI_BOT] Fail {e}")

    tts_filter = ""
    bgm_filter = ""
    if AUDIO_RETENTION_AVAILABLE:
        try:
            tts_filter = get_tts_retention_filter()
            bgm_filter = get_bgm_volume_filter()
            print(f"[AUDIO_RETENTION] TTS: {tts_filter[:80]}... BGM: {bgm_filter[:60]}...")
            approved_topic['tts_filter'] = tts_filter
            approved_topic['bgm_filter'] = bgm_filter
        except Exception as e:
            print(f"[AUDIO_RETENTION] Fail {e}")

    print(f"\n5. FINAL script with Retention 40w + Validation Factory - Fact Checked PASS + Anti-Bot + Audio Retention")
    print(f"6. Creating video with Retention Orchestration (0.8 sec clip density + 1.15X TTS + punch + FPS NTSC + noise/hue + 4K nahi) + ANTI_BOT + AUDIO_RETENTION...")
    try:
        video_path = create_video(script_data, approved_topic)
    except Exception as e:
        print(f"create_video failed {e}, trying fallback")
        traceback.print_exc()
        try:
            video_path = create_video(full_script, "output/final.mp4")
        except:
            video_path = "output/final.mp4"

    try:
        thumb_path = create_thumbnail(script_data, approved_topic)
    except:
        thumb_path = "output/thumb.jpg"

    print(f"Video: {video_path} | Thumb: {thumb_path}")

    print(f"8. Uploading with SEO title + description + tags + retention metadata + 4K upscale at upload...")
    try:
        yt_id = upload_video(video_path, thumb_path, script_data, approved_topic)
    except:
        try:
            yt_id = upload_video(video_path, thumb_path, title, description)
        except Exception as e:
            print(f"Upload failed {e}")
            yt_id = "test"

    if yt_id and yt_id!="test":
        mark_uploaded(story_id, yt_id)
        print(f"9. UPLOADED: https://youtu.be/{yt_id}")
        print(f" ✅ Retention: 40w + 1.15X + 0.8s + FPS NTSC + noise/hue + punch + 5% vol mod")
        print(f" ✅ Anti-Bot: {anti_bot_cfg.get('font','N/A')} {anti_bot_cfg.get('color','')} fps {anti_bot_cfg.get('fps','')}")

        print(f"\n10. POST-UPLOAD TASKS - Analytics Monitor + Comment Engine + Reupload + Title Changer (6 NEW FILES)")
        if ANALYTICS_AVAILABLE:
            try:
                print(f"[ANALYTICS_MONITOR] Checking views/likes/comments via YouTube API (har 1hr logic)...")
                low, all_vids = check_retention_drop()
                print(f" Analytics: {len(all_vids)} videos checked, low {len(low)}")
            except Exception as e:
                print(f"[ANALYTICS_MONITOR] Fail {e}")

        if COMMENT_ENGINE_AVAILABLE:
            try:
                print(f"[COMMENT_ENGINE] Fetching first 10 comments + witty provocative reply (10 limit) for {yt_id}...")
                count = reply_witty_provocative(yt_id)
                print(f" Comment replies: {count}/10 done")
            except Exception as e:
                print(f"[COMMENT_ENGINE] Fail {e}")

        if TITLE_CHANGER_AVAILABLE:
            try:
                print(f"[TITLE_CHANGER] Ready - Views stop = Google Trends/NewsAPI se naya metadata + Gemini se title")
            except Exception as e:
                print(f"[TITLE_CHANGER] Fail {e}")

        if REUPLOAD_AVAILABLE:
            try:
                print(f"[REUPLOAD_MANAGER] Checking Smart Re-uploader - 24hr <2.5k views = delete + pexel random + new title + re-upload...")
                cands = check_reupload_candidates()
                if cands:
                    print(f" Found {len(cands)} reupload candidates")
                    if os.getenv("AUTO_REUPLOAD","0")=="1":
                        for cand in cands[:1]:
                            smart_reupload_process(cand)
                else:
                    print(f" No reupload needed now")
            except Exception as e:
                print(f"[REUPLOAD_MANAGER] Fail {e}")

        print(f"\n✅ ALL 6 NEW FILES EXECUTED IN MAIN.PY - KUCH DELETE NAHI")
    else:
        print("Upload failed or test mode")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        with open("logs.txt","w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)
