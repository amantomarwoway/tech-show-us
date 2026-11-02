"""
Burned-in ASS captions for story videos.

  * "karaoke" (default): words light up as they are spoken (gold = not yet
    spoken, white = spoken — ASS karaoke colours).
  * "pop": each caption group fades in with a small scale pop.
  * Dialogue beats get a "SPEAKER: " prefix on their FIRST caption group only
    (never repeated every few words); narration gets none.

Timing comes from word-level alignment (src/aligner.py) already offset onto the
global video timeline. Karaoke durations run word-start to next-word-start so
the highlight never races ahead of the voice across pauses.
"""
from pathlib import Path

WORDS_PER_CAPTION = 4
THEMES = ("karaoke", "pop")


def _fmt_time(sec: float) -> str:
    sec = max(sec, 0.0)
    cs = int(round(sec * 100))
    h, rem = divmod(cs, 360000)
    m, rem = divmod(rem, 6000)
    s, c = divmod(rem, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def _safe(text: str) -> str:
    """ASS treats { } and \\ specially; captions never need them."""
    return str(text).replace("{", "(").replace("}", ")").replace("\\", "").replace("\n", " ").strip()


def _ass_header(font_size: int, margin_v: int, play_res_x: int, play_res_y: int) -> str:
    return (
        "[Script Info]\nScriptType: v4.00+\nWrapStyle: 0\nScaledBorderAndShadow: yes\n"
        f"PlayResX: {play_res_x}\nPlayResY: {play_res_y}\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
        "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,DejaVu Sans,{font_size},&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,"
        f"-1,0,0,0,100,100,0,0,1,4,1,2,60,60,{margin_v},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def _group_words(words: list[dict], size: int) -> list[list[dict]]:
    return [words[i:i + size] for i in range(0, len(words), size)]


def _line_karaoke(group: list[dict], prefix: str = "") -> str:
    start, end = group[0]["start"], max(group[-1]["end"], group[0]["start"] + 0.05)
    parts = []
    for i, w in enumerate(group):
        nxt = group[i + 1]["start"] if i + 1 < len(group) else w["end"]
        cs = max(int(round((nxt - w["start"]) * 100)), 5)
        parts.append(rf"{{\k{cs}}}{_safe(w['word'])}")
    # The prefix is plain text with no \k tag: it is not a spoken, timed word.
    return (f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,"
            rf"{{\fad(100,100)}}{prefix}{' '.join(parts)}" + "\n")


def _line_pop(group: list[dict], prefix: str = "") -> str:
    start, end = group[0]["start"], max(group[-1]["end"], group[0]["start"] + 0.05)
    text = prefix + " ".join(_safe(w["word"]) for w in group)
    tag = r"{\fad(120,120)\t(0,150,\fscx120\fscy120)\t(150,250,\fscx100\fscy100)}"
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{tag}{text}\n"


_RENDERERS = {"karaoke": _line_karaoke, "pop": _line_pop}


def build_story_captions(
    beats_with_words: list[tuple[dict, list[dict]]],
    out_path: Path,
    *,
    theme: str = "karaoke",
    is_short: bool = False,
) -> Path:
    """`beats_with_words`: [(beat, words)] where `words` are that beat's aligned
    words ALREADY offset into the global timeline (aligner.offset_words)."""
    if theme not in _RENDERERS:
        raise ValueError(f"Unknown caption theme {theme!r}; choose from {THEMES}")
    font_size, margin_v = (90, 200) if is_short else (70, 150)
    res_x, res_y = (1080, 1920) if is_short else (1920, 1080)
    size = 3 if is_short else WORDS_PER_CAPTION
    render = _RENDERERS[theme]

    lines = [_ass_header(font_size, margin_v, res_x, res_y)]
    for beat, words in beats_with_words:
        speaker = str(beat.get("speaker", ""))
        is_dialogue = beat.get("type") == "dialogue" and speaker
        for i, group in enumerate(_group_words(words, size)):
            if not group:
                continue
            prefix = f"{_safe(speaker).upper()}: " if (is_dialogue and i == 0) else ""
            lines.append(render(group, prefix))
    out_path = Path(out_path)
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path
