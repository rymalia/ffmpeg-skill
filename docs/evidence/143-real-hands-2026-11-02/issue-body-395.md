**What happens.** On Homebrew `ffmpeg-full` 9.0.2 (libass) on macOS, `caption.py` draws 🎬 and ✅ as two empty boxes (tofu). The result says `emoji rendered monochrome` and `verified: true`:

```
python3 scripts/caption.py in.mp4 --srt subs.srt -o out.mp4 --json     # cue 2: "Emoji 🎬✅"
  status: completed, verified: true, diagnostics.warnings: [emoji_monochrome]
  notes: "emoji rendered monochrome (no colour path on this ffmpeg; --emoji-assets DIR for colour)"
python3 -c "from _common.emoji import emoji_support; print(emoji_support())"   # from scripts/
  {'mode': 'mono', 'color_font': 'Apple Color Emoji', 'libass_color': False,
   'detail': 'Apple Color Emoji installed but libass renders it monochrome on this build'}
```

A frame at 4 s shows "Emoji" followed by two hollow rectangles, not monochrome emoji glyphs. `render.py --template tiktok --srt` gives the same: tofu on the sheet, `emoji_monochrome` in the result.

**Cause.** `_libass_color_probe()` (`_common/emoji.py`) renders one emoji and returns `False` when no pixel is coloured. `emoji_support()` then picks `mode: "mono"` because a colour emoji family is installed, and words it as "renders it monochrome". "No colour pixels" covers two outcomes the probe doesn't tell apart: a monochrome glyph, and a missing glyph drawn as a white `.notdef` box. On this build it's the second: libass gets no usable glyph from Apple Color Emoji (an `sbix` bitmap font).

**Why it matters.** `references/workflow.md` says "Tofu is a failed job", but this run is `verified: true` with a note that sounds acceptable. Running #143's rows, the two agents split on it. Codex saw the boxes on its `look.py` sheet and spent most of the run building its own emoji PNGs for `--emoji-assets`. Claude Code reported "the 🎬✅ will come out black and white", and Codex in a second run shipped a file with tofu and reported "captions are visible and readable" (🟢).

**Possible fixes** (your call):

- Have the probe tell "a glyph was drawn" from "the `.notdef` box was drawn", for example by comparing against a render of a code point no font has, or by checking whether the face covers the code point (`fc-query --format=%{charset}`). Report tofu as its own mode (`none`, a warning, not verified) instead of `mono`.
- Word the note from what was measured ("no colour pixels in the probe render") rather than assuming a monochrome glyph.

**What was run.** macOS 27.2, Apple M4 Max, Python 3.15.2, ffmpeg-skill 3.1.1, Homebrew `ffmpeg-full` 9.0.2_1. Apple Color Emoji is the only emoji face installed (system default); no `--emoji-assets`. Synthetic input (`testsrc2` + a 2-cue SRT). Not tried on Linux with Noto Color Emoji (CBDT), which the probe's docstring describes as rendering a monochrome outline there.
