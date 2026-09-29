"""
Weekly orchestration: pick word -> research -> script -> per-scene visuals +
voiceover + alignment -> build long video -> thumbnail -> SEO -> upload long
-> derive 2 shorts (reusing per-scene audio) -> upload shorts (scheduled) ->
persist to DB.

Voiceover and alignment are done PER SCENE (not once for the whole script)
so each scene's Ken Burns visual clip can be sized to that scene's real
narration length — this keeps captions and visuals in sync all the way
through the video instead of drifting apart from an arbitrary LLM duration
guess. See src/video_builder.py and src/aligner.py for the mechanics.

Every stage is wrapped so a failure logs and either falls back or aborts the
run cleanly (never crashes uncaught) — a failed long video skips short
derivation and upload for that run.
"""
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from src.aligner import align_words, offset_words
from src.caption_builder import build_ass_captions
from src.config import (
    LONG_HEIGHT,
    LONG_WIDTH,
    OUTPUT_DIR,
    REVIEW_MODE,
    SHORT_PUBLISH_DELAY_HOURS,
    TEMP_DIR,
)
from src.database import init_db, mark_word_used
from src.etymology_researcher import research_word
from src.script_writer import write_script
from src.seo_optimizer import build_long_metadata, build_short_metadata
from src.short_deriver import derive_shorts
from src.story_engine import check_loop_closure, pick_best_segments_for_shorts
from src.thumbnail_builder import build_thumbnail
from src.tts_engine import synthesize_voiceover, get_audio_duration_sec
from src.video_builder import build_long_video
from src.visual_generator import generate_all_scene_images
from src.word_picker import pick_word
from src.youtube_uploader import (
    compute_publish_at,
    next_publish_slot,
    upload_thumbnail,
    upload_video,
)

LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "bot.log"),
    ],
)
log = logging.getLogger("main")


_step_start_time = None
_pipeline_start_time = None


def step(name: str):
    """Logs a step header and the elapsed time since the previous step —
    useful for spotting which stage is eating your GitHub Actions minutes
    budget (see README's 'known limitations' on timing)."""
    global _step_start_time, _pipeline_start_time

    now = time.monotonic()
    if _pipeline_start_time is None:
        _pipeline_start_time = now
    if _step_start_time is not None:
        log.info("(previous step took %.1fs)", now - _step_start_time)
    _step_start_time = now
    log.info("=== STEP: %s === [elapsed: %.1fs]", name, now - _pipeline_start_time)


def _build_scene_audio_and_alignment(scenes: list[dict], word: str) -> list[dict]:
    """For each scene: synthesize its own voiceover, measure its real
    duration, and align its words locally (timestamps starting at 0.0).
    Mutates and returns `scenes` with `_audio_path`, `_duration`,
    `_local_words` attached to each scene dict. Raises only if a scene's
    voiceover synthesis fails outright (both TTS engines down) — a single
    bad alignment falls back to proportional timing rather than aborting.
    """
    for scene in scenes:
        scene_num = scene["scene_number"]
        narration = scene["narration"]

        audio_path = synthesize_voiceover(narration, f"{word}_scene{scene_num}_voice.mp3")
        duration = get_audio_duration_sec(audio_path)
        local_words = align_words(audio_path, narration)

        scene["_audio_path"] = audio_path
        scene["_duration"] = duration
        scene["_local_words"] = local_words

    return scenes


def _build_global_caption_timeline(scenes: list[dict]) -> list[dict]:
    """Stitches each scene's local (0.0-based) word alignment into one
    global timeline, offset by cumulative real scene durations, for
    captioning the full concatenated long video."""
    global_words = []
    cumulative = 0.0
    for scene in scenes:
        global_words.extend(offset_words(scene["_local_words"], cumulative))
        cumulative += scene["_duration"]
    return global_words


def run_weekly_pipeline() -> None:
    init_db()

    step("Pick word")
    picked = pick_word()
    word = picked["word"]
    log.info("Selected word: %s (angle: %s)", word, picked.get("angle"))

    step("Research etymology")
    research = research_word(word)

    step("Write script")
    script = write_script(word, research, angle=picked.get("angle", ""))
    check_loop_closure(script)  # logs a warning only, does not block

    scenes = script["scenes"]

    step("Generate scene visuals")
    scene_image_paths = generate_all_scene_images(scenes)
    if all(p is None for p in scene_image_paths):
        raise RuntimeError("All scene image generation failed — aborting run")

    step("Synthesize per-scene voiceover + alignment")
    scenes = _build_scene_audio_and_alignment(scenes, word)
    scene_audio_paths = [s["_audio_path"] for s in scenes]
    scene_durations = [s["_duration"] for s in scenes]

    step("Build global caption timeline")
    global_words = _build_global_caption_timeline(scenes)
    ass_path = TEMP_DIR / f"{word}_captions.ass"
    build_ass_captions(global_words, ass_path, theme="karaoke", is_short=False)

    step("Build long cinematic video")
    long_video_path = build_long_video(
        scenes, scene_image_paths, scene_audio_paths, scene_durations,
        ass_path, word, OUTPUT_DIR, LONG_WIDTH, LONG_HEIGHT,
    )

    step("Build thumbnail")
    thumbnail_path = build_thumbnail(word, hook_snippet=script.get("hook", "")[:30])

    step("Build SEO metadata (long)")
    long_meta = build_long_metadata(script, word)

    # REVIEW_MODE (default ON — see src/config.py) uploads everything PRIVATE
    # with no schedule, so a human checks it in YouTube Studio before it ever
    # goes public. This is the single most important safety valve for a
    # fully-automated channel: bad output stays invisible until a person
    # says otherwise. Only flip REVIEW_MODE off (repo variable, not secret)
    # once you've watched several runs end-to-end and trust the pipeline.
    #
    # When REVIEW_MODE is off, the long video is scheduled (not published
    # immediately) to the next fixed weekly slot (Tue/Fri 01:00 UTC by
    # default — see PUBLISH_WEEKDAYS/PUBLISH_HOUR_UTC in config.py) so "same
    # day, same time" holds regardless of how long THIS run's render took.
    # Shorts are scheduled relative to that same slot, not to "now" — two
    # runs that take 40 minutes vs 4 hours still produce identical publish
    # times for viewers.
    slot_time = next_publish_slot(datetime.now(timezone.utc))

    step("Upload long video")
    if REVIEW_MODE:
        long_video_id = upload_video(
            long_video_path,
            title=long_meta["title"],
            description=long_meta["description"],
            tags=long_meta["tags"],
            privacy_status="private",
        )
        log.info(
            "REVIEW_MODE is on: long video uploaded PRIVATE, no schedule set. "
            "Review it in YouTube Studio and publish manually. "
            "https://studio.youtube.com/video/%s/edit", long_video_id,
        )
    else:
        long_video_id = upload_video(
            long_video_path,
            title=long_meta["title"],
            description=long_meta["description"],
            tags=long_meta["tags"],
            publish_at_iso=compute_publish_at(slot_time, 0),
        )
        log.info(
            "Long video scheduled for %s: video_id=%s",
            slot_time.isoformat(), long_video_id,
        )
    upload_thumbnail(long_video_id, thumbnail_path)

    step("Derive shorts (reusing per-scene audio/alignment)")
    short_paths = derive_shorts(script, word)
    best_short_scenes = pick_best_segments_for_shorts(script, n=2)

    short_ids = [None, None]
    for i, (short_path, scene, delay_hours) in enumerate(
        zip(short_paths, best_short_scenes, SHORT_PUBLISH_DELAY_HOURS)
    ):
        if short_path is None:
            log.warning("Short %d was not built successfully — skipping upload", i + 1)
            continue
        step(f"Upload short {i + 1}")
        short_meta = build_short_metadata(scene, word, long_video_id, i + 1)
        try:
            if REVIEW_MODE:
                short_id = upload_video(
                    short_path,
                    title=short_meta["title"],
                    description=short_meta["description"],
                    tags=short_meta["tags"],
                    privacy_status="private",
                )
            else:
                short_id = upload_video(
                    short_path,
                    title=short_meta["title"],
                    description=short_meta["description"],
                    tags=short_meta["tags"],
                    publish_at_iso=compute_publish_at(slot_time, delay_hours),
                )
            short_ids[i] = short_id
        except Exception as e:
            log.error("Failed to upload short %d: %s", i + 1, e)

    step("Persist to database")
    # Strip non-serializable Path objects before persisting the script JSON.
    for scene in scenes:
        scene.pop("_audio_path", None)
        scene.pop("_local_words", None)
    mark_word_used(
        word,
        long_video_id=long_video_id,
        short_id_1=short_ids[0],
        short_id_2=short_ids[1],
        title=long_meta["title"],
        script=script,
    )

    log.info(
        "Run complete in %.1fs. word=%s long_video_id=%s short_ids=%s",
        time.monotonic() - _pipeline_start_time, word, long_video_id, short_ids,
    )


if __name__ == "__main__":
    try:
        run_weekly_pipeline()
    except Exception as e:
        log.exception("Weekly pipeline run failed: %s", e)
        sys.exit(1)
