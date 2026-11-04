---
session_id: 6ac5e57c-7a5b-46ca-aa04-32b2f830ea26
date: 2026-11-03
time: "2026-11-01 10:49 PM PST – 2026-11-03 10:58 PM PST"
resumed: "2026-11-03 09:42 PM PST"
project: ffmpeg-skill
branch: notes
---

# Session Summary: upstream 3.1.1 sync, #143 real-hands rows, issues #393–#397

> Timestamps: the start (2026-11-01 10:49 PM PST) is from the session's first SessionStart hook. The resume (2026-11-03 09:42 PM PST) is from the resume hook, which also overwrote the collector's `session_start`, so the collector shows the resume time as the start. The end time is from the metadata collector.

## Overview

- Assessed and merged upstream ffmpeg-skill 2.10.9 → **3.1.1** into `notes`, reinstalled it for Codex and Claude Code, and ran the full test suite on the M4 Max.
- Coordinated a video-motion Gate 1 re-run with the other session.
- Ran the **Codex** and **macOS plain-Homebrew-ffmpeg** rows of upstream tracker #143, and filed the five findings upstream as **#393–#397**, plus a results comment on #143.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Merge upstream 3.1.1 into `notes` with `--no-ff`; fast-forward local `main` to `origin/main`** | Same pattern as the 2.10.x syncs. A test merge (`git merge-tree`) showed no conflicts, because `notes` adds only docs. |
| **Archive `feat/audio-sample-rate` and `feat/color-to-bt709` as tags instead of plain deletion** | The user allowed deleting them "if no longer needed". They were never on origin, 3.1.1 has no `--sample-rate`/`--to-bt709`, and video-motion's carry-over list still says to draft issues for both. Tags keep the work recoverable, as with `archive/m-series-hw-parakeet`. |
| **Don't file the one-frame `--accurate` start skew the video-motion session reported** | Reproduced on synthetic 29.97 fps. It's documented in the #342 CHANGELOG entry and design-decisions (~line 1750) and reported as `av_start_skew_seconds`, so it is not a bug. |
| **Simulate "plain Homebrew ffmpeg" without touching Homebrew** | `ffmpeg-full` is force-linked and other sessions use it, and #321 swaps to `ffmpeg-full` whenever it's in the same prefix. The real lean `Cellar/ffmpeg/9.0.2_1` binaries were copied into a fake prefix with no `opt/ffmpeg-full`, and agents got a throwaway `ZDOTDIR` profile, because their login shells otherwise re-put `/opt/homebrew/bin` first. The simulation is labelled as such everywhere it's reported. |
| **Don't override the user's npm `min-release-age=3`** | It's a deliberate supply-chain guard. On 11-02 bare `npx` installed 2.21.1 (3.1.1 was too new), and 3.1.1 was restored from the checkout. On 11-03 the window had passed and bare `npx` installed 3.1.1. |
| **Synthetic inputs for all agent runs; a real iPhone clip only for direct tool runs** | Memory: synthetic for anything posted upstream, and the user's images aren't sent to external APIs (Codex views contact sheets). |
| **File #397 narrowly** | `references/gotchas.md:49` already documents "only the first audio track … dropped on re-encode". The issue asks only that the result report the drop, and notes that it also happens on stream copy. |
| **Issues follow #336's shape, offer no PR, and leave the fix shape to the maintainer** | These are the maintainer's expectations in memory: issue first, say what was actually run, keep simulated and real separate, British English. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Upstream merge** | `554fef7` on `notes`: merge of upstream 3.1.1 (`1ce2c18`). Local `main` moved to `origin/main` (`1ce2c18`). |
| **Skill install** | `~/.agents/skills/ffmpeg-skill` is 3.1.1. It went to 2.21.1 via bare `npx` on 11-02, back to 3.1.1 via `node bin/install.js --codex`, and on 11-03 to 3.1.1 via bare `npx ffmpeg-skill --codex`. The `~/.claude/skills/ffmpeg-skill` symlink was checked intact each time. |
| **Branch archive** | Tags `archive/audio-sample-rate` (`2f6b148`) and `archive/color-to-bt709` (`6626b9a`); both local branches deleted. The user pushed the tags. |
| **#143 results doc** | `docs/plans/issue-143-real-hands-2026-11-02.md` holds setup, both rows, five findings and the posted #143 comment. Evidence (logs, contact sheets, posted issue bodies) is in `docs/evidence/143-real-hands-2026-11-02/`. Commits `192836a` and `de204a0`; the "comment posted" status line is uncommitted (see Current State). |
| **Upstream issues** | Filed #393–#397 (see Issues & PRs). |
| **#143 comment** | Posted, with both rows, the macOS answer, the simulation caveat and links to #393–#397. |
| **Memory** | Updated `notes-branch.md` (archive tags) and `upstream-maintainer-expectations.md` (#143 state 11-02, rows run, issues filed, comment posted, npm guard). |

## Testing / Research Performed

- **Full suite on 3.1.1** (`tests/run_parallel.py`): 984 tests, 9 modules, all OK, 2785 s wall (46 min).
- **Contract suite** (`tests/test_contract.py`): 254 OK, 3 skipped. The skips are the real-device corpus (not fetched), `PR_SET_PDEATHSIG` (Linux only) and a drawtext test for FFmpeg 8.0–8.1.0 only.
- **`doctor`** on the installed 3.1.1: `ok: true`, nothing missing or unsupported, no `ffmpeg_security` warnings (FFmpeg 9.0.2, Python 3.15.2).
- **Upstream assessment:** read the full CHANGELOG from 2.10.9 to Unreleased (33 release sections), the diff stats (116 files), and the upstream issue/PR list. Searched by keyword and by meaning for overlaps with the five findings: none found. #298 and #344 were read for context.
- **Frame-skew repro:** `cut.py --accurate --codec prores` on synthetic 29.97 fps. A start on a frame gave 120 frames from 0. A start between frames (3.150) gave video at 0.033367, 119 frames, `verified: true`, `av_start_skew_seconds: -0.033367`.
- **#143 Codex row:** npx install, a skill-list query, a natural TikTok request in `日本語 テスト 🎬/` (log `codex-tiktok.log`), and direct probe, cut, render, check and look on the real iPhone clip and the synthetic clip.
- **#143 macOS row:** `doctor` and the installer with the lean stand-in. Direct probe and render (dry and real) and `look`. A natural caption request to Codex (gpt-5.6-luna high) and to Claude Code (`claude -p`, Opus 5.5) with only the lean ffmpeg reachable; `command -v ffmpeg` was checked in both agents first.
- **Re-verified every finding on 3.1.1 before posting**, with minimal synthetic repros in the scratchpad `repro/` folder: F1 parse error and passing dry run; F2 doctor `look: yes` with the default `look` failing and `--no-timecode` passing; F3 tofu crop with `emoji_monochrome` and `verified: true`; F4 `--write-srt` output; F5 a two-AAC-track MOV losing track 2.
- **Code reading:** `_libass_color_probe`/`emoji_support` (`_common/emoji.py:204–275`), the cue regex (`caption.py:77`), the `subtitles=`/`ass=` builders (`caption.py:1590,1611`), `escape_filter_path` (`decision.py:247`), `_homebrew_full_build` (`runner.py:171`), the installer's `checkFfmpeg` (`bin/install.js`), and `look.py`'s drawtext timecode.

## Discoveries / Handoff Notes

- **On FFmpeg 9.0.2, a missing filter given a positional argument fails as a parse error.** `subtitles=s.srt` gives `No option name near 's.srt'`; `subtitles=filename=s.srt` gives `No such filter`. That's why 3.1.0's `filter_missing` classifier misses the case (#393).
- **The emoji colour probe only looks for coloured pixels,** so tofu is reported as "monochrome" (#395). On Homebrew ffmpeg-full 9.0.2, Apple Color Emoji (sbix) gives tofu through libass.
- **Neither agent read `caption.usable` before running `caption.py`** (the #143 macOS question). Both trusted a passing dry run. Claude Code then invented an escaping bug; Codex quietly switched to the full build (only possible because of the stand-in) and shipped tofu as 🟢.
- **The installer checks only ffmpeg's presence and version,** not its capabilities, so a plain-Homebrew user sees "Done" with no warning.
- **Agents' login shells re-source the user's profile:** Codex `zsh -lc` and Claude Code's Bash. `~/.zshrc` runs `ensure-ffmpeg-full`. Use a throwaway `ZDOTDIR` to control `PATH` in agent tests.
- **The SessionStart resume hook overwrites `SESSION_START_TIME`,** so after a resume the summary collector reports the resume time as the start.
- **npm `min-release-age=3`** in `~/.npmrc` makes a fresh upstream release unavailable to `npx` for three days.
- **Gate 1 (other session):** 29/29 on 3.1.1. `snap_to_frame` is still needed for starts between frames, and the `settle` start shift is now a no-op. The gates README was corrected in video-motion `97842ef`.
- Codex garbled `話す` into `話સે` twice in its own commands. That's agent-side, not the tool.

## Issues & PRs

- https://github.com/kajisho5/ffmpeg-skill/issues/393 — missing `subtitles` filter: unclassified parse error; `--dry-run` passes
- https://github.com/kajisho5/ffmpeg-skill/issues/394 — `doctor` marks `look` usable without drawtext
- https://github.com/kajisho5/ffmpeg-skill/issues/395 — tofu emoji reported as `emoji_monochrome`, `verified: true`
- https://github.com/kajisho5/ffmpeg-skill/issues/396 — SRT given to `--text`/`--cues` burned in line by line
- https://github.com/kajisho5/ffmpeg-skill/issues/397 — stream-copy `cut` drops the second audio track silently
- https://github.com/kajisho5/ffmpeg-skill/issues/143#issuecomment-6624715127 — Codex and macOS rows

## Summary Statistics

- Upstream: 75 commits / about 33 releases (2.10.9–3.1.1) assessed and merged; 116 files changed upstream.
- Tests: 984 e2e plus 254 contract tests, all passing (3 contract skips, explained).
- Commits this session on `notes`: 3 (`554fef7`, `192836a`, `de204a0`), all pushed by the user.
- Agent runs: 3 natural-language task runs (Codex: TikTok and lean caption; Claude Code: lean caption), plus 4 short probes (Codex skill list, Codex `PATH` ×2, Claude Code `PATH` ×1).
- Upstream: 5 issues filed, 1 comment posted, 0 PRs.
- Branches: 2 archived as tags and deleted.

## Current State

- `notes` at `de204a0` = `origin/notes`. One uncommitted change: the status-line and heading update in `docs/plans/issue-143-real-hands-2026-11-02.md` marking the #143 comment as posted. It's committed together with this summary.
- Installed skill: 3.1.1, both agents. `ffmpeg-full` is still linked; Homebrew was never changed.
- Scratchpad (`r143/`, `repro/`) holds the working copies; everything needed was copied into `docs/evidence/`.
- Pre-existing untracked files, not from this session: `-encoders`, `CLAUDE.local.md`, `bench/`.

## Unfinished Work

- Watch #393–#397 for maintainer replies, and answer every request (memory rule). Pattern: well-evidenced issues tend to be implemented by the maintainer within days.
- Revive or drop `archive/audio-sample-rate` and `archive/color-to-bt709`. Reviving means rebasing onto `main` and drafting an issue first.
- Optional (video-motion): pass `--json` to `gate1.py`'s `skill()` and check `av_start_skew_seconds` (noted there, not adopted).
- Push the commit holding this summary.
