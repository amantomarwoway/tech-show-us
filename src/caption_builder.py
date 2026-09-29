"""
Builds .ass subtitle files from word-level timestamps with three visual
themes: pop (scale-in), bounce (rise + settle), karaoke (word-by-word gold
highlight). Burned into the final render via ffmpeg's `ass` filter.
"""
from pathlib import Path

WORDS_PER_CAPTION = 4


def _ass_header(font_size: int, margin_v: int, play_res_x: int, play_res_y: int) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_res_x}
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans Bold,{font_size},&H00FFFFFF,&H0000D7FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _group_words(words: list[dict], per_caption: int) -> list[list[dict]]:
    return [words[i:i + per_caption] for i in range(0, len(words), per_caption)]


def _line_pop(group: list[dict], play_res_x: int, play_res_y: int, margin_v: int) -> str:
    start, end = group[0]["start"], group[-1]["end"]
    text = " ".join(w["word"] for w in group)
    tag = r"{\fad(120,120)\t(0,150,\fscx120\fscy120)\t(150,250,\fscx100\fscy100)}"
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{tag}{text}\n"


def _line_bounce(group: list[dict], play_res_x: int, play_res_y: int, margin_v: int) -> str:
    r"""Rises up into the same bottom-anchored resting spot pop/karaoke use,
    instead of a fixed position.

    TESTED FOOTGUN: the previous version hardcoded \move(960,600,960,540,...)
    — pixel coordinates baked in for a 1920x1080 canvas. On a 1080x1920
    Shorts canvas that put the X origin (960) almost off the right edge
    instead of centered (540), and the fixed Y (540-600) landed in the
    vertical middle of the frame on EITHER canvas instead of near the
    bottom — nowhere close to the same safe-area pop/karaoke use via
    Alignment+MarginV. Always derive \move targets from the actual
    play_res_x/play_res_y/margin_v for the render being built, never
    hardcode them.
    """
    start, end = group[0]["start"], group[-1]["end"]
    text = " ".join(w["word"] for w in group)
    target_x = play_res_x // 2
    target_y = play_res_y - margin_v
    rise_from_y = target_y + 60  # starts slightly below resting position
    tag = (
        rf"{{\fad(100,100)\move({target_x},{rise_from_y},{target_x},{target_y},0,150)}}"
    )
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{tag}{text}\n"


def _line_karaoke(group: list[dict], play_res_x: int, play_res_y: int, margin_v: int) -> str:
    start, end = group[0]["start"], group[-1]["end"]
    parts = []
    for w in group:
        centiseconds = int(round((w["end"] - w["start"]) * 100))
        parts.append(rf"{{\k{max(centiseconds, 5)}}}{w['word']}")
    text = " ".join(parts)
    tag = r"{\fad(100,100)}"
    return f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{tag}{text}\n"


_THEME_RENDERERS = {"pop": _line_pop, "bounce": _line_bounce, "karaoke": _line_karaoke}


def build_ass_captions(
    words: list[dict],
    out_path: Path,
    *,
    theme: str = "karaoke",
    is_short: bool = False,
) -> Path:
    if theme not in _THEME_RENDERERS:
        raise ValueError(f"Unknown caption theme: {theme}")

    font_size = 90 if is_short else 70
    margin_v = 200 if is_short else 150
    play_res_x = 1080 if is_short else 1920
    play_res_y = 1920 if is_short else 1080
    words_per_caption = 3 if is_short else WORDS_PER_CAPTION

    renderer = _THEME_RENDERERS[theme]
    lines = [_ass_header(font_size, margin_v, play_res_x, play_res_y)]
    for group in _group_words(words, words_per_caption):
        if not group:
            continue
        lines.append(renderer(group, play_res_x, play_res_y, margin_v))

    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path
