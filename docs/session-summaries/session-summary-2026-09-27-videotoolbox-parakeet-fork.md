---
session_id: c5ed860f-d42c-4698-9f44-2b6c571bcb0f
date: 2026-09-27
time: "2026-09-26 9:53 PM PDT – 2026-09-27 1:59 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: VideoToolbox encoding + Parakeet ASR for ffmpeg-skill (M4 Max)

## Overview

Set up ffmpeg-skill on this M4 Max, benchmarked local speech engines (whisper.cpp vs Parakeet), then forked `kajisho5/ffmpeg-skill` and added opt-in Apple VideoToolbox (GPU) encoding and Parakeet speech engines. The work is committed as `3ff6462` on `m-series-hw-parakeet`, pushed to `rymalia/ffmpeg-skill`, and installed as the single shared copy for Claude Code and Codex.

## How We Got Here

1. **Environment check.** `npx ffmpeg-skill contract --json` / `doctor`: `missing`, `missing_optional` and `unknown` all empty (26 required, 41 optional capabilities). A `BrokenPipeError` traceback came from piping into `head`, not from the tool.
2. **Gaps found.** `whisper-cli` was installed, but the only model was Homebrew's `for-tests-ggml-tiny.bin`, outside the skill's search path (`~/.cache/whisper.cpp/`). `doctor` reports `external:whisper` from binary presence alone. The VideoToolbox encoders were built in but never used by any tool.
3. **Models and engines installed** (see Changes Made), then ASR benchmarked twice.
4. **User asked for GPU encoding and full Parakeet support.** Decisions came from an AskUserQuestion round (fork+branch / opt-in with env default / Parakeet for English), then a plan, a Codex plan review, the implementation, two Codex diff reviews, tests, commit, push, install, and the symlink layout.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Fork + branch, not patching the installed copy** | `npx ffmpeg-skill` overwrites `~/.claude/skills/ffmpeg-skill`. A fork keeps history, lets upstream be merged in, and allows an upstream PR later. The upstream push URL is set to `DISABLED`. |
| **`--hw` is opt-in; `FFMPEG_SKILL_HW=1` is the machine default, but not for `export.py` delivery presets** | The calibration sweep showed VideoToolbox is 2–7× faster but needs 1.2–2.5× the bytes at matched SSIM. That's right for drafts and intermediates, wrong for uploaded deliverables. `render.py`/`batch.py --hw` is the one switch that puts the export on the GPU too. |
| **Explicit render/batch `--hw` is passed to stages through an internal env marker (`_FFMPEG_SKILL_HW_EXPLICIT`), not argv** | render/batch have no `--codec`/crf of their own, and their children include tools with no `--hw` flag (probe, check). Tools without the flag ignore the marker. This addresses Codex's critical plan finding: an env default must not become an explicit export opt-in. |
| **VideoToolbox BT.709 tags go through `h264_metadata`/`hevc_metadata` bitstream filters on every FFmpeg version** | Measured tag-neutral PSNR on an untagged source: 49.9 dB through the BSF vs 23.8 dB through `-colorspace/-color_primaries/-color_trc` (a real matrix conversion on FFmpeg ≥7.1). Git builds report 7.1 as (7,0), so a version gate would pick the converting path. |
| **CRF→`-q:v` mapping: h264 `75 − 1.7·(crf−18)`, hevc `78 − 1.8·(crf−18)`, clamped 1–100** | Fitted by SSIM on three 1080p clips (Big Buck Bunny, Jellyfish, Sintel trailer) against x264/x265 `medium` at CRF 18/23/28. |
| **GPU→CPU runtime fallback by swapping the recorded VT arg slice back to its CPU line** | Encoder listing can't reveal hard limits (H.264 VT stops at 4096 wide). `run()` retries once on the CPU and reports it in `hw.notes`. |
| **Contract capability `external:parakeet` added; `external:whisper` left unchanged** | Renaming a capability changes a key's meaning, which requires a `contract_version` bump under `docs/contract.md`. The additive route needs no bump. |
| **`--engine auto` uses Parakeet only for English** | The default Parakeet model (tdt-0.6b-v2) is English-only. Routing order: explicit `--language`, then whisper.cpp `-dl` detection, then assume English (stated in `transcription.routing`). |
| **Parakeet model defaults to v2 (`mlx-community/parakeet-tdt-0.6b-v2`, `tdt-0.6b-v2-f16.gguf`)** | v3 on parakeet-mlx dropped words (6.17% WER, 40 deletions). The user set v2 as the default. |
| **`caption.py --model` default changed to `large-v3-turbo`** | Most accurate Whisper model in the benchmarks (2.43% WER) at 39× real time. |
| **`engine=` is passed to `transcribe`/`transcribe_words` only when `--engine` was given** | Existing upstream tests (and any wrapper) stub these functions with the pre-change signature. |
| **Codex's claim that VideoToolbox drops HDR10 metadata was tested and rejected** | A source with master-display + max-cll kept both side-data types through `hevc_videotoolbox` on FFmpeg 9.0. The planned warning note was removed, and a test now pins the behaviour. |
| **Skill layout: real files in `~/.agents/skills/ffmpeg-skill`, `~/.claude/skills/ffmpeg-skill` a relative symlink** | Matches the user's existing convention for other skills (`caveman`, `app-creator`, …) and gives Codex the same version. |

## Changes Made

### Outside the repo (machine setup)

| Change | Detail |
|--------|--------|
| **whisper.cpp models** | Downloaded `ggml-base.bin` (141 MB), `ggml-large-v3-turbo.bin` (1.5 GB), `ggml-small.bin` and `ggml-small.en.bin` (465 MB each) to `~/.cache/whisper.cpp/` |
| **parakeet-mlx** | `uv tool install parakeet-mlx` → `~/.local/bin/parakeet-mlx` |
| **parakeet.cpp v0.5.0** | Real binaries in `~/.local/libexec/parakeet.cpp/`. `~/.local/bin/parakeet-cli` and `parakeet-server` are wrapper scripts that add `--model ~/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf` when none is given (override with `PARAKEET_CPP_MODEL`). GGUFs `tdt-0.6b-v2-f16.gguf` and `tdt-0.6b-v3-f16.gguf` are in `~/.cache/parakeet.cpp/`. |
| **`~/.zshenv`** | Added `export PARAKEET_MODEL="mlx-community/parakeet-tdt-0.6b-v2"` and `export FFMPEG_SKILL_HW=1` |
| **Font** | `brew install --cask font-dejavu` reported it was already installed. `fc-list` then found DejaVu Sans (the earlier "missing" reading was likely a stale fontconfig cache; not confirmed). |
| **Skill install** | `node bin/install.js --codex` → `~/.agents/skills/ffmpeg-skill`. `~/.claude/skills/ffmpeg-skill` replaced with a symlink `→ ../../.agents/skills/ffmpeg-skill`. |

### In the repo (commit `3ff6462`, 22 files, +1199/−78)

| Change | Detail |
|--------|--------|
| **`--hw`/`--no-hw` plumbing** | `scripts/_common/runner.py`: Context fields `hw`, `hw_source`, `hw_notes`, `hw_swaps`; flags added in `add_common` (re-encoding tools + export); `apply_common` resolves flag / explicit marker / env; `add_hw_orchestrator_args` for render/batch; `hw_platform_reason()` (Darwin + arm64); `_hw_fallback()` and retry in `run()`; `ffmpeg_encoders()` now reads `ffprobe -encoders` (dry-run promise). |
| **VideoToolbox encoder lines** | `scripts/_common/decision.py`: `vt_quality`, `_vt_bt709`, `_vt_args` (h264 High / hevc Main or Main10+p010le+source tags / prores HQ p210le; AV1 → CPU with note), `_maybe_hw`, `encoder_args` → `_cpu_encoder_args` wrapper, `hw_preset_video`, `strip_movflags`, `restate_last_swap`. |
| **export.py** | Fixed presets mapped to VT under `--hw`; BT.709 CPU tagging skipped for VT lines; swap restated after `-movflags` stripping. |
| **Result reporting** | `scripts/_common/emit.py` `_encoder_report`: `encoder` (last non-copy encoder, else `copy`) and `hw` `{requested, source, used (true/false/null), notes}`. |
| **Render cache key** | `scripts/render.py` `cache_key` includes `[FFMPEG_SKILL_HW on, explicit marker]`. |
| **Parakeet engines** | `scripts/_common/asr.py`: `PARAKEET_ENGINES`, `ENGINE_CHOICES`, `FFMPEG_SKILL_ASR_ENGINE`, parsers for parakeet-mlx JSON (sub-word token merge) and parakeet.cpp `--json` words, `cues_from_words`, `detect_language` (whisper.cpp `-dl`), `parakeet_route`, model resolution (`_parakeet_model_for`, `_parakeet_cpp_gguf`), `run_parakeet`; both `transcribe` and `transcribe_words` route through them and gate Whisper engines on `--engine`; `LAST_RUN`/`LAST_WORDS`. |
| **caption.py / silence.py** | `--engine`; `transcription` key in results; caption karaoke uses Parakeet word timings; silence `filler.source` becomes `parakeet:ENGINE` for Parakeet runs. |
| **Contract** | `scripts/_contract.py`: `external:parakeet` capability, detection (reuses the runtime check) and fix hint; `doctor.hw {platform_ok, default_on}`; output schema for `encoder`, `hw`, `transcription`, `filler`. |
| **Docs** | `SKILL.md` (kept under its 30,000-byte budget: 29,998), `README.md`, `docs/contract.md`, `docs/design-decisions.md` (new "2.4" section), `references/scripts.md`, `references/gotchas.md`, `CHANGELOG.md` (Unreleased). |
| **Tests** | New `tests/test_accel.py` (31 tests); `tests/test_all.py` includes it; `tests/_fixtures.py` and `tests/test_contract.py` scrub `FFMPEG_SKILL_HW`, `_FFMPEG_SKILL_HW_EXPLICIT`, `FFMPEG_SKILL_ASR_ENGINE`, `PARAKEET_MODEL`, `PARAKEET_CPP_MODEL` at import; `tests/fixtures/mcp_tools.json` regenerated (`UPDATE_MCP_SNAPSHOT=1`): additions only, `hw` on 32 tools and `engine` on 2. |

## Testing / Research Performed

- **ASR benchmark (run twice).** 8 min 01 s of LibriSpeech (73 clips from `hf-internal-testing/librispeech_asr_dummy`, 1,150 reference words), one warm-up plus three timed runs, WER via jiwer with normalization:

  | Engine / model | Time | WER |
  |---|---|---|
  | whisper.cpp base | 4.9 s | 7.13% |
  | whisper.cpp small | 8.7 s | 5.04% |
  | whisper.cpp small.en | 8.5 s | 4.70% |
  | whisper.cpp large-v3-turbo | 12.3 s | 2.43% |
  | parakeet-mlx v2 | 4.0 s | 2.78% |
  | parakeet-mlx v3 | 4.2 s | 6.17% |
  | parakeet.cpp v2 | 7.8 s | 2.87% |
  | parakeet.cpp v3 | 8.3 s | 3.57% |

  Rerunning parakeet-mlx v3 with `--chunk-duration 0` still gave 5.22% (27 deletions), so the word drops are not only chunk seams.
- **Encoder calibration sweep.** 3 clips × {x264, x265 at CRF 18/23/28, h264_videotoolbox and hevc_videotoolbox at q 45–80}, SSIM + size + time. Timings are approximate because they overlapped a test-suite run.
- **VT behaviour probes.** BT.709 tagging PSNR (49.9 vs 23.8 dB); PQ/HLG tag carry-through with correctly tagged sources; HDR10 mastering-display + CLL survive `hevc_videotoolbox`.
- **Smoke tests.** fit.py CPU / `--hw` / env / `--no-hw` / hevc / prores / av1-fallback; render.py reels template in 4 modes (none → all libx264; env → VT intermediate + libx264 export; `--hw` → VT throughout; env+`--no-hw` → all CPU); caption `--transcribe` through each engine; `--engine` via env; contract `--static`, doctor, MCP `tools/list`.
- **Codex reviews (gpt-5.6-terra, high, read-only).**
  - Plan review: REVISE — 1 critical, 5 major, 3 minor, all incorporated.
  - Diff review 1: FIX — 6 major, 3 minor; all verified and fixed with regression tests.
  - Diff review 2: FIX — 1 high, 2 medium; fixed.
  - Diff review 3: cut off by the Codex usage limit. Its two questions (import side effects of `_common.asr` in `_contract`; env-selected engine) were checked by hand and passed.
- **Test suite.** Upstream baseline: `test_all` 577 OK. A mid-session full run showed 10 failures + 2 errors: 8 came from a stale shared `tests/out/` plus a concurrent `test_accel` run, 2 were real (`engine=` broke signature-pinned stubs, fixed), and `mcp_server_stdio` passed in isolation. The final clean run after `rm -rf tests/out`: **608 tests OK (2 skipped) + contract 150 OK (1 skipped)**.
- **Post-install checks.** `doctor --json` via the symlink: `ok: true`, `hw {default_on: true, platform_ok: true}`, `external:parakeet` available. A real `fit.py` encode through the symlink: `verified: true`, `encoder: h264_videotoolbox`, `hw.source: env`.

## Summary Statistics

- Repo files changed: 22 (1 new test module), +1199/−78 lines (`git diff --stat`)
- New tests: 31 in `tests/test_accel.py`
- Codex review passes: 1 plan + 3 diff (1 incomplete); findings fixed: 9 (pass 1) + 3 (pass 2)
- Local ASR models/engines installed: 4 whisper models, 2 Parakeet runtimes, 2 GGUFs
- Commits: 1 (`3ff6462`), pushed to `origin/m-series-hw-parakeet`

## Discoveries / Handoff Notes

- **`tests/out/` must be empty before a full run.** Many upstream tests write fixed default output names and the skill refuses to overwrite. Never run two test processes at once; they share `tests/out/`.
- **`render.py`/`batch.py` have no `--codec`/crf**, so `STATE.codec` is always None there. Child stages get settings only via `child_args()` (fast/dry-run/overwrite/timeout) and the inherited environment.
- **`SKILL.md` is capped at 30,000 bytes and 220 lines** (`tests/test_orchestration.py:1609-1610`). It is at 29,998 bytes after this change.
- **Upstream Python 3.14 `SyntaxWarning`s** in `_ass_overlay.py:41` and `_common/drawtext.py:106` (invalid escape sequences). Harmless; not fixed.
- **parakeet-mlx's default model is v3**, which dropped words in the benchmark. The skill passes a model explicitly (`PARAKEET_MODEL` or the v2 default).
- **whisper-cli `-np` suppresses the "auto-detected language" line**, so language detection must not pass `-np`.
- **Updating the installed skill:** from this repo run `node bin/install.js --codex`. A plain `npx ffmpeg-skill` / `node bin/install.js` targets `~/.claude/skills` and would likely replace the symlink with a separate copy.
- **When upgrading parakeet.cpp**, put the new binaries in `~/.local/libexec/parakeet.cpp/`, not `~/.local/bin` (that would overwrite the wrappers).
- Benchmark artifacts (scripts, transcripts, calibration table) were in this session's scratchpad (`/private/tmp/claude-501/.../scratchpad/bench`, `cal`) and are not durable.

## Current State

- Branch `m-series-hw-parakeet` at `3ff6462`, tracking `origin/m-series-hw-parakeet` on `github.com/rymalia/ffmpeg-skill`. Remotes: `origin` = fork, `upstream` = `kajisho5/ffmpeg-skill` (push URL `DISABLED`).
- This summary file is untracked (written after the commit).
- The installed skill (`~/.agents/skills/ffmpeg-skill`, symlinked from `~/.claude/skills/ffmpeg-skill`) matches commit `3ff6462`.

## Unfinished Work

- Rerun the third Codex review pass once the Codex quota resets (it was cut off at the usage limit), then decide whether anything it raises needs fixing.
- Optional: open an upstream issue at `kajisho5/ffmpeg-skill` proposing the feature. `CONTRIBUTING.md` asks for an issue before any PR larger than a bug fix; no PR has been opened.
- Optional: add a `demos/build.py` / `docs/demos.md` demo for `--hw` (Codex suggested it; skipped).
- Decide whether to commit this session summary to the branch.
