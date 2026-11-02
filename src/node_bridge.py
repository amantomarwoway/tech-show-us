"""
Bridge to the Node.js/Puppeteer headless-browser scraper in
tools/trending-scraper/ — the one piece of this pipeline that uses a
different language than Python, deliberately: Puppeteer's headless-Chrome
automation is Node's ecosystem, and there's no real benefit to reimplementing
that in Python (e.g. via Selenium) just for language consistency. Python
stays the backbone for everything AI/orchestration/media-processing; this
bridge exists because browser automation is a different kind of problem,
suited to a different tool. See tools/trending-scraper/scrape.js's top
comment for the full reasoning and its honest tested-vs-untested status.

src/topic_research.py's official YouTube Data API research is completely
independent of this — it works with or without Node.js installed. This
module is purely supplementary: a second, different-angle signal source
when it's available, never a hard requirement.
"""
import json
import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

SCRAPER_DIR = Path(__file__).resolve().parent.parent / "tools" / "trending-scraper"
SCRAPER_SCRIPT = SCRAPER_DIR / "scrape.js"
DEFAULT_TIMEOUT_SEC = 60


def is_available() -> bool:
    """True only if node is on PATH AND the scraper's npm dependencies
    look installed (node_modules present). Checked fresh on every call
    rather than cached/assumed — this is explicitly an optional
    component, not every environment running this repo will have set it
    up, and that's fine."""
    if shutil.which("node") is None:
        return False
    if not SCRAPER_SCRIPT.exists():
        return False
    if not (SCRAPER_DIR / "node_modules").exists():
        return False
    return True


def scrape_niche(
    query: str, max_results: int = 25, timeout_sec: int = DEFAULT_TIMEOUT_SEC
) -> list[dict] | None:
    """Returns a list of {videoId, title, channel, viewCountText,
    publishedTimeText} dicts scraped from a real YouTube search results
    page, or None if the scraper isn't set up / the call failed for any
    reason (check logs — this NEVER raises, since it's a supplementary
    signal source, never something that should take down a pipeline run
    over a missing optional dependency or a flaky scrape).
    """
    if not is_available():
        log.info(
            "Node.js trending-scraper not available (node missing, "
            "tools/trending-scraper/scrape.js missing, or `npm install` "
            "hasn't been run in that directory yet) — skipping browser-"
            "based research. src/topic_research.py's Data-API-based "
            "research is unaffected by this."
        )
        return None

    try:
        result = subprocess.run(
            ["node", str(SCRAPER_SCRIPT), "--query", query, "--max-results", str(max_results)],
            capture_output=True, text=True, timeout=timeout_sec, cwd=str(SCRAPER_DIR),
        )
    except subprocess.TimeoutExpired:
        log.warning(
            "Node trending-scraper timed out after %ds for query %r", timeout_sec, query
        )
        return None
    except Exception as e:
        log.warning("Node trending-scraper failed to launch: %s", e)
        return None

    if result.returncode != 0:
        log.warning(
            "Node trending-scraper exited %d for query %r: %s",
            result.returncode, query, result.stderr.strip()[:500],
        )
        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        log.warning(
            "Node trending-scraper returned invalid JSON for query %r: %s "
            "(raw output: %s)", query, e, result.stdout.strip()[:300],
        )
        return None

    return data.get("videos", [])
