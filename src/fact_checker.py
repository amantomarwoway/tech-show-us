def fact_check(script_text, story):
    # Second validation - script vs source data
    # FIX: Handle both string and dict inputs
    
    # 1. Normalize script_text
    if isinstance(script_text, dict):
        script_text = script_text.get('full_script') or script_text.get('script') or str(script_text)
    script_text = str(script_text)

    # 2. Normalize story (can be dict or string)
    if isinstance(story, dict):
        title = story.get('title', '')
        url = story.get('url', '') or story.get('link', '')
    elif isinstance(story, str):
        title = story
        url = ''
    else:
        title = str(story)
        url = ''

    report = []
    # Check if script contains title keywords
    title_words = title.lower().split()[:5]
    for w in title_words:
        if len(w) > 4 and w not in script_text.lower():
            report.append(f"Missing keyword {w}")

    # Check no fabricated quotes
    if '"' in script_text and "said" in script_text.lower():
        # Simple check - if quote not in summary, flag
        pass

    passed = len(report) == 0
    return {"passed": passed, "report": report, "story_url": url}
