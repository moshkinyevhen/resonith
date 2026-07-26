# Resonith Native Golden Core

Status: **EXECUTABLE MAIN-0 SUBSET**

This directory contains the dependency-free portable C++20 implementation of
the first frozen Resonith decoder primitives. The current subset validates the
compact `RSC1` section container and decodes `LiftPack-1`
objective-innovation streams through a stable C99 ABI.

## Runtime contract

The native Core:

- performs no heap allocation, I/O, logging, locking, or global mutation;
- writes only to caller-owned output and scratch buffers;
- validates the complete stream envelope and CRC before decoding;
- exposes zero-copy `RSC1` section views after a bounded linear validation
  pass and verifies section CRC-32 plus SHA-256 without dependencies;
- rejects non-canonical lengths, trailing bytes, non-zero padding, profile
  bound violations, and undersized buffers;
- uses a portable scalar implementation with no third-party dependency;
- exposes status codes rather than exceptions across the ABI.

The scratch requirement is reported in `int64_t` elements by
`resonith_liftpack_required_scratch()`. The input, output, and scratch
lifetimes remain owned by the caller. Output and scratch must not overlap.
The same decoder instance is reentrant and thread-safe because it owns no
mutable state.

## Build and test

```sh
cmake -S native -B build/native -DCMAKE_BUILD_TYPE=Release
cmake --build build/native --config Release
ctest --test-dir build/native --build-config Release --output-on-failure
```

`RESONITH_WARNINGS_AS_ERRORS=ON` is the default. CI builds the same source
with GCC, Clang, and MSVC. The C header is compiled by a C99 translation unit,
while the implementation remains C++20.

## Conformance anchor

`native/tests/liftpack_test.cpp` embeds the canonical 203-byte stream from the
Python Golden Encoder and checks all 192 reconstructed coefficients. Its
SHA-256 is:

```text
6d58812162388dfe58c2b602372bf144d36af00f7a19cb39250e0d920609fee6
```

`tests/test_native_vector.py` independently regenerates the packet and rejects
any byte drift between the Python and C++ sources. A second frozen stream
exercises all four transforms and both entropy modes and is independently
decoded by both implementations.

This is not yet the full Resonith decoder. Container parsing, Basis
materialization, Atom trajectories, transient rendering, gain laws, and
multi-channel synthesis remain subsequent parity stages.
