"""
Pulls free, factual grounding for a word before scripting:
- Wiktionary REST API for etymology + definitions
- Wikipedia summary API for broader psychological/cultural context
Both are best-effort: failures degrade gracefully to empty strings so the
script writer can still proceed using Gemini's own knowledge.
"""
import logging

import requests

from src.config import REQUEST_TIMEOUT_SEC

log = logging.getLogger(__name__)

WIKTIONARY_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/{word}"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{word}"

# TESTED FOOTGUN, already hit in production: Wikimedia's API gateway
# rejects requests with the default `python-requests/x.x` User-Agent with a
# 403 (their User-Agent policy requires a descriptive identifier —
# https://meta.wikimedia.org/wiki/User-Agent_policy). Without this header
# EVERY run silently loses etymology/Wikipedia grounding (it fails
# "gracefully" to an empty string, so it doesn't crash anything, but the
# script writer is then working from Gemini's own knowledge alone on every
# single episode). Never drop this header when touching these requests.
_HEADERS = {
    "User-Agent": (
        "WordsThatSpeaksBot/1.0 "
        "(https://github.com/; automated etymology research for a YouTube "
        "content pipeline; contact via repo issues)"
    )
}


def _fetch_wiktionary(word: str) -> str:
    try:
        resp = requests.get(
            WIKTIONARY_URL.format(word=word), timeout=REQUEST_TIMEOUT_SEC,
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        defs = []
        for lang_entries in data.values():
            for entry in lang_entries:
                for d in entry.get("definitions", []):
                    text = d.get("definition", "")
                    if text:
                        defs.append(text)
        return " | ".join(defs[:5])
    except Exception as e:
        log.info("Wiktionary lookup failed for '%s': %s", word, e)
        return ""


def _fetch_wikipedia_summary(word: str) -> str:
    try:
        resp = requests.get(
            WIKIPEDIA_SUMMARY_URL.format(word=word), timeout=REQUEST_TIMEOUT_SEC,
            headers=_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("extract", "")
    except Exception as e:
        log.info("Wikipedia summary lookup failed for '%s': %s", word, e)
        return ""


def research_word(word: str) -> dict:
    """Returns {"word", "wiktionary_definitions", "wikipedia_summary"}."""
    return {
        "word": word,
        "wiktionary_definitions": _fetch_wiktionary(word),
        "wikipedia_summary": _fetch_wikipedia_summary(word),
    }
