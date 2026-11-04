**What happens.** A stream-copy `cut.py` of a file with two audio tracks keeps only the first. The result is `verified: true` with no note, so a caller can't tell a track was left behind:

```
# two-audio.mov: h264 + aac mono (a:0) + aac 4.0 (a:1) + tmcd
python3 scripts/cut.py two-audio.mov --start 1 --end 4 -o part.mov --json
  status: completed, verified: true, mode: copy, notes: [], dropped_non_av_streams: false
  verification[streams].expected_count: {video: 1, audio: 1}
ffprobe part.mov  ->  h264, aac (1 ch), data (tmcd)      # the 4.0 track is gone
```

On a real iPhone clip (HEVC HLG, AAC stereo + Apple APAC 4-channel spatial audio + six Core Media metadata tracks), a stream-copy cut kept the video and the AAC track only, also silently.

**Context.** `references/gotchas.md` says "scripts map only the first audio track, so extra tracks are dropped on re-encode", so the policy is known. Two things don't match it, though:

- The drop happens on a lossless stream copy too, not only on re-encode.
- The result doesn't say so, while `export.py` has reported this kind of loss since 2.22.4 (`non_av_streams`, `dropped_non_av_streams`, a `notes` line). The `streams` step expects one audio stream, so it can't see the second go missing.

**Possible fix** (your call): report the audio tracks not carried over (a `notes` line and/or a `dropped_streams`-style field, like `export.py`), and say "stream copy and re-encode" in the gotcha. Whether `cut.py` should copy every track on a stream copy is a separate question; I'm only asking that the result says what happened.

**What was run.** macOS 27.2, Apple M4 Max, Python 3.15.2, ffmpeg-skill 3.1.1, Homebrew `ffmpeg-full` 9.0.2_1. The synthetic file was made with `ffmpeg -f lavfi -i testsrc2=… -f lavfi -i sine=f=440 -f lavfi -i "sine=f=880,pan=quad|…" -map 0 -map 1 -map 2 -c:v libx264 -c:a aac -timecode 01:00:00:00 two-audio.mov`. The iPhone clip is the user's own and isn't attached. Low priority; found while running #143's rows.
