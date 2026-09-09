# UPDATED JULY 2025 - GEMINI 3.6 FLASH LATEST + CHATGPT FALLBACK gpt-4o-mini - NO SAFE EXIT - NO FORCE PASS

"""
anti_bot_detector.py - ULTRA CLEAN ZERO CHAMAK
FIXED: Heavy chamak 100% removed - NO crop, NO zoom, NO noise/hue
"""
import random, json, hashlib, re
from pathlib import Path

HISTORY_FILE=Path("data/anti_bot_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
FONT_LIST=["Anton","BebasNeue","Oswald","Montserrat-ExtraBold","Impact","DejaVuSans-Bold","Anton-Regular","Oswald-Bold"]
COLOR_LIST=["#FF3B30","#FFD60A","#30D158","#0A84FF","#FF2D55","#FFFFFF","#FFE600","#AF52DE","#FF6B00","#00E5FF"]
FPS_CHOICES=[29.97,29.98,59.94,59.95]
# ULTRA CLEAN: NO FRAME VARIATION, NO NOISE HUE = CLEAN
FRAME_VARIATIONS=[""]  # FIXED: was heavy crop causing overexposure
NOISE_HUE=""  # FIXED: was noise=alls=5:h=2:s=1.08 causing neon chamak

def clean_id(text):
    if not text: return ""
    text = re.sub(r'/m/[a-z0-9]+', '', text, flags=re.I)
    text = re.sub(r'\b[mM][0-9][a-z0-9]+\b', '', text)
    return text

def get_anti_bot_config():
    hist=[]
    if HISTORY_FILE.exists():
        try: hist=json.loads(HISTORY_FILE.read_text())[-20:]
        except: hist=[]
    last_fonts=[h.get('font') for h in hist[-6:]]
    last_colors=[h.get('color') for h in hist[-6:]]
    for _ in range(30):
        font=random.choice(FONT_LIST)
        color=random.choice(COLOR_LIST)
        if font not in last_fonts or color not in last_colors:
            break
    else:
        font=random.choice(FONT_LIST); color=random.choice(COLOR_LIST)
    cfg={"font":font,"color":color,"fps":random.choice(FPS_CHOICES),"frame_rule":"","zoom":1.0,"stroke":random.choice([3,4]),"font_size_delta":random.randint(-2,2),"noise_hue":NOISE_HUE,"id":hashlib.md5(f"{font}{color}{random.random()}".encode()).hexdigest()[:7]}
    hist.append(cfg)
    HISTORY_FILE.write_text(json.dumps(hist[-20:], indent=2))
    print(f"[ANTI-BOT ULTRA CLEAN] font={cfg['font']} colour={cfg['color']} fps={cfg['fps']} zoom={cfg['zoom']} id={cfg['id']} - NO CHAMAK")
    return cfg

def get_ffmpeg_vf_and_fps():
    cfg=get_anti_bot_config()
    vf=""  # ULTRA CLEAN: No filter at all
    return vf, cfg['fps'], cfg
