# src/self_evolution.py - MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - DETAILED FIXED
# Khud seekhe retention power - Automated-Shorts-Generator + VUZA + MuckScraper

import os, json, time, sqlite3, random

DB_PATH = "data/database.db"

def self_evolution_main():
    """
    Self evolution - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE
    Har leg se seekhe - bina paid API ke
    """
    print("\n[SELF EVOLUTION - MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE]")
    print("Instruction: Har leg har cheez kahin se bhi best tarike se use kare")

    try:
        from src.database import get_retention_performance, get_validation_factory_stats, get_search_velocity_stats

        # Get stats
        try:
            rows = get_retention_performance(limit=30)
        except Exception as e:
            print(f"[EVOLUTION] get_retention_performance fail {e}")
            rows = []

        try:
            factory_stats = get_validation_factory_stats()
        except:
            factory_stats = {"total":0}

        try:
            velocity_stats = get_search_velocity_stats()
        except:
            velocity_stats = {"search_trend_count":0}

        print(f"[EVOLUTION] Total stories: {factory_stats.get('total',0)} | Trend: {factory_stats.get('search_trend',0)}")
        print(f"[EVOLUTION] Velocity: {velocity_stats.get('search_trend_count',0)}")

        # Analyze - MUCKSCRAPER + HOOK + VUZA
        muck_sources = {}
        hook_scores = {}
        vuza_success = 0
        total_success = 0

        for row in rows:
            try:
                # row format: id, title, words, duration, fps, tts_speed, validation_pass, market_hungry, yt_id, is_trend, confidence, seo_title, grouped_topic, muckscraper_source, hook, vuza_offline
                title = row[1] if len(row) > 1 else ""
                grouped_topic = row[12] if len(row) > 12 else ""
                actual_source = row[13] if len(row) > 13 else ""
                hook = row[14] if len(row) > 14 else ""
                vuza_offline = row[15] if len(row) > 15 else 0

                # FIXED line 112 - IndentationError fix - proper block
                if actual_source:
                    muck_sources[actual_source] = muck_sources.get(actual_source, 0) + 1
                    print(f" [MUCKSCRAPER] Source: {actual_source[:30]} count {muck_sources[actual_source]}")
                else:
                    # No source - VUZA offline case
                    muck_sources["vuza_offline"] = muck_sources.get("vuza_offline", 0) + 1

                if hook:
                    hook_key = hook[:20].upper()
                    hook_scores[hook_key] = hook_scores.get(hook_key, 0) + 1

                if vuza_offline:
                    vuza_success += 1
                    print(f" [VUZA OFFLINE] 100% FREE success - Hook: {hook[:20] if hook else 'N/A'}")

                total_success += 1

            except Exception as e:
                print(f"[EVOLUTION] Row parse fail {e} - skipping")
                continue

        # Learn best MuckScraper source
        best_muck = "muckscraper_reuters_live"
        if muck_sources:
            try:
                best_muck = max(muck_sources, key=muck_sources.get)
                print(f"[EVOLUTION] Best MuckScraper source: {best_muck} - {muck_sources[best_muck]} videos")
            except:
                best_muck = "muckscraper_reuters_live"

        # Learn best Hook
        best_hook = "SHOCKING LEAK"
        if hook_scores:
            try:
                best_hook = max(hook_scores, key=hook_scores.get)
                print(f"[EVOLUTION] Best Hook: {best_hook} - {hook_scores[best_hook]} videos")
            except:
                best_hook = "SHOCKING LEAK"

        # VUZA OFFLINE ratio
        vuza_ratio = (vuza_success / max(total_success,1)) * 100
        print(f"[EVOLUTION] VUZA OFFLINE ratio: {vuza_ratio:.1f}% - {vuza_success}/{total_success} - 100% FREE")

        # Save evolution
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS evolution
                         (id INTEGER PRIMARY KEY, learned TEXT, score INTEGER, source TEXT, hook TEXT, timestamp REAL)""")
            evolution_data = {
                "best_muckscraper_source": best_muck,
                "best_hook": best_hook,
                "muck_sources": muck_sources,
                "hook_scores": hook_scores,
                "vuza_success": vuza_success,
                "vuza_ratio": vuza_ratio,
                "total": total_success,
                "timestamp": time.time()
            }
            c.execute("INSERT INTO evolution (learned, score, source, hook, timestamp) VALUES (?,?,?,?,?)",
                      (json.dumps(evolution_data), int(vuza_ratio), best_muck, best_hook, time.time()))
            conn.commit()
            conn.close()
            print(f"[EVOLUTION] Saved evolution - MUCKSCRAPER + HOOK + VUZA")
        except Exception as e:
            print(f"[EVOLUTION] Save fail {e} - trying simple")
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS evolution (id INTEGER PRIMARY KEY, learned TEXT, score INTEGER, source TEXT, hook TEXT, timestamp REAL)")
                c.execute("INSERT INTO evolution (learned, score, source, hook, timestamp) VALUES (?,?,?,?,?)",
                          (f"muck:{best_muck} hook:{best_hook} vuza:{vuza_ratio}%", int(vuza_ratio), best_muck, best_hook, time.time()))
                conn.commit()
                conn.close()
            except Exception as e2:
                print(f"[EVOLUTION] Final save fail {e2}")

        # Return evolution summary - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE
        result = {
            "best_muckscraper_source": best_muck,
            "best_hook": best_hook,
            "vuza_offline_ratio": vuza_ratio,
            "vuza_success": vuza_success,
            "total_videos": total_success,
            "muck_sources": muck_sources,
            "evolution": "MUCKSCRAPER + OLLAMA + HOOK/RETAIN/REWARD + VUZA OFFLINE - 100% FREE - Khud seekhe retention power",
            "retention_rules": [
                "1. First 2 words SHOCKING BRUTAL - Hook 0-3s pattern interrupt",
                "2. 0.8s clip density - fast cuts American audience - VUZA style",
                "3. 1.11X speed + echo + 1.6X punch first 5 words - retention",
                "4. Wait till end hook + This affects you + Comment bait - Reward",
                "5. End tak rokne ki takat - detailed video 11-15 sec - Hook/Retain/Reward",
                "6. 100% FREE OFFLINE - Ollama + VUZA - no Pexels/Pixabay key needed"
            ]
        }

        print(f"\n[EVOLUTION DONE] {result}")
        return result

    except Exception as e:
        print(f"[SELF EVOLUTION] Crash {e} - MUCKSCRAPER + VUZA OFFLINE fallback")
        import traceback
        traceback.print_exc()
        return {
            "best_muckscraper_source": "muckscraper_reuters_live",
            "best_hook": "SHOCKING LEAK",
            "vuza_offline_ratio": 100.0,
            "total_videos": 0,
            "error": str(e),
            "evolution": "fallback - 100% FREE - VUZA OFFLINE"
        }

if __name__ == "__main__":
    self_evolution_main()
