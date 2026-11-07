---
session_id: 2904990e-8c99-4799-8ff4-5d03c5e1e597
date: 2026-11-06
time: "03:09 PM PST – 04:46 PM PST"
project: ffmpeg-skill
branch: notes
---

# Session Summary: #393–#397 re-check and test suite on 3.2.0

This session continues the earlier summary, `session-summary-2026-11-06-upstream-320-sync.md` (upstream 3.2.0 merge, reinstall, #143 tracker marked fixed). This summary covers the work after that one: running the test suite and re-checking the five #143 fixes on our setup.

### Overview

Ran the full test suite on `notes` at 3.2.0: all 1098 tests passed on a clean run. Re-checked the fixes for #393–#397 by running the tools directly on a plain-Homebrew stand-in and on `ffmpeg-full`. All five are fixed. One minor leftover remains in #397's area.

### Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Re-ran the suite with `OUT=<scratchpad dir>` instead of deleting `tests/out/`** | `tests/_fixtures.py` reads `OUT` from the environment, so a fresh output directory isolates the run without destroying 6.4 GB of git-ignored output. |
| **Unset `FFMPEG_SKILL_HW` for the suite and the re-checks** | The user's shell exports `FFMPEG_SKILL_HW=1`. The #143 runs were done with it unset, so the re-check had to match. |
| **Rebuilt the lean stand-in the same way as the #143 run** | Copying the real `Cellar/ffmpeg/9.0.2_1` binaries into a prefix with no `opt/ffmpeg-full` avoids touching Homebrew while other sessions use `ffmpeg-full`, and it takes the same discovery path (`ffmpeg_source: path`). |
| **Ran the tools directly instead of repeating the agent rows** | The issues are about tool behaviour, and direct runs answer that. A repeat of the agent rows would be a separate, larger task. |
| **Used real footage (`IMG_6426.MOV`) only locally** | It has the AAC + APAC + metadata-track layout from #397. Per the test-clip memory, nothing from it is kept or posted. |
| **Did not file the metadata-track leftover** | It's minor, and #397 asked only about audio tracks. It is recorded in the tracker instead. |

### Changes Made

| Change | Detail |
|--------|--------|
| **Tracker re-check section** | `a13fd8a`: new "Re-check on 3.2.0 (2026-11-06)" section in `docs/plans/issue-143-real-hands-2026-11-02.md`, with the setup, a result table for each issue, and the test suite outcome. |
| **Memory** | New `test-suite-clean-run.md` ("run with a fresh `OUT` and `FFMPEG_SKILL_HW` unset") and its `MEMORY.md` index line. |

### Testing / Research Performed

- **Test suite, first run** (`python3 tests/run_parallel.py`, inheriting `FFMPEG_SKILL_HW=1`, old `tests/out/`): 7 failures and 1 error, in `test_orchestration[3/3]` and `test_analysis[1/2]`/`[2/2]`. Most were `output_exists` refusals on files left by earlier runs. Also failed: `test_mcp_server_stdio` with `KeyError: 'probe'`, a plan path flagged as also being an input, and a verify stdout assertion. None were investigated, because the clean run passed.
- **Test suite, clean run** (`env -u FFMPEG_SKILL_HW OUT=<scratchpad>/testout python3 tests/run_parallel.py`): `1098 tests, 9 modules in 18 processes … 570s wall; all OK` (3 skipped). ffmpeg-full 9.0.2, Python 3.15.2.
- **#393** (lean): `caption.py --srt` and `render.py --template tiktok --srt` refuse in `--dry-run` and in the run with `reason: filter_missing` and the ffmpeg-full hint.
- **#394** (lean): `look.py` default completes with the `look_no_drawtext` fallback and a note. `doctor` still lists `look` and `render` as `usable: "yes"`.
- **#395** (ffmpeg-full): `emoji_support()` returns `mode: none`, `libass_glyph: false`. `caption.py --srt` leaves the emoji out, warns `emoji_not_drawn` (count 2), and stays `verified: true`. Cropped frames at 4.5 s and 7.5 s were viewed: "Emoji" with no tofu, and the Japanese cue renders correctly.
- **#396** (ffmpeg-full): `caption.py --text subs.srt` and `render.py --cues subs.srt` refuse with `kind: input` ("is an SRT file … pass it as --srt").
- **#397** (ffmpeg-full): a stream-copy cut of the synthetic `two-audio.mov` and of `IMG_6426.MOV` gives an `audio_tracks_dropped` warning (`source 2, kept 1, dropped 1`) and `dropped_audio_streams: 1`. On the iPhone file, ffprobe of the output shows that all six Core Media Metadata data tracks are gone with no note, and `dropped_non_av_streams: false`. The synthetic file's tmcd track is kept.

### Discoveries / Handoff Notes

- **A stale `tests/out/` gives false failures.** The 3.1.5+ output guards refuse to overwrite files left by older runs. Always use a fresh `OUT`.
- **#397 leftover:** `cut.py`'s stream copy drops iPhone timed-metadata tracks silently. That could be a follow-up issue if the user wants one, framed like #397 with a synthetic repro (needs a file with data tracks that ffmpeg can't copy).
- **#394 shape:** upstream fixed it with `look.py`'s fallback, not by changing doctor. `render` is still "usable: yes" on a lean build, but every caption/title template now refuses before any ffmpeg work, with a clear reason.
- The stand-in prefix and inputs are under the session scratchpad (`recheck/`), which goes away when the session ends.

### Current State

- `notes` is at `a13fd8a` plus this summary, 5 commits ahead of `origin/notes`. Not pushed; the user pushes.
- The untracked `-encoders`, `CLAUDE.local.md` and `bench/` were left alone. `tests/out/` was not deleted.

### Summary Statistics

- 1098 tests passed (clean run). 1 earlier run's false failures explained.
- 5 upstream fixes re-verified, with 12 direct tool runs (plus the `emoji_support()` probe) across the two builds.
- 1 docs commit plus this summary. 1 memory added.

### Unfinished Work

- Optional: file the iPhone metadata-track drop upstream (synthetic repro required).
- Optional: repeat the #143 agent rows (Codex + Claude Code) on 3.2.0 to see whether the agents now go straight to the right answer.
- Carried over from the earlier summary: merge `fix/scenes-beats-audio-only` once it's released, and re-anchor the video-motion plan's `color.py`/`overlay.py` references.
