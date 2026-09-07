"""
LIVE VIRAL HASHTAG - RETENTION + SECRET LEAK + VALIDATION FACTORY BOOST
Location: src/live_viral_hashtag.py
Edits: Leaked/behind closed doors/title boost + first to know + anti-bot - old preserved
"""
import requests, re, random, time

# NEW: Validation factory boost for title/hashtags
LEAK_TITLE_BOOSTERS = ["Leaked", "Secret Leak", "Behind Closed Doors", "Just Leaked", "Exposed"]
FIRST_TO_KNOW_PHRASES = ["First to Know", "You Need to Know", "Breaking"]

def get_google_searchable_title(topic: str) -> str:
    """
    F ka Fix + RETENTION: Google searchable viral title + secret leak boost
    """
    base_title = topic.title()[:95]
    try:
        # Anti-bot random UA
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
        ])
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":ua})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 5]
        if suggestions:
            # Random pick not always first - anti-bot
            title = random.choice(suggestions[:3])
            if len(title) < 10:
                title = topic.title() + " " + title
            
            # NEW: Add secret leak angle to title for validation factory + market hungerness
            # 70% chance add leak booster for CTR
            if random.random() < 0.7:
                booster = random.choice(LEAK_TITLE_BOOSTERS)
                if booster.lower() not in title.lower():
                    # Append booster if space
                    if len(title) < 75:
                        title = f"{title} {booster}"
            
            print(f"[GOOGLE TITLE F+RETENTION] Topic: {topic} -> Searchable Title: {title} (leak boost)")
            return title[:95].title()
    except Exception as e:
        print(f"[GOOGLE TITLE F] Fail: {e}")

    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"firefox","q":topic,"hl":"en","gl":"us"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        data = r.json()
        if len(data) > 1 and data[1]:
            title = data[1][0]
            if len(title) > 5:
                # Leak boost
                if random.random() < 0.6 and len(title)<75:
                    title = f"{title} {random.choice(LEAK_TITLE_BOOSTERS)}"
                print(f"[GOOGLE TITLE F] Firefox suggest -> {title} (leak boost)")
                return title[:95].title()
    except Exception as e:
        print(f"[GOOGLE TITLE F] Firefox fail: {e}")

    # Fallback with leak booster
    if random.random() < 0.5:
        base_title = f"{topic.title()[:70]} {random.choice(LEAK_TITLE_BOOSTERS)}"
    return base_title[:95]

def get_topic_hashtags_from_google(topic: str):
    """
    D,H,J ka Fix + RETENTION: Google se 4 precise hashtags + leak tags mandatory
    """
    hashtags = []
    try:
        ua = random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        ])
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":ua})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 3][:12] # 10 se 12 for variation

        for sug in suggestions:
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', sug).lower().strip()
            words = clean.split()
            if not words:
                continue
            if len(words) >= 2:
                tag = "#" + "".join(words[:2])
            else:
                tag = "#" + words[0]
            tag = tag[:20]
            if tag not in hashtags and len(tag) > 3:
                hashtags.append(tag)
            if len(hashtags) >= 3: # 3 only, 1 reserved for leak tag
                break
        print(f"[GOOGLE HASHTAGS D,H,J+RETENTION] Topic: {topic} -> {hashtags}")
    except Exception as e:
        print(f"[GOOGLE HASHTAGS D,H,J] Fail: {e}")

    # Fill from topic
    if len(hashtags) < 3:
        try:
            words = re.findall(r'\w+', topic.lower())
            for w in words:
                if len(w) > 2:
                    tag = "#" + re.sub(r'[^a-z0-9]', '', w)
                    if tag not in hashtags and len(tag) > 3:
                        hashtags.append(tag)
                if len(hashtags) >= 3:
                    break
        except:
            pass

    # NEW: 1 mandatory leak/secret hashtag for validation factory + market hungerness
    leak_hashtags = ["#leaked", "#secretleak", "#behindcloseddoors", "#exposed", "#justleaked"]
    # Pick one that not already in list
    for lh in leak_hashtags:
        if lh not in hashtags:
            hashtags.append(lh)
            break
    
    while len(hashtags) < 4:
        hashtags.append("#usa")

    # Anti-bot shuffle but keep leak tag at end for visibility
    if len(hashtags)>=4:
        main = hashtags[:3]
        random.shuffle(main)
        hashtags = main + [hashtags[3]]

    return hashtags[:4]

def get_world_viral_hashtag():
    """
    F ka Fix - World ka No.1 viral hashtag + leak boost for validation
    """
    # Try Google Trends first
    try:
        import feedparser
        feed = feedparser.parse("https://trends.google.com/trending/rss?geo=US")
        if feed.entries:
            title = feed.entries[0].title
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                # 50% chance return leak variant for market hungerness
                if random.random() < 0.3:
                    tag = random.choice(["#leaked", "#breakingnews", "#secretleak", "#exposed"])
                print(f"[WORLD VIRAL F+RETENTION] Google Trends US -> {title} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL F] Trends fail: {e}")

    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":" ","hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        if len(matches) > 1:
            viral_query = matches[1]
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', viral_query).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                if random.random() < 0.3:
                    tag = random.choice(["#leaked", "#breakingnews"])
                print(f"[WORLD VIRAL F] YT viral search -> {viral_query} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL F] YT suggest fail: {e}")

    try:
        r = requests.get("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", timeout=6)
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
        if len(titles) >= 2:
            viral_title = titles[1]
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', viral_title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                print(f"[WORLD VIRAL F] Google News -> {viral_title} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL F] News fail: {e}")

    # Fallback with leak bias for retention
    return random.choice(["#breakingnews", "#leaked", "#secretleak", "#usa"])

def get_live_viral_hashtag():
    """Backward compat - F + D,H,J combined + retention"""
    return get_world_viral_hashtag()

def get_google_structured_script(topic: str) -> dict:
    """GOOGLE DIRECT - Proper structured script + RETENTION 40w + leak angle"""
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m)>5][:5]
        google_context = " ".join(suggestions) if suggestions else topic
        # UPDATED HOOK: Secret leak + behind closed doors + first to know
        hook = f"{topic.title()} just leaked behind closed doors - this changes everything."
        news = f"WHAT HAPPENED: Inside sources reveal {topic} - {google_context[:80]}. Leaked documents show huge move."
        context = f"WHY IT MATTERS: First to know effect - why America is shocked by {topic}. You won't believe what's next."
        cta = f"First to know? Comment what you think about {topic} leaked."
        full = f"{hook} {news} {context} {cta}"
        # Trim to ~40 words target
        words = full.split()
        if len(words) > 45:
            full = " ".join(words[:40])
        return {"hook": hook, "news": news, "context": context, "cta": cta, "full": full[:600]}
    except:
        return {"hook": f"{topic.title()} just leaked behind closed doors - shocking.", "news": f"WHAT HAPPENED: Breaking leaked in {topic}.", "context": f"WHY IT MATTERS: First to know - why USA cares. This changes everything.", "cta": f"Comment below - first to know?", "full": f"{topic.title()} just leaked behind closed doors and changes everything. Inside sources reveal shocking truth. First to know effect is huge."}

def get_validation_factory_title(topic: str) -> str:
    """NEW: Title with mandatory validation keywords"""
    base = get_google_searchable_title(topic)
    # Ensure leak + behind closed doors in title
    if "leak" not in base.lower():
        base = f"{base} Leaked"
    return base[:95]

def get_market_hungry_hashtags(topic: str):
    """NEW: Market hungerness hashtags"""
    base = get_topic_hashtags_from_google(topic)
    hungry = ["#leaked", "#secret", "#breaking", "#exposed"]
    # Ensure at least 2 hungry tags
    for h in hungry:
        if h not in base and len(base)<6:
            base.append(h)
    return base[:6]
