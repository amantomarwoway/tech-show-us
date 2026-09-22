"""
main.py - AUTONOMOUS TEXT BOT - v32
- STRONG duplicate detection by youtube_video_id
- Title overlap threshold 4 → 3
- Cross-run topic memory (7 days)
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
from src.database import (
    init_db, save_story, mark_uploaded, get_performance_stats,
    is_youtube_id_used, get_recent_titles,
)

logger = setup_logger(__name__)

MIN_ACCEPTABLE_WORDS = 70
MAX_ACCEPTABLE_WORDS = 200
CANDIDATE_POOL_SIZE = 15
BOSS_FALLBACK_SCORE = 40
MIN_VIEWS_FOR_TREND = 50000
TRENDING_OVERRIDE_SCORE = 70
DUPLICATE_LOOKBACK_DAYS = 7      # Check last 7 days
TITLE_OVERLAP_MIN = 3            # was 4 → now 3

FILLER_PATTERNS = [
    r'\bstay\s+tuned\.?', r'\blet\'?s\s+dive\s+in\.?',
    r'\bin\s+conclusion\.?', r'\bwithout\s+further\s+ado\.?',
    r'\bdon\'?t\s+forget\s+to\s+(like|subscribe|comment|hit).*?\.',
    r'\bsmash\s+that\s+like\s+button\.?', r'\bhit\s+the\s+subscribe\s+button\.?',
    r'\blike\s+and\s+subscribe\.?', r'\bmore\s+coming\s+soon\.?',
    r'\bstay\s+with\s+me\.?', r'\bare\s+you\s+ready\?',
    r'\bthink\s+again\.?', r'\bhere\s+we\s+go\.?',
]


def safe_import(mp, fn=None):
    try:
        if fn:
            m = __import__(mp, fromlist=[fn])
            return getattr(m, fn)
        return __import__(mp)
    except Exception as e:
        logger.warning(f"Import failed {mp}: {e}")
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


def strip_filler(script):
    if not script:
        return script
    for p in FILLER_PATTERNS:
        script = re.sub(p, '', script, flags=re.IGNORECASE)
    script = re.sub(r'\s+', ' ', script).strip()
    script = re.sub(r'\.\s*\.', '.', script)
    if script and not script.endswith(('.', '!', '?')):
        script += "."
    return script


def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH - YOUTUBE TRENDING")
    logger.info("=" * 60)

    collector = safe_import('src.collectors.youtube_trending_collector',
                            'collect_youtube_trending')
    if not collector:
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

    before = len(stories)
    stories = [s for s in stories if s.get('view_count', 0) >= MIN_VIEWS_FOR_TREND]
    logger.info(f"Min views filter: {before} -> {len(stories)} (removed {before - len(stories)})")

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
    return {"facts": [], "visuals": []}


def boss_approval_main(video_path, script_data, full_story):
    result = {"approved": True, "score": 55, "reason": "Simplified approval"}
    logger.info(f"LEG 3: OK - {result['reason']}")
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
    logger.info("SELF EVOLUTION")
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


def _hashtags_from_title(title, category):
    hmap = {
        "music": "#Music", "gaming": "#Gaming",
        "entertainment": "#Trending", "sports": "#Sports",
        "news": "#News", "tech": "#Tech", "comedy": "#Comedy",
    }
    return [hmap.get(category, "#Trending"), "#Shorts", "#Trending"]


def generate_script_god(story):
    from src.collectors.yt_metadata_collector import (
        fetch_transcript, generate_script_and_tags
    )

    vid = story.get('youtube_video_id', '')
    title = story.get('title', '')
    desc = story.get('description', '')
    category = story.get('category', 'trending')

    logger.info(f"Generating script for: {title[:60]}")

    transcript = fetch_transcript(vid) if vid else None
    hashtags = _hashtags_from_title(title, category)

    ai = generate_script_and_tags(title, desc, transcript)
    if not ai:
        return None

    script = ai["script"]
    tags = ai["tags"]
    script = strip_filler(script)

    wc = len(script.split())
    logger.info(f"AI script (post-clean): {wc} words")

    if wc < MIN_ACCEPTABLE_WORDS:
        logger.warning(f"Too short ({wc} < {MIN_ACCEPTABLE_WORDS})")
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


def is_duplicate_title(title, recent_titles):
    """Fuzzy match against recent titles (last 7 days)."""
    if not title:
        return False
    key = _sig_words(title)
    if len(key) < 3:
        return False
    for ex_title, ex_yt_id in recent_titles:
        ex = _sig_words(ex_title)
        if not ex:
            continue
        overlap = len(key & ex)
        # 4+ overlap → duplicate
        if overlap >= 4:
            return True
        # 3+ overlap with 60% coverage → duplicate
        if overlap >= TITLE_OVERLAP_MIN:
            min_len = min(len(key), len(ex))
            if min_len > 0 and overlap / min_len >= 0.6:
                return True
    return False


def is_similar_this_run(title, seen):
    key = _sig_words(title)
    if len(key) < 3:
        return False
    for prev in seen:
        if len(key & prev) >= TITLE_OVERLAP_MIN:
            return True
    return False


def main():
    logger.info("=" * 60)
    logger.info("AUTONOMOUS TEXT BOT v32")
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

    # ============================================================
    # LOAD RECENT TITLES (last 7 days) — cross-run memory
    # ============================================================
    recent_titles = get_recent_titles(days=DUPLICATE_LOOKBACK_DAYS)
    logger.info(f"Loaded {len(recent_titles)} recent titles for dedup")

    stories = research_god_main()
    if not stories:
        logger.error("No candidates")
        return

    approved = None
    best_rejected = None
    skipped = 0
    seen = []
    lost = []

    for i, cand in enumerate(stories[:CANDIDATE_POOL_SIZE]):
        title = cand.get('title', '')
        yt_id = cand.get('youtube_video_id', '')
        logger.info(f"\nCANDIDATE {i+1}: {title[:60]}")
        logger.info(f"   {cand.get('region')}/{cand.get('category')} | "
                    f"{cand.get('view_count', 0):,}v | "
                    f"rising {cand.get('rising_score', 0):.0f} | "
                    f"score {cand.get('breakout_score', 0):.0f} | "
                    f"yt_id={yt_id}")

        # ============================================================
        # DEDUP 1: Exact YouTube video_id already used?
        # ============================================================
        if yt_id and is_youtube_id_used(yt_id, days=DUPLICATE_LOOKBACK_DAYS):
            logger.warning(f"   DEDUP: YouTube video_id {yt_id} already used")
            skipped += 1
            continue

        # ============================================================
        # DEDUP 2: Similar title in this run?
        # ============================================================
        if is_similar_this_run(title, seen):
            logger.warning("   DEDUP: Similar to earlier candidate in this run")
            skipped += 1
            continue
        seen.append(_sig_words(title))

        # ============================================================
        # DEDUP 3: Fuzzy title match with recent DB titles?
        # ============================================================
        if is_duplicate_title(title, recent_titles):
            logger.warning("   DEDUP: Title matches recent upload (7 days)")
            skipped += 1
            continue

        # Script generation
        sd = generate_script_god(cand)
        if not sd:
            lost.append((title, "script_failed"))
            continue

        wc = len(sd.get('short_script', '').split())
        if wc < MIN_ACCEPTABLE_WORDS:
            lost.append((title, f"short_{wc}"))
            continue

        ed = editor_god_main(sd, cand)
        full = {**cand, **sd}   # ← youtube_video_id gets carried into DB
        sid = save_story(full)
        vp = create_video_god(sd, ed)

        if not vp or not os.path.exists(vp):
            lost.append((title, "video_failed"))
            continue

        bd = boss_approval_main(vp, sd, full)

        if not bd.get('approved'):
            ts = cand.get('breakout_score', 0)
            if ts >= TRENDING_OVERRIDE_SCORE:
                bd['approved'] = True
                bd['score'] = 55

        if not best_rejected or bd.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (cand, sd, ed, bd, sid, vp)

        if not bd.get('approved'):
            lost.append((title, "boss_rejected"))
            continue

        approved = (cand, sd, ed, bd, sid, vp)
        break

    if not approved and best_rejected and best_rejected[3].get('score', 0) >= BOSS_FALLBACK_SCORE:
        approved = best_rejected

    if not approved:
        logger.error(f"No approved (skipped {skipped} duplicates)")
        for t, r in lost[-10:]:
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
