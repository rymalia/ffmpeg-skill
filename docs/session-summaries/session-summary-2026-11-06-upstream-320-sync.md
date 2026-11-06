---
session_id: 2904990e-8c99-4799-8ff4-5d03c5e1e597
date: 2026-11-06
time: "03:09 PM PST – 03:30 PM PST"
project: ffmpeg-skill
branch: notes
---

# Session Summary: upstream 3.2.0 sync and #143 tracker close-out

### Overview

Assessed the upstream releases 3.1.2–3.2.0 and the unreleased `fix/scenes-beats-audio-only` branch against our local interests. Merged `upstream/main` (3.2.0) into `notes`, reinstalled the skill for Codex and Claude Code, and marked the five #143 findings (#393–#397) fixed in the tracker doc.

### Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Did not merge `fix/scenes-beats-audio-only`** | It is unreleased (listed as "Unreleased" in its CHANGELOG). `notes` follows released `upstream/main`. |
| **Left the posted issue bodies unchanged** | The `docs/evidence/143-real-hands-2026-11-02/issue-body-39x.md` files are records of what was posted. Only the tracker plan doc records the fix status. |
| **Installed with `node bin/install.js --codex`** | Per CLAUDE.local.md, this keeps `~/.claude/skills/ffmpeg-skill` as a link to the Codex copy, so the two agents don't drift apart. |

### Changes Made

| Change | Detail |
|--------|--------|
| **Merge upstream 3.2.0** | `c320a5c`: `--no-ff` merge of `upstream/main` (`9bdb444`) into `notes`. 75 files, +7167/−701, no conflicts. |
| **Skill reinstalled** | `~/.agents/skills/ffmpeg-skill` is now at version 3.2.0. The `~/.claude/skills/ffmpeg-skill` link is intact. |
| **#143 tracker updated** | `4a24127`: `docs/plans/issue-143-real-hands-2026-11-02.md` now has a status line saying all five issues were fixed in 3.1.2 by PR #399 (`c005589`) and closed on 2026-11-05. The Findings heading and each finding 1–5 are tagged `[#39x, fixed in 3.1.2]`. |

### Testing / Research Performed

- Read the CHANGELOG entries for 3.1.2–3.2.0 and the scenes-beats branch's full non-test diff (`scenes.py`, `cut.py`, `_contract.py`, `SKILL.md`, `references/scripts.md`).
- Checked the video-motion plan (`~/projects/video-motion/docs/plans/footage-motion-skill-plan.md`) against what changed upstream: searched for `--to-bt709`, `color.py`, `overlay.py` and alpha references, and compared function line numbers in `color.py`/`overlay.py` at `1ce2c18` and `upstream/main`.
- `gh issue view` on #393–#397: all `CLOSED COMPLETED`, 2026-11-05. `git tag --contains c005589` returns `v3.1.2`.
- After the install: `SKILL.md` in the repo matches the installed copy, the installed `package.json` reports 3.2.0, and the installer found ffmpeg 9.0.2.
- No test suite was run. The fixes for #393–#397 were not re-verified on our setup.

### Discoveries / Handoff Notes

- **Beat-grid drift in 3.2.0:** `scenes.py --beats` and `cut.py --snap beats` time the envelope at 10 ms when the real step is 9.977 ms (220 samples at 22050 Hz). The grid stretches 0.23%, about 68 ms by 30 s, and tempos are rounded to whole steps. `fix/scenes-beats-audio-only` (`001a6a6`, `25a994f`) fixes this, adds audio-only input (`audio_only: true`) and per-onset `onset_refinement`, and flips `scenes` to `video_required: false`. Until it is released, don't rely on beat-snap precision on long music beds.
- **video-motion plan impacts:**
  - `color.py --to-bt709` is still not upstream.
  - The plan's line references were already stale and have moved further (`bt2020_sdr_to_bt709_chain` went from 176 to 204), so they should be re-anchored by function name.
  - 3.1.6 (#410) added shared colour helpers (`range_chain`, `matrix_chain`, `rgb_chain_to_bt709`), labels untagged sources BT.709 in `look.py`/`scenes --sheet`, and converts full-range SDR to limited range before mixing. The `--to-bt709` spec should build on these helpers.
  - #411 makes every scaling tool convert non-square pixels (DV/HDV) to square.
  - 3.2.0's ProRes 4444/alpha masters with alpha read-back make the deferred alpha overlay mode cheaper.
- **Other behaviour changes:** a `.webm` source now defaults to `.mp4` output, `metadata.py` writes MP4/MOV with faststart, and `batch.py` uses a separate work directory per item and refuses an `output_dir` that is the input folder.
- **zsh gotcha:** `"$r:scripts/..."` in zsh applies the `:s` history modifier ("bad substitution"). Use `"${r}:path"` in `git show` loops.

### Current State

- `notes` is at `4a24127`, ahead of `origin/notes` (not pushed; the user pushes).
- The untracked `-encoders`, `CLAUDE.local.md` and `bench/` were left alone.
- `/reload-skills` was not run by Claude (it's a built-in). The skill listing in this session already showed the updated description.

### Summary Statistics

- 2 commits on `notes` (1 merge, 1 docs) plus this summary.
- 7 upstream releases assessed (3.1.2–3.2.0), plus 1 unreleased branch (2 commits, 10 files).
- 5 upstream issues confirmed closed and recorded as fixed.

### Unfinished Work

- Re-verify the #393–#397 fixes on our setup (plain-Homebrew stand-in, ffmpeg-full emoji tofu, iPhone MOV cut).
- When `fix/scenes-beats-audio-only` is released, merge it and re-test `--snap beats` on a real music bed.
- Update the video-motion plan: re-anchor the `color.py`/`overlay.py` references by function name, and base the `--to-bt709` spec on the 3.1.6 helpers.
