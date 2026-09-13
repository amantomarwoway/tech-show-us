# src/uploader_god.py - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - REAL AEROPLANE - DETAILED FIXED
import os, pickle, json

def get_youtube_service():
    """Get YouTube service with refresh token - MUCKSCRAPER + VUZA - detailed"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        client_id=os.getenv("YT_CLIENT_ID","")
        client_secret=os.getenv("YT_CLIENT_SECRET","")
        refresh_token=os.getenv("YT_REFRESH_TOKEN","")

        if not (client_id and client_secret and refresh_token):
            print("[UPLOADER] No YT creds - skipping upload, but video ready - VUZA offline - detailed")
            return None

        creds=Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload"
            ]
        )

        from google.auth.transport.requests import Request
        creds.refresh(Request())

        service=build('youtube','v3', credentials=creds)
        print("[UPLOADER] YouTube service ready - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA offline - detailed")
        return service
    except Exception as e:
        print(f"[UPLOADER] YouTube service fail {e} - video saved locally - VUZA offline")
        import traceback; traceback.print_exc()
        return None

def upload_video_god(video_path, thumb_path, script_data, candidate, boss_data):
    """
    Upload video god - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - detailed with retention description
    Returns youtube_id or None
    """
    print("\n[UPLOADER GOD - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - DETAILED] Starting upload")

    # Title - Hook based - high CTR 60 chars
    title = script_data.get('seo_youtube_title','') if isinstance(script_data, dict) else ""
    if not title:
        title = candidate.get('title','')[:60]
    title = title[:60].strip()

    # Hook/Retain/Reward - Automated-Shorts-Generator
    hook = script_data.get('hook','') if isinstance(script_data, dict) else ""
    retain = script_data.get('retain','') if isinstance(script_data, dict) else ""
    reward = script_data.get('reward','') if isinstance(script_data, dict) else ""
    short_script = script_data.get('short_script','') if isinstance(script_data, dict) else ""

    # MuckScraper - grouped + source + Ollama
    grouped_topic = candidate.get('grouped_topic','') or candidate.get('grouped','') or script_data.get('grouped_topic','') if isinstance(script_data, dict) else ""
    muckscraper_source = candidate.get('source','') or candidate.get('muckscraper_source','') or ""
    ollama_summary = script_data.get('ollama_summary','') if isinstance(script_data, dict) else ""
    search_score = candidate.get('breakout_score',0) or candidate.get('search_potential_score',0)

    # Description - detailed + Hook/Retain/Reward chapters + MuckScraper + VUZA + comment bait + subscribe bait
    base_desc = script_data.get('description','') or candidate.get('title','') or title
    long_script = script_data.get('long_script','') if isinstance(script_data, dict) else ""
    hashtags = script_data.get('hashtags',[]) if isinstance(script_data, dict) else []
    if not hashtags:
        hashtags = ["#breakingnews","#worldnews","#viral","#shocking","#muckscraper"]

    # Chapters for Hook/Retain/Reward - YouTube SEO + retention
    chapters = ""
    if hook or retain or reward:
        chapters = f"""
⏱️ CHAPTERS - Hook/Retain/Reward:
0:00 - 🚨 HOOK: {hook[:50] if hook else 'Shocking leak'}
0:03 - 🔥 RETAIN: {retain[:50] if retain else 'Behind closed doors secret'}
0:10 - 💥 REWARD: {reward[:50] if reward else 'This affects you directly'}
"""

    muckscraper_block = ""
    if grouped_topic or muckscraper_source:
        muckscraper_block = f"""
📰 LIVE SOURCE: {muckscraper_source or 'MuckScraper live'}
📊 GROUPED TOPIC: {grouped_topic[:100] if grouped_topic else title}
🔥 BREAKOUT SCORE: {search_score}
🤖 AI SUMMARY: {ollama_summary[:150] if ollama_summary else short_script[:100]}
"""

    full_desc = f"""{base_desc}

{hook}

{retain}

{reward}

{chapters}
{muckscraper_block}

{long_script[:300]}

🚨 Wait till end - last part will shock you! (REWARD)
💥 This affects you directly! (REWARD)

👇 Do you think this is fair? Comment below 👇 (COMMENT BAIT)
👇 Should this be allowed? Is this right or wrong?

🔔 Subscribe before this gets deleted - more shocking leaks coming! (SUBSCRIBE BAIT)
🔔 Follow for real breaking news - VUZA offline 100% FREE

🎬 Made with VUZA OFFLINE - No paid API - 100% FREE - Open Montage style
🤖 Script: Automated-Shorts-Generator Hook/Retain/Reward + Ollama {script_data.get('ollama_model','llama3.1:8b') if isinstance(script_data, dict) else 'local'}
📰 Research: MuckScraper live HTML scrape - {muckscraper_source}

{' '.join(hashtags)}

Source: {candidate.get('url','') or 'MuckScraper live'}
#breaking #shocking #leaked #whitehouse #tariffs #muckscraper #vuza #hookretainreward #ollama
"""

    # Tags - world SEO + MuckScraper + Hook/Retain/Reward + VUZA
    tags = script_data.get('tags',[]) if isinstance(script_data, dict) else []
    if not tags:
        tags = ["breaking news","world news","shocking","white house","tariff","viral","muckscraper","vuza offline","hook retain reward"]

    # Add MuckScraper + Hook keywords to tags
    extra_tags = []
    if grouped_topic: extra_tags.append(grouped_topic[:30])
    if muckscraper_source and "muckscraper" in muckscraper_source.lower():
        extra_tags.append("muckscraper live news")
    if hook: extra_tags.append(clean_hook_tag(hook))
    extra_tags.extend(["vuza offline free", "ollama ai", "open montage"])

    tags = list(dict.fromkeys(tags + extra_tags))[:15]

    # Ensure video exists - VUZA offline fallback
    if not os.path.exists(video_path):
        print(f"[UPLOADER] Video not found {video_path} - check output folder - VUZA offline")
        alt_paths = ["output/final.mp4", "output/news_32.mp4", "output/god_output.mp4"]
        for alt in alt_paths:
            if os.path.exists(alt):
                video_path = alt
                print(f"[UPLOADER] Found alt {alt}")
                break
        else:
            print(f"[UPLOADER] No video to upload - VUZA offline folder empty - detailed")
            return None

    print(f"[UPLOADER] Video: {video_path} Title: {title}")
    print(f"[UPLOADER] Hook: {hook[:40]} | MuckScraper: {muckscraper_source} | VUZA offline: {os.path.getsize(video_path) if os.path.exists(video_path) else 0} bytes")
    print(f"[UPLOADER] Desc: {full_desc[:120]}... Tags: {tags[:5]}")

    service = get_youtube_service()
    if not service:
        print(f"[UPLOADER] Service None - saving local - VUZA offline - VIDEO READY at {video_path}")
        return f"local_vuza_{os.path.basename(video_path)}"

    try:
        from googleapiclient.http import MediaFileUpload

        body={
            "snippet": {
                "title": title,
                "description": full_desc[:5000],
                "tags": tags[:15],
                "categoryId": "25"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        }

        media=MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype='video/mp4')

        request=service.videos().insert(part="snippet,status", body=body, media_body=media)
        response=None
        while response is None:
            status, response=request.next_chunk()
            if status:
                print(f"[UPLOADER] Uploaded {int(status.progress()*100)}% - MUCKSCRAPER + VUZA")

        youtube_id=response.get('id','')
        print(f"[UPLOADER] ✅ UPLOADED https://youtu.be/{youtube_id} - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE - detailed viral")

        if thumb_path and os.path.exists(thumb_path) and youtube_id:
            try:
                service.thumbnails().set(videoId=youtube_id, media_body=MediaFileUpload(thumb_path, mimetype='image/jpeg')).execute()
                print(f"[UPLOADER] Thumbnail uploaded {thumb_path} - VUZA offline")
            except Exception as e:
                print(f"[UPLOADER] Thumb fail {e} - VUZA")

        try:
            comment_text = f"🚨 {hook[:60] if hook else 'Shocking leak'} - Do you think this is fair? Comment below - Should this be allowed? {reward[:40] if reward else 'This affects you!'} Subscribe before this gets deleted! 🔔 Source: {muckscraper_source or 'MuckScraper live'}"
            service.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": youtube_id,
                        "topLevelComment": {"snippet": {"textOriginal": comment_text[:500]}}
                    }
                }
            ).execute()
            print(f"[UPLOADER] Comment bait added - HOOK/RETAIN/REWARD + MuckScraper")
        except Exception as e:
            print(f"[UPLOADER] Comment fail {e}")

        return youtube_id

    except Exception as e:
        print(f"[UPLOADER] Upload crash {e} - video saved local - VUZA offline - detailed")
        import traceback; traceback.print_exc()
        return f"local_error_vuza_{os.path.basename(video_path)}"

def clean_hook_tag(text):
    """Clean hook for tag - HOOK/RETAIN/REWARD"""
    if not text: return "shocking breaking"
    import re
    text = re.sub(r'\s+', ' ', str(text)).strip()
    words = [w for w in text.split() if len(w)>3][:3]
    return " ".join(words).lower() if words else "shocking breaking"
