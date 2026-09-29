"""
Word-level timestamp alignment via faster-whisper (CPU, int8, 'small' model).
Falls back to proportional estimation (even time-per-character) if Whisper
is unavailable or fails, so the pipeline never hard-stops on this step.
"""
import logging
from pathlib import Path

from src.config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL_SIZE
from src.tts_engine import get_audio_duration_sec

log = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        _model = WhisperModel(
            WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE
        )
    return _model


def align_words(audio_path: Path, fallback_text: str) -> list[dict]:
    """Returns [{"word": str, "start": float, "end": float}, ...]."""
    try:
        model = _get_model()
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
        words = []
        for segment in segments:
            for w in segment.words or []:
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
        if words:
            return words
        raise RuntimeError("Whisper returned no word timestamps")
    except Exception as e:
        log.warning("faster-whisper alignment failed (%s); using proportional fallback", e)
        return _proportional_fallback(audio_path, fallback_text)


def _proportional_fallback(audio_path: Path, text: str) -> list[dict]:
    duration = get_audio_duration_sec(audio_path)
    words = text.split()
    if not words:
        return []
    per_word = duration / len(words)
    out = []
    t = 0.0
    for w in words:
        out.append({"word": w, "start": t, "end": t + per_word})
        t += per_word
    return out


def offset_words(words: list[dict], offset_sec: float) -> list[dict]:
    """Shift a local (scene-relative, starting at 0.0) word timeline by a
    fixed offset — used to stitch per-scene alignments into one global
    timeline for the full long-video captions."""
    return [
        {"word": w["word"], "start": w["start"] + offset_sec, "end": w["end"] + offset_sec}
        for w in words
    ]
