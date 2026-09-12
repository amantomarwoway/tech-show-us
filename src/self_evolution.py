# src/self_evolution.py - REAL AEROPLANE - DETAILED FIXED - Self Evolution - Khud seekhe
import os, sqlite3, json
from datetime import datetime

DB_PATH = "data/god_bot.db"

def self_evolution_main():
    """
    Self Evolution - kaunsi video viral hui, kaunsi nahi - khud seekhe
    Detailed: Retention power badhane ke liye learning
    """
    print("\n[SELF EVOLUTION - DETAILED] Starting - Khud seekhe retention power")

    try:
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DB_PATH):
            print(f"[EVOLUTION] No DB yet {DB_PATH} - first run")
            return {"learned": "First run - no data yet", "score": 0}

        conn=sqlite3.connect(DB_PATH)
        c=conn.cursor()

        # Get recent uploaded vs not uploaded
        try:
            c.execute("SELECT title, breakout_score, uploaded, search_volume FROM stories ORDER BY id DESC LIMIT 20")
            rows=c.fetchall()
        except:
            rows=[]

        if not rows:
            print("[EVOLUTION] No stories yet")
            conn.close()
            return {"learned": "No stories", "score": 0}

        # Analyze
        uploaded=[r for r in rows if r[2]==1]
        not_uploaded=[r for r in rows if r[2]==0]

        avg_score_uploaded = sum([r[1] for r in uploaded])/len(uploaded) if uploaded else 0
        avg_score_all = sum([r[1] for r in rows])/len(rows) if rows else 0

        # Learn viral keywords - detailed
        viral_keywords={}
        for r in rows:
            title=(r[0] or "").lower()
            for kw in ["white house","shocking","brutal","leaked","tariff","supreme court","breaking","secret"]:
                if kw in title:
                    viral_keywords[kw]=viral_keywords.get(kw,0)+1

        top_kw=sorted(viral_keywords.items(), key=lambda x: x[1], reverse=True)[:3]

        print(f"[EVOLUTION] Total: {len(rows)} Uploaded: {len(uploaded)} Avg score uploaded: {avg_score_uploaded:.0f} vs all {avg_score_all:.0f}")
        print(f"[EVOLUTION] Top viral keywords: {top_kw}")

        # Save learning
        learned={
            "total_stories": len(rows),
            "uploaded_count": len(uploaded),
            "avg_score_uploaded": avg_score_uploaded,
            "avg_score_all": avg_score_all,
            "top_keywords": top_kw,
            "retention_tip": "First 2 words SHOCKING BRUTAL, 0.8s density, 1.11X speed, wait till end hook"
        }

        try:
            c.execute("INSERT INTO evolution (learned, score) VALUES (?,?)", (json.dumps(learned), int(avg_score_uploaded)))
            conn.commit()
        except Exception as e:
            print(f"[EVOLUTION] Save learning fail {e}")

        conn.close()

        print(f"[EVOLUTION] ✅ Learned: {learned} - detailed retention power")

        return learned

    except Exception as e:
        print(f"[EVOLUTION] Crash {e} - skip")
        import traceback; traceback.print_exc()
        return {"learned": f"Crash {e}", "score": 0}
