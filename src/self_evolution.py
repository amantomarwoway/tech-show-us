import os, json, time, random
from pathlib import Path
DB_PATH="data/database.db"
def get_last_performance():
    try:
        import sqlite3
        if not os.path.exists(DB_PATH): return []
        conn=sqlite3.connect(DB_PATH); c=conn.cursor()
        c.execute("SELECT title, confidence_score, search_potential_score, seo_youtube_title FROM stories ORDER BY timestamp DESC LIMIT 10")
        rows=c.fetchall(); conn.close(); return rows
    except: return []
def analyze_and_evolve():
    print("[LEG5 SELF_EVOLUTION] Analyzing last videos - self improvement - best use everywhere")
    rows=get_last_performance()
    if not rows: return {"evolved":False,"reason":"first run"}
    best=max(rows, key=lambda x: x[1] or 0) if rows else None
    avg_conf=sum(r[1] or 0 for r in rows)/len(rows) if rows else 0
    evolution={"last_check":time.time(),"avg_confidence":avg_conf,"best_title":best[0] if best else "","best_score":best[1] if best else 0,"learning":f"Best: {best[0][:50] if best else 'none'}","next_improvement":"Increase threshold to 35" if avg_conf<80 else "Keep, focus leaked/secret","auto_tune":{"search_potential_min":35 if avg_conf<80 else 30,"confidence_min":80}}
    Path("data").mkdir(exist_ok=True)
    Path("data/evolution.json").write_text(json.dumps(evolution, indent=2))
    print(f"[LEG5] Evolved: Avg {avg_conf:.1f} Best: {best[0][:40] if best else 'none'}")
    return {"evolved":True,"data":evolution}
def self_evolution_main(): return analyze_and_evolve()
