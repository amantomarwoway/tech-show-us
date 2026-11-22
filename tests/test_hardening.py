"""
Failure-mode tests: everything that could make a 2-hour CI run fail (or silently
publish something wrong) is exercised here with injected faults.
Run: python -m unittest discover -s tests -p "test_*.py"
"""
import os
import random
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

HAVE_FFMPEG = shutil.which("ffmpeg") is not None


def with_elements(story: dict) -> dict:
    """Tag a fake story's beats so it passes the strict validation (five emotions, a jumpscare, a hook)."""
    cycle = ["fear", "curiosity", "suspense", "excitement", "mystery"]
    for i, b in enumerate(story["beats"]):
        if not isinstance(b, dict):
            continue
        b["elements"] = ["suspense", "mystery"] if i < 4 else [cycle[i % 5]]
        b["jumpscare"] = (i == 10)
    story.setdefault("series", {"title": "The Steel Vault", "planned_parts": 4, "arc": ["Part 1: a", "Part 2: b"]})
    story.setdefault("series_update", {"recap": "recap", "open_threads": ["t"], "cliffhanger": "c"})
    return story


class _Resp:
    def __init__(self, status=200, body=None):
        self.status_code, self._b = status, body if body is not None else {}

    def json(self):
        return self._b


# ---------------------------------------------------------------- TTS
class TtsResilienceTests(unittest.TestCase):
    def setUp(self):
        import src.tts_engine as tts
        self.tts = tts
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(tts, "TEMP_DIR", self.tmp); self.p.start()

    def tearDown(self):
        self.p.stop(); shutil.rmtree(self.tmp, ignore_errors=True)

    def _saver(self, plan, calls):
        """plan: list of 'fail' / 'ok' per attempt."""
        it = iter(plan)
        async def save(text, out_path, voice, *, rate="+0%", pitch="+0Hz"):
            calls.append((text, voice, rate, pitch))
            if next(it) == "fail":
                raise RuntimeError("NoAudioReceived")
            Path(out_path).write_bytes(b"\x01" * 2048)
        return save

    def test_transient_edge_failures_are_retried_not_dropped(self):
        calls = []
        with mock.patch.object(self.tts, "_edge_tts_save", side_effect=self._saver(["fail", "fail", "ok"], calls)), mock.patch("time.sleep") as sl:
            out = self.tts.synthesize_voiceover("Hello there.", "b1.mp3", voice="en-US-GuyNeural", rate="-8%", pitch="-5Hz")
        self.assertTrue(out.exists() and len(calls) == 3)
        self.assertEqual(calls[0][1:], ("en-US-GuyNeural", "-8%", "-5Hz"))
        self.assertEqual([c.args[0] for c in sl.call_args_list], [2, 4])

    def test_gives_up_after_three_attempts_then_piper_absent_means_a_clean_error(self):
        calls = []
        with mock.patch.object(self.tts, "_edge_tts_save", side_effect=self._saver(["fail"] * 3, calls)), \
                mock.patch("time.sleep"), mock.patch("shutil.which", return_value=None), \
                mock.patch.object(self.tts, "_ensure_piper_model", side_effect=AssertionError("must not download a model when piper isn't installed")):
            with self.assertRaises(RuntimeError): self.tts.synthesize_voiceover("Hello.", "b2.mp3")
        self.assertEqual(len(calls), 3)

    def test_stale_chunk_from_a_previous_beat_is_never_reused(self):
        stale = self.tmp / "tts_chunk_b3_0.mp3"; stale.write_bytes(b"STALE" * 400)
        async def save(text, out_path, voice, **kw):
            raise RuntimeError("service down")   # writes nothing
        with mock.patch.object(self.tts, "_edge_tts_save", side_effect=save), mock.patch("time.sleep"), mock.patch("shutil.which", return_value=None):
            with self.assertRaises(RuntimeError): self.tts.synthesize_voiceover("Hello.", "b3.mp3")
        self.assertFalse((self.tmp / "b3.mp3").exists(), "a stale file must not be returned as this beat's voice")

    def test_text_is_cleaned_for_speech(self):
        c = self.tts.clean_for_speech
        self.assertEqual(c('He said *run* & hid <behind> the _old_ door #3.\n  Next'), "He said run and hid behind the old door 3. Next")
        self.assertEqual(c(None), "")


# ---------------------------------------------------------------- story repair
class StoryRepairTests(unittest.TestCase):
    FILLER = " ".join(["word"] * 60)

    def _story(self):
        beats = [{"type": "dialogue", "speaker": "Sheriff Garrett", "text": f"Sheriff Tom Garrett: *Stay* back. {self.FILLER}"},
                 {"speaker": "Sarah", "text": f"I _won't_. {self.FILLER}"},
                 {"type": "dialogue", "speaker": "Stranger", "text": f"You should leave. {self.FILLER}"},
                 {"type": "narration", "text": "   "}, "garbage",
                 {"text": f"The lights died. {self.FILLER}", "visual_description": ""}]
        beats += [{"type": "narration", "speaker": "narrator", "text": self.FILLER, "visual_description": "x"} for _ in range(20)]
        return {"characters": [{"name": "Sheriff Tom Garrett", "gender": "MALE"}, {"name": "Sarah", "gender": "female"}, {"gender": "male"}], "beats": beats}

    def test_a_sloppy_but_usable_story_is_repaired_and_accepted(self):
        from src.story_writer import _normalize_story, _validate_story
        s = self._story(); _normalize_story(s); _validate_story(s)
        b = s["beats"]
        self.assertEqual((b[0]["type"], b[0]["speaker"]), ("dialogue", "Sheriff Tom Garrett"))
        self.assertTrue(b[0]["text"].startswith("Stay back"), "markdown + leading 'Name:' removed")
        self.assertEqual((b[1]["type"], b[1]["speaker"]), ("dialogue", "Sarah"), "missing type inferred from speaker")
        self.assertEqual((b[2]["type"], b[2]["speaker"]), ("narration", "narrator"), "unknown speaker -> the narrator reads the line")
        lights = next(x for x in b if x["text"].startswith("The lights died"))
        self.assertTrue(lights["visual_description"].startswith("a cinematic scene: The lights died"),
                        "a missing visual_description is built from the beat's own text")
        self.assertEqual([x["beat_number"] for x in b], list(range(1, len(b) + 1)))
        self.assertEqual([c["gender"] for c in s["characters"]], ["male", "female"])

    def test_stage_directions_are_removed_so_the_tts_never_reads_them_aloud(self):
        from src.story_writer import _normalize_story
        beats = [{"type": "narration", "text": "(whispering) Don't move. [beat] The door creaked (slowly) open.", "visual_description": "x"},
                 {"type": "narration", "text": "He counted twelve (12) steps.", "visual_description": "x"}]
        story = {"characters": [], "beats": beats}
        _normalize_story(story)
        self.assertEqual(story["beats"][0]["text"], "Don't move. The door creaked open.")
        self.assertIn("(12)", story["beats"][1]["text"], "numbers/longer parentheses are real content and stay")

    def test_write_story_accepts_a_list_wrapped_answer_and_rejects_junk(self):
        import src.story_writer as sw
        good = with_elements(self._story())
        with mock.patch.object(sw, "generate_json", return_value=[good]), mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room"):
            self.assertEqual(sw.write_story("horror")["pillar"], "locked_room")
        with mock.patch.object(sw, "generate_json", return_value="just text"), mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room"):
            with self.assertRaises(RuntimeError): sw.write_story("horror")

    LONG = ("The vault door sealed behind them with a heavy metallic clang that echoed through the corridor. "
            "Marcus pressed his ear against the cold steel and heard something moving inside. "
            "Detective Miller slammed her fist against the door and shouted for backup, but nobody answered. "
            "Then the lights died, one by one, until only a single red bulb glowed above the panic room.")

    def test_long_narration_is_split_and_audio_direction_follows_the_text(self):
        from src.story_writer import _split_long_beats
        from src.config import STORY_MAX_BEAT_WORDS
        b = {"type": "narration", "speaker": "narrator", "text": self.LONG, "visual_description": "a steel vault door in a basement",
             "bgm_keyword": "eerie piano", "sfx_keyword": "door slam", "sfx_kind": "action", "sfx_trigger_word": "slammed", "pause_after_sec": 3.0}
        parts = _split_long_beats([b])
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(all(len(p["text"].split()) <= STORY_MAX_BEAT_WORDS for p in parts))
        self.assertTrue(all(p["text"].rstrip()[-1] in ".!?" for p in parts), "never cut mid-sentence")
        self.assertEqual(" ".join(p["text"] for p in parts), self.LONG, "no words lost or reordered")
        self.assertEqual(len({p["visual_description"] for p in parts}), len(parts), "every piece gets its own image prompt")
        self.assertEqual(parts[0]["visual_description"], "a steel vault door in a basement")
        hit = [p for p in parts if p["sfx_kind"] == "action"]
        self.assertEqual(len(hit), 1); self.assertIn("slammed", hit[0]["text"])
        self.assertEqual([p["pause_after_sec"] for p in parts][:-1], [0] * (len(parts) - 1))
        self.assertEqual(parts[-1]["pause_after_sec"], 3.0)
        self.assertTrue(all(p["bgm_keyword"] == "eerie piano" for p in parts))

    def test_dialogue_and_short_beats_are_never_split_and_huge_sentences_are_wrapped(self):
        from src.story_writer import _split_long_beats
        d = {"type": "dialogue", "speaker": "Sarah", "text": " ".join(["word"] * 80), "visual_description": "x"}
        n = {"type": "narration", "speaker": "narrator", "text": "Short beat.", "visual_description": "x"}
        self.assertEqual(len(_split_long_beats([d, n])), 2)
        huge = {"type": "narration", "speaker": "narrator", "text": ", ".join(["a very long winding sentence part"] * 12), "visual_description": "x"}
        self.assertGreater(len(_split_long_beats([huge])), 2)

    def test_a_typical_thirty_second_beat_story_becomes_a_many_image_story_and_validates(self):
        from src.story_writer import _normalize_story, _validate_story
        sentence = "The porch light flickered twice before the old house fell silent again. "
        beats = [{"type": "narration", "speaker": "narrator", "text": sentence * 6, "visual_description": f"scene {i}"} for i in range(1, 36)]
        story = {"characters": [{"name": "Sarah", "gender": "female"}], "beats": beats}
        _normalize_story(story); _validate_story(story)
        self.assertGreater(len(story["beats"]), 70, "35 long beats became 70+ short ones (a new image every ~12 s)")

    def test_acceptance_window_is_wider_than_the_prompt_target_but_not_unlimited(self):
        from src.story_writer import _normalize_story, _validate_story
        s = self._story(); s["beats"] = s["beats"][:8]; _normalize_story(s)
        with self.assertRaises(ValueError): _validate_story(s)       # far too short a story is still rejected


class PromptAndImageSafetyTests(unittest.TestCase):
    def test_long_descriptions_are_trimmed_but_the_western_suffix_survives(self):
        from src.story_pipeline import MAX_IMAGE_PROMPT_CHARS, styled_prompt
        from src.config import STORY_VISUAL_STYLE_SUFFIX
        out = styled_prompt("a sheriff cruiser parked outside a diner " * 60)
        self.assertTrue(out.endswith(STORY_VISUAL_STYLE_SUFFIX))
        self.assertLessEqual(len(out), MAX_IMAGE_PROMPT_CHARS)
        self.assertTrue(out.startswith("a sheriff cruiser parked outside a diner"))
        self.assertEqual(styled_prompt("short one."), "short one" + STORY_VISUAL_STYLE_SUFFIX)

    def test_pollinations_429_pauses_before_trying_again(self):
        import src.visual_generator as vg
        from PIL import Image
        import io
        vg._pollinations_off_reason = None; vg._pollinations_notes_shown.clear()
        buf = io.BytesIO(); Image.effect_noise((300, 200), 60).convert("RGB").save(buf, "PNG")
        class R:
            text = ""
            def __init__(self, code, content=b"", headers=None): self.status_code, self.content, self.headers = code, content, headers or {}
        def reply(url, **kw):
            if "account/balance" in url: return R(200, b"{}")
            return next(replies)
        replies = iter([R(429, headers={"Retry-After": "7"}), R(200, buf.getvalue())])
        sleeps = []
        with mock.patch.dict(os.environ, {"POLLINATIONS_API_KEY": "K"}), mock.patch("requests.get", side_effect=reply), \
                mock.patch("time.sleep", side_effect=sleeps.append):
            img = vg._pollinations("a dark road", 320, 180)
        self.assertIsNotNone(img)
        self.assertIn(7, sleeps)


# ---------------------------------------------------------------- voices
class VoiceTests(unittest.TestCase):
    def test_gender_matched_distinct_voices_and_safe_fallback(self):
        from src.character_voices import assign_voices, voice_for_beat
        from src.config import STORY_FEMALE_VOICES, STORY_MALE_VOICES, STORY_NARRATOR_VOICE
        chars = [{"name": "Raju", "gender": "male"}, {"name": "Hariya", "gender": "male"}, {"name": "Meena", "gender": "female"}, {"name": "Kavya", "gender": "female"}]
        vm = assign_voices(chars)
        self.assertIn(vm["Meena"], STORY_FEMALE_VOICES); self.assertIn(vm["Kavya"], STORY_FEMALE_VOICES)
        self.assertIn(vm["Raju"], STORY_MALE_VOICES); self.assertIn(vm["Hariya"], STORY_MALE_VOICES)
        self.assertEqual(len(set(vm.values())), 4, "two same-gender characters never share a voice")
        self.assertNotIn(STORY_NARRATOR_VOICE, vm.values())
        self.assertEqual(voice_for_beat({"type": "narration", "speaker": "narrator"}, vm), STORY_NARRATOR_VOICE)
        self.assertEqual(voice_for_beat({"type": "dialogue", "speaker": "Meena"}, vm), vm["Meena"])
        self.assertEqual(voice_for_beat({"type": "dialogue", "speaker": "Nobody"}, vm), STORY_NARRATOR_VOICE)

    def test_five_characters_of_one_gender_still_get_five_distinct_voices(self):
        from src.character_voices import assign_voices
        vm = assign_voices([{"name": f"M{i}", "gender": "male"} for i in range(5)])
        self.assertEqual(len(set(vm.values())), 5)


# ---------------------------------------------------------------- learning loop
class PatternAnalyticsTests(unittest.TestCase):
    def setUp(self):
        import src.database as db
        self.db = db; self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(db, "DB_PATH", self.tmp / "t.db"); self.p.start(); db.init_db()

    def tearDown(self):
        self.p.stop(); shutil.rmtree(self.tmp, ignore_errors=True)

    def test_explores_evenly_without_data_then_favours_winners_but_never_locks_out_others(self):
        from src.pattern_analytics import suggest_next_pillar
        from src.config import STORY_PILLARS
        random.seed(7)
        none = Counter(suggest_next_pillar() for _ in range(600))
        self.assertTrue(all(40 < none[p] < 220 for p in STORY_PILLARS), none)
        for i in range(5):
            self.db.record_story_upload(f"a{i}", "t", "locked_room"); self.db.update_story_performance(f"a{i}", avg_view_percentage=0.7)
            self.db.record_story_upload(f"b{i}", "t", "twist_crime"); self.db.update_story_performance(f"b{i}", avg_view_percentage=0.25)
        some = Counter(suggest_next_pillar() for _ in range(1500))
        self.assertGreater(some["locked_room"], some["twist_crime"])
        self.assertTrue(all(some[p] > 0 for p in STORY_PILLARS), "exploration floor: no pillar is ever written off")


# ---------------------------------------------------------------- research + node bridge
class ResearchTests(unittest.TestCase):
    def _youtube(self, items, videos):
        yt = mock.MagicMock()
        yt.search().list().execute.return_value = {"items": items}
        yt.videos().list().execute.return_value = {"items": videos}
        return yt

    def test_aggregates_real_tags_and_title_words_and_survives_missing_fields(self):
        import src.topic_research as tr
        items = [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}, {"id": {}}]
        videos = [{"id": "v1", "snippet": {"title": "Dark Village Secret Story", "channelTitle": "A", "tags": ["mystery", "village"]}, "statistics": {"viewCount": "5000"}},
                  {"id": "v2", "snippet": {"title": "Village Crime Mystery", "tags": ["mystery", "crime"]}, "statistics": {}}]
        with mock.patch.object(tr, "_get_youtube_client", return_value=self._youtube(items, videos)), mock.patch.object(tr, "_scrape_niche_browser", return_value=None):
            r = tr.research_niche("mystery story")
        self.assertEqual(r["sample_size"], 2)
        self.assertEqual(r["suggested_tags"][0], "mystery")
        self.assertIn("village", r["suggested_keywords"])
        self.assertEqual(r["top_videos"][0]["view_count"], 5000)
        self.assertIsNone(r["browser_scraper_videos"])

    def test_non_english_results_are_dropped_and_english_is_requested(self):
        import src.topic_research as tr
        items = [{"id": {"videoId": f"v{i}"}} for i in range(4)]
        videos = [{"id": "v0", "snippet": {"title": "Movie Explained In Tamil", "tags": ["tamil", "suspense"]}, "statistics": {"viewCount": "9"}},
                  {"id": "v1", "snippet": {"title": "Dark Basement Suspense Story", "defaultAudioLanguage": "hi", "tags": ["suspense"]}, "statistics": {"viewCount": "8"}},
                  {"id": "v2", "snippet": {"title": "सस्पेंस कहानी भाग 3", "tags": []}, "statistics": {"viewCount": "7"}},
                  {"id": "v3", "snippet": {"title": "The Basement Door Suspense Story", "defaultAudioLanguage": "en-US", "tags": ["suspense", "scary stories"]}, "statistics": {"viewCount": "6"}}]
        yt = self._youtube(items, videos)
        with mock.patch.object(tr, "_get_youtube_client", return_value=yt), mock.patch.object(tr, "_scrape_niche_browser", return_value=None):
            r = tr.research_niche("suspense story narration")
        self.assertEqual([v["video_id"] for v in r["top_videos"]], ["v3"])
        self.assertEqual(r["suggested_tags"], ["suspense", "scary stories"])
        kw = yt.search.return_value.list.call_args.kwargs
        self.assertEqual((kw["relevanceLanguage"], kw["regionCode"]), ("en", "US"))

    def test_no_results_is_a_value_not_an_error(self):
        import src.topic_research as tr
        with mock.patch.object(tr, "_get_youtube_client", return_value=self._youtube([], [])), mock.patch.object(tr, "_scrape_niche_browser", return_value=None):
            r = tr.research_niche("zzz")
        self.assertEqual((r["sample_size"], r["suggested_tags"]), (0, []))


class NodeBridgeTests(unittest.TestCase):
    def test_missing_scraper_never_breaks_the_run(self):
        import src.node_bridge as nb
        with mock.patch.object(nb, "is_available", return_value=False):
            self.assertIsNone(nb.scrape_niche("x"))
        with mock.patch.object(nb, "is_available", return_value=True):
            ok = mock.Mock(returncode=0, stdout='{"videos": [{"videoId": "a"}]}', stderr="")
            with mock.patch("subprocess.run", return_value=ok):
                self.assertEqual(nb.scrape_niche("x"), [{"videoId": "a"}])
            for bad in (mock.Mock(returncode=1, stdout="", stderr="boom"), mock.Mock(returncode=0, stdout="{{{", stderr="")):
                with mock.patch("subprocess.run", return_value=bad):
                    self.assertIsNone(nb.scrape_niche("x"))
            with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("node", 60)):
                self.assertIsNone(nb.scrape_niche("x"))


# ---------------------------------------------------------------- metadata + publishers
class MetadataSafetyTests(unittest.TestCase):
    def test_null_fields_from_the_model_never_crash_metadata(self):
        from src.platform_metadata import build_long_posts, build_short_posts
        story = {"genre": "horror", "tags": None, "search_keywords": None, "description": None, "title_long": None, "title": None, "hook": None}
        research = {"suggested_tags": None}
        long = build_long_posts(story, research)
        self.assertTrue(long["youtube"]["title"] and "Hey Darky" in long["youtube"]["description"])
        sp = build_short_posts(story, research, {"hook": ""}, None)
        self.assertTrue(sp["youtube"]["title"].endswith("#Shorts") and not sp["youtube"]["title"].startswith(" "))
        self.assertNotIn("youtu.be", sp["youtube"]["description"])


class TagRelevanceTests(unittest.TestCase):
    def test_off_niche_research_tags_never_reach_hashtags_or_tags(self):
        from src.platform_metadata import build_hashtags, build_tags
        research = {"suggested_tags": ["movie explained in tamil", "sunday suspense", "hollywood movies explained", "horror", "true crime", "trailer"]}
        story = {"genre": "suspense", "tags": ["suspense story"], "search_keywords": []}
        tags = " ".join(build_hashtags(story, research, 8)).lower() + " " + " ".join(build_tags(story, research))
        self.assertNotIn("tamil", tags); self.assertNotIn("hollywood", tags); self.assertNotIn("trailer", tags)
        self.assertIn("sundaysuspense", tags.replace(" ", "")); self.assertIn("truecrime", tags.replace(" ", ""))


class FacebookGuardTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"FB_PAGE_ID": "P", "FB_ACCESS_TOKEN": "T"}); self.env.start()
        import src.facebook_publisher as fb
        self.fb = fb; fb._locale_cache = [6]; fb._page_token_cache = "T"
        self.f = Path(tempfile.mkdtemp()) / "v.mp4"; self.f.write_bytes(b"x" * 20000)

    def tearDown(self):
        self.env.stop(); shutil.rmtree(self.f.parent, ignore_errors=True)

    def test_a_server_that_stops_making_progress_cannot_hang_the_run(self):
        def req(method, url, **kw):
            d = kw.get("data") or {}
            if d.get("upload_phase") == "start":
                return _Resp(200, {"upload_session_id": "S", "video_id": "V", "start_offset": "0", "end_offset": "4096"})
            return _Resp(200, {"start_offset": "0", "end_offset": "4096"})        # never advances
        with mock.patch("requests.request", side_effect=req), mock.patch("time.sleep"):
            self.assertIsNone(self.fb.publish_long_video(self.f, "t", "d"))

    def test_reel_upload_resends_the_whole_body_on_retry(self):
        bodies, state = [], {"n": 0}
        def req(method, url, **kw):
            d = kw.get("data")
            if isinstance(d, dict) and d.get("upload_phase") == "start":
                return _Resp(200, {"video_id": "R", "upload_url": "https://rupload.facebook.com/x"})
            if "rupload" in url:
                bodies.append(kw["data"]); state["n"] += 1
                return _Resp(500, {}) if state["n"] == 1 else _Resp(200, {"success": True})
            return _Resp(200, {"success": True})
        with mock.patch("requests.request", side_effect=req), mock.patch("time.sleep"):
            self.assertEqual(self.fb.publish_reel(self.f, "d"), "R")
        self.assertEqual(len(bodies), 2)
        self.assertTrue(all(isinstance(b, bytes) and len(b) == 20000 for b in bodies), "both attempts carried the full file")


class FacebookPageTokenTests(unittest.TestCase):
    def setUp(self):
        import src.facebook_publisher as fb
        self.fb = fb; fb._page_token_cache = None; fb._hint_shown = False
        self.env = mock.patch.dict(os.environ, {"FB_PAGE_ID": "P1", "FB_ACCESS_TOKEN": "USERTOK"}); self.env.start()

    def tearDown(self):
        self.env.stop(); self.fb._page_token_cache = None; self.fb._hint_shown = False

    def test_a_user_token_is_exchanged_for_the_page_token_once(self):
        # real run: '(#100) No permission to publish the video' = a USER token was used to post to a Page
        with mock.patch("requests.get", return_value=_Resp(200, {"access_token": "PAGETOK", "id": "P1"})) as g:
            self.assertEqual(self.fb._creds(), ("P1", "PAGETOK"))
            self.assertEqual(self.fb._creds(), ("P1", "PAGETOK"))
        self.assertEqual(g.call_count, 1, "looked up once, then cached")
        self.assertEqual(g.call_args.kwargs["params"]["fields"], "access_token")

    def test_when_no_page_token_can_be_derived_the_configured_token_is_used(self):
        for resp in (_Resp(400, {"error": {"code": 100}}), _Resp(200, {"id": "P1"})):
            self.fb._page_token_cache = None
            with mock.patch("requests.get", return_value=resp):
                self.assertEqual(self.fb._creds(), ("P1", "USERTOK"))
        self.fb._page_token_cache = None
        import requests
        with mock.patch("requests.get", side_effect=requests.ConnectionError("down")):
            self.assertEqual(self.fb._creds(), ("P1", "USERTOK"))

    def test_a_permission_error_explains_exactly_what_to_fix_once(self):
        with self.assertLogs("src.facebook_publisher", level="ERROR") as cm:
            self.fb._permission_hint({"message": "(#200) Subject does not have permission to post videos"})
            self.fb._permission_hint({"message": "(#100) No permission to publish the video"})
        self.assertEqual(len(cm.output), 1)
        self.assertIn("PAGE access token", cm.output[0]); self.assertIn("publish_video", cm.output[0])


# ---------------------------------------------------------------- the chaos test
@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg required")
class PipelineChaosTest(unittest.TestCase):
    """Real pipeline code + real ffmpeg, with one voice-over failure and one image
    failure injected: the story must still render, in sync, minus only the beat
    that could not be voiced."""

    def test_one_beat_without_voice_and_one_without_image_does_not_stop_the_run(self):
        import src.aligner as aligner
        import src.story_pipeline as sp
        tmp = Path(tempfile.mkdtemp())
        filler = "the old house stood silent at the end of the road tonight"
        beats = [{"beat_number": i, "type": "narration", "speaker": "narrator", "text": f"Beat {i} {filler}",
                  "visual_description": f"scene {i} diner", "emotion": "dread", "bgm_keyword": "dark ambient drone" if i < 4 else "eerie piano",
                  "sfx_keyword": "none", "sfx_kind": "none", "sfx_trigger_word": "", "pause_after_sec": 2.0 if i == 3 else 0} for i in range(1, 7)]
        story = {"title": "Chaos Story", "characters": [{"name": "Sarah", "gender": "female"}], "beats": beats}

        def tts(text, name, voice=None, rate="+0%", pitch="+0Hz"):
            if "Beat 2 " in text:
                raise RuntimeError("TTS service down for this beat")
            dest = tmp / name
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=frequency=250:duration=1.6", "-c:a", "libmp3lame", str(dest)], check=True)
            return dest

        def image(prompt, n, width=1920, height=1080):
            if "scene 4" in prompt:
                raise RuntimeError("all image sources failed")
            from PIL import Image
            p = tmp / f"img_{n}.jpg"; Image.new("RGB", (width, height), (40, 40, 90)).save(p); return p

        patches = [mock.patch.object(sp, "synthesize_voiceover", side_effect=tts), mock.patch.object(sp, "generate_scene_image", side_effect=image),
                   mock.patch.object(aligner, "_get_model", side_effect=ImportError("no whisper in tests")),
                   mock.patch.object(sp, "TEMP_DIR", tmp), mock.patch.object(sp, "OUTPUT_DIR", tmp),
                   mock.patch.object(sp, "LONG_WIDTH", 320), mock.patch.object(sp, "LONG_HEIGHT", 180),
                   mock.patch("src.video_builder.TEMP_DIR", tmp), mock.patch("src.audio_fetcher.AUDIO_CACHE_DIR", tmp),
                   mock.patch.dict(os.environ, {"FREESOUND_API_KEY": ""})]
        for p in patches: p.start()
        try:
            assets = sp.prepare_story_assets(story)
            self.assertEqual(len(assets["items"]), 5, "the beat that could not be voiced is dropped, not fatal")
            self.assertNotIn("Beat 2 ", " ".join(i["beat"]["text"] for i in assets["items"]))
            images = [i["image"] for i in assets["items"]]
            self.assertEqual(len(set(images)), 4, "the failed image reuses a neighbour's image")
            out = sp.render_long_video(assets)
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(out)],
                                       capture_output=True, text=True).stdout)
            expected = sum(i["duration"] for i in assets["items"])
            self.assertAlmostEqual(dur, expected, delta=0.25)
            self.assertGreater(expected, 5 * 1.6, "the 2 s dramatic pause is part of the timeline")
        finally:
            for p in patches: p.stop()
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
