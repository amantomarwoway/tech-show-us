"""
HEY DARKY story bot — the single entry point that wires every piece together.

    python main_story.py build [--force]   # fill the next open weekly slot: write, render, schedule, publish
    python main_story.py publish-queue     # post what is due (Instagram cannot be scheduled by API)
    python main_story.py schedule          # print the slots, the stories and what is planned

THE SHOW. Three stories run in parallel, each owning one weekly slot (src/schedule.py: Wednesday / Friday /
Sunday 8 PM Eastern by default, because crime and horror viewers watch late at night). Every week each story
gets its NEXT PART — a story is a series, not a movie. After each part the audience decides what happens next
(src/series_planner.py): a hit is extended, a flop is wrapped up as soon as possible, and a finished story's
slot is taken by a brand-new story. Every part must deliver fear, curiosity, suspense, excitement and mystery,
open with a 30-second hook and (except a finale) end on a cliffhanger.

ONE RUN builds ONE episode: the soonest open slot inside the lead window (BUILD_LEAD_DAYS), with its Shorts.
  * YouTube long: uploaded now, PRIVATE with `publishAt` = the slot, so YouTube itself makes it public at that
    exact moment (no job has to be awake then); added to the story's playlist; the previous part's description
    gets a "Next part" link.
  * Facebook long: scheduled for the same moment.
  * 2-3 Shorts (7 a week = one per day) take the next free daily 5 PM ET slots — the first one on release day,
    ~3 hours BEFORE the episode, as its announcement: YouTube + Facebook are
    scheduled the same way; Instagram has no scheduler, so its posts wait in the queue until due.
  * A "related video" checklist (data/related_video_checklist.md): the YouTube API cannot link a Short to its
    long video, so each Short is listed with the episode it should point to (set it in Studio — a minute each).
YouTube is the primary platform: if its long upload fails the run FAILS. Facebook / Instagram / playlist /
description problems are logged and never undo a successful YouTube publish.

REVIEW_MODE (repo variable REVIEW_MODE, default "1"): nothing is scheduled — everything is uploaded PRIVATE /
unpublished immediately and Instagram is skipped, so the first runs can be checked by hand. Set the variable
to 0 for the fully automatic show.
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

from src import facebook_publisher, instagram_publisher, schedule
from src.config import (
    AUTO_SLOT_SWAP,
    CHANNEL_NAME,
    OUTPUT_DIR,
    REVIEW_MODE,
    ROOT_DIR,
    SHORT_LEAD_HOURS,
    SHORTS_PER_EPISODE_BY_SLOT,
    STORY_GENRES,
    STORY_RESEARCH_QUERIES,
    STORY_YT_CATEGORY,
)
from src.database import (
    create_series,
    enqueue_publish,
    episodes_for_series,
    get_active_series,
    get_due_publish_items,
    get_playlist,
    get_slots,
    init_db,
    mark_publish_item,
    record_story_upload,
    set_playlist,
    update_series,
)
from src.platform_metadata import build_long_posts, build_short_posts
from src.series_bible import new_bible, updated_bible
from src.series_planner import plan_for_slot
from src.story_pipeline import build_story_video
from src.story_shorts import build_story_shorts
from src.story_thumbnail import build_story_thumbnail
from src.topic_research import research_niche
from src.youtube_uploader import add_to_playlist, append_to_description, ensure_playlist, upload_thumbnail, upload_video

log = logging.getLogger("main_story")
PENDING_DIR = ROOT_DIR / "pending"                    # Shorts waiting for their Instagram post (the workflow caches this)
CHECKLIST_PATH = ROOT_DIR / "data" / "related_video_checklist.md"
_t0 = time.monotonic()


def step(name: str) -> None:
    log.info("=== STEP: %s === [elapsed: %.0fs]", name, time.monotonic() - _t0)


def _safe(label: str, fn, *args, **kwargs):
    """Run a secondary call; ANY exception (an unexpected API shape, a network error) is logged and becomes
    None, so Facebook / Instagram / playlists can never stop the Shorts, the queue or the database update
    after YouTube succeeded."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log.error("%s failed: %s: %s", label, type(e).__name__, e)
        return None


def _research(genre: str) -> dict | None:
    """Real recent YouTube data for this genre's niche; never fatal."""
    query = STORY_RESEARCH_QUERIES.get(genre, f"{genre} story narration")
    try:
        research = research_niche(query)
        if not research:
            return None
        log.info("Niche research %r: sample_size=%s, top tags=%s",
                 query, research.get("sample_size"), research.get("suggested_tags", [])[:5])
        return research
    except Exception as e:
        log.warning("Niche research failed (%s) — writing the story without it", e)
        return None


def _schedulable(when: datetime | None) -> datetime | None:
    """A slot time YouTube can still be given. If the build ran long and the slot is now less than 3 minutes
    away (or already past), publishAt would be refused — so the video simply goes public right away."""
    if when is None or when - datetime.now(timezone.utc) < timedelta(minutes=3):
        return None
    return when


def _publish_youtube(path, post: dict, review: bool, publish_at: datetime | None = None) -> str:
    """Upload to YouTube: private immediately in REVIEW_MODE, else private + publishAt so YouTube makes it
    public at the slot (no publishAt = public at once). Raises on failure."""
    publish_at = _schedulable(publish_at)
    return upload_video(
        path, post["title"], post["description"], post["tags"],
        privacy_status="private" if review else "public", category_id=STORY_YT_CATEGORY,
        publish_at=None if review else publish_at,
    )


def _publish_short(path, posts: dict, review: bool, done: dict | None = None,
                   publish_at: datetime | None = None, include_instagram: bool = True) -> dict:
    """Publish one Short to YouTube + Facebook Reel (+ Instagram Reel). Platforms already present (truthy) in
    `done` are NOT re-posted (retry safety: a retry must never create duplicates). With `publish_at`, YouTube
    and Facebook are SCHEDULED for that moment. Returns {platform: id-or-None[, errors]}."""
    res = dict(done or {})
    if not res.get("youtube"):
        try:
            res["youtube"] = _publish_youtube(path, posts["youtube"], review, publish_at)
        except Exception as e:
            log.error("YouTube Short upload failed: %s", e)
            res["youtube"], res["youtube_error"] = None, str(e)
    if not res.get("facebook") and facebook_publisher.is_configured():
        res["facebook"] = _safe("Facebook Reel", facebook_publisher.publish_reel, path,
                                posts["facebook"]["description"], published=not review,
                                scheduled_time=None if review else publish_at)
    if include_instagram and not res.get("instagram") and instagram_publisher.is_configured():
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


def _append_checklist(entries: list[str]) -> None:
    """data/related_video_checklist.md — one line per Short. YouTube's API has no field for a Short's
    "Related video", so this is the to-do list for linking each Short to its full episode in Studio."""
    CHECKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CHECKLIST_PATH.exists():
        CHECKLIST_PATH.write_text(
            "# Related-video checklist\n\nYouTube Studio -> Content -> Shorts -> open the Short -> Edit -> "
            "Related video -> pick the episode listed. Tick a line when done.\n\n", encoding="utf-8")
    existing = CHECKLIST_PATH.read_text(encoding="utf-8")
    new = [e for e in entries if e.split(" -> ")[0] not in existing]
    if new:
        CHECKLIST_PATH.write_text(existing.rstrip("\n") + "\n" + "\n".join(new) + "\n", encoding="utf-8")


def _channel_playlists(genre: str) -> list[str]:
    """Ids of the channel-wide playlists every episode joins besides its own series playlist (2026 guides:
    every video should sit in 3-4 playlists — they extend sessions and earn Browse / Suggested placements).
    Created on first use and remembered in the database."""
    out = []
    for key, title in ((f"genre:{genre}", f"{genre.title()} Stories | Hey Darky"), ("all-episodes", "Every Episode | Hey Darky")):
        pid = get_playlist(key)
        if not pid:
            pid = _safe(f"Playlist {key}", ensure_playlist, title, f"Narrated {genre} stories from Hey Darky.")
            if pid:
                set_playlist(key, pid)
        if pid:
            out.append(pid)
    return out


def _slot_labels(slot_index: int) -> tuple[str, str]:
    """("Friday night", "premieres Friday 8 PM ET") for the slot's weekday — the spoken closing line and the
    description's "Next:" line."""
    slot = next(s for s in get_slots() if s["slot_index"] == slot_index)
    day = schedule.WEEKDAYS[slot["weekday"]]
    return (f"{day} night" if slot["hour_local"] >= 17 else day,
            f"premieres {schedule.describe_slot(slot['weekday'], slot['hour_local'], slot['minute'])}")


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------
def run_build(force: bool = False) -> int:
    init_db()
    now = datetime.now(timezone.utc)
    swap = schedule.evaluate_slots()
    if swap and AUTO_SLOT_SWAP:
        schedule.apply_slot_swap(swap)
    elif swap:
        log.info("Slot report suggests a change (not applied — AUTO_SLOT_SWAP is off): %s", swap["reason"])
    target = schedule.next_open_long_slot(now, force=force)
    if target is None:
        log.info("No weekly slot is open inside the next days — nothing to build.")
        return 0
    slot_index, slot_time = target
    review = REVIEW_MODE
    plan = plan_for_slot(slot_index, now=now)
    series, part_no, mode = plan.series, plan.part_no, plan.mode
    genre = series["genre"] if series else (os.getenv("STORY_GENRE") or random.choice(STORY_GENRES))
    if genre not in STORY_GENRES:
        raise ValueError(f"STORY_GENRE={genre!r} is not one of {STORY_GENRES}")
    next_when, next_label = _slot_labels(slot_index)
    log.info("Building %s part %d (%s) for slot %d = %s UTC | REVIEW_MODE=%s | %s", genre, part_no, mode,
             slot_index, slot_time.strftime("%Y-%m-%d %H:%M"), review, plan.reason)

    step("Niche research")
    research = _research(genre)

    step("Episode: story + voices + images + video + audio layering")
    result = build_story_video(
        None if series else genre, premise=os.getenv("STORY_PREMISE", ""), research=research,
        series=series, part_no=part_no, mode=mode, planned_parts=plan.planned_parts, next_label=next_when)
    story, assets, long_path = result["story"], result["assets"], result["long_video_path"]
    series_title = series["title"] if series else story["series"]["title"]
    meta_series = {"title": series_title}

    step("Series playlist + thumbnail + per-platform metadata")
    playlist_id = series.get("playlist_id") if series else None
    if not playlist_id:
        playlist_id = _safe("YouTube playlist", ensure_playlist, f"{series_title} | {CHANNEL_NAME}",
                            (story.get("series") or {}).get("logline", ""))
    playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}" if playlist_id else None
    previous = episodes_for_series(series["id"]) if series else []
    prev_id = previous[-1]["video_id"] if previous else None
    thumb = build_story_thumbnail(story)
    long_posts = build_long_posts(story, research, series=meta_series, part_no=part_no, mode=mode,
                                  prev_url=f"https://youtu.be/{prev_id}" if prev_id else None,
                                  playlist_url=playlist_url, next_label=next_label)

    step("Publish the episode: YouTube")
    yt_long = _publish_youtube(long_path, long_posts["youtube"], review, slot_time)   # raises -> run fails (primary platform)
    if thumb:
        _safe("Thumbnail upload", upload_thumbnail, yt_long, thumb)

    # Only now — the upload succeeded — does the story become part of the show's database.
    if series is None:
        bible = new_bible(story)
        bible["voice_map"] = assets["voice_map"]
        series_id = create_series(series_title, genre, story["pillar"], story["series"]["planned_parts"], slot_index, bible)
        if playlist_id:
            update_series(series_id, playlist_id=playlist_id)
    else:
        series_id = series["id"]
        bible = updated_bible(series["bible"], story, assets["voice_map"])
    finished = mode == "finale"
    update_series(series_id, parts_done=part_no, bible=bible,
                  **({"status": "finished", "finished_at": datetime.now(timezone.utc).isoformat()} if finished else {}))
    record_story_upload(
        yt_long, long_posts["youtube"]["title"], story["pillar"], story.get("recurring_character_used", ""),
        kind="long", genre=genre, series_id=series_id, part_no=part_no, slot_index=slot_index,
        publish_at=slot_time.isoformat())
    log.info("YouTube episode: https://youtu.be/%s (goes public %s)", yt_long, "now/private (review)" if review else f"{slot_time:%Y-%m-%d %H:%M} UTC")
    for pid in ([playlist_id] if playlist_id else []) + _channel_playlists(genre):
        _safe("Add to playlist", add_to_playlist, pid, yt_long)
    if prev_id:
        _safe("Previous part's 'Next part' link", append_to_description, prev_id,
              f"▶ Next: Part {part_no} — https://youtu.be/{yt_long}")

    step("Publish the episode: Facebook")
    fb_long = _safe("Facebook long video", facebook_publisher.publish_long_video, long_path,
                    long_posts["facebook"]["title"], long_posts["facebook"]["description"],
                    published=not review, scheduled_time=None if review else slot_time)

    step("Shorts: render")
    want = SHORTS_PER_EPISODE_BY_SLOT[slot_index] if slot_index < len(SHORTS_PER_EPISODE_BY_SLOT) else 2
    part_label = "FINAL PART" if finished else f"PART {part_no}"
    # one banner for every platform: "related video" exists only on YouTube, so it points at the channel instead
    shorts = build_story_shorts(assets, want, cta_text=f"FULL STORY: {part_label} ON YOUTUBE — {CHANNEL_NAME.upper()}")
    if not shorts:
        log.error("No Short could be rendered for this episode — the long video is already scheduled")
    short_times = schedule.next_short_slots(slot_time - timedelta(hours=SHORT_LEAD_HOURS), len(shorts), now=now)
    summary = {"series": series_title, "part": part_no, "mode": mode, "genre": genre, "pillar": story["pillar"],
               "title": long_posts["youtube"]["title"], "youtube_long": yt_long, "facebook_long": fb_long,
               "goes_public": slot_time.isoformat(), "review_mode": review, "shorts": []}
    checklist = []

    for k, (short, when) in enumerate(zip(shorts, short_times)):
        posts = build_short_posts(story, research, short, yt_long, series=meta_series, part_no=part_no, mode=mode,
                                  playlist_url=playlist_url)
        step(f"Shorts: publish #{k + 1} ({'now, private' if review else f'scheduled for {when:%a %d %b %H:%M} UTC'})")
        res = _publish_short(short["path"], posts, review, publish_at=when, include_instagram=review)
        if res.get("youtube"):
            record_story_upload(
                res["youtube"], posts["youtube"]["title"], story["pillar"], story.get("recurring_character_used", ""),
                kind="short", parent_video_id=yt_long, genre=genre, series_id=series_id, part_no=part_no,
                slot_index=slot_index, publish_at=when.isoformat())
            checklist.append(f"- [ ] https://youtu.be/{res['youtube']} -> https://youtu.be/{yt_long} ({series_title}, {part_label.title()})")
        entry = {"n": k + 1, "goes_public": when.isoformat(), "published": res}
        if not review:
            PENDING_DIR.mkdir(parents=True, exist_ok=True)
            queued = PENDING_DIR / f"s{series_id}-p{part_no}-short{k + 1}.mp4"      # unique per story+part, never title-based
            shutil.copy(short["path"], queued)
            entry["queued_id"] = enqueue_publish(when.isoformat(), str(queued.relative_to(ROOT_DIR)), {"posts": posts}, result=res)
        summary["shorts"].append(entry)

    _safe("Related-video checklist", _append_checklist, checklist)
    (OUTPUT_DIR / "last_run.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    log.info("RUN COMPLETE: %s", json.dumps(summary, default=str))
    return 0


def run_publish_queue() -> int:
    """Post what is due. For scheduled Shorts YouTube and Facebook already have their ids (they publish by
    themselves at the slot), so only Instagram is posted here — at the due time."""
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
        previous = json.loads(item["result"]) if item.get("result") else {}
        step(f"Publish queued Short #{item['id']}")
        res = _publish_short(path, item["payload"]["posts"], review, done=previous)
        complete = _short_complete(res)
        mark_publish_item(item["id"], "done" if complete else "pending", res)
        log.info("Queued Short #%s: %s -> %s", item["id"], "DONE" if complete else "partial (will retry)", res)
        if complete:
            path.unlink(missing_ok=True)
    return 0


def run_schedule() -> int:
    """Print the slots, what they have achieved, and the stories on air."""
    init_db()
    now = datetime.now(timezone.utc)
    print("WEEKLY SLOTS (US Eastern):")
    for row in schedule.slot_report():
        print(f"  slot {row['slot_index']}: {row['when']:<22} episodes with data: {row['n']}  avg views: {row['avg_views']:.0f}")
    print("\nSTORIES ON AIR:")
    for s in get_active_series() or []:
        print(f"  #{s['id']} {s['title']!r} [{s['genre']}] slot {s['slot_index']}: {s['parts_done']}/{s['planned_parts']} parts")
    print("\nOPEN SLOTS in the next days:")
    for idx, t in schedule.open_long_slots(now):
        print(f"  slot {idx}: {t:%a %Y-%m-%d %H:%M} UTC")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Hey Darky story bot")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="fill the next open weekly slot (one episode + its Shorts)")
    b.add_argument("--force", action="store_true", help="look two weeks ahead instead of the usual lead window")
    sub.add_parser("publish-queue", help="post what is due (Instagram)")
    sub.add_parser("schedule", help="print the slots, the stories and what is open")
    args = parser.parse_args(argv)
    if args.command == "build":
        return run_build(args.force)
    return run_publish_queue() if args.command == "publish-queue" else run_schedule()


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
