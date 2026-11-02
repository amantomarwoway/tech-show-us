"""
Per-platform titles, descriptions, captions and hashtags for one story.
Each platform gets text written for ITS format and limits — never one blob
pasted everywhere:

  YouTube long   Reddit-style title (<=100), description with disclosure +
                 up to 5 hashtags, tags.
  YouTube Short  hook-line title + #Shorts, description that links the full story.
  Facebook long  title + description, <=5 hashtags, NO external link (Facebook
                 de-ranks posts that send people off-platform).
  Facebook Reel  hook + soft pointer to the YouTube story, <=5 hashtags.
  Instagram Reel caption: hook + teaser + "link in bio" pointer + <=8 hashtags
                 (Instagram captions cannot hold clickable links).

Everything is English-only: non-ASCII research tags are dropped, and every
title is stripped of characters YouTube rejects.
"""
import re

from src.config import (
    CHANNEL_NAME,
    FB_MAX_HASHTAGS,
    IG_CAPTION_LIMIT,
    IG_MAX_HASHTAGS,
    STORY_CHANNEL_HASHTAGS,
    STORY_GENRE_HASHTAGS,
    YT_MAX_DESC_HASHTAGS,
    YT_TITLE_LIMIT,
)


def _ascii(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text)


def clean_title(text: str, limit: int = YT_TITLE_LIMIT) -> str:
    """No angle brackets (YouTube rejects them), single spaces, cut at a word
    boundary — never mid-word — to fit `limit`."""
    text = re.sub(r"[<>]", "", re.sub(r"\s+", " ", str(text or ""))).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-–—")
    return cut or text[:limit]


def _tagify(phrase: str) -> str | None:
    if not _ascii(phrase):
        return None
    words = re.findall(r"[A-Za-z0-9]+", phrase)
    tag = "".join(w[:1].upper() + w[1:] for w in words)
    return f"#{tag}" if 2 < len(tag) <= 24 and not tag.isdigit() else None


def build_hashtags(story: dict, research: dict | None, limit: int, lead: tuple = ()) -> list[str]:
    """Priority: caller's lead tags, channel tag, genre tags, then real research
    tags, then the remaining channel tags. Case-insensitive de-dupe, capped."""
    candidates = list(lead) + [STORY_CHANNEL_HASHTAGS[0]]
    candidates += list(STORY_GENRE_HASHTAGS.get(story.get("genre", ""), ()))
    for t in ((research or {}).get("suggested_tags") or [])[:10]:
        tag = _tagify(t)
        if tag:
            candidates.append(tag)
    candidates += list(STORY_CHANNEL_HASHTAGS[1:])
    seen, out = set(), []
    for tag in candidates:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            out.append(tag)
        if len(out) >= limit:
            break
    return out


def build_tags(story: dict, research: dict | None, budget: int = 450) -> list[str]:
    """YouTube search tags (separate from hashtags): the story's own tags +
    search keywords + real research tags, ASCII only, within YouTube's ~500
    character total."""
    raw = [CHANNEL_NAME.lower(), f"{story.get('genre', '')} story", "story narration", "scary stories"]
    raw += list(story.get("tags") or []) + list(story.get("search_keywords") or [])
    raw += list(((research or {}).get("suggested_tags") or [])[:10])
    tags, seen, used = [], set(), 0
    for t in raw:
        t = re.sub(r"[<>#]", "", str(t)).strip().lower()
        if not t or not _ascii(t) or t in seen:
            continue
        cost = len(t) + (2 if " " in t else 0) + 1
        if used + cost > budget:
            break
        seen.add(t)
        tags.append(t)
        used += cost
    return tags


def _disclosure(story: dict, short: bool = False) -> str:
    town = story.get("universe_town", "")
    if short:
        return "Fictional story. AI-narrated."
    return (f"This is a work of fiction. All characters, events and places"
            f"{f' (including {town})' if town else ''} are fictional. Narration is AI-generated.")


def _first_para(text: str, limit: int = 600) -> str:
    return re.sub(r"[<>]", "", str(text or "").strip())[:limit].strip()


def build_long_posts(story: dict, research: dict | None) -> dict:
    title = clean_title(story.get("title_long") or story.get("title") or "A story from Blackwood Pines")
    body = _first_para(story.get("description") or story.get("premise") or story.get("hook"))
    cta = f"Subscribe to {CHANNEL_NAME} for a new story every 2 days."
    yt_tags = build_hashtags(story, research, YT_MAX_DESC_HASHTAGS)
    fb_tags = build_hashtags(story, research, FB_MAX_HASHTAGS)
    return {
        "youtube": {
            "title": title,
            "description": f"{body}\n\n{cta}\n\n{_disclosure(story)}\n\n{' '.join(yt_tags)}",
            "tags": build_tags(story, research),
        },
        "facebook": {
            "title": title,
            "description": f"{body}\n\n{cta}\n\n{' '.join(fb_tags)}",
        },
    }


def build_short_posts(story: dict, research: dict | None, short: dict, long_video_id: str | None) -> dict:
    hook = re.sub(r"[<>]", "", str(short.get("hook") or story.get("hook") or story.get("title") or "")).strip()
    hook = hook or "A story from Blackwood Pines"
    link = f"https://youtu.be/{long_video_id}" if long_video_id else None
    yt_tags = build_hashtags(story, research, YT_MAX_DESC_HASHTAGS, lead=("#Shorts",))
    fb_tags = build_hashtags(story, research, FB_MAX_HASHTAGS)
    ig_tags = build_hashtags(story, research, IG_MAX_HASHTAGS)
    title = clean_title(hook, YT_TITLE_LIMIT - len(" #Shorts")) + " #Shorts"
    full = f"Full story: {link}\n\n" if link else ""
    yt_tag_list = build_tags(story, research)
    caption = (
        f"{hook}\n\nThe full story is on YouTube — search \"{CHANNEL_NAME}\" (link in bio).\n\n"
        f"{_disclosure(story, short=True)}\n\n{' '.join(ig_tags)}"
    )
    if len(caption) > IG_CAPTION_LIMIT:
        caption = caption[: IG_CAPTION_LIMIT - 1].rsplit(" ", 1)[0]
    return {
        "youtube": {
            "title": title,
            "description": f"{hook}\n\n{full}Subscribe to {CHANNEL_NAME} for a new story every 2 days.\n\n"
                           f"{_disclosure(story, short=True)}\n\n{' '.join(yt_tags)}",
            "tags": yt_tag_list + ["shorts"] if "shorts" not in yt_tag_list else yt_tag_list,
        },
        "facebook": {
            "description": f"{hook}\n\nFull story on YouTube: {CHANNEL_NAME}\n\n{' '.join(fb_tags)}",
        },
        "instagram": {"caption": caption},
    }
