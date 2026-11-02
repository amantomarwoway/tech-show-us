"""
Safe background-music (BGM) and sound-effect (SFX) fetching for story mode.

SOURCE REALITY CHECK (verified against Pixabay's own API documentation, not
assumed): Pixabay's official API only searches IMAGES and VIDEOS — there is no
music/audio endpoint, so `media_type=music&duration_min=60` style requests do
not exist. Both BGM and SFX therefore come from Freesound, using the same
API key, separated by duration filters:
  - BGM: duration:[60 TO 600]   (long enough to be a real music/ambience bed)
  - SFX: duration:[0.5 TO 10.0] (quick effects only — never a 30-minute clip)
and BOTH restricted to `license:"Creative Commons 0"` so every asset is
free to use commercially with no attribution requirement.

FALLBACK CHAIN (so a missing key / outage / empty search never breaks a run):
  BGM: audio_cache  ->  Freesound  ->  local assets/music  ->  synthesized drone
  SFX: audio_cache  ->  Freesound  ->  local assets/sfx (name match)  ->  skip

API-SAFETY GUARDRAILS (covered by tests/test_story_wiring.py):
  * Local cache (audio_cache/): a keyword that was downloaded once is reused
    forever — the same asset never costs a second API hit.
  * Strict spacing: at least AUDIO_REQUEST_MIN_GAP_SEC (2s) between ANY two
    Freesound requests (search OR download).
  * HTTP 429: linear backoff — wait AUDIO_429_COOLDOWN_SEC * attempt (60s,
    120s, ...) before retrying, up to AUDIO_MAX_RETRIES attempts, then give
    up on that asset (the pipeline continues without it).
  * In-run memo of keywords that found nothing, so a missing sound is not
    searched repeatedly within one run.

LICENSING NOTE worth knowing (found while verifying the API, not something to
panic about): the SOUNDS filtered here are CC0, which is free for commercial
use. Freesound's separate API terms, however, describe API access as free for
non-commercial use — if this channel is monetized, check Freesound's API terms
(or email them) about commercial API use. The pipeline is built so this is
low-stakes: the cache means each sound is fetched once, and you can also
pre-download CC0 sounds by hand from freesound.org into assets/sfx and
assets/music — those local files are used automatically as fallbacks.
"""
import hashlib
import logging
import os
import random
import re
import subprocess
import time
from pathlib import Path

import requests

from src.config import (
    AUDIO_429_COOLDOWN_SEC,
    AUDIO_CACHE_DIR,
    AUDIO_MAX_RETRIES,
    AUDIO_REQUEST_MIN_GAP_SEC,
    FREESOUND_API_KEY_ENV,
    FREESOUND_BGM_DURATION_FILTER,
    FREESOUND_LICENSE_FILTER,
    FREESOUND_SEARCH_URL,
    FREESOUND_SFX_DURATION_FILTER,
    MUSIC_DIR,
    REQUEST_TIMEOUT_SEC,
    SFX_DIR,
)

log = logging.getLogger(__name__)

_last_request_at = 0.0
_misses: set[tuple[str, str]] = set()
_warned_no_key = False


def _slug(keyword: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", keyword.lower()).strip("_")[:60] or "sound"


def _throttle() -> None:
    """Sleep so that at least AUDIO_REQUEST_MIN_GAP_SEC separates this
    request from the previous one."""
    global _last_request_at
    wait = AUDIO_REQUEST_MIN_GAP_SEC - (time.monotonic() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def _auth_headers() -> dict | None:
    key = os.environ.get(FREESOUND_API_KEY_ENV)
    if not key:
        return None
    return {"Authorization": f"Token {key}"}


def _request(url: str, *, params: dict | None = None, headers: dict | None = None):
    """Throttled GET with 429 linear backoff. Returns a Response, or None if
    the request ultimately failed (never raises)."""
    for attempt in range(1, AUDIO_MAX_RETRIES + 1):
        _throttle()
        try:
            resp = requests.get(
                url, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SEC
            )
        except requests.RequestException as e:
            log.warning("Freesound request failed (%s): %s", url, e)
            return None
        if resp.status_code == 429:
            if attempt == AUDIO_MAX_RETRIES:
                break  # out of retries — don't burn a final cool-down just to give up
            wait = AUDIO_429_COOLDOWN_SEC * attempt
            log.warning(
                "Freesound HTTP 429 (attempt %d/%d) — cooling down %ds before retrying",
                attempt, AUDIO_MAX_RETRIES, wait,
            )
            time.sleep(wait)
            continue
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            log.warning("Freesound HTTP error for %s: %s", url, e)
            return None
        return resp
    log.warning("Freesound still rate-limiting after %d attempts — skipping this asset", AUDIO_MAX_RETRIES)
    return None


def _cache_path(kind: str, keyword: str) -> Path:
    return AUDIO_CACHE_DIR / f"{kind}_{_slug(keyword)}.mp3"


def _cached(kind: str, keyword: str) -> Path | None:
    path = _cache_path(kind, keyword)
    if path.exists() and path.stat().st_size > 1024:
        log.info("Audio cache hit: %s", path.name)
        return path
    return None


def _best_result(results: list[dict]) -> dict | None:
    """Highest-rated result that actually has an HQ mp3 preview. Ties keep
    Freesound's own relevance order (sorted() is stable)."""
    usable = [
        r for r in results
        if (r.get("previews") or {}).get("preview-hq-mp3")
    ]
    if not usable:
        return None
    return sorted(usable, key=lambda r: r.get("avg_rating") or 0, reverse=True)[0]


def _fetch_from_freesound(kind: str, keyword: str, duration_filter: str) -> Path | None:
    global _warned_no_key
    headers = _auth_headers()
    if headers is None:
        if not _warned_no_key:
            log.warning(
                "%s is not set — skipping Freesound entirely (local assets / "
                "synthesized fallbacks will be used instead).", FREESOUND_API_KEY_ENV,
            )
            _warned_no_key = True
        return None
    if (kind, _slug(keyword)) in _misses:
        return None

    resp = _request(
        FREESOUND_SEARCH_URL,
        params={
            "query": keyword,
            "filter": f"{duration_filter} {FREESOUND_LICENSE_FILTER}",
            "fields": "id,name,duration,previews,avg_rating,num_ratings,license",
            "sort": "score",
            "page_size": 15,
        },
        headers=headers,
    )
    if resp is None:
        return None
    try:
        results = resp.json().get("results", [])
    except ValueError:
        log.warning("Freesound returned non-JSON for %r", keyword)
        return None

    best = _best_result(results)
    if best is None:
        log.info("Freesound: no usable %s result for %r", kind, keyword)
        _misses.add((kind, _slug(keyword)))
        return None

    # Previews require authentication per Freesound's docs, so the download
    # carries the same token header.
    audio = _request(best["previews"]["preview-hq-mp3"], headers=headers)
    if audio is None or len(audio.content) < 1024:
        return None
    dest = _cache_path(kind, keyword)
    dest.write_bytes(audio.content)
    log.info(
        "Freesound: downloaded %s %r -> %s (%.1fs, rating %s)",
        kind, best.get("name"), dest.name, best.get("duration") or 0, best.get("avg_rating"),
    )
    return dest


def _local_music() -> Path | None:
    tracks = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.wav"))
    return random.choice(tracks) if tracks else None


def _local_sfx(keyword: str) -> Path | None:
    words = [w for w in re.split(r"[^a-z0-9]+", keyword.lower()) if len(w) >= 4]
    if not words:
        return None
    for path in list(SFX_DIR.glob("*.mp3")) + list(SFX_DIR.glob("*.wav")):
        if any(w in path.stem.lower() for w in words):
            return path
    return None


def synthesize_drone(keyword: str, duration_sec: int = 90) -> Path | None:
    """Last-resort BGM that needs no network, key, or licence: a dark ambient
    drone built from two low sine waves (a perfect fifth apart), brown noise
    and a slow tremolo, all generated by ffmpeg. Deterministic per keyword
    (the pitch comes from a hash of it) so different moods get different
    drones, and cached so it is generated once. It is a plain atmospheric
    bed, not a composed track — good enough to keep the audio layered when
    nothing better is available, not a replacement for real music."""
    dest = AUDIO_CACHE_DIR / f"bgm_synth_{_slug(keyword)}.mp3"
    if dest.exists() and dest.stat().st_size > 1024:
        return dest
    h = int(hashlib.sha1(keyword.encode("utf-8")).hexdigest(), 16)
    f1 = 40 + (h % 30)  # 40-69 Hz
    f2 = round(f1 * 1.5, 2)
    d = int(duration_sec)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error",
                "-f", "lavfi", "-i", f"sine=frequency={f1}:sample_rate=48000:duration={d}",
                "-f", "lavfi", "-i", f"sine=frequency={f2}:sample_rate=48000:duration={d}",
                "-f", "lavfi", "-i", f"anoisesrc=color=brown:sample_rate=48000:amplitude=0.25:duration={d}",
                "-filter_complex",
                "[0:a]volume=0.5[a];[1:a]volume=0.3[b];[2:a]lowpass=f=400[c];"
                "[a][b][c]amix=inputs=3:normalize=0,tremolo=f=0.12:d=0.5,"
                "lowpass=f=1200,aformat=channel_layouts=stereo[out]",
                "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", str(dest),
            ],
            check=True, capture_output=True, text=True,
        )
    except Exception as e:
        log.warning("Synthesized drone generation failed: %s", e)
        return None
    return dest


def get_bgm(keyword: str) -> Path | None:
    """Background-music bed for a mood keyword. Never raises; returns None
    only if every fallback (including the synthesized drone) failed."""
    keyword = (keyword or "").strip() or "dark ambient drone"
    cached = _cached("bgm", keyword)
    if cached:
        return cached
    fetched = _fetch_from_freesound("bgm", keyword, FREESOUND_BGM_DURATION_FILTER)
    if fetched:
        return fetched
    local = _local_music()
    if local:
        log.info("BGM %r: using local asset %s", keyword, local.name)
        return local
    log.info("BGM %r: falling back to a synthesized ambient drone", keyword)
    return synthesize_drone(keyword)


def get_sfx(keyword: str) -> Path | None:
    """Sound effect for a keyword, or None (the beat simply stays without
    that effect — a missing SFX never substitutes an unrelated sound)."""
    keyword = (keyword or "").strip()
    if not keyword or keyword.lower() == "none":
        return None
    cached = _cached("sfx", keyword)
    if cached:
        return cached
    fetched = _fetch_from_freesound("sfx", keyword, FREESOUND_SFX_DURATION_FILTER)
    if fetched:
        return fetched
    local = _local_sfx(keyword)
    if local:
        log.info("SFX %r: using local asset %s", keyword, local.name)
        return local
    return None
