"""
src/collectors/youtube_trending_collector.py
- Trending videos with RISING views (compares with last snapshot)
- English-only filter
- No education (404), no score cap
- Stores snapshots for velocity comparison
"""

import os
import json
import re
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

CATEGORIES = {
    "music": "10",
    "gaming": "20",
    "entertainment": "24",
    "sports": "17",
    "news": "25",
    "tech": "28",
    "comedy": "23",
}
REGIONS = ["US", "GB", "CA", "AU"]
SNAPSHOT_FILE = "data/trending_snapshots.json"
SNAPSHOT_KEEP_HOURS = 72


def _get_youtube_client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    cid = os.getenv("YT_CLIENT_ID", "")
    cs = os.getenv("YT_CLIENT_SECRET", "")
    rt = os.getenv("YT_REFRESH_TOKEN", "")
    if not all([cid, cs, rt]):
        return None
    try:
        creds = Credentials(
            token=None, refresh_token=rt,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cid, client_secret=cs,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
        )
        return build("youtube", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        logger.error(f"YouTube client failed: {e}")
        return None


def _age_hours(ts):
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
    except Exception:
        return 999


def _is_english(title):
    """Reject non-English (Hindi, Arabic, CJK, etc.)."""
    if not title:
        return False
    ascii_chars = sum(1 for c in title if ord(c) < 128)
    if ascii_chars / max(len(title), 1) < 0.75:
        return False
    # Reject Devanagari, Arabic, Chinese, Japanese, Korean, Cyrillic, Thai
    if re.search(r'[\u0900-\u097F\u0600-\u06FF\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u0400-\u04FF\u0E00-\u0E7F]', title):
        return False
    # Must have at least 2 English words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title)
    return len(words) >= 2


def _load_snapshots():
    if not os.path.exists(SNAPSHOT_FILE):
        return {}
    try:
        with open(SNAPSHOT_FILE) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_snapshots(data):
    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    try:
        with open(SNAPSHOT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Snapshot save failed: {e}")


def _prune_snapshots(data):
    cutoff = datetime.now().timestamp() - SNAPSHOT_KEEP_HOURS * 3600
    out = {}
    for vid, snaps in data.items():
        kept = [s for s in snaps if s.get("ts", 0) >= cutoff]
        if kept:
            out[vid] = kept
    return out


def _rising_score(video_id, current_views, snapshots):
    """
    Compare current views with previous snapshots.
    Return rising score (0-100) based on view growth rate.
    """
    snaps = snapshots.get(video_id, [])
    if not snaps:
        return 50  # neutral, no history yet

    # Find oldest snapshot in window
    oldest = snaps[0]
    old_views = oldest.get("views", 0)
    old_ts = oldest.get("ts", 0)
    if old_views <= 0:
        return 50

    hours_diff = (datetime.now().timestamp() - old_ts) / 3600
    if hours_diff < 1:
        return 50

    growth_rate = (current_views - old_views) / old_views  # fraction
    growth_per_hour = growth_rate / hours_diff

    # Score: 100 for 5%+ growth per hour, 0 for negative
    if growth_per_hour <= 0:
        return 10
    score = min(100, growth_per_hour * 2000)
    return score


def collect_youtube_trending():
    logger.info("=" * 60)
    logger.info("YOUTUBE TRENDING COLLECTOR (rising + English only)")
    logger.info("=" * 60)

    yt = _get_youtube_client()
    if not yt:
        logger.error("YouTube client failed")
        return []

    snapshots = _prune_snapshots(_load_snapshots())
    now_ts = datetime.now().timestamp()

    raw = []
    seen_ids = set()

    for region in REGIONS:
        for cat_name, cat_id in CATEGORIES.items():
            try:
                resp = yt.videos().list(
                    part="snippet,statistics,contentDetails",
                    chart="mostPopular",
                    regionCode=region,
                    videoCategoryId=cat_id,
                    maxResults=10,
                ).execute()
            except Exception as e:
                logger.warning(f"  {region}/{cat_name} fail: {str(e)[:80]}")
                continue

            for item in resp.get("items", []):
                vid = item.get("id", "")
                if not vid or vid in seen_ids:
                    continue
                seen_ids.add(vid)

                sn = item.get("snippet", {})
                st = item.get("statistics", {})
                title = sn.get("title", "").strip()
                if not title or len(title) < 10:
                    continue

                if not _is_english(title):
                    continue

                views = int(st.get("viewCount", 0) or 0)
                likes = int(st.get("likeCount", 0) or 0)
                comments = int(st.get("commentCount", 0) or 0)
                hours = _age_hours(sn.get("publishedAt", ""))
                if hours > 336:
                    continue

                # Rising score
                rising = _rising_score(vid, views, snapshots)

                # Update snapshot
                snaps = snapshots.setdefault(vid, [])
                snaps.append({"views": views, "ts": now_ts, "title": title[:80]})
                if len(snaps) > 20:
                    snapshots[vid] = snaps[-20:]

                raw.append({
                    "title": title,
                    "url": f"https://youtube.com/watch?v={vid}",
                    "source": "youtube_trending",
                    "region": region,
                    "category": cat_name,
                    "channel": sn.get("channelTitle", ""),
                    "published_at": sn.get("publishedAt", ""),
                    "view_count": views,
                    "like_count": likes,
                    "comment_count": comments,
                    "age_hours": hours,
                    "view_velocity": views / max(hours, 1),
                    "rising_score": rising,
                    "youtube_video_id": vid,
                    "thumbnail": sn.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "description": sn.get("description", "")[:500],
                })

            logger.info(f"  {region}/{cat_name}: {len(resp.get('items', []))} items")

    _save_snapshots(snapshots)

    # Dedupe by title
    seen_titles = set()
    unique = []
    for v in raw:
        k = v["title"][:40].lower()
        if k in seen_titles:
            continue
        seen_titles.add(k)
        unique.append(v)

    # Score: view + velocity + rising + engagement (NO cap)
    for v in unique:
        views = v["view_count"]
        velocity = v["view_velocity"]
        rising = v["rising_score"]
        eng = (v["like_count"] + v["comment_count"] * 3) / max(views, 1) * 1000

        v["breakout_score"] = (
            min(150, views / 50000) * 0.20        # views (0-150)
            + min(150, velocity / 3000) * 0.35    # velocity (0-150)
            + rising * 0.35                        # rising 0-100
            + min(100, eng * 5) * 0.10            # engagement
        )

    unique.sort(key=lambda x: x["breakout_score"], reverse=True)

    logger.info(f"YouTube trending total: {len(unique)}")
    logger.info("Top 5 by rising+velocity:")
    for v in unique[:5]:
        logger.info(
            f"  [{v['region']}/{v['category']}] {v['title'][:45]} "
            f"({v['view_count']:,}v, rising {v['rising_score']:.0f}, score {v['breakout_score']:.0f})"
        )

    return unique
