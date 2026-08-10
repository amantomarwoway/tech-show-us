import random, requests, textwrap, numpy as np, feedparser
from io import BytesIO
from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

print("Starting TOPIC-WISE REAL Bot...")

BANK = [
    {"title": "IPHONE BATTERY SECRET", "script": "Stop scrolling! Your iPhone battery is dying fast because of one secret setting Apple never tells you about. Go to Settings, then Battery, and turn off Background App Refresh right now. This hidden trick stops 20 apps from draining your battery in the background. Boom! You just got 2 extra hours of battery every single day.", "kw": "iphone"},
    {"title": "VIRAL GOOGLE HACK 2025", "script": "This viral Google trick is blowing up in America right now and it will save you 10 hours every month. Stop wasting time on fake sponsored results. Just type site colon reddit dot com before your question in Google. You will get real human answers from real people, not ads.", "kw": "google"},
    {"title": "ANDROID SUPER FAST CHARGE", "script": "This insane Android trick broke the internet in the US! Ninety percent of Android users have no idea about this hidden super fast charging mode. Just hold your power button and volume up button together for 3 seconds until you see the logo. Your phone will now charge fifty percent faster than normal.", "kw": "android"},
]

def get_prompt_from_sentence(sentence):
    # Sentence se hi prompt banega - 100% topic related
    s = sentence.lower()
    if "battery" in s:
        return "iphone battery settings ultra realistic 8k closeup, american hand holding iphone battery screen"
    elif "settings" in s or "background" in s:
        return "iphone settings background app refresh screen ultra realistic 8k"
    elif "google" in s or "search" in s or "reddit" in s:
        return "google search on laptop reddit results ultra realistic 8k, american person searching"
    elif "charge" in s or "power" in s or "volume" in s:
        return "android phone fast charging cable ultra realistic 8k, american person"
    elif "stop scrolling" in s or "omg" in s or "breaking" in s:
        return "shocked american tech youtuber face ultra realistic 8k, breaking news background"
    else:
        return f"{sentence} ultra realistic 8k tech, cinematic"

try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=Apple+iPhone+AI+trending&hl=en-US&gl=US&ceid=US:en")
    if feed.entries and len(feed.entries[0].title) > 20:
        selected = {"title": "OMG! BREAKING NEWS", "script": f"OMG! Breaking tech news is trending right now. {feed.entries[0].title}. This changes everything for iPhone and Android users in America. Experts say this update will affect millions of users.", "kw": "breaking"}
    else:
        selected = random.choice(BANK)
except:
    selected = random.choice(BANK)

sentences = [s.strip() for s in selected["script"].split('.') if len(s.strip()) > 5]
print(f"Topic: {selected['title']}")

# Stable American Avatar
try:
    av_url = f"https://randomuser.me/api/portraits/men/{random.randint(10,70)}.jpg"
    av_data = requests.get(av_url, timeout=15).content
    avatar_pil = Image.open(BytesIO(av_data)).convert("RGBA").resize((300,300))
    mask = Image.new("L", (300,300), 0)
    ImageDraw.Draw(mask).ellipse((0,0,300,300), fill=255)
    avatar_pil.putalpha(mask)
    border = Image.new("RGBA", (320,320), (0,0,0,0))
    ImageDraw.Draw(border).ellipse((0,0,320,320), fill=(255,235,0))
    border.paste(avatar_pil, (10,10), avatar_pil)
    avatar_np = np.array(border)
except:
    avatar_np = np.array(Image.new('RGB', (300,300), (255,235,0)))

clips=[]
for i, sentence in enumerate(sentences):
    gTTS(text=sentence, lang='en', tld='us', slow=False).save(f"v{i}.mp3")
    audio = AudioFileClip(f"v{i}.mp3")

    W,H = 1080,1920
    # TOPIC WISE IMAGE - Har sentence ka alag image
    try:
        ai_prompt = get_prompt_from_sentence(sentence)
        print(f"Generating for: {sentence[:30]} -> {ai_prompt}")
        prompt_enc = requests.utils.quote(ai_prompt + ", highly detailed, ultra premium, attractive, meta ai generated")
        url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=1080&height=1920&nologo=true&seed={random.randint(1,99999)}"
        img_bytes = requests.get(url, timeout=45).content
        img = Image.open(BytesIO(img_bytes)).convert("RGB").resize((W,H))
        img = ImageEnhance.Color(img).enhance(1.25)
        img = ImageEnhance.Contrast(img).enhance(1.15)
    except Exception as e:
        print(f"AI fail {e}")
        try:
            url = f"https://picsum.photos/1080/1920?random={random.randint(1,99999)}"
            img = Image.open(BytesIO(requests.get(url, timeout=10).content)).convert("RGB").resize((W,H))
        except:
            img = Image.new('RGB', (W,H), (15,15,30))

    # Word by Word - 3 words max
    words = sentence.split()
    chunks = [' '.join(words[j:j+3]) for j in range(0, len(words), 3)]
    if not chunks:
        chunks = [sentence]
    chunk_duration = audio.duration / len(chunks)

    for k, chunk_text in enumerate(chunks):
        frame_img = img.copy()
        draw = ImageDraw.Draw(frame_img, 'RGBA')
        draw.rectangle((0,0,W,300), fill=(0,0,0,110))
        draw.rectangle((0,1350,W,H), fill=(0,0,0,190))

        try:
            font_cap = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
        except:
            font_cap = ImageFont.load_default()
            font_title = font_cap

        draw.text((30,70), "🔥 " + selected["title"], fill=(255,235,0), font=font_title, stroke_width=5, stroke_fill="black")

        display_text = chunk_text.upper()
        wrapped = textwrap.fill(display_text, width=18)
        y = 1420
        for line in wrapped.split('\n'):
            bbox = draw.textbbox((0,0), line, font=font_cap)
            x = (W - (bbox[2]-bbox[0]))//2
            draw.text((x,y), line, fill="white", font=font_cap, stroke_width=8, stroke_fill="black")
            y+=80

        base = ImageClip(np.array(frame_img)).set_duration(chunk_duration)
        animated = base.resize(lambda t: 1.05 + 0.04*t) # Stable animation
        avatar_clip = ImageClip(avatar_np).set_duration(chunk_duration).set_position((700, 1050)) # Stable avatar

        final_c = CompositeVideoClip([animated, avatar_clip], size=(W,H))
        clips.append(final_c)

# Final audio sync
from moviepy.editor import concatenate_audioclips
all_audio = [AudioFileClip(f"v{j}.mp3") for j in range(len(sentences))]
full_audio = concatenate_audioclips(all_audio)

final_video_temp = concatenate_videoclips(clips, method="compose")
final_video_temp = final_video_temp.set_duration(full_audio.duration).set_audio(full_audio)

final = final_video_temp
while final.duration < 30:
    final = concatenate_videoclips([final, final_video_temp], method="compose")
    if final.duration > 36: break

final.write_videofile("final_shorts.mp4", fps=30, codec='libx264', audio_codec='aac', bitrate="8000k")
print(f"DONE - Topic Wise Images - {final.duration} sec")
from upload_youtube import upload_video
upload_video("final_shorts.mp4", "Tech News Today")
