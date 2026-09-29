---
session_id: c2b35f00-8ded-4df2-9272-b768f6f94814
date: 2026-09-28
time: "2026-09-27 11:12 PM PDT – 2026-09-28 10:32 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session summary: Parakeet "no speech" fall-through, and the Phase 2 handoff

This session was already summarised once, at the end of Phase 1:
`session-summary-2026-09-28-phase1-codec-vfr.md` (`cf28eb5`). This summary covers only what came
after: the user approved the carried open question and asked what's next, and the session then
handed Phase 2 off. The time range is the whole session, from the hook's start time to the
metadata script's end time.

## Overview

Resolved the plan's open question, as the user approved. A Parakeet engine that exits 0 but writes
unreadable output no longer reports "found no speech"; under `auto` it falls through to the next
engine like a crash (`9a90c31`). Then recommended a Phase 2 order and dropped a baton for a fresh
session to plan and build it.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **"No speech" means only the engine's own empty answer** (`{"words": []}` / `{"sentences": []}`) | Measured on the real engines installed here, on 3 s of silence: `parakeet-cli` wrote `{"text":"","frame_sec":0.08,"words":[],"tokens":[]}` and `parakeet-mlx` wrote `{"text":"","sentences":[]}`. The parsers return `[]` for both silence and garbage, so the document shape is the only way to tell them apart. |
| **The check lives in `run_parakeet`, which is shared by both callers** | `caption.py` (`_transcribe_in`) and `silence.py --filler` (`transcribe_words`) both take Parakeet results from it. |
| **Under `auto`, `transcribe_words` skips an engine that gives cues but no word timings** | Codex found it: a parakeet-mlx document with readable sentences but unreadable tokens gives caption cues but no words, and `--filler` refused on it. `run_parakeet` stays unchanged, so captions keep usable cues. |
| **A named `--engine` keeps its own refusals** | A second Codex pass showed the skip turned the accurate "ran but produced no word-level timings" (`kind: input`) into "install it" (`missing_tool`). |
| **Phase 2 order: `--segments` join gaps, then segment-past-video-end, then the 24 ms `--accurate` skew, then timeouts (grill first), then the `stage_hw` roll-up** | Join gaps are a live defect on the main lossless path for iPhone footage. Timeouts are a design problem with open questions. The roll-up is reporting only. |
| **Phase 2 starts in a fresh session, from a baton** | This session ran long, and the user prefers to wrap up before about half the context. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`9a90c31` fix(asr)** | `scripts/_common/asr.py`: new `_heard_nothing`. `run_parakeet` dies with no-speech only on the empty answer; otherwise it logs and returns `None`. `transcribe_words` skips a no-words result under `auto`. Also: 4 tests in `tests/test_accel.py` `ParakeetEngineTests` (with a `_run_with_mlx_writing` helper), a `CHANGELOG.md` entry, and a "Resolved" note on the open question in `docs/plans/2026-09-27-carry-forward-fixes.md`. |
| **Phase 2 baton** | `.baton/2026-09-28-carry-forward-phase2-plan.md` (git-ignored scratch). |

## Testing / Research Performed

- **Real-engine probe:** both installed Parakeet engines on a 3 s silent 16 kHz WAV (outputs
  above).
- **Red first:** the garbage-output test failed before the fix, and the filler test failed before
  its fix. The silence test passed before and after; it guards against over-correcting.
- **Mutation checks:** 4 mutants, all killed.
  - `_heard_nothing` always true (the old behaviour) and always false;
  - the `transcribe_words` skip removed;
  - the skip applied to named engines too.
- **Full suite:** 672 OK after the first fix, 673 OK after the filler fix, and 674 OK (3 skipped)
  after the named-engine scoping. Contract: 150 OK (1 skipped) on the first run; not rerun after,
  because only `asr.py` internals and tests changed.
- **Codex (`gpt-6-sol`, high, read-only):**
  - the first pass found one Major (the filler gap);
  - the second pass found one Minor (the named-engine refusal);
  - both were fixed with tests.

## Summary Statistics

- 1 code commit (`9a90c31`) after the Phase 1 summary.
- 4 new tests; the suite went from 670 to 674.
- 2 Codex passes, and 2 findings fixed.
- The branch is 6 commits ahead of origin, not pushed.

## Discoveries / Handoff Notes

- Both real Parakeet engines answer silence with an empty list, not an empty file or an error.
  That's the stable signal for "no speech".
- Free disk space went from about 4 GB to 35 GB between suite runs, cleared outside the session.
- Everything else a future session needs for Phase 2 is in the baton's "Learnings & Landmines":
  the `-read_intervals` keyframe behaviour, the `hev1` tag, fixture recipes, and the test policy.

## Current State

- Branch `m-series-hw-parakeet`, 6 commits ahead of `origin/m-series-hw-parakeet`, unpushed. The
  working tree is clean except the untracked `CLAUDE.local.md`.
- Phase 1 and the Parakeet open question are closed. Phase 2 has no plan yet; the baton holds the
  proposed scope.

## Unfinished Work

- **Push the branch:** `git push -u origin m-series-hw-parakeet` (the user pushes).
- **Phase 2**, from `.baton/2026-09-28-carry-forward-phase2-plan.md`:
  - confirm the scope (recommended: `--segments` join gaps, segment past the video's end, the
    `--accurate` 24 ms skew);
  - reproduce and measure;
  - write the plan and have Codex validate it;
  - build item by item.
