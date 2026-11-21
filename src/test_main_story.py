"""
Wiring tests for main_story.py — the series show. Heavy stages (story generation, rendering) and every network
call are mocked; the REAL database, schedule, series planner, metadata builders and queue logic run.
Run:  python -m unittest discover -s tests -p "test_*.py" -v
"""
import contextlib
import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import main_story
import src.database as db
from src import schedule
from src.config import SHORTS_PER_EPISODE_BY_SLOT


def make_story(part_no: int, mode: str) -> dict:
    story = {"genre": "horror", "pillar": "locked_room", "title": f"The Steel Vault p{part_no}",
             "title_long": "I broke into a sealed panic room. Something was inside.", "description": "A clerk. A stranger. A door.",
             "universe_town": "Blackwood Pines, Oregon", "recurring_character_used": "", "tags": ["horror story"],
             "hook": "The bell rang at 3 AM.", "thumbnail_text": "DON'T LOOK", "premise": f"premise {part_no}",
             "part_no": part_no, "mode": mode,
             "characters": [{"name": "Sarah", "gender": "female", "role": "detective", "voice_note": "calm", "appearance": "40s, navy coat"}],
             "series_update": {"recap": f"recap after part {part_no}", "open_threads": ["who locked it?"], "cliffhanger": f"cliffhanger {part_no}"}}
    if mode == "opening":
        story["series"] = {"title": "The Steel Vault", "logline": "Locked in with it.", "planned_parts": 4, "arc": ["Part 1: a"], "setting": "Oregon"}
    return story


class MainStoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for d in ("output", "pending", "data"):
            (self.tmp / d).mkdir()
        self.long = self.tmp / "long.mp4"; self.long.write_bytes(b"L" * 2048)
        self.yt_ids = iter([f"YT{i}" for i in range(20)])
        self.build_calls, self.short_calls, self.yt_calls = [], [], []
        self.stack = contextlib.ExitStack()
        P = self.stack.enter_context
        P(mock.patch.object(db, "DB_PATH", self.tmp / "t.db"))
        for name, value in (("ROOT_DIR", self.tmp), ("PENDING_DIR", self.tmp / "pending"), ("OUTPUT_DIR", self.tmp / "output"),
                            ("CHECKLIST_PATH", self.tmp / "data" / "related_video_checklist.md")):
            P(mock.patch.object(main_story, name, value))
        self.research = P(mock.patch.object(main_story, "research_niche", return_value={"sample_size": 3, "suggested_tags": ["horror"]}))

        def fake_build(genre=None, premise="", research=None, pillar=None, *, series=None, part_no=1, mode="opening", planned_parts=0, next_label=""):
            self.build_calls.append({"genre": genre, "series": series, "part_no": part_no, "mode": mode, "planned": planned_parts, "next_label": next_label})
            return {"story": make_story(part_no, mode), "long_video_path": self.long,
                    "assets": {"slug": f"vault-p{part_no}", "voice_map": {"Sarah": "en-US-JennyNeural"}, "items": [], "appearances": {}}}
        self.build = P(mock.patch.object(main_story, "build_story_video", side_effect=fake_build))

        def fake_shorts(assets, n=2, cta_text=None):
            self.short_calls.append((n, cta_text))
            out = []
            for k in range(1, n + 1):
                f = self.tmp / f"short{len(self.short_calls)}_{k}.mp4"; f.write_bytes(b"S" * 1024)
                out.append({"path": f, "hook": f"Hook {k}.", "duration": 28.0, "kind": "hook" if k == 1 else "tension", "beats": [k]})
            return out
        self.shorts = P(mock.patch.object(main_story, "build_story_shorts", side_effect=fake_shorts))
        self.thumb_path = self.tmp / "thumb.jpg"; self.thumb_path.write_bytes(b"J" * 50)
        self.thumb = P(mock.patch.object(main_story, "build_story_thumbnail", return_value=self.thumb_path))

        def fake_upload(path, title, desc, tags, **kw):
            vid = next(self.yt_ids); self.yt_calls.append({"id": vid, "title": title, "desc": desc, "tags": tags, "kw": kw}); return vid
        self.yt = P(mock.patch.object(main_story, "upload_video", side_effect=fake_upload))
        self.yt_thumb = P(mock.patch.object(main_story, "upload_thumbnail"))
        self.playlist = P(mock.patch.object(main_story, "ensure_playlist", return_value="PL1"))
        self.add_pl = P(mock.patch.object(main_story, "add_to_playlist"))
        self.append_desc = P(mock.patch.object(main_story, "append_to_description", return_value=True))
        fb, ig = main_story.facebook_publisher, main_story.instagram_publisher
        self.fb_long = P(mock.patch.object(fb, "publish_long_video", return_value="FB_LONG"))
        self.fb_reel = P(mock.patch.object(fb, "publish_reel", side_effect=lambda *a, **k: f"FB_R{self.fb_reel.call_count}"))
        P(mock.patch.object(fb, "is_configured", return_value=True)); P(mock.patch.object(ig, "is_configured", return_value=True))
        self.ig_reel = P(mock.patch.object(ig, "publish_reel", return_value="IG_REEL"))
        P(mock.patch.dict(os.environ, {"STORY_GENRE": "horror"}))
        db.init_db()
        self.now = datetime.now(timezone.utc)
        self.slot_index, self.slot_time = schedule.next_open_long_slot(self.now, force=True)

    def tearDown(self):
        self.stack.close(); shutil.rmtree(self.tmp, ignore_errors=True)

    def _build(self, review=False, force=True):
        with mock.patch.object(main_story, "REVIEW_MODE", review):
            return main_story.run_build(force=force)

    def _existing_series(self, parts_done=1, planned=4, slot_index=None):
        sid = db.create_series("The Steel Vault", "horror", "locked_room", planned, self.slot_index if slot_index is None else slot_index,
                               {"recap": "old recap", "voice_map": {"Sarah": "en-US-JennyNeural"}, "characters": [{"name": "Sarah", "gender": "female"}], "cliffhanger": "old"})
        db.update_series(sid, parts_done=parts_done, playlist_id="PLX")
        for part in range(1, parts_done + 1):
            db.record_story_upload(f"PREV{part}", f"t{part}", "locked_room", series_id=sid, part_no=part, slot_index=self.slot_index,
                                   publish_at=(self.slot_time - timedelta(days=7 * (parts_done - part + 1))).isoformat())
        return sid

    # -------------------------------------------------------------- a brand-new story
    def test_a_new_story_is_scheduled_on_every_platform_at_its_slot(self):
        self.assertEqual(self._build(), 0)
        call = self.build_calls[0]
        self.assertEqual((call["series"], call["part_no"], call["mode"], call["genre"]), (None, 1, "opening", "horror"))
        yt = self.yt_calls[0]
        self.assertEqual(yt["kw"]["publish_at"], self.slot_time, "YouTube makes it public at the slot by itself")
        self.assertTrue(yt["title"].endswith("(Part 1) | Scary Story"), yt["title"])
        self.assertIn("https://www.youtube.com/playlist?list=PL1", yt["desc"])
        self.assertIn("The Steel Vault — Part 1", yt["desc"].splitlines()[0])
        self.assertIn("Next: Part 2 premieres", yt["desc"])
        self.assertTrue(set(["scary stories", "horror stories"]) <= set(yt["tags"][:6]), "search phrases lead the tags")
        self.assertEqual(self.playlist.call_count, 3, "series + genre + all-episodes playlists are created")
        self.assertEqual(self.add_pl.call_count, 3, "the episode joins all three")
        self.assertEqual(self.add_pl.call_args_list[0].args, ("PL1", yt["id"]))
        self.assertIsNotNone(db.get_playlist("genre:horror")); self.assertIsNotNone(db.get_playlist("all-episodes"))
        self.yt_thumb.assert_called_once_with(yt["id"], self.thumb_path)
        fb = self.fb_long.call_args
        self.assertEqual((fb.kwargs["scheduled_time"], fb.kwargs["published"]), (self.slot_time, True))
        # the story enters the database only after the upload succeeded
        s = db.series_for_slot(self.slot_index)
        self.assertEqual((s["title"], s["planned_parts"], s["parts_done"], s["playlist_id"], s["status"]), ("The Steel Vault", 4, 1, "PL1", "active"))
        self.assertEqual(s["bible"]["voice_map"], {"Sarah": "en-US-JennyNeural"})
        ep = db.episodes_for_series(s["id"])[0]
        self.assertEqual((ep["part_no"], ep["slot_index"], ep["publish_at"]), (1, self.slot_index, self.slot_time.isoformat()))
        # the slot is now taken: the next run targets another one
        self.assertTrue(db.slot_taken("long", self.slot_time))

    def test_shorts_are_scheduled_one_per_day_and_instagram_waits_in_the_queue(self):
        self._build()
        want = SHORTS_PER_EPISODE_BY_SLOT[self.slot_index]
        self.assertEqual(self.short_calls[0], (want, "FULL STORY: PART 1 ON YOUTUBE — HEY DARKY"))
        shorts = self.yt_calls[1:]
        self.assertEqual(len(shorts), want)
        times = [c["kw"]["publish_at"] for c in shorts]
        self.assertEqual(times, sorted(times)); self.assertEqual(len({t.date() for t in times}), want, "one Short per day")
        self.assertGreater(times[0], self.now, "never scheduled in the past")
        self.assertLess(times[0], self.slot_time + timedelta(days=1), "the first Short is the release-day announcement")
        self.assertTrue(all(c["title"].endswith("#Shorts") for c in shorts))
        self.assertTrue(all("Part 1" in c["desc"] and "related video" in c["desc"].lower() for c in shorts))
        for call, t in zip(self.fb_reel.call_args_list, times):
            self.assertEqual(call.kwargs["scheduled_time"], t)
        self.ig_reel.assert_not_called()                            # Instagram cannot be scheduled: it waits for its due time
        queued = db.get_due_publish_items((self.now + timedelta(days=30)).isoformat())
        self.assertEqual(len(queued), want)
        for item, t, c in zip(queued, times, shorts):
            self.assertEqual(item["due_at"], t.isoformat())
            self.assertEqual(json.loads(item["result"])["youtube"], c["id"], "YouTube/Facebook ids are pre-filled")
            self.assertTrue((self.tmp / item["file_path"]).exists())
        with db.get_conn() as c:
            n_short_rows = c.execute("SELECT COUNT(*) FROM story_videos WHERE kind='short'").fetchone()[0]
        self.assertEqual(n_short_rows, want)
        text = (self.tmp / "data" / "related_video_checklist.md").read_text()
        self.assertEqual(text.count("- [ ] https://youtu.be/"), want)
        self.assertIn(f"-> https://youtu.be/{self.yt_calls[0]['id']}", text)

    # -------------------------------------------------------------- the next parts
    def test_the_next_part_continues_the_same_story_and_links_the_parts(self):
        sid = self._existing_series(parts_done=1)
        self._build()
        call = self.build_calls[0]
        self.assertEqual((call["part_no"], call["mode"], call["series"]["id"]), (2, "middle", sid))
        self.assertIsNone(call["genre"], "a continuation takes its genre from the series")
        self.assertEqual(self.playlist.call_count, 2, "only the channel-wide playlists are new; the series already has its own")
        yt = self.yt_calls[0]
        self.assertTrue(yt["title"].endswith("(Part 2) | Scary Story"))
        self.assertIn("Previous part: https://youtu.be/PREV1", yt["desc"])
        self.assertIn("playlist?list=PLX", yt["desc"])
        self.assertEqual(self.add_pl.call_args_list[0].args, ("PLX", yt["id"]))
        self.append_desc.assert_called_once_with("PREV1", f"▶ Next: Part 2 — https://youtu.be/{yt['id']}")
        s = db.get_series(sid)
        self.assertEqual((s["parts_done"], s["status"], s["bible"]["recap"]), (2, "active", "recap after part 2"))
        self.assertEqual(s["bible"]["voice_map"], {"Sarah": "en-US-JennyNeural"})
        self.assertEqual(self.build_calls[0]["next_label"].split()[0] in ("Wednesday", "Friday", "Sunday"), True)

    def test_the_finale_finishes_the_story_and_frees_its_slot(self):
        sid = self._existing_series(parts_done=3, planned=4)
        self._build()
        self.assertEqual((self.build_calls[0]["part_no"], self.build_calls[0]["mode"]), (4, "finale"))
        self.assertTrue(self.yt_calls[0]["title"].endswith("(Final Part) | Scary Story"))
        self.assertEqual(self.short_calls[0][1], "FULL STORY: FINAL PART ON YOUTUBE — HEY DARKY")
        self.assertNotIn("Next: Part", self.yt_calls[0]["desc"])
        s = db.get_series(sid)
        self.assertEqual(s["status"], "finished"); self.assertIsNotNone(s["finished_at"])
        self.assertIsNone(db.series_for_slot(self.slot_index), "the slot is free: the next occurrence starts a NEW story")

    # -------------------------------------------------------------- safety
    def test_review_mode_uploads_private_now_and_schedules_nothing(self):
        self._build(review=True)
        for c in self.yt_calls:
            self.assertIsNone(c["kw"]["publish_at"]); self.assertEqual(c["kw"]["privacy_status"], "private")
        self.assertFalse(self.fb_long.call_args.kwargs["published"])
        self.assertIsNone(self.fb_long.call_args.kwargs["scheduled_time"])
        self.assertTrue(all(not c.kwargs["published"] for c in self.fb_reel.call_args_list))
        self.ig_reel.assert_not_called()
        self.assertEqual(db.get_due_publish_items((self.now + timedelta(days=30)).isoformat()), [])

    def test_a_youtube_failure_creates_no_story_and_publishes_nothing_else(self):
        self.yt.side_effect = RuntimeError("quota exceeded")
        with self.assertRaises(RuntimeError): self._build()
        self.assertEqual(db.get_active_series(), [], "a failed upload must not leave an orphan series behind")
        self.fb_long.assert_not_called(); self.fb_reel.assert_not_called(); self.ig_reel.assert_not_called()
        self.assertFalse(db.slot_taken("long", self.slot_time), "the slot stays open: tomorrow's run retries it")

    def test_secondary_failures_never_stop_the_run(self):
        self.fb_long.side_effect = KeyError("start_offset"); self.fb_reel.side_effect = RuntimeError("socket closed")
        self.playlist.side_effect = RuntimeError("playlist api"); self.yt_thumb.side_effect = RuntimeError("thumb api")
        self.append_desc.side_effect = RuntimeError("desc api")
        self.assertEqual(self._build(), 0)
        self.assertEqual(db.series_for_slot(self.slot_index)["parts_done"], 1)
        self.assertEqual(len(db.get_due_publish_items((self.now + timedelta(days=30)).isoformat())), SHORTS_PER_EPISODE_BY_SLOT[self.slot_index])
        self.assertTrue((self.tmp / "output" / "last_run.json").exists())

    def test_nothing_is_built_when_no_slot_is_open(self):
        with mock.patch.object(schedule, "next_open_long_slot", return_value=None):
            self.assertEqual(self._build(force=False), 0)
        self.build.assert_not_called(); self.yt.assert_not_called()

    def test_a_slot_that_is_about_to_pass_goes_public_at_once_instead_of_being_refused(self):
        soon = (self.slot_index, datetime.now(timezone.utc) + timedelta(minutes=1))     # the build ran long
        with mock.patch.object(schedule, "next_open_long_slot", return_value=soon):
            self.assertEqual(self._build(), 0)
        self.assertIsNone(self.yt_calls[0]["kw"]["publish_at"], "YouTube would refuse a publishAt in the past")
        self.assertEqual(self.yt_calls[0]["kw"]["privacy_status"], "public")
        self.assertTrue(db.slot_taken("long", soon[1]), "the slot is still accounted for")

    def test_an_unknown_genre_is_rejected_before_any_work(self):
        with mock.patch.dict(os.environ, {"STORY_GENRE": "romance"}):
            with self.assertRaises(ValueError): self._build()
        self.research.assert_not_called()

    def test_research_failure_is_not_fatal(self):
        self.research.side_effect = RuntimeError("youtube api down")
        self.assertEqual(self._build(), 0)

    # -------------------------------------------------------------- the queue (Instagram at the due time)
    def _due_now(self):
        with db.get_conn() as c:
            c.execute("UPDATE publish_queue SET due_at = ?", ((datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),))

    def test_the_queue_posts_only_instagram_because_youtube_and_facebook_publish_themselves(self):
        self._build(); self._due_now()
        yt_before, fb_before = self.yt.call_count, self.fb_reel.call_count
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        want = SHORTS_PER_EPISODE_BY_SLOT[self.slot_index]
        self.assertEqual(self.ig_reel.call_count, want)
        self.assertIn("link in bio", self.ig_reel.call_args.args[1])
        self.assertEqual((self.yt.call_count, self.fb_reel.call_count), (yt_before, fb_before), "no second upload to YouTube/Facebook")
        self.assertEqual(db.get_due_publish_items(), [])
        self.assertFalse(any((self.tmp / "pending").iterdir()), "posted files are removed")
        self.ig_reel.reset_mock(); main_story.run_publish_queue()
        self.ig_reel.assert_not_called()

    def test_queued_files_are_named_by_story_and_part_so_equal_titles_cannot_overwrite_each_other(self):
        sid = self._existing_series(parts_done=1)
        self._build()
        names = sorted(p.name for p in (self.tmp / "pending").iterdir())
        self.assertTrue(all(n.startswith(f"s{sid}-p2-short") for n in names), names)
        self.assertEqual(len(names), len(set(names)))

    def test_a_failed_instagram_post_is_retried_without_duplicates(self):
        self._build(); self._due_now()
        self.ig_reel.return_value = None
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        want = SHORTS_PER_EPISODE_BY_SLOT[self.slot_index]
        self.assertEqual(len(db.get_due_publish_items()), want, "still pending")
        self.ig_reel.return_value = "IG_REEL"; self.ig_reel.reset_mock()
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        self.assertEqual(self.ig_reel.call_count, want); self.assertEqual(db.get_due_publish_items(), [])

    def test_a_missing_queued_file_is_marked_failed_not_crashed(self):
        self._build(); self._due_now()
        for f in (self.tmp / "pending").iterdir(): f.unlink()
        self.assertEqual(main_story.run_publish_queue(), 0)
        self.ig_reel.assert_not_called(); self.assertEqual(db.get_due_publish_items(), [])


if __name__ == "__main__":
    unittest.main()
