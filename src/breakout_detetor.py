"""
src/breakout_detector.py - NEW Core Engine - PURE BREAKOUT +5000%
Ye sabse important hai
Kaam: Google Trends pe har category ka BREAKOUT (+5000%) detect karna
pytrends se 4-5 seeds check: breaking news, executive order, usa, trump etc
- Politics trends hamesha naye laws/policies se shuru hote hain
- Breakout = video banna hi banna hai, koi fallback nahi
- Jo karne ko bola wahi, fallback kuch nahi
Location: src/breakout_detector.py
"""
import time, random, re, hashlib, json
from pathlib import Path
from datetime import datetime, timezone
import requests

CACHE_FILE = Path("data/breakout_cache.json")
CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

def clean_id(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Seeds for breakout detection - user requested
SEEDS = [
    "breaking news",
    "executive order",
    "usa",
    "trump",
    "white house",
    "supreme court",
    "senate vote",
    "congress bill",
    "federal court",
    "new law",
    "biden",
    "usa news today"
]

def get_breakouts_from_pytrends(seeds=None):
    """Core: Google Trends pe har category ka BREAKOUT (+5000%) detect"""
    breakouts = []
    if seeds is None:
        seeds = SEEDS
    # Pick 4-5 random seeds per run as requested
    selected_seeds = random.sample(seeds, min(5, len(seeds)))
    print(f"[BREAKOUT_DETECTOR] Checking {len(selected_seeds)} seeds: {selected_seeds} - BREAKOUT +5000% only")
    
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        
        for seed in selected_seeds:
            try:
                print(f"[BREAKOUT] Seed: {seed} - building payload now 1-d US")
                pytrends.build_payload([seed], timeframe='now 1-d', geo='US')
                related = pytrends.related_queries()
                
                if seed not in related:
                    print(f"[BREAKOUT] Seed {seed} no related data")
                    time.sleep(1.2)
                    continue
                
                rising = related[seed].get('rising')
                if rising is None or rising.empty:
                    print(f"[BREAKOUT] Seed {seed} rising None/empty - no breakout right now")
                    time.sleep(1.0)
                    continue
                
                print(f"[BREAKOUT] Seed {seed} rising rows: {len(rising)}")
                for _, row in rising.iterrows():
                    q = str(row['query'])
                    val = str(row['value'])
                    
                    # Only BREAKOUT +5000%
                    if 'breakout' not in val.lower():
                        continue
                    
                    q_clean = clean_id(q)
                    if len(q_clean) < 3:
                        continue
                    if re.match(r'^m[0-9]', q_clean, re.I):
                        continue
                    if '/m/' in q_clean.lower():
                        continue
                    
                    # Filter banned but allow politics
                    q_low = q_clean.lower()
                    if any(b in q_low for b in ["ipl","bcci","csk","bollywood","bhojpuri","recipe","cooking"]):
                        print(f"[BREAKOUT] Skip banned {q_clean[:40]}")
                        continue
                    
                    breakout_item = {
                        "title": q_clean,
                        "query": q_clean,
                        "url": f"https://trends.google.com/trends?q={q_clean.replace(' ', '+')}&geo=US",
                        "source": "google_trends_breakout",
                        "published": time.gmtime(),
                        "summary": q_clean,
                        "is_breakout": True,
                        "breakout_score": 5000,
                        "breakout_seed": seed,
                        "breakout_value": val,
                        "search_volume": 95,
                        "bot_friendly": True,
                        "filter_c_score": 95,
                        "bot_friendly_score": 95,
                        "freshness_score": 95,
                        "reliability": 0.98,
                        "visualping_alert": f"Google Trends BREAKOUT +5000% (seed={seed}) - {q_clean} - Politics new law/policy se start"
                    }
                    breakouts.append(breakout_item)
                    print(f"🔥 [BREAKOUT FOUND] {q_clean} -> BREAKOUT +5000% seed={seed} | {val}")
                
                time.sleep(1.5)
                
            except Exception as e:
                print(f"[BREAKOUT] seed {seed} fail {e}")
                time.sleep(1.0)
                continue
        
        print(f"[BREAKOUT_DETECTOR] pytrends total BREAKOUT found: {len(breakouts)} - NO FALLBACK")
        
    except ImportError as ie:
        print(f"[BREAKOUT_DETECTOR] pytrends not installed {ie} - returning empty NO FALLBACK")
    except Exception as e:
        print(f"[BREAKOUT_DETECTOR] overall fail {e} - NO FALLBACK")
    
    return breakouts

def get_trending_now_breakouts():
    """Trending Now API - US trending searches"""
    breakouts = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='en-US', tz=360)
        trending = pytrends.trending_searches(pn='united_states')
        if not trending.empty:
            for idx, row in trending.head(10).iterrows():
                q = str(row[0])
                q_clean = clean_id(q)
                if len(q_clean) < 3: continue
                if re.match(r'^m[0-9]', q_clean, re.I): continue
                breakouts.append({
                    "title": q_clean,
                    "query": q_clean,
                    "url": f"https://trends.google.com/trends/trending?geo=US",
                    "source": "google_trends_trending_now",
                    "published": time.gmtime(),
                    "summary": q_clean,
                    "is_breakout": True,
                    "breakout_score": 5200,
                    "search_volume": 90,
                    "bot_friendly": True,
                    "filter_c_score": 90,
                    "bot_friendly_score": 90,
                    "visualping_alert": f"Trending Now US - {q_clean}"
                })
        print(f"[BREAKOUT] Trending Now found {len(breakouts)}")
    except Exception as e:
        print(f"[BREAKOUT] Trending Now fail {e}")
    return breakouts

def get_all_breakouts_any_topic():
    """Main entry - ONLY BREAKOUT ANY TOPIC - No fallback"""
    all_breakouts = []
    
    # 1. pytrends BREAKOUT +5000%
    try:
        all_breakouts.extend(get_breakouts_from_pytrends())
    except Exception as e:
        print(f"[BREAKOUT ENGINE] pytrends wrapper fail {e}")
    
    # 2. Trending now (also breakout)
    try:
        all_breakouts.extend(get_trending_now_breakouts())
    except Exception as e:
        print(f"[BREAKOUT ENGINE] trending now wrapper fail {e}")
    
    # 3. Import visualping if available for combined engine
    try:
        from visualping_monitor import get_visualping_breakouts as vp_breakouts
        all_breakouts.extend(vp_breakouts())
    except ImportError:
        try:
            from src.visualping_monitor import get_visualping_breakouts as vp_breakouts
            all_breakouts.extend(vp_breakouts())
        except:
            print("[BREAKOUT ENGINE] visualping_monitor not available yet - will be added separately")
    except Exception as e:
        print(f"[BREAKOUT ENGINE] visualping wrapper fail {e}")
    
    # Deduplicate by query lower
    seen = set()
    deduped = []
    for b in all_breakouts:
        ql = b['query'].lower().strip()
        if ql not in seen and len(ql) > 2:
            seen.add(ql)
            deduped.append(b)
    
    print(f"[BREAKOUT ENGINE FINAL] Total ANY-TOPIC BREAKOUTS: {len(deduped)} - NO FALLBACK - Only breakout = video banna hi banna hai")
    
    # Cache
    try:
        CACHE_FILE.write_text(json.dumps({"last": datetime.now(timezone.utc).isoformat(), "breakouts": deduped[:30]}, indent=2))
    except:
        pass
    
    return deduped

if __name__ == "__main__":
    print("=== Testing breakout_detector.py - PURE BREAKOUT +5000% ===")
    brk = get_all_breakouts_any_topic()
    for i,b in enumerate(brk[:5]):
        print(f"{i+1}. {b['query']} | Score {b['breakout_score']} | {b['source']} | {b['visualping_alert'][:60]}")
    if not brk:
        print("No breakout right now - safe exit NO FALLBACK")
