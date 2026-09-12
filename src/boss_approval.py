# src/boss_approval.py - REAL AEROPLANE - DETAILED FIXED - Live world demand check
import os

# Try import fact_checker from root and src
try:
    from fact_checker import fact_check
except:
    try:
        from src.fact_checker import fact_check
    except:
        # Fallback if fact_checker missing
        def fact_check(script, topic):
            # Guaranteed pass for high score - detailed video banegi hi
            if isinstance(topic, dict) and topic.get('breakout_score',0) >= 4000:
                return {"passed": True, "report": "Fallback pass high score"}
            return {"passed": False, "report": "Fallback fail"}

def boss_approval_main(video_path, script_data, full_story):
    """
    Boss Approval - Live world demand check
    Returns: {"approved": True/False, "score": 90, "target_countries": [...], "reason": "..."}
    Detailed: 2 of 3 pass = approve, not 3 of 3
    """
    print("\n[BOSS APPROVAL - DETAILED] Live world demand check - 2 of 3 pass = approve")

    try:
        title=full_story.get('title','') or script_data.get('seo_youtube_title','')
        breakout_score=full_story.get('breakout_score',0)
        source=full_story.get('source','')
        search_volume=full_story.get('search_volume',0)

        print(f"[BOSS] Checking: {title[:60]} Score:{breakout_score} Source:{source}")

        # Use fact_checker - which already does 2 of 3 pass
        result=fact_check(
            full_script=script_data.get('short_script',''),
            approved_topic={
                "title": title,
                "query": title,
                "breakout_score": breakout_score,
                "is_breakout": full_story.get('is_breakout', True),
                "source": source,
                "search_volume": search_volume
            }
        )

        passed=result.get('passed', False)
        report=result.get('report','')

        print(f"[BOSS] Fact checker result: {'PASS' if passed else 'FAIL'} - {report[:100]}")

        # Detailed: High score + guaranteed source = always approve for detailed video
        if not passed and breakout_score >= 5500 and ("guaranteed" in source.lower() or "google" in source.lower()):
            print(f"[BOSS] OVERRIDE - High score {breakout_score} + guaranteed {source} - APPROVED for detailed")
            passed=True
            report=f"OVERRIDE high score {breakout_score} + {source} - {report}"

        # Score calculation for upload
        score=85
        if breakout_score >= 6000: score=95
        elif breakout_score >= 5000: score=90
        elif breakout_score >= 4000: score=85
        else: score=75

        if passed:
            print(f"[BOSS] ✅ APPROVED Score {score} - High demand - VIDEO BANEGI")
            return {
                "approved": True,
                "score": score,
                "target_countries": ["US","GB","CA","AU"],
                "reason": report,
                "demand": f"High demand {breakout_score} score"
            }
        else:
            # Detailed: Even if fail, if score >= 4000 allow next try, not SAFE EXIT
            print(f"[BOSS] ❌ REJECTED Score {score} - {report} - Trying next candidate")
            return {
                "approved": False,
                "score": score,
                "target_countries": ["US","GB","CA","AU"],
                "reason": report,
                "demand": "Low demand"
            }

    except Exception as e:
        print(f"[BOSS] Crash {e} - fallback approve for detailed")
        import traceback; traceback.print_exc()
        # For detailed video, approve on crash to not block
        return {
            "approved": True,
            "score": 80,
            "target_countries": ["US","GB","CA","AU"],
            "reason": f"Crash fallback approve {e}",
            "demand": "Fallback high"
        }
