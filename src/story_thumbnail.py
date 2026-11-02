"""
Thumbnail for a story's long video: ONE specific dark, atmospheric moment from
the story (the writer's `thumbnail_concept`), Western-styled like every other
image, with at most two overlaid words (`thumbnail_text`) — the image has to
carry the intrigue, not a wall of text. Saved as a JPEG under YouTube's 2 MB
limit. Never raises: a missing thumbnail must not block publishing the video.
"""
import logging
from pathlib import Path

from src.config import SCENES_DIR
from src.story_pipeline import styled_prompt
from src.visual_generator import generate_scene_image

log = logging.getLogger(__name__)

THUMB_W, THUMB_H = 1280, 720
MAX_BYTES = 1_900_000
_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _compose(base: Path, text: str, out: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(base).convert("RGB")
    if img.size != (THUMB_W, THUMB_H):  # cover-crop to exactly 16:9
        scale = max(THUMB_W / img.width, THUMB_H / img.height)
        img = img.resize((int(img.width * scale) + 1, int(img.height * scale) + 1))
        left, top = (img.width - THUMB_W) // 2, (img.height - THUMB_H) // 2
        img = img.crop((left, top, left + THUMB_W, top + THUMB_H))
    if text:
        # darken the lower third so the words stay readable on any image
        shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(shade)
        for y in range(THUMB_H // 2, THUMB_H):
            d.line([(0, y), (THUMB_W, y)], fill=(0, 0, 0, int(190 * (y - THUMB_H // 2) / (THUMB_H // 2))))
        img = Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB")
        try:
            font = ImageFont.truetype(_FONT, 150 if len(text) <= 10 else 110)
        except OSError:
            font = ImageFont.load_default()
        draw = ImageDraw.Draw(img)
        box = draw.textbbox((0, 0), text, font=font, stroke_width=8)
        x = (THUMB_W - (box[2] - box[0])) // 2
        y = THUMB_H - (box[3] - box[1]) - 70
        draw.text((x, y), text, font=font, fill="#FFD700", stroke_width=8, stroke_fill="black")
    quality = 92
    while True:
        img.save(out, "JPEG", quality=quality)
        if out.stat().st_size <= MAX_BYTES or quality <= 55:
            return out
        quality -= 8


def build_story_thumbnail(story: dict) -> Path | None:
    concept = story.get("thumbnail_concept") or story.get("premise") or story.get("title_long") or "a dark empty road at night"
    prompt = styled_prompt(
        f"{concept}, movie poster composition, dark blue and grey tones with one small red-amber accent, eerie"
    )
    try:
        base = generate_scene_image(prompt, "story_thumb", THUMB_W, THUMB_H)
        return _compose(Path(base), str(story.get("thumbnail_text") or "").strip(), SCENES_DIR / "story_thumb_final.jpg")
    except Exception as e:
        log.error("Story thumbnail failed (%s) — publishing without a custom thumbnail", e)
        return None
