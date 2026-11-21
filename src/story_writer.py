"""
Writes ONE EPISODE (part) of a multi-part crime / thriller / suspense / mystery / horror series for
the Hey Darky channel. One LLM call returns the whole episode as structured JSON:

  characters + a scene-by-scene beat sheet; every beat is narration or one character's dialogue and
  carries its own image prompt, its own audio direction (music mood, sound effect + kind + trigger
  word, dramatic pause) and its own emotion tags. Part 1 also returns the SERIES (title, planned
  length, arc, character appearances); every part returns a series_update (rolling recap, open
  threads, cliffhanger) that is stored in the series bible so the next part continues the same story.

What the writer is held to (and what is VALIDATED, retrying with feedback if it is missing):
  * the five emotions the audience comes for — fear (incl. a jumpscare), curiosity, suspense,
    excitement, mystery — each on at least ELEMENT_MIN_BEATS beats, tagged per beat;
  * a hook in the first ~30 seconds (the opening beats carry at least two of fear / suspense /
    curiosity / mystery);
  * a cliffhanger at the end of every part except the finale.

Robustness: a slightly sloppy answer is REPAIRED (speaker names matched, empty beats dropped, long
beats split into image-sized beats, stage directions removed) instead of rejected, because a rejected
story costs a Gemini call and a failed run publishes nothing.
"""
import logging
import random
import re

from src.config import (
    CHANNEL_NAME,
    ELEMENT_MIN_BEATS,
    MIN_JUMPSCARES,
    SERIES_PARTS_RANGE,
    STORY_ELEMENTS,
    STORY_LOCALE_NOTE,
    STORY_MAX_BEAT_WORDS,
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
    STORY_SPLIT_ABOVE_WORDS,
    STORY_UNIVERSE_TOWN,
)
from src.llm_client import generate_json
from src.series_bible import merged_characters

log = logging.getLogger(__name__)

SFX_KINDS = ("ambient", "action", "none")
DEFAULT_BGM = "dark ambient drone"
ELEMENT_NAMES = tuple(STORY_ELEMENTS)
HOOK_ELEMENTS = ("fear", "suspense", "curiosity", "mystery")
HOOK_BEATS = 4

STORY_PROMPT = """You are a screenwriter for the YouTube channel "{channel}", which tells original
{genre} stories as narrated short films, released as MULTI-PART SERIES — a new part every week, like a
TV show. The audience is English-speaking viewers who love horror, crime, thriller, suspense and
mystery stories and watch late at night. Viewers judge a part on ONE number: what percentage are still
watching at the end — and on whether they come back for the next part. Write for both.

{premise_instruction}

{research_block}
{series_block}
=====================================================================
SETTING & CHANNEL IDENTITY
=====================================================================
{locale_note}

The channel's stories share one recurring fictional town, {universe_town} (think Stephen King's
"Castle Rock"): small authentic details — a diner, a road, a landmark — recur across stories.

{recurring_character_instruction}

Content pillar: "{pillar_label}" ({pillar_key}). Every beat and plot choice should clearly fit it.

VISUAL RULE — every visual_description must depict a WESTERN (American) world: American or
European-looking people, clothing, homes, cars, objects, streets and landscapes (Pacific Northwest
forests, Midwest towns, New England harbors, diners, gas stations, sheriff's cruisers, suburban
cul-de-sacs). Never describe non-Western settings, clothing or architecture.

=====================================================================
THE FIVE THINGS EVERY PART MUST DELIVER — woven through the WHOLE part, not crammed into one scene
=====================================================================
{elements_block}

Tag every beat in "elements" with the ones it delivers (use exactly: fear, curiosity, suspense,
excitement, mystery; a beat may carry several, or none). EACH element must appear on at least
{element_min} beats. Include at least {min_jumpscares} JUMPSCARE: a sudden terrifying moment. Set
"jumpscare": true on that beat, give the beat BEFORE it "pause_after_sec": 3 (a held-breath silence)
and give the jumpscare beat an "action" sound effect (e.g. "woman scream", "door slam", "glass shatter").

=====================================================================
THE FIRST 30 SECONDS DECIDE EVERYTHING
=====================================================================
The first {hook_beats} beats are the HOOK. Open on the part's most shocking image, line or unanswered
question (a flash-forward to the climax is fine, then continue from the start), so a viewer who
watches only 30 seconds is already hooked. Tag those opening beats with at least two of: fear,
suspense, curiosity, mystery.

=====================================================================
RETENTION MECHANICS
=====================================================================
1. OPEN-LOOP STACKING: stack a new unresolved question before the last one resolves.
2. DIALOGUE CARRIES CHARACTER, NOT INFORMATION DUMPS: reveal information through what people do or evade.
3. ESCALATING STAKES: each scene raises tension from the last.
4. A GENUINE twist near the middle that recontextualizes what the viewer thought was happening.
5. THE END of the part: {ending_rule}

=====================================================================
TITLE & THUMBNAIL
=====================================================================
`title_long`: a specific, first-person, story-flavored hook of AT MOST 70 characters, in plain English,
no angle brackets — e.g. "I worked the night shift at a lonely gas station." The part number and search
keywords are added to it automatically — do NOT write "Part 2" yourself.
`thumbnail_concept`: ONE specific dark, atmospheric visual moment from this part (not a generic dark
background). `thumbnail_text`: at most 2 short English words to overlay (or "" for none).

=====================================================================
CHARACTERS
=====================================================================
{characters_rule}

=====================================================================
BEATS
=====================================================================
Break the ENTIRE part into {min_scenes}-{max_scenes} short beats. Each beat is either:
- "narration": third-person narrator, ONE or TWO sentences and AT MOST {max_beat_words} words (about 12
  seconds of speech). Every beat gets its own image, so a long paragraph in one beat means a static
  screen. Every distinct action, glance or setting change should be its own beat.
- "dialogue": ONE character's spoken line (short).

Every beat needs its OWN visual_description — a specific, concrete image prompt for exactly what is on
screen in that beat. Every beat ALSO carries audio direction (it drives the REAL music and sound effects):
- "bgm_keyword": a 2-3 word music mood. These phrases are SEARCHED on a sound library, so prefer proven
  ones: "dark ambient drone", "tense suspense strings", "eerie piano", "low synth pad", "ominous
  ambience", "horror atmosphere", "slow heartbeat", "cinematic tension", "creepy music box". Beats sharing
  a mood MUST use the EXACT same string. At most {max_bgm} distinct moods in the whole part.
- "sfx_keyword": a short, concrete, searchable sound-effect phrase for what is physically audible in
  this beat ("door slam", "floorboard creak", "heavy rain", "crickets night", "gunshot", "woman scream",
  "footsteps gravel"), or "none".
- "sfx_kind": "ambient" (continuous: rain, wind, crickets), "action" (one-shot: door slam, scream,
  gunshot) or "none".
- "sfx_trigger_word": for an "action" effect, the exact word of this beat's text at which it hits; else "".
- "pause_after_sec": 0, or a dramatic silence of 2-{max_pause} seconds after the beat (3-6 times per part).

Return ONLY this JSON schema:
{{
  "genre": "{genre}",
  "pillar": "{pillar_key}",
  "title": "short internal title of this part",
  "title_long": "the hook title (<= 70 chars)",
  "thumbnail_concept": "one specific dark atmospheric visual moment",
  "thumbnail_text": "1-2 words or empty",
  "premise": "1-2 sentence premise of THIS part",
  "universe_town": "{universe_town}",
  "recurring_character_used": "name if a recurring cast member appears, else empty string",{series_schema}
  "series_update": {{
    "recap": "a summary of the WHOLE story so far INCLUDING this part (at most 120 words)",
    "open_threads": ["unresolved question 1", "unresolved question 2"],
    "cliffhanger": "the last unresolved moment this part ends on ('' for a finale)",
    "next_part_teaser": "one tantalizing line about the next part ('' for a finale)"
  }},
  "characters": [
    {{"name": "character's name", "gender": "male", "role": "protagonist", "voice_note": "one line", "appearance": "one concrete visual sentence"}}
  ],
  "beats": [
    {{
      "beat_number": 1,
      "type": "narration",
      "speaker": "narrator",
      "text": "the narration line or the character's spoken line",
      "visual_description": "specific cinematic image prompt for exactly this beat",
      "emotion": "e.g. tension, dread, relief",
      "elements": ["suspense", "mystery"],
      "jumpscare": false,
      "bgm_keyword": "dark ambient drone",
      "sfx_keyword": "heavy rain",
      "sfx_kind": "ambient",
      "sfx_trigger_word": "",
      "pause_after_sec": 0
    }}
  ],
  "hook": "the opening hook line",
  "loop_sentence": "the final line",
  "description": "a 4-6 sentence English YouTube description; the first 125 characters are hook + keywords",
  "tags": ["tag1", "tag2"],
  "search_keywords": ["{genre} story", "scary story", "story narration"]
}}

Rules:
- {min_scenes}-{max_scenes} total beats; total words across all beats' "text" between {min_words} and
  {max_words} (15-20 minutes at ~130 words/minute).
- A dialogue beat's "speaker" MUST exactly match a character name (the bible's cast or a new one).
- Everything (title, description, tags, dialogue, narration) is in ENGLISH only.
- Fully fictional: no real victims, real ongoing investigations or real identifiable people.
- Return ONLY valid JSON, no markdown fences, no commentary.
"""

_SERIES_SCHEMA_OPENING = """
  "series": {
    "title": "the SERIES title (short, memorable)",
    "logline": "1-2 sentence logline of the whole story",
    "setting": "where and when it happens",
    "planned_parts": 5,
    "arc": ["Part 1: what happens", "Part 2: what happens", "... one sentence per planned part"]
  },"""


def _clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _research_block(research: dict | None) -> str:
    """Real recent YouTube data for this niche, folded into the prompt as inspiration for title style /
    keywords / tags — explicitly NOT as material to copy."""
    if not research or not research.get("sample_size"):
        return ""
    lines = [
        "REAL RECENT DATA from YouTube for this niche — use it ONLY to inform title style, keywords and "
        "tags. NEVER copy a title, plot or character from it:",
    ]
    if research.get("top_titles"):
        lines.append("  Top recent titles: " + " | ".join(research["top_titles"][:8]))
    if research.get("suggested_keywords"):
        lines.append("  Common title words: " + ", ".join(research["suggested_keywords"][:12]))
    if research.get("suggested_tags"):
        lines.append("  Common tags: " + ", ".join(research["suggested_tags"][:12]))
    return "\n".join(lines) + "\n"


def _series_block(mode: str, part_no: int, series: dict | None, planned_parts: int) -> str:
    lo, hi = SERIES_PARTS_RANGE
    if mode == "opening" or not series:
        return (
            f"=====================================================================\n"
            f"THIS IS PART 1 OF A NEW MULTI-PART SERIES\n"
            f"=====================================================================\n"
            f"Invent the whole series, then write ONLY Part 1 now. Decide how many ~15-20 minute parts this\n"
            f"story needs ({lo}-{hi}) and return it in the \"series\" object (title, logline, setting,\n"
            f"planned_parts, arc with one sentence per planned part). Give every character an APPEARANCE (age,\n"
            f"build, hair, clothes) — it keeps them looking like the same person in every image of every part.\n"
            f"Part 1 must end on a CLIFFHANGER that makes viewers need Part 2.\n"
        )
    bible = series.get("bible", {})
    cast = "\n".join(f"  - {c['name']} ({c.get('gender', '?')}): {c.get('role', '')}. Voice: {c.get('voice_note', '')}. "
                     f"Looks: {c.get('appearance', '')}" for c in bible.get("characters", []))
    threads = "\n".join(f"  - {t}" for t in bible.get("open_threads", [])) or "  (none recorded)"
    arc = "\n".join(f"  {a}" for a in bible.get("arc", [])) or "  (no arc recorded)"
    if mode == "finale":
        job = ("THIS IS THE FINAL PART. Resolve every open thread, reveal the truth, pay off the mystery and "
               "deliver a satisfying ending (one haunting last image is welcome). No cliffhanger.")
    else:
        job = ("Advance the plot, deepen the mystery, raise the stakes and reveal something that changes how "
               "the viewer sees the story. End on a NEW cliffhanger.")
    return (
        f"=====================================================================\n"
        f"THIS IS PART {part_no} of \"{series['title']}\" ({planned_parts} parts planned)\n"
        f"=====================================================================\n"
        f"{job}\n\nSERIES BIBLE — canon, never contradict it:\n"
        f"Logline: {bible.get('logline', '')}\nSetting: {bible.get('setting', '')}\nCast:\n{cast}\n"
        f"STORY SO FAR: {bible.get('recap', '')}\nOPEN THREADS:\n{threads}\n"
        f"PLANNED ARC:\n{arc}\nPREVIOUS PART ENDED WITH: {bible.get('cliffhanger', '')}\n\n"
        f"Open with a 'previously' recap of 2-3 narration beats (about 20-25 seconds) that re-hooks the "
        f"viewer with the story's biggest unanswered question — then continue the story.\n"
    )


def _elements_block() -> str:
    return "\n".join(f"- {text}" for text in STORY_ELEMENTS.values())


# ---------------------------------------------------------------------------------------------
# repair / normalize / validate
# ---------------------------------------------------------------------------------------------
def _tokens(name: str) -> set[str]:
    return set(re.findall(r"[a-z']+", str(name).lower()))


def _match_speaker(speaker: str, names: list[str]) -> str | None:
    """Map the model's speaker label onto a real character name: exact (case-insensitive) first, then
    unambiguous word overlap ("Sheriff Garrett" -> "Sheriff Tom Garrett", "Tom" -> "Sheriff Tom Garrett")."""
    sp = _clean(speaker)
    if not sp:
        return None
    for n in names:
        if n.lower() == sp.lower():
            return n
    st = _tokens(sp)
    hits = [n for n in names if st and (st <= _tokens(n) or _tokens(n) <= st)]
    return hits[0] if len(hits) == 1 else None


_CAMERA_VARIANTS = (
    "close-up on a telling detail", "wide establishing shot", "over-the-shoulder angle",
    "low-angle shot", "view from behind", "dim lit close shot",
)


def _split_sentences(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]


def _hard_wrap(text: str, max_words: int) -> list[str]:
    """Last resort for a single huge sentence: break at commas/semicolons, then by words."""
    parts, buf = [], []
    for piece in re.split(r"(?<=[,;:])\s+", text):
        if buf and len(" ".join(buf + [piece]).split()) > max_words:
            parts.append(" ".join(buf)); buf = []
        buf.append(piece)
    if buf:
        parts.append(" ".join(buf))
    out = []
    for part in parts:
        words = part.split()
        out += [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)] or [part]
    return out


def _chunk_text(text: str, max_words: int) -> list[str]:
    """Pack whole sentences into chunks of <= max_words (never cutting mid-sentence unless one sentence
    alone exceeds the limit)."""
    units = []
    for sent in _split_sentences(text):
        units += _hard_wrap(sent, max_words) if len(sent.split()) > max_words else [sent]
    chunks, cur = [], []
    for u in units:
        if cur and len(" ".join(cur + [u]).split()) > max_words:
            chunks.append(" ".join(cur)); cur = []
        cur.append(u)
    if cur:
        chunks.append(" ".join(cur))
    return chunks or [text]


def _vary_visual(original: str, chunk: str, index: int) -> str:
    """Give each sub-beat its own image prompt: same scene, different camera angle and the specific
    moment being narrated."""
    moment = " ".join(chunk.split()[:12]).strip(" .,;:!?\"'")
    return f"{original}, {_CAMERA_VARIANTS[index % len(_CAMERA_VARIANTS)]}, the moment: {moment}"


def _split_long_beats(beats: list[dict]) -> list[dict]:
    """A real run produced ~30-second narration beats: 35 images for a 17-minute video and Shorts with ONE
    image each. Narration beats longer than STORY_SPLIT_ABOVE_WORDS are split at sentence boundaries into
    beats of at most STORY_MAX_BEAT_WORDS, each with its own image prompt. Audio direction follows the
    text: music/ambience continue across the pieces, a one-shot effect (and a jumpscare flag) stays on the
    piece that holds its trigger word, a dramatic pause lands after the last piece. Dialogue is never split."""
    out = []
    for b in beats:
        if b.get("type") != "narration" or len(b["text"].split()) <= STORY_SPLIT_ABOVE_WORDS:
            out.append(b)
            continue
        chunks = _chunk_text(b["text"], STORY_MAX_BEAT_WORDS)
        if len(chunks) == 1:
            out.append(b)
            continue
        trig = re.sub(r"[^a-z0-9']", "", str(b.get("sfx_trigger_word") or "").lower())
        holder = next((i for i, c in enumerate(chunks) if trig and trig in re.sub(r"[^a-z0-9' ]", "", c.lower()).split()), 0)
        for i, chunk in enumerate(chunks):
            nb = dict(b)
            nb["text"] = chunk
            if i > 0:
                nb["visual_description"] = _vary_visual(b.get("visual_description", ""), chunk, i)
            if _clean(b.get("sfx_kind")).lower() == "action" and i != holder:
                nb["sfx_keyword"], nb["sfx_kind"], nb["sfx_trigger_word"] = "none", "none", ""
            if b.get("jumpscare") in (True, "true", "True", 1):
                nb["jumpscare"] = (i == holder) if _clean(b.get("sfx_kind")).lower() == "action" else (i == len(chunks) - 1)
            if i < len(chunks) - 1:
                nb["pause_after_sec"] = 0
            out.append(nb)
    return out


def _repair_structure(story: dict) -> None:
    """Fix the commonest ways an LLM bends the schema, in place:
      * beats with no text are dropped; stage directions "(whispering)" / "[beat]" (which a TTS would read
        ALOUD) and markdown symbols are removed from the text
      * unknown/missing beat type is inferred from the speaker
      * a dialogue speaker that matches no character is matched by name overlap, else the beat becomes
        narration (the line is still spoken, by the narrator)
      * a leading "Name:" prefix is stripped from dialogue text
      * a missing visual_description is built from the beat's own text
      * over-long narration beats are split at sentence boundaries (see _split_long_beats)
      * beats are renumbered 1..N"""
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
        text = _clean(b.get("text"))
        text = re.sub(r"\[[^\]]{0,60}\]|\(\s*[A-Za-z' ,-]{1,40}\s*\)", " ", text)
        text = _clean(re.sub(r"[*_#`]", "", text))
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
    kept = _split_long_beats(kept)
    for n, b in enumerate(kept, start=1):
        b["beat_number"] = n
    story["beats"] = kept


def _normalize_elements(story: dict) -> None:
    """Per-beat emotion tags -> a clean list of known element names; jumpscare -> bool."""
    for b in story.get("beats", []):
        raw = b.get("elements")
        if isinstance(raw, str):
            raw = re.split(r"[,/;| ]+", raw)
        tags = []
        for t in raw or []:
            t = _clean(t).lower()
            if t in ELEMENT_NAMES and t not in tags:
                tags.append(t)
        b["elements"] = tags
        b["jumpscare"] = b.get("jumpscare") in (True, "true", "True", "yes", 1)
        if b["jumpscare"] and "fear" not in tags:
            b["elements"].append("fear")


def _normalize_series(story: dict, mode: str) -> None:
    """Opening part: a usable series object (title, length inside the allowed range, one arc line per part)."""
    from src.series_planner import clamp_planned_parts

    update = story.get("series_update")
    story["series_update"] = update if isinstance(update, dict) else {}
    su = story["series_update"]
    su["open_threads"] = [_clean(t) for t in (su.get("open_threads") or []) if _clean(t)] if isinstance(su.get("open_threads"), list) else []
    for key in ("recap", "cliffhanger", "next_part_teaser"):
        su[key] = _clean(su.get(key))
    if mode != "opening":
        return
    series = story.get("series")
    series = series if isinstance(series, dict) else {}
    series["title"] = _clean(series.get("title")) or _clean(story.get("title")) or "Untitled"
    series["planned_parts"] = clamp_planned_parts(series.get("planned_parts"))
    arc = [_clean(a) for a in series.get("arc", []) if _clean(a)] if isinstance(series.get("arc"), list) else []
    series["arc"] = arc[: series["planned_parts"]]
    series["logline"] = _clean(series.get("logline")) or _clean(story.get("premise"))
    series["setting"] = _clean(series.get("setting"))
    story["series"] = series


def _normalize_story(story: dict) -> None:
    """Repair structure, then fill / clamp the audio-direction and emotion fields in place so a slightly
    sloppy LLM answer never costs a retry. Genuinely unusable stories are still rejected by _validate_story."""
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

    _normalize_elements(story)
    text = _clean(story.get("thumbnail_text")).upper()
    story["thumbnail_text"] = " ".join(text.split()[:2])[:24]
    story["title_long"] = _clean(story.get("title_long")) or _clean(story.get("title"))


def _validate_story(story: dict, *, require_elements: bool = False, require_series: bool = False) -> None:
    """The prompt asks for 40-70 beats / 1950-2600 words; ACCEPTANCE is looser (30-105 beats, 1170-3900
    words; over-long beats were already split) because a slightly short or long part is still a good
    video, while rejecting it wastes a Gemini call. With require_elements the five emotions, the
    jumpscare and the 30-second hook are enforced too."""
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

    if require_elements:
        problem = check_elements(beats)
        if problem:
            raise ValueError(problem)
    if require_series and not (story.get("series") or {}).get("title"):
        raise ValueError("Part 1 did not describe the series (title, planned_parts, arc)")


def check_elements(beats: list[dict]) -> str | None:
    """None when the part delivers the five emotions, a jumpscare and a 30-second hook; otherwise a
    sentence describing exactly what is missing (it is fed back to the model on the retry)."""
    counts = {e: sum(1 for b in beats if e in (b.get("elements") or [])) for e in ELEMENT_NAMES}
    missing = [f"{e} ({counts[e]}/{ELEMENT_MIN_BEATS} beats)" for e in ELEMENT_NAMES if counts[e] < ELEMENT_MIN_BEATS]
    if missing:
        return "these required emotions are missing or too thin: " + ", ".join(missing)
    if sum(1 for b in beats if b.get("jumpscare")) < MIN_JUMPSCARES:
        return "there is no jumpscare beat (\"jumpscare\": true with a silence before it and an action sound)"
    opening = set()
    for b in beats[:HOOK_BEATS]:
        opening |= set(b.get("elements") or [])
    if len(opening & set(HOOK_ELEMENTS)) < 2:
        return (f"the first {HOOK_BEATS} beats (the 30-second hook) must carry at least two of "
                f"{', '.join(HOOK_ELEMENTS)} — open on the most shocking moment")
    return None


# ---------------------------------------------------------------------------------------------
# the entry point
# ---------------------------------------------------------------------------------------------
def write_story(
    genre: str | None = None,
    premise: str = "",
    pillar: str | None = None,
    research: dict | None = None,
    *,
    series: dict | None = None,
    part_no: int = 1,
    mode: str = "opening",
    planned_parts: int = 0,
    max_retries: int = 2,
) -> dict:
    """Write one episode.

    New story:   write_story("horror")                                  -> part 1 + the series object
    Next part:   write_story(series=db_row, part_no=3, mode="middle")   -> part 3, continuing the bible
    Last part:   write_story(series=db_row, part_no=5, mode="finale")   -> resolves everything

    `series` is the database row (with its bible). `pillar` forces a content pillar for a new story
    (else src.pattern_analytics picks one from real performance data). `research` is real niche data
    folded into the prompt as inspiration. max_retries is small on purpose — each retry spends scarce
    Gemini quota — and a retry carries the exact reason the previous answer was rejected."""
    from src.config import STORY_GENRES

    if mode not in ("opening", "middle", "finale"):
        raise ValueError(f"Unknown mode {mode!r}")
    continuing = mode != "opening"
    if continuing and not series:
        raise ValueError("A continuation needs the series row (with its bible)")
    if continuing:
        genre = genre or series["genre"]
        pillar = pillar or series["pillar"]
    if genre not in STORY_GENRES:
        raise ValueError(f"Unknown genre {genre!r}; must be one of {STORY_GENRES}")
    if pillar is not None and pillar not in STORY_PILLARS:
        raise ValueError(f"Unknown pillar {pillar!r}; must be one of {STORY_PILLARS}")
    if pillar is None:
        from src.pattern_analytics import suggest_next_pillar

        pillar = suggest_next_pillar()

    chosen = None
    if continuing:
        premise_instruction = "Continue the series exactly as its bible dictates."
        recurring_character_instruction = "Use only the characters of the series bible, plus any NEW ones this part needs."
        characters_rule = ("List ONLY characters that are NEW in this part (the series bible already holds the cast; "
                           "dialogue beats may use the bible characters' exact names). Give each new one an appearance.")
        ending_rule = ("resolve the story completely — no cliffhanger, no loose threads." if mode == "finale"
                       else "end on a NEW CLIFFHANGER — the last beat is an unanswered, urgent question or danger that "
                            "makes the next part unmissable.")
    else:
        premise_instruction = (f"Build the story around this premise/seed idea: {premise}" if premise else
                               "Invent an original premise within this genre — avoid the most obvious cliché setup.")
        if STORY_RECURRING_CHARACTERS and random.random() < STORY_RECURRING_CHARACTER_RATE:
            chosen = random.choice(STORY_RECURRING_CHARACTERS)
        recurring_character_instruction = (
            f"Include this recurring cast member as one of your characters: {chosen['name']} ({chosen['gender']}, "
            f"{chosen['note']}). Keep them consistent with that description and set \"recurring_character_used\" "
            f"to their exact name." if chosen else
            "No recurring cast member is needed this time — all-new characters are fine. Set "
            "\"recurring_character_used\" to an empty string.")
        characters_rule = (f"Create {STORY_MIN_CHARACTERS}-{STORY_MAX_CHARACTERS} named characters. For each: gender "
                           f"(male/female — required, it picks the voice), a one-line voice/personality note, their role "
                           f"and an APPEARANCE sentence. Use Western/American names.")
        ending_rule = "end on a CLIFFHANGER — an unanswered, urgent question or danger that makes Part 2 unmissable."

    prompt = STORY_PROMPT.format(
        channel=CHANNEL_NAME,
        genre=genre,
        premise_instruction=premise_instruction,
        research_block=_research_block(research),
        series_block=_series_block(mode, part_no, series, planned_parts or (series or {}).get("planned_parts", 0)),
        locale_note=STORY_LOCALE_NOTE,
        universe_town=STORY_UNIVERSE_TOWN,
        recurring_character_instruction=recurring_character_instruction,
        pillar_key=pillar,
        pillar_label=STORY_PILLAR_LABELS[pillar],
        elements_block=_elements_block(),
        element_min=ELEMENT_MIN_BEATS,
        min_jumpscares=MIN_JUMPSCARES,
        hook_beats=HOOK_BEATS,
        ending_rule=ending_rule,
        characters_rule=characters_rule,
        series_schema=_SERIES_SCHEMA_OPENING if not continuing else "",
        min_scenes=STORY_MIN_SCENES,
        max_scenes=STORY_MAX_SCENES,
        min_words=STORY_MIN_WORDS,
        max_words=STORY_MAX_WORDS,
        max_bgm=STORY_MAX_BGM_KEYWORDS,
        max_pause=int(STORY_MAX_PAUSE_SEC),
        max_beat_words=STORY_MAX_BEAT_WORDS,
    )

    last_err, feedback = None, ""
    for attempt in range(max_retries + 1):
        try:
            story = generate_json(prompt + feedback, temperature=0.95)
            if isinstance(story, list) and len(story) == 1 and isinstance(story[0], dict):
                story = story[0]            # some answers wrap the object in a list
            if not isinstance(story, dict):
                raise ValueError(f"Gemini returned {type(story).__name__}, expected a JSON object")
            # Our own decisions are authoritative, whatever the model echoed back.
            story["genre"], story["pillar"], story["universe_town"] = genre, pillar, STORY_UNIVERSE_TOWN
            story["part_no"], story["mode"] = part_no, mode
            story.setdefault("recurring_character_used", chosen["name"] if chosen else "")
            if continuing:
                story["characters"] = merged_characters(series.get("bible", {}), story.get("characters", []))
            _normalize_story(story)
            _normalize_series(story, mode)
            _validate_story(story, require_elements=True, require_series=not continuing)
            return story
        except Exception as e:
            last_err = e
            log.warning("Story attempt %d/%d failed: %s", attempt + 1, max_retries + 1, e)
            feedback = (f"\n\nYOUR PREVIOUS ANSWER WAS REJECTED because: {e}. Write the part again and fix exactly "
                        f"that, keeping everything else in this brief.")

    raise RuntimeError(f"Failed to generate a valid {genre} story: {last_err}")
