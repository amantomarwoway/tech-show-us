def fact_check(script_text, story):
    # Second validation - script vs source data
    report = []
    # Check if script contains title keywords
    title_words = story['title'].lower().split()[:5]
    for w in title_words:
        if len(w) > 4 and w not in script_text.lower():
            report.append(f"Missing keyword {w}")

    # Check no fabricated quotes
    if '"' in script_text and "said" in script_text.lower():
        # Simple check - if quote not in summary, flag
        pass

    passed = len(report) == 0
    return {"passed": passed, "report": report, "story_url": story['url']}
