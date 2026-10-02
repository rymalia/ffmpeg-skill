# PR drafts: rymalia/ffmpeg-skill → kajisho5/ffmpeg-skill

Base: every branch is rebased onto `upstream/main` at `9392328` (v2.4.0, which added upstream #299 and #300). These features are not in 2.4.0, so the docs call them "Unreleased", never "2.4".

Paste these descriptions over GitHub's pre-filled body. For a one-commit PR, GitHub fills the body from the commit message, and A's message mentions the Opus/Codex review.

Order: **A, B and E now** (independent of each other). **C1 and C2 together** (independent). **D as a draft stacked on C1**, marked ready once C1 merges.

After each merge, the remaining PRs conflict in `CHANGELOG.md` (every pair does). Other conflicts:
- C1 × C2 (and C2 × D): `scripts/_contract.py`, `tests/test_all.py`, `docs/contract.md`, `docs/design-decisions.md`.
- B × C1, B × C2, B × D: `docs/design-decisions.md`, where each appends a section at the end; keep both.

`tests/fixtures/mcp_tools.json` merges cleanly in every pair. If it ever conflicts, regenerate it with `UPDATE_MCP_SNAPSHOT=1 python3 tests/test_contract.py`.

---

## A: `pr/graphics-wrapped-title` (1 commit)

**fix(graphics): a wrapped title is drawn on its lines**

`graphics.py` wrapped a title that did not fit, and sized its card for two lines. But `drawtext_text_opts` stripped every control character, the newline included. So "WHO SHOWS UP?" at `--scale 1.4` on a 1080x1920 frame, wrapped as `"WHO\nSHOWS UP?"`, lost its line break and rendered on one line as "WHOSHOWS UP?", running off both edges.

- The drawtext text file keeps newlines (CR and CRLF become LF). A tab, vertical tab or form feed becomes a space.
- New `drawtext_center_align()`: `text_align=C` on FFmpeg ≥ 6.1, added to the centred title, hook and meme templates.

**For review:** every drawtext caller (`overlay.py --text`, lower thirds, stickers) now renders a newline in the user's text as a line break. That is intended, but it is a behaviour change.

**Tests:** `MultiLineDrawtextTests`. `test_picture`: 211 OK (3 skipped).

---

## B: `pr/join-no-hole` (1 commit)

**fix(join): a plain cut leaves no hole where a clip's sound outruns its picture**

With `--transition none`, the concat filter starts each clip after the *longer* stream of the one before. So a clip whose sound runs past its picture left a hole in the video: 0.3 s for a padded music bed, one frame for an ordinary 20 ms AAC tail. The run still reported success.

- Every clip now gets one length for both streams (`clip_length`, the same rule the crossfade path uses):
  - when the sound runs more than a frame past the picture, the last frame is held;
  - otherwise the sound tail is trimmed.
- `-fps_mode passthrough` now covers the plain cut too.

**For review:**
- `expected_duration` now counts `clip_length`, not container durations.
- #300's `silent[].at`/`end` now counts the same lengths on a plain cut, so it gives the position of the clip's actual picture and sound. The audio-only path keeps `place_silent(durs, d)`.

**Tests:** `test_join_none_holds_a_picture_shorter_than_its_sound`, `test_join_none_trims_a_sound_tail_under_a_frame`. `test_editing`: 133 OK.

---

## E: `pr/loop-boomerang` (1 commit)

**feat(loop): `--boomerang` plays a clip forward then backward**

The frames play 0..N-1, then N-2..1, repeated, so the loop never jumps. Unlike the common split/reverse/concat recipe, each turnaround frame is shown once.

- `--times` counts round trips, and 1 is allowed. `--duration` still hits its target.
- The output is constant-rate at the source's nominal frame rate. A variable-frame-rate source is retimed by frame index.
- Audio is dropped, with a `notes` line explaining why.

**For review:** the `loop` filter's 32767-frame cap and the ~2 GiB memory warning.

**Tests:** 7 new tests in `test_editing`, including frame order checked by `framemd5` and a VFR source. `test_editing`: 138 OK. Contract: 152 OK (1 skipped).

---

## C1: `pr/hw-videotoolbox` (6 commits)

**feat: opt-in Apple VideoToolbox encoding (`--hw`)**

`--hw` / `--no-hw` works on every re-encoding tool and on `export.py`. `FFMPEG_SKILL_HW=1` makes it the machine default, except for `export.py`'s delivery presets, and `render.py` / `batch.py --hw` apply it to every stage.

- **Codecs:** h264, hevc (HDR Main10 with HDR10 side data) and prores. AV1 stays on SVT-AV1. Apple Silicon only.
- **Quality mapping:** CRF maps to `-q:v`, fitted with `tests/bench_vt.py`. The bench sweeps the GPU quality against the CPU encode's SSIM, pairing frames by index. HDR sources get their own curve.
  - At matched quality the GPU files run 1.1–2.9× the CPU bytes on SDR and 1.9–3.5× on HDR.
  - An encode chosen by `FFMPEG_SKILL_HW` rather than `--hw` says so in `hw.notes`.
- **Colour tags:** BT.709 tags go through `h264_metadata` / `hevc_metadata`, so an untagged source is never colour-converted.
- **Fallback:** a job the GPU refuses is re-encoded on the CPU. This includes an odd-sized source's even-dimension retry, whose scale is kept in the CPU fallback.
- **Reporting:** results carry `encoder` and `hw`, and the render cache key includes the GPU setting.

**For review:**
- `run()`'s GPU → CPU fallback, which rewrites a slice of the command, and `restate_last_swap` for export;
- the flag vs environment semantics;
- the fitted curve constants.

**Tests:** `tests/test_accel.py`, with real VideoToolbox encodes on Apple Silicon only. Full suite: 602 OK (3 skipped). `test_accel`: 25 OK. Contract: 152 OK (1 skipped).

---

## C2: `pr/asr-parakeet` (5 commits, independent of C1)

**feat: Parakeet speech engines for `--transcribe`**

`parakeet-mlx` and `parakeet.cpp` for `caption.py --transcribe` and `silence.py --filler --transcribe`.

- **Choosing an engine:** `--engine` or `FFMPEG_SKILL_ASR_ENGINE` picks one. `auto` runs Parakeet for English speech and Whisper for anything else. English is decided by an explicit `--language`, else by whisper.cpp's language detector, else it is assumed, and the result says so.
- **Failed runs:** an engine that exits 0 but writes something that isn't a transcript counts as a failed run, and `auto` moves on to the next engine. Malformed JSON never raises.
- **Reporting:** results carry `transcription` (engine, model, language, routing), in every `--mode`. New optional capability: `external:parakeet`.
- **Model default:** `caption.py --model` stays `base`, which is what the install hint tells whisper.cpp users to download. The Parakeet engines ignore a model name that isn't a Parakeet model.

**For review:**
- the "English assumed" routing when no detector is installed;
- how the subprocess JSON is parsed;
- the module-level `LAST_RUN` / `LAST_WORDS` hand-off to callers.

**Tests:** `tests/test_asr.py` (engines driven through fake binaries on an otherwise empty PATH), plus `WhisperDefaultModelTests`. Full suite: 598 OK (3 skipped). `test_asr`: 20 OK. Contract: 152 OK (1 skipped).

**Merge note:** if C1 merges first, this PR gets conflicts in `_contract.py`, where both add a function at the same spot (keep both), and in `test_all.py`, `docs/contract.md`, `docs/design-decisions.md` and `CHANGELOG.md`.

---

## D: `pr/cut-exact-joins` (9 commits, stacked on C1, draft until C1 merges)

**cut.py: exact `--segments` copy joins, and reports that say what happened**

- **Exact joins:** a `--segments` stream-copy join is frame-exact, or it isn't a copy. Parts are planned from the source's packets and the join is measured (`join_check`). Mismatched parts are re-cut from the source instead of going through the concat demuxer.
- **Single-part copies:** a single MP4/MOV copy keeps its edit list. `--accurate` and the join re-cut seek one second early, so frames just before a keyframe are kept.
- **VFR detection:** the VFR guard measures packet timing in sampled windows instead of comparing frame rates. `--vfr-copy` keeps a copy anyway.
- **Codec:** a re-encoded SDR HEVC source stays HEVC.
- **Reporting:** `reencode_reason`, per-segment precision and `segment_end_snap_seconds`. A segment past the video's end leaves no hole at its join.
- **Last GOP:** a segment in the last GOP is judged by the join check, not reported as a tolerance miss.
  - `--tolerance -1` is honoured there.
  - On B-frame video that join is re-cut. A mid-GOP copy of it isn't exact: main's "copy" gave 82 frames for 78.

**Depends on C1:** `join_from_source` switches the GPU off for a CPU re-encode of a GPU-refused chunk, and the result still reports `hw`.

**For review:** `plan_part`, `open_join_key` and `check_join`, the edit list vs `make_zero` semantics, and the `measure_frame_timing` windows.

**Tests:** `tests/test_cut_copy.py`, plus `test_editing`, `test_orchestration` and the contract suite: `test_cut_copy` 93 OK, `test_editing` 132 OK, `test_orchestration` 80 OK, `test_delivery` 21 OK, `test_accel` 25 OK, contract 152 OK (1 skipped).
