"""
main.py - GOD LEVEL YOUTUBE SHORTS BOT v3
Question-hook based system
- Title: Question + 1 hashtag
- White bar: 4-5 word question (no emoji)
- Script: Answers the question
- Clean topics (no publisher prefix)
- Skip duplicates
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
# 🧹 TOPIC CLEANING (Remove publisher prefix)
# ============================================================

def clean_topic(title):
    """Remove publisher prefix like 'MINNEAPOLIMEDIA BREAKING NEWS |' """
    if not title:
        return ""
    
    cleaned = title.strip()
    
    # Remove ALL-CAPS prefix with pipe: "MINNEAPOLIMEDIA BREAKING NEWS |"
    cleaned = re.sub(r'^[A-Z][A-Z\s]+\|\s*', '', cleaned)
    
    # Remove "Something BREAKING NEWS |"
    cleaned = re.sub(r'^[A-Za-z\s]+BREAKING NEWS\s*\|\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "BREAKING NEWS |"
    cleaned = re.sub(r'^BREAKING NEWS\s*\|\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "Something NEWS |"
    cleaned = re.sub(r'^[A-Za-z\s]+NEWS\s*\|\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "Something MEDIA |"
    cleaned = re.sub(r'^[A-Za-z\s]+MEDIA\s*\|\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "Something LIVE |"
    cleaned = re.sub(r'^[A-Za-z\s]+LIVE\s*\|\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove " - Source Name" at end (2-25 chars)
    cleaned = re.sub(r'\s+-\s+[A-Za-z\s]{2,25}$', '', cleaned)
    
    # Remove leading pipe or dash
    cleaned = re.sub(r'^[\|\-\s]+', '', cleaned)
    
    return cleaned.strip()


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
    logger.info("LEG 1: RESEARCH GOD")
    logger.info("=" * 60)
    
    all_stories = []
    
    rss_collector = safe_import('src.collectors.rss_collector', 'collect_rss_news')
    if rss_collector:
        try:
            s = rss_collector()
            logger.info(f"RSS: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"RSS failed: {e}")
    
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            s = google_collector()
            logger.info(f"Google News: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            s = trends_collector()
            logger.info(f"Trends: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            s = reddit_collector()
            logger.info(f"Reddit: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    if not all_stories:
        logger.warning("All collectors failed - fallback")
        all_stories = get_guaranteed_stories()
    
    # Clean titles
    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
    
    all_stories = deduplicate_stories(all_stories)
    ranked = score_and_rank_stories(all_stories)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} stories")
    return ranked[:10]


def get_guaranteed_stories():
    return [
        {
            "title": "White House Shocker Shatters Families Tonight",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 6000,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title": "What Did White House Just Do?"
        },
        {
            "title": "Supreme Court Brutal Order Panic Millions",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5800,
            "is_breakout": True,
            "search_volume": 88,
            "seo_youtube_title": "Who Will Supreme Court Target?"
        },
        {
            "title": "Brutal Tariffs Panic Millions of Families",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5700,
            "is_breakout": True,
            "search_volume": 85,
            "seo_youtube_title": "Who Pays The New Tariffs?"
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
    
    try:
        from src.media.asset_finder import find_assets_for_script
        visuals = find_assets_for_script(script_text, num_clips=16)
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
            
            if score >= 72:
                result['approved'] = True
                result['reason'] = f"High score: {score:.1f}"
            elif score >= 65:
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
                "title": script_data.get('seo_youtube_title', candidate.get('title', 'Breaking News'))[:100],
                "description": script_data.get('description', 'Breaking news update.'),
                "tags": script_data.get('tags', ['breaking news', 'world news'])
            }
        
        video_id = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            category_id="25"
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
# SCRIPT GENERATION - QUESTION-BASED
# ============================================================

def generate_script_god(story):
    """
    Generate QUESTION-based script:
    - Title: Question + 1 hashtag (30-50 chars)
    - White bar: 4-5 word question (NO emoji)
    - Script: Answers the question
    """
    # CLEAN TOPIC
    raw_topic = story.get('title', '')
    topic = clean_topic(raw_topic)
    
    if len(topic) < 10:
        topic = raw_topic
    
    seo_title = story.get('seo_youtube_title', '') or topic
    
    logger.info(f"   Raw: {raw_topic[:70]}")
    logger.info(f"   Clean: {topic[:70]}")
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt = f"""You are a YouTube Shorts QUESTION-HOOK expert. Create a question-based viral short.

TOPIC: {topic}

🚨 TITLE RULES (VERY STRICT):
- MUST be a QUESTION (ends with "?")
- MUST be 30-50 characters (including hashtag)
- MUST have EXACTLY 1 hashtag at the END
- NO more than 1 hashtag
- Question should create curiosity
- Example: "Why Did He Stay Silent? #Breaking"
- Example: "Who Really Pays Tariffs? #Economy"
- Example: "What's Hidden In The Bill? #Politics"

✅ GOOD TITLES (Question + 1 hashtag):
- "Why Did Biden Stay Silent? #Breaking"
- "Who Really Pays The Tariffs? #Economy"
- "What's In The Secret Bill? #Politics"
- "Is This The End For NATO? #WorldNews"
- "Why Are Markets Crashing? #Market"
- "Who Controls The AI Race? #Tech"

❌ BAD TITLES:
- "Russia Warns NATO" (not a question)
- "Why This Changes Everything" (no hashtag)
- "Hunter Biden News #Breaking #Politics" (2 hashtags)
- "Why Did This Happen? #Breaking #News #Viral" (3 hashtags)

🚨 WHITE BAR HOOK RULES (VERY STRICT):
- MUST be a QUESTION (ends with "?")
- MUST be exactly 4-5 WORDS
- NO EMOJI
- ALL CAPS
- Question related to topic
- Example: "WHY DID HE STAY SILENT?" (5 words)
- Example: "WHO REALLY PAYS TARIFFS?" (4 words)
- Example: "WHAT IS HE HIDING?" (4 words)

✅ GOOD HOOKS (4-5 words, question):
- "WHY DID HE STAY SILENT?"  (5)
- "WHO REALLY PAYS TARIFFS?"  (4)
- "WHAT IS HE HIDING?"  (4)
- "IS THIS THE REAL END?"  (5)
- "WHO WINS THIS WAR?"  (4)
- "WHY NOW, WHY HIM?"  (5)

❌ BAD HOOKS:
- "THEY KNEW ALL ALONG"  (not a question)
- "THIS CHANGES EVERYTHING?"  (not 4-5 words)
- "WHY DID HE STAY SILENT? 🚨"  (has emoji)

🚨 SCRIPT RULES (40 words):
- MUST ANSWER the question asked in white bar
- Start with strong hook (answer first line)
- Provide clear answer with context
- "reports say" for unverified claims
- End with what happens next

🚨 TAGS (15 max):
- Mix of short + specific
- Include: breaking news, world news, viral

OUTPUT JSON ONLY (NO EXTRA TEXT):
{{
    "short_script": "40-word script that ANSWERS the question",
    "seo_youtube_title": "Question? #OneHashtag",
    "description": "SEO description with subscribe CTA",
    "hashtags": ["#Breaking"],
    "tags": ["tag1", "tag2", "tag3"],
    "viral_hook": "4-5 WORD QUESTION?",
    "mood": "tense dramatic",
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
                            # HARD LIMITS & FIXES
                            # ============================================
                            
                            # --- Fix viral_hook ---
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
                                if 'WHAT' not in hook.upper() and 'WHO' not in hook.upper() and 'WHY' not in hook.upper() and 'HOW' not in hook.upper():
                                    hook = "WHY " + hook.upper()
                                    hook_words = hook.rstrip('?').split()
                                    if len(hook_words) > 5:
                                        hook_words = hook_words[:5]
                                    hook = " ".join(hook_words).upper() + "?"
                            
                            data['viral_hook'] = hook
                            
                            # --- Fix seo_youtube_title ---
                            title = data.get('seo_youtube_title', '')
                            title_clean = re.sub(r'#\w+', '', title).strip()
                            
                            if title_clean and not title_clean.endswith('?'):
                                title_clean = title_clean.rstrip('.!,') + '?'
                            
                            hashtag = data.get('hashtags', ['#Breaking'])[0] if data.get('hashtags') else '#Breaking'
                            if not hashtag.startswith('#'):
                                hashtag = '#' + hashtag
                            hashtag = hashtag.split()[0]
                            
                            title_full = f"{title_clean} {hashtag}"
                            
                            if len(title_full) > 50:
                                max_title_len = 50 - len(hashtag) - 1
                                title_clean = title_clean[:max_title_len].rsplit(' ', 1)[0]
                                if not title_clean.endswith('?'):
                                    title_clean = title_clean.rstrip('.!,') + '?'
                                title_full = f"{title_clean} {hashtag}"
                            
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
    """Fallback - Question-based title + hook"""
    
    words = [w for w in topic.split() if len(w) > 3 and w.lower() not in 
             ['the', 'and', 'for', 'with', 'from', 'this', 'that', 'says', 'said']]
    
    key = " ".join(words[:2]) if len(words) >= 2 else (words[0] if words else "News")
    
    title_templates = [
        f"Why Did {key[:20]} Happen?",
        f"Who Really Wins From {key[:15]}?",
        f"What's The Truth About {key[:15]}?",
        f"Is {key[:20]} The Real Problem?",
        f"How Did This Change {key[:15]}?",
    ]
    
    title_q = random.choice(title_templates)
    
    t_low = topic.lower()
    if any(w in t_low for w in ['war', 'military', 'strike', 'missile']):
        hashtag = "#Breaking"
        hook = "WHO WINS THIS WAR?"
    elif any(w in t_low for w in ['tariff', 'trade', 'economy', 'money']):
        hashtag = "#Economy"
        hook = "WHO PAYS FOR THIS?"
    elif any(w in t_low for w in ['trump', 'biden', 'congress', 'white house']):
        hashtag = "#Politics"
        hook = "WHY DID HE STAY SILENT?"
    elif any(w in t_low for w in ['ai', 'tech', 'robot']):
        hashtag = "#Tech"
        hook = "WHO CONTROLS THE AI?"
    elif any(w in t_low for w in ['secret', 'leaked', 'classified']):
        hashtag = "#Breaking"
        hook = "WHAT ARE THEY HIDING?"
    elif any(w in t_low for w in ['crash', 'drop', 'fall']):
        hashtag = "#Market"
        hook = "WHY ARE MARKETS CRASHING?"
    elif any(w in t_low for w in ['court', 'law', 'justice']):
        hashtag = "#Justice"
        hook = "WHO WINS IN COURT?"
    elif any(w in t_low for w in ['warning', 'danger']):
        hashtag = "#Breaking"
        hook = "WHY WAS THIS IGNORED?"
    else:
        hashtag = "#Breaking"
        hook = "WHY NOW, WHY HIM?"
    
    title_full = f"{title_q[:45]} {hashtag}"
    if len(title_full) > 50:
        max_title = 50 - len(hashtag) - 1
        title_q = title_q[:max_title].rsplit(' ', 1)[0]
        if not title_q.endswith('?'):
            title_q = title_q.rstrip('.!,') + '?'
        title_full = f"{title_q} {hashtag}"
    
    return {
        "short_script": f"Reports say the answer is more complicated than it looks. Officials confirm the basic facts. Legal experts say this could backfire. The situation is still developing. Here's what we know so far.",
        "seo_youtube_title": title_full,
        "description": f"{topic} - answer to your question. Subscribe for more.",
        "hashtags": [hashtag],
        "tags": [
            "breaking news", "world news", "politics", "usa",
            "viral", "shocking", "2026", "government",
            "international", "headlines", "leaked", "revealed",
            "exposed", "crisis", "developing"
        ],
        "viral_hook": hook,
        "mood": "tense dramatic news",
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
        
        title = script_data.get('seo_youtube_title', candidate.get('title', 'Breaking'))
        
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
    """Check if similar story already processed in last 3 days"""
    if not title:
        return False
    
    try:
        from src.database import get_connection
        
        # Clean title for comparison
        clean = re.sub(r'[^\w\s]', '', title.lower()).strip()
        # Get first 4 significant words
        words = [w for w in clean.split() if len(w) > 3][:4]
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
            existing_words = [w for w in existing.split() if len(w) > 3][:4]
            existing_key = ' '.join(existing_words)
            
            if search_key and existing_key:
                # Check overlap
                search_set = set(search_key.split())
                existing_set = set(existing_key.split())
                overlap = len(search_set & existing_set)
                
                if overlap >= 3:  # 3+ word overlap = duplicate
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
        
        # 🚫 SKIP DUPLICATES
        if is_duplicate(candidate.get('title', '')):
            logger.warning(f"⏭️ SKIPPED - Duplicate story (processed in last 3 days)")
            skipped_count += 1
            continue
        
        script_data = generate_script_god(candidate)
        
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
        if score >= 65:
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
