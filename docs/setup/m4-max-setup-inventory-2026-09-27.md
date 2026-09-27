# ffmpeg-skill setup inventory — M4 Max (2026-09-27)

Everything installed or changed on the first MacBook (M4 Max) for the ffmpeg-skill
VideoToolbox + Parakeet work. It was checked against the live machine on 2026-09-27, not
only taken from the session summaries. Background and rationale:
[session-summary-2026-09-27-videotoolbox-parakeet-fork.md](../session-summaries/session-summary-2026-09-27-videotoolbox-parakeet-fork.md),
[session-summary-2026-09-27-hw-real-video-test.md](../session-summaries/session-summary-2026-09-27-hw-real-video-test.md).

## 1. Pre-existing prerequisites (installed before this work, not changed)

| Tool | Version on this machine | Source |
|---|---|---|
| ffmpeg / ffprobe | 9.0.2 (VideoToolbox encoders built in) | Homebrew `ffmpeg` |
| whisper.cpp (`whisper-cli`) | 1.9.4 | Homebrew `whisper-cpp` |
| Python | 3.14.7 | Homebrew `python@3.14` (`/opt/homebrew/bin/python3`) |
| Node | v24.18.0 | nvm |
| uv | 0.12.19 | Homebrew `uv` |
| gh | authenticated as `rymalia` | Homebrew |
| DejaVu fonts | 2.37 | `brew install --cask font-dejavu` (reported already installed) |

`~/.local/bin` is on `PATH`. `~/.local/bin/parakeet` (a May 2026 Mach-O binary taking
`.safetensors`) predates this work, is **unrelated**, and the skill doesn't use it.

## 2. Git repository

| Item | Value |
|---|---|
| Fork | `github.com/rymalia/ffmpeg-skill`, created with `gh repo fork kajisho5/ffmpeg-skill --clone --default-branch-only` into `~/projects/ffmpeg-skill` |
| Remotes | `origin` = `https://github.com/rymalia/ffmpeg-skill.git`; `upstream` = `https://github.com/kajisho5/ffmpeg-skill.git`, **push URL set to `DISABLED`** |
| Base | upstream `main` at `df5d273` (package version 2.3.1) |
| Branch | `m-series-hw-parakeet`, tracking `origin/m-series-hw-parakeet` |
| Commits | `3ff6462` feat (22 files, +1199/−78), `1922a59` + `49e08f9` session-summary docs. All pushed. |

Files changed by `3ff6462`:

```
CHANGELOG.md  README.md  SKILL.md  docs/contract.md  docs/design-decisions.md
references/gotchas.md  references/scripts.md
scripts/_common/{asr,decision,emit,runner}.py  scripts/_contract.py
scripts/{batch,caption,export,render,silence}.py
tests/_fixtures.py  tests/fixtures/mcp_tools.json  tests/test_accel.py (new)
tests/test_all.py  tests/test_contract.py
```

What those changes do:

- `--hw` / `--no-hw` (Apple VideoToolbox). Opt-in per run. `FFMPEG_SKILL_HW=1` makes it
  the machine default for re-encoding tools, but not for `export.py` delivery presets.
  `render.py`/`batch.py --hw` also puts the export on the GPU. If VideoToolbox fails
  (e.g. H.264 wider than 4096) the run retries once on the CPU. Results report `encoder`
  and `hw {requested, source, used, notes}`.
- Parakeet ASR engines (`--engine parakeet-mlx | parakeet.cpp | auto | ...`) in
  `caption.py` and `silence.py`. `auto` uses Parakeet only for English. `caption.py
  --model` now defaults to `large-v3-turbo`. New contract capability `external:parakeet`
  and a new `doctor.hw` block.
- 31 new tests in `tests/test_accel.py`. Final clean run: `test_all` 608 OK (2 skipped),
  contract 150 OK (1 skipped).

## 3. Speech engines and models (outside the repo)

### whisper.cpp models → `~/.cache/whisper.cpp/`

The skill searches `~/.cache/whisper.cpp/ggml-<name>.bin`. Homebrew's bundled
`for-tests-ggml-tiny.bin` is outside that path and isn't found.

| File | Size (bytes) | Needed? | URL |
|---|---|---|---|
| `ggml-base.bin` | 147,951,465 | **Yes.** Used for language detection in `--engine auto` (the smallest installed of tiny/base/small) | `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin` |
| `ggml-large-v3-turbo.bin` | 1,624,555,275 | **Yes.** The `caption.py --model` default | `.../resolve/main/ggml-large-v3-turbo.bin` |
| `ggml-small.bin` | 487,601,967 | Optional (benchmark only) | `.../resolve/main/ggml-small.bin` |
| `ggml-small.en.bin` | 487,614,201 | Optional (benchmark only) | `.../resolve/main/ggml-small.en.bin` |

SHA-256: base `60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe`,
large-v3-turbo `1fc70f774d38eb169993ac391eea357ef47c88757ef72ee5943879b7e8e2bc69`.

### parakeet-mlx (primary Parakeet engine)

- `uv tool install parakeet-mlx` installed **v0.5.2**. Its venv is at
  `~/.local/share/uv/tools/parakeet-mlx/`, symlinked as `~/.local/bin/parakeet-mlx`.
- Model weights download to the Hugging Face cache on first use:
  `~/.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v2` (2.3 GB). The
  v3 model (2.3 GB) is also cached, from benchmarking only. Other `parakeet` CoreML
  entries in the HF cache (FluidInference, aufklarer) are unrelated to this work.

### parakeet.cpp v0.5.0 (secondary Parakeet engine)

- Release tarball
  `https://github.com/mudler/parakeet.cpp/releases/download/v0.5.0/parakeet-v0.5.0-bin-macos-metal-arm64.tar.gz`.
  Only the `bin` tarball is used; the `lib` tarball was downloaded but isn't needed. The
  binaries link only system libraries (checked with `otool -L`).
- Real binaries in `~/.local/libexec/parakeet.cpp/`:
  - `parakeet-cli` sha256 `c5915e86df54da4e5821b779648ff509d9f3650420ac541c7082fe399b35181d`
  - `parakeet-server` sha256 `27c658abeb62a6ec0f21d3b9feffdfddd22800246b051c0239be24f6e8c7e972`
- `~/.local/bin/parakeet-cli` and `~/.local/bin/parakeet-server` are identical
  `/bin/sh` wrapper scripts (mode 755). They add
  `--model ${PARAKEET_CPP_MODEL:-~/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf}` when no
  `--model` is given. The full text is in the handoff doc.
- GGUFs in `~/.cache/parakeet.cpp/` from `https://huggingface.co/mudler/parakeet-cpp-gguf/resolve/main/<file>`:
  - `tdt-0.6b-v2-f16.gguf`: 1,404,218,656 bytes, sha256 `f8df7f5dc7b9ceb5cd0637a81194aab5d93022ace555ce81c8969c7a694b8f3d`. **Required.**
  - `tdt-0.6b-v3-f16.gguf`: 1,441,046,400 bytes. Optional (multilingual; benchmark only).

## 4. Shell environment — `~/.zshenv` (appended)

```sh
# parakeet: default to the English-only v2 model
export PARAKEET_MODEL="mlx-community/parakeet-tdt-0.6b-v2"

# ffmpeg-skill: VideoToolbox (GPU) encoding by default for re-encoding tools; delivery exports stay on CPU unless --hw
export FFMPEG_SKILL_HW=1
```

(`~/.zshenv` also sources `$HOME/.cargo/env`. That line predates this work.)

## 5. Installed skill layout

| Path | What |
|---|---|
| `~/.agents/skills/ffmpeg-skill/` | Real files, from `node bin/install.js --codex` run in the fork checkout. Codex reads this path. |
| `~/.claude/skills/ffmpeg-skill` | Relative symlink `→ ../../.agents/skills/ffmpeg-skill`. It replaced an earlier plain `npx ffmpeg-skill` copy. |

Verified on 2026-09-27: installed `scripts/` and `SKILL.md` match the repo (the only
difference is a `.DS_Store`). `doctor --json` through the symlink gives `ok: true`,
`hw {platform_ok: true, default_on: true}` and `external:parakeet` available.

## 6. Non-durable / local-only artifacts

- `~/Downloads/ffmpeg-skill-hw-test/`: Reels `--hw` vs `--no-hw` test renders, JSON
  results, contact sheets.
- Benchmark and calibration scratch files were in the session scratchpad and are gone.

## 7. Reference numbers (M4 Max)

| ASR, 8 min LibriSpeech | Time | WER |
|---|---|---|
| whisper.cpp large-v3-turbo | 12.3 s | 2.43% |
| parakeet-mlx v2 | 4.0 s | 2.78% |
| parakeet.cpp v2 | 7.8 s | 2.87% |
| whisper.cpp base | 4.9 s | 7.13% |

Reels render of a real clip: `--hw` took 14.3 s and produced 45.06 MB; `--no-hw` took
21.7 s and produced 28.33 MB. SSIM between them was 0.983 and both were `verified: true`.
