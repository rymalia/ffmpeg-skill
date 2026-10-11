---
session_id: 4bd006f0-f2c3-40c9-bc45-9130a33416f3
date: 2026-09-29
time: "9:05 PM PDT – 11:00 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: Phase 2 item 1 (exact copy join) and T1 (drawtext newline)

## Overview

This session finished carry-forward Phase 2. It rebased the branch onto `origin`, and the user
then pushed it. It took up the item-1 baton and committed the step-0 prototype gate. It built
item 1, so that a `--segments` stream-copy join is exact or is not a copy, and passed it
through four Codex review passes. It built T1, a wrapped graphics title that lost its line
break. Everything is committed, and the baton is retired.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Rebase the 4 unpushed commits onto `origin`** | The remote had 3 commits of session summaries from another session. They touched none of the same files, and the local commits had never been pushed. The branch diff against the pre-rebase tip showed only those 3 files. |
| **Step 0's gate uses the plan's definition of exact:** frames bit-exact, steps within the join-check bound, beeps within 5 ms | A stricter "no step off by more than 1 ms" check flagged a gap that sub-frame sources show both today and with P3. There the frames are exact and A/V sync is intact. |
| **[R5] Widen change 3(b)'s bound to one frame plus the longer of ½ a frame and one audio frame** | With no B-frames, each part's AAC ends up to one codec frame after its picture, and the demuxer places the next part after the sound. Measured steps were 32.7 ms at 60 fps (bound 25 ms) and 53.5 ms at 30 fps with 44.1 kHz audio (bound 50 ms). The ½-frame bound would have re-encoded iPhone "Most Compatible" footage that copies exactly today. Codex judged the widening sound. |
| **The audio frame is the most common packet duration, not the longest** | Codex review 1, M1. One long packet must not widen every join's bound. |
| **Only copied parts are copy-joined (video)** | The suite showed that the end snap re-encoded every part of the 40-segment test. The matching re-encoded parts were then copy-joined, which is the per-part-encode join that left a 23 ms hole in item 2. PCM audio-only joins are exempt. |
| **A checked join is written in the temp dir and placed only when it passes** | Codex pass 2. A failed check followed by a failed re-cut could destroy an `--overwrite` target. |
| **`place_output` holds the output lock** | Codex pass 3. Without it, placement could race a concurrent writer. This also covers `render.py`'s final placement. |
| **Kept: a GOP that ends at EOF counts as closed** | `video_packets` is a full-file scan, so an EOF GOP has been read completely. Codex pass 2 agreed. |
| **Declined: an open start keyframe on segment 0 (m5)** | The failure is safe: a correct but unnecessary re-cut. No fixture has mixed GOPs. It is recorded in the plan. |
| **No regression test for the copy_failed guard** | No real-file trigger exists: FFmpeg 9 muxes PCM and FFV1 into MP4, so those copies do not fail. A mocked `main()` would test the mock. |
| **T1: keep `\n`, gate `text_align=C` on FFmpeg ≥ 6.1** | This was the plan's design. Applying it only to the centred templates leaves the lower-third, sticker and `overlay.py` left-aligned. |
| **T1 review by an Opus subagent** | Codex hit its usage limit mid-review (the CLI said it resets on Sep 30 at 2:26 AM). |

## Changes Made

| Change | Detail |
|--------|--------|
| **Rebase** | 4 local commits onto `origin/m-series-hw-parakeet` (`d041667`). The user pushed. |
| **`898300b` test(prototypes)** | `tests/prototypes/join_copy_p3.py`, the step-0 gate (P0 against P3, 16 rows, exits 1 on a closed-GOP failure). The plan gets a Step 0 result note. |
| **`2d4cea4` fix(cut)** | `scripts/cut.py`:<br>• new `video_packets`, `gop_is_open`, `plan_part`, `open_join_key`, `stream_packet_times`, `expected_packets`, `typical_duration`, `check_join`;<br>• `cut_one(copy_t=…)` for edit-listed P3 parts;<br>• the copy-join branch of `main` rewritten: early re-cut for open GOPs, tolerance parts or unreadable packets; the join staged in tmp and checked; `place_output` on success;<br>• new keys `join_check` and `segment_end_snap_seconds`.<br>`scripts/_common/runner.py`: `place_output` takes `_OutputLock`. `scripts/_contract.py` gets the schema. Docs: `docs/contract.md` table row, `docs/design-decisions.md` (the false "no length check" text replaced), `references/scripts.md`, `references/gotchas.md`, `CHANGELOG.md`, and the plan's as-built note (R5). |
| **Tests (item 1)** | `tests/test_cut_copy.py`:<br>• fixtures `h264bf`, `hevc25c`, `beep_bf`, `hlg_open`, `nob60`;<br>• integration tests 1-a to 1-i, the 2-c and 2-d copy variants, 60 fps no-B-frame, Matroska join check, 1-h (`--vfr-copy`);<br>• `CopyJoinPlanTests`: 18 unit tests;<br>• the old `test_keyframe_aligned_bframe_segments_stay_a_lossless_copy` rewritten as 1-a. |
| **`79db5cb` fix(graphics)** | `scripts/_common/drawtext.py`: the sanitiser keeps `\n`, normalises `\r`, and turns tab, VT and FF into a space; new `drawtext_center_align()`, re-exported via `_common/text.py` and `__init__.py`. `scripts/graphics.py` applies it to the title/subtitle, hook and meme drawtexts. `tests/test_picture.py` gets `MultiLineDrawtextTests` (3 tests). Also `ISSUES.md` (T1 marked fixed, cause corrected), `CHANGELOG.md`, and the plan's as-built note for T1. |
| **Baton** | `.baton/2026-09-29-phase2-item1-copy-join.md` deleted, since its work landed. |

## Testing / Research Performed

**Step 0 gate:**
- On FFmpeg 9.0.2, P3 was bit-exact on every closed-GOP row: `h264bf` and `hevc25c` in `.mp4` and `.mov`, EOF last parts, `late_audio`, and `h264bf_late` in `.mp4` and `.mov`.
- Beeps: 0 ms, or 379 ms on `beep_late` (its own offset). P0 drifted by 67 ms, then 133 ms.
- `hevc25` (open GOP) gave 144/150.

**Extra measurements:**
- P3 joins have no audio or video pts gaps on B-frame sources.
- On no-B-frame sources the step before a join is 38.7 or 49.4 ms at 30 fps, and 32.7 or 36.8 ms at 60 fps.

**Red first:**
- Item 1: 15 unit tests errored, and 10 of 11 integration tests failed for the expected reasons. 1-g already passed today; it stays as a guard.
- T1: all 3 tests were red.

**Mutation checks:**
- Item 1: 10 mutants, 9 killed. The survivor is the plan's expected one: with the join check disabled, 1-c still falls back via the open-GOP check.
- The first round had exposed two test gaps: the dts-rule case and the per-end judging case. Both were fixed.
- The `place_output` lock mutant was killed.
- T1: 2 mutants, both killed.

**Suites:**
- 708 tests with 1 failure. The chunk test caught the copy-join of re-encoded parts, which was then fixed.
- Then 711 OK, 713 OK and 716 OK, each with 3 skipped.
- Contract: 150 OK (1 skipped) on each run.
- One suite run was stopped: I had edited `runner.py` while it ran, so its result could not count.

**Reviews:**
- Codex (`gpt-5.6-terra`, xhigh) on item 1:
  - pass 1: FIX, 3 major and 2 minor;
  - pass 2: FIX, 1 major and 5 minor;
  - pass 3: FIX, 1 major;
  - pass 4: SHIP.
- T1: the Codex review ran into its usage limit. An Opus subagent gave SHIP with 4 minors; 2 were applied and 2 declined.

**Visual check:** T1 was reproduced ("WHOSHOWS UP?"). After the fix the frame was inspected by eye, and the line centres measured 538.5 and 539.5 px on a 1080-wide frame.

## Summary Statistics

- 3 commits (`898300b`, `2d4cea4`, `79db5cb`), plus the rebase of 4 earlier commits.
- The suite grew from 683 to 716 tests.
- Bugs fixed:
  - copy-join stray frames, holes and A/V drift on B-frame sources;
  - open-GOP joins reported as copies;
  - Matroska B-frame joins reported as copies;
  - re-encoded parts copy-joined with an AAC hole;
  - the `--overwrite` target at risk from a failed check;
  - a `place_output` lock race;
  - T1's lost line break.
- Review passes: 4 Codex (item 1), 1 Codex that did not finish, and 1 Opus (T1).

## Discoveries / Handoff Notes

- **No-B-frame copy joins are never step-perfect.** The concat demuxer places each part after
  its longer stream, and the AAC tail overruns by up to one codec frame. The frames and sync
  are exact, and `join_check` allows it by design.
- **Matroska `--segments` joins of B-frame video were wrong and reported as clean copies.** They
  keep the old part cut; the join check now catches them and re-cuts.
- **The iPhone split stands.** "High Efficiency" HEVC always re-encodes a `--segments` join
  (open GOP). "Most Compatible" H.264 stays a lossless copy.
- **zsh treats a bare `=====` as `=cmd` expansion.** Quote separators in shell commands.
- **Codex usage limit:** reached at about 22:50 on 2026-09-29. The CLI reported a reset on
  2026-09-30 at 2:26 AM.

## Current State

- Branch `m-series-hw-parakeet` is 3 commits ahead of `origin` and **not pushed**.
- Untracked and not part of this session: `CLAUDE.local.md`,
  `docs/ref-apple-videotoolbox-documentation.md` and
  `docs/ref-ffmpeg-tutorial-advanced-filtering-gpu-acceleration.md`. The two `docs/ref-*` files
  appeared mid-session from outside it.
- `.baton/` is empty.

## Unfinished Work

- **Push:** `git push -u origin m-series-hw-parakeet` (the user pushes).
- **Phase 2 is complete.** Deferred outside it:
  - smart rendering for open-GOP joins;
  - the T2 shrink-to-fit and the em-width wrap estimate (ISSUES.md T1 cause 1);
  - right-aligned sticker lines on the drawtext route;
  - item 6 (timeouts) and the `stage_hw` roll-up.
