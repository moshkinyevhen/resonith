# R-122 Bounded MAF DSP and Stream Integration

Date: **2026-07-27**  
Status: **implementation gate passed; no compression claim**

## Outcome

The portable C++23 Core now implements the first bounded MAF execution
substrate behind the stable C ABI. Main-0 whole-stream decoding and callback
playback route periodic Basis rendering and gain/Truth composition through one
transactional operation budget.

This milestone changes decoder safety and architecture, not encoder selection
or compressed bytes. It therefore makes no bitrate, Opus, or perceptual-quality
claim. Source-filter, stochastic, transient, and channel-matrix operations are
available as independently tested DSP primitives; their promoted typed stream
syntax and the complete R-118 19-item codec gate remain subsequent admission
work.

Implementation source: `cca3a16a0e6ec9ced7bc3f595ba67cda3261bf8d`.

## Implemented operation boundary

The public `resonith/maf.h` interface provides:

1. hard Main profile limits and complete resource preflight;
2. a monotonically decreasing per-transaction operation budget;
3. periodic immutable-Basis rendering;
4. sparse gain plus deterministic Truth Innovation composition;
5. absolute-index counter noise;
6. stable reflection-to-LPC filter preparation and causal filtering;
7. quantized Innovation addition;
8. onset-addressed transient injection;
9. Q1.15 channel-matrix mixing.

Every operation validates arguments, profile bounds, output capacity, and the
complete operation charge before the first output write. Rendering uses
caller-owned memory and performs no allocation, file/network access, model
discovery, logging, or locking.

The stream cannot carry native code, bytecode, scripts, shaders, dynamic
libraries, or unbounded graphs. CIBS remains limited to immutable Basis
materialization outside the render callback.

## Determinism and security gates

- Counter noise is a pure function of stream seed, field ID, channel, and
  absolute sample index.
- Periodic, filter, and noise tests compare whole-block and deliberately
  partitioned callback output.
- Insufficient operation budgets leave output and budget state unchanged.
- Malformed resource declarations, unstable filter parameters, excessive
  work, invalid transient state, and undersized buffers are rejected.
- The portable smoke harness sends three edge corpora and 20,000 deterministic
  pseudo-random inputs through the same `LLVMFuzzerTestOneInput` entry point.
- Linux CI separately runs ASan, UBSan, and libFuzzer targets.

## Cross-platform results

### Local workstation

| Gate | Result |
|---|---:|
| Clang 22.1.8 strict C++23 native tests | 12/12 passed |
| GCC 16.1.0 strict C++23 native tests | 12/12 passed |
| Python 3.14.6 reference/native/Opus integration | 195/195 passed |
| Deterministic adversarial MAF inputs | 20,003 passed |
| Android NDK r29 ARM64 build | passed |
| Android NDK r29 x86-64 build | passed |

### GitHub

The complete
[Tests run 30255223721](https://github.com/moshkinyevhen/resonith/actions/runs/30255223721)
passed on:

- Linux x64 GCC and Clang;
- Linux ARM64 GCC;
- Windows x64 and ARM64 MSVC;
- macOS ARM64 AppleClang;
- Android ARM64 NDK;
- the Python reference and native decoder-in-loop suites;
- ASan/UBSan/libFuzzer mutation gates.

The
[Mobile Core run 30255223694](https://github.com/moshkinyevhen/resonith/actions/runs/30255223694)
passed Android ARM64, Android x86-64, iOS device ARM64, and iOS simulator
x86-64. Published archive sizes were 1,010,449, 997,290, 71,858, and 70,268
bytes respectively.

## Portability defects found by the gate

The independent GCC gate found one narrowing diagnostic in the reverse
filter-history index. The index now uses the natural `size_t` domain without
changing output.

Windows ARM64 then exposed an architecture-dependent negative Q15 result in
the former unsigned-magnitude rounding helper. R-127 replaced it with the
explicit signed quotient/remainder definition of ties-away-from-zero.
The frozen transient vector now reconstructs:

```text
0, 0, 0, 1000, 2000, -1000, -500, 0
```

on Windows ARM64 and every other admitted compiler/architecture.

## Local artifact hashes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Clang Windows Core DLL | 631,808 | `f5f75c70d33c497a3848c82214827fc7a06c9c4e2f97b3bc69290580e2431694` |
| Clang MAF conformance executable | 96,768 | `f95f63b97a811c42c5570421a99f26cff155d0ecec828e35cab457dd09801ff3` |
| Clang MAF adversarial smoke executable | 96,256 | `23dd6163d9110af9e8c3b2f5758a1f07814228159f7259913406e430d2cb1cc7` |
| GCC Windows Core DLL | 394,622 | `a5f9e7de5fe54fc6175a65f30d4b270ef0b555f94ebed3a76e385da6abc74b3f` |
| Android ARM64 Core shared object | 2,415,328 | `b641ded217f02778c43abdbbba911d1b0bc70d60b284c332a059e6670a13a678` |
| Android x86-64 Core shared object | 2,283,072 | `c3c0d43985bc26f5e45b7e27c4941511d3d3235438a6cce42826c788b2ac2a94` |

These hashes identify the local builds. GitHub archive sizes identify separate
CI artifacts and are not asserted to have the same archive or binary hash.

## Admission boundary

R-122 is now sufficient for encoder experiments to target a small,
resource-bounded decoder rather than an imagined future runtime. It is not yet
a promoted MAF bitstream profile. Promotion still requires:

1. typed stream syntax and native block-player integration for the remaining
   MAF lifetimes;
2. independent Python/native vectors for every promoted operation sequence;
3. complete R-118 evaluation on the three full references and all sixteen
   heterogeneous classes;
4. complete-byte, objective, perceptual, robustness, resource, and listening
   evidence against the admitted Resonith fallback and current Opus anchor.
