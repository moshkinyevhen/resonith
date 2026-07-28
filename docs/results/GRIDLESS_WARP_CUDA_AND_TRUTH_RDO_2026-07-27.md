# Gridless warp CUDA and exact Truth-RDO diagnostic

Date: 2026-07-27  
Decisions: R-150, R-155, R-156, R-157  
Status: constructive architecture evidence; not an Opus or real-audio claim

## Implemented path

The diagnostic closes one complete lossless path:

```text
arbitrary interval origins
    -> complete declared fractional warp lattice
    -> C++23/CUDA fixed-point evaluation
    -> exact global dictionary-activation chart
    -> native MFT1 type-8 decode
    -> whole-signal exact Truth correction
    -> independent Truth fallback
```

The warp lattice includes ordered unequal Basis/target pairs, circular
fractional phase, forward and reverse traversal, bounded constant or linear
pitch-time step, and signed constant or linear gain. Python declares batches
and consumes records; it does not execute the candidate DSP.

## CPU/CUDA parity

The native conformance signal contains a known fractional source position,
non-unity initial pitch-time step, linear end step, and signed gain.

| Measurement | Result |
|---|---:|
| Device | NVIDIA GeForce RTX 2080 SUPER |
| Compute capability | 7.5 |
| NVRTC | 13.3 |
| Declared candidates | 6,912 |
| Executed candidates | 6,912 |
| Unequal tile sizes | 4,099 + 2,813 |
| CPU/GPU result equality | exact |
| Known warp correction SSE | 0 |

Every 48-byte result record matched for Basis and target indices, source
position, start/end step, start/end gain, flags, squared error, and target
energy.

## Complete-byte lossless construction

The second signal places eight transformed instances of one 64-sample Basis at
absolute positions not defined by a transform or CUDA block boundary.

| Measurement | Result |
|---|---:|
| Declared candidates | 7,168 |
| Executed candidates | 7,168 |
| Exact eligible relationships | 56 |
| Global chart states | 86,017 |
| Selected Basis | 1 |
| Selected instances | 8 |
| Native MFT1 bytes | 592 |
| Exact structured Truth bytes | 112 |
| Structured complete bytes | 704 |
| Independent lossless Truth | 1,156 |
| Saving against that Truth anchor | 39.10% |
| Reconstructed PCM | bit-exact |

The final complete-byte comparison, not the proposal fit, admitted the
structured representation. The same code retains independent Truth whenever
the Basis, transform records, or correction cost more.

## Validation

- Native C++23 CUDA/C ABI test passes on RTX 2080 Super.
- Python 3.14.6 CUDA/Core integration passes.
- The focused R-156/R-157, hierarchy, and typed-MAF union passes 30 tests.
- The decoder remains the portable bounded integer Core; CUDA and Python are
  encoder-side Foundry dependencies only.

## Remaining admission gates

This diagnostic intentionally contains repeated structure. It proves the
mechanism and safe fallback, not average compression. Promotion still requires
the complete R-118 union, matched official Opus anchors, quality-frontier
analysis, Orkela playback, mobile compile gates, versioning, hashes, and a
public release.
