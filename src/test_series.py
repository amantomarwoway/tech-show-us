"""
Tests for the series show: weekly slots (US Eastern, DST-safe), the continue / extend / wrap-up decisions,
the series bible, episode writing (five emotions, jumpscare, 30-second hook, feedback retry), scheduled
publishing parameters, series-aware metadata, Shorts selection and their end banner.
"""
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import src.database as db
from src import schedule
from src import series_planner as sp

UTC = timezone.utc


class _DbCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.p = mock.patch.object(db, "DB_PATH", self.tmp / "t.db"); self.p.start(); db.init_db()

    def tearDown(self):
        self.p.stop(); shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------- schedule
class ScheduleTests(_DbCase):
    def test_default_slots_are_late_night_us_eastern(self):
        self.assertEqual([(s["weekday"], s["hour_local"]) for s in db.get_slots()], [(2, 20), (4, 20), (6, 20)])

    def test_slots_keep_their_local_time_across_daylight_saving(self):
        summer, winter = datetime(2026, 7, 1, 12, tzinfo=UTC), datetime(2026, 12, 1, 12, tzinfo=UTC)
        a, b = schedule.next_occurrence(4, 20, 0, summer), schedule.next_occurrence(4, 20, 0, winter)
        self.assertEqual((a.weekday(), a.hour), (5, 0), "Friday 8 PM EDT = 00:00 UTC Saturday")
        self.assertEqual((b.weekday(), b.hour), (5, 1), "Friday 8 PM EST = 01:00 UTC Saturday")
        sun = schedule.next_occurrence(6, 20, 0, datetime(2026, 10, 30, 12, tzinfo=UTC))   # DST ends Sun 1 Nov 2026
        self.assertEqual((sun.day, sun.hour), (2, 1))

    def test_next_occurrence_is_strictly_in_the_future(self):
        t = datetime(2026, 11, 4, 20, 0, tzinfo=UTC)
        for wd, h in ((2, 15), (2, 20), (2, 21)):
            self.assertGreater(schedule.next_occurrence(wd, h, 0, t), t)

    def test_open_slots_respect_the_window_the_lead_time_and_what_is_filled(self):
        wed = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
        open_ = schedule.open_long_slots(wed)
        self.assertEqual([i for i, _ in open_], [0, 1])
        db.record_story_upload("V", "t", "p", series_id=1, part_no=1, slot_index=0, publish_at=open_[0][1].isoformat())
        self.assertEqual([i for i, _ in schedule.open_long_slots(wed)], [1], "a filled slot is no longer open")
        just_before = open_[1][1] - timedelta(minutes=30)
        self.assertNotIn(1, [i for i, _ in schedule.open_long_slots(just_before)], "too close to build and upload")
        sunday = wed - timedelta(days=3)                       # Sunday 1 Nov 10:00 UTC: Sunday 8 PM ET is the next slot
        self.assertEqual(schedule.next_open_long_slot(sunday, force=True)[0], 2)

    def test_there_is_one_short_per_day_skipping_taken_days(self):
        wed = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
        after = datetime(2026, 11, 5, 1, 0, tzinfo=UTC)
        s = schedule.next_short_slots(after, 3, now=wed)
        self.assertEqual(len({t.date() for t in s}), 3)
        self.assertTrue(all(t.hour in (21, 22) for t in s), "5 PM Eastern")
        db.record_story_upload("S", "s", "p", kind="short", publish_at=s[0].isoformat())
        self.assertGreater(schedule.next_short_slots(after, 1, now=wed)[0], s[0])

    def test_seven_shorts_a_week_cover_every_day(self):
        from src.config import SHORTS_PER_EPISODE_BY_SLOT
        self.assertEqual(sum(SHORTS_PER_EPISODE_BY_SLOT), 7)

    def test_a_slot_is_swapped_only_after_enough_data_and_only_for_the_worst(self):
        self.assertIsNone(schedule.evaluate_slots())
        for idx, views in ((0, 1000), (1, 2000), (2, 300)):
            for k in range(4):
                v = f"L{idx}{k}"; db.record_story_upload(v, "t", "p", series_id=1, part_no=k, slot_index=idx)
                db.update_story_performance(v, avg_view_percentage=0.5, views=views)
        plan = schedule.evaluate_slots()
        self.assertEqual(plan["slot_index"], 2)
        self.assertNotIn(plan["new"][0], (2, 4), "the replacement day differs from the other slots")
        self.assertNotIn(plan["new"], db.get_slot_history())
        schedule.apply_slot_swap(plan)
        self.assertEqual(db.get_slots()[2]["weekday"], plan["new"][0])
        self.assertIn(plan["old"], db.get_slot_history())
        self.assertEqual(schedule.describe_slot(4, 20), "Friday 8 PM ET")


# ---------------------------------------------------------------- planner
class PlannerTests(_DbCase):
    NOW = datetime(2026, 11, 20, 12, tzinfo=UTC)

    def _add(self, series, part, ret, views, age_days=7):
        vid = f"V{series}_{part}"
        db.record_story_upload(vid, "t", "p", series_id=series, part_no=part, slot_index=0, publish_at=(self.NOW - timedelta(days=age_days)).isoformat())
        db.update_story_performance(vid, avg_view_percentage=ret, views=views)

    def test_a_free_slot_starts_a_new_story(self):
        p = sp.plan_for_slot(0)
        self.assertEqual((p.series, p.part_no, p.mode), (None, 1, "opening"))

    def test_without_numbers_a_story_follows_its_plan(self):
        sid = db.create_series("S", "horror", "p", 5, 0, {}); db.update_series(sid, parts_done=1)
        p = sp.plan_for_slot(0, now=self.NOW)
        self.assertEqual((p.part_no, p.mode, p.planned_parts), (2, "middle", 5))

    def test_a_flop_is_wrapped_up_so_a_story_can_end_after_two_parts(self):
        sid = db.create_series("S", "horror", "p", 5, 0, {}); db.update_series(sid, parts_done=1)
        self._add(sid, 1, 0.15, 20)
        v = sp.craze(sid, now=self.NOW)
        self.assertEqual(v["label"], "cold")
        p = sp.plan_for_slot(0, now=self.NOW)
        self.assertEqual((p.part_no, p.mode), (2, "finale"))

    def test_numbers_that_are_too_fresh_are_ignored(self):
        sid = db.create_series("S", "horror", "p", 5, 0, {}); db.update_series(sid, parts_done=1)
        self._add(sid, 1, 0.05, 1, age_days=1)
        self.assertEqual(sp.craze(sid, now=self.NOW)["label"], "unknown")

    def test_a_hit_is_extended_instead_of_ending(self):
        sid = db.create_series("S", "horror", "p", 3, 0, {}); db.update_series(sid, parts_done=3)
        for part in (1, 2, 3):
            self._add(sid, part, 0.62, 5000 * part)
        self.assertEqual(sp.craze(sid, now=self.NOW)["label"], "hot")
        p = sp.plan_for_slot(0, now=self.NOW)
        self.assertEqual((p.part_no, p.mode, p.planned_parts), (4, "middle", 5))
        self.assertEqual(db.get_series(sid)["planned_parts"], 5)

    def test_a_lukewarm_story_ends_at_its_planned_length(self):
        sid = db.create_series("S", "horror", "p", 3, 0, {}); db.update_series(sid, parts_done=2)
        self._add(sid, 2, 0.45, 1500)
        p = sp.plan_for_slot(0, now=self.NOW)
        self.assertEqual((p.part_no, p.mode), (3, "finale"))

    def test_the_part_cap_always_ends_a_story(self):
        verdict = {"label": "hot", "score": 0.9, "part": 11}
        self.assertEqual(sp.decide_next_part({"parts_done": 11, "planned_parts": 12}, verdict)[0], "finale")

    def test_the_writers_proposed_length_is_clamped(self):
        self.assertEqual((sp.clamp_planned_parts(99), sp.clamp_planned_parts(1), sp.clamp_planned_parts("x")), (7, 3, 5))


# ---------------------------------------------------------------- bible + voices
class BibleTests(unittest.TestCase):
    def test_voices_persist_and_new_characters_get_unused_ones(self):
        from src.character_voices import assign_voices
        first = assign_voices([{"name": "Sarah", "gender": "female"}, {"name": "Tom", "gender": "male"}])
        later = assign_voices([{"name": "Dave", "gender": "male"}, {"name": "Sarah", "gender": "female"}], existing=first)
        self.assertEqual((later["Sarah"], later["Tom"]), (first["Sarah"], first["Tom"]))
        self.assertNotIn(later["Dave"], (first["Tom"], first["Sarah"]))

    def test_bible_round_trip(self):
        from src.series_bible import appearance_map, merged_characters, new_bible, updated_bible
        story = {"series": {"logline": "L", "setting": "S", "arc": ["a"]}, "series_update": {"recap": "R1", "open_threads": ["t1"], "cliffhanger": "c1"},
                 "characters": [{"name": "Sarah", "gender": "female", "role": "det", "voice_note": "calm", "appearance": "40s, navy coat"}]}
        bible = new_bible(story)
        self.assertEqual((bible["recap"], bible["characters"][0]["appearance"]), ("R1", "40s, navy coat"))
        part2 = {"characters": [{"name": "Dave", "gender": "male", "appearance": "teen, red hoodie"}], "series_update": {"recap": "R2", "cliffhanger": "c2"}}
        merged = merged_characters(bible, part2["characters"])
        self.assertEqual([c["name"] for c in merged], ["Sarah", "Dave"])
        after = updated_bible(bible, {**part2, "characters": part2["characters"]}, {"Sarah": "V1", "Dave": "V2"})
        self.assertEqual((after["recap"], after["cliffhanger"], after["open_threads"]), ("R2", "c2", ["t1"]), "old threads are kept when the writer omits them")
        self.assertEqual(after["voice_map"], {"Sarah": "V1", "Dave": "V2"})
        self.assertEqual(appearance_map(after), {"Sarah": "40s, navy coat", "Dave": "teen, red hoodie"})

    def test_characters_keep_their_looks_in_image_prompts(self):
        from src.story_pipeline import prompt_for_beat
        ap = {"Sarah Miller": "woman in her 40s, navy coat", "Sheriff Tom Garrett": "heavy man, grey moustache", "Dave": "teen in a red hoodie"}
        narr = {"type": "narration", "speaker": "narrator", "text": "Sarah opened the vault.", "visual_description": "a steel door."}
        self.assertEqual(prompt_for_beat(narr, ap), "a steel door, Sarah Miller: woman in her 40s, navy coat")
        talk = {"type": "dialogue", "speaker": "Sheriff Tom Garrett", "text": "Stay back.", "visual_description": "a tense face"}
        self.assertIn("grey moustache", prompt_for_beat(talk, ap))
        self.assertEqual(prompt_for_beat({"type": "narration", "speaker": "narrator", "text": "Nothing.", "visual_description": "an empty road"}, ap), "an empty road")
        self.assertEqual(prompt_for_beat(narr, None), "a steel door")

    def test_the_closing_line_tells_viewers_when_the_next_part_arrives(self):
        from src.story_pipeline import build_outro
        self.assertEqual(build_outro("middle", 2, "Friday night"), "That was part 2. Part 3 arrives Friday night. Subscribe and turn on notifications, so you never miss it.")
        self.assertIn("where this story ends", build_outro("finale", 5, "x"))


# ---------------------------------------------------------------- episode writing
def _episode(n_beats=60, tag=True, jumpscare=True, hook=True, words=40):
    beats = []
    cycle = ["fear", "curiosity", "suspense", "excitement", "mystery"]
    for i in range(n_beats):
        b = {"beat_number": i + 1, "type": "narration", "speaker": "narrator", "text": " ".join(["word"] * words) + ".",
             "visual_description": f"scene {i}", "elements": [cycle[i % 5]] if tag else []}
        if i < 4:
            b["elements"] = ["suspense", "mystery"] if hook else ["excitement"]     # no hook = nothing scary/curious up front
        if jumpscare and i == 10:
            b["jumpscare"] = True
        beats.append(b)
    return {"characters": [{"name": "Sarah", "gender": "female"}], "beats": beats,
            "series": {"title": "The Steel Vault", "planned_parts": 4, "arc": ["a"]}, "series_update": {"recap": "r"}}


class EpisodeWritingTests(unittest.TestCase):
    def _write(self, answers, **kw):
        import src.story_writer as sw
        prompts = []
        def gen(prompt, temperature=0.95):
            prompts.append(prompt); a = answers[min(len(prompts) - 1, len(answers) - 1)]
            if isinstance(a, Exception): raise a
            return a
        with mock.patch.object(sw, "generate_json", side_effect=gen), mock.patch("src.pattern_analytics.suggest_next_pillar", return_value="locked_room"):
            try:
                return sw.write_story("horror", **kw), prompts
            except RuntimeError as e:
                return e, prompts

    def test_a_complete_episode_passes(self):
        story, _ = self._write([_episode()])
        self.assertEqual((story["mode"], story["part_no"]), ("opening", 1))
        self.assertEqual(story["series"]["title"], "The Steel Vault")
        self.assertTrue(any(b["jumpscare"] for b in story["beats"]))

    def test_every_requirement_is_in_the_prompt(self):
        _, prompts = self._write([_episode()])
        p = prompts[0]
        for needle in ("FEAR (dar)", "CURIOSITY", "SUSPENSE", "EXCITEMENT", "MYSTERY (raaz)", "JUMPSCARE", "FIRST 30 SECONDS", "CLIFFHANGER", "PART 1 OF A NEW"):
            self.assertIn(needle, p)

    def test_a_missing_emotion_is_rejected_and_the_retry_names_exactly_what_to_fix(self):
        thin = _episode(tag=False)
        story, prompts = self._write([thin, _episode()])
        self.assertEqual(len(prompts), 2)
        self.assertIn("REJECTED because", prompts[1]); self.assertIn("required emotions are missing", prompts[1])
        self.assertTrue(isinstance(story, dict))

    def test_no_jumpscare_and_no_hook_are_each_caught(self):
        from src.story_writer import _normalize_story, _validate_story
        for kw, needle in ((dict(jumpscare=False), "jumpscare"), (dict(hook=False), "30-second hook")):
            ep = _episode(**kw); _normalize_story(ep)
            with self.assertRaises(ValueError) as cm: _validate_story(ep, require_elements=True)
            self.assertIn(needle, str(cm.exception))

    def test_a_continuation_carries_the_bible_the_recap_and_the_ending_rule(self):
        series = {"title": "The Steel Vault", "genre": "horror", "pillar": "locked_room", "planned_parts": 4, "parts_done": 2,
                  "bible": {"logline": "L", "setting": "S", "recap": "UNIQUE-RECAP-TEXT", "cliffhanger": "the lights died",
                            "open_threads": ["who locked it?"], "arc": ["Part 1: x"],
                            "characters": [{"name": "Sarah", "gender": "female", "role": "det", "voice_note": "calm", "appearance": "navy coat"}]}}
        ep = _episode(); ep.pop("series"); ep["characters"] = []
        ep["beats"][5].update(type="dialogue", speaker="Sarah")
        story, prompts = self._write([ep], series=series, part_no=3, mode="middle")
        self.assertIsInstance(story, dict, story)
        self.assertIn("UNIQUE-RECAP-TEXT", prompts[0]); self.assertIn("the lights died", prompts[0]); self.assertIn("'previously' recap", prompts[0])
        self.assertIn("PART 3 of", prompts[0]); self.assertIn("NEW CLIFFHANGER", prompts[0])
        self.assertEqual([c["name"] for c in story["characters"]], ["Sarah"], "the bible's cast is merged in")
        self.assertEqual(story["beats"][5]["speaker"], "Sarah")
        self.assertEqual((story["genre"], story["mode"], story["part_no"]), ("horror", "middle", 3))
        _, finale = self._write([ep], series=series, part_no=4, mode="finale")
        self.assertIn("FINAL PART", finale[0]); self.assertIn("no cliffhanger", finale[0])

    def test_three_attempts_with_the_reason_fed_back_each_time(self):
        story, prompts = self._write([_episode(tag=False), _episode(jumpscare=False), _episode()])
        self.assertEqual(len(prompts), 3); self.assertIsInstance(story, dict)
        self.assertIn("jumpscare", prompts[2]); self.assertIn("required emotions", prompts[1])
        err, prompts = self._write([_episode(tag=False)] * 3)
        self.assertIsInstance(err, RuntimeError); self.assertEqual(len(prompts), 3)

    def test_bad_modes_are_rejected(self):
        import src.story_writer as sw
        with self.assertRaises(ValueError): sw.write_story("horror", mode="sideways")
        with self.assertRaises(ValueError): sw.write_story("horror", mode="middle")      # a continuation needs the series row


# ---------------------------------------------------------------- publishing parameters
class SchedulingParamsTests(unittest.TestCase):
    def test_youtube_schedules_by_publishing_private_with_publish_at(self):
        import src.youtube_uploader as yu
        bodies = []
        class Req:
            def next_chunk(self): return None, {"id": "VID", "status": {"privacyStatus": "private"}}
        yt = mock.Mock(); yt.videos.return_value.insert.side_effect = lambda part, body, media_body: (bodies.append(body), Req())[1]
        when = datetime(2026, 11, 13, 1, 0, tzinfo=UTC)
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt), mock.patch.object(yu, "_media_upload", return_value=object()):
            with self.assertLogs("src.youtube_uploader", level="INFO") as cm:
                self.assertEqual(yu.upload_video(Path("x.mp4"), "t", "d", [], privacy_status="public", publish_at=when), "VID")
        st = bodies[0]["status"]
        self.assertEqual((st["privacyStatus"], st["publishAt"]), ("private", "2026-11-13T01:00:00.000Z"))
        self.assertTrue(any("Scheduled VID" in m for m in cm.output))
        self.assertFalse(any("audit lock" in m.lower() for m in cm.output), "a scheduled video is private on purpose — not an audit lock")

    def test_playlists_and_description_links(self):
        import src.youtube_uploader as yu
        yt = mock.MagicMock()
        yt.playlists.return_value.insert.return_value.execute.return_value = {"id": "PL9"}
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt):
            self.assertEqual(yu.ensure_playlist("Series | Hey Darky", "desc"), "PL9")
            self.assertEqual(yu.ensure_playlist("x", "y", existing_id="OLD"), "OLD")
            yu.add_to_playlist("PL9", "VID1")
        body = yt.playlistItems.return_value.insert.call_args.kwargs["body"]["snippet"]
        self.assertEqual((body["playlistId"], body["resourceId"]["videoId"]), ("PL9", "VID1"))
        yt.videos.return_value.list.return_value.execute.return_value = {"items": [{"snippet": {"title": "t", "description": "first", "categoryId": "24"}}]}
        with mock.patch.object(yu, "_get_youtube_client", return_value=yt):
            self.assertTrue(yu.append_to_description("VID0", "▶ Next: Part 2 — https://youtu.be/VID1"))
        sent = yt.videos.return_value.update.call_args.kwargs["body"]["snippet"]["description"]
        self.assertTrue(sent.startswith("first") and sent.endswith("https://youtu.be/VID1"))
        with mock.patch.object(yu, "_get_youtube_client", side_effect=RuntimeError("api down")):
            self.assertFalse(yu.append_to_description("VID0", "x"))

    def test_facebook_schedule_window_and_parameters(self):
        import src.facebook_publisher as fb
        now = datetime.now(UTC)
        self.assertIsNone(fb._schedule_params(None))
        self.assertIsNone(fb._schedule_params(now + timedelta(minutes=5)), "closer than Facebook's 10-minute minimum: publish now")
        self.assertIsNone(fb._schedule_params(now + timedelta(days=40)), "beyond 30 days")
        ts = fb._schedule_params(now + timedelta(days=3))
        self.assertAlmostEqual(ts, (now + timedelta(days=3)).timestamp(), delta=2)

    def test_facebook_posts_carry_the_schedule(self):
        import src.facebook_publisher as fb
        class R:
            status_code = 200
            def __init__(self, body): self._b = body
            def json(self): return self._b
        log = []
        def req(method, url, **kw):
            d = kw.get("data") or {}
            log.append(dict(d) if isinstance(d, dict) else "<bytes>")
            ph = d.get("upload_phase") if isinstance(d, dict) else None
            if url.endswith("/search"): return R({"data": [{"key": 6, "name": "English (US)"}]})
            if "graph-video" in url:
                return R({"upload_session_id": "S", "video_id": "V", "start_offset": "0", "end_offset": "4"} if ph == "start" else
                         {"start_offset": "4", "end_offset": "4"} if ph == "transfer" else {"success": True})
            if url.endswith("/video_reels"):
                return R({"video_id": "RV", "upload_url": "https://rupload.facebook.com/x"} if ph == "start" else {"success": True})
            return R({"success": True})
        f = Path(tempfile.mkdtemp()) / "v.mp4"; f.write_bytes(b"abcd")
        when = datetime.now(UTC) + timedelta(days=2)
        with mock.patch.dict(os.environ, {"FB_PAGE_ID": "P", "FB_ACCESS_TOKEN": "T"}), mock.patch("requests.request", side_effect=req):
            fb._page_token_cache = "T"; fb._locale_cache = [6]
            fb.publish_long_video(f, "t", "d", scheduled_time=when)
            fb.publish_reel(f, "d", scheduled_time=when)
        fin_long = next(x for x in log if isinstance(x, dict) and x.get("upload_phase") == "finish" and "upload_session_id" in x)
        fin_reel = next(x for x in log if isinstance(x, dict) and x.get("upload_phase") == "finish" and "video_id" in x)
        self.assertEqual((fin_long["published"], fin_long["scheduled_publish_time"]), ("false", int(when.timestamp())))
        self.assertEqual((fin_reel["video_state"], fin_reel["scheduled_publish_time"]), ("SCHEDULED", int(when.timestamp())))
        shutil.rmtree(f.parent, ignore_errors=True)


# ---------------------------------------------------------------- metadata
class SeriesMetadataTests(unittest.TestCase):
    STORY = {"genre": "horror", "universe_town": "Blackwood Pines, Oregon", "title_long": "I broke into a sealed panic room. Something was inside.",
             "description": "A clerk. A stranger.", "tags": ["horror story"]}

    def test_titles_carry_the_part_and_a_search_phrase_and_never_exceed_100(self):
        from src.platform_metadata import episode_title
        self.assertEqual(episode_title(self.STORY, 2, "middle"), "I broke into a sealed panic room. Something was inside. (Part 2) | Scary Story")
        self.assertTrue(episode_title(self.STORY, 7, "finale").endswith("(Final Part) | Scary Story"))
        long = dict(self.STORY, title_long="x " * 60)
        t = episode_title(long, 3, "middle")
        self.assertLessEqual(len(t), 100); self.assertIn("(Part 3)", t)
        self.assertNotIn("Part", episode_title(self.STORY))

    def test_the_description_leads_with_keywords_and_links_the_series(self):
        from src.platform_metadata import build_long_posts
        p = build_long_posts(self.STORY, None, series={"title": "The Steel Vault"}, part_no=2, mode="middle",
                             prev_url="https://youtu.be/AAA", playlist_url="https://www.youtube.com/playlist?list=PL1", next_label="premieres Friday 8 PM ET")
        yt = p["youtube"]
        first = yt["description"].splitlines()[0]
        self.assertEqual(first, "The Steel Vault — Part 2 | Scary Stories | Horror Stories"); self.assertLessEqual(len(first), 125)
        for needle in ("Previous part: https://youtu.be/AAA", "list=PL1", "Next: Part 3 premieres Friday 8 PM ET"):
            self.assertIn(needle, yt["description"])
        self.assertEqual(yt["tags"][:3], ["hey darky", "scary stories", "horror stories"])
        self.assertNotIn("youtu", p["facebook"]["description"], "no external links on Facebook")
        fin = build_long_posts(self.STORY, None, series={"title": "The Steel Vault"}, part_no=5, mode="finale", next_label="premieres x")["youtube"]["description"]
        self.assertNotIn("Next: Part", fin)

    def test_no_phrase_makes_a_false_claim(self):
        from src.config import STORY_SEARCH_KEYWORDS, STORY_TITLE_KEYWORD
        every = " ".join([*STORY_TITLE_KEYWORD.values(), *[k for v in STORY_SEARCH_KEYWORDS.values() for k in v]]).lower()
        self.assertNotIn("animated", every); self.assertNotIn("true story", every)
        self.assertEqual(set(STORY_TITLE_KEYWORD), set(STORY_SEARCH_KEYWORDS))

    def test_shorts_point_at_the_exact_part_and_the_series(self):
        from src.platform_metadata import build_short_posts
        p = build_short_posts(self.STORY, None, {"hook": "The door moved."}, "LONG1", series={"title": "The Steel Vault"}, part_no=2, mode="middle",
                              playlist_url="https://www.youtube.com/playlist?list=PL1")
        d = p["youtube"]["description"]
        self.assertIn("Full story (The Steel Vault — Part 2): https://youtu.be/LONG1", d); self.assertIn("list=PL1", d); self.assertIn("related video", d.lower())
        self.assertIn("Part 2", p["instagram"]["caption"]); self.assertNotIn("youtu.be", p["instagram"]["caption"])


# ---------------------------------------------------------------- Shorts + thumbnail
class ShortsAndThumbnailTests(unittest.TestCase):
    def _items(self, n=24, dur=5.0):
        return [{"beat": {"type": "narration", "elements": ["curiosity"], "emotion": "calm"}, "duration": dur} for _ in range(n)]

    def test_shorts_target_jumpscares_fear_and_excitement_without_overlapping(self):
        from src.story_shorts import plan_short_windows
        items = self._items()
        items[14]["beat"].update(jumpscare=True, elements=["fear"], sfx_kind="action")
        items[19]["beat"].update(elements=["excitement", "fear"])
        w = plan_short_windows(items, 3)
        self.assertEqual(w[0][0], 0, "the first Short is the episode's opening hook")
        self.assertTrue(any(14 in x for x in w), "the jumpscare is in a Short")
        flat = [i for x in w for i in x]
        self.assertEqual(len(flat), len(set(flat)), "no overlap")

    def test_the_closing_line_is_never_cut_into_a_short(self):
        from src import story_shorts as ss
        items = self_items = [{"beat": {"type": "narration", "elements": ["curiosity"], "emotion": "calm"}, "duration": 5.0} for _ in range(12)]
        items[-1]["beat"].update(outro=True, jumpscare=True, elements=["fear", "excitement"], sfx_kind="action")   # would be the best-scoring window
        seen = {}
        def fake_short(assets, idxs, k, kind, cta=None):
            seen[k] = idxs; return {"path": Path("x"), "hook": "h", "duration": 25.0, "kind": kind, "beats": idxs}
        with mock.patch.object(ss, "build_story_short", side_effect=fake_short):
            ss.build_story_shorts({"items": items}, 2, "cta")
        self.assertNotIn(11, [i for idxs in seen.values() for i in idxs])

    def test_the_end_banner_points_at_the_full_story(self):
        from src.caption_builder import build_story_captions
        words = [{"word": "w", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(40)]      # 20 seconds
        out = build_story_captions([({"type": "narration", "speaker": "narrator"}, words)], Path(tempfile.mkdtemp()) / "c.ass",
                                   is_short=True, end_cta="FULL STORY: PART 2 — SEE RELATED VIDEO")
        text = out.read_text()
        self.assertIn("Style: Cta,", text)
        line = next(l for l in text.splitlines() if ",Cta," in l and l.startswith("Dialogue"))
        self.assertIn("SEE RELATED VIDEO", line); self.assertIn("0:00:16.", line.split(",")[1], "the banner starts 3.5 s before the end")
        self.assertNotIn(",Cta,", build_story_captions([({"type": "narration", "speaker": "narrator"}, words)], out.with_name("n.ass")).read_text().split("[Events]")[1])

    def test_the_thumbnail_shows_a_part_badge_only_for_series_parts(self):
        from PIL import Image
        import src.story_thumbnail as st
        tmp = Path(tempfile.mkdtemp()); base = tmp / "b.jpg"; Image.new("RGB", (1280, 720), (20, 20, 60)).save(base)
        plain = st._compose(base, "", tmp / "a.jpg"); badge = st._compose(base, "", tmp / "b2.jpg", "PART 2")
        px = lambda p: Image.open(p).convert("RGB").getpixel((60, 60))
        self.assertNotEqual(px(plain), px(badge), "the badge darkens the top-left corner")
        story = {"thumbnail_concept": "x", "thumbnail_text": "", "part_no": 3, "mode": "middle", "series": {"title": "S"}}
        with mock.patch.object(st, "generate_scene_image", return_value=base), mock.patch.object(st, "SCENES_DIR", tmp), mock.patch.object(st, "_compose", wraps=st._compose) as comp:
            st.build_story_thumbnail(story)
            self.assertEqual(comp.call_args.args[3], "PART 3")
            st.build_story_thumbnail({**story, "mode": "finale", "part_no": 5})
            self.assertEqual(comp.call_args.args[3], "FINAL PART")
            st.build_story_thumbnail({"thumbnail_concept": "x", "thumbnail_text": ""})
            self.assertIsNone(comp.call_args.args[3])
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
