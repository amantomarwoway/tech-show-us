"""
END-TO-END run of the whole series show with REAL ffmpeg rendering and every network service replaced by a
stand-in (Gemini, TTS, image APIs, YouTube, Facebook, Instagram). Slow (a few minutes) — run by hand:

    python tests/e2e_story_render.py

What it proves, on real video files:
  1. PART 1 (opening): a model answer shaped like a real one (long multi-sentence beats, quotes, a stage direction)
     is repaired and split into image-sized beats, voiced, illustrated, rendered (15 s+ video with audio),
     mixed with music/sound effects, cut into Shorts (vertical, with the end banner), scheduled on YouTube
     (publishAt at the weekly slot), Facebook (scheduled) and queued for Instagram; the story enters the DB.
  2. PART 2 (continuation of the SAME story, in the same weekly slot a week later): the prompt carries the series
     bible and recap, the characters keep their voices, their looks are in the image prompts, the previous part gets a
     "Next part" link, and the episode joins the series playlist.
  3. The publish queue then posts only Instagram (YouTube/Facebook publish by themselves at the slot).
No faster-whisper needed: alignment falls back to proportional timing if it is absent.
"""
import contextlib
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(Path(__file__).resolve().parent.parent)

import main_story
import src.aligner as aligner
import src.config as c
import src.database as db
import src.story_pipeline as sp
import src.story_shorts as ss
import src.story_writer as sw
from src import schedule

PARA = ("The diner on Route nine closed at midnight, and Sarah counted the till twice. "
        "Rain tapped the windows while the neon sign buzzed above the empty parking lot, flickering between red and white. "
        "Somewhere behind the counter a cold coffee pot ticked as it cooled, and she could not shake the feeling "
        "that the room was holding its breath, waiting for somebody to make the first mistake of the night.")
TMP = None
VOICES, PROMPTS, IMAGE_PROMPTS = [], [], []


def make_story(part_no: int, mode: str) -> dict:
    """Shaped like a real Gemini answer: ~75-word narration beats, quoted dialogue with a stage direction."""
    cycle = ["fear", "curiosity", "suspense", "excitement", "mystery"]
    beats = []
    for i in range(1, 25):
        dialogue = i % 6 == 0
        speaker = ("Sarah" if i % 12 == 6 else ("Dave" if part_no > 1 else "Sheriff Garrett")) if dialogue else "narrator"
        beats.append({
            "beat_number": i, "type": "dialogue" if dialogue else "narration", "speaker": speaker,
            "text": (f'"(whispering) You should not be here, Sarah. Number {i} is not safe."' if dialogue else PARA),
            "visual_description": f"beat {i}: an american diner at night, sheriff cruiser outside",
            "emotion": "dread" if 14 <= i <= 20 else "calm",
            "elements": ["suspense", "mystery"] if i <= 4 else [cycle[i % 5]],
            "jumpscare": i == 12,
            "bgm_keyword": "eerie piano" if i < 10 else ("tense suspense strings" if i < 22 else "dark ambient drone"),
            "sfx_keyword": "heavy rain" if i in (1, 2, 3) else ("door slam" if i == 12 else "none"),
            "sfx_kind": "ambient" if i in (1, 2, 3) else ("action" if i == 12 else "none"),
            "sfx_trigger_word": "buzzed" if i == 12 else "",
            "pause_after_sec": 3.0 if i in (11, 19) else 0,
        })
    story = {
        "genre": "x", "pillar": "x", "title": f"The Diner On Route Nine p{part_no}",
        "title_long": "I closed the diner alone. I was not the only one inside.",
        "thumbnail_concept": "a lit diner window at night with a silhouette", "thumbnail_text": "DON'T LOOK",
        "description": "A clerk. A stranger. A door that never opens twice.", "tags": ["horror story"], "search_keywords": ["diner story"],
        "premise": f"part {part_no} premise", "recurring_character_used": "", "hook": "The bell rang at 3 AM.", "beats": beats,
        "series_update": {"recap": f"RECAP-AFTER-PART-{part_no}", "open_threads": ["who is behind the counter?"],
                          "cliffhanger": f"the bell rang again in part {part_no}", "next_part_teaser": "it gets worse"},
    }
    if mode == "opening":
        story["characters"] = [{"name": "Sarah", "gender": "female", "role": "clerk", "voice_note": "tired", "appearance": "woman in her 30s, brown ponytail, yellow diner uniform"},
                               {"name": "Sheriff Tom Garrett", "gender": "male", "role": "sheriff", "voice_note": "gruff", "appearance": "heavy man, grey moustache, tan uniform"}]
        story["series"] = {"title": "The Diner On Route Nine", "logline": "A clerk, a diner, a thing that knows her name.", "planned_parts": 4,
                           "arc": ["Part 1: the bell", "Part 2: the sheriff", "Part 3: the basement", "Part 4: the truth"], "setting": "Oregon"}
    else:
        story["characters"] = [{"name": "Dave", "gender": "male", "role": "cook", "voice_note": "nervous", "appearance": "thin man, red apron"}]
    return story


def fake_json(prompt, temperature=0.9):
    PROMPTS.append(prompt)
    if "NEW MULTI-PART SERIES" in prompt:
        return make_story(1, "opening")
    part = int(re.search(r"THIS IS PART (\d+) of", prompt).group(1))
    return make_story(part, "finale" if "FINAL PART" in prompt else "middle")


def fake_tts(text, name, voice=None, rate="+0%", pitch="+0Hz"):
    VOICES.append((text, voice))
    dest = TMP / name
    d = max(len(text.split()) * 0.05, 0.6)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency=220:duration={d}", "-c:a", "libmp3lame", str(dest)], check=True)
    return dest


def fake_image(prompt, scene_number, width=1920, height=1080):
    """Stand-in for the image APIs — no network in the test."""
    from PIL import Image, ImageDraw
    IMAGE_PROMPTS.append(prompt)
    seed = sum(map(ord, str(prompt))) % 200
    img = Image.new("RGB", (width, height), (20 + seed // 4, 25, 40 + seed // 3))
    ImageDraw.Draw(img).ellipse((width * .3, height * .3, width * .7, height * .7), fill=(255, 215, 0))
    dest = c.SCENES_DIR / f"scene{scene_number}.jpg"
    img.save(dest)
    return dest


def probe(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-show_entries", "format=duration",
                          "-of", "json", str(p)], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    video = next(s for s in j["streams"] if s["codec_type"] == "video")
    return {"duration": float(j["format"]["duration"]), "w": video["width"], "h": video["height"],
            "audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def main():
    global TMP
    sp.LONG_WIDTH, sp.LONG_HEIGHT = 640, 360
    ss.SHORT_WIDTH, ss.SHORT_HEIGHT = 360, 640
    TMP = Path(tempfile.mkdtemp(prefix="e2e_"))
    for d in ("pending", "output", "data", "sfx"):
        (TMP / d).mkdir()
    uploads, fb_calls, ig_calls, playlist_adds, desc_appends = [], [], [], [], []
    fb, ig = main_story.facebook_publisher, main_story.instagram_publisher
    ids = iter(f"YT{i:02d}" for i in range(60))

    def fake_upload(path, title, desc, tags, **kw):
        vid = next(ids); uploads.append({"id": vid, "path": Path(path), "title": title, "desc": desc, "kw": kw}); return vid

    playlists = iter(f"PL{i}" for i in range(10))
    patches = [
        mock.patch.object(db, "DB_PATH", TMP / "e2e.db"),
        mock.patch.object(main_story, "ROOT_DIR", TMP), mock.patch.object(main_story, "PENDING_DIR", TMP / "pending"),
        mock.patch.object(main_story, "OUTPUT_DIR", TMP / "output"), mock.patch.object(main_story, "REVIEW_MODE", False),
        mock.patch.object(main_story, "CHECKLIST_PATH", TMP / "data" / "related_video_checklist.md"),
        mock.patch.object(sw, "generate_json", side_effect=fake_json),
        mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room"),
        mock.patch.object(aligner, "_get_model", side_effect=ImportError("no whisper in the e2e")),
        mock.patch.object(sp, "synthesize_voiceover", side_effect=fake_tts),
        mock.patch.object(sp, "generate_scene_image", side_effect=fake_image),
        mock.patch("src.story_thumbnail.generate_scene_image", side_effect=fake_image),
        mock.patch("src.audio_fetcher.SFX_DIR", TMP / "sfx"),
        mock.patch.dict(os.environ, {"FREESOUND_API_KEY": "", "STORY_GENRE": "horror"}),
        mock.patch.object(main_story, "research_niche", return_value={"sample_size": 2, "suggested_tags": ["scary stories"], "top_titles": ["x"], "suggested_keywords": ["diner"]}),
        mock.patch.object(main_story, "upload_video", side_effect=fake_upload),
        mock.patch.object(main_story, "upload_thumbnail"),
        mock.patch.object(main_story, "ensure_playlist", side_effect=lambda *a, **k: next(playlists)),
        mock.patch.object(main_story, "add_to_playlist", side_effect=lambda pl, vid: playlist_adds.append((pl, vid))),
        mock.patch.object(main_story, "append_to_description", side_effect=lambda vid, text: desc_appends.append((vid, text)) or True),
        mock.patch.object(fb, "is_configured", return_value=True), mock.patch.object(ig, "is_configured", return_value=True),
        mock.patch.object(fb, "publish_long_video", side_effect=lambda p, t, d, **k: fb_calls.append(("long", k)) or "FBL"),
        mock.patch.object(fb, "publish_reel", side_effect=lambda p, d, **k: fb_calls.append(("reel", k)) or "FBR"),
        mock.patch.object(ig, "publish_reel", side_effect=lambda p, cap, **k: ig_calls.append((Path(p), cap)) or "IGR"),
    ]
    with contextlib.ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)


        # ============================== PART 1 ==============================
        assert main_story.run_build(force=True) == 0
        series = db.get_active_series()
        assert len(series) == 1, series
        s = series[0]
        assert (s["title"], s["planned_parts"], s["parts_done"], s["status"]) == ("The Diner On Route Nine", 4, 1, "active"), s
        assert s["bible"]["voice_map"].keys() >= {"Sarah", "Sheriff Tom Garrett"}
        long1 = uploads[0]
        assert long1["kw"]["publish_at"] is not None and long1["title"].endswith("(Part 1) | Scary Story"), long1["title"]
        info = probe(long1["path"])
        assert info["audio"] and (info["w"], info["h"]) == (640, 360) and info["duration"] > 60, info
        saved = json.loads(next(c.OUTPUT_DIR.glob("*p1_story.json")).read_text())
        words = [len(b["text"].split()) for b in saved["beats"]]
        assert len(words) >= 40 and max(words) <= 44, (len(words), max(words))
        assert not any("whispering" in b["text"] for b in saved["beats"]), "stage directions must not be spoken"
        assert "Part 2 arrives" in saved["beats"][-1]["text"], saved["beats"][-1]["text"]
        print(f"PART 1: {len(words)} beats (longest {max(words)} words) | long {info['duration']:.0f}s | outro: {saved['beats'][-1]['text'][:60]}...")
        shorts1 = uploads[1:]
        want = c.SHORTS_PER_EPISODE_BY_SLOT[s["slot_index"]]
        assert len(shorts1) == want, (len(shorts1), want)
        for sh in shorts1:
            si = probe(sh["path"]); assert si["audio"] and (si["w"], si["h"]) == (360, 640) and 15 < si["duration"] < 45, si
            assert sh["title"].endswith("#Shorts") and "Part 1" in sh["desc"]
        times = [sh["kw"]["publish_at"] for sh in shorts1]
        assert len({t.date() for t in times}) == want and times == sorted(times), times
        assert [k for k, _ in fb_calls].count("reel") == want and ig_calls == [], "Instagram waits for its due time"
        assert all(k.get("scheduled_time") for _, k in fb_calls), "Facebook is scheduled"
        print(f"PART 1: {want} Shorts scheduled one per day, first {times[0]:%a %d %b %H:%M} UTC; long goes public {long1['kw']['publish_at']:%a %d %b %H:%M} UTC")
        assert any("yellow diner uniform" in p for p in IMAGE_PROMPTS), "character looks must reach the image prompts"
        sarah = {v for t, v in VOICES if "Sarah" in t[:0] or v}
        checklist = (TMP / "data" / "related_video_checklist.md").read_text()
        assert checklist.count("- [ ]") == want, checklist
        queued = db.get_due_publish_items((dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)).isoformat())
        assert len(queued) == want

        # ============================== PART 2 (the same story, a week later) ==============================
        # Mark every other slot's next occurrences as taken so the soonest open slot is THIS story's next week.
        now = dt.datetime.now(dt.timezone.utc)
        for idx, t in schedule.open_long_slots(now, lead_days=15):
            if idx != s["slot_index"]:
                db.record_story_upload(f"FILL{idx}{t:%d}", "filler", "p", series_id=999, part_no=1, slot_index=idx, publish_at=t.isoformat())
        n_before, voices_before = len(uploads), len(VOICES)
        assert main_story.run_build(force=True) == 0
        s2 = db.get_series(s["id"])
        assert (s2["parts_done"], s2["status"], s2["bible"]["recap"]) == (2, "active", "RECAP-AFTER-PART-2"), s2
        assert len(db.get_active_series()) == 1, "part 2 continues the story; it does not start another"
        prompt2 = next(p for p in PROMPTS if "THIS IS PART 2 of" in p)
        for needle in ("RECAP-AFTER-PART-1", "the bell rang again in part 1", "yellow diner uniform", "'previously' recap", "NEW CLIFFHANGER"):
            assert needle in prompt2, needle
        long2 = uploads[n_before]
        assert long2["title"].endswith("(Part 2) | Scary Story") and f"Previous part: https://youtu.be/{long1['id']}" in long2["desc"], long2["desc"][:300]
        assert (long1["id"], f"▶ Next: Part 2 — https://youtu.be/{long2['id']}") in desc_appends, desc_appends
        series_pl = s2["playlist_id"]
        assert (series_pl, long1["id"]) in playlist_adds and (series_pl, long2["id"]) in playlist_adds
        voices2 = [v for t, v in VOICES[voices_before:]]
        assert set(s2["bible"]["voice_map"]) >= {"Sarah", "Sheriff Tom Garrett", "Dave"}
        vm1, vm2 = s["bible"]["voice_map"], s2["bible"]["voice_map"]
        assert all(vm2[n] == vm1[n] for n in vm1), "a character never changes voice between parts"
        assert len(set(vm2.values())) == len(vm2), "no two characters share a voice"
        info2 = probe(long2["path"]); assert info2["audio"] and info2["duration"] > 60, info2
        print(f"PART 2: continued the same story | recap+cliffhanger+looks in the prompt | voices kept {dict(vm2)} | long {info2['duration']:.0f}s")

        # ============================== the queue ==============================
        with db.get_conn() as cx:
            cx.execute("UPDATE publish_queue SET due_at = ?", ((dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)).isoformat(),))
        yt_before = len(uploads)
        assert main_story.run_publish_queue() == 0
        total_shorts = want + (len(uploads) - n_before - 1)
        assert len(ig_calls) == total_shorts, (len(ig_calls), total_shorts)
        assert all("Part" in cap and "link in bio" in cap for _, cap in ig_calls), ig_calls[0][1]
        assert len(uploads) == yt_before, "YouTube/Facebook are NOT re-uploaded by the queue"
        assert db.get_due_publish_items() == []
        print(f"QUEUE: {len(ig_calls)} Instagram Reels posted at their due time; nothing re-uploaded")

    print("E2E OK — series show: part 1 -> part 2 (same story, same voices, same looks) -> scheduled YouTube/Facebook -> Instagram queue -> DB")


if __name__ == "__main__":
    main()
