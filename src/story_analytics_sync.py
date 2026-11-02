"""
Closes the learning loop. Pulls REAL watch-time / CTR / views from the YouTube
Analytics API for every recorded story video that is old enough to have data,
and writes them into story_videos. pattern_analytics.suggest_next_pillar()
then reads those numbers (long videos only) to decide which content pillar
the NEXT story should lean toward — without this job the pillar learning
would have nothing to learn from.

Run daily:  python -m src.story_analytics_sync
(.github/workflows/story-analytics.yml does exactly that.)
"""
import logging
import sys

from src.youtube_analytics import fetch_ctr, fetch_video_stats
from src.database import get_story_videos_for_stats, init_db, update_story_performance

log = logging.getLogger(__name__)
WINDOW_DAYS = 28


def run_story_analytics_sync() -> int:
    """Returns how many videos were updated."""
    init_db()
    updated = 0
    for row in get_story_videos_for_stats(min_age_hours=48, max_age_days=90):
        vid = row["video_id"]
        stats = fetch_video_stats(vid, days_back=WINDOW_DAYS)
        if not stats or not stats.get("views"):
            log.info("No analytics yet for %s (%s)", vid, row["kind"])
            continue
        ctr = fetch_ctr(vid, days_back=WINDOW_DAYS)  # None when the API doesn't expose it
        update_story_performance(
            vid, avg_view_percentage=stats["averageViewPercentage"],
            ctr=ctr, views=int(stats["views"]),
        )
        updated += 1
        log.info("Updated %s [%s/%s]: retention=%.2f ctr=%s views=%s", vid, row["kind"],
                 row["pillar"], stats["averageViewPercentage"], ctr, stats["views"])
    return updated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        n = run_story_analytics_sync()
        log.info("Story analytics sync done: %d video(s) updated", n)
    except Exception:
        log.exception("Story analytics sync failed")
        sys.exit(1)
