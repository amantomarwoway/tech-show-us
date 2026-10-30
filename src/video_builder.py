"""
Assembles a story video from one image + one voice-over per beat.

PIPELINE (each stage encodes as little as possible):
  1. one silent Ken Burns clip per beat — slow centered zoom (alternating in/out),
     sized by CUMULATIVE frame boundaries: clip i covers
     round(end_i * FPS) - round(start_i * FPS) frames, so the total frame count
     matches the total voice-over to within ONE frame no matter how many beats.
     (Rounding each clip separately drifts: 40 clips x up to 1/60 s adds up.)
  2. clips joined with the fast stream-copy concat demuxer
  3. every beat's voice-over joined into ONE master track (encoded once)
  4. a single final pass: optional LUT colour grade + burned-in ASS captions,
     video encoded once, audio encoded once
Captions, the audio-mix timeline and the video all derive from the same real
voice-over durations, so everything stays in sync end to end.
Background music / sound effects are layered afterwards by src/audio_mixer.py.
"""
import logging
import subprocess
from pathlib import Path

from src.config import CLIP_PRESET, CRF, DEFAULT_LUT, FINAL_PRESET, FPS, TEMP_DIR

log = logging.getLogger(__name__)
ZOOM_MAX = 1.5


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("ffmpeg failed: %s\nSTDERR: %s", " ".join(cmd), result.stderr[-2000:])
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")


def _filter_path(path: Path) -> str:
    """Escape a file path for use inside an ffmpeg filter argument."""
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def frame_counts(durations: list[float]) -> list[int]:
    """Frames per clip from CUMULATIVE boundaries (see module docstring); every
    clip gets at least one frame."""
    counts, elapsed, prev = [], 0.0, 0
    for d in durations:
        elapsed += d
        edge = round(elapsed * FPS)
        counts.append(max(edge - prev, 1))
        prev += counts[-1]
    return counts


def _ken_burns_clip(image_path: Path, frames: int, out_path: Path, width: int, height: int, index: int) -> None:
    """Silent clip: slow zoom centred on the image, zooming OUT on even beats and
    IN on odd beats (variety without ever panning off-centre)."""
    if index % 2 == 0:
        zoom = f"max({ZOOM_MAX}-{ZOOM_MAX - 1}*on/{frames},1)"
    else:
        zoom = f"min(1+{ZOOM_MAX - 1}*on/{frames},{ZOOM_MAX})"
    vf = (
        f"scale={width * 2}:{height * 2},"
        f"zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS}"
    )
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(image_path), "-vf", vf,
        "-frames:v", str(frames), "-c:v", "libx264", "-preset", CLIP_PRESET, "-crf", str(CRF),
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-an", str(out_path),
    ])


def _concat_clips(clip_paths: list[Path], out_path: Path) -> None:
    list_file = TEMP_DIR / "clip_concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
    _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
          "-i", str(list_file), "-c", "copy", str(out_path)])


def _concat_audio(audio_paths: list[Path], out_path: Path) -> None:
    """One master voice track: every beat decoded, resampled to 48 kHz stereo and
    joined, losslessly (FLAC) so the only lossy audio encode is the final one."""
    inputs, labels = [], []
    for i, p in enumerate(audio_paths):
        inputs += ["-i", str(p)]
        labels.append(f"[a{i}]")
    chains = [f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]" for i in range(len(audio_paths))]
    chains.append("".join(labels) + f"concat=n={len(audio_paths)}:v=0:a=1[aout]")
    _run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains),
          "-map", "[aout]", "-c:a", "flac", str(out_path)])


def build_video(
    image_paths: list[Path],
    audio_paths: list[Path],
    durations: list[float],
    ass_path: Path,
    output_dir: Path,
    width: int,
    height: int,
    *,
    output_slug: str,
) -> Path:
    """Returns the finished (captioned, voice-only) video; BGM/SFX come later."""
    if not (len(image_paths) == len(audio_paths) == len(durations)):
        raise ValueError("image_paths, audio_paths and durations must be the same length")
    if any(p is None for p in image_paths) or any(p is None for p in audio_paths):
        raise RuntimeError("Missing image or audio for a beat")

    clips = []
    for i, (img, frames) in enumerate(zip(image_paths, frame_counts(durations))):
        clip = TEMP_DIR / f"clip_{output_slug}_{i}.mp4"
        _ken_burns_clip(img, frames, clip, width, height, i)
        clips.append(clip)

    video_only = TEMP_DIR / f"{output_slug}_silent.mp4"
    _concat_clips(clips, video_only)
    master_audio = TEMP_DIR / f"{output_slug}_voice.flac"
    _concat_audio(audio_paths, master_audio)

    vf = f"ass='{_filter_path(ass_path)}'"
    if DEFAULT_LUT.exists():
        vf = f"lut3d='{_filter_path(DEFAULT_LUT)}'," + vf
    else:
        log.info("No LUT at %s — skipping colour grade", DEFAULT_LUT)

    final = output_dir / f"{output_slug}_video.mp4"
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video_only), "-i", str(master_audio),
        "-vf", vf, "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", FINAL_PRESET, "-crf", str(CRF), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(final),
    ])
    for p in clips + [video_only, master_audio]:
        p.unlink(missing_ok=True)   # keep the runner's disk small on a 40-beat story
    return final
