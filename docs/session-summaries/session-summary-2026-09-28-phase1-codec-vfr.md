---
session_id: c2b35f00-8ded-4df2-9272-b768f6f94814
date: 2026-09-28
time: "2026-09-27 11:12 PM PDT – 2026-09-28 01:10 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: carry-forward Phase 1, part 2 (items 3.1, 2, 7, 4)

## Overview

Picked up the baton `.baton/2026-09-27-carry-forward-phase1-part2.md`. Finished the remaining
Phase 1 carry-forward fixes on `m-series-hw-parakeet`. Re-encoded cuts now keep an HEVC source's
codec (item 3.1). The VFR guard now samples packet timestamps instead of comparing averages
(item 2). `caption.py --mode mux` reports `transcription` (item 7). An encode that
`FFMPEG_SKILL_HW` put on the GPU carries a note (item 4). Four commits plus a design-decisions
entry. Each group was mutation-checked, run through the full suite on an empty `tests/out`, and
Codex-reviewed, including passes over the fixes.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **`source_codec_video_args` routes any HEVC source through `encoder_args("hevc")`, with no separate HDR clause** | A mutant that removed the planned HDR clause survived. For HEVC, `encoder_args("hevc", meta)` builds exactly the Main10 line `video_args` gives HDR, so the clause was dead code. |
| **The chunked `--segments` join restates the chunks' `-tag:v`** | Codex found, and it was reproduced: a copy of Matroska HEVC chunks into MP4 writes `hev1`. The real 40-segment test output was `hev1`. The bug already existed for HDR; item 3.1 would have made it common. |
| **Declined Codex's suggestion to compare against `video_args()` output in tests** | The repo test policy forbids using production code as the oracle. The GPU test instead runs the real `_vt_args` routing with the platform and encoder list mocked. |
| **The classifier reads integer pts/dts ticks, not `pts_time`** | ffprobe's six-decimal rounding would eat a one-tick tolerance. |
| **The tolerance is capped at half the smallest window median** | At a 1/fps time base (AVI), one tick is a whole frame, so the plan's "one tick" rule passed a dropped frame. Caught by a red unit test. |
| **Windows use an absolute `-read_intervals` end and keep only pts ≥ their start; the first window does not seek** | `-read_intervals` resolves a seek and a relative end against the keyframe it lands on. On `tests/out/source.mp4` (keyframes 0 and 8.33 s), `6%+6` read 0–5.93 s. A seek to `0` on an edit-listed MP4 read 13 packets instead of 72, and seeks near it were erratic (`0` and `-0.25` fail, `-1` and `0.5` work), so no seek margin is safe. |
| **Accepted the no-seek cost case** | A file whose video starts long after its first packet is demuxed, not decoded, up to the video start. Codex raised it (P2); a seek would bring the edit-list bug back. Recorded in the docstring and the plan. |
| **`-select_streams V:0`** | `V` is ffprobe's "video but not attached picture", which matches `probe()`'s choice. Not test-pinned: FFmpeg 9's MP4 muxer moves cover art last and Matroska drops the disposition. |
| **The VFR check is skipped (no `vfr_check` key) when nothing would copy** | `--accurate`, `--codec`, audio output, and a dry-run input a plan has not written yet. Measuring would be wasted work, so `vfr` and `codec` no longer both appear in `reencode_reason`. |
| **The env-hw note goes on the report's copy of `hw.notes`** | Computing the report twice cannot duplicate it. Pinned by a mutation test. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Item 3.1 — `79f3d24`** | `scripts/_common/decision.py` `source_codec_video_args` (exported). `scripts/cut.py` `video_encode_args` uses it; `_join_chunk` returns its codec args so the chunked join restates `-tag:v`. Contract `when` texts in `scripts/_contract.py`, `docs/contract.md`, `references/scripts.md`, `CHANGELOG.md`. Tests in `tests/test_cut_copy.py` (`SourceCodecArgsTests` plus integration). |
| **Item 2 — `2da15de`** | `scripts/_common/probe.py`: `complete_pts`, `classify_frame_timing`, `timing_window_starts`, `measure_frame_timing` (exported). `scripts/cut.py`: sampled VFR guard, `--vfr-copy`, `vfr_check`. Also the contract schema, `references/scripts.md` and `gotchas.md`, `README.md`, `CHANGELOG.md`, the plan's "As built" note for item 2, and the MCP snapshot (`vfr_copy` added). `tests/test_editing.py`'s VFR test asserts `reencode_reason` instead of stderr text. New `FrameTimingTests` and `VfrGuardTests`. |
| **Items 7 + 4 — `632820c`** | `scripts/caption.py`: the mux emit carries `transcription`. `scripts/_common/emit.py`: `ENV_HW_NOTE`, added when `hw_source == "env"` and VideoToolbox ran. Tests in `tests/test_accel.py`; contract text and changelog. |
| **Design notes — `57ff185`** | `docs/design-decisions.md`: why re-encoded cuts keep HEVC, and why VFR is sampled. |

## Testing / Research Performed

- **Full suite on an empty `tests/out` after each group.** The runs and their results:
  - item 3.1: 644 OK (3 skipped), and again 644 OK after the review fixes;
  - item 2: the first run was 666 with one failure (`test_editing` pinned the old stderr wording);
    a later run was stopped when the second review needed a code change; the final run was 668 OK
    (3 skipped);
  - items 7 + 4: 670 OK (3 skipped).
- **Contract suite:** 150 OK (1 skipped) on every run.
- **Mutation checks:**
  - item 3.1: 4 mutants. The HDR one survived, which led to removing that clause. The `hvc1` tag
    fix and the swap record were each killed.
  - item 2: 12 plus 3 plus 1 mutants. All killed except two, both explained: the early return on
    an ffprobe failure, whose empty windows classify the same, and `V:0`, which no fixture can
    reach.
  - item 4: 3 of 3 killed. Item 7: the red run before the fix.
- **Codex reviews (`gpt-6-sol`, high, read-only):**
  - item 3.1: FIX (1 Major, 3 Minor), then a second pass: wording only;
  - item 2: FIX (2 Major, 2 Minor), then a second pass: one new Major, a regression in my own
    seek fix, which was reproduced and fixed; then a third pass: one P2 cost note, accepted;
  - items 7 + 4: SHIP, no findings.
- **Empirical ffprobe probes:**
  - `-read_intervals` semantics on offset, long-GOP and edit-listed files;
  - attached-picture stream ordering on MP4, MOV and MKV;
  - VFR fixture shapes: a `setpts` jitter was normalised away by the encoder's time base, so the
    tests use dropped frames and a `setts` last-frame hold instead.

## Summary Statistics

- 5 commits: 4 feature/fix commits and 1 docs commit (`79f3d24`, `2da15de`, `632820c`, `57ff185`,
  plus this summary).
- Full suite grew from 624 to 670 tests (46 new), all passing.
- Codex review passes: 6 (3 on item 2).
- Bugs found beyond the plan: 4.
  - `hev1` on chunked joins;
  - a dropped frame passing at a coarse time base;
  - long-GOP windows re-reading the file's first seconds;
  - the edit-list first-window seek, which my own fix introduced.

## Discoveries / Handoff Notes

- **`-read_intervals` is keyframe-relative.** A seek lands on a keyframe (decode-time based), `+N`
  counts from there, and seeks around the start of an edit-listed MP4 are erratic. Don't sample
  with relative ends, and don't seek to 0.
- **Copy-concat out of Matroska drops `hvc1`.** Pass `-tag:v hvc1` on the final MP4 copy.
- **Encoders normalise timestamps.** A `setpts` jitter at a 30 fps time base is rounded away. Use
  dropped frames (`select` plus `-fps_mode vfr`) for a VFR fixture.
- **The FFmpeg 9 MP4 muxer puts `attached_pic` streams after the video**, so a cover-first MP4
  can't be built with it.
- **zsh doesn't word-split `$T`; use `${=T}`.** This bit again this session. So did the rule
  against editing code under a running suite, which is why one suite run was stopped.
- **Free disk space kept falling** during the session: 8.5 GB at the start, about 4.1 GB with
  `tests/out` present at the end. Check `df -h /Users` before each suite run.
- **`SKILL.md` is still frozen at its byte budget.** It still states the old SDR x264 rule, and
  its VFR advice ("`cut.py` switches to `--accurate`") remains broadly true.

## Current State

- Branch `m-series-hw-parakeet`, 5 commits ahead of `origin/m-series-hw-parakeet`; not pushed (the
  user pushes). The working tree is clean except the untracked `CLAUDE.local.md`, which is never
  committed.
- Phase 1 of `docs/plans/2026-09-27-carry-forward-fixes.md` is complete. The baton for this work
  was retired after this summary.

## Unfinished Work

- **Open question for the user (carried from the plan):** a Parakeet engine that outputs garbage is
  reported as "no speech" (`run_parakeet` → `die_no_speech`). Current lean: log it and fall
  through to the next engine, the same as a crash.
- **Phase 2 needs its own plan.** Candidates:
  - item 6 (timeout scaling);
  - the `stage_hw` roll-up of the item 4 note;
  - `--segments` edit lists (0.05–0.13 s gaps at boundaries on B-frame sources);
  - the `--accurate` x264 `make_zero` 24 ms A/V skew;
  - the two inferred item 3 edge cases in the plan's Phase 2 notes;
  - optionally, a bounded first VFR window for files whose video starts long after the first
    packet.
