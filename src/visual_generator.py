"""
Generates scene visuals (free, no paid APIs):
  1. Pollinations AI (unlimited, free, no key) — primary
  2. Pexels API (free, key optional via PEXELS_API_KEY) — fallback
  3. Pixabay API (free, key optional via PIXABAY_API_KEY) — fallback
"""
import logging
import os
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import (
    HF_IMAGE_MODEL,
    PEXELS_SEARCH_URL,
    PIXABAY_IMAGE_URL,
    POLLINATIONS_BASE,
    POLLINATIONS_SLEEP_SEC,
    REQUEST_TIMEOUT_SEC,
    SCENES_DIR,
)

log = logging.getLogger(__name__)


def _download(url: str, dest: Path, headers: dict | None = None) -> bool:
    try:
        resp = requests.get(url, headers=headers or {}, timeout=REQUEST_TIMEOUT_SEC)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return dest.stat().st_size > 1024  # reject near-empty/error responses
    except Exception as e:
        log.info("Download failed for %s: %s", url, e)
        return False


def _pollinations(prompt: str, dest: Path, width: int, height: int) -> bool:
    encoded = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded}?width={width}&height={height}&nologo=true"
    ok = _download(url, dest)
    time.sleep(POLLINATIONS_SLEEP_SEC)  # respect ~5 req/s rate limit
    return ok


def _huggingface(prompt: str, dest: Path, width: int, height: int) -> bool:
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        return False
    try:
        resp = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={
                "inputs": prompt,
                "parameters": {"width": width, "height": height},
            },
            timeout=60,  # cold-start model loading can be slow on free tier
        )
        if resp.status_code == 503:
            # Model is loading on HF's shared free inference infra — not
            # worth a long retry loop here, just fall through to the next
            # free source rather than blocking scene generation on it.
            log.info("HuggingFace model still loading (503) — skipping to next fallback")
            return False
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type:
            log.info("HuggingFace returned non-image response (%s)", content_type)
            return False
        dest.write_bytes(resp.content)
        return dest.stat().st_size > 1024
    except Exception as e:
        log.info("HuggingFace fallback failed: %s", e)
        return False


def _pexels_keywords(visual_prompt: str) -> str:
    # Strip the boilerplate styling language, keep the semantic core for search.
    junk = {
        "cinematic", "8k", "photorealistic", "teal-orange", "grading", "dramatic",
        "rim", "light", "high", "contrast", "mysterious", "dark", "background",
    }
    words = [w.strip(",.") for w in visual_prompt.lower().split()]
    kept = [w for w in words if w not in junk]
    return " ".join(kept[:6]) or visual_prompt[:40]


def _pexels(visual_prompt: str, dest: Path) -> bool:
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return False
    try:
        resp = requests.get(
            PEXELS_SEARCH_URL,
            headers={"Authorization": api_key},
            params={"query": _pexels_keywords(visual_prompt), "per_page": 1},
            timeout=REQUEST_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if not photos:
            return False
        img_url = photos[0]["src"]["large2x"]
        return _download(img_url, dest)
    except Exception as e:
        log.info("Pexels fallback failed: %s", e)
        return False


def _pixabay(visual_prompt: str, dest: Path) -> bool:
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        return False
    try:
        resp = requests.get(
            PIXABAY_IMAGE_URL,
            params={
                "key": api_key,
                "q": _pexels_keywords(visual_prompt),
                "image_type": "photo",
                "orientation": "horizontal",
                "per_page": 3,
            },
            timeout=REQUEST_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if not hits:
            return False
        return _download(hits[0]["largeImageURL"], dest)
    except Exception as e:
        log.info("Pixabay fallback failed: %s", e)
        return False


def generate_scene_image(
    visual_prompt: str, scene_number: int, width: int = 1920, height: int = 1080
) -> Path:
    """Try Pollinations, then HuggingFace, then Pexels, then Pixabay. Raises if all fail."""
    dest = SCENES_DIR / f"scene{scene_number}.jpg"
    if _pollinations(visual_prompt, dest, width, height):
        return dest
    log.warning("Pollinations failed for scene %s, trying HuggingFace", scene_number)
    if _huggingface(visual_prompt, dest, width, height):
        return dest
    log.warning("HuggingFace failed for scene %s, trying Pexels", scene_number)
    if _pexels(visual_prompt, dest):
        return dest
    log.warning("Pexels failed for scene %s, trying Pixabay", scene_number)
    if _pixabay(visual_prompt, dest):
        return dest
    raise RuntimeError(f"All visual sources failed for scene {scene_number}")


def generate_all_scene_images(scenes: list[dict]) -> list[Path]:
    paths = []
    for scene in scenes:
        try:
            path = generate_scene_image(
                scene["visual_prompt"], scene["scene_number"]
            )
            paths.append(path)
        except Exception as e:
            log.error("Scene %s image generation failed entirely: %s", scene.get("scene_number"), e)
            paths.append(None)
    return paths


def generate_thumbnail(word: str, width: int = 1280, height: int = 720) -> Path:
    prompt = (
        f"Clickable YouTube thumbnail, word '{word.upper()}' huge gold 3D letters "
        "centered, human shadow silhouette interacting touching the letters with "
        "hand, mysterious dark background, dramatic rim light, high contrast, 8K, "
        "photorealistic, text readable at small size"
    )
    dest = SCENES_DIR / f"thumbnail_{word}.jpg"
    if _pollinations(prompt, dest, width, height):
        return dest
    if _huggingface(prompt, dest, width, height):
        return dest
    if _pexels(prompt, dest):
        return dest
    if _pixabay(prompt, dest):
        return dest
    raise RuntimeError(f"All visual sources failed for thumbnail of '{word}'")
