import os, random, requests, tempfile, re, wave, math, subprocess

# ========== FIXED IMPORTS - MUCKSCRAPER + VUZA OFFLINE - FULL MECHANISM SAME ==========
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, vfx
    print("[VIDEO_GEN] moviepy 1.x loaded - MUCKSCRAPER + VUZA OFFLINE")
except ModuleNotFoundError:
    print("[VIDEO_GEN] moviepy.editor not found, using moviepy 2.x fallback - VUZA OFFLINE")
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip
    try:
        import moviepy.video.fx.all as vfx
    except:
        vfx = None

try:
    from piper import PiperVoice
except Exception as e:
    print(f"[VIDEO_GEN] piper not installed {e}, gTTS fallback - VUZA OFFLINE")
    PiperVoice = None

from PIL import Image, ImageDraw, ImageFont
import PIL.Image

WIDTH, HEIGHT = 1080, 1920
WHITE_BAR_HEIGHT = 210
BLACK_TOP_STRIP = 150 # Minus 40 as you asked (was 190)
BLACK_BOTTOM_STRIP = 200
BLACK_BORDER = 16
CORNER_RADIUS = 38
CLIP_DENSITY = 0.8
DURATION_MIN = 11
DURATION_MAX = 15
FPS_CHOICES = [29.97, 30, 59.94, 60]

# VUZA OFFLINE colors - Hook/Retain/Reward - Open Montage style
VUZA_COLORS = {
    "hook": [(180,30,30), (200,40,40), (160,20,20)], # Red - shocking
    "retain": [(20,40,90), (30,50,110), (15,35,80)], # Blue - secret meeting
    "reward": [(30,20,50), (40,25,60), (25,15,45)], # Purple - panic
    "default": [(30,20,40), (40,20,30), (20,30,40)]
}

MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"

FONT_BOLD_ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def get_piper_voice():
    if PiperVoice is None:
        print("[TTS] Piper not available - will use gTTS - VUZA OFFLINE")
        return None
    os.makedirs("models", exist_ok=True)
    mp="models/en_US-ryan-medium.onnx"; cp="models/en_US-ryan-medium.onnx.json"
    if not os.path.exists(mp):
        try:
            print("[TTS] Downloading Piper model - MUCKSCRAPER + VUZA")
            open(mp,'wb').write(requests.get(MODEL_URL, timeout=60).content)
            open(cp,'wb').write(requests.get(CONFIG_URL, timeout=60).content)
        except Exception as e:
            print(f"[TTS] Download fail {e} - gTTS fallback")
            return None
    try:
        return PiperVoice.load(mp, cp)
    except Exception as e:
        print(f"[TTS] Load fail {e} - gTTS")
        return None

def clean_id(text: str) -> str:
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_script_no_trim(text: str) -> str:
    text = clean_id(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'Visual:.*?\|', '', text, flags=re.I)
    text = re.sub(r'Audio:\s*', '', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_vuza_offline_clips(script_data, num=12):
    """VUZA / Open Montage OFFLINE - 100% FREE - Hook/Retain/Reward colors"""
    clips=[]
    if isinstance(script_data, dict):
        hook = script_data.get('hook','') or script_data.get('hook_visual','')
        retain = script_data.get('retain','') or script_data.get('retain_visual','')
        reward = script_data.get('reward','') or script_data.get('reward_visual','')
        grouped = script_data.get('grouped_topic','')
        muck_source = script_data.get('muckscraper_source','') or script_data.get('source','')
        vuza_offline = script_data.get('vuza_offline', True)
    else:
        hook = retain = reward = grouped = muck_source = ""
        vuza_offline = True

    print(f"[VUZA OFFLINE] Generating {num} offline clips - Hook:{hook[:20] if hook else 'N/A'} Retain:{retain[:20] if retain else 'N/A'} MuckScraper:{muck_source[:20] if muck_source else 'N/A'}")

    # Distribution: 0-3s Hook (3 clips), 3-10s Retain (5 clips), 10-15s Reward (4 clips)
    hook_count = max(2, int(num * 0.3))
    retain_count = max(3, int(num * 0.4))
    reward_count = num - hook_count - retain_count

    for i in range(hook_count):
        color = random.choice(VUZA_COLORS["hook"])
        clips.append(ColorClip(size=(WIDTH,HEIGHT), color=color, duration=CLIP_DENSITY))

    for i in range(retain_count):
        color = random.choice(VUZA_COLORS["retain"])
        clips.append(ColorClip(size=(WIDTH,HEIGHT), color=color, duration=CLIP_DENSITY))

    for i in range(reward_count):
        color = random.choice(VUZA_COLORS["reward"])
        clips.append(ColorClip(size=(WIDTH,HEIGHT), color=color, duration=CLIP_DENSITY))

    # Fill rest with default if needed
    while len(clips) < num:
        color = random.choice(VUZA_COLORS["default"])
        clips.append(ColorClip(size=(WIDTH,HEIGHT), color=color, duration=CLIP_DENSITY))

    random.shuffle(clips)
    # Keep hook first for retention
    if clips:
        # Ensure first clip is hook color (red) for 0-3s retention
        clips[0] = ColorClip(size=(WIDTH,HEIGHT), color=random.choice(VUZA_COLORS["hook"]), duration=CLIP_DENSITY)

    print(f"[VUZA OFFLINE] ✅ {len(clips)} offline clips ready - 100% FREE - Hook:{hook_count} Retain:{retain_count} Reward:{reward_count}")
    return clips[:num]

def get_best_free_clips_from_script(script_data, num=20):
    """Best clips - Pexels optional + VUZA OFFLINE 100% FREE fallback - MUCKSCRAPER + HOOK/RETAIN/REWARD"""
    key=os.getenv("PEXELS_API_KEY")

    if isinstance(script_data, dict):
        pexels_query = script_data.get('pexels_query', '') or script_data.get('hook_visual','') or script_data.get('seo_youtube_title','') or script_data.get('title','') or script_data.get('best_visual_prompt','')
        vuza_offline = script_data.get('vuza_offline', False) or script_data.get('offline', False)
        hook_visual = script_data.get('hook_visual','')
        retain_visual = script_data.get('retain_visual','')
        reward_visual = script_data.get('reward_visual','')
        muck_source = script_data.get('muckscraper_source','') or script_data.get('source','')
    else:
        pexels_query = str(script_data)[:50]
        vuza_offline = False
        hook_visual = retain_visual = reward_visual = muck_source = ""

    search_q = pexels_query or "shocked man reaction white house"

    if not key:
        print(f"[CLIPS] No PEXELS_API_KEY - VUZA OFFLINE mode - 100% FREE - Query: {search_q[:30]} MuckScraper: {muck_source[:20] if muck_source else 'N/A'}")
        return get_vuza_offline_clips(script_data, num=num)

    # If Pexels key exists, try Pexels but with Hook/Retain/Reward queries - VUZA fallback
    clips=[]
    try:
        h={"Authorization":key}
        # Try hook first for retention
        queries_to_try = []
        if hook_visual: queries_to_try.append(hook_visual)
        if retain_visual: queries_to_try.append(retain_visual)
        queries_to_try.append(search_q)
        if reward_visual: queries_to_try.append(reward_visual)

        for q_try in queries_to_try[:3]:
            if len(clips) >= num: break
            q_clean = clean_id(q_try)
            words_found = [w for w in re.findall(r'\w+', q_clean) if len(w)>2][:3]
            sq_final = " ".join(words_found) if words_found else "shocked man reaction"
            url=f"https://api.pexels.com/videos/search?query={sq_final}&per_page={num*2}&orientation=portrait&size=medium"
            try:
                res=requests.get(url,headers=h,timeout=15).json()
                videos=res.get('videos',[])
                random.shuffle(videos)
                for v in videos[:num]:
                    if len(clips)>=num: break
                    try:
                        video_files = sorted(v['video_files'], key=lambda x: x['width'])
                        link = video_files[-1]['link'] if video_files else None
                        if not link: continue
                        r = requests.get(link, timeout=20, stream=True)
                        if r.status_code!= 200: continue
                        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                        tmp_path = tmp_file.name; tmp_file.close()
                        with open(tmp_path, 'wb') as f:
                            for chunk in r.iter_content(8192):
                                if chunk: f.write(chunk)
                        if os.path.get
