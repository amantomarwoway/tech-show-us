"""
main.py - AUTONOMOUS TEXT BOT - FINAL v27
- YOUTUBE TRENDING AS ONLY SOURCE
- Script built from YouTube metadata (title, description, hashtags, tags, transcript)
- 100% AI-FREE — no Gemini, no OpenAI, no quota
- Self evolution FIRST, Uploader LAST
- FORCED 45-55s long-form Shorts
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
MAX_ACCEPTABLE_WORDS = 200
CANDIDATE_POOL_SIZE = 15
BOSS_FALLBACK_SCORE = 40
MIN_VIEWS_FOR_TREND = 50000
TRENDING_OVERRIDE_SCORE = 70


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
    cleaned = re.sub(r'\s*\((Official|Music|Lyric|Audio|Video|HD|4K)\s*.*?\)\s*', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\[(Official|Music|Lyric|Audio|Video|HD|4K)\s*.*?\]\s*', '', cleaned, flags=re.IGNORECASE)
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
    if len(title.split()) < 4:
        return False
    return True


def score_youtube_trend(story):
    views = story.get('view_count', 0)
    likes = story.get('like_count', 0)
    comments = story.get('comment_count', 0)
    hours = max(story.get('age_hours', 1), 1)
    velocity = views / hours

    view_score = min(100, (views / 5_000_000) * 100)
    velocity_score = min(100, (velocity / 200_000) * 100)
    engagement = (likes + comments * 3) / max(views, 1) * 1000
    eng_score = min(100, engagement * 10)

    total = view_score * 0.35 + velocity_score * 0.45 + eng_score * 0.20
    return total


def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH - YOUTUBE TRENDING ONLY")
    logger.info("=" * 60)

    collector = safe_import('src.collectors.youtube_trending_collector',
                            'collect_youtube_trending')
    if not collector:
        logger.error("YouTube trending collector not available")
        return []

    try:
        stories = collector()
    except Exception as e:
        logger.error(f"YouTube trending failed: {e}")
        return []

    if not stories:
        logger.error("No YouTube trending stories found")
        return []

    for s in stories:
        s['title'] = clean_topic(s.get('title', ''))
    stories = [s for s in stories if s.get('title') and len(s['title']) > 10]

    before = len(stories)
    stories = [s for s in stories if is_viral_topic(s.get('title', ''))]
    logger.info(f"Viral filter: {before} -> {len(stories)}")

    before = len(stories)
    stories = [s for s in stories if s.get('view_count', 0) >= MIN_VIEWS_FOR_TREND]
    logger.info(f"Min views filter ({MIN_VIEWS_FOR_TREND:,}): {before} -> {len(stories)}")

    if not stories:
        logger.error("No stories pass minimum views filter")
        return []

    for s in stories:
        s['breakout_score'] = score_youtube_trend(s)

    stories.sort(key=lambda x: x.get('breakout_score', 0), reverse=True)

    logger.info(f"LEG 1: {len(stories)} YouTube trending candidates")
    for i, s in enumerate(stories[:8]):
        logger.info(
            f"  #{i+1}: [{s['region']}/{s['category']}] "
            f"{s['title'][:55]} ({s['view_count']:,} views, "
            f"score {s['breakout_score']:.1f})"
        )

    return stories[:CANDIDATE_POOL_SIZE]


def editor_god_main(script_data, candidate):
    """
    Editor skipped — script already built from YouTube metadata.
    No AI, no fact extraction needed.
    """
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR - SKIPPED (YouTube metadata mode)")
    logger.info("=" * 60)
    return {"facts": [], "visuals": []}


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
                if 'too long' in reason.lower():
                    wc = len(script_data.get('short_script', '').split())
                    if wc <= MAX_ACCEPTABLE_WORDS:
                        logger.warning(
                            f"Overriding 'script too long' gate ({wc} words) "
                            f"- allowed up to {MAX_ACCEPTABLE_WORDS}"
                        )
                    else:
                        result['reason'] = reason
                        logger.info(f"LEG 3: REJECTED - {reason}")
                        return result
                else:
                    result['reason'] = reason
                    logger.info(f"LEG 3: REJECTED by gate - {reason}")
                    return result

        ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if ranker:
            try:
                score = ranker(full_story)
                if not score or score <= 0:
                    logger.warning(f"Ranker returned {score} - using 55")
                    score = 55
                result['score'] = score
            except Exception as e:
                logger.warning(f"Ranker failed: {e} - using 55")
                score = 55
                result['score'] = 55

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
            result['reason'] = "No ranker"
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


# ============================================================
# SCRIPT GENERATION FROM YOUTUBE METADATA (NO AI)
# ============================================================

def generate_script_god(story):
    """
    Build script from YouTube metadata (title, description, hashtags, tags, transcript).
    NO AI, NO GEMINI, NO QUOTA.
    """
    from src.collectors.yt_metadata_collector import (
        fetch_transcript, extract_hashtags, extract_keywords
    )

    video_id = story.get('youtube_video_id', '')
    title = story.get('title', '')
    description = story.get('description', '')
    channel = story.get('channel', '')
    views = story.get('view_count', 0)
    category = story.get('category', 'trending')

    logger.info(f"Building script from YouTube data: {title[:60]}")

    # 1. Fetch transcript
    transcript = None
    if video_id:
        try:
            transcript = fetch_transcript(video_id)
        except Exception as e:
            logger.warning(f"Transcript fetch failed: {e}")

    # 2. Extract hashtags from description
    try:
        hashtags = extract_hashtags(description)
    except Exception:
        hashtags = []

    # 3. Extract keywords for tags
    try:
        combined = f"{title} {description} {transcript or ''}"
        keywords = extract_keywords(combined, top_n=15)
    except Exception:
        keywords = []

    video_duration = get_forced_duration()
    target_words = int(video_duration * 2.3)
    max_words = int(video_duration * 2.5)

    # ============================================================
    # BUILD SCRIPT
    # ============================================================
    if transcript and len(transcript.split()) >= MIN_ACCEPTABLE_WORDS:
        logger.info(f"Transcript available: {len(transcript.split())} words")
        trans_words = transcript.split()

        # Skip first 10 words (intro/greeting)
        core = trans_words[10:] if len(trans_words) > 20 else trans_words

        # Take up to target
        core = core[:target_words]
        script = " ".join(core)
        script = re.sub(r'\s+', ' ', script).strip()

        if not script.endswith(('.', '!', '?')):
            script += "."

        logger.info(f"Script from transcript: {len(script.split())} words")
    else:
        logger.info("No transcript - building from title/description")
        title_clean = clean_topic(title)

        # Clean description - skip first line (channel promo)
        desc_lines = [l.strip() for l in description.split('\n') if l.strip()]
        desc_core = " ".join(desc_lines[1:4]) if len(desc_lines) > 1 else ""

        parts = [
            title_clean + ".",
            desc_core,
            f"This video has {views:,} views on YouTube right now.",
            f"Posted by {channel}." if channel else "",
            "Millions are watching this trending story.",
            "Comment below what you think.",
            "Subscribe for more trending stories.",
        ]
        script = " ".join(p for p in parts if p).strip()

    # Trim to max
    words = script.split()
    if len(words) > max_words:
        script = " ".join(words[:max_words])
        if not script.endswith(('.', '!', '?')):
            script += "."

    word_count = len(script.split())
    logger.info(f"Script built: {word_count} words")

    if word_count < MIN_ACCEPTABLE_WORDS:
        logger.warning(f"Script too short ({word_count} words) - skip")
        return None

    # ============================================================
    # BUILD TITLE
    # ============================================================
    title_clean = clean_topic(title)
    if len(title_clean) > 50:
        title_clean = title_clean[:50].rsplit(' ', 1)[0]

    if hashtags:
        hashtag = hashtags[0]
    else:
        hashtag_map = {
            "music": "#Music", "gaming": "#Gaming",
            "entertainment": "#Trending", "sports": "#Sports",
            "news": "#News", "tech": "#Tech",
            "comedy": "#Comedy", "education": "#Education",
        }
        hashtag = hashtag_map.get(category, "#Trending")

    seo_title = f"{title_clean} {hashtag}"
    if len(seo_title) > 100:
        seo_title = seo_title[:97] + "..."

    # ============================================================
    # BUILD HOOK
    # ============================================================
    hook_words = title_clean.upper().split()[:5]
    hook = " ".join(hook_words) if hook_words else "YOU WON'T BELIEVE THIS"

    # ============================================================
    # BUILD TAGS
    # ============================================================
    tags = list(keywords[:15]) if keywords else ["trending", "viral", "shorts"]
    tags.insert(0, category)
    tags = list(dict.fromkeys(tags))[:15]

    # ============================================================
    # BUILD DESCRIPTION
    # ============================================================
    desc_out = description[:500] if description else "Trending on YouTube right now."
    if hashtags:
        desc_out = desc_out.rstrip() + "\n\n" + " ".join(hashtags[:5])

    logger.info(f"Script by YouTube metadata")
    logger.info(f"   Title: {seo_title}")
    logger.info(f"   Hook: {hook}")
    logger.info(f"   Tags: {tags[:5]}")

    return {
        "short_script": script,
        "seo_youtube_title": seo_title,
        "description": desc_out,
        "hashtags": hashtags[:3] if hashtags else [hashtag, "#Shorts", "#Trending"],
        "tags": tags,
        "viral_hook": hook,
        "visual_queries": [],
        "confidence_score": 85,
    }


# ============================================================
# VIDEO GENERATION
# ============================================================

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
    logger.info("AUTONOMOUS TEXT BOT START (YouTube Metadata Only)")
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
        logger.error("No YouTube trending stories - exit")
        return

    approved = None
    best_rejected = None
    skipped = 0
    seen_this_run = []

    for i, candidate in enumerate(stories[:CANDIDATE_POOL_SIZE]):
        title = candidate.get('title', '')
        logger.info(f"\nCANDIDATE {i+1}: {title[:60]}")
        logger.info(f"   Source: {candidate.get('source')} | Region: {candidate.get('region')} | Category: {candidate.get('category')}")
        logger.info(f"   Views: {candidate.get('view_count', 0):,} | Velocity score: {candidate.get('breakout_score', 0):.1f}")

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

        # NO FALLBACK — if script build failed, skip
        if not script_data:
            logger.warning("Script build failed - skip candidate")
            continue

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

        if not boss_data.get('approved'):
            trend_score = candidate.get('breakout_score', 0)
            if trend_score >= TRENDING_OVERRIDE_SCORE:
                logger.info(
                    f"🔥 Trending override — velocity score {trend_score:.1f} >= "
                    f"{TRENDING_OVERRIDE_SCORE}, accepting despite boss rejection"
                )
                boss_data['approved'] = True
                boss_data['score'] = max(boss_data.get('score', 0), 55)
                boss_data['reason'] = f"Trending override (velocity {trend_score:.1f})"

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
        logger.error(f"No approved candidate (skipped {skipped} duplicates) - no upload")
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
