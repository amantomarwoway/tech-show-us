"""
src/collectors/youtube_trending_collector.py - v2
- Rising score as PRIMARY signal (50% weight)
- Already-viral penalty (5M+ views = low score)
- Title filter: reject clickbait/emoji-heavy
- Cache persistence friendly
"""

import os
import json
import re
from datetime import datetime
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

CATEGORIES = {
    "news": "25",
    "tech": "28",
    "sports": "17",
    "gaming": "20",
}

REGIONS = ["US", "GB", "CA", "AU"]
SNAPSHOT_FILE = "data/trending_snapshots.json"
SNAPSHOT_KEEP_HOURS = 72

BAD_TITLE_PATTERNS = [
    r'\b(official\s+)?music\s+video\b', r'\bofficial\s+video\b',
    r'\bofficial\s+audio\b', r'\blyric\s+video\b', r'\blyrics?\b',
    r'\bfeat\.?\b', r'\bft\.?\b', r'\(audio\)', r'\[audio\]',
    r'\bremix\b', r'\bcover\b', r'\bremaster(ed)?\b', r'\bmashup\b',
    r'\bkaraoke\b', r'\bmixtape\b', r'\balbum\b', r'\bsingle\b',
    r'\bMV\b', r'#shorts\b', r'\bvlog\b', r'\bprank\b',
    r'\breaction\b', r'\bmeme\b', r'\bcomedy\b', r'\bfunny\b',
]

HINDI_ARTIST_NAMES = [
    'yoyo honey', 'honey singh', 'arijit', 'shreya', 'rahman',
    'kumar sanu', 'sonu nigam', 'neha kakkar', 'shreya ghoshal',
    'pritam', 'amitabh', 'ranbir', 'deepika', 'priyanka',
    'badshah', 'raftaar', 'divine', 'romantic hindi',
    'bollywood', 't-series', 'tseries', 'zee music', 'sony music india',
    'saregama', 'speed records', 'tips official',
]

# Clickbait / conversation-style titles to reject
CLICKBAIT_STARTS = [
    'i think', 'i bet', 'i swear', 'i believe',
    'bro ', 'dude ', 'ngl ', 'fr ',
    'wait ', 'when ', 'why you should never',
    'at least', 'never thought', 'cannot believe',
]

CLICKBAIT_KEYWORDS = [
    'og will', 'always be the best',
    'came prepared', 'chose his safe side',
    'summoned the boss', 'road rage',
    'everyone needed oxygen',
]

BAD_TITLE_REGEX = re.compile("|".join(BAD_TITLE_PATTERNS), re.IGNORECASE)
EMOJI_REGEX = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE
)


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


def _emoji_count(text):
    return len(EMOJI_REGEX.findall(text or ""))


def _is_english(title):
    if not title:
        return False
    ratio = sum(1 for c in title if ord(c) < 128) / max(len(title), 1)
    if ratio < 0.75:
        return False
    if re.search(r'[\u0900-\u097F\u0600-\u06FF\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u0400-\u04FF\u0E00-\u0E7F]', title):
        return False
    words = re.findall(r'\b[a-zA-Z]{3,}\b', title)
    return len(words) >= 2


def _is_not_hindi(title):
    tl = title.lower()
    for name in HINDI_ARTIST_NAMES:
        if name in tl:
            return False
    return True


def _is_informative(title):
    """Reject music/comedy/clickbait."""
    if not title:
        return False
    if BAD_TITLE_REGEX.search(title):
        return False

    tl = title.lower().strip()

    # Reject clickbait starts
    for start in CLICKBAIT_STARTS:
        if tl.startswith(start):
            return False

    # Reject clickbait keywords
    for kw in CLICKBAIT_KEYWORDS:
        if kw in tl:
            return False

    # Reject if too many emojis (>2)
    if _emoji_count(title) > 2:
        return False

    # Reject if too short (< 6 words after removing emojis)
    text_only = EMOJI_REGEX.sub("", title)
    word_count = len(re.findall(r'\b[a-zA-Z]{2,}\b', text_only))
    if word_count < 6:
        return False

    # Reject if text portion (excluding emojis/hashtags) is < 25 chars
    clean = re.sub(r'#\w+', '', text_only).strip()
    if len(clean) < 25:
        return False

    return True


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
        logger.info(f"Snapshots saved: {len(data)} videos")
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
    Rising score based on:
    - gained views per hour (from snapshots)
    - recency ratio (recent gain / total views)
    Already-viral videos score LOW because their recency ratio is small.
    """
    snaps = snapshots.get(video_id, [])
    if len(snaps) < 2:
        return 30  # unknown

    now_ts = datetime.now().timestamp()

    # Find oldest snapshot with >= 1h gap
    oldest = None
    for s in snaps:
        hours = (now_ts - s.get("ts", 0)) / 3600
        if hours >= 1:
            oldest = s
            break

    if not oldest:
        return 30

    old_views = oldest.get("views", 0)
    old_ts = oldest.get("ts", 0)
    hours_diff = (now_ts - old_ts) / 3600

    if old_views <= 0 or current_views <= old_views:
        return 10

    gained = current_views - old_views
    gained_per_hour = gained / hours_diff
    recency_ratio = gained / current_views  # fraction

    # 100k/hr = score 100
    gain_score = min(100, gained_per_hour / 1000)
    # 20% recency = score 100
    recency_score = min(100, recency_ratio * 500)

    # Recency is more important — already-viral gets punished
    return int(gain_score * 0.4 + recency_score * 0.6)


def _views_score(views):
    """
    Reward sweet-spot videos (100k - 1M views).
    Penalize already-viral (>5M) and unknown (<50k).
    """
    if views > 5_000_000:
        return 20   # already peaked
    if views > 2_000_000:
        return 50
    if views > 1_000_000:
        return 80
    if views > 500_000:
        return 100  # sweet spot
    if views > 200_000:
        return 95
    if views > 100_000:
        return 85
    if views > 50_000:
        return 70
    return 40


def collect_youtube_trending():
    logger.info("=" * 60)
    logger.info("YOUTUBE TRENDING COLLECTOR v2 (rising-first)")
    logger.info("=" * 60)

    yt = _get_youtube_client()
    if not yt:
        return []

    snapshots = _prune_snapshots(_load_snapshots())
    logger.info(f"Loaded snapshots for {len(snapshots)} videos")
    now_ts = datetime.now().timestamp()

    raw = []
    seen_ids = set()
    skipped_music = 0
    skipped_lang = 0
    skipped_hindi = 0
    skipped_clickbait = 0

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

            kept = 0
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
                    skipped_lang += 1
                    continue

                if not _is_not_hindi(title):
                    skipped_hindi += 1
                    continue

                if not _is_informative(title):
                    # Distinguish music vs clickbait by pattern
                    if BAD_TITLE_REGEX.search(title):
                        skipped_music += 1
                    else:
                        skipped_clickbait += 1
                    continue

                views = int(st.get("viewCount", 0) or 0)
                likes = int(st.get("likeCount", 0) or 0)
                comments = int(st.get("commentCount", 0) or 0)
                hours = _age_hours(sn.get("publishedAt", ""))
                if hours > 336:
                    continue

                rising = _rising_score(vid, views, snapshots)

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
                kept += 1

            logger.info(f"  {region}/{cat_name}: {kept} kept")

    _save_snapshots(snapshots)

    logger.info(f"Skipped: music={skipped_music}, lang={skipped_lang}, "
                f"hindi={skipped_hindi}, clickbait={skipped_clickbait}")

    # Dedup by title
    seen_titles = set()
    unique = []
    for v in raw:
        k = v["title"][:40].lower()
        if k in seen_titles:
            continue
        seen_titles.add(k)
        unique.append(v)

    # ============================================================
    # NEW SCORING: rising is primary signal
    # ============================================================
    for v in unique:
        rising = v["rising_score"]
        velocity = v["view_velocity"]
        views = v["view_count"]
        eng = (v["like_count"] + v["comment_count"] * 3) / max(views, 1) * 1000

        # Components (each 0-100)
        rising_comp = rising
        velocity_comp = min(100, velocity / 5000)     # 500k/hr = 100
        eng_comp = min(100, eng * 5)
        views_comp = _views_score(views)

        # Weights: rising is PRIMARY
        v["breakout_score"] = (
            rising_comp * 0.50
            + velocity_comp * 0.25
            + eng_comp * 0.15
            + views_comp * 0.10
        )

    unique.sort(key=lambda x: x["breakout_score"], reverse=True)

    logger.info(f"YouTube trending total: {len(unique)}")
    logger.info("Top 5 (rising-first):")
    for v in unique[:5]:
        logger.info(
            f"  [{v['region']}/{v['category']}] {v['title'][:45]} "
            f"({v['view_count']:,}v, age {v['age_hours']:.0f}h, "
            f"rising {v['rising_score']}, score {v['breakout_score']:.0f})"
        )

    return unique
