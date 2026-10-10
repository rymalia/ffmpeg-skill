"""Time every engine on every set through the skill's own transcription path.

Standard library only. It calls scripts/_common/asr.py's transcribe_result(), the function
caption.py --transcribe calls, with --engine and --model set explicitly and --language en,
so each number is what a user of this checkout gets (audio extraction, model load and the
engine's own long-form handling included).

  caffeinate -ims python3 bench/asr/run.py --label m3-air [--runs 3]
  caffeinate -ims python3 bench/asr/run.py --label m4-max-extra --configs parakeet-mlx-v3,parakeet.cpp-v3

--configs picks configs from CONFIGS and EXTRA_CONFIGS; without it the run is exactly CONFIGS, in
order, so machines stay comparable. Extra configs belong under their own label.

On AC power only: it stops if the machine goes onto battery, because a laptop on battery
throttles and can sleep between runs.

Order: one untimed warm-up pass over every (set, config), then --runs timed passes. Every
pass walks the sets in turn and rotates the config order, so no engine always runs on a
hot (throttled) or a cold chip. The SRT of the first timed pass is kept for scoring.
Results: bench/asr/results/<label>/{machine.json, timings.jsonl, <set>/<config>.srt}.
"""
import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))

from _common.asr import transcribe_result  # noqa: E402

# name -> (engine, model); a whisper.cpp model is found as ~/.cache/whisper.cpp/ggml-<model>.bin
CONFIGS = {
    "whisper.cpp-base": ("whisper.cpp", "base"),
    "whisper.cpp-small": ("whisper.cpp", "small"),
    "whisper.cpp-large-v3-turbo": ("whisper.cpp", "large-v3-turbo"),
    "parakeet-mlx-v2": ("parakeet-mlx", "mlx-community/parakeet-tdt-0.6b-v2"),
    "parakeet.cpp-v2": ("parakeet.cpp", "base"),  # base is not a .gguf: the skill finds tdt-0.6b-v2-*.gguf
}
# Opt-in only (--configs): not part of the comparable run. A .gguf model is a path the skill loads as is.
EXTRA_CONFIGS = {
    "parakeet-mlx-v3": ("parakeet-mlx", "mlx-community/parakeet-tdt-0.6b-v3"),
    "parakeet.cpp-v3": ("parakeet.cpp", os.path.expanduser("~/.cache/parakeet.cpp/tdt-0.6b-v3-f16.gguf")),
}
ALL_CONFIGS = {**CONFIGS, **EXTRA_CONFIGS}
SETS = ("librispeech", "ami", "earnings22", "gigaspeech", "voxpopuli", "common_voice")
SCRUB = ("FFMPEG_SKILL_ASR_ENGINE", "PARAKEET_MODEL", "PARAKEET_CPP_MODEL", "FFMPEG_SKILL_HW")


def available(name: str) -> "tuple[bool, str]":
    engine, model = ALL_CONFIGS[name]
    if engine == "whisper.cpp":
        cli = shutil.which("whisper-cli") or shutil.which("whisper-cpp")
        path = os.path.expanduser(f"~/.cache/whisper.cpp/ggml-{model}.bin")
        return (bool(cli) and os.path.exists(path), f"whisper-cli={cli}, model={path}")
    if engine == "parakeet-mlx":
        return (bool(shutil.which("parakeet-mlx")), f"parakeet-mlx={shutil.which('parakeet-mlx')}")
    if model.endswith(".gguf"):
        return (bool(shutil.which("parakeet-cli")) and os.path.isfile(model), f"parakeet-cli={shutil.which('parakeet-cli')}, gguf={model}")
    gguf = sorted(Path(os.path.expanduser("~/.cache/parakeet.cpp")).glob("tdt-0.6b-v2-*.gguf"))
    return (bool(shutil.which("parakeet-cli")) and bool(gguf), f"parakeet-cli={shutil.which('parakeet-cli')}, gguf={gguf[:1]}")


def sh(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def on_battery() -> bool:
    """A laptop on battery throttles and may sleep between runs, so its timings mean nothing."""
    return "Battery Power" in sh("pmset", "-g", "batt")


def machine() -> dict:
    return {
        "chip": sh("sysctl", "-n", "machdep.cpu.brand_string"),
        "memory_gb": round(int(sh("sysctl", "-n", "hw.memsize") or 0) / 2**30),
        "macos": platform.mac_ver()[0],
        "power": sh("pmset", "-g", "batt").splitlines()[0] if sh("pmset", "-g", "batt") else "",
        "python": platform.python_version(),
        "ffmpeg": sh("ffmpeg", "-version").splitlines()[0] if sh("ffmpeg", "-version") else "",
        "whisper_cpp": sh("brew", "list", "--versions", "whisper-cpp"),
        "parakeet_mlx": next((l for l in sh("uv", "tool", "list").splitlines() if l.startswith("parakeet-mlx")), ""),
        "skill_commit": sh("git", "-C", str(HERE), "rev-parse", "--short", "HEAD"),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="machine label, e.g. m3-air or m4-max")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--configs", help="comma-separated config names (default: every entry of CONFIGS)")
    args = ap.parse_args()
    wanted = args.configs.split(",") if args.configs else list(CONFIGS)
    unknown = [n for n in wanted if n not in ALL_CONFIGS]
    if unknown:
        ap.error(f"unknown config(s) {', '.join(unknown)}; choose from {', '.join(ALL_CONFIGS)}")
    for var in SCRUB:
        os.environ.pop(var, None)
    out = HERE / "results" / args.label
    out.mkdir(parents=True, exist_ok=True)
    info = machine()
    configs = []
    for name in wanted:
        ok, detail = available(name)
        info.setdefault("configs", {})[name] = {"available": ok, "detail": detail}
        if ok:
            configs.append(name)
        else:
            print(f"skipping {name}: {detail}", file=sys.stderr)
    (out / "machine.json").write_text(json.dumps(info, indent=1) + "\n")
    data = HERE / "data"
    timings = (out / "timings.jsonl").open("a")
    for rep in range(args.runs + 1):
        # the warm-up may fetch a model; timed passes must not touch the network
        if rep == 1:
            os.environ["HF_HUB_OFFLINE"] = "1"
        for s_i, set_name in enumerate(SETS):
            wav = data / f"{set_name}.wav"
            k = (rep + s_i) % len(configs)
            for name in configs[k:] + configs[:k]:
                if on_battery():
                    sys.exit(f"on battery power: stopping before {set_name} {name} (pass {rep}). Plug in, "
                             f"delete {out} and start again under caffeinate.")
                engine, model = ALL_CONFIGS[name]
                srt = out / set_name / f"{name}.srt"
                srt.parent.mkdir(exist_ok=True)
                target = srt if rep == 1 else out / set_name / f".{name}.scratch.srt"
                t0 = time.perf_counter()
                try:
                    result = transcribe_result(str(wav), str(target), "en", model, engine=engine)
                    ran, error = result.engine, ""
                except SystemExit as e:  # the skill's die() on an engine failure
                    ran, error = "", f"exit {e.code}"
                dt = time.perf_counter() - t0
                if target != srt and target.exists():
                    target.unlink()
                row = {"rep": rep, "set": set_name, "config": name, "seconds": round(dt, 3), "engine_ran": ran, "error": error}
                timings.write(json.dumps(row) + "\n")
                timings.flush()
                print(f"[{'warm' if rep == 0 else rep}] {set_name:13s} {name:28s} {dt:7.1f}s {error}", flush=True)
    timings.close()


if __name__ == "__main__":
    main()
