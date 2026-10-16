---
session_id: f94b4695-8cae-4319-99a9-9890ab2452e5
date: 2026-10-16
time: "5:47 AM PDT – 6:14 AM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: syncing upstream 2.10.3 and checking what it changes for video-motion

## Overview

The session reviewed the 2026-10-12 summaries and the upstream activity since then. Upstream had
implemented both issues the user filed (#325 → PR #329, #326 → PR #331) and shipped 2.8.7 through
2.10.3. The session merged 2.10.3 into `notes` and reinstalled the skill. It then measured how the
release affects video-motion's Phase 2 and gates, and recorded the results in video-motion's plan,
issue draft and baton.

The user rejected the first attempt to read the summaries, a compound `cat "$(git show …)"`. The
request was re-sent with "and any issues and PRs" added, and the summaries were then read with
`Read`.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Merge `upstream/main` with `--no-ff`, matching the earlier `Merge upstream 2.8.6 into notes` commit** | Keeps `notes`' history readable: one merge commit per upstream sync. The merge was clean |
| **Clear `tests/out/` and re-run, rather than report two failures** | Both failures were `refusing to overwrite existing output` from earlier runs' files. `tests/out` is git-ignored |
| **Measure ProRes `cut` on BT.601 inputs before changing the plan** | #332 converts BT.601 on re-encode. If it had applied to `prep`'s ProRes chain, the plan's `--to-bt709` step and the gate baselines would have changed. It doesn't: ProRes lines are excluded, and the output is pixel-identical to 2.8.6 |
| **Keep `color.py --to-bt709` in Phase 2** | #332 converts the matrix only (primaries and transfer pass through, range untouched) and treats untagged sources as BT.709. The plan needs primaries, range and a declared colour |
| **Don't move the user's clips or edit `gate1.py`'s source path** | Four Gate 1 sources had moved to `~/Downloads/talking-heads-videos/`. Those four were re-run with `SOURCES` overridden in a one-off `python3 -c`, and the path question was left in the baton for the user |
| **Don't post the cut late-start issue** | Posting is outward-facing, and the baton says the user reviews and posts it. It was re-verified and updated instead |

## Changes Made

| Change | Detail |
|--------|--------|
| **ffmpeg-skill `notes` merge** | `953dc7e`: "Merge upstream 2.10.3 into notes (#329 …, #330 …, #331 …, #332-#334 …)". 49 files changed |
| **Skill reinstalled** | `node bin/install.js --codex`. `~/.agents/skills/ffmpeg-skill/package.json` reads 2.10.3, and the `~/.claude/skills/ffmpeg-skill` symlink is intact. `SKILL.md` didn't change between `38f98c0` and `HEAD`, so no `/reload-skills` is needed |
| **video-motion plan** | `docs/plans/footage-motion-skill-plan.md`: the Phase 2 `check.py` item is struck as done upstream, and a note on 2.10.x was added |
| **video-motion impact note** | New `docs/plans/ffmpeg-skill-2.10-impact.md`: a release table, measurements and the remaining Phase 2 list |
| **video-motion cut issue draft** | `docs/plans/ffmpeg-skill-cut-start-issue.md` now names 2.10.3 and has a re-check note |
| **video-motion commit** | `50bbd68` "docs(plans): Record what ffmpeg-skill 2.8.7-2.10.3 changes for Phase 2" |
| **video-motion baton** | `.baton/2026-10-12-bt709-fork-landed.md`: a "2026-10-16" update section, and Next Steps item 4 trimmed. Git-ignored |
| **Memory** | `upstream-maintainer-expectations.md`: #325 and #326 marked as implemented by the maintainer (#329/2.8.7, #331/2.10.0), plus the pattern that the maintainer implements well-evidenced issues within about 3 days. `MEMORY.md`'s index line updated |

## Testing / Research Performed

- **Upstream review:**
  - `gh issue list` and `gh pr list` (last 15 of each).
  - Bodies of PRs #329 and #331–#334.
  - `git log notes..upstream/main`: 13 commits, 2.8.7 → 2.10.3.
  - The only open issue is #143 (no activity since 2026-09-18). There are no open PRs.
- **Tests:** `python3 -m unittest tests.test_picture tests.test_contract` gave 397 tests with 2
  stale-output failures. After clearing `tests/out/`: **OK (skipped=3)**. pytest isn't installed for
  Python 3.15.
- **Cut late start on 2.10.3:** a testsrc2 30 fps clip with AAC, cut with `--start 1.0 --end 11.0
  --accurate --codec prores --no-hw`. Video `start_time` was 0.021354, audio 0.000000. The bug is
  unchanged, and `make_zero` is still at `cut.py:826`.
- **ProRes cut colour on 2.10.3** (smpte170m tv, bt470bg tv and smpte170m pc inputs): the tags stay
  BT.601. The pc input comes out tagged `tv`. Compared with `git archive v2.8.6`, the tags and video
  framemd5 match for the smpte170m tv and pc inputs.
- **Code read:** `bt709_matrix_filter()` (`scripts/_common/color.py:77-105`) is matrix-only
  `colorspace`. `audio.py` has no `--sample-rate`.
- **video-motion Gate 1 on 2.10.3:**
  - A full run gave 23/27. (a)–(c) all passed. The four (d) failures were "missing" sources.
  - A second run of (d) with `SOURCES` pointed at `~/Downloads/talking-heads-videos` passed the
    other four.
  - Together, all 10 (d) sources pass.

## Summary Statistics

- Upstream: 13 new commits (7 releases), 6 merged PRs reviewed, 2 of the user's issues closed by the
  maintainer's fixes.
- Commits: 1 merge on ffmpeg-skill `notes`, 1 docs commit on video-motion `main`.
- Test runs: 3 unittest runs (397 tests each), 2 Gate 1 runs.
- Synthetic clips made: 4 (1 for the cut start, 3 for colour), plus 2 cuts with 2.8.6.

## Discoveries / Handoff Notes

- **#332's conversion skips `--codec prores` lines and converts only the matrix.** A
  BT.601-tagged ProRes intermediate stays BT.601, so the plan's `prep` chain is unaffected.
- **`cut --accurate --codec prores` re-tags a full-range input as `tv`.** It did this in 2.8.6 too.
  It matters for the plan's `--range` rule (taken from the tag), so declare the range from the
  source, not from the cut.
- **Stale `tests/out/` makes overwrite-protection tests fail.** Clear it before a test run.
- **Gate 1's `SOURCES` (`gate1.py:42`)** is stale for four clips the user moved into
  `~/Downloads/talking-heads-videos/`.

## Current State

- **ffmpeg-skill `notes`:** `953dc7e` plus this summary. Not pushed: the user pushes.
  `CLAUDE.local.md` and `bench/` were untracked before the session, and still are.
- **Installed skill:** 2.10.3.
- **video-motion `main`:** `50bbd68`, ahead of origin, not pushed. The baton is updated.
- **Scratchpad only:** test clips under `.../scratchpad/cutstart/`, a `v2.8.6` scripts export, and
  the Gate 1 log.

### Unfinished Work

- **Push** (the user): `git -C ~/projects/ffmpeg-skill push -u origin notes`, then video-motion
  `main` as usual.
- **Gate 1 source path:** decide where the four moved clips should live, or update `gate1.py`'s
  `SOURCES`.
- **video-motion baton Next Steps 1–3**, untouched by this session:
  - decide on the fork-review findings;
  - post the fframes BT.709 and ffmpeg-skill cut-start drafts (the user reviews them first);
  - PIL Night on the fork.
- **Phase 2:** `color.py --to-bt709`, then `audio.py --sample-rate`, each issue-first upstream.
