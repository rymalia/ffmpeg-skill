# ASR benchmark: m3-air-mc0

Apple M3, 16 GB, macOS 26.7.1; ffmpeg version 9.0.2 Copyright (c) 2000-2026 the FFmpeg developers; whisper.cpp 1.9.5; parakeet-mlx v0.5.2; skill 04f4d88; power: Now drawing from 'AC Power'

## WER % (lower is better)

| set | whisper.cpp-base | whisper.cpp-base-mc0 | whisper.cpp-small | whisper.cpp-small-mc0 | whisper.cpp-large-v3-turbo | whisper.cpp-large-v3-turbo-mc0 |
|---|---|---|---|---|---|---|
| librispeech | 6.59 | 5.79 | 3.45 | 3.7 | 2.53 | 2.03 |
| ami | 38.05 | 38.34 | 47.92 | 32.91 | 25.72 | 27.55 |
| earnings22 | 22.84 | 18.72 | 16.36 | 17.42 | 188.76 | 13.42 |
| gigaspeech | 15.96 | 17.48 | 14.43 | 15.06 | 13.16 | 14.11 |
| voxpopuli | 10.39 | 8.64 | 7.47 | 7.34 | 8.38 | 5.91 |
| common_voice | 32.29 | 26.03 | 16.44 | 19.28 | 231.7 | 13.8 |
| **all (word-weighted)** | **19.87** | **18.33** | **17.07** | **15.42** | **69.12** | **12.52** |

## Median time, s (RTFx = audio seconds / time; higher is faster)

| set | whisper.cpp-base | whisper.cpp-base-mc0 | whisper.cpp-small | whisper.cpp-small-mc0 | whisper.cpp-large-v3-turbo | whisper.cpp-large-v3-turbo-mc0 |
|---|---|---|---|---|---|---|
| librispeech (10.0 min) | 12.91 (46.3x) | 11.78 (50.8x) | 28.68 (20.8x) | 26.28 (22.8x) | 55.56 (10.8x) | 48.1 (12.4x) |
| ami (8.3 min) | 8.92 (55.7x) | 19.58 (25.4x) | 16.76 (29.7x) | 31.77 (15.6x) | 79.23 (6.3x) | 62.84 (7.9x) |
| earnings22 (9.9 min) | 19.17 (31.0x) | 17.62 (33.7x) | 39.55 (15.0x) | 47.3 (12.5x) | 126.16 (4.7x) | 70.41 (8.4x) |
| gigaspeech (10.0 min) | 18.88 (31.6x) | 15.77 (37.9x) | 33.69 (17.7x) | 33.69 (17.7x) | 70.39 (8.5x) | 54.32 (11.0x) |
| voxpopuli (10.1 min) | 11.75 (51.8x) | 10.91 (55.8x) | 26.74 (22.8x) | 25.31 (24.0x) | 62.95 (9.7x) | 53.23 (11.4x) |
| common_voice (10.0 min) | 10.28 (58.3x) | 11.07 (54.2x) | 29.77 (20.1x) | 25.39 (23.6x) | 96.28 (6.2x) | 61.91 (9.7x) |
| **all** | **81.9 (42.6x)** | **86.7 (40.3x)** | **175.2 (19.9x)** | **189.7 (18.4x)** | **490.6 (7.1x)** | **350.8 (10.0x)** |
