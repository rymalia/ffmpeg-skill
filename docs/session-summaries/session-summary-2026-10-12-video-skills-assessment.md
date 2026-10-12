---
session_id: 916b6715-f496-4a49-aa01-c6a96c326cd7
date: 2026-10-12
time: "12:53 PM PDT – 2:14 PM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: assessing kajisho5's video-editing and motion-graphics skills, and the fframes 1.2.0 refresh

## Overview

This session assessed two new skills from the ffmpeg-skill maintainer, `video-editing-skill` and
`motion-graphics-skill`, and decided to skip both: they refuse ffmpeg-skill 2.x, and `render.py` already covers
our use. It also re-checked fframes. Version 1.2.0 builds on this Mac without our Skia patch, and upstream has
fixed the decode half of our colour work. The session then reinstalled `fframes-video` from fframes.studio,
left a status note in the fframes repo, fixed a rejected push there, and handed the colour decision to
video-motion through a new baton.

The user interrupted the first attempt early in the session and re-sent the request, adding the fframes
session summary `session-summary-2026-09-29-video-skills-cleanup.md` to the context.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Skip video-editing-skill and motion-graphics-skill** | Both refuse ffmpeg-skill ≥1.0 and emit the removed `--crf` flag. Their real extras (a DAG with several outputs, asset hashing, a strict boundary for untrusted callers) serve a multi-agent orchestrator, not one user with Claude Code. `render.py` + `project.json` already covers the rest |
| **Test them against ffmpeg-skill v0.12.5 as well as 2.8.6** | It's fair to judge their design on the engine they were written for. `git archive v0.12.5` into the scratchpad left the installed skill untouched |
| **The one idea worth taking: video/chroma-key keys in `render.py` `overlays[]`** | Verified: `render.py:1245-1252` accepts only logo, image or text, while `overlay.py:102-106` supports `--video` and `--chromakey*`. A small feature, so issue first, per upstream etiquette |
| **Reinstall fframes-video from fframes.studio, not by rsync from the repo** | The published copy was diffed against `upstream/main` and was identical. Local fframes `main` was behind, and this sets the lock to `well-known`, so `npx skills update` pulls from the index |
| **Record fframes news in a dated note on fframes `main`, through a temporary worktree** | `main` already holds the user's docs. A worktree avoided touching the user's `feat/bt709-colour` checkout |
| **Rebase fframes `main`'s two unpushed docs commits onto `origin/main`** (user hit a rejected push) | GitHub's "Sync fork" had fast-forwarded `origin/main` to upstream (`f962cd6`). The commits had never been pushed and only add `docs/` files, so rewriting them was safe. Backup branch `backup/main-pre-rebase-2026-10-12` |
| **Recommend measuring stock 1.2.0 before rebasing `feat/bt709-colour`** (user agreed, baton written) | The branch conflicts in 3 files the maintainer just rewrote. Stock output may now be wrong only in its matrix and tags, which would make a fresh small patch or an issue cheaper than a rebase |
| **Retire the 2026-09-29 Phase 1 baton by folding it in, not just deleting it** | It still held open Gate 1 and Phase 2 steps and the unanswered prores_ks question. Those moved into the new baton first |

## Changes Made

| Change | Detail |
|--------|--------|
| **Assessment doc** | `docs/assessments/2026-10-12-video-editing-motion-graphics-fframes.md`, commits `d7e38da`, `8325c97` (marked the refresh done) and `ffb0612` (hash update after the fframes rebase), on `notes` |
| **fframes-video reinstalled** | `npx skills add https://fframes.studio -g -y -s fframes-video -a claude-code codex`, run from the scratchpad. `~/.agents/skills/fframes-video` now equals `upstream/main:skills/fframes-video`. The lock records `sourceType: well-known`. The `~/.claude` symlink is unchanged. The old copy and lock were backed up in the scratchpad |
| **fframes status note** | `~/projects/fframes/docs/notes/2026-10-12-upstream-1.2.0-status.md`, committed on fframes `main` (first `80f4f63`, `56ea79a` after the rebase). The user then pushed it: `origin/main..main` = 0 |
| **fframes `main` rebased** | `f2060fd` + `80f4f63` → `5234533` + `56ea79a` on top of `f962cd6`. Backup branch `backup/main-pre-rebase-2026-10-12` |
| **video-motion baton** | New `~/projects/video-motion/.baton/2026-10-12-stock-1.2.0-colour-measure.md`. Retired `2026-09-29-video-motion-phase1-route-a.md` after folding in its open items. `.baton/` is git-ignored |
| **Memory** | Updated `fframes-build-on-macos27.md` (1.2.0 needs no patch) and `footage-motion-plan.md` (upstream `4a752de` overlaps the decode half; the encode side still matters) |
| **Scratch only** | Clones of both repos, a venv with both installed, test media, the `engine-0125` export, the `fframes-120` test project, Codex logs |

## Testing / Research Performed

- **Doctors against the installed 2.8.6:**
  - video-editing: `ok False`, 0 supported operations ("ffmpeg-skill version 2.8.6 (supported >=0.10.0,<1.0.0)").
  - motion-graphics: ffmpeg_skill `fail` ("outside the supported window [0.12.1, 1.0.0)", "graphics/overlay lacks
    flag(s) ['crf']").
- **Doctors against v0.12.5:**
  - video-editing: ok, all 9 operations supported.
  - motion-graphics: ok. Element-type statuses were mixed: `supported` or `unknown`.
- **Real renders on v0.12.5:**
  - video-editing: a 7-operation graph (TRIM, FILL, TRIM, FIT, SPEED, CONCAT with fade, OVERLAY) finished in
    3.89 s. Output h264 540×960 at 30/1, 3.6 s; the planned timeline was 7/2 s. A re-run was refused with
    `PATH_NOT_ALLOWED` (output exists).
  - motion-graphics: 6 elements (title, lower_third, image_overlay with fade, bug, progress, countdown) finished
    in 5.20 s, one `graphics`/`overlay` call per element. A contact sheet showed the title's scrim dimming the
    earlier logo, and the `bug` hidden under the logo with no warning. The first attempt correctly failed
    `INVALID_REQUEST` because I passed `text` to `bug`.
- **Test suites:**
  - video-editing on v0.12.5: 148 passed, 2 failed, 1 skipped, 1 error. The failure examined was
    `test_pipeline_e2e`: `VALIDATION_ERROR`, "frame rate 29.819 is not the requested 30" on the crossfade join
    (ffmpeg 9.0.2).
  - video-editing on 2.8.6: 104 passed, 47 skipped. The real-media tests skip themselves.
  - motion-graphics: the first run used the wrong environment variable (41 failed, my setup error). Re-run with
    `MOTION_GRAPHICS_FFMPEG_SKILL_DIR`: 312 passed, 1 failed (`test_countdown_draws_a_digit_throughout_its_window[0.5]`).
- **Codex (3 runs, read-only):**
  - Assessment of video-editing (gpt-6-luna high): alpha, SKIP.
  - Assessment of motion-graphics (gpt-5.6-luna xhigh): alpha, SKIP. Unreproduced code-reading findings:
    overwrite is not passed on, a final-probe error is misclassified, malformed JSON is treated as success.
  - Overlap with `render.py` (gpt-6-luna high): no fewer encode generations in either; porting estimate 2–4 days
    and 1–2 days (inference). The video/chroma-key gap was confirmed by hand.
- **Version history:** ffmpeg-skill tags `v0.10.0`–`v0.12.0` on 2026-09-07 and `v0.16.15` on 2026-09-11. The
  wrappers' last commits were 2026-09-08.
- **fframes:**
  - `upstream/main` was 30+ commits ahead (1.1.0, 1.2.0). #154 closed ("Fixed in 1.0.3").
  - The fframes.studio index returns 200.
  - `4a752de` (2026-09-30) applies the source matrix and range on decode.
  - A fresh 1.2.0 Skia project (a copy of `fframes-eval`, Skia patch removed) built in 28 s, and the hook
    rendered in about 2.0 s warm (2.75, 2.00, 1.97).
  - The output was tagged `tv/smpte170m/unknown/unknown`.
  - `git merge-tree feat/bt709-colour upstream/main` conflicts in 3 files. Upstream commits per file were
    checked with `git log`.
- **Gate 0 code read** for the baton: `evaluate` always decodes as BT.709 (`gatelib.py:80`). The unpatched
  control uses `--config` patch paths (`gate0.py:108-122`). The 2026-09-29 `result.txt` showed PASS 15/15.

## Summary Statistics

- Skills assessed: 3 (2 installed in a venv, 1 reinstalled). Real renders: 2 wrapper runs + 3 fframes renders.
- Test runs: 5 suite runs (one invalid, from my setup error). Codex runs: 3.
- Commits: 3 on ffmpeg-skill `notes`; 1 note commit plus 1 rebase on fframes `main`.
- Batons: 1 written, 1 retired. Memories updated: 2.

## Discoveries / Handoff Notes

- **The maintainer's wider ecosystem** includes `AI-video-production-OS`, `subtitle-skill`, `color-grading-skill`,
  `qc-skill`, `transcription-skill` and `audio-production-skill`. The two skills assessed are execution layers
  for it, frozen since 2026-09-08 while ffmpeg-skill went to 2.8.6.
- **ffmpeg-skill `render.py` uses one encode per graphics/overlay element** (`render.py:1222-1260`), the same as
  motion-graphics-skill.
- **GitHub's fork sync moves `origin/main`**, so local docs commits on fframes `main` need a rebase before each
  push.
- **The Gate 0 landmines** for 1.2.x (the `=1.0.2` pin sending path patches to the registry, BT.709-only
  decoding, prebuilt FFmpeg possibly lacking `prores_ks`) are written up in the baton.
- **The fframes status note's "31 ahead / 1 ahead" line** predates the rebase. The baton says so.

## Current State

- **ffmpeg-skill `notes`:** at `ffb0612`, plus this summary. Not pushed. `CLAUDE.local.md` and `bench/` were
  untracked before this session.
- **fframes:**
  - `main` is at `56ea79a`, equal to `origin/main` (pushed by the user).
  - The checkout is on `feat/bt709-colour` @ `9358c05`, untouched.
  - `~/projects/fframes-upstream` is still at the old `4d6557f`.
- **video-motion:** `main` is 5 ahead of origin, untouched by this session. Its `.baton/` holds the new
  colour-measure baton and `2026-09-29-pil-night-production.md`.
- **Installed:** `fframes-video` is the fframes.studio copy. Active sessions need `/reload-skills`.

### Unfinished Work

- **video-motion (next session):** grab `.baton/2026-10-12-stock-1.2.0-colour-measure.md`. Measure stock
  1.2.0 in both decode modes, then choose between a rebase, a fresh patch and an upstream issue (issue first).
  Gate 1 and Phase 2 follow, per the baton.
- **ffmpeg-skill upstream, optional:**
  - An issue for `check.py` mis-reporting `smpte170m` as untagged.
  - An issue for video/chroma-key keys in `render.py` `overlays[]`.
- **Optional:** delete `backup/main-pre-rebase-2026-10-12` in fframes once the push is confirmed. Push
  ffmpeg-skill `notes`: `git -C ~/projects/ffmpeg-skill push -u origin notes`.
- **Watch:** kajisho5's video-editing-skill and motion-graphics-skill for a 2.x port; no action until then.
