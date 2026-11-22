"""
Per-platform titles, descriptions, captions and hashtags for one EPISODE of a series. Each platform gets
text written for ITS format and limits — never one blob pasted everywhere:

  YouTube long   "<hook> (Part N) | Scary Story": the hook gets the click, "Part N" tells a browsing viewer
                 this is an episode, the trailing English search phrase tells YouTube what the video is
                 (a new channel has no watch history — its TEXT is how it gets matched to searches). The
                 description's FIRST LINE carries the series, the part and two search phrases (that is
                 what shows in results), then links to the previous part, the series playlist and a
                 note on when the next part drops. Tags start with the genre's search phrases.
  YouTube Short  hook-line title + #Shorts; description links the full episode and the series.
  Facebook long  title + description, <=5 hashtags, NO external link (Facebook de-ranks posts that send
                 people off-platform).
  Facebook Reel  hook + soft pointer to the YouTube episode, <=5 hashtags.
  Instagram Reel caption: hook + teaser + "link in bio" pointer + <=8 hashtags (captions cannot hold
                 clickable links).

Everything is English-only and every claim is accurate: non-ASCII or off-niche research tags are dropped,
titles are stripped of characters YouTube rejects, and no phrase calls the videos "animated" or "true".
"""
import re

from src.config import (
    CHANNEL_NAME,
    FB_MAX_HASHTAGS,
    IG_CAPTION_LIMIT,
    IG_MAX_HASHTAGS,
    STORY_CHANNEL_HASHTAGS,
    STORY_GENRE_HASHTAGS,
    STORY_SEARCH_KEYWORDS,
    STORY_TITLE_KEYWORD,
    YT_MAX_DESC_HASHTAGS,
    YT_TITLE_LIMIT,
)


def _ascii(text: str) -> bool:
    return all(ord(ch) < 128 for ch in text)


def clean_title(text: str, limit: int = YT_TITLE_LIMIT) -> str:
    """No angle brackets (YouTube rejects them), single spaces, cut at a word boundary — never mid-word —
    to fit `limit`."""
    text = re.sub(r"[<>]", "", re.sub(r"\s+", " ", str(text or ""))).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-–—")
    return cut or text[:limit]


# A research tag is only reused if it is about THIS niche (a real run's research surfaced "movie explained
# in tamil"; it must never reach the channel's hashtags).
_NICHE_WORDS = (
    "horror", "scary", "creepy", "ghost", "haunted", "paranormal", "crime", "murder", "killer",
    "detective", "thriller", "suspense", "mystery", "story", "stories", "narration", "fiction",
    "nightmare", "unsolved", "investigation", "darky", "spooky", "twist",
)
_OTHER_LANGUAGES = ("tamil", "hindi", "telugu", "malayalam", "kannada", "urdu", "bangla", "dubbed", "movie", "explained", "review", "trailer")


def _relevant(tag: str) -> bool:
    t = str(tag).lower()
    return any(w in t for w in _NICHE_WORDS) and not any(w in t for w in _OTHER_LANGUAGES)


def _tagify(phrase: str) -> str | None:
    if not _ascii(phrase):
        return None
    words = re.findall(r"[A-Za-z0-9]+", phrase)
    tag = "".join(w[:1].upper() + w[1:] for w in words)
    return f"#{tag}" if 2 < len(tag) <= 24 and not tag.isdigit() else None


def build_hashtags(story: dict, research: dict | None, limit: int, lead: tuple = ()) -> list[str]:
    """Priority: caller's lead tags, channel tag, genre tags, then real research tags, then the remaining
    channel tags. Case-insensitive de-dupe, capped."""
    candidates = list(lead) + [STORY_CHANNEL_HASHTAGS[0]]
    candidates += list(STORY_GENRE_HASHTAGS.get(story.get("genre", ""), ()))
    for t in ((research or {}).get("suggested_tags") or [])[:20]:
        if not _relevant(t):
            continue
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
    """YouTube search tags: the genre's SEARCH PHRASES first (highest weight), then the story's own tags,
    then niche-relevant research tags — ASCII only, within YouTube's ~500 character total."""
    genre = story.get("genre", "")
    raw = [CHANNEL_NAME.lower()] + list(STORY_SEARCH_KEYWORDS.get(genre, ())) + [f"{genre} story", "story narration"]
    raw += list(story.get("tags") or []) + list(story.get("search_keywords") or [])
    raw += [t for t in ((research or {}).get("suggested_tags") or [])[:20] if _relevant(t)]
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


def _part_tag(part_no: int | None, mode: str | None) -> str:
    if not part_no:
        return ""
    return "(Final Part)" if mode == "finale" else f"(Part {part_no})"


def episode_title(story: dict, part_no: int | None = None, mode: str | None = None) -> str:
    """"<hook> (Part N) | Scary Story" within 100 characters. When it does not fit, the search phrase is
    dropped first, then the hook is trimmed at a word boundary — the part tag is never cut."""
    hook = clean_title(story.get("title_long") or story.get("title") or "A story from Blackwood Pines", 90)
    tag = _part_tag(part_no, mode)
    kw = STORY_TITLE_KEYWORD.get(story.get("genre", ""), "")
    for suffix in (f" | {kw}" if kw else "", ""):
        title = " ".join(x for x in (hook, tag) if x) + suffix
        if len(title) <= YT_TITLE_LIMIT:
            return title
    room = YT_TITLE_LIMIT - len(tag) - 1
    return " ".join(x for x in (clean_title(hook, max(room, 10)), tag) if x)


def _keyword_line(story: dict, n: int = 2) -> str:
    return " | ".join(k.title() for k in STORY_SEARCH_KEYWORDS.get(story.get("genre", ""), ())[:n])


def build_long_posts(story: dict, research: dict | None, *, series: dict | None = None,
                     part_no: int | None = None, mode: str | None = None, prev_url: str | None = None,
                     playlist_url: str | None = None, next_label: str = "") -> dict:
    title = episode_title(story, part_no if series else None, mode)
    body = _first_para(story.get("description") or story.get("premise") or story.get("hook"))
    cta = f"Subscribe to {CHANNEL_NAME} — new parts every week."
    yt_tags = build_hashtags(story, research, YT_MAX_DESC_HASHTAGS)
    fb_tags = build_hashtags(story, research, FB_MAX_HASHTAGS)

    lines = []
    if series:
        label = "Final Part" if mode == "finale" else f"Part {part_no}"
        lines.append(f"{series['title']} — {label} | {_keyword_line(story)}")
    elif _keyword_line(story):
        lines.append(_keyword_line(story))
    lines += ["", body, ""]
    if series:
        if prev_url:
            lines.append(f"▶ Previous part: {prev_url}")
        if playlist_url:
            lines.append(f"▶ The whole series, in order: {playlist_url}")
        if mode != "finale" and next_label:
            lines.append(f"▶ Next: Part {part_no + 1} {next_label}")
        lines.append("")
    lines += [cta, "", _disclosure(story), "", " ".join(yt_tags)]
    return {
        "youtube": {"title": title, "description": "\n".join(lines).replace("\n\n\n", "\n\n").strip(),
                    "tags": build_tags(story, research)},
        "facebook": {"title": title, "description": f"{body}\n\n{cta}\n\n{' '.join(fb_tags)}"},
    }


def build_short_posts(story: dict, research: dict | None, short: dict, long_video_id: str | None, *,
                      series: dict | None = None, part_no: int | None = None, mode: str | None = None,
                      playlist_url: str | None = None) -> dict:
    hook = re.sub(r"[<>]", "", str(short.get("hook") or story.get("hook") or story.get("title") or "")).strip()
    hook = hook or "A story from Blackwood Pines"
    link = f"https://youtu.be/{long_video_id}" if long_video_id else None
    yt_tags = build_hashtags(story, research, YT_MAX_DESC_HASHTAGS, lead=("#Shorts",))
    fb_tags = build_hashtags(story, research, FB_MAX_HASHTAGS)
    ig_tags = build_hashtags(story, research, IG_MAX_HASHTAGS)
    title = clean_title(hook, YT_TITLE_LIMIT - len(" #Shorts")) + " #Shorts"
    which = (f"{series['title']} — " if series else "") + ("Final Part" if mode == "finale" else f"Part {part_no}" if part_no else "")
    which = which.rstrip(" —")
    full = f"▶ Full story{f' ({which})' if which else ''}: {link}\n" if link else ""
    pl = f"▶ The whole series, in order: {playlist_url}\n" if playlist_url else ""
    yt_tag_list = build_tags(story, research)
    caption = (
        f"{hook}\n\nThe full story{f' — {which}' if which else ''} is on YouTube: search \"{CHANNEL_NAME}\" (link in bio).\n\n"
        f"{_disclosure(story, short=True)}\n\n{' '.join(ig_tags)}"
    )
    if len(caption) > IG_CAPTION_LIMIT:
        caption = caption[: IG_CAPTION_LIMIT - 1].rsplit(" ", 1)[0]
    return {
        "youtube": {
            "title": title,
            "description": f"{hook}\n\n{full}{pl}Tap the related video below to watch the full story.\n"
                           f"Subscribe to {CHANNEL_NAME} — new parts every week.\n\n"
                           f"{_disclosure(story, short=True)}\n\n{' '.join(yt_tags)}",
            "tags": yt_tag_list + ["shorts"] if "shorts" not in yt_tag_list else yt_tag_list,
        },
        "facebook": {
            "description": f"{hook}\n\nFull story on YouTube: {CHANNEL_NAME}{f' — {which}' if which else ''}\n\n{' '.join(fb_tags)}",
        },
        "instagram": {"caption": caption},
    }
