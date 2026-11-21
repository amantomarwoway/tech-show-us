"""
Eight weeks of the show, day by day, on a fake clock: the daily 06:00 UTC cron runs main_story.run_build against the
REAL database, schedule and series planner (only story generation / rendering / network are mocked), and
YouTube "analytics" arrive three days after each episode goes public. This catches what single-run tests cannot:
duplicate or skipped slots, a story landing on the wrong weekday, daylight-saving drift, Shorts gaps, a flop that
does not end, a hit that does not extend.
The simulated run crosses the US daylight-saving change (1 Nov 2026).
"""
import contextlib
import shutil
import tempfile
import unittest
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

import main_story
import src.database as db
from src import schedule
from src.config import SHORTS_PER_EPISODE_BY_SLOT

ET = ZoneInfo("America/New_York")
START = datetime(2026, 10, 26, 6, 0, tzinfo=timezone.utc)       # a Monday, the week before DST ends
DAYS = 56
QUALITY = {1: (0.62, 5000), 2: (0.45, 1500), 3: (0.15, 100)}    # series #1 = hit, #2 = average, #3 = flop; later ones average


class Clock:
    value = START


class FakeDT(datetime):
    @classmethod
    def now(cls, tz=None):
        return Clock.value if tz else Clock.value.replace(tzinfo=None)


class ShowSimulation(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for d in ("pending", "output", "data"):
            (self.tmp / d).mkdir()
        self.long = self.tmp / "long.mp4"; self.long.write_bytes(b"L")
        self.opened = 0
        self.builds_per_run = []
        self.yt_counter = 0
        self.stack = contextlib.ExitStack()
        P = self.stack.enter_context
        P(mock.patch.object(db, "DB_PATH", self.tmp / "sim.db"))
        for name, value in (("ROOT_DIR", self.tmp), ("PENDING_DIR", self.tmp / "pending"), ("OUTPUT_DIR", self.tmp / "output"),
                            ("CHECKLIST_PATH", self.tmp / "data" / "c.md"), ("REVIEW_MODE", False)):
            P(mock.patch.object(main_story, name, value))
        P(mock.patch.object(main_story, "datetime", FakeDT))
        P(mock.patch.object(main_story, "research_niche", return_value=None))
        P(mock.patch.object(main_story, "build_story_thumbnail", return_value=None))
        P(mock.patch.object(main_story, "upload_thumbnail")); P(mock.patch.object(main_story, "append_to_description", return_value=True))
        self.n_playlist = 0
        def playlist(*a, **k):
            self.n_playlist += 1; return f"PL{self.n_playlist}"
        P(mock.patch.object(main_story, "ensure_playlist", side_effect=playlist)); P(mock.patch.object(main_story, "add_to_playlist"))
        fb, ig = main_story.facebook_publisher, main_story.instagram_publisher
        P(mock.patch.object(fb, "is_configured", return_value=True)); P(mock.patch.object(ig, "is_configured", return_value=True))
        P(mock.patch.object(fb, "publish_long_video", return_value="FB")); P(mock.patch.object(fb, "publish_reel", return_value="FBR"))
        P(mock.patch.object(ig, "publish_reel", return_value="IG"))
        P(mock.patch.dict("os.environ", {"STORY_GENRE": "horror"}))
        self.uploads = []
        def upload(path, title, desc, tags, **kw):
            self.yt_counter += 1; vid = f"V{self.yt_counter}"; self.uploads.append((vid, kw.get("publish_at"))); return vid
        P(mock.patch.object(main_story, "upload_video", side_effect=upload))

        def build(genre=None, premise="", research=None, pillar=None, *, series=None, part_no=1, mode="opening", planned_parts=0, next_label=""):
            self.builds_this_run += 1
            if mode == "opening":
                self.opened += 1
            title = series["title"] if series else f"Series {self.opened}"
            story = {"genre": "horror", "pillar": "locked_room", "title": f"{title} p{part_no}", "title_long": "hook", "description": "d",
                     "universe_town": "Blackwood Pines", "tags": [], "part_no": part_no, "mode": mode, "hook": "h", "thumbnail_text": "",
                     "characters": [{"name": "Sarah", "gender": "female", "appearance": "x"}],
                     "series_update": {"recap": f"r{part_no}", "open_threads": [], "cliffhanger": "c"}}
            if mode == "opening":
                story["series"] = {"title": title, "logline": "l", "planned_parts": 3, "arc": []}
            return {"story": story, "long_video_path": self.long,
                    "assets": {"slug": f"s{self.opened}-{part_no}", "voice_map": {"Sarah": "V"}, "items": [], "appearances": {}}}
        P(mock.patch.object(main_story, "build_story_video", side_effect=build))

        def shorts(assets, n=2, cta_text=None):
            out = []
            for k in range(n):
                f = self.tmp / f"sh_{assets['slug']}_{k}.mp4"; f.write_bytes(b"S")
                out.append({"path": f, "hook": "h", "duration": 25.0, "kind": "hook", "beats": [k]})
            return out
        P(mock.patch.object(main_story, "build_story_shorts", side_effect=shorts))
        db.init_db()

    def tearDown(self):
        self.stack.close(); shutil.rmtree(self.tmp, ignore_errors=True)

    def _settle(self, now):
        """YouTube analytics: an episode's numbers exist three days after it goes public; quality depends on the story."""
        with db.get_conn() as c:
            rows = c.execute("SELECT v.video_id, v.publish_at, s.title FROM story_videos v JOIN series s ON s.id = v.series_id "
                             "WHERE v.kind = 'long' AND v.avg_view_percentage IS NULL").fetchall()
        for r in rows:
            if datetime.fromisoformat(r["publish_at"]) <= now - timedelta(days=3):
                n = int(r["title"].split()[-1])
                ret, views = QUALITY.get(n, QUALITY[2])
                db.update_story_performance(r["video_id"], avg_view_percentage=ret, views=views)

    def test_eight_weeks_of_the_show(self):
        for day in range(DAYS):
            now = START + timedelta(days=day)
            Clock.value = now
            self._settle(now)                      # the 02:30 UTC analytics job runs BEFORE the 06:00 UTC build
            self.builds_this_run = 0
            self.assertEqual(main_story.run_build(force=False), 0, f"day {day}")
            self.builds_per_run.append(self.builds_this_run)
        self.assertLessEqual(max(self.builds_per_run), 1, "one episode per run")

        with db.get_conn() as c:
            series = [dict(r) for r in c.execute("SELECT * FROM series ORDER BY id")]
            longs = [dict(r) for r in c.execute("SELECT * FROM story_videos WHERE kind='long' ORDER BY publish_at")]
            shorts = [dict(r) for r in c.execute("SELECT * FROM story_videos WHERE kind='short' ORDER BY publish_at")]
        slots = {s["slot_index"]: s for s in db.get_slots()}

        # --- no slot is ever used twice, nothing is scheduled in the past
        publish_times = [l["publish_at"] for l in longs]
        self.assertEqual(len(publish_times), len(set(publish_times)), "a slot was filled twice")
        first_week = [l for l in longs if datetime.fromisoformat(l["publish_at"]) < START + timedelta(days=9)]
        self.assertEqual({l["part_no"] for l in first_week}, {1}, "week 1 = Part 1 of every story")
        self.assertEqual(len({l["series_id"] for l in first_week}), 3, "three stories open in week one")

        # --- every episode lands on its slot's weekday at 8 PM Eastern, whatever the daylight-saving state
        for l in longs:
            local = datetime.fromisoformat(l["publish_at"]).astimezone(ET)
            slot = slots[l["slot_index"]]
            self.assertEqual((local.weekday(), local.hour, local.minute), (slot["weekday"], slot["hour_local"], slot["minute"]), l["publish_at"])
        # the simulated weeks include the DST change: both UTC offsets occurred
        self.assertEqual({datetime.fromisoformat(l["publish_at"]).hour for l in longs if l["slot_index"] == 0}, {0, 1})

        # --- each story: exactly one part per week, in order, always the same slot
        by_series = defaultdict(list)
        for l in longs:
            by_series[l["series_id"]].append(l)
        for sid, eps in by_series.items():
            self.assertEqual([e["part_no"] for e in eps], list(range(1, len(eps) + 1)), f"series {sid} parts out of order")
            self.assertEqual(len({e["slot_index"] for e in eps}), 1)
            gaps = {(datetime.fromisoformat(b["publish_at"]).astimezone(ET).date() - datetime.fromisoformat(a["publish_at"]).astimezone(ET).date()).days
                    for a, b in zip(eps, eps[1:])}
            self.assertLessEqual(gaps, {7}, f"series {sid}: a story must get its next part exactly a week later, got {gaps}")

        # --- the audience decides: the flop ends after 2 parts, the hit is extended, the slot is reused
        flop = next(s for s in series if s["title"] == "Series 3")
        self.assertEqual((flop["status"], flop["parts_done"]), ("finished", 2), "a story nobody cared about ends after part 2")
        hit = next(s for s in series if s["title"] == "Series 1")
        self.assertGreater(hit["planned_parts"], 3, "a hit is extended beyond its planned length")
        self.assertGreater(hit["parts_done"], 3)
        self.assertGreater(len(series), 3, "finished stories free their slot for new stories")
        successor = [s for s in series if s["slot_index"] == flop["slot_index"] and s["id"] != flop["id"]]
        self.assertTrue(successor, "the flop's slot started a new story")
        last_flop = max(datetime.fromisoformat(e["publish_at"]) for e in by_series[flop["id"]])
        self.assertTrue(all(datetime.fromisoformat(by_series[s["id"]][0]["publish_at"]) > last_flop for s in successor))
        # no slot ever goes dark: every weekly occurrence of every slot (first to last) holds an episode, even across a
        # story ending and the next one starting in the same slot
        for idx in slots:
            dates = [datetime.fromisoformat(l["publish_at"]).astimezone(ET).date() for l in longs if l["slot_index"] == idx]
            self.assertGreaterEqual(len(dates), 7, f"slot {idx} should have aired about 7-8 episodes in 8 weeks")
            self.assertEqual({(b - a).days for a, b in zip(dates, dates[1:])}, {7}, f"slot {idx} skipped a week: {dates}")
        self.assertEqual(len({l["slot_index"] for l in longs}), 3)

        # --- one Short every day once the show is up and running (days 10..44), never two
        per_day = Counter(datetime.fromisoformat(s["publish_at"]).astimezone(ET).date() for s in shorts)
        for day in range(10, 45):
            d = (START + timedelta(days=day)).astimezone(ET).date()
            self.assertEqual(per_day.get(d, 0), 1, f"{d}: expected exactly one Short, found {per_day.get(d, 0)}")
        for s in shorts:
            local = datetime.fromisoformat(s["publish_at"]).astimezone(ET)
            self.assertEqual((local.hour, local.minute), (17, 0), "Shorts go out at 5 PM Eastern")
        per_episode = Counter(s["parent_video_id"] for s in shorts)
        self.assertEqual(set(per_episode.values()), set(SHORTS_PER_EPISODE_BY_SLOT) , per_episode)


if __name__ == "__main__":
    unittest.main()
