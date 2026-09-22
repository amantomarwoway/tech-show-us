"""
main.py - AUTONOMOUS TEXT BOT v34
- Preset channels source
- Permanent dedup by youtube_video_id
- Gemini 3.6 Flash only
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
    is_youtube_id_used, get_all_uploaded_yt_ids,
)

logger = setup_logger(__name__)

MIN_ACCEPTABLE_WORDS = 70
MAX_ACCEPTABLE_WORDS = 200
CANDIDATE_POOL_SIZE = 20
BOSS_FALLBACK_SCORE = 40

FILLER_PATTERNS = [
    r'\bstay\s+tuned\.?', r'\blet\'?s\s+dive\s+in\.?',
    r'\bin\s+conclusion\.?', r'\bwithout\s+further\s+ado\.?',
    r'\bdon\'?t\s+forget\s+to\s+(like|subscribe|comment|hit).*?\.',
    r'\bsmash\s+that\s+like\s+button\.?', r'\bhit\s+the\s+subscribe\s+button\.?',
    r'\blike\s+and\s+subscribe\.?', r'\bmore\s+coming\s+soon\.?',
    r'\bstay\s+with\s+me\.?', r'\bare\s+you\s+ready\?',
    r'\bthink\s+again\.?', r'\bhere\s+we\s+go\.?',
    r'\bpicture\s+the\s+day\b', r'\bimagine\s+if\b',
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
    logger.info("LEG 1: RESEARCH - PRESET CHANNELS")
    logger.info("=" * 60)

    collector = safe_import('src.collectors.preset_channels_collector',
                            'collect_preset_channels')
    if not collector:
        logger.error("Preset channels collector not found")
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

    # Permanent dedup
    uploaded_ids = get_all_uploaded_yt_ids()
    before = len(stories)
    stories = [s for s in stories
               if s.get('youtube_video_id', '') not in uploaded_ids]
    logger.info(f"Permanent dedup: {before} -> {len(stories)} "
                f"(removed {before - len(stories)} already-uploaded)")

    stories.sort(key=lambda x: x.get('breakout_score', 0), reverse=True)

    logger.info(f"LEG 1: {len(stories)} fresh candidates")
    for i, s in enumerate(stories[:8]):
        logger.info(
            f"  #{i+1}: [{s['category']}] {s['title'][:55]} "
            f"({s['view_count']:,}v, {s['age_hours']:.0f}h, score {s['breakout_score']:.0f})"
        )

    return stories[:CANDIDATE_POOL_SIZE]


def editor_god_main(script_data, candidate):
    return {"facts": [], "visuals": []}


def boss_approval_main(video_path, script_data, full_story):
    return {"approved": True, "score": 55, "reason": "Approved"}


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
        "motivation": "#Motivation", "story": "#Story",
        "facts": "#Facts", "podcast": "#Podcast", "science": "#Science",
        "music": "#Music", "gaming": "#Gaming", "entertainment": "#Trending",
        "sports": "#Sports", "news": "#News", "tech": "#Tech",
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


def main():
    logger.info("=" * 60)
    logger.info("AUTONOMOUS TEXT BOT v34 (preset channels + Gemini)")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    init_db()

    try:
        from src.learning.auto_optimizer import init_autonomous_config, get_all_config
        init_autonomous_config()
        config = get_all_config()
        logger.info(f"Config v{config.get('version')}")
    except Exception as e:
        logger.warning(f"Config: {e}")

    logger.info(f"Stats: {get_performance_stats()}")
    self_evolution_main()

    uploaded_ids = get_all_uploaded_yt_ids()
    logger.info(f"Permanent memory: {len(uploaded_ids)} uploaded videos")

    stories = research_god_main()
    if not stories:
        logger.error("No fresh candidates")
        return

    approved = None
    skipped = 0
    seen = []

    for i, cand in enumerate(stories[:CANDIDATE_POOL_SIZE]):
        title = cand.get('title', '')
        yt_id = cand.get('youtube_video_id', '')
        logger.info(f"\nCANDIDATE {i+1}: {title[:60]}")
        logger.info(f"   {cand.get('category')} | "
                    f"{cand.get('view_count', 0):,}v | "
                    f"score {cand.get('breakout_score', 0):.0f} | "
                    f"yt_id={yt_id}")

        if yt_id and yt_id in uploaded_ids:
            logger.warning("   DEDUP: already uploaded")
            skipped += 1
            continue

        sig = set(w for w in re.findall(r'\w+', title.lower()) if len(w) > 4)
        if any(len(sig & p) >= 4 for p in seen):
            logger.warning("   DEDUP: similar title this run")
            skipped += 1
            continue
        seen.append(sig)

        sd = generate_script_god(cand)
        if not sd:
            continue

        wc = len(sd.get('short_script', '').split())
        if wc < MIN_ACCEPTABLE_WORDS:
            continue

        ed = editor_god_main(sd, cand)
        full = {**cand, **sd}
        sid = save_story(full)
        vp = create_video_god(sd, ed)

        if not vp or not os.path.exists(vp):
            continue

        bd = boss_approval_main(vp, sd, full)

        if not bd.get('approved'):
            continue

        approved = (cand, sd, ed, bd, sid, vp)
        break

    if not approved:
        logger.error(f"No approved candidate (skipped {skipped})")
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
