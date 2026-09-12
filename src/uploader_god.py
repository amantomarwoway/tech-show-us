# src/uploader_god.py - REAL AEROPLANE - DETAILED FIXED - World viral upload
import os, pickle, json

def get_youtube_service():
    """Get YouTube service with refresh token - detailed"""
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        client_id=os.getenv("YT_CLIENT_ID","")
        client_secret=os.getenv("YT_CLIENT_SECRET","")
        refresh_token=os.getenv("YT_REFRESH_TOKEN","")

        if not (client_id and client_secret and refresh_token):
            print("[UPLOADER] No YT creds - skipping upload, but video ready detailed")
            return None

        # Build creds from refresh token
        creds=Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/youtube.upload"]
        )

        # Refresh
        from google.auth.transport.requests import Request
        creds.refresh(Request())

        service=build('youtube','v3', credentials=creds)
        print("[UPLOADER] YouTube service ready - detailed")
        return service
    except Exception as e:
        print(f"[UPLOADER] YouTube service fail {e} - video saved locally")
        import traceback; traceback.print_exc()
        return None

def upload_video_god(video_path, thumb_path, script_data, candidate, boss_data):
    """
    Upload video god - detailed with retention description
    Returns youtube_id or None
    """
    print("\n[UPLOADER GOD - DETAILED] Starting upload")

    title=script_data.get('seo_youtube_title','') or candidate.get('title','')[:60]
    title=title[:60] # YouTube limit for high CTR

    # Description - detailed with comment bait + subscribe bait + retention hooks
    description=script_data.get('description','') or candidate.get('title','')
    hashtags=script_data.get('hashtags',[]) or ["#breakingnews","#worldnews","#viral"]

    # Build detailed description
    full_desc=f"""{description}

{script_data.get('long_script','')[:200]}

🚨 Wait till end - last part will shock you!
💥 This affects you directly!

👇 Do you think this is fair? Comment below 👇
🔔 Subscribe before this gets deleted - more shocking leaks coming!

{ ' '.join(hashtags) }

Source: {candidate.get('url','')}
#breaking #shocking #leaked #whitehouse #tariffs
"""

    # Tags - world SEO
    tags=script_data.get('tags',[]) or ["breaking news","world news","shocking","white house","tariff","viral"]

    # Detailed: Ensure output exists
    if not os.path.exists(video_path):
        print(f"[UPLOADER] Video not found {video_path} - check output folder")
        # Check alternative
        alt="output/final.mp4"
        if os.path.exists(alt):
            video_path=alt
        else:
            print(f"[UPLOADER] No video to upload - detailed folder empty")
            return None

    print(f"[UPLOADER] Video: {video_path} Title: {title}")
    print(f"[UPLOADER] Desc: {full_desc[:100]}... Tags: {tags[:3]}")

    service=get_youtube_service()
    if not service:
        print(f"[UPLOADER] Service None - saving local detailed - VIDEO READY at {video_path}")
        # Return fake id for DB marking
        return f"local_{os.path.basename(video_path)}"

    try:
        from googleapiclient.http import MediaFileUpload

        body={
            "snippet": {
                "title": title,
                "description": full_desc[:5000],
                "tags": tags[:15],
                "categoryId": "25" # News & Politics
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
                print(f"[UPLOADER] Uploaded {int(status.progress()*100)}%")

        youtube_id=response.get('id','')
        print(f"[UPLOADER] ✅ UPLOADED https://youtu.be/{youtube_id} - detailed viral")

        # Thumbnail upload - detailed
        if thumb_path and os.path.exists(thumb_path) and youtube_id:
            try:
                service.thumbnails().set(videoId=youtube_id, media_body=MediaFileUpload(thumb_path, mimetype='image/jpeg')).execute()
                print(f"[UPLOADER] Thumbnail uploaded {thumb_path}")
            except Exception as e:
                print(f"[UPLOADER] Thumb fail {e}")

        # Comment + Subscribe bait - add first comment
        try:
            comment_text="🚨 Do you think this is fair? Comment below - Should this be allowed? Subscribe before this gets deleted! 🔔"
            service.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": youtube_id,
                        "topLevelComment": {"snippet": {"textOriginal": comment_text}}
                    }
                }
            ).execute()
            print(f"[UPLOADER] Comment bait added")
        except Exception as e:
            print(f"[UPLOADER] Comment fail {e}")

        return youtube_id

    except Exception as e:
        print(f"[UPLOADER] Upload crash {e} - video saved local detailed")
        import traceback; traceback.print_exc()
        return f"local_error_{os.path.basename(video_path)}"
