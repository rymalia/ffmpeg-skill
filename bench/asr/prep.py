# /// script
# requires-python = ">=3.9"
# dependencies = ["huggingface_hub>=0.24", "pyarrow>=15", "fsspec"]
# ///
"""Build one long 16 kHz mono WAV per set from the clips pinned in manifest.json.

Each set's clips are joined in manifest order with GAP_S of silence between them, the way a
caption job hands the engine one long file (one model load, real long-form chunking), and the
references are joined in the same order. Output goes to data/ (git-ignored):
data/<set>.wav, data/<set>.ref.txt, data/<set>.json (clip ids and offsets).
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem

HERE = Path(__file__).parent
GAP_S = 0.75


def decode(blob: bytes, dst: Path) -> None:
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", "pipe:0", "-ac", "1", "-ar", "16000",
                    "-c:a", "pcm_s16le", str(dst)], input=blob, check=True)


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    repo, rev = manifest["repo"], manifest["revision"]
    fs = HfFileSystem()
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    for name, entry in manifest["sets"].items():
        if (data / f"{name}.wav").exists():
            print(f"{name}: already built")
            continue
        tmp = Path(tempfile.mkdtemp(prefix=f"asrbench_{name}_"))
        try:
            gap = tmp / "gap.wav"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                            f"anullsrc=r=16000:cl=mono", "-t", str(GAP_S), "-c:a", "pcm_s16le", str(gap)], check=True)
            cache = {}
            parts, refs, index, offset = [], [], [], 0.0
            for n, clip in enumerate(entry["clips"]):
                key = (clip["shard"], clip["row_group"])
                if key not in cache:
                    pf = pq.ParquetFile(fs.open(f"datasets/{repo}@{rev}/{clip['shard']}", "rb"))
                    cache.clear()
                    cache[key] = pf.read_row_group(clip["row_group"], columns=["audio", "text", "id"]).to_pylist()
                row = cache[key][clip["row"]]
                wav = tmp / f"{n:04d}.wav"
                decode(row["audio"]["bytes"], wav)
                parts += [wav, gap]
                refs.append(row["text"].strip())
                index.append({"id": row["id"], "offset_s": round(offset, 3), "seconds": clip["seconds"]})
                offset += clip["seconds"] + GAP_S
            listing = tmp / "list.txt"
            listing.write_text("".join(f"file '{p}'\n" for p in parts))
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                            "-c:a", "pcm_s16le", str(data / f"{name}.wav")], check=True)
            (data / f"{name}.ref.txt").write_text("\n".join(refs) + "\n")
            (data / f"{name}.json").write_text(json.dumps(index, indent=1) + "\n")
            print(f"{name}: {len(refs)} clips, {offset / 60:.1f} min")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
