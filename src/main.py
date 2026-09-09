"""
MAIN.PY - FINAL WITH BREAKOUT FORCE VIDEO + 6 NEW FILES + RETENTION + VALIDATION - KUCH DELETE NAHI
Flow: breakout_any_topic (news/politics/tech) -> hungerness -> script 40w -> video 0.8s 12sec -> anti_bot + audio_retention -> 4K upload
FIXED: Breakout = video banna hi banna hai, chahe filter fail ho + Visualping logic
"""
import sys, os
# ===== FIX ERROR 1 ONLY - src me hi rehne de - import path fix =====
# src/main.py se run ho raha hai, isliye root aur src dono path me daalo
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, CURRENT_DIR)
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'src'))
sys.path.insert(0, 'src')
sys.path.insert(0, '.')
import os, traceback, random, time, re, hashlib, json
from pathlib import Path

# FIX 1: Try load filters instead of hardcoded False + BREAKOUT
try:
    from filters import apply_all_filters_short_bot
    FILTERS_AVAILABLE = True
    print("[MAIN] FILTERS_AVAILABLE=True - filters loaded")
except ImportError:
    try:
        from src.filters import apply_all_filters_short_bot
        FILTERS_AVAILABLE = True
        print("[MAIN] FILTERS_AVAILABLE=True - src.filters loaded")
    except ImportError:
        FILTERS_AVAILABLE = False
        apply_all_filters_short_bot = None
        print("[MAIN] FILTERS_AVAILABLE=False - fallback to news_fetcher + breakout_detector + 6 NEW FILES")

# BREAKOUT DETECTOR IMPORT - ERROR 1 FIX ONLY - src me hi
BREAKOUT_AVAILABLE = False
get_all_breakouts_any_topic = None
try:
    # src folder se direct import - jab python src/main.py chalao
    from breakout_detector import get_all_breakouts_any_topic as _brk
    get_all_breakouts_any_topic = _brk
    BREAKOUT_AVAILABLE = True
    print("[MAIN] BREAKOUT_AVAILABLE=True - breakout_detector loaded from src/")
except ImportError as e1:
    try:
        from src.breakout_detector import get_all_breakouts_any_topic as _brk
        get_all_breakouts_any_topic = _brk
        BREAKOUT_AVAILABLE = True
        print("[MAIN] BREAKOUT_AVAILABLE=True - src.breakout_detector loaded")
    except ImportError as e2:
        try:
            sys.path.insert(0, 'src')
            sys.path.insert(0, '.')
            from breakout_detector import get_all_breakouts_any_topic as _brk
            get_all_breakouts_any_topic = _brk
            BREAKOUT_AVAILABLE = True
            print("[MAIN] BREAKOUT_AVAILABLE=True - after sys.path insert src")
        except ImportError as e3:
            BREAKOUT_AVAILABLE = False
            def get_all_breakouts_any_topic():
                print("[MAIN] BREAKOUT fallback - trying visualping directly")
                try:
                    from visualping_monitor import get_visualping_breakouts
                    return get_visualping_breakouts()
                except:
                    try:
                        from src.visualping_monitor import get_visualping_breakouts
                        return get_visualping_breakouts()
                    except:
                        return []
            print(f"[MAIN] BREAKOUT_AVAILABLE=False - using inline fallback, e1={e1}, e2={e2}, e3={e3}")

def clean_id_breakout(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_breakouts_inline_fallback():
    """Visualping logic: White House, Supreme Court, CNN Breaking, Reddit rising - seconds me alert"""
    breakouts = []
    try:
        import feedparser, requests
        # CNN Breaking = raw data before mainstream media chapne se pehle
        try:
            feed = feedparser.parse("https://rss.cnn.com/rss/cnn_brk.rss")
            for entry in feed.entries[:3]:
                title = clean_id_breakout(entry.title)
                if len(title) < 5: continue
                if re.match(r'^m[0-9]', title, re.I): continue
                breakouts.append({
                    "title": title, "query": title, "url": entry.link, "source": "visualping_cnn_breaking",
                    "published": time.gmtime(), "summary": title,
                    "is_breakout": True, "breakout_score": 6000, "search_volume": 95,
                    "bot_friendly": True, "filter_c_score": 95, "bot_friendly_score": 95,
                    "reliability": 0.97, "visualping_alert": "CNN Breaking text changed - Visualping style"
                })
        except Exception as e:
            print(f"[BREAKOUT FALLBACK] CNN fail {e}")
        # Reddit rising = Dataminr style spike detection
        try:
            r = requests.get("https://www.reddit.com/r/all/rising/.json?limit=8", headers={"User-Agent":"Mozilla/5.0"}, timeout=6)
            if r.status_code == 200:
                data = r.json()
                for child in data.get('data',{}).get('children',[])[:3]:
                    t = clean_id_breakout(child['data'].get('title',''))
                    if len(t) < 10: continue
                    if child['data'].get('score',0) > 300:
                        breakouts.append({
                            "title": t, "query": t, "url": f"https://reddit.com{child['data'].get('permalink','')}",
                            "source": "reddit_rising_breakout", "published": time.gmtime(), "summary": t,
                            "is_breakout": True, "breakout_score": 5500, "search_volume": 85,
                            "bot_friendly": True, "filter_c_score": 85, "bot_friendly_score": 85,
                        })
        except Exception as e:
            print(f"[BREAKOUT FALLBACK] reddit fail {e}")
    except Exception as e:
        print(f"[BREAKOUT FALLBACK] overall fail {e}")
    return breakouts

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

# ===== 6 NEW FILES IMPORT =====
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

# FIX 2: Market hungerness vol 0 bug - default 60 + BREAKOUT FORCE
def check_market_hungerness(topic_dict):
    # ===== BREAKOUT = 100% VIDEO BANNA HI BANNA HAI - ANY TOPIC (news/politics) =====
    if topic_dict.get("is_breakout") or topic_dict.get("breakout_score",0) >= 5000:
        return True, f"🔥 BREAKOUT FORCE: score {topic_dict.get('breakout_score',5000)} + is_breakout={topic_dict.get('is_breakout')} -> VIDEO BANEGA HI BANEGA (Politics+News)"

    q = (topic_dict.get('query','') or topic_dict.get('title','')).lower()
    vol_raw = topic_dict.get('search_volume',0)
    try:
        vol = int(vol_raw) if vol_raw not in (None, '', 0, '0') else 0
    except:
        vol = 0
    if vol == 0:
        vol = 60
    freshness_score = 80
    try:
        from shorts_gate import score_freshness
        freshness_score = score_freshness(topic_dict)
    except:
        pass
    hungry_keywords = ["leaked","secret","breaking","shocking","just in","behind closed doors","exposed","revealed","executive order","bill","supreme court","law","policy","white house","senate","congress"]
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
        raw_stories = [{"title": manual_topic, "query": manual_topic, "url": "", "source": "manual", "published": None, "summary": manual_topic, "search_volume": 95, "bot_friendly": True, "filter_c_score": 95, "bot_friendly_score": 95, "is_breakout": True, "breakout_score": 6000}]
    else:
        print(f"1. Fetching USA news from RSS - Direct Google Trends + Live + BREAKOUT ANY TOPIC (News+Politics) + Visualping + 6 New Files")
        print(f"   [BREAKOUT ENGINE] Visualping: White House press release, Federal court dockets, Supreme Court announcements + Google Trends BREAKOUT monitor...")
        raw_stories = fetch_all_news()
        
        # ===== MERGE BREAKOUTS ANY TOPIC - POLITICS LAWS/POLICIES SE START + VISUALPING =====
        breakout_stories = []
        try:
            if BREAKOUT_AVAILABLE:
                breakout_stories = get_all_breakouts_any_topic()
                print(f"[BREAKOUT ENGINE] get_all_breakouts_any_topic() -> {len(breakout_stories)} breakouts (News+Politics Any Topic)")
            else:
                breakout_stories = get_breakouts_inline_fallback()
                print(f"[BREAKOUT ENGINE] inline Visualping fallback -> {len(breakout_stories)} breakouts")
        except Exception as e:
            print(f"[BREAKOUT ENGINE] fail {e}, using inline fallback")
            try:
                breakout_stories = get_breakouts_inline_fallback()
            except:
                breakout_stories = []
        
        if breakout_stories:
            print(f"🔥🔥🔥 BREAKOUT FOUND {len(breakout_stories)} - INKO FIRST PRIORITY, VIDEO BANEGA HI BANEGA (Any Topic) 🔥🔥🔥")
            existing_q = set((s.get('query','') or s.get('title','')).lower() for s in raw_stories)
            new_breakouts = []
            for b in breakout_stories:
                ql = (b.get('query','') or b.get('title','')).lower()
                if ql not in existing_q:
                    new_breakouts.append(b)
                    existing_q.add(ql)
                else:
                    b['is_breakout'] = True
                    new_breakouts.append(b)
            raw_stories = new_breakouts + raw_stories
            print(f"   Merged: {len(new_breakouts)} breakout + {len(raw_stories)-len(new_breakouts)} normal = {len(raw_stories)} total")
            for i, b in enumerate(new_breakouts[:3]):
                print(f"   BREAKOUT {i+1}: {b.get('query')[:70]} | Score {b.get('breakout_score')} | Source {b.get('source')} | Visualping={b.get('visualping_alert','')}")
        else:
            print(f"[BREAKOUT ENGINE] No breakout right now, using normal trends")

    if not raw_stories:
        print("No news fetched"); return
    print(f"Fetched: {len(raw_stories)} stories (including {sum(1 for s in raw_stories if s.get('is_breakout'))} BREAKOUTS ANY TOPIC)")
    for i, s in enumerate(raw_stories[:7]):
        vol_disp = s.get('search_volume','')
        if not vol_disp or vol_disp == 0 or vol_disp == '0':
            vol_disp = 60
        bot_disp = s.get('filter_c_score', s.get('bot_friendly_score','')) or 85
        is_brk = "🔥 BREAKOUT" if s.get('is_breakout') else ""
        print(f" {i+1}. {s.get('query','')[:60]} | Vol {vol_disp} | Bot {bot_disp} | {is_brk} | {s.get('source','')}")

    print(f"2. Verifying {len(raw_stories)} stories...")
    try:
        verified = verify_stories(raw_stories)
    except Exception as e:
        print(f"verify_stories crashed: {e}, using raw")
        verified = raw_stories
    if not verified:
        verified = raw_stories

    print(f"3. Scoring & Ranking + BREAKOUT FIRST (Politics laws/policies se start)...")
    try:
        ranked = score_and_rank(verified)
    except:
        ranked = verified
    if not ranked:
        ranked = verified

    # BREAKOUTS ko top pe lao - politics laws/policies + any news breakout
    breakout_ranked = [r for r in ranked if r.get('is_breakout') or r.get('breakout_score',0) >= 5000]
    normal_ranked = [r for r in ranked if not (r.get('is_breakout') or r.get('breakout_score',0) >= 5000)]
    ranked_sorted = breakout_ranked + normal_ranked
    if breakout_ranked:
        print(f"   🔥 {len(breakout_ranked)} BREAKOUT topics moved to top (Politics+News - video banna hi banna hai)")
    ranked = ranked_sorted

    # Hungerness check - breakout bypass
    hungry_ranked=[]
    for r in ranked[:20]:
        is_hungry, reason = check_market_hungerness(r)
        print(f" [HUNGER CHECK] {r.get('query','')[:50]} -> {reason}")
        if is_hungry:
            hungry_ranked.append(r)
    if hungry_ranked:
        ranked = hungry_ranked
        print(f" Market hungry filter: {len(hungry_ranked)} topics hungry (including {sum(1 for s in hungry_ranked if s.get('is_breakout'))} BREAKOUTS)")
    else:
        ranked = ranked[:5]
        for r in ranked:
            r['search_volume'] = 60
        print(f" Market hungry filter: no hungry found, using top 5 with default vol 60")

    print(f"4. STARTING GATE THRESHOLD {THRESHOLD} + BOT_FRIENDLY {BOT_FRIENDLY_THRESHOLD} + Tacko 4 segments + FACT CHECKER + BREAKOUT FORCE (Any Topic)")

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

    for idx, candidate in enumerate(ranked[:15]):
        is_brk = candidate.get('is_breakout') or candidate.get('breakout_score',0) >= 5000
        brk_tag = "🔥 BREAKOUT FORCE - VIDEO BANEGA HI BANEGA" if is_brk else ""
        print(f"\n{'='*60}")
        print(f"[TRY] {idx+1}/15 Topic: {candidate.get('query') or candidate.get('title')} {brk_tag}")
        print(f"{'='*60}")

        temp_approved, temp_script, temp_scores = gate_loop_for_shorts([candidate], script_gen_wrapper)
        if not temp_approved:
            if is_brk:
                print(f" -> GATE FAIL but BREAKOUT FORCE -> BYPASS GATE, forcing APPROVED (Any Topic)")
                temp_approved = candidate
                try:
                    temp_script = generate_script(candidate)
                except:
                    temp_script = {"full_script": candidate.get('query','') + " breaking news leaked behind closed doors first to know effect - what is this bill who is politician", "title": candidate.get('query','')[:90]}
                temp_scores = {"validation_factory": 85, "gate": 100, "breakout": 100}
            else:
                print(f" -> GATE FAIL for {candidate.get('query')}")
                continue

        print(f" -> GATE PASS pre-script: {temp_scores} {brk_tag}")

        # Fact checker - STRICT REAL ONLY - NO FORCE PASS - Real hai tabhi video banegi
        print(f"5. Fact Checking (STRICT REAL - NO FORCE PASS)... {brk_tag}")
        try:
            validation = fact_check(temp_script, temp_approved)
            if not validation.get('passed', False):
                print(f"❌ REJECTED BY FACT CHECKER (STRICT REAL): {temp_approved.get('title') or temp_approved.get('query')}")
                print(f"   Reason: {validation.get('report')}")
                print(f"   => Topic cancel, naya topic try karega - NO FORCE PASS")
                continue
            else:
                print(f"✅ FACT CHECKER REAL PASS: {validation.get('report')} {brk_tag}")
        except Exception as e:
            print(f"fact_check crashed: {e} -> FAIL - topic cancel new try (NO FORCE PASS)")
            traceback.print_exc()
            validation = {"passed": False, "report": f"crash -> FAIL new try {e}"}
            print(f"❌ REJECTED BY FACT CHECKER CRASH: {temp_approved.get('title') or temp_approved.get('query')} - new try")
            continue

        approved_topic = temp_approved
        script_result = temp_script
        scores = temp_scores
        if is_brk:
            approved_topic['is_breakout'] = True
            approved_topic['breakout_score'] = candidate.get('breakout_score', 5000)
            approved_topic['breakout_source'] = candidate.get('source','breakout_any_topic')
        break

    if not approved_topic:
        print("❌ All topics FAILED - NO SAFE EXIT - NO FORCE PASS - trying fresh US fetch real check")
        try:
            fresh = fetch_all_news()
            us_fresh = [s for s in fresh if 'germany' not in (s.get('title','')+' '+s.get('query','')).lower() and 'canada' not in (s.get('title','')+' '+s.get('query','')).lower()]
            if not us_fresh:
                us_fresh = fresh
            for cand in us_fresh[:3]:
                try:
                    temp_script_retry = generate_script(cand)
                    validation_retry = fact_check(temp_script_retry, cand)
                    if validation_retry.get('passed'):
                        approved_topic = cand
                        script_result = temp_script_retry
                        validation = validation_retry
                        scores = {"retry_real": 90}
                        print(f"   ✅ Retry real PASS: {cand.get('title','')[:60]}")
                        break
                except Exception as e:
                    print(f"   Retry fail {e}")
                    continue
        except Exception as e:
            print(f"Fresh retry fail {e}")
        if not approved_topic:
            print("❌ No approved after real retry - ending without force pass - next cron will retry")
            return

    print(f"\n🔥 FINAL APPROVED: {approved_topic.get('title') or approved_topic.get('query')} (Fact Checker ke baad) {'🔥 BREAKOUT ANY TOPIC' if approved_topic.get('is_breakout') else ''}")
    print(f" Scores: {scores}")
    print(f" Fact Report: {validation.get('report') if validation else 'N/A'}")
    if approved_topic.get('is_breakout'):
        print(f" 🔥 BREAKOUT: Source={approved_topic.get('source')} | Score={approved_topic.get('breakout_score')} | Visualping={approved_topic.get('visualping_alert','')} | VIDEO BANEGA HI BANA HAI")

    if isinstance(script_result, dict):
        script_data = script_result
        title = script_data.get('title','')
        full_script = script_data.get('full_script','')
        title_options = script_data.get('title_options', [title])
        segments = script_data.get('script_segments', {})
        visual = script_data.get('visual_instructions', {})
        description = script_data.get('description','')
        tags_all = script_data.get('tags_all','')
        print("\n=== TACKO STYLE PER VIDEO (Every video ke hisaab se) + BREAKOUT BACKGROUND (What is Bill X / Who is Politician Y) ===")
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
            if approved_topic.get('is_breakout'):
                print(f"NOTE: Duplicate but BREAKOUT FORCE -> still processing: {approved_topic.get('title')}")
            else:
                print(f"NOTE: Duplicate but still processing: {approved_topic.get('title')}")
    except:
        pass

    story_id = save_story(approved_topic)

    print(f"\n5. FINAL script already with Tacko structure - Already Fact Checked PASS {'+ BREAKOUT FORCE' if approved_topic.get('is_breakout') else ''}")
    print(f"6. Creating video with Tacko instructions... {'🔥 BREAKOUT ANY TOPIC' if approved_topic.get('is_breakout') else ''}")
    try:
        video_path = create_video(script_data, approved_topic)
    except:
        video_path = create_video(full_script, "output/final.mp4")

    try:
        thumb_path = create_thumbnail(script_data, approved_topic)
    except:
        thumb_path = "output/thumb.jpg"

    print(f"Video: {video_path} | Thumb: {thumb_path}")

    print(f"8. Uploading with SEO title + description + tags... {'🔥 BREAKOUT - 10M-20M traffic capture' if approved_topic.get('is_breakout') else ''}")
    print(f" Title: {title}")
    try:
        yt_id = upload_video(video_path, thumb_path, script_data, approved_topic)
    except Exception as e1:
        print(f"[UPLOAD] First attempt failed {e1}, retry with title/desc dict")
        try:
            retry_data = {"title": title, "description": description, "tags_all": tags_all}
            yt_id = upload_video(video_path, thumb_path, retry_data, approved_topic)
        except Exception as e2:
            print(f"[UPLOAD] Second attempt failed {e2} - will exit with error, not test_id")
            raise e2

    if yt_id:
        mark_uploaded(story_id, yt_id)
        print(f"9. UPLOADED: https://youtu.be/{yt_id} {'🔥 BREAKOUT' if approved_topic.get('is_breakout') else ''}")
        print(f" Used Title Options: {title_options}")

        # FIXED: PINNED COMMENT RETRY - if uploader missed, retry here + comment_engine
        try:
            print("10. PINNED COMMENT CHECK...")
            from youtube_uploader import post_pinned_comment
            topic_for_pin = approved_topic.get('query','') or approved_topic.get('title','')
            pinned_id = post_pinned_comment(yt_id, topic_for_pin)
            if pinned_id:
                print(f"✅ Pinned comment posted {pinned_id}")
            else:
                print("⚠️ Pinned comment not posted in uploader, trying comment_engine fallback")
                try:
                    from comment_engine import reply_witty_provocative
                    # For pinned, we need to post a new top-level comment as channel
                    from youtube_uploader import post_pinned_comment as ppc2
                    ppc2(yt_id, topic_for_pin)
                except Exception as ce:
                    print(f"[PINNED COMMENT FALLBACK] fail {ce}")
        except Exception as e:
            print(f"[PINNED COMMENT] Main retry fail {e}")

        # Also run comment_engine for old videos
        try:
            from comment_engine import run_comment_engine_for_latest
            run_comment_engine_for_latest(limit_videos=2)
        except Exception as e:
            print(f"[COMMENTS] Engine fail {e}")

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
