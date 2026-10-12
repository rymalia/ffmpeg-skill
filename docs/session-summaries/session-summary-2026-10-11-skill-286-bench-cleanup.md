---
session_id: fe5d7932-18b8-411c-8606-a66c9a9f26de
date: 2026-10-11
time: "10:02 PM PDT – 10:24 PM PDT"
resumed: "2026-10-11 10:02 PM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: skill 2.8.6 install, upstream 2.8.4–2.8.6 review, bench worktree removal

## Overview

This summary covers only the last stretch of a long-running session, after it resumed at 10:02 PM.

The user's `npx ffmpeg-skill@2.8.6 --codex` failed with `sh: ffmpeg-skill: command not found`. I found the cause and installed 2.8.6 properly, then reviewed upstream releases 2.8.4–2.8.6 and removed the benchmark worktree.

The session's earlier work, from 2026-10-09 to 2026-10-11, is in `session-summary-2026-10-11-upstream-prs-asr-bench.md`. That file was deliberately left unchanged. The collector's `session_start` reports the resume time because the resume hook overwrote it.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Install from the scratchpad with `--codex`** | Inside the repo, `npx` resolves the repo's own `package.json` (also named `ffmpeg-skill`) and finds no command. `--codex` writes to `~/.agents/skills/ffmpeg-skill`, the real directory behind the `~/.claude/skills` symlink. |
| **No merge into `notes`** | The M4 session (`b4b20b84`) had already merged 2.8.6 (`e59499e`) and pushed. Local `notes` already matched origin at `fd29363`. |
| **Remove `ffmpeg-skill-wt-bench`** (user approved) | #318 is closed. The branch is pushed (`1d72cb0`), and the only ignored files are reproducible (`data/` via `prep.py`, `.cache/`) or superseded (the logs and the aborted run). |

## Changes Made

| Change | Detail |
|--------|--------|
| **Skill 2.8.6 installed** | `npx -y ffmpeg-skill@2.8.6 --codex`, run from the session scratchpad, updated `~/.agents/skills/ffmpeg-skill`. |
| **Bench worktree removed** | Plain `git worktree remove ../ffmpeg-skill-wt-bench`, then `git worktree prune`. The local branch `bench/asr-parakeet-vs-whisper` is kept. |
| **Memory** | New `npx-install-outside-repo.md`, indexed in `MEMORY.md`. Updated `upstream-maintainer-expectations.md`: #318 closed through #323, and #324 verified by the M4. |

## Testing / Research Performed

- **Reproduced the `npx` failure:** `npx -y ffmpeg-skill@2.8.6 doctor` fails in the repo and works from the scratchpad. `npm view` shows the same `bin` entry for 2.8.3 and 2.8.6, so the package isn't at fault.
- **Install check:**
  - `package.json` reports 2.8.6.
  - `diff -rq` of the installed `scripts/` against `git archive upstream/main scripts` (`f62e7d0`) shows no differences.
  - `doctor` reports ok: 69 capabilities available, 0 missing.
- **Upstream review** (`f1a4f2a..upstream/main`):

  | release | PR | change |
  |---|---|---|
  | 2.8.4 | #322 | cut `-reinit_filter 0` |
  | 2.8.5 | #323 | whisper.cpp `-mc 0` by default; "Acts on #318 (measurement by rymalia)" |
  | 2.8.6 | #324 | VideoToolbox when the build has no libx264/libx265 |

- **Follow-through:**
  - #318 has the user's (M4) reply at 04:34 UTC and was closed as completed.
  - #324 asked @rymalia for a check, and the M4 posted LGPL and full-build results (issuecomment-6117811068). No maintainer reply yet.
  - The `-mc` help line on this Mac matches whisper.cpp 1.9.5.
- **Before removing the worktree:** `git status --porcelain --ignored` showed no tracked changes, and local matched origin at `1d72cb0`.

## Discoveries / Handoff Notes

- **Never run `npx ffmpeg-skill` inside the repo or its worktrees.** Run it from a neutral directory.
- **`~/.claude/skills/ffmpeg-skill` was recreated at 21:55 with an absolute target**, `/Users/rymalia/.agents/skills/ffmpeg-skill`. This session didn't do it. It still resolves to the same directory.
- **The M4 now does upstream work in parallel.** Check `notes` and the upstream threads before acting, because work may already be done.

## Current State

- **Main checkout:** on `notes` at `fd29363`, matching origin. It is the only worktree.
- **Installed skill:** 2.8.6.
- **Upstream:** at `f62e7d0` (v2.8.6).

## Unfinished Work

- **#324:** wait for the maintainer's reply to the M4's verification comment.
- **Optional:** delete the local branches `pr/macos-ffmpeg-full-link` (merged upstream as #319) and `bench/asr-parakeet-vs-whisper` (never merged; it lives on the fork, and #318 links to it). Both are on the fork, so nothing is lost.
