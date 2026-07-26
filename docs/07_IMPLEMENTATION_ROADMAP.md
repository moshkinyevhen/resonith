# Plan for the first implementation of MAF

Status: order - **ACCEPTED**; timing and gain - **TARGET / HYPOTHESIS**.

The goal of the first branch is not to immediately implement all families, but to obtain
falsifiable codec loop, in which each new mechanism proves its own
net gain.

## Milestone 0 - Golden Core

Artifacts:

- canonical PCM reader/writer;
- exact rational sample timeline;
- integer lifting baseline;
- deterministic rounding/saturation library;
- bit-exact CIBS integer synthesis kernel;
- versioned CIBS model package parser and Basis hash;
- bit counter with full overhead;
- Core checksum;
- first conformance vectors.

Criterion: encode/decode exact in Lossless and bit-identical on two independent
decoder paths.

## Milestone 1 – Periodic + CIBS oracle

Minimal grammar:

```text
STREAM_CONFIG
STATE_RESET
BASIS_SET(TIMBRE)
ATOM_SET(PERIODIC)
INNOVATION
CHECKPOINT
```

Encoder:

1. finds isolated stable pitch tracks;
2. builds one integer `TIMBRE_BASIS`;
3. encodes Basis in two competing ways:
   `RAW/LIFTED` and `CIBS_LATENT + basis correction`;
4. optimizes absolute phase/amplitude law;
5. decodes candidate;
6. encodes the remaining lifting residual;
7. compares three full bitstreams with a lifting-only baseline.

Kill-gate: minimum 20% net gain on isolated pitched material at equal
objective error.

## Milestone 2 — Train/export CIBS and shared structure

Add:

- `CONTROL_BASIS`;
- CIBS analysis model, quantization-aware export and fixed model package;
- repeated timbre across multiple notes;
- excitation–resonator factorization;
- content-addressed Basis reuse;
- Studio whole-track dynamic programming.

Individual ablation shows the contribution of each mechanism.

## Milestone 3 — Transient and stochastic

Add one at a time:

- short transient basis without pre-echo;
- counter-based stochastic atom;
- switching continuity tests;
- packet loss/checkpoint tests.

Each family goes through its own kill-gate and can be turned off without changing
the rest is bitstream.

## Milestone 4 - Broad codec

- speech/predictive candidate;
- stereo/spatial mixer;
- Realtime latency path;
- MUSHRA harness;
- Opus and xHE-AAC/USAC anchors;
- general/classical corpus;
- independent decoder.

The Immersive room model and Perceptual profile start only after the Core
demonstrates a gain on broad objective and perceptual tests.

## Code architecture target

```text
reference/
  decoder-core/ bit-exact integer Core
  bitstream/ parser, entropy, validation
encoder/
  oracle/ slow analysis-by-synthesis
  consumer/ later: distilled top-K router
experiments/
  cibs0/
  periodic_oracle/
  transient_ablation/
  stochastic_ablation/
tests/
  conformance/
  corruption/listening/
```

The first oracle MAY remain fast-moving Python research code, but normative
arithmetic is isolated from the beginning in a small independently testable
Core. The implementation sequence is:

1. keep MAF-P0 operational as the Python oracle;
2. freeze the smallest useful P0 arithmetic and container subset;
3. implement exact parity in the portable C++20 Golden Core and stable C ABI;
4. call that Core from decoder-in-the-loop Python RDO;
5. build the Rust parser, scheduler, and player services around the C ABI;
6. move only measured encoder bottlenecks to C++/SIMD/CUDA;
7. add an independent Rust decoder after Main-0 semantics stabilize.

The complete language, portability, and real-time contract is defined in
[11_IMPLEMENTATION_LANGUAGE.md](11_IMPLEMENTATION_LANGUAGE.md).
