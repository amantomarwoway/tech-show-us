"""
main.py - GOD LEVEL YOUTUBE SHORTS BOT v10
- Gemini 3.6-flash ONLY (with 2 retries)
- GitHub Models (OpenAI GPT-4o, GPT-4o-mini) - 100% FREE
- No Groq, No paid OpenAI
- Fixed 40-word fallback template
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
    if not title:
        return False
    title_lower = title.lower()
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
# 🔥 AUDIENCE ACTIVITY CHECK
# ============================================================

def is_audience_active(story):
    title = story.get('title', '')
    source = story.get('source', '').lower()
    logger.info(f"🔍 Activity check: {title[:55]}")
    
    signals = []
    
    reddit_score = 40
    if 'reddit' in source:
        reddit_upvotes = story.get('reddit_score', 0)
        if reddit_upvotes >= 5000:
            reddit_score = 100
        elif reddit_upvotes >= 2000:
            reddit_score = 80
        elif reddit_upvotes >= 1000:
            reddit_score = 60
        elif reddit_upvotes >= 500:
            reddit_score = 45
        else:
            reddit_score = 25
    
    signals.append(('reddit', reddit_score))
    logger.info(f"   🔥 Reddit freshness: {reddit_score}/100")
    
    trends_score = 40
    if 'trends' in source or 'trending' in source or 'breakout' in source:
        trends_score = 85
    elif 'google_news' in source:
        trends_score = 60
    
    signals.append(('trends', trends_score))
    logger.info(f"   📊 Trends freshness: {trends_score}/100")
    
    spike_score = check_trends_spike(title)
    signals.append(('spike', spike_score))
    logger.info(f"   ⚡ Real-time spike: {spike_score}/100")
    
    weighted_score = (
        reddit_score * 0.35 +
        trends_score * 0.30 +
        spike_score * 0.35
    )
    
    active_signals = sum(1 for _, score in signals if score >= 50)
    logger.info(f"   🎯 Weighted: {weighted_score:.1f}/100 ({active_signals}/3 active)")
    
    if active_signals >= 1 or weighted_score >= 45:
        return True, weighted_score, f"Active ({active_signals}/3)"
    else:
        return False, weighted_score, f"Low ({active_signals}/3)"


def check_trends_spike(title):
    try:
        from pytrends.request import TrendReq
        words = [w for w in title.split() if len(w) > 4][:3]
        if not words:
            return 40
        query = " ".join(words)
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10)
        except TypeError:
            pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload([query], timeframe='now 1-H', geo='US')
        time.sleep(1)
        data = pytrends.interest_over_time()
        if data.empty or query not in data.columns:
            return 40
        values = data[query].tolist()
        if not values:
            return 40
        current = values[-1]
        if current >= 80: return 100
        elif current >= 50: return 80
        elif current >= 20: return 55
        elif current >= 5: return 35
        else: return 20
    except Exception as e:
        logger.debug(f"   Trends spike failed: {str(e)[:60]}")
        return 45


# ============================================================
# LEG 1: RESEARCH GOD
# ============================================================

def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD - VIRAL TOPICS ONLY")
    logger.info("=" * 60)
    
    all_stories = []
    
    reddit_collector = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit_collector:
        try:
            s = reddit_collector()
            logger.info(f"🔥 Reddit RSS: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    trends_collector = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends_collector:
        try:
            s = trends_collector()
            logger.info(f"🔥 Google News Trending: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    google_collector = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google_collector:
        try:
            s = google_collector()
            logger.info(f"🔥 Google News: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Google News failed: {e}")
    
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
    
    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
        if not story['title'] or len(story['title']) < 10:
            story['title'] = 'Trending Topic'
    
    all_stories = [s for s in all_stories if s.get('title') and len(s['title']) > 10]
    
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
        {"title": "This Just Broke The Internet", "url": "https://trends.google.com", "source": "guaranteed_trends", "breakout_score": 6500, "is_breakout": True, "search_volume": 90, "seo_youtube_title": "This Just Broke The Internet"},
        {"title": "Nobody Expected This To Happen Today", "url": "https://trends.google.com", "source": "guaranteed_trends", "breakout_score": 6300, "is_breakout": True, "search_volume": 88, "seo_youtube_title": "Nobody Expected This"},
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
    script_text = (script_data.get('short_script', '') or script_data.get('full_script', '') or script_data.get('viral_hook', ''))
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
        title = script_data.get('seo_youtube_title', '') or candidate.get('title', 'Trending')
        video_id = uploader(
            video_path=video_path,
            thumbnail_path=thumbnail_path,
            title=title[:100],
            description=script_data.get('description', 'Trending now.'),
            tags=script_data.get('tags', ['trending', 'viral']),
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
# PROMPT BUILDER
# ============================================================

def build_prompt(topic):
    return f"""You are a YouTube Shorts VIRAL expert + VISUAL DIRECTOR.

TRENDING TOPIC: {topic}

🚨 YOUR TASK:
1. Create a VIRAL STATEMENT title (no question)
2. Write a 40-word script that creates CURIOSITY
3. Provide 6 SPECIFIC visual search queries

🚨 TITLE RULES (STATEMENT PATTERNS - NO QUESTIONS):
- MUST be 30-50 characters
- MUST NOT be a question (no "?" in title)
- MUST have 1 hashtag at END

PATTERN 1: "The Reason [X] Nobody Knows #Viral"
PATTERN 2: "This [X] Just Broke The Internet #Trending"
PATTERN 3: "Nobody Expected [X] To Happen #News"
PATTERN 4: "The Truth About [X] Revealed #Viral"
PATTERN 5: "[X] Is Bigger Than Anyone Thought #Viral"

✅ GOOD TITLES: "The Reason Nobody Saw This Coming #Viral"
❌ BAD: "Why Did This Happen? #Viral"

FORBIDDEN WORDS: BREAKING NEWS, MINNEAPOLIMEDIA, CNN, BBC, ABC, NBC, CBS, FOX, MSNBC, NYT, WSJ, AP, REUTERS

🚨 WHITE BAR HOOK:
- MUST be 4-5 WORDS
- NO question mark
- ALL CAPS
✅ "NOBODY SAW THIS COMING", "THIS CHANGES EVERYTHING", "THE TRUTH REVEALED"

🚨 SCRIPT RULES (40 words):
- First sentence = HOOK (statement)
- Then 2-3 surprising facts
- End with mystery

🚨 VISUAL QUERIES (6 queries, 2-4 words each):
- MUST be SPECIFIC and VISUAL
- NO abstract words

OUTPUT JSON ONLY:
{{
    "short_script": "40-word script",
    "seo_youtube_title": "Statement title #OneHashtag",
    "description": "SEO description",
    "hashtags": ["#Viral"],
    "tags": ["tag1", "tag2"],
    "viral_hook": "4-5 WORD STATEMENT",
    "visual_queries": ["q1", "q2", "q3", "q4", "q5", "q6"],
    "mood": "engaging curious",
    "confidence_score": 85
}}
"""


# ============================================================
# PROCESS AI RESPONSE
# ============================================================

def process_ai_response(text, model_name):
    if not text:
        return None
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
    except:
        return None
    
    vq = data.get('visual_queries', [])
    if not isinstance(vq, list):
        vq = []
    clean_vq = [q.strip() for q in vq if isinstance(q, str) and 3 <= len(q.strip()) <= 50]
    data['visual_queries'] = clean_vq[:6]
    if clean_vq:
        logger.info(f"   🎨 Visual queries ({len(clean_vq)}): {clean_vq}")
    
    hook = data.get('viral_hook', '')
    emoji_pat = re.compile("[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+", flags=re.UNICODE)
    hook = emoji_pat.sub('', hook).strip()
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
    
    title = data.get('seo_youtube_title', '')
    title = clean_topic(title)
    title_clean = re.sub(r'#\w+', '', title).strip()
    title_clean = re.sub(r'\b[A-Z]{4,}\b', '', title_clean)
    for bad in ['MINNEAPOLI', 'BREAKING', 'NEWS', 'MEDIA', 'LIVE']:
        title_clean = re.sub(rf'\b{bad}\b', '', title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r'\s+', ' ', title_clean).strip()
    title_clean = re.sub(r'^[\-:\|?]+', '', title_clean).strip()
    title_clean = title_clean.replace('?', '').strip()
    
    if has_publisher_name(title_clean):
        logger.warning(f"   ⚠️ Publisher in title - skipping")
        return None
    
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
        return None
    
    data['seo_youtube_title'] = title_full
    data['hashtags'] = [hashtag]
    
    logger.info(f"✅ Script by {model_name}")
    logger.info(f"   Title ({len(title_full)}): {title_full}")
    logger.info(f"   Hook: {data['viral_hook']}")
    return data


# ============================================================
# SCRIPT GENERATION - Gemini 3.6 + GitHub Models (Free OpenAI)
# ============================================================

def generate_script_god(story):
    """
    Priority:
    1. Gemini 3.6-flash (2 retries)
    2. GitHub Models: openai/gpt-4o-mini (FREE)
    3. GitHub Models: openai/gpt-4o (FREE)
    4. Fixed 40-word template
    """
    raw_topic = story.get('title', '')
    topic = clean_topic(raw_topic)
    if len(topic) < 15:
        topic = raw_topic
    
    logger.info(f"   Raw: {raw_topic[:70]}")
    logger.info(f"   Clean: {topic[:70]}")
    
    prompt = build_prompt(topic)
    
    # ============================================================
    # 1. GEMINI 3.6-FLASH ONLY (with 2 retries)
    # ============================================================
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            
            for attempt in range(1, 3):  # 2 attempts
                try:
                    logger.info(f"   🔷 Gemini 3.6-flash (attempt {attempt}/2)")
                    resp = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt
                    )
                    text = getattr(resp, 'text', '')
                    if text:
                        data = process_ai_response(text, "Gemini-3.6-flash")
                        if data:
                            return data
                except Exception as e:
                    logger.warning(f"   ❌ Gemini attempt {attempt}: {str(e)[:80]}")
                    if attempt < 2:
                        logger.info(f"   ⏳ Waiting 3s before retry...")
                        time.sleep(3)
                    continue
        except Exception as e:
            logger.warning(f"   Gemini client failed: {e}")
    
    # ============================================================
    # 2. GITHUB MODELS - FREE OpenAI (gpt-4o-mini, gpt-4o)
    # ============================================================
    # Uses GITHUB_TOKEN from GitHub Actions (already available)
    github_token = os.getenv("GITHUB_TOKEN", "")
    
    if github_token:
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=github_token,
                base_url="https://models.github.ai/inference"
            )
            
            # Real OpenAI models - FREE via GitHub Models
            github_models = [
                "openai/gpt-4o-mini",    # Fast + free
                "openai/gpt-4o",         # Best + free
            ]
            
            for model in github_models:
                try:
                    logger.info(f"   🟢 Trying GitHub Models (FREE OpenAI): {model}")
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You are a viral YouTube Shorts expert. Always respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9,
                        max_tokens=1500,
                        response_format={"type": "json_object"}
                    )
                    
                    text = response.choices[0].message.content
                    if text:
                        data = process_ai_response(text, f"GitHub-{model}")
                        if data:
                            return data
                except Exception as e:
                    logger.warning(f"   ❌ GitHub Models {model}: {str(e)[:100]}")
                    continue
        except ImportError:
            logger.warning("   OpenAI library not installed")
        except Exception as e:
            logger.warning(f"   GitHub Models failed: {e}")
    else:
        logger.warning("   GITHUB_TOKEN not available")
    
    # ============================================================
    # FALLBACK TEMPLATE (40-word script)
    # ============================================================
    logger.info("⚠️ All AI failed - using fixed template")
    return get_template_script(topic)


# ============================================================
# FIXED FALLBACK TEMPLATE (40-word script)
# ============================================================

def get_template_script(topic):
    t_low = topic.lower()
    
    if any(w in t_low for w in ['mugshot', 'arrested', 'police', 'crime']):
        hashtag, hook, title_q = "#Viral", "NOBODY SAW THIS COMING", "The Story Everyone Is Missing"
        vq = ["police mugshot", "woman portrait", "smartphone scrolling", "social media icons", "camera flash", "photo comparison"]
    elif any(w in t_low for w in ['celebrity', 'actress', 'singer', 'taylor', 'kelce']):
        hashtag, hook, title_q = "#Entertainment", "THIS CHANGED EVERYTHING", "What Really Happened Here"
        vq = ["celebrity red carpet", "paparazzi camera", "glamorous woman", "fashion studio", "camera flash", "movie premiere"]
    elif any(w in t_low for w in ['kid', 'child', 'boy', 'girl', 'young']):
        hashtag, hook, title_q = "#Viral", "THIS BROKE THE INTERNET", "The Kid Everyone Is Watching"
        vq = ["happy child playing", "young kid portrait", "children playing outside", "kid smiling", "family moment", "young boy portrait"]
    elif any(w in t_low for w in ['sport', 'match', 'goal', 'nba', 'nfl']):
        hashtag, hook, title_q = "#Sports", "NOBODY EXPECTED THIS", "The Moment Everyone Missed"
        vq = ["stadium crowd", "athlete action", "sports trophy", "football field", "basketball court", "crowd cheering"]
    elif any(w in t_low for w in ['music', 'song', 'album', 'concert']):
        hashtag, hook, title_q = "#Music", "THIS BROKE THE INTERNET", "The Reason This Blew Up"
        vq = ["concert stage", "singer microphone", "music studio", "crowd dancing", "headphones", "vinyl records"]
    elif any(w in t_low for w in ['ai', 'tech', 'robot', 'chatgpt']):
        hashtag, hook, title_q = "#Tech", "THIS CHANGES EVERYTHING", "What The Tech World Missed"
        vq = ["artificial intelligence", "AI robot", "computer code", "smartphone screen", "tech office", "server room"]
    elif any(w in t_low for w in ['trend', 'viral', 'tiktok', 'challenge']):
        hashtag, hook, title_q = "#Viral", "THIS WENT CRAZY VIRAL", "The Truth Behind This Trend"
        vq = ["viral video screen", "young people phone", "social media", "city crowd", "smartphone scrolling", "trending icons"]
    elif any(w in t_low for w in ['crash', 'dead', 'killed', 'accident']):
        hashtag, hook, title_q = "#Breaking", "NOBODY SAW THIS COMING", "The Reason This Happened"
        vq = ["car accident", "emergency lights", "police scene", "ambulance", "road closed", "emergency response"]
    elif any(w in t_low for w in ['trump', 'biden', 'president', 'congress']):
        hashtag, hook, title_q = "#Politics", "THIS CHANGES EVERYTHING", "What They Dont Want You To See"
        vq = ["government building", "press conference", "politician podium", "capitol building", "microphone interview", "protest crowd"]
    elif any(w in t_low for w in ['cat', 'dog', 'kitten', 'puppy', 'animal']):
        hashtag, hook, title_q = "#Viral", "THIS MELTED THE INTERNET", "The Cutest Story Today"
        vq = ["cute kitten", "cute puppy", "animal rescue", "pet playing", "cat portrait", "dog portrait"]
    else:
        hashtag, hook, title_q = "#Viral", "NOBODY SAW THIS COMING", "The Story Behind This Moment"
        vq = ["viral video screen", "young people phone", "social media", "city crowd", "smartphone scrolling", "trending icons"]
    
    title_full = f"{title_q} {hashtag}"
    if len(title_full) > 50:
        max_title = 50 - len(hashtag) - 1
        title_q = title_q[:max_title].rsplit(' ', 1)[0]
        title_full = f"{title_q} {hashtag}"
    
    script_40 = (
        "This moment went viral for one surprising reason. "
        "Sources confirm the details nobody expected. "
        "Reports show millions are watching this unfold right now. "
        "Experts say the trend is only getting bigger. "
        "Here is what everyone is missing."
    )
    
    return {
        "short_script": script_40,
        "seo_youtube_title": title_full,
        "description": "The story behind this trend. Subscribe for more viral content.",
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
    
    logger.info("=" * 60)
    logger.info("🔥 AUDIENCE ACTIVITY FILTER")
    logger.info("=" * 60)
    
    active_stories = []
    for story in stories[:8]:
        is_active, score, reason = is_audience_active(story)
        story['activity_score'] = score
        story['activity_reason'] = reason
        if is_active:
            active_stories.append(story)
            logger.info(f"   ✅ ACTIVE ({score:.0f}): {story.get('title', '')[:50]}")
        else:
            logger.info(f"   ❌ SKIP ({score:.0f}): {story.get('title', '')[:50]}")
    
    if not active_stories:
        logger.warning("⚠️ No active topics - using top 5 anyway")
        for s in stories[:5]:
            if 'activity_score' not in s:
                s['activity_score'] = 0
                s['activity_reason'] = "Fallback"
        active_stories = stories[:5]
    else:
        logger.info(f"🔥 {len(active_stories)} ACTIVE topics found")
    
    stories = active_stories
    
    approved = None
    best_rejected = None
    skipped_count = 0
    
    for i, candidate in enumerate(stories[:5]):
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDIDATE {i+1}/5: {candidate.get('title', '')[:60]}")
        logger.info(f"   🔥 Activity Score: {candidate.get('activity_score', 0):.0f}/100")
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
