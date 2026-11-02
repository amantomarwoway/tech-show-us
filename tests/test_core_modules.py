"""
Behaviour tests for the core modules the story pipeline stands on: Gemini client,
captions, aligner, image chain, YouTube uploader/analytics, video builder timing.
No network, no keys. Run: python -m unittest discover -s tests -p "test_*.py"
"""
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HAVE_FFMPEG = shutil.which("ffmpeg") is not None


class _Resp:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self._b, self.content = status, body if body is not None else {}, content

    def json(self):
        return self._b


# ------------------------------------------------------------------ Gemini client
class LlmClientTests(unittest.TestCase):
    def _client(self, behaviours, calls):
        it = iter(behaviours)

        class M:
            def generate_content(self, model, contents, config):
                calls.append((model, config))
                b = next(it)
                if isinstance(b, Exception):
                    raise b
                return mock.Mock(text=b)

        c = mock.Mock(); c.models = M()
        return c

    def test_quota_exhaustion_skips_straight_to_fallback_without_waiting(self):
        import src.llm_client as lc
        calls = []
        client = self._client([Exception("429 RESOURCE_EXHAUSTED quota"), "ok from fallback"], calls)
        with mock.patch.object(lc, "_get_client", return_value=client), mock.patch("time.sleep") as sleep:
            self.assertEqual(lc.generate_text("p"), "ok from fallback")
        self.assertEqual([m for m, _ in calls], [lc.GEMINI_PRIMARY_MODEL, lc.GEMINI_FALLBACK_MODEL])
        sleep.assert_not_called()

    def test_transient_503_backs_off_and_retries_the_same_model(self):
        import src.llm_client as lc
        calls, sleeps = [], []
        client = self._client([Exception("503 UNAVAILABLE high demand"), "recovered"], calls)
        with mock.patch.object(lc, "_get_client", return_value=client), mock.patch("time.sleep", side_effect=sleeps.append):
            self.assertEqual(lc.generate_text("p"), "recovered")
        self.assertEqual([m for m, _ in calls], [lc.GEMINI_PRIMARY_MODEL] * 2)
        self.assertEqual(sleeps, [5])

    def test_json_mode_and_output_cap_are_requested(self):
        import src.llm_client as lc
        calls = []
        with mock.patch.object(lc, "_get_client", return_value=self._client(['{"a": 1}'], calls)):
            self.assertEqual(lc.generate_json("p"), {"a": 1})
        cfg = calls[0][1]
        self.assertEqual(cfg["response_mime_type"], "application/json")
        self.assertEqual(cfg["max_output_tokens"], lc.GEMINI_MAX_OUTPUT_TOKENS)
        self.assertGreaterEqual(cfg["max_output_tokens"], 16000)

    def test_json_parsing_survives_fences_and_chatter(self):
        import src.llm_client as lc
        self.assertEqual(lc._parse_json('```json\n{"x": [1, 2]}\n```'), {"x": [1, 2]})
        self.assertEqual(lc._parse_json('Sure! Here it is: {"x": 1} hope it helps'), {"x": 1})
        with self.assertRaises(json.JSONDecodeError):
            lc._parse_json("no json at all")

    def test_generate_json_retries_malformed_output_then_succeeds(self):
        import src.llm_client as lc
        with mock.patch.object(lc, "generate_text", side_effect=["{broken", '{"ok": true}']):
            self.assertEqual(lc.generate_json("p", max_retries=2), {"ok": True})

    def test_generate_json_retries_a_total_api_outage_too(self):
        # regression: an earlier version let RuntimeError escape on the first attempt
        import src.llm_client as lc
        with mock.patch.object(lc, "generate_text", side_effect=[RuntimeError("down"), '{"ok": 1}']), mock.patch("time.sleep"):
            self.assertEqual(lc.generate_json("p", max_retries=2), {"ok": 1})
        with mock.patch.object(lc, "generate_text", side_effect=RuntimeError("down")), mock.patch("time.sleep"):
            with self.assertRaises(RuntimeError): lc.generate_json("p", max_retries=2)


# ------------------------------------------------------------------ captions
class CaptionBuilderTests(unittest.TestCase):
    def _words(self, start, texts, step=0.4):
        return [{"word": w, "start": start + i * step, "end": start + i * step + 0.35} for i, w in enumerate(texts)]

    def test_speaker_prefix_only_on_first_group_of_dialogue(self):
        from src.caption_builder import build_story_captions
        tmp = Path(tempfile.mkdtemp())
        beats = [({"type": "narration", "speaker": "narrator"}, self._words(0, ["The", "night", "was", "dark"])),
                 ({"type": "dialogue", "speaker": "Hariya"}, self._words(2, "What is the secret in your firewood boy".split()))]
        text = build_story_captions(beats, tmp / "c.ass").read_text()
        self.assertEqual(text.count("HARIYA:"), 1)
        self.assertNotIn("NARRATOR", text)
        self.assertIn("PlayResX: 1920", text)

    def test_karaoke_runs_word_start_to_next_word_start(self):
        from src.caption_builder import build_story_captions
        tmp = Path(tempfile.mkdtemp())
        words = [{"word": "a", "start": 1.0, "end": 1.2}, {"word": "b", "start": 2.0, "end": 2.2}]   # 0.8 s silence between
        text = build_story_captions([({"type": "narration", "speaker": "narrator"}, words)], tmp / "c.ass").read_text()
        self.assertIn(r"{\k100}a", text, "the 1.0 s gap is covered so the highlight can't race ahead of the voice")
        self.assertIn(r"{\k20}b", text)
        self.assertIn("0:00:01.00", text); self.assertIn("0:00:02.20", text)

    def test_short_format_hostile_characters_and_bad_theme(self):
        from src.caption_builder import build_story_captions
        tmp = Path(tempfile.mkdtemp())
        words = [{"word": "{evil\\}", "start": 0, "end": 0.3}]
        text = build_story_captions([({"type": "narration", "speaker": "narrator"}, words)], tmp / "c.ass", is_short=True).read_text()
        self.assertIn("PlayResY: 1920", text)
        self.assertNotIn("{evil", text)
        with self.assertRaises(ValueError):
            build_story_captions([], tmp / "x.ass", theme="rainbow")


# ------------------------------------------------------------------ aligner
@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg required")
class AlignerTests(unittest.TestCase):
    def test_fallback_is_proportional_covers_the_clip_and_offset_shifts(self):
        import src.aligner as al
        tmp = Path(tempfile.mkdtemp()); wav = tmp / "a.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=300:duration=4", str(wav)], check=True)
        with mock.patch.object(al, "_get_model", side_effect=ImportError("faster_whisper not installed")):
            words = al.align_words(wav, "one two three four five")
        self.assertEqual([w["word"] for w in words], "one two three four five".split())
        self.assertAlmostEqual(words[-1]["end"], 4.0, places=1)
        self.assertTrue(all(words[i]["end"] <= words[i + 1]["start"] + 1e-9 for i in range(4)))
        shifted = al.offset_words(words, 10.0)
        self.assertAlmostEqual(shifted[0]["start"], 10.0)

    def test_whisper_timing_keeps_the_scripts_spelling(self):
        import src.aligner as al
        tmp = Path(tempfile.mkdtemp()); wav = tmp / "a.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=300:duration=2", str(wav)], check=True)
        seg = mock.Mock(words=[mock.Mock(word=" Garet", start=0.1, end=0.5), mock.Mock(word=" said", start=0.6, end=0.9)])
        model = mock.Mock(); model.transcribe.return_value = ([seg], None)
        with mock.patch.object(al, "_get_model", return_value=model):
            words = al.align_words(wav, "Garrett said")
        self.assertEqual([w["word"] for w in words], ["Garrett", "said"])
        self.assertEqual(words[0]["start"], 0.1)


# ------------------------------------------------------------------ images
class VisualGeneratorTests(unittest.TestCase):
    def setUp(self):
        import src.visual_generator as vg
        self.vg = vg
        self.tmp = Path(tempfile.mkdtemp())
        self.stack = [mock.patch.object(vg, "SCENES_DIR", self.tmp), mock.patch("time.sleep"),
                      mock.patch.dict(os.environ, {"POLLINATIONS_API_KEY": "PK", "PEXELS_API_KEY": "XK", "PIXABAY_API_KEY": "BK"})]
        for p in self.stack: p.start()

    def tearDown(self):
        for p in self.stack: p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _png(self, w=400, h=300):
        from PIL import Image
        buf = io.BytesIO(); Image.effect_noise((w, h), 60).convert("RGB").save(buf, "PNG"); return buf.getvalue()

    def test_pollinations_anonymous_first_then_api_key_and_exact_size(self):
        seen = []
        def get(url, params=None, headers=None, timeout=None):
            seen.append((url, dict(headers or {}), params))
            return _Resp(401) if not headers else _Resp(200, content=self._png())
        with mock.patch("requests.get", side_effect=get):
            path = self.vg.generate_scene_image("a lonely diner at night", 5, 640, 360)
        self.assertEqual([bool(h) for _, h, _ in seen], [False, True], "anonymous first, then the Bearer key")
        self.assertEqual(seen[1][1]["Authorization"], "Bearer PK")
        self.assertEqual(seen[0][2]["model"], "flux")
        from PIL import Image
        with Image.open(path) as im:
            self.assertEqual(im.size, (640, 360))
        self.assertEqual(path.name, "scene5.jpg")

    def test_chain_falls_through_pollinations_pexels_pixabay_in_order(self):
        order = []
        def get(url, params=None, headers=None, timeout=None):
            if "pollinations" in url: order.append("pollinations"); return _Resp(402)
            if "pexels.com/v1/search" in url: order.append("pexels"); return _Resp(403)
            if "pixabay.com/api" in url:
                order.append("pixabay"); return _Resp(200, {"hits": [{"largeImageURL": "https://cdn/p.jpg"}]})
            order.append("download"); return _Resp(200, content=self._png())
        with mock.patch("requests.get", side_effect=get):
            self.vg.generate_scene_image("old farmhouse porch light", 1, 320, 180)
        uniq = [x for i, x in enumerate(order) if x != "pollinations" or i == 0]
        self.assertEqual(uniq[0], "pollinations")
        self.assertLess(order.index("pexels"), order.index("pixabay"))
        self.assertEqual(order[-1], "download")

    def test_all_sources_failing_raises_and_keywords_come_from_the_start_of_the_prompt(self):
        with mock.patch("requests.get", return_value=_Resp(500)):
            with self.assertRaises(RuntimeError): self.vg.generate_scene_image("x", 2, 320, 180)
        kw = self.vg._keywords("a sheriff cruiser parked outside a dark diner, set in the United States: authentic Western people")
        self.assertTrue(kw.startswith("sheriff cruiser parked"), kw)
        self.assertLessEqual(len(kw.split()), 6)


# ------------------------------------------------------------------ YouTube
class YouTubeUploaderTests(unittest.TestCase):
    def _yt(self, responses):
        calls = []
        it = iter(responses)
        class Req:
            def __init__(self, body): self.body = body
            def next_chunk(self):
                r = next(it)
                if isinstance(r, Exception): raise r
                return None, r
        yt = mock.Mock()
        def insert(part, body, media_body):
            calls.append(body); return Req(body)
        yt.videos.return_value.insert.side_effect = insert
        return yt, calls

    def _http_error(self, status, content=b""):
        e = Exception(f"HTTP {status}"); e.resp = mock.Mock(status=status); e.content = content; return e

    def test_body_declares_english_ai_disclosure_and_sanitizes(self):
        import src.youtube_uploader as yu
        yt, calls = self._yt([{"id": "VID1", "status": {"privacyStatus": "public"}}])
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()):
            vid = yu.upload_video(Path("x.mp4"), "<b>Hello</b> " + "t" * 200, "desc <x>", ["a<", "b"], privacy_status="public")
        self.assertEqual(vid, "VID1")
        body = calls[0]
        self.assertEqual((body["snippet"]["defaultLanguage"], body["snippet"]["defaultAudioLanguage"]), ("en", "en"))
        self.assertTrue(body["status"]["containsSyntheticMedia"])
        self.assertFalse(body["status"]["selfDeclaredMadeForKids"])
        self.assertLessEqual(len(body["snippet"]["title"]), 100)
        self.assertNotIn("<", body["snippet"]["title"] + body["snippet"]["description"] + "".join(body["snippet"]["tags"]))
        self.assertEqual(body["snippet"]["categoryId"], "24")

    def test_transient_errors_are_retried_and_synthetic_flag_rejection_falls_back(self):
        import src.youtube_uploader as yu
        yt, calls = self._yt([self._http_error(503), {"id": "V2", "status": {"privacyStatus": "private"}}])
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()), mock.patch("time.sleep"):
            self.assertEqual(yu.upload_video(Path("x.mp4"), "t", "d", [], privacy_status="private"), "V2")
        yt, calls = self._yt([self._http_error(400, b"Invalid value for containsSyntheticMedia"), {"id": "V3", "status": {"privacyStatus": "private"}}])
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()):
            self.assertEqual(yu.upload_video(Path("x.mp4"), "t", "d", [], privacy_status="private"), "V3")
        self.assertTrue(calls[0]["status"].get("containsSyntheticMedia") and "containsSyntheticMedia" not in calls[1]["status"])

    def test_non_transient_errors_propagate(self):
        import src.youtube_uploader as yu
        yt, _ = self._yt([self._http_error(403, b"quotaExceeded")])
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()):
            with self.assertRaises(Exception): yu.upload_video(Path("x.mp4"), "t", "d", [])

    def test_audit_lock_is_reported_loudly(self):
        import src.youtube_uploader as yu
        yt, _ = self._yt([{"id": "LOCKED", "status": {"privacyStatus": "private"}}])
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()):
            with self.assertLogs("src.youtube_uploader", level="ERROR") as cm:
                yu.upload_video(Path("x.mp4"), "t", "d", [], privacy_status="public")
        self.assertIn("audit", " ".join(cm.output).lower())

    def test_credentials_are_built_without_scopes(self):
        import sys, types
        import src.youtube_uploader as yu
        captured = {}
        class Creds:
            def __init__(self, **kw): captured.update(kw)
            def refresh(self, req): captured["refreshed"] = True
        oauth = types.ModuleType("google.oauth2.credentials"); oauth.Credentials = Creds
        transport = types.ModuleType("google.auth.transport.requests"); transport.Request = lambda: object()
        mods = {"google": types.ModuleType("google"), "google.oauth2": types.ModuleType("google.oauth2"), "google.oauth2.credentials": oauth,
                "google.auth": types.ModuleType("google.auth"), "google.auth.transport": types.ModuleType("google.auth.transport"),
                "google.auth.transport.requests": transport}
        with mock.patch.dict(sys.modules, mods), mock.patch.dict(os.environ, {"YT_REFRESH_TOKEN": "r", "YT_CLIENT_ID": "i", "YT_CLIENT_SECRET": "s"}):
            yu._get_credentials()
        self.assertNotIn("scopes", captured, "passing scopes caused invalid_scope refresh failures in production")
        self.assertTrue(captured["refreshed"] and captured["refresh_token"] == "r")


class YouTubeAnalyticsTests(unittest.TestCase):
    def test_retention_is_a_fraction_and_ctr_failure_is_not_fatal(self):
        import src.youtube_analytics as ya
        with mock.patch.object(ya, "_query", return_value=[1200, 410.5, 62.0]):
            s = ya.fetch_video_stats("V")
        self.assertEqual((s["views"], round(s["averageViewPercentage"], 2)), (1200, 0.62))
        with mock.patch.object(ya, "_query", return_value=None):
            self.assertIsNone(ya.fetch_video_stats("V"))
        with mock.patch.object(ya, "_query", side_effect=Exception("400 unknown metric")):
            self.assertIsNone(ya.fetch_ctr("V")); self.assertIsNone(ya.fetch_video_stats("V"))
        with mock.patch.object(ya, "_query", return_value=[4.5]):
            self.assertAlmostEqual(ya.fetch_ctr("V"), 0.045)

    def test_sync_writes_real_numbers_into_the_database(self):
        import src.database as db
        import src.story_analytics_sync as sync
        from datetime import datetime, timedelta, timezone
        tmp = Path(tempfile.mkdtemp())
        with mock.patch.object(db, "DB_PATH", tmp / "t.db"):
            db.init_db()
            db.record_story_upload("OLDLONG", "t", "locked_room", kind="long")
            db.record_story_upload("FRESH", "t", "locked_room", kind="long")
            with db.get_conn() as c:
                c.execute("UPDATE story_videos SET uploaded_at=? WHERE video_id='OLDLONG'", ((datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),))
            with mock.patch.object(sync, "fetch_video_stats", return_value={"views": 900, "averageViewPercentage": 0.55}), \
                    mock.patch.object(sync, "fetch_ctr", return_value=0.06):
                self.assertEqual(sync.run_story_analytics_sync(), 1, "a video younger than 48 h has no stable data yet")
            self.assertEqual(db.get_pillar_stats()["locked_room"]["avg_retention"], 0.55)
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ video timing
@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg required")
class VideoTimingTests(unittest.TestCase):
    def test_frame_counts_never_drift_from_the_total(self):
        import random
        import src.video_builder as vb
        random.seed(1)
        durs = [random.uniform(1.0, 6.0) for _ in range(45)]
        counts = vb.frame_counts(durs)
        self.assertLessEqual(abs(sum(counts) - sum(durs) * vb.FPS), 1.0)
        self.assertTrue(all(c >= 1 for c in counts))
        self.assertEqual(vb.frame_counts([0.001, 0.001]), [1, 1])

    def test_exact_wav_removes_the_mp3_container_overshoot_and_pads_pauses(self):
        from src.story_pipeline import _to_exact_wav
        from src.tts_engine import get_audio_duration_sec
        tmp = Path(tempfile.mkdtemp()); mp3 = tmp / "b.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=300:duration=2.0", "-c:a", "libmp3lame", str(mp3)], check=True)
        plain = _to_exact_wav(mp3)                # same output name each time -> measure before the next call
        d_plain = get_audio_duration_sec(plain)
        import wave
        with wave.open(str(plain)) as wf:
            exact_seconds = wf.getnframes() / wf.getframerate()
        d_pad = get_audio_duration_sec(_to_exact_wav(mp3, 3.0))
        self.assertAlmostEqual(d_pad - d_plain, 3.0, places=2)
        self.assertAlmostEqual(d_plain, exact_seconds, places=3)   # duration == samples / rate, exactly

    def test_build_video_keeps_video_audio_and_timeline_in_sync(self):
        import src.video_builder as vb
        from src.story_pipeline import _to_exact_wav
        from src.tts_engine import get_audio_duration_sec
        from PIL import Image
        tmp = Path(tempfile.mkdtemp()); imgs, wavs, durs = [], [], []
        for i, d in enumerate([2.37, 1.91, 3.13, 2.02, 2.76, 1.55]):
            im = tmp / f"i{i}.jpg"; Image.new("RGB", (320, 180), (20 * i, 40, 90)).save(im); imgs.append(im)
            mp3 = tmp / f"a{i}.mp3"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"sine=frequency={220 + 30 * i}:duration={d}", "-c:a", "libmp3lame", str(mp3)], check=True)
            w = _to_exact_wav(mp3, 2.0 if i == 2 else 0.0); wavs.append(w); durs.append(get_audio_duration_sec(w))
        ass = tmp / "c.ass"
        ass.write_text("[Script Info]\nPlayResX: 320\nPlayResY: 180\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,20,&H00FFFFFF,&H0000D7FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\k50}Hello {\\k50}world\n")
        out = vb.build_video(imgs, wavs, durs, ass, tmp, 320, 180, output_slug="t")
        def sdur(st):
            return float(subprocess.run(["ffprobe", "-v", "error", "-select_streams", st, "-show_entries", "stream=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out)],
                                        capture_output=True, text=True).stdout.split()[0])
        self.assertLess(abs(sdur("v:0") - sum(durs)), 0.06)
        self.assertLess(abs(sdur("a:0") - sum(durs)), 0.06)
        self.assertEqual(vb._filter_path(Path("/a b/c:d's.ass")), "/a b/c\\:d\\'s.ass")


if __name__ == "__main__":
    unittest.main()
