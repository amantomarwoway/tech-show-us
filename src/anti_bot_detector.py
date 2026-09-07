"""
anti_bot_detector.py (final) - No same font, random font colour, randomisation logic, frame variation rule
"""
import random, json, hashlib
from pathlib import Path

HISTORY_FILE=Path("data/anti_bot_history.json")
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
FONT_LIST=["Anton","BebasNeue","Oswald","Montserrat-ExtraBold","Impact","DejaVuSans-Bold","Anton-Regular","Oswald-Bold"]
COLOR_LIST=["#FF3B30","#FFD60A","#30D158","#0A84FF","#FF2D55","#FFFFFF","#FFE600","#AF52DE","#FF6B00","#00E5FF"]
FPS_CHOICES=[29.97,29.98,59.94,59.95]
FRAME_VARIATIONS=["crop=iw*0.96:ih*0.96:(iw-ow)/2:(ih-oh)/2","crop=iw*0.92:ih*0.92:iw*0.04:ih*0.04","scale=iw*1.03:ih*1.03,crop=iw:ih","scale=iw*0.98:ih*0.98:flags=lanczos",""]
NOISE_HUE="noise=alls=5:allf=t:allp=7,hue=h=2:s=1.08"

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
    cfg={"font":font,"color":color,"fps":random.choice(FPS_CHOICES),"frame_rule":random.choice(FRAME_VARIATIONS),"zoom":round(random.uniform(0.97,1.06),3),"stroke":random.choice([3,4,5,6]),"font_size_delta":random.randint(-6,10),"noise_hue":NOISE_HUE,"id":hashlib.md5(f"{font}{color}{random.random()}".encode()).hexdigest()[:7]}
    hist.append(cfg)
    HISTORY_FILE.write_text(json.dumps(hist[-20:], indent=2))
    print(f"[ANTI-BOT] font={cfg['font']} colour={cfg['color']} fps={cfg['fps']} frame_rule={cfg['frame_rule'][:25]} zoom={cfg['zoom']} id={cfg['id']}")
    return cfg

def get_ffmpeg_vf_and_fps():
    cfg=get_anti_bot_config()
    vf_parts=[]
    if cfg['frame_rule']: vf_parts.append(cfg['frame_rule'])
    if cfg['zoom']!=1.0: vf_parts.append(f"scale=iw*{cfg['zoom']}:ih*{cfg['zoom']},crop=iw:ih")
    vf_parts.append(cfg['noise_hue'])
    vf=",".join([p for p in vf_parts if p])
    return vf, cfg['fps'], cfg

if __name__=="__main__":
    vf,fps,cfg=get_ffmpeg_vf_and_fps()
    print(vf,fps)
