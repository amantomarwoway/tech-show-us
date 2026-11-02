"""
Fast wiring + behaviour tests for the Hey Darky story bot (no network, no
real uploads; a few real-ffmpeg audio checks). Run from the repo root:

    python -m unittest discover -s tests -p "test_*.py" -v

The GitHub workflow runs this BEFORE the bot so a broken wiring fails in
seconds instead of after a 90-minute render. The slow full-render test lives in
tests/e2e_story_render.py.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

HAVE_FFMPEG = shutil.which("ffmpeg") is not None


class _Resp:
    def __init__(self, status=200, body=None, content=b"", text=""):
        self.status_code, self._body, self.content, self.text = status, body if body is not None else {}, content, text

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


# ---------------------------------------------------------------- story writer
class StoryWriterTests(unittest.TestCase):
    def test_normalizer_repairs_sloppy_llm_audio_fields(self):
        from src.story_writer import _normalize_story
        T = "A line of narration."          # beats without text are dropped by the repair step
        story = {"title": "T", "title_long": "  I saw   it ", "thumbnail_text": "don't answer the phone now",
                 "characters": [],
                 "beats": [{"text": T, "bgm_keyword": "Dark Ambient"}, {"text": T, "bgm_keyword": ""}] + [{"text": T, "bgm_keyword": f"m{i}"} for i in range(2, 9)]
                 + [{"text": T, "sfx_keyword": "Door Slam", "sfx_kind": "ACTION", "sfx_trigger_word": " slammed ", "pause_after_sec": "3.5"},
                    {"text": T, "sfx_keyword": "rain", "sfx_kind": "weird", "pause_after_sec": 99},
                    {"text": T, "sfx_keyword": "wind", "sfx_kind": "ambient", "pause_after_sec": 1}]}
        _normalize_story(story)
        b = story["beats"]
        self.assertEqual(b[1]["bgm_keyword"], "dark ambient")
        self.assertLessEqual(len({x["bgm_keyword"] for x in b}), 6)
        self.assertEqual((b[-3]["sfx_keyword"], b[-3]["sfx_kind"], b[-3]["sfx_trigger_word"], b[-3]["pause_after_sec"]),
                         ("door slam", "action", "slammed", 3.5))
        self.assertEqual((b[-2]["sfx_kind"], b[-2]["pause_after_sec"]), ("none", 4.0))
        self.assertEqual(b[-1]["pause_after_sec"], 0.0)
        self.assertEqual(story["thumbnail_text"], "DON'T ANSWER")
        self.assertEqual(story["title_long"], "I saw it")

    def _valid_story(self):
        beats = [{"beat_number": i, "type": "dialogue" if i % 4 == 0 else "narration",
                  "speaker": "Sarah" if i % 4 == 0 else "narrator", "text": " ".join(["word"] * 65),
                  "visual_description": "a diner at night"} for i in range(1, 31)]
        return {"characters": [{"name": "Sarah", "gender": "female"}, {"name": "Tom", "gender": "male"}], "beats": beats}

    def test_validator_rejects_bad_structure(self):
        from src.story_writer import _validate_story
        _validate_story(self._valid_story())
        s = self._valid_story(); s["beats"][3]["speaker"] = "Ghost"
        with self.assertRaises(ValueError): _validate_story(s)
        s = self._valid_story(); s["beats"] = s["beats"][:5]
        with self.assertRaises(ValueError): _validate_story(s)
        s = self._valid_story(); s["beats"][0]["visual_description"] = ""
        with self.assertRaises(ValueError): _validate_story(s)

    def test_write_story_wires_research_pillar_and_overrides_model_echo(self):
        import src.story_writer as sw
        sent = {}
        story = self._valid_story(); story.update(genre="WRONG", pillar="WRONG")

        def fake_json(prompt, temperature=0.9):
            sent["prompt"] = prompt
            return story
        research = {"sample_size": 5, "top_titles": ["Real Title X"], "suggested_keywords": ["nightshift"], "suggested_tags": ["creepy"]}
        with mock.patch.object(sw, "generate_json", side_effect=fake_json), \
                mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room") as pick:
            out = sw.write_story("horror", research=research)
        pick.assert_called_once()
        self.assertEqual((out["genre"], out["pillar"]), ("horror", "locked_room"), "our decisions beat the model's echo")
        for needle in ("Real Title X", "nightshift", "WESTERN (American)", "Hey Darky", "Reddit-confession", "bgm_keyword"):
            self.assertIn(needle, sent["prompt"])
        with self.assertRaises(ValueError): sw.write_story("romance")
        with self.assertRaises(ValueError): sw.write_story("horror", pillar="nope")

    def test_all_five_niches_are_enabled(self):
        from src.config import STORY_GENRES, STORY_RESEARCH_QUERIES, STORY_GENRE_HASHTAGS
        self.assertEqual(set(STORY_GENRES), {"crime", "thriller", "suspense", "mystery", "horror"})
        for g in STORY_GENRES:
            self.assertIn(g, STORY_RESEARCH_QUERIES)
            self.assertIn(g, STORY_GENRE_HASHTAGS)

    def test_every_image_prompt_is_western_styled(self):
        from src.story_pipeline import styled_prompt
        out = styled_prompt("A boy walks a river path.  ")
        self.assertTrue(out.startswith("A boy walks a river path"))
        self.assertIn("Western (American)", out)
        self.assertIn("United States", out)

    def test_channel_is_hey_darky(self):
        from src.config import CHANNEL_NAME, STORY_CHANNEL_HASHTAGS
        self.assertEqual(CHANNEL_NAME, "Hey Darky")
        self.assertEqual(STORY_CHANNEL_HASHTAGS[0], "#HeyDarky")


# ---------------------------------------------------------------- audio
class AudioFetcherTests(unittest.TestCase):
    def setUp(self):
        import src.audio_fetcher as af
        self.af = af
        self.tmp = Path(tempfile.mkdtemp())
        self._patches = [mock.patch.object(af, "AUDIO_CACHE_DIR", self.tmp),
                         mock.patch.object(af, "MUSIC_DIR", self.tmp / "nomusic"),
                         mock.patch.object(af, "SFX_DIR", self.tmp / "nosfx"),
                         mock.patch.dict(os.environ, {"FREESOUND_API_KEY": "KEY"})]
        for p in self._patches: p.start()
        af._misses.clear(); af._last_request_at = 0.0

    def tearDown(self):
        for p in self._patches: p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _search(self):
        return _Resp(200, {"results": [
            {"name": "low", "avg_rating": 2.0, "previews": {"preview-hq-mp3": "https://cdn/low.mp3"}},
            {"name": "best", "avg_rating": 4.8, "previews": {"preview-hq-mp3": "https://cdn/best.mp3"}},
            {"name": "nopreview", "avg_rating": 5.0, "previews": {}}]})

    def _getter(self, script, calls):
        it = iter(script)
        def get(url, params=None, headers=None, timeout=None):
            calls.append((url, params, headers)); return next(it)
        return get

    def test_cc0_duration_filters_auth_toprated_and_cache(self):
        calls = []
        with mock.patch("requests.get", side_effect=self._getter([self._search(), _Resp(200, content=b"ID3" + b"\0" * 3000)], calls)), \
                mock.patch("time.sleep"):
            sfx = self.af.get_sfx("Door Slam")
        self.assertEqual(sfx.name, "sfx_door_slam.mp3")
        url, params, headers = calls[0]
        self.assertEqual(url, "https://freesound.org/apiv2/search/")
        self.assertEqual(params["filter"], 'duration:[0.5 TO 10.0] license:"Creative Commons 0"')
        self.assertEqual(headers["Authorization"], "Token KEY")
        self.assertEqual(calls[1][0], "https://cdn/best.mp3", "highest-rated usable result")
        self.assertEqual(calls[1][2]["Authorization"], "Token KEY", "previews need the token too")
        with mock.patch("requests.get", side_effect=AssertionError("cache hit must not touch the network")):
            self.assertEqual(self.af.get_sfx("door slam!!"), sfx)
        calls.clear()
        with mock.patch("requests.get", side_effect=self._getter([self._search(), _Resp(200, content=b"ID3" + b"\0" * 3000)], calls)), \
                mock.patch("time.sleep"):
            self.af.get_bgm("dark ambient drone")
        self.assertEqual(calls[0][1]["filter"], 'duration:[60 TO 600] license:"Creative Commons 0"')

    def test_429_linear_backoff_then_give_up_without_trailing_wait(self):
        sleeps, calls = [], []
        with mock.patch("requests.get", side_effect=self._getter([_Resp(429), _Resp(429), self._search(), _Resp(200, content=b"ID3" + b"\0" * 3000)], calls)), \
                mock.patch("time.sleep", side_effect=sleeps.append):
            self.assertIsNotNone(self.af.get_sfx("gunshot"))
        self.assertEqual([s for s in sleeps if s >= 60], [60, 120])
        sleeps.clear(); self.af._misses.clear()
        with mock.patch("requests.get", side_effect=self._getter([_Resp(429)] * 3, [])), mock.patch("time.sleep", side_effect=sleeps.append):
            self.assertIsNone(self.af.get_sfx("scream"))
        self.assertEqual([s for s in sleeps if s >= 60], [60, 120])

    def test_two_second_minimum_gap_between_requests(self):
        clock, slept = {"t": 1000.0}, []
        self.af._last_request_at = 0.0
        with mock.patch.object(self.af.time, "monotonic", side_effect=lambda: clock["t"]), \
                mock.patch.object(self.af.time, "sleep", side_effect=lambda s: (slept.append(s), clock.__setitem__("t", clock["t"] + s))), \
                mock.patch("requests.get", return_value=_Resp(200, {"results": []})):
            self.af._request("https://x"); clock["t"] += 0.3; self.af._request("https://x")
        self.assertTrue(any(abs(s - 1.7) < 1e-6 for s in slept), slept)

    @unittest.skipUnless(HAVE_FFMPEG, "ffmpeg required")
    def test_no_key_means_no_network_and_a_synthesized_bgm_fallback(self):
        with mock.patch.dict(os.environ, {"FREESOUND_API_KEY": ""}), \
                mock.patch("requests.get", side_effect=AssertionError("no network without a key")):
            bgm = self.af.get_bgm("slow horror pad")
            self.assertIsNone(self.af.get_sfx("door slam"))
        self.assertTrue(bgm.name.startswith("bgm_synth_") and bgm.stat().st_size > 10_000)


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg required")
class AudioMixerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        t = cls.tmp
        gate = "clip(min((t-{a})/0.05\\,({b}-t)/0.05)\\,0\\,1)"
        expr = "+".join(gate.format(a=a, b=b) for a, b in ((0, 3), (4.5, 7), (10, 13)))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=320x240:d=13:r=10",
                        "-f", "lavfi", "-i", f"aevalsrc='sin(2*PI*300*t)*0.5*({expr})':d=13:s=48000",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(t / "vo.mp4")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=110:duration=20", str(t / "bgm.mp3")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=900:duration=0.5", str(t / "hit.mp3")], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=500:duration=2", str(t / "amb.mp3")], check=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _peak(self, f, ss, t):
        r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(ss), "-t", str(t), "-i", str(f), "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True)
        return float(re.search(r"max_volume:\s*(-?[\d.]+)", r.stderr).group(1))

    def test_timeline_merges_moods_and_places_sfx_on_trigger_word(self):
        from src.audio_mixer import build_audio_timeline
        beats = [{"bgm_keyword": "Dark Ambient", "sfx_keyword": "rain", "sfx_kind": "ambient"},
                 {"bgm_keyword": "dark  ambient", "sfx_keyword": "rain", "sfx_kind": "ambient"},
                 {"bgm_keyword": "tense strings", "sfx_keyword": "door slam", "sfx_kind": "action", "sfx_trigger_word": "slammed"},
                 {"bgm_keyword": "tense strings", "sfx_keyword": "none", "sfx_kind": "none"}]
        words = [[], [], [{"word": "The", "start": .1, "end": .2}, {"word": "slammed.", "start": 1.7, "end": 2.1}], []]
        tl = build_audio_timeline(beats, [3.0, 2.0, 4.0, 1.0], words)
        self.assertEqual(tl["total"], 10.0)
        self.assertEqual([s["keyword"] for s in tl["bgm_segments"]], ["dark ambient", "tense strings"])
        amb = [e for e in tl["sfx_events"] if e["kind"] == "ambient"]
        self.assertEqual((len(amb), amb[0]["start"], amb[0]["end"]), (1, 0.0, 5.0))
        act = [e for e in tl["sfx_events"] if e["kind"] == "action"][0]
        self.assertAlmostEqual(act["start"], 6.7, places=6)

    def test_pause_detection_ignores_short_gaps(self):
        from src.audio_mixer import detect_pauses
        p = detect_pauses(self.tmp / "vo.mp4")
        self.assertEqual(len(p), 1)
        self.assertTrue(6.9 < p[0][0] < 7.2 and 9.8 < p[0][1] < 10.2)

    def test_measured_levels_bgm_22_below_vo_and_12_in_pauses(self):
        from src.audio_mixer import mix_story_audio
        out = self.tmp / "o1.mp4"
        mix_story_audio(self.tmp / "vo.mp4", out, {"total": 13.0, "bgm_segments": [{"keyword": "x", "start": 0.0, "end": 13.0}], "sfx_events": []},
                        fetch_bgm=lambda k: self.tmp / "bgm.mp3", fetch_sfx=lambda k: None, normalize_output=False)
        vo, low, high = self._peak(out, 0.5, 2.0), self._peak(out, 3.4, 0.9), self._peak(out, 7.8, 1.4)
        self.assertTrue(-2.0 < vo < 0.0, vo)
        self.assertTrue(20 < vo - low < 24, (vo, low))
        self.assertTrue(10 < vo - high < 14, (vo, high))

    def test_sfx_lands_on_its_timestamp_and_ambient_loops(self):
        from src.audio_mixer import mix_story_audio
        out = self.tmp / "o2.mp4"
        files = {"hit": self.tmp / "hit.mp3", "amb": self.tmp / "amb.mp3"}
        tl = {"total": 13.0, "bgm_segments": [], "sfx_events": [
            {"keyword": "hit", "kind": "action", "start": 8.0}, {"keyword": "amb", "kind": "ambient", "start": 7.2, "end": 9.8}]}
        rep = mix_story_audio(self.tmp / "vo.mp4", out, tl, fetch_bgm=lambda k: None, fetch_sfx=lambda k: files[k], normalize_output=False)
        self.assertEqual(rep["sfx_events"], 2)
        amb, hit, looped = self._peak(out, 8.6, .5), self._peak(out, 8.05, .4), self._peak(out, 9.25, .3)
        self.assertTrue(-31 < amb < -23 and -31 < looped < -23, (amb, looped))
        self.assertTrue(-11 < hit < -6 and hit - amb > 12, (hit, amb))
        r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", "7.9", "-t", "0.4", "-i", str(out), "-af", "silencedetect=noise=-17dB:d=0.01", "-f", "null", "-"],
                           capture_output=True, text=True)
        onset = 7.9 + float(re.findall(r"silence_end: ([\d.]+)", r.stderr)[0])
        self.assertLess(abs(onset - 8.0), 0.06)

    def test_mixing_never_loses_the_video(self):
        from src.audio_mixer import mix_story_audio
        out = self.tmp / "o3.mp4"
        rep = mix_story_audio(self.tmp / "vo.mp4", out, {"total": 13.0, "bgm_segments": [{"keyword": "x", "start": 0, "end": 13}], "sfx_events": []},
                              fetch_bgm=lambda k: None, fetch_sfx=lambda k: None)
        self.assertTrue(rep["copied_through"] and out.exists())


# ---------------------------------------------------------------- metadata + analytics
class PlatformMetadataTests(unittest.TestCase):
    def setUp(self):
        self.story = {"genre": "horror", "universe_town": "Blackwood Pines, Oregon",
                      "title_long": "I worked the night shift at a lonely gas station. I should have ignored the last customer <and> never looked back at the window again, ever.",
                      "description": "A clerk. A stranger. A door. " * 4, "tags": ["horror story", "गुप्त"], "search_keywords": ["night shift story"]}
        self.research = {"suggested_tags": ["horror", "creepypasta", "true crime", "डरावनी"]}

    def test_each_platform_gets_its_own_text(self):
        from src.platform_metadata import build_long_posts, build_short_posts
        from src.config import IG_CAPTION_LIMIT
        long = build_long_posts(self.story, self.research)
        yt, fb = long["youtube"], long["facebook"]
        self.assertTrue(len(yt["title"]) <= 100 and "<" not in yt["title"] and ">" not in yt["title"])
        tags = yt["description"].strip().splitlines()[-1].split()
        self.assertTrue(tags[0] == "#HeyDarky" and len(tags) <= 5)
        self.assertIn("fiction", yt["description"].lower())
        self.assertTrue(all(all(ord(c) < 128 for c in t) for t in yt["tags"]), "English/ASCII tags only")
        self.assertLessEqual(sum(len(t) + (2 if " " in t else 0) + 1 for t in yt["tags"]), 500)
        self.assertNotIn("youtu", fb["description"])
        sp = build_short_posts(self.story, self.research, {"hook": "The bell rang at 3 AM."}, "abc123XYZ")
        self.assertEqual(sp["youtube"]["title"], "The bell rang at 3 AM. #Shorts")
        self.assertIn("https://youtu.be/abc123XYZ", sp["youtube"]["description"])
        ig = sp["instagram"]["caption"]
        self.assertTrue(len(ig) <= IG_CAPTION_LIMIT and "youtu" not in ig and "link in bio" in ig)
        ig_tags = [w for w in ig.split() if w.startswith("#")]
        self.assertTrue(3 <= len(ig_tags) <= 8 and ig_tags[0] == "#HeyDarky")


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        import src.database as db
        self.db = db
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(db, "DB_PATH", self.tmp / "t.db"); self.p.start()
        db.init_db()

    def tearDown(self):
        self.p.stop(); shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cadence_is_driven_by_real_uploads(self):
        db = self.db; now = datetime.now(timezone.utc)
        self.assertTrue(db.should_build_long_today(2))
        db.record_story_upload("L1", "T", "locked_room", kind="long", genre="horror")
        self.assertFalse(db.should_build_long_today(2))
        self.assertTrue(db.should_build_long_today(2, now + timedelta(days=2)))
        self.assertFalse(db.should_build_long_today(2, now + timedelta(days=1, hours=10)))
        db.record_story_upload("S1", "short", "locked_room", kind="short", parent_video_id="L1")
        self.assertFalse(db.should_build_long_today(2), "a Short must not reset the long-video clock")

    def test_pillar_learning_uses_long_videos_only(self):
        db = self.db
        db.record_story_upload("L1", "T", "locked_room", kind="long")
        db.record_story_upload("S1", "s", "locked_room", kind="short", parent_video_id="L1")
        db.update_story_performance("L1", avg_view_percentage=0.6, ctr=0.07, views=900)
        db.update_story_performance("S1", avg_view_percentage=0.1, views=50)
        self.assertEqual(db.get_pillar_stats()["locked_room"]["count"], 1)

    def test_queue_lifecycle_and_idempotent_migration(self):
        db = self.db; now = datetime.now(timezone.utc)
        db.init_db(); db.init_db()
        qid = db.enqueue_publish((now - timedelta(minutes=1)).isoformat(), "pending/x.mp4", {"a": 1})
        db.enqueue_publish((now + timedelta(hours=5)).isoformat(), "pending/y.mp4", {})
        due = db.get_due_publish_items()
        self.assertEqual([i["id"] for i in due], [qid]); self.assertEqual(due[0]["payload"], {"a": 1})
        db.mark_publish_item(qid, "done", {"youtube": "id"})
        self.assertEqual(db.get_due_publish_items(), [])


# ---------------------------------------------------------------- publishers
class SocialPublisherTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"FB_PAGE_ID": "PAGE1", "FB_ACCESS_TOKEN": "TOK", "IG_USER_ID": "IG1"}); self.env.start()
        self.f = Path(tempfile.mkdtemp()) / "v.mp4"; self.f.write_bytes(bytes(range(256)) * 40)
        self.size = self.f.stat().st_size
        import src.facebook_publisher as fb
        self.fb = fb; fb._locale_cache = None

    def tearDown(self):
        self.env.stop(); shutil.rmtree(self.f.parent, ignore_errors=True)

    def _router(self, log, targeting_rejected=False, locales_ok=True):
        size = self.size
        def req(method, url, **kw):
            data = kw.get("data") or {}
            log.append((method, url, dict(data) if isinstance(data, dict) else "<stream>", kw.get("headers"), kw.get("files")))
            if url.endswith("/search"):
                return _Resp(200, {"data": [{"key": 6, "name": "English (US)"}, {"key": 24, "name": "English (UK)"}, {"key": 9, "name": "Spanish"}]}) if locales_ok else _Resp(400, {"error": {"code": 100}})
            phase = data.get("upload_phase") if isinstance(data, dict) else None
            if "graph-video" in url:
                if phase == "start": return _Resp(200, {"upload_session_id": "S1", "video_id": "V1", "start_offset": "0", "end_offset": "4096"})
                if phase == "transfer":
                    nxt = int(data["start_offset"]) + 4096
                    return _Resp(200, {"start_offset": str(size), "end_offset": str(size)}) if nxt >= size else _Resp(200, {"start_offset": str(nxt), "end_offset": str(min(nxt + 4096, size))})
                if phase == "finish":
                    return _Resp(400, {"error": {"code": 100}}) if (targeting_rejected and "targeting" in data) else _Resp(200, {"success": True})
            if url.endswith("/video_reels"):
                if phase == "start": return _Resp(200, {"video_id": "RV1", "upload_url": "https://rupload.facebook.com/video-upload/v23.0/RV1"})
                if phase == "finish": return _Resp(200, {"success": True})
            if "rupload" in url: return _Resp(200, {"success": True})
            return _Resp(404, {"error": {"message": "unexpected " + url}})
        return req

    def test_facebook_long_video_chunking_and_english_targeting(self):
        log = []
        with mock.patch("requests.request", side_effect=self._router(log)), mock.patch("time.sleep"):
            self.assertEqual(self.fb.publish_long_video(self.f, "My Title", "desc"), "V1")
        transfers = [l for l in log if isinstance(l[2], dict) and l[2].get("upload_phase") == "transfer"]
        self.assertEqual([int(t[2]["start_offset"]) for t in transfers], [0, 4096, 8192])
        self.assertEqual(b"".join(t[4]["video_file_chunk"][1] for t in transfers), self.f.read_bytes())
        fin = [l[2] for l in log if isinstance(l[2], dict) and l[2].get("upload_phase") == "finish"][0]
        self.assertEqual(json.loads(fin["feed_targeting"])["locales"], [6, 24])
        self.assertEqual(json.loads(fin["targeting"])["locales"], [6, 24], "Spanish locale excluded")
        self.assertEqual((fin["published"], fin["title"]), ("true", "My Title"))

    def test_facebook_never_loses_a_post_over_targeting(self):
        log = []
        with mock.patch("requests.request", side_effect=self._router(log, targeting_rejected=True)), mock.patch("time.sleep"):
            self.assertEqual(self.fb.publish_long_video(self.f, "T", "d"), "V1")
        fins = [l[2] for l in log if isinstance(l[2], dict) and l[2].get("upload_phase") == "finish"]
        self.assertTrue(len(fins) == 2 and "targeting" in fins[0] and "targeting" not in fins[1])
        self.fb._locale_cache = None; log.clear()
        with mock.patch("requests.request", side_effect=self._router(log, locales_ok=False)), mock.patch("time.sleep"):
            self.assertEqual(self.fb.publish_long_video(self.f, "T", "d"), "V1")
        fins = [l[2] for l in log if isinstance(l[2], dict) and l[2].get("upload_phase") == "finish"]
        self.assertTrue(len(fins) == 1 and "targeting" not in fins[0])

    def test_facebook_reel_headers_and_draft_state(self):
        self.fb._locale_cache = [6]
        for published, state in ((True, "PUBLISHED"), (False, "DRAFT")):
            log = []
            with mock.patch("requests.request", side_effect=self._router(log)), mock.patch("time.sleep"):
                self.assertEqual(self.fb.publish_reel(self.f, "reel desc", published=published), "RV1")
            up = [l for l in log if "rupload" in l[1]][0]
            self.assertEqual((up[3]["Authorization"], up[3]["offset"], up[3]["file_size"]), ("OAuth TOK", "0", str(self.size)))
            fin = [l[2] for l in log if isinstance(l[2], dict) and l[2].get("upload_phase") == "finish"][0]
            self.assertEqual((fin["video_state"], fin["description"]), (state, "reel desc"))

    def test_unconfigured_platforms_do_nothing(self):
        import src.instagram_publisher as ig
        with mock.patch.dict(os.environ, {"FB_PAGE_ID": "", "FB_ACCESS_TOKEN": "", "IG_USER_ID": ""}), \
                mock.patch("requests.request", side_effect=AssertionError("no network")), mock.patch("requests.post", side_effect=AssertionError("no network")):
            self.assertIsNone(self.fb.publish_long_video(self.f, "T", "d"))
            self.assertIsNone(self.fb.publish_reel(self.f, "d"))
            self.assertIsNone(ig.publish_reel(self.f, "c"))

    def test_instagram_reel_flow_and_failed_container_is_not_published(self):
        import src.instagram_publisher as ig
        def make(statuses):
            calls, it = [], iter(statuses)
            def post(url, **kw):
                calls.append(("POST", url, kw))
                if url.endswith("/IG1/media"): return _Resp(200, {"id": "C1", "uri": "https://rupload.facebook.com/ig-api-upload/v23.0/C1"})
                if "rupload" in url: return _Resp(200, {"success": True})
                if url.endswith("/media_publish"): return _Resp(200, {"id": "M1"})
                return _Resp(404, {})
            def get(url, **kw):
                calls.append(("GET", url, kw)); return _Resp(200, {"status_code": next(it)})
            return calls, post, get
        calls, post, get = make(["IN_PROGRESS", "IN_PROGRESS", "FINISHED"])
        with mock.patch("requests.post", side_effect=post), mock.patch("requests.get", side_effect=get), mock.patch("time.sleep"):
            self.assertEqual(ig.publish_reel(self.f, "x" * 3000), "M1")
        create = calls[0][2]["data"]
        self.assertEqual((create["media_type"], create["upload_type"], len(create["caption"])), ("REELS", "resumable", 2200))
        up = [c for c in calls if "rupload" in c[1]][0][2]["headers"]
        self.assertEqual((up["Authorization"], up["file_size"]), ("OAuth TOK", str(self.size)))
        self.assertEqual([c[0] for c in calls].count("GET"), 3)
        calls, post, get = make(["IN_PROGRESS", "ERROR"])
        with mock.patch("requests.post", side_effect=post), mock.patch("requests.get", side_effect=get), mock.patch("time.sleep"):
            self.assertIsNone(ig.publish_reel(self.f, "c"))
        self.assertFalse(any(c[1].endswith("/media_publish") for c in calls))


# ---------------------------------------------------------------- shorts planning
class ShortsPlanningTests(unittest.TestCase):
    def _items(self, n=14, dur=5.0):
        return [{"beat": {"type": "dialogue" if i % 3 == 0 else "narration", "emotion": "dread" if 8 <= i <= 10 else "calm",
                          "sfx_kind": "action" if i == 9 else "none", "text": f"Beat {i}."}, "duration": dur} for i in range(n)]

    def test_windows_fit_start_at_hook_and_do_not_overlap(self):
        from src.story_shorts import plan_short_windows
        from src.config import SHORT_MAX_SEC
        items = self._items()
        w1, w2 = plan_short_windows(items, 2)
        self.assertEqual(w1[0], 0)
        self.assertLessEqual(sum(items[i]["duration"] for i in w1), SHORT_MAX_SEC)
        self.assertLessEqual(sum(items[i]["duration"] for i in w2), SHORT_MAX_SEC)
        self.assertFalse(set(w1) & set(w2))
        self.assertTrue(set(range(8, 11)) & set(w2), "the second Short targets the high-tension stretch")

    def test_tiny_story_still_yields_two_windows(self):
        from src.story_shorts import plan_short_windows
        self.assertEqual(len(plan_short_windows(self._items(3, 8.0), 2)), 2)
        self.assertEqual(plan_short_windows([], 2), [])


if __name__ == "__main__":
    unittest.main()
