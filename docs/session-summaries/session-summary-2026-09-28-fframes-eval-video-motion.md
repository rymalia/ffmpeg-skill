---
session_id: f5f53f67-824e-4331-b290-0dc0987a84bf
date: 2026-09-28
time: "2:13 PM PDT – 5:30 PM PDT"
resumed: "10:56 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
related_pr: dmtrKovalenko/fframes#155
---

# Session Summary: fframes-video evaluation, the Skia fix upstream, and the video-motion plan

## Overview

Tested the newly installed `fframes-video` skill against ffmpeg-skill on real footage, got it
building on macOS 27 (a Rust toolchain pin and a one-line Skia bindings patch), benchmarked Skia
vs CPU, and sent the Skia finding upstream as fframes issue #154 and docs PR #155. Then planned a
combined skill, **video-motion** (ffmpeg-skill preps and delivers footage, fframes draws the
graphics), through four revisions and four Codex plan reviews.

Timestamps: the start is this session's first SessionStart hook (`2026-09-28 02:13 PM PDT`).
The end, 5:30 PM PDT, is as stated by the user; the session was resumed at 10:56 PM PDT only to
write this summary, and the metadata collector reported that resume time as `session_start`.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Test fframes on the SHOW UP hook over a real concert plate** | Titles were ffmpeg-skill's weakest area in the SHOW UP reel (ISSUES.md T1, `.ttc` face 0 only), so it was a fair head-to-head and exercised the handoff between the tools |
| **Pin Rust 1.98.1 per project (`rust-toolchain.toml`), leave the global default at 1.94** | Rust 1.94's proc-macro dylib is rejected by macOS 27's loader; pinning avoids changing the user's other Rust projects |
| **Fix Skia with a vendored `fframes-skia-bindings` + `[patch.crates-io]`, not the CPU backend** | Adding `"std::__hash_table.*"` to `OPAQUE_TYPES` matched rust-skia's own fix (#1335); Skia brings `preview` and shaders |
| **File an issue plus a docs PR, not a code PR, upstream** | The bindings source is not in the fframes repo (published from the maintainer's rust-skia snapshot); two Codex reviews recommended both |
| **Combined skill as a thin orchestration layer, not a merge** | Both skills are maintained upstream; the value is the undocumented handoff (plate prep, safe zones, audio ownership, generations) |
| **v1 format fixed at 1080x1920 / 30 fps / BT.709 / 48 kHz** | fframes' frame size and fps are compile-time consts (`override_fps` is never read) |
| **Colour route A: patch fframes' colour conversion in the fork and PR upstream** (user choice) | Measured that fframes' BT.601 decode and encode cancel for the plate but mis-encode RGB graphics; a post-hoc conversion or retag cannot fix both |
| **Name `video-motion`, private repo, Skia default backend** (user choices) | Skia measured ~1.7x faster and is the only backend with `preview`, which the user liked |
| **Hand off revision 5 to a new session** | Context economy per the user's global instructions; the handoff doc and review logs were saved outside the scratchpad |

## Changes Made

| Change | Detail |
|--------|--------|
| **cargo-fframes 1.0.2** | `cargo install --locked cargo-fframes` → `~/.cargo/bin/cargo-fframes` |
| **Rust 1.98.1 toolchain** | `rustup toolchain install 1.98.1 --profile minimal`; global default unchanged (1.94) |
| **`~/projects/fframes-eval`** | Skia/Metal test project: hook video (`src/lib.rs`, runtime `assets/` loader in `src/main.rs`), `rust-toolchain.toml`, vendored patched bindings in `vendor/fframes-skia-bindings`, `[patch.crates-io]` in `Cargo.toml` (~3.6 GB) |
| **`~/projects/fframes-eval-cpu`** | CPU-backend copy with the same video plus an `FX=1` blur/glow/bokeh toggle; renders `out.mp4`, `strip.png`, `onion.png`, benchmark files (~2.2 GB) |
| **Plate and assets** | ffmpeg-skill `cut.py` + `fit.py` made a 6 s 1080x1920 plate from `trey-meyer-thru-mind.mp4` (303–309 s); plate audio WAV, a synthesized whoosh, `Futura.ttc` copied into `assets/` |
| **fframes fork** | `git remote set-url --push upstream DISABLED`; branch `docs/macos27-build-troubleshooting` (from `upstream/main`, tracking unset), commit `98db226` (`skills/fframes-video/SKILL.md`, +15/−2), pushed to `origin`; checkout returned to `fix/landing-footer-x-link` |
| **Upstream issue and PR** | dmtrKovalenko/fframes#154 (Skia on Xcode 27), #155 (docs: troubleshooting + zsh-safe `R` function) |
| **Plan and handoff** | `~/projects/docs/plans/footage-motion-skill-plan.md` (revision 4), `footage-motion-handoff.md`, `footage-motion-codex-review-4.log` and `.prompt.txt` |
| **Memory** | New `fframes-build-on-macos27.md` and `footage-motion-plan.md`, with `MEMORY.md` pointers |

No ffmpeg-skill source was changed and nothing was committed in this repository.

## Testing / Research Performed

- **Install check:** skill files present and symlinked like ffmpeg-skill; system libraries present;
  `cargo-fframes` missing (installed). First build failed twice, deterministically.
- **Root causes, reproduced:** `dlopen` of the proc-macro dylib failed with "mis-aligned LINKEDIT
  string pool" (fixed by Rust 1.98.1); the Skia bindgen output had an unbound `_Traits` in
  `std___hash_table___node_allocator` (fixed by the one-line patch; rust-skia issue #1331 / PR #1335
  found afterwards with the same fix plus `std::__rebind_alloc.*`).
- **fframes CLI loop on the hook video:** `timeline`, `inspect` (24 frames, no problems), `strip`,
  `frame`, `onion`, `audio analyze` (−15.5 LUFS, −2.9 dBTP), `audio at`, `render` (180 frames,
  A/V 6.000 s, 1.8 s wall on CPU). Futura Condensed ExtraBold resolved from the system `.ttc` by
  weight 800 + `font-stretch="condensed"`.
- **Cross-check with ffmpeg-skill:** `check.py --platform reels` on fframes' output 12 PASS / 1 WARN
  (subtitles); `loudness.py --measure-only` −15.58 LUFS / −2.99 dBTP (agrees within 0.1).
  Side-by-side frame vs `graphics.py --template hook` (3 s render, static 91 px text).
- **Benchmark (3 runs each, uncontended):** Skia 1.11–1.17 s vs CPU 1.83–1.97 s; with FX 1.46–1.67 s
  vs 2.66–2.71 s. Effects verified visible in frames from both backends.
- **Skia patch evidence:** 476 non-std structs identical before/after; no Skia struct embeds
  `std::__hash_table`; the bindings carry 1041 compile-time layout assertions (an earlier claim of
  none was wrong, corrected after Codex flagged it).
- **zsh:** confirmed `R="cargo run --release --"; $R` fails in zsh and `R() { cargo run --release -- "$@"; }`
  works in zsh and bash. `typos` passes on the edited SKILL.md (after rewording dyld's "mis-aligned").
- **Colour measurement:** fframes output tagged `tv,smpte170m,unknown,unknown` vs the plate's
  `bt709`; frame 0 vs plate YUV 46.3 dB PSNR, vs a correct 709→601 conversion 40.9 dB.
- **Codebase facts verified for the plan:** fframes `Video` consts and unused `override_fps`; no
  `sws_setColorspaceDetails` in fframes/fframes-media; `_common/color.py` tags only; `audio.py` never
  re-encodes video and has no sample-rate option; `audio render` has no sample-rate flag; bundled
  FFmpeg config has `prores_ks`, `qtrle`, mov muxer; `fit.py --fps 30 --codec prores --no-hw` dry run.
- **Sources probed:** 10 files in `~/Downloads` (rates from 23.976 to 60, VFR cases, SD/HD/native
  9:16) for the plan's gate table.
- **Codex reviews (7 runs):** Skia fix, gpt-6-luna xhigh and gpt-5.6-luna high: both SHIP (as-is).
  Plan reviews 1–4, gpt-5.6-terra xhigh: REVISE each time (review 3 resolved 10 of 12 prior
  findings; review 4: 4 resolved, 6 partial, 1 new critical on primaries/transfer).

## Summary Statistics

- Test projects built: 2 (Skia, CPU); uncontended benchmark renders: 12
- Upstream contributions: 1 issue (#154), 1 PR (#155, 1 file)
- Codex runs: 2 diff reviews + 4 plan reviews (plus 2 aborted launches, restarted)
- Plan revisions: 4; source videos probed: 10
- Memory files added: 2

## Discoveries / Handoff Notes

- **`check.py` defect:** it reported fframes' `smpte170m`-tagged output as "untagged (players
  assume bt709)" and passed it. Not yet in ISSUES.md.
- **fframes colour:** plate pixels survive fframes (decode and encode both BT.601) but are
  mislabelled; RGB graphics are mis-encoded. `sws_setColorspaceDetails` only sets matrix and range,
  so BT.601 sources also need a real primaries/transfer conversion in `prep` (Codex review 4).
- **fframes builds FFmpeg from source** even with Homebrew FFmpeg installed; its build warns that
  the `videotoolbox` feature is off.
- **The skill's `R=` idiom breaks in zsh** (fixed in PR #155).
- **Process lesson:** `cd DIR && (…) &` roots only the first group; one Codex review started in the
  wrong repo, and `pkill -f` on a model name also killed the parent shell. Launch each background
  review as its own task.

## Current State

- ffmpeg-skill repo: branch `m-series-hw-parakeet`, untouched by this session except this summary;
  `CLAUDE.local.md` untracked as before.
- fframes fork: on `fix/landing-footer-x-link`, upstream push `DISABLED`, the user's untracked
  `docs/` left alone.
- The patched Skia build in `~/projects/fframes-eval` works; `preview` there was not launched by the
  agent (the user reported liking it).

## Issues & PRs

- https://github.com/dmtrKovalenko/fframes/issues/154
- https://github.com/dmtrKovalenko/fframes/pull/155

## Unfinished Work

- The user was asked to approve all 7 Codex review-4 edits; then write revision 5 and run Codex
  review 5, following `~/projects/docs/plans/footage-motion-handoff.md`.
- Phase 1 of the plan: the fframes BT.709 colour patch (branch `feat/bt709-colour`), then Gate 0.
- Add the `check.py` smpte170m defect to ISSUES.md.
- Watch fframes #154 / #155 for maintainer response.
- Optional: rename the `footage-motion-*` plan files to `video-motion-*` once review cycles finish.
