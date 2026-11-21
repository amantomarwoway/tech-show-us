"""
Decides, for each weekly slot, WHICH story gets the next part and HOW that part must end.

The model: SERIES_ACTIVE (3) stories run in parallel, each owning one weekly slot for its whole life.
Every week each story gets its next part. A story is not a fixed-length movie — the audience decides:

  * a new story is planned for 3-7 parts, but is judged by the numbers of its LATEST part:
      hot   (score >= CRAZE_HOT)   -> never ends early; at its planned end it is EXTENDED by 2 parts
                                      (up to SERIES_MAX_PARTS) — the audience is asking for more
      warm                         -> runs to its planned length, then ends
      cold  (score < CRAZE_COLD)   -> wrapped up NOW: the next part is written as the FINALE. This is
                                      the "story that stops at 2 parts because nobody cared": part 2 is
                                      decided from part 1's numbers, so it can already be the ending
      unknown (no data yet)        -> follows the plan
  * when a story ends its slot frees up and the next occurrence of that slot starts a NEW story.

"Craze" combines retention (how much of the video people actually watched) with views PER DAY relative to the
channel's OTHER stories — never views alone, since a new channel's views are tiny and noisy, and never against
the story's own numbers.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from src.config import (
    CRAZE_COLD,
    CRAZE_HOT,
    CRAZE_MIN_AGE_HOURS,
    CRAZE_RETENTION_TARGET,
    SERIES_MAX_PARTS,
    SERIES_MIN_PARTS,
    SERIES_PARTS_RANGE,
)
from src.database import channel_baseline, episodes_for_series, series_for_slot, update_series

log = logging.getLogger(__name__)


@dataclass
class Plan:
    series: dict | None      # the existing series row, or None for a brand-new story
    slot_index: int
    part_no: int
    mode: str                # "opening" | "middle" | "finale"
    planned_parts: int       # possibly extended; 0 for a new story (the writer proposes it)
    reason: str


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def craze(series_id: int, *, now: datetime | None = None) -> dict:
    """{"label": hot|warm|cold|unknown, "score", "part", "retention", "views_per_day"} from the newest episode of
    this series that is old enough (CRAZE_MIN_AGE_HOURS) AND has real analytics numbers.

    score = 0.6 x retention / CRAZE_RETENTION_TARGET  +  0.4 x (views per day / twice the typical views per day of
    the channel's OTHER stories). The story is never compared with itself, and views are per day of age so a
    3-day-old part is not judged against month-old ones. While there is nothing else to compare with (the very
    first stories), retention alone decides."""
    now = now or datetime.now(timezone.utc)
    for ep in reversed(episodes_for_series(series_id)):
        if ep.get("avg_view_percentage") is None:
            continue
        try:
            ref = datetime.fromisoformat(ep.get("publish_at") or ep["uploaded_at"])
        except (TypeError, ValueError):
            continue
        age = now - ref
        if age < timedelta(hours=CRAZE_MIN_AGE_HOURS):
            continue
        r, v = float(ep["avg_view_percentage"]), ep.get("views")
        rate = v / min(max(age.total_seconds() / 86400, 1.0), 28.0) if v is not None else None
        base = channel_baseline(exclude_series_id=series_id, now=now)
        retention_score = _clamp(r / CRAZE_RETENTION_TARGET)
        if rate is not None and base["views_per_day"]:
            score = 0.6 * retention_score + 0.4 * _clamp(rate / (2 * base["views_per_day"]))
        else:
            score = retention_score
        label = "hot" if score >= CRAZE_HOT else "cold" if score < CRAZE_COLD else "warm"
        return {"label": label, "score": round(score, 3), "part": ep.get("part_no"), "retention": r,
                "views_per_day": None if rate is None else round(rate, 1)}
    return {"label": "unknown", "score": None, "part": None, "retention": None, "views_per_day": None}


def decide_next_part(series: dict, verdict: dict) -> tuple[str, int, str]:
    """(mode, planned_parts, reason) for the part after `series["parts_done"]`."""
    done = int(series.get("parts_done") or 0)
    planned = int(series.get("planned_parts") or SERIES_PARTS_RANGE[0])
    part, label = done + 1, verdict["label"]
    if done == 0:
        return "opening", planned, "first part of a new story"
    if part >= SERIES_MAX_PARTS:
        return "finale", planned, f"reached the cap of {SERIES_MAX_PARTS} parts"
    if label == "cold" and part >= SERIES_MIN_PARTS:
        return "finale", part, f"part {verdict['part']} scored {verdict['score']} (cold) — wrapping the story up now"
    if part < planned:
        return "middle", planned, f"planned {planned} parts, craze {label}"
    # part >= planned: the story's planned end
    if label == "hot" and part < SERIES_MAX_PARTS:
        extended = min(planned + 2, SERIES_MAX_PARTS)
        return "middle", extended, f"part {verdict['part']} is a hit (score {verdict['score']}) — extended from {planned} to {extended} parts"
    return "finale", planned, f"planned end of the story (craze {label})"


def plan_for_slot(slot_index: int, *, now: datetime | None = None) -> Plan:
    """What to write for this weekly slot."""
    series = series_for_slot(slot_index)
    if series is None:
        return Plan(None, slot_index, 1, "opening", 0, "the slot is free — starting a new story")
    verdict = craze(series["id"], now=now)
    mode, planned, reason = decide_next_part(series, verdict)
    if planned != series.get("planned_parts"):
        update_series(series["id"], planned_parts=planned)
        series = {**series, "planned_parts": planned}
    part_no = int(series.get("parts_done") or 0) + 1
    log.info("Series %s %r: part %d -> %s (%s)", series["id"], series.get("title"), part_no, mode, reason)
    return Plan(series, slot_index, part_no, mode, planned, reason)


def clamp_planned_parts(n) -> int:
    """The writer proposes a length for a new story; keep it inside SERIES_PARTS_RANGE."""
    lo, hi = SERIES_PARTS_RANGE
    try:
        return max(lo, min(hi, int(n)))
    except (TypeError, ValueError):
        return (lo + hi) // 2
