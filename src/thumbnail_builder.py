"""
Builds the clickable thumbnail: AI-generated base image (word + human shadow)
via visual_generator, with an optional Pillow text overlay for extra CTR
punch (kept subtle since the AI image already renders the word in-scene).
"""
import logging
from pathlib import Path

from src.config import COLOR_GOLD, FONT_BOLD
from src.visual_generator import generate_thumbnail as _generate_base_thumbnail

log = logging.getLogger(__name__)


def _overlay_hook_text(image_path: Path, hook_words: str, out_path: Path) -> Path:
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{FONT_BOLD}.ttf", 64)
        except OSError:
            font = ImageFont.load_default()

        # Bottom-left small hook text banner for extra CTR without cluttering
        # the AI-generated word+shadow composition.
        margin = 40
        text_pos = (margin, img.height - 120)
        bbox = draw.textbbox(text_pos, hook_words, font=font)
        draw.rectangle(
            [bbox[0] - 10, bbox[1] - 10, bbox[2] + 10, bbox[3] + 10], fill=(0, 0, 0)
        )
        draw.text(text_pos, hook_words, font=font, fill=COLOR_GOLD)
        img.save(out_path, quality=95)
        return out_path
    except Exception as e:
        log.warning("Thumbnail text overlay failed (%s); using base AI thumbnail as-is", e)
        return image_path


def build_thumbnail(word: str, hook_snippet: str = "") -> Path:
    base = _generate_base_thumbnail(word)
    if not hook_snippet:
        return base
    overlaid_path = base.with_name(f"thumbnail_{word}_overlay.jpg")
    return _overlay_hook_text(base, hook_snippet[:30], overlaid_path)
