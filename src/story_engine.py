"""
Lightweight retention analysis on top of a generated script:
- verifies the loop payoff actually echoes the hook (heuristic word-overlap check,
  logged only — not a hard gate, since Gemini already targets this in the prompt)
- scores scenes for "best segment" selection, used by short_deriver to choose
  which two ~20-35s windows to cut into Shorts.
"""
import logging

log = logging.getLogger(__name__)

# Keywords whose presence in a scene's `emotion` field indicate strong
# stand-alone hook/twist potential for a Short.
HIGH_ENERGY_EMOTIONS = {
    "tension", "unease", "curiosity", "shock", "suspense", "revelation", "fear",
}


def check_loop_closure(script: dict) -> bool:
    """Heuristic: does the loop sentence share meaningful words with the hook?"""
    hook = set(script.get("hook", "").lower().split())
    loop = set(script.get("loop_sentence", "").lower().split())
    overlap = hook & loop
    # Filter out trivial stopwords so the check means something.
    stopwords = {"the", "a", "an", "is", "your", "it", "and", "to", "of", "in"}
    meaningful_overlap = overlap - stopwords
    closed = len(meaningful_overlap) > 0
    if not closed:
        log.warning(
            "Loop payoff does not clearly echo the hook — hook=%r loop=%r",
            script.get("hook"), script.get("loop_sentence"),
        )
    return closed


def score_scene_for_short(scene: dict, position_index: int, total_scenes: int) -> float:
    """Higher score = better standalone hook/twist material for a Short."""
    score = 0.0
    emotion = str(scene.get("emotion", "")).lower()
    if any(word in emotion for word in HIGH_ENERGY_EMOTIONS):
        score += 3.0
    # Early scenes (hook/twist) and late-middle scenes (thriller reveal) are
    # the best Short material; middle exposition scenes score lower.
    relative_pos = position_index / max(total_scenes - 1, 1)
    if relative_pos <= 0.25 or 0.55 <= relative_pos <= 0.85:
        score += 2.0
    if scene.get("people_connection"):
        score += 1.0
    narration_len = len(scene.get("narration", "").split())
    # Prefer scenes close to a natural 20-35s narration length at ~130wpm
    # (~43-76 words), to minimize awkward cutting.
    if 35 <= narration_len <= 90:
        score += 1.5
    return score


def pick_best_segments_for_shorts(script: dict, n: int = 2) -> list[dict]:
    scenes = script.get("scenes", [])
    scored = [
        (score_scene_for_short(s, i, len(scenes)), i, s)
        for i, s in enumerate(scenes)
    ]
    scored.sort(key=lambda t: t[0], reverse=True)
    # Ensure the two picks aren't adjacent duplicates of the same beat where possible.
    picks = []
    used_indices = set()
    for _, idx, scene in scored:
        if len(picks) >= n:
            break
        if any(abs(idx - u) <= 0 for u in used_indices):
            continue
        picks.append(scene)
        used_indices.add(idx)
    # Fallback: if not enough distinct picks, just take top-n regardless.
    if len(picks) < n:
        picks = [s for _, _, s in scored[:n]]
    return picks
