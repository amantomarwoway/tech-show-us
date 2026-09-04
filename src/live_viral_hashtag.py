import requests, re

def get_google_searchable_title(topic: str) -> str:
    """
    F ka Fix - Google se searchable viral title
    YouTube suggest API se jo sabse zyada search ho raha hai
    """
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 5]
        if suggestions:
            title = suggestions[0]
            if len(title) < 10:
                title = topic.title() + " " + title
            print(f"[GOOGLE TITLE F] Topic: {topic} -> Searchable Title: {title}")
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
                print(f"[GOOGLE TITLE F] Firefox suggest -> {title}")
                return title[:95].title()
    except Exception as e:
        print(f"[GOOGLE TITLE F] Firefox fail: {e}")

    return topic.title()[:95]

def get_topic_hashtags_from_google(topic: str):
    """
    D,H,J ka Fix - Google se 4 precise hashtags jo topic se related ho
    """
    hashtags = []
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 3][:10]

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
            if len(hashtags) >= 4:
                break
        print(f"[GOOGLE HASHTAGS D,H,J] Topic: {topic} -> {hashtags}")
    except Exception as e:
        print(f"[GOOGLE HASHTAGS D,H,J] Fail: {e}")

    if len(hashtags) < 4:
        try:
            words = re.findall(r'\w+', topic.lower())
            for w in words:
                if len(w) > 2:
                    tag = "#" + re.sub(r'[^a-z0-9]', '', w)
                    if tag not in hashtags and len(tag) > 3:
                        hashtags.append(tag)
                if len(hashtags) >= 4:
                    break
        except:
            pass

    while len(hashtags) < 4:
        hashtags.append("#usa")

    return hashtags[:4]

def get_world_viral_hashtag():
    """
    F ka Fix - World ka No.1 viral hashtag - Google se
    """
    try:
        import feedparser
        feed = feedparser.parse("https://trends.google.com/trending/rss?geo=US")
        if feed.entries:
            title = feed.entries[0].title
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                print(f"[WORLD VIRAL F] Google Trends US -> {title} -> {tag}")
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

    return "#breakingnews"

def get_live_viral_hashtag():
    """Backward compat - F + D,H,J combined"""
    return get_world_viral_hashtag()

def get_google_structured_script(topic: str) -> dict:
    """GOOGLE DIRECT - Proper structured script"""
    try:
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m)>5][:5]
        google_context = " ".join(suggestions) if suggestions else topic
        # --- ADD-ON D,H,J - Fixed Hook ---
        hook = f"The White House is panicking - {topic.title()} just shocked America."
        news = f"WHAT HAPPENED: Here's what happened in {topic} - {google_context[:100]}. This is breaking right now."
        context = f"WHY IT MATTERS: Wait, here's the crazy part - why America is talking about {topic}. This changes everything for USA."
        cta = f"What do y'all think about {topic}? Comment below."
        full = f"{hook} {news} {context} {cta}"
        return {"hook": hook, "news": news, "context": context, "cta": cta, "full": full[:600]}
    except:
        return {"hook": f"The White House is panicking - {topic.title()} just happened.", "news": f"WHAT HAPPENED: Breaking in {topic}.", "context": f"WHY IT MATTERS: Why USA cares.", "cta": f"Comment below.", "full": f"The White House is panicking - Breaking in {topic} - this just happened and it's huge. What do y'all think? Comment below."}
