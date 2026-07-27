# MAF rate-distortion frontier

Date: 2026-07-27
Status: **NORMATIVE-DRAFT METHOD / TARGETS AND HYPOTHESES**

## 1. There is no single theoretical compression limit

A rate-distortion limit exists only after defining:

- the source distribution and channel layout;
- sample rate and bandwidth;
- latency, packet-loss, seek, and checkpoint contract;
- decoder model, memory, compute, and package cost;
- distortion contract.

Resonith therefore maintains three disjoint frontiers:

1. **Exact PCM frontier** — bit-exact reconstruction. The relevant comparison
   is lossless coding, and generative detail contributes zero admissible
   saving.
2. **Objective Truth frontier** — bounded deterministic lossy reconstruction
   under declared waveform, spectral, intelligibility, transient, spatial,
   and listening constraints.
3. **Perceptual frontier** — MUSHRA/ABX non-inferiority under a declared
   listener and use-case distribution. Optional generative detail is reported
   separately and never becomes Truth state.

No result may move between these frontiers by changing the quality definition
after encoding.

## 2. Pinned speech checkpoint

The current complete-byte anchor is:

| Stream | Complete bytes | Status |
|---|---:|---|
| official Opus 1.6.1 anchor | 17,942 | **MEASURED** |
| admitted LPS6 candidate | 17,904 | **MEASURED** |
| R-119 Q4 PVQ fast-gate candidate | 18,376 | **MEASURED** |
| 40% saving checkpoint | 10,765 maximum | **TARGET** |

R-119's selected logical fields explain why entropy cleanup alone cannot reach
the checkpoint:

| Q4 PVQ field | Bits | Approximate bytes |
|---|---:|---:|
| shape | 82,169 | 10,271 |
| gain | 39,367 | 4,921 |
| pulse counts | 23,566 | 2,946 |

The shape field alone almost consumes the complete checkpoint. The dominant
requirement is therefore to replace repeated shape with long-lived acoustic
state, not merely to pack the same vectors more tightly.

## 3. Unified target budget

The first feasibility budget for the pinned speech item is:

| Joint field | Maximum target |
|---|---:|
| state and primary-mode events | 0.60 KiB |
| filter/envelope state | 1.20 KiB |
| coherent excitation and trajectories | 3.00 KiB |
| stochastic plus transient state | 1.80 KiB |
| remaining Truth | 3.70 KiB |
| container and checkpoints | 0.45 KiB |
| **complete target** | **10.75 KiB** |

These numbers are **TARGETS**, not measurements, and are intentionally tighter
than isolated current fields. They are a stop/go ledger: if one field exceeds
its allowance and no other field saves the difference, the 40% checkpoint is
mathematically missed.

## 4. Mechanisms and useful ceilings

The following ranges are engineering hypotheses for structured content at
matched perceived quality. They are conditional shares of the current Opus
rate, not independently additive savings:

| Mechanism | Conditional rate-removal opportunity | Principal failure |
|---|---:|---|
| band-local single-primary RDO | 5–20% | signalling and short lifetimes |
| continuous source-filter state | 15–55% on voiced speech; 0–10% on dense music | unvoiced transitions and identity drift |
| state/mode persistence | 5–30% | state mutations may cost more than fresh coding |
| stochastic field | 10–45% on noise-like bands; near 0% on deterministic tones | waveform metrics reject a different realization |
| transient path | 3–15% on attack-heavy material | onset overhead and temporal smearing |
| cached immutable Basis and motifs | 5–35% on repeated sources; near 0% on short/noise input | correction and package cost |
| joint-channel/spatial reuse | 10–45% on correlated multichannel material | decorrelated ambience |
| shared conditional entropy | 3–15% after factorization | little redundancy remains |

Because the mechanisms interact, the project does not sum the right column.
It encodes one stream and publishes disable-one ablations.

## 5. Empirical frontier targets

The current research evidence supports these planning bands, not achieved
claims:

| Content and contract | Plausible Resonith target versus Opus | Status |
|---|---:|---|
| structured clean speech, deterministic Core | 35–65% smaller | **HYPOTHESIS** |
| solo/chamber or repeating structured music | 30–60% smaller | **HYPOTHESIS** |
| dense mixed music | 15–40% smaller | **HYPOTHESIS** |
| correlated stereo/immersive persistent emitters | 25–55% smaller | **HYPOTHESIS** |
| entropy-like noise, exact realization important | −5% to 15% smaller | **HYPOTHESIS** |
| perceptual neural detail, separately labelled | 70–90% smaller on supported domains | **RESEARCH HYPOTHESIS** |

The upper speech and perceptual ranges are not arbitrary physical limits.
Published neural systems demonstrate that much lower subjective speech/audio
rates are possible under different model and evaluation contracts. Resonith
must reproduce comparable evidence before using those rates in a claim.

## 6. Admission experiment

Every unified MAF revision publishes:

1. the actual complete candidate and preceding/Opus streams;
2. a mode/state byte ledger;
3. decoded PCM from each actual decoder;
4. the complete R-118 19-item table;
5. dedicated transient, stochastic, stereo, loss, seek, resource, and mobile
   gates affected by the revision;
6. a disable-one ablation for every active representation;
7. MUSHRA/ABX evidence before claiming perceptual non-inferiority.

The frontier for each item is the smallest complete Resonith stream that passes
the same declared quality/resource constraints as its anchor. A file-level
fallback is valid engineering but contributes no candidate saving.

## 7. R-120 speech diagnostic

The first unified implementation establishes the following measured points.
They are one-item fast diagnostics and cannot promote a codec version:

| Candidate | Complete bytes | STOI | ESTOI | Log-mel RMSE | Result |
|---|---:|---:|---:|---:|---|
| official Opus 1.6.1 | 17,942 | 0.993172 | 0.988046 | 0.601168 | anchor |
| MFC1 gain memory plus PVQ-default map | 19,277 | 0.979699 | 0.954469 | 1.117839 | rejected versus Opus |
| SFT1/EPV1 byte-checkpoint point | 10,294 | 0.878153 | 0.795882 | 1.313313 | rejected on quality |
| SFT1/EPV1 closed-loop adaptive point | 12,548 | 0.908976 | 0.846112 | 1.190511 | rejected on quality |

The 10,765-byte target is therefore feasible as a serialized rate but not at
the required quality with the current scalar pitch and sparse excitation
model. The measured bottleneck is no longer container or dictionary overhead:
the adaptive point changes pitch state in 1,134 of 1,464 subframes and its
fixed codebook cannot preserve the remaining excitation with eight pulses per
64 samples. A 40% claim remains open, not achieved or disproved.
