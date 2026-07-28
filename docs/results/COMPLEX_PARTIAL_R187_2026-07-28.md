# R-187 Complex-Partial Analyzer Gate

Date: 2026-07-28  
Status: analyzer evidence only; no compression or Opus claim

## Result

The audited R-187/R-188/R-189 synthetic gate passes. The result does not
contain a predictor, normative stream, final Truth, or bitrate comparison.

| Counterexample | Measured result |
|---|---:|
| Clean 440.3 Hz frequency error | 0.114116 Hz |
| Clean-tone mean phase-continuation error | 0.010607 rad |
| First crossing chirp median frequency error | 0.317631 Hz |
| Second crossing chirp median frequency error | 0.283677 Hz |
| Weak-line relative level | -47.604225 dB |
| Weak protected-path median frequency error | 0.000006 Hz |
| White-noise canonical candidate pool | 1,140 |
| White-noise retained observations | 460 |
| White-noise candidates explicitly resource-pruned | 680 |
| Reproducible gate wall time | 25.262 s |

The frozen one-second chirp observation at frame 50 retains exactly one
canonical candidate near each planted 460 Hz and 940 Hz component. The old
453.1/459.6 and 940.2/953.1 band-boundary pairs are gone. On the reduced
half-second crossing gate, both planted trajectories survive the independent
top-K family union.

The weak 2 kHz line uses amplitude 50 against a 12,000-amplitude 440 Hz line.
It survives for 33 observations in the protected weak-line family even when
its phase confidence is unknown. Unknown phase is not charged in continuation
cost.

## Reproduction

```powershell
$env:PYTHONPATH='.;reference'
python experiments/complex_partial_r187_gate.py `
  --output experiments/results/complex_partial_r187_2026-07-28.json
```

The test union is:

```powershell
python -m pytest -q `
  tests/test_complex_partial_analyzer.py `
  tests/test_complex_partial_tracker.py
```

Result: 10 passed in 31.62 seconds.

## Evidence

- [Machine report](../../experiments/results/complex_partial_r187_2026-07-28.json)
- [Adversarial review](../reviews/R187_PARTIAL_PATH_UNION_AUDIT_2026-07-28.md)
- [Decision log](../06_DECISION_LOG.md)
- [Analyzer implementation](../../reference/maf_p0/complex_partial_analyzer.py)
- [Tracker implementation](../../reference/maf_p0/complex_partial_tracker.py)

## Remaining blocker

The current Python code is an independent research oracle and bounded
proposer. Native C++23/CUDA sparse-graph parity, a second adversarial audit,
decoder-domain synthesis, final Truth, actual complete bytes, long-first R-118
evidence, and maximum-effort Opus remain mandatory before any codec claim.
