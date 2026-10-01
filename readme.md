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
  Pexels/Pixabay fallback — see "Run #114 fixes" below for why HuggingFace
  isn't in that chain), synthesizes voiceover **per scene**
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
   - Optional free-tier keys: `PEXELS_API_KEY`, `PIXABAY_API_KEY`,
     `POLLINATIONS_API_KEY` (free at [enter.pollinations.ai](https://enter.pollinations.ai) —
     see "Run #113 fixes" below for why this was added). `HF_TOKEN` is
     accepted but currently unused by default — see "Run #114 fixes" for why
     the HuggingFace image fallback is disabled.
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

## Run #114 fixes: model priority swap, HuggingFace removed, script rewrite

Run #114 **succeeded** (26m57s) — the OAuth fix and Pollinations/HF endpoint
updates from run #113 all worked. Pixabay ended up carrying the entire run
(every scene image, 8 of 9 calls succeeded there), which prompted a few
more changes:

1. **gemini-3.6-flash is now PRIMARY, gemini-3.7-flash is the fallback**
   (`src/config.py`) — per your request, and backed by real evidence: two
   consecutive production runs both hit sustained 503 "high demand" on
   gemini-3.7-flash specifically (every retry, every time), while
   gemini-3.6-flash succeeded immediately as the fallback both times. If
   3.7's availability visibly improves in your own logs later, swap it
   back by setting the `GEMINI_PRIMARY_MODEL`/`GEMINI_FALLBACK_MODEL` repo
   secrets rather than editing the code.
2. **The HuggingFace image fallback is now disabled** (not called from the
   active chain in `src/visual_generator.py`). The corrected
   `router.huggingface.co` endpoint from the last fix still returned `410
   Gone` — this time because `black-forest-labs/FLUX.1-schnell` isn't
   deployable via any of HuggingFace's current Inference Providers at all
   (confirmed on the model's own HuggingFace page), not because of a wrong
   URL. Guessing a replacement model risked a third broken fix in a row, so
   the function is kept as a reference implementation with a clear comment
   on what to verify before re-enabling it, rather than guessed at again.
   The chain is now Pollinations → Pexels → Pixabay.
3. **Pixabay now has an explicit rate-limit pause** (`PIXABAY_SLEEP_SEC` in
   `src/config.py`, 0.6s/call) — their free tier is 100 requests/60s. A
   single run's ~9 calls wouldn't hit that alone, but Pixabay has become
   the pipeline's de facto primary source while Pollinations/Pexels are
   unreliable, and this costs nothing to add now.
4. **Pexels 403 is still unresolved — diagnosed, not fixed.** Your
   `PEXELS_API_KEY` is confirmed set (the code skips Pexels entirely with
   no key) but every scene call returned `403 Forbidden` — except one
   thumbnail call ~20 minutes later in the same run, which succeeded with
   the same key. Pexels' own docs treat 403 ("Forbidden" — an access/key
   problem) and 429 ("Too Many Requests" — a rate-limit problem) as
   distinct, and their free-tier limit (200/hour) is far above what this
   run used, so this doesn't look like ordinary rate limiting either. One
   intermittent success doesn't fit a simple "bad key" theory cleanly, and
   I can't test your actual key from here — **please verify it directly**:
   ```
   curl -H "Authorization: $PEXELS_API_KEY" "https://api.pexels.com/v1/search?query=cat&per_page=1"
   ```
   outside this pipeline, and check its status on your Pexels dashboard.
   If that curl also 403s, the key itself is the problem; if it succeeds,
   there's something more specific to this pipeline's request pattern
   worth investigating further (header casing, a WAF rule on rapid
   sequential calls — genuinely uncertain without being able to reproduce
   it here).
5. **Script-writing prompt substantially rewritten for retention**
   (`src/script_writer.py`). The previous prompt described the desired
   tone ("mystery/suspense/thriller") but gave little concrete guidance on
   *how* to keep viewers watching. The new prompt is built around named,
   well-documented retention mechanisms rather than vibes:
   - **open-loop stacking** (a chain of unresolved questions, not one hook
     that resolves into flat exposition),
   - explicit guidance that **the first 15 seconds** (no channel-intro
     throat-clearing, hook as the literal first sentence) and the **30-60s
     / 40-60% marks** (mandatory re-hooks) are the documented drop-off
     cliffs to defend,
   - **specificity-over-abstraction** and **escalating stakes** rules with
     concrete good/bad examples,
   - a **banned-patterns list** of the specific phrases/structures that
     make a script read as generic or AI-flavored ("In this video...",
     "In conclusion...", repeated rhetorical-question crutches, three
     sentences in a row with identical openings),
   - pacing guidance given as **proportions of runtime** rather than fixed
     minute-marks, since actual scene count/length varies run to run.

   This can't be benchmarked from here without real Gemini calls and real
   audience data, so treat it as a strong starting point to evaluate
   against your own actual output — if a particular banned pattern keeps
   slipping through, or a retention mechanic isn't landing, that's a
   one-line addition to the prompt, not a rewrite.

## Run #113 fixes: OAuth invalid_scope, Pollinations migration, dead HF endpoint

A second real run got past the Gemini resilience fixes above (both models
succeeded on retry — confirms those fixes work) but then hit three more
issues, all fixed now:

1. **CRITICAL — uploads were failing with `invalid_scope: Bad Request`.**
   `_get_credentials()` in `src/youtube_uploader.py` was passing an explicit
   `scopes=` list to the refresh-token `Credentials` object. google-auth
   sends that in the token-refresh request, and if it doesn't *exactly*
   match what your refresh token was actually granted during the one-time
   OAuth Playground consent (easy to get out of sync — e.g. only checking
   2 of the 3 scope boxes), Google's token endpoint rejects the refresh
   entirely — which fails **every** API call, not just ones needing the
   missing scope. Fixed: `scopes` is no longer passed on refresh (it's not
   needed there — omitting it lets the refresh succeed with whatever was
   actually granted). The `SCOPES` list still documents what to select
   during the initial OAuth Playground consent step.
   **If you still see `invalid_scope` after updating**: your refresh token
   itself may have been issued without one of the 3 scopes. Regenerate it
   via OAuth Playground, double-checking all three boxes
   (`youtube.upload`, `youtube`, `yt-analytics.readonly`) are selected
   before exchanging for a refresh token.
2. **Pollinations migrated their API — the old endpoint now 402s.** The
   real run's logs showed `402 Payment Required` from
   `image.pollinations.ai/prompt/...` on every single scene. That host is
   being deprecated in favor of a unified API at `gen.pollinations.ai`.
   Fixed: `POLLINATIONS_BASE` now points at
   `https://gen.pollinations.ai/image/`. Pollinations' own documentation is
   inconsistent about whether unauthenticated basic access still works on
   the new host — if scene generation keeps failing here, get a free key at
   [enter.pollinations.ai](https://enter.pollinations.ai) and set it as the
   `POLLINATIONS_API_KEY` secret (optional — code works without it, just
   less reliably per Pollinations' own docs).
3. **The HuggingFace image fallback was calling a dead endpoint.**
   `api-inference.huggingface.co` now returns HTTP 410 with HuggingFace's
   own message: *"no longer supported, use
   https://router.huggingface.co/hf-inference instead."* Same request
   shape, just the wrong host. Fixed: `HF_INFERENCE_BASE` now points at
   `https://router.huggingface.co/hf-inference/models/`.
4. **Pexels returned 403 in that run.** This means a `PEXELS_API_KEY` was
   set (the code skips Pexels entirely with no key) but was rejected — most
   likely invalid, revoked, or mistyped. Check the key in your Pexels
   dashboard; this isn't something the code can fix for you.
5. **Added success logging for every fallback source.** Previously only
   failures were logged, so a run where e.g. Pixabay quietly saved the day
   for every scene looked, from the logs alone, like "everything failed but
   somehow it worked anyway" — confusing to debug. Each of
   `generate_scene_image()`/`generate_thumbnail()` now logs which source
   actually succeeded (`"Scene 3 image: Pixabay succeeded"`, etc.).

6. **Bonus find while fixing the above**: `ctr-optimizer.yml` wasn't
   passing `HF_TOKEN`/`PEXELS_API_KEY`/`PIXABAY_API_KEY` to the daily CTR
   job at all — so a Pollinations failure during thumbnail regeneration had
   only HuggingFace available as a fallback (and only if `HF_TOKEN` was set
   some other way), instead of all four sources. Fixed: that workflow now
   passes the same image-source secrets `run-bot.yml` does.

**None of items 2-4 were things our retry logic could paper over** — a
dead or moved endpoint fails identically no matter how many times or how
patiently you retry it. This is also a useful general lesson for this
repo: when a free external API stops working, check whether it moved
(search "`<service> API migration`" / "`<service> deprecated endpoint`")
before assuming it's just down.

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
- **HuggingFace image fallback is disabled by default** (see "Run #114
  fixes") — the active visual chain is Pollinations → Pexels → Pixabay only.

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
