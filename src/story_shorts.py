"""
Vertical Shorts (1080x1920, 20-35 s) cut from a finished story's assets.

Each episode yields 2-3 Shorts (SHORTS_PER_EPISODE_BY_SLOT; seven a week = one per day):
  * Short 1 "hook":    the episode's opening beats (the writer must put the biggest hook there)
  * the others:        the best-scoring non-overlapping windows — jumpscares, fear, excitement

Both end on a beat boundary (never mid-sentence) and reuse the long video's
already-synthesized voice-over, word alignment and audio direction — nothing is
voiced twice. Only the 9:16 images are new (each beat's own Western-styled
prompt at portrait size). The Short's description/caption always points viewers
to the full story (see src/platform_metadata.py).
"""
import logging
import re

from src.config import SHORT_HEIGHT, SHORT_MAX_SEC, SHORT_MIN_SEC, SHORT_WIDTH
from src.story_pipeline import attach_images, render_video

log = logging.getLogger(__name__)

_TENSION_WORDS = (
    "dread", "fear", "terror", "panic", "tension", "suspicion", "shock", "horror",
    "suspense", "revelation", "anger", "desperat", "menace", "unease", "scream",
)


def _window_from(items: list[dict], start: int, max_sec: float) -> tuple[list[int], float]:
    """Consecutive beats from `start` while the total stays <= max_sec. A
    single over-long first beat is still returned alone (so it never loops)."""
    idxs, total = [], 0.0
    for i in range(start, len(items)):
        d = items[i]["duration"]
        if idxs and total + d > max_sec:
            break
        idxs.append(i)
        total += d
    return idxs, total


_ELEMENT_WEIGHT = {"fear": 2.0, "excitement": 2.0, "suspense": 1.5, "mystery": 1.0, "curiosity": 1.0}


def _tension(items: list[dict], idxs: list[int], total_beats: int) -> float:
    """How well a window works as a standalone Short. The writer tags every beat with the emotions it
    delivers; Shorts want the PUNCHY ones: a jumpscare is worth the most, then fear and excitement
    (chases, escapes), then suspense, mystery and curiosity."""
    score = 0.0
    for i in idxs:
        beat = items[i]["beat"]
        if beat.get("jumpscare"):
            score += 4.0
        score += sum(_ELEMENT_WEIGHT.get(e, 0.0) for e in beat.get("elements") or [])
        emotion = str(beat.get("emotion", "")).lower()
        if any(w in emotion for w in _TENSION_WORDS):
            score += 1.0
        if beat.get("type") == "dialogue":
            score += 0.5
        if beat.get("sfx_kind") == "action":
            score += 1.0
    position = idxs[0] / max(total_beats - 1, 1)
    if 0.5 <= position <= 0.85:   # the thriller-reveal zone of the story
        score += 1.5
    return score


def plan_short_windows(items: list[dict], n: int = 2) -> list[list[int]]:
    """Indices (into `items`) for each Short. Window 1 starts at beat 0 — the writer is required to
    put the part's biggest hook there. Every further Short is the best-scoring window that does not
    overlap an earlier one. If the story is too short to fit non-overlapping windows, the remaining
    Shorts reuse a mid-story window rather than fail."""
    if not items:
        return []
    first, _ = _window_from(items, 0, SHORT_MAX_SEC)
    windows = [first]
    used = set(first)
    while len(windows) < n:
        best, best_score = None, -1.0
        for s in range(len(items)):
            if s in used:
                continue
            idxs, total = _window_from(items, s, SHORT_MAX_SEC)
            idxs = [i for k, i in enumerate(idxs) if not (set(idxs[: k + 1]) & used)]   # stop at the first used beat
            if not idxs:
                continue
            total = sum(items[i]["duration"] for i in idxs)
            penalty = 0.0 if total >= SHORT_MIN_SEC * 0.75 else 5.0  # too short to be a good Short
            score = _tension(items, idxs, len(items)) - penalty
            if score > best_score:
                best, best_score = idxs, score
        if best is None:  # no room left: allow overlap
            mid = max(1, len(items) // 2)
            best, _ = _window_from(items, mid, SHORT_MAX_SEC)
        windows.append(best)
        used |= set(best)
    return windows


def _first_sentence(text: str, limit: int = 110) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    sentence = m.group(1) if m else text
    return sentence[:limit].rstrip()


def build_story_short(assets: dict, idxs: list[int], short_no: int, kind: str, cta_text: str | None = None) -> dict:
    """Render ONE Short. Returns {"path", "hook", "duration", "kind", "beats"}
    where `hook` is the Short's opening line (used for its title/caption)."""
    items = [assets["items"][i] for i in idxs]
    images = attach_images(items, SHORT_WIDTH, SHORT_HEIGHT, tag=f"s{short_no}_", appearances=assets.get("appearances"))
    path, _ = render_video(
        items, images, SHORT_WIDTH, SHORT_HEIGHT, f"{assets['slug']}-short{short_no}",
        is_short=True, ass_name=f"story_short{short_no}.ass", end_cta=cta_text,
    )
    # The hook is the first SPOKEN line of the window; prefer a dialogue line
    # when the window has one in its first two beats (more intriguing).
    lead = next((it["beat"] for it in items[:2] if it["beat"].get("type") == "dialogue"), items[0]["beat"])
    return {
        "path": path,
        "hook": _first_sentence(lead["text"]),
        "duration": sum(it["duration"] for it in items),
        "kind": kind,
        "beats": idxs,
    }


def build_story_shorts(assets: dict, n: int = 2, cta_text: str | None = None) -> list[dict]:
    """The Shorts for one episode. `cta_text` is the banner shown at the end of each ("FULL STORY: PART 2 —
    SEE RELATED VIDEO"). A Short that fails to render is skipped (with an error log) rather than losing
    the others."""
    items = assets["items"]
    usable = items[:-1] if items and items[-1]["beat"].get("outro") else items   # the closing "Part N+1 arrives..." line is not Short material
    windows = plan_short_windows(usable, n)
    kinds = ["hook", "tension", "tension", "tension"]
    shorts = []
    for k, idxs in enumerate(windows, start=1):
        try:
            shorts.append(build_story_short(assets, idxs, k, kinds[min(k, 4) - 1], cta_text))
        except Exception as e:
            log.error("Short %d failed to render: %s", k, e)
    return shorts
