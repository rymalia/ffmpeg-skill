#!/usr/bin/env python3
"""Phase 2 item 1, step 0: the prototype gate for an exact `--segments` stream-copy join.

Not part of the suite. It rebuilds the evidence in docs/plans/2026-09-28-carry-forward-phase2.md
(M1, M1b) from lavfi fixtures and compares two ways of cutting the parts a concat-demuxer join
reads:

  P0  today:  -ss s -i SRC -t (e-s) -c copy -avoid_negative_ts make_zero
  P3  the plan: -ss s -i SRC -t (end_key_dts - s) -c copy     (edit-listed, no make_zero;
              a part that ends at the source's end keeps -t (e-s))

Every output frame is checked bit-exact (framemd5) against the literal source frames the
segments name, and every presentation step against 1/fps. The beep rows also measure A/V sync:
each beep's onset against the pts of the frame it belongs to.

A row passes when its frames are exact, every step is within half a frame of 1/fps (the plan's
join check), and every beep lands within 5 ms. `max step` shows what remains below half a frame:
with no B-frames a part's audio ends up to one AAC frame after its video, the concat demuxer
places the next part after the audio, and that frame is shown a few ms longer. Both streams of
the next part move together, so the beeps stay in sync (the nob row).

    python3 tests/prototypes/join_copy_p3.py [--dir tests/out/prototypes]

Exit status 1 when a closed-GOP row is not exact with P3 (the plan's stop condition).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BEEP = "aevalsrc='if(between(mod(t\\,1)\\,0.5\\,0.54)\\,0.8*sin(2*PI*1000*t)\\,0)':s=48000:d=12"
DELAY = 0.379   # the late_audio offset the suite uses


def run(*args, check=True):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if check and r.returncode:
        raise SystemExit(f"failed: {' '.join(map(str, args))}\n{r.stderr[-800:]}")
    return r


def ff(*args):
    return run("ffmpeg", "-y", "-v", "error", *args)


def fixtures(d):
    """name -> (path, fps, closed_gop). Built once; delete the directory to rebuild."""
    tsrc = lambda fps, dur: ("-f", "lavfi", "-i", f"testsrc2=s=320x180:r={fps}:d={dur}")
    sine = lambda dur: ("-f", "lavfi", "-i", f"sine=f=440:d={dur}:sample_rate=48000")
    x264bf = ("-c:v", "libx264", "-g", "60", "-bf", "3", "-x264-params", "scenecut=0")
    x265 = lambda extra: ("-c:v", "libx265", "-x265-params",
                          f"bframes=4:keyint=50:min-keyint=50:scenecut=0:log-level=error{extra}",
                          "-tag:v", "hvc1")
    recipes = {
        "h264bf": (30, True, lambda p: ff(*tsrc(30, 12), *sine(12), *x264bf, "-c:a", "aac", "-shortest", p)),
        "hevc25c": (25, True, lambda p: ff(*tsrc(25, 12), *sine(12), *x265(":open-gop=0"), "-c:a", "aac", "-shortest", p)),
        "hevc25": (25, False, lambda p: ff(*tsrc(25, 12), *sine(12), *x265(""), "-c:a", "aac", "-shortest", p)),
        "beep": (30, True, lambda p: ff(*tsrc(30, 12), "-f", "lavfi", "-i", BEEP, *x264bf, "-c:a", "aac", "-shortest", p)),
        # no B-frames, the shape of iPhone "Most Compatible" H.264
        "nob": (30, True, lambda p: ff(*tsrc(30, 12), "-f", "lavfi", "-i", BEEP, "-c:v", "libx264", "-bf", "0", "-g", "60",
                                       "-x264-params", "scenecut=0", "-c:a", "aac", "-shortest", p)),
    }
    out = {}
    for name, (fps, closed, make) in recipes.items():
        p = d / f"{name}.mp4"
        if not p.exists():
            make(p)
        out[name] = (p, fps, closed)
    # delayed audio: the suite's late_audio (baseline, no B-frames), and the same offset on
    # B-frame sources, where the part's own start_time is the video's reorder delay
    late = d / "late_audio.mp4"
    if not late.exists():
        base = d / "late_base.mp4"
        ff(*tsrc(30, 8), "-f", "lavfi", "-i", "sine=f=440:d=8", "-c:v", "libx264", "-profile:v", "baseline",
           "-g", "30", "-c:a", "aac", base)
        ff("-i", base, "-itsoffset", DELAY, "-i", base, "-map", "0:v", "-map", "1:a", "-c", "copy", late)
    out["late_audio"] = (late, 30, True)
    for name in ("h264bf", "beep"):
        p = d / f"{name}_late.mp4"
        if not p.exists():
            src = out[name][0]
            ff("-i", src, "-itsoffset", DELAY, "-i", src, "-map", "0:v", "-map", "1:a", "-c", "copy", p)
        out[f"{name}_late"] = (p, 30, True)
    return out


def hashes(p):
    raw = run("ffmpeg", "-v", "error", "-i", p, "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "framemd5", "-").stdout
    return [l.split(",")[-1].strip() for l in raw.splitlines() if l and not l.startswith("#")]


def frame_pts(p):
    o = run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time", "-of", "csv=p=0", p).stdout
    return sorted(float(x.strip(",")) for x in o.split())


def streams(p):
    o = json.loads(run("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,start_time,duration",
                       "-of", "json", p).stdout)
    return {s["codec_type"][0]: (round(float(s["start_time"]), 3), round(float(s.get("duration", "nan")), 3))
            for s in o["streams"]}


def keyframes(src):
    """[(pts, dts)] of every video keyframe, normalised by the file's format.start_time."""
    fmt = json.loads(run("ffprobe", "-v", "error", "-show_entries", "format=start_time", "-of", "json", src).stdout)
    origin = float(fmt["format"].get("start_time", 0) or 0)
    o = run("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,dts_time,flags",
            "-of", "csv=p=0", src).stdout
    keys = []
    for line in o.split():
        p, d, f = line.split(",")[:3]
        if "K" in f:
            keys.append((float(p) - origin, float(d) - origin))
    return keys


def onsets(p):
    """Beep onsets: every silence_end, less the one silencedetect logs where the audio ends."""
    log = run("ffmpeg", "-v", "info", "-i", p, "-map", "0:a:0", "-af", "silencedetect=n=-30dB:d=0.3", "-f", "null", "-").stderr
    start, dur = streams(p)["a"]
    return [float(x) for x in re.findall(r"silence_end: (-?[0-9.]+)", log) if abs(float(x) - (start + dur)) > 0.005]


def cut_parts(design, src, segs, keys, ext, tag, d):
    names = []
    for i, (s, e) in enumerate(segs):
        part = d / f"{tag}_{design}_{i}{ext}"
        names.append(part)
        if design == "P0":
            ff("-ss", s, "-i", src, "-t", e - s, "-c", "copy", "-avoid_negative_ts", "make_zero", part)
            continue
        at = [kd for kp, kd in keys if abs(kp - e) < 1e-3]
        t = (at[0] - s) if at else (e - s)      # no keyframe at e: a part that ends at EOF
        ff("-ss", s, "-i", src, "-t", f"{t:.6f}", "-c", "copy", part)
    lst = d / f"{tag}_{design}.txt"
    lst.write_text("".join(f"file '{n.name}'\n" for n in names))
    out = d / f"{tag}_{design}_out{ext}"
    ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default="tests/out/prototypes")
    a = ap.parse_args()
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    fx = fixtures(d)

    std, eof = [(0, 2), (4, 6), (8, 10)], [(0, 2), (4, 6), (10, 12)]
    rows = [  # (fixture, output ext, segments, beep skew expected in ms or None)
        ("h264bf", ".mp4", std, None), ("h264bf", ".mov", std, None),
        ("hevc25c", ".mp4", std, None), ("hevc25c", ".mov", std, None),
        ("hevc25", ".mp4", std, None), ("hevc25", ".mov", std, None),
        ("h264bf", ".mp4", eof, None), ("h264bf", ".mov", eof, None), ("hevc25c", ".mp4", eof, None),
        ("late_audio", ".mp4", [(0, 2), (4, 6)], None), ("h264bf_late", ".mp4", std, None),
        ("h264bf_late", ".mov", std, None),
        ("beep", ".mp4", std, 0), ("beep", ".mov", std, 0), ("beep_late", ".mp4", std, round(DELAY * 1000)),
        ("nob", ".mp4", std, 0),
    ]
    failed = []
    print(f"{'row':34s} {'design':6s} {'frames':9s} exact  max step ms  V(start,dur)    A(start,dur)    beep skew ms")
    for n, (name, ext, segs, skew) in enumerate(rows):
        src, fps, closed = fx[name]
        keys = keyframes(src)
        source = hashes(src)
        want = [source[i] for s, e in segs for i in range(round(s * fps), min(round(e * fps), len(source)))]
        label = f"{name}{ext} {','.join(f'{s}-{e}' for s, e in segs)}" + ("" if closed else " [open GOP]")
        for design in ("P0", "P3"):
            out = cut_parts(design, src, segs, keys, ext, f"r{n}", d)
            got = hashes(out)
            pts = frame_pts(out)
            steps = [y - x for x, y in zip(pts, pts[1:])]
            worst = max(steps, key=lambda x: abs(x - 1 / fps))
            smooth = abs(worst - 1 / fps) < 0.5 / fps
            st = streams(out)
            beeps = ""
            if skew is not None:
                on = onsets(out)
                # beep j (at output j + 0.5 s) belongs to output frame (j + 0.5) * fps
                sk = [round((o - pts[int((j + 0.5) * fps)]) * 1000) for j, o in enumerate(on[:6])]
                beeps = f"{sk} ({len(on)} onsets)"
                if design == "P3" and (len(on) != 6 or any(abs(x - skew) > 5 for x in sk)):
                    failed.append(f"{name}{ext} {design}: beep skew {sk}, want {skew} +/- 5 on 6 onsets")
            exact = got == want
            print(f"{label:34s} {design:6s} {len(got):3d}/{len(want):<5d} {str(exact):6s} {worst * 1000:7.1f}{'' if smooth else '!':5s}"
                  f"{str(st.get('v')):15s} {str(st.get('a')):15s} {beeps}")
            if design == "P3" and closed and not (exact and smooth):
                failed.append(f"{name}{ext} {design}: exact={exact} max step {worst * 1000:.1f} ms ({len(got)}/{len(want)})")
            label = ""
    print()
    if failed:
        print("GATE FAILED (closed-GOP rows must be exact with P3):")
        for f in failed:
            print("  " + f)
        return 1
    print("GATE PASSED: every closed-GOP row is exact with P3, continuous within half a frame, and in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
