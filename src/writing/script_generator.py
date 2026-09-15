"""
src/writing/script_generator.py - Script generation engine
"""

import os
import json
import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def generate_script(story, target_duration=30):
    """
    Generate script for YouTube Short
    
    target_duration: 20, 30, 45, or 60 seconds
    """
    topic = story.get('title', '')
    
    # Try AI generation
    script = try_ai_script_generation(story, target_duration)
    
    if not script:
        script = generate_template_script(story, target_duration)
    
    return script


def try_ai_script_generation(story, target_duration):
    """Try to generate script using AI"""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if not gemini_key:
        return None
    
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        
        topic = story.get('title', '')
        word_count = {
            20: '35-40',
            30: '45-50',
            45: '60-70',
            60: '80-90'
        }.get(target_duration, '45-50')
        
        prompt = f"""
Write a YouTube Shorts script about this news topic.

TOPIC: {topic}
DURATION: {target_duration} seconds ({word_count} words)

REQUIREMENTS:
1. First sentence = shocking hook (pattern interrupt)
2. Use "according to reports" for unverified claims
3. NO "hello guys", NO intro
4. End with open loop / "what happens next"
5. Factual, neutral, accurate

STRUCTURE:
0-2 sec: HOOK
2-7 sec: WHAT HAPPENED
7-20 sec: WHY IT MATTERS
20-40 sec: MOST IMPORTANT DETAIL
40-55 sec: WHAT HAPPENS NEXT
Final: OPEN LOOP

OUTPUT JSON ONLY:
{{
    "hook": "first sentence",
    "script": "full script",
    "facts": ["fact1", "fact2"],
    "sources": ["source1", "source2"]
}}
"""
        
        for model in ["gemini-2.0-flash", "gemini-1.5-flash"]:
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                text = getattr(resp, 'text', '')
                
                if text:
                    match = re.search(r'\{.*\}', text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        logger.info(f"AI script generated ({model})")
                        return data
            except Exception as e:
                logger.warning(f"AI script {model} failed: {e}")
                continue
    
    except Exception as e:
        logger.warning(f"AI script generation failed: {e}")
    
    return None


def generate_template_script(story, target_duration):
    """Generate template-based script (fallback)"""
    topic = story.get('title', 'Breaking News')
    
    scripts = {
        20: f"Breaking: {topic}. According to reports, this changes everything. Officials say the situation is developing. What happens next?",
        30: f"Breaking: {topic}. According to multiple sources, this is a major development. Officials have confirmed the basic facts. The situation continues to evolve. Here's what we know. What happens next?",
        45: f"Breaking news: {topic}. According to reports, this development could affect millions. Officials say the situation is still developing. Here's what we know so far. The key facts are still emerging. This story is developing and we will update as more information becomes available.",
        60: f"Breaking news: {topic}. According to multiple sources, this is a developing story with major implications. Officials have confirmed the basic facts but caution that the situation is still evolving. Here's what we know so far. The key questions remain unanswered. We will continue to monitor this story and provide updates as more information becomes available."
    }
    
    return {
        "hook": f"Breaking: {topic}",
        "script": scripts.get(target_duration, scripts[30]),
        "facts": [],
        "sources": []
    }


def create_fact_map(script_text, sources):
    """
    Create FACT_MAP linking sentences to sources
    
    Returns:
        list of {sentence_id, factual_claim, source_url, confidence}
    """
    sentences = re.split(r'[.!?]+', script_text)
    
    fact_map = []
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        
        fact_map.append({
            'sentence_id': i,
            'factual_claim': sentence,
            'source_url': sources[i % len(sources)] if sources else '',
            'confidence': 50
        })
    
    return fact_map
