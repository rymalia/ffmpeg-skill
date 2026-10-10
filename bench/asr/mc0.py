"""A/B test: does whisper.cpp's -mc 0 (no previous-text context) stop the repetition loops?

In the main run, large-v3-turbo repeated one sentence ~300 times on two sets and lost the rest
of each file. This runs the skill's exact whisper.cpp command (asr.py: `-m MODEL -f WAV -osrt
-of OUT -l en`) twice per (set, model): as is, and with `-mc 0` added. Both arms go through the
same raw call, so the flag is the only difference. WER only: one pass, and the timings are kept
but are not a speed benchmark.

  caffeinate -ims python3 bench/asr/mc0.py --label m3-air-mc0
  uv run bench/asr/score.py m3-air-mc0

Results land in results/<label>/ in run.py's format, with configs named
whisper.cpp-<model> and whisper.cpp-<model>-mc0.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run import SETS, machine, on_battery  # noqa: E402

MODELS = ("base", "small", "large-v3-turbo")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    args = ap.parse_args()
    cli = shutil.which("whisper-cli") or sys.exit("whisper-cli not found")
    out = HERE / "results" / args.label
    out.mkdir(parents=True, exist_ok=True)
    info = machine()
    info["note"] = "raw whisper-cli A/B of -mc 0; one pass; WER only"
    (out / "machine.json").write_text(json.dumps(info, indent=1) + "\n")
    timings = (out / "timings.jsonl").open("a")
    for set_name in SETS:
        wav = HERE / "data" / f"{set_name}.wav"
        for model in MODELS:
            path = os.path.expanduser(f"~/.cache/whisper.cpp/ggml-{model}.bin")
            for extra in ([], ["-mc", "0"]):
                if on_battery():
                    sys.exit("on battery power: stopping. Plug in and start again.")
                name = f"whisper.cpp-{model}" + ("-mc0" if extra else "")
                (out / set_name).mkdir(exist_ok=True)
                with tempfile.TemporaryDirectory(prefix="asrbench_mc0_") as tmp:
                    base = os.path.join(tmp, "out")
                    cmd = [cli, "-m", path, "-f", str(wav), "-osrt", "-of", base, "-l", "en"] + extra
                    t0 = time.perf_counter()
                    proc = subprocess.run(cmd, capture_output=True, text=True)
                    dt = time.perf_counter() - t0
                    error = "" if proc.returncode == 0 and os.path.exists(base + ".srt") else f"exit {proc.returncode}"
                    if not error:
                        shutil.copy(base + ".srt", out / set_name / f"{name}.srt")
                row = {"rep": 1, "set": set_name, "config": name, "seconds": round(dt, 3),
                       "engine_ran": "whisper.cpp", "error": error}
                timings.write(json.dumps(row) + "\n")
                timings.flush()
                print(f"{set_name:13s} {name:32s} {dt:7.1f}s {error}", flush=True)
    timings.close()


if __name__ == "__main__":
    main()
