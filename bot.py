import textwrap, random, numpy as np
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

scripts = [
    {"text": "WAIT! Apple is making a foldable iPhone with NO CREASE! It will cost 2000 dollars and launch in 2026. Would you buy it?", "mood": "shock"},
    {"text": "STOP! Your phone is spying on you! This one setting stops Google tracking. Go to Settings Privacy Turn off Ads Personalization NOW!", "mood": "angry"},
    {"text": "This AI trick is INSANE! Remove any person from your photo in one tap. Open Google Photos tap Tools Magic Eraser and BOOM!", "mood": "happy"}
]

item = random.choice(scripts)
full_text = item["text"]
mood = item["mood"]
sentences = [s for s in full_text.replace('! ','. ').split('. ') if len(s.strip())>2]

HIGHLIGHTS = ["APPLE","IPHONE","FOLDABLE","2000","DOLLARS","NO CREASE","2026","SPYING","AI","INSANE"]

def draw_character(base_img, mood):
    W,H = base_img.size
    draw = ImageDraw.Draw(base_img)
    # Character position - niche center
    cx, cy = W//2, 1650

    # Body color by mood
    if mood=="shock": body_col=(255,235,59)
    elif mood=="angry": body_col=(255,80,80)
    else: body_col=(80,200,255)

    # Body
    draw.ellipse([cx-120, cy-100, cx+120, cy+150], fill=body_col, outline="black", width=6)
    # Head
    draw.ellipse([cx-90, cy-200, cx+90, cy-20], fill=(255,220,180), outline="black", width=6)
    # Eyes
    if mood=="shock":
        draw.ellipse([cx-50, cy-150, cx-25, cy-120], fill="white", outline="black", width=3)
        draw.ellipse([cx+25, cy-150, cx+50, cy-120], fill="white", outline="black", width=3)
        draw.ellipse([cx-42, cy-140, cx-33, cy-130], fill="black")
        draw.ellipse([cx+33, cy-140, cx+42, cy-130], fill="black")
        draw.ellipse([cx-20, cy-80, cx+20, cy-50], fill="black") # open mouth
    else:
        draw.arc([cx-50, cy-140, cx-15, cy-110], 0, 180, fill="black", width=4)
        draw.arc([cx+15, cy-140, cx+50, cy-110], 0, 180, fill="black", width=4)
        draw.arc([cx-25, cy-80, cx+25, cy-60], 0, 180, fill="black", width=4)

    # Hands by mood
    if mood=="shock":
        draw.ellipse([cx-180, cy-80, cx-120, cy-20], fill=(255,220,180), outline="black", width=5) # hands up
        draw.ellipse([cx+120, cy-80, cx+180, cy-20], fill=(255,220,180), outline="black", width=5)
    else:
        draw.ellipse([cx-150, cy+0, cx-90, cy+60], fill=(255,220,180), outline="black", width=5) # pointing
        draw.ellipse([cx+90, cy+0, cx+150, cy+60], fill=(255,220,180), outline="black", width=5)

    return base_img

clips=[]
for i, sentence in enumerate(sentences):
    tts = gTTS(text=sentence, lang='en', tld='us')
    mp3=f"v{i}.mp3"
    tts.save(mp3)
    audio=AudioFileClip(mp3)

    W,H=1080,1920
    c1,c2=(15,15,45),(80,20,120)
    img=Image.new('RGB',(W,H),c1)
    d=ImageDraw.Draw(img)
    for y in range(H):
        r=int(c1[0]+(c2[0]-c1[0])*y/H)
        g=int(c1[1]+(c2[1]-c1[1])*y/H)
        b=int(c1[2]+(c2[2]-c1[2])*y/H)
        d.line([(0,y),(W,y)],fill=(r,g,b))

    # Character add
    img = draw_character(img, mood)

    try:
        font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",68)
        font_s=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",34)
    except:
        font=ImageFont.load_default()
        font_s=font

    # Caption niche centre se thoda up - character ke upar
    words=sentence.upper().split()
    lines=[]; curr=""
    for w in words:
        if len(curr+" "+w)<18:
            curr=curr+" "+w if curr else w
        else:
            lines.append(curr); curr=w
    if curr: lines.append(curr)

    y_start=850
    for line in lines:
        l_words=line.split()
        total_w=sum([d.textbbox((0,0),w+" ",font=font)[2] for w in l_words])
        curr_x=(W-total_w)//2
        for w in l_words:
            col=(255,235,59) if any(h in w for h in HIGHLIGHTS) else (255,255,255)
            d.text((curr_x,y_start),w+" ",fill=col,font=font,stroke_width=6,stroke_fill="black")
            curr_x+=d.textbbox((0,0),w+" ",font=font)[2]
        y_start+=80

    d.text((30,1850),"Tech Operation Theatre",fill="white",font=font_s,stroke_width=3,stroke_fill="black")
    ic=ImageClip(np.array(img)).set_duration(audio.duration).set_audio(audio)
    clips.append(ic)

final=concatenate_videoclips(clips,method="compose")
final.write_videofile("final_shorts.mp4",fps=24,codec='libx264',audio_codec='aac',preset='ultrafast',threads=1)
