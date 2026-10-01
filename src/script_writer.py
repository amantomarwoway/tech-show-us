"""
Turns a word + etymology research into a full mystery/suspense/thriller
script broken into scenes ready for TTS + visual generation.

The prompt below is deliberately long and prescriptive about RETENTION
specifically (not just content correctness) — a script that is factually
fine but paced like a textbook will still lose viewers by the 30% mark.
Every section of the prompt maps to a concrete, well-documented YouTube
retention mechanism (open loops / Zeigarnik effect, pattern interrupts,
specificity over abstraction, escalating stakes) rather than vague
"make it engaging" instructions, because vague instructions are what the
previous version of this prompt had and it produced correct-but-flat
scripts.
"""
import logging

from src.config import LONG_MAX_SCENES, LONG_MAX_WORDS, LONG_MIN_SCENES, LONG_MIN_WORDS
from src.llm_client import generate_json

log = logging.getLogger(__name__)

SCRIPT_PROMPT = """You are a retention-obsessed YouTube scriptwriter for the
channel "WordsThatSpeaks" (ONE WORD = ONE CINEMATIC STORY — etymology +
psychology, mystery/suspense/thriller tone, think Freudian depth meets
true-crime-documentary pacing). Your scripts are judged ONLY by one number:
what percentage of viewers are still watching at the end. A factually
perfect script that loses half its audience by minute 2 is a failure. A
slightly less exhaustive script that keeps 80% of viewers to the loop payoff
is a success. Write for that second outcome.

WORD: {word}
RESEARCH (may be partial — use your own knowledge to fill gaps, but never
invent fake statistics or fake study citations; keep numeric claims
general/qualitative if you are not confident of an exact figure):
- Wiktionary: {wiktionary}
- Wikipedia: {wikipedia}
- Suggested angle: {angle}

=====================================================================
RETENTION MECHANICS — apply these, don't just mention "mystery/suspense"
=====================================================================

1. OPEN-LOOP STACKING, not one hook then flat exposition. A single hook at
   0:00 that gets "resolved" by minute 2 and then settles into lecture mode
   is the single most common way scripts like this lose viewers. Instead:
   open loop #1 at the very first sentence, open loop #2 (a DIFFERENT
   question) before loop #1 is even answered, and keep at least one loop
   open at all times until the final payoff closes the last one. Think of
   it as a chain, not a single arc: hook -> partial answer that raises a
   bigger question -> partial answer that raises a bigger question -> ...
   -> payoff that finally closes everything at once.

2. THE FIRST 15 SECONDS ARE WHERE MOST VIEWERS DECIDE TO LEAVE. No channel
   intro, no "in this video", no throat-clearing. The very first sentence
   must be the hook itself — a claim, a contradiction, or a question so
   specific and strange that NOT knowing the answer is uncomfortable. Bad:
   "Have you ever wondered about ego?" (generic, answerable with "not
   really", zero stakes). Good: a concrete, slightly unsettling claim
   that's immediately about THEM, the viewer, not about the word as a
   dictionary entry.

3. SPECIFICITY BEATS ABSTRACTION, always. "Psychologists say this trait is
   complex" retains nobody. One vivid, concrete, sensory image, scenario,
   or moment does. If you catch yourself writing an abstract psychological
   claim, immediately follow it with a specific, visualizable instance of
   it — a moment, a room, a decision, a feeling in the body — not another
   abstract claim layered on top.

4. ESCALATING STAKES, not escalating information. Each scene should raise
   the emotional temperature from the last one, not just add another fact.
   If scene 3 is "interesting," scene 4 needs to feel more urgent or more
   personal than scene 3, not just more detailed.

5. PATTERN INTERRUPTS roughly every 20-40 seconds of runtime: a direct
   question to the viewer, a sentence-length change (several short, punchy
   sentences after a longer immersive one), a reversal ("but here's what
   nobody tells you"), or a sudden zoom from abstract to intensely
   specific. Monotone pacing — same sentence rhythm, same information
   density, scene after scene — is the second most common way these
   scripts lose viewers, right after a weak opening.

6. RE-HOOKS at the 30-60 SECOND mark and again at the 40-60% mark of total
   runtime are NON-NEGOTIABLE, not decorative. These are the two
   best-documented drop-off cliffs in long-form YouTube retention curves.
   Each re-hook must introduce a genuinely new question or twist — not
   rephrase the opening hook, actually complicate it.

7. SECOND PERSON, OFTEN. "You" does something a third-person psychological
   description never does: it makes the claim about the viewer's own mind
   right now, while they're watching. Don't overload every sentence with
   it, but return to it deliberately at emotional high points.

8. THE LOOP PAYOFF MUST RE-CONTEXTUALIZE THE HOOK, not just repeat it. The
   viewer should feel like the opening line meant something different than
   they thought when they first heard it — that's what makes a loop payoff
   land as satisfying rather than just "and that's why X matters, thanks
   for watching."

=====================================================================
BANNED PATTERNS — these are the specific tells of a flat, AI-flavored
script, and a human editor would cut every one of them on sight
=====================================================================
- NEVER open with "In this video", "Today we're going to talk about",
  "Have you ever wondered", "Let's dive in", "Without further ado", or any
  equivalent throat-clearing. Start IN the hook, first word.
- NEVER end a section with "In conclusion", "To sum up", or anything that
  sounds like a lecture wrapping up — this breaks the narrative spell.
- NEVER stack more than two sentences in a row with the same opening
  structure (e.g. three sentences in a row starting with "This means...").
- NEVER use a rhetorical question as a crutch more than 2-3 times total in
  the whole script — overused rhetorical questions ("Crazy, right?") read
  as filler, not curiosity, and viewers tune them out fast.
- NEVER let a scene be pure information delivery with no emotional or
  narrative movement — if a scene could be a Wikipedia paragraph with the
  serial numbers filed off, rewrite it.

=====================================================================
STRUCTURE (target 750-1300 words total, ~130 words/minute pacing)
=====================================================================
Pace these as PROPORTIONS of total runtime, not fixed minute-marks (your
actual scene count and total words will vary):
1. Hook (first ~5% of runtime): the strongest, strangest, most specific
   claim or question you have. This is not a preview — it IS the opening.
2. Origin Twist (~5-20%): true etymology, reframed as a reveal, not a
   definition — something the viewer did not expect going in.
3. Suspense / People Connection (~20-50%): a vivid, specific human
   scenario (avoid inventing fake precise statistics) that makes the
   abstract concept feel like something happening to a real person, right
   now, that could be the viewer.
4. Thriller Revelation (~50-85%): the deeper psychological mechanism — why
   this trait/concept exists, what it protects or threatens, escalating to
   the highest stakes point of the whole script.
5. Loop Payoff (final ~15%): closes every open loop at once, re-contextualizes
   the hook, lands on a final line that stays with the viewer after the
   video ends.

Break the narration into 6 to 10 scenes. Return ONLY this JSON schema:
{{
  "word": "{word}",
  "hook": "the opening hook sentence",
  "loop_sentence": "the closing sentence that mirrors AND re-contextualizes the hook",
  "full_script_word_count": 000,
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "100-150 words of narration for this scene",
      "visual_prompt": "cinematic, word '{word_upper}' in big gold 3D letters, human shadow silhouette interacting with the letters, mysterious dark background, dramatic rim light, high contrast, 8K, photorealistic, teal-orange grading",
      "emotion": "e.g. unease, curiosity, tension, release",
      "fact": "a factual nugget grounding this scene (or empty string)",
      "people_connection": "a relatable human angle for this scene (or empty string)",
      "duration_hint_sec": 60
    }}
  ],
  "title": "50-60 char YouTube title, front-loaded with the word",
  "description": "a 5-6 sentence YouTube description, first 125 chars = hook + keywords",
  "chapters": [{{"timestamp": "0:00", "label": "Hook"}}],
  "tags": ["tag1", "tag2"],
  "search_keywords": ["{word} meaning", "{word} definition", "what is {word}"],
  "evergreen_keywords": ["psychology of {word}"]
}}

Rules:
- {min_scenes}-{max_scenes} scenes total.
- Total narration word count must land between {min_words} and {max_words} words.
- Every visual_prompt must mention the word in gold 3D letters + a human shadow
  interacting with it, to keep visual identity consistent across the video.
- Do not fabricate specific named studies, specific numeric statistics, or
  specific institutions unless you are confident they are real; prefer general,
  well-hedged phrasing ("research suggests", "many psychologists note") over
  invented precision.
- Before finalizing, check your own draft against the BANNED PATTERNS list
  above and rewrite any line that matches one.
- Return ONLY valid JSON, no markdown fences, no commentary.
"""


def _validate_script(script: dict) -> None:
    scenes = script.get("scenes", [])
    if not (LONG_MIN_SCENES <= len(scenes) <= LONG_MAX_SCENES):
        raise ValueError(f"Scene count {len(scenes)} outside allowed range")
    total_words = sum(len(s.get("narration", "").split()) for s in scenes)
    if not (LONG_MIN_WORDS * 0.7 <= total_words <= LONG_MAX_WORDS * 1.3):
        # Soft tolerance band; hard failure only if wildly off.
        raise ValueError(f"Total narration word count {total_words} far outside target range")
    script["_computed_word_count"] = total_words


def write_script(word: str, research: dict, angle: str = "", max_retries: int = 2) -> dict:
    prompt = SCRIPT_PROMPT.format(
        word=word,
        word_upper=word.upper(),
        wiktionary=research.get("wiktionary_definitions", "") or "(none found)",
        wikipedia=research.get("wikipedia_summary", "") or "(none found)",
        angle=angle or "(none provided — invent one)",
        min_scenes=LONG_MIN_SCENES,
        max_scenes=LONG_MAX_SCENES,
        min_words=LONG_MIN_WORDS,
        max_words=LONG_MAX_WORDS,
    )

    last_err = None
    for attempt in range(max_retries + 1):
        try:
            script = generate_json(prompt, temperature=0.9)
            _validate_script(script)
            return script
        except Exception as e:
            last_err = e
            log.warning("Script attempt %d/%d failed: %s", attempt + 1, max_retries + 1, e)

    raise RuntimeError(f"Failed to generate a valid script for '{word}': {last_err}")
