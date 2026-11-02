"""
FULL-PIPELINE wiring check (slow: a few minutes, real ffmpeg rendering).
NOT run by CI's fast pre-flight (the filename deliberately doesn't match
test_*.py). Run it by hand whenever you change the pipeline:

    python tests/e2e_story_render.py

It drives main_story.run_build() end to end — real story validation/normalizing,
real per-beat audio + alignment plumbing, real Ken Burns video, real BGM/SFX
mixing, real Shorts, real metadata, real database + queue — with ONLY the
outside world mocked: Gemini, TTS, image APIs, YouTube, Facebook, Instagram.
No faster-whisper needed: alignment falls back to proportional timing if it is absent.
Frames are shrunk to 640x360 / 360x640 so it finishes quickly.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.pop("FREESOUND_API_KEY", None)
os.environ["STORY_GENRE"] = "horror"

import main_story
import src.config as c
import src.database as db
import src.story_pipeline as sp
import src.story_shorts as ss
import src.story_writer as sw


def make_story():
    filler = " ".join(["word"] * 55)
    beats = []
    for i in range(1, 27):
        dialogue = i % 5 == 0
        beats.append({
            "beat_number": i, "type": "dialogue" if dialogue else "narration",
            "speaker": ("Sarah" if i % 10 == 5 else "Sheriff Tom Garrett") if dialogue else "narrator",
            "text": f"Line {i} of the story begins here. {filler}",
            "visual_description": f"beat {i}: an american diner at night, sheriff cruiser outside",
            "emotion": "dread" if 14 <= i <= 20 else "calm",
            "bgm_keyword": "eerie piano" if i < 10 else ("tense suspense strings" if i < 22 else "dark ambient drone"),
            "sfx_keyword": "heavy rain" if i in (1, 2, 3) else ("door slam" if i == 12 else "none"),
            "sfx_kind": "ambient" if i in (1, 2, 3) else ("action" if i == 12 else "none"),
            "sfx_trigger_word": "begins" if i == 12 else "",
            "pause_after_sec": 3.0 if i in (11, 19) else 0,
        })
    return {"genre": "x", "pillar": "x", "title": "The Diner On Route Nine", "title_long": "I closed the diner alone. I was not the only one inside.",
            "thumbnail_concept": "a lit diner window at night with a silhouette", "thumbnail_text": "DON'T LOOK",
            "description": "A clerk. A stranger. A door that never opens twice.", "tags": ["horror story"], "search_keywords": ["diner story"],
            "characters": [{"name": "Sarah", "gender": "female"}, {"name": "Sheriff Tom Garrett", "gender": "male"}],
            "recurring_character_used": "Sheriff Tom Garrett", "hook": "The bell rang at 3 AM.", "beats": beats}


def fake_tts(text, name, voice=None, rate="+0%", pitch="+0Hz"):
    dest = c.TEMP_DIR / name
    d = len(text.split()) * 0.05
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                    f"aevalsrc='sin(2*PI*220*t)*0.4*clip(min(t/0.05\\,({d:.2f}-t)/0.05)\\,0\\,1)':d={d:.2f}:s=24000",
                    "-c:a", "libmp3lame", "-b:a", "64k", str(dest)], check=True)
    return dest


def fake_image(prompt, scene_number, width=1920, height=1080):
    """Stand-in for the image APIs (Pollinations/Pexels/Pixabay) — no network in the test."""
    from PIL import Image, ImageDraw
    seed = sum(map(ord, str(prompt))) % 200
    img = Image.new("RGB", (width, height), (20 + seed // 4, 25, 40 + seed // 3))
    ImageDraw.Draw(img).ellipse((width * .3, height * .3, width * .7, height * .7), fill=(255, 215, 0))
    dest = c.SCENES_DIR / f"scene{scene_number}.jpg"
    img.save(dest)
    return dest


def probe(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-show_entries", "format=duration",
                        "-of", "json", str(p)], capture_output=True, text=True)
    j = json.loads(o.stdout)
    v = [s for s in j["streams"] if s["codec_type"] == "video"][0]
    return float(j["format"]["duration"]), v["width"], v["height"], any(s["codec_type"] == "audio" for s in j["streams"])


def main():
    sp.LONG_WIDTH, sp.LONG_HEIGHT = 640, 360
    ss.SHORT_WIDTH, ss.SHORT_HEIGHT = 360, 640
    tmp = Path(tempfile.mkdtemp())
    (tmp / "output").mkdir(); (tmp / "pending").mkdir(); (tmp / "sfx").mkdir()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=300:duration=0.6", str(tmp / "door_slam.mp3")], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=color=pink:duration=3:amplitude=0.3", str(tmp / "heavy_rain.mp3")], check=True)
    seen_prompt = {}
    uploads, fb_calls, ig_calls = [], [], []

    def fake_json(prompt, temperature=0.9):
        seen_prompt["p"] = prompt
        return make_story()

    def fake_upload(path, title, desc, tags, **kw):
        vid = f"YT{len(uploads) + 1}"
        uploads.append({"id": vid, "path": Path(path), "title": title, "kw": kw}); return vid

    research = {"sample_size": 4, "top_titles": ["Real Competitor Title"], "suggested_keywords": ["diner"], "suggested_tags": ["horror", "creepypasta"]}
    fb, ig = main_story.facebook_publisher, main_story.instagram_publisher
    with mock.patch.object(db, "DB_PATH", tmp / "e2e.db"), \
            mock.patch.object(main_story, "ROOT_DIR", tmp), mock.patch.object(main_story, "PENDING_DIR", tmp / "pending"), \
            mock.patch.object(main_story, "OUTPUT_DIR", tmp / "output"), mock.patch.object(main_story, "REVIEW_MODE", False), \
            mock.patch.object(sw, "generate_json", side_effect=fake_json), \
            mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room"), \
            mock.patch.object(sp, "synthesize_voiceover", side_effect=fake_tts), \
            mock.patch.object(sp, "generate_scene_image", side_effect=fake_image), \
            mock.patch("src.story_thumbnail.generate_scene_image", side_effect=fake_image), \
            mock.patch("src.audio_fetcher.SFX_DIR", tmp / "sfx"), \
            mock.patch.object(main_story, "research_niche", return_value=research), \
            mock.patch.object(main_story, "upload_video", side_effect=fake_upload), \
            mock.patch.object(main_story, "upload_thumbnail"), \
            mock.patch.object(fb, "is_configured", return_value=True), mock.patch.object(ig, "is_configured", return_value=True), \
            mock.patch.object(fb, "publish_long_video", side_effect=lambda p, t, d, **k: fb_calls.append(("long", Path(p))) or "FBL"), \
            mock.patch.object(fb, "publish_reel", side_effect=lambda p, d, **k: fb_calls.append(("reel", Path(p))) or "FBR"), \
            mock.patch.object(ig, "publish_reel", side_effect=lambda p, cap, **k: ig_calls.append((Path(p), cap)) or "IGR"):
        assert main_story.run_build(force=True) == 0

        # --- the story prompt really carried research + channel strategy
        for needle in ("Real Competitor Title", "WESTERN (American)", "Hey Darky", "bgm_keyword"):
            assert needle in seen_prompt["p"], needle

        # --- YouTube: long + short1 uploaded now (public), short2 queued
        assert [u["id"] for u in uploads] == ["YT1", "YT2"], uploads
        long_up, s1_up = uploads
        d, w, h, a = probe(long_up["path"])
        print(f"LONG  {d:.1f}s {w}x{h} audio={a}")
        assert (w, h) == (640, 360) and a and d > 60
        d1, w1, h1, a1 = probe(s1_up["path"])
        print(f"SHORT {d1:.1f}s {w1}x{h1} audio={a1}")
        assert (w1, h1) == (360, 640) and a1 and 15 <= d1 <= 36

        # --- Facebook: long + short reel; Instagram: ONLY the short
        assert fb_calls == [("long", long_up["path"]), ("reel", s1_up["path"])], fb_calls
        assert len(ig_calls) == 1 and ig_calls[0][0] == s1_up["path"] and "link in bio" in ig_calls[0][1]

        # --- audio layering really happened (mixed file, voice + bgm + sfx)
        assert long_up["path"].name.endswith("_mixed.mp4"), long_up["path"].name
        horizon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=2)).isoformat()
        q = db.get_due_publish_items(horizon)
        assert len(q) == 1 and (tmp / q[0]["file_path"]).exists()
        print("queued Short #2 ->", q[0]["file_path"])

        # --- tomorrow: the queued Short goes to all three
        with db.get_conn() as cn:
            cn.execute("UPDATE publish_queue SET due_at='2000-01-01T00:00:00+00:00'")
        n_before = len(uploads)
        assert main_story.run_publish_queue() == 0
        assert len(uploads) == n_before + 1 and len(ig_calls) == 2 and fb_calls[-1][0] == "reel"
        print("queued Short published to YouTube + Facebook + Instagram")
        with db.get_conn() as cn:
            kinds = sorted((r["kind"], r["parent_video_id"] or "") for r in cn.execute("SELECT * FROM story_videos"))
        assert kinds == [("long", ""), ("short", "YT1"), ("short", "YT1")], kinds
    print("E2E OK — research -> story -> voices -> images -> video -> audio -> shorts -> metadata -> YouTube/Facebook/Instagram -> queue -> DB")


if __name__ == "__main__":
    main()
