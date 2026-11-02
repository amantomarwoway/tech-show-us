"""
Real performance numbers from the YouTube Analytics API (v2) — the raw material
for the bot's learning loop (src/story_analytics_sync.py -> pattern_analytics).

  * retention (averageViewPercentage) is the PRIMARY learning signal.
  * CTR (videoThumbnailImpressionsClickRate) is best-effort: Google added it to
    the Analytics API in 2026 but documentation/behaviour has been inconsistent,
    so any failure simply returns None and learning continues on retention.
Needs the yt-analytics.readonly scope on the refresh token.
"""
import logging
from datetime import date, timedelta

from src.youtube_uploader import _get_credentials

log = logging.getLogger(__name__)


def _analytics_client():
    from googleapiclient.discovery import build

    return build("youtubeAnalytics", "v2", credentials=_get_credentials(), cache_discovery=False)


def _query(video_id: str, metrics: str, days_back: int) -> list | None:
    end = date.today()
    resp = _analytics_client().reports().query(
        ids="channel==MINE",
        startDate=(end - timedelta(days=days_back)).isoformat(),
        endDate=end.isoformat(),
        metrics=metrics,
        filters=f"video=={video_id}",
    ).execute()
    rows = resp.get("rows") or []
    return rows[0] if rows else None


def fetch_video_stats(video_id: str, days_back: int = 28) -> dict | None:
    """{"views", "averageViewDuration", "averageViewPercentage"} where
    averageViewPercentage is a FRACTION (0.62 = 62%), or None if there is no data yet."""
    try:
        row = _query(video_id, "views,averageViewDuration,averageViewPercentage", days_back)
    except Exception as e:
        log.warning("Analytics stats failed for %s: %s", video_id, e)
        return None
    if not row:
        return None
    views, avg_dur, avg_pct = row
    return {"views": int(views), "averageViewDuration": float(avg_dur), "averageViewPercentage": float(avg_pct) / 100.0}


def fetch_ctr(video_id: str, days_back: int = 28) -> float | None:
    """Thumbnail click-through rate as a fraction, or None when unavailable."""
    try:
        row = _query(video_id, "videoThumbnailImpressionsClickRate", days_back)
    except Exception as e:
        log.info("CTR not available for %s (%s) — learning continues on retention alone", video_id, e)
        return None
    if not row or row[0] is None:
        return None
    value = float(row[0])
    return value / 100.0 if value > 1 else value
