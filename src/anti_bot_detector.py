"""
anti_bot_detector.py (final) - ULTRA CLEAN ZERO CHAMAK - FIXED TYPO + OVEREXPOSURE
- frame_rule log leak band, only font/colour/fps log
- allp=7 invalid ffmpeg param removed -> exit 8 fix
- No same font, random font colour, randomisation logic, frame variation rule preserved (LIGHT)
- FIXED: Heavy chamak removed + typo "1.o1" fixed
"""
import random, json, hashlib, re
from pathlib import Path

HISTORY_FILE=Path("data/anti_bot_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
FONT_LIST=["Anton","BebasNeue","Oswald","Montserrat-ExtraBold","Impact","DejaVuSans-Bold","Anton-Regular","Oswald-Bold"]
COLOR_LIST=["#FF3B30","#FFD60A","#30D158","#0A84FF","#FF2D55","#FFFFFF","#FFE600","#AF52DE","#FF6B00","#00E5FF"]
FPS_CHOICES=[29.97,29.98,59.94,59.95]
# ULTRA CLEAN FIX: Only very light crop, no heavy scale, and fixed typo "1.o1" -> "1.01"
# Pehle: ["crop=iw*0.98:ih*0.98:...","scale=iw*1:ih*1.01:ih*1.o1,crop=iw:ih","",""]  <- TYPO + heavy
# Ab: sirf light crop ya empty = clean
FRAME_VARIATIONS=["crop=iw*0.98:ih*0.98:(iw-ow)/2:(ih-oh)/2","",""]  # FIXED: typo removed, heavy scale removed
# ULTRA CLEAN: NO noise/hue = zero chamak. Was "noise=alls=2:allf=t,hue=h=0.5:s=1.02" still giving light chamak
NOISE_HUE=""  # FIXED: empty = no overexposure

def clean_id(text: str) -> str:
    if not text:
        return ""
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
    # ULTRA CLEAN: zoom 1.0 fixed = no crop zoom chamak, was 0.99-1.02
    cfg={"font":font,"color":color,"fps":random.choice(FPS_CHOICES),"frame_rule":random.choice(FRAME_VARIATIONS),"zoom":1.0,"stroke":random.choice([3,4]),"font_size_delta":random.randint(-2,2),"noise_hue":NOISE_HUE,"id":hashlib.md5(f"{font}{color}{random.random()}".encode()).hexdigest()[:7]}
    hist.append(cfg)
    HISTORY_FILE.write_text(json.dumps(hist[-20:], indent=2))
    # FIX: frame_rule log leak band - only short log, no full crop rule
    print(f"[ANTI-BOT ULTRA CLEAN] font={cfg['font']} colour={cfg['color']} fps={cfg['fps']} zoom={cfg['zoom']} id={cfg['id']} - NO CHAMAK")
    return cfg

def get_ffmpeg_vf_and_fps():
    cfg=get_anti_bot_config()
    vf_parts=[]
    if cfg['frame_rule']: vf_parts.append(cfg['frame_rule'])
    # ULTRA CLEAN: zoom 1.0 so no scale filter added
    if cfg['zoom']!=1.0: vf_parts.append(f"scale=iw*{cfg['zoom']}:ih*{cfg['zoom']},crop=iw:ih")
    if cfg['noise_hue']: vf_parts.append(cfg['noise_hue'])
    vf=",".join([p for p in vf_parts if p])
    # FIX: clean vf from invalid params
    vf = vf.replace("allp=7,","").replace(":allp=7","").replace("allp=7","")
    return vf, cfg['fps'], cfg

if __name__=="__main__":
    vf,fps,cfg=get_ffmpeg_vf_and_fps()
    print(f"VF: {vf[:80] if vf else 'EMPTY (ULTRA CLEAN NO FILTER)'}...")
    print(f"FPS: {fps}")
