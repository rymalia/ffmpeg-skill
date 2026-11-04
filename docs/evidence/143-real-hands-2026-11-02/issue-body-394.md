**What happens.** On a build without `drawtext` (Homebrew's plain `ffmpeg` 9.0.2), `doctor` reports `look` as `usable: "yes"`, but `look.py`'s default contact sheet fails:

```
python3 scripts/_contract.py doctor --json
  ok: false, missing: [filter:drawtext, filter:subtitles, filter:vidstabdetect, filter:vidstabtransform]
  tools.caption/graphics/stabilize: usable "no" (with the ffmpeg-full fix line)
  tools.look: {"usable": "yes"}      tools.render: {"usable": "yes"}
python3 scripts/look.py in.mp4 -o sheet.png --json
  status: failed, error.reason: filter_missing
  hint: "this ffmpeg build has no drawtext filter: `python3 scripts/_contract.py doctor` lists what it has and how to get a fuller build"
python3 scripts/look.py in.mp4 -o sheet.png --no-timecode --json
  status: completed
```

**Cause.** The default sheet draws its timecodes with `drawtext` (`look.py`'s `drawtext=text='%{pts\:hms…}'`), but `look`'s doctor row doesn't list `filter:drawtext`, presumably because `--no-timecode` works without it.

**Why it matters.** The failure hint sends the agent to `doctor`, and `doctor` says `look` is fine, so the agent has nowhere to go. SKILL.md step 8 makes `look.py` part of every picture change, so on this build the step always fails unless the agent finds `--no-timecode` on its own. `render` has the same shape: it's `usable: "yes"`, but every template with captions or a title fails on this build (#393).

**Possible fixes** (your call): mark `look` as degraded rather than "yes" when drawtext is missing, naming `--no-timecode`. Or have `look.py` fall back to no timecodes with a `diagnostics.fallbacks` entry. Or at least name `--no-timecode` in the `filter_missing` hint.

**What was run.** macOS 27.2, Apple M4 Max, Python 3.15.2, ffmpeg-skill 3.1.1. Homebrew `ffmpeg` 9.0.2 (lean) binaries, copied into a prefix with no `opt/ffmpeg-full` so #321's swap doesn't apply (a stand-in for a machine without `ffmpeg-full`, not a real uninstall). Synthetic input (`testsrc2`). Found while running #143's macOS row.
