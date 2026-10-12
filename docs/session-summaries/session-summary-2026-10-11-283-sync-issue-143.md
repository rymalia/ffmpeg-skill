---
session_id: b4b20b84-0002-46df-bae4-9dbe17f2efb8
date: 2026-10-11
time: "2026-10-09 7:21 PM PDT – 2026-10-11 6:16 PM PDT"
resumed: "2026-10-11 1:54 PM PDT, 2026-10-11 2:22 PM PDT, 2026-10-11 2:54 PM PDT, 2026-10-11 6:01 PM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: 2.8.3 sync on the M4, and a close reading of upstream issue #143

## Overview

This summary continues the same session. It covers the work after
`session-summary-2026-10-11-m4-asr-bench-notes-sync.md` (`4b5fd0d`):

- **2.8.3 sync:** checked the user's own 2.8.3 reinstall, and brought `notes` and `main` on
  the M4 up to 2.8.3.
- **Issue #143:** read the maintainer's "real-hands verification" issue closely, with
  everything that references it, and checked their statements against GitHub, npm and the
  repo. I saved the findings to memory and posted nothing upstream.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Fast-forwarded local `main` to `upstream/main`, not `origin/main`** | The fork's `main` was still at 2.8.2. The user wanted `main` to match `notes` (2.8.3). It's a fast-forward, and `main` still tracks `origin`. |
| **Called the "corpus run on macOS" claim unverified, not false** | I found no evidence of it in CI or in the docs, but the maintainer could have run it on a machine this session can't see. |
| **Checked #285's claim against the issue's edit history** | #285 says the editor round trip was "added to #143's checklist". The body text alone couldn't show whether it was ever there and later removed. GraphQL `lastEditedAt: null` settled it. |
| **Counted releases from npm publish times** | Git tags are incomplete (13 tags vs 26 npm versions before #136), so tags can't test the "23 releases" claim. |
| **Added the findings to the existing maintainer memory instead of a new file** | That file already holds what we know about the maintainer. Keeping it in one place avoids duplicates. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`notes` fast-forwarded** | `4b5fd0d` → `37a1ff1` (the M3 session merged upstream 2.8.3 / #321 into `notes`). |
| **`main` fast-forwarded** | `6cfa6c7` → `f1a4f2a` (v2.8.3), 2 ahead of `origin/main`. The user was given `git push -u origin main`. |
| **Memory** | `upstream-maintainer-expectations.md`: #321 merged; the #143 section (its definition of done, the rows the user can supply, the doc drift); the `MEMORY.md` index line updated. |
| **Installed skill** | The user ran `npx ffmpeg-skill@2.8.3 --codex`; I only checked it afterwards. |

## Testing / Research Performed

- **2.8.3 install:**
  - the installed `package.json` says `2.8.3`, and npm's 2.8.3 `gitHead` is `f1a4f2a`;
  - 59 of 59 installed files under `scripts/` plus `SKILL.md` match `notes`;
  - doctor: `ok: True`, `ffmpeg_source: path` (`/opt/homebrew/bin/ffmpeg`).
- **`main`:** after the fast-forward, its `scripts/` and `SKILL.md` are identical to
  `notes`.
- **#143 sources read:**
  - the body and its 1 comment (2026-09-18 acceptance table);
  - the timeline: 6 cross-references (#148, #153, #223, #249, #240, #285) and commit
    `3550c4f`;
  - the text around each mention, including PR bodies and comments;
  - `git grep` of `upstream/main`: README:409, CHANGELOG:337, design-decisions
    :280/:337/:735, roadmap:484/:616, evals iterations 21 and 22.
- **Confirmed:**
  - #100, #111 and #105 have the authors and bugs #143 cites;
  - #136's fix (`~/.codex/skills` → `~/.agents/skills`);
  - the CI matrix includes ubuntu, macos and windows;
  - both `references/*-pitfalls.md` files exist;
  - `render.py --template`/`--cues` exist, and `tiktok` is a template;
  - SKILL.md step 8 is "Look at the picture".
- **Inaccurate or contradicted:**
  - **Editor round trip:** #285 / CHANGELOG:337 / design-decisions:735 say it was "added to
    #143's checklist". The #143 body was never edited and no comment adds it.
  - **Definition of done:** roadmap:616 ("Windows CI corpus job … closes #143") and
    design-decisions:280 ("the corpus run is the criterion") contradict #143's own
    definition, which says CI and maintainer runs don't count and never mentions the corpus.
  - **Release count:** "through 23 releases" vs 26 npm versions (0.1.0–1.0.2) published
    before #136 merged at 2026-09-11 04:08:58Z.
- **Unverified:**
  - README:407 says the corpus "has been run on … macOS", but no CI job or record shows it;
  - #136's statement that Cursor reads `~/.agents/skills` wasn't checked against Cursor's
    documentation.

## Discoveries / Handoff Notes

- **What #143 wants:** each acceptance-table row needs 4 cells: install, a non-ASCII path
  probe, `render.py --template tiktok --cues`, and a reviewed `look.py` sheet. Every cell is
  `not run`, and the maintainer won't fill a cell they didn't measure.
- **The user can supply real rows:**
  - **macOS (plain Homebrew `ffmpeg`):** the #321 A/B on 2.8.2 showed doctor `NOT ok` and
    `caption.usable: no`. The row's real question is still untested: does the *agent* read
    `caption.usable` before calling `caption.py`?
  - **Codex:** the user installs into `~/.agents/skills` and uses Codex daily.
- **The fork's `main` lags upstream** unless someone pushes it; GitHub doesn't sync forks
  automatically.
- **npm `time --json` can return a list.** Take the last element before indexing.

## Current State

- **Checkout:** on `notes` at `37a1ff1`, matching origin. This summary is uncommitted at
  the time of writing.
- **Local `main`:** `f1a4f2a`, 2 ahead of `origin/main` (not yet pushed).
- **Installed skill:** 2.8.3.
- **Upstream:**
  - #321 merged (v2.8.3);
  - #318, #317 and #314 have no new comments as of the 2:22 PM check;
  - #143 is open, with every row `not run`.

## Unfinished Work

- **User pushes:** `git push -u origin main`, and `notes` once this summary is committed.
- **Possible #143 contributions** (the user's call; nothing posted):
  - real Codex and macOS rows, with machine, commands and pasted output, keeping real results
    apart from simulated ones;
  - pointing out the doc drift above (checklist item never added, CI-closes-#143
    contradiction).
- **Still waiting on the maintainer:** #318 (whether `-mc 0` becomes the default or
  opt-in). #314 stays on hold.
