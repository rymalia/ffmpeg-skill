---
session_id: 9b553388-600e-46cf-9746-f64d31e129db
date: 2026-09-27
time: "3:44 PM PDT – 4:34 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: ffmpeg-skill carry-forward guide (lessons from the original skill)

## Overview

Read six earlier ffmpeg-skill session summaries, the fork session summary and the five related memory files. From them, wrote one guidance document of the tips and gotchas worked out on this machine with the original skill, so they carry over when the forked skill (`rymalia/ffmpeg-skill`, branch `m-series-hw-parakeet`) is set up here. No code, config or git state was changed.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Saved the guide to `~/projects/docs/`, not the fork repo** | It sits beside the six source session summaries and stays out of the fork branch, where it would be an untracked personal note. The `~/projects` docs are also indexed by QMD for later sessions. |
| **Saved it as a local Markdown file, not a Claude Doc or artifact** | The user will use it from a future Claude Code session on this machine, which can read a local file directly. Publishing it as a shareable page was offered but not requested. |
| **Checked the machine's current state before writing, rather than trusting the summaries** | The guide calls out real differences on this machine, and each one was observed this session (see Testing). |
| **Added a section on how the fork changes the old lessons** | Setting `FFMPEG_SKILL_HW=1` as the default sends `overlay.py`, `freeze.py` and hybrid cuts to VideoToolbox. That conflicts with the earlier choice of x265 medium CRF 18 for deliverables, so the guide recommends `--no-hw` for finals. |
| **Did not change the `upstream` push URL** | The user hadn't authorized it. It's flagged at the top of the guide and was offered as a next step. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Guidance document** | Created `/Users/rymalia/projects/docs/ffmpeg-skill-carry-forward-guide.md`. Sections: §0 setup checklist, §1 ffmpeg-full build and self-healing, §2 cutting and trimming, §3 masking, blurring and overlays, §4 long jobs and timeout, §5 shell and verification traps, §6 how the fork changes things, plus a pre-flight checklist. |
| **This session summary** | `docs/session-summaries/session-summary-2026-09-27-carry-forward-guide.md` in the fork repo, left untracked. |

## Research Performed

- **Sources read:**
  - 6 session summaries in `~/projects/docs/session-summaries/`: 09-17 setup and split, 09-19 upgrade and self-healing, 09-21 corner mask, 09-21 masking and slicing, 09-22 scoreboard overlay, 09-24 lossless trim.
  - The fork summary `session-summary-2026-09-27-videotoolbox-parakeet-fork.md`.
  - 6 memory files: `ffmpeg-full-selfhealing`, `ffmpeg-skill-masking-gotchas`, `ffmpeg-skill-timeout-default`, `ffmpeg-lossless-trim-plain-command`, `brew-uses-intersection-gotcha`, `user_two_computers`.
- **Machine state checks (one Bash call):**
  - `~/.claude/skills/ffmpeg-skill` is an **absolute** symlink to `~/.agents/skills/ffmpeg-skill`.
  - `~/.local/bin/ensure-ffmpeg-full` exists, and the `brew()` wrapper is in `~/.zshrc`.
  - Active `ffmpeg` resolves to `Cellar/ffmpeg-full/9.0.2`.
  - `~/.zshenv` has no `FFMPEG_SKILL_HW` or `PARAKEET_*` exports.
  - `~/.cache/whisper.cpp` does not exist.
  - `parakeet-mlx` is not on PATH, while `whisper-cli` is at `/opt/homebrew/bin`.
  - `git remote -v` shows a real push URL for `upstream` (`kajisho5/ffmpeg-skill`), not `DISABLED`.
  - The installed `cut.py:300` still forces `--accurate` on VFR-suspected sources.

## Summary Statistics

- Sources synthesized: 7 session summaries and 6 memory files.
- Files created: 2 (the guide and this summary).
- Differences between this machine and the other one found and documented: 4 (upstream push URL not disabled, no whisper models, no parakeet-mlx, symlink absolute rather than relative).

## Discoveries / Handoff Notes

- **The upstream push URL is live on this machine.** `git remote set-url --push upstream DISABLED` is still needed; this breaks the fork-only rule in the user's global CLAUDE.md until it's fixed.
- `doctor` reports `external:whisper` as available on this machine just because `whisper-cli` exists, even though no model is in the skill's search path.
- `docs/session-summaries/` in this repo now also holds `session-summary-2026-09-27-hw-real-video-test.md` and `session-summary-2026-09-27-second-mac-handoff.md`. Neither was written in this session.

## Current State

- The fork repo is on `m-series-hw-parakeet` at `1922a59`, tracking `origin/m-series-hw-parakeet`. No commits or pushes this session.
- The guide is at `/Users/rymalia/projects/docs/ffmpeg-skill-carry-forward-guide.md` (`~/projects` is not a git repo).
- No machine setup was changed.

## Unfinished Work

- Disable the upstream push URL in `~/projects/ffmpeg-skill` (offered, not yet done).
- Set up the fork on this machine following §0 of the guide: `node bin/install.js --codex`, whisper and Parakeet models, and the `~/.zshenv` exports. Decide on the `FFMPEG_SKILL_HW` default first (§6).
- Optional: save the "fork vs. the old lessons" points (§6) as a memory, or publish the guide as a shareable page.
