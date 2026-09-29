# Plan: carry-forward fixes — Phase 2 (joins that leave no gap)

Branch `m-series-hw-parakeet` (fork `rymalia/ffmpeg-skill`). This follows
`docs/plans/2026-09-27-carry-forward-fixes.md` (Phase 1). The raw backlog is in that plan's
"Phase 2" section, and `ISSUES.md` J1 is folded in.

**Scope (chosen by the user, 2026-09-28):** one theme, **a join must not leave a hole in the
video, stray frames, or an A/V offset while it reports success**. Four items, in build order:

- **J1:** the `join.py --transition none` hole.
- **Item 2:** a `--segments` segment that runs past the video's end.
- **Item 1:** the `--segments` stream-copy join on B-frame sources.
- **T1:** `ISSUES.md` T1, multi-line drawtext. It is its own small item, planned after the three
  join items land.

Deferred: the `--accurate` 24 ms skew, item 6 (timeouts), and the `stage_hw` roll-up.

**Revision history**
- **R1**: written from the measurements below.
- **R4** (this version; R4b adds the fourth pass's null rule for `segment_end_snap_seconds`) answers the third Codex pass (REVISE: no critical, 2 major, 1 minor; every
  other R1 and R2 finding resolved). The end snap gets a structured field, 1-i asserts the
  re-encode first, the "+21 ms" is scoped, and step 0's prototype must be committed. Marked
  **[R4]**.
- **R3** answers the second Codex pass (gpt-5.6-terra, xhigh: REVISE). 9 of the 13
  R1 findings were resolved and 4 were partial. Its new critical finding is that a sound tail
  shorter than one frame still leaves a hole; J1-b's red run shows the same in `join.py`. R3
  also adds the user's real iPhone footage (**M4**). Changes are marked **[R3]**.
- **R2** answers the Codex review of R1 (gpt-5.6-terra, xhigh: REVISE, 2 critical /
  7 major / 2 minor). Changes are marked **[R2]**. The critical "21 ms first-part offset" is one AAC
  frame of priming: 1024 / 48000 = 21.328 ms, the same value in P0 and P3. It is not an A/V
  offset, since the measured beeps at 1, 2, 4 and 5 s land on their pictures. The review was
  right that the t=0 onset was never measured, and right about everything else.

---

## Evidence (measured 2026-09-28, FFmpeg 9.0.2, M3 Air, `FFMPEG_SKILL_HW` unset)

Fixtures are built with lavfi in a scratch directory, using the `tests/test_cut_copy.py` recipes:
- `hevc25`: x265, 25 fps, keyint 50, bframes 4. x265's default is an **open GOP**.
- `hevc25c`: the same with `open-gop=0`.
- `h264bf`: x264, 30 fps, g 60, bf 3. x264's default is a closed GOP.
- `beep264`: `h264bf` with a 40 ms 1 kHz beep at every whole second, for A/V sync.
- `longaudio`: H.264, video 6.0 s, audio 6.3 s.

Every frame was checked bit-exact against the source with `framemd5`.

### M1: the `--segments` copy join today is wrong, and says `mode: copy`

`cut.py SRC --segments 0-2,4-6,8-10`. Every cut point is a keyframe, so this is the "best case"
that `test_keyframe_aligned_bframe_segments_stay_a_lossless_copy` only checks for `mode`.

| Source | Frames (want) | Output length | Irregular pts steps | Result |
|---|---|---|---|---|
| hevc25 | 156 (150) | 6.672 s | 5 | `mode: copy`, `duration_error_ms: 672` |
| h264bf | 186 (180) | 6.381 s | 5 | `mode: copy`, `duration_error_ms: 381` |

On `beep264`, the beep lands **67 ms, then 133 ms, after its picture** in the second and third
segments. So there is an A/V drift as well as the extra frames. (P0's frame-to-beep pairing is
approximate, because its frames are not the source's.)

**Cause, from one part (`-ss 0 -t 2 -c copy -avoid_negative_ts make_zero`):**
- **The start.** `make_zero` makes the lowest DTS 0, so the video starts at pts 0.08 (the reorder
  delay) and the audio at 0.059. The concat demuxer removes each file's `start_time` (the minimum
  over its streams).
- **The end.** An input `-t` stops in **decode** order. The next GOP's keyframe (pts 2.00,
  dts 1.92) and its first P-frame (dts 1.96) are both copied. That gives 2 stray frames per part,
  and a hole where their B-frames would be.

### M1b: which copy-join design is exact

Four designs were prototyped on `0-2,4-6,8-10`:

| Design | h264bf | hevc25c (closed GOP) | hevc25 (open GOP) |
|---|---|---|---|
| P0: today (`make_zero` parts, `-t e-s`) | 186/180, gaps | 156/150, gaps | 156/150, gaps |
| P1: `make_zero`, ends at the next keyframe's **dts** | 180 exact, pts gaps | 150 exact, pts gaps | 144/150 |
| P2: P1 plus a concat `duration` directive | 180 exact, pts gaps | 150 exact, pts gaps | 144/150 |
| **P3: edit-listed parts (no `make_zero`), ends at the next keyframe's dts** | **180/180 exact, no gaps, V 6.000 s** | **150/150 exact, no gaps, V 6.000 s** | 144/150 |
| P4: no parts; the source listed with `inpoint`/`outpoint` | 180 exact, negative steps | 150 exact, negative steps | 144/150 |

- **A/V sync for P3, on `beep264`:** every *measured* beep lands at its picture, **0 ms**,
  including the first beep of the second and third segments.
  - **[R2]** The onset at output 0 s cannot be measured, because `silencedetect` has no
    silence before it. The rebuilt fixture beeps at k + 0.5 s.
  - **[R2]** Video `start_time` 0.021328 against audio 0 is AAC priming (1024 / 48000). So
    `duration_error_ms` on an exact copy join is about +21 ms, one AAC frame, not zero.
  - The audio ends 38–59 ms before the video, at the file's tail only; there is no drift.
  - The whole output starts with its video 21 ms after its audio, as P0 does.
- **P5 is worse.** P5 is P3 with the audio taken from a second input, cut to the real end. It
  drifts −5 ms and then −16 ms. P3 it is.
- **Open GOP is the limit.** In `hevc25`, the frames at 1.88, 1.92 and 1.96 decode *after* the
  keyframe at 2.0 (dts 1.80). They are leading pictures, so no decode-order cut can end a part
  cleanly there. Every design lost those 2 frames per part.

### M1c: off-keyframe cut points (h264bf, P3 parts)

- **A start that is not a keyframe:** the part alone presents exactly the right frames, because
  its edit list hides the pre-roll. The concat demuxer **ignores that edit list**, though, and
  the join presents the pre-roll. The result is a keyframe snap, as today.
- **An end that is not a keyframe:** the part carries 2 extra frames, and the join shows one
  missing frame and one stray frame.

**Conclusion:** a stream-copy join is exact only when **every part runs from a keyframe to a
keyframe, cut at the end keyframe's dts, on a closed GOP**. Everything else must snap or
re-encode.

### M2: J1 reproduced (`join.py longaudio longaudio --transition none`)

- There is a 0.333 s pts step at 5.967 s: one frame plus a 0.3 s hole.
- The average rate comes out as `1200/41`.
- The run succeeds, although `verification[duration]` is `ok: false` (12.3 measured against 12.6
  expected).
- **Correction to `ISSUES.md` J1.** This is not a stream copy. `join.py` always re-encodes, and
  its plain cut goes through the `concat` **filter**. That filter starts each clip's streams after
  the clip's *longest* stream. The crossfade path already pads both streams to `clip_length`,
  but the plain-cut path does not.

### M3: item 2 reproduced (`cut.py longaudio --segments 4-6.3,0-2`)

| Path | Hole at the join | Result |
|---|---|---|
| copy | 0.355 s | `mode: copy`, `reencode_reason: []` |
| `--accurate` (`_join_chunk`) | 0.355 s | `mode: accurate` |

Both of `cut.py`'s join paths have the bug. In `_join_chunk`, `trim`/`atrim` cut both streams to
`d`, but a video that ends early is shorter than `d` anyway, and the concat filter places the next
segment after the audio.

### [R3] M4: the user's real iPhone footage

Eight clips were inspected (packet scans over the whole file), and three were join-tested
frame by frame (P0 and P3; `framemd5` against the source; two keyframe-to-keyframe segments).

| Clip | Camera setting | Stream | GOP | P0 today | P3 |
|---|---|---|---|---|---|
| iPhone 12 `.mp4` | High Efficiency | HEVC Main 8-bit SDR, 30 fps, B-frames | open, 119 of 120 keys | not run | not run |
| iPhone 17 Pro IMG_0759 (+4 more) | High Efficiency | HEVC Main10 **HLG**, 60 fps, B-frames | open, every key but the first | **287/224 (63 stray)** | 219/224 (3 missing per end) |
| iPhone 17 Pro IMG_0776 | High Efficiency, 30 fps | HEVC Main10 HLG, B-frames | open | **170/112 (58 stray)** | 107/112 |
| iPhone 17 Pro IMG_0777 | **Most Compatible** | H.264 High SDR, **no B-frames** | closed | 116/116 exact | 116/116 exact |

- **High Efficiency HEVC (the user's default, and required for HDR and 4K60) is open-GOP.**
  Three leading pictures follow every keyframe. On this footage item 1 **re-encodes every
  `--segments` join**. That is correct output where today's is badly wrong (a quarter or more
  of the frames are stray), but it is not lossless.
- **Most Compatible (H.264) has no B-frames at all**, so a copy join is exact both today and
  after. It stays a lossless copy.
- **The 17 Pro's `.MOV` files carry an `apple_apac` spatial-audio track and 6 data tracks.** The
  re-encode fallback drops them, and reports it (`dropped_non_av_streams`).
- **Decided by the user 2026-09-29:** ship detection plus re-encode. **Smart rendering**
  (copy each segment's interior and re-encode only the GOPs at each join) is out of Phase 2, a
  possible later item.

### Not measured

- **[R2]** The prototype scripts reproduce P0, the open-GOP packet pattern and P3 on
  `hevc25c`/`h264bf`. They were not all run on every cell of the M1b table. These were **not
  measured at all**: `.mov` output, delayed-audio sources, a part whose end keyframe has no
  following GOP, and an audio-correlation sync check. Item 1 therefore starts with a prototype
  gate (step 0).

- **Real iPhone footage.** No Apple-made video was found on this Mac. Whether iPhone HEVC uses
  open GOPs decides how often item 1 falls back. The design below is correct either way; ask the
  user for a clip to measure the cost.

---

## Constraints (all items)

These are the same as Phase 1:
- Python 3.9 stdlib only.
- Result-key changes are additive under 2.x. Correcting a wrong value (`mode: copy` on a broken
  join) is a defect fix with a changelog entry.
- **No `SKILL.md` change** (29,998 of 30,000 bytes).
- New keys go into `_contract.py` and `docs/contract.md`.
- **No new `reencode_reason` enum value.** `concat_fallback` already means "`--segments` parts
  could not be joined by stream copy". The *why* goes in `notes`, and in the additive key
  described under item 1.
- Test policy:
  - assert observable results (decoded frames by hash or PSNR, packet timestamps, probes, result
    keys), never command-line spelling;
  - use literal expected values, never a production function as the oracle;
  - write each test red first, and mutation-check it.
- Each behaviour change gets a `## Unreleased` changelog entry in the same commit.

---

## Item J1: `join.py --transition none` pads each clip like the crossfade path does

**Change.** In `main`, compute `lens = [clip_length(m, fps) for m in metas]` for **both** paths.
Build the `tpad` hold / `apad` / `trim` / `atrim` per-clip chain for both, feeding
`concat=n:v=1:a=1` for `none` and `xfade` for a transition.
- **The hold rule is `clip_length`'s.** When the audio runs more than a frame past the picture,
  the last frame is held for it ("narration is never cut"). A shorter AAC tail is trimmed.
- **`expected` becomes `unpending_length(lens, 0)` for `none`.** Today it is the sum of container
  durations, which is what hid the hole.
- A pending input (dry run) keeps today's container-duration fallback, through `clip_length`'s
  own fallback.

**Tests** (`tests/test_join*.py`, alongside the existing join tests):
- **J1-a:** two `longaudio`-shaped clips (a 3.0 s picture and 3.3 s of audio, generated),
  `--transition none`. Assert:
  - every pts step of the output video is 1/fps (literal `1/30`, rounded to 4 places);
  - the frame count is 2 × 99 = 198 (99 = 3.3 s at 30 fps);
  - frame 90..98 of the output is the held last frame (identical hash to frame 89);
  - `verification[duration].ok` is true.
- **[R2]** The J1 fixtures use `testsrc2` (a picture that changes every frame), so "frame 90 has
  the same hash as frame 89" is a real hold, not a constant grey. A `--dry-run` with a pending
  input and a no-audio clip each keep planning without error.
- **J1-b (guard against over-correcting):** two clips whose AAC tail is under a frame. The output
  has 2 × 90 frames and no held frame.
- **Mutation:** keep the old `lens = durs` for `none`. J1-a must fail.

---

## Item 2: a segment past the video's end, on both `cut.py` join paths

The source's audio outlasts its video, and a **non-last** segment runs past the video's end.

**[R3] Behaviour: `clip_length`'s whole rule.**
- **More than one frame past the end:** hold the last frame for the rest of the segment. The
  requested sound is kept.
- **Up to one frame past the end:** end **both** streams at the video's end. The segment
  becomes `(s, vend)`, trimming the sub-frame audio tail. Otherwise the concat filter places
  the next segment after the tail, which leaves a fractional hole (Codex R2; J1-b measured
  the same thing in `join.py`: a 20 ms AAC tail gave a one-frame step).

- **Fallback path, `_join_chunk`.** When a segment's end is more than one frame past the source
  video's end, the video chain gets `tpad=stop_mode=clone:stop_duration=<e - vend>` before its
  `trim`. Then both streams are `d` long, and the concat filter places the next segment
  correctly.
- **[R2] The video end must be in cut-time coordinates.** `-ss`/segment times are relative
  to the file's start (`format.start_time`), and stream `start_time` is raw. So
  `vend = video.start_time + video.duration - format.start_time`, with `format.start_time` read
  once, as `seek_keyframe` already does (`_ORIGINS`). Test on the existing `hevc_offset`
  fixture (timestamps starting at 10 s).
- **[R2]** Audio-only input or output skips all of this: there is no picture to hold.
- **Copy path.** A copy cannot add frames. Before cutting, `main` checks each non-last segment,
  using the same one-frame rule. If any fails, the copy is skipped and `join_from_source` runs
  directly.
  - `reencode_reason` gets `concat_fallback`.
  - A note says: "segment N runs X s past the end of the video; a stream-copy join would leave a
    hole there, so every segment was re-cut".
- **The last segment is unchanged.** It has no join after it, so a sound-only tail is what the
  source had.

**Tests** (`tests/test_cut_copy.py`, with a new `longaudio` fixture: video 6.0 s, audio 6.3 s,
H.264 g30):
- **2-a (copy):** `--segments 4-6.3,0-2`. Assert:
  - `concat_fallback` is in `reencode_reason`;
  - the output's pts steps are all 1/30 (the hole is gone);
  - the frame count is 69 + 60 = 129;
  - output frames 60..68 are the held source frame 179.
- **2-b (`--accurate`):** the same segments, with the same frame assertions.
- **2-c (the last segment untouched):** `--segments 0-2,4-6.3`. No fallback note is added, and
  no frame is held. **[R2]** Its exact-copy assertions (frame count 120, video 4.0 s) land
  **with item 1**; before that, the copy join still leaks frames (M1). Until then, 2-c asserts
  only that `reencode_reason` has no `concat_fallback` from the item-2 pre-check.
- **[R3] 2-d (a sub-frame tail):** a source with video 6.0 s and audio 6.02 s, cut as
  `--segments 4-6.02,0-2`. Every pts step is 1/30, there are 60 + 60 frames, and the segment is
  reported trimmed to its video end in `notes`.
- **Mutation:** remove the `tpad`; remove the pre-check; remove the sub-frame trim (2-d must
  fail).

---

## Item 1: a `--segments` stream-copy join is exact, or it isn't a copy

### [R2] Step 0: the prototype gate, before production code

**[R4]** Commit `tests/prototypes/join_copy_p3.py` (not a scratch copy), so the evidence reproduces.
It runs P0 and P3 over every row below and prints frames, exactness, pts steps and beep skews:
- `h264bf` and `hevc25c` (closed GOP), and `hevc25` (open GOP);
- `.mp4` and **`.mov`** output;
- the `late_audio` fixture (delayed audio);
- a last part with no following GOP (it ends at EOF);
- a beep fixture with all onsets measurable.

**If any closed-GOP row is not exact, stop and revise this item before building.**

### Change 1: cut the parts the P3 way

In `cut_one`, when `edit_list_ok=False` (concat parts):
- **Drop `make_zero` for MOV-family parts.** The part keeps the edit list that a plain copy
  writes. In the join, that edit list places the part; it does not hide pre-roll (M1c).
  - Matroska and TS parts keep today's behaviour (`make_zero`). They get no exactness guarantee,
    and the post-join check covers them.
- **Snap the end to a keyframe.** **[R2]** Candidates are only keyframes whose **dts is after
  the part's actual seek landing** (the start keyframe's dts), so `-t` is always positive.
  Test this with a short segment spanning a B-frame keyframe. Among them, find the keyframe
  whose pts is nearest the segment's end,
  using a `seek_keyframe`-style packet scan that returns (pts, dts). If it is within
  `--tolerance` of the end, the part stops at its **dts** (`-t = key_dts - start`).
  - No keyframe within tolerance: the part re-encodes, with `tolerance` added to its own reasons.
    The parts then differ, so the join falls back as today.
  - A segment ending at or past the video's end: `-t e-s`. There are no frames after it to leak.
- **Snap the start as today** (the input `-ss` lands on a keyframe). **[R2] Each end is judged
  separately** against `--tolerance`, not only the part's total length:
  - **the start** by `|start_key_pts − start|`, which is what the join presents (M1c: the concat
    demuxer shows the pre-roll the edit list hid);
  - **the end** by `|end_key_pts − end|`.
  A snap past tolerance re-encodes that part (reason `tolerance`), as today. Today a start snapped
  0.4 s early and an end snapped 0.4 s early cancel out.

### Change 2: open-GOP detection, before the join

A keyframe is **open** when **[R2] any packet after it in decode order, up to the next
keyframe**, has a pts below the keyframe's pts. A missing or unparseable timestamp in that span,
or a scan that ends before the next keyframe, counts as **open** (conservative). These are leading pictures (M1b). The scan already reads
pts/dts/flags around each cut point.

If any **end** keyframe is open, a stream-copy join cannot be exact. The parts are not joined by
copy; `join_from_source` runs with `concat_fallback` and a note ("the source uses open GOPs:
frames before keyframe T decode after it, so a stream-copy join would drop them").
- A **start** keyframe that is open is fine in the join: the concat demuxer presents from the
  keyframe (a snap, reported as today). Its leading pictures are dropped by the decoder at a
  stream start, but mid-stream after a join they would be decoded against the wrong references.
  **So an open start keyframe on any segment but the first also forces the fallback.**
  **[R2]** This is not verified by "decodes with no errors", because reference corruption
  can decode silently. Test 1-c asserts the frames themselves.

### Change 3: verify the join, don't predict it

After a copy join exits 0, and before it is reported, measure the output **without decoding**:
- read `ffprobe -select_streams v:0 -show_entries packet=pts_time` (demux only; **[R2]**
  seconds, not time-base ticks);
- **[R3] Every pts is normalised** to cut-time by subtracting that file's `format.start_time`
  (the `_ORIGINS` value for the source; the output's own for the output), as `seek_keyframe`
  already does. The `hevc_offset` fixture (timestamps starting at 10 s) pins it.
- **[R2] (a) packet count against the source's own packets.** The expected count is the number
  of **source** video packets with `start_key_pts ≤ pts < end_key_pts`, summed over parts
  (for the last part ending at EOF, `pts ≥ start_key_pts`). The same probe on the source
  gives a literal count of what the ranges hold. That makes the check codec-agnostic: if a
  codec packs several frames per packet, both counts do. It also works under `--vfr-copy`;
- **(b) presentation continuity:** sort the output `pts_time` (presentation order; packet
  order is legitimately non-monotonic with B-frames). Every sorted step must be within ½ frame
  of 1/fps. **[R2] (b) runs only for CFR input**; under `--vfr-copy` only (a) runs.
- If either check fails: discard the join, run `join_from_source`, add `concat_fallback`, and
  add a note giving the measured count and the largest step.

This is the backstop for the shapes this plan cannot foresee: Matroska parts, unusual B-frame
structures, and open-GOP cases that change 2 misses. It is cheap because it only demuxes.

### Reporting (additive)

- **New key `join_check`** `{"packets": n, "expected_packets": m, "max_step_seconds": x|null,
  "ok": bool}`. **[R2] Presence, precisely:**
  - a successful or a failed-then-fallback copy join: the object (on failure, the failing
    measurement);
  - `--vfr-copy`: the object with `max_step_seconds: null`;
  - single segment, audio-only (no video stream), dry run, incompatible parts (no copy join
    attempted), concat-demuxer error: `null`.
  - **[R3] `null` unless every part stayed a source stream copy.** That covers `--accurate`,
    `--codec`, a forced VFR re-encode, and the item-2 pre-check's direct fallback. Re-encoded
    parts have no source-packet oracle.
- **`duration_error_ms`** is unchanged in meaning. **[R4]** On the measured fixtures (1024-sample
  AAC at 48 kHz), an exact copy join read about +21 ms, one AAC frame of priming. PCM and other
  codecs or sample rates differ, so no test pins a universal value.
- **[R4] New key `segment_end_snap_seconds`** (`--segments` only): a list with one entry per
  segment, holding the signed seconds the copied part's end moved to its keyframe
  (`end_key_pts − end`), or `null` for a part that was re-encoded or ended at EOF. It goes in
  the cut schema and `docs/contract.md`.
  - **[R4b] It describes the output.** The whole key is `null` whenever the output is not the
    joined copied parts: a single segment, a dry run, **audio-only** (no video stream, or an
    audio output extension), `join_check.ok == false`, or any fallback to `join_from_source`.
  - This is unlike `join_check`, which keeps the failed measurement because it explains why the
    fallback happened.
  - Tests: 1-e (`[0.2, 0.0]`), 1-c (open-GOP fallback → `null`), and the existing WAV
    `--segments` join (→ `null`).

### Tests (`tests/test_cut_copy.py`; new fixtures `h264bf`, `hevc25c`; the existing `hevc25` is
open-GOP)

- **1-a, rewriting `test_keyframe_aligned_bframe_segments_stay_a_lossless_copy`:** `h264bf`
  `0-2,4-6,8-10`. Assert:
  - `mode: copy`;
  - **180 frames, each bit-identical** (`framemd5`) to source frames 0–59, 120–179 and 240–299
    (literal ranges);
  - every pts step is 1/30;
  - `join_check.ok`.
- **1-b:** the same on `hevc25c`, with 150 frames.
- **[R3] 1-i (HDR open GOP):** an HLG 10-bit open-GOP fixture (x265 `open-gop=1`, HLG tags).
  **[R4]** It first asserts `reencoded: true` and `concat_fallback` in `reencode_reason` (so a
  broken detector that stream-copies cannot pass). Then the output is HEVC, `yuv420p10le`,
  with `color_transfer=arib-std-b67`, so the re-encode never flattens the user's iPhone HDR.
- **1-c (open GOP, the existing `hevc25`):** `0-2,4-6,8-10`. Assert:
  - `concat_fallback` in `reencode_reason`;
  - 150 frames;
  - every pts step is 1/25;
  - boundary frames match their source frames by PSNR (the `assertFrameIs` style).
  - *This changes the old test's `mode: copy` expectation for hevc25. The old expectation pinned
    a join that was 672 ms long.*
- **1-d (A/V sync):** a beep fixture with beeps at k + 0.5 s, cut as `0-2,4-6,8-10`. **[R2]**
  Each of the 6 beep onsets (`silencedetect`) lands within 5 ms of the pts of the frame it
  belongs to: output frames 15, 45, 75, 105, 135 and 165 at 30 fps (literal). All six onsets
  are real measurements.
- **[R2] 1-g (a short segment across a B-frame keyframe):** the end snap never yields `-t ≤ 0`.
  The output is valid and its frames are exact or it falls back.
- **[R2] 1-h (`--vfr-copy`):** the existing VFR-copy test keeps its copy. `join_check` has
  `max_step_seconds: null`.
- **1-e (an off-keyframe end within tolerance):** `h264bf` `0-1.8` joined to `4-6`. The first
  part's end snaps to the keyframe at 2.0 (0.2 s < 0.5 s), giving 60 + 60 frames, exact.
  **[R3]** `keyframe_snapped` stays **false**: by contract (`references/scripts.md:82`) it
  describes the presented *start* only. **[R4]** The test asserts
  `segment_end_snap_seconds == [0.2, 0.0]` (literal, rounded to 3 places).
- **1-f (an off-keyframe end past tolerance):** `h264bf` `0-1.0,4-6` with `--tolerance 0.3`.
  Part 1 re-encodes, so the join falls back, the frames are exact by PSNR, and there are no pts
  gaps.
- **Unit tests:**
  - open-GOP detection on synthetic packet lists (open, closed, and a keyframe at EOF);
  - the join check on synthetic `pts_time` lists: exact; one extra packet; one hole; B-frame
    packet order that sorts to exact (**[R2]** replaces the impossible "negative step" case).
- **Mutation:**
  - restore `make_zero` on parts, and 1-a must fail;
  - restore `-t e-s` on parts, and 1-a must fail;
  - disable the open-GOP check, and 1-c must still fail via the join check (showing the
    backstop works);
  - disable the join check, and 1-c must fail via the open-GOP check. Then disable **both**, and
    1-c must fail.

---

## Item T1: multi-line drawtext drops the line break

**[R2] Reproduced and root-caused, 2026-09-28.** Running
`graphics.py bg.mp4 --template hook --title "WHO SHOWS UP?" --scale 1.4` on a 1080×1920 frame
(Verdana, 128 px) renders **"WHOSHOWS UP?"** on one line, running off both edges. Its backing
box is 453 px tall, sized for two lines, so the wrap *was* decided.

- **`ISSUES.md`'s theory is wrong.** FFmpeg 9.0.2 drawtext renders `\n` from a `textfile=` as a
  line break. This was tested directly with LF and CRLF, and with `expansion=none` and `normal`.
- **The cause is one line.** `_common/drawtext.py` `drawtext_text_opts` runs
  `re.sub(r"[\x00-\x1f\x7f]", "", text)`, which strips the `\n` that `graphics.py`
  `wrapped()` inserted.
  - The two docstrings contradict each other. `wrapped()` says "drawtext … render[s] a literal
    newline as a line break", while the sanitiser says "a one-line burnt-in label has no use
    for them".
  - The stripping dates from the inline-escape era (CHANGELOG ~:1529: control characters broke
    the graph parser). The 1.15 `textfile=` route removed that reason.
- **`wrap_text`'s em-width estimate is a separate matter (T2-adjacent).** Here the wrap was
  correct: the title is wider than 90% of 1080 at Verdana 128 px. An over-eager wrap with a
  condensed face is a fit problem, not a lost break, and it is out of scope.

**Change.** **[R3]**
- **The sanitiser keeps `\n`.** It normalises `\r\n` and `\r` to `\n`, then strips the other
  control characters.
- **Centring is version-gated, not split per line.** FFmpeg ≥ 6.1 has drawtext `text_align`
  (Codex R2 corrected the earlier "7.0"). Centred templates add `text_align=C` behind a
  version gate, like the existing `boxborderw` gate. On 5.1 and 6.0 the multi-line block is
  centred as a whole (`x=(w-text_w)/2`) with its lines left-aligned inside it. The text is
  correct, only the line alignment is plainer.
  - Splitting into one drawtext per line was rejected. It would break the boxed and
    sticker-style templates, the lower-third's sliding `x`, and shared `enable`/alpha
    expressions, and it needs a line-height formula per font.
- **`overlay.py --text` is unchanged** apart from keeping a user's `\n`: one multi-line
  drawtext, left-aligned.
- **Audit the callers** (`graphics.py` :334/:359/:366/:385/:421/:447/:468, `overlay.py` :314) for
  any that relied on newlines being dropped.

**Tests.**
- A unit test: the text registered for a `"A\nB"` label keeps the newline, and `"A\x07B"` still
  loses the bell.
- **[R3] An integration test:** the `hook` template with a title that must wrap into two
  lines of **unequal width**. The font is found through the repository's existing
  font-discovery convention, since no test font is tracked in git; skip with a reason if none
  resolves.
  - Decode one frame inside the enable window, crop away the progress bar, and find the text
    rows (luma above the background).
  - There must be **two separated bands**.
  - Where `text_align` is available, each band's horizontal centre is within 2 px of the
    frame's centre.
  - A frame outside the enable window has no text.
- **Mutation:** restore the full control-character strip, and the integration test must fail.

Codex validates this section together with the rest of R2.

## Docs

- `CHANGELOG.md` `## Unreleased`, one entry per item.
- `docs/design-decisions.md`: why copy joins snap both ends to keyframes, and why they verify by
  demuxing. **[R2]** *Replace* the now-false "no length check against the parts" decision
  (~:849–861), and extend the J1 crossfade-only decision (~:634–636) to `transition none`.
- `references/scripts.md` (~:84–101) and the per-tool key table in `docs/contract.md`; the cut
  schema in `_contract.py` (~:462–477).
- `references/scripts.md` and `gotchas.md`, for the `--segments` behaviour.
- The `join_check` key in `_contract.py` and `docs/contract.md`.
- `ISSUES.md`: correct J1's component, and mark J1 fixed.

## Order and verification

1. J1 (smallest, independent).
2. Item 2 (both paths).
3. Item 1: the unit-tested helpers first (open-GOP detection, the join check), then the P3 part
   cut, then wiring.
4. T1: reproduce, write the plan section, have Codex validate it, then build.

For each item:
- run `rm -rf tests/out && env -u FFMPEG_SKILL_HW -u PARAKEET_MODEL python3 tests/test_all.py`
  and `python3 tests/test_contract.py`;
- run a Codex diff review (`gpt-5.6-terra`, xhigh), plus a pass over the fixes, until a pass
  changes no code;
- then commit.

Baseline: `test_all` 674 OK (3 skipped), contract 150 OK (1 skipped).

## Open questions

1. **Real iPhone footage:** open or closed GOP? This decides whether item 1 keeps iPhone
   `--segments` joins lossless.
2. **The held-frame rule** for items 2 and J1 (keep the sound, hold the picture), rather than cut
   the sound at the picture's end. It is chosen for consistency with `join.py`'s existing
   crossfade rule. Flag it if the user prefers otherwise.
