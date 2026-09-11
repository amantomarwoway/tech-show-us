import os, random, json, time
try:
    from src.config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
except:
    from config import GOD_INSTRUCTION, ENGLISH_COUNTRIES
def get_youtube_service():
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        CLIENT_ID=os.getenv("YT_CLIENT_ID"); CLIENT_SECRET=os.getenv("YT_CLIENT_SECRET"); REFRESH_TOKEN=os.getenv("YT_REFRESH_TOKEN")
        if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]): return None
        creds=Credentials(None, refresh_token=REFRESH_TOKEN, token_uri="https://oauth2.googleapis.com/token", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, scopes=["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube"])
        return build("youtube","v3",credentials=creds)
    except: return None
def upload_video_god(video_path, thumbnail_path, script_data, story_data, boss_data):
    print(GOD_INSTRUCTION)
    print("[LEG4 UPLOADER_GOD] Upload with world SEO - best title/hashtag/description/tags from Leg1 - best use")
    seo_title=story_data.get('seo_youtube_title') or story_data.get('title') or (script_data.get('title','') if isinstance(script_data,dict) else str(script_data)[:60])
    if isinstance(script_data,dict): seo_title=script_data.get('seo_youtube_title') or script_data.get('title') or seo_title
    description=story_data.get('description','') or (script_data.get('description','') if isinstance(script_data,dict) else "")
    tags=story_data.get('tags',[]) or (script_data.get('tags',[]) if isinstance(script_data,dict) else [])
    if not tags: tags=["breaking news","world news","viral","USA news","news explained"]
    hashtags=story_data.get('hashtags',["#breakingnews","#worldnews","#viral"])
    if boss_data and boss_data.get('top_countries'):
        countries_str=", ".join([c[0] if isinstance(c,tuple) else c for c in boss_data['top_countries']])
        description+=f"\n\nHigh demand in: {countries_str}"
    if hashtags and not any(h in description for h in hashtags[:2]):
        description+=f"\n\n{' '.join(hashtags)}"
    youtube=get_youtube_service()
    if not youtube:
        fake_id=f"test_{random.randint(1000,9999)}"
        print(f"[UPLOADER_GOD] Mock upload: {seo_title} -> {fake_id}")
        return fake_id
    try:
        body={"snippet":{"title":seo_title[:95],"description":description[:4900],"tags":tags[:15],"categoryId":"25","defaultLanguage":"en","defaultAudioLanguage":"en"},"status":{"privacyStatus":"public","selfDeclaredMadeForKids":False}}
        from googleapiclient.http import MediaFileUpload
        media=MediaFileUpload(video_path, mimetype='video/*', resumable=True)
        request=youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response=None
        while response is None:
            status, response=request.next_chunk()
        yt_id=response['id']
        print(f"[UPLOADER_GOD] Uploaded https://youtu.be/{yt_id}")
        if thumbnail_path and os.path.exists(thumbnail_path):
            try: youtube.thumbnails().set(videoId=yt_id, media_body=MediaFileUpload(thumbnail_path, mimetype='image/jpeg')).execute()
            except: pass
        return yt_id
    except Exception as e:
        print(f"[UPLOADER_GOD] Upload fail {e}")
        return f"test_{random.randint(1000,9999)}"
