# ffmpeg-skill — known issues

Problems in the skill's scripts and shared code, with the workaround that works today and the
direction of a permanent fix. Each entry names the component, how to trigger it, and what is known
about the cause. First observed 2026-09-28 on macOS (Apple Silicon), ffmpeg 9.0.2, fontconfig 2.18.3.

Severity: **High** = wrong or lost output with no warning; **Medium** = wrong output that is visible
or reported; **Low** = friction, surprising default, or missing option.

---

## Text and graphics

### T1. Multi-line drawtext drops line breaks and the space between them — High
- **Component:** `scripts/graphics.py` (`wrapped()`), `scripts/_common/wrap.py` (`wrap_text`),
  `scripts/_common/drawtext.py` (`drawtext_text_opts`, `textfile=…:expansion=none`)
- **Symptom:** a title that gets wrapped renders as ONE line with the space at the break removed:
  "WHO SHOWS UP?" → "WHOSHOWS UP?"; "NOBODY SHOWS UP FOR THE WORK" → "…UPFOR THE…", running off
  both edges of the frame. Nothing in the JSON reports it.
- **Repro:** `graphics.py in.mp4 --template hook --title "WHO SHOWS UP?" --scale 1.4` on a 1080-wide frame.
- **Cause (two bugs):**
  1. `wrapped()` decides the break from `wrap_text(text, W*0.9/fontsize)`, a generic em-width
     estimate, not the real font — so it wraps text that fits (a condensed face at 128 px fits easily).
  2. The `"\n"` it inserts reaches drawtext through `textfile=`, and on ffmpeg 9.0.2 drawtext does
     not render it as a line break; the lines are joined with no space.
- **Workaround:** keep the title under the wrap threshold (for a 13-character title, `--scale` ≤ 1.19,
  about 109 px), or use `overlay.py --text` with one entry per line. A non-breaking space (U+00A0) does
  NOT help: `wrap_text` treats it as a normal space.
- **Fix direction:** measure the wrap width with the actual font file (the same measured path
  caption.py uses); draw each wrapped line as its own drawtext, or confirm `\n` handling on ffmpeg 9.x
  in a test; add a verification that rendered text width ≤ frame width.

### T2. Hook template has no shrink-to-fit — Medium
- **Component:** `scripts/graphics.py`, `hook` template (and likely `title`, `meme`)
- **Symptom:** a long hook title runs off the frame instead of shrinking; the size comes from
  `base * 0.085 * --scale`, whatever the font's width. Condensed faces come out visibly smaller than
  wide faces at the same `--scale`.
- **Workaround:** a shorter title, or set `--scale` by hand per font.
- **Fix direction:** reuse caption.py's `fit_size` logic: measure with the chosen font, shrink to a
  floor before wrapping, and report the size used in the JSON.

### T3. A style inside a `.ttc` font collection can't be selected — Medium
- **Component:** `scripts/_common/fonts.py` (name → path resolution), every drawtext user
  (`graphics.py`, `overlay.py`, `look.py`, `grid.py`)
- **Symptom:** `--font "Futura:style=Condensed ExtraBold"` renders Futura Medium. fc-match resolves
  the family to the `.ttc` path, the tools pass `fontfile=<path>`, and drawtext has no face-index
  option, so face 0 is always used. On macOS most good display faces live at a non-zero index:
  Futura Condensed ExtraBold (#4), Avenir Next Condensed Heavy (#8), Helvetica Neue Condensed Black (#9).
- **Workaround:** extract the face to a standalone file and pass `--font-file`:
  ```sh
  uv run --with fonttools python3 -c "from fontTools.ttLib import TTCollection; \
    TTCollection('/System/Library/Fonts/Supplemental/Futura.ttc').fonts[4].save('FuturaCondExtraBold.ttf')"
  ```
  (`fc-scan --format "%{index}: %{fullname}\n" FILE.ttc` lists the faces.)
- **Fix direction:** when a style is requested or the match is a `.ttc` face other than 0, pass
  drawtext `font=` (fontconfig pattern) instead of `fontfile=`, or extract and cache the face.

### T4. `title` template dims and desaturates the whole frame — Low
- **Component:** `scripts/graphics.py`, `title` template
- **Symptom:** the card greys out everything behind it, which hides a payoff shot under an end card.
- **Workaround:** `overlay.py --text … --box` (or a project `overlays[]` entry) for an end-card line.
- **Fix direction:** an option to keep the background untouched (e.g. `--backdrop none|dim`).

### T5. Default display font is DejaVu Sans — Low
- **Component:** `graphics.py` / `overlay.py` defaults, social templates in `render.py`
- **Symptom:** hooks, titles and end cards look unstyled on social deliverables unless a brand
  font is supplied.
- **Fix direction:** a per-template default display face (resolved by T3's fix, with DejaVu as the
  fallback), or document `brand.json` `font_file` prominently in the social templates.

---

## Render projects (`render.py`)

### R1. `graphics[]` entries can't take a font — Medium
- **Component:** `scripts/render.py`: the allowed-keys schema for `graphics[]` and the argv mapping
  in the graphics stage
- **Symptom:** `graphics.py` accepts `--font` / `--font-file`, but a `graphics[]` entry has no
  `font` / `font_file` key (`overlays[]` does). The only project-level route is a brand font, which
  also changes the captions.
- **Workaround:** run `graphics.py --font-file …` on the clip before `render.py`, and leave that
  entry out of the project. The downside: the graphic is then invisible to `--cache`,
  `--export-timeline` and re-renders of the project.
- **Fix direction:** add `font`, `font_file` (and `wrap`) to the `graphics[]` keys and the flag mapping.

### R2. `--cache` reused nothing when only a later stage changed — Medium (needs investigation)
- **Component:** `scripts/render.py` cache keys
- **Symptom:** a second render changed only `graphics`/`overlays`, yet `fit` and `captions`
  (upstream) re-ran: "cache: 0 hit(s), 6 miss(es)". The second run also added `--overwrite`, and the
  project's output path had changed.
- **Fix direction:** check whether the stage key includes the final output path or run flags; stage
  keys should depend only on stage inputs and parameters.

### R3. Audio past the end of the video, varying between renders — Low
- **Component:** the `loudness` → `export` stages
- **Symptom:** the final file's audio runs 33–73 ms past its video, and the amount changed between
  two renders of identical audio (measured offset 0.0 between them). The container duration follows
  the audio, so a render's reported length moves by tens of milliseconds.
- **Fix direction:** trim the audio to the video length at export (or pad the video), and make it
  deterministic; `check.py` could report an A/V length mismatch.

---

## Joining and timing

### J1. Stream-copy join leaves a video timestamp gap when a clip's audio is longer than its video — Medium
- **Component:** `scripts/join.py` (concat copy path, `--transition none`)
- **Symptom:** clip A has video 57.067 s and audio 57.304 s. Clip B's video is placed after A's
  *container* duration, leaving a 0.237 s hole in the video timeline. Probe then reports odd rates
  (`5993/200`), and downstream re-encodes inherit them (`broll.py` wrote 29.887 fps). A/V stays in
  sync, and a later CFR export fills the hole with a held frame. `duplicates`/`short_segments` in the
  JSON stay empty, so nothing flags it.
- **Common trigger:** `audio.py --music` output (the audio is padded to the container length).
- **Workaround:** export to CFR at the end (any re-encode with `--fps` conforms it); or trim the
  clip's audio to its video before joining.
- **Fix direction:** detect an A/V length mismatch per clip before a copy-concat, then trim or pad
  the audio, or fall back to re-encoding and say why in the JSON.

---

## Analysis

### A1. `scenes.py --sheet` fails on long inputs and discards all measurements — High
- **Component:** `scripts/scenes.py`, sheet generation
- **Symptom:** with ~200+ scenes (an 11-minute multi-camera concert), the sheet builds one
  `select='eq(n,0)+eq(n,62)+…'` expression. ffmpeg fails to parse it ("Error while parsing
  expression", then "Cannot allocate memory", exit 244), and the whole run returns `status: failed`,
  losing the scenes, shots, beats and highlights already measured.
- **Workaround:** run without `--sheet`; use `look.py --tiles CxR` or `look.py --at …` for pictures.
- **Fix direction:** build the sheet in chunks, or pick frames by timestamp ranges; never fail the
  measurement because the sheet failed (write the JSON, then report the sheet error as a warning).

### A2. `cropdetect.py --motion-centre` follows hands, not the face, on talking heads — Low
- **Component:** `scripts/cropdetect.py`
- **Symptom:** on a seated interview it reports sparse samples (15 in 57 s) that follow the
  speaker's gesturing hands, so it is not usable to place a 9:16 crop on the face.
- **Workaround:** pick `--crop-x` from `look.py` frames, and crop per shot (`cut.py --accurate`
  per shot → `fit.py --crop-x` → `join.py`).
- **Fix direction:** document the limitation in `--help`; optionally report a per-shot centroid.

### A3. `scenes.py --beats` isn't usable on live band recordings — Low (limitation)
- **Component:** `scripts/scenes.py --beats`
- **Symptom:** a live rock performance measured 113 BPM at confidence 0.35 (`usable: false`), so
  "cut on the beat" isn't available for concert audio.
- **Fix direction:** document it; if a beat grid is needed, measure it from a studio version or a
  separate track.

---

## Other tools

### O1. `grid.py` defaults to 16:9 cells and burns filenames — Low
- **Component:** `scripts/grid.py`
- **Symptom:** cells default to 480x270 whatever the inputs' shape, so vertical clips are
  pillarboxed and tiny; `--label auto` burns each filename on by default.
- **Workaround:** `--cell-width 540 --cell-height 960 --label none` for 9:16 inputs.
- **Fix direction:** default the cell aspect to the first input's.

### O2. Speech transcription can split a word across two cues — Low
- **Component:** `scripts/_common/asr.py` / `caption.py --transcribe` (Parakeet engine)
- **Symptom:** the final cue came out as "…looking at cl" / "ips." (a 1-second cue holding the end of
  one word).
- **Workaround:** merge the two cues in the SRT (text unchanged) before burning.
- **Fix direction:** when building cues, never split inside a word token; merge a trailing fragment
  into the previous cue.

---

## Environment notes (not bugs)

- **`FFMPEG_SKILL_HW=1`** makes every re-encode use `h264_videotoolbox`, intermediates included
  (larger files than x264 CRF 18 at the same quality). Check the environment before comparing quality
  or file sizes between machines.
- **zsh doesn't word-split variables:** a string variable holding several flags
  (`A="--at 1 --at 2"; look.py $A`) is passed as ONE argument. Build repeated flags with an array:
  `A=(); A+=(--at 1); look.py "${A[@]}"`.
