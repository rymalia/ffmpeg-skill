# Parakeet vs whisper.cpp on more than LibriSpeech

This benchmark compares Parakeet with whisper.cpp for `--transcribe`. It measures speed and
accuracy for each engine, run through this checkout's own `scripts/_common/asr.py`.

## Material

About 58 minutes of English speech in six sets. The clips come from
`hf-audio/esb-datasets-test-only-sorted`, pinned at revision `de79e57`:

| set | what it is |
|---|---|
| librispeech | read audiobooks, test.clean (the earlier figures were on LibriSpeech) |
| ami | meeting recordings, overlapping conversational speech (8.3 min, very short clips) |
| earnings22 | earnings calls: accented, domain-heavy speech |
| gigaspeech | podcasts and YouTube |
| voxpopuli | European Parliament speeches |
| common_voice | crowd-sourced read speech, many accents and microphones |

`manifest.json` pins the exact rows, so every machine scores identical audio. The rows span
each set's range of clip lengths.

Each set's clips are joined into one 16 kHz mono WAV, with 0.75 s of silence between clips.
That is how a caption job reaches the engine: one long file, one model load, and the engine's
own long-form handling.

## Engines

Every engine is called through `transcribe_result()`, the function `caption.py --transcribe`
calls. Each call passes `--engine` and `--model` explicitly, with `--language en`.

| config | engine and model |
|---|---|
| whisper.cpp-base | whisper-cli, `ggml-base.bin` (caption.py's default `--model`) |
| whisper.cpp-small | whisper-cli, `ggml-small.bin` |
| whisper.cpp-large-v3-turbo | whisper-cli, `ggml-large-v3-turbo.bin` |
| parakeet-mlx-v2 | parakeet-mlx, `mlx-community/parakeet-tdt-0.6b-v2` (the skill's default) |
| parakeet.cpp-v2 | parakeet-cli, `tdt-0.6b-v2-f16.gguf` |

A config whose engine or model is missing is skipped, and `machine.json` records why.

## Run it

```sh
uv run bench/asr/prep.py                    # download the pinned rows, build data/*.wav (~140 MB)
python3 bench/asr/run.py --label <machine>  # 1 warm-up + 3 timed passes; run on AC power, machine otherwise idle
uv run bench/asr/score.py <machine> [<other machine> ...]   # report.md + summary.json per label
```

Extra configs (`EXTRA_CONFIGS` in `run.py`, such as the Parakeet v3 models) run only when named with
`--configs`, under a label of their own, for example
`python3 bench/asr/run.py --label <machine>-extra --configs parakeet-mlx-v3,parakeet.cpp-v3`. A plain run is
always the five configs in `CONFIGS`, so the machines stay comparable.

`pick_clips.py` only needs re-running to change the selection. It rewrites `manifest.json`.

## How it's measured

- **Time:** the median of three timed passes, wall clock around `transcribe_result()`. That
  covers audio extraction, model load and transcription.
  - The passes rotate the engine order, so no engine always gets a cold or a throttled chip.
  - Timed passes run with `HF_HUB_OFFLINE=1`, so no download lands in a timing.
  - **RTFx** = speech seconds / median seconds. Higher is faster. Speech seconds are the clips'
    own lengths, without the silence gaps; AMI's 381 short clips add about 4.8 min of gaps to its
    file, which every engine still has to get through.
- **WER:** jiwer, with the Open ASR Leaderboard's `EnglishTextNormalizer` applied to the
  reference and the hypothesis. It's fetched at commit `97b92fb` and handles numbers, spelling
  variants and punctuation. The transcript scored is the first timed pass's SRT.
- **Caveats:**
  - Each set's references are joined, so WER is per set, not per clip.
  - A set's 0.75 s gaps are silence, never speech.
  - A fanless MacBook Air throttles under sustained load, which is why each machine's results
    say which chip they came from.

## Results

The `results/<label>/` directories hold `machine.json`, the raw `timings.jsonl`, each engine's
SRTs, and `report.md`.
