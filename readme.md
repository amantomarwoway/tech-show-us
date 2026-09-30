# WordsThatSpeaks — Weekly Oscar-Level Word Bot

One word → one cinematic etymology/psychology story, automated end-to-end,
using only free tiers and free-credit APIs. Publishes 2 long videos (5-10
min) and 4 derived Shorts per week on a fixed schedule, with a daily job
that regenerates underperforming titles/thumbnails based on real Analytics.

**Safety first:** by default every upload goes up **private**, for you to
review in YouTube Studio before it ever reaches an audience. See
"REVIEW_MODE" below before you turn that off.

## What it does

- **Tue & Fri 01:00 UTC** (`run-bot.yml`): picks a fresh word (Gemini +
  semantic-similarity dedup against everything used before), researches it
  (Wiktionary + Wikipedia), writes a 750-1300 word mystery/suspense/thriller
  script in 6-10 scenes, generates AI visuals per scene (Pollinations, with
  Pexels/Pixabay/HuggingFace fallback), synthesizes voiceover **per scene**
  (Edge TTS, Piper offline fallback), aligns word timestamps (faster-whisper),
  builds a graded 1920x1080 video with parallax Ken Burns motion + kinetic
  typography + animated captions + ducked music + scene-change SFX + a
  clickable thumbnail, uploads it (private for review, or scheduled — see
  REVIEW_MODE), then derives and schedules 2 vertical Shorts that link back
  to the long video.
- **Daily 02:00 UTC** (`ctr-optimizer.yml`): checks Analytics for videos
  older than 48h; if CTR or average-view-duration is under threshold,
  regenerates title/thumbnail and pushes the update.
- **Permanent dedup**: `data/words.db` is committed back to the repo after
  every run, so used words persist across GitHub Actions runs (which don't
  share state otherwise).

## REVIEW_MODE (read this before your first real run)

`REVIEW_MODE` is a GitHub Actions **repo variable** (Settings → Secrets and
variables → Actions → *Variables* tab — not a secret), read by
`src/config.py`. It defaults to `"1"` (on) if you never set it.

- **`REVIEW_MODE=1` (default):** the long video and both Shorts upload as
  **private**, with no publish schedule. Nothing goes public until you open
  YouTube Studio and publish it yourself. `main.py` logs a direct
  `studio.youtube.com/video/<id>/edit` link for the long video so you can
  find it fast.
- **`REVIEW_MODE=0`:** the long video is uploaded **private with a
  scheduled `publishAt`**, set to the next fixed weekly slot
  (`PUBLISH_WEEKDAYS`/`PUBLISH_HOUR_UTC` in `src/config.py`, Tue/Fri 01:00
  UTC by default) — YouTube flips it to public automatically at that time.
  Both Shorts are scheduled the same way, 24h/48h after that same slot.
  Because the slot is a fixed weekday+hour (not "now + N hours"), a run
  that takes 40 minutes and a run that takes 4 hours both produce the exact
  same publish time for viewers — "same day, same time" holds regardless
  of render time.

Only flip `REVIEW_MODE` to `0` after you've watched several full runs
end-to-end in review mode and you're confident the script quality,
visuals, and metadata are consistently good. This one setting is the
difference between "an AI's rough draft that a human approves" and "fully
unsupervised uploads to a real channel" — treat it accordingly.

## Kinetic typography + parallax Ken Burns (how it actually works)

This was added and tested in this revision — read `src/kinetic_typography.py`'s
module docstring for the full mechanical explanation; short version:

- **Parallax** = the background photo zooms via `zoompan` (Ken Burns) while
  the word overlay drifts independently at its own rate/direction — two
  layers moving differently is what reads as depth. It is NOT full
  depth-based image parallax (that would need subject/background
  segmentation of the AI-generated photo, which isn't something we can do
  reliably on generated images without a depth model) — it's the
  word-layer-vs-image-layer motion difference described in the original
  spec, which is what actually renders as "parallax" to a viewer.
- **Kinetic typography** = the episode's word, rendered on a fully
  transparent RGBA canvas with animated `drawtext` (fontsize/x/y/alpha all
  support live time-expressions in ffmpeg — verified, not something we had
  to fake with per-frame image rendering), then composited onto the Ken
  Burns background with `overlay=format=auto`. Three styles, rotating by
  scene index so consecutive scenes vary:
  - `typewriter` — letters revealed one at a time via stacked `drawtext`
    filters, each active only in its own time window. Only works because
    the overlay text is always short (the single episode word) — this
    approach would NOT scale to full sentences.
  - `glow` — two passes: a soft bordered copy blurred with `gblur` (the
    halo), then a crisp copy on top.
  - `bounce` — a single `drawtext` whose y-position follows a damped
    cosine so it overshoots and settles.
- **Word placement is deliberately in the upper band of the frame**
  (`WORD_Y_FRACTION = 0.12` in `kinetic_typography.py`), not vertical
  center. We tested centering it first and it collided with both the
  AI-generated scene image (which, per its own prompt engineering, tends
  to render its own subject/word near center) and the bottom-anchored
  captions — three competing text/graphic elements stacked on each other.
  If you ever change scene composition or caption position, re-check this
  doesn't reintroduce that collision.
- **TESTED FOOTGUN, do not reintroduce:** never insert `format=yuv420p`
  *inside* an ffmpeg `filter_complex` graph for this overlay work. We hit
  this directly — converting to yuv420p mid-graph before the final output
  stage silently produces a wrong color range/matrix and paints the entire
  background frame a false purple/magenta tint. `-pix_fmt yuv420p` must
  only ever be set as the ffmpeg **process's output argument**, never as a
  filter step. `overlay=format=auto` is what keeps the graph correct in
  RGB internally — don't "simplify" that.

## Caption themes (pop / bounce / karaoke)

`src/caption_builder.py` burns ASS subtitles with three themes. All three
are bottom-anchored, computed from the actual canvas size at render time
(`play_res_x`, `play_res_y`, `margin_v` — different for long 1920x1080 vs.
Shorts 1080x1920). **This was a real bug we found and fixed:** the
`bounce` theme originally used a hardcoded `\move(960,600,960,540,...)` —
pixel coordinates baked in for a 1920-wide canvas. On a 1080-wide Shorts
canvas that placed the X origin almost off-frame instead of centered, and
the fixed Y landed in the vertical *middle* of the frame on either canvas
instead of near the bottom, nowhere close to where `pop`/`karaoke` sit via
the style's `Alignment`+`MarginV`. If you add a fourth theme, derive its
position from `play_res_x`/`play_res_y`/`margin_v` the same way — never
hardcode pixel coordinates for one canvas size.

## Setup checklist

1. **Secrets** (repo Settings → Secrets and variables → Actions → *Secrets*
   tab):
   - `GEMINI_API_KEY` — from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
   - `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` — OAuth client
     with scopes `youtube.upload`, `youtube`, `yt-analytics.readonly`. Get a
     refresh token once via the
     [OAuth Playground](https://developers.google.com/oauthplayground) using
     your own client ID/secret, then store it as a secret — it will keep
     refreshing indefinitely as long as the OAuth consent screen is in
     **Production** mode (Testing mode tokens expire after 7 days).
   - Optional free-tier keys: `HF_TOKEN`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`
2. **Repo variable** (Settings → Secrets and variables → Actions →
   *Variables* tab): `REVIEW_MODE` — leave unset or `"1"` for your first
   several runs (see above).
3. **Google Cloud**: enable the YouTube Data API v3 and YouTube Analytics
   API on the project tied to your OAuth client; push the consent screen to
   Production.
4. **Assets** (all optional — the pipeline degrades gracefully without
   them, just with less polish):
   - Drop 3-5 royalty-free tracks into `assets/music/` (e.g. from Pixabay).
   - Drop a free teal-orange `.cube` LUT at `assets/luts/teal_orange.cube`.
   - Drop whoosh/pop SFX into `assets/sfx/` (used on scene-change cuts).
5. **First run**: trigger `run-bot.yml` manually via `workflow_dispatch`
   with `REVIEW_MODE` unset/`1`, watch the log/artifact output, and check
   the uploaded (private) video in YouTube Studio before ever setting
   `REVIEW_MODE=0`.

## Gemini 503 "high demand" resilience (added after a real production failure)

A real run failed with `main.py` crashing entirely because both
`gemini-3.7-flash` and `gemini-3.6-flash` returned `503 UNAVAILABLE` for
about 4 straight minutes. Two real bugs and one design gap came out of
debugging that log, all fixed now:

1. **`generate_json`'s own retry loop never actually ran.** It only caught
   `json.JSONDecodeError`, so when `generate_text` raised (an API outage,
   not a parsing problem), that exception skipped straight past the loop
   instead of being retried. All the apparent "retrying" in the failed run
   was actually `write_script`'s outer loop burning through both models
   with almost no wait between attempts. Fixed: `generate_json` now retries
   on any failure, not just malformed JSON.
2. **Backoff was too short for a real outage** (1s/2s/4s). Gemini's own
   error message says these spikes are "usually temporary" — that only
   helps if the retry loop waits long enough for temporary to pass.
   `generate_text`'s backoff is now 5s/10s/20s (capped at 30s) per attempt.
3. **New outer safety net in `main.py`**: `_pick_research_and_write_script()`
   wraps word-pick + research + script-write with one additional full cycle
   (fresh word, fresh research, fresh script attempt) after a
   `WORD_SCRIPT_RETRY_COOLDOWN_SEC` (3 minute, configurable in
   `src/config.py`) cooldown — specifically for an outage that outlasts
   even the deeper per-call retries above. This is layered on top of, not
   instead of, the fixes above.
4. **Unrelated but found in the same log**: Wiktionary and Wikipedia were
   both returning `403 Forbidden` on every single run. Wikimedia's API
   gateway rejects the default `python-requests` User-Agent per their
   [User-Agent policy](https://meta.wikimedia.org/wiki/User-Agent_policy) —
   `src/etymology_researcher.py` now sends a descriptive one. This failed
   "gracefully" (empty string, script writing still worked from Gemini's
   own knowledge) so it never crashed anything, but every episode was
   silently missing real etymology/Wikipedia grounding until this fix.

None of this makes a sustained multi-hour Gemini outage survivable — at
some point the run genuinely should fail rather than hang for the entire
job timeout. If a run fails with "Word/research/script cycle failed after
2 full attempts", both a first attempt AND a retry 3 minutes later hit the
same wall; that's a real, extended outage (or a bad `GEMINI_API_KEY`, or a
non-retryable error being misclassified — check `_RETRYABLE_STATUS_HINTS`
in `src/llm_client.py` if this ever fires for something other than an
actual outage). Re-running the workflow later, once, is the correct move.

## Known limitations / things to verify before relying on this in production

- **Timing budget is tight, not guaranteed.** A long-video build involves
  8-10 sequential AI image calls (1s rate-limit sleep each), 8-10 separate
  TTS+alignment calls (one per scene), a kinetic-typography+Ken-Burns
  `filter_complex` pass per scene (~4s/scene in our tests), then concat →
  LUT → SFX → caption burn → music mix → re-encode. This routinely takes
  well over an hour depending on runner performance and Pollinations
  latency — the 350-minute workflow timeout is a ceiling, not an estimate.
  `main.py` logs elapsed time at every step (`=== STEP: ... === [elapsed:
  Ns]`) so you can see exactly where the time goes in your Actions logs.
- **GitHub Actions free-tier minutes** (2,000/month) can be used up faster
  than expected at 2 long-video runs/week if any run is slow or retries;
  monitor actual minutes consumed in the first few weeks and scale back to
  1 run/week if needed.
- **YouTube CTR via Analytics API**: `impressionClickThroughRate` typically
  requires impressions to have accrued and may behave differently for
  Shorts vs. long-form; `ctr_optimizer.py` treats a missing/unavailable CTR
  metric as "skip the CTR gate, fall back to average-view-percentage only"
  rather than guessing a number. It also caps itself: max 2 regeneration
  attempts per video, a 7-day cooldown between attempts, never touches
  videos older than 28 days or with under 100 views (see `CTR_*` constants
  in `src/config.py`) — this exists specifically so a genuinely bad title
  doesn't get rewritten forever, chasing noise in low-traffic stats.
- **YouTube API daily quota** is 10,000 units; each upload costs ~1,600
  units, so 1 long + 2 shorts in a single run (~4,800 units) plus daily
  optimizer updates should fit, but this isn't heavily margin-tested here.
- **AI-content disclosure**: uploads set `containsSyntheticMedia: true` on
  the video status (YouTube's disclosure requirement for realistic
  synthetic voice/visuals). If your API version rejects that field, the
  uploader retries once without it rather than losing a multi-hour render
  over a metadata technicality — but check your channel's content settings
  reflect AI use regardless.
- **No named/fabricated statistics**: the script-writing prompt explicitly
  tells Gemini not to invent specific studies or precise numbers it isn't
  confident about, and to hedge with general phrasing instead — worth
  spot-checking generated scripts for this periodically.
- **Shorts duration tradeoff**: a Short's narration is trimmed to end on a
  complete sentence within YouTube's 20-35s window where possible (never
  mid-sentence), falling back to a hard cut at 35s only if no sentence
  boundary exists in range — see `plan_short_cut()` in `short_deriver.py`.
- **Vertical Shorts are rebuilt from scene images**, not center-cropped from
  the finished long render, so they'll look slightly different in framing
  from the long video (intentional — cleaner vertical composition).
- **Gemini model names** (`gemini-3.7-flash` / `gemini-3.6-flash`, set in
  `src/config.py`) should be re-checked against
  [ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models)
  periodically — model availability and naming shift over time.
- **HuggingFace image fallback** uses the shared free Inference API, which
  can return a `503` while a model cold-starts; the code treats that as
  "skip to the next free source" rather than waiting, to avoid stalling
  scene generation on a slow cold start.

## What's been tested end-to-end (not just compiled)

Everything below was verified by actually running ffmpeg/the pipeline in a
sandbox and inspecting output frames/audio, not just checked for syntax:

- Multi-scene `build_long_video()` with real per-scene audio durations,
  all three kinetic-typography styles in the same video, LUT, captions,
  music, SFX, and final encode — video/audio duration match confirmed via
  `ffprobe`.
- Each kinetic typography style individually, frame-by-frame, on a real
  Ken Burns background (not just a flat test canvas).
- The `format=yuv420p`-mid-graph color bug (found, root-caused, fixed).
- The bounce-caption hardcoded-coordinates bug on both long and short
  canvases (found, fixed, re-verified on both).
- `short_deriver.py`'s single-short build with the updated kinetic
  typography positioning.
- `next_publish_slot()` against several now-times spanning both weekdays
  and both "too close to the slot" edge cases.

What is **not** yet tested end-to-end: a full real run against live
Gemini/YouTube APIs (everything above uses synthetic stand-ins for
LLM/API calls, since those need real credentials and would consume your
quota) — the review-mode-private-upload safety net exists precisely so
that first real run is low-risk.

## Local dry-run (without uploading)

You can exercise most of the pipeline locally by setting `GEMINI_API_KEY`
and running the individual modules (e.g. `python -c "from src.word_picker
import pick_word; print(pick_word())"`) before wiring up YouTube credentials
— everything through `build_long_video()` requires no YouTube auth at all.
