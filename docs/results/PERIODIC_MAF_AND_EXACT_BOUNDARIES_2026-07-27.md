# R-131/R-134 Periodic MAF and Exact-Boundary Fast Diagnostic

Date: 2026-07-27  
Status: **FAST DIAGNOSTIC; COMPLETE R-118 AND OPUS GATES PENDING**  
Source revision:
`b86fdadc501c57c7fe635e6ad9bff1da1e5bad17`

## Scope

This diagnostic tests two narrow questions:

1. Can an approximate semantic timestamp be converted into bounded exact
   source-sample candidates without trusting the provider time?
2. Can one immutable periodic Basis plus long-lived phase records materially
   replace lapped Truth on a deliberately favorable sustained-tone item?

It is not a release, an Opus comparison, a general-audio result, or evidence
that the current quality objective is sufficient.

## Exact-boundary result

The local boundary path now performs:

- a bounded 250 ms coarse search around the provider timestamp;
- one-millisecond coarse time-frequency analysis;
- opposing six-millisecond original-PCM windows at a nominal
  quarter-millisecond hop;
- non-maximum selection of at most four independent anchors;
- individual-source-sample expansion around each anchor;
- at most 256 exact candidates per event plus mandatory `NO_BOUNDARY`.

At 48 kHz the candidate lattice has one-sample, 20.833 microsecond spacing.
This is search precision, not a claim that every acoustic transition is
physically instantaneous.

Two deterministic vectors pass:

| Vector | Provider error | Result |
|---|---:|---|
| Exact step onset at sample 8,007, 16 kHz | 40.438 ms | aligned sample is exactly 8,007 |
| 220 Hz to 880 Hz change at sample 24,013, 48 kHz | 13.271 ms | true boundary is present within one sample in the RDO set |

AI confidence and timestamp resolution do not admit either boundary. A later
complete-stream decoder-in-loop RDO stage remains responsible for choosing
one exact candidate or `NO_BOUNDARY`.

## Periodic-Basis result

The first periodic router incorrectly limited autocorrelation to 500 Hz. On
the EBU SQAM 1 kHz sustained-sine item it therefore preferred an almost exact
ten-cycle recurrence near 441 samples instead of the 44.1-sample fundamental.
The corrected router searches periodic Basis recurrences through 5 kHz and
selects the shortest strong local autocorrelation peak.

Input:

- `ebu-sustained-sine.wav`;
- 529,200 mono PCM16 frames at 44.1 kHz;
- 1,058,444 source bytes;
- source SHA-256
  `78faec4d9b92b72cba0ae1d13ec16bfc520c6c31e1b6df5f4e97e89515557e57`.

Configuration:

- 240 ms router segments;
- 64-sample lapped half-window;
- eight bands;
- maximum 24 Truth coefficients per transform frame;
- exact outer `RSC1` bytes;
- native C++23 `MFT1` decode;
- deterministic Truth fallback.

| Measurement | MFT1 + Truth | Direct Truth baseline | Direction |
|---|---:|---:|---|
| Complete bytes | 58,081 | 233,745 | MFT1 −75.15% |
| SNR | 41.883 dB | 41.104 dB | MFT1 +0.779 dB |
| SI-SDR | 41.882 dB | 41.106 dB | MFT1 +0.777 dB |
| Maximum absolute error | 0.00827 | 0.10120 | MFT1 lower |
| Log-mel RMSE | 2.182 | 1.404 | MFT1 worse |
| Magnitude cosine similarity | 0.999970 | 0.999992 | MFT1 worse |

The complete candidate contains 2,560 predictor bytes and 55,233 residual
bytes. The router selected 29 periodic-Basis, 11 impulse, seven stochastic,
and three `NO_MODEL` segments. Wall time was 9.189 seconds for 12 seconds of
audio on the development host.

The candidate wins the current exact-byte plus waveform-SSE gate, but the
spectral regressions prove that waveform SSE alone is not a sufficient
release-admission objective. It therefore remains research evidence only.

## Validation

- 210 Python 3.14 tests passed; four optional external-device/tool tests
  skipped.
- Clang 22 strict C++23: 14/14 tests passed.
- GCC 16.1 strict C++23: 14/14 tests passed.
- Android NDK r29 ARM64 complete build passed.
- Periodic callback-partition PCM is bit-identical.
- Exact-boundary tests include mandatory `NO_BOUNDARY` and resource bounds.

## Next admission gate

Before any general claim:

1. replace SSE-only admission with a declared multi-objective quality guard;
2. connect the exact sample candidates to complete-stream boundary RDO;
3. run all three complete references and all 16 R-111 classes;
4. compare complete bytes against the preceding Resonith stream and current
   official Opus anchors;
5. publish every selected MAF candidate, fallback, quality regression, and
   wall time.
