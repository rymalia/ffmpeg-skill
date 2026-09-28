---
session_id: efee1612-66d4-4d79-a90f-ed8f61f8ddc2
date: 2026-09-27
time: "8:09 PM PDT – 10:39 PM PDT"
resumed: "9:24 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: Phase 1 carry-forward fixes — refactor A, the safe join, edit-list copies

## Overview

This session picked up the baton `.baton/2026-09-27-carry-forward-phase1.md` and did five things:

- revised the plan twice (R5, R6), grounding each revision in local FFmpeg measurements, and
  added R7 notes while implementing;
- implemented refactor A;
- implemented item 3's safe `--segments` join;
- implemented item 1 (edit-list copies) together with a newly found `--accurate` seek bug (R7);
- ran a Codex or Claude review over each piece, then a second review over the fixes.

Items 3.1, 2, 7 and 4 and the MCP snapshot are handed off in a new baton.

**On the times:**
- The start (8:09 PM) comes from this session's first SessionStart hook.
- The session was resumed at 9:24 PM, after the disk filled; the metadata collector reports that
  resume time as its `session_start`.
- Both values are hook output. The end time comes from the metadata collector.

## How We Got Here

1. **The baton checked out.** Its `.gitignore` step was already committed (`52ec81a`).
2. **R5 was measured before it was written.** Three experiments shaped it:
   - an edit-list copy presents the first source frame with pts ≥ T;
   - a concat filter over `make_zero` parts leaves a gap, even with a `setpts` rebase;
   - re-cutting every segment from the source is exact.
3. **Codex reviewed R5 (REVISE, 2 critical).** Critical 2, the lost A/V offset, was
   reproduced, and R6 fixed it. Critical 1 was reproduced only outside `cut.py`; through `cut.py`
   it is the `--tolerance` trade the user asked for, so it was downgraded.
4. **Refactor A was built and reviewed** (Codex: FIX). The user chose "apply the 4 valid".
5. **Codex hit its usage limit.** The user said to use Claude subagents for about an hour.
6. **Item 3 was implemented.** Along the way two more problems turned up and were fixed:
   - B-frame loss from the decode-time seek, and from input `-t`;
   - a 23 ms A/V shift from MP4 chunks.
7. **The disk filled.** A full suite in a second worktree ran out of space (`OSError(28)`), which
   also left a test mutation applied to `cut.py`. The user freed space and the session resumed. The
   leftover mutation was found by diffing against the backup and restored.
8. **Item 3 was reviewed twice.** An Opus subagent found a critical regression: the join-length
   check rejected lossless joins. It was reproduced and the check removed. Codex, now back, found
   the GPU-chunk issue, which was fixed.
9. **Item 1 + R7 were implemented.** Codex reviewed them twice (FIX both times), and every finding
   was reproduced or verified before it was fixed.
10. **Wrap-up:** the baton and this summary.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **The join fallback re-cuts every segment from the source, instead of joining the parts** (R5) | Measured: the concat filter starts each segment at the end of its longest stream, and `make_zero` parts carry keyframe pre-roll and an audio tail. That left a 0.1 s gap even after a `setpts` rebase. Re-cutting from the source gave 120/120 frames with no gap. |
| **Shift both streams by one constant, and pad the audio with `aresample=async=1:first_pts=0`** (R6) | A per-stream `PTS-STARTPTS` moved a 0.379 s-late audio track 0.379 s early (measured with `silencedetect`). |
| **The fallback seeks 1 s early and reads 1 s past the end** | The MP4 demuxer seeks by *decode* time: `-ss 9.9` landed on the keyframe at 10.0 (dts 9.833) and lost 3 frames. An input `-t` also stopped reading before B-frames stored late. |
| **At most 32 segments per ffmpeg call; chunks are Matroska with PCM audio** | Each segment is its own input (fd, demuxer, decoder). MP4/AAC chunks copy-joined put the video 23 ms behind the audio; PCM chunks don't, and the audio is encoded once. |
| **A missing extradata hash on both sides matches only for pcm/mp3/mp2 or MPEG-TS output** (R6) | PCM has no `extradata_hash`, so R4's "missing means incompatible" would have sent every WAV join to a re-encode. Codex found that AAC in TS also lacks one. |
| **The join-length check was removed** | The Opus reviewer reproduced it rejecting keyframe-aligned lossless joins. Across five source shapes, neither format nor stream duration sums predict a copy join (off by 0.03–1.3 s). |
| **`--hw` chunk mismatch: re-encode every chunk on the CPU rather than refuse** | Codex (and the Opus reviewer, as inferred): a VideoToolbox refusal on one chunk makes the CPU retry's signature differ. `_maybe_hw` reads `STATE.hw` when the command is built, so turning it off and re-encoding works. |
| **Item 1 reports from the source's packets, not the output's durations** | The double probe (normal vs `-ignore_editlist`) differs even on a keyframe-aligned start (B-frame composition offset). The pre-roll formula gave 0.233 s for a real 0.3 s. `seek_keyframe` (largest dts ≤ start) plus the first presented pts is exact. |
| **An end-only tolerance miss on an edit-listed copy offers no `--start` alternative** | Codex: the start is exact, so no other start fixes an end overshoot. Two pinned tests moved to `.mkv`, where the keyframe snap (and the alternative) still exist. |
| **The Codex refactor A review's `edit_list` and `docs/contract.md` findings were dropped** (user's choice) | `edit_list` arrived with item 1. `docs/contract.md` lists no per-tool keys; `_contract.py`'s schema is the reference. |
| **The session stops after item 1 + R7, with a baton** | Context budget. Items 3.1 and 2 are substantial (a probe/classifier feature). |

## Changes Made

| Change | Detail |
|--------|--------|
| **`5a87c34` plan R5** | Applies the eight R4 findings, with the measurements and a resolution table. |
| **`a581182` plan R6** | Folds in the Codex review of R5 (shared-origin shift, segment floor, extradata rule, chunking, `.6f`). |
| **`965a952` refactor A** | `cut_one` returns an outcome dict. New keys `reencode_reason` and `segment_precision`; the top-level precision is the least exact segment's. Batch: `reencode_reasons` counts, and new log wording. A join-only fallback now reports `hybrid`. |
| **`b61e69b` item 3 safe join** | `join_signature`, `signatures_match`, `join_from_source`, `_join_chunk`, `JOIN_CHUNK`, `SEEK_MARGIN`, the segment floor, and the GPU chunk retry. New `tests/test_cut_copy.py`, registered in `tests/test_all.py`. Docs: CHANGELOG, `references/scripts.md`, `docs/design-decisions.md`, plus R7 plan notes. |
| **`a63739e` item 1 + R7** | Single MP4/MOV copies keep their edit list. `seek_keyframe` / `copy_presentation` / `av_skew`. New keys `edit_list`, `stored_preroll_seconds`, `av_start_skew_seconds`, `notes`. The probe gains per-stream `start_time`. `--accurate` uses a margin seek. Two tests moved to `.mkv` (`test_editing.py`, `test_contract.py`). Docs: gotchas, scripts, design decisions, CHANGELOG, plan. The message was amended to state the contract count exactly. |
| **Baton** | New `.baton/2026-09-27-carry-forward-phase1-part2.md` (git-ignored). The old baton was moved out of `.baton/` to the session scratchpad. |

## Testing / Research Performed

**Full suites**

| Run | Result |
|---|---|
| After refactor A, in a worktree | Died from a full disk (`OSError(28)`, exit 120) after 464 passes. Invalid. |
| Refactor A + item 3 (empty `tests/out`) | `test_all` **624 OK (3 skipped)**, 761.9 s; contract **150 OK (1 skipped)**. |
| Re-check on the final item 3 code (`test_cut_copy` + `test_editing`) | 1 failure: a stale-output refusal, confirmed by its stderr (`silence_wav_in_tight.wav`). |
| Two item 1 runs | Invalid: `cut.py` was edited while they ran, and both were killed. |
| Item 1, clean | `test_all` 637 run, **636 OK** (1 failure); contract **149/150**. Both failures pinned the old `.mp4` snap; after moving them to `.mkv`, both pass when rerun on their own. |

**Mutation checks** (each broke the guarded behaviour and confirmed a test failed; `cut.py` was
restored every time):

| Group | Mutations |
|---|---|
| Refactor A | 6: no codec reason, no tolerance reason, no `requested`, `segment_precision` on a single segment, least → most exact, codec only without `--accurate` |
| Item 3 | 11: no signature check, per-stream `STARTPTS`, no seek margin, no chunking, absent extradata always equal, no join-length check (a check later removed), no segment floor, rotation not in the signature, MP4 chunks, always-fallback, no GPU→CPU chunk retry |
| Item 1 + R7 | 11: `make_zero` on every copy, keyframe by pts, no accurate margin, pre-roll from dts, skew limit, ignored origin, pre-roll from t, no end-only branch, dry-run losing `edit_list`, notes dropped, unknown start treated as exact |

**FFmpeg experiments** (FFmpeg 9.0.2, scratch fixtures):
- **Edit-list first frame:** T = 4.3 gives source frame 129 and T = 4.31 gives frame 130, both
  at 99 dB.
- **End overshoot:** +4–5 frames at `-t 3` with `bframes=4`. The tail frames are not
  contiguous (217, 218, 221, 223).
- **Join gaps:**
  - a concat filter over the parts, with and without a rebase: a 0.1 s gap at the join;
  - the source re-cut: 120 frames, V = A = 4.000 s, boundary frames at ~55 dB against 27–31 dB for
    their neighbours.
- **Delayed audio:** `STARTPTS` put the silence at 1.64–2.0 s, where the shared origin put it at
  0–0.379 s.
- **The decode-time seek:** the keyframe pts/dts pairs are 10.0/9.833 and 4.0/3.9. `-ss 9.9`
  begins at frame 300, for both copy and decode.
- **Copy-join durations:** neither format nor stream duration sums predict the join across five
  shapes (h25 ×2, h30 ×11, x264, 29.97).
- **FFmpeg 9 colour conversion:** an untagged vs BT.709-tagged pair reads 22.7–24.5 dB via
  `format=gray`, and 53.6 dB with a forced matrix.
- **The `--accurate` x264 start:** video at 0.067 s and audio at 0.043 s, identical in the old
  and new commands (it predates this session).
- **WAV extradata:** a `pcm_s16le` stream has no `extradata_hash`.

**Reviews:**

| Pass | Reviewer | Verdict |
|---|---|---|
| Plan R5 | Codex gpt-6-sol, xhigh | REVISE: 2 critical / 4 major / 1 minor |
| Refactor A diff | Codex gpt-6-sol, xhigh | FIX: 2 major / 4 minor |
| Item 3 diff | Opus subagent | FIX: 1 critical, 1 major, 5 minor |
| Item 3 fixes | Codex gpt-6-sol, high | FIX: 1 major (the GPU chunk) |
| Item 1 diff | Codex gpt-6-sol, high | FIX: 2 major / 2 minor |
| Item 1 fixes | Codex gpt-6-sol, high | FIX: 2 P2 / 1 P3 |

All the review findings acted on were reproduced or verified first, and all were fixed. The
exceptions were the downgraded plan C1 and the dropped refactor A minors (user's choice).

## Summary Statistics

- **Commits:** 5 (`5a87c34`, `a581182`, `965a952`, `b61e69b`, `a63739e`), all local; the user
  pushes.
- **Production files changed:** `scripts/cut.py`, `scripts/batch.py`, `scripts/_contract.py`,
  `scripts/_common/probe.py`.
- **New test module:** `tests/test_cut_copy.py`, 24 tests. Plus 1 new test in `test_editing.py`,
  and edits to `test_editing.py`, `test_orchestration.py` and `test_contract.py`.
- **Suite size:** 612 → 637 tests.
- **Mutation checks:** 28. **Review passes:** 6 (5 Codex, 1 Opus).
- **Live bugs fixed:**
  - the corrupt-success concat-demuxer join;
  - the join-only fallback reported as `copy`;
  - lost frames in `--accurate` before a keyframe;
  - `make_zero` pre-roll on MP4 copies.

## Discoveries / Handoff Notes

- **The MP4 demuxer seeks by decode time.** With B-frames, a start a few frames before a keyframe
  lands on that keyframe. This hits stream copies too, where it's reported as `keyframe_snapped`,
  with no fix.
- **Lossless `--segments` copy joins have a timing gap at each boundary** (0.05–0.13 s on B-frame
  sources). This predates the session, and it's in the plan's Phase 2 "item 1 on `--segments`".
- **An `--accurate` x264 re-encode with `make_zero` starts its video 24 ms after its audio.** This
  predates the session and is a Phase 2 candidate.
- **The disk:** this Mac has ~9 GB free, and a full suite writes ~1.9 GB. Don't run a suite in a
  second worktree, and don't edit code while a suite runs (that happened twice).
- **Test-helper traps:**
  - FFmpeg 9 converts between differently tagged inputs, so use `extractplanes=y`, not
    `format=gray`;
  - rawvideo decoding duplicates a late first frame, so use `-fps_mode passthrough`;
  - zsh doesn't word-split `$VAR`, so use `${=VAR}`.
- **A stale `tests/out` causes false failures:** the 2.0 overwrite guard refuses tests that
  write a default output. That's what the MCP stdio and render-cache failures were at the start of
  the session.

## Current State

- **Branch `m-series-hw-parakeet`:** the 5 commits above are local; the last push was before
  `5a87c34`.
- **Untracked:** only `CLAUDE.local.md`, which is deliberate.
- **Baton:** `.baton/2026-09-27-carry-forward-phase1-part2.md`.
- **The installed skill** (`~/.agents/skills/ffmpeg-skill`) predates these commits and the
  parser fix. `node bin/install.js --codex` updates it.
- **`tests/out`** holds output from the last suite run.

## Unfinished Work

1. **Push:** `git push -u origin m-series-hw-parakeet` (the user pushes).
2. **Phase 1, from the baton:**
   - item 3.1 (source-codec HEVC re-encode);
   - item 2 (the sampled VFR guard and `--vfr-copy`);
   - item 7 (caption mux `transcription`);
   - item 4 (the env GPU note);
   - the MCP snapshot.

   Each gets a full suite, a Codex review plus a pass over the fixes, and a commit.
3. **Decide:** should an engine that outputs garbage be reported as "no speech"? Lean: fall
   through to the next engine.
4. **Phase 2 plan:**
   - timeout scaling;
   - the `stage_hw` roll-up;
   - `--segments` edit lists and their boundary gaps;
   - the `--accurate` `make_zero` skew;
   - two inferred item 3 edge cases.
5. **Reinstall the skill** after Phase 1 lands.
