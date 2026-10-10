# ASR benchmark: m4-max

Apple M4 Max, 128 GB, macOS 27.0; ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers; whisper.cpp 1.9.5; parakeet-mlx v0.5.2; skill 35bba62; power: Now drawing from 'AC Power'

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
| librispeech (10.0 min) | 6.69 (89.4x) | 12.66 (47.2x) | 15.79 (37.9x) | 5.22 (114.5x) | 4.14 (144.4x) |
| ami (8.3 min) | 4.83 (102.9x) | 7.02 (70.8x) | 17.73 (28.0x) | 5.74 (86.6x) | 4.18 (118.8x) |
| earnings22 (9.9 min) | 8.35 (71.1x) | 13.04 (45.5x) | 24.41 (24.3x) | 5.54 (107.0x) | 4.2 (141.2x) |
| gigaspeech (10.0 min) | 7.52 (79.5x) | 11.96 (49.9x) | 16.98 (35.2x) | 5.66 (105.5x) | 4.4 (135.8x) |
| voxpopuli (10.1 min) | 5.62 (108.3x) | 10.48 (58.0x) | 14.39 (42.3x) | 5.2 (117.1x) | 4.12 (147.6x) |
| common_voice (10.0 min) | 4.72 (127.0x) | 8.68 (69.1x) | 19.54 (30.7x) | 4.83 (124.0x) | 3.75 (159.9x) |
| **all** | **37.7 (92.6x)** | **63.8 (54.7x)** | **108.8 (32.1x)** | **32.2 (108.5x)** | **24.8 (140.9x)** |
