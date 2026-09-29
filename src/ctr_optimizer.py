"""
Daily job: fetch YouTube Analytics for videos older than 48h, and for any
underperforming ones (CTR or average-view-duration below threshold),
regenerate title/description/hashtags/thumbnail via Gemini + Pollinations
and push the update via the Data API.

Run standalone: `python -m src.ctr_optimizer`
"""
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from src.config import (
    CTR_CHECK_MIN_AGE_HOURS,
    CTR_COOLDOWN_DAYS,
    CTR_MAX_AGE_DAYS,
    CTR_MAX_ATTEMPTS,
    CTR_MIN_VIEWS,
    LONG_AVG_VIEW_PCT_MIN,
    LONG_CTR_MIN,
    SHORT_AVG_VIEW_PCT_MIN,
    SHORT_CTR_MIN,
)
from src.database import (
    get_videos_needing_ctr_check,
    increment_thumb_version,
    init_db,
    record_ctr_attempt,
    update_ctr,
)
from src.llm_client import generate_json
from src.thumbnail_builder import build_thumbnail
from src.youtube_uploader import update_video_metadata, upload_thumbnail

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


def _get_analytics_client():
    from googleapiclient.discovery import build

    from src.youtube_uploader import _get_credentials

    return build("youtubeAnalytics", "v2", credentials=_get_credentials())


def _fetch_video_stats(video_id: str, days_back: int = 7) -> dict | None:
    try:
        analytics = _get_analytics_client()
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days_back)
        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="averageViewDuration,averageViewPercentage,views",
            filters=f"video=={video_id}",
        ).execute()
        rows = response.get("rows", [])
        if not rows:
            return None
        avg_duration, avg_view_pct, views = rows[0]
        return {
            "averageViewDuration": avg_duration,
            "averageViewPercentage": avg_view_pct / 100.0,
            "views": views,
        }
    except Exception as e:
        log.warning("Analytics fetch failed for video %s: %s", video_id, e)
        return None


def _fetch_ctr(video_id: str, days_back: int = 7) -> float | None:
    # NOTE: click-through-rate for impressions is exposed via the "cardCTR" /
    # traffic-source-level metrics in the Analytics API, and access to
    # impressions-based CTR can require additional scope/report type; this
    # helper degrades to None (skips CTR gating) if unavailable rather than
    # guessing a number.
    try:
        analytics = _get_analytics_client()
        end = datetime.now(timezone.utc).date()
        start = end - timedelta(days=days_back)
        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=start.isoformat(),
            endDate=end.isoformat(),
            metrics="impressions,impressionClickThroughRate",
            filters=f"video=={video_id}",
        ).execute()
        rows = response.get("rows", [])
        if not rows:
            return None
        _, ctr = rows[0]
        return ctr / 100.0
    except Exception as e:
        log.info("CTR metric unavailable for video %s (%s) — skipping CTR gate", video_id, e)
        return None


REGEN_PROMPT = """You are refreshing underperforming YouTube metadata for the
word "{word}" on the channel WordsThatSpeaks (etymology + psychology,
mystery/thriller tone). The current title is: "{old_title}"

Write a fresh, punchier title (max 60 chars) and a short 3-word hook phrase
suitable for a thumbnail overlay, aimed at improving click-through rate
without becoming misleading clickbait. Return ONLY JSON:
{{"title": "...", "hook_overlay": "..."}}
"""


def _regenerate_metadata(word: str, old_title: str) -> dict:
    prompt = REGEN_PROMPT.format(word=word, old_title=old_title)
    return generate_json(prompt, temperature=1.0)


def _is_eligible_for_ctr_check(row, field: str, stats: dict) -> tuple[bool, str]:
    """CTR_MAX_AGE_DAYS / CTR_COOLDOWN_DAYS / CTR_MAX_ATTEMPTS / CTR_MIN_VIEWS
    gate — without this, a genuinely bad title could get rewritten forever,
    chasing noise in low-traffic stats, or a video could be endlessly
    "optimized" long after it's stopped getting meaningful traffic. Returns
    (eligible, reason_if_not)."""
    try:
        uploaded = datetime.fromisoformat(row["uploaded_at"])
        age_days = (datetime.now(timezone.utc) - uploaded).total_seconds() / 86400
    except (TypeError, ValueError):
        age_days = 0
    if age_days > CTR_MAX_AGE_DAYS:
        return False, f"video is {age_days:.0f}d old (max {CTR_MAX_AGE_DAYS}d)"

    if stats["views"] < CTR_MIN_VIEWS:
        return False, f"only {stats['views']} views (min {CTR_MIN_VIEWS})"

    attempts_col = f"ctr_attempts_{field}"
    attempts = row[attempts_col] if row[attempts_col] is not None else 0
    if attempts >= CTR_MAX_ATTEMPTS:
        return False, f"already regenerated {attempts}x (max {CTR_MAX_ATTEMPTS})"

    last_attempt_col = f"last_ctr_attempt_{field}"
    last_attempt = row[last_attempt_col]
    if last_attempt:
        try:
            last_dt = datetime.fromisoformat(last_attempt)
            days_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 86400
            if days_since < CTR_COOLDOWN_DAYS:
                return False, f"last attempt {days_since:.1f}d ago (cooldown {CTR_COOLDOWN_DAYS}d)"
        except (TypeError, ValueError):
            pass

    return True, ""


def run_ctr_optimizer() -> None:
    init_db()
    candidates = get_videos_needing_ctr_check(CTR_CHECK_MIN_AGE_HOURS)
    log.info("Found %d video(s) old enough for CTR review", len(candidates))

    # field: (db field-key used for ctr_attempts_<field>/last_ctr_attempt_<field>
    #          columns, the video_id column, CTR threshold, avg-view threshold)
    fields = (
        ("long", "long_video_id", LONG_CTR_MIN, LONG_AVG_VIEW_PCT_MIN),
        ("short1", "short_id_1", SHORT_CTR_MIN, SHORT_AVG_VIEW_PCT_MIN),
        ("short2", "short_id_2", SHORT_CTR_MIN, SHORT_AVG_VIEW_PCT_MIN),
    )

    for row in candidates:
        word = row["word"]
        for field, video_id_col, ctr_min, view_min in fields:
            video_id = row[video_id_col]
            if not video_id:
                continue
            stats = _fetch_video_stats(video_id)
            if stats is None:
                continue

            eligible, reason = _is_eligible_for_ctr_check(row, field, stats)
            if not eligible:
                log.info("Skipping video %s ('%s'): %s", video_id, word, reason)
                continue

            ctr = _fetch_ctr(video_id)
            underperforming = stats["averageViewPercentage"] < view_min or (
                ctr is not None and ctr < ctr_min
            )
            if not underperforming:
                log.info("Video %s ('%s') performing within thresholds", video_id, word)
                continue

            log.info(
                "Video %s ('%s') underperforming (avgViewPct=%.2f ctr=%s) — regenerating",
                video_id, word, stats["averageViewPercentage"], ctr,
            )
            try:
                fresh = _regenerate_metadata(word, row["title"] or word)
                update_video_metadata(video_id, title=fresh["title"])
                new_thumb = build_thumbnail(word, hook_snippet=fresh.get("hook_overlay", ""))
                upload_thumbnail(video_id, new_thumb)
                increment_thumb_version(word)
                # Only record the attempt (which counts toward CTR_MAX_ATTEMPTS
                # and starts the CTR_COOLDOWN_DAYS clock) after the update
                # actually succeeded — a failed attempt shouldn't burn one of
                # the video's limited regeneration attempts.
                record_ctr_attempt(word, field)
                if field == "long":
                    update_ctr(word, ctr_long=ctr)
                elif field == "short1":
                    update_ctr(word, ctr_short1=ctr)
                else:
                    update_ctr(word, ctr_short2=ctr)
            except Exception as e:
                log.error("Failed to regenerate metadata for video %s: %s", video_id, e)


if __name__ == "__main__":
    try:
        run_ctr_optimizer()
    except Exception as e:
        log.exception("CTR optimizer run failed: %s", e)
        sys.exit(1)
