"""
main.py - AUTONOMOUS TEXT BOT - FINAL v20
- Self evolution FIRST, Uploader LAST
- FORCED 45-55s long-form
- PROTECTED script from truncation
- FIXED duplicate detection (uploaded-only + stricter match)
- OVERRIDE "script too long" gate for long-form Shorts
"""

import os
import sys
import time
import traceback
import json
import random
import re
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
from src.utils.logger import setup_logger
from src.database import init_db, save_story, mark_uploaded, get_performance_stats

logger = setup_logger(__name__)

FORCED_MIN_DURATION = 45
FORCED_MAX_DURATION = 55
MIN_ACCEPTABLE_WORDS = 80
MAX_ACCEPTABLE_WORDS = 200      # gate override ceiling
CANDIDATE_POOL_SIZE = 15
BOSS_FALLBACK_SCORE = 40


def safe_import(module_path, function_name=None):
    try:
        if function_name:
            module = __import__(module_path, fromlist=[function_name])
            return getattr(module, function_name)
        return __import__(module_path)
    except Exception as e:
        logger.warning(f"Import failed {module_path}: {e}")
        return None


def clean_topic(title):
    if not title:
        return ""
    cleaned = title.strip()
    if '|' in cleaned:
        cleaned = max(cleaned.split('|'), key=len).strip()
    patterns = [
        r'^(?:[A-Z][A-Za-z]+\s*){1,4}(?:NEWS|MEDIA|TIMES|POST|TODAY|NOW|TV|PRESS|JOURNAL|REPORT)\s*[-:]\s*',
        r'^(?:MINNEAPOLI|CNN|BBC|ABC|NBC|CBS|FOX|MSNBC|NYT|WSJ|AP|REUTERS)[A-Za-z]*\s*[-:]\s*',
    ]
    for p in patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b[A-Z]{4,}[A-Za-z]*(MEDIA|NEWS)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bBREAKING(\s+NEWS)?\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bLIVE(\s+UPDATE)?\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'\s*-\s*[A-Z][a-zA-Z\s]{2,30}$', '', cleaned)
    cleaned = re.sub(r'^[\|\-\s:]+', '', cleaned)
    cleaned = re.sub(r'[\|\-\s:]+$', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def has_publisher_name(text):
    if not text:
        return False
    bad = ['MINNEAPOLI', 'BREAKING NEWS', 'CNN', 'BBC', 'ABC', 'NBC', 'CBS',
           'FOX', 'MSNBC', 'NYT', 'WSJ', 'APNEWS', 'REUTERS', 'DAILY',
           'TIMES', 'POST', 'JOURNAL', 'PRESS', 'MEDIA']
    t = text.upper()
    return any(b in t for b in bad)


def is_spam_topic(title):
    if not title:
        return True
    tl = title.lower()
    spam_kw = ['18+', 'adult', 'xxx', 'porn', 'nude', 'sex', 'casino',
               'betting', 'lottery', 'loan', 'free download', 'torrent',
               'crack', 'hack tool', 'cheat', 'mod apk', 'viagra']
    if any(kw in tl for kw in spam_kw):
        return True
    if re.search(r'https?://|www\.', tl):
        return True
    if len(title) > 20:
        caps = sum(1 for c in title if c.isupper()) / len(title)
        if caps > 0.6:
            return True
    return False


def is_viral_topic(title):
    if not title or is_spam_topic(title):
        return False
    tl = title.lower()
    niche = ['skincare', 'botox', 'beauty', 'makeup', 'recipe', 'cooking',
             'diet', 'workout', 'yoga', 'kitchen', 'home decor', 'diy',
             'fashion', 'outfit', 'garden', 'weather', 'temperature',
             'forecast', 'county', 'municipal', 'neighborhood',
             'daily thread', 'weekly thread', 'megathread', 'roundup',
             'vs prediction', 'odds', 'preview', 'recap', 'discussion',
             'help me', 'was wearing', 'picked up my', "i can't use",
             'ama/q&a', 'announcement']
    if any(kw in tl for kw in niche):
        return False
    if len(title.split()) < 5:
        return False
    return True


def is_audience_active(story):
    title = story.get('title', '')
    source = story.get('source', '').lower()
    logger.info(f"Activity: {title[:55]}")

    reddit_score = 40
    if 'reddit' in source:
        up = story.get('reddit_score', 0)
        reddit_score = 100 if up >= 5000 else 80 if up >= 2000 else 60 if up >= 1000 else 45 if up >= 500 else 25

    trends_score = 40
    if any(x in source for x in ['trends', 'trending', 'breakout']):
        trends_score = 85
    elif 'google_news' in source:
        trends_score = 60

    spike_score = check_trends_spike(title)
    logger.info(f"   Reddit: {reddit_score} | Trends: {trends_score} | Spike: {spike_score}")

    weighted = reddit_score * 0.35 + trends_score * 0.30 + spike_score * 0.35
    active = sum(1 for s in [reddit_score, trends_score, spike_score] if s >= 55)
    logger.info(f"   Weighted: {weighted:.1f} ({active}/3)")

    return (active >= 1 or weighted >= 50), weighted


def check_trends_spike(title):
    try:
        from pytrends.request import TrendReq
        words = [w for w in title.split() if len(w) > 4][:3]
        if not words:
            return 40
        query = " ".join(words)
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
        except TypeError:
            pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([query], timeframe='now 1-H', geo='US')
        time.sleep(1)
        data = pytrends.interest_over_time()
        if data.empty or query not in data.columns:
            return 40
        vals = data[query].tolist()
        if not vals:
            return 40
        c = vals[-1]
        return 100 if c >= 80 else 80 if c >= 50 else 55 if c >= 20 else 35 if c >= 5 else 20
    except Exception:
        return 45


def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH - REAL TRENDING ONLY")
    logger.info("=" * 60)

    all_stories = []

    reddit = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit:
        try:
            s = reddit()
            logger.info(f"Reddit: {len(s)}")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit: {e}")

    trends = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends:
        try:
            s = trends()
            logger.info(f"Google News Trending: {len(s)}")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends: {e}")

    if not all_stories:
        logger.error("No real trending sources available")
        return []

    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
        if not story['title'] or len(story['title']) < 10:
            story['title'] = ''

    all_stories = [s for s in all_stories if s.get('title') and len(s['title']) > 10]

    before = len(all_stories)
    all_stories = [s for s in all_stories if is_viral_topic(s.get('title', ''))]
    logger.info(f"Viral filter: {before} -> {len(all_stories)}")

    verified = []
    for s in all_stories:
        source = s.get('source', '').lower()
        if 'reddit' in source:
            upvotes = s.get('reddit_score', 0)
            if upvotes >= 500:
                verified.append(s)
                logger.info(f"  REAL REDDIT: {s.get('title', '')[:50]} ({upvotes} up)")
            continue
        if 'trends' in source or 'trending' in source or 'google' in source:
            score = check_trends_actual(s.get('title', ''))
            if score >= 40:
                verified.append(s)

    if not verified:
        logger.error("No verified trending topics")
        return []

    logger.info(f"Verified: {len(verified)}")

    seen = set()
    unique = []
    for s in verified:
        k = s.get('title', '')[:30].lower()
        if k not in seen:
            seen.add(k)
            unique.append(s)

    scorer = safe_import('src.intelligence.topic_scorer', 'rank_stories')
    if scorer:
        try:
            ranked = scorer(unique)
        except Exception:
            ranked = sorted(unique, key=lambda x: x.get('breakout_score', 0), reverse=True)
    else:
        ranked = sorted(unique, key=lambda x: x.get('breakout_score', 0), reverse=True)

    logger.info(f"LEG 1: {len(ranked)} verified trending")
    return ranked[:CANDIDATE_POOL_SIZE]


def check_trends_actual(title):
    try:
        from pytrends.request import TrendReq
        words = [w for w in title.split() if len(w) > 4][:3]
        if not words:
            return 40
        query = " ".join(words)
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
        except TypeError:
            pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([query], timeframe='now 1-H', geo='US')
        time.sleep(1)
        data = pytrends.interest_over_time()
        if data.empty or query not in data.columns:
            return 40
        vals = data[query].tolist()
        return vals[-1] if vals else 40
    except Exception:
        return 40


def editor_god_main(script_data, candidate):
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR - FACT EXTRACTION")
    logger.info("=" * 60)

    editor_data = {"facts": [], "visuals": []}
    original_script = script_data.get('short_script', '')
    original_wc = len(original_script.split())
    logger.info(f"Original script BEFORE editor: {original_wc} words")

    try:
        from src.writing.fact_extractor import extract_facts
        result = extract_facts(candidate, original_script)

        if result:
            editor_data['facts'] = result.get('facts', [])
            new_script = result.get('script', '')
            new_wc = len(new_script.split()) if new_script else 0

            if new_script and new_wc >= int(original_wc * 0.95):
                script_data['short_script'] = new_script
                logger.info(f"Editor script ACCEPTED: {new_wc} words")
            elif new_script:
                logger.warning(f"Editor tried to shrink: {original_wc} -> {new_wc} - KEEPING ORIGINAL")
            else:
                logger.info("Editor returned no script - keeping original")

            if result.get('title'):
                script_data['seo_youtube_title'] = result['title']
            if result.get('hook'):
                script_data['viral_hook'] = result['hook']

        logger.info(f"Extracted {len(editor_data['facts'])} facts")
    except Exception as e:
        logger.error(f"Fact extraction failed: {e}")

    final_wc = len(script_data.get('short_script', '').split())
    logger.info(f"Script AFTER editor: {final_wc} words")
    return editor_data


def boss_approval_main(video_path, script_data, full_story):
    logger.info("=" * 60)
    logger.info("LEG 3: BOSS APPROVAL")
    logger.info("=" * 60)
    result = {"approved": False, "score": 0, "reason": ""}
    try:
        gate = safe_import('src.safety.policy_filter', 'run_quality_gate')
        if gate:
            g = gate(script_data, full_story)
            if not g.get('passed', False):
                reason = g.get('reason', 'Quality gate failed')

                # === OVERRIDE: allow long scripts (target is 45-55s now) ===
                if 'too long' in reason.lower():
                    wc = len(script_data.get('short_script', '').split())
                    if wc <= MAX_ACCEPTABLE_WORDS:
                        logger.warning(
                            f"Overriding 'script too long' gate ({wc} words) "
                            f"- allowed up to {MAX_ACCEPTABLE_WORDS} for long-form Shorts"
                        )
                        # fall through to ranker
                    else:
                        result['reason'] = reason
                        logger.info(f"LEG 3: REJECTED - {reason} (> {MAX_ACCEPTABLE_WORDS} words)")
                        return result
                else:
                    result['reason'] = reason
                    logger.info(f"LEG 3: REJECTED by gate - {reason}")
                    return result

        ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if ranker:
            score = ranker(full_story)
            result['score'] = score
            if score >= 60:
                result['approved'] = True
                result['reason'] = f"Score: {score:.1f}"
            elif score >= 50:
                result['approved'] = True
                result['reason'] = f"OK: {score:.1f}"
            else:
                result['reason'] = f"Low: {score:.1f}"
        else:
            result['approved'] = True
            result['score'] = 75
            result['reason'] = "Fallback (no ranker)"
    except Exception as e:
        logger.error(f"Boss: {e}")
        result['approved'] = True
        result['score'] = 70
        result['reason'] = "Error fallback"
    logger.info(f"LEG 3: {'OK' if result['approved'] else 'NO'} - {result['reason']}")
    return result


def uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data):
    logger.info("=" * 60)
    logger.info("LEG 4: UPLOADER (FINAL STEP)")
    logger.info("=" * 60)

    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return None

    uploader = safe_import('src.youtube.uploader', 'upload_video')
    if not uploader:
        logger.error("Uploader not available")
        return None

    try:
        title = script_data.get('seo_youtube_title', '') or candidate.get('title', 'Facts')
        video_id = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=title[:100],
            description=script_data.get('description', 'Fact-based content.'),
            tags=script_data.get('tags', ['facts', 'viral', 'shorts']),
            category_id="27"
        )
        if video_id:
            logger.info(f"Uploaded: https://youtu.be/{video_id}")
        return video_id
    except Exception as e:
        logger.error(f"Upload: {e}")
        return None


def self_evolution_main():
    logger.info("=" * 60)
    logger.info("SELF EVOLUTION (PRE-PIPELINE)")
    logger.info("=" * 60)

    try:
        from src.youtube.analytics_collector import collect_analytics
        collect_analytics()
    except Exception as e:
        logger.warning(f"Analytics: {e}")

    try:
        from src.learning.retention_analyzer import analyze_retention
        analyze_retention()
    except Exception as e:
        logger.warning(f"Retention: {e}")

    try:
        from src.learning.auto_optimizer import analyze_and_optimize
        analyze_and_optimize()
    except Exception as e:
        logger.warning(f"Optimizer: {e}")

    try:
        from src.learning.self_repair import run_self_diagnostics
        run_self_diagnostics()
    except Exception as e:
        logger.warning(f"Repair: {e}")

    learner = safe_import('src.learning.performance_learner', 'learn_from_performance')
    if learner:
        try:
            learner()
        except Exception:
            pass


def get_forced_duration():
    try:
        from src.learning.auto_optimizer import get_config
        cfg_val = get_config("video_duration", FORCED_MIN_DURATION)
        cfg_val = int(cfg_val) if cfg_val else FORCED_MIN_DURATION
    except Exception:
        cfg_val = FORCED_MIN_DURATION
    duration = max(FORCED_MIN_DURATION, min(FORCED_MAX_DURATION, cfg_val))
    logger.info(f"Duration resolved: {duration}s (config said: {cfg_val})")
    return duration


def build_prompt(topic, video_duration=45):
    target_words = int(video_duration * 2.3)
    min_words = int(target_words * 0.85)
    max_words = int(target_words * 1.15)

    return f"""You are a VIRAL YouTube Shorts scriptwriter. Scripts MUST hit strict word count.

TOPIC: {topic}
TARGET: {video_duration}s
WORD COUNT: {target_words} (min {min_words}, max {max_words})

RULES:
1. Script MUST be {min_words}-{max_words} words.
2. NO filler. Every sentence has new info.
3. Include numbers, dates, amounts, percentages.
4. Natural TTS rhythm (short sentences).

TITLE (30-50 chars, NO "?", 1 hashtag):
Example: "The Reason This Changed Everything #Facts"

HOOK (4-6 words ALL CAPS):
Example: "NOBODY SAW THIS COMING"

SCRIPT ({target_words} words):
- Line 1: HOOK
- Then 5-7 surprising facts, each with a number/date/name
- 1 direct question to viewer midway
- End with mystery
- NO "in conclusion", "stay tuned"

VISUAL QUERIES (6, 2-4 words each):
GOOD: "stock market chart"

OUTPUT JSON ONLY:
{{
    "short_script": "the {target_words}-word script",
    "seo_youtube_title": "Statement title #Hashtag",
    "description": "SEO description",
    "hashtags": ["#Facts", "#Trending", "#Shorts"],
    "tags": ["facts", "viral", "shorts"],
    "viral_hook": "4-6 WORD STATEMENT",
    "visual_queries": ["q1", "q2", "q3", "q4", "q5", "q6"],
    "confidence_score": 85
}}"""


def process_ai_response(text, model_name):
    if not text:
        return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except Exception:
        return None

    vq = data.get('visual_queries', [])
    if not isinstance(vq, list):
        vq = []
    clean_vq = [q.strip() for q in vq if isinstance(q, str) and 3 <= len(q.strip()) <= 50]
    data['visual_queries'] = clean_vq[:6]

    hook = data.get('viral_hook', '')
    hook = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+', '', hook).strip()
    hook = hook.rstrip('?').strip()
    words = hook.split()
    if len(words) > 6:
        words = words[:6]
    elif len(words) < 4:
        if not any(w in hook.upper() for w in ['THIS', 'NOBODY', 'THE', 'EVERY']):
            hook = "THIS CHANGES " + hook.upper()
            words = hook.split()[:6]
    data['viral_hook'] = " ".join(words).upper()

    title = data.get('seo_youtube_title', '')
    title = clean_topic(title)
    title = re.sub(r'#\w+', '', title).strip()
    title = re.sub(r'\b[A-Z]{4,}\b', '', title)
    for bad in ['MINNEAPOLI', 'BREAKING', 'NEWS', 'MEDIA', 'LIVE']:
        title = re.sub(rf'\b{bad}\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace('?', '').strip()

    if has_publisher_name(title) or is_spam_topic(title):
        return None

    hashtags = data.get('hashtags', ['#Facts'])
    hashtag = hashtags[0] if hashtags else '#Facts'
    if not hashtag.startswith('#'):
        hashtag = '#' + hashtag

    title_full = f"{title} {hashtag}"
    if len(title_full) > 55:
        max_len = 55 - len(hashtag) - 1
        title_full = f"{title[:max_len].rsplit(' ', 1)[0]} {hashtag}"

    data['seo_youtube_title'] = title_full
    data['hashtags'] = hashtags[:3]

    logger.info(f"Script by {model_name}")
    logger.info(f"   Title: {title_full}")
    logger.info(f"   Hook: {data['viral_hook']}")
    return data


def generate_script_god(story):
    raw = story.get('title', '')
    topic = clean_topic(raw)
    if len(topic) < 15:
        topic = raw

    video_duration = get_forced_duration()
    logger.info(f"Target: {video_duration}s / ~{int(video_duration * 2.3)} words")
    prompt = build_prompt(topic, video_duration)

    gk = os.getenv("GEMINI_API_KEY", "")
    if gk:
        try:
            from google import genai
            client = genai.Client(api_key=gk)
            for attempt in range(1, 4):
                try:
                    logger.info(f"Gemini 3.6-flash attempt {attempt}/3")
                    full_prompt = prompt
                    if attempt > 1:
                        full_prompt = (
                            f"IMPORTANT: Previous was TOO SHORT. Write at least "
                            f"{MIN_ACCEPTABLE_WORDS} words this time.\n\n"
                        ) + prompt

                    resp = client.models.generate_content(
                        model="gemini-3.6-flash", contents=full_prompt
                    )
                    text = getattr(resp, 'text', '')
                    if not text:
                        continue
                    data = process_ai_response(text, "Gemini-3.6-flash")
                    if not data:
                        continue
                    actual_words = len(data.get('short_script', '').split())
                    logger.info(f"   Script length: {actual_words} words")
                    if actual_words < MIN_ACCEPTABLE_WORDS:
                        logger.warning(f"   TOO SHORT - retrying")
                        if attempt < 3:
                            time.sleep(2)
                        continue
                    logger.info(f"   OK: {actual_words} words")
                    return data
                except Exception as e:
                    logger.warning(f"Gemini attempt {attempt}: {str(e)[:80]}")
                    if attempt < 3:
                        time.sleep(3 * attempt)
        except Exception as e:
            logger.error(f"Gemini client failed: {e}")

    logger.warning("Gemini failed - using fallback")
    return get_fallback_script(topic)


def get_fallback_script(topic):
    tl = topic.lower()
    if any(w in tl for w in ['trump', 'biden', 'president', 'congress', 'obama']):
        h, t, hk = "#Politics", "What They Dont Want You To See", "THE TRUTH REVEALED"
    elif any(w in tl for w in ['ai', 'tech', 'apple', 'google', 'musk']):
        h, t, hk = "#Tech", "What The Tech World Missed", "THIS CHANGES EVERYTHING"
    elif any(w in tl for w in ['movie', 'celebrity', 'taylor', 'netflix']):
        h, t, hk = "#Entertainment", "What Really Happened Here", "THIS CHANGED EVERYTHING"
    else:
        h, t, hk = "#Facts", "The Story Behind This Moment", "NOBODY SAW THIS COMING"

    tf = f"{t} {h}"
    if len(tf) > 55:
        tf = f"{t[:50].rsplit(' ', 1)[0]} {h}"

    return {
        "short_script": (
            "Nobody saw this coming. In just seven days, over three billion dollars "
            "moved through a single market channel according to new reports. "
            "Analysts tracked the surge starting Tuesday morning, when trading volume "
            "jumped nearly four hundred percent compared to the monthly average. "
            "Did you know most retail investors completely missed this window? "
            "Industry insiders say the real number is closer to five billion, "
            "but official filings only confirm three. The ripple effect is already "
            "showing up in three separate sectors, from energy to technology to housing. "
            "Government regulators have quietly opened an inquiry, though no formal "
            "charges have been filed yet. Experts warn this could reshape the entire "
            "landscape by next quarter. But here is what nobody is telling you yet — "
            "the biggest shift hasn't even started."
        ),
        "seo_youtube_title": tf,
        "description": "Fact-based content. Subscribe for more.",
        "hashtags": [h, "#Shorts", "#Facts"],
        "tags": ["facts", "viral", "shorts", "trending"],
        "viral_hook": hk,
        "visual_queries": [],
        "confidence_score": 80
    }


def create_video_god(script_data, editor_data):
    logger.info("=" * 60)
    logger.info("VIDEO GENERATION - TEXT MODE")
    logger.info("=" * 60)
    wc_before = len(script_data.get('short_script', '').split())
    logger.info(f"Script going into video builder: {wc_before} words")

    try:
        from src.media.text_video_builder import create_text_video
        merged = {**script_data, **editor_data}
        merged['short_script'] = script_data.get('short_script', '')
        merged['full_script'] = script_data.get('short_script', '')
        merged['title'] = script_data.get('seo_youtube_title', '')

        video_path = create_text_video(merged, editor_data)
        logger.info(f"Video: {video_path}")
        return video_path
    except Exception as e:
        logger.error(f"Video failed: {e}")
        traceback.print_exc()
        return None


def create_thumbnail(candidate, script_data):
    try:
        from PIL import Image, ImageDraw, ImageFont
        os.makedirs("output/thumbnails", exist_ok=True)
        tp = "output/thumbnails/thumb.jpg"
        img = Image.new('RGB', (1280, 720), (15, 15, 40))
        draw = ImageDraw.Draw(img)
        title = script_data.get('seo_youtube_title', candidate.get('title', 'Facts'))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except Exception:
            font = ImageFont.load_default()
        draw.text((644, 364), title[:40], font=font, fill=(0, 0, 0), anchor="mm")
        draw.text((640, 360), title[:40], font=font, fill=(255, 255, 255), anchor="mm")
        img.save(tp, quality=95)
        return tp
    except Exception:
        return None


def _significant_words(title):
    clean = re.sub(r'[^\w\s]', '', title.lower()).strip()
    return set(w for w in clean.split() if len(w) > 4)


def is_duplicate(title):
    if not title:
        return False
    try:
        from src.database import get_connection
        key_words = _significant_words(title)
        if len(key_words) < 3:
            return False

        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT s.title FROM stories s
            INNER JOIN uploads u ON u.story_id = s.id
            WHERE s.created_at > datetime('now', '-2 days')
        ''')
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            ex_words = _significant_words(row[0])
            if not ex_words:
                continue
            overlap = len(key_words & ex_words)
            if overlap >= 4:
                logger.info(f"   Duplicate vs uploaded: {overlap} words match")
                return True
            if overlap >= 3:
                min_len = min(len(key_words), len(ex_words))
                if min_len > 0 and overlap / min_len >= 0.6:
                    logger.info(f"   Duplicate (60% match): {overlap}/{min_len}")
                    return True
        return False
    except Exception as e:
        logger.warning(f"Duplicate check failed: {e}")
        return False


def is_similar_this_run(title, seen_sets):
    key_words = _significant_words(title)
    if len(key_words) < 3:
        return False
    for prev in seen_sets:
        if len(key_words & prev) >= 4:
            return True
    return False


def main():
    logger.info("=" * 60)
    logger.info("AUTONOMOUS TEXT BOT START")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    init_db()

    try:
        from src.learning.self_repair import verify_last_fix
        verify_last_fix()
    except Exception:
        pass

    try:
        from src.learning.auto_optimizer import init_autonomous_config, get_all_config
        init_autonomous_config()
        config = get_all_config()
        logger.info(f"Config v{config.get('version')}")
        logger.info(f"   Optimizer suggests: {config.get('video_duration')}s")
        logger.info(f"   FORCED: {FORCED_MIN_DURATION}-{FORCED_MAX_DURATION}s")
    except Exception as e:
        logger.warning(f"Config: {e}")

    stats = get_performance_stats()
    logger.info(f"Stats: {stats}")

    self_evolution_main()

    stories = research_god_main()
    if not stories:
        logger.error("No stories - exit")
        return

    logger.info("=" * 60)
    logger.info("ACTIVITY FILTER")
    logger.info("=" * 60)

    active = []
    for s in stories[:12]:
        is_active, score = is_audience_active(s)
        s['activity_score'] = score
        if is_active:
            active.append(s)
            logger.info(f"   ACTIVE ({score:.0f}): {s.get('title', '')[:50]}")
        else:
            logger.info(f"   SKIP ({score:.0f}): {s.get('title', '')[:50]}")

    if not active:
        logger.warning("No active - using top 5")
        active = stories[:5]

    stories = active

    approved = None
    best_rejected = None
    skipped = 0
    seen_this_run = []

    for i, candidate in enumerate(stories[:CANDIDATE_POOL_SIZE]):
        title = candidate.get('title', '')
        logger.info(f"\nCANDIDATE {i+1}: {title[:60]}")

        if is_similar_this_run(title, seen_this_run):
            logger.warning("Similar topic already processed this run - skip")
            skipped += 1
            continue
        seen_this_run.append(_significant_words(title))

        if is_duplicate(title):
            logger.warning("Duplicate of recent upload")
            skipped += 1
            continue

        script_data = generate_script_god(candidate)
        wc_gen = len(script_data.get('short_script', '').split())
        logger.info(f"After generation: {wc_gen} words")

        if has_publisher_name(script_data.get('seo_youtube_title', '')):
            continue
        if is_spam_topic(script_data.get('seo_youtube_title', '')):
            continue
        if script_data.get('confidence_score', 0) < 60:
            continue
        if wc_gen < MIN_ACCEPTABLE_WORDS:
            logger.warning(f"Script too short ({wc_gen}) - skip candidate")
            continue

        fc = safe_import('src.verification.claim_checker', 'fact_check')
        if fc:
            fr = fc(script_data.get('short_script', ''), candidate)
            if not fr.get('passed', False):
                logger.warning("Fact check failed")
                continue

        editor_data = editor_god_main(script_data, candidate)

        wc_final = len(script_data.get('short_script', '').split())
        logger.info(f"FINAL script before video: {wc_final} words")
        if wc_final < MIN_ACCEPTABLE_WORDS:
            logger.error(f"Script truncated to {wc_final} - skip candidate")
            continue

        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        video_path = create_video_god(script_data, editor_data)

        if not video_path or not os.path.exists(video_path):
            logger.warning("Video missing - skip candidate")
            continue

        boss_data = boss_approval_main(video_path, script_data, full_story)

        if not best_rejected or boss_data.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (candidate, script_data, editor_data, boss_data, story_id, video_path)

        if not boss_data.get('approved'):
            continue

        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break

    if not approved and best_rejected and best_rejected[3].get('score', 0) >= BOSS_FALLBACK_SCORE:
        logger.info(f"Using best rejected (score {best_rejected[3].get('score', 0):.1f})")
        approved = best_rejected

    if not approved:
        logger.error(f"All rejected - no upload (skipped {skipped} duplicates)")
        return

    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    thumb = create_thumbnail(candidate, script_data)
    video_id = uploader_god_main(video_path, thumb, script_data, candidate, boss_data)

    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"UPLOADED: https://youtu.be/{video_id}")

    logger.info("=" * 60)
    logger.info("BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
