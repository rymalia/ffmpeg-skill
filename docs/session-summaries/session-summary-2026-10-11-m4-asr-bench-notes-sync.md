---
session_id: b4b20b84-0002-46df-bae4-9dbe17f2efb8
date: 2026-10-11
time: "2026-10-09 7:21 PM PDT – 2026-10-11 2:32 PM PDT"
resumed: "2026-10-11 1:54 PM PDT, 2026-10-11 2:22 PM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: M4 Max ASR benchmark, `--configs` hardening and syncing this Mac to 2.8.2

## Overview

This session ran on the M4 Max. It is the M4 side of the work recorded in the M3's
`session-summary-2026-10-11-upstream-prs-asr-bench.md`.

- **ffmpeg-full self-healing setup** (2026-10-09): installed. It has its own summary,
  `session-summary-2026-10-09-ffmpeg-full-self-healing.md`.
- **ASR benchmark:** picked up from the baton and ran on this machine. The `m4-max` run is
  pinned and comparable with the M3. The `m4-max-extra` run adds Parakeet v3.
- **Harness:** gained an opt-in `--configs` flag, which was then hardened after review.
- **Issue #314:** assessed, and a reply drafted. The user put both on hold, and nothing was
  posted.
- **This Mac synced to the M3's new layout:**
  - the self-healing docs carried onto `notes`;
  - local `main` moved to v2.8.2, and the skill reinstalled from it;
  - the retired `m-series-hw-parakeet` branch deleted.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Ran the bench in the main checkout, not the baton's worktree** | The user asked to switch to the branch. The branch was tracking `origin`, as the baton required. |
| **Built the data while the Mac was on battery, but timed only on AC** | `prep.py` doesn't depend on power. The baton requires AC for timing. The user plugged in before the timed run started. |
| **Added `--configs` + `EXTRA_CONFIGS` instead of editing `CONFIGS`** | The user wanted a Parakeet v3 run. Editing `CONFIGS` would have changed the rotation order, so the M4 results would no longer compare with the M3's. With the flag off, a run is unchanged. |
| **Queued the extra run behind the main run's PID** | Two timed runs must never overlap. |
| **Scored only after both runs had finished** | Scoring is CPU work, and it would have disturbed the extra run's timings. |
| **Reported the large-v3-turbo loops and the parakeet-mlx word splits; changed nothing** | Both are real skill output, so the scorer is right to count them. |
| **Hardened `--configs` after an Opus review** | The review found that `--configs ""` silently started the full run, that duplicates doubled their samples, and that a run with no usable config crashed with ZeroDivisionError. All three are cheap to fix. |
| **Rebased the one local commit onto the M3's commits instead of merging** | It had never been pushed, and a rebase keeps the history linear. |
| **Turned down widening `$FFMPEG_SKILL_HW` to export presets in the #314 assessment** | Keeping delivery presets off VideoToolbox was a deliberate choice in #311 (VT needs about 1.2–2.5× the bytes). Using VT automatically only when the CPU encoder is missing respects that choice. |
| **Codex model rule: `gpt-5.6-luna` (high/xhigh) or `gpt-6-luna` (high only)** | Set by the user. `gpt-6-luna` costs too many tokens at xhigh. `~/.codex/config.toml` keeps `gpt-6-sol`. |
| **Left the bench branch on its 2.8.0 base** | Its `machine.json` files record the skill commits they ran on (`35bba62`, `7072293`). A rebase would change those commits. |
| **Cherry-picked onto `notes` before deleting `m-series-hw-parakeet`** | 3 files from this session existed only in that branch's 2 unpushed commits. |

## Changes Made

| Change | Detail |
|--------|--------|
| **Plan docs committed** | `2b36fe3` (later cherry-picked to `notes` as `6d378df`). The 10-09 summary was `da398dd` (cherry-picked to `notes` as `1eaf5a7`). |
| **Bench data** | `uv run bench/asr/prep.py` built the 6 WAVs in `bench/asr/data/` (git-ignored). |
| **`m4-max` results** | `7a1fce2`: `machine.json`, `timings.jsonl`, 30 SRTs, `report.md`, `summary.json`. |
| **`--configs` flag** | `7072293`: `EXTRA_CONFIGS` with `parakeet-mlx-v3` (`mlx-community/parakeet-tdt-0.6b-v3`) and `parakeet.cpp-v3` (absolute `.gguf` path), plus a README note. |
| **`m4-max-extra` results** | `bb2c971`: Parakeet v3, 48 rows. |
| **`--configs` hardening** | `6b1b4d5`, rebased to `1d72cb0`. An empty value is an error. Names are trimmed and deduplicated. When nothing can run, the script exits before `out.mkdir`. |
| **Rebase** | `git pull --rebase` put `1d72cb0` on top of the M3's `04f4d88` (battery stop, caffeinate) and `7eae948` (M3 results, `mc0.py`). The user pushed. |
| **`~/.claude/CLAUDE.md`** | The Subagent Model Choice entry now names luna instead of terra, with the `gpt-6-luna` high-only rule and the instruction to leave `config.toml` unchanged. |
| **`notes` branch** | Created locally from `origin/notes`, with `1eaf5a7` and `6d378df` cherry-picked on top. The user pushed. |
| **`main` and installed skill** | `main` fast-forwarded to `6cfa6c7` (v2.8.2). `node bin/install.js --codex` refreshed `~/.agents/skills/ffmpeg-skill`. The `~/.claude/skills` symlink is intact. |
| **Branch deleted** | Local `m-series-hw-parakeet` (`2b36fe3`). Fetched the tag `archive/m-series-hw-parakeet` (`869a223`). |

## Testing / Research Performed

- **Data integrity:** all 6 sets matched the baton's clip counts and the first 16 hex
  characters of their sha256 (FFmpeg 9.0.2 on both machines).
- **Runs:**
  - `m4-max`: 120 rows (4 passes × 6 sets × 5 configs), with no `exit` errors and no
    skipped configs.
  - `m4-max-extra`: 48 rows, no errors.
- **Results** (word-weighted WER, RTFx):

  | config | WER | RTFx |
  |---|---|---|
  | whisper.cpp base | 19.87% | 92.6× |
  | whisper.cpp small | 17.07% | 54.7× |
  | whisper.cpp large-v3-turbo | 69.12% | 32.1× |
  | parakeet-mlx v2 | 14.73% | 108.5× |
  | parakeet.cpp v2 | 14.25% | 140.9× |
  | parakeet-mlx v3 | 27.54% | 101.0× |
  | parakeet.cpp v3 | 32.96% | 139.4× |

- **Anomalies checked:**
  - **large-v3-turbo loops:** one line repeated 293× on earnings22 (WER 188.76%) and
    another 303× on common_voice (231.7%).
  - **Per-set durations:** they exclude the 0.75 s gaps between clips (ami: 381 × 0.75 s
    ≈ 4.8 min), so they're shorter than `prep.py`'s figures.
  - **Word splits:** a heuristic found about 28 (v2) and 20 (v3) words split across cue
    boundaries, in parakeet-mlx output only.
- **`--configs` checks:**
  - `available()` resolves both v3 configs.
  - Before hardening, an unknown name exited before any results folder was created.
  - After hardening:
    - `""` and `" , "` give `--configs is empty`;
    - a duplicate- and space-laden list collapses correctly;
    - a patched copy whose v3 `.gguf` didn't exist exited 1 without creating
      `results/zz-test/`.
  - After the rebase: `py_compile` passed, the same error messages appeared, and
    `import mc0` worked.
- **Reviews:**
  - **Opus subagent** on `7072293`: no real bug, and 3 minor edge cases, all fixed.
  - **Codex `gpt-5.6-luna` xhigh** on `1d72cb0`: SHIP, no findings. Its run left no stray
    files.
- **Merge checks:** `git merge-tree` was clean against both `04f4d88` and `7eae948`. Only
  `run.py` was changed on both sides, in separate hunks.
- **#314:** read the issue and checked each claim against v2.8.0:
  - `decision.py:340` (`_maybe_hw`);
  - `export.py:62,68,77`;
  - `runner.py` env handling;
  - `_contract.py:61`.
- **Install check:** 59 of 59 installed files under `scripts/` plus `SKILL.md` were
  byte-identical to the repo. Doctor: `ok: True`, captions usable.
- **Upstream status check (2026-10-11):**
  - `upstream/main` still at `6cfa6c7`.
  - #321 gained `b00a0ce` and a maintainer reply accepting the `docs/contract.md`
    paths point. I read the diff.
  - #314, #317 and #318 have no comments.

## Discoveries / Handoff Notes

- The M3 and M4 SRTs are byte-identical, so only speed differs between machines. The
  `-mc 0` A/B (`7eae948`) fixes the turbo loops (overall WER 12.52%).
- Python compiles a script when it starts, so editing `run.py` while a run is in progress
  doesn't affect that run. That's how `--configs` was added mid-run.
- In zsh, `echo ======` fails with `= not found` (`=word` expansion), which can make a
  command chain exit 1.
- `bench/asr/data/` and `.cache/` show as untracked on branches other than the bench
  branch, because only that branch's `.gitignore` covers them.
- **#314 context:** VideoToolbox-only ffmpeg builds come from LGPL ffmpeg bundled in
  closed-source Mac apps. x264/x265 are GPL. VideoToolbox is a system framework, so it has
  no licensing issue.

## Current State

- **Main checkout:** `notes`, in sync with `origin/notes`. `CLAUDE.local.md` is untracked,
  as before.
- **Local branches:**
  - `notes`;
  - `main` at v2.8.2;
  - `bench/asr-parakeet-vs-whisper` at `1d72cb0`, the same as origin.
- **Installed skill:** 2.8.2. **Homebrew:** `ffmpeg` resolves to ffmpeg-full.
- **#321:** still a draft and mergeable. The user added a 👍 reaction and no comment.

## Unfinished Work

- **#314:** on hold at the user's request. My assessment and draft reply exist only in
  this conversation; nothing was posted.
- **Wait for the maintainer** to merge #321 and to answer #318 on `-mc 0`. The M3 summary
  lists the cleanup that follows.
- **Optional:** delete the old remote branch from the fork with
  `git push origin --delete m-series-hw-parakeet`. `git ls-remote` shows the branch still
  there at `59b2c4e`. The tag `archive/m-series-hw-parakeet` is already on the fork and
  contains that tip, so deleting the branch loses nothing.
