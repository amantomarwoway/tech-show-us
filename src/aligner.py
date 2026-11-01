"""
Word-level timestamps for one beat's voice-over (used for karaoke captions and
for placing sound effects on the exact spoken word).

faster-whisper aligns the real audio; if it is unavailable or fails, words are
spread proportionally across the clip's real duration — captions stay roughly
in sync instead of the run failing.
"""
import logging
import subprocess
from pathlib import Path

from src.config import WHISPER_MODEL_SIZE

log = logging.getLogger(__name__)
_model = None


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _proportional_words(text: str, duration: float) -> list[dict]:
    words = text.split()
    if not words:
        return []
    weights = [max(len(w), 2) for w in words]
    total = sum(weights)
    out, t = [], 0.0
    for w, wt in zip(words, weights):
        d = duration * wt / total
        out.append({"word": w, "start": t, "end": t + d})
        t += d
    return out


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _model


def align_words(audio_path: Path, fallback_text: str) -> list[dict]:
    """[{word, start, end}] with times relative to the start of `audio_path`."""
    duration = _duration(Path(audio_path))
    try:
        segments, _ = _get_model().transcribe(str(audio_path), word_timestamps=True, language="en")
        words = [
            {"word": w.word.strip(), "start": float(w.start), "end": float(w.end)}
            for seg in segments for w in (seg.words or []) if w.word.strip()
        ]
        if words:
            script = fallback_text.split()
            if len(script) == len(words):
                # Same word count: keep Whisper's TIMING but the script's own
                # spelling (names like "Garrett" must not be mis-heard on screen).
                words = [{**w, "word": s} for w, s in zip(words, script)]
            return words
        log.warning("Whisper returned no words for %s — using proportional timing", Path(audio_path).name)
    except Exception as e:
        log.warning("Whisper alignment unavailable (%s) — using proportional timing", e)
    return _proportional_words(fallback_text, duration)


def offset_words(words: list[dict], offset: float) -> list[dict]:
    """Shift a beat's local word times onto the global timeline."""
    return [{**w, "start": w["start"] + offset, "end": w["end"] + offset} for w in words]
