"""
Assembles the final cinematic video from scene images + per-scene voiceover +
captions:
  - Ken Burns zoom per scene (ffmpeg zoompan), sized to that scene's REAL
    voiceover duration (not an arbitrary LLM duration guess) so visuals stay
    in sync with narration all the way through the video
  - optional teal-orange LUT colour grade (ffmpeg lut3d, if .cube file present)
  - optional whoosh SFX at each scene boundary (if assets/sfx/*.mp3 present)
  - ASS captions burned in
  - background music ducked under narration
Every optional enhancement (LUT, music, SFX) degrades gracefully if the
asset file is missing, so a bare-bones video still gets produced.
"""
import logging
import random
import subprocess
from pathlib import Path

from src.config import CRF, DEFAULT_LUT, FPS, MUSIC_DIR, SFX_DIR, TEMP_DIR
from src.kinetic_typography import build_overlay_filter_complex

log = logging.getLogger(__name__)


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("ffmpeg command failed: %s\nSTDERR: %s", " ".join(cmd), result.stderr[-2000:])
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")


def _ken_burns_clip(
    image_path: Path,
    duration_sec: float,
    out_path: Path,
    width: int,
    height: int,
    *,
    word: str | None = None,
    scene_index: int = 0,
    typography_style: str | None = None,
) -> None:
    """Ken Burns zoom on the background image. If `word` is given, also
    composites an independently-moving kinetic-typography word layer on top
    (see src/kinetic_typography.py for how/why) — this is what gives the
    "parallax" feel: the photo zooms at its own rate while the word layer
    drifts at a different, unrelated rate.

    If `word` is None, falls back to a plain Ken Burns clip with no overlay
    (used e.g. for quick/degraded-mode rendering where kinetic typography
    isn't wanted).
    """
    if word:
        filter_complex = build_overlay_filter_complex(
            word, duration_sec, width, height, scene_index, style=typography_style
        )
        _run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(duration_sec),
            "-pix_fmt", "yuv420p", str(out_path),
        ])
        return

    zoom_expr = "if(lte(zoom,1.0),1.5,max(1.5-0.0008*on,1))"
    frames = max(int(duration_sec * FPS), 1)
    _run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path),
        "-vf",
        f"scale={width * 2}:{height * 2},"
        f"zoompan=z='{zoom_expr}':d={frames}:s={width}x{height}:fps={FPS}",
        "-t", str(duration_sec),
        "-pix_fmt", "yuv420p", str(out_path),
    ])


def _mux_scene_audio(video_only_path: Path, audio_path: Path, out_path: Path) -> None:
    """Mux one scene's own real voiceover onto its matching Ken Burns clip.
    -shortest guards against sub-frame rounding drift between the two."""
    _run([
        "ffmpeg", "-y", "-i", str(video_only_path), "-i", str(audio_path),
        "-c:v", "libx264", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0", "-shortest", str(out_path),
    ])


def build_scene_clips(
    scenes: list[dict],
    scene_image_paths: list[Path],
    scene_audio_paths: list[Path],
    scene_durations: list[float],
    width: int,
    height: int,
    *,
    word: str | None = None,
) -> list[Path]:
    """Builds one audio+video clip per scene, each sized to that scene's real
    voiceover duration, so narration and visuals stay aligned throughout.
    If `word` is given, each scene also gets a kinetic-typography word
    overlay (style rotates per scene index — see kinetic_typography.py)."""
    clip_paths = []
    for i, (scene, img_path, audio_path, duration) in enumerate(
        zip(scenes, scene_image_paths, scene_audio_paths, scene_durations)
    ):
        if img_path is None:
            raise RuntimeError(f"Missing image for scene {scene.get('scene_number')}")
        scene_num = scene["scene_number"]
        video_only = TEMP_DIR / f"clip_{scene_num}_video.mp4"
        _ken_burns_clip(img_path, duration, video_only, width, height, word=word, scene_index=i)

        with_audio = TEMP_DIR / f"clip_{scene_num}_final.mp4"
        _mux_scene_audio(video_only, audio_path, with_audio)
        clip_paths.append(with_audio)
    return clip_paths


def _concat_clips(clip_paths: list[Path], out_path: Path) -> None:
    """Concatenates clips that all share matching codecs/params (as produced
    by build_scene_clips) via the fast stream-copy concat demuxer."""
    list_file = TEMP_DIR / "clip_concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy", str(out_path),
    ])


def _apply_lut(in_path: Path, out_path: Path, lut_path: Path) -> bool:
    if not lut_path.exists():
        log.info("No LUT found at %s — skipping colour grade", lut_path)
        return False
    try:
        _run([
            "ffmpeg", "-y", "-i", str(in_path),
            "-vf", f"lut3d='{lut_path}'",
            "-c:a", "copy", str(out_path),
        ])
        return True
    except Exception as e:
        log.warning("LUT application failed (%s); continuing ungraded", e)
        return False


def _burn_captions(in_path: Path, ass_path: Path, out_path: Path) -> None:
    _run([
        "ffmpeg", "-y", "-i", str(in_path),
        "-vf", f"ass={ass_path}",
        "-c:a", "copy", str(out_path),
    ])


def _pick_sfx_track() -> Path | None:
    tracks = list(SFX_DIR.glob("*.mp3")) + list(SFX_DIR.glob("*.wav"))
    return random.choice(tracks) if tracks else None


def _add_scene_transition_sfx(
    in_path: Path, out_path: Path, transition_timestamps: list[float]
) -> None:
    """Overlays a short whoosh/pop SFX at each scene-boundary timestamp,
    mixed under the existing audio. Skips silently if no SFX assets exist
    or if there's only one scene (no transitions to mark)."""
    sfx = _pick_sfx_track()
    if sfx is None or not transition_timestamps:
        log.info("No SFX assets or no transitions — skipping scene-change SFX")
        in_path.rename(out_path) if in_path != out_path else None
        return
    try:
        # Build one delayed+volume-reduced copy of the SFX per transition,
        # then mix them all under the original audio track.
        filter_parts = []
        input_args = ["-i", str(in_path)]
        for i, ts in enumerate(transition_timestamps):
            input_args += ["-i", str(sfx)]
            delay_ms = int(ts * 1000)
            filter_parts.append(
                f"[{i + 1}:a]volume=0.35,adelay={delay_ms}|{delay_ms}[sfx{i}]"
            )
        sfx_labels = "".join(f"[sfx{i}]" for i in range(len(transition_timestamps)))
        filter_complex = (
            ";".join(filter_parts)
            + f";[0:a]{sfx_labels}amix=inputs={len(transition_timestamps) + 1}:"
            "duration=first:dropout_transition=2[aout]"
        )
        _run([
            "ffmpeg", "-y", *input_args,
            "-filter_complex", filter_complex,
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", str(out_path),
        ])
    except Exception as e:
        log.warning("Scene-transition SFX mixing failed (%s); shipping without SFX", e)
        in_path.rename(out_path)


def _pick_music_track() -> Path | None:
    tracks = list(MUSIC_DIR.glob("*.mp3"))
    return random.choice(tracks) if tracks else None


def _add_ducked_music(video_path: Path, out_path: Path) -> None:
    music = _pick_music_track()
    if music is None:
        log.info("No background music assets found — skipping music bed")
        video_path.rename(out_path)
        return
    try:
        # sidechaincompress ducks music under narration automatically.
        _run([
            "ffmpeg", "-y", "-i", str(video_path), "-stream_loop", "-1", "-i", str(music),
            "-filter_complex",
            "[1:a]volume=0.25[music];"
            "[0:a][music]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=300[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=2,loudnorm[aout]",
            "-map", "0:v:0", "-map", "[aout]",
            "-c:v", "copy", "-shortest", str(out_path),
        ])
    except Exception as e:
        log.warning("Music mixing failed (%s); shipping without music bed", e)
        video_path.rename(out_path)


def build_long_video(
    scenes: list[dict],
    scene_image_paths: list[Path],
    scene_audio_paths: list[Path],
    scene_durations: list[float],
    ass_captions_path: Path,
    word: str,
    output_dir: Path,
    width: int,
    height: int,
) -> Path:
    """Full pipeline: per-scene Ken Burns+audio (real durations) -> concat ->
    LUT -> scene-change SFX -> captions -> music."""
    clip_paths = build_scene_clips(
        scenes, scene_image_paths, scene_audio_paths, scene_durations, width, height,
        word=word,
    )

    concatenated = TEMP_DIR / "concatenated.mp4"
    _concat_clips(clip_paths, concatenated)

    graded = TEMP_DIR / "graded.mp4"
    if not _apply_lut(concatenated, graded, DEFAULT_LUT):
        graded = concatenated

    # Scene-change transition timestamps = cumulative sum of durations,
    # excluding the very last boundary (end of video, nothing to mark there).
    cumulative = 0.0
    transition_timestamps = []
    for d in scene_durations[:-1]:
        cumulative += d
        transition_timestamps.append(cumulative)

    with_sfx = TEMP_DIR / "with_sfx.mp4"
    _add_scene_transition_sfx(graded, with_sfx, transition_timestamps)

    captioned = TEMP_DIR / "captioned.mp4"
    _burn_captions(with_sfx, ass_captions_path, captioned)

    final_path = output_dir / f"{word}_long.mp4"
    _add_ducked_music(captioned, final_path)

    # Re-encode final output to target CRF/pix_fmt for upload compatibility.
    encoded_final = output_dir / f"{word}_long_final.mp4"
    _run([
        "ffmpeg", "-y", "-i", str(final_path),
        "-c:v", "libx264", "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(encoded_final),
    ])
    return encoded_final
