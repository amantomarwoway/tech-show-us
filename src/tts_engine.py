"""
Text-to-speech: Edge TTS (free, unlimited, online) primary,
Piper (free, offline) fallback if Edge TTS is unreachable/rate-limited.
Long scripts are chunked under TTS_CHUNK_CHAR_LIMIT and concatenated via ffmpeg.
"""
import asyncio
import logging
import subprocess
import textwrap
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


def _chunk_text(text: str, limit: int) -> list[str]:
    return textwrap.wrap(
        text, width=limit, break_long_words=False, break_on_hyphens=False
    )


async def _edge_tts_save(text: str, out_path: Path, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def _synthesize_edge_tts(text: str, out_path: Path) -> bool:
    try:
        chunks = _chunk_text(text, TTS_CHUNK_CHAR_LIMIT)
        chunk_paths = []
        for i, chunk in enumerate(chunks):
            chunk_path = TEMP_DIR / f"tts_chunk_{i}.mp3"
            asyncio.run(_edge_tts_save(chunk, chunk_path, EDGE_TTS_VOICE))
            if not chunk_path.exists() or chunk_path.stat().st_size < 512:
                raise RuntimeError(f"Edge TTS produced empty output for chunk {i}")
            chunk_paths.append(chunk_path)

        if len(chunk_paths) == 1:
            chunk_paths[0].rename(out_path)
        else:
            _concat_audio(chunk_paths, out_path)
        return True
    except Exception as e:
        log.warning("Edge TTS failed: %s", e)
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


def synthesize_voiceover(text: str, out_name: str) -> Path:
    """Returns path to the generated mp3. Raises if both engines fail."""
    out_path = TEMP_DIR / out_name
    if _synthesize_edge_tts(text, out_path):
        return out_path
    log.warning("Falling back to Piper offline TTS")
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
