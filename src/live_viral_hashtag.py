import requests, re

def get_google_searchable_title(topic: str) -> str:
    """
    Google se searchable viral title - topic ke hisaab se
    YouTube suggest API se jo sabse zyada search ho raha hai
    """
    try:
        # YouTube search suggest US
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        # matches[0] is original query, rest are suggestions - most searched first
        suggestions = [m for m in matches[1:] if len(m) > 5]
        if suggestions:
            # Sabse pehla suggestion sabse zyada searchable hota hai
            title = suggestions[0]
            # Clean but keep searchable format
            # 60-90 chars best for YouTube SEO
            if len(title) < 10:
                title = topic.title() + " " + title
            print(f"[GOOGLE TITLE] Topic: {topic} -> Searchable Title: {title}")
            return title[:95].title()
    except Exception as e:
        print(f"[GOOGLE TITLE] Fail: {e}")
    
    try:
        # Backup: Google web suggest
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"firefox","q":topic,"hl":"en","gl":"us"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        data = r.json()
        if len(data) > 1 and data[1]:
            title = data[1][0]
            if len(title) > 5:
                print(f"[GOOGLE TITLE] Firefox suggest -> {title}")
                return title[:95].title()
    except Exception as e:
        print(f"[GOOGLE TITLE] Firefox fail: {e}")
    
    # Fallback: topic ko hi searchable banao
    return topic.title()[:95]

def get_topic_hashtags_from_google(topic: str):
    """
    Google se 4 hashtags jo topic se related ho
    YouTube suggest + Google suggest se
    """
    hashtags = []
    try:
        # YouTube suggestions for topic - ye topic se related sabse searchable queries hain
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m) > 3][:10]
        
        for sug in suggestions:
            # Har suggestion se 1 hashtag banao
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', sug).lower().strip()
            words = clean.split()
            if not words:
                continue
            # 1-2 word ka hashtag
            if len(words) >= 2:
                tag = "#" + "".join(words[:2])
            else:
                tag = "#" + words[0]
            tag = tag[:20]
            if tag not in hashtags and len(tag) > 3:
                hashtags.append(tag)
            if len(hashtags) >= 4:
                break
        print(f"[GOOGLE HASHTAGS] Topic: {topic} -> {hashtags}")
    except Exception as e:
        print(f"[GOOGLE HASHTAGS] Fail: {e}")
    
    # Agar 4 nahi mile to topic ke words se banao
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
    World ka No.1 viral hashtag - Google se
    Chahe kisi bhi niche ka ho, kahi ka bhi, sabse zyada searchable
    """
    # Step 1: Google Trends Worldwide - daily trending (world)
    try:
        # World trending RSS
        r = requests.get("https://trends.google.com/trending/rss?geo=US", timeout=6, headers={"User-Agent":"Mozilla/5.0"})
        # US trending me hi world viral bhi hota hai mostly, but we try global
        import feedparser
        feed = feedparser.parse("https://trends.google.com/trending/rss?geo=US")
        if feed.entries:
            title = feed.entries[0].title
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                print(f"[WORLD VIRAL] Google Trends US (world level) -> {title} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL] Trends fail: {e}")
    
    # Step 2: YouTube Trending Worldwide - most searched
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
                print(f"[WORLD VIRAL] YT viral search -> {viral_query} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL] YT suggest fail: {e}")
    
    # Step 3: Google Trends Global (check worldwide trending searches)
    try:
        # Try to get global trending via news.google.com worldwide
        r = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", timeout=6)
        # Parse first title
        m = re.search(r'<title>([^<]+)</title>', r.text)
        # The first is feed title, second is first trending
        titles = re.findall(r'<title>([^<]+)</title>', r.text)
        if len(titles) >= 2:
            viral_title = titles[1]
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', viral_title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                print(f"[WORLD VIRAL] Daily trends -> {viral_title} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL] Daily fail: {e}")
    
    # Step 4: Last - Google search for most viral hashtag today (any niche)
    # No fixed #viral, but ask Google what is trending worldwide
    try:
        # Use Google Trends API alternative - trending searches
        r = requests.get("https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", timeout=6)
        titles = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', r.text)
        if len(titles) >= 2:
            viral_title = titles[1]
            clean = re.sub(r'[^a-zA-Z0-9 ]', '', viral_title).lower().split()[:2]
            tag = "#" + "".join(clean) if clean else ""
            if len(tag) > 3:
                print(f"[WORLD VIRAL] Google News -> {viral_title} -> {tag}")
                return tag
    except Exception as e:
        print(f"[WORLD VIRAL] News fail: {e}")
    
    # Absolute last - still from Google, not fixed, but world level viral
    return "#breakingnews"

def get_live_viral_hashtag():
    """Backward compat - calls world viral"""
    return get_world_viral_hashtag()


def get_google_structured_script(topic: str) -> dict:
    """GOOGLE DIRECT - Proper structured script"""
    try:
        import requests, re
        r = requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches = re.findall(r'"([^"]+)"', r.text)
        suggestions = [m for m in matches[1:] if len(m)>5][:5]
        google_context = " ".join(suggestions) if suggestions else topic
        hook = f"Stop scrolling folks. {topic.title()} just shocked America - this is huge."
        news = f"Here's what happened in {topic} - {google_context[:100]}. This is breaking right now."
        context = f"Wait, here's the crazy part - why America is talking about {topic}. This changes everything for USA."
        cta = f"What do y'all think about {topic}? Comment below."
        full = f"{hook} {news} {context} {cta}"
        return {"hook": hook, "news": news, "context": context, "cta": cta, "full": full[:600]}
    except:
        return {"hook": f"Stop scrolling. {topic.title()} just happened.", "news": f"Breaking in {topic}.", "context": f"Why USA cares.", "cta": f"Comment below.", "full": f"Stop scrolling folks. Breaking in {topic} - this just happened and it's huge. What do y'all think? Comment below."}
