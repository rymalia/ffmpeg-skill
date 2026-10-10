---
session_id: b4b20b84-0002-46df-bae4-9dbe17f2efb8
date: 2026-10-09
time: "7:21 PM PDT – 7:33 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary — ffmpeg-full self-healing setup

### Overview

Today's Homebrew upgrade had relinked the lean `ffmpeg` 9.0.2_1 over `ffmpeg-full`, which removed `drawtext`, `subtitles` and `ass`. The self-healing setup had never been installed on this Mac. Following `docs/plans/ffmpeg-full-self-healing-setup.md`, I installed the healer script and the `brew()` wrapper, relinked `ffmpeg-full`, and checked the result, including a deliberate break-and-repair test.

### Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Edited `~/.zshrc` directly** | `ls -la` showed it is a regular file, not a dotfiles symlink, so there was no source repo to edit instead. |
| **Backed up `~/.zshrc` first** (`~/.zshrc.bak-ffmpeg-full`) | It's a cheap way to undo the change to a personal shell config. |
| **Left `~/.zshenv` unchanged** | `~/.local/bin` was already on PATH (Step 0 output). |
| **Kept the lean `ffmpeg` installed** | Following the runbook: other formulae depend on it. It is now unlinked. |
| **Ran the optional end-to-end test** | It confirms the wrapper repairs a real relink, not just that the script runs. |

### Changes Made

| Change | Detail |
|--------|--------|
| **Healer script** | Created `~/.local/bin/ensure-ffmpeg-full`, copied exactly from the runbook, and ran `chmod +x`. |
| **brew() wrapper** | Added it to the end of `~/.zshrc`. It runs the healer after `upgrade/install/reinstall/link/unlink/uninstall`. |
| **Backup** | Saved `~/.zshrc.bak-ffmpeg-full`, a copy of the file before the edit. |
| **Homebrew links** | Unlinked the lean `ffmpeg` and force-linked `ffmpeg-full` 9.0.2 (done by the healer). |

No files in the repo were changed by this session, apart from this summary.

### Testing / Research Performed

- **Step 0 (before):** arm64, `/opt/homebrew/bin/brew`. Installed: `ffmpeg 9.0.2_1`, `ffmpeg-full 9.0.2` and `ffmpeg@7 7.1.5_3`. `ffmpeg` resolved to `../Cellar/ffmpeg/9.0.2_1/bin/ffmpeg`, and the text filter count was **0**. No healer or wrapper existed.
- **Syntax:** `zsh -n ~/.zshrc` passed (SYNTAX OK).
- **Repair:** the first healer run printed both relink messages. The second run printed nothing and exited 0, which confirms it is idempotent.
- **Step 5:** `ffmpeg` resolves to `../Cellar/ffmpeg-full/9.0.2/bin/ffmpeg`, and the filter count is **3**. `type brew` in an interactive shell reports "brew is a shell function from /Users/rymalia/.zshrc". The skill's doctor printed `True yes` (`ok`, caption usable).
- **End-to-end:** ran `zsh -ic 'brew unlink ffmpeg-full; brew link ffmpeg; readlink …'`. The wrapper repaired the link twice, once after each mutating command. The `unlink` left no `ffmpeg` on PATH, so the healer relinked then too. Both the inner and outer `readlink` showed `ffmpeg-full`, and the filter count stayed at 3.

### Summary Statistics

- Files created outside the repo: 2 (the healer script and the `.zshrc` backup). Files edited: 1 (`~/.zshrc`).
- Verification checks run: 7 (syntax, idempotency, readlink, filter count, wrapper type, doctor, end-to-end).

### Discoveries / Handoff Notes

- The carry-forward guide had told agents this section was "already set up here", so the setup was skipped on this machine until the upgrade on 2026-10-09 exposed it. The guide was corrected before this session.
- The healer also repairs things when **no** `ffmpeg` is linked at all (an empty `command -v`), not only when the lean build is linked.
- The wrapper only loads in interactive zsh. After an agent or script runs `brew upgrade` or `brew install`, run `ensure-ffmpeg-full` by hand.

### Current State

- `ffmpeg` points to `ffmpeg-full` 9.0.2, and the `drawtext`, `subtitles` and `ass` filters are available.
- Untracked files in the repo, all present before this session: `CLAUDE.local.md`, `docs/plans/ffmpeg-full-self-healing-setup.md` and `docs/plans/ffmpeg-skill-carry-forward-guide.md`.

### Unfinished Work

None. Optional: once you're happy with the change, delete `~/.zshrc.bak-ffmpeg-full`.
