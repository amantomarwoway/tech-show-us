"""
main.py - GOD LEVEL YOUTUBE SHORTS BOT v6
Statement hooks + Statement titles + Better topic filter
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
# 🧹 TOPIC CLEANING
# ============================================================

def clean_topic(title):
    """Remove publisher prefixes/suffixes"""
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
    if not text:
        return False
    
    bad_words = [
        'MINNEAPOLI', 'BREAKING NEWS', 'CNN', 'BBC', 'ABC', 'NBC', 'CBS',
        'FOX', 'MSNBC', 'NYT', 'WSJ', 'APNEWS', 'REUTERS', 'DAILY',
        'TIMES', 'POST', 'JOURNAL', 'PRESS', 'MEDIA'
    ]
    
    text_upper = text.upper()
    return any(bad in text_upper for bad in bad_words)


# ============================================================
# VIRAL TOPIC FILTER
# ============================================================

def is_viral_topic(title):
    """Strict filter - only real viral topics pass"""
    if not title:
        return False
    
    title_lower = title.lower()
    
    # HARD REJECT
    reject_keywords = [
        'weather', 'temperature', 'forecast', 'muggy', 'humid',
        'recipe', 'cooking', 'diet', 'meal prep', 'workout',
        'county', 'municipal', 'district', 'neighborhood',
        'daily thread', 'weekly thread', 'megathread', 'roundup',
        'i made', 'i did', 'my dog', 'my cat',
        'vs prediction', 'odds', 'preview', 'recap',
        'fall lovers', 'autumn movies', 'pokemon cards',
        'trending down', 'week 1 loss',
        'discussion', 'questions about', 'help me',
        'what did you', 'how do you'
    ]
    
    for kw in reject_keywords:
        if kw in title_lower:
            return False
    
    # Min 5 words
    if len(title.split()) < 5:
        return False
    
    return True


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
# LEG 1: RESEARCH GOD
# ============================================================

def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD - VIRAL TOPICS ONLY")
    logger.info("=" * 60)
    
    all_stories = []
    
    # 1. Reddit RSS
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            s = reddit_collector()
            logger.info(f"🔥 Reddit RSS: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    # 2. Google News Trending
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            s = trends_collector()
            logger.info(f"🔥 Google News Trending: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    # 3. Google News standard
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            s = google_collector()
            logger.info(f"🔥 Google News: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
    # 4. RSS feeds (only if needed)
    if len(all_stories) < 30:
        rss_collector = safe_import('src.collectors.rss_collector', 'collect_rss_news')
        if rss_collector:
            try:
                s = rss_collector()
                logger.info(f"🔥 RSS: {len(s)} stories")
                all_stories.extend(s)
            except Exception as e:
                logger.error(f"RSS failed: {e}")
    
    if not all_stories:
        all_stories = get_guaranteed_stories()
    
    # Clean titles
    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
        if not story['title'] or len(story['title']) < 10:
            story['title'] = 'Trending Topic'
    
    all_stories = [s for s in all_stories if s.get('title') and len(s['title']) > 10]
    
    # VIRAL FILTER
    before = len(all_stories)
    all_stories = [s for s in all_stories if is_viral_topic(s.get('title', ''))]
    logger.info(f"Viral filter: {before} -> {len(all_stories)}")
    
    all_stories = deduplicate_stories(all_stories)
    ranked = score_and_rank_stories(all_stories)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} trending stories")
    
    for i, story in enumerate(ranked[:5]):
        logger.info(f"  #{i+1}: {story.get('title', '')[:60]}")
        logger.info(f"       Source: {story.get('source', 'unknown')}")
    
    return ranked[:10]


def get_guaranteed_stories():
    return [
        {
            "title": "This Just Broke The Internet",
            "url": "https://trends.google.com",
            "source": "guaranteed_trends",
            "breakout_score": 6500,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title": "This Just Broke The Internet"
        },
        {
            "title": "Nobody Expected This To Happen Today",
            "url": "https://trends.google.com",
            "source": "guaranteed_trends",
            "breakout_score": 6300,
            "is_breakout": True,
            "search_volume": 88,
            "seo_youtube_title": "Nobody Expected This"
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
# LEG 2: EDITOR GOD
# ============================================================

def editor_god_main(script_data, candidate):
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR GOD")
    logger.info("=" * 60)
    
    editor_data = {"segments": [], "visuals": [], "background_music": None, "sound_effects": []}
    
    script_text = (script_data.get('short_script', '') or
                   script_data.get('full_script', '') or
                   script_data.get('viral_hook', ''))
    
    if not script_text:
        return editor_data
    
    visual_queries = script_data.get('visual_queries', [])
    if visual_queries:
        logger.info(f"🎨 AI visual queries: {len(visual_queries)}")
    
    try:
        from src.media.asset_finder import find_assets_for_script
        visuals = find_assets_for_script(script_text, num_clips=16, visual_queries=visual_queries)
        editor_data['visuals'] = visuals
        logger.info(f"✅ Editor: {len(visuals)} visual assets")
    except Exception as e:
        logger.error(f"Asset finder failed: {e}")
    
    return editor_data


# ============================================================
# LEG 3: BOSS APPROVAL
# ============================================================

def boss_approval_main(video_path, script_data, full_story):
    logger.info("=" * 60)
    logger.info("LEG 3: BOSS APPROVAL")
    logger.info("=" * 60)
    
    result = {"approved": False, "score": 0, "reason": "", "target_countries": ENGLISH_COUNTRIES}
    
    try:
        quality_gate = safe_import('src.safety.policy_filter', 'run_quality_gate')
        if quality_gate:
            gate_result = quality_gate(script_data, full_story)
            if not gate_result.get('passed', False):
                result['reason'] = gate_result.get('reason', 'Quality gate failed')
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
# SCRIPT GENERATION - STATEMENT TITLES + HOOKS + VISUALS
# ============================================================

def generate_script_god(story):
    """Generate STATEMENT-based title + hook + visual queries"""
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
            
            prompt = f"""You are a YouTube Shorts VIRAL expert + VISUAL DIRECTOR.

TRENDING TOPIC: {topic}

🚨 YOUR TASK:
1. Create a VIRAL STATEMENT title (no question)
2. Write a 40-word script that creates CURIOSITY
3. Provide 6 SPECIFIC visual search queries

🚨 TITLE RULES (STATEMENT PATTERNS - NO QUESTIONS):
- MUST be 30-50 characters
- MUST NOT be a question (no "?" in title)
- MUST have 1 hashtag at END
- MUST use viral statement patterns

PATTERN 1: "The Reason [X] Nobody Knows #Viral"
PATTERN 2: "This [X] Just Broke The Internet #Trending"
PATTERN 3: "Nobody Expected [X] To Happen #News"
PATTERN 4: "The Truth About [X] Revealed #Viral"
PATTERN 5: "[X] Is Bigger Than Anyone Thought #Viral"
PATTERN 6: "This [X] Changes Everything #Trending"

✅ GOOD TITLES (statements):
- "The Reason Nobody Saw This Coming #Viral"
- "This Just Broke The Internet #Trending"
- "Nobody Expected This To Happen #News"
- "The Truth About This Trend #Viral"
- "This Is Bigger Than Anyone Thought #Viral"

❌ BAD TITLES (questions - LOW CTR):
- "Why Did This Happen? #Viral"
- "What Is This Trend? #Trending"
- "Is This Real? #News"
- "Who Is Behind This? #News"

FORBIDDEN WORDS: BREAKING NEWS, MINNEAPOLIMEDIA, CNN, BBC, ABC, NBC, CBS, FOX, MSNBC, NYT, WSJ, AP, REUTERS

🚨 WHITE BAR HOOK (STATEMENTS - NO QUESTIONS):
- MUST be 4-5 WORDS
- NO question mark
- ALL CAPS
- Match the title theme

✅ GOOD HOOKS:
- "NOBODY SAW THIS COMING"
- "THIS CHANGES EVERYTHING"
- "THE TRUTH REVEALED"
- "EVERYONE IS WRONG"
- "THIS BROKE THE INTERNET"
- "MILLIONS ARE WATCHING"
- "THE REASON IS SHOCKING"

❌ BAD HOOKS (questions):
- "WHY DID THIS HAPPEN?"
- "WHAT IS THIS TREND?"
- "IS THIS REAL?"

🚨 SCRIPT RULES (40 words):
- First sentence = HOOK (statement, not question)
- Then 2-3 surprising facts
- End with "what happens next" or mystery
- Use "reports say" for unverified

🚨 VISUAL QUERIES (6 queries, 2-4 words each):
- MUST be SPECIFIC and VISUAL
- NO abstract words (sources, indicate, story, continue)
- Use ACTION words or OBJECTS
- Example for "JLo lookalike mugshot": "police mugshot camera", "glamorous woman red carpet", "smartphone screen scrolling", "paparazzi camera flash", "photo comparison side by side", "woman serious portrait"

OUTPUT JSON ONLY:
{{
    "short_script": "40-word script",
    "seo_youtube_title": "Statement title? #OneHashtag",
    "description": "SEO description with subscribe CTA",
    "hashtags": ["#Viral"],
    "tags": ["tag1", "tag2"],
    "viral_hook": "4-5 WORD STATEMENT",
    "visual_queries": ["q1", "q2", "q3", "q4", "q5", "q6"],
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
                            
                            # Extract visual queries
                            vq = data.get('visual_queries', [])
                            if not isinstance(vq, list):
                                vq = []
                            clean_vq = [q.strip() for q in vq if isinstance(q, str) and 3 <= len(q.strip()) <= 50]
                            data['visual_queries'] = clean_vq[:6]
                            
                            if clean_vq:
                                logger.info(f"   🎨 Visual queries ({len(clean_vq)}): {clean_vq}")
                            
                            # Fix hook (statement)
                            hook = data.get('viral_hook', '')
                            emoji_pat = re.compile("[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
                            hook = emoji_pat.sub('', hook).strip()
                            
                            # Remove question mark if present
                            hook = hook.rstrip('?').strip()
                            
                            hook_words = hook.split()
                            if len(hook_words) > 5:
                                hook_words = hook_words[:5]
                            elif len(hook_words) < 4:
                                if not any(w in hook.upper() for w in ['THIS', 'NOBODY', 'THE', 'EVERY', 'MILLIONS']):
                                    hook = "THIS CHANGES " + hook.upper()
                                    hook_words = hook.split()[:5]
                            hook = " ".join(hook_words).upper()
                            data['viral_hook'] = hook
                            
                            # Fix title (statement)
                            title = data.get('seo_youtube_title', '')
                            title = clean_topic(title)
                            title_clean = re.sub(r'#\w+', '', title).strip()
                            title_clean = re.sub(r'\b[A-Z]{4,}\b', '', title_clean)
                            
                            for bad in ['MINNEAPOLI', 'BREAKING', 'NEWS', 'MEDIA', 'LIVE']:
                                title_clean = re.sub(rf'\b{bad}\b', '', title_clean, flags=re.IGNORECASE)
                            
                            title_clean = re.sub(r'\s+', ' ', title_clean).strip()
                            title_clean = re.sub(r'^[\-:\|?]+', '', title_clean).strip()
                            
                            # Remove question marks from title
                            title_clean = title_clean.replace('?', '').strip()
                            
                            if has_publisher_name(title_clean):
                                continue
                            
                            hashtag = data.get('hashtags', ['#Viral'])[0] if data.get('hashtags') else '#Viral'
                            if not hashtag.startswith('#'):
                                hashtag = '#' + hashtag
                            hashtag = hashtag.split()[0]
                            
                            title_full = f"{title_clean} {hashtag}"
                            
                            if len(title_full) > 50:
                                max_title_len = 50 - len(hashtag) - 1
                                title_clean = title_clean[:max_title_len].rsplit(' ', 1)[0]
                                title_full = f"{title_clean} {hashtag}"
                            
                            if has_publisher_name(title_full):
                                continue
                            
                            data['seo_youtube_title'] = title_full
                            data['hashtags'] = [hashtag]
                            
                            logger.info(f"✅ Script by {model}")
                            logger.info(f"   Title ({len(title_full)}): {title_full}")
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
    """Fallback - Statement based"""
    words = [w for w in topic.split() if len(w) > 3 and w.lower() not in 
             ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'says', 
              'said', 'breaking', 'news', 'media', 'live', 'update']]
    
    key = " ".join(words[:3]) if len(words) >= 3 else (words[0] if words else "This")
    
    title_templates = [
        f"The Reason {key[:25]} Nobody Knows",
        f"This {key[:25]} Just Went Viral",
        f"Nobody Expected {key[:20]} Today",
        f"The Truth About {key[:20]} Revealed",
    ]
    
    title_q = random.choice(title_templates)
    
    t_low = topic.lower()
    
    if any(w in t_low for w in ['mugshot', 'arrested', 'police']):
        hashtag = "#Viral"
        hook = "NOBODY SAW THIS COMING"
        vq = ["police mugshot", "woman portrait", "smartphone scrolling", "social media icons", "camera flash", "photo comparison"]
    elif any(w in t_low for w in ['celebrity', 'actress', 'singer', 'star']):
        hashtag = "#Entertainment"
        hook = "THIS CHANGED EVERYTHING"
        vq = ["celebrity red carpet", "paparazzi camera", "glamorous woman", "fashion studio", "camera flash", "movie premiere"]
    elif any(w in t_low for w in ['sport', 'match', 'goal', 'team']):
        hashtag = "#Sports"
        hook = "NOBODY EXPECTED THIS"
        vq = ["stadium crowd", "athlete action", "sports trophy", "football field", "basketball court", "crowd cheering"]
    elif any(w in t_low for w in ['music', 'song', 'album']):
        hashtag = "#Music"
        hook = "THIS BROKE THE INTERNET"
        vq = ["concert stage", "singer microphone", "music studio", "crowd dancing", "headphones", "vinyl records"]
    else:
        hashtag = "#Viral"
        hook = "NOBODY SAW THIS COMING"
        vq = ["viral video screen", "young people phone", "social media", "city crowd", "smartphone scrolling", "trending icons"]
    
    title_full = f"{title_q} {hashtag}"
    if len(title_full) > 50:
        max_title = 50 - len(hashtag) - 1
        title_q = title_q[:max_title].rsplit(' ', 1)[0]
        title_full = f"{title_q} {hashtag}"
    
    return {
        "short_script": f"This {key[:30]} went viral for one surprising reason. Sources confirm the details nobody expected. Reports suggest this trend will continue. Here's what happens next.",
        "seo_youtube_title": title_full,
        "description": f"The story behind this trend. Subscribe for more viral content.",
        "hashtags": [hashtag],
        "tags": ["trending", "viral", "2026", "shorts", "viral video", "must watch"],
        "viral_hook": hook,
        "visual_queries": vq,
        "mood": "engaging curious",
        "confidence_score": 80
    }


# ============================================================
# VIDEO CREATION
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
        merged['visual_queries'] = script_data.get('visual_queries', [])
        
        vq = merged.get('visual_queries', [])
        if vq:
            logger.info(f"🎨 Passing visual queries: {len(vq)}")
        
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
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except:
            font = ImageFont.load_default()
        
        draw.text((640 + 4, 360 + 4), title[:40], font=font, fill=(0, 0, 0), anchor="mm")
        draw.text((640, 360), title[:40], font=font, fill=(255, 255, 255), anchor="mm")
        
        img.save(thumb_path, quality=95)
        logger.info(f"Thumbnail: {thumb_path}")
        return thumb_path
    except Exception as e:
        logger.error(f"Thumbnail failed: {e}")
        return None


# ============================================================
# DUPLICATE CHECK
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
        cursor.execute('''SELECT title FROM stories WHERE created_at > datetime('now', '-3 days')''')
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            existing = re.sub(r'[^\w\s]', '', row[0].lower()).strip()
            existing_words = [w for w in existing.split() if len(w) > 3][:5]
            existing_key = ' '.join(existing_words)
            
            if search_key and existing_key:
                overlap = len(set(search_key.split()) & set(existing_key.split()))
                if overlap >= 3:
                    return True
        return False
    except:
        return False


# ============================================================
# MAIN
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
            logger.warning(f"⏭️ SKIPPED - Duplicate")
            skipped_count += 1
            continue
        
        script_data = generate_script_god(candidate)
        
        final_title = script_data.get('seo_youtube_title', '')
        
        if has_publisher_name(final_title):
            logger.warning(f"⏭️ SKIPPED - Publisher")
            continue
        
        if script_data.get('confidence_score', 0) < 60:
            continue
        
        logger.info("Fact checking...")
        fact_checker = safe_import('src.verification.claim_checker', 'fact_check')
        if fact_checker:
            fact_result = fact_checker(script_data.get('short_script', ''), candidate)
            if not fact_result.get('passed', False):
                logger.warning(f"Fact check failed")
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
            continue
        
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    if skipped_count > 0:
        logger.info(f"⏭️ Skipped {skipped_count} duplicates")
    
    if not approved and best_rejected:
        if best_rejected[3].get('score', 0) >= 55:
            approved = best_rejected
    
    if not approved:
        logger.error("All rejected - SAFE EXIT")
        return
    
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    thumbnail_path = create_thumbnail(candidate, script_data)
    video_id = uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"\nUPLOADED: https://youtu.be/{video_id}")
    
    self_evolution_main()
    
    logger.info("\n" + "=" * 60)
    logger.info("GOD LEVEL BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
