---
title: Self-healing ffmpeg-full setup (agent runbook)
date: 2026-10-09
applies_to: any Apple Silicon or Intel Mac using Homebrew ffmpeg ≥ 8
source_machine: ryan-M3-MacBook-Air (set up 2026-09-19, confirmed working on a real `brew upgrade` 2026-10-09)
---

# Self-healing ffmpeg-full setup — agent runbook

**Audience:** a coding agent (Claude Code, Codex) on a Mac where `ffmpeg` does not point to
`ffmpeg-full`. Follow the steps in order. Every step can be run again safely. Report what you
found and what you changed at the end.

**Goal:** the bare `ffmpeg` on PATH is Homebrew's `ffmpeg-full`, and it goes back to being
`ffmpeg-full` after every `brew upgrade` without anyone having to do anything.

## Why this is needed

- Homebrew split ffmpeg at v8. The plain `ffmpeg` formula is now a **lean** build: no
  freetype, libass, fontconfig or harfbuzz, so it has **no `drawtext`, no `subtitles` and no `ass`
  filter**. ffmpeg-skill's `caption.py`, `graphics.py` and other tools need those filters.
- The full build is `ffmpeg-full`. It is **keg-only**, so `brew install ffmpeg-full` alone does not
  put it on PATH. We force-link it over the lean one.
- Keep the lean `ffmpeg` installed (other formulae such as `ocrmypdf`, `unpaper` and `vhs` depend on
  it), but **unlinked**.
- **Every `brew upgrade` that updates the lean `ffmpeg` links it back over `ffmpeg-full`.** This
  happens every time, and nothing warns you. Homebrew has no per-formula post-upgrade hook, so the
  fix has two parts:
  1. `~/.local/bin/ensure-ffmpeg-full` is an idempotent healer. It does nothing and prints nothing
     when things are already correct.
  2. A `brew()` function in `~/.zshrc` runs the healer after any brew command that changes what is
     linked.

## Step 0 — Look at the current state (change nothing yet)

```sh
uname -m; command -v brew
brew list --versions ffmpeg ffmpeg-full ffmpeg@7
readlink "$(command -v ffmpeg)"            # want: …/Cellar/ffmpeg-full/<ver>/bin/ffmpeg
ffmpeg -hide_banner -filters 2>/dev/null | grep -cE ' (drawtext|subtitles|ass) '   # want: 3
ls -la ~/.local/bin/ensure-ffmpeg-full 2>&1
grep -n 'ensure-ffmpeg-full' ~/.zshrc ~/.zshenv ~/.zprofile 2>/dev/null
echo "$PATH" | tr ':' '\n' | grep -n 'local/bin'
```

Write down what you see. If the healer and wrapper both exist already, skip to Step 5 and work out
why they didn't fire (most likely the upgrade ran in a non-interactive shell; see "Limits").

If `~/.zshrc` is a symlink or is managed by a dotfiles repo, edit the source file in that repo, not
the symlink.

## Step 1 — Install ffmpeg-full if it is missing

```sh
brew list ffmpeg-full >/dev/null 2>&1 || brew install ffmpeg-full
```

Don't uninstall the lean `ffmpeg`. If you're ever tempted to, check dependents **one formula at a
time**. `brew uses --installed a b` returns the *intersection*, not the union, so a combined query
can come back empty even when real dependents exist:

```sh
brew uses --installed ffmpeg
```

## Step 2 — Create the healer script

Make sure `~/.local/bin` exists and is on PATH (Step 0 shows this). If it isn't on PATH, add
`export PATH="$HOME/.local/bin:$PATH"` to `~/.zshenv`.

Write this file **exactly** to `~/.local/bin/ensure-ffmpeg-full`, then `chmod +x` it:

```bash
#!/usr/bin/env bash
# ensure-ffmpeg-full — keep Homebrew's full-featured `ffmpeg-full` as the active `ffmpeg`.
#
# Why this exists:
#   Homebrew split ffmpeg at v8. The plain `ffmpeg` formula is now "lean" (no
#   libfreetype/libass/fontconfig/harfbuzz -> no drawtext, no subtitles). The full
#   build lives only in `ffmpeg-full`, which is keg-only. We force-link ffmpeg-full
#   so bare `ffmpeg` has the text/subtitle stack. But `brew upgrade` relinks the lean
#   `ffmpeg` on top every time it updates it, silently breaking drawtext again.
#
# This script re-establishes ffmpeg-full as the active `ffmpeg`. It is idempotent and
# safe to run any time: it does nothing (and prints nothing) when already correct, or
# when ffmpeg-full is not installed.
#
# Added 2026-09-19.
set -euo pipefail

# Locate brew regardless of PATH state (Apple Silicon or Intel).
if command -v brew >/dev/null 2>&1; then
  BREW="$(command -v brew)"
elif [ -x /opt/homebrew/bin/brew ]; then
  BREW=/opt/homebrew/bin/brew
elif [ -x /usr/local/bin/brew ]; then
  BREW=/usr/local/bin/brew
else
  exit 0   # no Homebrew here; nothing to do
fi

# If ffmpeg-full isn't installed, there is nothing to enforce.
if ! "$BREW" --prefix ffmpeg-full >/dev/null 2>&1; then
  exit 0
fi

# Is the active `ffmpeg` already the full build? Resolve the symlink and look for the
# ffmpeg-full keg in the path (version-agnostic, no ffmpeg process spawned).
active="$(command -v ffmpeg 2>/dev/null || true)"
if [ -n "$active" ]; then
  # realpath via a portable readlink loop (macOS /usr/bin/readlink has no -f).
  resolved="$active"
  while [ -L "$resolved" ]; do
    target="$(readlink "$resolved")"
    case "$target" in
      /*) resolved="$target" ;;
      *)  resolved="$(cd "$(dirname "$resolved")" && cd "$(dirname "$target")" && pwd)/$(basename "$target")" ;;
    esac
  done
  case "$resolved" in
    */ffmpeg-full/*) exit 0 ;;   # already correct
  esac
fi

# Re-establish ffmpeg-full as the linked `ffmpeg`.
echo "ensure-ffmpeg-full: relinking ffmpeg-full over the lean ffmpeg..." >&2
"$BREW" unlink ffmpeg >/dev/null 2>&1 || true   # lean ffmpeg may be absent/unlinked
"$BREW" link --overwrite --force ffmpeg-full >/dev/null
echo "ensure-ffmpeg-full: done — 'ffmpeg' now points to ffmpeg-full." >&2
```

How it works:

- It decides by checking whether the resolved path contains `/ffmpeg-full/`. That works for any
  version and never starts an `ffmpeg` process.
- It resolves symlinks with a manual loop because macOS `/usr/bin/readlink` has no `-f`.
- It does nothing when `ffmpeg-full` isn't installed, so it's safe on any machine.

## Step 3 — Add the `brew()` wrapper to `~/.zshrc`

Add this only if `grep -q 'ensure-ffmpeg-full' ~/.zshrc` finds nothing, so the block never gets
added twice. Put it near the end of the file:

```zsh
# Keep ffmpeg-full as the active `ffmpeg`. It is keg-only, and `brew upgrade` relinks
# the lean `ffmpeg` formula on top whenever it updates it, silently dropping drawtext/
# subtitles. This wrapper re-heals after any mutating brew command via the idempotent
# ~/.local/bin/ensure-ffmpeg-full script.
brew() {
  command brew "$@"
  local _brew_status=$?
  case "$1" in
    upgrade|install|reinstall|link|unlink|uninstall)
      ensure-ffmpeg-full
      ;;
  esac
  return $_brew_status
}
```

The wrapper returns brew's own exit status. Read-only commands such as `brew list` don't trigger
the healer.

Check the syntax: `zsh -n ~/.zshrc && echo OK`.

## Step 4 — Heal now

```sh
~/.local/bin/ensure-ffmpeg-full
```

If it was broken, this prints the two `ensure-ffmpeg-full:` lines. Run it again and it should print
nothing, which shows it's idempotent.

## Step 5 — Verify

```sh
readlink "$(command -v ffmpeg)"            # contains /ffmpeg-full/
ffmpeg -hide_banner -filters 2>/dev/null | grep -cE ' (drawtext|subtitles|ass) '   # 3
zsh -ic 'type brew' | head -1              # "brew is a shell function"
```

If ffmpeg-skill is installed, also run its doctor. The installed copy is usually at
`~/.agents/skills/ffmpeg-skill` or `~/.claude/skills/ffmpeg-skill`:

```sh
python3 ~/.agents/skills/ffmpeg-skill/scripts/_contract.py doctor --json 2>/dev/null | python3 -c \
  'import json,sys; d=json.load(sys.stdin); print(d["ok"], d["tools"]["caption"]["usable"])'
# want: True yes
```

There is no `doctor.py`. `doctor` is a subcommand of `_contract.py`, or run
`npx ffmpeg-skill doctor`. You want `filter:drawtext`, `filter:subtitles` and `filter:ass` to show
as available, and `caption` to be usable.

**Optional end-to-end test** (it changes what's linked for a moment, then repairs it). Run it in
an interactive shell so the wrapper loads:

```sh
zsh -ic 'brew unlink ffmpeg-full >/dev/null; brew link ffmpeg >/dev/null; readlink "$(command -v ffmpeg)"'
# the wrapper's heal messages should appear, and the readlink line should already show ffmpeg-full
readlink "$(command -v ffmpeg)"
```

## Limits (tell the user about these)

- **The wrapper only exists in interactive zsh.** Scripts, cron, launchd jobs and some agent shells
  never load `.zshrc`. If brew was changed from one of those, run `ensure-ffmpeg-full` by hand
  afterwards. Agents: if you run `brew upgrade` or `install` yourself, run
  `ensure-ffmpeg-full` straight after it.
- **`brew doctor` may warn** about the force-linked keg-only `ffmpeg-full`. That's expected and
  harmless.
- **`ffmpeg-full` always tracks the latest major version, and there is no `ffmpeg-full@N`.**
  `ffmpeg@7` was the last all-in-one versioned formula. Keep it if a pinned full build is ever
  needed.

## Report back

Tell the user:

- what Step 0 showed;
- which files you created or edited (the script, `~/.zshrc` or its dotfiles source, and
  `~/.zshenv` if you changed PATH);
- whether the heal ran;
- the results from Step 5.

Never run `git push`.
