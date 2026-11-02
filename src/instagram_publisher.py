"""
Instagram Reels publishing (Instagram Graph API, content publishing) — used for
the DAILY SHORT ONLY, by design.

Flow (verified against Meta's docs):
  1. POST /{ig-user-id}/media  media_type=REELS, upload_type=resumable, caption
       -> {id: <container>, uri: <rupload url>}
  2. POST the video bytes to that uri (headers: Authorization: OAuth <token>,
       offset: 0, file_size: <bytes>) — no public video URL needed.
  3. Poll GET /{container}?fields=status_code until FINISHED (ERROR/EXPIRED = fail)
  4. POST /{ig-user-id}/media_publish  creation_id=<container>

Instagram's API has NO audience-targeting parameter and no scheduling for
organic Reels; reach is driven by the English caption/hashtags and by who
engages. The publish is immediate. Never raises (returns the media id or None).
"""
import logging
import os
import time
from pathlib import Path

import requests

from src.config import (
    FB_ACCESS_TOKEN_ENV,
    GRAPH_API_VERSION,
    IG_CAPTION_LIMIT,
    IG_USER_ID_ENV,
)

log = logging.getLogger(__name__)
GRAPH = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
POLL_INTERVAL_SEC = 10
POLL_TIMEOUT_SEC = 900


def is_configured() -> bool:
    return bool(os.environ.get(IG_USER_ID_ENV) and os.environ.get(FB_ACCESS_TOKEN_ENV))


def _json(resp: requests.Response) -> dict:
    try:
        body = resp.json()
    except ValueError:
        body = {}
    if resp.status_code >= 400 or (isinstance(body, dict) and body.get("error")):
        log.error("Instagram API error %s: %s", resp.status_code, body.get("error", body) if isinstance(body, dict) else body)
        return {}
    return body


def publish_reel(path: Path, caption: str, *, share_to_feed: bool = True) -> str | None:
    if not is_configured():
        log.info("Instagram not configured (IG_USER_ID / FB_ACCESS_TOKEN) — skipping")
        return None
    ig_id, token = os.environ[IG_USER_ID_ENV], os.environ[FB_ACCESS_TOKEN_ENV]
    path = Path(path)
    size = path.stat().st_size
    caption = caption[:IG_CAPTION_LIMIT]
    try:
        container = _json(requests.post(
            f"{GRAPH}/{ig_id}/media", timeout=60,
            data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                  "share_to_feed": "true" if share_to_feed else "false", "access_token": token},
        ))
        if not container.get("id") or not container.get("uri"):
            return None
        with open(path, "rb") as f:
            up = requests.post(
                container["uri"], data=f, timeout=600,
                params={"access_token": token},
                headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)},
            )
        if up.status_code >= 400:
            log.error("Instagram upload failed %s: %s", up.status_code, up.text[:300])
            return None

        deadline = time.monotonic() + POLL_TIMEOUT_SEC
        while True:
            status = _json(requests.get(
                f"{GRAPH}/{container['id']}", timeout=30,
                params={"fields": "status_code,status", "access_token": token},
            ))
            code = status.get("status_code")
            if code == "FINISHED":
                break
            if code in ("ERROR", "EXPIRED") or not status:
                log.error("Instagram container %s ended as %s: %s", container["id"], code, status.get("status"))
                return None
            if time.monotonic() > deadline:
                log.error("Instagram container %s still %s after %ds — giving up", container["id"], code, POLL_TIMEOUT_SEC)
                return None
            time.sleep(POLL_INTERVAL_SEC)

        published = _json(requests.post(
            f"{GRAPH}/{ig_id}/media_publish", timeout=60,
            data={"creation_id": container["id"], "access_token": token},
        ))
        media_id = published.get("id")
        if media_id:
            log.info("Instagram Reel published: %s", media_id)
        return str(media_id) if media_id else None
    except requests.RequestException as e:
        log.error("Instagram publish failed: %s", e)
        return None
