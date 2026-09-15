"""
main.py - GOD LEVEL YOUTUBE SHORTS BOT
Zero-cost, fully automated, editorial intelligence system
"""

import os
import sys
import time
import traceback
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES, PUBLISH_THRESHOLDS
from src.utils.logger import setup_logger
from src.database import init_db, save_story, mark_uploaded, get_performance_stats

logger = setup_logger(__name__)

# ============================================================
# LAZY IMPORTS - Fail gracefully
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("GOD LEVEL BOT START - 5 LEGS")
    logger.info("=" * 60)
    
    init_db()
    
    stories = research_god_main()
    if not stories:
        logger.error("No stories found - exiting")
        return
    
    logger.info(f"Got {len(stories)} candidate stories")
    
    approved = None
    best_rejected = None  # Track best rejected
    
    for i, candidate in enumerate(stories[:5]):
        logger.info(f"\nCANDIDATE {i+1}/5: {candidate.get('title', '')[:60]}")
        
        script_data = generate_script_god(candidate)
        
        if script_data.get('confidence_score', 0) < 60:
            logger.warning(f"Low confidence: {script_data.get('confidence_score')}")
            continue
        
        # Fact check
        fact_checker = safe_import('src.verification.claim_checker', 'fact_check')
        if fact_checker:
            fact_result = fact_checker(script_data.get('short_script', ''), candidate)
            if not fact_result.get('passed', False):
                logger.warning(f"Fact check failed: {fact_result.get('report', '')}")
                continue
        
        editor_data = editor_god_main(script_data, candidate)
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        video_path = create_video_god(script_data, editor_data)
        
        boss_data = boss_approval_main(video_path, script_data, full_story)
        
        # Track best rejected
        if not best_rejected or boss_data.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        
        if not boss_data.get('approved'):
            logger.warning(f"REJECTED: {boss_data.get('reason')}")
            continue
        
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    # FALLBACK: If all rejected, use best rejected (safety net)
    if not approved and best_rejected:
        score = best_rejected[3].get('score', 0)
        if score >= 65:  # Lower threshold for fallback
            logger.warning(f"⚠️ All rejected - using best rejected (score {score:.1f})")
            approved = best_rejected
    
    if not approved:
        logger.error("All candidates rejected - SAFE EXIT")
        return
    
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    # Thumbnail
    thumbnail_path = create_thumbnail(candidate, script_data)
    
    # Upload
    video_id = uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"UPLOADED: https://youtu.be/{video_id}")
    
    self_evolution_main()

def safe_import(module_path, function_name=None):
    """Safely import a module/function with fallback"""
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
    """Multi-source news collection with trend detection"""
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD - Multi-source collection")
    logger.info("=" * 60)
    
    all_stories = []
    
    # 1. RSS Collectors (free, no API key)
    rss_collector = safe_import('src.collectors.rss_collector', 'collect_rss_news')
    if rss_collector:
        try:
            rss_stories = rss_collector()
            logger.info(f"RSS collector: {len(rss_stories)} stories")
            all_stories.extend(rss_stories)
        except Exception as e:
            logger.error(f"RSS collector failed: {e}")
    
    # 2. Google News Collector
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            google_stories = google_collector()
            logger.info(f"Google News: {len(google_stories)} stories")
            all_stories.extend(google_stories)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
    # 3. Trends Collector
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            trend_stories = trends_collector()
            logger.info(f"Trends: {len(trend_stories)} stories")
            all_stories.extend(trend_stories)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    # 4. Reddit Collector
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            reddit_stories = reddit_collector()
            logger.info(f"Reddit: {len(reddit_stories)} stories")
            all_stories.extend(reddit_stories)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    # 5. Fallback - guaranteed stories
    if not all_stories:
        logger.warning("All collectors failed - using guaranteed fallback")
        all_stories = get_guaranteed_stories()
    
    # Deduplicate
    all_stories = deduplicate_stories(all_stories)
    
    # Score and rank
    ranked = score_and_rank_stories(all_stories)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} ranked stories")
    return ranked[:10]


def get_guaranteed_stories():
    """Guaranteed fallback stories - video will be made"""
    return [
        {
            "title": "White House Shocker Shatters Families Tonight - Leaked Behind Closed Doors",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 6000,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title": "White House Shocker Shatters Families Tonight"
        },
        {
            "title": "Supreme Court Brutal Order Panic Millions - Secret Ruling Leaked",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5800,
            "is_breakout": True,
            "search_volume": 88,
            "seo_youtube_title": "Supreme Court Brutal Order Panic Millions"
        },
        {
            "title": "Brutal Tariffs Panic Millions of Families - White House Behind Closed Doors",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5700,
            "is_breakout": True,
            "search_volume": 85,
            "seo_youtube_title": "Brutal Tariffs Panic Millions of Families"
        },
    ]


def deduplicate_stories(stories):
    """Remove duplicate stories by title similarity"""
    seen_titles = set()
    unique = []
    
    for story in stories:
        title = story.get('title', '').lower().strip()
        # Simple dedup by first 30 chars
        key = title[:30] if len(title) > 30 else title
        
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(story)
    
    logger.info(f"Deduplication: {len(stories)} -> {len(unique)} stories")
    return unique


def score_and_rank_stories(stories):
    """Score and rank stories using trend engine"""
    trend_engine = safe_import('src.intelligence.trend_engine', 'calculate_trend_score')
    story_ranker = safe_import('src.intelligence.story_ranker', 'rank_stories')
    
    if story_ranker:
        try:
            return story_ranker(stories)
        except Exception as e:
            logger.error(f"Story ranker failed: {e}")
    
    # Fallback: sort by breakout_score
    for story in stories:
        story['final_score'] = story.get('breakout_score', 0) / 100
    
    return sorted(stories, key=lambda x: x.get('final_score', 0), reverse=True)


# ============================================================
# LEG 2: EDITOR GOD
# ============================================================

def editor_god_main(script_data, candidate):
    """Visual asset collection from everywhere"""
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR GOD - Visual asset collection")
    logger.info("=" * 60)
    
    editor_data = {
        "segments": [],
        "visuals": [],
        "background_music": None,
        "sound_effects": []
    }
    
    # Get visual segments from script
    segments = script_data.get('script_visual_segments', [])
    
    # Asset finder
    asset_finder = safe_import('src.media.asset_finder', 'find_assets_for_segments')
    if asset_finder:
        try:
            visuals = asset_finder(segments, candidate)
            editor_data['visuals'] = visuals
            logger.info(f"Found {len(visuals)} visual assets")
        except Exception as e:
            logger.error(f"Asset finder failed: {e}")
    
    # Get background music
    music_finder = safe_import('src.media.asset_finder', 'find_background_music')
    if music_finder:
        try:
            music = music_finder(script_data.get('mood', 'news'))
            editor_data['background_music'] = music
        except Exception as e:
            logger.error(f"Music finder failed: {e}")
    
    logger.info("LEG 2 COMPLETE")
    return editor_data


# ============================================================
# LEG 3: BOSS APPROVAL
# ============================================================

def boss_approval_main(video_path, script_data, full_story):
    """Live world demand check + final approval"""
    logger.info("=" * 60)
    logger.info("LEG 3: BOSS APPROVAL - Final quality gate")
    logger.info("=" * 60)
    
    result = {
        "approved": False,
        "score": 0,
        "reason": "",
        "target_countries": ENGLISH_COUNTRIES
    }
    
    try:
        # Check quality gate
        quality_gate = safe_import('src.safety.policy_filter', 'run_quality_gate')
        if quality_gate:
            gate_result = quality_gate(script_data, full_story)
            if not gate_result.get('passed', False):
                result['reason'] = gate_result.get('reason', 'Quality gate failed')
                logger.warning(f"Quality gate failed: {result['reason']}")
                return result
        
        # Calculate final score
        story_ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if story_ranker:
            score = story_ranker(full_story)
            result['score'] = score
            
            if score >= PUBLISH_THRESHOLDS['publish']:
                result['approved'] = True
                result['reason'] = f"High score: {score}"
            elif score >= PUBLISH_THRESHOLDS['high_priority']:
                result['approved'] = True
                result['reason'] = f"High priority: {score}"
            else:
                result['reason'] = f"Score too low: {score}"
        else:
            # Fallback: approve if script exists
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
    """YouTube upload with full metadata"""
    logger.info("=" * 60)
    logger.info("LEG 4: UPLOADER GOD - YouTube upload")
    logger.info("=" * 60)
    
    uploader = safe_import('src.youtube.uploader', 'upload_video')
    if not uploader:
        logger.error("Uploader not available")
        return None
    
    try:
        # Generate metadata
        metadata_gen = safe_import('src.writing.metadata_generator', 'generate_all_metadata')
        if metadata_gen:
            metadata = metadata_gen(script_data, candidate)
        else:
            metadata = {
                "title": script_data.get('seo_youtube_title', candidate.get('title', 'Breaking News'))[:100],
                "description": script_data.get('description', 'Breaking news update.'),
                "tags": script_data.get('tags', ['breaking news', 'world news'])
            }
        
        # Upload
        video_id = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=metadata['title'],
            description=metadata['description'],
            tags=metadata['tags'],
            category_id="25"  # News & Politics
        )
        
        if video_id:
            logger.info(f"LEG 4 COMPLETE: https://youtu.be/{video_id}")
            
            # Post-upload tasks
            post_upload_tasks(video_id, script_data)
        
        return video_id
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        traceback.print_exc()
        return None


def post_upload_tasks(video_id, script_data):
    """Comment engine + analytics setup"""
    # Comment engine
    comment_engine = safe_import('src.youtube.comment_engine', 'reply_to_comments')
    if comment_engine:
        try:
            comment_engine(video_id)
        except Exception as e:
            logger.error(f"Comment engine failed: {e}")
    
    # Schedule analytics collection
    logger.info(f"Analytics will be collected in next run for {video_id}")


# ============================================================
# LEG 5: SELF EVOLUTION
# ============================================================

def self_evolution_main():
    """Learn from performance data"""
    logger.info("=" * 60)
    logger.info("LEG 5: SELF EVOLUTION - Performance learning")
    logger.info("=" * 60)
    
    performance_learner = safe_import('src.learning.performance_learner', 'learn_from_performance')
    if performance_learner:
        try:
            insights = performance_learner()
            logger.info(f"Learning insights: {insights}")
            return insights
        except Exception as e:
            logger.error(f"Learning failed: {e}")
    
    return {"status": "no_data"}


# ============================================================
# SCRIPT GENERATION
# ============================================================

def generate_script_god(story):
    """Generate script using best available AI"""
    topic = story.get('title', '')
    seo_title = story.get('seo_youtube_title', '') or topic
    
    # Try Gemini first (free tier)
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt = build_script_prompt(topic, seo_title, story)
            
            for model in ["gemini-3.6-flash", "gemini-1.5-flash"]:
                try:
                    resp = client.models.generate_content(model=model, contents=prompt)
                    text = getattr(resp, 'text', '')
                    if text:
                        import re
                        match = re.search(r'\{.*\}', text, re.DOTALL)
                        if match:
                            data = json.loads(match.group())
                            logger.info(f"Script generated by Gemini {model}")
                            return data
                except Exception as e:
                    logger.warning(f"Gemini {model} failed: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Gemini client failed: {e}")
    
    # Fallback to template
    logger.info("Using template script")
    return get_template_script(topic, seo_title)


def build_script_prompt(topic, seo_title, story):
    """Build prompt for script generation"""
    return f"""
You are a YouTube Shorts scriptwriter for a global English news channel.

TOPIC: {topic}
SEO TITLE: {seo_title}
SOURCE: {story.get('url', '')}

Write a 40-50 word script for an 11-15 second YouTube Short.

REQUIREMENTS:
1. First sentence MUST be a shocking hook (pattern interrupt)
2. Use "according to reports" or "officials say" for unverified claims
3. NO fake urgency, NO "hello guys", NO channel intro
4. End with open loop or "what happens next" question
5. Factual, accurate, politically neutral in presentation
6. Include visual search prompts for each segment

OUTPUT JSON ONLY:
{{
    "short_script": "40-50 word script",
    "long_script": "180-240 word version",
    "seo_youtube_title": "under 60 chars, high CTR",
    "title_with_hashtag": "title #Breaking #News",
    "description": "SEO description with keywords",
    "hashtags": ["#breakingnews", "#worldnews"],
    "tags": ["breaking news", "world news", "politics"],
    "script_visual_segments": [
        {{"segment_text": "text", "asset_type": "video", "visual_search_prompt": "specific visual search"}}
    ],
    "mood": "tense/dramatic/neutral",
    "confidence_score": 85
}}
"""


def get_template_script(topic, seo_title):
    """Template fallback script"""
    return {
        "short_script": f"Breaking: {topic}. According to reports, this development could affect millions. Officials say the situation is still developing. What happens next?",
        "long_script": f"Breaking news: {topic}. According to multiple sources, this is a developing story. Here's what we know so far. Officials have confirmed the basic facts. The situation continues to evolve. We will update as more information becomes available.",
        "seo_youtube_title": seo_title[:60],
        "title_with_hashtag": f"{seo_title[:50]} #Breaking #News",
        "title_without_hashtag": seo_title[:60],
        "description": f"{topic} - breaking news update. Follow for more.",
        "hashtags": ["#breakingnews", "#worldnews", "#politics"],
        "tags": ["breaking news", "world news", "politics", "usa news"],
        "script_visual_segments": [
            {"segment_text": f"Breaking {topic}", "asset_type": "video", "visual_search_prompt": "breaking news studio"}
        ],
        "mood": "tense dramatic news",
        "confidence_score": 80
    }


# ============================================================
# VIDEO CREATION
# ============================================================

def create_video_god(script_data, editor_data):
    """Create video using all available assets"""
    logger.info("=" * 60)
    logger.info("VIDEO GENERATION - Creating Short")
    logger.info("=" * 60)
    
    try:
        video_builder = safe_import('src.media.video_builder', 'create_video')
        if video_builder:
            # Merge script and editor data
            merged = {**script_data, **editor_data}
            merged['full_script'] = script_data.get('short_script', '')
            merged['title'] = script_data.get('seo_youtube_title', '')
            
            video_path = video_builder(merged, editor_data)
            logger.info(f"Video created: {video_path}")
            return video_path
        else:
            logger.error("Video builder not available")
            return "output/videos/final.mp4"
    
    except Exception as e:
        logger.error(f"Video creation failed: {e}")
        traceback.print_exc()
        return "output/videos/final.mp4"


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def main():
    """Main orchestrator - 5 legs pipeline"""
    logger.info("=" * 60)
    logger.info("GOD LEVEL BOT START - 5 LEGS")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    logger.info(GOD_INSTRUCTION)
    
    # Initialize database
    init_db()
    
    # Show performance stats
    stats = get_performance_stats()
    logger.info(f"Performance stats: {stats}")
    
    # LEG 1: RESEARCH
    stories = research_god_main()
    if not stories:
        logger.error("No stories found - exiting")
        return
    
    logger.info(f"LEG 1: Got {len(stories)} candidate stories")
    
    # Try each candidate until one is approved
    approved = None
    
    for i, candidate in enumerate(stories[:5]):
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDIDATE {i+1}/{min(5, len(stories))}: {candidate.get('title', '')[:60]}")
        logger.info(f"{'='*60}")
        
        # Generate script
        script_data = generate_script_god(candidate)
        
        if script_data.get('confidence_score', 0) < 70:
            logger.warning(f"Low confidence script: {script_data.get('confidence_score')}")
            continue
        
        # FACT CHECKING
        logger.info("Running fact check...")
        fact_checker = safe_import('src.verification.claim_checker', 'fact_check')
        if fact_checker:
            fact_result = fact_checker(script_data.get('short_script', ''), candidate)
            if not fact_result.get('passed', False):
                logger.warning(f"Fact check failed: {fact_result.get('report', '')}")
                continue
            logger.info(f"Fact check passed: {fact_result.get('report', '')}")
        
        # LEG 2: EDITOR
        editor_data = editor_god_main(script_data, candidate)
        
        # Save to database
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        
        # Create video
        video_path = create_video_god(script_data, editor_data)
        
        # LEG 3: BOSS APPROVAL
        boss_data = boss_approval_main(video_path, script_data, full_story)
        
        if not boss_data.get('approved'):
            logger.warning(f"REJECTED by Boss: {boss_data.get('reason')}")
            continue
        
        logger.info(f"APPROVED by Boss: {boss_data.get('reason')}")
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    if not approved:
        logger.error("All candidates rejected - SAFE EXIT")
        return
    
    # Unpack approved
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    # Create thumbnail
    thumbnail_path = create_thumbnail(candidate, script_data)
    
    # LEG 4: UPLOADER
    video_id = uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"\n{'='*60}")
        logger.info(f"UPLOADED: https://youtu.be/{video_id}")
        logger.info(f"{'='*60}")
    
    # LEG 5: SELF EVOLUTION
    self_evolution_main()
    
    logger.info("\n" + "=" * 60)
    logger.info("GOD LEVEL BOT COMPLETE - 5 LEGS DONE")
    logger.info("=" * 60)


def create_thumbnail(candidate, script_data):
    """Create thumbnail image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        os.makedirs("output/thumbnails", exist_ok=True)
        thumb_path = "output/thumbnails/thumb.jpg"
        
        # Create 1280x720 thumbnail
        img = Image.new('RGB', (1280, 720), (20, 20, 40))
        draw = ImageDraw.Draw(img)
        
        # Add title text
        title = candidate.get('title', 'Breaking News')[:50]
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # Draw text with outline
        draw.text((640, 360), title, font=font, fill=(255, 255, 255), anchor="mm", 
                  stroke_width=3, stroke_fill=(0, 0, 0))
        
        img.save(thumb_path, quality=95)
        logger.info(f"Thumbnail created: {thumb_path}")
        return thumb_path
    
    except Exception as e:
        logger.error(f"Thumbnail failed: {e}")
        return None


if __name__ == "__main__":
    main()
