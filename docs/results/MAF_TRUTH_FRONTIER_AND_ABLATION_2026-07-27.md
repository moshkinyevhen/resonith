# R-136–R-138 MAF Truth Frontier and Family Ablation

Date: 2026-07-27  
Status: **RESEARCH GATE; OPTIMIZED TRUTH FOUND, MAF NOT ADMITTED**  
Source revision:
`b86fdadc501c57c7fe635e6ad9bff1da1e5bad17`

## Trigger

The complete R-118 gate found one large MAF rate opportunity on the 12-second
EBU electronic-tune item: 27,318 versus 86,387 bytes. It was not admissible
because log-mel and multiresolution STFT quality regressed. These experiments
separate three possible causes:

1. too few Truth coefficients;
2. a harmful full-band representation family;
3. an over-budget preceding ordinary Truth point.

The preceding reference has:

- 86,387 complete bytes;
- 36.181 dB SNR;
- 0.4593 log-mel RMSE;
- official byte-matched Opus anchor: 86,411 bytes, 43.384 dB SNR, and 0.9186
  log-mel RMSE.

Machine metrics are not a substitute for listening. The Opus values are
reported only as the already pinned objective anchor.

## R-136 residual frontier

All points use the same all-family MAF predictor and exact native decode.

| Residual coefficients/frame | Complete bytes | SNR | Log-mel | Result |
|---:|---:|---:|---:|---|
| 12 | 27,360 | 36.406 dB | 4.001 | Rejected |
| 16 | 33,029 | 37.642 dB | 3.866 | Rejected |
| 24 | 43,554 | 39.352 dB | 3.611 | Rejected |
| 32 | 53,114 | 40.381 dB | 3.379 | Rejected |
| 48 | 71,907 | 41.353 dB | 2.949 | Rejected |
| 64 | 91,929 | 41.730 dB | 2.580 | Rejected |
| 71 | 99,928 | 41.821 dB | 2.430 | Rejected |

No point passes R-135. Above budget 48 the candidate also loses its rate
advantage. Adding more of the same residual is therefore closed as the
solution.

## R-137 family ablation

Every mask uses residual budget 48. `NO_MODEL` is always available.

| Enabled MAF families | Complete bytes | SNR | Log-mel | Result |
|---|---:|---:|---:|---|
| None | 63,412 | 36.181 dB | 0.4656 | Eligible |
| Periodic only | 64,607 | 43.634 dB | 0.5117 | Rejected |
| Impulse only | 73,416 | 35.782 dB | 3.3048 | Rejected |
| Stochastic only | 71,458 | 36.167 dB | 1.8817 | Rejected |
| Periodic + impulse | 75,155 | 41.258 dB | 3.1743 | Rejected |
| Periodic + stochastic | 72,666 | 42.909 dB | 2.0061 | Rejected |
| Impulse + stochastic | 70,936 | 36.008 dB | 2.8737 | Rejected |
| All | 71,907 | 41.353 dB | 2.9493 | Rejected |

The only eligible point is ordinary optimized Truth. It saves 22,975 bytes,
or 26.59%, versus the preceding Resonith stream, and 26.62% versus the pinned
Opus file. This is not an MAF gain and is not yet a subjective quality claim.

Periodic-only demonstrates useful structure: for only 1,195 bytes above
optimized Truth it improves waveform SNR by 7.45 dB. It nevertheless exceeds
the declared log-mel and magnitude-similarity limits. Full-band impulse and
stochastic modes are clearly harmful under the current router.

## R-138 gain-shape residual ablation

Six periodic-only gain-shape variants tested frame whitening 0, 0.02, 0.10,
and 0.25 plus two band-whitened combinations. Complete bytes ranged from
63,866 to 64,595 and log-mel from 0.5170 to 0.5420. None passed R-135.

## Decision

- Optimized `NO_MODEL` becomes the incremental architecture baseline.
- No byte saving from that point may be attributed to MAF.
- Full-band impulse and stochastic promotion is disabled.
- Periodic MAF remains promising but requires final-output band-local
  allocation rather than a looser threshold.
- The next primary mechanism is R-139 content-defined immutable motif memory:
  exact reuse first, then gain/phase and bounded pitch/time normalization.

## Artifacts

Local machine reports and listening files:

- `artifacts/r136-electronic-tune-frontier/report.json`;
- `artifacts/r137-electronic-tune-ablation/report.json`;
- `artifacts/r138-periodic-f000-b000` through
  `artifacts/r138-periodic-f010-b010`.

Every point retains its complete stream, decoded WAV, SHA-256, full metric
tree, predictor ledger, and wall time.
