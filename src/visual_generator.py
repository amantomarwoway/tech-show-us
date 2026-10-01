"""
Generates scene visuals (free, no paid APIs):
  1. Pollinations AI (free, optional key via POLLINATIONS_API_KEY) — primary
  2. Pexels API (free, key optional via PEXELS_API_KEY) — fallback
  3. Pixabay API (free, key optional via PIXABAY_API_KEY) — fallback

HuggingFace Inference is intentionally NOT in the active chain — see the
_huggingface() docstring below for why, and what to check before
re-enabling it.
"""
import logging
import os
import time
import urllib.parse
from pathlib import Path

import requests

from src.config import (
    HF_IMAGE_MODEL,
    HF_INFERENCE_BASE,
    PEXELS_SEARCH_URL,
    PIXABAY_IMAGE_URL,
    PIXABAY_SLEEP_SEC,
    POLLINATIONS_API_KEY_ENV,
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
    """Uses the current gen.pollinations.ai/image/{prompt} endpoint (the
    legacy image.pollinations.ai/prompt/... host is being deprecated and
    was observed returning 402 Payment Required in production — see the
    TESTED FOOTGUN note on POLLINATIONS_BASE in config.py). Sends an API
    key if POLLINATIONS_API_KEY is set; without one, production logs have
    shown 401 Unauthorized on this host, so a key is effectively required
    now, not just recommended — get one free at enter.pollinations.ai."""
    encoded = urllib.parse.quote(prompt)
    url = f"{POLLINATIONS_BASE}{encoded}?width={width}&height={height}&nologo=true"
    api_key = os.environ.get(POLLINATIONS_API_KEY_ENV)
    if api_key:
        url += f"&key={api_key}"
    ok = _download(url, dest)
    time.sleep(POLLINATIONS_SLEEP_SEC)  # respect Pollinations' rate limit
    return ok


def _huggingface(prompt: str, dest: Path, width: int, height: int) -> bool:
    """DISABLED — not called from generate_scene_image()/generate_thumbnail()
    below. Kept only as a reference implementation.

    TESTED FOOTGUN, already hit TWICE in production: first the legacy
    api-inference.huggingface.co host returned 410 Gone ("no longer
    supported, use router.huggingface.co/hf-inference instead"). After
    switching to that corrected host, it returned 410 Gone AGAIN — this
    time because HF_IMAGE_MODEL (black-forest-labs/FLUX.1-schnell) is not
    currently deployable via ANY of HuggingFace's supported Inference
    Providers at all (confirmed on the model's own HF page: "This model
    cannot be deployed to the HF Inference API"). This isn't a host/URL
    problem the second time — the specific free model this code requests
    simply isn't servable this way anymore.

    Before re-enabling this in the active chain: pick a model you've
    PERSONALLY confirmed works against https://router.huggingface.co/hf-inference
    right now (HuggingFace's supported-providers list changes over time
    and guessing one here, confidently, is exactly how this broke twice).
    """
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        return False
    try:
        resp = requests.post(
            f"{HF_INFERENCE_BASE}{HF_IMAGE_MODEL}",
            headers={"Authorization": f"Bearer {hf_token}"},
            json={
                "inputs": prompt,
                "parameters": {"width": width, "height": height},
            },
            timeout=60,  # cold-start model loading can be slow on free tier
        )
        if resp.status_code == 503:
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
    """NOTE: production logs have shown intermittent 403 Forbidden with a
    PEXELS_API_KEY that is confirmed set — Pexels' own docs distinguish 403
    ("Forbidden" — an access/key problem) from 429 ("Too Many Requests" —
    a rate-limit problem), and their free-tier limit (200/hour) is far
    above what this pipeline calls per run, so this doesn't look like
    ordinary rate limiting. If this keeps failing, verify the key directly
    (e.g. `curl -H "Authorization: $PEXELS_API_KEY" https://api.pexels.com/v1/search?query=cat`)
    outside this pipeline to isolate whether it's the key itself."""
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
    """Pixabay's free tier is rate-limited to 100 requests/60s. This has
    become the pipeline's most reliable source in production (Pollinations
    and Pexels have both failed consistently in recent runs — see README),
    so PIXABAY_SLEEP_SEC paces every call even though a single run's ~9
    calls wouldn't come close to the limit on their own; this matters more
    once the daily CTR optimizer job and a weekly run could plausibly
    overlap, and costs almost nothing to respect up front."""
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
        ok = _download(hits[0]["largeImageURL"], dest)
        time.sleep(PIXABAY_SLEEP_SEC)
        return ok
    except Exception as e:
        log.info("Pixabay fallback failed: %s", e)
        return False


def generate_scene_image(
    visual_prompt: str, scene_number: int, width: int = 1920, height: int = 1080
) -> Path:
    """Try Pollinations, then Pexels, then Pixabay. Raises if all fail.

    HuggingFace is deliberately NOT in this chain — see _huggingface()'s
    docstring above; it's confirmed non-functional for the model this
    pipeline would request, twice over, not just rate-limited."""
    dest = SCENES_DIR / f"scene{scene_number}.jpg"
    if _pollinations(visual_prompt, dest, width, height):
        log.info("Scene %s image: Pollinations succeeded", scene_number)
        return dest
    log.warning("Pollinations failed for scene %s, trying Pexels", scene_number)
    if _pexels(visual_prompt, dest):
        log.info("Scene %s image: Pexels succeeded", scene_number)
        return dest
    log.warning("Pexels failed for scene %s, trying Pixabay", scene_number)
    if _pixabay(visual_prompt, dest):
        log.info("Scene %s image: Pixabay succeeded", scene_number)
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
        log.info("Thumbnail: Pollinations succeeded")
        return dest
    log.warning("Pollinations failed for thumbnail, trying Pexels")
    if _pexels(prompt, dest):
        log.info("Thumbnail: Pexels succeeded")
        return dest
    log.warning("Pexels failed for thumbnail, trying Pixabay")
    if _pixabay(prompt, dest):
        log.info("Thumbnail: Pixabay succeeded")
        return dest
    raise RuntimeError(f"All visual sources failed for thumbnail of '{word}'")
