---
session_id: 551e1e58-b125-472f-9904-6ba921d1cb3d
date: 2026-09-30
time: "1:26 AM PDT – 4:16 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: re-fitting the VideoToolbox quality mapping

## Overview

This session picked up the baton `.baton/2026-09-30-vt-quality-refit.md`. It wrote
`tests/bench_vt.py`, measured the VideoToolbox `-q:v` that matches the CPU encode's SSIM on
synthetic and iPhone footage, and re-fitted `vt_quality()` with a separate HDR curve. Under
`--hw`, HLG phone footage now comes out at about 2–3.5× x265's bytes instead of 6–8×. There are
two commits; neither is pushed.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Sweep a `-q:v` grid once per clip and codec, then interpolate every CRF target from it** | VideoToolbox encodes are cheap. One curve serves CRF 18/23/28, and it keeps the bytes-vs-SSIM data for judging other designs later without new encodes. |
| **The bench calls `_cpu_encoder_args` / `_vt_args` instead of copying argument lines** | It measures exactly what the scripts run: the HDR CRF+2 offset, the Main10 `p010le` line and the BT.709 bitstream-filter tags. |
| **Pair frames with `settb=1/1000,setpts=N`, not `setpts=N/FRAME_RATE/TB`** | The old recipe rounds whenever the time base does not divide the frame duration, so two frames in three were compared with a neighbour (see Discoveries). |
| **Interpolate the match in SSIM dB, and take the first crossing** | Near 1.0, raw SSIM barely moves between grid points. The first crossing is the conservative choice on a noisy curve. (Suggested by the Opus review of the bench.) |
| **HDR gets its own curve; there is no content class and no bitrate ceiling** | Every HLG clip needed `-q:v` 16–22 below the SDR curve, including a 30 fps clip from the same phone as the SDR clip. So the gap follows `bt2020_or_hdr`, a probe fact, not content. The user chose "HDR branch + steeper SDR" from three options (the others were HDR only, and HDR plus a bitrate ceiling). |
| **At each CRF, take the highest matched `-q:v` across the clips** | A GPU encode then never measures below the CPU encode, and the clips that need less pay in bytes. HDR is set by IMG_0776 (30 fps); the 60 fps clips pay 2.6–3.5× x265's bytes. |
| **The HDR curve applies only to the HEVC Main10 line** (`hdr and codec == "hevc"`) | The Fable review found an export preset's H.264 line on an HDR source picking up `-q:v 63`. That line replaces x264 at the same CRF, so it keeps the H.264 curve. |
| **Keep hardware decode deferred** | It helped only on 10-bit HEVC at 60 fps (single timings) and did nothing for H.264 SDR or the synthetic clips. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`tests/bench_vt.py`** (commit `dbeb01f`) | New bench. Uses three synthetic 1080p30 clips (testsrc2, mandelbrot, grain on gradients) plus any `--clip`. Encodes the CPU line at `--crf`, sweeps VideoToolbox `-q:v` (default 4–100 in steps of 4, plus today's values), and reports the matched q, bytes and time as JSON and a markdown table. Optional `--hwdec` timing. A frame-count mismatch against the reference fails the run, because the ssim filter would otherwise repeat the shorter input's last frame. |
| **`vt_quality(codec, crf, hdr=False)`** (commit `ea481f6`, `scripts/_common/decision.py`) | CRF 18/23/28 maps to: HDR 63/55/47 (was 78/69/60); h264 SDR 75/64/53 (was 75/66/58); hevc SDR 78/68/58 (was 78/69/60). The fit comment was rewritten. `_vt_args` passes `hdr and codec == "hevc"`. |
| **Tests** (`tests/test_accel.py`) | The monotonic/bounded test now covers the HDR curve. New: `test_an_hdr_source_gets_the_hdr_quality_curve`, `test_the_curves_keep_the_measured_values`, `test_an_h264_line_on_an_hdr_source_keeps_the_h264_curve`. |
| **Docs** | `docs/design-decisions.md` §2.4 has an updated measurement sentence and a new bullet on the safe-side fit and the HDR curve. README, `references/gotchas.md`, `emit.py` `ENV_HW_NOTE` and `docs/setup/HANDOFF-replicate-on-second-mac.md` now give 1.1–2.9× (SDR) / 1.9–3.5× (HDR) in place of 1.2–2.5×. CHANGELOG has a new entry, and two older Unreleased lines that cited the M4 Max fit and 1.2–2.5× were corrected. |
| **Memory** | `iphone-ssim-pair-by-index.md` was corrected: the `setpts=N/FRAME_RATE/TB` recipe it recommended is not enough. |

## Testing / Research Performed

- **Bench runs:**
  - A 2 s smoke run exposed the pairing bug (a CG clip scored 0.95 SSIM at CRF 23). A second smoke run after the fix gave 0.976–0.987.
  - Full run: 7 clips (3 synthetic, IMG_0761, IMG_0757, IMG_0776, IMG_0777) × CRF 18/23/28 × a ~27-point sweep, 11 clip-codec pairs with `--hwdec`. It exited 0, with JSON kept in the session scratchpad.
- **Candidate-fit evaluation:** the approved fit was checked against every sweep curve. All 33 rows land at or above the CPU SSIM. Three rows are within 0.3 q, inside VideoToolbox's run-to-run noise.
- **Reviews:**
  - Codex on the bench hit its usage limit and produced nothing.
  - Opus subagent on the bench: SHIP, with 2 guards adopted (frame-count check, dB interpolation plus a monotonic flag).
  - Fable subagent, final review: SHIP after fixes. The H.264-on-HDR leak was reproduced here before it was fixed. Stale CHANGELOG/README claims and an overstated HDR spread were corrected.
  - Codex (`gpt-5.6-terra` xhigh) on the diff and fixes: no Critical or Major findings, one Minor (the stale setup-doc ratio), fixed.
- **Suites, each with a fresh `OUT`:**
  - before the review fixes: suite 724 OK (3 skipped), contract 150 OK (1 skipped);
  - on the final tree: suite 726 OK (3 skipped), contract 150 OK (1 skipped);
  - `tests.test_accel` 44 OK after the fixes.
  The only change after the final suite run was a doc line in the setup handoff, which no test reads (checked with grep).

## Summary Statistics

- Commits: 2 (`dbeb01f`, `ea481f6`), not pushed.
- Files changed in `ea481f6`: 9. New file in `dbeb01f`: 1.
- Clips benchmarked: 7 (4 real iPhone 17 Pro, 3 synthetic), giving 33 CRF rows.
- Review passes: 4 (1 Codex that produced nothing, 1 Opus, 1 Fable, 1 Codex).
- Bugs found and fixed: 2. One in measurement (the SSIM pairing recipe) and one in code (the HDR curve on the H.264 line).

## Discoveries / Handoff Notes

- **`setpts=N/FRAME_RATE/TB` mispairs frames.** When the time base does not divide the frame duration it rounds: 1/1000 at 30 fps (ffv1/mkv), and 1/600 at 29.97 (IMG_0777 reports an average of 29.97). Two frames in three were then compared with a neighbour, measuring 27–29 dB for encodes that are really 45–47 dB. `settb=1/1000,setpts=N` on both inputs is exact at any rate. The baton's IMG_0777 SSIMs (0.9866/0.9858) came from the flawed recipe.
- **The ssim filter repeats the shorter input's last frame.** An encode 30 frames short measured 0.893 instead of about 0.99, with no error. The bench now checks frame counts.
- **HDR, not content, drives the gap.** At CRF 18/23/28 the HLG matches were 55.6–62.1 / 45.0–54.7 / 35.2–45.0, against SDR hevc on real footage at 76.2 / 66.3 / 57.7. The HDR matches spread by 6.6 at CRF 18 and about 10 at 23/28, with the 60 fps clips lowest.
- **Old mapping on HLG:** IMG_0761 at `-q:v 78` came to 6.77× x265's bytes (SSIM 0.9979 against 0.9888).
- **Hardware decode (`--hwdec`, single timings):**
  - IMG_0761 3.18 s → 1.45 s, IMG_0757 3.78 s → 2.87 s, IMG_0776 1.90 s → 1.59 s;
  - IMG_0777 (h264 SDR) and the ffv1 synthetic clips: no change.
- **The synthetic grain clip's curves are not monotonic** (temporal noise). It is a stress case and does not set the fit.
- **Codex ran out of usage** at the first review. The limit reset at 2:26 AM PDT, and the later pass ran normally.

## Current State

- Branch `m-series-hw-parakeet`, HEAD `ea481f6`. Two new commits are on top of `1be7895`, none pushed; the user pushes with `git push -u origin m-series-hw-parakeet`.
- The working tree is clean apart from the untracked `CLAUDE.local.md` (never committed) and this summary.
- `.baton/2026-09-30-vt-quality-refit.md` is still on disk. Its work has landed, and deleting it was offered to the user.

### Unfinished Work

- Retire `.baton/2026-09-30-vt-quality-refit.md` once the user confirms. The only item in it that has not landed is the deferred hardware-decode idea.
- Optional: time `-hwaccel videotoolbox` across more clips and filters (`tests/bench_vt.py --hwdec`) before deciding whether `--hw` should decode on the GPU.
- Optional: re-run `tests/bench_vt.py` on the M4 Max to confirm the curves hold on the other machine. They were measured on the M3.
