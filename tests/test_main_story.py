"""
Wiring tests for main_story.py: every step, in order, on the right platform,
with the right arguments. Heavy stages (story generation, rendering) and all
network publishing are mocked; the REAL database, metadata builders and queue
logic run. Run:  python -m unittest discover -s tests -p "test_*.py" -v
"""
import contextlib
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import main_story
import src.database as db

STORY = {"genre": "horror", "pillar": "locked_room", "title": "The Diner", "title_long": "I closed the diner alone. Someone was already inside.",
         "description": "A clerk. A stranger. A door that never opens twice.", "universe_town": "Blackwood Pines, Oregon",
         "recurring_character_used": "Sheriff Tom Garrett", "tags": ["horror story"], "search_keywords": ["diner story"],
         "hook": "The bell rang at 3 AM.", "thumbnail_text": "DON'T LOOK"}
RESEARCH = {"sample_size": 5, "top_titles": ["x"], "suggested_keywords": ["diner"], "suggested_tags": ["horror", "creepypasta"]}


class MainStoryWiringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "output").mkdir(); (self.tmp / "pending").mkdir()
        self.long = self.tmp / "long.mp4"; self.long.write_bytes(b"L" * 2048)
        self.shorts = []
        for k in (1, 2):
            p = self.tmp / f"short{k}.mp4"; p.write_bytes(b"S" * 1024)
            self.shorts.append({"path": p, "hook": f"Hook number {k}.", "duration": 28.0, "kind": "hook" if k == 1 else "tension", "beats": [k]})
        self.yt_ids = iter(["YT_LONG", "YT_S1", "YT_S2", "YT_S3"])
        self.stack = contextlib.ExitStack()
        P = self.stack.enter_context
        P(mock.patch.object(db, "DB_PATH", self.tmp / "t.db"))
        P(mock.patch.object(main_story, "ROOT_DIR", self.tmp)); P(mock.patch.object(main_story, "PENDING_DIR", self.tmp / "pending"))
        P(mock.patch.object(main_story, "OUTPUT_DIR", self.tmp / "output"))
        self.research = P(mock.patch.object(main_story, "research_niche", return_value=RESEARCH))
        self.build = P(mock.patch.object(main_story, "build_story_video", return_value={
            "story": dict(STORY), "assets": {"slug": "the-diner", "items": []}, "long_video_path": self.long}))
        self.mk_shorts = P(mock.patch.object(main_story, "build_story_shorts", return_value=self.shorts))
        self.thumb_path = self.tmp / "thumb.jpg"; self.thumb_path.write_bytes(b"J" * 100)
        self.thumb = P(mock.patch.object(main_story, "build_story_thumbnail", return_value=self.thumb_path))
        self.yt = P(mock.patch.object(main_story, "upload_video", side_effect=lambda *a, **k: next(self.yt_ids)))
        self.yt_thumb = P(mock.patch.object(main_story, "upload_thumbnail"))
        fb, ig = main_story.facebook_publisher, main_story.instagram_publisher
        self.fb_long = P(mock.patch.object(fb, "publish_long_video", return_value="FB_LONG"))
        self.fb_reel = P(mock.patch.object(fb, "publish_reel", return_value="FB_REEL"))
        P(mock.patch.object(fb, "is_configured", return_value=True)); P(mock.patch.object(ig, "is_configured", return_value=True))
        self.ig_reel = P(mock.patch.object(ig, "publish_reel", return_value="IG_REEL"))
        P(mock.patch.dict("os.environ", {"STORY_GENRE": "horror"}, clear=False))
        db.init_db()

    def tearDown(self):
        self.stack.close(); shutil.rmtree(self.tmp, ignore_errors=True)

    def _build(self, review):
        with mock.patch.object(main_story, "REVIEW_MODE", review):
            return main_story.run_build(force=True)

    # ---- the daily cadence
    def test_nothing_happens_when_no_long_story_is_due(self):
        db.record_story_upload("OLD", "t", "locked_room", kind="long")
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            self.assertEqual(main_story.run_build(force=False), 0)
        self.build.assert_not_called(); self.yt.assert_not_called()

    def test_full_public_run_publishes_everything_to_the_right_platforms(self):
        self.assertEqual(self._build(review=False), 0)
        # research -> story, with the research passed through
        self.research.assert_called_once()
        self.assertEqual(self.build.call_args.args[0], "horror")
        self.assertEqual(self.build.call_args.kwargs["research"], RESEARCH)
        # YouTube long: public, Entertainment category, own title/tags, English declared, thumbnail set
        long_call, s1_call = self.yt.call_args_list[0], self.yt.call_args_list[1]
        self.assertEqual(long_call.args[0], self.long)
        self.assertEqual(long_call.args[1], "I closed the diner alone. Someone was already inside.")
        self.assertEqual((long_call.kwargs["privacy_status"], long_call.kwargs["category_id"]), ("public", "24"))
        self.assertIn("horror story", long_call.args[3])
        self.yt_thumb.assert_called_once_with("YT_LONG", self.thumb_path)
        # Facebook long: its own title/description, published, no YouTube link
        fb_args = self.fb_long.call_args
        self.assertEqual(fb_args.args[0], self.long)
        self.assertNotIn("youtu", fb_args.args[2]); self.assertTrue(fb_args.kwargs["published"])
        # Short 1 goes out NOW on all three platforms; the Reel/caption are platform-specific
        self.assertEqual(s1_call.args[0], self.shorts[0]["path"])
        self.assertEqual(s1_call.args[1], "Hook number 1. #Shorts")
        self.assertIn("https://youtu.be/YT_LONG", s1_call.args[2])
        self.assertEqual(self.fb_reel.call_count, 1); self.assertTrue(self.fb_reel.call_args.kwargs["published"])
        self.assertEqual(self.ig_reel.call_count, 1, "Instagram gets exactly ONE video per run: the daily Short, never the long story")
        self.assertIn("link in bio", self.ig_reel.call_args.args[1])
        self.assertEqual(self.ig_reel.call_args.args[0], self.shorts[0]["path"])
        # Short 2 is queued for tomorrow, not published now
        self.assertEqual(self.yt.call_count, 2)
        q = db.get_due_publish_items((datetime.now(timezone.utc) + timedelta(hours=21)).isoformat())
        self.assertEqual(len(q), 1)
        self.assertEqual(db.get_due_publish_items(), [], "not due yet")
        self.assertTrue((self.tmp / q[0]["file_path"]).exists(), "queued file copied into the cached pending/ folder")
        self.assertIn("https://youtu.be/YT_LONG", q[0]["payload"]["posts"]["youtube"]["description"])
        # database learned about the long + the short (for pillar learning / analytics)
        with db.get_conn() as c:
            rows = {r["video_id"]: dict(r) for r in c.execute("SELECT * FROM story_videos")}
        self.assertEqual((rows["YT_LONG"]["kind"], rows["YT_LONG"]["pillar"], rows["YT_LONG"]["genre"]), ("long", "locked_room", "horror"))
        self.assertEqual((rows["YT_S1"]["kind"], rows["YT_S1"]["parent_video_id"]), ("short", "YT_LONG"))
        self.assertTrue((self.tmp / "output" / "last_run.json").exists())

    def test_review_mode_is_private_unpublished_and_skips_instagram(self):
        self._build(review=True)
        self.assertTrue(all(c.kwargs["privacy_status"] == "private" for c in self.yt.call_args_list))
        self.assertEqual(self.yt.call_count, 3, "both Shorts uploaded privately right away (nothing queued)")
        self.assertFalse(self.fb_long.call_args.kwargs["published"])
        self.assertTrue(all(not c.kwargs["published"] for c in self.fb_reel.call_args_list))
        self.ig_reel.assert_not_called()
        self.assertEqual(db.get_due_publish_items((datetime.now(timezone.utc) + timedelta(days=3)).isoformat()), [])

    # ---- failure policy
    def test_youtube_long_failure_fails_the_run_and_publishes_nothing_else(self):
        self.yt.side_effect = RuntimeError("quota exceeded")
        with self.assertRaises(RuntimeError): self._build(review=False)
        self.fb_long.assert_not_called(); self.fb_reel.assert_not_called(); self.ig_reel.assert_not_called()
        self.assertTrue(db.should_build_long_today(2), "nothing recorded -> tomorrow's run retries")

    def test_facebook_and_thumbnail_failures_never_undo_the_youtube_publish(self):
        self.fb_long.return_value = None; self.fb_reel.return_value = None; self.ig_reel.return_value = None
        self.yt_thumb.side_effect = RuntimeError("thumbnail api down")
        self.assertEqual(self._build(review=False), 0)
        self.assertEqual(self.yt.call_count, 2)
        self.assertTrue(db.last_story_long_upload() is not None)

    def test_unexpected_exceptions_from_facebook_or_instagram_never_stop_the_run(self):
        self.fb_long.side_effect = KeyError("start_offset")      # an API answer in an unexpected shape
        self.fb_reel.side_effect = RuntimeError("socket closed")
        self.ig_reel.side_effect = ValueError("bad json")
        self.assertEqual(self._build(review=False), 0)
        self.assertEqual(self.yt.call_count, 2, "YouTube long + Short 1 still published")
        self.assertEqual(len(db.get_due_publish_items((datetime.now(timezone.utc) + timedelta(hours=21)).isoformat())), 1,
                         "Short 2 still queued")
        self.assertTrue((self.tmp / "output" / "last_run.json").exists())

    def test_unknown_genre_is_rejected_before_any_work(self):
        with mock.patch.dict("os.environ", {"STORY_GENRE": "romance"}):
            with self.assertRaises(ValueError): self._build(review=False)
        self.research.assert_not_called()

    def test_research_failure_is_not_fatal(self):
        self.research.side_effect = RuntimeError("youtube api down")
        self.assertEqual(self._build(review=False), 0)
        self.assertIsNone(self.build.call_args.kwargs["research"])

    # ---- the next day: the queued Short
    def _make_queued_due(self):
        self._build(review=False)
        with db.get_conn() as c:
            c.execute("UPDATE publish_queue SET due_at = ?", ((datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),))

    def test_publish_queue_posts_to_all_three_and_cleans_up(self):
        self._make_queued_due()
        for m in (self.yt, self.fb_reel, self.ig_reel): m.reset_mock()
        self.yt.side_effect = lambda *a, **k: "YT_S2"
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        self.assertEqual((self.yt.call_count, self.fb_reel.call_count, self.ig_reel.call_count), (1, 1, 1))
        self.assertEqual(self.yt.call_args.kwargs["privacy_status"], "public")
        self.assertEqual(self.yt.call_args.args[1], "Hook number 2. #Shorts")
        self.assertEqual(self.ig_reel.call_args.args[0].name, "the-diner-short2.mp4")
        self.assertEqual(db.get_due_publish_items(), [])
        self.assertFalse(any((self.tmp / "pending").iterdir()), "published file removed from pending/")
        with db.get_conn() as c:
            row = dict(c.execute("SELECT * FROM story_videos WHERE video_id='YT_S2'").fetchone())
        self.assertEqual((row["kind"], row["parent_video_id"], row["pillar"]), ("short", "YT_LONG", "locked_room"))
        for m in (self.yt, self.fb_reel, self.ig_reel): m.reset_mock()
        main_story.run_publish_queue()
        self.yt.assert_not_called()   # nothing left: never posts the same Short twice

    def test_retry_never_creates_duplicates(self):
        self._make_queued_due()
        self.yt.reset_mock(); self.fb_reel.reset_mock(); self.ig_reel.reset_mock()
        self.yt.side_effect = lambda *a, **k: "YT_S2"
        self.fb_reel.return_value = None                       # Facebook fails on the first attempt
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        self.assertEqual(len(db.get_due_publish_items()), 1, "partial success stays queued for a retry")
        self.fb_reel.return_value = "FB_REEL"
        with mock.patch.object(main_story, "REVIEW_MODE", False):
            main_story.run_publish_queue()
        self.assertEqual(self.yt.call_count, 1, "YouTube was NOT uploaded again on the retry")
        self.assertEqual(self.ig_reel.call_count, 1, "Instagram was NOT posted again on the retry")
        self.assertEqual(self.fb_reel.call_count, 2)
        self.assertEqual(db.get_due_publish_items(), [])

    def test_missing_queued_file_is_marked_failed_not_crashed(self):
        self._make_queued_due()
        for f in (self.tmp / "pending").iterdir(): f.unlink()
        self.yt.reset_mock()
        self.assertEqual(main_story.run_publish_queue(), 0)
        self.yt.assert_not_called(); self.assertEqual(db.get_due_publish_items(), [])


if __name__ == "__main__":
    unittest.main()
