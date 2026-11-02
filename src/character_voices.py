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


def assign_voices(characters: list[dict]) -> dict[str, str]:
    """Returns {character_name: edge_tts_voice}. Cycles through each
    gender's voice pool by order of appearance, so e.g. the 1st and 3rd
    male characters in a story get different voices from the pool rather
    than colliding on the same one (collision is only possible once a
    single story has more same-gender characters than that gender's pool
    size — 5 voices per gender, and STORY_MAX_CHARACTERS is 5 total, so
    this cannot happen in practice)."""
    voice_map: dict[str, str] = {}
    male_idx = 0
    female_idx = 0
    for char in characters:
        name = char.get("name")
        gender = str(char.get("gender", "")).lower()
        if not name:
            continue
        if gender == "female":
            voice_map[name] = STORY_FEMALE_VOICES[female_idx % len(STORY_FEMALE_VOICES)]
            female_idx += 1
        else:
            # Default to the male pool for "male" or any unrecognized value
            # rather than silently dropping the character's voice assignment.
            if gender != "male":
                log.warning(
                    "Character %r has unrecognized gender %r — defaulting to "
                    "a male voice. Fix the story's character gender field if "
                    "this is wrong.", name, char.get("gender"),
                )
            voice_map[name] = STORY_MALE_VOICES[male_idx % len(STORY_MALE_VOICES)]
            male_idx += 1
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
