# HEY DARKY — a weekly series show of horror / crime / thriller / suspense / mystery stories

Fully automatic. Every story is original fiction, narrated by several characters with their own voices
(female characters get female voices, male characters male voices), with scene-matched images, music and
sound effects. **A story is a series, not a movie**: it is released in parts, one part a week.

## 1. The show

**Three stories run in parallel.** Each owns one weekly slot for its whole life (US Eastern time, because
crime and horror viewers watch late at night — roughly 9 PM to midnight — and a fixed slot is the one
scheduling factor every study agrees on):

| Slot | Default time | Why |
|---|---|---|
| 0 | Wednesday 8 PM ET | mid-week night |
| 1 | Friday 8 PM ET | the weekend starts — stay-up-late night |
| 2 | Sunday 8 PM ET | relaxed Sunday evening |
| Shorts | every day 5 PM ET | on release days ~3 h *before* the episode, as its announcement |

Week 1 = Part 1 of three new stories. Week 2 = Part 2 of each. And so on. Per week: 3 long episodes
(15–20 min, YouTube + Facebook) and 7 Shorts, one a day (YouTube + Facebook + Instagram — Instagram gets
only the Shorts).

**The audience decides how long a story lives** (`src/series_planner.py`). A new story is planned for 3–7
parts, and after every part the bot reads that part's real YouTube numbers (retention + views relative to the
channel's normal video):

* **hit** → never ends early; at its planned end it is *extended* (2 more parts, up to 12);
* **average** → runs to its planned length, then ends;
* **flop** → wrapped up *now*: the next part is written as the finale — so an unloved story can end after
  2 parts;
* when a story ends, its slot starts a brand-new story.

**Every part must deliver** (written into the prompt *and* validated; a part missing any of it is rejected
and re-written with the exact reason):

| Emotion | What it means |
|---|---|
| **Fear** | a monster, an unknown presence, danger — and at least one **jumpscare** (silence, then a sudden sound) |
| **Curiosity** | what happened here? who is behind this? what is hiding? |
| **Suspense** | what happens next? approaching danger, the unexpected |
| **Excitement** | chases, escapes, survival, unexpected encounters |
| **Mystery** | hidden stories, clues, secrets, theories |

Plus: a **hook in the first 30 seconds** (the biggest moment first), a **"previously"** recap in every part
after the first, and a **cliffhanger** at the end of every part except the finale. The closing line tells
viewers when the next part arrives. Characters keep their **voices** and their **looks** (appearance text in
every image prompt) across parts.

## 2. Setting it up (fresh repo, or updating)

1. Copy **everything** in this folder into the repo root (keep the structure; `.github` is hidden).
   **Keep `data/words.db` if you already have one** — it migrates itself to the new tables.
2. Secrets (Settings → Secrets and variables → Actions): `GEMINI_API_KEY`, `YT_CLIENT_ID`,
   `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`, `POLLINATIONS_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`,
   `FREESOUND_API_KEY`, `FB_PAGE_ID`, `FB_ACCESS_TOKEN`, `IG_USER_ID`, `HF_TOKEN` (optional).
   Variable `REVIEW_MODE`: `1` (default) = everything uploaded private/unpublished immediately, nothing
   scheduled, Instagram skipped — for checking by hand; `0` = the fully automatic show. **Note:** in review mode
   the series still advances (Part 1 is recorded, its slot is used), so publish those private videos yourself
   in Studio, or the story will have a private hole when you switch to `0`.
3. Actions → **HEY DARKY STORY BOT** → Run workflow → `build`, `force = true`. One run builds ONE episode
   (~30–60 min) and its Shorts. Run it three times to open the three stories.

## 3. A day in the life

```
06:00 UTC  build   -> is a weekly slot open in the next few days? if so: research -> write the episode
                      (bible + recap) -> voices -> images -> video -> music+SFX -> thumbnail (with PART N)
                      -> YouTube upload as private + publishAt = the slot (YouTube itself makes it public
                         at that exact moment) -> series/genre/all-episodes playlists
                      -> previous part's description gets a "Next part" link -> Facebook scheduled
                      -> 2-3 Shorts rendered and scheduled (YouTube + Facebook); Instagram queued
21:05/22:05 UTC queue -> posts the Instagram Reels that are due (5 PM ET in summer / winter)
02:30 UTC  analytics -> real retention / views from YouTube -> database -> the next decisions
```
`python main_story.py schedule` prints the slots, the stories on air and what is open.

## 4. What the bot does for reach — and what it cannot

Done automatically: fixed weekly slots at late-night US times (the analytics job logs how each slot performs;
the bot does **not** move slots on its own, because an episode's views depend on its story far more than on its
day, and with a few stories the two cannot be told apart — set `AUTO_SLOT_SWAP=1` if you want it to try anyway,
or edit `LONG_SLOTS_DEFAULT` yourself after a couple of months of data); titles `Hook (Part N) | Scary
Story`, a keyword-rich first description line, genre search phrases as the first tags (all accurate — never
"animated", never "true story"); thumbnails with at most 2 words and a PART badge; a hook in 30 seconds; every
video in 3 playlists (its series, its genre, all episodes); the Short→full-episode links in descriptions;
English declared as the language; Shorts at an evening slot with an end banner pointing at the full story.

Not possible through the API — **do these by hand**:
* **Related video on Shorts.** The YouTube API has no field for it. `data/related_video_checklist.md` lists
  every Short with the episode it should point to (Studio → Content → Shorts → Edit → Related video).
* **Reply to every comment in the first 48 hours** and pin a question — early engagement is the strongest
  signal for a new channel. Pinning is not available in the API.

## 5. Things you must know

* **First real run: 26 minutes, YouTube + Instagram worked** (YouTube published public — no API-audit lock on
  this project). Facebook failed with a permission error — see below.
* **Pollinations** needs a key AND balance: anonymous = 401, no balance = **402**. The model is FLUX.1 Schnell
  (`black-forest-labs/flux.1-schnell`, alias `flux` as backup; `POLLINATIONS_MODELS` overrides). The balance is
  logged at the start of image generation; on 401/402 Pollinations is switched off for the run and Pexels/Pixabay
  stock photos take over. Check/top up at enter.pollinations.ai.
* **Facebook needs a PAGE access token** (`pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
  `publish_video`; `FB_PAGE_ID` = the Page's own id). The bot derives the Page token from a user token if it
  can, and logs exactly what to fix otherwise. Facebook/Instagram failures never undo a YouTube publish.
* **YouTube is primary**: if its long upload fails the run fails (nothing is recorded; the slot stays open and
  the next daily run retries it).
* **Audit lock**: videos uploaded by an *unverified* Google Cloud project are forced private; the uploader logs
  `audit lock` if a requested-public upload comes back private. (Scheduled videos are private until their slot
  by design — that is not the lock.)
* **Targeting**: YouTube/Instagram have no organic audience-targeting API (English is declared on YouTube;
  Facebook gets English-locale targeting where Meta allows it). Research is requested in English and
  non-English results are discarded.
* **Music**: Pixabay has no music API; music and SFX come from Freesound (CC0) with query fallbacks, then your
  `assets/` files, then a synthesized drone. Check Freesound's API terms if the channel is monetized.
* **Cost**: ~15 builds a month × 30–60 min plus ~60 short daily jobs ≈ well under 2000 free private-repo
  minutes; a public repo has no limit. Not verifiable without your keys: Gemini's story quality over a whole
  series, and Meta behaviour beyond what the first run showed.

## 6. Safety nets (run before every bot run)

```
python tools/wiring_audit.py                             # imports, orphans, secrets, workflow YAML
python -m unittest discover -s tests -p "test_*.py" -v   # 130+ tests, incl. injected failures
python tests/e2e_story_render.py                         # slow, by hand: 2 episodes rendered for real
# (the fast suite also runs tests/test_show_simulation.py: 8 weeks of the show on a fake clock, DST included)
```

## 7. Troubleshooting

| You see | Cause | Do |
|---|---|---|
| `No weekly slot is open` | the next slots are already filled | normal; use `force` to look 2 weeks ahead |
| `audit lock` | unverified API project | apply for the YouTube API audit |
| `Pollinations unavailable: HTTP 402` | no pollen balance | top up at enter.pollinations.ai |
| `FACEBOOK PERMISSION PROBLEM` | token cannot publish to the Page | see section 5 |
| `these required emotions are missing` | the model skipped a required element | automatic retry with that feedback |
| `quotaExceeded` (YouTube) | one episode with its Shorts costs ~6.7k of the 10k daily API units | never run two builds on the same day |
| `quota exhausted` (gemini) | free tier ~20 requests/day/model | wait; the fallback model is tried |
| `Failed to generate a valid ... story` | two attempts failed validation | rerun; the log names the missing item |

## 8. Layout

```
main_story.py                       entry point: build | publish-queue | schedule
src/config.py                       every setting (slots, series rules, emotions, keywords...)
src/schedule.py                     weekly slots (US Eastern, DST-safe), daily Short slots, slot learning
src/series_planner.py               which story gets the next part; hit / average / flop decisions
src/series_bible.py                 cast, voices, looks, rolling recap, open threads
src/story_writer.py                 writes one episode (validated: 5 emotions, jumpscare, hook)
src/story_pipeline.py / story_shorts.py / story_thumbnail.py / video_builder.py / audio_*.py
src/platform_metadata.py            titles, descriptions, tags, hashtags per platform
src/youtube_uploader.py / youtube_analytics.py / facebook_publisher.py / instagram_publisher.py
src/database.py                     series, episodes + real numbers, slots, playlists, publish queue
src/topic_research.py / node_bridge.py / pattern_analytics.py / story_analytics_sync.py
tools/wiring_audit.py   tests/   .github/workflows/run-story-bot.yml, story-analytics.yml
data/related_video_checklist.md     created by the bot: Shorts to link to their episode in Studio
```
