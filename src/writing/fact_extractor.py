"""
src/writing/fact_extractor.py - v2
- Extracts facts + title + hook from story
- NEVER returns a script shorter than the original
- Returns None on AI failure so caller keeps original script intact
"""

import os
import json
import re
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def extract_facts(story, raw_script=""):
    """
    Extract facts + title + hook.
    IMPORTANT: This function will NEVER return a shorter script than raw_script.
    On AI failure, returns None (caller keeps original).
    """
    topic = story.get('title', '')
    url = story.get('url', '')
    original_wc = len(raw_script.split())

    prompt = f"""Extract SPECIFIC FACTS from this news story.

TOPIC: {topic}
SOURCE: {url}
CONTEXT: {raw_script[:800]}

Extract 3 SPECIFIC FACTS:
- Each fact must have a NUMBER or SPECIFIC DETAIL
- NO generic statements
- Must be interesting and surprising

GOOD: "Apple holds 200 billion in cash reserves"
BAD:  "This is a developing story"

Also create:
- TITLE: 30-50 chars, statement (NO "?"), ends with 1 hashtag
- HOOK: 4-6 words, ALL CAPS

OUTPUT JSON ONLY:
{{
    "facts": ["fact 1 with number", "fact 2 with detail", "fact 3 with number"],
    "title": "Statement title #Hashtag",
    "hook": "TOP HOOK TEXT HERE"
}}

DO NOT include a "script" field. Only facts, title, hook."""

    gk = os.getenv("GEMINI_API_KEY", "")
    if gk:
        try:
            from google import genai
            client = genai.Client(api_key=gk)
            for attempt in range(1, 3):
                try:
                    logger.info(f"Gemini attempt {attempt}/2")
                    resp = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    text = getattr(resp, 'text', '')
                    result = parse_response(text, original_wc)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Gemini: {str(e)[:80]}")
                    if attempt < 2:
                        time.sleep(3)
        except Exception as e:
            logger.warning(f"Gemini client failed: {e}")

    gh = os.getenv("GITHUB_TOKEN", "")
    if gh:
        for endpoint in ["https://models.inference.ai.azure.com",
                         "https://models.github.ai/inference"]:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=gh, base_url=endpoint)
                for model in ["gpt-4o-mini", "gpt-4o"]:
                    try:
                        logger.info(f"GitHub Models {model}")
                        r = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": "Extract facts. JSON only."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=800,
                            response_format={"type": "json_object"}
                        )
                        text = r.choices[0].message.content
                        result = parse_response(text, original_wc)
                        if result:
                            return result
                    except Exception as e:
                        logger.warning(f"GH {model}: {str(e)[:80]}")
                        continue
            except Exception as e:
                logger.warning(f"GH endpoint failed: {e}")
                continue

    # CRITICAL: Return None on failure — caller keeps original script
    logger.info("Fact extraction failed - keeping original script")
    return None


def parse_response(text, original_wc):
    if not text:
        return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
        facts = data.get('facts', [])
        if not isinstance(facts, list) or len(facts) < 2:
            return None

        clean_facts = []
        for f in facts[:4]:
            if isinstance(f, str) and len(f.strip()) > 15:
                clean_facts.append(f.strip())

        if len(clean_facts) < 2:
            return None

        title = data.get('title', '').strip()
        hook = data.get('hook', '').strip()

        if not title:
            return None

        title = re.sub(r'#\w+', '', title).strip()
        title = title.replace('?', '').strip()
        hashtags = re.findall(r'#\w+', data.get('title', ''))
        hashtag = hashtags[0] if hashtags else '#Facts'

        title = f"{title} {hashtag}"
        if len(title) > 55:
            title = title[:52].rsplit(' ', 1)[0] + f" {hashtag}"

        logger.info(f"Extracted {len(clean_facts)} facts")
        for i, f in enumerate(clean_facts):
            logger.info(f"   Fact {i+1}: {f[:70]}")

        # NOTE: NO script returned — main.py keeps original 128-word script
        return {
            'facts': clean_facts,
            'title': title,
            'hook': hook.upper() if hook else "DID YOU KNOW"
        }
    except Exception as e:
        logger.warning(f"Parse failed: {e}")
        return None
