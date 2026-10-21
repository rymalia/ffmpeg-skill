---
session_id: 7f4506be-598f-4113-9fc8-16f4bff82d32
date: 2026-10-21
time: "2026-10-20 11:26 AM PDT – 2026-10-21 01:38 AM PDT"
resumed: "2026-10-21 01:16 AM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: upstream check, #336 outcome, and the 2.10.5 → 2.10.7 sync

## Overview

Checked upstream (kajisho5/ffmpeg-skill) activity and found our issue #336 fixed by the maintainer's own PR #342. Deleted the now-superseded local branch, merged upstream into `notes` twice (2.10.5, then 2.10.7 the next morning), reinstalled the skill with `--codex` each time, and ran the full test suite on both versions. Both runs passed.

The start time comes from the first SessionStart hook (`SESSION_START_TIME=2026-10-20 11:26 AM PDT`). The metadata collector reported `session_start: 2026-10-21 01:16 AM PDT`, which is the resume hook overwriting it, so it is recorded as the resume time instead.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Delete `feat/cut-accurate-start` (user's call)** | #342 fixes #336 differently: it drops `-avoid_negative_ts make_zero` on accurate video re-encodes only. The branch (`34ae4ea`, `ab33bf1`) was never pushed. |
| **No follow-up issue for the between-frames offset (for now)** | #342 deliberately keeps about one frame (0.033 s) of offset on FFmpeg 7.1/Homebrew when `--start` falls between frames, because moving the picture alone would leave the sound a frame ahead. Anything further would need a new issue with numbers. |
| **Sync through merge commits into `notes`, install with `--codex`** | Follows the established `notes` pattern and CLAUDE.local.md: one installer run updates both Codex's copy and Claude Code's link to it. |
| **Clear `tests/out` before each test run** | Matches how the maintainer reports runs ("on a clean `tests/out`"). The directory only holds generated output and is git-ignored. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Branch deleted** | `feat/cut-accurate-start` (was `ab33bf1`), after switching to `notes`. Recoverable with `git branch feat/cut-accurate-start ab33bf1` while the reflog lasts. |
| **Merge 2.10.5** | `notes` ← `upstream/main` `f02bab4`: #337 README header, #338 join pictures start at 0, #341 FAQ + `redact.py` delogo mode + Nirmala.ttc, #342 accurate-cut pictures start at 0. `SKILL.md` changed (+3/−2). |
| **Merge 2.10.7** | `notes` ← `upstream/main` `4334225`: #343 audit fixes (release-check, `--scale` on text refused, sync-offset-0 wording, MCP `--timeout`), #344 rotated frames at displayed size + emoji probe on colon paths, #345 README FAQ. `SKILL.md` unchanged. |
| **Skill reinstalled twice** | `node bin/install.js --codex`; `~/.agents/skills/ffmpeg-skill/package.json` reported 2.10.5, then 2.10.7. `~/.claude/skills/ffmpeg-skill` is still a link to it. The installer found ffmpeg 9.0.2. |
| **Memory updated** | `upstream-maintainer-expectations.md` gained a #336/#342 follow-up line; the `MEMORY.md` index now reads "#325/#326/#336 … 2.8.7/2.10.0/2.10.5". |
| **Pushed (by the user)** | The user pushed `notes` (13 commits ahead before the push). |

## Testing / Research Performed

- **Upstream survey (2026-10-20):** recent upstream commits; open PRs #340, #343, #344; recent PRs; open issues (only #143); issues by and involving `rymalia`; the #336 body (it has no comments); the #342 body and its non-bot comments (none); bodies of #343, #344, #340; #339 and #143 status.
- **`npm test` on 2.10.5** (clean `tests/out`, ffmpeg 9.0.2): `tests/test_all.py` 912 tests OK (2 skipped); `tests/test_contract.py` 169 OK (1 skipped). Wall time 24:52.
- **`npm test` on 2.10.7** (same setup): `tests/test_all.py` 922 OK (2 skipped); `tests/test_contract.py` 172 OK (1 skipped). Wall time 16:34.
- Skips are the same on both versions and come from this Mac's setup: an ASR engine is installed, the ffmpeg on PATH has no fribidi, and the real-device corpus isn't downloaded.

## Summary Statistics

- Upstream releases synced: 2 (2.10.5, 2.10.7); upstream PRs absorbed: 7 (#337, #338, #341, #342, #343, #344, #345)
- Full suite runs: 2, both passing (1,081 and 1,094 tests)
- Local branches deleted: 1
- Memory files updated: 2

## Discoveries / Handoff Notes

- **Pattern holds:** #336 is the third of our issues (after #325 and #326) that the maintainer implemented within days and closed with no comment.
- **#342's design:** `make_zero` is kept for stream copies and for audio-only `--accurate` cuts (where it folds AAC priming into the reported length). Matroska has no edit list, so in an MKV the priming packet can sit about 21 ms before 0 while the picture is at 0.
- **#340** (Nirmala fallback) is still open with an empty description, though #341 already shipped Nirmala.ttc support.
- **#143** (the real-hands tracker) has had no change since 2026-09-18; the Codex and macOS rows we could fill are still `not run`.
- **The test suite got faster:** 2.10.7 ran in 16:34 against 24:52 for 2.10.5, despite 13 more tests. The cause wasn't investigated.
- **Metadata quirk:** on a resumed session the collector's `session_start` equals the resume time; the true start is only in the first hook output.

## Current State

- The checkout is on `notes`, which contains upstream 2.10.7; the user has pushed it. Fork `main` equals `upstream/main` (`4334225`).
- Installed skill: 2.10.7 for Codex and Claude Code.
- Untracked and pre-existing (not from this session): `CLAUDE.local.md`, `bench/`.
- Test logs (scratchpad, temporary): `test-2.10.5.log`, `test-2.10.7.log`.

## Issues & PRs

- https://github.com/kajisho5/ffmpeg-skill/issues/336 (ours, closed by #342)
- https://github.com/kajisho5/ffmpeg-skill/pull/342
- https://github.com/kajisho5/ffmpeg-skill/pull/343
- https://github.com/kajisho5/ffmpeg-skill/pull/344
- https://github.com/kajisho5/ffmpeg-skill/pull/340

### Unfinished Work

None required. Optional: if the remaining ~1-frame offset on between-frames `cut --accurate` starts (FFmpeg 7.1/Homebrew) matters for `fit --fps`, measure it and file a new issue rather than reviving the deleted branch.
