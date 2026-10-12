# Assessment: video-editing-skill, motion-graphics-skill, fframes-video (2026-10-12)

Should we adopt kajisho5's `video-editing-skill` and `motion-graphics-skill`, and where does `fframes-video` stand?
Method: both repos were cloned and installed in a scratch venv and run for real. They were tested against the
installed ffmpeg-skill 2.8.6 and against v0.12.5, the version they were written for. There were three Codex
passes: an assessment of each repo (gpt-6-luna high, gpt-5.6-luna xhigh) and an overlap analysis against
`render.py` (gpt-6-luna high). fframes 1.2.0 was rebuilt from scratch.

## Verdict

| Skill | Maturity | Works with our ffmpeg-skill 2.8.6? | Recommendation |
|---|---|---|---|
| video-editing-skill | alpha. 27 commits, 2026-09-04..08, quiet since | **No.** Its doctor refuses it, and every operation is unavailable | **Skip.** Watch only if the maintainer ports it |
| motion-graphics-skill | alpha. 12 commits, 2026-09-05..08, quiet since | **No.** Same refusal, and it emits the removed `--crf` flag | **Skip.** Lift one idea upstream (below) |
| fframes-video | active. Releases 1.1.0 and 1.2.0, pushed 2026-10-12 | n/a (separate engine) | **Keep. Refresh the installed skill**, which is ~30 upstream commits behind |

## video-editing-skill and motion-graphics-skill

**What they are.** They are typed-JSON "execution" layers for the maintainer's multi-agent *AI Video Production
Ecosystem* (`AI-video-production-OS`, `subtitle-skill`, `color-grading-skill`, `qc-skill`, ...). An orchestrator
agent sends a request document. The skill validates it, runs ffmpeg-skill scripts with typed argv, and returns
hashes, probes and per-operation provenance. Neither adds an editing or rendering primitive that ffmpeg-skill
lacks.

**Why they don't run today (reproduced).**
- Version gates: `>=0.10.0,<1.0.0` and `>=0.12.1,<1.0.0`. ffmpeg-skill went from 0.10 to 0.16 between Sep 7 and
  Sep 11 and is now 2.8.6. Both doctors fail closed: they refuse cleanly and never produce wrong output.
- Both emit `--crf`, which 2.x removed in favour of `--quality`.
- Neither looks in `~/.agents/skills/ffmpeg-skill`, so the path has to be set by an environment variable.
- The test suites hide this. Against 2.8.6, video-editing-skill reports "104 passed, 47 skipped": the real-media
  tests skip themselves, so CI would stay green while the skill does nothing.

**On their intended engine (v0.12.5) they work and are well built.**
- video-editing-skill: a 7-operation graph (trim → fill/fit 9:16 → 2× speed → crossfade concat → logo overlay)
  rendered in 3.9 s, with an exact rational timeline map and per-step provenance. A re-run correctly refused to
  overwrite the output. Tests: 148 passed, 2 failed, 1 error. The failure examined was its own validator
  catching a 29.819 fps crossfade join that should have been 30 fps, a real engine quirk.
- motion-graphics-skill: 6 element types (title, lower-third, image overlay with fade, bug, progress bar,
  countdown) rendered in 5.2 s. Tests: 312 passed, 1 failed (countdown timing). Error messages are good: an
  unknown field returns the list of allowed fields.
- Rendering limits seen in the output: elements are layered strictly by `(start, id)`. The title's scrim dimmed
  a logo placed earlier, and a `bug` hidden under the logo raised no warning. Each element is one full re-encode
  of the plate. `render.py` does the same, one generation per overlay, so this isn't unique to the skill.

**Why we don't need them.** ffmpeg-skill 2.x's `render.py` + `project.json` already covers our single-user use:
declarative clips, speed, transitions and frame; graphics and overlays; `brand.json`; `--cache`/`--from`;
`--dry-run`; and FCPXML/EDL/OTIO export. The wrappers' real extras are:
- an arbitrary DAG with several outputs (video-editing)
- canonical element ids and font/asset hashing (motion-graphics)
- a strict security boundary for *untrusted* callers

Those matter for a multi-agent orchestrator, not for one person driving Claude Code. Codex estimates a port to
2.8.6 at 2–4 days (video-editing) and 1–2 days (motion-graphics). That work belongs to the maintainer, not us.

**Codex defect findings** (from reading the code; not reproduced):
- video-editing: if a later output copy fails, earlier outputs stay on disk. The work dir is created before its
  symlink-escape check. `pyproject` says 0.2.0 but the runtime says 0.4.0. SKILL.md still says OVERLAY needs
  audio.
- motion-graphics: `overwrite` is never passed on as `--overwrite`, so it would fail on 2.x. A final-probe
  failure surfaces as `INVALID_INPUT` instead of `VALIDATION_ERROR`. Malformed tool JSON with exit 0 is treated
  as success. An `OSError` can escape as a traceback.

**Worth taking (verified).** `render.py`'s `overlays[]` accepts only `logo`/`image`/`text` (`render.py:1245-1252`),
although `overlay.py` supports `--video` and `--chromakey*` (`overlay.py:102-106`). Picture-in-picture and
green-screen therefore can't be done in a project file. That is a small, clean feature for ffmpeg-skill.
Upstream wants an issue first (see the maintainer-expectations memory).

## fframes-video

Changes since our 2026-09-28 evaluation:
- **#154 closed ("fixed in 1.0.3").** fframes 1.2.0 builds on this Mac **without our Skia bindings patch**. A
  clean `cargo build --release` took 28 s (prebuilt Skia and ffmpeg are now downloaded on macOS); it was about
  20 minutes plus the patch on 1.0.2. The Rust 1.98.1 pin is still used.
- The SHOW UP hook re-rendered unchanged on 1.2.0: 6.000 s, 1080×1920, ~2.0 s warm. That is not directly
  comparable to the old 1.1 s Skia figure, which came from an idle machine.
- **Colour:** upstream `4a752de` (2026-09-30) now honours the source YUV matrix and range on decode, which
  overlaps the decode half of our `feat/bt709-colour` (`50223a9`). 1.2.0 output is still tagged
  `smpte170m`, so the encode-side BT.709 work in video-motion is still needed. Re-scope the drafted upstream
  PRs against `upstream/main` before sending them.
- The upstream skill text changed (`api.md`, `design.md`, SKILL.md): it forbids writing tests, offers `preview`
  before full renders, and adds reference-video matching and shader-mode guidance. The `fframes.studio`
  well-known index now returns 200, so a reinstall from there (planned on 2026-09-29) is unblocked.

fframes stays the graphics engine for video-motion. It covers what motion-graphics-skill cannot: real
animation, shaders, GPU preview, and one encode for any number of elements.

## Next steps

1. ~~Refresh `~/.agents/skills/fframes-video`~~ Done 2026-10-12 from fframes.studio (lock now `well-known`); see `~/projects/fframes/docs/notes/2026-10-12-upstream-1.2.0-status.md` (fframes `main` 56ea79a after the 2026-10-12 rebase onto origin/main), which also records that `feat/bt709-colour` conflicts with upstream in 3 files.
2. Optional: file an ffmpeg-skill issue for `video`/`chromakey` keys in `render.py` `overlays[]`.
3. video-motion: diff `feat/bt709-colour` against upstream `4a752de`, and keep only the encode side.
4. No action on video-editing-skill or motion-graphics-skill.
