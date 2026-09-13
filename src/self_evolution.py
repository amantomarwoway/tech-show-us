# src/self_evolution.py - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - DETAILED FIXED
import os, sqlite3, json
from datetime import datetime

DB_PATH = "data/god_bot.db"

def self_evolution_main():
    """
    Self Evolution - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - Khud seekhe
    Detailed: kaunsi video viral hui, kaunsa hook chala, kaunsa MuckScraper source best, VUZA offline kitna chala
    Retention power badhane ke liye learning
    """
    print("\n[SELF EVOLUTION - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - DETAILED] Starting - Khud seekhe retention power")

    try:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DB_PATH):
            print(f"[EVOLUTION] No DB yet {DB_PATH} - first run - MUCKSCRAPER + VUZA")
            return {"learned": "First run - no data yet - MUCKSCRAPER + VUZA offline ready", "score": 0}

        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()

        # Get recent - with MuckScraper + Hook/Retain/Reward + VUZA columns - migration safe
        rows=[]
        try:
            # Try new columns first
            c.execute("""
                SELECT title, breakout_score, uploaded, search_volume,
                       hook, retain, reward, source, muckscraper_source,
                       vuza_offline, grouped_topic
                FROM stories ORDER BY id DESC LIMIT 30
            """)
            rows=c.fetchall()
        except Exception as e:
            # Fallback old schema
            try:
                c.execute("SELECT title, breakout_score, uploaded, search_volume FROM stories ORDER BY id DESC LIMIT 30")
                old_rows=c.fetchall()
                # Convert to new format
                rows=[(r[0], r[1], r[2], r[3], "", "", "", "", "", 0, "") for r in old_rows]
            except Exception as e2:
                print(f"[EVOLUTION] Old schema also fail {e2}")
                rows=[]

        if not rows:
            print("[EVOLUTION] No stories yet - MUCKSCRAPER + VUZA first run")
            conn.close()
            return {"learned": "No stories - MUCKSCRAPER + VUZA ready", "score": 0}

        # Analyze - MuckScraper + Hook/Retain/Reward + VUZA
        uploaded=[r for r in rows if len(r)>2 and r[2]==1]
        not_uploaded=[r for r in rows if len(r)>2 and r[2]==0]

        avg_score_uploaded = sum([r[1] for r in uploaded])/len(uploaded) if uploaded else 0
        avg_score_all = sum([r[1] for r in rows])/len(rows) if rows else 0

        # ===== HOOK/RETAIN/REWARD LEARNING - Automated-Shorts-Generator =====
        hook_performance={}
        retain_performance={}
        reward_performance={}
        top_hooks_uploaded=[]

        for r in rows:
            try:
                title = (r[0] or "").lower()
                score = r[1] or 0
                is_uploaded = r[2]==1 if len(r)>2 else False
                hook = (r[4] or "") if len(r)>4 else ""
                retain = (r[5] or "") if len(r)>5 else ""
                reward = (r[6] or "") if len(r)>6 else ""

                # Hook performance
                if hook:
                    hook_lower = hook.lower()
                    for kw in ["shocking", "brutal", "breaking", "leaked", "white house", "secret"]:
                        if kw in hook_lower:
                            if kw not in hook_performance:
                                hook_performance[kw]= {"count":0, "uploaded":0, "avg_score":0, "scores":[]}
                            hook_performance[kw]["count"]+=1
                            hook_performance[kw]["scores"].append(score)
                            if is_uploaded:
                                hook_performance[kw]["uploaded"]+=1
                                top_hooks_uploaded.append(hook)

                # Viral keywords from title
                for kw in ["white house","shocking","brutal","leaked","tariff","supreme court","breaking","secret","muckscraper","vuza"]:
                    if kw in title:
                        if kw not in retain_performance:
                            retain_performance[kw]=0
                        retain_performance[kw]+=1
            except:
                continue

        # Avg scores for hooks
        for kw in hook_performance:
            scores = hook_performance[kw]["scores"]
            hook_performance[kw]["avg_score"] = sum(scores)/len(scores) if scores else 0
            del hook_performance[kw]["scores"]

        top_hooks = sorted(hook_performance.items(), key=lambda x: x[1]["avg_score"], reverse=True)[:3]
        top_kw = sorted(retain_performance.items(), key=lambda x: x[1], reverse=True)[:5]

        # ===== MUCKSCRAPER LEARNING =====
        muckscraper_stats={}
        for r in rows:
            try:
                source = (r[7] or "") if len(r)>7 else ""
                muck_source = (r[8] or "") if len(r)>8 else ""
                grouped = (r[10] or "") if len(r)>10 else ""
                actual_source = muck_source or source
                if actual_source:
