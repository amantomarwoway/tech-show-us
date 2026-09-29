"""
Builds SEO metadata (title, description, tags, hashtags) for the long video
and its two derived Shorts, blending search-based and evergreen keywords
already produced by script_writer with a real free YouTube-autocomplete
lookup (actual search-suggestion data, not just LLM guesses).

Also enforces YouTube's hard API limits so an upload never gets rejected on
a metadata technicality:
  - title: 100 chars max (we target 60 for readability/CTR, but never exceed 100)
  - description: 5000 chars max
  - tags: 500 chars combined max
"""
import json
import logging

import requests

from src.config import REQUEST_TIMEOUT_SEC, YT_HASHTAG_CAP

log = logging.getLogger(__name__)

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"

YT_TITLE_HARD_LIMIT = 100
YT_DESCRIPTION_HARD_LIMIT = 5000
YT_TAGS_HARD_LIMIT_CHARS = 500


def fetch_autocomplete_suggestions(word: str) -> list[str]:
    """Real YouTube search-suggestion data for the word — free, no key.
    Used to ground tags/keywords in what people actually search, rather
    than relying solely on the LLM's guesses."""
    try:
        resp = requests.get(
            AUTOCOMPLETE_URL,
            params={"client": "youtube", "ds": "yt", "q": word},
            timeout=REQUEST_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        # Response is JSONP-ish: window.google.ac.h(["query",[["suggestion",0],...]])
        text = resp.text
        start = text.find("[")
        data = json.loads(text[start:])
        return [item[0] for item in data[1]] if len(data) > 1 else []
    except Exception as e:
        log.info("Autocomplete lookup failed for '%s': %s", word, e)
        return []


def _cap_hashtags(tags: list[str]) -> list[str]:
    return tags[:YT_HASHTAG_CAP]


def _cap_tags_to_char_budget(tags: list[str], limit: int = YT_TAGS_HARD_LIMIT_CHARS) -> list[str]:
    """YouTube counts tags against a combined ~500 character budget
    (commas included); truncate the list rather than let the API reject
    the whole upload over one oversized tag set."""
    out, total = [], 0
    for tag in tags:
        added_len = len(tag) + (1 if out else 0)  # +1 for the joining comma
        if total + added_len > limit:
            break
        out.append(tag)
        total += added_len
    return out


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def build_long_metadata(script: dict, word: str) -> dict:
    title = script.get("title", f"{word.upper()}: The Word That Controls You")
    title = title[:YT_TITLE_HARD_LIMIT]

    description_parts = [script.get("description", "")]

    chapters = script.get("chapters", [])
    if chapters:
        description_parts.append("\n\nChapters:")
        for ch in chapters:
            description_parts.append(f"{ch.get('timestamp', '0:00')} {ch.get('label', '')}")

    hashtags = _cap_hashtags(
        [f"#{word.capitalize()}", "#WordsThatSpeaks", "#Psychology", "#Etymology", "#WordOfTheDay"]
    )
    description_parts.append("\n\n" + " ".join(hashtags))

    description = "\n".join(description_parts).strip()[:YT_DESCRIPTION_HARD_LIMIT]

    # Blend LLM-suggested keywords with real search-suggestion data.
    autocomplete = fetch_autocomplete_suggestions(word)
    combined_tags = _dedupe_keep_order(
        script.get("tags", [])
        + script.get("search_keywords", [])
        + script.get("evergreen_keywords", [])
        + autocomplete
    )
    tags = _cap_tags_to_char_budget(combined_tags)

    return {
        "title": title,
        "description": description,
        "tags": tags,
        "hashtags": hashtags,
    }


def build_short_metadata(scene: dict, word: str, long_video_id: str, index: int) -> dict:
    hook = scene.get("narration", "")[:35].strip()
    title = f"{word.upper()}: {hook}"[:40]

    description = (
        f"{scene.get('narration', '')[:100]}...\n\n"
        f"Full 10-min cinematic story: https://youtu.be/{long_video_id}\n\n"
        f"#{word.capitalize()} #WordsThatSpeaks #WordOfTheDay #Shorts #Etymology"
    )[:YT_DESCRIPTION_HARD_LIMIT]

    tags = _cap_tags_to_char_budget(
        [word, "shorts", "psychology", "etymology", "wordsthatspeaks"]
    )

    return {
        "title": title,
        "description": description,
        "tags": tags,
    }
