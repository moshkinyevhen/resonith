# R-112 Native Packing Optimization

Date: 2026-07-27  
Status: **passed**

## Outcome

The R-107 encoder now produces the same prospective LPS5 stream substantially
faster. Complete Mozart encoded in 155.866 seconds instead of 385.976 seconds:
a 2.476x end-to-end speedup and 2.571x realtime throughput on the same host.

This is an implementation-speed result. It does not change syntax, decoded
PCM, bitrate, or quality.

## What changed

Profiling the eight-second Emotional piano reference attributed 6.225 of
10.982 profiled seconds to Python adaptive arithmetic packing. The new
allocation-free C++20 routine encodes the exact LAF1 adaptive model behind the
stable C ABI. It accepts caller-owned symbol and output arrays, supports
alphabets from 2 through 512, owns no heap or mutable global state, and emits
the same canonical little-endian bit field as the independent Python oracle.

The normal LPS5 encode path also stopped building and decoding a duplicate
monolithic LPF1 stream. The duplicate comparison remains available as an
explicit conformance mode; packet decode still runs through the native Golden
Core for every measured encode.

## Complete-reference timing

| Reference | Audio | Published encode | Optimized encode | Speedup | Throughput | Stream identity |
|---|---:|---:|---:|---:|---:|---|
| Speech | 5.855 s | 1.010 s | 0.439 s | 2.301x | 13.347x realtime | exact |
| Emotional piano | 8.000 s | 6.981 s | 2.859 s | 2.442x | 2.798x realtime | exact |
| Complete Mozart | 400.773 s | 385.976 s | 155.866 s | 2.476x | 2.571x realtime | exact |

Exact compressed-stream identities:

- Speech: 17,924 bytes,
  `a25435922af489adf4e5aedccc308c23a82f7261b47162af5e97ef021515c91f`.
- Emotional piano: 117,225 bytes,
  `7bd27f3fbba8a20a0565c52ad24f5a0e4084c6e218dea93d5fda448e083f49ff`.
- Complete Mozart: 6,526,665 bytes,
  `9018223f167b21bb47be165c1b39d947b4e580f96dd8eda4315438f8d5c9ff6f`.

## Heterogeneous regression

All 16 R-111 class streams were re-encoded with their published R-107
budgets. Every complete `.resonith` file matched its prior bytes and SHA-256.
The 192 seconds of source audio completed in 60.174 seconds. Per-clip
throughput ranged from 2.345x to 6.364x realtime.

The gate covers deterministic sustain, pink noise, vibrato and resonance,
electronic material, violin, claves, side drum, cymbal, grand piano, soprano,
male and female speech, dense orchestra, dense popular music, and two stereo
film mixes.

## Verification

- LLVM-MinGW 20260616, Clang 22.1.8, C++20, release `-O3`.
- Strict `-Wall -Wextra -Wconversion -Wpedantic -Wshadow -Werror` build:
  passed.
- Native Core SHA-256:
  `fba0805a8038e006440d4285ca870171423f5ddc2dfd4e1fd1682728962f20bb`.
- Independent adaptive-encoder byte identity tested for alphabet sizes 2, 16,
  63, 256, and 512.
- Complete Python/native suite: 180 tests passed; four unavailable
  external-device or external-tool integrations were skipped.

Because every compressed byte is identical, all previously published SNR,
SI-SDR, segmental SNR, STOI, ESTOI, multi-resolution STFT, log-spectral, and
log-mel values remain exactly applicable.

Machine-readable summary:
[`native_packing_optimization_2026-07-27.json`](../../experiments/results/native_packing_optimization_2026-07-27.json).
