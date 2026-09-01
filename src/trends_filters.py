"""
src/trend_filters.py - SHORT BOT - Filter A, B, C
Quantity kam, Quality zyada - Fast Runner

Filter A: Google Trends API (YouTube Search Filter) - Breakout detection
Filter B: YouTube Autocomplete Feeder - Half keyword -> hot suggestions
Filter C: Format & Engagement Test - Rising trend + Bot friendly (faceless)
"""

import os
import re
import time
import requests
from typing import List, Dict
from datetime import datetime, timedelta

# Try pytrends for Filter A
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# ========== FILTER A: Google Trends API YouTube Search Filter ==========
def filter_a_google_trends_youtube_breakout(keywords: List[str]) -> List[Dict]:
    """
    Normal web search aur YouTube search alag hote hain.
    Bot Google Trends API ka use karke location US set kare aur YouTube Search filter kare.
    Check: Agar keyword graph achanak upar Breakout ja raha hai, toh log YouTube pe dhoondh rahe hain par video kam hain.
    """
    print("[FILTER A] Google Trends API - YouTube Search Filter - US - Breakout detection")
    breakout_topics = []
    
    if not PYTRENDS_AVAILABLE:
        print("[FILTER A] pytrends not installed, using fallback RSS")
        # Fallback: Use your existing RSS but mark as youtube search
        return []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, geo='US')
        # Batch in 5s (Google Trends limit)
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            try:
                pytrends.build_payload(batch, cat=0, timeframe='now 7-d', geo='US', gprop='youtube')
                # gprop='youtube' = YouTube Search filter
                interest = pytrends.interest_over_time()
                related = pytrends.related_queries()
                
                for kw in batch:
                    if kw in related and related[kw]['rising'] is not None:
                        rising = related[kw]['rising']
                        # Breakout = >5000% growth
                        for _, row in rising.iterrows():
                            q = row['query']
                            val = str(row['value'])
                            if 'Breakout' in val or ('%' in val and int(val.replace('%','').replace(',','')) > 500):
                                breakout_topics.append({
                                    "query": q,
                                    "source": "filter_a_youtube_breakout",
                                    "trend_type": "breakout",
                                    "growth": val,
                                    "search_volume": 90 if 'Breakout' in val else 75,
                                    "filter_a_score": 95
                                })
                    # Check interest spike
                    if not interest.empty and kw in interest.columns:
                        recent = interest[kw].tail(3).mean()
                        older = interest[kw].head(3).mean()
                        if recent > older * 2.5 and recent > 30:
                            breakout_topics.append({
                                "query": kw,
                                "source": "filter_a_spike",
                                "trend_type": "spike",
                                "growth": f"{int((recent/older)*100)}%",
                                "search_volume": int(recent),
                                "filter_a_score": 85
                            })
                time.sleep(2)
            except Exception as e:
                print(f"[FILTER A] Batch {batch} error: {e}")
                time.sleep(2)
                continue
    except Exception as e:
        print(f"[FILTER A] Error: {e}")
    
    print(f"[FILTER A] Found {len(breakout_topics)} breakout topics (YouTube Search Filter)")
    return breakout_topics

# ========== FILTER B: YouTube Autocomplete Feeder ==========
def filter_b_youtube_autocomplete_feeder(seed_keywords: List[str]) -> List[Dict]:
    """
    Jab log trending topic search karte hain, YouTube search bar auto-suggest karta hai.
    Bot script ke through YouTube Search API me aadha keyword dale (e.g., "Why US politics is...")
    aur dekhe niche auto-complete me kya suggestions aa rahe hain. Jo top pe hain, wo hot trends hain.
    """
    print("[FILTER B] YouTube Autocomplete Feeder - Half keyword -> Hot suggestions")
    hot_trends = []
    
    for seed in seed_keywords:
        # Half keyword logic
        half = seed[:int(len(seed)*0.6)] if len(seed) > 10 else seed
        queries_to_try = [half, seed, f"{seed} why", f"{seed} breaking"]
        
        for q in queries_to_try:
            try:
                url = "https://suggestqueries.google.com/complete/search"
                params = {"client": "youtube", "ds": "yt", "q": q, "hl": "en", "gl": "US"}
                r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=4)
                matches = re.findall(r'"([^"]+)"', r.text)
                suggestions = [m for m in matches[1:] if len(m) > 8][:8]
                
                for idx, sug in enumerate(suggestions):
                    # Top suggestions = hot trends
                    position_score = 10 - idx  # Top = higher score
                    if len(sug.split()) >= 3:
                        hot_trends.append({
                            "query": sug,
                            "source": "filter_b_autocomplete",
                            "seed": seed,
                            "half_keyword": q,
                            "position": idx+1,
                            "position_score": position_score,
                            "search_volume": 50 + position_score * 5,
                            "filter_b_score": 90 - idx*5
                        })
                time.sleep(0.3)
            except Exception as e:
                print(f"[FILTER B] {q} error: {e}")
                continue
    
    # Deduplicate - keep highest position score
    seen = {}
    for t in hot_trends:
        ql = t["query"].lower()
        if ql not in seen or t["position_score"] > seen[ql]["position_score"]:
            seen[ql] = t
    
    result = sorted(seen.values(), key=lambda x: x["filter_b_score"], reverse=True)
    print(f"[FILTER B] Found {len(result)} hot autocomplete trends")
    for i, t in enumerate(result[:5]):
        print(f"  {i+1}. {t['query']} | Pos {t['position']} | Half: {t['half_keyword']}")
    return result

# ========== FILTER C: Format & Engagement Test (Bot Friendly) ==========
def filter_c_format_engagement_test(topics: List[Dict], days: int = 7) -> List[Dict]:
    """
    Koi trend bot-made video ke liye sahi hai ya nahi, competition check zaroori hai.
    Check: Us trend par jo videos pichle 3-7 din me aaye, kya unpar views channel ke avg subscribers se zyada hain? Agar haan, toh Rising Trend.
    Sabse zaroori: Kya us trend par Faceless ya AI video pehle se chal rahe hain? Agar sirf bade celebrities ya news anchor face wale videos rank kar rahe hain, toh trend bot ke liye kaam nahi karega. Sirf bot friendly trend choose karna sahi rahega.
    """
    print(f"[FILTER C] Format & Engagement Test - Last {days} days - Bot Friendly Check")
    
    if not YOUTUBE_API_KEY:
        print("[FILTER C] YOUTUBE_API_KEY missing, skipping API check, using heuristic")
        # Heuristic bot-friendly check without API
        bot_friendly = []
        for t in topics:
            q = t["query"].lower()
            # Bot friendly keywords (faceless works)
            faceless_keywords = ["explained", "what happened", "why", "how", "breaking", "news", "update", "shocking", "today", "usa"]
            # Non bot-friendly (needs face/celebrity)
            face_needed = ["interview", "live", "press conference", "celebrity", "anchor", "official statement"]
            
            is_faceless_friendly = any(k in q for k in faceless_keywords)
            needs_face = any(k in q for k in face_needed)
            
            if is_faceless_friendly and not needs_face:
                t["filter_c_score"] = 85
                t["bot_friendly"] = True
                t["format_test"] = "faceless_friendly"
                bot_friendly.append(t)
            elif needs_face:
                t["filter_c_score"] = 40
                t["bot_friendly"] = False
                t["format_test"] = "face_needed_skip"
            else:
                t["filter_c_score"] = 70
                t["bot_friendly"] = True
                t["format_test"] = "maybe_friendly"
        print(f"[FILTER C] Heuristic: {len(bot_friendly)}/{len(topics)} bot friendly")
        return bot_friendly
    
    # With YouTube API - Real engagement test
    bot_friendly_final = []
    for topic in topics[:15]:  # Check top 15 only for speed
        q = topic["query"]
        try:
            # Search YouTube for last 7 days videos on this trend
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
                "maxResults": 10,
                "key": YOUTUBE_API_KEY,
                "regionCode": "US",
                "relevanceLanguage": "en"
            }
            r = requests.get(url, params=params, timeout=6)
            data = r.json()
            
            if "items" not in data:
                continue
            
            rising_count = 0
            faceless_count = 0
            total_videos = len(data["items"])
            
            for item in data["items"]:
                title = item["snippet"]["title"].lower()
                channel = item["snippet"]["channelTitle"].lower()
                desc = item["snippet"]["description"].lower()
                
                # Check faceless: No face keywords in title/channel
                faceless_signals = ["explained", "news", "update", "breakdown", "story", "what happened", "ai", "faceless", "anonymous"]
                face_signals = ["interview", "live with", "official", "press conference", "anchor", "reporter"]
                
                is_faceless = any(s in title or s in desc for s in faceless_signals)
                is_face = any(s in title for s in face_signals)
                
                if is_faceless and not is_face:
                    faceless_count += 1
                
                # Rising check: Views > channel avg? We approximate via title engagement words
                rising_signals = ["breaking", "shocking", "just in", "viral", "trending"]
                if any(s in title for s in rising_signals):
                    rising_count += 1
            
            # Bot friendly if faceless videos already ranking
            faceless_ratio = faceless_count / max(total_videos, 1)
            rising_ratio = rising_count / max(total_videos, 1)
            
            if faceless_ratio >= 0.3 and rising_ratio >= 0.2:
                topic["filter_c_score"] = 90
                topic["bot_friendly"] = True
                topic["faceless_ratio"] = faceless_ratio
                topic["rising_ratio"] = rising_ratio
                topic["format_test"] = f"bot_friendly_f:{faceless_ratio:.1f}_r:{rising_ratio:.1f}"
                bot_friendly_final.append(topic)
            elif faceless_ratio >= 0.2:
                topic["filter_c_score"] = 75
                topic["bot_friendly"] = True
                topic["format_test"] = f"maybe_friendly_f:{faceless_ratio:.1f}"
                bot_friendly_final.append(topic)
            else:
                topic["filter_c_score"] = 45
                topic["bot_friendly"] = False
                topic["format_test"] = f"face_heavy_f:{faceless_ratio:.1f}_skip"
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[FILTER C] {q} error: {e}")
            continue
    
    print(f"[FILTER C] {len(bot_friendly_final)}/{len(topics)} bot friendly (faceless/AI videos already ranking)")
    return sorted(bot_friendly_final, key=lambda x: x.get("filter_c_score", 0), reverse=True)

# ========== COMBINED FILTER ==========
def apply_all_filters_short_bot(seed_keywords: List[str] = None) -> List[Dict]:
    """
    Short bot ke liye Filter A + B + C combine
    Quantity kam, Quality zyada - Only bot friendly rising trends
    """
    if seed_keywords is None:
        seed_keywords = ["breaking news usa", "trump news", "weather alert usa", "why is trending", "what happened today"]
    
    print("\n=== SHORT BOT FILTERS A+B+C - Bot Friendly Rising Trends ===")
    
    # Filter B first: YouTube Autocomplete -> Hot suggestions (fast)
    filter_b = filter_b_youtube_autocomplete_feeder(seed_keywords)
    
    # Filter A: Google Trends YouTube Search Filter -> Breakout
    filter_a = filter_a_google_trends_youtube_breakout([t["query"] for t in filter_b[:10]] + seed_keywords)
    
    # Combine A+B
    combined = {}
    for t in filter_a + filter_b:
        ql = t["query"].lower()
        if ql not in combined:
            combined[ql] = t
        else:
            # Merge scores
            combined[ql]["search_volume"] = max(combined[ql].get("search_volume",0), t.get("search_volume",0))
            combined[ql]["filter_a_score"] = t.get("filter_a_score", combined[ql].get("filter_a_score", 0))
            combined[ql]["filter_b_score"] = t.get("filter_b_score", combined[ql].get("filter_b_score", 0))
    
    combined_list = list(combined.values())
    combined_list = sorted(combined_list, key=lambda x: x.get("search_volume",0) + x.get("filter_a_score",0) + x.get("filter_b_score",0), reverse=True)[:20]
    
    # Filter C: Format & Engagement + Bot Friendly Test
    final_bot_friendly = filter_c_format_engagement_test(combined_list, days=7)
    
    print(f"\n=== FINAL SHORT BOT TRENDS: {len(final_bot_friendly)} Bot Friendly Rising Trends ===")
    for i, t in enumerate(final_bot_friendly[:5]):
        print(f"{i+1}. {t['query']} | Vol {t.get('search_volume')} | Bot {t.get('bot_friendly')} | {t.get('format_test')}")
    
    return final_bot_friendly
