# Plan for the first implementation of MAF

Status: order - **ACCEPTED**; timing and gain - **TARGET / HYPOTHESIS**.

The goal of the first branch is not to immediately implement all families, but to obtain
falsifiable codec loop, in which each new mechanism proves its own
net gain.

## Execution update — 2026-07-26

Status: **IMPLEMENTED / EXPERIMENTAL**

- MAF-P0 periodic RAW/CIBS loop is complete.
- MAF-P1 multi-Basis lifetimes, content reuse, and absolute phase trajectories
  are complete in the Python oracle.
- The bounded reversible transient path is complete, but its first forced
  ablation lost 0.72%; `auto` correctly rejected it.
- A real official Opus encode/decode anchor is integrated locally and in Linux
  CI with full container-byte and executable-provenance accounting.
- `LiftPack-1`, acoustic change-point proposals, full-stream boundary RDO, and
  the first licensed real-music corpus test are complete.
- The fixed-integer bounded adaptive-density lapped candidate now has a
  synchronized offline blind-listening harness, a hidden reference, an explicit
  low-pass anchor, strict result validation, and three real-music trials
  rate-matched to complete Opus bytes within 1.10%.
- The bounded `LAF1` adaptive integer entropy candidate preserves the selected
  reconstruction exactly and reduced complete R-084 bytes by 6.47% on piano,
  5.34% on drums, and 7.67% on Corelli. Its allocation-free C99 path passes
  Python parity, x64/ARM64 cross-compilation, Android NDK, and sanitized
  mutation gates. On the physical Xeon host its complete-field entropy stage
  ran at 259x–357x realtime median with 81.8–119.1 KB caller workspace.
- Independently reset compact LAF1 records passed the R-097 transport gate at
  12,288 frames: prospective LPS5 saved 5.32% on piano, 3.43% on drums, and
  5.95% on Corelli against complete LPS4 bytes with identical reconstruction.
  The 34.8 ms point did not pass, so LPS4 remains the Realtime fallback.
- Native LPS5 integration reuses the allocation-free LPS4 pull/stateless ABI
  and is undergoing cross-compiler, decoder-in-loop, and sanitized mutation
  gates under R-098.
- The portable Core now decodes a complete typed mono RSC1 stream through one
  allocation-free C API call.
- Python encoder RDO is bound to the native whole-stream decoder and rejects
  any cross-decoder PCM mismatch.
- LiftPack-2 bounded integer LPC passed its declared three-clip byte gate and
  is implemented in the native Core.
- Exact block indexing, independent block decode, a linear forward cursor,
  callback-oriented playback for zero-Atom and model-bearing state partitions,
  and separate LiftPack/Main-0 sanitized fuzz targets are implemented and
  cross-compiler verified.
- The optional source-bound RSI1 seek sidecar and its dedicated sanitized
  fuzzer are implemented. The mandatory Truth stream remains independently
  sequentially decodable.
- Latent-only typed `BCIB` Basis records now resolve through immutable
  application registries and decode through both whole-stream and callback
  paths with preflighted Basis hashes and shared LiftPack/CIBS scratch.
- The same Core passes native Linux, Windows, and macOS ARM64 tests and an
  Android NDK arm64-v8a build without platform-specific DSP source.
- Stateless LPS4 record-pair decode and the standalone callback-tail benchmark
  pass every cross-platform gate. An external ADB runner is ready for named
  phone temperature, frequency, deadline, and sustained-run evidence.
- The exact CI-built Windows executable has completed 26,100 callback
  observations on the current physical host with zero deadline misses,
  9.81x-12.33x realtime decode, and 29.5-37.8 KB caller workspace.
- Variable block lifetimes and three bounded waveform-domain stereo families
  failed their declared promotion gates and added no Main syntax.
- Held-out cached-Basis overlap has now also failed its complete-byte gate:
  zero Atoms won all three clips because residual savings did not repay the
  `BCIB`, `ATOM`, and directory records. Simultaneous periodic mixing is not
  promoted.
- The next blocking evidence is real blinded listening and named physical-phone
  timing. No new lossy syntax is promoted while these gates are open.
- New compression tools resume only through declared complete-byte or
  matched-listening gates. Model ROM is always reported separately and
  amortized; it is never treated as free per-stream knowledge.

Detailed measurements are in
[10_MAF_P0_IMPLEMENTATION.md](10_MAF_P0_IMPLEMENTATION.md) and
[12_LIFTPACK_AND_STATE_RDO.md](12_LIFTPACK_AND_STATE_RDO.md).

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

## Mandatory continuous evidence loop

Every material milestone uses the same loop:

1. implement one falsifiable change behind an ablation switch;
2. run unit, conformance, corruption, and native decoder parity tests;
3. encode the pinned LibriSpeech excerpt, Emotional piano reference, and
   complete Mozart overture;
4. rate-match the current official Opus anchor by complete Ogg bytes;
5. decode through the exact release decoder and measure waveform,
   multi-resolution spectral, log-mel, harmonic, and speech-intelligibility
   diagnostics;
6. compare complete bytes and quality against both the preceding Resonith
   version and Opus;
7. remove a losing mechanism or retain it under an explicit research status;
8. publish the report, listening artifacts, hashes, tool versions, source
   commit, and wall times;
9. update `CHANGELOG.md`, the semantic version, and the matching local and
   GitHub release.

Objective diagnostics never authorize a transparent or perceptually superior
claim without controlled blinded listening. The detailed contract is
[15_CONTINUOUS_EVIDENCE.md](15_CONTINUOUS_EVIDENCE.md).

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

The first falsification oracle MAY remain fast-moving Python research code,
but Python is only the research control plane. Normative arithmetic is
isolated from the beginning in a small independently testable Core, and every
material loop that scales with samples, coefficients, candidates, or PVQ
pulses moves to native code before a full-corpus promotion gate. The
implementation sequence is:

1. keep MAF-P0 operational as the Python oracle;
2. freeze the smallest useful P0 arithmetic and container subset;
3. implement exact parity in the portable C++20 Golden Core and stable C ABI;
4. call that Core from decoder-in-the-loop Python RDO;
5. build the Rust parser, scheduler, and player services around the C ABI;
6. move measured transform, search, reconstruction, synthesis, and other
   scaling encoder bottlenecks to C++/SIMD/CUDA while retaining Python for
   rapidly editable search policy, metrics, and reporting;
7. add an independent Rust decoder after Main-0 semantics stabilize.

The complete language, portability, and real-time contract is defined in
[11_IMPLEMENTATION_LANGUAGE.md](11_IMPLEMENTATION_LANGUAGE.md).
Official codec, SDK, embedded, command-line, and Orkela deliverables have zero
Python runtime dependency under R-110.
