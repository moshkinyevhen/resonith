# Whole-Track Self-Supervised Causal Foundry

Status: **R-182 ACCEPTED ARCHITECTURE / IMPLEMENTATION IN PROGRESS**.

## Purpose

The Foundry learns the smallest anonymous causal explanation of each input
recording. It does not classify speech, instruments, notes, or environments.
It learns reusable waveform memory and the laws that carry that memory through
the complete timeline and channel field.

The released decoder is not trained. File-specific analysis is compiled into a
small bounded integer program plus one final Truth.

## Signal program

For output channel \(c\):

\[
x_c[n]=
\sum_s Route_{c,s}(n)
\left(
  Resonator_s(State_s,Excitation_s)[n]
  +Transient_s[n]
  +Stochastic_s[n]
\right)
+Truth_c[n].
\]

One anonymous point cause owns a vector partial state:

\[
\begin{aligned}
f_{s,k}(n)&=k f_{s,0}(n)+\Delta f_{s,k}(n),\\
z_{s,k}(n)&=A_{s,k}(n)e^{j\phi_{s,k}(n)},\\
Shape_s(n)&=\{z_{s,k}(n), Resonator_s(n), Envelope_s(n)\}.
\end{aligned}
\]

This represents a changing harmonic or inharmonic shape, not one stationary
frequency. Independent transient, stochastic, and route lanes prevent the
coherent state from paying for attacks, noise, reverberation, or channel
interference that have cheaper explanations.

## What is learned from the file

- arbitrary-origin, multi-resolution partial tracks with exact complex phase;
- slowly changing vector waveform shape and bounded detuning;
- excitation and persistent resonator/filter state;
- immutable leaf Basis and acyclic CompoundBasis memory;
- returns of an existing cause after gaps;
- sparse event and transformation grammars over the whole timeline;
- cross-channel delay, gain, polarity, phase, decay, and shared route laws;
- transient and stochastic distributions where literal waveform reuse loses;
- one mixture-domain Truth after the independently decoded sum.

The learned fields are anonymous. A field may combine or split physical
instruments if that produces the shorter exact decoded explanation.

## Training algorithm

### 1. Phase-preserving observation

Analyze the original PCM and the current decoder-domain residual on overlapping
scales. Windows and GPU tiles overlap and never constrain event boundaries.
Direct long candidates remain available even after a useful micro-pattern is
found.

The coherent analysis does not begin by guessing one or several fundamental
frequencies. It first measures anonymous complex spectral partials at sub-bin
frequency, amplitude, phase, and channel-route coordinates. A whole-track
continuation graph links them through crossings, gaps, births, and deaths.
Additive first-order costs use exact min-cost flow; higher-order shared laws use
bounded deterministic search.

Every selected partial path remains an independent candidate. Paths are grouped
under a harmonic, bounded-inharmonic, common-modulation, common-envelope,
resonator, motif, or route law only when that grouping reduces the actual
complete description. This prevents an incorrect fundamental hypothesis from
defining source identity.

### 2. File-specific initialization

Deterministic DSP creates the mandatory candidate union. Optional local neural
models or cloud AI may initialize boundaries and parameters or add proposals.
They cannot remove deterministic candidates or decide the bitstream.

### 3. Alternating system identification

Each generation performs deterministic edits:

1. quantize and re-estimate trajectory, partial, resonator, envelope, and route
   parameters against the actual decoder;
2. add or remove a causal column;
3. split or merge lifetimes;
4. link separated events under a gapped law or unlink a losing law;
5. grow or deduplicate leaf and CompoundBasis memory;
6. share or separate channel routes;
7. pack, decode, add one final Truth, and measure complete bytes and quality.

Before each grouping edit, the Foundry compares:

- independent complex-partial trajectories;
- a shared cause law plus per-partial corrections;
- a direct immutable Basis or motif;
- the corresponding transient, stochastic, or Truth alternative.

Phase is integrated from frequency inside a trajectory. Sparse phase
innovations or a restart are charged only when continuity loses. Cross-channel
phase first competes as a delay/transfer law and falls back to independent
channel phase when that is cheaper.

Small column sets use exact subset enumeration. Large sets use reproducible
column generation and add/remove/swap/split/merge beam search. Every run records
its finite hypothesis manifest and resource limits.

### 4. Admission and stopping

An edit is retained only if it adds a new complete rate/quality/resource Pareto
point. A structure that saves less final Truth than it costs in program,
events, routes, and checkpoints is rejected.

Training stops after a full pass without a frontier edit or at an explicitly
reported Foundry resource limit. The direct-Truth incumbent is always present.

## Why this is not waveform memorization

A per-file model may fit every sample, but every quantized parameter and Basis
sample is counted in the file. Moving PCM into a large learned weight array
does not reduce the objective. Only a law reused enough times to repay its
description can win.

An unrestricted neural function is therefore an encoder oracle, not the
bitstream. Useful learned behavior must be distilled into the bounded integer
ISA or paid as immutable Basis memory.

## Limits

- A mixture does not uniquely identify its physical source tracks. Resonith
  seeks the shortest decoded factorization, not a claim about the real world.
- Incompressible innovation exists; no lossless codec can shrink every input.
- Unrestricted sparse program selection is NP-hard. Completeness is claimed
  only for the published finite exact subproblems.
- Long files can amortize memory better than short files. The encoder therefore
  preserves duration-specific Pareto points rather than forcing one mode.

## First executable gate

1. recover crossing, gapped, harmonic, inharmonic, and channel-routed complex
   partial paths on known synthetic mixtures without source labels;
2. compile the vector-partial predictor into the existing native bounded DSP;
3. integrate it as an exclusive coherent owner in the R-179 global program;
4. train deterministic whole-track configurations with actual-byte coordinate
   search and independent decode;
5. run at least 120 seconds of Mozart first and freeze the long frontier;
6. run the short speech, dense-orchestra, and pink-noise diagnostics;
7. port scaling proposal and fit kernels to C++23/CUDA without reducing the
   declared candidate union;
8. run R-118 and the maximum-effort official Opus frontier before any general
   compression claim.

## Evidence accounting

Every row reports:

- input and decoded hashes;
- learned Basis, state, event, route, checkpoint, and Truth bytes;
- complete file bytes and wall time;
- model and residual energy only as diagnostics;
- waveform, spectral, log-mel, harmonic, and applicable intelligibility
  metrics from actual decoder PCM;
- exact/beam search manifest, stopping reason, and fallback status.

Primary sources are recorded in [REFERENCES.md](REFERENCES.md). The canonical
decision is [R-182](06_DECISION_LOG.md#r-182--whole-track-self-supervised-causal-foundry).
