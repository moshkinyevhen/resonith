# R-108 Corrected PVQ Envelope Fast Gate

Date: 2026-07-27
Status: **failed as a universal base; retained for band-local RDO**

## Correction

The first PVE1 encoder proportionally rounded coefficient magnitudes and used
the unprojected source norm as gain. That did not minimize error for the
decoded integer direction. The corrected compiler performs a deterministic
greedy squared-correlation-per-energy pulse search and then transmits the
projection-optimal gain. The decoder syntax is unchanged.

## Measured result

| Reference | Candidate bytes | LPS5 bytes | Candidate SNR | LPS5 SNR | Candidate log-mel | LPS5 log-mel |
|---|---:|---:|---:|---:|---:|---:|
| Speech | 18,580 | 17,924 | 12.134 dB | 19.605 dB | 1.465 | 3.690 |
| Sustained sine | 23,926 | 83,061 | 36.103 dB | 37.829 dB | 2.035 | 0.854 |

Speech STOI/ESTOI were 0.961999/0.928951 for corrected PVE1 versus
0.953579/0.905907 for LPS5. The corrected PVQ direction therefore preserves
useful speech-envelope structure, but its Truth reconstruction loses
7.471 dB SNR while using 656 more bytes.

The sine result demonstrates the opposite trade: a 71.2% smaller stream, but
lower SNR and substantially worse log-mel error. It is not an equal-quality
win.

## Decision

Pure PVE1 does not replace sparse TruthInnovation. Proportional and corrected
greedy PVQ remain optional band-local encoder candidates. PVE2 may combine
them with sparse exact innovation, but no new decoder opcode is promoted until
complete-stream RDO beats the existing path on the mandatory and heterogeneous
gates.

Machine-readable evidence:
[`pvq_envelope_greedy_projection_2026-07-27.json`](../../experiments/results/pvq_envelope_greedy_projection_2026-07-27.json).
