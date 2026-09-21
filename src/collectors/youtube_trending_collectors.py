"""
src/collectors/youtube_trending_collector.py
- Fetches YouTube Trending videos (chart=mostPopular)
- Uses existing uploader credentials (readonly scope already present)
- Returns stories in standard format
"""

import os
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# YouTube category IDs
CATEGORIES = {
    "music": "10",
    "gaming": "20",
    "entertainment": "24",
    "sports": "17",
    "news": "25",
    "tech": "28",
    "comedy": "23",
    "education": "27",
}

REGIONS = ["US", "GB", "CA", "AU"]


def _get_youtube_client():
    """Build YouTube Data API client with existing credentials."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    client_id = os.getenv("YT_CLIENT_ID", "")
    client_secret = os.getenv("YT_CLIENT_SECRET", "")
    refresh_token = os.getenv("YT_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        logger.error("YouTube credentials missing")
        return None

    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
        )
        youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
        return youtube
    except Exception as e:
        logger.error(f"YouTube client build failed: {e}")
        return None


def _age_hours(published_at):
    """Return age in hours from ISO timestamp."""
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        return (now - dt).total_seconds() / 3600
    except Exception:
        return 999


def collect_youtube_trending():
    """
    Fetch trending videos across regions and categories.
    Returns list of story dicts in standard format.
    """
    logger.info("=" * 60)
    logger.info("YOUTUBE TRENDING COLLECTOR")
    logger.info("=" * 60)

    youtube = _get_youtube_client()
    if not youtube:
        return []

    all_videos = []
    seen_ids = set()

    for region in REGIONS:
        for cat_name, cat_id in CATEGORIES.items():
            try:
                response = youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    chart="mostPopular",
                    regionCode=region,
                    videoCategoryId=cat_id,
                    maxResults=10,
                ).execute()
            except Exception as e:
                logger.warning(f"  {region}/{cat_name} API fail: {str(e)[:80]}")
                continue

            items = response.get("items", [])
            if not items:
                continue

            for item in items:
                vid_id = item.get("id", "")
                if not vid_id or vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)

                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})

                title = snippet.get("title", "").strip()
                if not title or len(title) < 10:
                    continue

                views = int(stats.get("viewCount", 0) or 0)
                likes = int(stats.get("likeCount", 0) or 0)
                comments = int(stats.get("commentCount", 0) or 0)

                hours = _age_hours(snippet.get("publishedAt", ""))
                if hours > 336:
                    continue

                velocity = views / max(hours, 1)

                all_videos.append({
                    "title": title,
                    "url": f"https://youtube.com/watch?v={vid_id}",
                    "source": "youtube_trending",
                    "region": region,
                    "category": cat_name,
                    "channel": snippet.get("channelTitle", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "view_count": views,
                    "like_count": likes,
                    "comment_count": comments,
                    "age_hours": hours,
                    "view_velocity": velocity,
                    "youtube_video_id": vid_id,
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "description": snippet.get("description", "")[:500],
                })

            logger.info(f"  {region}/{cat_name}: {len(items)} items")

    logger.info(f"YouTube trending total (raw): {len(all_videos)}")

    seen_titles = set()
    unique = []
    for v in all_videos:
        key = v["title"][:40].lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        unique.append(v)

    unique.sort(key=lambda x: x["view_velocity"], reverse=True)

    logger.info(f"YouTube trending unique: {len(unique)}")
    logger.info("Top 5 by velocity:")
    for v in unique[:5]:
        logger.info(
            f"  [{v['region']}/{v['category']}] {v['title'][:50]} "
            f"({v['view_count']:,} views, {v['age_hours']:.0f}h old)"
        )

    return unique
