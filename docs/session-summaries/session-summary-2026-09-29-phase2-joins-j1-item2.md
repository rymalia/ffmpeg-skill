---
session_id: 69d37c5e-884f-4a5d-b024-376fa83424d1
date: 2026-09-29
time: "2026-09-28 10:38 PM PDT – 2026-09-29 03:08 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: Phase 2 plan, J1 and item 2 (joins that leave no gap)

## Overview

This session did three things. It resolved the branch's divergence from `origin` by rebasing. It
measured and planned carry-forward Phase 2, and had Codex validate the plan in four passes. It
then built and committed two items: J1 (`join.py` plain-cut hole) and item 2 (a `--segments`
segment past the video's end, plus a hole at every `--accurate` join). Item 1 (the exact
stream-copy join) and T1 (the drawtext newline) are handed off in a baton.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Rebase the 7 unpushed local commits onto `origin`, not merge** | The remote side was 2 docs-only commits (`ISSUES.md` and a session summary) that touched no common files, and the trial merge was clean. The local commits were unpushed, so rebasing rewrote nothing shared and the user's push was a fast-forward. |
| **Scope: one theme, "a join must not leave a hole"** (J1 + items 1 and 2), then T1 | Chosen by the user. `ISSUES.md` J1 turned out to be the same mechanism as items 1 and 2. |
| **Codex model: `gpt-5.6-terra` xhigh** | Chosen by the user; saved to memory (`codex-model-choice`). |
| **Item 1 design P3: edit-listed parts ending at the end keyframe's dts, with open-GOP detection falling back to a re-encode** | Of 5 prototyped designs, only P3 was bit-exact and A/V-synced on closed-GOP sources. On open-GOP sources no concat-demuxer copy can be exact. |
| **Ship detect-and-re-encode for open-GOP footage; defer smart rendering** | The user chose option 1 after the real-footage results. Their High Efficiency iPhone footage is open-GOP, so their joins will be correct but re-encoded. |
| **Items 2 and J1 use `clip_length`'s rule:** hold the last frame for sound more than a frame past the picture; trim a shorter tail | The same rule as `join.py`'s existing crossfade path, so the two paths behave alike. |
| **`--accurate` multi-segment joins go straight to `join_from_source`** (unplanned) | Per-part encodes plus a copy join left a 23 ms (one AAC frame) hole at every `--accurate` join, found while testing item 2. The re-cut path was already measured exact, and it encodes once. |
| **Item 2 was reviewed by an Opus subagent** | Codex hit its usage limit mid-session. The user's global rules allow Opus. |
| **Item 1 and T1 are handed to a fresh session** | The session ran long, and the user prefers to wrap up early rather than compact. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Rebase** | 7 local commits replayed onto `origin/m-series-hw-parakeet` (`a8cca5a`). The user pushed (`a8cca5a..ea6a309`). |
| **`f03e627` docs(plan)** | `docs/plans/2026-09-28-carry-forward-phase2.md`, evidence M1–M4 and revisions R1–R4b. Items 1 and 2 got as-built notes in later commits. |
| **`17a5532` fix(join)** | `scripts/join.py`: both paths pad each clip to `clip_length`, and `-fps_mode passthrough` is now unconditional. Two tests in `tests/test_editing.py`. Also the `CHANGELOG.md` entry, a `docs/design-decisions.md` entry, the `references/scripts.md` join text, and `ISSUES.md` J1 (marked fixed, component corrected). |
| **`a3b6db6` fix(cut)** | `scripts/cut.py`: new `file_origin()` and `video_end()`; the pre-check trims or holds a segment past the video's end; `_join_chunk` holds by segment position (`hold`, `first`); `--accurate` joins route to `join_from_source`; the VFR guard is skipped when a hold rules out a copy. Also the `scripts/_contract.py` cut `notes` text, 7 new tests plus 3 fixtures in `tests/test_cut_copy.py`, and the changelog, design-decisions and references text. |
| **Baton** | `.baton/2026-09-29-phase2-item1-copy-join.md` (git-ignored). The old `2026-09-28-carry-forward-phase2-plan.md` baton was retired. |
| **Memory** | `codex-model-choice.md`, `iphone-footage-open-gop.md`, and the `MEMORY.md` index. |

## Testing / Research Performed

**Prototypes** (FFmpeg 9.0.2, lavfi fixtures, every frame checked bit-exact with `framemd5`):
- P0–P5 copy-join designs on H.264 B-frame, closed-GOP HEVC and open-GOP HEVC fixtures.
- A/V sync measured with a beep-per-second fixture.
- Off-keyframe start and end behaviour.

**The user's iPhone footage:**
- 8 clips were inspected (codec, B-frames, GOP structure over the whole file).
- 3 were join-tested frame by frame.
- IMG_0759: 287/224 frames today, 219/224 with P3.
- IMG_0776: 170/112 today, 107/112 with P3.
- IMG_0777 (H.264): 116/116 both ways.

**T1:**
- Reproduced "WHOSHOWS UP?".
- A direct drawtext test showed FFmpeg renders `\n` from a `textfile=`.
- The root cause was traced to the sanitiser.

**Red-first tests:**
- J1: 2 tests.
- Item 2: 7 tests (5 at first; 1 added for the `--accurate` hole and 1 after the review; the
  copy-held test gained a `vfr_check` assertion).

**Mutation checks:**
- J1: 2 mutants, each killed by at least one test.
- Item 2: 7 mutants, all killed. One ("last segment held too") survived at first and was killed
  after a frame-count assertion was added.

**Suites:**
- After J1, the first run was 676 with 2 errors: the new `_psnr` helper shadowed
  `MediaFixtures._psnr`. After the fix, 676 OK (3 skipped).
- After item 2: 682 OK, then 683 OK (3 skipped) after the review fixes.
- Contract: 150 OK (1 skipped) on each run.

**Reviews:**
- Codex plan passes R1 to R4: REVISE ×4. The findings shrank from 2 critical / 7 major to one
  spec gap, which was closed.
- Codex J1 review: minors, then one fix (`fps_mode`), then SHIP.
- Opus item-2 review: FIX (1 major, 3 minor), then SHIP on the fixes.

## Summary Statistics

- 3 commits (`f03e627`, `17a5532`, `a3b6db6`), plus the rebase of 7 earlier commits.
- Tests: 674 → 683: 9 new test methods (2 for J1, 7 for item 2).
- Bugs fixed: 3. The J1 plain-cut hole; the past-the-end hole on both `cut.py` join paths; the
  23 ms hole at every `--accurate` join.
- Review passes: 4 Codex on the plan, 3 Codex on J1, 2 Opus on item 2.

## Discoveries / Handoff Notes

- **Every hole found this session has one cause.** Both concat routes place the next segment
  after the previous segment's *longer* stream: the demuxer by container duration, the filter by
  the longest stream.
- **The user's iPhone "High Efficiency" HEVC is open-GOP at every keyframe**, with 3 leading
  pictures. No concat-demuxer copy join is exact on it. "Most Compatible" H.264 has no B-frames
  and is exact.
- **The concat demuxer ignores a part's edit-list start**, so pre-roll is shown. It honours the
  part's edit-listed duration, and that is why P3 works.
- **Video `start_time` 0.021328 against audio 0 is AAC priming** (1024/48000), not an A/V offset.
- **`ISSUES.md` T1's stated cause was wrong.** drawtext renders newlines; `drawtext_text_opts`
  strips them. drawtext's `text_align` exists from FFmpeg **6.1**; the repo supports 5.1.
- **The auto-mode safety classifier returned "no verdict" errors for a while**, blocking writes.
  It cleared on its own.
- **Codex hit its usage limit around 01:00.** The CLI's message said it resets at 2:22 AM.

## Current State

- Branch `m-series-hw-parakeet` is 3 commits ahead of `origin`, **not pushed**.
- The working tree is clean apart from the untracked `CLAUDE.local.md` and this summary.
- The item-1 baton is at `.baton/2026-09-29-phase2-item1-copy-join.md`.

## Unfinished Work

- **Push:** `git push -u origin m-series-hw-parakeet` (the user pushes).
- **Item 1,** from the baton. Step 0 comes first: commit `tests/prototypes/join_copy_p3.py` and
  confirm the closed-GOP rows are exact. Then open-GOP detection, the demux join check,
  `join_check` and `segment_end_snap_seconds`, tests 1-a to 1-i, and the deferred copy
  assertions for 2-c and 2-d.
- **T1:** keep `\n` in the sanitiser, and gate `text_align=C` on FFmpeg ≥ 6.1.
- **Smart rendering** for open-GOP joins: deferred by the user, and outside Phase 2.
