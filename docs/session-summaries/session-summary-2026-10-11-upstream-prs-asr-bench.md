---
session_id: fe5d7932-18b8-411c-8606-a66c9a9f26de
date: 2026-10-11
time: "2026-10-09 06:05 PM PDT – 2026-10-11 01:13 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
related_pr: 319
---

# Session Summary: macOS ffmpeg-full fix, ASR benchmark and upstream follow-through

## Overview

This session ran over three days and caught up on the follow-ups owed to the upstream maintainer (@kajisho5):
- It wrote a runbook to carry the self-healing `ffmpeg-full` setup to the user's other Mac.
- PR #319 (macOS install hints) was opened and merged into v2.8.2.
- Issue #317 was filed, which the maintainer then implemented as PR #321. The session verified #321 on real hardware and reported back.
- A Parakeet vs whisper.cpp benchmark ran on two Macs and was posted as issue #318. It found a whisper.cpp repetition loop that `-mc 0` stops.

The session was compacted once, partway through 2026-10-09/10. This summary covers both halves.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Fix the macOS hint first as docs (#319); the automatic resolver goes in an issue (#317)** | The maintainer wants issue-first for anything beyond a bug or doc fix, and no 2.x behaviour changes without discussion. Swapping in another binary automatically changes behaviour. |
| **Benchmark through the skill's own `transcribe_result()` on pinned ESB data** | The numbers are then what a user of the skill gets. `manifest.json` (ESB revision `de79e57`) and the pinned normaliser (`97b92fb`) make the runs reproducible on both machines. |
| **Run the same benchmark on the M4 Max through a baton, on the fork** | Two machines separate the effect of the chip from the effect of the engine. The fork branch carries the harness and the results. |
| **`-mc 0`: offer it in #318 rather than sending a PR** | It changes decoding for every whisper.cpp user. Whether it becomes the default or opt-in is the maintainer's call. |
| **Drop the claim that "whisper.cpp base looped too"** | Re-checking showed the earnings22 reference itself says "thank you" 19 times, and base's 23 cues are spread over 7 minutes. That isn't evidence of a loop. |
| **Verify #321 with a real `brew unlink ffmpeg-full && brew link ffmpeg`, restored by `ensure-ffmpeg-full`** | The maintainer asked for the real setup. The symlink-shim simulation was done first but labelled separately in the reply. |
| **Leave Codex's "Major" (ffmpeg and ffprobe resolve independently) out of the #321 reply** | It reproduces only with a contrived PATH. Both Homebrew formulas ship the pair, and that PATH could mix builds before the PR too. |
| **Raise the `docs/contract.md:363` "no paths" contradiction in the #321 reply** | Confirmed: the new `ffmpeg_path` / `ffprobe_path` keys contradict a deliberate privacy promise in the contract doc. |
| **Codex model is `gpt-5.6-luna` xhigh, run serially** | The user corrected terra to luna. Three terra xhigh runs in parallel had hit the usage limit. |

## Changes Made

| Change | Detail |
|--------|--------|
| **ffmpeg-full runbook** | Created `~/projects/docs/ffmpeg-full-self-healing-setup.md`, with the healer script embedded verbatim (diffed identical to `~/.local/bin/ensure-ffmpeg-full`). Fixed `ffmpeg-skill-carry-forward-guide.md` §1, which had said there was "nothing to redo". |
| **PR #319** | Worktree `ffmpeg-skill-wt-readme`, branch `pr/macos-ffmpeg-full-link`, commit `f87345e`. Touches `README.md`, `bin/install.js`, `scripts/_common/runner.py`, `scripts/_contract.py`, and `tests/test_contract.py` (new test). The user pushed; I opened it. Merged 2026-10-11 as `e51e18a` and released in v2.8.2. |
| **Bench harness and results** | Fork branch `bench/asr-parakeet-vs-whisper` (worktree `ffmpeg-skill-wt-bench`). `bench/asr/{pick_clips,prep,run,score,mc0}.py`, plus results for `m4-max`, `m4-max-extra`, `m3-air` and `m3-air-mc0`. The M3 results and the `-mc 0` A/B are `7eae948`. The M4 agent added `1d72cb0` (stricter `--configs`). The local branch was fast-forwarded to match origin. |
| **Upstream posts** | Comment on #311 (apology, `test_accel` 54 OK, the real 8K refusal). Issues #317 and #318, PR #319, and the verification comment on #321. |
| **Memory and global config** | Rewrote `codex-model-choice`. Added and updated `upstream-maintainer-expectations`. Reinforced `suite-entry-point` (use a fresh `OUT` every run). Changed `~/.claude/CLAUDE.md` from `gpt-5.6-terra` to `gpt-5.6-luna`. |
| **Verification worktrees** | Added detached worktrees `ffmpeg-skill-wt-pr321` (`25a0ef5`) and `ffmpeg-skill-wt-main282` (`6cfa6c7`). |

## Testing / Research Performed

- **#319:**
  - The new test failed before the fix and passed after.
  - A clean suite run gave `test_all` 847 OK (3 skipped) and `test_contract` 157 OK (1 skipped).
  - It had 1 Codex pass and 3 Opus review passes.
  - Upstream CI: 11 checks passed, 2 skipped.
- **ASR benchmark:** 6 ESB sets (librispeech, ami, earnings22, gigaspeech, voxpopuli, common_voice), about 58 minutes of speech in total. Five configurations, with 1 warm-up and 3 timed passes each, on the M3 Air and the M4 Max.
  - **Same transcripts on both machines:** all 30 SRTs are byte-identical across the two Macs, and the WAV sha256 values match (noted in `7a1fce2`).
  - **Word-weighted WER:**
    - whisper.cpp base 19.87, small 17.07, large-v3-turbo 69.12 (two loops);
    - parakeet-mlx v2 14.73, parakeet.cpp v2 14.25.
  - **RTFx** (M4 / M3):

    | config | M4 Max | M3 Air |
    |---|---|---|
    | whisper.cpp base | 92.6× | 47.4× |
    | whisper.cpp small | 54.7× | 21.4× |
    | whisper.cpp large-v3-turbo | 32.1× | 7.5× |
    | parakeet-mlx v2 | 108.5× | 29.4× |
    | parakeet.cpp v2 | 140.9× | 40.2× |

  - **`-mc 0` A/B on the M3:** WER drops to 18.33 for base, 15.42 for small and 12.52 for turbo, and both turbo loops disappear.
    - The loops: earnings22 293× from 07:12, and common_voice 303× from 03:58 to 11:14.
  - **Parakeet v3** (M4 only, extra run): 27.54 for mlx and 32.96 for cpp, mostly deletions.
  - **Timing check:** confirmed the `-mc 0` run didn't overlap the main M3 run (22:51:01 end vs 22:52:27 start).
- **#318 draft:**
  - Checked by Codex (luna xhigh), whose verdict was FIX. Every table value was correct; the wording fixes were applied after each was checked.
  - My own re-checks found that the A/B's "as is" SRTs match the main run in text but not in bytes (the skill strips leading spaces). I also dropped the base-loop claim.
- **#321 verification:**
  - Full suite on `25a0ef5`: `test_all` 867 OK (3 skipped), `test_contract` 161 OK (1 skipped). `tests/_fixtures.py` removes `FFMPEG_SKILL_HW`, so the user's environment didn't affect it.
  - **Real lean link:**
    - v2.8.2: doctor `NOT ok`, with drawtext, subtitles and vidstab missing. `graphics.py` drawtext fails with `No such filter: 'drawtext'`, and the fix hint wrongly says "drawtext crashed".
    - #321: doctor `ok` (69 capabilities), with `ffmpeg_source: homebrew-ffmpeg-full`. The render succeeds, and a frame was checked by eye.
  - **Controls:** ffmpeg-full linked, `opt/ffmpeg-full/bin` first on PATH, and a lean binary via a wrapper outside any Cellar all give `source: "path"`.
  - **Restore:** after `ensure-ffmpeg-full`, doctor is `ok` with `source: path`.
  - **Codex:** a code review (FIX: 1 Major, 4 Minor, each verified; only the doc contradiction was kept). The reply's fact-check came back FIX, and the second pass SHIP.
- **Maintainer research:**
  - Read all of kajisho5's comments on the user's PRs.
  - All 40 of their recent PRs carry claude.ai/code session links.
  - #143 and their comments say they have no Windows machine in their environment, and they ask contributors for hardware checks.

## Discoveries / Handoff Notes

- **The maintainer works through Claude Code on the web (cloud Linux).** Real Mac and Windows checks come from contributors. Report exact commands, the machine, PATH state and pasted output, and keep simulated results apart from real ones. What hardware they own personally is unknown.
- **On #321, `_homebrew_full_build` decides from the binary's real path.** A PATH directory of symlinks into `Cellar/ffmpeg/` therefore exercises the same code as a real `brew link`. That's useful for safe simulation.
- **`whisper-cli` keeps a leading space on each cue line; the skill strips it.** Compare cue text, not bytes, when matching raw whisper output against the skill's output.
- **The user's shell exports `FFMPEG_SKILL_HW=1`.** The test suite removes it, but hand-run tools pick VideoToolbox.
- **A monitor's `pgrep -f` pattern can match its own command line** and give false "not started" or "still running" results.
- **`select.py` broke `subprocess`** because it shadows the stdlib `select` module. Never name bench files after stdlib modules.

## Current State

- **Main checkout:** on `m-series-hw-parakeet` (`59b2c4e`). `CLAUDE.local.md` is untracked, as before this session. This summary is the session's only change in this checkout.
- **Worktrees:**
  - `ffmpeg-skill-wt-bench` at `1d72cb0`, matching origin;
  - `ffmpeg-skill-wt-readme` at `f87345e` (#319, merged);
  - `ffmpeg-skill-wt-pr321` and `ffmpeg-skill-wt-main282`, both detached.
- **Homebrew:** `ffmpeg` links to ffmpeg-full again (restored and checked).
- **Upstream:** at `6cfa6c7` (v2.8.2).

## Issues & PRs

- https://github.com/kajisho5/ffmpeg-skill/pull/319: macOS keg-only install hints (the user's). Merged into v2.8.2.
- https://github.com/kajisho5/ffmpeg-skill/issues/317: find keg-only ffmpeg-full automatically. Open; implemented by #321.
- https://github.com/kajisho5/ffmpeg-skill/pull/321: the maintainer's resolver. Verification posted at https://github.com/kajisho5/ffmpeg-skill/pull/321#issuecomment-6113231741
- https://github.com/kajisho5/ffmpeg-skill/issues/318: the ASR benchmark and the `-mc 0` finding. Open, no reply yet.
- https://github.com/kajisho5/ffmpeg-skill/pull/311#issuecomment-6093159622: the apology and the `test_accel` and 8K results. The maintainer replied: "No need to apologise…"
- #320 (the maintainer's) was closed in favour of #319.

## Summary Statistics

| | |
|---|---|
| Upstream posts | 5: 2 issues, 1 PR, 2 comments. |
| Codex (luna xhigh) passes | 4 since the correction to luna: #318 draft, #321 code, #321 reply, reply pass 2. Plus 4 terra runs earlier, before the usage limit. |
| Full test-suite runs reported | 2: #319, and #321 at `25a0ef5`. |
| Benchmark | 2 machines; 6 sets × 5 configs, plus a 2-config v3 run and an 18-cell `-mc 0` A/B. |

## Unfinished Work

- **Wait for the maintainer** on #318 (whether `-mc 0` becomes the default or opt-in) before sending a PR, and on #321 (merge, or a response to the "no paths" doc point).
- **After #321 merges:**
  - remove the worktrees `ffmpeg-skill-wt-pr321`, `ffmpeg-skill-wt-main282` and `ffmpeg-skill-wt-readme`;
  - delete the fork branch `pr/macos-ffmpeg-full-link` if wanted.
- **Reinstall the skill from the latest release.** An earlier check in this session found the installed copy at 2.3.1. The 2.8.2 in this session's doctor output came from running in the worktrees.
- **Retire the `m-series-hw-parakeet` branch**, now that #311 and #312 have landed upstream.
- **Optional:** the `.m4v` `--help` doc gap noted earlier.
