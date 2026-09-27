---
session_id: c5ed860f-d42c-4698-9f44-2b6c571bcb0f
date: 2026-09-27
time: "2026-09-26 9:53 PM PDT – 2026-09-27 3:57 PM PDT"
resumed: "2026-09-27 3:56 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: `--hw` on real footage (follow-up)

## Overview

This follows [session-summary-2026-09-27-videotoolbox-parakeet-fork.md](session-summary-2026-09-27-videotoolbox-parakeet-fork.md), which covers the main work of this session: the VideoToolbox `--hw` and Parakeet implementation, reviews, tests, commit `3ff6462`, and the install/symlink layout. After that summary was written, the session committed and pushed it, then ran the first `--hw` test on the user's own footage: a Reels delivery rendered on the GPU and on the CPU from the same clip, both verified.

**Timestamp note:** the session was resumed at 3:56 PM. On this run the collector reported `session_start` equal to the resume time. The original start, `2026-09-26 09:53 PM PDT`, comes from this session's first collector run (recorded in the earlier summary), so it is used for the range above.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Test clip: `good-blended-video-1759239237943.mp4` through the `reels` template** | All three candidates are ≤720p, where x264 is already fast. A Reels render upscales to 1080×1920, so encode cost dominates, and it also covers VFR→CFR conforming (the source is VFR, ~74.5 fps average) and the full chain: fit, loudness, export, check. |
| **Same edit twice, `render.py --hw` vs `--no-hw`** | `render.py --hw` is the only switch that also puts the export stage on the GPU. `--no-hw` overrides `FFMPEG_SKILL_HW=1` from `~/.zshenv`, which gives a clean CPU baseline. |
| **Outputs in `~/Downloads/ffmpeg-skill-hw-test/`** | Keeps the user's originals and the Downloads root untouched (skill workflow step 7). |
| **Crop framing reported, not changed** | Where the subject sits is a judgement call the skill leaves to the user; the options were offered (`--fit blur`, `--crop-x`). |

## Changes Made

| Change | Detail |
|--------|--------|
| **Committed the first session summary** | `1922a59 docs: session summary for the VideoToolbox + Parakeet work` on `m-series-hw-parakeet`, pushed to `origin` (`3ff6462..1922a59`). Committed at the user's explicit request. |
| **Test outputs (not in the repo)** | `~/Downloads/ffmpeg-skill-hw-test/`: `blended_reels--hw.mp4`, `blended_reels--no-hw.mp4`, `r--hw.json`, `r--no-hw.json`, `sheet--hw.png`, `sheet--no-hw.png` |
| **This summary** | Written after `1922a59`; not committed. |

## Testing / Research Performed

- **Probed all three candidate clips** (`probe.py --json`):
  - `good-blended-video-1759239237943.mp4`: 640×360, fps 74.49, VFR suspected, 19.7 s, BT.709.
  - `retarded.mp4`: 720×540, 29.97 fps, 38.9 s, no colour tags.
  - `Chinese Neon.mp4`: 320×568, 30 fps, 25.3 s.
- **Render comparison** (`render.py --template reels`, wall time including loudness passes, probes and check):

  | | `--hw` | `--no-hw` |
  |---|---|---|
  | Wall time | 14.3 s | 21.7 s |
  | Encoder (final) | h264_videotoolbox | libx264 |
  | Size / video bitrate | 45.06 MB / 17.9 Mb/s | 28.33 MB / 11.1 Mb/s |
  | Output | 20.008 s, 1080×1920, 30 fps | same |
  | Reels check | loudness −14.3 LUFS PASS, true peak −1.0 dBTP PASS, `verified: true` | same |
  | Colour tags | bt709/bt709/bt709 | bt709/bt709/bt709 |

- **SSIM between the GPU and CPU outputs:** All 0.983079.
- **Contact sheet `sheet--hw.png` viewed** (copied to the scratchpad because reading `~/Downloads` directly was denied). Colours look natural with no washout. The centre crop partly cuts off the woman on the left at 0 s and leaves the dog at the left edge, mostly out of frame, by 16.5 s. `sheet--no-hw.png` was generated but not viewed.

## Summary Statistics

- Clips probed: 3; renders: 2 (both `verified: true`); contact sheets: 2 (1 viewed)
- End-to-end speedup on this clip: 1.5× (14.3 s vs 21.7 s); size penalty: 1.59× (45.06 vs 28.33 MB)
- Commits this segment: 1 (`1922a59`), pushed

## Discoveries / Handoff Notes

- **End-to-end speedup is smaller than encode-only.** On a short, low-resolution source, render's non-encode work (two-pass loudness, probes, check) is a fixed cost. The calibration's 2–7× applies to the encode step alone; 4K or long sources should show more.
- **Output ran 0.27 s longer than the source** (20.008 s vs 19.74 s) after VFR→30 fps conforming. Both GPU and CPU outputs are identical in this respect, so it is not related to `--hw`.
- **Reading files under `~/Downloads` needs permission** in this environment. Copying images into the session scratchpad works for `look.py` sheets.
- **The `reels` template crops by default,** so any off-centre subject can be lost.

## Current State

- Branch `m-series-hw-parakeet` at `1922a59`, in sync with `origin/m-series-hw-parakeet`. The working tree was clean before this file was written.
- Installed skill: `~/.agents/skills/ffmpeg-skill` (from the fork) with `~/.claude/skills/ffmpeg-skill` symlinked to it; `FFMPEG_SKILL_HW=1` set in `~/.zshenv`.
- Test outputs remain in `~/Downloads/ffmpeg-skill-hw-test/`.

## Unfinished Work

- User choice pending: re-render the Reels test with `--fit blur` or a `--crop-x` bias to keep the subjects in frame.
- A stronger `--hw` test was proposed and not yet run: a 4K (ideally iPhone HDR) clip to exercise the HEVC Main 10 path, or a longer file with a pure re-encode (`fit.py --height 1080`, `stabilize.py`) to measure encode-only speedup.
- Carried over from the earlier summary: rerun the third Codex review (cut off by the Codex usage limit); optional upstream issue at `kajisho5/ffmpeg-skill`; optional `--hw` demo.
- Decide whether to commit this summary.
