# Causal Sequence Atlas R-171 through R-173

Date: 2026-07-27  
Status: **Real PCM / Fast sequence-discovery diagnostic / Exact reconstruction**

This report measures causal-event discovery. It does **not** measure a complete
Resonith stream, perceptual quality, or compression against Opus. Pattern
counts are suffix-automaton end-position equivalence families and may overlap;
they are neither semantic sound classes nor counts of distinct audible motifs.
Input names such as Mozart, female speech, dense orchestra, and pink noise
identify separate benchmark files only. The analyzer does not infer speech,
an instrument, or any other named source inside the Mozart input.

## Inputs and order

The run followed the mandatory duration order:

1. first continuous 120 seconds of the pinned Mozart input;
2. freeze the long result;
3. 12-second female speech, dense orchestra, and pink-noise diagnostics.

Every row used real PCM16 and reproduced the input PCM hash exactly after
rendering the analytic lanes plus one final Truth correction.

## R-171 harmonic-event atlas

R-171 first indexed phase-aware coherent-partial observations. It proved that
the Mozart input contains reusable transformed causal sequences, but it did not
represent every causal lane.

| Input | Duration | Harmonic events | Repeated classes | Maximum events | Maximum occurrences | Wall time |
|---|---:|---:|---:|---:|---:|---:|
| Mozart | 120 s | 20,849 | 681 | 4 | 6 | 38.693 s |
| Female speech | 12 s | 1,216 | 11 | 3 | 2 | 2.549 s |
| Dense orchestra | 12 s | 8 | 0 | — | — | 2.747 s |
| Pink noise | 12 s | 1,779 | 0 | — | — | 3.341 s |

The Mozart result contains 680 bounded-second-difference classes and one
constant-offset/first-difference class. This is constructive evidence against
the claim that the long music input contains no transformed repetition.

## R-172 failed all-coordinate conjunction

R-172 exposed harmonic, deterministic-inharmonic, transient, and stochastic
lane events, but the first implementation required every coordinate of an
event to repeat jointly.

| Input | All-lane events | Joint classes | Wall time |
|---|---:|---:|---:|
| Mozart | 64,501 | 0 | 48.782 s |
| Female speech | 5,037 | 2 | 3.174 s |
| Dense orchestra | 3,837 | 0 | 3.302 s |
| Pink noise | 5,606 | 0 | 4.207 s |

This was rejected as a search construction, not interpreted as absence of
structure. A difference in stochastic realization phase, route, or envelope
could erase a valid pitch, gain, timing, or resonator repetition.

## R-173 factorized-law atlas

R-173 independently indexes timing, pitch, phase, gain, envelope, resonator,
and route laws inside every causal lane. Stochastic realization phase is not
predictive state.

| Input | All-lane events | Factorized candidate families | Joint candidate families | Longest covered law | Highest occurrence family | Wall time |
|---|---:|---:|---:|---:|---:|---:|
| Mozart | 64,501 | 258,664 | 0 | 1,117 events | 19,178 | 69.576 s |
| Female speech | 5,037 | 22,875 | 2 | 226 events | 1,675 | 4.361 s |
| Dense orchestra | 3,837 | 12,238 | 0 | 97 events | 1,634 | 4.221 s |
| Pink noise | 5,606 | 22,511 | 0 | 95 events | 1,624 | 5.531 s |

The large counts include constant-hop timing runs and overlapping
suffix-automaton length intervals. They prove coverage, not compression.
Non-timing Mozart laws also produced substantial candidate sets, including
gain, envelope, resonator, pitch, phase, and route classes. For example,
coherent-harmonic gain reached 14-event classes, while stochastic envelope
reached 10-event classes.

## Decision

1. Keep separate causal lanes and one final mixture-domain Truth.
2. Keep exact factorized-law discovery; do not restore the rejected
   all-coordinate admission requirement.
3. Feed the discovered laws to a bounded synchronized `CompoundBasis` grammar.
4. Admit a law only when dictionary, events, parameters, entropy,
   checkpoints, render cost, and final Truth beat the expanded ledger or create
   an eligible matched-rate quality point.
5. Count no pattern as a codec win until actual decoder-produced files pass the
   long-first R-118 and maximum-effort Opus gates.

## Machine evidence

- [R-171 harmonic atlas JSON](../../experiments/results/causal_sequence_atlas_r171_2026-07-27.json)
- [R-172 rejected joint atlas JSON](../../experiments/results/all_lane_causal_sequence_atlas_r172_2026-07-27.json)
- [R-173 factorized-law atlas JSON](../../experiments/results/factorized_law_causal_sequence_atlas_r173_2026-07-27.json)
