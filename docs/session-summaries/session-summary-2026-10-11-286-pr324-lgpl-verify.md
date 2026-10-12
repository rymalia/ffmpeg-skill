---
session_id: b4b20b84-0002-46df-bae4-9dbe17f2efb8
date: 2026-10-11
time: "2026-10-09 7:21 PM PDT – 2026-10-11 9:35 PM PDT"
resumed: "2026-10-11 1:54 PM PDT, 2026-10-11 2:22 PM PDT, 2026-10-11 2:54 PM PDT, 2026-10-11 6:01 PM PDT, 2026-10-11 9:11 PM PDT"
project: ffmpeg-skill
branch: notes
related_pr: 324
---

# Session Summary: 2.8.6 sync, and real-Mac verification of #324 with an LGPL ffmpeg

## Overview

This summary continues the session after
`session-summary-2026-10-11-283-sync-issue-143.md` (`520ccc0`).

- **Upstream releases:** 2.8.4, 2.8.5 and 2.8.6 were out. Two of them came from this week's
  threads:
  - #323 makes whisper.cpp `-mc 0` the default (from #318);
  - #324 switches to VideoToolbox automatically when the build has no libx264/libx265 (from
    #314). Its test plan asked @rymalia for real-Mac checks.
- **Sync:** synced this Mac to 2.8.6.
- **LGPL ffmpeg:** built FFmpeg 9.0.2 as an LGPL build with VideoToolbox, and ran #324's
  checks on it and on the full Homebrew build.
- **Upstream comments:** after two Codex fact-check passes and the user's approval, I posted
  the results on #324 and a `-mc` flag confirmation on #318.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Built LGPL FFmpeg 9.0.2 from source** (user approved) | Every ffmpeg on this Mac is GPL with libx264, including the "lean" Homebrew formula. Only a real LGPL build tests the case #324 targets. |
| **Ran every check with `FFMPEG_SKILL_HW` unset** | The user's shell exports `FFMPEG_SKILL_HW=1`. That would choose VideoToolbox through the environment and hide `source: "auto"`. |
| **Used a synthetic `testsrc2` + sine input** | The results could be reproduced by anyone, and no personal footage went into a public comment. |
| **Also ran the three behaviours the PR only mocked** (`--codec hevc`, `--no-hw`, VT refusal) | The maintainer's environment is Linux, so these had no real-hardware evidence. |
| **Measured the VT width boundary (4096 vs 4098)** | Codex pass 2 objected that `-12903` alone doesn't prove width caused the failure. A measurement settled it better than softer wording. |
| **Dropped Codex finding 1 ("setup unsupported")** | Codex lacked the evidence, but this session had it: the commands I ran and `machine.json`. |
| **#318 comment says the issue can be closed** | #323 shipped the fix as the default, which answered the open question in #318. |

## Changes Made

| Change | Detail |
|--------|--------|
| **`main`** | Fast-forwarded to `f62e7d0` (2.8.6), which equals `origin/main`. The user had synced the fork. |
| **`notes`** | `e59499e`: "Merge upstream 2.8.6 into notes (#322, #323, #324)". It differs from upstream only by the deliberate `tests/prototypes/join_copy_p3.py`. The user pushed it. |
| **Installed skill** | `node bin/install.js --codex` installed 2.8.6. 59 of 59 files match the repo. |
| **LGPL build** | In the scratchpad: `lgpl/bin/{ffmpeg,ffprobe}`, from the `ffmpeg-9.0.2.tar.xz` tarball (sha256 `8c385028…e002e`, the same as Homebrew's). Configured with `--disable-doc --disable-ffplay --enable-videotoolbox --enable-audiotoolbox`, no `--enable-gpl`. Homebrew was not touched. |
| **Test harness** | Scratchpad `t324/run_checks.sh`: the four requested checks plus a doctor summary, run once per build. |
| **Upstream posts** | #324 issuecomment-6117811068; #318 issuecomment-6117811236. Both bodies were re-fetched and are byte-identical to the approved drafts. |
| **Memory** | New `test-clip-sources.md` (`~/Downloads/juni-volleyball/`, `~/Movies/`). `upstream-maintainer-expectations.md` updated with 2.8.4–2.8.6 and the #324/#318 posts. |

## Testing / Research Performed

- **LGPL build checks:**
  - `ffmpeg -L` reports the GNU Lesser GPL, and `-buildconf` has no `enable-gpl`;
  - its encoders: `h264_videotoolbox`, `hevc_videotoolbox`, `aac`, `aac_at`;
  - no libx264/libx265, and `otool -L` shows no x264/x265 library.
- **Full build** (Homebrew `ffmpeg-full` 9.0.2):
  - `export --preset reels`, `fit --aspect 1:1` and `cut --accurate` all give
    `encoder: libx264` with no `hw` block;
  - doctor: `ok: true`, `covered_by: {}`, libx264 available.
- **LGPL build, the same three tools:**
  - each gives `encoder: h264_videotoolbox` and
    `hw {requested: false, source: auto, used: true, fallback: false}`;
  - each has the "libx264 is not in this ffmpeg build…" note and the "not CRF-equivalent"
    note.
- **All six outputs:** H.264 High, yuv420p, the expected size, and they decode to the end.
  `export` has `verified: false` on both builds, caused only by loudness: the synthetic tone
  is −21.8 LUFS against −14.
- **LGPL doctor:**
  - `covered_by` maps libx264 → h264_videotoolbox and libx265 → hevc_videotoolbox, and
    libx264 is in neither `available` nor `missing`;
  - `export`/`fit`/`cut` are usable, and `fit` carries the per-tool `covered_by`;
  - overall `ok: false`. `boxblur`, `cropdetect`, `eq` and `hqdn3d` are GPL-only in the
    tarball's `configure` (`*_filter_deps="gpl"`), and libvidstab is on its GPL library list.
    `drawtext`/`subtitles` were missing only because this minimal build has no
    freetype/harfbuzz/libass.
- **Extra runs on the LGPL build:**
  - **`--codec hevc`:** `hevc_videotoolbox`, `hvc1`, `source: auto`.
  - **`--no-hw`:** fails with `Unrecognized option 'preset'`, not the "Unknown encoder" the
    PR expects, and has no hint.
  - **4400x2480 input:** VideoToolbox refuses with `-12903`. 2 commands were recorded, both
    `h264_videotoolbox`. The second comes from `run_keeping_subtitles()`
    (`scripts/_common/runner.py:1059`), which drops the `0:s?`/`0:d?` maps. It is not a CPU
    retry.
  - **Width boundary:** at height 2480, 4096 px encodes and 4098 px is refused (`-12903`).
- **whisper.cpp 1.9.5:** `whisper-cli --help` lists `-mc N, --max-context N [-1]`.
- **Codex fact-checks:**
  - **`gpt-5.6-luna` xhigh:** FIX, with 4 findings. Three were applied after I checked
    them, and one was dropped.
  - **`gpt-6-luna` high, on the fixed lines:** OK, OK, FIX. That FIX was resolved by the
    4096/4098 measurement.
  - I checked the `run_keeping_subtitles` claim in the code myself.

## Discoveries / Handoff Notes

- **On any LGPL ffmpeg, `doctor` stays `ok: false`,** and `cropdetect`, `denoise`, `redact`
  and `stabilize` are unusable, because their filters or libraries are GPL-only. That's
  correct reporting and relevant to #314's reporter.
- **`run_keeping_subtitles()` retries any failed first attempt,** including encoder
  failures it can't fix. That doubles the attempts on a VT refusal. It predates #324.
- **A plain LGPL ffmpeg builds in a few minutes on the M4 Max** with
  `./configure --enable-videotoolbox --enable-audiotoolbox`. Useful for any future
  "no GPL encoders" question.
- **A guarded removal blocks `rm -f $X/*.mp4`.** Use `"${X:?}"/…` or skip the `rm` when the
  directory is new.

## Current State

- **Checkout:** `notes` at `e59499e`, the same as origin. This summary is the next commit.
- **Branches:** `main` = `origin/main` = `f62e7d0`. Installed skill 2.8.6. Homebrew
  `ffmpeg` still resolves to ffmpeg-full.
- **Scratchpad (may not survive a resume):** the LGPL build, the test outputs, the drafts and
  the Codex logs. The posted comments are the durable record.

## Unfinished Work

- **The maintainer's move:** closing #318, and possibly the clearer `--no-hw` hint listed as
  a #324 follow-up. Watch #324 for replies.
- **Not tested:** `export.py --preset youtube-hdr` with an HDR source on an LGPL build, which
  the PR also listed as a follow-up.
- **The user pushes `notes`** once this summary is committed.
