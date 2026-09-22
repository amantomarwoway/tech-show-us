"""
src/collectors/yt_metadata_collector.py
- Transcript (v1.2.0 compatible)
- Script from Gemini 3.6 Flash (NO Pollinations)
"""

import os
import re
import json
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

GEMINI_MODEL = "gemini-3.6-flash"

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U0001F000-\U0001F02F"
    "]+",
    flags=re.UNICODE
)


def _clean_text(text):
    if not text:
        return ""
    text = EMOJI_PATTERN.sub('', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    text = re.sub(r'>>\s*', '', text)
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'[‑—–]', '-', text)
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_transcript(video_id):
    """Fetch transcript (v1.2.0 compatible)."""
    if not video_id:
        return None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    # NEW API (v1.2.0+)
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        snippets = list(fetched)
        text = " ".join(
            (s.text if hasattr(s, 'text') else s.get('text', ''))
            for s in snippets
        )
        text = _clean_text(text)
        if len(text) > 50:
            logger.info(f"Transcript OK: {len(text)} chars")
            return text
    except Exception as e:
        logger.warning(f"Transcript fetch failed: {str(e)[:100]}")

    return None


def extract_hashtags(description):
    if not description:
        return []
    tags = re.findall(r'#\w+', description)
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)
    return unique[:10]


def extract_keywords(text, top_n=15):
    stop = {"the","a","an","and","or","but","is","are","was","were","be","been",
            "being","have","has","had","do","does","did","will","would","could",
            "should","may","might","must","can","to","of","in","on","at","by",
            "for","with","about","as","into","through","during","before","after",
            "above","below","from","up","down","out","off","over","under","again",
            "further","then","once","here","there","when","where","why","how","all",
            "any","both","each","few","more","most","other","some","such","no",
            "nor","not","only","own","same","so","than","too","very","s","t",
            "just","don","now","i","you","he","she","it","we","they","this","that",
            "these","those","what","which","who","whom","your","my","his","her",
            "our","their","its","like","get","got","go","going","one","two"}
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    freq = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top_n]]


def _build_prompt(title, description, transcript):
    tp = transcript[:3000] if transcript else "No transcript available."
    dp = description[:600] if description else "No description."

    return f"""You are a viral YouTube Shorts scriptwriter.

SOURCE:
Title: {title}
Description: {dp}
Transcript: {tp}

TASK: Write a factual script that FULLY covers this topic. Natural length — 70-130 words. No filler, no padding.

RULES:
- First sentence = strong hook
- 3-7 facts with specific numbers/names/dates
- 1 direct question to viewer midway
- End with a mystery
- Short sentences, natural TTS rhythm
- NO filler ("stay tuned", "think again", "in conclusion", "let's dive in")
- NO emojis, NO hashtags, NO markdown, NO channel promo
- NO "picture the day" style intros
- Start with a FACT or a specific moment

ALSO generate 12-15 YouTube tags (lowercase, no #).

OUTPUT JSON ONLY (no markdown, no code fences):
{{
  "script": "the full script",
  "tags": ["tag1", "tag2", "..."]
}}"""


def _parse_ai_json(text):
    if not text:
        return None
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text)
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except Exception:
        return None
    script = _clean_text(data.get('script', '').strip())
    tags = data.get('tags', [])
    if not script or len(script.split()) < 40:
        return None
    if not isinstance(tags, list):
        tags = []
    tags = [
        str(t).strip().lower().lstrip('#')
        for t in tags if isinstance(t, str) and len(str(t).strip()) >= 2
    ][:15]
    return {"script": script, "tags": tags}


def _try_gemini(prompt, timeout=90):
    """Generate script via Gemini 3.6 Flash."""
    gk = os.getenv("GEMINI_API_KEY", "")
    if not gk:
        logger.warning("GEMINI_API_KEY missing")
        return None
    try:
        from google import genai
        client = genai.Client(api_key=gk)
        for attempt in range(1, 3):
            try:
                logger.info(f"Gemini attempt {attempt}/2")
                resp = client.models.generate_content(
                    model=GEMINI_MODEL, contents=prompt
                )
                text = getattr(resp, 'text', '') or ''
                if not text:
                    continue
                result = _parse_ai_json(text)
                if result:
                    return result
            except Exception as e:
                err = str(e)
                logger.warning(f"Gemini attempt {attempt}: {err[:120]}")
                if attempt < 2:
                    time.sleep(3)
    except Exception as e:
        logger.error(f"Gemini client failed: {e}")
    return None


def generate_script_and_tags(title, description, transcript):
    """
    Generate script + tags via Gemini 3.6 Flash only.
    No Pollinations, no fallback.
    """
    prompt = _build_prompt(title, description, transcript)

    logger.info("AI: Gemini 3.6 Flash")
    result = _try_gemini(prompt)
    if result:
        logger.info(f"Gemini OK: {len(result['script'].split())} words, "
                    f"{len(result['tags'])} tags")
        return result

    logger.error("Gemini failed — no fallback available")
    return None
