---
session_id: 916b6715-f496-4a49-aa01-c6a96c326cd7
date: 2026-10-12
time: "12:53 PM PDT – 3:07 PM PDT"
project: ffmpeg-skill
branch: notes
---

# Session Summary: filing ffmpeg-skill #325 (check.py colour tags) and #326 (render.py video overlays)

## Overview

This summary covers only the stretch after the session's first summary
(`session-summary-2026-10-12-video-skills-assessment.md`, written at 2:14 PM and left unchanged). In that time:

- The fframes backup branch was deleted after its commits were confirmed on the fork.
- The user pushed ffmpeg-skill `notes`.
- Two issues from the morning's assessment were reproduced on 2.8.6 with synthetic clips and filed upstream:
  **#325**, a bug, and **#326**, a feature request.

The `time` range is the whole session: the collector's `session_start` through its `now`.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Delete `backup/main-pre-rebase-2026-10-12` only after a range-diff** | `git range-diff` showed both old commits `=` their rebased copies on `origin/main` (`f2060fd`=`5234533`, `80f4f63`=`56ea79a`), and `docs/` was identical, so nothing was lost |
| **#325 as an issue, at the user's request** | The maintainer-expectations memory says a bug fix can go straight to a PR, but the user asked for an issue. It also leaves the fix's shape (and the row's wording) to the maintainer |
| **Synthetic clips only, with tags written through x264 VUI** | Per the test-clip memory, anything posted upstream uses reproducible `testsrc2`. On FFmpeg 9.0.2 the `-color_primaries`/`-color_trc` output options did not stick, so tags went through `-x264-params`, the method `_common/color.py` itself uses on FFmpeg ≥ 7.1 |
| **#326 argued from verified behaviour; a wrong guess dropped** | I expected a corner PiP to be cropped by a 9:16 reframe. A frame grab showed `render.py` letterboxes instead, so the issue argues from the PiP shrinking (480 px → about 270 px), the platform margins and the stage order |
| **No PR offer in #326** | It would have committed the user to follow-up work. The maintainer often implements issues themselves. The memory now says to reply if they ask for a PR |

## Changes Made

| Change | Detail |
|--------|--------|
| **fframes backup branch deleted** | `git branch -D backup/main-pre-rebase-2026-10-12` (was `80f4f63`). No backup branches remain; the checkout is still on `feat/bt709-colour` |
| **Upstream issue #325** | https://github.com/kajisho5/ffmpeg-skill/issues/325: "check.py: a BT.601 matrix-only file passes as \"untagged (players assume bt709)\"" |
| **Upstream issue #326** | https://github.com/kajisho5/ffmpeg-skill/issues/326: "render.py: overlays[] can't take a video layer (overlay.py --video / --chromakey)" |
| **Memory** | `upstream-maintainer-expectations.md` gained a #325 entry and a #326 entry |
| **video-motion baton** | `.baton/2026-10-12-stock-1.2.0-colour-measure.md`: the two `check.py` mentions now point to #325 ("follow it, do not re-file"). The baton is git-ignored |
| **Pushes by the user** | ffmpeg-skill `notes`, `8325c97..38f98c0`, now tracking `origin/notes`. fframes `main` was confirmed pushed earlier (`origin/main` = `main` = `56ea79a`) |

## Testing / Research Performed

- **Duplicate searches** with `gh issue list --search`:
  - Colour terms found #159, #316, #146 and #148, none of them this bug.
  - Chroma/PiP terms found #141 (`broll.py`, standalone only) and #53, none of them this feature.
- **#325 root cause:** `check.py:164-165` builds `tags` from `color_primaries` and `color_transfer` only, and
  `untagged` is true when both are empty. `probe.py` does report `color_space`; the check just never reads it.
- **#325 repro** (ffmpeg-skill 2.8.6, FFmpeg 9.0.2), `check.py --platform reels`:

  | clip | matrix / primaries / transfer | colour row |
  |---|---|---|
  | matrix-only-601 | `smpte170m,unknown,unknown` | PASS "untagged (players assume bt709)" |
  | full-601 | `smpte170m,smpte170m,smpte170m` | WARN |
  | matrix-only-709 | `bt709,unknown,unknown` | PASS "untagged" |
  | full-709 | `bt709,bt709,bt709` | PASS |

  The first attempt was invalid: zsh passed the argument string as a single word, and the tag options
  didn't apply.
- **#326 repro:**
  - `overlay.py talk.mp4 --video green.mp4 --chromakey 0x00ff00 --position bottom-right --scale 480` finished
    `completed`, `verified: true`. A frame grab showed the green keyed out and the inset in the corner.
  - A `render.py` project with `{"video": ..., "chromakey": ...}` in `overlays[]` was refused:
    `unknown key 'video'`, followed by the list of 15 valid keys.
  - Pre-compositing, then a 9:16 project: `render.py` letterboxed the frame, and the PiP shrank to an estimated
    270 px.
- **Code facts cited in #326:**
  - `render.py:1245-1252`: overlays branch only on logo, image or text.
  - `render.py:1258`: the "review 12" platform-margin comment.
  - `_READ_ORDER` (`render.py:425`): overlays run after `fit` and before `export`/`check`.
  - The SKILL.md ordering rule: frame changes before captions.

## Summary Statistics

- Upstream issues filed: 2 (#325 bug, #326 feature). Duplicate searches: 2.
- Synthetic test clips: 4 (#325) + 2 sources, 3 renders and 1 refused project (#326).
- Branches deleted: 1. Memory entries added: 2. Baton references updated: 2.

## Discoveries / Handoff Notes

- **FFmpeg 9.0.2 drops plain `-color_primaries`/`-color_trc` on a libx264 encode of a `lavfi` source**: the
  output came out `unknown`. Tag through `-x264-params colorprim=...:transfer=...:colormatrix=...` when a
  clip needs exact tags. `-colorspace` alone may also convert pixels on FFmpeg ≥ 7.1, according to the
  `_common/color.py` docstring.
- **`render.py`'s default 9:16 reframe letterboxes rather than crops.**
- **`overlay.py` used the VideoToolbox hardware encoder by default on this Mac** and printed its not-CRF note
  in the JSON warnings.

## Current State

- **ffmpeg-skill `notes`:** `38f98c0` = `origin/notes`, plus this summary (uncommitted until the commit
  below).
- **fframes:** `main` = `origin/main` = `56ea79a`. The checkout is on `feat/bt709-colour` @ `9358c05`. No
  backup branches.
- **video-motion:** unchanged except the git-ignored baton.
- **Upstream:** #325 and #326 are open with no replies yet.

### Unfinished Work

- **Watch #325 and #326** and reply to any maintainer request. If they ask for a PR, follow
  `upstream-maintainer-expectations` (one fix per PR; a feat must reach every surface).
- **video-motion's next session:** grab `.baton/2026-10-12-stock-1.2.0-colour-measure.md`. Start Claude Code
  in `~/projects/video-motion` with `--add-dir ~/projects/fframes --add-dir ~/projects/fframes-upstream`.
- **Push** this summary: `git -C ~/projects/ffmpeg-skill push -u origin notes`.
