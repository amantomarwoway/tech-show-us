"""
YouTube uploads (Data API v3, resumable) for the Hey Darky channel.

HARD-WON LESSONS built in:
  * Credentials are built from the refresh token WITHOUT passing scopes=. Passing
    scopes made Google reject the refresh with `invalid_scope` whenever they
    differed from the scopes the token was minted with.
  * `containsSyntheticMedia` (the AI-content disclosure) is always set; if the
    API ever rejects that field the upload is retried once without it.
  * Language: snippet.defaultLanguage AND defaultAudioLanguage are set at upload
    time — YouTube has no organic audience-targeting API, and declaring English is
    the one lever that exists.
  * AUDIT LOCK (documented by Google): videos uploaded through videos.insert by an
    UNVERIFIED API project (created after 28 July 2020) are forced to PRIVATE, and
    cannot be made public by the API or Studio until the project passes YouTube's
    API compliance audit. upload_video() reads the privacy status YouTube actually
    applied and logs a loud error when a requested-public video came back private,
    so a locked project can never be mistaken for a working auto-publisher.
"""
import logging
import os
import re
import time
from pathlib import Path

from src.config import (
    STORY_LANGUAGE,
    STORY_YT_CATEGORY,
    YT_CLIENT_ID_ENV,
    YT_CLIENT_SECRET_ENV,
    YT_REFRESH_TOKEN_ENV,
    YT_TITLE_LIMIT,
    YT_TOKEN_URI,
    YT_UPLOAD_CHUNK_BYTES,
)

log = logging.getLogger(__name__)
_RETRYABLE_STATUS = {500, 502, 503, 504}


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=None,
        refresh_token=os.environ[YT_REFRESH_TOKEN_ENV],
        client_id=os.environ[YT_CLIENT_ID_ENV],
        client_secret=os.environ[YT_CLIENT_SECRET_ENV],
        token_uri=YT_TOKEN_URI,
        # NOTE: deliberately no scopes= (see module docstring).
    )
    creds.refresh(Request())
    return creds


def _get_youtube_client():
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=_get_credentials(), cache_discovery=False)


def _media_upload(path: Path):
    from googleapiclient.http import MediaFileUpload

    return MediaFileUpload(str(path), chunksize=YT_UPLOAD_CHUNK_BYTES, resumable=True, mimetype="video/mp4")


def _http_status(exc: Exception) -> int | None:
    return getattr(getattr(exc, "resp", None), "status", None)


def _run_resumable(request, max_retries: int = 5) -> dict:
    """Drive a resumable upload to completion, retrying transient failures."""
    response, retries = None, 0
    while response is None:
        try:
            _, response = request.next_chunk()
        except Exception as e:  # googleapiclient.errors.HttpError or a network error
            status = _http_status(e)
            transient = status in _RETRYABLE_STATUS or (status is None and isinstance(e, (ConnectionError, TimeoutError, OSError)))
            if not transient or retries >= max_retries:
                raise
            retries += 1
            wait = min(60, 2 ** retries)
            log.warning("YouTube upload chunk failed (%s): retry %d/%d in %ds", status or type(e).__name__, retries, max_retries, wait)
            time.sleep(wait)
    return response


def _clean(text: str, limit: int) -> str:
    return re.sub(r"[<>]", "", str(text or "")).strip()[:limit]


def upload_video(
    file_path: Path,
    title: str,
    description: str,
    tags: list[str],
    *,
    privacy_status: str = "public",
    category_id: str = STORY_YT_CATEGORY,
    language: str = STORY_LANGUAGE,
    made_for_kids: bool = False,
) -> str:
    """Uploads and returns the new video id. Raises on failure."""
    youtube = _get_youtube_client()
    snippet = {
        "title": _clean(title, YT_TITLE_LIMIT),
        "description": _clean(description, 4900),
        "tags": [_clean(t, 60) for t in tags if _clean(t, 60)],
        "categoryId": category_id,
        "defaultLanguage": language,
        "defaultAudioLanguage": language,
    }
    status = {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": made_for_kids}

    def attempt(synthetic: bool) -> dict:
        body = {"snippet": snippet, "status": {**status, **({"containsSyntheticMedia": True} if synthetic else {})}}
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=_media_upload(Path(file_path)))
        return _run_resumable(request)

    try:
        response = attempt(synthetic=True)
    except Exception as e:
        if "containsSyntheticMedia" in str(getattr(e, "content", b"")) or "containsSyntheticMedia" in str(e):
            log.warning("API rejected containsSyntheticMedia — retrying the upload without it")
            response = attempt(synthetic=False)
        else:
            raise

    video_id = response["id"]
    applied = (response.get("status") or {}).get("privacyStatus")
    if privacy_status == "public" and applied and applied != "public":
        log.error(
            "YouTube applied privacyStatus=%r to %s although 'public' was requested. This is the API "
            "audit lock: uploads from an unverified Google Cloud project are forced private until the "
            "project passes YouTube's API compliance audit. Auto-public publishing will NOT work until then.",
            applied, video_id,
        )
    log.info("Uploaded %s as %s (%s)", video_id, applied or privacy_status, Path(file_path).name)
    return video_id


def upload_thumbnail(video_id: str, thumbnail_path: Path) -> None:
    from googleapiclient.http import MediaFileUpload

    _get_youtube_client().thumbnails().set(
        videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg")
    ).execute()
