# R-104 Voiced Long-Term Predictor Fast Gate

Date: 2026-07-27  
Status: **MEASURED / SPEECH FAST GATE FAILED**

R-104 tested a bounded causal speech predictor. Every fixed interval carried a
pitch lag and Q7 gain; an ordinary lapped stream coded the prediction
Innovation. The research decoder reconstructed through one signed integer
multiply-accumulate per sample.

## Equal-size result

| Codec path | Complete bytes | SNR | STOI | ESTOI | Log-mel RMSE |
|---|---:|---:|---:|---:|---:|
| Resonith energy baseline | 17,744 | 19.619 dB | 0.94989 | 0.90297 | 3.8249 |
| R-104 voiced predictor | 17,757 | 17.321 dB | 0.92744 | 0.87187 | 2.9411 |
| Public Opus anchor | 17,942 | 9.297 dB | 0.99317 | 0.98805 | 0.6012 |

The candidate was within 0.073% of the Resonith baseline and improved broad
log-mel detail by 23.1%. It nevertheless lost 2.30 dB SNR and reduced both
speech-intelligibility diagnostics. The declared gate failed.

The predictor marked 51.1% of 1,024-sample intervals voiced and used 62
coefficients per transform frame. Three other state lengths showed the same
tradeoff. The experiment took 151.2 seconds and evaluated 84 complete
candidate encode/decode paths.

## Interpretation

The result rejects a conventional recursive long-term predictor as a
Resonith Main primitive in this form. Prediction error is added to already
lossy reconstructed history, so it propagates along the pitch recurrence.
That recovers some quiet spectral structure but damages waveform accuracy and
intelligibility.

The next candidate should render a bounded excitation/harmonic Basis from an
absolute phase law. Such a Basis does not recursively reference degraded
samples and therefore cannot accumulate the same error.

## Reproducibility

- Machine report:
  [`voiced_predictive_2026-07-27.json`](../../experiments/results/voiced_predictive_2026-07-27.json)
- Research parser and decoder:
  [`voiced_predictive_oracle.py`](../../reference/maf_p0/voiced_predictive_oracle.py)
- Gate runner:
  [`voiced_predictive_gate.py`](../../experiments/voiced_predictive_gate.py)

No VPR1 syntax or decoder operation is promoted by this result.
