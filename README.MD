# HEY DARKY — automated horror / crime / thriller / suspense / mystery stories

A fully automatic channel bot. Every story is fictional, has several characters with
their own voices (female characters get female voices, male characters male voices),
and is told as a narrated film: scene-matched Western-style images, background music
and sound effects.

| What | Cadence | Where it goes |
|---|---|---|
| Long story, 15–20 min | one every **2 days** | YouTube + Facebook Page |
| Short, 20–35 s | one **every day** | YouTube + Facebook Reel + Instagram Reel |

Instagram gets **only** the daily Short. Each platform gets its own title, description
and hashtags. Everything is English.

---

## 1. Fresh start — exact steps

1. In your GitHub repo delete **every old file** (keep the `.git` folder / the repo itself).
2. Copy **everything inside this folder** into the repo root, keeping the structure below.
   (`.github/` is a hidden folder — make sure it is copied.)
3. Add the secrets and the variable from section 2.
4. Actions tab → **HEY DARKY STORY BOT** → *Run workflow* → `command = build`, `force = true`.
   With the default `REVIEW_MODE=1` everything is uploaded **private / unpublished**, so you
   can check the first video by hand. (First run ≈ 1.5–2 h.)
5. Happy with it? Settings → Secrets and variables → Actions → **Variables** →
   `REVIEW_MODE` = `0`. From then on it publishes publicly and fully automatically.

## 2. Secrets (Settings → Secrets and variables → Actions → Secrets)

Names must match exactly:

| Secret | Used for |
|---|---|
| `GEMINI_API_KEY` | writing the story |
| `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` | YouTube upload, research, analytics (token needs upload + readonly + analytics-readonly scopes) |
| `POLLINATIONS_API_KEY` | AI scene images |
| `PEXELS_API_KEY`, `PIXABAY_API_KEY` | stock-image fallback |
| `FREESOUND_API_KEY` | background music + sound effects |
| `FB_PAGE_ID`, `FB_ACCESS_TOKEN` | Facebook Page (and the token is reused for Instagram) |
| `IG_USER_ID` | Instagram Reels |
| `HF_TOKEN` | optional (model downloads) |

Variable: `REVIEW_MODE` (`1` = private/unpublished review mode, `0` = fully public).

## 3. How a day works

```
18:00 UTC  build job  -> is a long story due? (decided from what was ACTUALLY uploaded)
                         research -> story -> voices -> images -> video -> music+SFX
                         -> thumbnail -> YouTube long + Facebook long
                         -> Short #1 -> YouTube + Facebook Reel + Instagram Reel (now)
                         -> Short #2 -> queued for tomorrow
19:30 UTC  queue job  -> publishes yesterday's queued Short to all three
02:30 UTC  analytics  -> real retention/CTR from YouTube -> database -> the next story learns
```
Change the times in `.github/workflows/run-story-bot.yml` (cron, UTC).
Manual: `python main_story.py build [--force]` · `python main_story.py publish-queue`.

## 4. Things you must know (verified, not guesses)

* **YouTube audit lock.** Google forces videos uploaded through the API by an
  *unverified* Google Cloud project to **private**, and they cannot be made public until
  the project passes YouTube's API compliance audit. The bot detects this and logs a loud
  `audit lock` error. If your first public run shows it, apply for the audit; until then
  YouTube stays private (Facebook/Instagram are unaffected).
* **Audience targeting.** YouTube and Instagram have **no** organic targeting API. YouTube:
  English is declared as language + audio language, text is English-only. Instagram:
  English caption + niche hashtags. **Facebook** is the only one with a real control:
  English-locale `targeting`/`feed_targeting` on every post (keys resolved live from Meta;
  if Meta rejects it the post is still published untargeted). Enable *Audience Optimization
  for Posts* in the Page settings. Interest matching ("likes horror") is done by each
  platform from watch behaviour — consistent genre content is the lever.
* **Music.** Pixabay's official API has no music endpoint (images and videos only), so
  music **and** sound effects come from Freesound (CC0 only), with your own files in
  `assets/music` / `assets/sfx` or a synthesized drone as fallbacks. Freesound's *API terms*
  describe API use as free for non-commercial use even though CC0 sounds are free to use
  commercially — if the channel is monetized, check with Freesound.
* **Instagram** can only be exercised with `REVIEW_MODE=0` (nothing is posted in review mode).
  A Facebook/Instagram failure never affects YouTube.
* **Cost.** One long-story run ≈ 1.5–2 h. On a private repo that is ~15 runs/month ≈
  1800 of the 2000 free minutes; a public repo has no limit.
* **Not verifiable without your keys:** real Gemini story quality, real Freesound, real Meta
  Graph calls, real render time.

## 5. Safety nets (run automatically before every bot run)

```
python tools/wiring_audit.py                             # imports, orphans, secrets, workflow entry points
python -m unittest discover -s tests -p "test_*.py" -v   # 80 fast tests
python tests/e2e_story_render.py                         # slow, manual: whole pipeline with real ffmpeg
```
If any wiring breaks, the run fails in seconds — not after a 90-minute render.

## 6. Troubleshooting

| You see | Cause | Do |
|---|---|---|
| `audit lock` error, video private | unverified API project | apply for YouTube API audit |
| `quota exhausted` for gemini-… | Gemini free tier is ~20 requests/day/model | wait a day or upgrade; the bot already skips to the fallback model |
| Pollinations 401 / 402 | key/credit issue | check pollen balance; Pexels/Pixabay take over automatically |
| `Freesound HTTP 429` | rate limit | automatic 60 s / 120 s backoff; cached files never re-download |
| Instagram `ERROR` container | Reel rejected / token scope | read the Graph error in the log; token needs `instagram_content_publish` |
| `Facebook rejected audience targeting` | Page setting / API | post still published untargeted |

## 7. Layout

```
main_story.py                      entry point (build / publish-queue)
requirements.txt  .gitignore
.github/workflows/run-story-bot.yml, story-analytics.yml
src/config.py                      all settings
src/story_writer.py                one Gemini call -> characters, beats, audio direction
src/llm_client.py                  Gemini with quota-aware retries
src/character_voices.py            gender-matched voices   src/tts_engine.py   Edge TTS (+ Piper fallback)
src/aligner.py                     word timestamps         src/caption_builder.py   speaker-labelled karaoke captions
src/visual_generator.py            Pollinations -> Pexels -> Pixabay
src/video_builder.py               Ken Burns video, drift-free sync
src/audio_fetcher.py / audio_mixer.py   Freesound music + SFX, ducking
src/story_pipeline.py              wires a whole story together   src/story_shorts.py   2 vertical Shorts per story
src/story_thumbnail.py             thumbnail
src/platform_metadata.py           per-platform titles / descriptions / hashtags
src/youtube_uploader.py  youtube_analytics.py  facebook_publisher.py  instagram_publisher.py
src/topic_research.py + node_bridge.py + tools/trending-scraper/   niche research (YouTube API + optional Puppeteer)
src/pattern_analytics.py + story_analytics_sync.py + database.py   learning loop + publish queue
tools/wiring_audit.py   tests/
assets/{music,sfx,luts}/   optional files: your own CC0 music/effects, a cinematic.cube colour grade
```
