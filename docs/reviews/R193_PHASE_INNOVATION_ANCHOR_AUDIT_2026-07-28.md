# R-193 Phase-Innovation Anchor Audit

Date: 2026-07-28  
Status: independent red-team GO for an evidence gate; NO-GO for syntax

## Question

Should Resonith replace repeated short-time phase estimates with persistent
complex-partial phase state and sparse objective correction events?

## Independent verdict

The mechanism deserves a controlled experiment after the current partial-graph
and predictor gates. It is not a new architecture by itself, and it does not
justify a bitstream opcode before complete-byte evidence.

The strongest potentially differentiating combination is:

```text
anonymous complex paths
+ bounded absolute integer phase laws
+ byte-priced phase innovations
+ shared cross-channel route laws
+ one final mixture-domain Truth
+ random-access and corruption checkpoints
```

## Prior-art correction

The motivating claim that current codecs estimate one block and forget phase
is too broad:

- [Opus](https://datatracker.ietf.org/doc/html/rfc6716) combines lapped MDCT,
  inter-frame energy prediction, CELT pitch filtering, and SILK long-term
  prediction. It does not expose one persistent sinusoidal object, but it does
  exploit temporal state and reconstructs local waveform phase through its
  coefficients and overlap.
- [FLAC](https://www.rfc-editor.org/rfc/rfc9639) is lossless. Its block
  predictor does not discard phase because the residual recovers the exact
  samples.
- [McAulay and Quatieri](https://www.ll.mit.edu/r-d/publications/audio-signal-processing-based-sinusoidal-analysissynthesis)
  track sinusoidal amplitude, frequency, and phase through births and deaths
  and use smooth phase functions for synthesis.
- [MPEG-4 HILN](https://heikopurnhagen.net/sigproc/diss-hp.pdf) used
  phase-continuous sinusoidal trajectories and interpolation. Persistence and
  phase continuity are therefore established prior art.
- Modern learned work can also model phase explicitly; for example,
  [APCodec](https://arxiv.org/abs/2402.10533) encodes amplitude and phase
  spectra in parallel.

Resonith must therefore prove an economic improvement from its bounded,
anonymous, Truth-corrected composition rather than claim invention of
continuous phase.

## Existing implementation versus the proposal

| Mechanism | Current state |
|---|---|
| Absolute integer phase/frequency trajectory and partition-independent render | Implemented in the trajectory core |
| Periodic Basis with absolute phase and finite lifetime | Implemented research/normative-draft infrastructure |
| Phase, phase-step, uncertainty, and endpoint-error observation evidence | Implemented in R-190/R-191 analysis |
| Phase-aware partial-path ranking | Implemented analyzer evidence only |
| Python columns named continuous and phase-locked | Implemented research candidates |
| Persistent synthesis from the audited multi-partial graph | Not implemented |
| Sparse phase-innovation events | Not implemented |
| Complete anchor/no-anchor native decoder RDO | Not implemented |
| Shared stereo route, checkpoints, and bounded packet-loss recovery | Not implemented |
| Long-real complete-byte advantage | Not measured |

The current Python `phase-locked` column is not the proposed mechanism. It
creates short `MafBasisWarpInstance` records at analysis cadence and supplies
an absolute source position for each instance. It therefore does not yet turn
dense phase signaling into sparse innovation.

## Accepted finite model

For partial \(k\):

\[
z_k[n] = a_k[n]e^{i\theta_k[n]},
\]

\[
\theta_k[n] =
\theta_{0,k}+\Phi_{\omega_k}(n)
+\sum_j\Delta_{k,j}G(n-\tau_{k,j})
\pmod {2^{32}}.
\]

- `Phi` is the absolute integral of a bounded integer frequency law.
- `Delta` is a transmitted quantized phase innovation.
- `G` is one fixed bounded causal correction ramp.
- Each event has explicit time, magnitude, duration, rate, memory, and
  dependency cost.
- A true discontinuity competes as split/rebirth plus deterministic crossfade.

The decoder does not recursively depend on every preceding sample. Origins and
checkpoints make state an absolute function of sample index, preserving
partition-independent render and bounded seek.

## Falsification risks

- Crossing partials can swap identity.
- Close tones produce beating that a single oscillator may chase incorrectly.
- Phase is weakly identified near zero amplitude.
- A real cosine has a gain-sign versus phase-plus-pi ambiguity.
- Window origin and overlapping components make a spectral-peak phase
  gauge-dependent rather than physically unique.
- Abrupt phase assignment creates a broadband transient.
- Independent channel anchors can destroy stereo delay and cancellation.
- A lost anchor can corrupt all future state without a checkpoint.
- Reverberation may require too many partials and anchors.
- Dense anchors can cost as much as ordinary transform Truth.

The graph must retain alternative crossings and independent paths until actual
decoder-domain RDO. Transients, stochastic material, and unresolved dense
fields keep their existing specialized or direct-Truth alternatives.

## Mandatory ablation

Run the same candidate lattice with:

1. direct Truth;
2. the preceding short harmonic/event predictor;
3. persistent amplitude/frequency knots without phase anchors;
4. denser frequency knots;
5. sparse phase-innovation anchors;
6. split/rebirth plus deterministic crossfade;
7. a free exact-phase oracle;
8. magnitude-only or randomized-phase negative control;
9. shared source phase plus route versus independent channel phases.

The free oracle tests whether the target contains enough compressible phase
structure before syntax engineering begins.

## Admission gates

- Kill syntax work unless the free exact-phase oracle reduces compressed final
  Truth by at least 10% in at least three long coherent classes.
- Anchor mode must beat no-anchor, dense-frequency-knot, and
  rebirth/crossfade alternatives by at least 3% complete bytes in at least two
  long real coherent classes at the declared quality floor.
- A stationary sinusoid and exactly representable linear chirp require no
  anchors after onset.
- A ten-minute bounded-vibrato case permits at most one anchor per second.
- Required adversarial cases include sub-resolution close tones, beating,
  crossing chirps, cancellation, onset/offset, noise, impulses, reverb,
  anti-phase stereo, and changing inter-channel delay.
- Random-access slices and every callback partition produce the same PCM as
  linear decode.
- Corruption propagation ends at a declared recovery checkpoint.
- Complete cost includes all IDs, state events, routes, entropy, checkpoints,
  decoder work/memory, and final Truth.
- Promotion requires the complete R-118 union, current maximum-effort Opus
  frontier, decoder output, objective metrics, and listening evidence.

## Final recommendation

Append this gate after the current last Orkela-coupled execution step. Reuse and
amend R-192 rather than creating a parallel predictor architecture. No public
syntax or compression claim is authorized by this review.
