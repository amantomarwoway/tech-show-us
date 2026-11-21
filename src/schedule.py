"""
WHEN things are published. Slots are defined in US Eastern local time (config.SLOT_TIMEZONE) so a
"Friday 8 PM" slot stays at 8 PM through daylight-saving changes; everything here returns UTC.

  * LONG episodes live in three fixed weekly slots (schedule_slots table). A story keeps the SAME
    slot for its whole life, so its viewers get a predictable "TV schedule" (consistency is the one
    scheduling factor every study agrees on).
  * SHORTS have a daily slot; each episode's Shorts take the next free days after the episode drops,
    so exactly one Short goes out every day.
  * The channel REPORTS how each slot performs (slot_report). evaluate_slots() can propose swapping a clearly
    worst slot for an untried candidate, but main_story only APPLIES it when AUTO_SLOT_SWAP=1: views depend on
    the story more than on the time, and each story keeps one slot, so the two are confounded.
"""
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from src.config import (
    BUILD_LEAD_DAYS,
    LONG_SLOT_CANDIDATES,
    SHORT_SLOT_HOUR,
    SHORT_SLOT_MINUTE,
    SLOT_MIN_LEAD_MINUTES,
    SLOT_MIN_SAMPLES,
    SLOT_SWAP_BELOW,
    SLOT_TIMEZONE,
)
from src.database import get_slot_history, get_slots, set_slot, slot_stats, slot_taken

log = logging.getLogger(__name__)
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
_UTC = timezone.utc


def next_occurrence(weekday: int, hour: int, minute: int, after: datetime) -> datetime:
    """First moment strictly after `after` that is `weekday` at hour:minute in SLOT_TIMEZONE,
    returned in UTC. Arithmetic is done on the local wall clock, so the local time is preserved
    across a daylight-saving change."""
    tz = ZoneInfo(SLOT_TIMEZONE)
    local = after.astimezone(tz)
    cand = local.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=(weekday - local.weekday()) % 7)
    if cand.astimezone(_UTC) <= after.astimezone(_UTC):
        cand += timedelta(days=7)
    return cand.astimezone(_UTC)


def describe_slot(weekday: int, hour: int, minute: int = 0) -> str:
    """e.g. 'Friday 8 PM ET'."""
    h12 = hour % 12 or 12
    return f"{WEEKDAYS[weekday]} {h12}{f':{minute:02d}' if minute else ''} {'AM' if hour < 12 else 'PM'} ET"


def open_long_slots(now: datetime, *, lead_days: int = BUILD_LEAD_DAYS,
                    min_lead_minutes: int = SLOT_MIN_LEAD_MINUTES) -> list[tuple[int, datetime]]:
    """Weekly long slots inside the build window that are not yet filled, soonest first:
    [(slot_index, slot_time_utc)]. A slot closer than min_lead_minutes is skipped — there is not
    enough time left to build and upload before it."""
    start = now + timedelta(minutes=min_lead_minutes)
    end = now + timedelta(days=lead_days)
    out = []
    for slot in get_slots():
        t = next_occurrence(slot["weekday"], slot["hour_local"], slot["minute"], start - timedelta(seconds=1))
        while t <= end:
            if not slot_taken("long", t):
                out.append((slot["slot_index"], t))
            t = next_occurrence(slot["weekday"], slot["hour_local"], slot["minute"], t + timedelta(minutes=1))
    return sorted(out, key=lambda x: x[1])


def next_open_long_slot(now: datetime, *, force: bool = False) -> tuple[int, datetime] | None:
    """The slot to build for. Normally the soonest open slot inside the lead window; with force=True
    the window widens to two weeks so a manual run always finds something to do."""
    found = open_long_slots(now, lead_days=14 if force else BUILD_LEAD_DAYS)
    return found[0] if found else None


def next_short_slots(after: datetime, count: int, *, now: datetime | None = None,
                     min_lead_minutes: int = SLOT_MIN_LEAD_MINUTES) -> list[datetime]:
    """The next `count` free daily Short slots strictly after `after` (and no sooner than the minimum
    lead from `now`)."""
    now = now or datetime.now(_UTC)
    cursor = max(after, now + timedelta(minutes=min_lead_minutes)) - timedelta(seconds=1)
    out = []
    while len(out) < count:
        weekday = cursor.astimezone(ZoneInfo(SLOT_TIMEZONE)).weekday()
        # the next occurrence of ANY weekday: take the nearest of today's/tomorrow's slot
        nxt = min(next_occurrence((weekday + d) % 7, SHORT_SLOT_HOUR, SHORT_SLOT_MINUTE, cursor) for d in (0, 1))
        cursor = nxt
        if not slot_taken("short", nxt):
            out.append(nxt)
    return out


# ---------------------------------------------------------------------------
# learning which slots work
# ---------------------------------------------------------------------------
def slot_report() -> list[dict]:
    """One row per slot: its time and what its episodes achieved so far."""
    stats = slot_stats()
    return [{"slot_index": s["slot_index"], "when": describe_slot(s["weekday"], s["hour_local"], s["minute"]),
             **stats.get(s["slot_index"], {"n": 0, "avg_views": 0.0, "avg_retention": 0.0})} for s in get_slots()]


def evaluate_slots() -> dict | None:
    """A swap proposal {"slot_index", "old", "new", "reason"} or None. Conservative by design: no
    judgement until EVERY slot has SLOT_MIN_SAMPLES episodes with data (views depend on the story as
    much as on the time, so a few episodes prove nothing), only the single worst slot is ever touched,
    and only toward a slot the channel has never used before."""
    slots = get_slots()
    stats = slot_stats()
    if len(slots) < 2 or any(stats.get(s["slot_index"], {}).get("n", 0) < SLOT_MIN_SAMPLES for s in slots):
        return None
    ranked = sorted(slots, key=lambda s: stats[s["slot_index"]]["avg_views"])
    worst, best = ranked[0], ranked[-1]
    w, b = stats[worst["slot_index"]]["avg_views"], stats[best["slot_index"]]["avg_views"]
    if b <= 0 or w >= SLOT_SWAP_BELOW * b:
        return None
    used = get_slot_history()
    taken_days = {s["weekday"] for s in slots if s["slot_index"] != worst["slot_index"]}
    for wd, hr, mn in LONG_SLOT_CANDIDATES:
        if (wd, hr, mn) not in used and wd not in taken_days:
            return {"slot_index": worst["slot_index"],
                    "old": (worst["weekday"], worst["hour_local"], worst["minute"]), "new": (wd, hr, mn),
                    "reason": f"{describe_slot(worst['weekday'], worst['hour_local'])} averages {w:.0f} views vs "
                              f"{b:.0f} for {describe_slot(best['weekday'], best['hour_local'])}"}
    return None


def apply_slot_swap(plan: dict) -> None:
    set_slot(plan["slot_index"], *plan["new"])
    log.info("Schedule learning: moved slot %d from %s to %s — %s", plan["slot_index"],
             describe_slot(*plan["old"]), describe_slot(*plan["new"]), plan["reason"])
