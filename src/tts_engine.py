"""
Text-to-speech: Edge TTS (free, unlimited, online) primary,
Piper (free, offline) fallback if Edge TTS is unreachable/rate-limited.
Long scripts are chunked under TTS_CHUNK_CHAR_LIMIT and concatenated via ffmpeg.
"""
import asyncio
import logging
import re
import shutil
import subprocess
import textwrap
import time
from pathlib import Path

from src.config import (
    EDGE_TTS_VOICE,
    PIPER_CONFIG_URL,
    PIPER_FALLBACK_MODEL,
    PIPER_MODEL_DIR,
    PIPER_MODEL_URL,
    TEMP_DIR,
    TTS_CHUNK_CHAR_LIMIT,
)

log = logging.getLogger(__name__)


def clean_for_speech(text: str) -> str:
    """Remove characters that break SSML or get read aloud ("asterisk", "hash"):
    markup symbols are dropped, '&' becomes 'and', stray angle brackets vanish,
    whitespace is collapsed."""
    text = str(text or "")
    text = text.replace("&", " and ")
    text = re.sub(r"[<>*_#`~^|\\]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _chunk_text(text: str, limit: int) -> list[str]:
    return textwrap.wrap(
        text, width=limit, break_long_words=False, break_on_hyphens=False
    )


async def _edge_tts_save(
    text: str, out_path: Path, voice: str, *, rate: str = "+0%", pitch: str = "+0Hz"
) -> None:
    """rate/pitch are real edge_tts.Communicate() parameters (confirmed
    against the library's own source — e.g. rate="-8%", pitch="-5Hz" for a
    slightly slower, deeper read), used for the story-mode narrator's
    "deep, ominous narrator" voice (see STORY_NARRATOR_RATE/PITCH in
    config.py). `rate` is the more reliably-effective of the two across
    edge-tts versions — some reports note `pitch` having reduced effect in
    certain releases — so don't rely on pitch alone for the "deep voice"
    effect; rate is doing most of the real work."""
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


EDGE_ATTEMPTS = 3   # Edge TTS is a free websocket service: transient failures are normal


def _synthesize_edge_tts(
    text: str, out_path: Path, voice: str, *, rate: str = "+0%", pitch: str = "+0Hz"
) -> bool:
    """Retries each chunk (2 s, 4 s backoff) before giving up: one transient
    websocket error must not cost a beat its voice. Chunk files are unique per
    output and deleted before writing, so a stale file from a previous beat can
    never be mistaken for fresh audio."""
    try:
        chunks = _chunk_text(text, TTS_CHUNK_CHAR_LIMIT)
        if not chunks:
            raise ValueError("empty text")
        chunk_paths = []
        for i, chunk in enumerate(chunks):
            chunk_path = TEMP_DIR / f"tts_chunk_{out_path.stem}_{i}.mp3"
            for attempt in range(1, EDGE_ATTEMPTS + 1):
                chunk_path.unlink(missing_ok=True)
                try:
                    asyncio.run(_edge_tts_save(chunk, chunk_path, voice, rate=rate, pitch=pitch))
                    if not chunk_path.exists() or chunk_path.stat().st_size < 512:
                        raise RuntimeError("empty audio")
                    break
                except Exception as e:
                    if attempt == EDGE_ATTEMPTS:
                        raise
                    log.warning("Edge TTS %s chunk %d attempt %d/%d failed (%s) — retrying",
                                out_path.name, i, attempt, EDGE_ATTEMPTS, e)
                    time.sleep(2 * attempt)
            chunk_paths.append(chunk_path)

        if len(chunk_paths) == 1:
            chunk_paths[0].replace(out_path)
        else:
            _concat_audio(chunk_paths, out_path)
            for p in chunk_paths:
                p.unlink(missing_ok=True)
        return True
    except Exception as e:
        log.warning("Edge TTS failed for %s: %s", out_path.name, e)
        return False


def _concat_audio(paths: list[Path], out_path: Path) -> None:
    list_file = TEMP_DIR / "tts_concat_list.txt"
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in paths))
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(out_path),
        ],
        check=True, capture_output=True,
    )


def _ensure_piper_model() -> tuple[Path, Path]:
    import requests

    PIPER_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = PIPER_MODEL_DIR / f"{PIPER_FALLBACK_MODEL}.onnx"
    config_path = PIPER_MODEL_DIR / f"{PIPER_FALLBACK_MODEL}.onnx.json"
    if not model_path.exists():
        resp = requests.get(PIPER_MODEL_URL, timeout=120)
        resp.raise_for_status()
        model_path.write_bytes(resp.content)
    if not config_path.exists():
        resp = requests.get(PIPER_CONFIG_URL, timeout=60)
        resp.raise_for_status()
        config_path.write_bytes(resp.content)
    return model_path, config_path


def _synthesize_piper(text: str, out_path: Path) -> bool:
    if shutil.which("piper") is None:
        log.warning("Piper fallback unavailable (the `piper` command is not installed)")
        return False
    try:
        model_path, config_path = _ensure_piper_model()
        wav_path = out_path.with_suffix(".wav")
        proc = subprocess.run(
            [
                "piper", "--model", str(model_path), "--config", str(config_path),
                "--output_file", str(wav_path),
            ],
            input=text.encode("utf-8"), capture_output=True, check=True,
        )
        if not wav_path.exists() or wav_path.stat().st_size < 512:
            raise RuntimeError("Piper produced empty output")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_path), str(out_path)],
            check=True, capture_output=True,
        )
        return True
    except Exception as e:
        log.error("Piper fallback failed: %s", e)
        return False


def synthesize_voiceover(
    text: str, out_name: str, voice: str | None = None,
    *, rate: str = "+0%", pitch: str = "+0Hz",
) -> Path:
    """Returns path to the generated mp3. Raises if both engines fail.

    `voice` lets callers pick a specific Edge TTS voice (e.g. a particular
    character's voice in story mode — see src/character_voices.py); default
    is EDGE_TTS_VOICE.
    `rate`/`pitch` adjust delivery speed/tone (e.g. a deeper, slower
    narrator read — see STORY_NARRATOR_RATE/PITCH in config.py); default is
    no adjustment.

    NOTE for story mode: Piper (the offline fallback) is a single fixed
    voice with no per-call voice OR rate/pitch selection — if Edge TTS is
    down and this falls back to Piper, every character will sound
    identical and the narrator won't get its deeper read until Edge TTS is
    reachable again. That's a real limitation worth knowing about before
    assuming "fallback kicked in" means multi-voice/narrator-tone still
    works.
    """
    voice = voice or EDGE_TTS_VOICE
    text = clean_for_speech(text)
    out_path = TEMP_DIR / out_name
    if _synthesize_edge_tts(text, out_path, voice, rate=rate, pitch=pitch):
        return out_path
    log.warning(
        "Falling back to Piper offline TTS (single voice — no per-character "
        "voice distinction while on this fallback)"
    )
    if _synthesize_piper(text, out_path):
        return out_path
    raise RuntimeError("Both Edge TTS and Piper failed to synthesize voiceover")


def get_audio_duration_sec(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())
