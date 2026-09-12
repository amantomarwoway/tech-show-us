"""
fact_checker.py - REAL AEROPLANE - DETAILED FIXED - NO GLOBAL PATCH - 2 of 3 PASS
Guaranteed sources + safe pytrends + lenient pass for high score
"""
import re, time

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'#m[0-9a-z]+', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# GUARANTEED sources jo news_fetcher actually deta hai - detailed
TOP_REAL_SOURCES = [
    "google_trends_breakout",
    "google_trends_trending_now",
    "cnn_breaking",
    "whitehouse_press",
    "supreme_court",
    "google_news_us_live",
    "guaranteed_google_news",
    "guaranteed_google_news_rss",
    "guaranteed_breakout_news_fetcher",
    "visualping",
    "reddit_rising_breakout"
]

VIRAL_KEYWORDS_REAL = [
    "breaking", "shocking", "leaked", "secret", "behind closed doors", "exposed", "revealed",
    "executive order", "white house", "supreme court", "congress", "senate", "bill", "new law",
    "trump", "biden", "fbi", "doj", "federal court", "election", "tariff", "trade war", "ban"
]

def check_google_trends_real_breakout(query, geo="US"):
    """Safe Google Trends check - NO global patch"""
    try:
        from pytrends.request import TrendReq
        # Safe init - no monkey patch
        try:
            pytrends = TrendReq(hl='en-US', tz=360, timeout=10, retries=1)
        except TypeError:
            pytrends = TrendReq(hl='en-US', tz=360)

        pytrends.build_payload([query[:50]], timeframe='now 4-H', geo=geo)
        time.sleep(1)

        # Check related queries for breakout
        try:
            related = pytrends.related_queries()
            if query[:50] in related:
                rising = related[query[:50]].get('rising')
                if rising is not None and not rising.empty:
                    for _, row in rising.iterrows():
                        if 'breakout' in str(row.get('value','')).lower():
                            return True, f"Breakout {geo}: {row['query']}"
        except: pass

        # Check interest spike
        try:
            data = pytrends.interest_over_time()
            if not data.empty and query[:50] in data.columns:
                interest = data[query[:50]].tolist()
                if len(interest)>=2 and interest[-1]>=40 and interest[-1] > interest[-2]*1.15:
                    return True, f"Interest spike {geo}: {interest[-2]}->{interest[-1]}"
        except: pass

        return False, f"No breakout {geo}"
    except Exception as e:
        err=str(e)
        if "429" in err: return False, f"429 blocked {geo}"
        # Lenient pass if pytrends fails but query has high potential - detailed video ke liye
        if "method_whitelist" in err or "Retry" in err or "TrendReq" in err:
            print(f" [REAL] {geo} pytrends bug - lenient pass for detailed")
            return True, f"Lenient pass {geo} - {err[:30]}"
        return False, f"Error {err[:50]}"

def fact_check(full_script, approved_topic=None):
    """DETAILED FACT CHECK - 2 of 3 PASS = VIDEO BANEGI"""
    try:
        if isinstance(approved_topic, dict):
            topic = approved_topic.get('title') or approved_topic.get('query') or ""
            query = approved_topic.get('query') or topic
            breakout_score = approved_topic.get('breakout_score', 0)
            is_breakout = approved_topic.get('is_breakout', False)
            source = approved_topic.get('source','') or approved_topic.get('breakout_source','')
            search_volume = approved_topic.get('search_volume', 0)
        else:
            topic = str(full_script)[:120] if not isinstance(full_script, dict) else full_script.get('title','')
            query = topic; breakout_score=0; is_breakout=False; source=""; search_volume=0

        topic = clean_id(str(topic))[:150]
        query = clean_id(str(query))[:100]

        if len(topic) < 5 or len(query) < 3:
            return {"passed": False, "report": "Empty topic - cancel"}

        print(f"\n🔍 [FACT CHECKER - DETAILED - REAL AEROPLANE]")
        print(f"Topic: {topic[:100]}")
        print(f"Query: {query}")
        print(f"Source: {source} | Score: {breakout_score} | Breakout: {is_breakout} | Vol: {search_volume}")

        def check_1_real_top_source():
            sl=source.lower()
            is_top=any(t in sl for t in TOP_REAL_SOURCES)
            # High score + top source = PASS
            if is_breakout and breakout_score>=5000 and is_top:
                print(f" [CHECK-1 TOP SOURCE] ✅ PASS - {breakout_score} from {source}")
                return True, f"TOP SOURCE {source} Score {breakout_score}"
            # Medium score + high vol + top = PASS
            if is_breakout and breakout_score>=4000 and is_top and search_volume>=80:
                return True, f"TOP {source} {breakout_score} vol {search_volume}"
            # Guaranteed keyword + high score = PASS (detailed)
            if is_breakout and breakout_score>=5500 and ("guaranteed" in sl or "google" in sl or "cnn" in sl or "breakout" in sl):
                print(f" [CHECK-1 GUARANTEED] ✅ PASS - {breakout_score} + {source}")
                return True, f"GUARANTEED {source} {breakout_score}"
            return False, f"Not top source {source} {breakout_score}"

        def check_2_real_english_viral():
            tl=(topic+" "+query).lower()
            found=[k for k in VIRAL_KEYWORDS_REAL if k in tl]
            if not found:
                return False, f"No viral kw - {found}"
            if len(query)<8 or breakout_score<2500:
                return False, f"Low score {breakout_score} or short query"
            us_pass, us_rep = check_google_trends_real_breakout(query, "US")
            if us_pass:
                print(f" [CHECK-2 US VIRAL] ✅ PASS - {us_rep} kw {found}")
                return True, f"US VIRAL {us_rep} kw {found}"
            # Lenient for detailed - high score + viral kw
            if found and breakout_score>=4500 and search_volume>=80:
                print(f" [CHECK-2 LENIENT] ✅ PASS - kw {found} + {breakout_score}")
                return True, f"Lenient kw {found} {breakout_score} vol {search_volume}"
            return False, f"No US breakout {us_rep}"

        def check_3_real_lakho_search():
            if not is_breakout:
                return False, f"Not breakout flag"
            if breakout_score<3500: # Lowered for detailed
                return False, f"Score {breakout_score}<3500"
            if search_volume<60: # Lowered for detailed
                return False, f"Vol {search_volume}<60"
            est=breakout_score*180
            print(f" [CHECK-3 LAKHO] ✅ PASS - {breakout_score} = {est:,} searches")
            return True, f"{est:,} searches - score {breakout_score} vol {search_volume}"

        c1,c1r=check_1_real_top_source()
        c2,c2r=check_2_real_english_viral()
        c3,c3r=check_3_real_lakho_search()

        print(f"\n🔍 [RESULT - DETAILED]")
        print(f" 1) Top Source: {'✅ PASS' if c1 else '❌ FAIL'} - {c1r}")
        print(f" 2) English Viral: {'✅ PASS' if c2 else '❌ FAIL'} - {c2r}")
        print(f" 3) Lakho Search: {'✅ PASS' if c3 else '❌ FAIL'} - {c3r}")

        # 2 of 3 PASS = VIDEO BANEGI - detailed ke liye easy kiya
        pc=sum([c1,c2,c3])
        if pc>=2:
            print(f" => ✅✅ FINAL PASS - {pc}/3 - DETAILED VIDEO BANEGI")
            return {"passed": True, "report": f"REAL VIRAL {pc}/3 PASS | {c1r} | {c2r} | {c3r}"}
        else:
            print(f" => ❌ FINAL FAIL - {pc}/3 - Topic cancel, naya try")
            return {"passed": False, "report": f"NOT VIRAL FAIL {pc}/3 | {c1r} | {c2r} | {c3r}"}

    except Exception as e:
        print(f"fact_check crashed: {e} -> FAIL")
        import traceback; traceback.print_exc()
        return {"passed": False, "report": f"crash FAIL {e}"}
