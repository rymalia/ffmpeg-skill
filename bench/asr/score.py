# /// script
# requires-python = ">=3.9"
# dependencies = ["jiwer>=3.0", "regex"]
# ///
"""Score results/<label>/ against the references and write report.md + summary.json there.

WER uses the Open ASR Leaderboard's EnglishTextNormalizer, fetched once at a pinned commit,
on references and hypotheses alike. Time is the median of the timed runs; RTFx is audio
seconds divided by that median (higher is faster).

  uv run bench/asr/score.py m3-air [m4-max ...]
"""
import json
import statistics
import sys
import urllib.request
from pathlib import Path

import jiwer

HERE = Path(__file__).resolve().parent
NORMALIZER_COMMIT = "97b92fbe1e6be5f4c503a7dd63a0f4de49e76561"
NORMALIZER_FILES = ("normalizer.py", "english_abbreviations.py")


def normalizer():
    pkg = HERE / ".cache" / "oal_normalizer"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").touch()
    for name in NORMALIZER_FILES:
        dst = pkg / name
        if not dst.exists():
            url = f"https://raw.githubusercontent.com/huggingface/open_asr_leaderboard/{NORMALIZER_COMMIT}/normalizer/{name}"
            dst.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    sys.path.insert(0, str(pkg.parent))
    from oal_normalizer.normalizer import EnglishTextNormalizer
    from oal_normalizer.english_abbreviations import english_spelling_normalizer
    return EnglishTextNormalizer(english_spelling_normalizer)


def srt_text(path: Path) -> str:
    lines = []
    for block in path.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        rows = block.strip().splitlines()
        lines += [r for r in rows[2:] if r.strip()] if len(rows) > 2 else []
    return " ".join(lines)


def score(label: str, norm) -> None:
    out = HERE / "results" / label
    rows = [json.loads(l) for l in (out / "timings.jsonl").read_text().splitlines() if l.strip()]
    info = json.loads((out / "machine.json").read_text())
    sets = list(dict.fromkeys(r["set"] for r in rows))
    configs = list(dict.fromkeys(r["config"] for r in rows))
    summary = {"label": label, "machine": info, "cells": []}
    totals = {c: {"ref": [], "hyp": [], "audio": 0.0, "time": 0.0} for c in configs}
    for s in sets:
        ref = norm((HERE / "data" / f"{s}.ref.txt").read_text())
        audio = sum(c["seconds"] for c in json.loads((HERE / "data" / f"{s}.json").read_text()))
        for c in configs:
            timed = [r for r in rows if r["set"] == s and r["config"] == c and r["rep"] >= 1]
            errors = [r["error"] for r in timed if r["error"]]
            srt = out / s / f"{c}.srt"
            cell = {"set": s, "config": c, "audio_s": round(audio, 1), "runs": len(timed), "errors": errors}
            if timed and not errors and srt.exists():
                hyp = norm(srt_text(srt))
                m = jiwer.process_words(ref, hyp)
                med = statistics.median(r["seconds"] for r in timed)
                cell.update(wer=round(100 * m.wer, 2), sub=m.substitutions, dele=m.deletions, ins=m.insertions,
                            ref_words=len(ref.split()), median_s=round(med, 2), rtfx=round(audio / med, 1),
                            spread_s=[round(r["seconds"], 2) for r in timed], engine_ran=timed[0]["engine_ran"])
                t = totals[c]
                t["ref"].append(ref), t["hyp"].append(hyp)
                t["audio"] += audio
                t["time"] += med
            summary["cells"].append(cell)
    summary["overall"] = {}
    for c, t in totals.items():
        if t["ref"]:
            m = jiwer.process_words(t["ref"], t["hyp"])
            summary["overall"][c] = {"wer": round(100 * m.wer, 2), "audio_s": round(t["audio"], 1),
                                     "time_s": round(t["time"], 1), "rtfx": round(t["audio"] / t["time"], 1)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")

    md = [f"# ASR benchmark: {label}", "",
          f"{info.get('chip')}, {info.get('memory_gb')} GB, macOS {info.get('macos')}; {info.get('ffmpeg')}; "
          f"{info.get('whisper_cpp')}; {info.get('parakeet_mlx')}; skill {info.get('skill_commit')}; power: {info.get('power')}", "",
          "## WER % (lower is better)", "", "| set | " + " | ".join(configs) + " |", "|---|" + "---|" * len(configs)]
    cell = {(x["set"], x["config"]): x for x in summary["cells"]}
    for s in sets:
        md.append(f"| {s} | " + " | ".join(str(cell[(s, c)].get("wer", "n/a")) for c in configs) + " |")
    md.append("| **all (word-weighted)** | " + " | ".join(f"**{summary['overall'].get(c, {}).get('wer', 'n/a')}**" for c in configs) + " |")
    md += ["", "## Median time, s (RTFx = audio seconds / time; higher is faster)", "",
           "| set | " + " | ".join(configs) + " |", "|---|" + "---|" * len(configs)]
    for s in sets:
        md.append(f"| {s} ({cell[(s, configs[0])]['audio_s'] / 60:.1f} min) | " + " | ".join(
            f"{cell[(s, c)]['median_s']} ({cell[(s, c)]['rtfx']}x)" if "median_s" in cell[(s, c)] else "n/a" for c in configs) + " |")
    md.append("| **all** | " + " | ".join(
        f"**{summary['overall'][c]['time_s']} ({summary['overall'][c]['rtfx']}x)**" if c in summary["overall"] else "n/a"
        for c in configs) + " |")
    (out / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    norm = normalizer()
    for label in sys.argv[1:]:
        score(label, norm)
