# R-105 Nonrecursive Harmonic Basis Fast Gate

Date: 2026-07-27  
Status: **MEASURED / SPEECH FAST GATE FAILED**

R-105 replaced recursive history prediction with a fixed-ROM harmonic Basis.
Each active interval carried a pitch lag and two, four, or six signed
sine/cosine amplitude pairs. The decoder rendered absolute local phase and
added an ordinary lapped Innovation stream.

## Final sparse-envelope result

| Codec path | Complete bytes | SNR | STOI | ESTOI | Log-mel RMSE |
|---|---:|---:|---:|---:|---:|
| Resonith energy baseline | 17,744 | 19.619 dB | 0.94989 | 0.90297 | 3.8249 |
| R-105 harmonic Basis | 17,825 | 19.534 dB | 0.94855 | 0.90257 | 3.7157 |
| Public Opus anchor | 17,942 | 9.297 dB | 0.99317 | 0.98805 | 0.6012 |

The selected stream was within 0.456% of the baseline, lost only 0.085 dB
SNR, and improved log-mel error by 2.86%. It still slightly reduced both STOI
and ESTOI, so the declared gate failed.

The winner used two harmonics, 4,096-sample intervals, the unchanged 64
transform coefficients per frame, and active Basis data in 39.1% of
intervals. Sparse event transport and signed 12-bit coefficient packing
reduced the complete Basis envelope from 309 to 114 bytes.

## Interpretation

The nonrecursive design avoided the error amplification measured in R-104 and
came close to the transform anchor. Static local pitch and phase still restart
at interval boundaries. Shorter intervals track voice changes better in the
log spectrum but introduce larger intelligibility losses; adding harmonics
does not fix the discontinuity.

The next oracle should carry continuous pitch, phase, and amplitude
trajectories across voiced regions, with sparse changes and explicit
transient boundaries. No HBR1 syntax is promoted by this result.

## Reproducibility

- Machine report:
  [`harmonic_basis_2026-07-27.json`](../../experiments/results/harmonic_basis_2026-07-27.json)
- Research parser and decoder:
  [`harmonic_basis_oracle.py`](../../reference/maf_p0/harmonic_basis_oracle.py)
- Gate runner:
  [`harmonic_basis_gate.py`](../../experiments/harmonic_basis_gate.py)

The final gate evaluated nine architecture combinations and their complete
byte-matched transform budgets in 252.0 seconds.
