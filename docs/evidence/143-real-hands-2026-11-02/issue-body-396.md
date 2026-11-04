**What happens.** An SRT file given to `caption.py --text` (or `render.py --cues`) is burned in line by line: the cue numbers and the `-->` timing lines become on-screen captions, auto-timed 3 s apart. The run is `completed`, `verified: true`, and `check.py` passes.

```
cat subs.srt
  1
  00:00:00,500 --> 00:00:02,500
  Hello

  2
  00:00:03,000 --> 00:00:05,000
  Emoji 🎬✅
python3 scripts/caption.py --text subs.srt --write-srt cues.srt
  1 / 00:00:00,000 --> 00:00:03,000 / "1"
  2 / 00:00:03,000 --> 00:00:06,000 / "00:00:00,500 --> 00:00:02,500"
  3 / 00:00:06,000 --> 00:00:09,000 / "Hello"  ...
python3 scripts/caption.py in.mp4 --text subs.srt -o out.mp4 --json      # 6 s clip
  status: completed, verified: true
  notes: "4 cue(s) fall outside the video (0–6.0 s) and are not drawn"
```

Through `render.py --template tiktok --cues subs.srt` on a 12 s clip, the contact sheet shows `1`, then `00:00:00,500 -- > 00:00:03,000`, then the text, each for 3 s. The Japanese cue was never drawn ("5 cue(s) fall outside the video").

**Cause.** The cue-file regex (`caption.py`, `^\s*(?P<a>…)\s*(?:-->|-|–|to)\s*(?P<b>…)\s+(?P<text>.+)$`) needs text on the same line as the times. An SRT puts its text on the next line, so the timing line doesn't match and falls through to "text without a time is auto-timed".

**Why it matters.** `render.py` has `--srt` for this, but the easy path leads to `--cues`. SKILL.md's request table maps "make this a TikTok / Reel / Short" to `--cues cues.txt`, and #143's acceptance table asks testers to run `render.py --template tiktok --cues ...`. I made exactly this mistake while running #143 by hand with an SRT. The result gave no hint beyond "cues fall outside the video", which reads like a timing problem.

**Possible fixes** (your call): treat a cue file whose lines include a bare `A --> B` timing line (or a `.srt` file) as SRT, either by parsing it as one or by refusing with a pointer to `--srt` (`kind: input`). That keeps `--text`'s own format unchanged.

**What was run.** macOS 27.2, Apple M4 Max, Python 3.15.2, ffmpeg-skill 3.1.1, Homebrew `ffmpeg-full` 9.0.2_1. Synthetic input.
