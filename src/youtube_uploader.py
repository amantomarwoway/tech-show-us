"""
YouTube Data API v3 wrapper: OAuth via a long-lived refresh token (set the
Cloud Console OAuth consent screen to Production to avoid 7-day test-token
expiry), resumable video upload, thumbnail upload, scheduled publishing via
publishAt, and metadata update calls used by the CTR optimizer.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import (
    MIN_LEAD_TIME_HOURS,
    PUBLISH_HOUR_UTC,
    PUBLISH_WEEKDAYS,
    YT_CATEGORY_EDUCATION,
)

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _get_credentials():
    from google.oauth2.credentials import Credentials

    client_id = os.environ["YT_CLIENT_ID"]
    client_secret = os.environ["YT_CLIENT_SECRET"]
    refresh_token = os.environ["YT_REFRESH_TOKEN"]

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )


def _get_youtube_client():
    from googleapiclient.discovery import build

    creds = _get_credentials()
    return build("youtube", "v3", credentials=creds)


def upload_video(
    file_path: Path,
    title: str,
    description: str,
    tags: list[str],
    *,
    privacy_status: str = "public",
    publish_at_iso: str | None = None,
    made_for_kids: bool = False,
    category_id: str = YT_CATEGORY_EDUCATION,
) -> str:
    """Uploads a video, returns its video_id. If publish_at_iso is set, the
    video is uploaded private with a scheduled public release time."""
    from googleapiclient.http import MediaFileUpload

    youtube = _get_youtube_client()

    # AI-generated voice/visuals: disclose it. YouTube requires disclosure for
    # realistic synthetic media and it protects the channel from policy strikes.
    status: dict = {
        "selfDeclaredMadeForKids": made_for_kids,
        "containsSyntheticMedia": True,
    }
    if publish_at_iso:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at_iso
    else:
        status["privacyStatus"] = privacy_status

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": status,
    }

    def _do_upload(request_body: dict) -> str:
        media = MediaFileUpload(
            str(file_path), chunksize=-1, resumable=True, mimetype="video/mp4"
        )
        request = youtube.videos().insert(
            part="snippet,status", body=request_body, media_body=media
        )
        response = None
        while response is None:
            status_progress, response = request.next_chunk()
            if status_progress:
                log.info("Upload progress: %d%%", int(status_progress.progress() * 100))
        return response["id"]

    try:
        video_id = _do_upload(body)
    except Exception as e:
        # If the API rejects the disclosure field, retry once without it rather
        # than losing a multi-hour render over a metadata technicality.
        if "containsSyntheticMedia" in str(e):
            log.warning("API rejected containsSyntheticMedia; retrying without it")
            body["status"].pop("containsSyntheticMedia", None)
            try:
                video_id = _do_upload(body)
            except Exception as e2:
                _handle_api_error(e2)
                raise
        else:
            _handle_api_error(e)
            raise
    log.info("Uploaded video_id=%s title=%r", video_id, title)
    return video_id


def upload_thumbnail(video_id: str, thumbnail_path: Path) -> None:
    from googleapiclient.http import MediaFileUpload

    youtube = _get_youtube_client()
    try:
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
        ).execute()
    except Exception as e:
        _handle_api_error(e)
        raise


def update_video_metadata(
    video_id: str, *, title: str | None = None, description: str | None = None, tags: list[str] | None = None
) -> None:
    youtube = _get_youtube_client()
    try:
        existing = youtube.videos().list(part="snippet", id=video_id).execute()
        items = existing.get("items", [])
        if not items:
            raise RuntimeError(f"Video {video_id} not found for metadata update")
        snippet = items[0]["snippet"]
        if title:
            snippet["title"] = title
        if description:
            snippet["description"] = description
        if tags:
            snippet["tags"] = tags
        youtube.videos().update(part="snippet", body={"id": video_id, "snippet": snippet}).execute()
    except Exception as e:
        _handle_api_error(e)
        raise


def compute_publish_at(base_time_utc: datetime, delay_hours: int) -> str:
    return (base_time_utc + timedelta(hours=delay_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_publish_slot(now_utc: datetime) -> datetime:
    """Next fixed weekly slot (PUBLISH_WEEKDAYS at PUBLISH_HOUR_UTC) that is at
    least MIN_LEAD_TIME_HOURS in the future. Same slot every week regardless of
    how long the render took."""
    earliest = now_utc + timedelta(hours=MIN_LEAD_TIME_HOURS)
    for day_offset in range(0, 8):
        candidate = (earliest + timedelta(days=day_offset)).replace(
            hour=PUBLISH_HOUR_UTC, minute=0, second=0, microsecond=0
        )
        if candidate.weekday() in PUBLISH_WEEKDAYS and candidate >= earliest:
            return candidate
    raise RuntimeError("No publish slot found within 8 days — check PUBLISH_WEEKDAYS")


def _handle_api_error(e: Exception) -> None:
    msg = str(e)
    if "quotaExceeded" in msg or "403" in msg:
        log.error("YouTube API quota exceeded or forbidden: %s", msg)
    elif "401" in msg or "invalid_grant" in msg.lower():
        log.error(
            "YouTube API unauthorized — refresh token may be invalid/expired "
            "(ensure OAuth consent screen is in Production mode): %s", msg,
        )
    else:
        log.error("YouTube API error: %s", msg)
