# Causal Law and Event Ledgers R-174/R-175

Date: 2026-07-27  
Status: **Real PCM / Exact ledger-byte diagnostic**

These results measure anonymous causal metadata only. They exclude acoustic
Basis payloads, bounded synthesis, checkpoints, final Truth bytes, and a
complete `.resonith` container. They are not full-codec or Opus comparisons.
Corpus names identify separate input files; no semantic source class is used
or transmitted.

## Test order

1. first continuous 120 seconds of the pinned Mozart input;
2. freeze the long result;
3. 12-second female-speech, dense-orchestra, and pink-noise files.

Every selected ledger passed exact decoder round-trip. The analytic causal
lanes plus one final Truth reproduced every evaluated PCM hash exactly.

## R-174 independent factorized-law ledgers

R-174 compared a literal token stream, immutable token dictionary, and bounded
acyclic pair grammar for each factorized law.

| Input | Literal ledgers | Selected ledgers | Delta | Grammar wall time |
|---|---:|---:|---:|---:|
| Mozart, 120 s | 611,298 B | 514,946 B | -15.761871% | 11.907 s |
| Female speech, 12 s | 41,466 B | 37,080 B | -10.577340% | 0.911 s |
| Dense orchestra, 12 s | 46,392 B | 43,574 B | -6.074323% | 0.745 s |
| Pink noise, 12 s | 58,155 B | 51,220 B | -11.925028% | 1.928 s |

On Mozart, immutable dictionaries selected 16 law ledgers, direct raw fallback
selected nine, and hierarchical grammar selected only
`coherent_harmonic/timing` and `sparse_transient/timing`. This is the desired
anti-complexity behavior: a macro is retained only when its actual payload
beats the simpler form.

## R-175 one timeline per causal lane

R-175 removed repeated clocks. One ordered event timeline is shared by pitch,
phase, gain, envelope, resonator, and route columns inside each anonymous lane.
Zero/default columns and identity mono routes are omitted.

| Input | Complete row ledgers | Selected row/column ledgers | Delta | Ledger wall time |
|---|---:|---:|---:|---:|
| Mozart, 120 s | 602,415 B | 471,002 B | -21.814364% | 8.588 s |
| Female speech, 12 s | 37,297 B | 34,274 B | -8.105210% | 0.501 s |
| Dense orchestra, 12 s | 34,409 B | 31,001 B | -9.904385% | 0.664 s |
| Pink noise, 12 s | 46,532 B | 39,826 B | -14.411588% | 1.414 s |

All four Mozart lanes selected shared-time columns:

| Anonymous law family | Events | Row | Column |
|---|---:|---:|---:|
| Coherent harmonic | 20,849 | 204,809 B | 157,053 B |
| Deterministic inharmonic | 21,151 | 209,116 B | 163,349 B |
| Sparse transient | 1,350 | 14,639 B | 13,263 B |
| Stochastic law | 21,151 | 173,851 B | 137,337 B |

Short transient ledgers and the eight-event dense-orchestra harmonic ledger
selected row fallback because independent column headers cost more. No
factorized form is forced.

## Interpretation

The measured improvement validates two narrow claims:

1. the discovered causal state is substantially cheaper when immutable
   dictionaries and bounded hierarchical reuse compete by actual bytes;
2. independent law search must not imply independent timeline transmission.

It does not yet show that causal metadata plus audio Truth beats the current
Resonith or Opus stream. The next gate integrates the selected ledger with
bounded rendering and prices the one final mixture-domain Truth.

## Machine evidence

- [R-174 token-ledger JSON](../../experiments/results/causal_law_grammar_r174_2026-07-27.json)
- [R-175 shared-timeline event-ledger JSON](../../experiments/results/causal_event_ledger_r175_2026-07-27.json)

