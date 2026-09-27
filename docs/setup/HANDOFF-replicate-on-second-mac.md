# Handoff: replicate the ffmpeg-skill (VideoToolbox + Parakeet) setup on this Mac

**For:** the coding agent on the user's second MacBook.
**Goal:** reproduce the first machine's setup exactly: the forked skill on branch
`m-series-hw-parakeet`, installed once and shared by Claude Code and Codex, with Parakeet
and whisper.cpp speech engines and GPU encoding on by default.
**Source of truth:** `docs/setup/m4-max-setup-inventory-2026-09-27.md` in the same repo.

No code changes are needed. The feature work is already committed and pushed to the fork.
This is installation and verification only.

## Ground rules (user's standing instructions)

- **Never run `git commit`.** Never push to `kajisho5/ffmpeg-skill`. This task shouldn't
  need any commit or push.
- **Don't fork again.** The fork `rymalia/ffmpeg-skill` already exists; clone it.
- **Don't run `npx ffmpeg-skill`** or a bare `node bin/install.js`. Both install upstream
  or a separate `~/.claude` copy, which would replace the symlink layout.
- **Look before overwriting or deleting.** If something already exists (a skill copy,
  `~/.zshenv` lines, models), inspect it and report it before replacing it.
- Put big downloads (about 6 GB total) where the steps say. Don't download into the repo.
- Stop and ask the user if the machine isn't Apple Silicon (`uname -m` ≠ `arm64`).
  VideoToolbox `--hw` and parakeet-mlx/Metal need it.

## Step 0 — Inspect the current state (report it before changing anything)

```sh
uname -m; sw_vers -productVersion
which ffmpeg ffprobe whisper-cli uv node python3 gh brew
ffmpeg -version | head -1; ffmpeg -hide_banner -encoders | grep -i videotoolbox
python3 --version; node --version; gh auth status
ls -la ~/.claude/skills/ffmpeg-skill ~/.agents/skills/ffmpeg-skill 2>&1
ls -la ~/projects/ffmpeg-skill 2>&1 | head -3
ls -la ~/.cache/whisper.cpp ~/.cache/parakeet.cpp ~/.local/libexec/parakeet.cpp 2>&1
ls -la ~/.local/bin/parakeet* 2>&1
grep -nE 'PARAKEET|FFMPEG_SKILL' ~/.zshenv 2>&1
echo "$PATH" | tr : '\n' | grep -n '.local/bin'
```

Expected on the reference machine: ffmpeg 9.0.x with `h264_videotoolbox`,
`hevc_videotoolbox` and `prores_videotoolbox`; whisper.cpp 1.9.x; Python 3.14; Node 24;
uv 0.12. Close versions are fine. The Python code is standard library only (3.9+).

## Step 1 — Prerequisites (install only what's missing)

```sh
brew install ffmpeg whisper-cpp uv gh python
brew install --cask font-dejavu
```

- `~/.local/bin` must be on `PATH`. If it isn't, add `export PATH="$HOME/.local/bin:$PATH"`
  to `~/.zshenv` (ask the user first).
- If `gh auth status` fails, ask the user to run `! gh auth login`. The user has no SSH
  keys; git rewrites GitHub SSH URLs to HTTPS.
- After the font install, check it with `fc-list | grep -i "DejaVu Sans"`. If it's
  missing, run `fc-cache -f` once.

## Step 2 — Clone the fork and set up the remotes

If `~/projects/ffmpeg-skill` already exists, inspect it (`git remote -v`, `git status`,
`git branch -vv`) and report before touching it. Otherwise:

```sh
cd ~/projects
git clone https://github.com/rymalia/ffmpeg-skill.git
cd ffmpeg-skill
git remote add upstream https://github.com/kajisho5/ffmpeg-skill.git
git remote set-url --push upstream DISABLED
git fetch upstream
git switch m-series-hw-parakeet          # auto-tracks origin/m-series-hw-parakeet
git branch -vv | grep m-series           # must show [origin/m-series-hw-parakeet]
git log --oneline -4                     # expect 49e08f9, 1922a59, 3ff6462, df5d273 (or newer on top)
```

## Step 3 — whisper.cpp models → `~/.cache/whisper.cpp/`

```sh
mkdir -p ~/.cache/whisper.cpp && cd ~/.cache/whisper.cpp
for m in base large-v3-turbo; do
  [ -f ggml-$m.bin ] || curl -fL --progress-bar -o ggml-$m.bin \
    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-$m.bin
done
shasum -a 256 ggml-base.bin ggml-large-v3-turbo.bin
# 60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe  ggml-base.bin
# 1fc70f774d38eb169993ac391eea357ef47c88757ef72ee5943879b7e8e2bc69  ggml-large-v3-turbo.bin
```

Both are required. `base` does language detection for `--engine auto`, and
`large-v3-turbo` is the `caption.py` default. `ggml-small.bin` and `ggml-small.en.bin`
were only used for benchmarking; skip them unless the user asks.

## Step 4 — parakeet-mlx (primary Parakeet engine)

```sh
uv tool install parakeet-mlx            # reference machine: v0.5.2
which parakeet-mlx                      # ~/.local/bin/parakeet-mlx
```

The model (`mlx-community/parakeet-tdt-0.6b-v2`, about 2.3 GB) downloads to
`~/.cache/huggingface/hub/` on the first transcription. Step 8 triggers that download.
Always use v2: parakeet-mlx's own default is v3, which dropped words in benchmarks
(6.17% vs 2.78% WER). The skill passes the model explicitly through `PARAKEET_MODEL`.

## Step 5 — parakeet.cpp v0.5.0 (secondary engine): real binaries + wrapper scripts

Real binaries go in `~/.local/libexec/parakeet.cpp/`. `~/.local/bin` gets small wrappers
that add a default `--model`. Don't put the real binaries in `~/.local/bin`, because that
would clobber the wrappers.

```sh
T=$(mktemp -d) && cd "$T"
curl -fsSL -o bin.tgz https://github.com/mudler/parakeet.cpp/releases/download/v0.5.0/parakeet-v0.5.0-bin-macos-metal-arm64.tar.gz
tar xzf bin.tgz
mkdir -p ~/.local/libexec/parakeet.cpp
install -m 755 parakeet-v0.5.0-bin-macos-metal-arm64/parakeet-{cli,server} ~/.local/libexec/parakeet.cpp/
shasum -a 256 ~/.local/libexec/parakeet.cpp/*
# c5915e86df54da4e5821b779648ff509d9f3650420ac541c7082fe399b35181d  parakeet-cli
# 27c658abeb62a6ec0f21d3b9feffdfddd22800246b051c0239be24f6e8c7e972  parakeet-server
~/.local/libexec/parakeet.cpp/parakeet-cli --version   # parakeet-cli 0.5.0
```

If Gatekeeper blocks the binary, report it to the user before clearing quarantine. On
the reference machine it ran without needing that.

Model:

```sh
mkdir -p ~/.cache/parakeet.cpp
curl -fL --progress-bar -o ~/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf \
  https://huggingface.co/mudler/parakeet-cpp-gguf/resolve/main/tdt-0.6b-v2-f16.gguf
shasum -a 256 ~/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf
# f8df7f5dc7b9ceb5cd0637a81194aab5d93022ace555ce81c8969c7a694b8f3d
```

(`tdt-0.6b-v3-f16.gguf` is optional and multilingual. Skip it unless the user asks.)

Wrappers. Write this exact content to **both** `~/.local/bin/parakeet-cli` and
`~/.local/bin/parakeet-server`, then `chmod 755` both:

```sh
#!/bin/sh
# Wrapper: adds a default --model when none is given. Override per run with --model,
# or set PARAKEET_CPP_MODEL. Real binary: ~/.local/libexec/parakeet.cpp/
real="$HOME/.local/libexec/parakeet.cpp/$(basename "$0")"
model="${PARAKEET_CPP_MODEL:-$HOME/.cache/parakeet.cpp/tdt-0.6b-v2-f16.gguf}"
for a in "$@"; do [ "$a" = "--model" ] && exec "$real" "$@"; done
if [ "$(basename "$0")" = "parakeet-server" ]; then
  exec "$real" --model "$model" "$@"
fi
case "$1" in
  transcribe|bench|bench-batch|bench-decode) sub="$1"; shift; exec "$real" "$sub" --model "$model" "$@" ;;
  *) exec "$real" "$@" ;;
esac
```

Check: `which parakeet-cli` → `~/.local/bin/parakeet-cli`.

(If this machine has an unrelated `~/.local/bin/parakeet` binary, leave it alone.)

## Step 6 — Shell environment

Append to `~/.zshenv` unless the lines are already there (check with `grep` first):

```sh
# parakeet: default to the English-only v2 model
export PARAKEET_MODEL="mlx-community/parakeet-tdt-0.6b-v2"

# ffmpeg-skill: VideoToolbox (GPU) encoding by default for re-encoding tools; delivery exports stay on CPU unless --hw
export FFMPEG_SKILL_HW=1
```

Then `source ~/.zshenv` in the current shell, or export both variables for the rest of
the session. New Claude Code and Codex sessions pick them up automatically.

## Step 7 — Install the skill (one copy, shared by Codex and Claude Code)

```sh
cd ~/projects/ffmpeg-skill
node bin/install.js --codex              # → ~/.agents/skills/ffmpeg-skill (real files)
```

Then point Claude Code at the same copy with a **relative** symlink. If
`~/.claude/skills/ffmpeg-skill` exists as a real directory (e.g. an earlier `npx` install),
diff it against the new copy and report the diff before removing it:

```sh
cd ~/.claude/skills
[ -d ffmpeg-skill ] && [ ! -L ffmpeg-skill ] && diff -rq ffmpeg-skill ../../.agents/skills/ffmpeg-skill | grep -v __pycache__ | head
# after reporting (and user OK if it held anything non-upstream):
rm -rf ffmpeg-skill && ln -s ../../.agents/skills/ffmpeg-skill ffmpeg-skill
ls -la ~/.claude/skills/ffmpeg-skill     # → ../../.agents/skills/ffmpeg-skill
diff -q ~/.claude/skills/ffmpeg-skill/SKILL.md ~/projects/ffmpeg-skill/SKILL.md && echo match
```

To update the installed skill later, rerun `node bin/install.js --codex` from the fork
checkout.

## Step 8 — Verify (report the results)

Run all of these with `FFMPEG_SKILL_HW` and `PARAKEET_MODEL` exported.

1. **Contract / doctor**
   ```sh
   S=~/.claude/skills/ffmpeg-skill/scripts
   python3 $S/_contract.py doctor --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print("ok",d.get("ok"),"hw",d.get("hw"),"missing",d.get("missing"),"missing_optional",d.get("missing_optional"))'
   ```
   Expect `ok True`, `hw {'platform_ok': True, 'default_on': True}` and empty `missing`.
   `external:parakeet` should show as available. If the JSON shape differs, print the
   whole output and read it; don't guess.
   (Piping into `head` can print a `BrokenPipeError` traceback. That's harmless.)

2. **GPU encode through the installed skill.** Make a test clip in a temp dir and fit it:
   ```sh
   T=$(mktemp -d) && cd "$T"
   ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc2=size=1920x1080:rate=30:duration=5 \
     -f lavfi -i sine=frequency=440:duration=5 -c:v libx264 -c:a aac -shortest src.mp4
   python3 $S/fit.py src.mp4 --height 720 --json
   ```
   Expect `verified: true`, `encoder: h264_videotoolbox` and `hw.source: env`. Repeat with
   `--no-hw` and expect `libx264`.

3. **Speech engines.** Use a short English clip with speech. If the user has none, make
   one with `say -o speech.aiff "The quick brown fox jumps over the lazy dog." && ffmpeg
   -i speech.aiff speech.wav`, wrapped in a video if caption.py requires video. Run
   `caption.py --transcribe` once per engine: `--engine parakeet-mlx` (this downloads the
   2.3 GB model the first time), `--engine parakeet.cpp`, and `--engine whisper.cpp`.
   Check `references/scripts.md` for exact flags. Each should report its engine under
   `transcription` in the JSON and produce sensible text.

4. **Test suite (optional, ~several minutes).** Start with an empty `tests/out/` and run
   only one test process at a time, because they share output names:
   ```sh
   cd ~/projects/ffmpeg-skill && rm -rf tests/out
   env -u FFMPEG_SKILL_HW -u PARAKEET_MODEL python3 tests/test_all.py
   python3 tests/test_contract.py
   ```
   Reference: 608 OK (2 skipped) and contract 150 OK (1 skipped). The fixtures already
   scrub the env vars; `env -u` is belt-and-braces. Python 3.14 `SyntaxWarning`s from
   `_ass_overlay.py` / `_common/drawtext.py` come from upstream and are harmless.

## Step 9 — Report back to the user

Give a short table: each step done, skipped (already present) or failed, with versions
and the key verification values (`doctor ok`, encoder name, engine outputs, test counts).
List anything you found pre-existing and left alone. Suggest no git commands; nothing
here should need a commit.

## Known gotchas

- `doctor` reports `external:whisper` from the binary's presence alone. It won't tell you
  a model is missing. Step 3 is what makes whisper actually work.
- `export.py` delivery presets stay on the CPU even with `FFMPEG_SKILL_HW=1`, by design
  (VideoToolbox needs 1.2–2.5× the bytes at matched quality). `render.py`/`batch.py --hw`
  is the explicit GPU-export switch.
- H.264 VideoToolbox tops out at 4096 wide. The skill falls back to the CPU on its own and
  notes it in `hw.notes`.
- Reading files under `~/Downloads` may need permission in Claude Code. Copying into the
  scratchpad works.
