"""
Turns a word + etymology research into a full mystery/suspense/thriller
script broken into scenes ready for TTS + visual generation.
"""
import logging

from src.config import LONG_MAX_SCENES, LONG_MAX_WORDS, LONG_MIN_SCENES, LONG_MIN_WORDS
from src.llm_client import generate_json

log = logging.getLogger(__name__)

SCRIPT_PROMPT = """You are writing a psychological-thriller-style YouTube video
script for the channel "WordsThatSpeaks". Format: ONE WORD = ONE CINEMATIC STORY,
mixing etymology, psychology, a real study or example, and a mystery/suspense/
thriller narrative tone. Think Freudian depth meets true-crime-documentary pacing.

WORD: {word}
RESEARCH (may be partial — use your own knowledge to fill gaps, but never invent
fake statistics or fake study citations; keep numeric claims general/qualitative
if you are not confident of an exact figure):
- Wiktionary: {wiktionary}
- Wikipedia: {wikipedia}
- Suggested angle: {angle}

STRUCTURE (target 750-1300 words total, ~130 words/minute pacing, 5-10 minutes):
1. Mystery Hook (0-30s): an unsettling, curiosity-gap opening line about the word.
2. Origin Twist (~30s-2m): true etymology, with a surprising reframe.
3. Suspense / People Connection (~2m-5m): a relatable human example or general
   real-world pattern (avoid inventing fake precise statistics).
4. Thriller Revelation (~5m-8m): the deeper psychological mechanism — why this
   trait/concept exists and what it protects or threatens.
5. Loop Payoff (~8m-10m): a closing line that calls back to and re-contextualizes
   the opening hook.

Also weave in one re-hook (a fresh question or twist) around the 30-60 second
mark and another around the 40-60% mark of the runtime.

Break the narration into 6 to 10 scenes. Return ONLY this JSON schema:
{{
  "word": "{word}",
  "hook": "the opening hook sentence",
  "loop_sentence": "the closing sentence that mirrors the hook",
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
