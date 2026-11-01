"""
HEY DARKY story bot — the single entry point that wires every piece together.

    python main_story.py build [--force]   # a long story is due? build + publish it
    python main_story.py publish-queue     # publish today's queued Short

CADENCE (one long video every 2 days, one Short every day):
  Day 1  build: research -> story -> video -> thumbnail
         -> YouTube long + Facebook long
         -> Short 1: YouTube + Facebook Reel + Instagram Reel (now)
         -> Short 2: queued for tomorrow
  Day 2  publish-queue: Short 2 -> YouTube + Facebook Reel + Instagram Reel
  Day 3  build again ...
"Due" is decided from what was ACTUALLY uploaded (database), not the calendar,
so a failed day is retried the next day on its own.

PLATFORMS: the long story goes to YouTube + Facebook; every Short goes to
YouTube + Facebook + Instagram; Instagram gets ONLY the daily Short. Each
platform gets its own title / description / hashtags (src/platform_metadata.py).
YouTube is the primary: if its long upload fails the run FAILS (so the CI
run shows red). Facebook / Instagram problems are logged and never undo a
successful YouTube publish.

REVIEW_MODE (config; repo variable REVIEW_MODE, default "1"): everything is
uploaded PRIVATE / unpublished and Instagram is skipped, so you can check the
first runs by hand. Set the repo variable REVIEW_MODE=0 for fully automatic
public publishing.
"""
import argparse
import json
import logging
import os
import random
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone

from src import facebook_publisher, instagram_publisher
from src.config import (
    OUTPUT_DIR,
    REVIEW_MODE,
    ROOT_DIR,
    STORY_GENRES,
    STORY_LONG_EVERY_DAYS,
    STORY_RESEARCH_QUERIES,
    STORY_SHORT_QUEUE_DELAY_HOURS,
    STORY_SHORTS_PER_STORY,
    STORY_YT_CATEGORY,
)
from src.database import (
    enqueue_publish,
    get_due_publish_items,
    init_db,
    mark_publish_item,
    record_story_upload,
    should_build_long_today,
)
from src.platform_metadata import build_long_posts, build_short_posts
from src.story_pipeline import build_story_video
from src.story_shorts import build_story_shorts
from src.story_thumbnail import build_story_thumbnail
from src.topic_research import research_niche
from src.youtube_uploader import upload_thumbnail, upload_video

log = logging.getLogger("main_story")
PENDING_DIR = ROOT_DIR / "pending"   # queued Shorts live here (the workflow caches this folder)
_t0 = time.monotonic()


def step(name: str) -> None:
    log.info("=== STEP: %s === [elapsed: %.0fs]", name, time.monotonic() - _t0)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _research(genre: str) -> dict | None:
    """Real recent YouTube data for this genre's niche; never fatal."""
    query = STORY_RESEARCH_QUERIES.get(genre, f"{genre} story narration")
    try:
        research = research_niche(query)
        log.info("Niche research %r: sample_size=%s, top tags=%s",
                 query, research.get("sample_size"), research.get("suggested_tags", [])[:5])
        return research
    except Exception as e:
        log.warning("Niche research failed (%s) — writing the story without it", e)
        return None


def _safe(label: str, fn, *args, **kwargs):
    """Run a secondary-platform call; ANY exception (an unexpected API shape, a
    network error) is logged and becomes None, so Facebook/Instagram can never
    stop the Shorts, the queue or the database update after YouTube succeeded."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.error("%s failed: %s: %s", label, type(e).__name__, e)
        return None


def _publish_youtube(path, post: dict, review: bool) -> str:
    """Upload to YouTube (private in REVIEW_MODE, else public now). English is
    declared as the video's language by the uploader itself. Raises on failure."""
    return upload_video(
        path, post["title"], post["description"], post["tags"],
        privacy_status="private" if review else "public", category_id=STORY_YT_CATEGORY,
    )


def _publish_short(path, posts: dict, review: bool, done: dict | None = None) -> dict:
    """Publish one Short to YouTube + Facebook Reel + Instagram Reel. Platforms
    already present (truthy) in `done` are NOT re-posted (retry safety: a retry
    must never create duplicates). Returns {platform: id-or-None[, errors]}."""
    res = dict(done or {})
    if not res.get("youtube"):
        try:
            res["youtube"] = _publish_youtube(path, posts["youtube"], review)
        except Exception as e:
            log.error("YouTube Short upload failed: %s", e)
            res["youtube"], res["youtube_error"] = None, str(e)
    if not res.get("facebook") and facebook_publisher.is_configured():
        res["facebook"] = _safe("Facebook Reel", facebook_publisher.publish_reel, path, posts["facebook"]["description"], published=not review)
    if not res.get("instagram") and instagram_publisher.is_configured():
        if review:
            res["instagram"] = "skipped (REVIEW_MODE)"
        else:
            res["instagram"] = _safe("Instagram Reel", instagram_publisher.publish_reel, path, posts["instagram"]["caption"])
    return res


def _short_complete(res: dict) -> bool:
    """Every CONFIGURED platform has an id (or was deliberately skipped)."""
    if not res.get("youtube"):
        return False
    if facebook_publisher.is_configured() and not res.get("facebook"):
        return False
    if instagram_publisher.is_configured() and not res.get("instagram"):
        return False
    return True


def _record_short(res: dict, posts: dict, meta: dict) -> None:
    if res.get("youtube"):
        record_story_upload(
            res["youtube"], posts["youtube"]["title"], meta["pillar"], meta.get("recurring", ""),
            kind="short", parent_video_id=meta.get("long_video_id"), genre=meta.get("genre"),
        )


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def run_build(force: bool = False) -> int:
    init_db()
    if not force and not should_build_long_today(STORY_LONG_EVERY_DAYS):
        log.info("No long story is due yet (one every %d days) — nothing to build.", STORY_LONG_EVERY_DAYS)
        return 0

    genre = os.getenv("STORY_GENRE") or random.choice(STORY_GENRES)
    if genre not in STORY_GENRES:
        raise ValueError(f"STORY_GENRE={genre!r} is not one of {STORY_GENRES}")
    review = REVIEW_MODE
    log.info("Building a %s story | REVIEW_MODE=%s", genre, review)

    step("Niche research")
    research = _research(genre)

    step("Story + voices + images + video + audio layering")
    result = build_story_video(genre, premise=os.getenv("STORY_PREMISE", ""), research=research)
    story, assets, long_path = result["story"], result["assets"], result["long_video_path"]

    step("Thumbnail + per-platform metadata")
    thumb = build_story_thumbnail(story)
    long_posts = build_long_posts(story, research)

    step("Publish long story: YouTube")
    yt_long = _publish_youtube(long_path, long_posts["youtube"], review)   # raises -> run fails (primary platform)
    if thumb:
        try:
            upload_thumbnail(yt_long, thumb)
        except Exception as e:
            log.warning("Thumbnail upload failed (video is still live): %s", e)
    record_story_upload(
        yt_long, long_posts["youtube"]["title"], story["pillar"],
        story.get("recurring_character_used", ""), kind="long", genre=genre,
    )
    log.info("YouTube long: https://youtu.be/%s", yt_long)

    step("Publish long story: Facebook")
    fb_long = _safe("Facebook long video", facebook_publisher.publish_long_video,
                    long_path, long_posts["facebook"]["title"], long_posts["facebook"]["description"], published=not review)

    step("Shorts: render")
    shorts = build_story_shorts(assets, STORY_SHORTS_PER_STORY)
    if not shorts:
        log.error("No Short could be rendered for this story — the long video is already published")
    meta = {"pillar": story["pillar"], "genre": genre,
            "recurring": story.get("recurring_character_used", ""), "long_video_id": yt_long}
    summary = {"genre": genre, "pillar": story["pillar"], "title": long_posts["youtube"]["title"],
               "youtube_long": yt_long, "facebook_long": fb_long, "review_mode": review, "shorts": []}

    for k, short in enumerate(shorts):
        posts = build_short_posts(story, research, short, yt_long)
        if k == 0 or review:
            step(f"Shorts: publish #{k + 1} now (YouTube + Facebook + Instagram)")
            res = _publish_short(short["path"], posts, review)
            _record_short(res, posts, meta)
            summary["shorts"].append({"n": k + 1, "published": res})
        else:
            step(f"Shorts: queue #{k + 1} for tomorrow")
            PENDING_DIR.mkdir(parents=True, exist_ok=True)
            queued = PENDING_DIR / f"{assets['slug']}-short{k + 1}.mp4"
            shutil.copy(short["path"], queued)
            due = datetime.now(timezone.utc) + timedelta(hours=STORY_SHORT_QUEUE_DELAY_HOURS)
            qid = enqueue_publish(due.isoformat(), str(queued.relative_to(ROOT_DIR)),
                                  {"posts": posts, "meta": meta})
            summary["shorts"].append({"n": k + 1, "queued_id": qid, "due_at": due.isoformat()})

    (OUTPUT_DIR / "last_run.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    log.info("RUN COMPLETE: %s", json.dumps(summary, default=str))
    return 0


def run_publish_queue() -> int:
    init_db()
    items = get_due_publish_items()
    if not items:
        log.info("Publish queue: nothing due.")
        return 0
    review = REVIEW_MODE
    for item in items:
        path = ROOT_DIR / item["file_path"]
        if not path.exists():
            log.error("Queued file is missing (%s) — likely a workflow-cache miss; marking failed.", path)
            mark_publish_item(item["id"], "failed", {"error": "file missing"})
            continue
        payload = item["payload"]
        previous = json.loads(item["result"]) if item.get("result") else {}
        step(f"Publish queued Short #{item['id']}")
        res = _publish_short(path, payload["posts"], review, done=previous)
        _record_short(res, payload["posts"], payload.get("meta", {}))
        complete = _short_complete(res)
        mark_publish_item(item["id"], "done" if complete else "pending", res)
        log.info("Queued Short #%s: %s -> %s", item["id"], "DONE" if complete else "partial (will retry)", res)
        if complete:
            path.unlink(missing_ok=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hey Darky story bot")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="build + publish the next long story (and its Shorts) if one is due")
    b.add_argument("--force", action="store_true", help="build even if no story is due yet")
    sub.add_parser("publish-queue", help="publish queued Shorts that are due")
    args = parser.parse_args(argv)
    return run_build(args.force) if args.command == "build" else run_publish_queue()


if __name__ == "__main__":
    (ROOT_DIR / "logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(ROOT_DIR / "logs" / "story_bot.log")],
    )
    try:
        sys.exit(main())
    except Exception:
        log.exception("Story bot run failed")
        sys.exit(1)
