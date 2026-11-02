"""
One image per beat: Pollinations (AI, free) -> Pexels (stock) -> Pixabay (stock).

PRODUCTION LESSONS built in:
  * Pollinations moved to gen.pollinations.ai; the model must be pinned
    (POLLINATIONS_MODEL, default "flux"). Anonymous access is tried FIRST and the
    API key (Bearer) second — in real runs one of the two worked when the other
    returned 401.
  * Pexels intermittently 403s; Pixabay is the dependable stock fallback and is
    spaced by PIXABAY_SLEEP_SEC to respect its rate limit.
  * The stock fallbacks search on the FIRST few words of the prompt, which is why
    the Western-culture suffix is appended at the END (see story_pipeline).
Every image is cover-cropped to EXACTLY width x height so ffmpeg never sees a
surprise size. Raises only if all three sources fail.
"""
import io
import logging
import os
import random
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image

from src.config import (
    PEXELS_API_KEY_ENV,
    PEXELS_SEARCH_URL,
    PIXABAY_API_KEY_ENV,
    PIXABAY_SEARCH_URL,
    PIXABAY_SLEEP_SEC,
    POLLINATIONS_API_KEY_ENV,
    POLLINATIONS_BASE,
    POLLINATIONS_MODEL,
    POLLINATIONS_SLEEP_SEC,
    POLLINATIONS_TIMEOUT_SEC,
    REQUEST_TIMEOUT_SEC,
    SCENES_DIR,
)

log = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "of", "in", "on", "at", "and", "with", "to", "from", "by", "for", "is", "are", "was",
    "his", "her", "their", "its", "as", "into", "over", "under", "near", "while", "who", "that", "this",
    "very", "cinematic", "photorealistic", "dark", "moody", "lighting", "shot", "close", "wide", "up",
}
MAX_PROMPT_CHARS = 900


def _keywords(prompt: str, n: int = 6) -> str:
    words = [w for w in re.findall(r"[A-Za-z]+", prompt.lower()) if w not in _STOPWORDS and len(w) > 2]
    return " ".join(words[:n]) or "dark night"


def _fit(img: Image.Image, width: int, height: int) -> Image.Image:
    """Cover-crop to exactly width x height."""
    img = img.convert("RGB")
    scale = max(width / img.width, height / img.height)
    img = img.resize((max(int(img.width * scale + 0.5), width), max(int(img.height * scale + 0.5), height)))
    left, top = (img.width - width) // 2, (img.height - height) // 2
    return img.crop((left, top, left + width, top + height))


def _decode(content: bytes) -> Image.Image | None:
    if len(content) < 5_000:
        return None
    try:
        img = Image.open(io.BytesIO(content))
        img.load()
        return img
    except Exception:
        return None


def _pollinations(prompt: str, width: int, height: int) -> Image.Image | None:
    url = f"{POLLINATIONS_BASE}{quote(prompt[:MAX_PROMPT_CHARS], safe='')}"
    params = {"width": width, "height": height, "model": POLLINATIONS_MODEL,
              "nologo": "true", "seed": random.randint(1, 10_000_000)}
    key = os.environ.get(POLLINATIONS_API_KEY_ENV)
    attempts = [("anonymous", {})] + ([("api key", {"Authorization": f"Bearer {key}"})] if key else [])
    for label, headers in attempts:
        time.sleep(POLLINATIONS_SLEEP_SEC)
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=POLLINATIONS_TIMEOUT_SEC)
        except requests.RequestException as e:
            log.warning("Pollinations (%s) request error: %s", label, e)
            continue
        if resp.status_code == 200:
            img = _decode(resp.content)
            if img is not None:
                return img
            log.warning("Pollinations (%s) returned a non-image / tiny response", label)
        elif resp.status_code == 429:
            retry_after = str((getattr(resp, "headers", None) or {}).get("Retry-After", "10"))
            wait = min(int(retry_after) if retry_after.isdigit() else 10, 30)
            log.warning("Pollinations (%s) rate-limited (429) — pausing %ds before the next attempt", label, wait)
            time.sleep(wait)
        else:
            log.warning("Pollinations (%s) HTTP %s", label, resp.status_code)
    return None


def _download(url: str) -> Image.Image | None:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT_SEC * 2)
        return _decode(resp.content) if resp.status_code == 200 else None
    except requests.RequestException as e:
        log.warning("Image download failed: %s", e)
        return None


def _pexels(prompt: str, width: int, height: int) -> Image.Image | None:
    key = os.environ.get(PEXELS_API_KEY_ENV)
    if not key:
        return None
    try:
        resp = requests.get(
            PEXELS_SEARCH_URL, headers={"Authorization": key}, timeout=REQUEST_TIMEOUT_SEC,
            params={"query": _keywords(prompt), "per_page": 15,
                    "orientation": "portrait" if height > width else "landscape"},
        )
        if resp.status_code != 200:
            log.warning("Pexels HTTP %s", resp.status_code)
            return None
        photos = resp.json().get("photos", [])
    except (requests.RequestException, ValueError) as e:
        log.warning("Pexels error: %s", e)
        return None
    random.shuffle(photos)
    for p in photos[:3]:
        img = _download(p.get("src", {}).get("large2x") or p.get("src", {}).get("large", ""))
        if img is not None:
            return img
    return None


def _pixabay(prompt: str, width: int, height: int) -> Image.Image | None:
    key = os.environ.get(PIXABAY_API_KEY_ENV)
    if not key:
        return None
    time.sleep(PIXABAY_SLEEP_SEC)
    try:
        resp = requests.get(
            PIXABAY_SEARCH_URL, timeout=REQUEST_TIMEOUT_SEC,
            params={"key": key, "q": _keywords(prompt), "image_type": "photo", "per_page": 20,
                    "safesearch": "true", "orientation": "vertical" if height > width else "horizontal"},
        )
        if resp.status_code != 200:
            log.warning("Pixabay HTTP %s", resp.status_code)
            return None
        hits = resp.json().get("hits", [])
    except (requests.RequestException, ValueError) as e:
        log.warning("Pixabay error: %s", e)
        return None
    random.shuffle(hits)
    for h in hits[:3]:
        img = _download(h.get("largeImageURL") or h.get("webformatURL", ""))
        if img is not None:
            return img
    return None


def generate_scene_image(
    visual_prompt: str, scene_number, width: int = 1920, height: int = 1080
) -> Path:
    """Returns the path of a width x height JPEG. Raises if all sources fail."""
    dest = SCENES_DIR / f"scene{scene_number}.jpg"
    for name, source in (("Pollinations", _pollinations), ("Pexels", _pexels), ("Pixabay", _pixabay)):
        img = source(visual_prompt, width, height)
        if img is not None:
            _fit(img, width, height).save(dest, "JPEG", quality=92)
            log.info("Image for scene %s from %s", scene_number, name)
            return dest
    raise RuntimeError(f"All image sources failed for scene {scene_number}: {visual_prompt[:80]!r}")
