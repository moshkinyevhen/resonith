# R-103 Active-Band Selection Fast Gate

Date: 2026-07-27  
Status: **MEASURED / FAST GATE FAILED**

R-103 tested an encoder-only coefficient selector. It reserved one nonzero
peak in each lapped band within 40 dB of a frame peak, then spent the remaining
unchanged coefficient budget by the existing squared-energy ranking. The
candidate changed no bitstream syntax or decoder operation.

## Results

| Reference | Selector | Complete LPF1 bytes | SNR | STOI | ESTOI | Log-mel RMSE |
|---|---|---:|---:|---:|---:|---:|
| Speech | Energy baseline | 17,744 | 19.619 dB | 0.94989 | 0.90297 | 3.8249 |
| Speech | Active band | 18,012 | 16.973 dB | 0.94815 | 0.91217 | 2.3883 |
| Emotional piano | Energy baseline | 121,821 | 40.433 dB | — | — | 1.05526 |
| Emotional piano | Active band | 121,830 | 40.433 dB | — | — | 1.05457 |

The speech candidate improved ESTOI and log-mel error but was 1.51% larger,
lost 2.65 dB SNR, and slightly reduced STOI. It failed the declared fast gate.
The complete Mozart promotion run was therefore not performed.

The Opus files recorded in the machine report are contextual anchors, not a
new equal-byte verdict: the fast gate terminated against the preceding
Resonith selector before a current-decoder Opus rematch was warranted. The
public equal-byte Opus comparison remains the
[0.1.0-alpha.1 benchmark](PUBLIC_BENCHMARK_2026-07-26.md).

## Reproducibility

- Machine report:
  [`active_band_selection_2026-07-27.json`](../../experiments/results/active_band_selection_2026-07-27.json)
- Decision and thresholds: R-103 in
  [`06_DECISION_LOG.md`](../06_DECISION_LOG.md)
- Actual decoded WAV files were measured; objective diagnostics are not a
  substitute for controlled listening.

## Verdict

Do not promote active-band reservation into the default encoder. The result
shows that broad log-domain detail can be recovered, but reallocating the same
transform coefficients is not enough. The next speech experiment must remove
predictable voiced energy before coding Innovation, using a bounded
pitch/predictive Basis with a complete fallback.
