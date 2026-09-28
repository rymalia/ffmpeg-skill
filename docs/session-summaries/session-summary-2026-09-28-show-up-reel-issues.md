---
session_id: fbcf60fc-9f34-4fff-984c-ad77151b350a
date: 2026-09-28
time: "9:55 AM PDT – 12:58 PM PDT"
resumed: "11:31 AM PDT"
project: ffmpeg-skill
branch: m-series-hw-parakeet
---

# Session Summary: "SHOW UP" reel stress test and ISSUES.md

## Overview

Used the installed ffmpeg-skill end to end on two real sources to build a 64 s vertical Reel (Druski's
"show up for the work" speech cut against Trey Anastasio / John Mayer concert footage), iterating through
four versions. Every skill defect or rough edge hit along the way was logged, then rewritten as a permanent,
component-grouped `ISSUES.md` and committed (`bde9c54`).

Timestamps: the start time is from the first SessionStart hook in context (`SESSION_START_TIME=2026-09-28
09:55 AM PDT`). The session resumed at 11:31 AM PDT after a network drop, and the metadata collector then
reported `session_start` = the resume time (11:31); the original 9:55 hook value is used for the start.

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| **Concept: Druski's speech as the spine, concert shots as cutaways, concert music ducked under the voice, hard cut to a full-volume concert climax** | Speech content ("nobody shows up for the work") maps onto musicians doing the work; the drop from ducked bed to full music gives the ending a payoff |
| **Bed audio taken so it runs straight into the outro (concert 606.5–663.7 s → outro 663.7–670.3 s)** | The outro's own audio is the continuation of the bed, so the cut is seamless with no doubled music |
| **Cutaways chosen per spoken line, not per beat** | `scenes.py --beats` measured 113 BPM at confidence 0.35 (`usable: false`) |
| **Per-shot Druski crops (crop-x 0.5 / 0.63 / 0.5 at the 8.2 s and 17.9 s shot changes)** | The face moves between wide and tight shots; `cropdetect --motion-centre` tracked hands, so framing came from contact sheets |
| **Wide concert shots blur-fit, close-ups crop-fit** | Keeps both guitarists in wide shots; close-ups fill the frame |
| **Futura Condensed ExtraBold for titles (user choice from an 8-font comparison)** | User disliked the DejaVu default; face extracted from `Futura.ttc` (index 4) with fontTools because the skill can only use face 0 of a collection |
| **Hook burned with `graphics.py` before `render.py`, at `--scale 1.19`** | `graphics[]` in a project can't take a font; above ~109 px the wrap/newline bug drops the space ("WHOSHOWS UP?") |
| **v4 ending: face-crop close-up of the blue-guitar player with the joke line placed below the mic (user-marked area)** | User's choice after comparing wide vs face crop; lines moved to 800/900 px so the face stays visible |
| **ISSUES.md rewritten as a permanent, component-grouped reference at the repo root** | User asked for it to target the skill and its code, not this session, for future fixes and documented workarounds |

## Changes Made

| Change | Detail |
|--------|--------|
| **ISSUES.md** | New file at repo root: 14 numbered entries (T1–T5, R1–R3, J1, A1–A3, O1–O2) plus environment notes; each with component, symptom, repro, cause, workaround, fix direction, severity. Committed as `bde9c54` |
| **Reel deliverables (outside the repo)** | `~/Downloads/show_up_reel.mp4` (v1), `show_up_reel_v2.mp4` (high-res Druski + Futura titles), `show_up_reel_v3.mp4` (wide ending), `show_up_reel_v3_face.mp4`, `show_up_reel_v4.mp4` (face crop, joke line below mic). All 1080x1920, 30 fps, H.264, AAC stereo, ~-13.9/-14.0 LUFS, -1.0 dBTP, 64.00–64.07 s |
| **Memory** | Added `scratchpad-lost-on-resume.md` + MEMORY.md pointer: keep user-requested tracking files out of the scratchpad |
| **This summary** | `docs/session-summaries/session-summary-2026-09-28-show-up-reel-issues.md` |

No skill source code was changed.

## Testing / Research Performed

- `probe.py` on all three sources (druski-large confirmed a drop-in: 3096x1764, same 1712 frames; `sync.py` offset 0.0, confidence 0.613).
- Transcription with Parakeet (`parakeet-mlx`, `parakeet-tdt-0.6b-v2`) via `caption.py --transcribe`.
- `scenes.py` on the 686 s concert: 212 scenes, 212 labelled shots (104 static / 58 motion / 50 pan), 829 audio peaks, beat grid unusable. The `--sheet` run failed (exit 244) and was reproduced.
- Every render finished with `check.py --platform reels`: 12 PASS, 1 WARN (subtitles: none; captions are burned in) for v1–v4.
- `look.py` frames and contact sheets viewed for every version (captions in the safe area, title fit, crop placement).
- Root-caused the dropped-space hook bug by reproducing `wrap_text` output at font sizes 91–128 (wraps from 111 px) and confirming a non-breaking space is normalised.
- Confirmed v3's audio is unchanged vs v2 (`sync.py` offset 0.0; identical 1912-frame video) while the container length differs (64.000 vs 64.073 s).
- Traced the 29.887 fps output to a 0.237 s video timestamp gap from a stream-copy `join.py` (video 57.067 s vs audio 57.304 s).

## Summary Statistics

- 4 reel versions (+1 variant) rendered and checked; 13 check rows each.
- 8 fonts compared on 2 title placements (16 sample renders).
- 14 numbered issues documented (2 High, 5 Medium, 7 Low) plus 2 environment notes.
- 1 commit (`bde9c54`), 1 file added to the repo before this summary.

## Discoveries / Handoff Notes

- **The session scratchpad is wiped on resume.** Everything in `/private/tmp/.../scratchpad` (project JSONs, extracted fonts, intermediates, the first ISSUES draft) was lost at 11:31 AM; only `~/Downloads` copies survived. ISSUES.md was rebuilt from the conversation.
- **Rebuilding the reel pieces**, if more edits are needed: Druski crops `cut.py --accurate` 0–8.2 / 8.2–17.9 / 17.9–57.214 on `druski-large.mp4`, `fit.py --aspect 9:16 --fit crop --crop-x 0.5 / 0.63 / 0.5 --width 1080 --height 1920`. Cutaways (concert time → reel window): 298.6–302.3 blur → 5.9–9.6; 183.0–185.3 crop 0.36 → 19.4–21.7; 373.5–376.3 blur → 22.4–25.2; 353.5–357.1 blur → 25.2–28.8; 522.4–525.0 crop 0.91 → 29.9–32.5; 646.4–650.0 blur → 39.6–43.2; 502.5–507.1 crop 0.43 → 44.2–48.8. Bed 606.5–663.7 (`audio.py --music-volume -16 --duck --duck-amount 14`); outro 663.7–670.3 blur; final shot 303.0–305.9 crop 0.75 → 61.134–63.97. Titles: hook "WHO SHOWS UP?" `--scale 1.19` 0–3 s; "SHOW UP." overlay 170 px, margin 300, 58.2 s on; "OR WE’RE STUCK" / "WITH THIS IDIOT" 84 px at margins 800 / 900 from 61.134 s. The last cue of the SRT had "cl"/"ips" merged into "clips".
- **`FFMPEG_SKILL_HW=1` is set in the environment**, so all intermediates were encoded with `h264_videotoolbox`.
- Files `show_up_reel_v4 copy.mp4`, `-trimmed`, `-360`, `-480`, `-720` in `~/Downloads` were made by the user, not this session.

## Current State

- Branch `m-series-hw-parakeet`, head at `bde9c54` before this summary's commit; nothing pushed.
- `CLAUDE.local.md` is untracked and was deliberately left out of commits.

## Unfinished Work

- Open question to the user: raise "SHOW UP." ~100 px during the final 2.8 s of v4 so the guitarist's head is fully clear, or leave it.
- None of the ISSUES.md entries are fixed yet; T1 (hook line-break bug) and A1 (`scenes.py --sheet` losing all measurements) are the High-severity starting points.
- Push when ready: `git push -u origin m-series-hw-parakeet`.
