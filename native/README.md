# Resonith Native Golden Core

Status: **EXECUTABLE MAIN-0 SUBSET**

This directory contains the dependency-free portable C++20 implementation of
the first frozen Resonith decoder primitives. The current subset validates the
compact `RSC1` section container and decodes complete mono model-bearing and
one-through-eight-channel residual-only Main-0 streams through a stable C99
ABI.

## Runtime contract

The native Core:

- performs no heap allocation, I/O, logging, locking, or global mutation;
- writes only to caller-owned output and scratch buffers;
- validates the complete stream envelope and CRC before decoding;
- exposes zero-copy `RSC1` section views after a bounded linear validation
  pass and verifies section CRC-32 plus SHA-256 without dependencies;
- materializes registered CIBS models once with bounded integer projection,
  adapter, refinement, correction, and atomic Basis-hash verification;
- resolves latent-only typed `BCIB` Basis records through immutable
  caller-owned registries, preflights every materialized hash before PCM
  delivery, and shares non-overlapping int64 staging with LiftPack;
- prepares absolute Q32 phase-knot origins once and renders arbitrary periodic
  slices with callback-size-independent Q16 interpolation;
- applies sparse absolute Q17.15 gain events and objective Innovation in one
  bounded saturating Truth-composition pass;
- decodes bounded LiftPack-1 and LiftPack-2 residuals, including Main-0 Q12
  LPC with an order-16 ceiling;
- independently inspects and decodes the prospective fixed/bounded LPF1
  research path through Q14/Q15 quarter-wave ROM, sparse Rice/packed fields,
  caller-owned overlap memory, and preflighted int64 arithmetic;
- supports both fixed LSE1 density and implicit-state LSE2 count trajectories
  through the same transform, entropy primitives, and output path;
- validates and exports caller-owned byte/sample block indexes for bounded
  seek planning without decoding PCM or allocating memory;
- builds and verifies optional source-bound `RSI1` seek sidecars with
  independent CRC-32/SHA-256 integrity and exact entry/source equality;
- opens immutable Main-0 player views, decodes independently seeded zero-Atom
  Truth blocks directly to PCM16, and streams complete model-bearing state
  partitions with output-atomic block failure;
- validates aligned independent-channel RSL2 partitions and emits canonical
  interleaved PCM through one allocation-free callback using one channel block
  plus one interleaved output block;
- exposes a caller-owned pull session with one forward cursor per channel;
  cursor state commits only after every channel reconstructs the same block,
  making the primitive suitable for device callbacks and bounded ring buffers;
- decodes minimal typed `BRAW` Basis payloads into aligned caller-owned
  host-endian memory without generic array metadata;
- parses fixed `CONF` and state-local periodic `ATOM` payloads, reports exact
  maximum per-state workspace, reuses immutable Basis references across a
  canonical state partition, and orchestrates whole-container decode with no
  hidden allocation;
- rejects non-canonical lengths, trailing bytes, non-zero padding, profile
  bound violations, and undersized buffers;
- uses a portable scalar implementation with no third-party dependency;
- exposes status codes rather than exceptions across the ABI.

The scratch requirement is reported in `int64_t` elements by
`resonith_liftpack_required_scratch()`. The input, output, and scratch
lifetimes remain owned by the caller. Output and scratch must not overlap.
The same decoder instance is reentrant and thread-safe because it owns no
mutable state.

`resonith_liftpack_index_blocks()` validates each block envelope after the
whole-stream CRC and emits exact byte offsets, sample offsets, transform IDs,
entropy parameters, and LPC order. LiftPack blocks carry their own LPC seeds,
so `resonith_liftpack_decode_block()` can reconstruct one selected block into
caller-owned memory without decoding earlier PCM. A player layer may cache the
index or serialize independently checked checkpoints.

`resonith_main0_player_open()` verifies the complete typed RSC1 stream once.
`resonith_main0_player_decode_block()` exposes the production zero-Atom Truth
path as bounded PCM16 callback-sized work without retaining decoder state. The
view borrows immutable stream bytes; applications decide whether to keep an
in-memory block index or a separately verified seek table. For continuous
zero-Atom playback, `resonith_main0_player_stream()` advances one caller-owned
LiftPack cursor. `resonith_main0_player_stream_complete()` adds state-local
periodic prediction and resolves Atom transitions even when a residual block
crosses a state boundary. Both functions emit canonical blocks through the
same C callback; live residual workspace remains one block.

## Build and test

```sh
cmake -S native -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native --build-config Release --output-on-failure
```

`RESONITH_WARNINGS_AS_ERRORS=ON` is the default. CI builds the same source
with GCC, Clang, and MSVC. The C header is compiled by a C99 translation unit,
while the implementation remains C++20.

The build also emits `resonith_core_shared` from the identical source set.
Python RDO loads it only through an explicit `RESONITH_NATIVE_CORE` path:

```sh
cmake --build build/native --target resonith_core_shared
export RESONITH_NATIVE_CORE="$PWD/build/native/libresonith_core_shared.so"
python -m unittest discover -s tests -p test_native_bridge.py -v
```

The binding inspects exact workspace counts and applies a host memory ceiling
before creating caller-owned arrays.

The same C99 ABI now exposes allocation-explicit fixed Q15/Q14 forward
analysis through `resonith_lapped_analyze_requirements` and
`resonith_lapped_analyze_pcm16`. It emits immutable scale, quantized
coefficient, and squared-score grids for encoder-side frontier searches; it
does not pack policy or RDO decisions into the decoder Core.

`resonith_lapped_packet_open()` preflights an independently authenticated
`LPS1` or `LPS2` sequence and reports the maximum child workspace, temporary
child PCM, and logical output capacities. A caller-owned
`resonith_lapped_packet_session` then advances with
`resonith_lapped_packet_decode_next()`. Each pull revalidates its packet,
decodes either one context-bearing LPF1 child or one direct transform-boundary
LSE2 field, emits the declared logical interval, and commits the session only
on success. Both forms share the same entropy and integer synthesis kernel.
The session borrows immutable input bytes and contains no hidden allocation or
persistent transform state.

`resonith_lapped_compact_open()` separately preflights prospective `LPS4`
single-owner records. It verifies the sequence SHA-256, derived record lengths,
every CRC-32, canonical padding, inherited shape, and maximum current plus
one-record-lookahead resources without allocation.
`resonith_lapped_compact_decode_next()` then decodes both caller-owned field
workspaces and renders the shared transform boundary transactionally. Frozen,
long-stream cross-decoder, hosted resource, and sanitized mutation gates pass.

For independently transported records,
`resonith_lapped_compact_sequence_open()` validates exactly the immutable
60-byte context and `resonith_lapped_compact_decode_record_pair()` decodes an
exact record frame under an explicit packet index. Non-final records require
their immediate successor; final records forbid lookahead. The transport must
authenticate the context, index, and bytes and enforce replay policy before
calling the Core. CRC-32 is not authentication. The mapping is stateless, so a
missing record does not contaminate later Truth. Cryptographic transport
integration, physical-device, reordering/loss-scheduling, and listening gates
remain prospective.

## Physical-device callback benchmark

`resonith_lapped_device_bench` is built from the same portable source on
desktop, ARM64, and Android targets. It preflights one LPS4 file and allocates
the reported caller workspaces before timing. The measured interval contains
only transactional pull decode. Its JSON result reports callback tail latency,
deadline misses, realtime speed, memory, and a repeat-stable PCM hash:

```sh
build/native/resonith_lapped_device_bench input.lps 20 3
```

File I/O, allocation, and reporting are outside callback timing. External
device runners may collect temperature, frequency, power, and battery data,
but those platform APIs do not enter the codec Core.

For a physical Android arm64-v8a device, the external runner verifies local and
device-side hashes, refuses ambiguous device selection, executes sustained
native runs, and records available thermal zones, CPU frequencies, and battery
state:

```sh
python experiments/android_device_gate.py \
  --benchmark build/android-arm64/resonith_lapped_device_bench \
  --stream input.lps \
  --iterations 50 --warmups 5 --sustained-runs 5 \
  --output artifacts/android-device/report.json
```

Pass `--serial` when multiple authorized devices are attached. Missing vendor
sensors remain missing in the report; battery state is not represented as an
energy measurement.

## Sanitized fuzzing

Clang builds the LiftPack, Main-0, seek-sidecar, and lapped-stream parsers and
inverse DSP into separate ASan/UBSan/libFuzzer targets:

```sh
cmake -S native -B build/fuzz \
  -DBUILD_TESTING=OFF \
  -DRESONITH_BUILD_FUZZERS=ON
cmake --build build/fuzz \
  --target resonith_liftpack_fuzz resonith_main0_fuzz resonith_seek_fuzz \
  resonith_lapped_fuzz resonith_lapped_packet_fuzz \
  resonith_lapped_compact_fuzz
python scripts/generate_fuzz_corpus.py artifacts/fuzz_corpus
build/fuzz/resonith_liftpack_fuzz \
  artifacts/fuzz_corpus/liftpack -runs=5000
build/fuzz/resonith_main0_fuzz \
  artifacts/fuzz_corpus/main0 -runs=5000
build/fuzz/resonith_seek_fuzz \
  artifacts/fuzz_corpus/seek -runs=5000
build/fuzz/resonith_lapped_fuzz \
  artifacts/fuzz_corpus/lapped -runs=5000
build/fuzz/resonith_lapped_packet_fuzz \
  artifacts/fuzz_corpus/lapped_packet -runs=5000
build/fuzz/resonith_lapped_compact_fuzz \
  artifacts/fuzz_corpus/lapped_compact -runs=5000
```

The harnesses cap host allocations after a successful envelope inspection;
the Core itself remains allocation-free. CI starts from deterministic valid
RSL1, RSL2/LPC, zero-Atom, periodic-Atom, source-bound RSI1, fixed- and
adaptive-density LPF1, LPS1, LPS2, and compact LPS4 seeds.
Mutations therefore reach container, typed-section, seek, block, entropy,
model-render, and inverse-DSP paths rather than stopping only at an outer
checksum.

## Conformance anchor

`native/tests/liftpack_test.cpp` embeds the canonical 203-byte LiftPack-1
stream from the Python Golden Encoder and checks all 192 reconstructed
coefficients. Its SHA-256 is:

```text
6d58812162388dfe58c2b602372bf144d36af00f7a19cb39250e0d920609fee6
```

`tests/test_native_vector.py` independently regenerates the packet and rejects
any byte drift between the Python and C++ sources. A second frozen stream
exercises all four transforms and both entropy modes and is independently
decoded by both implementations. A third vector exercises LiftPack-2 LPC and
its signed nearest, ties-away Q12 inverse recurrence.

`native/tests/cibs_test.cpp` executes the same demo projection, adapter,
refinement, correction, and SHA-256 vectors as the Python CIBS oracle. The
model is an operator conformance fixture and remains explicitly non-normative.

`native/tests/trajectory_test.cpp` verifies prepared knot origins, every Q32
phase, every rendered sample, and equality across deliberately irregular
callback partitions.

`native/tests/composition_test.cpp` verifies sparse gain events, negative
floor-division, Innovation scaling, saturation, and slice independence.

`native/tests/basis_test.cpp` verifies the first typed acoustic payload and
cross-endian sample reconstruction.

`native/tests/pipeline_test.cpp` embeds a complete 557-byte RSC1 stream and
calls the public whole-stream decoder once. The canonical stream SHA-256 is:

```text
32e4e7d0f8b5ff7c2d7c33ed51579c24731d57ee9c681cbc480eee23e0e3aa74
```

Python independently decodes the same stream and checks the exact PCM vector.
The test also proves that a rejected undersized workspace leaves output PCM
unchanged.

The native Python bridge independently generates an aligned stereo RSC1
stream, then requires whole native decode, interleaved callback decode, and the
Python decoder to produce identical frames.

This is not yet the full Resonith decoder. Promoted transient rendering,
gated source-specific models, and spatial/object synthesis remain subsequent
parity stages.
