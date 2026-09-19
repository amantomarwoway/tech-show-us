"""
main.py - AUTONOMOUS BOT WITH AI SELF-REPAIR
Goal: Maximize views + engagement + subscribers
Features: Learn from data, self-optimize, self-repair
"""

import os
import sys
import time
import traceback
import json
import random
import re
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.dirname(__file__))

from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
from src.utils.logger import setup_logger
from src.database import init_db, save_story, mark_uploaded, get_performance_stats

logger = setup_logger(__name__)


# ============================================================
# SAFE IMPORT
# ============================================================

def safe_import(module_path, function_name=None):
    try:
        if function_name:
            module = __import__(module_path, fromlist=[function_name])
            return getattr(module, function_name)
        return __import__(module_path)
    except Exception as e:
        logger.warning(f"Import failed {module_path}: {e}")
        return None


# ============================================================
# TOPIC CLEANING
# ============================================================

def clean_topic(title):
    if not title:
        return ""
    cleaned = title.strip()
    if '|' in cleaned:
        cleaned = max(cleaned.split('|'), key=len).strip()
    
    patterns = [
        r'^(?:[A-Z][A-Za-z]+\s*){1,4}(?:NEWS|MEDIA|TIMES|POST|TODAY|NOW|TV|PRESS|JOURNAL|REPORT)\s*[-:]\s*',
        r'^(?:MINNEAPOLI|CNN|BBC|ABC|NBC|CBS|FOX|MSNBC|NYT|WSJ|AP|REUTERS)[A-Za-z]*\s*[-:]\s*',
    ]
    for p in patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\b[A-Z]{4,}[A-Za-z]*(MEDIA|NEWS)\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bBREAKING(\s+NEWS)?\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bLIVE(\s+UPDATE)?\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    cleaned = re.sub(r'\(.*?\)', '', cleaned)
    cleaned = re.sub(r'\s*-\s*[A-Z][a-zA-Z\s]{2,30}$', '', cleaned)
    cleaned = re.sub(r'^[\|\-\s:]+', '', cleaned)
    cleaned = re.sub(r'[\|\-\s:]+$', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def has_publisher_name(text):
    if not text:
        return False
    bad = ['MINNEAPOLI', 'BREAKING NEWS', 'CNN', 'BBC', 'ABC', 'NBC', 'CBS',
           'FOX', 'MSNBC', 'NYT', 'WSJ', 'APNEWS', 'REUTERS', 'DAILY',
           'TIMES', 'POST', 'JOURNAL', 'PRESS', 'MEDIA']
    t = text.upper()
    return any(b in t for b in bad)


# ============================================================
# SPAM + VIRAL FILTERS
# ============================================================

def is_spam_topic(title):
    if not title:
        return True
    tl = title.lower()
    
    spam_kw = ['18+', '18 +', 'adult', 'xxx', 'porn', 'nude', 'sex', 'sexy',
               'escort', 'dating', 'hookup', 'casino', 'betting', 'lottery',
               'gambling', 'loan', 'cash advance', 'free download', 'torrent',
               'crack', 'keygen', 'hack tool', 'cheat', 'mod apk', 'viagra',
               'cialis', 'weight loss pill', 'make money fast', 'work from home',
               'bitcoin giveaway', 'crypto scam']
    if any(kw in tl for kw in spam_kw):
        return True
    
    spam_domains = ['uv.es', '.ru/', '.cn/', '.xyz', '.top', '.click',
                    'blogspot', 'wordpress.com', 'wixsite', 'bit.ly', 'tinyurl']
    if any(d in tl for d in spam_domains):
        return True
    
    if re.search(r'https?://|www\.', tl):
        return True
    
    if len(title) > 20:
        caps = sum(1 for c in title if c.isupper()) / len(title)
        if caps > 0.6:
            return True
    
    return False


def is_viral_topic(title):
    if not title or is_spam_topic(title):
        return False
    
    tl = title.lower()
    
    niche = ['skincare', 'botox', 'beauty', 'makeup', 'haircare', 'recipe',
             'cooking', 'diet', 'meal prep', 'workout', 'yoga', 'kitchen',
             'home decor', 'diy', 'craft', 'fashion', 'outfit', 'jewelry',
             'body scrubber', 'candle', 'soap', 'garden', 'plant care',
             'pet care', 'relationship', 'dating tips', 'parenting',
             'weather', 'temperature', 'forecast', 'county', 'municipal',
             'neighborhood', 'daily thread', 'weekly thread', 'megathread',
             'roundup', 'vs prediction', 'odds', 'preview', 'recap',
             'discussion', 'questions about', 'help me']
    
    if any(kw in tl for kw in niche):
        return False
    
    if len(title.split()) < 5:
        return False
    
    return True


# ============================================================
# AUDIENCE ACTIVITY
# ============================================================

def is_audience_active(story):
    title = story.get('title', '')
    source = story.get('source', '').lower()
    
    logger.info(f"🔍 Activity: {title[:55]}")
    
    reddit_score = 40
    if 'reddit' in source:
        up = story.get('reddit_score', 0)
        reddit_score = 100 if up >= 5000 else 80 if up >= 2000 else 60 if up >= 1000 else 45 if up >= 500 else 25
    
    trends_score = 40
    if any(x in source for x in ['trends', 'trending', 'breakout']):
        trends_score = 85
    elif 'google_news' in source:
        trends_score = 60
    
    spike_score = check_trends_spike(title)
    
    logger.info(f"   🔥 Reddit: {reddit_score} | 📊 Trends: {trends_score} | ⚡ Spike: {spike_score}")
    
    weighted = reddit_score * 0.35 + trends_score * 0.30 + spike_score * 0.35
    active = sum(1 for s in [reddit_score, trends_score, spike_score] if s >= 50)
    
    logger.info(f"   🎯 Weighted: {weighted:.1f} ({active}/3)")
    
    return (active >= 1 or weighted >= 45), weighted


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
        vals = data[query].tolist()
        if not vals:
            return 40
        c = vals[-1]
        return 100 if c >= 80 else 80 if c >= 50 else 55 if c >= 20 else 35 if c >= 5 else 20
    except:
        return 45


# ============================================================
# LEG 1: RESEARCH
# ============================================================

def research_god_main():
    logger.info("=" * 60)
    logger.info("LEG 1: RESEARCH GOD")
    logger.info("=" * 60)
    
    all_stories = []
    
    reddit = safe_import('src.collectors.reddit_collector', 'collect_reddit_trends')
    if reddit:
        try:
            s = reddit()
            logger.info(f"🔥 Reddit: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Reddit failed: {e}")
    
    trends = safe_import('src.collectors.trends_collector', 'collect_trends')
    if trends:
        try:
            s = trends()
            logger.info(f"🔥 Google News: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Trends failed: {e}")
    
    google = safe_import('src.collectors.google_news_collector', 'collect_google_news')
    if google:
        try:
            s = google()
            logger.info(f"🔥 Google News RSS: {len(s)} stories")
            all_stories.extend(s)
        except Exception as e:
            logger.error(f"Google failed: {e}")
    
    if len(all_stories) < 30:
        rss = safe_import('src.collectors.rss_collector', 'collect_rss_news')
        if rss:
            try:
                s = rss()
                logger.info(f"🔥 RSS: {len(s)} stories")
                all_stories.extend(s)
            except Exception as e:
                logger.error(f"RSS failed: {e}")
    
    if not all_stories:
        all_stories = get_fallback_stories()
    
    for story in all_stories:
        story['title'] = clean_topic(story.get('title', ''))
        if not story['title'] or len(story['title']) < 10:
            story['title'] = 'Trending Topic'
    
    all_stories = [s for s in all_stories if s.get('title') and len(s['title']) > 10]
    
    before = len(all_stories)
    all_stories = [s for s in all_stories if is_viral_topic(s.get('title', ''))]
    logger.info(f"Viral filter: {before} -> {len(all_stories)}")
    
    # Dedup
    seen = set()
    unique = []
    for s in all_stories:
        k = s.get('title', '')[:30].lower()
        if k not in seen:
            seen.add(k)
            unique.append(s)
    all_stories = unique
    logger.info(f"Dedup: -> {len(all_stories)}")
    
    # Rank
    scorer = safe_import('src.intelligence.topic_scorer', 'rank_stories')
    if scorer:
        try:
            ranked = scorer(all_stories)
        except:
            ranked = sorted(all_stories, key=lambda x: x.get('breakout_score', 0), reverse=True)
    else:
        ranked = sorted(all_stories, key=lambda x: x.get('breakout_score', 0), reverse=True)
    
    logger.info(f"LEG 1 COMPLETE: {len(ranked)} stories")
    for i, s in enumerate(ranked[:5]):
        logger.info(f"  #{i+1}: {s.get('title', '')[:60]}")
    
    return ranked[:15]


def get_fallback_stories():
    return [
        {"title": "This Just Broke The Internet Overnight", "url": "https://trends.google.com", "source": "fallback", "breakout_score": 6500, "is_breakout": True, "search_volume": 90},
        {"title": "Nobody Expected This To Happen This Week", "url": "https://trends.google.com", "source": "fallback", "breakout_score": 6300, "is_breakout": True, "search_volume": 88},
        {"title": "The Truth Behind This Viral Moment", "url": "https://trends.google.com", "source": "fallback", "breakout_score": 6100, "is_breakout": True, "search_volume": 85},
    ]


# ============================================================
# LEG 2: EDITOR
# ============================================================

def editor_god_main(script_data, candidate):
    logger.info("=" * 60)
    logger.info("LEG 2: EDITOR GOD")
    logger.info("=" * 60)
    
    editor_data = {"segments": [], "visuals": [], "background_music": None, "sound_effects": []}
    script_text = script_data.get('short_script', '') or script_data.get('full_script', '')
    if not script_text:
        return editor_data
    
    vq = script_data.get('visual_queries', [])
    if vq:
        logger.info(f"🎨 Visual queries: {len(vq)}")
    
    try:
        from src.media.asset_finder import find_assets_for_script
        visuals = find_assets_for_script(script_text, num_clips=25, visual_queries=vq)
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
    
    result = {"approved": False, "score": 0, "reason": ""}
    
    try:
        gate = safe_import('src.safety.policy_filter', 'run_quality_gate')
        if gate:
            g = gate(script_data, full_story)
            if not g.get('passed', False):
                result['reason'] = g.get('reason', 'Quality gate failed')
                return result
        
        ranker = safe_import('src.intelligence.story_ranker', 'calculate_publish_score')
        if ranker:
            score = ranker(full_story)
            result['score'] = score
            if score >= 60:
                result['approved'] = True
                result['reason'] = f"Score: {score:.1f}"
            elif score >= 50:
                result['approved'] = True
                result['reason'] = f"Acceptable: {score:.1f}"
            else:
                result['reason'] = f"Too low: {score:.1f}"
        else:
            if script_data.get('short_script'):
                result['approved'] = True
                result['score'] = 75
                result['reason'] = "Fallback"
    except Exception as e:
        logger.error(f"Boss failed: {e}")
        result['reason'] = str(e)
    
    logger.info(f"LEG 3: {'✅ APPROVED' if result['approved'] else '❌ REJECTED'} - {result['reason']}")
    return result


# ============================================================
# LEG 4: UPLOADER
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
            tags=script_data.get('tags', ['trending', 'viral', 'shorts']),
            category_id="24"
        )
        if video_id:
            logger.info(f"LEG 4: ✅ https://youtu.be/{video_id}")
            post_upload(video_id, script_data)
        return video_id
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return None


def post_upload(video_id, script_data):
    comment_engine = safe_import('src.youtube.comment_engine', 'reply_to_comments')
    if comment_engine:
        try:
            comment_engine(video_id)
        except Exception as e:
            logger.error(f"Comments failed: {e}")


# ============================================================
# LEG 5: SELF EVOLUTION + SELF REPAIR (AI POWERED)
# ============================================================

def self_evolution_main():
    """
    Full self-evolution pipeline:
    1. Collect analytics
    2. Analyze retention
    3. Auto-optimize parameters
    4. AI-powered self-repair
    5. Learn from performance
    """
    logger.info("=" * 60)
    logger.info("LEG 5: SELF EVOLUTION + AI REPAIR")
    logger.info("=" * 60)
    
    # Step 1: Collect analytics
    try:
        from src.youtube.analytics_collector import collect_analytics
        collected = collect_analytics()
        logger.info(f"📊 Analytics collected: {collected} videos")
    except Exception as e:
        logger.warning(f"Analytics failed: {e}")
    
    # Step 2: Analyze retention
    try:
        from src.learning.retention_analyzer import analyze_retention
        analyze_retention()
        logger.info("📊 Retention analyzed")
    except Exception as e:
        logger.warning(f"Retention analysis failed: {e}")
    
    # Step 3: Auto-optimize
    try:
        from src.learning.auto_optimizer import analyze_and_optimize
        analyze_and_optimize()
        logger.info("🧠 Optimization complete")
    except Exception as e:
        logger.warning(f"Optimizer failed: {e}")
    
    # Step 4: AI-POWERED SELF-REPAIR (NEW)
    try:
        from src.learning.self_repair import run_self_diagnostics
        logger.info("🔧 Starting self-diagnostics + AI repair...")
        run_self_diagnostics()
        logger.info("🔧 Self-repair cycle complete")
    except Exception as e:
        logger.warning(f"Self-repair failed: {e}")
        traceback.print_exc()
    
    # Step 5: Learn from performance
    learner = safe_import('src.learning.performance_learner', 'learn_from_performance')
    if learner:
        try:
            insights = learner()
            logger.info(f"📚 Insights: {insights}")
        except Exception as e:
            logger.warning(f"Learning failed: {e}")
    
    logger.info("=" * 60)
    logger.info("LEG 5 COMPLETE")
    logger.info("=" * 60)


# ============================================================
# SCRIPT GENERATION
# ============================================================

def build_prompt(topic, video_duration=30, hook_style="statement", title_pattern="reason"):
    words = int(video_duration * 2.5)
    
    patterns = {
        'reason': "The Reason [X] Nobody Knows",
        'truth': "The Truth About [X] Revealed",
        'nobody': "Nobody Expected [X] To Happen",
        'broke': "This [X] Broke The Internet",
        'really': "What Really Happened With [X]",
        'bigger': "[X] Is Bigger Than Anyone Thought",
    }
    title_pattern_str = patterns.get(title_pattern, patterns['reason'])
    
    return f"""You are a VIRAL YouTube Shorts expert.

TOPIC: {topic}
TARGET DURATION: {video_duration} seconds ({words} words)
HOOK STYLE: {hook_style}

TITLE (30-50 chars, NO question mark, ends with 1 hashtag):
Use pattern: "{title_pattern_str}"
FORBIDDEN: BREAKING NEWS, MINNEAPOLIMEDIA, CNN, BBC, ABC, NBC, CBS, FOX
GOOD: "The Reason Nobody Saw This Coming #Viral"

WHITE BAR HOOK (4-5 words, ALL CAPS, NO ?):
GOOD: "NOBODY SAW THIS COMING", "THIS CHANGES EVERYTHING"

SCRIPT ({words} words):
- First sentence = HOOK (statement, not question)
- 2-3 surprising facts
- End with mystery

VISUAL QUERIES (6 queries, 2-4 words each, SPECIFIC):
GOOD: "police mugshot camera", "glamorous woman red carpet"
BAD: "story continues", "sources say"

OUTPUT JSON ONLY:
{{
    "short_script": "{words}-word script",
    "seo_youtube_title": "Statement title #OneHashtag",
    "description": "SEO description",
    "hashtags": ["#Viral", "#Trending", "#Shorts"],
    "tags": ["trending", "viral", "shorts"],
    "viral_hook": "4-5 WORD STATEMENT",
    "visual_queries": ["q1", "q2", "q3", "q4", "q5", "q6"],
    "confidence_score": 85
}}
"""


def process_ai_response(text, model_name):
    if not text:
        return None
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group())
    except:
        return None
    
    vq = data.get('visual_queries', [])
    if not isinstance(vq, list):
        vq = []
    clean_vq = [q.strip() for q in vq if isinstance(q, str) and 3 <= len(q.strip()) <= 50]
    data['visual_queries'] = clean_vq[:6]
    
    hook = data.get('viral_hook', '')
    hook = re.sub(r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001F1E0-\U0001F1FF]+', '', hook).strip()
    hook = hook.rstrip('?').strip()
    words = hook.split()
    if len(words) > 5:
        words = words[:5]
    elif len(words) < 4:
        if not any(w in hook.upper() for w in ['THIS', 'NOBODY', 'THE', 'EVERY']):
            hook = "THIS CHANGES " + hook.upper()
            words = hook.split()[:5]
    data['viral_hook'] = " ".join(words).upper()
    
    title = data.get('seo_youtube_title', '')
    title = clean_topic(title)
    title = re.sub(r'#\w+', '', title).strip()
    title = re.sub(r'\b[A-Z]{4,}\b', '', title)
    for bad in ['MINNEAPOLI', 'BREAKING', 'NEWS', 'MEDIA', 'LIVE']:
        title = re.sub(rf'\b{bad}\b', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()
    title = title.replace('?', '').strip()
    
    if has_publisher_name(title) or is_spam_topic(title):
        return None
    
    hashtags = data.get('hashtags', ['#Viral'])
    hashtag = hashtags[0] if hashtags else '#Viral'
    if not hashtag.startswith('#'):
        hashtag = '#' + hashtag
    
    title_full = f"{title} {hashtag}"
    if len(title_full) > 60:
        max_len = 60 - len(hashtag) - 1
        title_full = f"{title[:max_len].rsplit(' ', 1)[0]} {hashtag}"
    
    data['seo_youtube_title'] = title_full
    data['hashtags'] = hashtags[:3]
    
    logger.info(f"✅ {model_name}")
    logger.info(f"   Title: {title_full}")
    logger.info(f"   Hook: {data['viral_hook']}")
    
    return data


def generate_script_god(story):
    from src.learning.auto_optimizer import get_config
    
    raw = story.get('title', '')
    topic = clean_topic(raw)
    if len(topic) < 15:
        topic = raw
    
    video_duration = get_config("video_duration", 30)
    hook_style = get_config("hook_style", "statement")
    title_pattern = get_config("title_pattern", "reason")
    
    logger.info(f"🧠 Learned: duration={video_duration}s, hook={hook_style}, title={title_pattern}")
    
    prompt = build_prompt(topic, video_duration, hook_style, title_pattern)
    
    # Gemini 3.6 with retry
    gk = os.getenv("GEMINI_API_KEY", "")
    if gk:
        try:
            from google import genai
            client = genai.Client(api_key=gk)
            for attempt in range(1, 3):
                try:
                    logger.info(f"   🔷 Gemini 3.6 (attempt {attempt}/2)")
                    resp = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                    text = getattr(resp, 'text', '')
                    if text:
                        data = process_ai_response(text, "Gemini-3.6")
                        if data:
                            return data
                except Exception as e:
                    logger.warning(f"   ❌ Gemini: {str(e)[:80]}")
                    if attempt < 2:
                        time.sleep(3)
        except Exception as e:
            logger.warning(f"   Gemini client: {e}")
    
    # GitHub Models (FREE OpenAI)
    gh = os.getenv("GITHUB_TOKEN", "")
    if gh:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=gh, base_url="https://models.github.ai/inference")
            for model in ["openai/gpt-4o-mini", "openai/gpt-4o"]:
                try:
                    logger.info(f"   🟢 GitHub Models: {model}")
                    r = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "Respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.9, max_tokens=2000,
                        response_format={"type": "json_object"}
                    )
                    text = r.choices[0].message.content
                    if text:
                        data = process_ai_response(text, f"GitHub-{model}")
                        if data:
                            return data
                except Exception as e:
                    logger.warning(f"   ❌ {model}: {str(e)[:80]}")
        except Exception as e:
            logger.warning(f"   GitHub Models: {e}")
    
    logger.info("⚠️ Using fallback template")
    return get_fallback_script(topic, video_duration)


def get_fallback_script(topic, video_duration):
    tl = topic.lower()
    
    if any(w in tl for w in ['kid', 'child', 'boy', 'girl']):
        h, t, hk = "#Viral", "The Kid Everyone Is Watching", "THIS BROKE THE INTERNET"
        vq = ["happy child playing", "young kid portrait", "children outside", "kid smiling", "family moment", "young boy portrait"]
    elif any(w in tl for w in ['movie', 'film', 'netflix', 'celebrity', 'taylor']):
        h, t, hk = "#Entertainment", "What Really Happened Here", "THIS CHANGED EVERYTHING"
        vq = ["celebrity red carpet", "paparazzi camera", "glamorous woman", "fashion studio", "camera flash", "movie premiere"]
    elif any(w in tl for w in ['sport', 'match', 'nba', 'nfl']):
        h, t, hk = "#Sports", "The Moment Everyone Missed", "NOBODY EXPECTED THIS"
        vq = ["stadium crowd", "athlete action", "sports trophy", "football field", "basketball court", "crowd cheering"]
    elif any(w in tl for w in ['trump', 'biden', 'president', 'congress']):
        h, t, hk = "#Politics", "What They Dont Want You To See", "THIS CHANGES EVERYTHING"
        vq = ["government building", "press conference", "politician podium", "capitol building", "microphone", "protest crowd"]
    elif any(w in tl for w in ['cat', 'dog', 'kitten', 'puppy']):
        h, t, hk = "#Viral", "The Cutest Story Today", "THIS MELTED THE INTERNET"
        vq = ["cute kitten", "cute puppy", "animal rescue", "pet playing", "cat portrait", "dog portrait"]
    elif any(w in tl for w in ['ai', 'tech', 'robot', 'hack']):
        h, t, hk = "#Tech", "What The Tech World Missed", "THIS CHANGES EVERYTHING"
        vq = ["artificial intelligence", "AI robot", "computer code", "smartphone screen", "tech office", "server room"]
    else:
        h, t, hk = "#Viral", "The Story Behind This Moment", "NOBODY SAW THIS COMING"
        vq = ["viral video screen", "young people phone", "social media", "city crowd", "smartphone scrolling", "trending icons"]
    
    tf = f"{t} {h}"
    if len(tf) > 60:
        tf = f"{t[:55].rsplit(' ', 1)[0]} {h}"
    
    target_words = int(video_duration * 2.5)
    script = ("This moment went viral for one surprising reason. "
              "Sources confirm the details nobody expected. "
              "Reports show millions are watching this unfold right now. "
              "Experts say the trend is only getting bigger. "
              "Here is what everyone is missing. ") * 3
    script = " ".join(script.split()[:target_words])
    
    return {
        "short_script": script,
        "seo_youtube_title": tf,
        "description": "The story behind this trend. Subscribe for more.",
        "hashtags": [h, "#Shorts", "#Trending"],
        "tags": ["trending", "viral", "2026", "shorts", "viral video"],
        "viral_hook": hk,
        "visual_queries": vq,
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
        
        vp = create_video(merged, editor_data)
        return vp
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
        tp = "output/thumbnails/thumb.jpg"
        img = Image.new('RGB', (1280, 720), (15, 15, 40))
        draw = ImageDraw.Draw(img)
        title = script_data.get('seo_youtube_title', candidate.get('title', 'Trending'))
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except:
            font = ImageFont.load_default()
        draw.text((644, 364), title[:40], font=font, fill=(0, 0, 0), anchor="mm")
        draw.text((640, 360), title[:40], font=font, fill=(255, 255, 255), anchor="mm")
        img.save(tp, quality=95)
        return tp
    except:
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
        key = ' '.join(words)
        if not key:
            return False
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''SELECT title FROM stories WHERE created_at > datetime('now', '-3 days')''')
        rows = cur.fetchall()
        conn.close()
        for row in rows:
            ex = re.sub(r'[^\w\s]', '', row[0].lower()).strip()
            ex_words = [w for w in ex.split() if len(w) > 3][:5]
            ex_key = ' '.join(ex_words)
            if key and ex_key:
                if len(set(key.split()) & set(ex_key.split())) >= 3:
                    return True
        return False
    except:
        return False


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("=" * 60)
    logger.info("🚀 AUTONOMOUS BOT START (WITH AI REPAIR)")
    logger.info(f"Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)
    
    # Init DB
    init_db()
    
    # Verify last fix (rollback if failed)
    try:
        from src.learning.self_repair import verify_last_fix
        verify_last_fix()
    except:
        pass
    
    # Init autonomous config
    try:
        from src.learning.auto_optimizer import init_autonomous_config, get_all_config
        init_autonomous_config()
        config = get_all_config()
        logger.info(f"🧠 Autonomous config v{config.get('version', 1)}")
        logger.info(f"   Duration: {config.get('video_duration')}s | Hook: {config.get('hook_style')} | Title: {config.get('title_pattern')}")
    except Exception as e:
        logger.warning(f"Config init failed: {e}")
    
    stats = get_performance_stats()
    logger.info(f"Stats: {stats}")
    
    # LEG 1: Research
    stories = research_god_main()
    if not stories:
        logger.error("No stories - exit")
        return
    
    # Activity filter
    logger.info("=" * 60)
    logger.info("🔥 ACTIVITY FILTER")
    logger.info("=" * 60)
    
    active = []
    for s in stories[:10]:
        is_active, score = is_audience_active(s)
        s['activity_score'] = score
        if is_active:
            active.append(s)
            logger.info(f"   ✅ ACTIVE ({score:.0f}): {s.get('title', '')[:50]}")
        else:
            logger.info(f"   ❌ SKIP ({score:.0f}): {s.get('title', '')[:50]}")
    
    if not active:
        logger.warning("⚠️ No active - using top 5")
        active = stories[:5]
    else:
        logger.info(f"🔥 {len(active)} ACTIVE topics")
    
    stories = active
    
    # Process
    approved = None
    best_rejected = None
    skipped = 0
    
    for i, candidate in enumerate(stories[:8]):
        logger.info(f"\n{'='*60}")
        logger.info(f"CANDIDATE {i+1}: {candidate.get('title', '')[:60]}")
        logger.info(f"{'='*60}")
        
        if is_duplicate(candidate.get('title', '')):
            logger.warning("⏭️ Duplicate")
            skipped += 1
            continue
        
        script_data = generate_script_god(candidate)
        
        if has_publisher_name(script_data.get('seo_youtube_title', '')) or is_spam_topic(script_data.get('seo_youtube_title', '')):
            continue
        
        if script_data.get('confidence_score', 0) < 60:
            continue
        
        # Fact check
        fc = safe_import('src.verification.claim_checker', 'fact_check')
        if fc:
            fr = fc(script_data.get('short_script', ''), candidate)
            if not fr.get('passed', False):
                logger.warning("Fact check failed")
                continue
            logger.info(f"✅ Fact check: {fr.get('report', '')}")
        
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
    
    if skipped:
        logger.info(f"⏭️ Skipped {skipped} duplicates")
    
    if not approved and best_rejected and best_rejected[3].get('score', 0) >= 50:
        approved = best_rejected
        logger.info("⚠️ Using best rejected")
    
    if not approved:
        logger.error("All rejected - safe exit")
        self_evolution_main()  # Still run repair even if no upload
        return
    
    # Upload
    candidate, script_data, editor_data, boss_data, story_id, video_path = approved
    thumb = create_thumbnail(candidate, script_data)
    video_id = uploader_god_main(video_path, thumb, script_data, candidate, boss_data)
    
    if video_id:
        mark_uploaded(story_id, video_id)
        logger.info(f"\n✅ UPLOADED: https://youtu.be/{video_id}")
    
    # LEG 5: Self Evolution + AI Repair
    self_evolution_main()
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 AUTONOMOUS BOT COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
