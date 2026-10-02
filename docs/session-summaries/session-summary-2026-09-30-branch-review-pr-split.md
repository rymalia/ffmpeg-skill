---
session_id: 6355d404-2923-48b3-b29b-16e6d68dfd04
date: 2026-09-30
time: "12:51 PM PDT – 4:30 PM PDT"
resumed: "2026-10-02 02:31 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: reviewing the whole branch, fixing what it found, and splitting it into upstream PRs

## Overview

This session reviewed all 40 commits of `m-series-hw-parakeet` against `main` in one pass, with three reviewers: Codex, Sonnet 5.5 and Fable 5.1. It fixed every finding that held up and committed the fixes as 3 commits. It then split the branch into six PR branches for upstream (`kajisho5/ffmpeg-skill`); each is cut from `upstream/main` and passes its tests. Nothing was pushed.

**Timestamps:**
- The start time comes from the original SessionStart hook (`SESSION_START_TIME=2026-09-30 12:51 PM PDT`).
- The user set the finish time to "Wednesday 4:30 PM", which is 2026-09-30. The metadata script's `now` was 2026-10-02 02:38 AM, but that was when this summary was written.
- The session was resumed on 2026-10-02 at 02:31 AM only to write this summary, so the file is dated by the session's end, not the metadata date.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Delete the finished baton `.baton/2026-09-30-vt-quality-refit.md`** | Its work had landed in `dbeb01f` and `ea481f6`. The only item left in it, hardware decode, is already recorded as deferred in the earlier session summaries. The file was untracked, so there was nothing to commit. |
| **Review the whole branch, not each feature again** | Each feature had been reviewed when it landed. A pass over all of `main..HEAD` is the only one that sees how the features interact through the shared helpers (`decision.py`, `runner.py`, `probe.py`, `asr.py`). |
| **Three independent reviewers on one shared brief** | The user asked for Codex (`gpt-5.6-terra` xhigh) plus a Sonnet subagent, and later a Fable agent for a deep inspection and the PR plan. The shared brief made their findings comparable. Sonnet's verdict was SHIP, while Codex and Fable each found Majors that Sonnet missed. |
| **Fix all findings on the branch before splitting** | Every PR then carries the fixes. Each code fix started with a test that failed. |
| **Go back to `base` for the whisper model default (user's choice)** | The install hint tells whisper.cpp users to download `ggml-base.bin`, so the `large-v3-turbo` default handed whisper-cli a bare model name. faster-whisper users would also have downloaded about 1.5 GB on their first `--transcribe`. The Parakeet engines ignore a model name that isn't a Parakeet model. |
| **The last-GOP join still re-encodes; only its reason changes** | `main`'s "copy" of that cut was corrupt (82 frames where 78 were asked for), so the branch's fallback was correct. The bug was blaming `tolerance`, which made no sense under `--tolerance -1`. |
| **Leave the GPU off only while the chunks re-encode, instead of reporting off `hw_source`** | `hw_source` is also `"flag"` for `--no-hw`, so keying the report off it would add an `hw` block to `--no-hw` runs. The concat that follows the chunks is `-c:v copy`, so switching the GPU back on can't reach an encode. |
| **Drop the test for Sonnet's "cosmetic" finding (#9)** | `_fail` prints only `cmd[0]`, so the wrong command never reaches the user. The test would only have checked an argument nobody sees, which makes it tautological. |
| **Upstream gets six PRs: A, B, E independent; C1 and C2 independent; D stacked on C1** | Fable's trial cherry-picks and its dependency analysis showed this. D needs only C1, because `join_from_source` reads `STATE.hw` and `Context` uses `__slots__`. The user agreed to the whole plan, including splitting `3ff6462` into its VideoToolbox and Parakeet halves. |
| **The Parakeet tests move to a new `tests/test_asr.py`** | If both halves created `test_accel.py`, merging the second would hit an add/add conflict. |
| **Working notes stay out of every PR** | `ISSUES.md`, `docs/plans/`, `docs/session-summaries/`, `docs/setup/`, `tests/prototypes/` and the `.baton` line in `.gitignore` are the user's working record, not something the maintainer needs to review. Commit messages that referred to them were reworded. |
| **C2's `SKILL.md` table row is shorter than the branch's** | C2 doesn't get C1's shortened "Shared flags" line, and without it the branch's wording put `SKILL.md` 6 bytes over the 30 KB budget. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`83de4e0` fix(cut)** | `plan_part`: a part whose start is in the last GOP (no keyframe after it) now keeps its requested end, and `check_join` judges it. `join_from_source` switches `STATE.hw` off only while it re-encodes the chunks. The CHANGELOG `vfr_check` keys now read `windows`/`deltas`. Tests: `test_a_segment_in_the_last_gop_is_not_a_tolerance_reencode`, plus the extended `test_a_gpu_chunk_refusal_reencodes_every_chunk_on_the_cpu`. |
| **`bf4b93c` fix(hw)** | `run()` builds the CPU fallback from the last command tried (the variable `tried`), so it keeps an odd-size retry's even scale. `SKILL.md` now says "CPU re-encodes: x264 `medium`". Test: `test_the_cpu_fallback_keeps_the_even_dimension_scale_of_a_retry`. |
| **`1744df8` fix(asr)** | `caption.py --model` defaults to `base` again. The `--help` text of `caption.py` and `silence.py`, README ("five installs"), `references/scripts.md` and `docs/contract.md` now name the Parakeet engines. Test: `WhisperDefaultModelTests`, which runs end to end against a stub whisper-cli. |
| **`03b23f8` docs(plan)** | `docs/plans/2026-09-30-upstream-pr-series.md`: the six PR descriptions, the pacing, what each reviewer should focus on, and the test results. |
| **Six local PR branches** (no upstream tracking) | `pr/graphics-wrapped-title` (1 commit), `pr/join-no-hole` (1), `pr/loop-boomerang` (1), `pr/hw-videotoolbox` (6), `pr/asr-parakeet` (5), `pr/cut-exact-joins` (9 commits on top of C1). |
| **Memory** | New: `suite-entry-point.md`. Fixed: the stale index line for `iphone-ssim-pair-by-index` (`setpts=N/FRAME_RATE/TB` → `settb=1/1000,setpts=N`). |
| **Baton deleted** | `.baton/2026-09-30-vt-quality-refit.md` (untracked). |

## Testing / Research Performed

**Reviews:**
- **Codex** `gpt-5.6-terra` xhigh. The first run hit its usage limit after 115k tokens and produced no findings. The rerun returned FIX, with 2 Major and 6 Minor findings.
- **Sonnet 5.5:** SHIP, with 2 Minor findings. Its own test run was killed by its 1500 s timeout, so it doesn't count.
- **Fable 5.1:** FIX, with 2 Major and 3 Minor findings, plus the PR plan. The plan came from trial cherry-picks in detached worktrees, each with its group's tests. It also showed that `main` equals `upstream/main` (`df5d273`).
- **Codex** `gpt-6-luna` xhigh, the model the user named for the rest of the session, on the fixes: no Critical or Major findings, 2 doc Minors, both fixed.

**Verified by hand before fixing:**
- The odd-dimension fallback, with a stubbed `_execute`: the third call (the CPU fallback) had no scale.
- The `hw` block loss, by reading `cut.py:651` and `emit.py:88`.
- Fable's last-GOP finding, on a 10 s lavfi clip (GOP 1 s, 3 B-frames), branch against `main`:
  - the branch gave `hybrid ['tolerance','concat_fallback']`, and `main` gave `copy`;
  - `main`'s output had 82 frames where 78 were asked for, including source frames 60, 62, 288 and 290.
- The whisper default: whisper-cli was handed the bare `large-v3-turbo`.
- The doc Minors, by grep. One Codex Minor, "CHANGELOG leaves out `vfr_inconclusive`", was mostly wrong and was dropped.

**Red, then green:** each of the four new or extended tests failed before its fix and passed after it. The last-GOP test was also checked with the fix stashed: it failed on both subtests.

**Suites** (each with a fresh `OUT`):
- **Before the fixes:** the first run, through `unittest discover`, ran 1602 tests with 8 failures and 1 error. All of them were duplicate runs of tests hitting the refuse-to-overwrite guard, not real failures. Run the documented way: suite **726 OK** (3 skipped), contract **150 OK** (1 skipped).
- **After the fixes:**
  - suite **729**, with 1 failure, and contract 1 failure. Both were the `SKILL.md` 30 KB budget, which my edit had pushed to 30,091 bytes;
  - after shortening the line to 29,999 bytes: contract **150 OK**, and the `test_orchestration` budget test OK.

**PR branch tests**, in their worktrees:

| PR | Tests | Result |
|---|---|---|
| A | `test_picture` | OK (3 skipped) |
| B | `test_editing` | OK |
| E | `test_editing`, contract | OK; contract OK (1 skipped) |
| C1 | `test_all`, contract | 602 OK (3 skipped); 150 OK. `test_accel` 25 OK on the final tip, which the full run started before |
| C2 | `test_all`, contract, `test_asr` | 598 OK (3 skipped); 150 OK; 11 OK |
| D | `test_cut_copy`, `test_editing`, `test_orchestration`, contract | 93, 132 and 80 OK; 150 OK |

**Union check:** all six PR branches were merged onto `upstream/main` in a throwaway worktree, with the one `_contract.py` conflict resolved as both functions.
- `scripts/` came out byte-identical to `m-series-hw-parakeet`.
- The `test_accel` + `test_asr` test set equals the branch's 45 tests.

## Summary Statistics

- **Commits on `m-series-hw-parakeet`:** 4 (3 fixes, 1 plan doc).
- **PR branches built:** 6, with 1/1/1/6/5/9 commits.
- **Findings:** 4 Major-level issues were confirmed and fixed:
  - last-GOP join (Fable);
  - odd-size fallback (Codex);
  - whisper default (Sonnet and Fable);
  - lost `hw` block (all three reviewers).

  7 doc Minors were also fixed. 1 finding was dropped as wrong, and 1 because it never reaches the user.
- **Reviewers:** 4 review runs that produced findings, plus 1 that hit the usage limit.
- **New or extended tests:** 4 (3 new, 1 extended).

## Discoveries / Handoff Notes

- **Run the suite as `tests/test_all.py`, never `unittest discover`.** `test_all` imports every module, so `discover` runs each module twice and the duplicates false-fail on the overwrite guard. This is saved to memory.
- **`SKILL.md` is at 29,999 of 30,000 bytes** on the branch. Any wording change there needs an equal cut somewhere else; the detail belongs in `references/gotchas.md`.
- **zsh aborts the whole command** on an unmatched glob (`rm -rf dir/o-*`). Two background runs died this way without any test running. Use `bash -c` or `rm -f ./*.mp4` with a fallback.
- **A copy that ends mid-GOP on B-frame video can never be exact.** An input `-t` stops in decode order, so `main`'s "copies" of such joins were silently wrong.
- **`_fail` prints only `cmd[0]`**, so which command was passed to it never reaches the user.
- **The C2 contract run once failed with 7 `input not found` errors**, where `c_source.mp4` disappeared mid-run in that run's `OUT`. A rerun with a fresh `OUT` passed all 150 tests. The cause was not found.
- **`git filter-branch --msg-filter` over a range** rewords messages without an interactive rebase, which this environment can't run. The tree hash was checked unchanged afterwards.
- **Merge conflicts the maintainer will see.** Whichever of C1/C2 merges second gets conflicts in:
  - `_contract.py`: both add a function at the same spot; keep both, `_parakeet_available` then `_hw_default`;
  - `test_all.py`, `docs/contract.md`, `docs/design-decisions.md` and `CHANGELOG.md`.

  Regenerate `tests/fixtures/mcp_tools.json` with `UPDATE_MCP_SNAPSHOT=1 python3 tests/test_contract.py` rather than hand-merging it.

## Current State

- **Branch `m-series-hw-parakeet`** is at `03b23f8`, 4 commits ahead of `origin/m-series-hw-parakeet` (`c32a7b6`). Not pushed.
- **Six `pr/*` branches** exist locally with no upstream tracking. Their scratch worktrees were removed, so all six can be checked out from the main repo.
- **Untracked:** `CLAUDE.local.md` only (pre-existing).
- **No baton** is on disk.

## Unfinished Work

- **Push and open the PRs.** The user pushes with `git push -u origin pr/<name>`.
  - Open A, B and E first.
  - Then C1 and C2 together.
  - Then D, as a draft based on C1's branch, marked ready once C1 merges and D is rebased onto `upstream/main`.
  - The descriptions are in `docs/plans/2026-09-30-upstream-pr-series.md`.
- **After each upstream merge,** rebase the remaining PRs: keep each PR's own CHANGELOG bullets, regenerate the MCP snapshot, and rerun that PR's test modules.
- **Optional:** push `m-series-hw-parakeet` itself, with `git push -u origin m-series-hw-parakeet`.
- **Optional, carried over:**
  - re-run `tests/bench_vt.py` on the M4 Max to confirm the VideoToolbox curves there;
  - time hardware decode more broadly before deciding on `--hw` decode.
