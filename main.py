"""
main.py - AUTONOMOUS TEXT BOT - v29
- YouTube trending only (rising + English)
- Script from FREE AI (Pollinations + Groq)
- Natural length (no force)
- All 23 problems addressed where possible
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

# Natural length — AI decides
MIN_ACCEPTABLE_WORDS = 40
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
    c = title.strip()
    if '|' in c:
        c = max(c.split('|'), key=len).strip()
    for p in [
        r'^(?:[A-Z][A-Za-z]+\s*){1,4}(?:NEWS|MEDIA|TIMES|POST|TODAY|NOW|TV|PRESS|JOURNAL|REPORT)\s*[-:]\s*',
        r'^(?:MINNEAPOLI|CNN|BBC|ABC|NBC|CBS|FOX|MSNBC|NYT|WSJ|AP|REUTERS)[A-Za-z]*\s*[-:]\s*',
    ]:
        c = re.sub(p, '', c, flags=re.IGNORECASE)
    c = re.sub(r'\bBREAKING(\s+NEWS)?\b', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\bLIVE(\s+UPDATE)?\b', '', c, flags=re.IGNORECASE)
    c = re.sub(r'\[.*?\]', '', c)
    c = re.sub(r'\(.*?\)', '', c)
    c = re.sub(r'\s*-\s*[A-Z][a-zA-Z\s]{2,30}$', '', c)
    c = re.sub(r'^[\|\-\s:]+', '', c)
    c = re.sub(r'[\|\-\s:]+$', '', c)
    c = re.sub(r'\s+', ' ', c)
    return c.strip()


def has_publisher_name(text):
    if not text:
        return False
    bad = ['MINNEAPOLI', 'BREAKING NEWS', 'CNN', 'BBC', 'ABC', 'NBC', 'CBS',
           'FOX', 'MSNBC', 'NYT', 'WSJ', 'APNEWS', 'REUTERS']
    t = text.upper()
    return any(b in t for b in bad)


def is_spam_topic(title):
    if not title:
        return True
    tl = title.lower()
    for kw in ['18+', 'adult', 'xxx', 'porn', 'casino', 'betting', 'lottery',
               'loan', 'torrent', 'crack', 'hack tool', 'mod apk', 'viagra']:
        if kw in tl:
            return True
    if re.search(r'https?://|www\.', tl):
        return True
    return False


def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH - YOUTUBE TRENDING (rising)")
    logger.info("=" * 60)

    collector = safe_import('src.collectors.youtube_trending_collector',
                            'collect_youtube_trending')
    if not collector:
        logger.error("Collector missing")
        return []

    try:
        stories = collector()
    except Exception as e:
        logger.error(f"Collector failed: {e}")
        return []

    if not stories:
        return []

    for s in stories:
        s['title'] = clean_topic(s.get('title', ''))
    stories = [s for s in stories if s.get('title') and len(s['title']) > 10]

    # Min views filter (FIXED — logs actual count removed)
    before = len(stories)
    removed = [s for s in stories if s.get('view_count', 0) < MIN_VIEWS_FOR_TREND]
    stories = [s for s in stories if s.get('view_count', 0) >= MIN_VIEWS_FOR_TREND]
    logger.info(f"Min views filter ({MIN_VIEWS_FOR_TREND:,}): {before} -> {len(stories)} (removed {len(removed)})")

    # Sort by rising + velocity
    stories.sort(key=lambda x: x.get('breakout_score', 0), reverse=True)

    logger.info(f"LEG 1: {len(stories)} candidates")
    for i, s in enumerate(stories[:8]):
        logger.info(
            f"  #{i+1}: [{s['region']}/{s['category']}] "
            f"{s['title'][:50]} ({s['view_count']:,}v, "
            f"rising {s.get('rising_score', 0):.0f}, "
            f"score {s.get('breakout_score', 0):.0f})"
        )

    return stories[:CANDIDATE_POOL_SIZE]


def editor_god_main(script_data, candidate):
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR - SKIPPED (AI script mode)")
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
                        logger.warning(f"Override 'too long' ({wc} words)")
                    else:
                        result['reason'] = reason
                        return result
                else:
                    result['reason'] = reason
                    return result

        ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if ranker:
            try:
                score = ranker(full_story)
                if not score or score <= 0:
                    score = 55
                result['score'] = score
            except Exception:
                score = 55
                result['score'] = 55

            if score >= 50:
                result['approved'] = True
                result['reason'] = f"Score: {score:.1f}"
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
    logger.info("LEG 4: UPLOADER")
    logger.info("=" * 60)
    if not os.path.exists(video_path):
        logger.error(f"Missing: {video_path}")
        return None
    uploader = safe_import('src.youtube.uploader', 'upload_video')
    if not uploader:
        return None
    try:
        title = script_data.get('seo_youtube_title', '') or candidate.get('title', 'Trending')
        vid = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=title[:100],
            description=script_data.get('description', ''),
            tags=script_data.get('tags', ['trending', 'viral', 'shorts']),
            category_id="27"
        )
        if vid:
            logger.info(f"Uploaded: https://youtu.be/{vid}")
        return vid
    except Exception as e:
        logger.error(f"Upload: {e}")
        return None


def self_evolution_main():
    logger.info("=" * 60)
    logger.info("SELF EVOLUTION (PRE-PIPELINE)")
    logger.info("=" * 60)
    for mod, fn in [
        ('src.youtube.analytics_collector', 'collect_analytics'),
        ('src.learning.retention_analyzer', 'analyze_retention'),
        ('src.learning.auto_optimizer', 'analyze_and_optimize'),
        ('src.learning.self_repair', 'run_self_diagnostics'),
    ]:
        try:
            m = __import__(mod, fromlist=[fn])
            getattr(m, fn)()
        except Exception as e:
            logger.warning(f"{fn}: {str(e)[:80]}")


def generate_script_god(story):
    from src.collectors.yt_metadata_collector import (
        fetch_transcript, extract_hashtags, generate_script_and_tags
    )

    vid = story.get('youtube_video_id', '')
    title = story.get('title', '')
    desc = story.get('description', '')
    category = story.get('category', 'trending')

    logger.info(f"Generating script for: {title[:60]}")

    transcript = fetch_transcript(vid) if vid else None
    hashtags = extract_hashtags(desc) or []

    if not hashtags:
        hmap = {"music": "#Music", "gaming": "#Gaming", "entertainment": "#Trending",
                "sports": "#Sports", "news": "#News", "tech": "#Tech", "comedy": "#Comedy"}
        hashtags = [hmap.get(category, "#Trending"), "#Shorts", "#Trending"]

    ai = generate_script_and_tags(title, desc, transcript)
    if not ai:
        return None

    script = ai["script"]
    tags = ai["tags"]
    wc = len(script.split())
    logger.info(f"AI script: {wc} words | tags: {tags[:6]}")

    if wc < MIN_ACCEPTABLE_WORDS:
        logger.warning(f"Too short ({wc}) - skip")
        return None

    title_clean = clean_topic(title)
    if len(title_clean) > 50:
        title_clean = title_clean[:50].rsplit(' ', 1)[0]
    seo_title = f"{title_clean} {hashtags[0]}"[:100]

    hook_words = title_clean.upper().split()[:5]
    hook = " ".join(hook_words) if hook_words else "WATCH THIS"

    all_tags = [category] + tags
    all_tags = list(dict.fromkeys([t for t in all_tags if t]))[:15]

    desc_out = desc[:500] if desc else "Trending on YouTube."
    if hashtags:
        join = " ".join(hashtags[:5])
        if join not in desc_out:
            desc_out = desc_out.rstrip() + "\n\n" + join

    logger.info(f"   Title: {seo_title}")
    logger.info(f"   Tags: {all_tags[:6]}")

    return {
        "short_script": script,
        "seo_youtube_title": seo_title,
        "description": desc_out,
        "hashtags": hashtags[:3],
        "tags": all_tags,
        "viral_hook": hook,
        "visual_queries": [],
        "confidence_score": 85,
    }


def create_video_god(script_data, editor_data):
    logger.info("=" * 60)
    logger.info("VIDEO GENERATION")
    logger.info("=" * 60)
    try:
        from src.media.text_video_builder import create_text_video
        merged = {**script_data, **editor_data}
        merged['short_script'] = script_data.get('short_script', '')
        merged['full_script'] = script_data.get('short_script', '')
        merged['title'] = script_data.get('seo_youtube_title', '')
        p = create_text_video(merged, editor_data)
        logger.info(f"Video: {p}")
        return p
    except Exception as e:
        logger.error(f"Video failed: {e}")
        return None


def create_thumbnail(candidate, script_data):
    try:
        from PIL import Image, ImageDraw, ImageFont
        os.makedirs("output/thumbnails", exist_ok=True)
        tp = "output/thumbnails/thumb.jpg"
        img = Image.new('RGB', (1280, 720), (15, 15, 40))
        d = ImageDraw.Draw(img)
        title = script_data.get('seo_youtube_title', candidate.get('title', 'Trending'))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except Exception:
            font = ImageFont.load_default()
        d.text((644, 364), title[:40], font=font, fill=(0, 0, 0), anchor="mm")
        d.text((640, 360), title[:40], font=font, fill=(255, 255, 255), anchor="mm")
        img.save(tp, quality=95)
        return tp
    except Exception:
        return None


def _sig_words(title):
    clean = re.sub(r'[^\w\s]', '', title.lower()).strip()
    return set(w for w in clean.split() if len(w) > 4)


def is_duplicate(title):
    if not title:
        return False
    try:
        from src.database import get_connection
        key = _sig_words(title)
        if len(key) < 3:
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''SELECT s.title FROM stories s
                       INNER JOIN uploads u ON u.story_id = s.id
                       WHERE s.created_at > datetime('now', '-2 days')''')
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            ex = _sig_words(row[0])
            if not ex:
                continue
            overlap = len(key & ex)
            if overlap >= 4:
                return True
            if overlap >= 3 and min(len(key), len(ex)) > 0:
                if overlap / min(len(key), len(ex)) >= 0.6:
                    return True
        return False
    except Exception:
        return False


def is_similar_this_run(title, seen):
    key = _sig_words(title)
    if len(key) < 3:
        return False
    for prev in seen:
        if len(key & prev) >= 4:
            return True
    return False


def main():
    logger.info("=" * 60)
    logger.info("AUTONOMOUS TEXT BOT v29 (YouTube + Free AI)")
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
    except Exception as e:
        logger.warning(f"Config: {e}")

    logger.info(f"Stats: {get_performance_stats()}")
    self_evolution_main()

    stories = research_god_main()
    if not stories:
        logger.error("No candidates")
        return

    approved = None
    best_rejected = None
    skipped = 0
    seen = []
    lost_stories = []  # track silently-lost ones

    for i, cand in enumerate(stories[:CANDIDATE_POOL_SIZE]):
        title = cand.get('title', '')
        logger.info(f"\nCANDIDATE {i+1}: {title[:60]}")
        logger.info(f"   {cand.get('region')}/{cand.get('category')} | "
                    f"{cand.get('view_count', 0):,}v | "
                    f"rising {cand.get('rising_score', 0):.0f} | "
                    f"score {cand.get('breakout_score', 0):.0f}")

        if is_similar_this_run(title, seen):
            logger.warning("Similar to earlier - skip")
            skipped += 1
            continue
        seen.append(_sig_words(title))

        if is_duplicate(title):
            logger.warning("Duplicate of recent upload")
            skipped += 1
            continue

        sd = generate_script_god(cand)
        if not sd:
            logger.warning("Script failed - skip")
            lost_stories.append((title, "script_failed"))
            continue

        wc = len(sd.get('short_script', '').split())
        if wc < MIN_ACCEPTABLE_WORDS:
            logger.warning(f"Script short ({wc}) - skip")
            lost_stories.append((title, f"short_{wc}"))
            continue

        ed = editor_god_main(sd, cand)
        full = {**cand, **sd}
        sid = save_story(full)
        vp = create_video_god(sd, ed)

        if not vp or not os.path.exists(vp):
            logger.warning("Video failed - skip")
            lost_stories.append((title, "video_failed"))
            continue

        bd = boss_approval_main(vp, sd, full)

        if not bd.get('approved'):
            ts = cand.get('breakout_score', 0)
            if ts >= TRENDING_OVERRIDE_SCORE:
                logger.info(f"🔥 Trending override (score {ts:.0f})")
                bd['approved'] = True
                bd['score'] = max(bd.get('score', 0), 55)
                bd['reason'] = f"Trending override ({ts:.0f})"

        if not best_rejected or bd.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (cand, sd, ed, bd, sid, vp)

        if not bd.get('approved'):
            lost_stories.append((title, "boss_rejected"))
            continue

        approved = (cand, sd, ed, bd, sid, vp)
        break

    if not approved and best_rejected and best_rejected[3].get('score', 0) >= BOSS_FALLBACK_SCORE:
        logger.info(f"Using best rejected (score {best_rejected[3].get('score', 0):.0f})")
        approved = best_rejected

    if not approved:
        logger.error(f"No approved candidate (skipped {skipped})")
        logger.error(f"Lost stories trace:")
        for t, r in lost_stories[-10:]:
            logger.error(f"   [{r}] {t[:60]}")
        return

    cand, sd, ed, bd, sid, vp = approved
    thumb = create_thumbnail(cand, sd)
    vid = uploader_god_main(vp, thumb, sd, cand, bd)

    if vid:
        mark_uploaded(sid, vid)
        logger.info(f"UPLOADED: https://youtu.be/{vid}")

    logger.info("=" * 60)
    logger.info("BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
