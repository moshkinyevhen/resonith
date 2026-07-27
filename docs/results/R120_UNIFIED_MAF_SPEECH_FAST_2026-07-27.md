# R-120 unified MAF speech fast diagnostic

Date: 2026-07-27
Status: **FAST DIAGNOSTIC — REJECTED FOR PROMOTION**

This report evaluates one pinned LibriSpeech item. It is not the mandatory
R-118 19-item architecture gate and supports no general codec claim.

## Result

| Stream | Complete bytes | SNR dB | STOI | ESTOI | Log-mel RMSE |
|---|---:|---:|---:|---:|---:|
| official Opus 1.6.1 | 17,942 | 9.297437 | 0.993172 | 0.988046 | 0.601168 |
| MFC1 unified cell | 19,277 | 15.847947 | 0.979699 | 0.954469 | 1.117839 |
| SFT1/EPV1, 5 pulses | 10,294 | 5.568254 | 0.878153 | 0.795882 | 1.313313 |
| SFT1/EPV1, 8 pulses | 12,548 | 7.211959 | 0.908976 | 0.846112 | 1.190511 |

The 10,294-byte point is 42.6% smaller than the Opus file, but its quality is
not comparable. It is rejected. The higher-rate adaptive point is also
rejected. Opus remains decisively better on speech intelligibility and
spectral-envelope error.

## What was proved

- MFC1 serializes one band-local competition with actual independent decode.
- Its ledger closes exactly: 3,066 map bits, 2,849 mode bits, 146,380 command
  bits, and zero unclassified bits.
- PVQ-default syntax and gain memory removed 2,206 bytes from the initial
  21,483-byte MFC1 implementation without a material speech-quality change.
- Cached integer vocal-tract Basis reduced the source-filter envelope from
  2,577 to 701 bytes in the first comparison and to 606 bytes in the current
  block-128 adaptive stream.
- Correct source-filter order and closed-loop adaptive excitation improved the
  sparse-excitation result, but current pitch state still changes in 1,134 of
  1,464 subframes at the eight-pulse point.

## What remains false

- Resonith has not beaten Opus on this speech item.
- The 40% saving target has not been achieved at matched perceived quality.
- The current scalar pitch law is not a long-lived MAF state.
- No default, released syntax, or semantic version changed.

## Reproduction

Run `experiments/unified_maf_fast_gate.py` with the pinned speech WAV, official
Opus stream/decode, C++23 native Core, `--source-filter`,
`--source-filter-block-size 128`, `--source-filter-parameter-lambda 0`,
`--excitation-backend epvq`, `--excitation-subframe-size 64`,
`--adaptive-quality-guard-q12 4608`, and either five or eight excitation
pulses.

The machine-readable hashes, wall times, byte ledger, and metrics are in
[`unified_maf_speech_fast_2026-07-27.json`](../../experiments/results/unified_maf_speech_fast_2026-07-27.json).
