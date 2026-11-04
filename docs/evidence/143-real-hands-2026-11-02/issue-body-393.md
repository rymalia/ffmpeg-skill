**What happens.** On an FFmpeg 9.0.2 build with no `subtitles`/`ass` filter (Homebrew's plain `ffmpeg` formula, no libass), `caption.py --srt` fails with `kind: ffmpeg`, no `error.reason` and no hint. The message is a filter-parse error that doesn't name the missing filter. `--dry-run` reports nothing wrong beforehand, though `doctor` already knows the filter is missing (`caption.usable: "no"`). Seen on ffmpeg-skill 3.1.1 (`1ce2c18`).

```
python3 scripts/caption.py in.mp4 --srt subs.srt -o out.mp4 --dry-run --json   # status completed, no error
python3 scripts/caption.py in.mp4 --srt subs.srt -o out.mp4 --json
  status: failed, error.kind: ffmpeg, error.reason: null, error.hint: null
  [AVFilterGraph @ 0x...] No option name near 'subs.srt:force_style=FontName=...'
```

`render.py --template tiktok --srt subs.srt` fails the same way at its caption stage (`No option name near '…/captioned.ass:fontsdir=…'`), after a `--dry-run` that also passed.

**Cause.** On this build, a filter that doesn't exist, given a *positional* first argument, fails at parse time before the "no such filter" check:

```
ffmpeg -f lavfi -i color=s=320x240:d=1 -vf "subtitles=s.srt" -f null -
  No option name near 's.srt'
  Error parsing a filter description around:
ffmpeg -f lavfi -i color=s=320x240:d=1 -vf "subtitles=filename=s.srt" -f null -
  No such filter: 'subtitles'
  Error opening output files: Filter not found
```

`caption.py` builds `subtitles=<path>:force_style=…` and `ass=<path>` (positional), so the message 3.1.0's classifier looks for (`No such filter: '…'` → `filter_missing`, `runner.py`) never appears.

**Why it matters.** This is the case #143's macOS row asks about ("does the agent read `caption.usable: "no"` and say so, or run `caption.py` and hit the runtime error?"). I ran it with Codex CLI 0.166 (gpt-5.6-luna) and Claude Code 2.1.316 (Opus 5.5) on a plain request, "Burn the captions from subs.srt into clip.mp4". Neither ran `doctor` first, which SKILL.md's "Never start with it" allows. Both dry-ran `caption.py` (passed), ran it, and got the parse error above. Claude Code then blamed the non-ASCII file name, retried with an ASCII copy, and claimed `caption.py` doesn't escape the path (it does, `escape_filter_path`) before running `doctor` and reporting correctly. A `filter_missing` reason with the doctor fix line, or a dry run that refuses, would have sent both straight to the right answer.

**Possible fixes** (your call):

- A capability check in `caption.py` and `render.py` (dry run included) against the same table `doctor` uses, refusing with `reason: filter_missing` and doctor's `fix` line before ffmpeg runs.
- And/or pass the path as a named option (`subtitles=filename=…`, `ass=filename=…`), so the build's own message is the one the classifier already handles.
- And/or classify `No option name near` when the filter isn't in `-filters`.

**What was run.** macOS 27.2, Apple M4 Max, Python 3.15.2, ffmpeg-skill 3.1.1. The lean build was the real Homebrew `ffmpeg` 9.0.2 binary (`Cellar/ffmpeg/9.0.2_1/bin`). Because `ffmpeg-full` is installed on this machine and #321 would otherwise pick it, the lean binaries were copied into a separate prefix with no `opt/ffmpeg-full`, so discovery takes the plain-user path (`ffmpeg_source: path`, `doctor ok: false`). That copy is a stand-in, not a real uninstall. The raw `ffmpeg -vf` commands above are the lean binary alone. Inputs were synthetic (`testsrc2` + `sine`, a 2-cue SRT). Not run on Linux; I'd expect any libass-less FFmpeg 9 build to behave the same, but haven't measured it.
