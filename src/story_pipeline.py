"""
Story mode asset + video pipeline for the Hey Darky channel:

  write_story()  ->  voices per character  ->  per-beat TTS (+ dramatic pauses)
  -> per-beat word alignment  ->  one Western-styled image per beat
  -> speaker-aware captions  ->  video  ->  scene-matched BGM + exact SFX mix

prepare_story_assets() does everything that is shared by the long video AND
the Shorts (story, voices, audio, alignment) exactly once; render_long_video()
turns those assets into the 16:9 video; src/story_shorts.py reuses the same
assets for the vertical Shorts, so no beat is ever synthesized twice.

ROBUSTNESS (a 90-minute CI run must not die for one bad beat):
  * a beat whose voice-over cannot be synthesized is DROPPED (a story with one
    short beat missing still plays; a crashed run publishes nothing);
  * a beat whose image fails reuses the neighbouring beat's image.
Nothing is uploaded here — publishing lives in main_story.py.
"""
import json
import logging
import re
import subprocess
from pathlib import Path

from src.aligner import align_words, offset_words
from src.audio_mixer import build_audio_timeline, mix_story_audio
from src.caption_builder import build_story_captions
from src.character_voices import assign_voices, voice_for_beat
from src.config import (
    LONG_HEIGHT,
    LONG_WIDTH,
    OUTPUT_DIR,
    STORY_NARRATOR_PITCH,
    STORY_NARRATOR_RATE,
    STORY_VISUAL_STYLE_SUFFIX,
    TEMP_DIR,
)
from src.story_writer import write_story
from src.tts_engine import get_audio_duration_sec, synthesize_voiceover
from src.video_builder import build_video
from src.visual_generator import generate_scene_image

log = logging.getLogger(__name__)


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(title).lower()).strip("-")
    return slug[:60] or "story"


MAX_IMAGE_PROMPT_CHARS = 880   # visual_generator caps URLs at 900; leave headroom


def styled_prompt(prompt: str) -> str:
    """Every image prompt gets the Western-culture suffix (config), so scenes show
    American/Western people, places and objects no matter what the model wrote.
    The suffix goes at the END (the Pexels/Pixabay fallbacks search on the first
    few words only) — so a long description is trimmed at a word boundary to make
    room for it; the suffix itself is never the part that gets cut."""
    room = MAX_IMAGE_PROMPT_CHARS - len(STORY_VISUAL_STYLE_SUFFIX)
    text = str(prompt).strip().rstrip(".,; ")
    if len(text) > room:
        text = text[:room].rsplit(" ", 1)[0].rstrip(".,; ")
    return text + STORY_VISUAL_STYLE_SUFFIX


def _to_exact_wav(audio_path: Path, pad_seconds: float = 0.0) -> Path:
    """Decode a beat's voice-over to 48 kHz stereo PCM WAV, optionally appending
    `pad_seconds` of digital silence (a deliberate dramatic pause).

    WHY: ffprobe reports an MP3's CONTAINER duration, but the decoded audio is
    ~38 ms shorter per file (encoder delay/padding). Across 40 beats that is a
    ~1.5 s drift between the audio and everything timed from it (video frames,
    captions, sound-effect timestamps). A WAV's duration is exactly
    samples / sample-rate, so all timing is derived from these files."""
    out = audio_path.with_name(audio_path.stem + "_exact.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(audio_path)]
    if pad_seconds > 0:
        cmd += ["-af", f"apad=pad_dur={pad_seconds:.3f}"]
    cmd += ["-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(out)]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out


def _synthesize_items(beats: list[dict], voice_map: dict) -> list[dict]:
    """One dict per beat that could be voiced: {beat, audio, duration, words}.
    Narration gets the deeper/slower narrator read (STORY_NARRATOR_RATE/PITCH);
    character dialogue stays at normal rate/pitch so it sounds like a
    different person, not just a different name."""
    items = []
    for idx, beat in enumerate(beats, start=1):
        voice = voice_for_beat(beat, voice_map)
        is_narration = beat.get("type") == "narration" or beat.get("speaker") == "narrator"
        try:
            kwargs = {"rate": STORY_NARRATOR_RATE, "pitch": STORY_NARRATOR_PITCH} if is_narration else {}
            audio = synthesize_voiceover(beat["text"], f"story_beat_{idx}.mp3", voice=voice, **kwargs)
            words = align_words(audio, beat["text"])  # aligned on the original, before padding
            pause = float(beat.get("pause_after_sec") or 0)
            audio = _to_exact_wav(audio, pause if pause >= 2.0 else 0.0)
            duration = get_audio_duration_sec(audio)
        except Exception as e:
            log.error("Beat %s (%r...) could not be voiced — dropping it: %s", idx, str(beat.get("text"))[:40], e)
            continue
        items.append({"beat": beat, "audio": audio, "duration": duration, "words": words})
    return items


def attach_images(items: list[dict], width: int, height: int, tag: str = "") -> list[Path]:
    """One image per item from that beat's own visual_description (Western-
    styled). A failed image reuses the nearest successful neighbour; only if
    EVERY image fails does this raise."""
    paths: list[Path | None] = []
    for k, item in enumerate(items, start=1):
        try:
            paths.append(generate_scene_image(
                styled_prompt(item["beat"]["visual_description"]), f"{tag}{k}", width, height))
        except Exception as e:
            log.warning("Image for beat %s failed (%s) — will reuse a neighbouring image", k, e)
            paths.append(None)
    if all(p is None for p in paths):
        raise RuntimeError("All beat image generation failed — aborting story build")
    last = next(p for p in paths if p is not None)  # leading gaps use the first good image
    for i, p in enumerate(paths):
        if p is None:
            paths[i] = last
        else:
            last = p
    return paths


def prepare_story_assets(story: dict) -> dict:
    """Voices + audio + alignment for every beat (shared by long video and
    Shorts). Returns {"story", "voice_map", "slug", "items"} where each item
    also carries its 16:9 image under "image"."""
    voice_map = assign_voices(story["characters"])
    log.info("Synthesizing %d beats...", len(story["beats"]))
    items = _synthesize_items(story["beats"], voice_map)
    if not items:
        raise RuntimeError("No beat could be voiced — aborting story build")
    if len(items) < len(story["beats"]):
        log.warning("%d of %d beats were dropped (voice-over failures)", len(story["beats"]) - len(items), len(story["beats"]))
    log.info("Generating %d Western-styled beat images...", len(items))
    images = attach_images(items, LONG_WIDTH, LONG_HEIGHT, tag="")
    for item, image in zip(items, images):
        item["image"] = image
    return {"story": story, "voice_map": voice_map, "slug": slugify(story.get("title") or story.get("title_long")), "items": items}


def render_video(items: list[dict], images: list[Path], width: int, height: int, slug: str,
                 *, is_short: bool, ass_name: str) -> tuple[Path, dict]:
    """Shared renderer for the long video and the Shorts: captions -> Ken Burns
    video with the voice-over -> BGM + SFX mix. Returns (final_path, mix_report)."""
    beats = [it["beat"] for it in items]
    durations = [it["duration"] for it in items]
    local_words = [it["words"] for it in items]

    cumulative, beats_with_words = 0.0, []
    for it in items:
        beats_with_words.append((it["beat"], offset_words(it["words"], cumulative)))
        cumulative += it["duration"]
    ass_path = TEMP_DIR / ass_name
    build_story_captions(beats_with_words, ass_path, theme="karaoke", is_short=is_short)

    video = build_video(
        images, [it["audio"] for it in items], durations, ass_path,
        OUTPUT_DIR, width, height, output_slug=slug,
    )
    timeline = build_audio_timeline(beats, durations, local_words)
    mixed = video.with_name(f"{slug}_mixed.mp4")
    report = mix_story_audio(video, mixed, timeline)
    log.info("Audio layering for %s: %s", slug, report)
    return mixed, report


def render_long_video(assets: dict) -> Path:
    items = assets["items"]
    final, _ = render_video(
        items, [it["image"] for it in items], LONG_WIDTH, LONG_HEIGHT, assets["slug"],
        is_short=False, ass_name="story_captions.ass",
    )
    return final


def build_story_video(genre: str, premise: str = "", research: dict | None = None,
                      pillar: str | None = None) -> dict:
    """Genre -> finished 15-20 minute video file. Returns
    {"story", "voice_map", "long_video_path", "assets"}; `assets` is what
    src/story_shorts.py needs to cut the Shorts without re-synthesizing."""
    log.info("Writing %s story...", genre)
    story = write_story(genre, premise, pillar=pillar, research=research)
    log.info("Story: %r | pillar=%s | %d characters | %d beats",
             story.get("title"), story.get("pillar"), len(story["characters"]), len(story["beats"]))
    assets = prepare_story_assets(story)
    long_video_path = render_long_video(assets)
    (OUTPUT_DIR / f"{assets['slug']}_story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"story": story, "voice_map": assets["voice_map"],
            "long_video_path": long_video_path, "assets": assets}
