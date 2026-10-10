# ASR benchmark: m4-max-extra

Apple M4 Max, 128 GB, macOS 27.0; ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers; whisper.cpp 1.9.5; parakeet-mlx v0.5.2; skill 7072293; power: Now drawing from 'AC Power'

## WER % (lower is better)

| set | parakeet-mlx-v3 | parakeet.cpp-v3 |
|---|---|---|
| librispeech | 4.56 | 21.13 |
| ami | 23.82 | 24.95 |
| earnings22 | 21.31 | 30.25 |
| gigaspeech | 34.07 | 31.28 |
| voxpopuli | 41.56 | 57.34 |
| common_voice | 46.28 | 33.76 |
| **all (word-weighted)** | **27.54** | **32.96** |

## Median time, s (RTFx = audio seconds / time; higher is faster)

| set | parakeet-mlx-v3 | parakeet.cpp-v3 |
|---|---|---|
| librispeech (10.0 min) | 5.54 (107.9x) | 4.14 (144.2x) |
| ami (8.3 min) | 6.51 (76.3x) | 4.72 (105.3x) |
| earnings22 (9.9 min) | 6.51 (91.1x) | 4.58 (129.7x) |
| gigaspeech (10.0 min) | 5.85 (102.1x) | 4.41 (135.4x) |
| voxpopuli (10.1 min) | 5.12 (118.9x) | 3.52 (172.7x) |
| common_voice (10.0 min) | 5.05 (118.6x) | 3.68 (162.8x) |
| **all** | **34.6 (101.0x)** | **25.1 (139.4x)** |
