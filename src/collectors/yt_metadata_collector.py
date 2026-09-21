"""
src/collectors/yt_metadata_collector.py
- Transcript (v1.x API)
- Script from AI (Pollinations.ai FREE + Groq fallback) — NATURAL LENGTH
- Emoji/hashtag/channel-promo removal
"""

import os
import re
import json
import time
import urllib.parse
import requests
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    text = re.sub(r'#\w+', '', text)  # remove hashtags
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_transcript(video_id):
    if not video_id:
        return None
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        return None

    # New API (v1.x)
    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        snippets = list(fetched)
        text = " ".join(
            (s.text if hasattr(s, 'text') else s.get('text', '')) for s in snippets
        )
        text = _clean_text(text)
        if len(text) > 50:
            logger.info(f"Transcript OK: {len(text)} chars")
            return text
    except Exception as e:
        logger.warning(f"Transcript v1 API failed: {str(e)[:100]}")

    # Old API fallback
    try:
        tl = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t = tl.find_manually_created_transcript(['en', 'en-US', 'en-GB'])
        except Exception:
            try:
                t = tl.find_generated_transcript(['en', 'en-US', 'en-GB'])
            except Exception:
                t = next(iter(tl)).translate('en')
        data = t.fetch()
        text = " ".join(
            (seg.get('text', '') if isinstance(seg, dict) else seg.text)
            for seg in data
        )
        text = _clean_text(text)
        if len(text) > 50:
            logger.info(f"Transcript OK (old API): {len(text)} chars")
            return text
    except Exception as e:
        logger.warning(f"Transcript old API failed: {str(e)[:100]}")

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
    stop = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "can",
        "to", "of", "in", "on", "at", "by", "for", "with", "about", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "from", "up", "down", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "s", "t", "just", "don", "now", "i", "you",
        "he", "she", "it", "we", "they", "this", "that", "these", "those",
        "what", "which", "who", "whom", "your", "my", "his", "her", "our",
        "their", "its", "like", "get", "got", "go", "going", "one", "two",
    }
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    freq = {}
    for w in words:
        if w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:top_n]]


# ============================================================
# NATURAL-LENGTH SCRIPT PROMPT (no force)
# ============================================================

def _build_prompt(title, description, transcript):
    tp = transcript[:2500] if transcript else "No transcript available."
    dp = description[:400] if description else "No description."

    return f"""You are a viral YouTube Shorts scriptwriter. Write a factual, engaging script.

SOURCE:
Title: {title}
Description: {dp}
Transcript: {tp}

TASK:
Write a script that FULLY covers this trending topic. Let the content decide the length — no filler, no padding.

NATURAL LENGTH RULE:
- Short topic → 40-60 words
- Rich topic → 90-130 words
- Use only as many words as the content genuinely needs

RULES:
- First sentence = strong hook
- Then 3-7 facts with specific numbers, names, or dates from the source
- Include 1 direct question to the viewer midway
- End with a mystery / tease
- Short sentences for natural TTS rhythm
- NO filler ("in conclusion", "stay tuned", "let's dive in")
- NO emojis, NO hashtags, NO markdown, NO channel promo
- If music video: artist, chart impact, fan reaction
- If gameplay: challenge, scale, outcome
- If sports: moment, stats, context

ALSO generate 12-15 YouTube tags (lowercase words/phrases, no #).

OUTPUT JSON ONLY (no markdown, no code fences):
{{
  "script": "the full script here",
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
    if not script or len(script.split()) < 30:
        return None
    if not isinstance(tags, list):
        tags = []
    tags = [
        str(t).strip().lower().lstrip('#')
        for t in tags if isinstance(t, str) and len(str(t).strip()) >= 2
    ][:15]
    return {"script": script, "tags": tags}


def _try_pollinations(prompt, timeout=90):
    try:
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}?model=openai&json=true"
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            logger.warning(f"Pollinations HTTP {r.status_code}")
            return None
        return _parse_ai_json(r.text)
    except Exception as e:
        logger.warning(f"Pollinations fail: {str(e)[:120]}")
        return None


def _try_groq(prompt, timeout=60):
    gk = os.getenv("GROQ_API_KEY", "")
    if not gk:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {gk}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
                "max_tokens": 1500,
            },
            timeout=timeout,
        )
        if r.status_code != 200:
            logger.warning(f"Groq HTTP {r.status_code}")
            return None
        content = r.json()["choices"][0]["message"]["content"]
        return _parse_ai_json(content)
    except Exception as e:
        logger.warning(f"Groq fail: {str(e)[:120]}")
        return None


def generate_script_and_tags(title, description, transcript):
    """Try Pollinations → Groq → Pollinations retry."""
    prompt = _build_prompt(title, description, transcript)

    logger.info("AI: Pollinations")
    r = _try_pollinations(prompt)
    if r:
        logger.info(f"Pollinations OK: {len(r['script'].split())} words, {len(r['tags'])} tags")
        return r

    if os.getenv("GROQ_API_KEY", ""):
        logger.info("AI: Groq")
        r = _try_groq(prompt)
        if r:
            logger.info(f"Groq OK: {len(r['script'].split())} words")
            return r

    logger.info("AI: Pollinations retry")
    time.sleep(2)
    r = _try_pollinations(prompt)
    if r:
        logger.info(f"Pollinations retry OK: {len(r['script'].split())} words")
        return r

    logger.error("All AI attempts failed")
    return None
