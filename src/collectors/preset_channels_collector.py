"""
src/collectors/preset_channels_collector.py
- Fetches latest uploads from preset big channels
- Motivation / Story / Facts / Educational / Podcast
- Uses readonly scope
"""

import os
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# ============================================================
# PRESET CHANNELS — big English channels
# ============================================================
PRESET_CHANNELS = {
    # Motivation
    "motivation": [
        "UC0meQ8Bq1XmJcC8m_d5_A_g",  # Motiversity
        "UC5P_mW3pJqSgU8hbcO-2LjA",  # Fearless Motivation
        "UCbA4iH5YvOm-vs7hLxLCHwA",  # Mulligan Brothers
    ],
    # Storytelling / Documentary
    "story": [
        "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast
        "UC4ijq8Cg-8zQKx8_RHxhAbQ",  # Dhar Mann
        "UC8m5YVWQanWlNhF5FqXwxXQ",  # Johnny Harris
    ],
    # Facts / Educational
    "facts": [
        "UCn8ujwUJnFTw1iVc9d0-8ZQ",  # RealLifeLore
        "UCDsElQQt_gSZgfmZLEnBbDA",  # Half as Interesting
        "UCXgNowiGxwwnLeQ7DXTwXPg",  # Wendover Productions
    ],
    # Podcasts
    "podcast": [
        "UCGq-a57w-aPwyi3pW7XLiHw",  # Diary of a CEO
        "UCSHZKyawb77ixDdsGog4iWA",  # Lex Fridman
    ],
    # Science / Tech
    "science": [
        "UCHnyfMqiRRG1u-2MsSQLbXA",  # Veritasium
        "UC6nSFpj9HTCZ5t-N3Rm3-HA",  # Vsauce
        "UCsXVk37bltHxD1rDPwtNM8Q",  # Kurzgesagt
    ],
}


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


def collect_preset_channels(max_per_channel=3, max_age_hours=168):
    """
    Fetch latest uploads from preset channels.
    max_age_hours = 7 days default
    """
    logger.info("=" * 60)
    logger.info("PRESET CHANNELS COLLECTOR")
    logger.info("=" * 60)

    yt = _get_youtube_client()
    if not yt:
        return []

    # Permanent dedup
    try:
        from src.database import get_all_uploaded_yt_ids
        uploaded_ids = get_all_uploaded_yt_ids()
        logger.info(f"Already uploaded (excluded): {len(uploaded_ids)} videos")
    except Exception:
        uploaded_ids = set()

    stories = []
    seen_ids = set()

    for category, channel_ids in PRESET_CHANNELS.items():
        for channel_id in channel_ids:
            try:
                resp = yt.search().list(
                    part="snippet",
                    channelId=channel_id,
                    order="date",
                    type="video",
                    maxResults=max_per_channel,
                    videoDuration="medium",   # 4-20 min
                ).execute()
            except Exception as e:
                logger.warning(f"  {channel_id} fail: {str(e)[:60]}")
                continue

            kept = 0
            for item in resp.get("items", []):
                vid = item.get("id", {}).get("videoId", "")
                if not vid or vid in seen_ids or vid in uploaded_ids:
                    continue
                seen_ids.add(vid)

                sn = item.get("snippet", {})
                title = sn.get("title", "").strip()
                if not title or len(title) < 15:
                    continue

                hours = _age_hours(sn.get("publishedAt", ""))
                if hours > max_age_hours:
                    continue

                # Fetch stats
                try:
                    vstats = yt.videos().list(
                        part="statistics,snippet",
                        id=vid,
                    ).execute()
                    items2 = vstats.get("items", [])
                    if not items2:
                        continue
                    st = items2[0].get("statistics", {})
                    sn2 = items2[0].get("snippet", {})
                except Exception:
                    continue

                views = int(st.get("viewCount", 0) or 0)
                likes = int(st.get("likeCount", 0) or 0)
                comments = int(st.get("commentCount", 0) or 0)

                if views < 10000:
                    continue

                velocity = views / max(hours, 1)
                engagement = (likes + comments * 3) / max(views, 1) * 1000

                # Score
                velocity_score = min(100, velocity / 2000)
                eng_score = min(100, engagement * 5)
                recency = max(0, 100 - hours * 0.5)

                score = (
                    velocity_score * 0.45
                    + eng_score * 0.30
                    + recency * 0.25
                )

                stories.append({
                    "title": title,
                    "url": f"https://youtube.com/watch?v={vid}",
                    "source": f"preset_{category}",
                    "region": "US",
                    "category": category,
                    "channel": sn2.get("channelTitle", ""),
                    "published_at": sn2.get("publishedAt", ""),
                    "view_count": views,
                    "like_count": likes,
                    "comment_count": comments,
                    "age_hours": hours,
                    "view_velocity": velocity,
                    "rising_score": int(min(100, velocity_score)),
                    "breakout_score": score,
                    "youtube_video_id": vid,
                    "thumbnail": sn2.get("thumbnails", {}).get("high", {}).get("url", ""),
                    "description": sn2.get("description", "")[:500],
                })
                kept += 1

            if kept:
                logger.info(f"  {category}/{channel_id[:20]}: {kept} new")

    stories.sort(key=lambda x: x["breakout_score"], reverse=True)

    logger.info(f"Preset channels total (fresh): {len(stories)}")
    for v in stories[:8]:
        logger.info(
            f"  [{v['category']}] {v['title'][:55]} "
            f"({v['view_count']:,}v, score {v['breakout_score']:.0f})"
        )

    return stories
