# Implementation Language and Runtime Architecture

Status: **ACCEPTED — R-110**
Date: 2026-07-27

## 1. Decision

Resonith uses a deliberately split implementation stack:

1. **Portable C++23** for the bit-exact Golden Core, reference decoder,
   real-time renderer, entropy layer, state machine, and production DSP.
2. **A stable C ABI** around the decoder and conformance surface.
3. **Python 3.14.6** as a thin research control plane for rapidly expressing
   hypotheses, oracle search spaces, RDO cost functions, corpus tooling,
   visualization, training, metrics, and experiment orchestration.
4. **PyTorch** for non-normative teacher models and CIBS training/export.
5. **C++23, portable SIMD, and CUDA C++** for every measured encoder
   bottleneck whose work scales materially with samples, coefficients,
   candidates, or PVQ pulses. CUDA is never a conformance dependency.
6. **Rust** for untrusted package parsing, streaming/network orchestration,
   capability negotiation, player runtime services, and an independent
   decoder once the native P0 semantics stabilize.

This is not a compromise between two equivalent choices. Python is the
laboratory control surface; native code is the computation engine and the
product. Resonith libraries, tools, SDKs, embedded builds, and playback paths
have no Python runtime dependency.

## 2. Why the current Python prototype is correct

MAF-P0 is an experimental oracle. Python minimizes the cost of changing:

- basis extraction;
- period and pitch search;
- RDO candidate generation;
- CIBS training/export;
- benchmark accounting;
- plots and corpus analysis.

The Python layer SHOULD describe candidate graphs and costs, invoke native
kernels in batches, compare actual serialized streams, and publish evidence.
It MUST NOT retain a material per-sample, per-coefficient, per-candidate, or
per-pulse loop merely for implementation convenience. Profiling, rather than
language preference, defines the next native migration.

Rewriting the orchestration layer in C++ before the representation is stable
would slow research without improving the bitstream. Conversely, leaving
transform, PVQ search, synthesis, or decode loops in Python would make
full-track gates unnecessarily slow without improving iteration quality.

Python must not, however, become the only definition of decoding behavior.
Interpreter overhead, the GIL, dependency weight, mobile/embedded deployment,
real-time scheduling, SIMD control, and reproducible integer semantics make a
Python-only production decoder the wrong foundation for a hardware-targeted
standard.

## 3. Why the Golden Core is C++23 rather than Python

The normative path needs:

- exact-width integer arithmetic;
- explicit saturation, rounding, and overflow rules;
- bounded memory with no allocation on the audio thread;
- deterministic event ordering;
- portable SIMD and straightforward C/C++ compiler support;
- Android, iOS, desktop, browser/WASM, DSP, and embedded integration;
- direct reuse of kernels in CUDA and hardware-model code;
- sanitizers, fuzzers, coverage, and conformance-vector tooling.

C++23 adds stronger types, RAII, `constexpr` tables, templates for checked
fixed-point arithmetic, and safer ownership than a large C codebase while
retaining the deployment ecosystem required by codec and chip vendors.

C++23 is the production ceiling, not a license to use every new library
facility. Decoder-critical code uses only features that pass the project's
current Clang, GCC, MSVC, Apple Clang, Android NDK, iOS, WASM, and embedded
compile gates. C++26 remains a non-blocking forward-compatibility experiment
until those targets support it without reducing coverage.

The public boundary remains C-compatible so that browsers, operating systems,
game engines, FFmpeg-like frameworks, Rust, Swift, Java/Kotlin, and hardware
test benches do not depend on a C++ ABI.

## 4. Why not pure C or pure Rust

### Pure C

C remains an excellent portability baseline, and major deployed codecs prove
it. For Resonith, however, persistent atom state, immutable Basis objects,
multiple bounded payload schemas, checked fixed-point types, and CUDA sharing
make a carefully restricted C++23 core more maintainable.

A small C99 conformance decoder MAY be added later, but maintaining it before
the syntax stabilizes would duplicate effort.

### Pure Rust

Rust is attractive for parser safety and an independent decoder. It is not the
first implementation because the audio/DSP, codec-standardization, CUDA,
embedded, and vendor-integration ecosystems still center on C/C++ interfaces.
Starting with Rust would not remove the need for a C ABI or C++/CUDA kernels.

Rust becomes valuable immediately around the C ABI as the safe host for
untrusted files and networks. The fully independent Rust decoder follows once
bitstream semantics are stable enough to avoid implementing two moving
targets.

## 5. Normative C++ restrictions

The Truth Core MUST follow a stricter subset than general application C++:

- no undefined signed overflow;
- no implementation-dependent right shift in normative arithmetic;
- no `-ffast-math` or equivalent in Truth code;
- no floating-point normative state;
- no exceptions, RTTI, blocking locks, I/O, or heap allocation in the
  sample-render loop;
- no unordered iteration affecting output;
- all shifts, division, rounding, clipping, and saturation defined by helper
  primitives with exhaustive boundary tests;
- explicit upper bounds for every container, loop, recursion depth, and
  payload;
- little-endian bitstream reads implemented independently of host endianness;
- sanitizers and fuzzing in CI;
- identical conformance hashes across MSVC, Clang, GCC, x86-64, ARM64, and
  WASM.

The specification, not C++ source code, remains normative. The Golden Core is
the executable reference used to expose ambiguity.

## 6. Repository layout target

```text
spec/                   language-independent bitstream and decoder semantics
reference/cpp/          portable C++23 Golden Core
include/resonith/       stable public C API
bindings/python/        thin bindings to the exact C++ Core
research/python/        oracle encoder, RDO, training, and experiments
kernels/cuda/           optional non-normative encoder acceleration
tests/conformance/      golden vectors and cross-compiler hashes
tests/fuzz/             parser/state-machine fuzz targets
```

Python experiments MUST call the C++ decoder through the binding for final
decoder-in-the-loop RDO. Expensive forward analysis, transform, PVQ search,
candidate reconstruction, synthesis, and decode MUST call shared native
kernels before a full-corpus promotion gate. A separately structured Python
renderer MAY remain as an independent oracle and must never silently define
the bitstream.

## 7. Migration order

1. Keep MAF-P0 Python operational as the research control plane and
   independent oracle.
2. Freeze the smallest P0 container and arithmetic subset needed for parity.
3. Implement C++23 container parsing, CIBS materialization, phase rendering,
   block-gain law, residual reconstruction, and WAV-independent sample API.
4. Generate shared golden vectors and require byte/sample equality.
5. Bind the C++ Core into Python.
6. Move every measured sample-, coefficient-, candidate-, and pulse-scaling
   encoder bottleneck to C++/SIMD/CUDA while its search policy remains rapidly
   configurable from Python.
7. Add a Rust independent decoder after Main-0 semantics stabilize.

The first C++ parity target is deliberately small. It must not trigger a
rewrite of the research encoder.

A candidate may begin as an entirely Python oracle for a small falsification
crop. Before the permanent three-reference or extended-corpus gate, its heavy
kernels must expose a bounded native API, preserve exact serialized bytes or
declare a distinct encoder search level, and pass native/independent equality.
This keeps the first experiment cheap without allowing laboratory overhead to
become product architecture.

Steps 2 through 5 now have an executable mono periodic subset: RSC1, `CONF`,
`ATOM`, `BRAW`/`BCIB`, and `RSL1`/`RSL2` decode through allocation-free whole
and callback C entry points. Python candidate RDO accepts a stream only after
native/reference PCM equality. Promoted transients, multiple simultaneous
Atoms, and channels remain outside that completed subset.

## 8. Player and cross-platform runtime

The codec library and the player are separate layers:

```text
native UI / service integration
        |
Rust player runtime and secure stream/package parser
        |
stable versioned C ABI
        |
C++23 Resonith Golden Core
        |
platform audio and compute adapters
```

The Core MUST NOT depend on a window system, audio API, filesystem, network
stack, UI toolkit, Python runtime, GPU API, or operating system.

Platform adapters target:

| Platform | Audio/output | Compute and presentation |
|---|---|---|
| Windows | WASAPI | D3D12, Vulkan |
| macOS/iOS | CoreAudio / AudioUnit | Metal |
| Android | AAudio / Oboe adapter | Vulkan |
| Linux | PipeWire/ALSA adapters | Vulkan |
| Browser | AudioWorklet | WASM SIMD, WebGPU |
| Embedded/DSP | callback/ring-buffer C ABI | scalar, vendor SIMD, DMA |

The mandatory first mobile matrix is:

| Artifact | Architecture | Baseline |
|---|---|---|
| Android production Core | `arm64-v8a` | NDK r29, API 26, static libc++ |
| Android emulator Core | `x86_64` | NDK r29, API 26, static libc++ |
| iOS device Core | ARM64 | stable Xcode, iOS 15 deployment |
| iOS simulator Core | x86-64 | stable Xcode, iOS 15 deployment |

These are codec-library gates. Orkela owns separate UI, file-provider,
background-audio, lifecycle, interruption, and device-output tests. A library
compile does not by itself establish player compatibility.

The desktop and mobile UI may use native UI, Qt/QML, or Flutter, but the
choice is non-normative and lives above the Rust/C ABI boundary. No UI
framework may enter the decoder dependency graph.

For SceneLith/Resonith synchronized playback, the player runtime may share the
master timeline and entity metadata through SceneLith AV Bridge. Each codec
still exposes an independently usable library.

## 9. Real-time and portability contract

The render callback MUST:

- perform no heap allocation, file/network I/O, logging, blocking lock, or
  lazy model loading;
- consume prevalidated immutable state through bounded queues;
- use fixed maximum scratch memory supplied by the host;
- expose exact worst-case work and state limits for every profile/level;
- support planar and interleaved integer/float host output without changing
  normative internal samples;
- tolerate arbitrary host callback sizes without changing decoded output;
- support zero-copy input slices and output spans where alignment permits.

The portable scalar path is mandatory. SIMD is an exactly equivalent
acceleration layer with runtime dispatch:

- x86-64 SSE4.1/AVX2 and optional AVX-512;
- ARM64 NEON and optional SVE2;
- WASM SIMD128;
- vendor DSP intrinsics behind isolated adapters.

No architecture-specific path may define different rounding or clipping.

## 10. Modern engineering quality gates

Every public change to the native Core must pass:

1. MSVC, Clang, and GCC builds.
2. Windows x86-64, Linux x86-64/ARM64, macOS ARM64, Android ARM64, iOS ARM64,
   and WASM compile checks.
3. Bit-exact cross-compiler conformance hashes.
4. ASan, UBSan, TSan where applicable, and MSVC runtime checks.
5. libFuzzer/AFL++ parser and state-machine fuzzing.
6. Property tests for arithmetic, random access, checkpoint recovery, and
   block-size independence.
7. Static analysis with clang-tidy and CodeQL.
8. Reproducible release builds, dependency lockfiles, SBOM, and signed
   artifacts.
9. ABI compatibility tests and semantic versioning.
10. Real-time tests that detect allocation, lock contention, deadline misses,
    denormals, and priority inversion.

The project should use CMake Presets as the portable native build contract,
with Ninja in CI. Package managers may assist development, but the Core keeps
zero mandatory third-party runtime dependencies.

## 11. Commenting and debug-readability contract

Comments are part of the engineering interface. They MUST maximize useful
debugging information for both human contributors and AI agents without
turning source files into prose.

### Required comments

- Every public C ABI symbol, externally visible type, and non-obvious module
  has a concise contract: inputs, outputs, ownership, lifetime, thread-safety,
  error behavior, and resource bounds.
- Every normative DSP kernel cites the applicable specification clause and
  states Q-format, accumulator width, rounding, saturation, overflow, phase,
  and aliasing assumptions.
- Every Atom or Basis state mutation explains its preconditions, atomic commit
  point, rollback behavior, and the invariant preserved after failure.
- Every lock-free queue, SIMD path, and platform adapter explains its memory
  ordering, real-time assumptions, and exact equivalence to the scalar path.
- Every security boundary states what has already been validated and what
  remains untrusted.
- A non-trivial function is divided into a few named logical phases when this
  makes control flow visibly easier to debug, for example:

  ```cpp
  // 1. Validate the complete BASIS_SET without mutating the Basis Bank.
  // 2. Materialize and hash the candidate in bounded staging memory.
  // 3. Commit atomically, or discard the candidate on any mismatch.
  ```

### Noise is prohibited

- Do not restate syntax, types, or operations already obvious from the code.
- Do not comment every line, use decorative ASCII banners, or duplicate the
  specification inside source files.
- Remove dead commented-out code; version control already preserves history.
- A `TODO`, `FIXME`, temporary approximation, or unexplained constant MUST
  include a tracked issue or decision identifier and an explicit removal gate.
- Comments MUST be updated in the same commit as the behavior they describe.
  A stale comment is treated as a defect.

### Debug visibility

- Complex pipelines expose optional structured trace events with stable IDs
  for parse, validate, stage, synthesize, render, commit, fallback, and reject
  phases.
- Trace output is deterministic for a deterministic input, carries sample
  timestamps and Atom/Basis IDs, and can be compared across implementations.
- Logging is compiled out or disabled by default in the audio callback and
  never changes scheduling, allocation, state, or decoded samples.
- Assertions document internal invariants; malformed external input follows
  checked error paths rather than assertions.

Comment quantity is never a quality metric. Review evaluates whether a new
contributor can identify the contract, invariants, state transition, numerical
rules, and failure path without reading unrelated code.

## 12. Evidence from current codecs

- The Opus reference implementation is portable C and supports C89/C99,
  including a fixed-point build:
  <https://github.com/xiph/opus>.
- 3GPP publishes the EVS fixed-point reference as ANSI C in TS 26.442:
  <https://portal.3gpp.org/desktopmodules/Specifications/SpecificationDetails.aspx?specificationId=1464>.
- Google liblc3 uses a C codec implementation validated against a Python
  implementation and specification intermediate values:
  <https://github.com/google/liblc3>.
- Fraunhofer FDK AAC is distributed as a native C/C++-style library:
  <https://github.com/mstorsjo/fdk-aac>.
- Meta EnCodec is a Python/PyTorch research implementation and explicitly
  limits official platform support, illustrating why neural research code is
  not by itself a universal embedded decoder:
  <https://github.com/facebookresearch/encodec>.

The pattern is consistent: Python dominates model research; portable native
code dominates deployed deterministic codec cores. Resonith should exploit
both instead of forcing one language to serve incompatible roles.
