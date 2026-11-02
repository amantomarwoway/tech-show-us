"""
Facebook Page publishing (Graph API) for the Hey Darky channel:
  * long story  -> Page video, resumable upload (graph-video.facebook.com)
  * Short       -> Page Reel (3-phase video_reels flow)

AUDIENCE TARGETING — what is and isn't possible (verified in Meta's docs):
Facebook is the ONLY platform in this project with an official organic-audience
control: Page posts accept `feed_targeting` (a PREFERRED audience — people
outside it are merely less likely to see the post) and `targeting` (a hard
visibility restriction), both supporting `locales` and `geo_locations`.
This module applies English-locale targeting to every post. The locale KEYS are
resolved live from Meta's own `adlocale` search (never hard-coded), and if
targeting can't be resolved or the API rejects it, the post is published
WITHOUT targeting rather than lost. Note: Meta's "Audience Optimization for
Posts" must be enabled in the Page's settings for feed_targeting to apply.
(YouTube and Instagram expose no organic targeting API at all — see README.)

Every public function returns the new video id, or None on failure, and NEVER
raises: a Facebook problem must never undo a successful YouTube publish.
"""
import json
import logging
import os
import time
from pathlib import Path

import requests

from src.config import (
    FB_ACCESS_TOKEN_ENV,
    FB_HARD_TARGETING,
    FB_PAGE_ID_ENV,
    FB_TARGET_COUNTRIES,
    FB_TARGET_LOCALE_QUERY,
    GRAPH_API_VERSION,
)

log = logging.getLogger(__name__)

GRAPH = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
GRAPH_VIDEO = f"https://graph-video.facebook.com/{GRAPH_API_VERSION}"
_RATE_LIMIT_CODES = {4, 17, 32, 613}
_locale_cache: list[int] | None = None


def is_configured() -> bool:
    return bool(os.environ.get(FB_PAGE_ID_ENV) and os.environ.get(FB_ACCESS_TOKEN_ENV))


def _creds() -> tuple[str, str]:
    return os.environ[FB_PAGE_ID_ENV], os.environ[FB_ACCESS_TOKEN_ENV]


def _call(method: str, url: str, *, retries: int = 3, timeout: int = 180, **kwargs) -> dict | None:
    """One Graph call with backoff on rate limits / 5xx. Returns parsed JSON or
    None; the Graph error body is logged so a bad token/permission is obvious."""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.request(method, url, timeout=timeout, **kwargs)
        except requests.RequestException as e:
            log.warning("Facebook request error (%s): %s", url, e)
            if attempt == retries:
                return None
            time.sleep(15 * attempt)
            continue
        try:
            body = resp.json()
        except ValueError:
            body = {}
        err = body.get("error") if isinstance(body, dict) else None
        if resp.status_code < 400 and not err:
            return body
        code = (err or {}).get("code")
        if (code in _RATE_LIMIT_CODES or resp.status_code >= 500) and attempt < retries:
            wait = 60 * attempt
            log.warning("Facebook %s (code=%s) — backing off %ds (attempt %d/%d)", resp.status_code, code, wait, attempt, retries)
            time.sleep(wait)
            continue
        log.error("Facebook API error %s for %s: %s", resp.status_code, url.split("?")[0], (err or body))
        return None
    return None


def resolve_english_locales() -> list[int]:
    """English-locale keys from Meta's own targeting search (type=adlocale)."""
    global _locale_cache
    if _locale_cache is not None:
        return _locale_cache
    _, token = _creds()
    body = _call("GET", f"{GRAPH}/search",
                 params={"type": "adlocale", "q": FB_TARGET_LOCALE_QUERY, "limit": 50, "access_token": token},
                 retries=2, timeout=30)
    keys = []
    for row in (body or {}).get("data", []):
        if str(row.get("name", "")).lower().startswith("english") and row.get("key") is not None:
            try:
                keys.append(int(row["key"]))
            except (TypeError, ValueError):
                pass
    _locale_cache = sorted(set(keys))
    if not _locale_cache:
        log.warning("Could not resolve English locale keys — posts will be published without audience targeting")
    return _locale_cache


def build_targeting() -> dict:
    """Extra POST params: {} (no targeting) or feed_targeting [+ targeting]."""
    locales = resolve_english_locales()
    if not locales:
        return {}
    spec = {"locales": locales}
    if FB_TARGET_COUNTRIES:
        spec["geo_locations"] = {"countries": list(FB_TARGET_COUNTRIES)}
    out = {"feed_targeting": json.dumps(spec)}
    if FB_HARD_TARGETING:
        out["targeting"] = json.dumps(spec)
    return out


def _with_targeting_fallback(url: str, data: dict) -> dict | None:
    """Try with audience targeting; if Graph rejects it, retry without."""
    targeting = build_targeting()
    if targeting:
        resp = _call("POST", url, data={**data, **targeting})
        if resp is not None:
            return resp
        log.warning("Facebook rejected audience targeting — retrying this post without it")
    return _call("POST", url, data=data)


def publish_long_video(path: Path, title: str, description: str, *, published: bool = True) -> str | None:
    """Resumable upload: start -> transfer chunks (server dictates the byte
    ranges) -> finish. published=False leaves it as an unpublished draft
    (used by REVIEW_MODE)."""
    if not is_configured():
        log.info("Facebook not configured (FB_PAGE_ID / FB_ACCESS_TOKEN) — skipping")
        return None
    page, token = _creds()
    path = Path(path)
    size = path.stat().st_size
    url = f"{GRAPH_VIDEO}/{page}/videos"
    start = _call("POST", url, data={"upload_phase": "start", "file_size": size, "access_token": token})
    if not start or "upload_session_id" not in start:
        return None
    session, video_id = start["upload_session_id"], start.get("video_id")
    s_off, e_off = int(start["start_offset"]), int(start["end_offset"])
    with open(path, "rb") as f:
        for _ in range(5000):                       # hard stop: never loop forever on a misbehaving server
            if s_off == e_off:
                break
            f.seek(s_off)
            chunk = f.read(e_off - s_off)
            resp = _call(
                "POST", url, timeout=600,
                data={"upload_phase": "transfer", "start_offset": s_off,
                      "upload_session_id": session, "access_token": token},
                files={"video_file_chunk": ("chunk.bin", chunk, "application/octet-stream")},
            )
            if not resp:
                return None
            new_s, new_e = int(resp["start_offset"]), int(resp["end_offset"])
            if new_s == s_off and new_e == e_off:
                log.error("Facebook upload made no progress at offset %d — aborting", s_off)
                return None
            s_off, e_off = new_s, new_e
        else:
            log.error("Facebook upload exceeded the chunk limit — aborting")
            return None
    fin = _with_targeting_fallback(url, {
        "upload_phase": "finish", "upload_session_id": session, "access_token": token,
        "title": title, "description": description, "published": "true" if published else "false",
    })
    if not fin:
        return None
    log.info("Facebook long video %s (%s)", video_id, "published" if published else "unpublished draft")
    return str(video_id)


def publish_reel(path: Path, description: str, *, published: bool = True) -> str | None:
    """Page Reel: start -> upload binary to the returned upload_url -> finish."""
    if not is_configured():
        log.info("Facebook not configured (FB_PAGE_ID / FB_ACCESS_TOKEN) — skipping")
        return None
    page, token = _creds()
    path = Path(path)
    size = path.stat().st_size
    url = f"{GRAPH}/{page}/video_reels"
    start = _call("POST", url, data={"upload_phase": "start", "access_token": token})
    if not start or not start.get("video_id") or not start.get("upload_url"):
        return None
    video_id = str(start["video_id"])
    # Read the Short (a few MB) into memory so a retried request re-sends the WHOLE
    # body; a file handle would already be at EOF on the second attempt.
    up = _call("POST", start["upload_url"], timeout=600, data=path.read_bytes(),
               headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)})
    if not up:
        return None
    fin = _with_targeting_fallback(url, {
        "upload_phase": "finish", "video_id": video_id, "access_token": token,
        "video_state": "PUBLISHED" if published else "DRAFT", "description": description,
    })
    if not fin:
        return None
    log.info("Facebook Reel %s (%s)", video_id, "published" if published else "draft")
    return video_id
