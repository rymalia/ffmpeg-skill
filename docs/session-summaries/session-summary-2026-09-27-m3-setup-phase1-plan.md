---
session_id: de0c2171-dfd3-4878-a45d-e904f6043eac
date: 2026-09-27
time: "3:43 PM PDT – 8:06 PM PDT"
resumed: "4:18 PM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: M3 Air setup replication, test audit, and the Phase 1 carry-forward plan

## Overview

This session covered three pieces of work on the second MacBook (an Apple M3 Air, 16 GB):

1. It replicated the M4 Max's ffmpeg-skill setup, following
   `docs/setup/HANDOFF-replicate-on-second-mac.md`, and verified it end to end.
2. It wrote a Phase 1 fix plan from the carry-forward guide
   (`~/projects/docs/ffmpeg-skill-carry-forward-guide.md`), taking it through four Codex plan
   reviews.
3. It audited the fork's tests with Codex, which found and fixed a crash in the Parakeet
   parsers.

Implementation of the plan was deliberately deferred to the next session through a baton, to
stay within the context budget.

The start time (3:43 PM) comes from this session's original SessionStart hook. The metadata
collector reported 4:18 PM because the session was restarted with `/resume` at 4:18 PM; both
values are hook output.

## How We Got Here

1. **A false start.** The first request ("replicate what I did on the other machine … from my
   repo's plugin url") pointed at a Claude Code plugin install, but the repo has no
   `marketplace.json`, and the fork's default branch (`main`) is plain upstream. A clarifying
   question was rejected. The user then supplied three documents (the second-Mac handoff, the
   M4 setup inventory, and the handoff session summary), which showed the real layout: an
   `install.js --codex` copy plus a symlink.
2. **The handoff.** Steps 0–8 were run, with verification.
3. **The plan.** The user shared the carry-forward guide. Its lessons were checked against the
   fork's code, giving seven improvement candidates. The user chose items 1, 2, 3, 4, 6 and 7
   for a plan with a Codex review.
4. **Four plan reviews, each REVISE.** The user split the work into two phases after the second
   review.
5. **A test audit** (`/codex-doit`), then fixes, a review of those fixes, and more fixes.
6. **The context cutoff**, then the baton and this summary.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Follow the handoff doc's install layout, not a plugin install** | The M4 uses `node bin/install.js --codex` to `~/.agents/skills/ffmpeg-skill`, with `~/.claude/skills/ffmpeg-skill` as a relative symlink. The fork has no `marketplace.json`, and its `main` branch lacks the changes. |
| **Overwrite the old skill copy** | Before overwriting, it was checked file by file against the `v1.18.4` tag: 0 differences, so it was a pristine upstream install. |
| **Download only the required models** | Only `ggml-base` (language detection) and `ggml-large-v3-turbo` (the caption default), plus the v2 GGUF. The machine had 25 GB free, and the handoff marks the small/v3 models as benchmark-only. The parakeet-mlx v2 HF model was already in the cache. |
| **Put the parakeet.cpp wrappers in `~/.local/bin`, leave the Homebrew `parakeet-cli` alone** | `~/.local/bin` comes before `/opt/homebrew/bin` on PATH. The Homebrew binary ships with whisper.cpp 1.9.4 and belongs to that formula. |
| **Split the plan into Phase 1 and Phase 2** (user's choice) | Item 6 (timeout scaling) and the item-4 render/batch roll-up kept growing with each review (MCP `per_call`, the parallel-batch shared deadline, the ASR flat timeout, render cache hits). Items 1–3 and 7 were converging. |
| **Limit item 1 (edit-list copies) to single-segment MOV output** | Concat parts feed an unnormalised copy concat; edit-listed parts through the concat demuxer are unproven. |
| **Always report `reencode_reason` as a list** | It avoids any precedence rules between overlapping causes (`--accurate` + `--codec`, VFR + codec, a concat fallback). |
| **Replace the concat-demuxer join fallback with the concat filter** | The existing `cut.py:366` fallback re-encodes through the demuxer, which requires compatible inputs. Codex observed H.264 followed by HEVC exiting 0 with decoder errors. |
| **Trim the 8K VideoToolbox test rather than delete it** | A 0.5 s trim still triggers the real refusal: 26.3 s became 1.7 s, with the same assertions. The mocked `run()` retry test covers the logic; the real encode still proves VideoToolbox refuses frames wider than 4096. |
| **Put back two integration runs after cutting too far** | The Codex review of the test diff showed that making both exports dry runs left no test running `export.py --hw` to completion (or checking the 30 fps preset), and that dropping the env caption run left `FFMPEG_SKILL_ASR_ENGINE` → `caption.py` untested. |
| **Harden the parsers in production code** | Six malformed JSON shapes raised `TypeError`/`AttributeError`, which would crash `caption.py` with a traceback. A new `_dicts()` helper makes wrong shapes yield no words. |
| **Stop at the context cutoff and hand off with a baton** (user's instruction) | Phase 1 implementation (a refactor plus four items, each with a Codex review) wouldn't fit in the remaining budget without passing the user's ~50% guideline. |

## Changes Made

### Outside the repo (machine setup)

| Change | Detail |
|--------|--------|
| **Upstream push disabled** | `git remote set-url --push upstream DISABLED` |
| **whisper.cpp models** | `~/.cache/whisper.cpp/ggml-base.bin` and `ggml-large-v3-turbo.bin`. The SHA-256 matched the inventory (`60ed5bc3…`, `1fc70f77…`). |
| **parakeet-mlx** | Installed with `uv tool install parakeet-mlx` to `~/.local/bin/parakeet-mlx`. |
| **parakeet.cpp v0.5.0** | Binaries in `~/.local/libexec/parakeet.cpp/` (SHA-256 matched: `c5915e86…` cli, `27c658ab…` server). The wrapper scripts `~/.local/bin/parakeet-cli` and `parakeet-server` use the handoff's exact text. The GGUF `~/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf` matched `f8df7f5d…`. |
| **`~/.zshenv`** | Appended `PARAKEET_MODEL="mlx-community/parakeet-tdt-0.6b-v2"` and `FFMPEG_SKILL_HW=1`. |
| **Skill install** | `node bin/install.js --codex` to `~/.agents/skills/ffmpeg-skill`. The absolute symlink `~/.claude/skills/ffmpeg-skill` was replaced with the relative `../../.agents/skills/ffmpeg-skill`. `SKILL.md` and `scripts/` match the repo. |

### In the repo

| Change | Detail |
|--------|--------|
| **`1605b66` fix(asr)** | `scripts/_common/asr.py`: the `_dicts()` helper, used by `_words_from_parakeet_cpp_json`, `_words_from_parakeet_mlx_json` and `_cues_from_parakeet_mlx_json`. `tests/test_accel.py`: audit fixes and new tests (see below). `CHANGELOG.md` `Unreleased`: the parser fix entry. |
| **`52ec81a` chore** | `.gitignore` gains `.baton/`. |
| **`docs/plans/2026-09-27-carry-forward-fixes.md`** | Written and revised through R1–R4 plus an R5 amendment block during this session. It was **committed by the user** in `ce7bed7` (17:41, from another session), together with their `session-summary-2026-09-27-carry-forward-guide.md`. |
| **`.baton/2026-09-27-carry-forward-phase1.md`** | The handoff for the Phase 1 implementation. It's git-ignored and local to this machine. |

**`test_accel.py` changes in `1605b66`** (from 31 tests in 40.1 s to 35 tests in 13.8 s):
- **Trimmed:** the 8K refusal test runs `--duration 0.5 --method trim`.
- **Tautologies fixed:** the cue-split and auto-routing tests now assert literal values instead
  of `asr.CUE_MAX_SECONDS` / `asr.PARAKEET_ENGINES`.
- **Merged or loosened:**
  - the BT.709 tag tests became one test over h264/hevc and four version guesses;
  - the exact `vt_quality("h264", 18) == 75` assertion is gone;
  - export: the env case is a dry run, and the `--hw` case still encodes and checks 30 fps;
  - the caption flag and env runs became separate tests.
- **New:**
  - `test_run_retries_a_refused_videotoolbox_encode_on_the_cpu_and_reports_it` (mocked
    `runner._execute`);
  - `test_malformed_engine_output_yields_no_words_instead_of_crashing`;
  - `test_engine_flag_beats_the_environment_which_beats_auto`;
  - `test_caption_takes_the_engine_from_the_environment`;
  - `test_auto_falls_through_a_failing_parakeet_mlx_to_parakeet_cpp`, which checks a marker
    file proving the crashing fake mlx ran, with PATH restricted to the fakes.

## Testing / Research Performed

**Setup verification** (through the installed symlink, with the env vars exported):
- `_contract.py doctor --json`: `ok True`, `hw {default_on: True, platform_ok: True}`, and
  empty `missing`, `missing_optional` and `unknown`. `external:parakeet` was available, and
  `filter:drawtext`/`ass`/`subtitles` were present (`ffmpeg` links to `ffmpeg-full` 9.0.2).
- `fit.py` 1080p→720p: `verified True`, `encoder h264_videotoolbox`, `hw.source env`. With
  `--no-hw`: `libx264`.
- `caption.py --transcribe` on a `say` clip, once per engine:

  | Engine | Time | Transcription |
  |---|---|---|
  | parakeet-mlx | 5.17 s | correct |
  | parakeet.cpp | 8.79 s | correct |
  | whisper.cpp | 2.77 s | correct |
  | auto | 2.95 s | correct; routed to parakeet-mlx |

  A burn-mode run reported
  `transcription {routing: 'auto: detected English', engine: parakeet-mlx, model: …v2}`.

**Test suite**

| Run | Result |
|---|---|
| Baseline, before changes | `test_all` 608 OK (3 skipped), 764.6 s; contract 150 OK (1 skipped) |
| First run after the audit edits | `FAILED (failures=1, skipped=3)`. The failing test's name wasn't captured (output was tailed), and `test_accel.py` was edited while that run was in progress. |
| Rerun after the parser hardening | **612 OK (3 skipped)**, 773.1 s; contract **150 OK (1 skipped)** |

**Mutation checks.** Five were run. Each broke the guarded behaviour and confirmed the test
failed, restoring the scripts afterwards:
- the CPU retry disabled;
- `CUE_MAX_SECONDS` 7 → 8;
- `PARAKEET_ENGINES` reduced to mlx only;
- the Parakeet fallthrough loop broken;
- the env value placed ahead of `--engine`.

**Parser crash reproduction.** Six crashes, all from `3ff6462` code: `{"words": 5}` gave a
TypeError; `{"sentences": 5}` and `{"sentences": [5]}` crashed both mlx parsers; `{"tokens":
[5]}` crashed the word parser.

**FFmpeg experiments** (in the scratchpad):
- **B-frame HEVC cut at 4.3 s for 5 s.** The plain command gave V/A start 0/0 and video
  5.067 s, and its first frame's framemd5 equalled the source frame at 4.3 s. With `make_zero`:
  video start 0.1455 s, video 5.433 s. `-ignore_editlist 1` showed the stored video at 5.433 s,
  meaning 0.367 s of pre-roll with negative pts.
- **The suite's `source.mp4` cut at 1.13 s for 4.58 s.** MP4 with the edit list: video 4.670 s
  (end overshoot), audio 4.582 s. With `make_zero`: 5.800 s. MKV: 5.8 s either way.
- **A VFR false positive.** Lengthening only the last frame of a CFR file gives avg 29.316 vs
  r 30, and `probe.py` flags VFR.
- **A four-part ffprobe check:**
  - one `-read_intervals` call with three windows returned 180 packets (correct);
  - a `setts` remux reset the timescale;
  - `-show_data_hash sha256` gives `extradata_hash`, which a stream copy preserves;
  - PCM has no extradata hash.

**Codex passes, all read-only.** Their claims were checked against the code before being
reported:

| Pass | Model | Verdict |
|---|---|---|
| Plan R1 | gpt-5.6-terra, high | REVISE: 2 critical / 7 major / 5 minor |
| (attempt) | `gpt-6.0-terra` | Rejected: model not available on the ChatGPT account |
| Plan R2 | gpt-6-sol, xhigh | REVISE: 2 critical / 8 major / 3 minor |
| Plan R3 | gpt-6-sol, xhigh | REVISE: 1 critical / 4 major / 1 minor |
| Plan R4 | gpt-6-sol, xhigh | REVISE: 2 critical / 3 major / 2 minor |
| Test audit | config default, high | 31 committed tests classified; about 8 planned tests cut or fixed |
| Test-diff review | config default, high | FIX: 4 medium / 1 low, all addressed |

The audit estimated 1–4 minutes saved. The measured saving was about 28 s.

## Summary Statistics

- **Commits:** 2 (`1605b66`, `52ec81a`), pushed by the user; plus the commit holding this summary.
- **Production files changed:** 1 (`scripts/_common/asr.py`). **Test files:** 1 (35 tests,
  from 31).
- **Parser crash shapes fixed:** 6.
- **Codex passes:** 7, one of them a failed model attempt. **Plan revisions:** R1–R4, plus an
  R5 amendment block.
- **Full suite runs:** 3 `test_all` (608 OK baseline, 1 failure unidentified, 612 OK) and 3
  contract runs (150 OK each).
- **External artifacts installed:** 2 whisper models, 1 GGUF, 2 parakeet.cpp binaries, 2
  wrappers, 1 uv tool.

## Discoveries / Handoff Notes

- **Existing bug:** `cut.py:366`'s join fallback re-encodes through the concat demuxer and can
  produce a corrupt output that exits 0. The plan's item 3 replaces it.
- **`caption.py --mode mux --transcribe` omits `transcription`** from its result: only the burn
  path sets it (`caption.py:1594`). This is plan item 7.
- **An engine that outputs garbage is reported as "no speech"** (`run_parakeet` →
  `die_no_speech`). This is an open question for the user.
- **`probe.py:235`'s VFR heuristic (`|r − avg| > 0.01`) trips on iPhone files** (30 vs 29.979).
- **`cut.py --tolerance 0` re-encodes every segment**, since `abs(delta) >= 0`.
- **`fit.py --duration`** speeds the clip up unless `--method trim` is given. `silence.py` has
  no `--language`.
- **A safety check blocks `rm -f *` after `cd "$T"`.** Use a fresh `mktemp -d` directory
  instead.
- **This Mac's `~/.zshenv` also exports an unrelated API key** (a pre-existing line). Its value
  appeared once in command output during Step 0 and wasn't repeated.
- **Codex models on this account:** gpt-5.5, gpt-5.6-luna/sol/terra and gpt-6-astra/luna/sol.
  The config default is `gpt-6-sol`.

## Current State

- The branch `m-series-hw-parakeet`: `1605b66` and `52ec81a` are pushed to `origin`; this summary's
  commit is local until the next push. The only untracked file is `CLAUDE.local.md` (deliberate).
- The installed skill (`~/.agents/skills/ffmpeg-skill`) matches the repo as of the setup, which
  predates `1605b66`. To pick up the parser fix, rerun `node bin/install.js --codex`.
- The baton is at `.baton/2026-09-27-carry-forward-phase1.md`.

## Unfinished Work

1. **Push this summary's commit:** `git push -u origin m-series-hw-parakeet` (the user pushes).
2. **Update the installed skill** with the parser fix: `node bin/install.js --codex` from the
   repo.
3. **Phase 1**, following the baton:
   1. apply the R5 amendments in the plan (item 3's join: an audio-only graph, a
      `setpts`/`asetpts` rebase, display-geometry and rotation normalisation, a frame-identity
      oracle, codec-specific extradata; plus the `keyframe_snapped` source-frame rule, the
      corrected 29.97 pts sequence, and the audio-lag tolerance);
   2. run one Codex pass on the join;
   3. implement: refactor A, then the safe join, then items 1/3/2, then 7, then 4, then the MCP
      snapshot.
4. **Decide** the "garbage output reported as no speech" question.
5. **Phase 2 plan:** item 6 timeout scaling, the render/batch `stage_hw` roll-up, and
   `--segments` edit lists.
6. **Carried over** from earlier sessions: rerun the third Codex review of `3ff6462`; an
   optional upstream issue; an optional `--hw` demo.
