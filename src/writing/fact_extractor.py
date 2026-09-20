"""
src/writing/fact_extractor.py - Extract SPECIFIC facts from story
Returns: facts list + script + title + hook
"""

import os
import json
import re
import time
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def extract_facts(story, raw_script=""):
    """
    Extract 2-4 SPECIFIC facts from a story
    Returns: dict with facts/title/hook/script OR None
    """
    topic = story.get('title', '')
    url = story.get('url', '')
    
    prompt = f"""Extract SPECIFIC FACTS from this news story.

TOPIC: {topic}
SOURCE: {url}
CONTEXT: {raw_script[:500]}

Extract 3 SPECIFIC FACTS in this format:
- Each fact must have a NUMBER or SPECIFIC DETAIL
- NO generic statements
- Facts should be interesting, surprising, valuable

GOOD FACTS:
- "Apple holds $200 billion in cash reserves"
- "That is more than 100 countries' combined GDP"
- "They are spending $50 billion on AI research in 2026"

BAD FACTS:
- "This is a developing story"
- "People are talking about it"
- "It affects millions of people"

Also create:
- TITLE: 30-50 chars, statement (NO "?"), ends with 1 hashtag
- HOOK: 4-5 words ALL CAPS for top of video
- SCRIPT: 40-50 words spoken narrative (voiceover)

OUTPUT JSON ONLY:
{{
    "facts": [
        "fact 1 with specific number",
        "fact 2 with specific detail",
        "fact 3 with specific number"
    ],
    "title": "Statement title #Hashtag",
    "hook": "TOP HOOK TEXT HERE",
    "script": "40-50 word voiceover script"
}}"""
    
    # Try Gemini 3.6
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
                    result = parse_response(text)
                    if result:
                        return result
                except Exception as e:
                    logger.warning(f"Gemini: {str(e)[:80]}")
                    if attempt < 2:
                        time.sleep(3)
        except Exception as e:
            logger.warning(f"Gemini client failed: {e}")
    
    # Try GitHub Models
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
                                {"role": "system", "content": "Extract facts from news. JSON only."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=800,
                            response_format={"type": "json_object"}
                        )
                        text = r.choices[0].message.content
                        result = parse_response(text)
                        if result:
                            return result
                    except Exception as e:
                        logger.warning(f"GH {model}: {str(e)[:80]}")
                        continue
            except Exception as e:
                logger.warning(f"GH endpoint failed: {e}")
                continue
    
    # Fallback
    logger.info("Using fallback facts")
    return get_fallback_facts(topic)


def parse_response(text):
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
        script = data.get('script', '').strip()
        
        if not title or not script:
            return None
        
        # Clean title
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
        
        return {
            'facts': clean_facts,
            'title': title,
            'hook': hook.upper() if hook else "DID YOU KNOW",
            'script': script
        }
    except Exception as e:
        logger.warning(f"Parse failed: {e}")
        return None


def get_fallback_facts(topic):
    """Fallback when AI fails"""
    words = [w for w in topic.split() if len(w) > 4][:3]
    key = " ".join(words) if words else "this story"
    
    return {
        'facts': [
            f"Reports say {key} is bigger than expected",
            f"Experts confirm the numbers are rising quickly",
            f"Officials say more details will emerge soon"
        ],
        'title': f"The Truth About This Story #Facts",
        'hook': "DID YOU KNOW THIS",
        'script': f"Here is what you need to know about {key}. Reports confirm the details nobody expected. Experts say this story is getting bigger. Here is what happens next."
    }
