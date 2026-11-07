# #143 real-hands rows (Codex + macOS), 2026-11-02

Status: **issues posted 2026-11-03** as #393 (finding 1), #394 (2), #395 (3), #396 (4), #397 (5); the #143 comment was posted 2026-11-03 (https://github.com/kajisho5/ffmpeg-skill/issues/143#issuecomment-6624715127).
**All five fixed in 3.1.2** by upstream PR #399 (`c005589`, "Fix #393-#397: lean builds, tofu emoji, SRT as --text, dropped audio tracks"); the maintainer closed #393-#397 as completed on 2026-11-05. Fixes not yet re-verified on our setup (plain-Homebrew stand-in, ffmpeg-full emoji, iPhone MOV cut).
Evidence is in `docs/evidence/143-real-hands-2026-11-02/`. The scratchpad copies are gone after the session.

## Setup

- Machine: Apple M4 Max, macOS 27.2. Python 3.15.2, Node 24.22.1.
- Agents: Codex CLI 0.166.0 (`gpt-5.6-luna`, reasoning `high`) and Claude Code 2.1.316 (`claude-opus-5-5`).
- ffmpeg-skill 3.1.1 at `~/.agents/skills/ffmpeg-skill`. Claude Code reads it through the `~/.claude/skills/ffmpeg-skill` symlink.
- FFmpeg: Homebrew `ffmpeg-full` 9.0.2, force-linked as `/opt/homebrew/bin/ffmpeg`. Homebrew's plain `ffmpeg` 9.0.2 is also installed.
- `FFMPEG_SKILL_HW` was unset for every run. The user's shell normally exports it.
- Workspace folders used non-ASCII names: `日本語 テスト 🎬/`, `lean 字幕 🎬/`, `direct 直接 📂/`.
- Inputs:
  - A synthetic 12 s 1920x1080 29.97 H.264 + AAC test pattern, `話す clip 🎤.mp4`.
  - A 3-cue SRT (English, Japanese, and an emoji cue with 🎬✅), `字幕 subs.srt`.
  - For direct tool runs only, a real iPhone clip copied as `iPhone 撮影 📱.MOV`. It is 1.7 s, HEVC HLG, rotation -90, VFR, with AAC and a second Apple APAC audio track. The agents never saw it, and no frames of it are kept.

### How "plain Homebrew ffmpeg" was reproduced (stand-in, not a real `brew` change)

Since #321, the skill switches to the keg-only `ffmpeg-full` whenever it exists in the same prefix. So a real plain-ffmpeg user is one who never installed `ffmpeg-full`. To avoid changing Homebrew while other sessions use `ffmpeg-full`:

- The real lean Homebrew binaries were copied: `Cellar/ffmpeg/9.0.2_1/bin/{ffmpeg,ffprobe}` went into a fake prefix `lean-hb/Cellar/ffmpeg/9.0.2_1/bin/`, with no `opt/ffmpeg-full` beside it. A PATH directory symlinks to them. `_homebrew_full_build()` takes the realpath into this fake Cellar and finds no `ffmpeg-full`, which is the same code path a real plain user hits.
- `ZDOTDIR` pointed at a throwaway zsh config. The agents' login shells, Codex's `zsh -lc` and Claude's Bash, otherwise re-source `~/.zprofile`/`~/.zshrc`, which put `/opt/homebrew/bin` first. `command -v ffmpeg` was checked in both agents before the test.
- What differs from a real plain-Homebrew Mac: the full build still exists at `/opt/homebrew/bin/ffmpeg`, so an agent that goes looking can find it. On a real plain-Homebrew Mac that path *is* the lean build. Codex did this; see below.

## Codex row

| Cell | Result |
|---|---|
| Install | PASS. Bare `npx -y ffmpeg-skill --codex` installed into `~/.agents/skills/ffmpeg-skill`, not `~/.codex/skills` (#136). The Claude Code symlink survived. `npx ffmpeg-skill@3.1.1` was refused by the user's `~/.npmrc` `min-release-age=3`: every 3.x was published 2026-10-31, so the guard resolved bare `npx` to **2.21.1**. 3.1.1 was put back from the repo checkout (`node bin/install.js --codex`). The install mechanics are the same in both versions. |
| Listed / triggers | PASS. Asked to list its skills, Codex listed `ffmpeg-skill` once. Given a plain request ("Make … into a vertical TikTok with the captions from … burned in"), its first command read `SKILL.md`. |
| Non-ASCII path | PASS for the tools: probe, cut, render, check and look all ran in `日本語 テスト 🎬/` on `話す clip 🎤.mp4`. Agent-side note: Codex twice typed the filename as `話સે clip 🎤.mp4` (Gujarati characters) in its own commands. The tool refused the missing file, and Codex retried. |
| TikTok template | PASS with findings. Codex routed to `render.py --template tiktok … --srt '字幕 subs.srt'`, dry-ran it, then ran it: verified, `check.py --platform tiktok` all PASS except the `subtitles` WARN. **The emoji cue rendered as two tofu boxes, while the result said `emoji_monochrome`** (finding 3). Codex spotted the boxes on the sheet, then took a long detour: it compiled a Swift emoji rasteriser in `/private/tmp`, rebuilt the pipeline by hand (fit → caption `--emoji png --emoji-assets` → loudness → export `--normalize`), and delivered that. The final file is correct (sheet: `codex-tiktok-final-sheet.png`). Its report used the user's quick-recap format, not the skill's Done/Steps/Check/Look/Notes, and didn't mention the detour. |
| look sheet reviewed | PASS. Codex viewed its sheets, and I viewed them too. |

## macOS row (plain Homebrew ffmpeg, via the stand-in above)

| Cell | Result |
|---|---|
| Install | The installer only checks that `ffmpeg -version` runs and is ≥ 6.1. With the lean build it printed `found ffmpeg version 9.0.2 … Done.` and **said nothing about missing drawtext/subtitles**. The `ffmpeg-full` hint appears only when ffmpeg is missing entirely. |
| doctor | `ok: false` with missing `filter:drawtext`, `filter:subtitles`, `filter:vidstab*`, and `caption`, `graphics`, `stabilize` marked `usable: "no"` with the ffmpeg-full fix line. **But `look` (and `render`) say `usable: "yes"`, and `look.py`'s default sheet needs drawtext** (finding 2). |
| Non-ASCII path probe | PASS. `probe.py` on `iPhone 撮影 📱.MOV`. |
| TikTok template | FAIL, explained poorly. `render.py --template tiktok --srt …` **`--dry-run` reports no problem**, then the run fails with `kind: ffmpeg`, no `reason`, no hint: `No option name near '…/captioned.ass:fontsdir=…'` (finding 1). |
| look sheet | FAIL with a good message: `reason: filter_missing`, "this ffmpeg build has no drawtext filter". The hint points to `doctor`, which says `look` is usable. `--no-timecode` exists but isn't suggested. |
| **The row's real question: does the agent read `caption.usable: "no"` first?** | **No, in both agents.** Neither ran `doctor` before `caption.py`. SKILL.md says "Never start with it", so this follows the skill. Both dry-ran `caption.py --srt` (passed), ran it, and hit the same unclassified parse error. **Claude Code** then guessed the non-ASCII filename, retried with an ASCII copy, ran `doctor`, and reported correctly. It left the folder clean, didn't switch builds, and offered `--mode mux` as the option that works. It also claimed `caption.py` doesn't escape the SRT path, which is false (`escape_filter_path()`). The cryptic error invited it. **Codex** ran `doctor`, found the full build at `/opt/homebrew/bin`, reran with `PATH=/opt/homebrew/bin` + python3.12, and reported "🟢 … captions burned in" without saying it switched ffmpeg (a stand-in artefact, see Setup). Its file has **tofu emoji**, which it didn't report (finding 3). |

## Findings (filed as #393-#397, all fixed in 3.1.2 by #399; reproducible with synthetic input)

1. [#393, fixed in 3.1.2] **A missing `subtitles`/`ass` filter is not classified, and `--dry-run` doesn't catch it.** On FFmpeg 9.0.2, a filter that doesn't exist given a positional argument fails at parse time: `-vf "subtitles=s.srt"` prints `No option name near 's.srt'`, not `No such filter: 'subtitles'`. With a named option (`subtitles=filename=s.srt`) the same build prints `No such filter`. The 3.1.0 classifier (`runner.py`, the `No such filter` regex) therefore misses it. `caption.py` and `render.py` fail with no `reason` or hint, and both agents tried other explanations first. `--dry-run` passes, though `doctor` knows the filter is missing. Possible fixes (maintainer's call): a capability preflight in `caption.py`/`render.py` (and their dry runs) using doctor's table; and/or named options (`subtitles=filename=…`, `ass=filename=…`) so the build's own message is the classifiable one.
2. [#394, fixed in 3.1.2] **`doctor` marks `look` usable on a build without drawtext, while `look.py`'s default fails.** The sheet's timecodes use drawtext. `look.py --no-timecode` would work, but neither doctor nor the failure hint says so. Also, `render` is "usable" while every template with captions or a title fails.
3. [#395, fixed in 3.1.2] **`emoji_monochrome` is reported when the emoji are drawn as tofu.** On Homebrew `ffmpeg-full` 9.0.2 with libass, `caption.py --srt` (direct, and through `render.py --template tiktok`) draws 🎬✅ as two empty boxes (`codex-tiktok-template-sheet.png`, `lc-emoji.png`). The result says `emoji rendered monochrome … Apple Color Emoji installed but libass renders it monochrome on this build` and `verified: true`. workflow.md says "Tofu is a failed job". One agent noticed and spent ~1,500 log lines working around it. The other read "monochrome" as fine and shipped tofu.
4. [#396, fixed in 3.1.2] **An SRT given to `--cues` / `caption.py --text` is burned as text.** The SRT's timing lines carry no text after the times, so they don't match the cue regex. Every line, including `1` and `00:00:00,500 --> 00:00:03,000`, becomes an auto-timed 3 s caption. Result: `verified: true`, `check.py` all PASS, and a note that "5 cue(s) fall outside the video" (`direct-tiktok-cues-srt-sheet.png`). `render.py` has `--srt` for this, but SKILL.md routes "make this a TikTok" to `--cues cues.txt`, and #143's own table says `--cues`. A file whose lines are SRT timing lines (or a `.srt` extension) could be refused or redirected to `--srt`.
5. [#397, fixed in 3.1.2] **Minor:** a stream-copy `cut` of an iPhone MOV keeps 1 of 2 audio tracks (drops the 4-channel `apple_apac`, for which FFmpeg has no decoder) and the six timed-metadata data tracks, with no note. `streams` expects 1 audio and passes. (`export.py` reports such drops since 2.22.4; `cut.py` doesn't.)

Per the maintainer's rules these are bug/behaviour reports, so each would be an issue with a synthetic repro, one fix per issue. The fix shape is left to them. Finding 4 could be argued as docs drift (#143's table says `--cues`).

## Comment posted on #143 (2026-11-03)

> **Codex and macOS (plain Homebrew `ffmpeg`) rows, run 2026-11-02 on a machine that isn't the maintainer's** (Apple M4 Max, macOS 27.2, ffmpeg-skill 3.1.1, Codex CLI 0.166.0 with gpt-5.6-luna, Claude Code 2.1.316 with Opus 5.5). Inputs were synthetic, in folders named `日本語 テスト 🎬/` etc.; one real iPhone HEVC/HLG clip was used for direct tool runs only.
>
> | Device family | Install | Non-ASCII path | TikTok template | `look.py` sheet reviewed |
> |---|---|---|---|---|
> | Codex (`~/.agents/skills`) | pass: bare `npx ffmpeg-skill --codex` → `~/.agents/skills`, listed once, triggered on a plain request (read SKILL.md first) | pass | pass (`--template tiktok --srt`), but emoji drawn as tofu while reported monochrome → #395 | pass |
> | macOS, plain Homebrew `ffmpeg` (simulated, see below) | pass, but the installer says nothing about the missing drawtext/subtitles | pass | fails with an unclassified `No option name near …` error; `--dry-run` passed → #393 | default `look.py` fails (`filter_missing`); doctor lists `look` as usable → #394 |
>
> **The macOS question (does the agent read `caption.usable: "no"`?): no, for both Codex and Claude Code.** Both dry-ran `caption.py` (passed), ran it, hit the unclassified parse error, and only then ran `doctor`. Claude Code first suspected the non-ASCII filename, then reported the missing filter correctly. With a classified `filter_missing` error, or a dry run that refused, the detour wouldn't happen.
>
> Simulation, stated plainly: `ffmpeg-full` is installed here, so the real lean `Cellar/ffmpeg/9.0.2_1` binaries were copied into a fake prefix with no `opt/ffmpeg-full`, and the agents' shells were given a profile that puts it first. Discovery takes the plain-user path (`ffmpeg_source: path`, doctor `ok: false`). Because the full build still existed, one agent found it and switched to it, which a real plain-Homebrew Mac wouldn't allow. Also: `npx ffmpeg-skill@3.1.1` was refused by this machine's npm `min-release-age=3`, so bare `npx` installed 2.21.1 on 11-02; on 11-03, after the guard window passed, the same `npx ffmpeg-skill --codex` installed 3.1.1 into `~/.agents/skills`.
>
> Issues filed from this: #393 (missing subtitles filter unclassified, dry run doesn't catch it), #394 (doctor/look), #395 (emoji tofu reported as monochrome), #396 (SRT given to `--cues`), #397 (cut drops the second audio track silently).

## Re-check on 3.2.0 (2026-11-06)

The tools were run directly; this was not an agent run. ffmpeg-skill 3.2.0 (`notes` at `c320a5c`), with `FFMPEG_SKILL_HW` unset. The lean build is the same stand-in as above: real `Cellar/ffmpeg/9.0.2_1` binaries copied into a prefix with no `opt/ffmpeg-full`, and `PATH` limited to that prefix plus `/usr/bin:/bin`. doctor reports `ffmpeg_source: path`, `ok: false`. The full build is Homebrew `ffmpeg-full` 9.0.2. Inputs: a synthetic 12 s `testsrc2` clip with a non-ASCII name, a 3-cue SRT (English, emoji 🎬✅, Japanese), the synthetic `two-audio.mov` from #397, and a real iPhone MOV (HEVC + AAC stereo + APAC 4-ch + six Core Media Metadata tracks; the user's own footage, not kept).

| Issue | Result |
|---|---|
| #393 | **Fixed.** On the lean build, `caption.py --srt` refuses **in `--dry-run` and in the run**, with `kind: ffmpeg`, `reason: filter_missing`, "no subtitles filter, which burning captions needs", and the ffmpeg-full hint. `render.py --template tiktok --srt` does the same in both modes (it names the `ass` filter). |
| #394 | **Fixed** (fallback route). `look.py`'s default sheet completes on the lean build with the `look_no_drawtext` fallback and a "no timecode stamps" note. doctor still lists `look` (and `render`) as `usable: "yes"`, which is now accurate for `look`. |
| #395 | **Fixed.** `emoji_support()` now reports `mode: none` and `libass_glyph: false` ("libass draws no emoji glyph … an empty box or nothing"). `caption.py --srt` leaves the emoji out of the drawn text and warns `emoji_not_drawn` (count 2, with an `--emoji-assets` fix). A cropped frame shows "Emoji" with no boxes. The Japanese cue renders correctly. `verified` is still `true`, with the warning. |
| #396 | **Fixed.** `caption.py --text subs.srt` and `render.py --template tiktok --cues subs.srt` refuse with `kind: input`: "is an SRT file (line 2 is a timing line with no text …); pass it as --srt (render.py: --srt, not --cues)". |
| #397 | **Fixed for audio.** A stream-copy `cut.py` of `two-audio.mov` and of the iPhone MOV adds a note and an `audio_tracks_dropped` warning (`source 2, kept 1, dropped 1`) plus `dropped_audio_streams: 1`. **Leftover (minor, not filed):** the iPhone cut also drops all six Core Media Metadata data tracks with no note, and `dropped_non_av_streams` is `false`. The synthetic file's tmcd track is kept. |

The test suite on the same checkout, `env -u FFMPEG_SKILL_HW OUT=<fresh dir> python3 tests/run_parallel.py`: **1098 tests, all OK** (3 skipped), 570 s wall, ffmpeg-full 9.0.2, Python 3.15.2. The first attempt reused the old `tests/out/` and inherited `FFMPEG_SKILL_HW=1`; 7 tests failed, mostly `output_exists` refusals on files left by earlier runs. They were not code failures.
