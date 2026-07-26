# Encoder compiler Resonith

Status: pipeline - **ACCEPTED**; numerical parameters - **TARGET**.

## 1. Encoder understands music, decoder performs physics

Encoder MAY to use:

- pitch/onset/tempo/score transcription;
- source separation and emitter tracking;
- instrument, speaker and room recognition;
- long-context music/audio foundation model;
- global motif retrieval;
- differentiable analysis-by-synthesis;
- exhaustive beam/graph search.

The result of the analysis is not transmitted as mandatory semantics. Encoder
compiles hypotheses into `TIMBRE_BASIS`, atoms, parameter tracks and Innovation and
checks them with the same bit-exact decoder that the listener will receive.

## 2. Not a classifier switch, but a competition of candidates

Router offers top-K views for each source/time-frequency
region. Candidates MAY overlap and stack. Final function:

\[
\begin{aligned}
J={}&R_{\mathrm{total}}
+ \lambda D_{\mathrm{truth}}
+ \alpha D_{\mathrm{perceptual}}\\
&+\mu C_{\mathrm{decode}}
+ \nu M_{\mathrm{state}}
+ \rho L_{\mathrm{latency}}
+ \kappa P_{\mathrm{loss}}
+ \eta S_{\mathrm{switch}}.
\end{aligned}
\]

`R_total` includes basis, adapters, events, indexes, checkpoints, entropy
headers and FEC. Proxy is allowed only for shortlist; final RDO counts
actual bitstream.

An incorrect semantic hypothesis is safe: if the “violin” basis is not
paid off, exact RDO chooses lifting residual.

## 3. Analysis-by-synthesis pipeline

1. Normalize channel layout and sample timeline without losing the source.
2. Find onsets, periodic tracks, residual noise and long decay.
3. Construct source hypotheses without requiring perfect separation.
4. Find reusable timbre/excitation/room bases.
5. For each Basis, compare raw/lifting and CIBS latent+correction.
6. Offer atom tracks with absolute phase.
7. Offer transient and stochastic predictors.
8. Synthesize the candidate bit-exact Core decoder.
9. Code the remainder Innovation.
10. Perform full RDO and temporal dynamic programming.
11. Place checkpoints and packet-loss boundaries.

A source separation error is not a decoder error: it simply raises
Innovation and can make decomposition unprofitable.

## 4. Encoder profiles

### Live

- causal or small lookahead;
- bounded top-K;
- Realtime profile;
- low-delay lifting fallback;
- packet-loss-aware RDO.

### Studio

- full track/product;
- bidirectional analysis;
- global timbre and motif dictionary;
- accurate phase tracking through pauses and re-entry;
- beam search by sections.

### Foundry

- multi-hour/multi-day budget;
- ensemble neural teachers;
- global source/score/room hypothesis;
- Pareto search and distillation in Consumer/Studio router;
- the same bitstream and decoder.

## 5. Consumer practicality**TARGET:** the first encoder must be run on a regular PC without the required
clouds. The main working set is tiled by source hypotheses, frequency bands
and temporary sections; long-term bases are unloaded into RAM.

Audio is significantly lighter in size than video. GPU is useful for neural analysis
and batched RDO, but the Core prototype must have a CPU path. Productivity
will be measured separately for Live, Studio and Foundry; before implementation numerical
speeds are not declared as a fact.

## 6. How to avoid architectural jerks

The semantic spine is frozen:

```text
continuous timeline
immutable reusable basis
fixed update-time CIBS
absolute parameter tracks
RESET / SET / END
small integer DSP ISA
objective Innovation fallback
optional non-reference Perceptual Detail
```

New encoder models, quantizers and basis synthesizers are only allowed if
they are compiled into this spine. A new opcode is added only after:

1. oracle ablation;
2. net gain after full overhead;
3. decoder complexity audit;
4. conformance and corruption analysis;
5. evidence that the existing ISA does not express the mechanism intelligently.

## 7. Teacher–student moat

Foundry saves not only the winner, but also the Pareto-set:

- rejected basis families;
- atom lifetime and update decisions;
- bit value basis/reuse/innovation;
- phase/pitch tracking alternatives;
- packet and checkpoint decisions;
- uncertainty and reasons for fallback.

The compact router learns to offer top-K. Exact RDO retains the latest
word. The benefit is transferred to encoder/data, not to the private decoder.
