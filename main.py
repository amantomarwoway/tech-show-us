"""
main.py - GOD LEVEL YOUTUBE SHORTS BOT v5
Question-hook ONLY system + AI Visual Queries
- Title: ONLY QUESTION + 1 hashtag (no publisher names EVER)
- White bar: 4-5 word question (no emoji)
- Script: Answers the question
- AI provides 6 visual search queries
- Duplicate stories skipped
- Any TRENDING topic
"""

import os
import sys
import time
import traceback
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES, PUBLISH_THRESHOLDS
from src.utils.logger import setup_logger
from src.database import init_db, save_story, mark_uploaded, get_performance_stats

logger = setup_logger(__name__)


# ============================================================
# 🧹 AGGRESSIVE TOPIC CLEANING
# ============================================================

def clean_topic(title):
    """Remove ALL publisher prefixes/suffixes"""
    if not title:
        return ""
    
    cleaned = title.strip()
    
    if '|' in cleaned:
        parts = cleaned.split('|')
        cleaned = max(parts, key=len).strip()
    
    publisher_patterns = [
        r'^(?:[A-Z][A-Za-z]+\s*){1,4}(?:NEWS|MEDIA|TIMES|POST|TODAY|NOW|TV|PRESS|JOURNAL|REPORT)\s*[-:]\s*',
        r'^(?:MINNEAPOLI|CNN|BBC|ABC|NBC|CBS|FOX|MSNBC|NYT|WSJ|AP|REUTERS)[A-Za-z]*\s*[-:]\s*',
    ]
    
    for pattern in publisher_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\b[A-Z]{4,}[A-Za-z]*MEDIA\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\b[A-Z]{4,}[A-Za-z]*NEWS\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bBREAKING\s+NEWS\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bBREAKING\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bLIVE\s+UPDATE\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bLIVE\b', '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\s*-\s*[A-Z][a-zA-Z\s]{2,30}$', '', cleaned)
    cleaned = re.sub(r'\s*\([A-Za-z\s]{2,30}\)\s*$', '', cleaned)
    
    cleaned = re.sub(r'^[\|\-\s:]+', '', cleaned)
    cleaned = re.sub(r'[\|\-\s:]+$', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


def has_publisher_name(text):
    """Check if text contains publisher name"""
    if not text:
        return False
    
    bad_words = [
        'MINNEAPOLI', 'BREAKING NEWS', 'CNN', 'BBC', 'ABC', 'NBC', 'CBS',
        'FOX', 'MSNBC', 'NYT', 'WSJ', 'APNEWS', 'REUTERS', 'DAILY',
        'TIMES', 'POST', 'JOURNAL', 'PRESS', 'MEDIA'
    ]
    
    text_upper = text.upper()
    for bad in bad_words:
        if bad in text_upper:
            return True
    return False


# ============================================================
# SAFE IMPORT
# ============================================================

def safe_import(module_path, function_name=None):
    try:
        if function_name:
            module = __import__(module_path, fromlist=[function_name])
            return getattr(module, function_name)
        else:
            return __import__(module_path)
    except Exception as e:
        logger.warning(f"Import failed {module_path}: {e}")
        return None


# ============================================================
# 🔥 LEG 1: RESEARCH GOD
# ============================================================

def research_god_main():
    """Collect TRENDING topics from ALL sources"""
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD - ALL TRENDING TOPICS")
    logger.info("=" * 60)
    
    all_stories = []
    
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            s = trends_collector()
            logger.info(f"🔥 Google Trends: {len(s)} trending topics")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            s = reddit_collector()
            logger.info(f"🔥 Reddit (r/all, r/popular): {len(s)} trending stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            s = google_collector()
            logger.info(f"🔥 Google News: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
    rss_collector = safe_import('src.collectors.rss_collector', 'collect_rss_news')
    if rss_collector:
        try:
            s = rss_collector()
            logger.info(f"🔥 RSS (all categories): {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"RSS failed: {e}")
    
    if not all_stories:
        logger.warning("All collectors failed - using fallback")
        all_stories = get_guaranteed_stories()
    
    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
        if not story['title'] or len(story['title']) < 5:
            story['title'] = 'Trending Topic'
    
    all_stories = [s for s in all_stories if s.get('title') and len(s['title']) > 5]
    
    all_stories = deduplicate_stories(all_stories)
    ranked = score_and_rank_stories(all_stories)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} trending stories (ALL TOPICS)")
    
    for i, story in enumerate(ranked[:5]):
        logger.info(f"  #{i+1}: {story.get('title', '')[:60]} | Type: {story.get('story_type', 'trending')}")
    
    return ranked[:10]


def get_guaranteed_stories():
    return [
        {
            "title": "Why Is Everyone Talking About This?",
            "url": "https://trends.google.com",
            "source": "guaranteed_trends",
            "breakout_score": 6000,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title": "Why Is Everyone Talking About This?"
        },
        {
            "title": "This Viral Moment Just Broke The Internet",
            "url": "https://trends.google.com",
            "source": "guaranteed_trends",
            "breakout_score": 5800,
            "is_breakout": True,
            "search_volume": 88,
            "seo_youtube_title": "What Made This Go Viral?"
        },
        {
            "title": "New Trend Everyone Is Following Today",
            "url": "https://trends.google.com",
            "source": "guaranteed_trends",
            "breakout_score": 5700,
            "is_breakout": True,
            "search_volume": 85,
            "seo_youtube_title": "What Is This New Trend?"
        },
    ]


def deduplicate_stories(stories):
    seen = set()
    unique = []
    for story in stories:
        title = story.get('title', '').lower().strip()
        key = title[:30] if len(title) > 30 else title
        if key not in seen:
            seen.add(key)
            unique.append(story)
    logger.info(f"Dedup: {len(stories)} -> {len(unique)}")
    return unique


def score_and_rank_stories(stories):
    story_ranker = safe_import('src.intelligence.story_ranker', 'rank_stories')
    if story_ranker:
        try:
            return story_ranker(stories)
        except Exception as e:
            logger.error(f"Ranker failed: {e}")
    
    for story in stories:
        story['final_score'] = story.get('breakout_score', 0) / 100
    
    return sorted(stories, key=lambda x: x.get('final_score', 0), reverse=True)


# ============================================================
# LEG 2: EDITOR GOD (WITH VISUAL QUERIES)
# ============================================================

def editor_god_main(script_data, candidate):
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR GOD - Script-based visuals")
    logger.info("=" * 60)
    
    pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
    if pexels_key:
        logger.info(f"✅ PEXELS_API_KEY present (len={len(pexels_key)})")
    else:
        logger.warning("❌ PEXELS_API_KEY MISSING")
    
    editor_data = {
        "segments": [],
        "visuals": [],
        "background_music": None,
        "sound_effects": []
    }
    
    script_text = (
        script_data.get('short_script', '') or
        script_data.get('full_script', '') or
        script_data.get('viral_hook', '')
    )
    
    if not script_text:
        logger.warning("No script text")
        return editor_data
    
    logger.info(f"📝 Script: {script_text[:100]}...")
    
    # Get visual queries from AI
    visual_queries = script_data.get('visual_queries', [])
    if visual_queries:
        logger.info(f"🎨 AI visual queries: {visual_queries}")
    
    try:
        from src.media.asset_finder import find_assets_for_script
        visuals = find_assets_for_script(
            script_text,
            num_clips=16,
            visual_queries=visual_queries
        )
        editor_data['visuals'] = visuals
        logger.info(f"✅ Editor: {len(visuals)} visual assets")
    except Exception as e:
        logger.error(f"Asset finder failed: {e}")
    
    try:
        from src.media.asset_finder import find_background_music
        music = find_background_music(script_data.get('mood', 'news'))
        editor_data['background_music'] = music
    except:
        pass
    
    logger.info("LEG 2 COMPLETE")
    return editor_data


# ============================================================
# LEG 3: BOSS APPROVAL
# ============================================================

def boss_approval_main(video_path, script_data, full_story):
    logger.info("=" * 60)
    logger.info("LEG 3: BOSS APPROVAL")
    logger.info("=" * 60)
    
    result = {
        "approved": False,
        "score": 0,
        "reason": "",
        "target_countries": ENGLISH_COUNTRIES
    }
    
    try:
        quality_gate = safe_import('src.safety.policy_filter', 'run_quality_gate')
        if quality_gate:
            gate_result = quality_gate(script_data, full_story)
            if not gate_result.get('passed', False):
                result['reason'] = gate_result.get('reason', 'Quality gate failed')
                logger.warning(f"Quality gate failed: {result['reason']}")
                return result
        
        story_ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if story_ranker:
            score = story_ranker(full_story)
            result['score'] = score
            
            if score >= 65:
                result['approved'] = True
                result['reason'] = f"High score: {score:.1f}"
            elif score >= 55:
                result['approved'] = True
                result['reason'] = f"Acceptable: {score:.1f}"
            else:
                result['reason'] = f"Score too low: {score:.1f}"
        else:
            if script_data.get('short_script'):
                result['approved'] = True
                result['score'] = 75
                result['reason'] = "Fallback approval"
    
    except Exception as e:
        logger.error(f"Boss approval failed: {e}")
        result['reason'] = f"Error: {e}"
    
    logger.info(f"LEG 3: {'APPROVED' if result['approved'] else 'REJECTED'} - {result['reason']}")
    return result


# ============================================================
# LEG 4: UPLOADER GOD
# ============================================================

def uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data):
    logger.info("=" * 60)
    logger.info("LEG 4: UPLOADER GOD")
    logger.info("=" * 60)
    
    uploader = safe_import('src.youtube.uploader', 'upload_video')
    if not uploader:
        logger.error("Uploader not available")
        return None
    
    try:
        metadata_gen = safe_import('src.writing.metadata_generator', 'generate_all_metadata')
        if metadata_gen:
            metadata = metadata_gen(script_data, candidate)
        else:
            metadata = {
                "title": script_data.get('seo_youtube_title', candidate.get('title', 'Trending'))[:100],
                "description": script_data.get('description', 'Trending now.'),
                "tags": script_data.get('tags', ['trending', 'viral'])
            }
        
        video_id = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            category_id="24"
        )
        
        if video_id:
            logger.info(f"LEG 4 COMPLETE: https://youtu.be/{video_id}")
            post_upload_tasks(video_id, script_data)
        
        return video_id
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return None


def post_upload_tasks(video_id, script_data):
    comment_engine = safe_import('src.youtube.comment_engine', 'reply_to_comments')
    if comment_engine:
        try:
            comment_engine(video_id)
        except Exception as e:
            logger.error(f"Comment engine failed: {e}")
    logger.info(f"Analytics next run for {video_id}")


# ============================================================
# LEG 5: SELF EVOLUTION
# ============================================================

def self_evolution_main():
    logger.info("=" * 60)
    logger.info("LEG 5: SELF EVOLUTION")
    logger.info("=" * 60)
    
    try:
        from src.youtube.analytics_collector import collect_analytics
        collect_analytics()
    except Exception as e:
        logger.warning(f"Analytics failed: {e}")
    
    performance_learner = safe_import('src.learning.performance_learner', 'learn_from_performance')
    if performance_learner:
        try:
            insights = performance_learner()
            logger.info(f"Insights: {insights}")
            return insights
        except Exception as e:
            logger.error(f"Learning failed: {e}")
    
    return {"status": "no_data"}


# ============================================================
# SCRIPT GENERATION - QUESTION + VISUAL QUERIES
# ============================================================

def generate_script_god(story):
    """
    Generate QUESTION title + hook + 6 SPECIFIC visual queries
    """
    raw_topic = story.get('title', '')
    topic = clean_topic(raw_topic)
    
    if len(topic) < 15:
        topic = raw_topic
    
    seo_title = story.get('seo_youtube_title', '') or topic
    
    logger.info(f"   Raw: {raw_topic[:70]}")
    logger.info(f"   Clean: {topic[:70]}")
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt = f"""You are a YouTube Shorts QUESTION-HOOK expert + VISUAL DIRECTOR.

TRENDING TOPIC: {topic}

🚨 YOUR TASK:
1. Create a QUESTION title (only question + 1 hashtag)
2. Write a 40-word script that ANSWERS that question
3. **CRITICAL:** Provide 6 SPECIFIC visual search queries for stock footage

🚨 TITLE RULES (VERY STRICT):
- MUST be a QUESTION (ends with "?")
- MUST start with: Why / What / Who / How / Is / Will / Can / Are / Does
- MUST be 30-50 characters INCLUDING hashtag
- MUST have EXACTLY 1 hashtag at END
- MUST NOT contain ANY publisher name
- FORBIDDEN WORDS: BREAKING NEWS, MINNEAPOLIMEDIA, CNN, BBC, ABC, NBC, CBS, FOX, MSNBC, NYT, WSJ, AP, REUTERS

✅ GOOD TITLE EXAMPLES:
- "Why Did Everyone Miss This? #Viral"
- "What Made This Go Viral? #Trending"
- "Who Is Behind This Trend? #Trending"
- "Why Is Everyone Talking? #Viral"
- "How Did This Break Records? #Sports"
- "Why Did Fans React This Way? #Music"
- "What's The Real Story? #News"

❌ NEVER PRODUCE:
- "MINNEAPOLIMEDIA BREAKING NEWS | Biden Cancer"
- "Russia Warns NATO" (not a question)
- "Travis Kelce News" (not a question)
- "Why This Changes Everything" (no hashtag)

🚨 WHITE BAR HOOK RULES:
- MUST be a QUESTION (ends with "?")
- MUST be 4-5 WORDS
- NO EMOJI
- ALL CAPS

✅ GOOD HOOKS:
- "WHY DID THIS GO VIRAL?"
- "WHAT ARE THEY HIDING?"
- "WHO IS BEHIND THIS?"
- "WHY IS EVERYONE TALKING?"

🚨 SCRIPT RULES (40 words):
- First sentence = DIRECT ANSWER
- Then 2-3 supporting facts
- End with "what happens next"

🚨 VISUAL QUERIES (VERY IMPORTANT):

Provide 6 SPECIFIC visual search queries that match the script.
Each query must be 2-4 WORDS and DESCRIBE A REAL VISUAL.

❌ BAD QUERIES (too generic - Pexels returns nothing):
- "song went"
- "indicate recently"
- "story continues"
- "experts changes"
- "sources answer"
- "the topic"
- "trending"

✅ GOOD QUERIES (specific, visual, actionable):

For "GG EZ viral AI song" topic:
- "gaming keyboard rgb"
- "kpop dance studio"
- "smartphone streaming music"
- "young people phone"
- "viral social media"
- "AI robot face"

For "Trump tariff" topic:
- "government building"
- "shipping containers port"
- "stock market chart"
- "businessman serious"
- "dollar bills money"
- "factory workers"

For "SpaceX launch" topic:
- "rocket launch smoke"
- "space control room"
- "astronaut helmet"
- "launch pad night"
- "stars night sky"
- "mission control screen"

For "Travis Kelce Taylor Swift" topic:
- "football stadium crowd"
- "concert lights crowd"
- "celebrity red carpet"
- "young woman smiling"
- "sports tv broadcast"

RULES FOR VISUAL QUERIES:
1. Each query = 2-4 WORDS (specific)
2. Must be VISUAL (things you can film)
3. Must be RELATED to topic
4. NO abstract words (indicate, sources, story, continue, answer)
5. Use ACTION words or OBJECTS
6. Different query for each part of script

🚨 TAGS (15 max):
- Mix of short + specific

OUTPUT JSON ONLY (NO EXTRA TEXT):
{{
    "short_script": "40-word script that ANSWERS the title question",
    "seo_youtube_title": "Question? #OneHashtag",
    "description": "SEO description with subscribe CTA",
    "hashtags": ["#Trending"],
    "tags": ["tag1", "tag2", "tag3"],
    "viral_hook": "4-5 WORD QUESTION?",
    "visual_queries": ["query 1", "query 2", "query 3", "query 4", "query 5", "query 6"],
    "mood": "engaging curious",
    "confidence_score": 85
}}
"""
            
            models = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
            
            for model in models:
                try:
                    resp = client.models.generate_content(model=model, contents=prompt)
                    text = getattr(resp, 'text', '')
                    
                    if text:
                        match = re.search(r'\{.*\}', text, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            
                            # ============================================
                            # EXTRACT VISUAL QUERIES
                            # ============================================
                            visual_queries = data.get('visual_queries', [])
                            if not isinstance(visual_queries, list):
                                visual_queries = []
                            
                            # Clean queries
                            clean_vq = []
                            for q in visual_queries:
                                if isinstance(q, str):
                                    q = q.strip()
                                    if 3 <= len(q) <= 50:
                                        clean_vq.append(q)
                            
                            data['visual_queries'] = clean_vq[:6]
                            
                            if clean_vq:
                                logger.info(f"   🎨 Visual queries ({len(clean_vq)}): {clean_vq}")
                            
                            # ============================================
                            # FIX HOOK
                            # ============================================
                            hook = data.get('viral_hook', '')
                            
                            emoji_pat = re.compile(
                                "[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+",
                                flags=re.UNICODE
                            )
                            hook = emoji_pat.sub('', hook).strip()
                            
                            if hook and not hook.endswith('?'):
                                hook = hook.rstrip('.!') + '?'
                            
                            hook_words = hook.rstrip('?').split()
                            if len(hook_words) > 5:
                                hook_words = hook_words[:5]
                            hook = " ".join(hook_words).upper() + "?"
                            
                            if len(hook_words) < 4:
                                if not any(hook.upper().startswith(w) for w in ['WHY', 'WHAT', 'WHO', 'HOW', 'IS', 'WILL', 'CAN', 'ARE', 'DOES']):
                                    hook = "WHY " + hook.upper()
                                    hook_words = hook.rstrip('?').split()
                                    if len(hook_words) > 5:
                                        hook_words = hook_words[:5]
                                    hook = " ".join(hook_words).upper() + "?"
                            
                            data['viral_hook'] = hook
                            
                            # ============================================
                            # FIX TITLE
                            # ============================================
                            title = data.get('seo_youtube_title', '')
                            title = clean_topic(title)
                            title_clean = re.sub(r'#\w+', '', title).strip()
                            title_clean = re.sub(r'\b[A-Z]{4,}\b', '', title_clean)
                            
                            for bad in ['MINNEAPOLI', 'BREAKING', 'NEWS', 'MEDIA', 'LIVE', 'CNN', 'BBC', 'ABC', 'NBC']:
                                title_clean = re.sub(rf'\b{bad}\b', '', title_clean, flags=re.IGNORECASE)
                            
                            title_clean = re.sub(r'\s+', ' ', title_clean).strip()
                            title_clean = re.sub(r'^[\-:\|]+', '', title_clean).strip()
                            
                            if title_clean and not title_clean.endswith('?'):
                                title_clean = title_clean.rstrip('.!,') + '?'
                            
                            if title_clean and not any(title_clean.upper().startswith(w) for w in ['WHY', 'WHAT', 'WHO', 'HOW', 'IS', 'WILL', 'CAN', 'ARE', 'DOES']):
                                title_clean = "Why " + title_clean
                            
                            if has_publisher_name(title_clean):
                                logger.warning(f"   ⚠️ Publisher name detected - skipping")
                                continue
                            
                            hashtag = data.get('hashtags', ['#Trending'])[0] if data.get('hashtags') else '#Trending'
                            if not hashtag.startswith('#'):
                                hashtag = '#' + hashtag
                            hashtag = hashtag.split()[0]
                            
                            title_full = f"{title_clean} {hashtag}"
                            
                            if len(title_full) > 50:
                                max_title_len = 50 - len(hashtag) - 2
                                title_clean = title_clean[:max_title_len].rsplit(' ', 1)[0]
                                if not title_clean.endswith('?'):
                                    title_clean = title_clean.rstrip('.!,') + '?'
                                title_full = f"{title_clean} {hashtag}"
                            
                            if has_publisher_name(title_full):
                                logger.warning(f"   ⚠️ Final title has publisher - using fallback")
                                continue
                            
                            data['seo_youtube_title'] = title_full
                            data['hashtags'] = [hashtag]
                            
                            logger.info(f"✅ Script by {model}")
                            logger.info(f"   Title ({len(title_full)} chars): {title_full}")
                            logger.info(f"   Hook: {data['viral_hook']}")
                            return data
                except Exception as e:
                    logger.warning(f"Model {model}: {str(e)[:80]}")
                    continue
        
        except Exception as e:
            logger.warning(f"Gemini failed: {e}")
    
    logger.info("Using fallback template")
    return get_template_script(topic, seo_title)


def get_template_script(topic, seo_title):
    """Fallback - Pure question title + hook + visual queries"""
    
    words = [w for w in topic.split() if len(w) > 3 and w.lower() not in 
             ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'says', 
              'said', 'breaking', 'news', 'media', 'live', 'update', 'today']]
    
    key = " ".join(words[:2]) if len(words) >= 2 else (words[0] if words else "This")
    
    t_low = topic.lower()
    
    if any(w in t_low for w in ['war', 'military', 'strike', 'missile', 'attack']):
        hashtag = "#Breaking"
        title_q = "Who Wins This Conflict?"
        hook = "WHO WINS THIS WAR?"
        vq = ["military tanks", "soldiers marching", "explosion smoke", "war planes", "army trucks", "war zone"]
    elif any(w in t_low for w in ['tariff', 'trade', 'economy', 'money', 'cost', 'price']):
        hashtag = "#Economy"
        title_q = "Who Really Pays For This?"
        hook = "WHO PAYS FOR THIS?"
        vq = ["shipping containers", "stock market chart", "businessman serious", "dollar bills", "factory workers", "port cargo"]
    elif any(w in t_low for w in ['trump', 'biden', 'congress', 'senate', 'white house']):
        hashtag = "#Politics"
        title_q = "Why Did He Stay Silent?"
        hook = "WHY DID HE STAY SILENT?"
        vq = ["government building", "press conference", "politician podium", "capitol building", "man serious", "microphone interview"]
    elif any(w in t_low for w in ['ai', 'tech', 'robot', 'artificial', 'iphone', 'apple']):
        hashtag = "#Tech"
        title_q = "Who Controls The AI Race?"
        hook = "WHO CONTROLS THE AI?"
        vq = ["artificial intelligence", "AI robot face", "computer code", "smartphone screen", "tech office", "server room"]
    elif any(w in t_low for w in ['movie', 'film', 'netflix', 'series', 'actor', 'actress']):
        hashtag = "#Entertainment"
        title_q = "Why Is Everyone Watching?"
        hook = "WHY IS EVERYONE WATCHING?"
        vq = ["cinema screen", "movie theater", "film camera", "actor on stage", "tv remote", "streaming laptop"]
    elif any(w in t_low for w in ['song', 'music', 'album', 'concert', 'tour']):
        hashtag = "#Music"
        title_q = "Why Is This Song Everywhere?"
        hook = "WHY IS THIS EVERYWHERE?"
        vq = ["concert stage lights", "music studio", "singer microphone", "dance crowd", "headphones listening", "spotify phone"]
    elif any(w in t_low for w in ['game', 'gaming', 'playstation', 'xbox', 'nintendo']):
        hashtag = "#Gaming"
        title_q = "What Changed In Gaming?"
        hook = "WHAT CHANGED IN GAMING?"
        vq = ["gaming keyboard rgb", "console controller", "gamer playing", "computer gaming setup", "esports crowd", "video game screen"]
    elif any(w in t_low for w in ['sport', 'game', 'match', 'goal', 'team', 'player', 'nba', 'nfl', 'football']):
        hashtag = "#Sports"
        title_q = "Who Wins This Match?"
        hook = "WHO WINS THIS MATCH?"
        vq = ["football stadium", "basketball court", "soccer goal", "crowd cheering", "athlete running", "sports trophy"]
    elif any(w in t_low for w in ['viral', 'trending', 'tiktok', 'meme']):
        hashtag = "#Viral"
        title_q = "Why Did This Go Viral?"
        hook = "WHY DID THIS GO VIRAL?"
        vq = ["young people phone", "social media icons", "viral video", "smartphone close", "trending hashtag", "internet crowd"]
    elif any(w in t_low for w in ['crash', 'drop', 'fall', 'plunge']):
        hashtag = "#Market"
        title_q = "Why Are Markets Crashing?"
        hook = "WHY ARE MARKETS CRASHING?"
        vq = ["stock market chart", "trading floor", "crypto screen", "businessman worried", "red arrow down", "wall street"]
    elif any(w in t_low for w in ['space', 'launch', 'nasa', 'rocket', 'spacex']):
        hashtag = "#Space"
        title_q = "Why Do Launches Cost So Much?"
        hook = "WHY SO EXPENSIVE?"
        vq = ["rocket launch smoke", "space control room", "astronaut helmet", "launch pad night", "stars night sky", "space satellite"]
    elif any(w in t_low for w in ['climate', 'weather', 'storm', 'rain', 'flood']):
        hashtag = "#Weather"
        title_q = "What's The Real Impact?"
        hook = "WHAT IS THE IMPACT?"
        vq = ["storm clouds", "heavy rain", "flood water", "climate change glacier", "city rain night", "dark clouds sky"]
    else:
        hashtag = "#Trending"
        title_q = "Why Is This Trending?"
        hook = "WHY IS THIS TRENDING?"
        vq = ["trending viral video", "young people phone", "social media", "city skyline", "crowd of people", "news studio"]
    
    title_full = f"{title_q} {hashtag}"
    if len(title_full) > 50:
        max_title = 50 - len(hashtag) - 1
        title_q = title_q[:max_title].rsplit(' ', 1)[0]
        if not title_q.endswith('?'):
            title_q = title_q.rstrip('.!,') + '?'
        title_full = f"{title_q} {hashtag}"
    
    return {
        "short_script": f"Reports say the reason is simpler than expected. Experts point to recent developments. The story is still unfolding. Here's what we know.",
        "seo_youtube_title": title_full,
        "description": f"Answer to: {title_q} Subscribe for more trending content.",
        "hashtags": [hashtag],
        "tags": [
            "trending", "viral", "2026", "shorts",
            "entertainment", "news", "viral video",
            "trending now", "must watch", "shocking",
            "interesting", "story", "explained",
            "why trending", "what happened"
        ],
        "viral_hook": hook,
        "visual_queries": vq,
        "mood": "engaging curious",
        "confidence_score": 80
    }


# ============================================================
# VIDEO CREATION (WITH VISUAL QUERIES)
# ============================================================

def create_video_god(script_data, editor_data):
    logger.info("=" * 60)
    logger.info("VIDEO GENERATION")
    logger.info("=" * 60)
    
    try:
        from src.media.video_builder import create_video
        merged = {**script_data, **editor_data}
        merged['full_script'] = script_data.get('short_script', '')
        merged['title'] = script_data.get('seo_youtube_title', '')
        
        # Pass visual_queries
        vq = script_data.get('visual_queries', [])
        merged['visual_queries'] = vq
        if vq:
            logger.info(f"🎨 Passing visual queries: {vq}")
        
        video_path = create_video(merged, editor_data)
        logger.info(f"Video: {video_path}")
        return video_path
    except Exception as e:
        logger.error(f"Video failed: {e}")
        traceback.print_exc()
        return "output/videos/final.mp4"


# ============================================================
# THUMBNAIL
# ============================================================

def create_thumbnail(candidate, script_data):
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        os.makedirs("output/thumbnails", exist_ok=True)
        thumb_path = "output/thumbnails/thumb.jpg"
        
        img = Image.new('RGB', (1280, 720), (15, 15, 40))
        draw = ImageDraw.Draw(img)
        
        title = script_data.get('seo_youtube_title', candidate.get('title', 'Trending'))
        
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70
            )
        except:
            font = ImageFont.load_default()
        
        draw.text((640 + 4, 360 + 4), title[:40], font=font,
                  fill=(0, 0, 0), anchor="mm")
        draw.text((640, 360), title[:40], font=font,
                  fill=(255, 255, 255), anchor="mm")
        
        img.save(thumb_path, quality=95)
        logger.info(f"Thumbnail: {thumb_path}")
        return thumb_path
    
    except Exception as e:
        logger.error(f"Thumbnail failed: {e}")
        return None


# ============================================================
# 🚫 DUPLICATE CHECK
# ============================================================

def is_duplicate(title):
    if not title:
        return False
    
    try:
        from src.database import get_connection
        
        clean = re.sub(r'[^\w\s]', '', title.lower()).strip()
        words = [w for w in clean.split() if len(w) > 3][:5]
        search_key = ' '.join(words)
        
        if not search_key:
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title FROM stories 
            WHERE created_at > datetime('now', '-3 days')
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            existing = re.sub(r'[^\w\s]', '', row[0].lower()).strip()
            existing_words = [w for w in existing.split() if len(w) > 3][:5]
            existing_key = ' '.join(existing_words)
            
            if search_key and existing_key:
                search_set = set(search_key.split())
                existing_set = set(existing_key.split())
                overlap = len(search_set & existing_set)
                
                if overlap >= 3:
                    return True
        
        return False
    except Exception as e:
        logger.warning(f"Duplicate check failed: {e}")
        return False


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("GOD LEVEL BOT START - 5 LEGS")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    logger.info(GOD_INSTRUCTION)
    
    init_db()
    
    stats = get_performance_stats()
    logger.info(f"Stats: {stats}")
    
    stories = research_god_main()
    if not stories:
        logger.error("No stories - exit")
        return
    
    logger.info(f"Got {len(stories)} candidates")
    
    approved = None
    best_rejected = None
    skipped_count = 0
    
    for i, candidate in enumerate(stories[:5]):
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDIDATE {i+1}/5: {candidate.get('title', '')[:60]}")
        logger.info(f"{'='*60}")
        
        if is_duplicate(candidate.get('title', '')):
            logger.warning(f"⏭️ SKIPPED - Duplicate story")
            skipped_count += 1
            continue
        
        script_data = generate_script_god(candidate)
        
        final_title = script_data.get('seo_youtube_title', '')
        
        if has_publisher_name(final_title):
            logger.warning(f"⏭️ SKIPPED - Publisher name in title")
            continue
        
        if '?' not in final_title:
            logger.warning(f"⏭️ SKIPPED - No question mark in title")
            continue
        
        if script_data.get('confidence_score', 0) < 60:
            logger.warning(f"Low confidence: {script_data.get('confidence_score')}")
            continue
        
        logger.info("Fact checking...")
        fact_checker = safe_import('src.verification.claim_checker', 'fact_check')
        if fact_checker:
            fact_result = fact_checker(script_data.get('short_script', ''), candidate)
            if not fact_result.get('passed', False):
                logger.warning(f"Fact check failed: {fact_result.get('report', '')}")
                continue
            logger.info(f"✅ Fact check: {fact_result.get('report', '')}")
        
        editor_data = editor_god_main(script_data, candidate)
        
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        
        video_path = create_video_god(script_data, editor_data)
        
        boss_data = boss_approval_main(video_path, script_data, full_story)
        
        if not best_rejected or boss_data.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        
        if not boss_data.get('approved'):
            logger.warning(f"REJECTED: {boss_data.get('reason')}")
            continue
        
        logger.info(f"APPROVED: {boss_data.get('reason')}")
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    if skipped_count > 0:
        logger.info(f"⏭️ Skipped {skipped_count} duplicate stories")
    
    if not approved and best_rejected:
        score = best_rejected[3].get('score', 0)
        if score >= 55:
            logger.warning(f"⚠️ Using best rejected (score {score:.1f})")
            approved = best_rejected
    
    if not approved:
        logger.error("All rejected - SAFE EXIT")
        return
    
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    thumbnail_path = create_thumbnail(candidate, script_data)
    
    video_id = uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"\n{'='*60}")
        logger.info(f"UPLOADED: https://youtu.be/{video_id}")
        logger.info(f"{'='*60}")
    
    self_evolution_main()
    
    logger.info("\n" + "=" * 60)
    logger.info("GOD LEVEL BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
