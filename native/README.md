# Resonith Native Golden Core

Status: **EXECUTABLE MAIN-0 SUBSET**

This directory contains the dependency-free portable C++20 implementation of
the first frozen Resonith decoder primitives. The current subset validates the
compact `RSC1` section container and decodes the first complete mono Main-0
stream through a stable C99 ABI.

## Runtime contract

The native Core:

- performs no heap allocation, I/O, logging, locking, or global mutation;
- writes only to caller-owned output and scratch buffers;
- validates the complete stream envelope and CRC before decoding;
- exposes zero-copy `RSC1` section views after a bounded linear validation
  pass and verifies section CRC-32 plus SHA-256 without dependencies;
- materializes registered CIBS models once with bounded integer projection,
  adapter, refinement, correction, and atomic Basis-hash verification;
- prepares absolute Q32 phase-knot origins once and renders arbitrary periodic
  slices with callback-size-independent Q16 interpolation;
- applies sparse absolute Q17.15 gain events and objective Innovation in one
  bounded saturating Truth-composition pass;
- decodes bounded LiftPack-1 and LiftPack-2 residuals, including Main-0 Q12
  LPC with an order-16 ceiling;
- validates and exports caller-owned byte/sample block indexes for bounded
  seek planning without decoding PCM or allocating memory;
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
so this index is the first allocation-free random-access primitive; a later
player layer may cache it or serialize independently checked checkpoints.

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

This is not yet the full Resonith decoder. Typed CIBS stream integration,
transient rendering, multi-Atom mixing, and multi-channel synthesis remain
subsequent parity stages.
