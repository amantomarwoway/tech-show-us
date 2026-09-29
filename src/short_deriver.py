"""
Derives 2 vertical Shorts (1080x1920, 20-35s) from the best-scoring scenes of
the long video, per story_engine's scoring. Reuses each scene's own
already-synthesized voiceover + word alignment (computed once in main.py
during the long-video build) rather than re-synthesizing audio or guessing
at timestamps — this also fixes a real bug where the old implementation
sliced the first N words of the FULL script's timeline regardless of which
scene was actually picked, misaligning captions on any Short built from a
scene other than the first.
"""
import logging
from pathlib import Path

from src.caption_builder import build_ass_captions
from src.config import DEFAULT_LUT, OUTPUT_DIR, SHORT_HEIGHT, SHORT_MAX_SEC, SHORT_WIDTH, TEMP_DIR
from src.story_engine import pick_best_segments_for_shorts
from src.video_builder import _apply_lut, _burn_captions, _mux_scene_audio, _ken_burns_clip, _run
from src.visual_generator import generate_scene_image

log = logging.getLogger(__name__)


SENTENCE_END = (".", "!", "?", "\u2026")
MIN_SENTENCE_CUT_SEC = 12.0  # don't cut so early that the Short feels empty
TAIL_PAD_SEC = 0.25


def _sentence_safe_cut(words: list[dict], max_sec: float) -> float | None:
    """End time (sec) of the last complete sentence finishing within max_sec,
    or None if no sentence boundary falls in the usable window."""
    best = None
    for w in words:
        token = w["word"].rstrip("\"'\u201d\u2019)")
        if w["end"] <= max_sec and token.endswith(SENTENCE_END):
            best = w["end"]
    if best is not None and best >= MIN_SENTENCE_CUT_SEC:
        return best
    return None


def _trim_audio(audio_path: Path, cut_sec: float, out_path: Path) -> Path:
    """Trim narration to cut_sec with a short fade-out so it never pops."""
    fade_start = max(cut_sec - 0.3, 0.0)
    _run([
        "ffmpeg", "-y", "-i", str(audio_path), "-t", f"{cut_sec:.3f}",
        "-af", f"afade=t=out:st={fade_start:.3f}:d=0.3", str(out_path),
    ])
    return out_path


def plan_short_cut(words: list[dict], real_duration: float) -> tuple[float, bool]:
    """Decide where a Short's narration ends. Returns (cut_sec, needs_trim).

    Under the limit -> keep everything. Over it -> end on the last full
    sentence inside the limit (a Short that stops mid-sentence hurts
    retention); hard-cut at the limit only if no sentence boundary exists."""
    if real_duration <= SHORT_MAX_SEC:
        return real_duration, False
    safe = _sentence_safe_cut(words, SHORT_MAX_SEC)
    return (safe if safe is not None else float(SHORT_MAX_SEC)), True


def _build_single_short(scene: dict, word: str, index: int) -> Path:
    """`scene` must carry the fields main.py attaches during the long-video
    build: `_audio_path`, `_duration`, `_local_words` (word timestamps local
    to that scene's own audio, i.e. starting at 0.0)."""
    audio_path = scene.get("_audio_path")
    local_words = scene.get("_local_words", [])
    real_duration = scene.get("_duration")
    if audio_path is None or real_duration is None:
        raise RuntimeError(
            f"Scene {scene.get('scene_number')} is missing precomputed audio/duration "
            "— main.py must attach these before calling derive_shorts()"
        )

    cut_sec, needs_trim = plan_short_cut(local_words, real_duration)
    if needs_trim:
        audio_path = _trim_audio(audio_path, cut_sec, TEMP_DIR / f"short_{index}_trimmed.mp3")
        local_words = [w for w in local_words if w["end"] <= cut_sec + 0.05]
        log.info(
            "Short %d: narration %.1fs trimmed to %.1fs at a sentence boundary",
            index, real_duration, cut_sec,
        )
    duration_for_visual = cut_sec + TAIL_PAD_SEC

    # Regenerate a vertical-oriented image for this scene (the long-video
    # image is landscape and wouldn't crop cleanly to 9:16).
    img_path = generate_scene_image(
        scene["visual_prompt"],
        scene_number=f"short{index}_{scene['scene_number']}",
        width=SHORT_WIDTH,
        height=SHORT_HEIGHT,
    )

    ass_path = TEMP_DIR / f"short_{index}_captions.ass"
    build_ass_captions(local_words, ass_path, theme="pop", is_short=True)

    video_only = TEMP_DIR / f"short_{index}_video_only.mp4"
    # Shorts always get scene_index=0's style (a fixed, punchy style rather
    # than whatever position this scene happened to occupy in the long
    # video) — a Short is watched in isolation, so "which style looks best
    # standalone" matters more than continuity with the long-form cut.
    _ken_burns_clip(
        img_path, duration_for_visual, video_only, SHORT_WIDTH, SHORT_HEIGHT,
        word=word, scene_index=0,
    )

    with_audio = TEMP_DIR / f"short_{index}_with_audio.mp4"
    _mux_scene_audio(video_only, audio_path, with_audio)

    graded = TEMP_DIR / f"short_{index}_graded.mp4"
    if not _apply_lut(with_audio, graded, DEFAULT_LUT):
        graded = with_audio

    captioned = TEMP_DIR / f"short_{index}_captioned.mp4"
    _burn_captions(graded, ass_path, captioned)

    final_path = OUTPUT_DIR / f"{word}_short_{index}.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(captioned),
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(final_path),
    ])
    return final_path


def derive_shorts(script: dict, word: str) -> list[Path]:
    """Requires that every scene in script['scenes'] already carries
    `_audio_path`, `_duration`, `_local_words` (set by main.py)."""
    segments = pick_best_segments_for_shorts(script, n=2)
    out_paths = []
    for i, scene in enumerate(segments, start=1):
        try:
            path = _build_single_short(scene, word, i)
            out_paths.append(path)
        except Exception as e:
            log.error("Failed to build short %d for '%s': %s", i, word, e)
            out_paths.append(None)
    return out_paths
