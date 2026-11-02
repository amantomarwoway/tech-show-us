"""
"DNA pattern" performance learning — the channel-strategy loop from
README "Channel strategy": publish, measure retention/CTR, find what this
audience likes, make the next story lean toward that pattern, repeat.

This module doesn't hardcode the literal "video 1-10 / 11-20 / 21-30"
phase boundaries from that strategy as fixed thresholds — it implements
the same INTENT (explore evenly with no data, gradually weight toward
what's working as real data accumulates, never fully lock out the other
pillars) driven by how much performance data actually exists, which
naturally tracks the same curve without brittle magic numbers tied to an
exact video count.
"""
import logging
import random

from src.config import STORY_PILLARS
from src.database import get_pillar_stats

log = logging.getLogger(__name__)

# A pillar needs at least this many performance-tracked videos before its
# average is trusted enough to influence selection — below this, a single
# unusually good/bad video could swing the whole pillar's apparent
# performance.
MIN_SAMPLE_FOR_CONFIDENCE = 3

# Even once pillars are performance-ranked, each one keeps at least this
# fraction of "flat" selection weight — this is what stops the system from
# fully locking onto one pillar forever (the strategy doc's "YouTube ko
# audience batane ki koshish mat karo" principle: stay genuinely varied
# enough for the audience/algorithm to keep telling you what's working,
# rather than assuming you already know for good).
EXPLORATION_FLOOR = 0.3

# A pillar with performance data defaults to this score if its retention
# number is missing for some reason — deliberately not zero, so a data
# hiccup doesn't make a pillar look artificially terrible.
DEFAULT_RETENTION_SCORE = 0.3


def get_pillar_ranking() -> list[tuple[str, dict]]:
    """Returns [(pillar, stats_dict), ...] sorted by avg_retention
    descending, for pillars with enough confirmed performance data
    (>= MIN_SAMPLE_FOR_CONFIDENCE). Pillars without enough data are
    omitted — not scored as zero, just not ranked yet."""
    stats = get_pillar_stats()
    confident = {
        p: s for p, s in stats.items() if s.get("count", 0) >= MIN_SAMPLE_FOR_CONFIDENCE
    }
    return sorted(confident.items(), key=lambda item: item[1]["avg_retention"], reverse=True)


def suggest_next_pillar() -> str:
    """Returns the pillar to use for the next story.

    - If fewer than 2 pillars have enough confirmed performance data yet
      (MIN_SAMPLE_FOR_CONFIDENCE each), there's nothing meaningful to
      differentiate on — picks uniformly at random across all pillars.
      This is the early-channel "explore evenly, gather signal" phase,
      sized by actual data rather than a hardcoded video count.
    - Once at least 2 pillars have enough data, performance-weights the
      choice (stronger average retention -> higher chance of being picked
      again) while EXPLORATION_FLOOR guarantees every pillar — including
      ones with no data yet, or weaker-performing ones — keeps a real
      chance of being chosen, so the system can't permanently write off a
      pillar on a small or temporarily-unlucky sample.
    """
    stats = get_pillar_stats()
    ranked = get_pillar_ranking()

    if len(ranked) < 2:
        choice = random.choice(STORY_PILLARS)
        log.info(
            "Not enough performance data to differentiate pillars yet "
            "(%d/%d pillars have >= %d tracked videos) — exploring evenly. Picked: %s",
            len(ranked), len(STORY_PILLARS), MIN_SAMPLE_FOR_CONFIDENCE, choice,
        )
        return choice

    scores = {
        p: stats.get(p, {}).get("avg_retention", DEFAULT_RETENTION_SCORE)
        for p in STORY_PILLARS
    }
    total_score = sum(scores.values()) or 1.0
    weights = [
        EXPLORATION_FLOOR / len(STORY_PILLARS)
        + (1 - EXPLORATION_FLOOR) * (scores[p] / total_score)
        for p in STORY_PILLARS
    ]
    choice = random.choices(STORY_PILLARS, weights=weights, k=1)[0]
    log.info(
        "Pillar performance ranking: %s — weighted pick: %s",
        [(p, round(s["avg_retention"], 3)) for p, s in ranked], choice,
    )
    return choice
