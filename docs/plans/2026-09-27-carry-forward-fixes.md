# Plan: carry-forward fixes — Phase 1 (cut.py correctness, hw note, caption mux)

Branch `m-series-hw-parakeet` (fork `rymalia/ffmpeg-skill`). Source of the lessons:
`~/projects/docs/ffmpeg-skill-carry-forward-guide.md` (real failures on iPhone / Core Media HEVC
footage with the upstream skill). Item numbers follow that review.

**Revision history**
- **R1**, reviewed by Codex (gpt-5.6-terra, high): REVISE, 2 critical / 7 major / 5 minor.
- **R2**, reviewed by Codex (gpt-6-sol, xhigh): REVISE, 2 critical / 8 major / 3 minor, mostly
  on item 6 and the item-4 roll-up. The user split the work into two phases.
- **R3** (Phase 1 only), reviewed by Codex (gpt-6-sol, xhigh): REVISE, 1 critical / 4 major /
  1 minor. Most R2 findings were marked resolved.
- **R4** folds in three things, marked **[R4]**:
  - every R3 finding;
  - a Codex test-quality audit of the planned tests: cut the redundant and tautological ones,
    move cheap checks to unit level, and add the missing cases;
  - two local measurements:
    - an MP4 edit-list copy overshoots at the **end** by a few frames (packet-boundary `-t` plus
      B-frame reorder);
    - `ffprobe -show_data_hash sha256` reports a per-stream `extradata_hash`, which a stream copy
      preserves.
- **R5** (this version) applies the eight findings of the Codex review of R4 (gpt-6-sol, xhigh:
  REVISE), marked **[R5]**. It is grounded in four local measurements (FFmpeg 9.0.2, 2026-09-27,
  on the HEVC fixture from item 1):
  - **The edit list presents the first source frame with pts ≥ T.** T = 4.3 gave source frame
    129 and T = 4.31 gave frame 130 (at 4.333 s); both decoded bit-identical to the source
    frame.
  - **The end overshoot is larger than R4 assumed.** A `-t 3` copy gave 94–95 frames, 4–5
    over, with `bframes=4`.
  - **A concat filter over the parts leaves a gap even after a `setpts` rebase.** The filter
    starts each segment at the end of its longest stream. A `make_zero` copy part is the wrong
    length for that: it carries keyframe pre-roll (2.4 s of video for a 2 s request) and an
    audio tail (2.44 s). Both variants showed a 0.1 s hole at the join.
  - **A join that re-cuts every segment from the source is exact.** Using per-segment input
    `-ss/-t`, then `trim`/`atrim` and a `PTS-STARTPTS` rebase into `concat`, gave 120/120
    frames, no pts gap, and V and A both 4.000 s. The boundary frames matched their source
    frames at ~55 dB against 27–31 dB for their neighbours.
  - **PCM has no `extradata_hash`**, confirmed on a `pcm_s16le` WAV.
- **Phase 2**, a separate plan later: item 6 (timeout scaling) and the item-4 render/batch
  roll-up. Their carried findings are at the end. Item 5 is out of scope.

### How R5 answers the R4 review

| R4 finding | R5 resolution |
|---|---|
| 1. PCM has no extradata | `extradata_hash` is compared as a value, where "absent in both" counts as equal (item 3.3). An audio-only join is specified (`concat=n=N:v=0:a=1`) and tested. |
| 2. The filter join needs a rebase | The fallback no longer joins the parts: it **re-cuts every segment from the source** (item 3.4). Each segment is trimmed to its exact duration and rebased, so there's no pre-roll, A/V offset or gap to repair. Continuity is tested by frame count and pts deltas. |
| 3. Rotation, SAR, HDR | Every segment decodes from the same source with the same autorotation. Encoding goes through the same `encode_args` as a single `--accurate` cut, so geometry, SAR, HDR and tags follow the existing single-cut rules. `rotation`, `color_transfer` and `color_primaries` join the copy-concat signature. A test runs on the rotated fixture. |
| 4. The lossy boundary oracle | A stdlib frame-identity helper (below). Exact `framemd5` is kept for stream-copy assertions only. The part-signature difference is asserted before a fixture is called a mismatch. |
| 5. A computable `keyframe_snapped` | The rule is measured: the edit list presents the first source frame with pts ≥ T. It's tested with an off-grid T (item 1.2). |
| 6. The 29.97 fixture | Pts are generated as `round(n × 20.02)` ticks. The file-start first delta gets a rule and a test (item 2.2). |
| 7. Audio-lag tolerance | Both sides are decoded with the same decoder. The tolerance is ±48 samples (1 ms at 48 kHz), to be tightened once measured. |
| 8. The mixed H.264/HEVC test | The fallback takes the source rather than the parts, so it can never concatenate an H.264 part with an HEVC part. The signature helper is unit-tested on prepared H.264 and HEVC parts (they must differ), and the integration mismatch test checks for a clean decode. |

**Frame-identity oracle [R5].** A test helper (in `tests/test_cut_copy.py`, shared by items 1
and 3):
- decode frames with `-vf scale=64:36,format=gray -f rawvideo` and compute PSNR in stdlib;
- a frame "is" source frame *k* when *k* is its best match within ±5 frames, the PSNR is
  ≥ 40 dB, and it leads the runner-up by ≥ 10 dB;
- `testsrc2` changes on every frame (neighbours measure 27–31 dB), so the margin separates
  adjacent frames;
- a stream copy is also checked for exactness (99 dB, meaning an identical decode).

**Suggested next step:** one short Codex pass on item 3's R5 join, then implement in the order
below.

## Constraints (all items)

- Python 3.9 stdlib only.
- Result-key changes must be additive under the 2.x guarantee (`docs/contract.md:38`). Correcting
  values that were wrong (`reencoded`/`mode`/`precision` after a concat fallback) is a defect fix
  with a changelog entry.
- **No `SKILL.md` change.** It is exactly 29,998 of 30,000 bytes
  (`tests/test_orchestration.py:1602-1610`).
- New keys go into `_contract.py` (the cut schema block ~`:461`, `REENCODE_META` ~`:257`) and
  `docs/contract.md`.
- `--vfr-copy` requires regenerating `tests/fixtures/mcp_tools.json` with `UPDATE_MCP_SNAPSHOT=1`.
- New test modules go into `tests/test_all.py`.
- Each behaviour change gets a `## Unreleased` changelog entry in the same commit.
- **Test policy [R4]:**
  - assert observable results (decoded frames, probes, result keys), never command-line
    spelling;
  - use literal expected values, never production constants as the oracle;
  - check logic cheaply with unit tests and keep real encodes for integration;
  - every new test is mutation-checked: it must fail when the guarded behaviour is broken.

---

## A. Shared refactor: structured cut outcomes

1. Keep `requested_accurate = args.accurate` before the VFR and `--codec` guards overwrite it
   (`cut.py:303-309`).
2. `cut_one` returns a per-segment outcome:
   `{"reencoded", "reasons": [...], "precision", "keyframe_snapped", "edit_list", "stored_preroll_seconds"}`.
   - `pcm_container` (`:111-113`), `copy_failed` (`:136-138`) and `tolerance` (`:140-152`) each
     add their reason.
3. **Caller reasons:** `requested` (from the saved flag), `codec`, `vfr`, `vfr_inconclusive`, and
   `concat_fallback`.
4. **New additive key `reencode_reason`**: always a list of distinct enum strings in first-seen
   order, `[]` when nothing was re-encoded.
5. **Precision is per segment.** The top-level `precision` is the least exact segment's, in the
   order `packet` < `codec_frame` < `frame` < `sample`. That's a conservative order for this
   tool's same-kind segments, not a universal scale.
   - `keyframe_snapped` is true if any segment snapped.
   - A re-encoded join never upgrades either value.
   - New key `segment_precision` (multi-segment cuts only).
6. `mode` is `copy` only when nothing was re-encoded at any stage, the join included.
7. **[R4] Wording updates:** batch's messages at `batch.py:538` *and* `:550` stop calling every
   re-encode a "hybrid tolerance fallback" and cite `reencode_reason` instead.

## Item 1 — single-segment MOV-family copies use the edit list (drop `make_zero`)

**Evidence.**
- `cut.py:131-133` adds `-avoid_negative_ts make_zero` to every stream copy.
- On Core Media HEVC this gave ~3.7 s of audio with no picture at the start, and ffmpeg exited 0.
- The plain `-ss T -i in -c copy out.mp4` writes an edit list. It was verified correct on a
  70-minute real file (guide, §2.3).

**Measurements (FFmpeg 9.0.2, 2026-09-27).**

- **HEVC fixture:** `testsrc2 640x360@30 12 s` + `sine`, encoded with `libx265
  bframes=4:b-pyramid=1:keyint=60`, `hvc1`, AAC. Cut with `-ss 4.3 -t 5`.

  | Variant | V start | A start | V duration | First decoded frame |
  |---|---|---|---|---|
  | Edit list | 0 | 0 | 5.067 s (+2 frames at the end) | = source @ 4.3 s (framemd5) |
  | `make_zero` | 0.1455 | 0 | 5.433 s | pre-roll shown |

- **The suite's own `source.mp4`** (x264 veryfast, keyframes at 0 and 8.33 s). Cut with
  `-ss 1.13 -t 4.58`:

  | Variant | V duration | A duration | Notes |
  |---|---|---|---|
  | Edit list | 4.670 s (+0.09 s at the end) | 4.582 s | |
  | `make_zero` | 5.800 s, V start 0.067 | 5.735 s, A start 0.043 | the 1.13 s pre-roll is shown |
  | `.mkv` output | | | format duration 5.8 s with or without `make_zero` (no edit lists) |

- **Conclusion.** The edit list makes the **start** exact. The **end** still lands on a packet
  boundary, and here it overshot by 2–3 frames.

**Scope.** Single-segment output only. Concat parts keep `make_zero`, and the fix is not claimed
for `--segments` (see Phase 2).

**Change.**
1. In the video stream-copy branch, with an output of `.mp4 .mov .m4v` and `for_concat=False`,
   omit `make_zero`. Every other path is unchanged.
2. **Reporting [R4, definitions tightened]:**
   - `edit_list`: true when the edit list actually changes the presentation. Probe the output's
     video stream twice, normally and with `-ignore_editlist 1`; if their `duration` or
     `start_time` differ, an edit list is in effect.
   - `stored_preroll_seconds` = `max(0, duration_ignoring_editlist − duration_presented)` for
     the video stream. It is `null` if either probe fails. On the HEVC fixture it measured
     5.433 − 5.067 = 0.367 s, which equals the negative-pts span.
   - `keyframe_snapped` **[R5, a computable rule]**:
     - When `edit_list` is true it is **false**. The measured rule is that the edit list
       presents the first source frame with pts ≥ T, which is within one frame of the request
       by construction.
     - When `edit_list` is false and the copy started more than one frame from T (for
       example `.mkv`, which has no edit lists), it is true.
     - It is only ever true on a stream copy.
   - `duration_delta_seconds`: unchanged in meaning (presented minus requested). It is now
     small and positive, the end overshoot.
   - Note, when `edit_list` is true: "N s of pre-roll stored, hidden by the MP4 edit list; a
     player or tool that ignores edit lists will show it."
3. **Tolerance check.** It still compares the presented duration. If format and video-stream
   durations differ by more than one frame, use the video stream's and add a note.
4. **A/V start check.**
   - New compact-probe fields `video.start_time` and `audio.start_time`.
   - Additive `av_start_skew_seconds` (null when either stream is absent).
   - A warning note suggesting `--accurate` when the absolute skew exceeds max(2 frames, 0.1 s).
   - Never re-encode automatically.

**Tests** (new `tests/test_cut_copy.py`, on the HEVC fixture unless noted).
- **First frame:** the output's decoded first frame equals the source frame at T (framemd5),
  with T on a frame boundary.
- **Off-grid first frame [R5]:** with T = 4.31 (between frames 129 and 130), the first frame is
  source frame **130**, pinning the pts ≥ T rule. This is the literal index, not a computed
  one.
- **Last frame [R4]:** the output's last presented frame equals the source frame at *its actual
  presented timestamp*. That timestamp is read from the output, not computed as T + d.
- **End overshoot [R5]:** bounded separately as `0 ≤ output video duration − requested ≤ 6
  frame durations`. The fixture has `bframes=4` and measured +4 to +5 frames at `-t 3`.
- **Audio lag [R4, R5 tolerance]:**
  - use a **non-periodic** audio track (`anoisesrc` with a fixed seed, mixed at a low level
    with a chirp), so cross-correlation can't lock on a repeat;
  - decode the source window and the output with the same decoder and settings (`-c:a aac`
    priming handled identically, 48 kHz mono s16);
  - the lag must be within **±48 samples (1 ms)**, computed in stdlib;
  - record the measured value in the test's comment and tighten the bound to it plus a margin.
- **Report fields:** `edit_list` true; `stored_preroll_seconds` ≈ 0.367 (within one frame);
  `keyframe_snapped` false; `mode` copy; `reencode_reason` `[]`; skew ≈ 0.
- **Non-zero source start** (`-output_ts_offset 10`): the same decoded first-frame check, plus
  `edit_list` true.
- **An already edit-listed source** (the first output fed back in): the second output's decoded
  first frame matches.
- **A/V skew above the threshold [R4, missing before]:** a unit test of the skew and warning
  computation with synthetic start times (0.0 vs 0.5 s), checking that the note names
  `--accurate`. No encode.
- **No-audio skew [R4, moved to unit level]:** the same unit test with the audio absent gives
  `null`.
- **Existing tests updated [R4, both of them]:**
  - `test_editing.py:52-57` (`test_cut_json_reports_requested_vs_actual_and_mode`): the MP4
    copy at 2–6 s. `keyframe_snapped` becomes false, since the start is presented exactly. The
    comment says why.
  - `test_editing.py:91` (`…keyframe_snap_reports_a_real_nonzero_delta`): switch its output to
    `.mkv`, the unchanged path, where the non-zero delta and `keyframe_snapped` true still hold.
    The docstring gets a note.
- **Cut [R4]:**
  - "command omits `-avoid_negative_ts`": command spelling;
  - "audio-only still uses `make_zero`": command spelling. The existing audio-cut tests cover
    that behaviour;
  - the separate `.mkv` test: redundant with the updated `:91`;
  - the "MP4 path" rewrite of `:91`: redundant with the new decoded-frame tests.

## Item 2 — VFR guard: sampled measurement, honest reporting, opt-out

**Evidence.** `probe.py:235` flags VFR when `|r − avg| > 0.01`, and iPhone files (30 vs 29.979)
trip it. `cut.py:303` then forces `--accurate` with no opt-out.

**Change.**
1. **`measure_frame_timing(path, duration)`** in `_common/probe.py`, exported through
   `_common/__init__.py`, is split into two parts:
   - **the pure `classify_frame_timing(windows, time_base) -> dict`**, where `windows` is a list
     of pts lists. This is where every classification test runs, with no encodes;
   - **the ffprobe driver**: one call per window, using
     `ffprobe -v error -select_streams v:0 -show_packets -show_entries packet=pts_time:stream=time_base -of json -read_intervals "<start>%+6" <path>`.
     This returns packets plus `streams[0].time_base` on FFmpeg 9.0.2. There are five windows
     of 6 s, evenly spaced, with fewer on short files.
2. **Classifier rules [R4: no in-window outliers allowed].** Per window:
   - skip pts that are missing or non-finite;
   - sort (decode order puts B-frames out of sequence);
   - take consecutive deltas and drop zero deltas;
   - **[R5]** in the window that begins at the file's first packet only, drop the **first**
     delta. A container-start interval (an edit-list or priming artefact on the first frame) is
     not evidence of variable timing. Every other delta counts, including the first delta of
     later windows;
   - the tolerance is max(1 ms, one time-base tick + 1 µs).

   The result is one of:
   - **`sampled_cfr`**: **every** delta in **every** window is within tolerance of that
     window's median, and the window medians agree. A single dropped or irregular frame inside
     a sampled window is therefore `vfr`. *(R3 finding 3: the 99% rule let one outlier
     through.)*
   - **`vfr`**: otherwise.
   - **`inconclusive`**: fewer than 20 deltas in total, or an ffprobe failure.
3. **Guard policy:**
   - `vfr` forces `--accurate` with reason `vfr`;
   - `inconclusive` forces it with reason `vfr_inconclusive`;
   - `sampled_cfr` keeps the copy.
4. **The between-window limitation is explicit.** VFR confined to an unsampled stretch is called
   `sampled_cfr`. That's accepted: the guard it replaces is a whole-file average, the copy is
   lossless, and `--accurate` is always available. The key reports
   `vfr_check: {heuristic: true, measured, method: "sampled", windows, deltas}`.
5. **`--vfr-copy`** keeps the copy even on `vfr` or `inconclusive`, with a note.
6. The measurement runs under dry run (it's read-only). Audio-only input gets no check and no
   key. `variable_frame_rate_suspected` keeps its meaning.

**Tests.**
- **Classifier unit tests with fixed timestamps, no encodes [R4]:**
  - exact 1/30 → `sampled_cfr`;
  - **[R5]** 29.97 at time base 1/600: pts = `round(n × 600 × 1001 / 30000)` ticks, which is
    mostly 20-tick deltas with a 21 about every 50 frames (not alternating) → `sampled_cfr`.
    The test asserts that the fixture's delta multiset has 21-tick deltas in it;
  - **[R5]** an unusual first delta at the file start on an otherwise CFR stream →
    `sampled_cfr`; the same unusual delta as the *second* delta → `vfr`;
  - **one dropped frame** (a single 2× delta) in one window → `vfr`;
  - jitter → `vfr`;
  - VFR only in the stretch between windows (the windows themselves are clean) → `sampled_cfr`,
    which pins the documented limitation;
  - unsorted B-frame order → the same result as sorted;
  - fewer than 20 deltas → `inconclusive`.
- **Integration**, cut with real fixtures:
  - The false-positive fixture keeps `mode: copy`, with `measured: sampled_cfr`. Recipe:
    1. Encode `testsrc2 @30 10 s` with `libx264 -bf 0 -video_track_timescale 600`.
    2. Remux with `-c copy -bsf:v "setts=duration=if(eq(N\,299)\,DURATION*8\,DURATION)"`. That
       gives avg 29.316 vs r 30, while every pts delta is 1/30 s. A `setts` remux resets the
       track timescale, so pass `-video_track_timescale` again if one matters.
  - A genuinely VFR fixture (a `setpts` jitter with `-fps_mode passthrough`) gives
    `measured: vfr`, `reencode_reason: ["vfr"]` and `reencoded: true`.
  - `--vfr-copy --tolerance -1` on it gives `mode: copy`.
  - A mocked ffprobe failure gives `["vfr_inconclusive"]`, **and** the cut really re-encoded.
  - A dry run carries `vfr_check`; audio-only input has none.
- **Cut [R4]:**
  - "`--vfr-copy` with the default tolerance": not a stable assertion;
  - the separate 29.97/600 encode: moved to a classifier unit test.

## Item 3 — re-encoded cuts keep the source codec; a safe join

**Evidence.**
- `encode_args` goes through `video_args` (`decision.py:453`), which sends SDR to x264, so an
  HEVC source comes out H.264.
- Mixed parts are joined with `-c copy`.
- **The existing join fallback is itself unsafe [R4, R3 critical].** `cut.py:366` re-encodes
  through the **concat demuxer** (`-f concat -i list`), which requires compatible streams
  whatever the output codec. Codex observed H.264 followed by HEVC through it exiting 0 while
  logging decoder errors, which is a corrupt "success". This bug exists today, independent of
  the plan.

**Change.**
1. **`source_codec_video_args(meta, crf, preset)`**, exported through `_common/__init__.py`:
   - For SDR HEVC with no `--codec`, it returns `encoder_args("hevc", …)`: through
     `_maybe_hw`, with `hw_swaps` recorded, BT.709-tagged.
   - Otherwise it returns `video_args(...)`.
   - `cut.py`'s `encode_args` uses it.
2. **Contract text:**
   - `docs/contract.md:208`: "…except `cut.py` re-encodes keep an SDR HEVC source's codec".
   - `_contract.py:80`: cut's x265 capability also covers SDR HEVC.
3. **Compatibility signature [R4, strengthened].** One full ffprobe per part with
   `-show_data_hash sha256` (verified: it gives a per-stream `extradata_hash`, which a stream
   copy preserves). Compare:
   - **stream order and types**, as an ordered list of `codec_type`;
   - video: codec, profile, pix_fmt, width, height, `r_frame_rate`, `time_base`, SAR,
     **`extradata_hash`**, and **[R5]** `rotation`, `color_transfer` and `color_primaries`;
   - audio: codec, sample_rate, channels, `time_base`, `extradata_hash`.
   - **A failed probe, or a missing stream, counts as incompatible.** (FFmpeg's automatic concat
     conversion covers H.264-in-MP4 but not HEVC, so for the HEVC case this plan centres on,
     only an exact match is safe.)
   - **[R5] Fields are compared as values:** a field that's absent from *both* parts is equal,
     and absent from only one is a mismatch. PCM carries no `extradata_hash`, so two WAV parts
     still match and keep their lossless copy join. An H.264 or HEVC part that lost its
     extradata no longer matches one that has it.
4. **A safe join fallback [R4, redesigned in R5].** On any mismatch, or if the copy concat
   fails, **re-cut every segment from the source** in one filter graph. The parts are
   discarded. The fallback is a re-encode, so no segment keeps a lossless copy either way, and
   re-cutting avoids having to repair parts that are the wrong length (the pre-roll and audio
   tail measured above).
   - One input per segment: `-ss <s_i> -t <d_i> -i SRC`. Input seeking with the default
     `accurate_seek` decodes from the prior keyframe and discards frames up to `s_i`.
   - Per segment: `[i:v]trim=duration=<d_i>,setpts=PTS-STARTPTS[v_i]` and
     `[i:a]atrim=duration=<d_i>,asetpts=PTS-STARTPTS[a_i]`. Both streams are cut to the same
     length, so the concat filter's longest-stream rule leaves no gap.
   - `concat=n=N:v=V:a=A`:
     - V = 1 when the source has video and the output isn't an audio extension;
     - A = 1 when the source has audio;
     - **audio-only: `concat=n=N:v=0:a=1`**, with `-vn` and the output extension's audio codec.
   - Then `-sn -dn`, and `encode_args(meta, output, crf, preset)`: the same codec, CFR, HDR and
     tag rules as a single `--accurate` cut, including item 3.1's source codec.
   - Every segment decodes from the same source with the same autorotation, so rotation, SAR
     and geometry are consistent by construction. The output is display-oriented with rotation
     0, as the `--accurate` path already produces.
   - **Reporting:** `concat_fallback` in the reasons; `reencoded` true; `mode` is not `copy`;
     `segment_precision` is each segment's re-encoded precision (`frame` for video, `sample` or
     `codec_frame` for audio); `keyframe_snapped` false; `dropped_non_av_streams: true` when
     the source had any.
   - This replaces the demuxer path at `:366`, which also fixes today's bug: that path
     concatenated incompatible parts, and the new one never takes parts at all.
   - A copy concat of matching parts isn't decode-checked. The signature match is the guard,
     and the fallback runs if the copy concat still fails.

**Tests.**
- **Codec kept:** an SDR HEVC source with `--accurate` gives `hevc`, `hvc1` and BT.709.
- **Explicit override:** `--codec h264` on HEVC gives `h264`.
- **Helper, unit level [R4]:**
  - with `STATE.hw` true and `_maybe_hw`'s platform and encoder checks mocked,
    `source_codec_video_args` returns the `hevc_videotoolbox` line and records a CPU swap;
  - with HDR metadata, it returns the unchanged `video_args` result.
  - No real VideoToolbox encode.
- **A guaranteed mismatch [R4, replacing the "match or fallback" test that couldn't fail]:**
  - Build a two-segment HEVC cut whose first segment starts on a keyframe (copy) and whose
    second starts mid-GOP, with a tolerance small enough to force a re-encode, but not 0,
    since `abs(delta) >= 0` re-encodes everything.
  - Before running it, check the fixture: the first segment's copy delta is below the chosen
    tolerance and the second's is above it.
  - Assert: `concat_fallback` is in the reasons, `reencoded` true, `mode` not copy, and
    `segment_precision == ["frame", "frame"]` **[R5: the fallback re-cuts both segments]**.
  - **Continuity [R5]:**
    - the frame count equals the literal sum of the segments' frame counts;
    - every consecutive pts delta is one frame;
    - video and audio durations agree within one frame.
  - **Boundary identity [R5]:** four output frames (first, last of segment 0, first of
    segment 1, and last) are identified by the frame-identity oracle as the literal source
    frame indices for the requested edges. The oracle is not exact `framemd5`.
  - The output decodes clean: `ffmpeg -v error -i out -f null -` gives empty stderr.
- **Signature helper, unit level on prepared parts [R5, replaces the mixed-codec join test]:**
  - an H.264 part and an HEVC part of the same source differ;
  - a copy part and a re-encoded part of the same codec differ, since their `extradata_hash`
    differs. The test asserts that premise directly;
  - two WAV (PCM) parts match, with no extradata on either side;
  - a rotated copy part differs from its auto-rotated re-encode.
- **Audio-only fallback [R5]:** on a WAV source, the join helper is called with two segments
  and an audio-only meta. The output has 0 video streams and 1 PCM audio stream, and its sample
  count is the literal sum of the segments' counts.
- **WAV copy join stays lossless [R5]:** `cut.py talk.wav --segments …` (with no
  `--accurate`) gives `mode: copy` and no `concat_fallback`. That's the R4 finding 1
  regression.
- **Rotated source [R5]:** on the rotated fixture (`test_editing.py`'s `self.rot`), a mixed
  copy/re-encode `--segments` cut gives `concat_fallback`, `rotation` 0, output
  width × height = the source's **display** size, and the continuity checks above.
- **Subtitles:** a source with a subtitle stream and mixed parts gives `concat_fallback` and
  `dropped_non_av_streams: true`, and the output probe shows 0 subtitle streams.
- **Cut [R4]:**
  - "H.264 source stays H.264": existing cut tests already probe H.264 output;
  - the real `FFMPEG_SKILL_HW` VideoToolbox cut: moved to the helper unit test.

## Item 4 (Phase 1 part) — a per-tool note on env-chosen GPU encodes

In `_common/emit.py` `_encoder_report` (~`:86`): when `used` is true and `source == "env"`, add
one note to `hw.notes` ("VideoToolbox chosen by FFMPEG_SKILL_HW=1 (machine default; ~1.2–2.5× the
bytes of x264/x265 at matched quality); rerun with --no-hw for a final deliverable"). Every tool
emits it. The roll-up is Phase 2.

**Test [R4: one parameterized unit test of `_encoder_report`, no encodes].** Each case sets
`STATE.commands` to a VideoToolbox or libx264 command line and checks the result:
- `(hw=True, source="env", used)` has the note;
- `(hw=True, source="flag", used)` has no note;
- `(hw=True, source="env")` with a CPU fallback has no note, since the GPU wasn't used;
- `hw=False` gives a result where the **`hw` key is absent**. The earlier "`hw` is null" claim
  was wrong: `emit.py:83` omits it.

## Item 7 — `caption.py --mode mux --transcribe` reports `transcription`

Add `**({"transcription": args._asr} if getattr(args, "_asr", None) else {})` to the mux `emit`
(`caption.py:1428`); the metadata is already set at `:1253`.

**Test.** In `test_accel.py`'s `ParakeetEngineTests`, which already has the fake-engine PATH, run
`caption.py … --transcribe --mode mux --engine parakeet.cpp` and check that
`transcription.engine == "parakeet.cpp"`. It's mutation-checked by removing the new kwarg.

## Open question for the user (not in Phase 1 unless approved)

- **An engine that produces garbage is reported as "no speech".** If a Parakeet engine outputs
  malformed JSON, the parsers correctly return nothing (pinned by
  `test_malformed_engine_output_yields_no_words_instead_of_crashing`). `run_parakeet` then calls
  `die_no_speech`, which reports **"no speech in the video"** instead of "the engine's output was
  unreadable". The proposed fix: when the engine exited 0 but its output didn't parse, log it
  and fall through to the next engine, the same as a crash.

---

## Docs (Phase 1)

- `references/scripts.md`: `cut.py`'s new keys and `--vfr-copy`, the source-codec re-encode, and
  the source re-cut join fallback.
- `references/gotchas.md`: the Core Media HEVC edit-list lesson; that edit-listed copies store
  pre-roll; and that the end still lands on a packet boundary.
- `docs/contract.md` and `_contract.py`: the new additive keys, plus the item 3 text.
- `CHANGELOG.md` `## Unreleased`: behaviour changes, plus defect fixes for the concat-fallback
  report values **and the unsafe concat-demuxer re-encode**.
- `docs/design-decisions.md`: the why behind the item 1 edit-list semantics, the item 2 sampled
  measurement, and the item 3 source re-cut join.

## Order and verification

1. Refactor A.
2. Item 3's safe join, landed first because it fixes a live bug.
3. Items 1, 3 (the codec part) and 2.
4. Item 7.
5. Item 4.
6. Regenerate the MCP snapshot once, after `--vfr-copy`.

Run the full suite on an empty `tests/out/` after each group. Baselines on this M3 Air: `test_all`
612 OK (3 skipped, after `1605b66`), contract 150 OK (1 skipped). The `test_accel.py` cleanup has already
landed. Commit per group, with a Codex diff review before each commit.

---

## Phase 2 (separate plan later) — carried findings

**Item 6, timeout scaling.** Direction: a `timeout_source` slot and a `max_input_duration`
basis. Unresolved:
- MCP always passes `per_call` (`mcp/server.py:98`; test at `tests/test_contract.py:1634`).
- A parallel batch has a shared flat deadline (`batch.py:265`; pinned at
  `tests/test_orchestration.py:1225`).
- ASR uses the flat `STATE.timeout` (`asr.py:129, :194, :656`).
- Keep a finite, duration-aware outer watchdog.
- `verify.py`'s 600 s stays as it is.

**The item-4 roll-up (`stage_hw`).**
- Render cache hits have no child document (`render.py:515`), and the sidecar stores no hw
  (`:666`).
- Pack (`:326`) and plan (`:718`) runs have their own paths.
- Batch discards step documents (`batch.py:160`), and batch projects nest render documents.

**Item 1 on `--segments`.** Edit-listed concat parts need decoded join-boundary tests before
`make_zero` can be dropped there.
