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
import re
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
# SAFE IMPORT
# ============================================================

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
    """Multi-source news collection"""
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD")
    logger.info("=" * 60)
    
    all_stories = []
    
    rss_collector = safe_import('src.collectors.rss_collector', 'collect_rss_news')
    if rss_collector:
        try:
            rss_stories = rss_collector()
            logger.info(f"RSS: {len(rss_stories)} stories")
            all_stories.extend(rss_stories)
        except Exception as e:
            logger.error(f"RSS failed: {e}")
    
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            google_stories = google_collector()
            logger.info(f"Google News: {len(google_stories)} stories")
            all_stories.extend(google_stories)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            trend_stories = trends_collector()
            logger.info(f"Trends: {len(trend_stories)} stories")
            all_stories.extend(trend_stories)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            reddit_stories = reddit_collector()
            logger.info(f"Reddit: {len(reddit_stories)} stories")
            all_stories.extend(reddit_stories)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    if not all_stories:
        logger.warning("All collectors failed - using fallback")
        all_stories = get_guaranteed_stories()
    
    all_stories = deduplicate_stories(all_stories)
    ranked = score_and_rank_stories(all_stories)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} stories")
    return ranked[:10]


def get_guaranteed_stories():
    """Fallback stories"""
    return [
        {
            "title": "White House Shocker Shatters Families Tonight",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 6000,
            "is_breakout": True,
            "search_volume": 90,
            "seo_youtube_title": "White House Shocker Tonight"
        },
        {
            "title": "Supreme Court Brutal Order Panic Millions",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5800,
            "is_breakout": True,
            "search_volume": 88,
            "seo_youtube_title": "Supreme Court Brutal Order"
        },
        {
            "title": "Brutal Tariffs Panic Millions of Families",
            "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
            "source": "guaranteed_google_news",
            "breakout_score": 5700,
            "is_breakout": True,
            "search_volume": 85,
            "seo_youtube_title": "Brutal Tariffs Panic Millions"
        },
    ]


def deduplicate_stories(stories):
    """Remove duplicates"""
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
    """Score and rank"""
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
    """Script-based visual asset collection"""
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
    """Quality gate"""
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
    """YouTube upload"""
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
    """Post-upload tasks"""
    comment_engine = safe_import('src.youtube.comment_engine', 'reply_to_comments')
    if comment_engine:
        try:
            comment_engine(video_id)
        except Exception as e:
            logger.error(f"Comment engine failed: {e}")
    
    logger.info(f"Analytics will be collected next run for {video_id}")


# ============================================================
# LEG 5: SELF EVOLUTION
# ============================================================

def self_evolution_main():
    """Performance learning"""
    logger.info("=" * 60)
    logger.info("LEG 5: SELF EVOLUTION")
    logger.info("=" * 60)
    
    # Collect analytics FIRST
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
# SCRIPT GENERATION - SHORT TITLES + EMOJI HOOKS
# ============================================================

def generate_script_god(story):
    """
    Generate SHORT + engaging title + script
    - Title: 30-50 chars MAX
    - Hook: 5 words + 1 emoji (auto-selected)
    """
    topic = story.get('title', '')
    seo_title = story.get('seo_youtube_title', '') or topic
    
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            prompt = f"""You are a YouTube Shorts CTR expert. Create a SHORT, punchy title + script.

TOPIC: {topic}

🚨 TITLE RULES (STRICT):
1. Title MUST be 30-50 characters (COUNT THEM!)
2. Short, punchy, mobile-friendly
3. NO long sentences. NO full news headline.
4. Use ONE of these SHORT formulas:
   • "The [X] Nobody Noticed"          (~28 chars)
   • "[X] Just Got Leaked"              (~22 chars)
   • "Why [X] Changes Everything"       (~28 chars)
   • "[X] — What Really Happened"       (~30 chars)
   • "This [X] Is Huge"                 (~18 chars)
   • "[X]: The Real Story"              (~22 chars)
5. Power words: leaked, exposed, revealed, warning, crisis, huge
6. If title > 50 chars → make SHORTER

❌ BAD (too long):
- "Russian Strike on Train Station Near Ukraine-Poland Border Seen as Warning"
- "We Must Heed Warnings of AI Tech Developers, Says UK Minister"

✅ GOOD (short, punchy):
- "Russia's Warning to NATO"           (25 chars)
- "The AI Warning Nobody Heard"        (29 chars)
- "Ukraine's Message to the West"      (30 chars)
- "Why This Changes Everything"        (28 chars)

🚨 WHITE BAR HOOK RULES:
1. MAXIMUM 5 words (VERY short!)
2. ALL CAPS
3. Include EXACTLY 1 relevant emoji at END
4. Create strong curiosity gap

🚨 EMOJI SELECTION RULE:
Choose the MOST RELEVANT emoji based on topic. Options:
- 🚨 breaking/urgent/alert
- ⚠️ warning/danger/risk
- 🔥 viral/hot/trending
- 💥 shocking/explosive
- 🚫 banned/blocked/refused
- 👀 look/exposed/watching
- ⚡ instant/breaking/fast
- 🎯 direct/aimed/targeted
- 💰 money/economy/tariffs
- 🏛️ government/politics/congress
- ⚔️ war/military/conflict
- 🤖 AI/tech/robots
- 📉 crash/drop/fall
- 📈 rise/growth/surge
- 🔒 secret/classified
- ❗ important/critical
- 🌍 global/world
- 🏆 win/victory
- ⚖️ law/court/justice
- 🔔 alert/subscribe

Example hooks with emojis:
- "THEY KNEW ALL ALONG 🚨"
- "TARIFFS CRUSHING MILLIONS 💰"
- "NATO'S FINAL WARNING ⚔️"
- "AI JUST CHANGED EVERYTHING 🤖"
- "THE SECRET IS OUT 🔒"
- "MARKETS ARE CRASHING 📉"
- "WARNING IGNORED ⚠️"
- "LEAKED JUST NOW 🔥"

🚨 SCRIPT (40 words):
- First sentence = strong hook
- Use "reports say" for unverified
- End with open loop

🚨 TAGS (15 max):
- Mix of short (1-2 words) and specific
- Include: breaking news, world news, viral, 2026

OUTPUT JSON ONLY:
{{
    "short_script": "40-word script",
    "seo_youtube_title": "30-50 char title ONLY",
    "description": "SEO description with subscribe CTA",
    "hashtags": ["#BreakingNews", "#WorldNews", "#TopicSpecific"],
    "tags": ["tag1", "tag2", "tag3"],
    "viral_hook": "MAX 5 WORDS + 1 EMOJI",
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
                            
                            # HARD LIMIT: Title 50 chars max
                            title = data.get('seo_youtube_title', '')
                            if len(title) > 50:
                                # Smart truncate at word boundary
                                title = title[:50].rsplit(' ', 1)[0]
                                if len(title) < 25:
                                    title = title + "..."
                                data['seo_youtube_title'] = title
                            
                            # HARD LIMIT: Hook 5 words + emoji
                            hook = data.get('viral_hook', '')
                            
                            # Ensure emoji present
                            emoji_pattern = re.compile(
                                "[\U0001F300-\U0001F9FF\U00002600-\U000027BF]+",
                                flags=re.UNICODE
                            )
                            
                            if not emoji_pattern.search(hook):
                                # Auto-add emoji based on topic
                                topic_lower = topic.lower()
                                if any(w in topic_lower for w in ['war', 'military', 'strike', 'missile', 'attack']):
                                    hook = hook + " ⚔️"
                                elif any(w in topic_lower for w in ['tariff', 'trade', 'economy', 'money', 'dollar']):
                                    hook = hook + " 💰"
                                elif any(w in topic_lower for w in ['trump', 'biden', 'congress', 'senate', 'white house', 'government']):
                                    hook = hook + " 🏛️"
                                elif any(w in topic_lower for w in ['ai', 'tech', 'robot', 'artificial']):
                                    hook = hook + " 🤖"
                                elif any(w in topic_lower for w in ['secret', 'leaked', 'classified', 'hidden']):
                                    hook = hook + " 🔒"
                                elif any(w in topic_lower for w in ['crash', 'drop', 'fall', 'plunge']):
                                    hook = hook + " 📉"
                                elif any(w in topic_lower for w in ['rise', 'surge', 'grow', 'soar']):
                                    hook = hook + " 📈"
                                elif any(w in topic_lower for w in ['court', 'law', 'justice', 'supreme']):
                                    hook = hook + " ⚖️"
                                else:
                                    hook = hook + " 🚨"
                            
                            # Limit words
                            words = hook.split()
                            if len(words) > 6:
                                words = words[:5] + [words[-1]]  # Keep last word (emoji)
                                hook = " ".join(words)
                            
                            data['viral_hook'] = hook
                            
                            logger.info(f"✅ Script by {model}")
                            logger.info(f"   Title ({len(data['seo_youtube_title'])} chars): {data['seo_youtube_title']}")
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
    """Fallback with SHORT title + emoji hook"""
    
    # Short title templates (max 50 chars)
    title_templates = [
        f"The {topic[:25]} Nobody Noticed",
        f"Why {topic[:30]} Matters",
        f"{topic[:40]} Just Changed",
        f"The Real {topic[:25]} Story",
    ]
    
    title = random.choice(title_templates)
    if len(title) > 50:
        title = title[:47] + "..."
    
    # Auto-select emoji based on topic
    topic_lower = topic.lower()
    if any(w in topic_lower for w in ['war', 'military', 'strike', 'missile']):
        emoji = "⚔️"
    elif any(w in topic_lower for w in ['tariff', 'trade', 'economy', 'money']):
        emoji = "💰"
    elif any(w in topic_lower for w in ['trump', 'biden', 'congress', 'white house']):
        emoji = "🏛️"
    elif any(w in topic_lower for w in ['ai', 'tech', 'robot']):
        emoji = "🤖"
    elif any(w in topic_lower for w in ['secret', 'leaked', 'classified']):
        emoji = "🔒"
    elif any(w in topic_lower for w in ['court', 'law', 'justice']):
        emoji = "⚖️"
    else:
        emoji = "🚨"
    
    hook_templates = [
        f"THEY KNEW ALL ALONG {emoji}",
        f"THIS CHANGES EVERYTHING {emoji}",
        f"WARNING IGNORED {emoji}",
        f"NOBODY NOTICED THIS {emoji}",
        f"THE PART EVERYONE MISSED {emoji}",
    ]
    
    hook = random.choice(hook_templates)
    
    return {
        "short_script": f"Breaking: {topic}. According to reports, this changes everything. Officials say the situation is developing. What happens next?",
        "seo_youtube_title": title,
        "description": f"{topic} - breaking news update. Subscribe for more.",
        "hashtags": ["#BreakingNews", "#WorldNews", "#GlobalNews"],
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
    """Create video"""
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
    """Create thumbnail"""
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
        
        # Text with shadow
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
# MAIN ORCHESTRATOR
# ============================================================

def main():
    """Main orchestrator"""
    logger.info("=" * 60)
    logger.info("GOD LEVEL BOT START - 5 LEGS")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    logger.info(GOD_INSTRUCTION)
    
    init_db()
    
    stats = get_performance_stats()
    logger.info(f"Stats: {stats}")
    
    # LEG 1
    stories = research_god_main()
    if not stories:
        logger.error("No stories - exit")
        return
    
    logger.info(f"Got {len(stories)} candidates")
    
    approved = None
    best_rejected = None
    
    for i, candidate in enumerate(stories[:5]):
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDIDATE {i+1}/5: {candidate.get('title', '')[:60]}")
        logger.info(f"{'='*60}")
        
        # Script
        script_data = generate_script_god(candidate)
        
        if script_data.get('confidence_score', 0) < 60:
            logger.warning(f"Low confidence: {script_data.get('confidence_score')}")
            continue
        
        # Fact check
        logger.info("Fact checking...")
        fact_checker = safe_import('src.verification.claim_checker', 'fact_check')
        if fact_checker:
            fact_result = fact_checker(script_data.get('short_script', ''), candidate)
            if not fact_result.get('passed', False):
                logger.warning(f"Fact check failed: {fact_result.get('report', '')}")
                continue
            logger.info(f"✅ Fact check: {fact_result.get('report', '')}")
        
        # LEG 2
        editor_data = editor_god_main(script_data, candidate)
        
        # Save
        full_story = {**candidate, **script_data}
        story_id = save_story(full_story)
        
        # Video
        video_path = create_video_god(script_data, editor_data)
        
        # LEG 3
        boss_data = boss_approval_main(video_path, script_data, full_story)
        
        # Track best rejected
        if not best_rejected or boss_data.get('score', 0) > best_rejected[3].get('score', 0):
            best_rejected = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        
        if not boss_data.get('approved'):
            logger.warning(f"REJECTED: {boss_data.get('reason')}")
            continue
        
        logger.info(f"APPROVED: {boss_data.get('reason')}")
        approved = (candidate, script_data, editor_data, boss_data, story_id, video_path)
        break
    
    # Fallback: use best rejected if score >= 65
    if not approved and best_rejected:
        score = best_rejected[3].get('score', 0)
        if score >= 65:
            logger.warning(f"⚠️ Using best rejected (score {score:.1f})")
            approved = best_rejected
    
    if not approved:
        logger.error("All rejected - SAFE EXIT")
        return
    
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    
    # Thumbnail
    thumbnail_path = create_thumbnail(candidate, script_data)
    
    # LEG 4
    video_id = uploader_god_main(video_path, thumbnail_path, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"\n{'='*60}")
        logger.info(f"UPLOADED: https://youtu.be/{video_id}")
        logger.info(f"{'='*60}")
    
    # LEG 5
    self_evolution_main()
    
    logger.info("\n" + "=" * 60)
    logger.info("GOD LEVEL BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
