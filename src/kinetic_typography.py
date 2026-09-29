"""
Kinetic typography + parallax word overlay, composited on top of a Ken Burns
background clip.

=====================================================================
HOW THIS WORKS (read this before touching the filter strings below)
=====================================================================
The word is rendered on its own fully-transparent RGBA canvas
(`color=c=black@0.0:...,format=rgba`), animated with drawtext, and then
composited onto the real Ken Burns background with `overlay=format=auto`.
This is NOT the same as drawing directly onto the background with a single
`-vf drawtext=...`. Two things depend on going through this separate
transparent layer:

  1. GLOW needs a Gaussian blur (`gblur`) applied ONLY to the text, never to
     the background photo. Blurring the composited frame directly would
     blur the whole scene.
  2. TESTED FOOTGUN — do not "simplify" this by adding `format=yuv420p`
     ANYWHERE inside the filter_complex chain (on the [bg], [fg], or
     post-overlay). We tested this: converting to yuv420p mid-graph before
     the final output stage produces a wrong color range/matrix and paints
     the entire background a false purple/magenta tint (looked like a
     colorspace bug, and it is one). `format=yuv420p` must ONLY be set via
     the ffmpeg process's `-pix_fmt yuv420p` OUTPUT argument, never as a
     filter step. `overlay=format=auto` keeps the graph in RGB internally
     and this is what avoids the bug — leave it as `auto`.

=====================================================================
THE THREE STYLES
=====================================================================
- "typewriter": the word is revealed letter-by-letter via a chain of
  drawtext filters, each showing a longer prefix, each active only in its
  own `enable='between(t,t0,t1)'` window. Works because our overlay word is
  always short (the episode's single word), so a handful of stacked
  drawtext filters is cheap. This would NOT scale to full sentences.
- "glow": TWO drawtext passes on the transparent canvas — a soft bordered
  copy that gets `gblur`red (the glow halo), then a crisp copy on top with
  no blur. fontsize and alpha are animated with time expressions directly
  in drawtext (`fontsize='80+min(t/0.4,1)*160'` etc.) — ffmpeg's drawtext
  DOES support this (verified: fontsize/x/y/alpha are all runtime
  expressions, not just static values), so no per-frame Pillow rendering
  is needed anywhere in this pipeline.
- "bounce": a single drawtext whose y-position follows a damped cosine
  (`+150*exp(-4*t)*cos(14*t)`) so it overshoots and settles, like a
  physical drop-and-bounce.

=====================================================================
PARALLAX
=====================================================================
"Parallax Ken Burns" here means: the background photo zooms via zoompan
(see video_builder._ken_burns_clip) while THIS word layer drifts
independently — a slow horizontal term added to x (or, for glow, a slow
sinusoidal drift) that has nothing to do with the background's zoom rate.
Two layers moving at different rates/directions is what produces the
depth illusion; direction alternates per scene so consecutive scenes don't
all drift the same way.
"""
import logging

from src.config import COLOR_GOLD, FPS

log = logging.getLogger(__name__)

FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STYLES = ("typewriter", "glow", "bounce")

# Vertical placement, as a fraction of frame height, for the drawtext y=
# (top-left) coordinate. Deliberately NOT vertical-center: the AI-generated
# scene image already tends to render its own subject/word near the center
# (see visual_generator.py's prompt engineering — "word in gold 3D letters
# centered"), and the ASS captions are anchored near the bottom. Centering
# the kinetic-typography layer too would stack three competing text/graphic
# elements on top of each other. Placing it in the upper band keeps all
# three visually separated. Verified at 0.12 on both 1920x1080 and 1080x1920
# canvases: comfortably clears the caption safe-area at the bottom and never
# clips at the top even for the largest fontsize used here (~180px).
WORD_Y_FRACTION = 0.12


def style_for_scene(scene_index: int) -> str:
    """Deterministic style rotation so consecutive scenes vary, but a given
    scene always gets the same style across retries (no flicker on re-run)."""
    return STYLES[scene_index % len(STYLES)]


def _escape_drawtext(text: str) -> str:
    """Escape characters drawtext's `text=` option treats specially.
    Order matters: backslash first, then the rest, or we'd double-escape."""
    for ch in ("\\", ":", "'", "%"):
        text = text.replace(ch, "\\" + ch)
    return text


def _drift_expr(scene_index: int, amplitude_px: int = 35, kind: str = "linear") -> str:
    """Independent-of-zoom horizontal drift for the word layer. Direction
    alternates by scene so a multi-scene video doesn't drift the same way
    every time — that reads as a mistake, not a design choice."""
    direction = 1 if scene_index % 2 == 0 else -1
    if kind == "sine":
        # Gentle oscillation — used by "glow" so the halo doesn't exit frame.
        return f"{direction}*{amplitude_px}*sin(t*0.6)"
    # Slow constant drift — used by "bounce"/"typewriter".
    return f"{direction}*{amplitude_px // 3}*t"


def _typewriter_chain(word: str, width: int, height: int, duration: float, scene_index: int) -> str:
    word = _escape_drawtext(word.upper())
    letters = list(word)
    n = len(letters)
    if n == 0:
        # Degenerate input guard — an empty word would produce zero drawtext
        # filters, which is invalid ffmpeg syntax. Fall back to a 1-frame
        # invisible layer rather than crash the whole scene render.
        return (
            f"color=c=black@0.0:s={width}x{height}:d={duration}:r={FPS},"
            f"format=rgba[fg]"
        )

    reveal_window = min(0.6, max(duration * 0.3, 0.15))  # total reveal time
    per_letter = reveal_window / n
    drift = _drift_expr(scene_index, kind="linear")

    parts = [f"color=c=black@0.0:s={width}x{height}:d={duration}:r={FPS},format=rgba"]
    for i in range(1, n + 1):
        prefix = _escape_drawtext("".join(letters[:i]))
        t_start = (i - 1) * per_letter
        # Last prefix (the full word) stays visible for the rest of the clip.
        enable = (
            f"between(t\\,{t_start:.3f}\\,{i * per_letter:.3f})"
            if i < n else f"gte(t\\,{t_start:.3f})"
        )
        parts.append(
            f"drawtext=fontfile={FONT_BOLD_PATH}:text='{prefix}':"
            f"fontcolor={COLOR_GOLD}:fontsize=110:"
            f"x=(w-text_w)/2+({drift}):y=h*{WORD_Y_FRACTION}:"
            f"enable='{enable}'"
        )
    return ",".join(parts) + "[fg]"


def _glow_chain(word: str, width: int, height: int, duration: float, scene_index: int) -> str:
    word = _escape_drawtext(word.upper())
    drift = _drift_expr(scene_index, kind="sine")
    fontsize_expr = f"90+min(t/0.4\\,1)*70"
    x_expr = f"(w-text_w)/2+({drift})"
    return (
        f"color=c=black@0.0:s={width}x{height}:d={duration}:r={FPS},format=rgba,"
        # Pass 1: soft bordered rim, blurred -> the glow halo.
        f"drawtext=fontfile={FONT_BOLD_PATH}:text='{word}':"
        f"fontcolor={COLOR_GOLD}@0.5:fontsize='{fontsize_expr}':"
        f"x={x_expr}:y=h*{WORD_Y_FRACTION}:borderw=14:bordercolor={COLOR_GOLD}@0.35,"
        f"gblur=sigma=12,"
        # Pass 2: crisp text on top, no blur.
        f"drawtext=fontfile={FONT_BOLD_PATH}:text='{word}':"
        f"fontcolor=white:fontsize='{fontsize_expr}':"
        f"x={x_expr}:y=h*{WORD_Y_FRACTION}:alpha='min(t/0.3\\,1)'"
        f"[fg]"
    )


def _bounce_chain(word: str, width: int, height: int, duration: float, scene_index: int) -> str:
    word = _escape_drawtext(word.upper())
    drift = _drift_expr(scene_index, kind="linear")
    return (
        f"color=c=black@0.0:s={width}x{height}:d={duration}:r={FPS},format=rgba,"
        f"drawtext=fontfile={FONT_BOLD_PATH}:text='{word}':"
        f"fontcolor={COLOR_GOLD}:fontsize=150:"
        f"x=(w-text_w)/2+({drift}):"
        f"y='h*{WORD_Y_FRACTION} + 140*exp(-4*t)*cos(14*t)':"
        f"alpha='min(t/0.2\\,1)'"
        f"[fg]"
    )


_CHAIN_BUILDERS = {
    "typewriter": _typewriter_chain,
    "glow": _glow_chain,
    "bounce": _bounce_chain,
}


def build_overlay_filter_complex(
    word: str,
    duration: float,
    width: int,
    height: int,
    scene_index: int,
    style: str | None = None,
) -> str:
    """Returns a complete filter_complex string with input pad [0:v], that
    outputs a single [out] pad: background Ken Burns zoom + composited
    kinetic-typography word layer. Caller supplies [0:v] via a single
    `-loop 1 -i <image>` input (matches _ken_burns_clip's existing usage).
    """
    style = style or style_for_scene(scene_index)
    if style not in _CHAIN_BUILDERS:
        raise ValueError(f"Unknown kinetic typography style: {style}")

    frames = max(int(duration * FPS), 1)
    zoom_expr = "if(lte(zoom,1.0),1.5,max(1.5-0.0008*on,1))"
    bg_chain = (
        f"[0:v]scale={width * 2}:{height * 2},"
        f"zoompan=z='{zoom_expr}':d={frames}:s={width}x{height}:fps={FPS}[bg]"
    )
    fg_chain = _CHAIN_BUILDERS[style](word, width, height, duration, scene_index)

    # NOTE: format=auto here, deliberately — see module docstring above
    # about why no format=yuv420p belongs inside this graph.
    return f"{bg_chain};{fg_chain};[bg][fg]overlay=format=auto[out]"
