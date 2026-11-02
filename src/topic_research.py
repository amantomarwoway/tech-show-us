"""
Real competitive-research signals pulled from YouTube's own search results
for a niche (e.g. "mystery story", "true crime", "village folk tale") —
actual recently-uploaded, relatively successful videos matching that
niche — rather than a guessed "what's trending" answer.

Reuses the same OAuth credentials youtube_uploader.py already sets up; no
new scope is required beyond what's already configured (the broad
`youtube` scope already covers these read calls). If you'd rather run
with a narrower, read-only-only credential for safety, `youtube.readonly`
covers everything this module calls (search.list, videos.list) — this
module never calls an API that writes anything.

HONEST LIMITS, stated up front rather than left for someone to discover
the hard way: YouTube does not expose a bulk "what's trending in this
niche" endpoint to third-party developers — `search.list` with
`order=viewCount` is the closest available signal, and it's filtered
through YouTube's own (not-externally-visible) search ranking before you
ever see it. What this module gives you is real: actual tags, actual
titles, actual view counts of real videos that actually rank for your
search terms right now. What it can't give you is a guarantee those are
THE best keywords/topics — a small sample size, an unusual or very
competitive niche term, or YouTube's ranking simply not surfacing the
true top performers for a broad query can all skew the picture. The
`sample_size` field in research_niche()'s output is there so you can see
how much (or little) this result is actually based on, rather than
trusting a confident-looking list blindly.
"""
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from src.node_bridge import scrape_niche as _scrape_niche_browser
from src.youtube_uploader import _get_youtube_client

log = logging.getLogger(__name__)

_TITLE_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "and", "to", "is", "for", "with",
    "this", "that", "it", "at", "by", "from", "as", "but", "or", "not",
    "you", "your", "i", "my", "we", "our", "what", "how", "why", "who",
    "when", "video", "full", "part", "official",
}


def search_niche_videos(niche: str, max_results: int = 25, days_back: int = 30) -> list[dict]:
    """Real, recent videos matching `niche`, ordered by view count (the
    closest `search.list` gets to "what's doing well"). Returns
    [{video_id, title, channel, published_at, view_count, tags}, ...],
    sorted by view_count descending. Returns an empty list (not an
    exception) if nothing matches — a niche term with no recent uploads is
    real information, not a failure.
    """
    youtube = _get_youtube_client()
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=days_back)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    search_resp = youtube.search().list(
        part="snippet",
        q=niche,
        type="video",
        order="viewCount",
        publishedAfter=published_after,
        maxResults=min(max_results, 50),  # YouTube API's own per-call cap
    ).execute()

    video_ids = [
        item["id"]["videoId"] for item in search_resp.get("items", [])
        if item.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return []

    # search.list doesn't return tags or statistics — a second call to
    # videos.list is required to get those for the ids search.list found.
    videos_resp = youtube.videos().list(
        part="snippet,statistics", id=",".join(video_ids),
    ).execute()

    results = []
    for item in videos_resp.get("items", []):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        results.append({
            "video_id": item.get("id", ""),
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "published_at": snippet.get("publishedAt", ""),
            "view_count": int(stats.get("viewCount", 0) or 0),
            "tags": snippet.get("tags", []),
        })

    results.sort(key=lambda v: v["view_count"], reverse=True)
    return results


def _extract_title_keywords(titles: list[str], top_n: int = 15) -> list[str]:
    """Frequency-ranked significant words across a set of real titles —
    not a guess, a count of what's actually there."""
    counts = Counter()
    for title in titles:
        for word in title.lower().split():
            word = word.strip(".,!?:;\"'()[]{}—-")
            if len(word) > 2 and word not in _TITLE_STOPWORDS:
                counts[word] += 1
    return [word for word, _ in counts.most_common(top_n)]


def research_niche(
    niche: str, max_results: int = 25, days_back: int = 30, *, use_browser_scraper: bool = True
) -> dict:
    """Aggregates search_niche_videos() into a research summary:

    {
      "niche": the query you passed in,
      "sample_size": how many real videos this is based on — LOOK AT THIS
                      before trusting the rest; a result built from 3
                      videos is much weaker evidence than one from 25,
      "suggested_tags": most common real tags across the result set,
      "suggested_keywords": most common significant words across titles,
      "top_titles": the actual highest-view-count titles found,
      "top_videos": full data for the top 10 (title, channel, view_count,
                     published_at, tags) in case you want more than just
                     the aggregated keyword/tag lists,
      "browser_scraper_videos": supplementary results from the Node.js/
                      Puppeteer headless-browser scraper (src/node_bridge.py)
                      if it's installed and available — None if it isn't
                      set up (a missing OPTIONAL dependency, not an error;
                      everything else in this dict is unaffected either way).
    }

    If search_niche_videos() finds nothing, sample_size is 0 and the list
    fields are empty — this is a real, meaningful result (the niche term
    as given has no recent matches), not an error to retry blindly.
    """
    browser_videos = _scrape_niche_browser(niche, max_results) if use_browser_scraper else None
    videos = search_niche_videos(niche, max_results, days_back)
    if not videos:
        return {
            "niche": niche,
            "sample_size": 0,
            "suggested_tags": [],
            "suggested_keywords": [],
            "top_titles": [],
            "top_videos": [],
            "note": (
                "No results in the last %d days for this niche term — try "
                "a broader phrase, a longer days_back window, or check "
                "the term isn't too narrow/misspelled." % days_back
            ),
            "browser_scraper_videos": browser_videos,
        }

    all_tags = [t for v in videos for t in v.get("tags", [])]
    tag_counts = Counter(t.lower() for t in all_tags)
    suggested_tags = [t for t, _ in tag_counts.most_common(15)]
    suggested_keywords = _extract_title_keywords([v["title"] for v in videos])

    return {
        "niche": niche,
        "sample_size": len(videos),
        "suggested_tags": suggested_tags,
        "suggested_keywords": suggested_keywords,
        "top_titles": [v["title"] for v in videos[:10]],
        "top_videos": videos[:10],
        "browser_scraper_videos": browser_videos,
    }
