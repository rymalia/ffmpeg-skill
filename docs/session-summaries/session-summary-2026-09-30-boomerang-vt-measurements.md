---
session_id: 860d6167-9cea-4787-809d-d900ada96367
date: 2026-09-30
time: "2026-09-29 11:35 PM PDT – 2026-09-30 01:00 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: a boomerang loop, VideoToolbox options and hardware decode

## Overview

This session took the baton `.baton/2026-09-29-boomerang-loop-vt-options.md` and closed all three
of its items.
- It built `loop.py --boomerang` test-first and committed it as `0886993`, after three review
  passes that found and fixed two variable-frame-rate bugs.
- It measured the VideoToolbox encoder options and `-hwaccel videotoolbox` decoding on the user's
  iPhone footage. The user decided to adopt neither for now.
- It dropped a new baton for the one follow-up the numbers exposed: the CRF→`-q:v` fit overshoots
  badly on iPhone 60 fps HLG.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Boomerang frame order 0..N-1, then N-2..1** | Neither turnaround frame is shown twice. The tutorial's split/reverse/concat shows each one twice. The reverse branch is trimmed by frame index (`trim=start_frame=1,reverse,trim=start_frame=1`), so no frame count is needed. |
| **`loop=size=32767`, one constant** | Verified: `loop` replays what it has buffered when the stream ends before `size`. Only the real cycle length needs a cap, so a cycle over 32767 frames is refused. |
| **A boomerang is silent, with a `notes` line** | Reversed audio plays backwards. The user can add a bed with `audio.py`; this was the baton's lean. |
| **`--times` counts round trips, and 1 is allowed** | A single forward-and-back pass is a distinct, useful output. Without `--boomerang` the minimum stays 2. |
| **Retime by index at an exact-fraction rate, then `fps=`, passed through** | Review pass 1: `cfr_args` after the reverse duplicated a turnaround frame on VFR sources. Pass 2: without `fps=`, the encoder's time base followed the source's `r_frame_rate` and quantised the frames unevenly. |
| **The rate is `r_frame_rate` when within 1% of the average, else the average, else frames/duration, else 30; anything over 240 fps is a time base** | iPhone clips report 60/1 against 59.95 from a 1/600 time base. Pass 3 found that a 90000/1 `r_frame_rate` with no usable average would squeeze the clip into milliseconds. |
| **Memory warning counts about one clip of frames** | The reviewer measured `split`/`trim`/`loop` sharing frame references: max RSS matched a plain `reverse`. The first estimate of 3N-3 frames overcounted about 3×. |
| **No VideoToolbox encoder option adopted** | Three of them are no-ops in `-q:v` mode, and `prio_speed=1` is mixed (see Research). The user agreed. |
| **Hardware decode deferred** | It only wins for a `--hw` job with a CPU filter (about 4 s on a 10 s clip), and it would touch rotation, pixel formats and the CPU fallback. The user agreed to fold its timing into the re-fit bench instead. |
| **Re-fit `-q:v` in a later session** | Here, VideoToolbox wrote 112 MB against x265's 16 MB, from a 22 MB source. The new baton holds the method. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`--boomerang`** | `scripts/loop.py`: `_boomerang_graph`, `_nominal_rate`, `_fraction`, `LOOP_FILTER_MAX_FRAMES`, `MAX_PLAUSIBLE_FPS`, the docstring, `emit(boomerang=…, notes=…)`, and `-fps_mode passthrough` in boomerang mode. |
| **Tests** | `tests/test_editing.py`, 7 new tests: frame order by `framemd5` (`--times 2`, `--times 1`, `--duration 1.7`), dropped audio with a note, a VFR source (order plus even packet durations and r = avg), the rate choice, and the under-3-frames refusal. |
| **Contract** | `scripts/_contract.py`: the `loop` outputs text, optional `filter:reverse`/`filter:loop` when `--boomerang`, audio `conditional`, and a `loop` result schema (`boomerang`, `notes`). `tests/fixtures/mcp_tools.json` was regenerated. |
| **Docs** | `references/scripts.md` `loop.py` section and a `CHANGELOG.md` Unreleased entry. |
| **Commit** | `0886993 feat(loop): --boomerang plays a clip forward then backward`. Not pushed. |
| **Batons** | Retired `.baton/2026-09-29-boomerang-loop-vt-options.md`. Wrote `.baton/2026-09-30-vt-quality-refit.md`. |
| **Reference docs** | The user deleted both untracked `docs/ref-*` files. |

## Testing / Research Performed

- **Red, then green, with TDD:**
  - five boomerang tests were red on the missing flag, then green;
  - the VFR test was red with `[… 5, 4, 4, 3 …]`, then green;
  - its timing assertion was red with 1024/2048 packets, then green;
  - the rate test was red with `'90000/1' != '25'`, then green.
- **Full suite:**
  - The first run failed 8 tests, plus 1 error. Every one was `refusing to overwrite existing
    output` from stale `tests/out` files, not from this diff.
  - It was re-run with a fresh `OUT`: **722 OK (3 skipped)**. The contract ran **150 OK
    (1 skipped)**, after the MCP snapshot was regenerated.
  - After the final rate fix: `test_editing` **141 OK** with a fresh `OUT`, the contract OK, and
    boomerang tests 7 OK.
- **Real footage:**
  - IMG_0761, 2 s cut, `--duration 5`: 300 frames at 60/1 = 5.000 s, `yuv420p10le`, `arib-std-b67`,
    audio dropped with a note.
  - A synthetic 60000/1001 clip with `--duration 30`: 1798 frames × 1001 ticks = 29.997 s.
  - The reviewer's NTSC 1/600 MOV: 476 frames, every packet 1001 ticks.
- **Review:** an Opus `general-purpose` subagent made three passes (Codex was at its usage limit
  until 2:26 AM). It found the VFR duplicate, the uneven timing, the unchecked `r_frame_rate`
  fallback and the overcounted memory estimate. Each finding was reproduced before it was fixed.
- **VideoToolbox options** (M3 Air, FFmpeg 9.0.2; `-q:v` 66 for h264, 69 for hevc; SSIM paired by
  frame index; best of 2 runs):

  | Clip / codec | Baseline | `spatial_aq=1` / `power_efficient=1` / `prio_speed=0` | `prio_speed=1` |
  |---|---|---|---|
  | IMG_0777 SDR 1080p30, h264 | 0.9866, 8.16 MB, 1.46 s | identical | identical |
  | IMG_0777, hevc | 0.9858, 6.41 MB, 1.57 s | identical | 0.9856, 6.40 MB, 0.97 s |
  | IMG_0761 HLG 1080p60, hevc | 0.9957, 55.3 MB, 3.14 s | identical | 0.9953, 59.8 MB, 3.38 s |

- **Hardware decode** (IMG_0761, 9.3 s):
  - GPU and CPU decodes are **bit-identical**: 559 of 559 framemd5.
  - Decode alone: CPU 2.15 s, GPU 0.76 s.
  - Every path kept `yuv420p10le`, bt2020 and `arib-std-b67`.

  | Decode → encode | No filter | `scale=1280:-2` |
  |---|---|---|
  | CPU → x265 (medium, CRF 20) | 36.5 s, 16.4 MB, 0.989 | 20.0 s |
  | GPU → x265 | 37.6 s | 23.0 s |
  | CPU → VideoToolbox (q 78) | 3.19 s, 112 MB, 0.998 | 6.41 s |
  | GPU → VideoToolbox | 3.13 s | 2.51 s |
  | All-GPU `scale_vt` | — | 1.89 s, SSIM 0.994 |

## Summary Statistics

- 1 commit (`0886993`): 6 files changed.
- 7 new tests, all red first.
- 4 bugs fixed before commit: the VFR duplicate frame, uneven VFR timing, the unchecked time-base
  rate, and the overcounted memory warning.
- 3 review passes.
- 15 encoder-option measurements, 9 decode/encode paths, and 1 decode bit-exactness check.

## Discoveries / Handoff Notes

- **SSIM/PSNR on iPhone footage must pair frames by index.** The filters pair by timestamp, and
  iPhone timestamps jitter (1.801667 where 1.800 is expected). The first bench read 0.795 SSIM and
  24.9 dB for an encode that is really 0.9957 SSIM and about 48 dB. `libx265` showed the same
  "slip", which proved it was the metric, not the encoder. Use `setpts=N/FRAME_RATE/TB` on both
  inputs.
- **VideoToolbox output is not bit-deterministic.** Its MD5 changes run to run even with `-q:v`,
  so compare bytes and SSIM.
- **`-spatial_aq`, `-power_efficient` and `-prio_speed 0` do nothing in `-q:v` mode on this M3 Air.**
  They are accepted silently.
- **`scale_vt` needs no `-pix_fmt`.** Passing `-pix_fmt p010le` on the all-GPU path fails with
  EINVAL.
- **`tests/out` is never wiped.** Reusing it makes unrelated tests fail on the refuse-to-overwrite
  guard, so run a suite with a fresh `OUT=`.
- **The baton was off in three places:**
  - there was 41 GiB free, not 12;
  - the tutorial doc was never committed;
  - the iPhone clips are 1080p, not 4K (there is no 4K footage on disk).
- **zsh:** `$x` is not word-split (use `${=x}`), and `$var[v]` is an array subscript.

## Current State

- Branch `m-series-hw-parakeet`, HEAD `0886993`, one commit ahead of `origin`. Push it with
  `git push -u origin m-series-hw-parakeet`, which the user does themselves.
- Untracked: `CLAUDE.local.md` only.
- `.baton/2026-09-30-vt-quality-refit.md` is the only baton.

### Unfinished Work

- **Re-fit `vt_quality` on mixed footage.** Write `tests/bench_vt.py` (x265/x264 at CRF 18/23/28
  against a `-q:v` sweep, SSIM paired by index), show the table, then change the fit or add a
  bitrate ceiling. The full plan is in `.baton/2026-09-30-vt-quality-refit.md`.
- **Hardware decode on `--hw`:** deferred. Time it on the re-fit bench's clips, and adopt it only if
  the win holds broadly.
