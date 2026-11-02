"""
Multi-character crime / thriller / suspense / mystery / horror story
generation for the Hey Darky channel.

One LLM call returns a structured story: named characters plus a scene-by-scene
beat sheet where EVERY beat is either narration or one character's dialogue,
and carries its own visual description AND its own audio direction
(background-music mood, sound effect + kind + trigger word, optional dramatic
pause). That single JSON then drives every downstream stage:
  src/character_voices.py  -> per-character voices
  src/story_pipeline.py    -> one image per beat (Western-styled), captions
  src/audio_mixer.py       -> scene-matched BGM + exact-timestamp SFX
  src/platform_metadata.py -> per-platform titles / descriptions / hashtags

The channel strategy lives here too: every story is set in the same recurring
fictional American town (STORY_UNIVERSE_TOWN), is tagged with one content
pillar (chosen by src/pattern_analytics.py from real performance data), may
feature a recurring character, and is written for an English-speaking
audience that actually likes this genre.
"""
import logging
import random
import re

from src.config import (
    CHANNEL_NAME,
    STORY_LOCALE_NOTE,
    STORY_MAX_BGM_KEYWORDS,
    STORY_MAX_CHARACTERS,
    STORY_MAX_PAUSE_SEC,
    STORY_MAX_SCENES,
    STORY_MAX_WORDS,
    STORY_MIN_CHARACTERS,
    STORY_MIN_SCENES,
    STORY_MIN_WORDS,
    STORY_PILLAR_LABELS,
    STORY_PILLARS,
    STORY_RECURRING_CHARACTER_RATE,
    STORY_RECURRING_CHARACTERS,
    STORY_UNIVERSE_TOWN,
)
from src.llm_client import generate_json

log = logging.getLogger(__name__)

SFX_KINDS = ("ambient", "action", "none")
DEFAULT_BGM = "dark ambient drone"

STORY_PROMPT = """You are a screenwriter for the YouTube channel "{channel}", which
tells original {genre} stories as narrated short films — a documentary-style
narrator's voice wrapped around scripted dramatic scenes with real character
dialogue. The audience is English-speaking viewers who love horror, crime,
thriller, suspense and mystery stories. Viewers judge the video on ONE number:
what percentage are still watching at the end. Write for that.

{premise_instruction}

{research_block}
=====================================================================
SETTING & CHANNEL IDENTITY — read before writing anything
=====================================================================
{locale_note}

This story is set in or connected to the same recurring fictional town used
across this channel's stories: {universe_town}. Treat it like Stephen King's
"Castle Rock" — small authentic details (a diner, a specific road, a local
landmark) can recur across stories, building a sense of one real, continuous
place.

{recurring_character_instruction}

This story belongs to the content pillar: "{pillar_label}" ({pillar_key}).
Every beat and plot choice should clearly fit that pillar.

VISUAL RULE — every visual_description must depict a WESTERN (American) world:
American or European-looking people, clothing, homes, cars, objects, streets and
landscapes (Pacific Northwest forests, Midwest towns, New England harbors,
diners, gas stations, sheriff's cruisers, suburban cul-de-sacs). Never describe
non-Western settings, clothing or architecture.

=====================================================================
RETENTION MECHANICS (apply these, don't just label the genre)
=====================================================================
1. OPEN-LOOP STACKING: a question raised in the first 15 seconds must not be
   the only one — stack a new unresolved question before the last one
   resolves, all the way to the climax.
2. COLD OPEN: start inside a moment of tension or strangeness, not with flat
   scene-setting exposition.
3. DIALOGUE CARRIES CHARACTER, NOT INFORMATION DUMPS: reveal information
   through what people do or evade, not speeches.
4. ESCALATING STAKES: each scene raises tension from the last.
5. A GENUINE twist: the mid-point must recontextualize what the viewer thought
   was happening.
6. THE ENDING lands as a payoff, not a moral or a summary.

=====================================================================
TITLE STYLE — Reddit-confession style, not a generic label
=====================================================================
Write `title_long` as a specific, first-person, story-flavored title (at most
95 characters), like: "I worked the night shift at a lonely gas station. I
should have ignored the last customer." — NOT "A Scary Story From A Small
Town". It must be plain English, with no angle brackets.

THUMBNAIL: `thumbnail_concept` = ONE specific dark, atmospheric visual moment
from the story (not a generic dark background). `thumbnail_text` = at most 2
short English words to overlay (e.g. "DON'T ANSWER"). Favor dark blue/grey tones
with a small warm red-amber accent.

=====================================================================
CHARACTERS
=====================================================================
Create {min_characters}-{max_characters} named characters. For each: gender
(male/female — used to pick a matching voice, so it is required), a one-line
voice/personality note, and their role. Use Western/American names.

=====================================================================
BEATS
=====================================================================
Break the ENTIRE story into {min_scenes}-{max_scenes} short beats. Each beat is
either:
- "narration": third-person narrator, 1-3 sentences. Every distinct action or
  setting change should usually be its own beat.
- "dialogue": ONE character's spoken line (short).

Every beat needs its OWN visual_description — a specific, concrete image prompt
for exactly what is on screen in that beat.

Every beat ALSO carries audio direction (this drives the REAL background music
and sound effects mixed under the narration):
- "bgm_keyword": a 2-4 word music mood for this beat, e.g. "dark ambient
  drone", "tense suspense strings", "eerie piano". Beats sharing a mood MUST use
  the EXACT same string (it merges them into one music segment). Use at most
  {max_bgm} distinct moods in the whole story.
- "sfx_keyword": a short, concrete, searchable sound-effect phrase for what is
  physically audible in this beat (e.g. "door slam", "floorboard creak",
  "heavy rain", "crickets night", "gunshot", "woman scream", "footsteps
  gravel"), or "none".
- "sfx_kind": "ambient" (continuous background sound, looped: rain, wind,
  crickets), "action" (one-shot: door slam, scream, gunshot) or "none".
- "sfx_trigger_word": for an "action" effect, the exact word from this beat's
  "text" at which it should hit (e.g. "slammed"); otherwise "".
- "pause_after_sec": 0, or a dramatic silence of 2-{max_pause} seconds after the
  beat. Use sparingly (3-6 times in the whole story) — before a reveal or a
  jump scare.

Return ONLY this JSON schema:
{{
  "genre": "{genre}",
  "pillar": "{pillar_key}",
  "title": "short internal title",
  "title_long": "the Reddit-confession-style YouTube title (<= 95 chars)",
  "thumbnail_concept": "one specific dark atmospheric visual moment",
  "thumbnail_text": "1-2 words",
  "premise": "1-2 sentence premise",
  "universe_town": "{universe_town}",
  "recurring_character_used": "character name if a recurring cast member appears, else empty string",
  "characters": [
    {{"name": "character's name", "gender": "male", "role": "protagonist", "voice_note": "one line"}}
  ],
  "beats": [
    {{
      "beat_number": 1,
      "type": "narration",
      "speaker": "narrator",
      "text": "the narration line or the character's spoken line",
      "visual_description": "specific cinematic image prompt for exactly this beat",
      "emotion": "e.g. tension, dread, relief",
      "bgm_keyword": "dark ambient drone",
      "sfx_keyword": "heavy rain",
      "sfx_kind": "ambient",
      "sfx_trigger_word": "",
      "pause_after_sec": 0
    }}
  ],
  "hook": "the opening hook line",
  "loop_sentence": "the final payoff line",
  "description": "a 4-6 sentence English YouTube description; the first 125 characters are hook + keywords",
  "tags": ["tag1", "tag2"],
  "search_keywords": ["{genre} story", "scary story", "story narration"]
}}

Rules:
- {min_scenes}-{max_scenes} total beats.
- Total words across all beats' "text" must be between {min_words} and
  {max_words} (15-20 minutes at ~130 words/minute).
- A dialogue beat's "speaker" MUST exactly match a character "name".
- Everything (title, description, tags, dialogue, narration) is in ENGLISH only.
- Fully fictional: no real victims, real ongoing investigations or real
  identifiable people.
- Return ONLY valid JSON, no markdown fences, no commentary.
"""


def _clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _research_block(research: dict | None) -> str:
    """Real recent YouTube data for this niche (from src/topic_research.py),
    folded into the prompt as inspiration for title style / keywords / tags —
    explicitly NOT as material to copy."""
    if not research or not research.get("sample_size"):
        return ""
    lines = [
        "REAL RECENT DATA from YouTube for this niche — use it ONLY to inform "
        "title style, keywords and tags. NEVER copy a title, plot or character "
        "from it:",
    ]
    if research.get("top_titles"):
        lines.append("  Top recent titles: " + " | ".join(research["top_titles"][:8]))
    if research.get("suggested_keywords"):
        lines.append("  Common title words: " + ", ".join(research["suggested_keywords"][:12]))
    if research.get("suggested_tags"):
        lines.append("  Common tags: " + ", ".join(research["suggested_tags"][:12]))
    return "\n".join(lines) + "\n"


def _tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z']+", str(name).lower()))


def _match_speaker(speaker: str, names: list[str]) -> str | None:
    """Map the model's speaker label onto a real character name: exact
    (case-insensitive) first, then unambiguous word overlap ("Sheriff Garrett"
    -> "Sheriff Tom Garrett", "Tom" -> "Sheriff Tom Garrett")."""
    sp = _clean(speaker)
    if not sp:
        return None
    for n in names:
        if n.lower() == sp.lower():
            return n
    st = _tokens(sp)
    hits = [n for n in names if st and (st <= _tokens(n) or _tokens(n) <= st)]
    return hits[0] if len(hits) == 1 else None


def _repair_structure(story: dict) -> None:
    """Fix the commonest ways an LLM bends the schema, in place, so a fixable
    story is never thrown away (a discarded story costs a retry = scarce Gemini
    quota, and a failed run publishes nothing):
      * beats with no text are dropped; markdown symbols removed from the text
      * unknown/missing beat type is inferred from the speaker
      * a dialogue speaker that matches no character is matched by name overlap,
        else the beat becomes narration (the line is still spoken, by the narrator)
      * a leading "Name:" prefix is stripped from dialogue text
      * a missing visual_description is built from the beat's own text
      * beats are renumbered 1..N
    """
    characters = [c for c in story.get("characters", []) if isinstance(c, dict) and _clean(c.get("name"))]
    for c in characters:
        c["name"] = _clean(c["name"])
        g = _clean(c.get("gender")).lower()
        c["gender"] = g if g in ("male", "female") else c.get("gender", "")
    story["characters"] = characters
    names = [c["name"] for c in characters]

    kept = []
    for b in story.get("beats", []) if isinstance(story.get("beats"), list) else []:
        if not isinstance(b, dict):
            continue
        text = re.sub(r"[*_#`]", "", _clean(b.get("text")))
        if not text:
            continue
        b["text"] = text
        kind = _clean(b.get("type")).lower()
        speaker = _clean(b.get("speaker"))
        if kind not in ("narration", "dialogue"):
            kind = "dialogue" if speaker and speaker.lower() not in ("narrator", "narration") else "narration"
        if kind == "dialogue":
            matched = _match_speaker(speaker, names)
            if matched:
                b["speaker"] = matched
                b["text"] = re.sub(rf"^\s*{re.escape(matched)}\s*:\s*", "", b["text"], flags=re.I) or b["text"]
            else:
                kind = "narration"
        if kind == "narration":
            b["speaker"] = "narrator"
        b["type"] = kind
        if not _clean(b.get("visual_description")):
            b["visual_description"] = f"a cinematic scene: {b['text'][:160]}"
        b.setdefault("emotion", "tension")
        kept.append(b)
    for n, b in enumerate(kept, start=1):
        b["beat_number"] = n
    story["beats"] = kept


def _normalize_story(story: dict) -> None:
    """Repair structure, then fill / clamp the audio-direction fields in place so
    a slightly sloppy LLM answer never costs a retry. Genuinely unusable stories
    (far too few beats / words) are still rejected by _validate_story."""
    _repair_structure(story)
    beats = story.get("beats", [])
    last_bgm = DEFAULT_BGM
    allowed: list[str] = []
    for beat in beats:
        bgm = _clean(beat.get("bgm_keyword")).lower() or last_bgm
        if bgm not in allowed:
            if len(allowed) >= STORY_MAX_BGM_KEYWORDS:
                bgm = allowed[-1]  # too many moods: fold the extras into the latest allowed one
            else:
                allowed.append(bgm)
        beat["bgm_keyword"] = bgm
        last_bgm = bgm

        kw = _clean(beat.get("sfx_keyword")).lower()
        kind = _clean(beat.get("sfx_kind")).lower()
        if not kw or kw == "none" or kind not in ("ambient", "action"):
            kw, kind = "none", "none"
        beat["sfx_keyword"], beat["sfx_kind"] = kw, kind
        beat["sfx_trigger_word"] = _clean(beat.get("sfx_trigger_word")) if kind == "action" else ""

        try:
            pause = float(beat.get("pause_after_sec") or 0)
        except (TypeError, ValueError):
            pause = 0.0
        beat["pause_after_sec"] = 0.0 if pause < 2.0 else min(pause, STORY_MAX_PAUSE_SEC)

    text = _clean(story.get("thumbnail_text")).upper()
    story["thumbnail_text"] = " ".join(text.split()[:2])[:24]
    story["title_long"] = _clean(story.get("title_long")) or _clean(story.get("title"))


def _validate_story(story: dict) -> None:
    """The prompt asks for 24-45 beats / 1950-2600 words; ACCEPTANCE is looser
    (18-67 beats, 1170-3900 words) because a slightly short or long story is
    still a good video, while rejecting it wastes a Gemini call."""
    beats = story.get("beats", [])
    lo_b, hi_b = int(STORY_MIN_SCENES * 0.75), int(STORY_MAX_SCENES * 1.5)
    if not (lo_b <= len(beats) <= hi_b):
        raise ValueError(f"Beat count {len(beats)} outside accepted range {lo_b}-{hi_b}")

    characters = story.get("characters", [])
    if not (1 <= len(characters) <= 8):
        raise ValueError(f"Character count {len(characters)} outside accepted range 1-8")

    character_names = {c["name"] for c in characters if "name" in c}
    for beat in beats:
        if beat.get("type") not in ("narration", "dialogue"):
            raise ValueError(f"Beat {beat.get('beat_number')} has invalid type {beat.get('type')!r}")
        if beat.get("type") == "dialogue" and beat.get("speaker") not in character_names:
            raise ValueError(
                f"Beat {beat.get('beat_number')} speaker "
                f"{beat.get('speaker')!r} doesn't match any character name"
            )
        if not _clean(beat.get("text")) or not _clean(beat.get("visual_description")):
            raise ValueError(f"Beat {beat.get('beat_number')} is missing text or visual_description")

    total_words = sum(len(b.get("text", "").split()) for b in beats)
    lo_w, hi_w = int(STORY_MIN_WORDS * 0.6), int(STORY_MAX_WORDS * 1.5)
    if not (lo_w <= total_words <= hi_w):
        raise ValueError(f"Total word count {total_words} outside accepted range {lo_w}-{hi_w}")
    story["_computed_word_count"] = total_words


def write_story(
    genre: str,
    premise: str = "",
    pillar: str | None = None,
    research: dict | None = None,
    max_retries: int = 1,
) -> dict:
    """genre must be one of src.config.STORY_GENRES. `premise` seeds the story
    (else the model invents one). `pillar` forces a content pillar; if None,
    src.pattern_analytics.suggest_next_pillar() picks one from real
    performance data. `research` is a src.topic_research.research_niche()
    result folded into the prompt as inspiration. max_retries is deliberately
    small — see src/llm_client.py for how Gemini quota is protected."""
    from src.config import STORY_GENRES

    if genre not in STORY_GENRES:
        raise ValueError(f"Unknown genre {genre!r}; must be one of {STORY_GENRES}")
    if pillar is not None and pillar not in STORY_PILLARS:
        raise ValueError(f"Unknown pillar {pillar!r}; must be one of {STORY_PILLARS}")
    if pillar is None:
        from src.pattern_analytics import suggest_next_pillar

        pillar = suggest_next_pillar()

    premise_instruction = (
        f"Build the story around this premise/seed idea: {premise}"
        if premise
        else "Invent an original premise within this genre — avoid the most obvious cliché setup."
    )

    chosen = None
    if STORY_RECURRING_CHARACTERS and random.random() < STORY_RECURRING_CHARACTER_RATE:
        chosen = random.choice(STORY_RECURRING_CHARACTERS)
    if chosen:
        recurring_character_instruction = (
            f"Include this recurring cast member as one of your characters: "
            f"{chosen['name']} ({chosen['gender']}, {chosen['note']}). Keep them "
            f"consistent with that description and set \"recurring_character_used\" "
            f"to their exact name."
        )
    else:
        recurring_character_instruction = (
            "No recurring cast member is needed this time — all-new characters are "
            "fine. Set \"recurring_character_used\" to an empty string."
        )

    prompt = STORY_PROMPT.format(
        channel=CHANNEL_NAME,
        genre=genre,
        premise_instruction=premise_instruction,
        research_block=_research_block(research),
        locale_note=STORY_LOCALE_NOTE,
        universe_town=STORY_UNIVERSE_TOWN,
        recurring_character_instruction=recurring_character_instruction,
        pillar_key=pillar,
        pillar_label=STORY_PILLAR_LABELS[pillar],
        min_characters=STORY_MIN_CHARACTERS,
        max_characters=STORY_MAX_CHARACTERS,
        min_scenes=STORY_MIN_SCENES,
        max_scenes=STORY_MAX_SCENES,
        min_words=STORY_MIN_WORDS,
        max_words=STORY_MAX_WORDS,
        max_bgm=STORY_MAX_BGM_KEYWORDS,
        max_pause=int(STORY_MAX_PAUSE_SEC),
    )

    last_err = None
    for attempt in range(max_retries + 1):
        try:
            story = generate_json(prompt, temperature=0.95)
            if isinstance(story, list) and len(story) == 1 and isinstance(story[0], dict):
                story = story[0]            # some answers wrap the object in a list
            if not isinstance(story, dict):
                raise ValueError(f"Gemini returned {type(story).__name__}, expected a JSON object")
            # Our own decisions are authoritative, whatever the model echoed back.
            story["genre"] = genre
            story["pillar"] = pillar
            story["universe_town"] = STORY_UNIVERSE_TOWN
            story.setdefault("recurring_character_used", chosen["name"] if chosen else "")
            _normalize_story(story)
            _validate_story(story)
            return story
        except Exception as e:
            last_err = e
            log.warning("Story attempt %d/%d failed: %s", attempt + 1, max_retries + 1, e)

    raise RuntimeError(f"Failed to generate a valid {genre} story: {last_err}")
