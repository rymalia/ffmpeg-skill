---
title: ffmpeg-skill carry-forward guide
date: 2026-09-27
applies_to: rymalia/ffmpeg-skill fork (branch m-series-hw-parakeet) and upstream kajisho5/ffmpeg-skill
sources:
  - docs/session-summaries/session-summary-2026-09-17-ffmpeg-setup-video-split.md
  - docs/session-summaries/session-summary-2026-09-19-ffmpeg-upgrade-self-healing.md
  - docs/session-summaries/session-summary-2026-09-21-volleyball-corner-mask.md
  - docs/session-summaries/session-summary-2026-09-21-ffmpeg-masking-slicing.md
  - docs/session-summaries/session-summary-2026-09-22-scoreboard-overlay-composite.md
  - docs/session-summaries/session-summary-2026-09-24-lossless-volleyball-trim.md
  - ffmpeg-skill/docs/session-summaries/session-summary-2026-09-27-videotoolbox-parakeet-fork.md
  - memories: ffmpeg-full-selfhealing, ffmpeg-skill-masking-gotchas, ffmpeg-skill-timeout-default,
    ffmpeg-lossless-trim-plain-command, brew-uses-intersection-gotcha
---

# ffmpeg-skill carry-forward guide

What we learned using the original `ffmpeg-skill` on this machine. Read it before starting an
ffmpeg-skill session, including one on the forked version. Every item below came from a real
failure or a verified fix, not theory.

**Core rule:** the skill sometimes makes choices without telling you: hybrid re-encodes, the VFR
guard, the 30-minute timeout, and the fork's hardware-encoding env default. After every run, check
`mode`, `reencoded`, `encoder`, `hw` and the output codec. Don't assume a lossless or CPU path.

---

## 0. Before you start (setting up the fork on this machine)

- [ ] **Block pushes to upstream first.** On this machine, `git remote -v` in
      `~/projects/ffmpeg-skill` shows a real push URL for `upstream` (`kajisho5/ffmpeg-skill`).
      The other machine has it set to `DISABLED`. Fix it:
      ```sh
      git -C ~/projects/ffmpeg-skill remote set-url --push upstream DISABLED
      ```
      Only push to `origin` (the fork), and always as `git push -u origin <branch>`.
- [ ] **Install the fork with `node bin/install.js --codex`** from the repo. This writes the real
      files to `~/.agents/skills/ffmpeg-skill`. `~/.claude/skills/ffmpeg-skill` is already a
      symlink to that directory, so Claude Code and Codex share one copy. Don't run plain
      `npx ffmpeg-skill` or `node bin/install.js`: they target `~/.claude/skills` and would
      likely replace the symlink with a separate copy.
      - On this machine the symlink is absolute. On the other machine it's relative
        (`../../.agents/skills/ffmpeg-skill`). Either works.
- [ ] **Install the speech models.** They aren't on this machine yet: `~/.cache/whisper.cpp/`
      doesn't exist and `parakeet-mlx` isn't installed. `doctor` reports `external:whisper` as
      available just because the binary exists, even with no usable model.
      - whisper.cpp models go in `~/.cache/whisper.cpp/`. At minimum get `ggml-large-v3-turbo.bin`
        (best accuracy, and the fork's `caption.py` default). The other machine also has
        `ggml-base.bin`, `ggml-small.bin` and `ggml-small.en.bin`.
      - `uv tool install parakeet-mlx`, which installs to `~/.local/bin/parakeet-mlx`.
      - Optional: parakeet.cpp v0.5.0. Put the real binaries in `~/.local/libexec/parakeet.cpp/`
        and the wrapper scripts (`parakeet-cli`, `parakeet-server`) in `~/.local/bin`. Put the
        GGUF models in `~/.cache/parakeet.cpp/`. When you upgrade parakeet.cpp, never drop the
        binaries into `~/.local/bin`, because that overwrites the wrappers.
- [ ] **Add these to `~/.zshenv` to match the other machine** (but read §6 first):
      ```sh
      export PARAKEET_MODEL="mlx-community/parakeet-tdt-0.6b-v2"
      export FFMPEG_SKILL_HW=1
      ```
      Use Parakeet **v2**. v3 dropped words in the benchmark (6.17% WER vs 2.78%), and parakeet-mlx
      uses v3 by default unless you pass a model.
- [ ] **Run the checks:** `doctor --json` should show `ok: true`,
      `hw {platform_ok: true, default_on: …}`, and `external:parakeet` available. Then run one real
      `fit.py` encode and confirm `verified: true`.

---

## 1. The ffmpeg build

> **To set this up on a new machine, follow
> [`ffmpeg-full-self-healing-setup.md`](ffmpeg-full-self-healing-setup.md).** It has the full
> healer script and the wrapper, plus verification steps. This section only describes the setup;
> it doesn't contain the code. (Until 2026-10-09 this heading said "already set up here; nothing to
> redo", so an agent working through this guide on the second Mac skipped it.)

- **Homebrew split ffmpeg at v8.** The plain `ffmpeg` formula, and every `ffmpeg@N` from 8 on, is
  now a lean build: no freetype/libass/fontconfig/harfbuzz, which means **no `drawtext` and no
  subtitles**. The full build is only available as `ffmpeg-full`: keg-only (brew doesn't link it by
  default), always the latest major, and there's no `ffmpeg-full@N`. `ffmpeg@7` was the last
  all-in-one build and is kept as a fallback.
- **The active `ffmpeg` is `ffmpeg-full`, force-linked over the lean formula:**
  ```sh
  brew unlink ffmpeg && brew link --overwrite --force ffmpeg-full
  ```
  Keep the lean `ffmpeg` installed but unlinked, because `ocrmypdf`, `unpaper` and `vhs` depend on
  it. `brew doctor` may warn about the force-linked keg. That's expected.
- **Every `brew upgrade` that touches ffmpeg relinks the lean build on top.** It happens every time.
  This is repaired automatically:
  - `~/.local/bin/ensure-ffmpeg-full` is an idempotent healer and a silent no-op when things are
    already correct.
  - The `brew()` wrapper in `~/.zshrc` runs it after `upgrade|install|reinstall|link|unlink|uninstall`.
  - The wrapper only runs in **interactive zsh**. If a script or an agent's shell changed brew,
    run `ensure-ffmpeg-full` by hand.
- **Quick check:** `readlink "$(which ffmpeg)"` should include `/ffmpeg-full/`, and the skill's
  `doctor` should report `filter:drawtext`, `filter:ass` and `filter:subtitles`.
- **`brew uses --installed a b` returns the intersection, not the union.** A combined query can
  come back empty even when a real dependent exists. Query each formula on its own before
  uninstalling anything.

---

## 2. Cutting and trimming

### 2.1 `cut.py` can re-encode to H.264 without telling you
By default, when a cut point is more than 0.5 s from a keyframe, `cut.py` switches to
**`mode: hybrid`**. That re-encodes and loses both losslessness and the HEVC codec, with no warning.

- For a copy with no re-encode, pass **`--tolerance -1`**, which snaps to a keyframe instead.
- **Always probe the output afterwards** and confirm `reencoded: false`, `mode: copy`, and that the
  codec is unchanged. In one slicing pass, clip A stayed HEVC while clips B–G had quietly become
  H.264.

### 2.2 The VFR guard overrides `--tolerance -1`
If `probe.py` reports `variable_frame_rate_suspected: true`, `cut.py` forces `--accurate`: a full
x264 re-encode that also drops HEVC. `--tolerance -1` doesn't prevent it, and no flag turns it off
(`scripts/cut.py` around line 300; the fork didn't change it). iPhone/Core Media HEVC trips this
guard because its average frame rate is 29.979 vs a nominal 30.
**A lossless trim of such a file can't be done through `cut.py`.** Use §2.3.

### 2.3 Lossless start-trim: use the plain command with no extra flags
```sh
ffmpeg -ss 00:07:35 -i in.mp4 -c copy out.mp4
```
- The MP4 muxer writes an **edit list**. The file data starts at the previous keyframe, the
  pre-roll is hidden, and playback starts at exactly T. You get every frame and the full tail, and
  a 70-minute 3.8 GB file took 17 s.
- **Don't add timestamp flags.** On Core Media HEVC, which runs about 3.6 s ahead in display time
  vs decode time:
  - `-avoid_negative_ts make_zero` and output-side `-ss` each gave about 3.7 s of audio with no
    picture.
  - A negative `-output_ts_offset` fixed the start but **silently dropped the last 3.7 s**.
  - Every bad variant exited 0.
- **Verify it** (these checks are what separated the good output from the bad ones):
  - Both streams have `start_time` 0.
  - Video packet count and last PTS match the source from T onward, so the tail is intact.
  - Mean absolute pixel diff between output t=0 and source T is 0.
  - Audio cross-correlation lag between output and source is 0 samples.
  - `-ignore_editlist 1` shows whether packets are actually missing or just hidden.
- Try the plain command first. Add flags only when one of these checks fails.
- Caveat: a player that ignores edit lists will show the pre-roll. Modern players respect them.
- `ffprobe` frame output filtered to key frames can mislead: the first *keyframe* may display at
  0.767 s, while the non-key frames from 0.000 still decode fine.

### 2.4 Keyframe snap can be large
A stream-copy cut snaps to a keyframe. Phone HEVC here had a keyframe about every 0.93 s, but the
skill's own x265 `medium` encodes had a GOP of about 8 s, so a "remove 90 s" trim actually removed
83.4 s. If the exact frame matters, use `--accurate`, which re-encodes. Snapping also adds about
0.5–1.3 s of lead-in per slice and can make adjacent slices overlap slightly.

### 2.5 Finding cut points
Use `scenes.py --threshold 0.3` to find hard cuts, then confirm the exact frame with a frame
montage (for example frames 1805–1810). A cut that isn't on a keyframe needs `--accurate`.

---

## 3. Masking, blurring and overlays

### 3.1 Shapes
`crop` only makes rectangles, and `redact.py` only blurs rectangles. For a diagonal or polygon
region, build a **full-frame RGBA PNG mask**: opaque where masked, transparent elsewhere.
Composite it rather than cropping, so the full 16:9 frame is kept.

### 3.2 Detect the operator's guide lines computationally, not by eye
```python
from PIL import Image
im = Image.open(path).convert("RGB"); W, H = im.size; px = im.load()
def is_green(r, g, b): return g > 150 and r < 120 and b < 120 and g - r > 60 and g - b > 60
# per-row center x of the drawn line:
centers = {y: (min(xs) + max(xs)) / 2 for y in range(H)
           if (xs := [x for x in range(W) if is_green(*px[x, y])])}
```
- Fill each row from the line to the frame edge: `[center, W]` for "right of line",
  `[0, center]` for "left of line". Interpolate across gaps and extrapolate to `y = 0`. This
  follows bends and notches exactly, which picking a few polygon vertices doesn't.
- **Red bounding boxes:** threshold the red pixels, then read dense row/column profiles to find the
  border lines and ignore stray red text.
- **Preview the mask composited on a clean still before any long encode.**

### 3.3 Solid black region (supported by the skill)
```sh
overlay.py clip.mp4 --image mask.png --position 0,0
```

### 3.4 Polygon blur (no script does this; use a raw filtergraph)
```sh
ffmpeg -i clip.mp4 -loop 1 -framerate 30 -i mask.png \
  -filter_complex "[0:v]split=2[base][pre];[pre]gblur=sigma=22[bl];\
[1:v]format=rgba,alphaextract[al];[bl][al]alphamerge[blA];\
[base][blA]overlay=0:0:shortest=1[out]" \
  -map "[out]" -map "0:a:0?" -t <DURATION> \
  -c:v libx265 -preset medium -crf 18 -pix_fmt yuv420p -tag:v hvc1 \
  -movflags +faststart -c:a aac -b:a 192k out.mp4
```
Two things in this recipe are required:
1. **Never use `maskedmerge`.** A gray mask makes it convert every input to grayscale, which strips
   the color from the whole frame. `alphamerge` plus `overlay` keeps the color.
2. **`-loop 1` makes the mask an infinite stream.** `alphamerge`/`overlay` run until their longest
   input, so without **both** `-t <clip_duration>` and `overlay=…:shortest=1` the encode never
   stops. A 90 s clip grew to 208 MB after about 20 CPU-minutes. `overlay.py` avoids this because
   it adds its own `-t`.

Test the filtergraph on a single frame before the full encode. Tell the user when you've stepped
outside the skill's scripts.

### 3.5 Moving another video's graphic into this one (scoreboard overlay)
- `overlay.py --video` composites the **whole** layer, so crop the graphic out first with
  `crop.py`. A static crop box works when the graphic doesn't move on screen.
- Trim a few pixels off the crop edges to remove rounded corners if you want a clean rectangular
  strip.
- Scale to keep the same fraction of the frame. A 920 px bar on 720p needed 1.5× on 1080p. Upscaling
  720p softens it slightly.
- If the overlay source is shorter than the base, `freeze.py --mode extend` holds its last frame.
- If both sources are CFR at the same fps and already in sync, overlaying at 0:0 keeps the graphic
  locked to the frames with no offset math.
- Build a 15 s sample of each layout and get approval before the full-length run.

### 3.6 Cropping out padded or letterboxed content
Run `cropdetect.py`. Equal top and bottom bars are a strong sign of real letterbox padding. Low
confidence (such as 0.54) can come from an end card of a different size, so confirm the crop on a
contact sheet before committing.

---

## 4. Long jobs

- **Every skill script defaults to `--timeout 1800` (30 min)** and kills the job with nothing
  written (`kind: timeout`). This is the skill's own limit, not ffmpeg's or the OS's. For anything
  with an ETA near or above about 25 min, set `--timeout` generously above the real ETA up front
  (for example `--timeout 5400`).
- **Don't change `--preset` (for example medium → fast) to dodge the timeout.** It deviates from
  the settings the user approved in the sample. The user flagged it when it happened. Raise the
  timeout and keep the preset.
- Reference speeds: x265 `medium` CRF 18 with full-frame `gblur` took about 20–24 min per 24 min of
  1080p. The scoreboard overlay encodes took about 32–54 min for 41 min of 1080p. Stream-copy cuts
  of 1 GB slices take a couple of minutes (limited by disk speed).
- **Run CPU-heavy encodes one at a time.** Parallel runs compete for the CPU.
- Detached `nohup … &` encodes keep running through session forks and sleep, but the session
  doesn't track them. Add a `run_in_background` waiter (`while kill -0 <pid>; do sleep 30; done`)
  to get notified when it finishes, and read the process's own progress log to confirm.
- If a file is growing far past its expected size, it's usually the infinite-loop bug from §3.4.

---

## 5. Shell, harness and verification traps

- **zsh treats an unquoted `-map 0:a:0?` as a glob.** You get "no matches found", ffmpeg never
  starts, and a following `echo $?` still prints `0`. Always quote map specs and `[labels]`.
- **zsh doesn't word-split `$VAR`.** Use arrays (`B=(...)`, then `$B`) for shared ffmpeg argument
  lists.
- **`look.py -o name.png` writes relative to the shell's working directory**, which the session
  resets between commands (often to `~/projects`). Pass absolute `-o` paths, and delete
  verification PNGs from the user's folders when you're done.
- **`look.py` timestamp labels are drawn on the frame grab only**, not the video. Say so each time
  you show one.
- **Attached images sometimes arrive as a generic "PNG" icon.** Find the real file by modified time
  in `~/Downloads`, `~/Pictures` or the footage folder (for example `vlcsnap-*.png`), and read it
  directly.
- **Check every render on real frames** (`look.py` single frames or contact sheets). A probe can't
  tell you whether a mask or overlay landed in the right place.
- Keep the source codec and quality when no delivery target is named. For the volleyball footage
  that was HEVC x265 `medium` CRF 18 with `-tag:v hvc1`. Use H.264 when a crop forces a re-encode
  of an AV1 or odd source and wide playback compatibility matters.
- Never touch the originals. Write outputs next to the source, with clear suffixes.

---

## 6. How the fork changes these lessons

- **`FFMPEG_SKILL_HW=1` sends every re-encoding tool to VideoToolbox (Apple's GPU encoder) except
  `export.py` delivery presets.** That includes `overlay.py`, `freeze.py`, `crop.py`, `fit.py`, and
  hybrid or accurate cuts.
  - VideoToolbox is **2–7× faster** but needs **1.2–2.5× the bytes** for the same SSIM. That's fine
    for drafts and intermediates, but not for deliverables where the user expects x265 medium
    CRF 18.
  - **For final deliverables, pass `--no-hw`**, or don't set the env var and use `--hw` only for
    drafts. Decide this before copying `~/.zshenv` over.
  - Check the output's `encoder` and `hw.source`. `hw.source: env` means the env var chose the GPU,
    not you.
  - `render.py`/`batch.py --hw` is the one switch that also puts the export on the GPU.
- The raw polygon-blur recipe (§3.4) always uses libx265, so it's unaffected. Same for the plain
  lossless trim (§2.3).
- Stream copies (`cut.py --tolerance -1`) don't encode, so hardware encoding doesn't matter there.
- Faster GPU encodes make the 30-minute timeout (§4) less likely to hit, but it still applies.
- If VideoToolbox hits a hard limit (H.264 VT stops at 4096 px wide), the fork retries once on the
  CPU and reports it in `hw.notes`.
- The fork tags BT.709 with `h264_metadata`/`hevc_metadata` bitstream filters.
  `-colorspace/-color_primaries/-color_trc` do a real color conversion on FFmpeg 7.1+ (tested at
  23.8 dB vs 49.9 dB PSNR). Don't swap them back.
- HDR10 mastering-display and max-CLL metadata survive `hevc_videotoolbox` on FFmpeg 9.0. A test
  pins this.
- **Speech engines:** `--engine auto` picks Parakeet only for English (explicit `--language`, then
  whisper `-dl` detection, then assumes English). `caption.py --model` now defaults to
  `large-v3-turbo`. whisper-cli `-np` hides the language-detection line, so don't pass `-np` when
  you need detection.

Benchmark (8 min of LibriSpeech, M4 Max):

| Engine / model | Time | WER |
|---|---|---|
| whisper.cpp base | 4.9 s | 7.13% |
| whisper.cpp small.en | 8.5 s | 4.70% |
| whisper.cpp large-v3-turbo | 12.3 s | 2.43% |
| parakeet-mlx v2 | 4.0 s | 2.78% |
| parakeet-mlx v3 | 4.2 s | 6.17% |
| parakeet.cpp v2 | 7.8 s | 2.87% |

### Working on the fork's code
- Empty `tests/out/` before a full test run (`rm -rf tests/out`). Tests write fixed output names
  and the skill refuses to overwrite. **Never run two test processes at once**, because they share
  that directory.
- `SKILL.md` is capped at 30,000 bytes and 220 lines by a test. It was at 29,998 bytes after the
  fork's changes, so any addition needs an equal cut.
- Renaming a contract capability requires a `contract_version` bump. Additive changes don't.
- **Still open:** the third Codex review pass on commit `3ff6462` was cut off by the usage limit.
  Rerun it, and consider opening an upstream issue before any PR (per `CONTRIBUTING.md`).

---

## Quick pre-flight checklist

1. Did `readlink "$(which ffmpeg)"` include `/ffmpeg-full/`? If not, run `ensure-ffmpeg-full`.
2. Did `probe.py` on the source report the codec, fps, VFR flag and HDR? The VFR flag rules out
   `cut.py` for lossless work.
3. For a lossless trim, did you use the plain `-ss … -c copy` (§2.3) or `cut.py --tolerance -1`, and
   check `mode`, `reencoded` and the codec afterwards?
4. For a masked region, did you detect the guide line with PIL and preview the mask on a still?
5. For a raw filtergraph with a looped input, did you add `-t` and `shortest=1`?
6. For an encode longer than about 25 min, did you set `--timeout` above the ETA and keep the
   approved preset?
7. Is this a deliverable? Pass `--no-hw` unless the user chose GPU encoding.
8. Did you quote `-map` specs and pass absolute `-o` paths?
9. Did you check the result on real frames, then clean up the verification images?
