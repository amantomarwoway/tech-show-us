"""
The "bible" of a multi-part story: everything a later part must remember so the story stays ONE story.

  characters   name, gender, role, voice note and APPEARANCE (one concrete visual sentence)
  voice_map    which Edge TTS voice each character speaks with — fixed for the series' whole life,
               so a character never changes voice between parts
  recap        a rolling summary of the WHOLE story so far (replaced after every part)
  open_threads unresolved questions the story still owes the audience
  cliffhanger  how the previous part ended
  arc          one sentence per planned part

Stored as JSON in the series table (src/database.py). Everything here tolerates a model that bends the schema
(a string where a list belongs, a character without a name, a missing object): a malformed answer must degrade to
"less detail", never to a crash after the episode has already been uploaded.
"""
import re


def _clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value) -> list:
    """A list stays a list, a lone string becomes a one-item list (NOT a list of characters), anything else is empty."""
    if isinstance(value, list):
        return value
    return [value] if isinstance(value, str) and value.strip() else []


def _named(characters) -> list[dict]:
    return [c for c in _as_list(characters) if isinstance(c, dict) and _clean(c.get("name"))]


def _character(c: dict) -> dict:
    return {"name": _clean(c["name"]), "gender": c.get("gender", ""), "role": _clean(c.get("role")),
            "voice_note": _clean(c.get("voice_note")), "appearance": _clean(c.get("appearance"))}


def _texts(value) -> list[str]:
    return [_clean(t) for t in _as_list(value) if _clean(t)]


def new_bible(story: dict) -> dict:
    """Bible for a brand-new series, from the writer's opening answer (part 1)."""
    series = _as_dict(story.get("series"))
    update = _as_dict(story.get("series_update"))
    return {
        "logline": _clean(series.get("logline")),
        "setting": _clean(series.get("setting")) or _clean(story.get("universe_town")),
        "arc": _texts(series.get("arc")),
        "characters": [_character(c) for c in _named(story.get("characters"))],
        "voice_map": {},
        "recap": _clean(update.get("recap")),
        "open_threads": _texts(update.get("open_threads")),
        "cliffhanger": _clean(update.get("cliffhanger")),
    }


def merged_characters(bible: dict, new_characters: list[dict]) -> list[dict]:
    """The bible's cast followed by any characters this part introduces (dedupe by name, case-insensitive)."""
    cast = [dict(c) for c in _named(_as_dict(bible).get("characters"))]
    known = {_clean(c["name"]).lower() for c in cast}
    for c in _named(new_characters):
        key = _clean(c["name"]).lower()
        if key not in known:
            cast.append(_character(c))
            known.add(key)
    return cast


def _tail_at_word(text: str, limit: int) -> str:
    """The last `limit` characters of text, starting at a whole word."""
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    return cut.split(" ", 1)[1] if " " in cut else cut


def updated_bible(bible: dict, story: dict, voice_map: dict) -> dict:
    """The bible after a part has been written: merged cast, the voices actually used, and the writer's new
    recap / open threads / cliffhanger. If the writer omitted its update the old recap is kept and extended with
    this part's premise (the newest 900 characters), so the next part is never written blind."""
    bible = _as_dict(bible)
    update = _as_dict(story.get("series_update"))
    out = dict(bible)
    out["characters"] = merged_characters(bible, story.get("characters", []))
    out["voice_map"] = {**_as_dict(bible.get("voice_map")), **_as_dict(voice_map)}
    recap = _clean(update.get("recap"))
    out["recap"] = recap or _tail_at_word(_clean(f"{bible.get('recap', '')} {story.get('premise', '')}"), 900)
    out["open_threads"] = _texts(update.get("open_threads")) or _texts(bible.get("open_threads"))
    out["cliffhanger"] = _clean(update.get("cliffhanger"))
    return out


def appearance_map(bible: dict, characters: list[dict] | None = None) -> dict[str, str]:
    """{character name: appearance sentence} — injected into image prompts so a character looks like the same
    person in every image of every part. Later entries (this part's own characters) win over the bible's."""
    cast = _named(_as_dict(bible).get("characters")) + _named(characters)
    return {_clean(c["name"]): _clean(c.get("appearance")) for c in cast if _clean(c.get("appearance"))}
