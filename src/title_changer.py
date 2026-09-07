"""
title_changer.py - Views stop = Google Trends/NewsAPI se naya metadata + Gemini se title
"""
import os, random, re, requests

def get_new_trending_title(old_title):
    """Google Trends/NewsAPI se naya metadata + Gemini se title"""
    topic=old_title.replace("Leaked","").replace("Secret","").strip()[:60]
    
    # 1. Google Trends suggest for new metadata
    new_keywords=[]
    try:
        r=requests.get("https://suggestqueries.google.com/complete/search",
            params={"client":"youtube","ds":"yt","q":topic,"hl":"en","gl":"US"},
            timeout=5, headers={"User-Agent":"Mozilla/5.0"})
        matches=re.findall(r'"([^"]+)"', r.text)
        new_keywords=[m for m in matches[1:] if len(m)>5][:4]
        print(f"[TITLE CHANGER] Trends metadata: {new_keywords}")
    except Exception as e:
        print(f"[TITLE CHANGER] Trends fail {e}")
    
    # 2. Gemini se title (if key available)
    gemini_key=os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model=genai.GenerativeModel('gemini-1.5-flash')
            prompt=f"""Rewrite this YouTube Shorts title for max CTR with secret leak angle, keep under 90 chars, include leaked/behind closed doors/exposed, first to know effect:
            Old title: {old_title}
            Trending keywords: {new_keywords}
            Return only 1 new title, no quotes, no explanation, 40-80 chars, must have leaked angle and bold claim like 'this changes everything'."""
            resp=model.generate_content(prompt)
            new_title=resp.text.strip().replace('"','').replace("'","")[:95]
            if len(new_title)>15:
                print(f"[TITLE CHANGER] Gemini new title: {new_title}")
                return new_title
        except Exception as e:
            print(f"[TITLE CHANGER] Gemini fail {e}")
    
    # 3. Fallback template with leak boost
    templates=[
        f"{topic} Just Leaked Behind Closed Doors - This Changes Everything",
        f"Secret {topic} Exposed - You Won't Believe What's Next",
        f"{topic} Leaked: Inside Sources Reveal Shocking Truth",
        f"Breaking: {topic} Behind Closed Doors Secret Out",
        f"{topic} Leaked Docs Show Huge Move - First to Know"
    ]
    # Add trending keyword if available
    if new_keywords:
        kw=new_keywords[0].title()
        templates.append(f"{kw} Leaked - {topic} Shocks America")
    
    new_title=random.choice(templates)[:95]
    print(f"[TITLE CHANGER] Fallback new title: {new_title}")
    return new_title

def auto_change_titles(low_performers):
    """Views stop = change title"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        CLIENT_ID=os.getenv("YT_CLIENT_ID")
        CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET")
        REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
            print("[TITLE CHANGER] Secrets missing")
            return
        
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token",
                          client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                          scopes=["https://www.googleapis.com/auth/youtube"])
        youtube=build("youtube","v3",credentials=creds)
        
        for video in low_performers:
            yt_id=video['video_id']
            old_title=video.get('title','USA News')
            try:
                new_title=get_new_trending_title(old_title)
                # Get existing video
                resp=youtube.videos().list(part="snippet", id=yt_id).execute()
                if not resp.get('items'):
                    continue
                snippet=resp['items'][0]['snippet']
                snippet['title']=new_title
                # Update
                youtube.videos().update(part="snippet", body={"id": yt_id, "snippet": snippet}).execute()
                print(f"[TITLE CHANGER] Changed {yt_id}: {old_title[:30]} -> {new_title}")
                import time; time.sleep(2)
            except Exception as e:
                print(f"[TITLE CHANGER] Fail for {yt_id} {e}")
    except Exception as e:
        print(f"[TITLE CHANGER] Auto fail {e}")

if __name__=="__main__":
    print(get_new_trending_title("Tacko Fall Signs 76ers Leaked"))
