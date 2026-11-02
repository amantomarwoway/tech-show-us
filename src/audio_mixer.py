"""
Story-mode audio layering: voice-over (VO) + scene-by-scene background music
(BGM) + exact-timestamp sound effects (SFX), mixed with ffmpeg.

TIMELINE: the per-beat bgm_keyword / sfx_keyword / sfx_kind / sfx_trigger_word
fields come from the story writer (one LLM call, same JSON as the story
itself). The LLM cannot know real timings before the voice-over exists, so it
names KEYWORDS and (for one-shot effects) the TRIGGER WORD; the exact
millisecond is then computed here from the real, measured TTS durations and
the word-level alignment — more precise than asking the LLM to guess seconds.

MIX LEVELS (dB relative to the voice-over, which is peak-normalized and treated
as the 0 dB reference; see config):
  * BGM bed            -22 dB under narration
  * BGM during pauses  -12 dB whenever the VO is silent for >= 2 s (smooth
                        0.5 s ramps up and back down — no clicks)
  * ambient loops      -26 dB (rain, crickets, wind) looped for the beat span
  * action one-shots    -8 dB (door slam, scream, gunshot) at the exact moment
Every fetched asset is first peak-normalized so those offsets mean the same
thing for a quiet file and a loud one. These levels were MEASURED on real
mixed output (BGM 22.1 dB under the VO, 12.0 dB in pauses, SFX onset within
5 ms of the requested timestamp) — see tests/test_story_wiring.py.
"""
import logging
import re
import shutil
import subprocess
from pathlib import Path

from src.audio_fetcher import get_bgm, get_sfx
from src.config import (
    STORY_ACTION_DB,
    STORY_AMBIENT_DB,
    STORY_BGM_CROSSFADE_SEC,
    STORY_BGM_DB,
    STORY_BGM_PAUSE_DB,
    STORY_PAUSE_MIN_SEC,
)

log = logging.getLogger(__name__)

_RAMP_SEC = 0.5


def _norm_keyword(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _norm_word(word) -> str:
    return re.sub(r"[^a-z0-9']+", "", str(word or "").lower())


def _trigger_offset(trigger_word, words, duration: float) -> float:
    """Seconds into the beat at which `trigger_word` is spoken (from the
    word-level alignment). Falls back to the beat's start if the word is
    missing/not found — an action effect a little early beats a lost one."""
    target = _norm_word(trigger_word)
    if not target or not words:
        return 0.0
    for w in words:
        if _norm_word(w.get("word")) == target:
            return max(0.0, min(float(w.get("start", 0.0)), max(duration - 0.05, 0.0)))
    return 0.0


def build_audio_timeline(beats: list[dict], durations: list[float], local_words: list) -> dict:
    """Pure function (no I/O): turns per-beat fields + real durations into
        {"total": seconds,
         "bgm_segments": [{"keyword", "start", "end"}],       # consecutive same-mood beats merged
         "sfx_events":   [{"keyword","kind","start"[, "end"]}]}  # ambient spans merged too
    All three lists must be the same length and in beat order."""
    starts, t = [], 0.0
    for d in durations:
        starts.append(t)
        t += d
    total = t

    segments: list[dict] = []
    for beat, st, dur in zip(beats, starts, durations):
        kw = _norm_keyword(beat.get("bgm_keyword")) or "dark ambient drone"
        if segments and segments[-1]["keyword"] == kw:
            segments[-1]["end"] = st + dur
        else:
            segments.append({"keyword": kw, "start": st, "end": st + dur})

    events: list[dict] = []
    for beat, st, dur, words in zip(beats, starts, durations, local_words):
        kw = _norm_keyword(beat.get("sfx_keyword"))
        kind = str(beat.get("sfx_kind") or "none").strip().lower()
        if not kw or kw == "none" or kind not in ("ambient", "action"):
            continue
        if kind == "ambient":
            if events and events[-1]["kind"] == "ambient" and events[-1]["keyword"] == kw \
                    and abs(events[-1]["end"] - st) < 0.01:
                events[-1]["end"] = st + dur
            else:
                events.append({"keyword": kw, "kind": "ambient", "start": st, "end": st + dur})
        else:
            offset = _trigger_offset(beat.get("sfx_trigger_word"), words, dur)
            events.append({"keyword": kw, "kind": "action", "start": st + offset})

    return {"total": total, "bgm_segments": segments, "sfx_events": events}


def detect_pauses(media_path: Path, min_sec: float = STORY_PAUSE_MIN_SEC) -> list[tuple[float, float]]:
    """(start, end) of every stretch where the voice-over is silent for at
    least `min_sec` — found by ffmpeg's silencedetect on the real audio, not
    guessed from the script."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-vn", "-i", str(media_path),
         "-af", f"silencedetect=noise=-35dB:d={min_sec}", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    pauses, start = [], None
    for line in proc.stderr.splitlines():
        m = re.search(r"silence_start:\s*(-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = re.search(r"silence_end:\s*([\d.]+)", line)
        if m and start is not None:
            pauses.append((start, float(m.group(1))))
            start = None
    if start is not None:  # file ended while still silent
        dur = _media_duration(media_path)
        if dur > start + min_sec:
            pauses.append((start, dur))
    return pauses


def _media_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def _peak_gain_db(path: Path, target_peak_db: float = -1.0) -> float:
    """dB gain that brings this file's loudest peak to target_peak_db
    (measured with ffmpeg volumedetect). 0 if it can't be measured."""
    # Measured AFTER the same mono->stereo conversion the mix applies: ffmpeg's
    # default upmix changes a mono source's level, so measuring before it (an
    # earlier version did) left mono assets ~3 dB off the configured level —
    # caught by measuring the actual mixed output.
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-vn", "-i", str(path),
         "-af", "aformat=channel_layouts=stereo,volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", proc.stderr)
    if not m:
        return 0.0
    return max(-30.0, min(40.0, target_peak_db - float(m.group(1))))


def _bgm_gain_expr(pauses: list[tuple[float, float]]) -> str:
    """volume= argument for the summed BGM bus: constant STORY_BGM_DB, lifted
    toward STORY_BGM_PAUSE_DB inside each pause with smooth ramps."""
    if not pauses:
        return f"volume={STORY_BGM_DB}dB"
    delta = STORY_BGM_PAUSE_DB - STORY_BGM_DB
    terms = "+".join(
        f"clip(min((t-{s:.3f})/{_RAMP_SEC}\\,({e:.3f}-t)/{_RAMP_SEC})\\,0\\,1)"
        for s, e in pauses
    )
    return f"volume='pow(10\\,({STORY_BGM_DB}+{delta}*({terms}))/20)':eval=frame"


def mix_story_audio(
    video_in: Path,
    video_out: Path,
    timeline: dict,
    *,
    fetch_bgm=get_bgm,
    fetch_sfx=get_sfx,
    normalize_output: bool = True,
) -> dict:
    """Layers BGM + SFX under the video's existing voice-over track and writes
    `video_out` (video stream copied untouched). Never raises for a missing
    asset: anything that couldn't be fetched is skipped, and if NOTHING could
    be fetched the video is simply copied through. Returns a report dict."""
    total = min(timeline["total"], _media_duration(video_in) or timeline["total"])
    report = {"bgm_segments": 0, "sfx_events": 0, "pauses": [], "copied_through": False}

    bgm_cache: dict[str, Path | None] = {}
    bgm_items = []
    for seg in timeline["bgm_segments"]:
        kw = seg["keyword"]
        if kw not in bgm_cache:
            bgm_cache[kw] = fetch_bgm(kw)
        if bgm_cache[kw] is not None:
            bgm_items.append((seg, bgm_cache[kw]))

    sfx_cache: dict[str, Path | None] = {}
    sfx_items = []
    for ev in timeline["sfx_events"]:
        kw = ev["keyword"]
        if kw not in sfx_cache:
            sfx_cache[kw] = fetch_sfx(kw)
        if sfx_cache[kw] is not None:
            sfx_items.append((ev, sfx_cache[kw]))

    if not bgm_items and not sfx_items:
        log.warning("No BGM or SFX assets available — copying video through unchanged")
        if Path(video_in) != Path(video_out):
            shutil.copy(video_in, video_out)
        report["copied_through"] = True
        return report

    pauses = detect_pauses(video_in)
    report["pauses"] = pauses

    input_args = ["-i", str(video_in)]
    # The voice-over is the 0 dB reference: peak-normalize it like every other
    # asset so "BGM at -22 dB" really means 22 dB below the narration's peak.
    vo_norm = _peak_gain_db(video_in)
    chains: list[str] = [
        f"[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={vo_norm:.2f}dB[vo]"
    ]
    mix_labels = ["[vo]"]
    idx = 1

    # ---- BGM segments (crossfaded, summed into one bus) ----
    xf = STORY_BGM_CROSSFADE_SEC
    bgm_labels = []
    for seg, path in bgm_items:
        start = max(0.0, seg["start"] - xf / 2)
        end = min(total, seg["end"] + xf / 2)
        length = max(end - start, 0.5)
        fade = min(xf, length / 2)
        norm = _peak_gain_db(path)
        ms = int(start * 1000)
        input_args += ["-stream_loop", "-1", "-i", str(path)]
        chains.append(
            f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"atrim=0:{length:.3f},asetpts=PTS-STARTPTS,volume={norm:.2f}dB,"
            f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={max(length - fade, 0):.3f}:d={fade:.3f},"
            f"adelay={ms}|{ms}[b{idx}]"
        )
        bgm_labels.append(f"[b{idx}]")
        idx += 1
    if bgm_labels:
        if len(bgm_labels) == 1:
            chains.append(f"{bgm_labels[0]}anull[bgmsum]")
        else:
            chains.append(
                "".join(bgm_labels) + f"amix=inputs={len(bgm_labels)}:normalize=0:dropout_transition=0[bgmsum]"
            )
        chains.append(f"[bgmsum]{_bgm_gain_expr(pauses)}[bgm]")
        mix_labels.append("[bgm]")

    # ---- SFX events ----
    for ev, path in sfx_items:
        norm = _peak_gain_db(path)
        ms = int(ev["start"] * 1000)
        if ev["kind"] == "ambient":
            end = min(total, ev["end"])
            length = max(end - ev["start"], 0.5)
            fade = min(0.5, length / 2)
            input_args += ["-stream_loop", "-1", "-i", str(path)]
            chains.append(
                f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
                f"atrim=0:{length:.3f},asetpts=PTS-STARTPTS,volume={norm + STORY_AMBIENT_DB:.2f}dB,"
                f"afade=t=in:st=0:d={fade:.3f},afade=t=out:st={max(length - fade, 0):.3f}:d={fade:.3f},"
                f"adelay={ms}|{ms}[s{idx}]"
            )
        else:
            input_args += ["-i", str(path)]
            chains.append(
                f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
                f"volume={norm + STORY_ACTION_DB:.2f}dB,adelay={ms}|{ms}[s{idx}]"
            )
        mix_labels.append(f"[s{idx}]")
        idx += 1

    tail = "alimiter=limit=0.95"
    if normalize_output:
        tail += ",loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"
    chains.append(
        "".join(mix_labels)
        + f"amix=inputs={len(mix_labels)}:normalize=0:duration=first:dropout_transition=0,{tail}[aout]"
    )

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", *input_args,
        "-filter_complex", ";".join(chains),
        "-map", "0:v:0", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(video_out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # A mixing failure must not lose a finished video.
        log.error("Audio mix failed (%s) — shipping the voice-over-only video", (e.stderr or "")[-400:])
        if Path(video_in) != Path(video_out):
            shutil.copy(video_in, video_out)
        report["copied_through"] = True
        return report

    report["bgm_segments"] = len(bgm_items)
    report["sfx_events"] = len(sfx_items)
    return report
