# Complete GPU Foundry and hierarchical grammar diagnostic

Date: 2026-07-27  
Decisions: R-149, R-150  
Status: architecture diagnostic; not an R-118, Opus, or codec claim

## Implemented search language

The first native Foundry backend exhaustively evaluates:

```text
all fixed-lattice blocks
    x all ordered unequal block pairs
    x all circular sample phases
    x signed constant/linear Q1.15 gain laws
```

The backend is a separate C++23 shared library. NVIDIA NVRTC 13.3 compiles the
kernel at runtime and the CUDA Driver API executes deterministic tiles on an
RTX 2080 Super (compute capability 7.5, 8,589,475,840 reported device bytes).
The Resonith decoder remains CPU-portable and has no CUDA dependency.

Former `maximum_bases * 4` seed budgets and 24/32-location probe exits were
removed. `maximum_bases` and `maximum_instances` constrain only the emitted
profile, after candidate evaluation.

## Exact parity gate

The native test enumerated four blocks as 384 exact candidates in uneven
73-candidate tiles. Clang 22.1.8 and GCC 16.1.0 builds both reported:

- 384/384 candidates executed;
- exact CPU/GPU equality for indices, phase, constant/linear gains, target
  energy, and integer squared error;
- recall of a known circular phase, negative gain, and zero-error transform;
- recall of a known linear gain state law;
- NVRTC 13.3 and compute capability 7.5.

An initial analytic gain fit missed an exact transform by one squared sample.
The gate exposed it and the implementation now evaluates the required fixed
Q1.15 neighbours before selecting a gain.

## Constructive complete-stream diagnostic

A generated 512-sample mono signal contained eight circularly shifted,
positive/negative gain instances of one 64-sample Basis.

| Measurement | Result |
|---|---:|
| Declared candidates | 3,584 |
| Executed candidates | 3,584 |
| Selected Basis | 1 |
| Selected instances | 8 |
| Independent Resonith Truth | 800 bytes |
| MFT1 Basis + exact Truth | 588 bytes |
| Lossless saving vs that Truth anchor | 26.50% |

The decoded PCM was exact. This is a favorable constructive signal and is not
evidence against Opus or on real audio.

## Real speech diagnostic

Input: pinned `ebu-female-speech-en.wav`, active mono analysis interval
starting at frame 61,440, 4,096 samples at the source rate
(0.0928798 seconds). One 64-sample scale was declared.

| Measurement | Result |
|---|---:|
| Declared candidates | 258,048 |
| Executed candidates | 258,048 |
| CUDA wall time | 0.4367 s |
| Fit-eligible ordered pairs | 305 |
| Candidate Basis / instances | 10 / 56 |
| Linear-gain instances | 43 |
| Raw PCM payload | 8,192 bytes |
| Independent Resonith Truth | 4,823 bytes |
| MFT1 prediction | 3,328 bytes |
| Exact Truth correction after MFT1 | 5,380 bytes |
| Forced Basis + exact Truth candidate | 8,708 bytes |
| Candidate delta | +80.55% |

The candidate reconstructed exact PCM but lost complete-byte RDO. A compliant
selector therefore retains the 4,823-byte Truth fallback. The result shows
that exhaustive phase/gain matching finds substantial speech relationships,
but the current flat dictionary and correction are not yet an economic speech
representation. Both paths are mathematically lossless: full waveform error
is zero. The MFT1 prediction alone, before exact correction, measured only
8.2421 dB SNR, 2,395.65-sample RMSE, and 16,994 maximum absolute error.

## Hierarchical anti-blindness gate

The R-150 oracle passed five bounded exact-chart cases:

1. a direct large span replaces already discovered micro-atoms;
2. a locally attractive merge is rejected when its one-time Basis cost makes
   the global path worse;
3. an existing CompoundBasis is reused without duplicate activation bytes;
4. identical phase/gain increment laws unify occurrences with different
   absolute initial states;
5. independent Truth wins when no merge is economic.

Direct candidates from original PCM and bottom-up compounds enter the same
chart. Discovery does not claim samples; only global complete cost assigns
ownership.

## Validation

- Clang 22.1.8 C++23: 15/15 native tests passed.
- GCC 16.1.0 C++23: 15/15 native tests passed.
- Python 3.14.6 plus native integrations: 230 tests passed, 4 optional
  external/device tests skipped.
- Strict CUDA Python bridge: 2/2 tests passed.
- Android NDK r29 ARM64 and x86-64 Core compile gates passed with the optional
  Foundry backend explicitly disabled; mobile decoding retains no CUDA/NVRTC
  dependency.

## Open work before a compression claim

- integrate the R-150 global chart into the emitted multiscale stream instead
  of using the current flat candidate construction;
- add exhaustive partial-band, pitch/time, short-filter, stochastic, overlap,
  and cross-channel transfer families;
- replace brute-force materialization with mathematically admissible
  lower-bound/index traversal that preserves 100% declared candidate recall;
- cache the compiled CUDA module and move correction entropy estimation and
  complete RDO into persistent GPU batches;
- run the full R-118 corpus and matched current Opus anchor. The present report
  makes no Opus or real-audio compression improvement claim.
