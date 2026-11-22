"""
Assigns a distinct Edge TTS voice to each character in a story (by gender,
cycling through a pool so same-gender characters don't all sound identical).
Narration beats use STORY_NARRATOR_VOICE, dialogue beats use their character's
assigned voice (a female character always gets a female voice, a male character
a male voice).

Voice names were cross-checked against the live edge-tts voice catalog (not
guessed). STORY_NARRATOR_VOICE is deliberately kept out of both character pools
so no character can end up sounding identical to the narrator. The narrator's
deeper/slower read (rate/pitch) is applied by src/story_pipeline.py.
"""
import logging

from src.config import STORY_FEMALE_VOICES, STORY_MALE_VOICES, STORY_NARRATOR_VOICE

log = logging.getLogger(__name__)


def assign_voices(characters: list[dict], existing: dict[str, str] | None = None) -> dict[str, str]:
    """{character name: Edge TTS voice}. `existing` is the series' voice map: characters already in it
    KEEP their voice forever (a character must never change voice between parts); new characters get
    the first voice of their gender's pool that nobody is using yet, so two same-gender characters never
    share a voice (the pools hold 5 each and STORY_MAX_CHARACTERS keeps casts small)."""
    voice_map: dict[str, str] = dict(existing or {})
    used = set(voice_map.values())
    for char in characters:
        name = char.get("name")
        if not name or name in voice_map:
            continue
        gender = str(char.get("gender", "")).lower()
        if gender not in ("male", "female"):
            log.warning(
                "Character %r has unrecognized gender %r — defaulting to a male voice. Fix the story's "
                "character gender field if this is wrong.", name, char.get("gender"),
            )
            gender = "male"
        pool = STORY_FEMALE_VOICES if gender == "female" else STORY_MALE_VOICES
        free = [v for v in pool if v not in used]
        pick = free[0] if free else pool[len([v for v in used if v in pool]) % len(pool)]
        voice_map[name] = pick
        used.add(pick)
    return voice_map


def voice_for_beat(beat: dict, voice_map: dict[str, str]) -> str:
    """Returns the Edge TTS voice name that should speak this beat."""
    if beat.get("type") == "narration" or beat.get("speaker") == "narrator":
        return STORY_NARRATOR_VOICE
    speaker = beat.get("speaker")
    if speaker not in voice_map:
        # Should be unreachable if the story passed story_writer's
        # validation (which checks every dialogue speaker matches a
        # character), but fall back to the narrator voice rather than
        # crashing a whole run over one malformed beat.
        log.warning(
            "Beat %s speaker %r has no assigned voice — falling back to "
            "narrator voice", beat.get("beat_number"), speaker,
        )
        return STORY_NARRATOR_VOICE
    return voice_map[speaker]
