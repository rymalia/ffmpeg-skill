---
session_id: 1a28d11f-897d-45f7-81f4-8a5a9bafa34f
date: 2026-09-27
time: "3:58 PM PDT – 4:15 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: setup inventory and second-Mac handoff

## Overview

The user is replicating the ffmpeg-skill VideoToolbox + Parakeet setup on a second
MacBook. This session wrote two documents, checked against the live machine: a full
inventory of every install and file change on this M4 Max, and a step-by-step handoff for
the agent on the other machine. They were committed as `8c00dfb` and pushed to the fork.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Checked the live machine instead of only restating the two earlier summaries** | The handoff has to be exact. The session read versions, file sizes and SHA-256 hashes, the wrapper script text, `~/.zshenv`, the skill symlink, and the download URLs and commands recorded in the earlier session's transcript (`c5ed860f…jsonl`). |
| **Labelled each model as required or optional, based on the code** | `scripts/_common/asr.py` detects language with the smallest installed of tiny/base/small, and `caption.py --model` defaults to `large-v3-turbo`, so those two whisper models are required. `small`/`small.en` and the Parakeet v3 files were only used for benchmarks, and skipping them saves about 5 GB on the second machine. |
| **The handoff installs the parakeet.cpp binaries directly into `~/.local/libexec/`, with wrappers in `~/.local/bin`** | On the first machine they went into `~/.local/bin` first and were moved later. The handoff goes straight to the final layout. |
| **The handoff clones the existing fork instead of forking again** | `rymalia/ffmpeg-skill` already exists. The handoff sets up `upstream` with a `DISABLED` push URL and checks that the branch tracks `origin`, following the user's fork-only rule. |
| **Checked every CLI flag in the handoff's verification steps before finalising** | `doctor --json` keys (`ok`, `hw`, `missing`), `fit.py --height/--json/--hw/--no-hw` and `caption.py --transcribe/--engine` were confirmed against the installed tools. |
| **Left `CLAUDE.local.md` out of the commit** | It holds the user's local instructions for Claude, not project content. |
| **Removed the accidental `/replay` output by rewriting local history, not adding a revert** | The user had meant `/session-tools:session-summary`. The replay commit `038131f` was unpushed, so `git reset HEAD~1` plus deleting the file removed it cleanly. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`docs/setup/m4-max-setup-inventory-2026-09-27.md`** (new) | Tools that were already installed, with versions; fork/remotes/branch and the 22 files in `3ff6462`; whisper.cpp and parakeet.cpp models with URLs, byte sizes and SHA-256; the parakeet-mlx 0.5.2 install; parakeet.cpp v0.5.0 binaries (hashes), wrappers and GGUFs; `~/.zshenv` additions; the skill layout; reference benchmark numbers. |
| **`docs/setup/HANDOFF-replicate-on-second-mac.md`** (new) | Ground rules (no commits, no upstream push, no re-fork, no `npx ffmpeg-skill`, look before overwriting), then steps 0–9: check current state, prerequisites, clone and remotes, whisper models, parakeet-mlx, parakeet.cpp with the full wrapper text, `~/.zshenv`, `install.js --codex` plus the relative symlink, verification (doctor, a GPU encode, the three speech engines, the optional test suite), and the report back to the user. |
| **Commit `8c00dfb`**, pushed | `49e08f9..8c00dfb` to `origin/m-series-hw-parakeet`, at the user's request. `CLAUDE.local.md` in the repo authorises agent commits. |
| **Replay created, then removed** | `docs/replay-1a28d11f.md` was committed as `038131f` and not pushed. At the user's request it was reset out of the history and the file deleted. |
| **This summary** | `docs/session-summaries/session-summary-2026-09-27-second-mac-handoff.md` |

## Testing / Research Performed

- **Machine state read directly:** `git remote -v`, the branch and log; `~/.zshenv`; `ls -la`
  of the skill paths, `~/.cache/whisper.cpp`, `~/.cache/parakeet.cpp`,
  `~/.local/libexec/parakeet.cpp` and `~/.local/bin/parakeet*`; the wrapper script contents;
  `brew list --versions`; `uv tool list`; `parakeet-cli --version` (0.5.0) and
  `parakeet-mlx --help` (v0.5.2); the Hugging Face cache listing.
- **Provenance:** grepped the earlier session's transcript for the `curl`, `uv tool install`,
  `gh repo fork`, `git remote set-url` and `install.js` commands and URLs.
- **Integrity:** SHA-256 of both parakeet.cpp binaries, the v2 GGUF, and the base and
  large-v3-turbo whisper models. `otool -L` showed the parakeet.cpp binaries link only
  system libraries.
- **Installed skill vs repo:** `diff -rq` on `scripts/` (only a `.DS_Store` differs) and
  `diff -q` on `SKILL.md` (they match).
- **Flag checks:** `_contract.py doctor --json` returned `ok True`,
  `hw {default_on: True, platform_ok: True}` and `missing []`. The `fit.py --help` and
  `caption.py --help` flags matched the handoff.
- **CHANGELOG check (user question):** `## Unreleased` already has the VideoToolbox and
  Parakeet entries from `3ff6462`. The commits after it are docs-only, so nothing needed
  adding.
- The handoff has **not** been run on the second machine.

## Summary Statistics

- New docs: 2 (committed in `8c00dfb`, pushed); 1 replay created and then removed (unpushed)
- Artifacts hashed: 5 (2 binaries, 1 GGUF, 2 whisper models)
- Commits pushed this session: 1

## Discoveries / Handoff Notes

- `~/.local/bin/parakeet` (a May 2026 Mach-O binary that takes `.safetensors`) predates this
  work and is unrelated to the skill. The handoff says to leave it alone.
- The Hugging Face cache also holds unrelated Parakeet CoreML models (FluidInference,
  aufklarer). Only `mlx-community/parakeet-tdt-0.6b-v2` matters to the skill.
- Only the parakeet.cpp `bin` release tarball is needed. The `lib` tarball was downloaded on
  the first machine but isn't used.
- Changelog practice for this branch: add or amend an `Unreleased` entry in the same commit
  as any change to behaviour, flags, result keys or defaults. Docs-only commits get no entry.

## Current State

- Branch `m-series-hw-parakeet` at `8c00dfb`, in sync with `origin/m-series-hw-parakeet`
  (before this summary is committed).
- Untracked: `CLAUDE.local.md` (deliberately not committed).

## Unfinished Work

- Run `docs/setup/HANDOFF-replicate-on-second-mac.md` on the second MacBook and fix the
  handoff if anything differs there.
- Carried over from earlier sessions: rerun the third Codex review pass; an optional
  upstream issue at `kajisho5/ffmpeg-skill`; an optional `--hw` demo; the Reels re-render
  with `--fit blur` / `--crop-x`; a 4K/HDR `--hw` test.
