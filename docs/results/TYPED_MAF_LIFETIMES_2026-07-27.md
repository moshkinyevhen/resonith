# R-130 Typed MAF Lifetime Gate

Date: 2026-07-27  
Status: **DECODER/SYNTAX GATE PASSED; ENCODER EVIDENCE PENDING**  
Source revision:
`3d7dc4c1923a17716a56bc86582ceb0677e7b2bd`

## Scope

This gate implements prospective `MFT1`, the first executable typed stream
that keeps MAF source filters, stochastic fields, transients, and output mixes
alive over explicit sample lifetimes. It also makes R-129 boundary precision
unambiguous: provider timestamps are local-search centers only; the admitted
stream boundary must be an exact sample selected by decoder-in-loop RDO.

This result does not claim smaller files or higher quality than Opus. The
complete R-118 encoder comparison is the next admission gate.

## Executed vector

The canonical 32-frame stereo vector contains:

- one immutable stable order-two filter;
- one directly rendered counter-addressed stochastic emitter;
- one excitation-only stochastic field;
- one impulse-excited source-filter lifetime over frames `[0, 16)`;
- one stochastic-excited source-filter lifetime over frames `[16, 32)`;
- one four-sample transient at frame 8;
- one stereo mix lifetime covering the complete stream.

The decoder renders the same stream as `16 + 16` frames and as
`7 + 5 + 4 + 9 + 7` frames. PCM16 is bit-identical and non-zero. This proves
that an application callback boundary does not become an acoustic state
boundary.

## Security and transaction results

| Gate | Result |
|---|---|
| Exact header, payload, and CRC inspection | Pass |
| Canonical type and identifier order | Pass |
| Stable reflection-to-LPC preparation | Pass |
| Resolved stochastic/filter/emitter references | Pass |
| Non-overlapping source lifetimes | Pass |
| Contiguous complete mix coverage | Pass |
| Exact caller-owned persistent/scratch sizes | Pass |
| Truncated stream rejection | Pass |
| Checksum mutation rejection | Pass |
| Overlapping lifetime rejection | Pass |
| Underdeclared operation budget rejection | Pass |
| Output, cursor, and history unchanged on budget failure | Pass |
| End-of-stream zero-frame success | Pass |
| 20,003 deterministic hostile-input smoke calls | Pass |

## Local toolchain results

| Toolchain | Result |
|---|---|
| LLVM/Clang 22, strict C++23, Windows x64 | 14/14 native targets passed |
| GCC 16.1, strict C++23, Windows x64 | 14/14 native targets passed |
| C99 public-header compatibility | Passed under Clang and GCC |
| Android NDK r29, API 24, ARM64 | Complete static/shared/test build passed |
| Python 3.14 reference/native regression | 186 passed, 5 device/tool skips |
| R-129 sample-boundary validation | 9/9 passed |

The five Python skips are optional external-tool or physical-device gates on
the Windows host. They are not failures of `MFT1`.

## Artifact hashes

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Clang `resonith_maf_typed_test.exe` | 581,120 | `2214855a82979045e4193bdd5493662dc9a5575095797af532bc5ac8696910b2` |
| Clang `libresonith_core_shared.dll` | 642,048 | `cd620e3102e31af008f4f88346fe07a6809c16773a179f866a1189627d7b45af` |
| GCC `resonith_maf_typed_test.exe` | 665,284 | `661a24ceaa5e1dea503e2a3a56c60d4956b54d820e0895803bcaac390998fe46` |
| Android ARM64 `libresonith_core_shared.so` | 2,487,184 | `e07706a76145992b5285886d4c717d2f3a936e49eec2168a33cbcab1ea203c30` |

## GitHub evidence

The public Mobile Core workflow for the source revision completed
successfully as run
[`30259430787`](https://github.com/moshkinyevhen/resonith/actions/runs/30259430787).
The general
[`Tests` run 30259430766](https://github.com/moshkinyevhen/resonith/actions/runs/30259430766)
and
[`Lapped native benchmark` run 30259430752](https://github.com/moshkinyevhen/resonith/actions/runs/30259430752)
also completed successfully for the same source revision.

## Honest admission boundary

The MAF name is now backed by an executable lifetime state machine instead of
only transform research primitives. What remains unproved is whether the
encoder can replace enough Truth coefficients with these records to beat the
preceding Resonith candidate and byte-matched Opus at equal perceived quality.

The next step is not another decoder opcode. It is an exact candidate compiler:

1. generate source-filter, stochastic, transient, and mix lifetime candidates
   from local PCM and optional aligned semantic hints;
2. synthesize each candidate through this exact `MFT1` decoder;
3. code deterministic Truth for the remaining error;
4. compare complete bytes and decoded metrics against the unchanged Truth
   fallback;
5. run all 19 R-118 items and publish every win, fallback, and loss.
