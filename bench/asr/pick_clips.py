# /// script
# requires-python = ">=3.9"
# dependencies = ["huggingface_hub>=0.24", "pyarrow>=15", "fsspec"]
# ///
"""Pick the benchmark clips once and pin them in manifest.json.

Both machines then read the same rows from the same dataset revision, so their WER numbers
score identical audio. Run it only to change the selection; prep.py reads the committed
manifest.

Selection, per set: read only the `audio_length_s` column of every shard (cheap), then take
MAX_GROUPS row groups evenly spaced across the whole set (the set is sorted by duration, so
this spans short to long clips), and inside each one evenly spaced rows until the set holds
about TARGET_S seconds of speech.
"""
import json
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfApi, HfFileSystem

REPO = "hf-audio/esb-datasets-test-only-sorted"
REVISION = "de79e57adf9983993bcc72586d7313460825f5eb"
# set name -> shard filename filter (librispeech holds test.clean and test.other)
SETS = {
    "librispeech": "librispeech/test.clean-",
    "ami": "ami/test-",
    "earnings22": "earnings22/test-",
    "gigaspeech": "gigaspeech/test-",
    "voxpopuli": "voxpopuli/test-",
    "common_voice": "common_voice/test-",
}
TARGET_S = 600.0
MAX_GROUPS = 6


def main() -> None:
    fs = HfFileSystem()
    files = sorted(s.rfilename for s in HfApi().dataset_info(REPO, revision=REVISION).siblings
                   if s.rfilename.endswith(".parquet"))
    manifest = {"repo": REPO, "revision": REVISION, "target_s": TARGET_S, "sets": {}}
    for name, prefix in SETS.items():
        groups = []  # (shard, row group, first global row, lengths)
        for fn in (f for f in files if f.startswith(prefix)):
            pf = pq.ParquetFile(fs.open(f"datasets/{REPO}@{REVISION}/{fn}", "rb"))
            for g in range(pf.metadata.num_row_groups):
                lengths = pf.read_row_group(g, columns=["audio_length_s"]).column(0).to_pylist()
                groups.append((fn, g, lengths))
        step = max(1, len(groups) // MAX_GROUPS)
        chosen = groups[step // 2::step][:MAX_GROUPS]
        per_group = TARGET_S / len(chosen)
        clips = []
        for fn, g, lengths in chosen:
            mean = sum(lengths) / len(lengths)
            k = max(1, min(len(lengths), round(per_group / mean)))
            for j in range(k):
                row = int(len(lengths) * (j + 0.5) / k)
                clips.append({"shard": fn, "row_group": g, "row": row, "seconds": round(lengths[row], 3)})
        total = sum(c["seconds"] for c in clips)
        manifest["sets"][name] = {"clips": clips, "seconds": round(total, 1)}
        print(f"{name}: {len(clips)} clips, {total / 60:.1f} min from {len(chosen)} row groups")
    Path(__file__).with_name("manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")


if __name__ == "__main__":
    main()
