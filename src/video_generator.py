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
                        if os.path.getsize(tmp_path) < 50000:
                            try: os.remove(tmp_path)
                            except: pass
                            continue
                        try:
                            video_clip = VideoFileClip(tmp_path)
                            if video_clip.duration < 0.5:
                                video_clip.close()
                                try: os.remove(tmp_path)
                                except: pass
                                continue
                            final_clip = video_clip.subclip(0, min(2, video_clip.duration)).resize(height=1920).set_position('center').without_audio()
                            clips.append(final_clip)
                        except:
                            try: os.remove(tmp_path)
                            except: pass
                            continue
                    except: continue
            except Exception as e:
                print(f"[CLIPS] Pexels query {sq_final} fail {e} - VUZA fallback")
                continue

        if clips:
            random.shuffle(clips)
            final_cuts=[]
            for c in clips:
                try:
                    d = CLIP_DENSITY
                    if hasattr(c, 'duration') and c.duration > d:
                        start = random.uniform(0, max(0, c.duration-d-0.2))
                        cut = c.subclip(start, start+d)
                    else:
                        cut = c.subclip(0, min(d, c.duration)) if hasattr(c, 'subclip') else c
                    cut = cut.set_duration(d)
                    final_cuts.append(cut)
                except:
                    final_cuts.append(c)
            # Fill with VUZA if not enough
            if len(final_cuts) < num:
                vuza_fill = get_vuza_offline_clips(script_data, num=num-len(final_cuts))
                final_cuts.extend(vuza_fill)
            print(f"[CLIPS] ✅ {len(final_cuts[:num])} clips - {len(clips)} Pexels + {len(final_cuts)-len(clips)} VUZA OFFLINE - MUCKSCRAPER {muck_source[:20]}")
            return final_cuts[:num]
    except Exception as e:
        print(f"Pexels error: {e} - VUZA OFFLINE fallback - 100% FREE")

    # Fallback VUZA OFFLINE - 100% FREE
    return get_vuza_offline_clips(script_data, num=num)

def make_74k_white_bar_FINAL(text, bar_height=210):
    viral_text = clean_id(text).strip()
    viral_text = " ".join(viral_text.split()[:8])
    if len(viral_text) > 62:
        viral_text = viral_text[:62].rsplit(' ',1)[0]
    words = viral_text.split()
    if len(words) >= 4:
        mid = (len(words)+1)//2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        lines = [line1, line2]
    else:
        lines = [viral_text]
    top_black_h = BLACK_TOP_STRIP
    white_h = WHITE_BAR_HEIGHT
    total_h = top_black_h + white_h
    img = Image.new('RGB', (WIDTH, total_h), (0,0,0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, WIDTH, top_black_h], fill=(0,0,0))
    d.rectangle([0, top_black_h, WIDTH, total_h], fill=(255,255,255))
    try:
        f1 = ImageFont.truetype(FONT_BOLD_ITALIC, 58)
        f2 = ImageFont.truetype(FONT_BOLD_ITALIC, 56)
    except:
        try:
            f1 = ImageFont.truetype(FONT_BOLD, 58)
            f2 = ImageFont.truetype(FONT_BOLD, 56)
        except:
            f1 = ImageFont.load_default()
            f2 = ImageFont.load_default()
    if len(lines) == 1:
        d.text((WIDTH//2, top_black_h + white_h//2), lines[0], font=f1, fill=(0,0,0), anchor="mm")
    else:
        d.text((WIDTH//2, top_black_h + white_h//2 - 32), lines[0], font=f1, fill=(0,0,0), anchor="mm")
        d.text((WIDTH//2, top_black_h + white_h//2 + 32), lines[1], font=f2, fill=(0,0,0), anchor="mm")
    p = f"temp/whitebar_final_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p, quality=95)
    return p, total_h

def make_74k_bottom_text_FINAL(text, total_duration):
    viral_text = clean_id(text).strip()[:90]
    w, h = WIDTH, BLACK_BOTTOM_STRIP
    img = Image.new('RGB', (w, h), (0,0,0))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(FONT_BOLD, 32)
    except:
        f = ImageFont.load_default()
    d.text((w//2, h//2), viral_text, font=f, fill=(200,200,200), anchor="mm")
    p = f"temp/bottom_final_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p, quality=95)
    clip = ImageClip(p).set_duration(total_duration).set_position((0, HEIGHT - h))
    return clip

def make_black_rounded_border_FINAL(total_duration):
    w, h = WIDTH, HEIGHT
    img = Image.new('RGBA', (w, h), (0,0,0,0))
    d = ImageDraw.Draw(img)
    try:
        d.rounded_rectangle([0,0,w,h], radius=CORNER_RADIUS, fill=None, outline=(0,0,0,255), width=BLACK_BORDER)
    except:
        d.rectangle([0,0,w,h], fill=None, outline=(0,0,0,255), width=BLACK_BORDER)
    p = f"temp/border_final_{random.randint(1,999999999)}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(total_duration).set_position((0,0))
    return clip

def word_clip_FINAL(word, dur, is_keyword=False, is_first_word=False):
    word = word.upper().strip()[:20]
    if not word: word = "SHOCKING"
    if is_first_word:
        font_size = 92
        stroke = 8
        fill = (255, 255, 0) # Yellow for Hook - Automated-Shorts-Generator
    elif is_keyword:
        font_size = 78
        stroke = 6
        fill = (255, 255, 255)
    else:
        font_size = 62
        stroke = 5
        fill = (255, 255, 255)
    try:
        font = ImageFont.truetype(FONT_BOLD, font_size)
    except:
        font = ImageFont.load_default()
    dummy = Image.new('RGB', (10,10))
    dmy = ImageDraw.Draw(dummy)
    try:
        bbox = dmy.textbbox((0,0), word, font=font, stroke_width=stroke)
        w = bbox[2]-bbox[0] + 30
        h = bbox[3]-bbox[1] + 30
    except:
        w = len(word)*font_size*0.6 + 30
        h = font_size + 30
    img = Image.new('RGBA', (int(w), int(h)), (0,0,0,0))
    d = ImageDraw.Draw(img)
    d.text((w//2, h//2), word, font=font, fill=fill, stroke_width=stroke, stroke_fill=(0,0,0), anchor="mm")
    p = f"temp/txt_{random.randint(1,999999999)}_{word[:5]}.png"
    os.makedirs("temp", exist_ok=True)
    img.save(p)
    clip = ImageClip(p).set_duration(dur).set_position(('center',0.65),relative=True)
    if is_first_word:
        clip = clip.resize(lambda t: 1.4 - 0.25*t/dur if t < dur*0.4 else 1.0)
    else:
        clip = clip.resize(lambda t: 1.15 - 0.15*t/dur if t < dur*0.3 else 1.0)
    return clip

def create_video(script_data, story=None, output_path="output/news_32.mp4"):
    print("[VIDEO_GEN] FULL MECHANISM create_video called - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE 100% FREE")
    if isinstance(script_data, dict):
        raw_script=script_data.get('full_script','') or script_data.get('short_script','') or ""
        title=script_data.get('title','Brutal New Tariffs Panic Millions')
        viral_hook=script_data.get('viral_hook','') or script_data.get('hook','') or title
        first_punch = script_data.get('first_sentence_punch','') or script_data.get('hook','') or viral_hook[:60]
        hook = script_data.get('hook','')
        retain = script_data.get('retain','')
        reward = script_data.get('reward','')
        grouped_topic = script_data.get('grouped_topic','')
        muckscraper_source = script_data.get('muckscraper_source','') or script_data.get('source','')
        vuza_offline = script_data.get('vuza_offline', True)
    elif isinstance(script_data, str) and story and isinstance(story, str) and story.endswith('.mp4'):
        output_path = story
        raw_script = script_data
        title = raw_script[:50]
        viral_hook = title
        first_punch = raw_script[:60]
        hook = retain = reward = grouped_topic = muckscraper_source = ""
        vuza_offline = True
    else:
        raw_script=str(script_data)
        title=raw_script[:50]
        viral_hook=title
        first_punch = raw_script[:60]
        hook = retain = reward = grouped_topic = muckscraper_source = ""
        vuza_offline = True

    os.makedirs("output",exist_ok=True)
    os.makedirs("temp",exist_ok=True)
    script_text = clean_script_no_trim(raw_script)
    if len(script_text.split()) > 50:
        script_text = " ".join(script_text.split()[:50])

    print(f"[VIDEO_GEN] Hook:{hook[:30] if hook else 'N/A'} Retain:{retain[:30] if retain else 'N/A'} MuckScraper:{muckscraper_source[:20] if muckscraper_source else 'N/A'} VUZA:{vuza_offline}")

    # TTS - Piper with gTTS fallback - MUCKSCRAPER + VUZA
    voice=get_piper_voice()
    audio_path="temp/voice.wav"
    os.makedirs("temp", exist_ok=True)
    audio_chunks = []
    sample_rate = 22050
    piper_success=False
    if voice is not None:
        try:
            gen = voice.synthesize(script_text, length_scale=1.25, noise_scale=0.6, noise_w_scale=0.75)
            for ch in gen:
                audio_chunks.append(ch)
                sample_rate = ch.sample_rate
            piper_success=True
        except TypeError:
            try:
                gen = voice.synthesize(script_text)
                for ch in gen:
                    audio_chunks.append(ch)
                    sample_rate = ch.sample_rate
                piper_success=True
            except:
                audio_chunks = []
        except:
            audio_chunks = []

    try:
        if not audio_chunks:
            if not piper_success:
                print("[TTS] Using gTTS fallback - MUCKSCRAPER + VUZA OFFLINE")
                try:
                    from gtts import gTTS
                    tts = gTTS(text=script_text, lang='en', slow=False)
                    tts.save(audio_path)
                except Exception as e:
                    print(f"[TTS] gTTS fail {e} - silent fallback")
                    with wave.open(audio_path, "wb") as wav:
                        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
                        wav.writeframes(bytes([0]*22050*2*2))
            else:
                with wave.open(audio_path, "wb") as wav:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050)
                    wav.writeframes(bytes([0]*22050*2*2))
        else:
            with wave.open(audio_path, "wb") as wav:
                wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sample_rate)
                for ch in audio_chunks:
                    wav.writeframes(ch.audio_int16_bytes)
    except:
        try:
            subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=22050:cl=mono","-t","2","-c:a","pcm_s16le",audio_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    # Audio retention filter - Hook/Retain/Reward
    try:
        from audio_retention import get_tts_retention_filter
        temp_audio_filtered = "temp/voice_filtered.wav"
        af_filter = get_tts_retention_filter(first_punch, american_mode=True)
        cmd = ["ffmpeg","-y","-i", audio_path, "-af", af_filter, "-c:a", "pcm_s16le", temp_audio_filtered]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        audio=AudioFileClip(temp_audio_filtered)
    except:
        try:
            audio=AudioFileClip(audio_path)
            if vfx and hasattr(vfx, 'speedx'):
                audio = audio.fx(vfx.speedx, random.choice([1.0, 1.02, 1.03]))
        except:
            audio=AudioFileClip(audio_path)

    total=audio.duration
    if total < DURATION_MIN:
        try:
            if vfx and hasattr(vfx, 'speedx'):
                audio = audio.fx(vfx.speedx, total / DURATION_MIN)
        except: pass
        total = DURATION_MIN
    if total > DURATION_MAX:
        try: audio = audio.subclip(0, DURATION_MAX)
        except: pass
        total = DURATION_MAX

    clips_needed = max(8, int(total / CLIP_DENSITY) + 2)
    raw_clips = get_best_free_clips_from_script(script_data, num=clips_needed)
    final_video_clips=[]
    t=0
    for c in raw_clips:
        if t >= total: break
        dur = min(CLIP_DENSITY, total-t)
        try:
            sub = c.subclip(0, dur).set_start(t)
            final_video_clips.append(sub)
        except:
            try:
                final_video_clips.append(c.set_start(t).set_duration(dur))
            except:
                final_video_clips.append(c.set_duration(dur).set_start(t))
        t+=dur
    if not final_video_clips:
        # VUZA OFFLINE final fallback
        final_video_clips=[ColorClip((WIDTH, HEIGHT), color=random.choice(VUZA_COLORS["hook"]), duration=total)]
        print("[VIDEO_GEN] No clips - VUZA OFFLINE final fallback")

    base_video = CompositeVideoClip(final_video_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    whitebar_path, actual_h = make_74k_white_bar_FINAL(viral_hook, bar_height=WHITE_BAR_HEIGHT)
    white_bar_clip = ImageClip(whitebar_path).set_duration(total).set_position((0,0))
    bottom_text_clip = make_74k_bottom_text_FINAL(viral_hook, total)
    border_clip = make_black_rounded_border_FINAL(total)
    try:
        from audio_retention import get_american_captions_timing
        timing = get_american_captions_timing(total, len(script_text.split()), 5)
        base_dur = timing["base_dur"]; first_dur = timing["first_dur"]; keyword_dur = timing["keyword_dur"]; overlap = timing["overlap"]
    except:
        base_dur = total / max(len(script_text.split()),1) * 0.95
        base_dur = max(0.28, min(0.38, base_dur))
        first_dur = base_dur * 1.4; keyword_dur = base_dur * 1.2; overlap = 0.92
    words = script_text.split()
    caption_clips=[]
    first_words_count = min(5, len(words)) # Hook - first 5 words yellow big
    current_time = 0
    for i,w in enumerate(words):
        is_first = i < first_words_count # HOOK
        is_kw = any(k in w.upper() for k in ["BRUTAL","TARIFFS","PANIC","MILLIONS","SHOCKING","BREAKING","TRUMP","BIDEN","CANADA","BAN","SECRET","VOTER","TEST","LEAKED","WHITE","HOUSE"]) or is_first
        dur = first_dur if is_first else (keyword_dur if is_kw else base_dur)
        if current_time >= total: break
        if current_time + dur > total: dur = max(0.15, total - current_time)
        wc = word_clip_FINAL(w.upper(), dur, is_kw, is_first).set_start(current_time)
        caption_clips.append(wc)
        current_time += dur * overlap
    comp = CompositeVideoClip([base_video, white_bar_clip, bottom_text_clip, border_clip] + caption_clips, size=(WIDTH, HEIGHT)).set_duration(total)
    fps = random.choice(FPS_CHOICES)
    comp = comp.set_audio(audio)
    print(f"[VIDEO_GEN] Writing {output_path} FPS:{fps} Duration:{total:.1f}s - MUCKSCRAPER:{muckscraper_source[:20] if muckscraper_source else 'N/A'} VUZA:{vuza_offline} Hook:{hook[:20] if hook else 'N/A'}")
    comp.write_videofile(output_path, fps=fps, codec='libx264', audio_codec='aac', preset='ultrafast', threads=4, logger=None)
    try:
        import glob
        for f in glob.glob("temp/whitebar_final_*.png") + glob.glob("temp/bottom_final_*.png") + glob.glob("temp/border_final_*.png") + glob.glob("temp/txt_*.png"):
            try: os.remove(f)
            except: pass
    except: pass
    print(f"[VIDEO_GEN] ✅ DONE {output_path} - MUCKSCRAPER + HOOK/RETAIN/REWARD + VUZA OFFLINE 100% FREE")
    return output_path
