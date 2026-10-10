# ASR benchmark: m3-air

Apple M3, 16 GB, macOS 26.7.1; ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers; whisper.cpp 1.9.5; parakeet-mlx v0.5.2; skill 2c4e37b; power: Now drawing from 'AC Power'

## WER % (lower is better)

| set | whisper.cpp-base | whisper.cpp-small | whisper.cpp-large-v3-turbo | parakeet-mlx-v2 | parakeet.cpp-v2 |
|---|---|---|---|---|---|
| librispeech | 6.59 | 3.45 | 2.53 | 2.96 | 2.03 |
| ami | 38.05 | 47.92 | 25.72 | 20.86 | 24.45 |
| earnings22 | 22.84 | 16.36 | 188.76 | 19.84 | 23.96 |
| gigaspeech | 15.96 | 14.43 | 13.16 | 16.43 | 14.38 |
| voxpopuli | 10.39 | 7.47 | 8.38 | 9.29 | 6.43 |
| common_voice | 32.29 | 16.44 | 231.7 | 21.43 | 14.87 |
| **all (word-weighted)** | **19.87** | **17.07** | **69.12** | **14.73** | **14.25** |

## Median time, s (RTFx = audio seconds / time; higher is faster)

| set | whisper.cpp-base | whisper.cpp-small | whisper.cpp-large-v3-turbo | parakeet-mlx-v2 | parakeet.cpp-v2 |
|---|---|---|---|---|---|
| librispeech (10.0 min) | 12.83 (46.6x) | 29.96 (20.0x) | 66.63 (9.0x) | 18.3 (32.7x) | 13.74 (43.5x) |
| ami (8.3 min) | 9.47 (52.5x) | 19.6 (25.4x) | 80.39 (6.2x) | 21.79 (22.8x) | 15.79 (31.5x) |
| earnings22 (9.9 min) | 16.31 (36.4x) | 32.99 (18.0x) | 105.85 (5.6x) | 20.22 (29.3x) | 15.07 (39.4x) |
| gigaspeech (10.0 min) | 14.28 (41.8x) | 29.77 (20.1x) | 72.86 (8.2x) | 20.89 (28.6x) | 15.17 (39.4x) |
| voxpopuli (10.1 min) | 11.9 (51.1x) | 27.48 (22.1x) | 64.39 (9.4x) | 20.18 (30.1x) | 14.34 (42.4x) |
| common_voice (10.0 min) | 8.97 (66.8x) | 23.72 (25.3x) | 74.32 (8.1x) | 17.35 (34.6x) | 12.69 (47.3x) |
| **all** | **73.8 (47.4x)** | **163.5 (21.4x)** | **464.4 (7.5x)** | **118.7 (29.4x)** | **86.8 (40.2x)** |
