# R-221 bounded rate-only implementation audit

Date: 2026-08-02

Status: **INDEPENDENT GO FOR ONE FRESH REAL CORPUS RUN ONLY**

## Audited identity

- Preflight SHA-256:
  `a97c1da031e905e4ac55d16f13f069f12cc330a2a657951e7824eadf1ca2c755`.
- Runner SHA-256:
  `830ed4ac12b369bcf9de7308fa18bfb5b31c0989c11aaa665f052a9d87d869a3`.
- Focused-test SHA-256:
  `76f51f610927169bbe0cb1a51b30e1d7e53c5c496f2d099d09bec2e26a2e3947`.
- Frozen source revision:
  `1c45376eebe7daa49904acae885c47d6d571cf87`.

## Independent result

The independent auditor reproduced all 32 focused tests in 2.71 seconds and
issued GO with no blocking findings. The exact implementation preserves the
first four R-219 feedback encodes and the single fixed official Opus 1.6.1
configuration. Only integer requested bitrate may vary. Additional attempts
use the exact integer midpoint of the tightest directly observed sign-changing
bracket, are recomputed without a global monotonicity assumption, and stop at
twelve total observations.

Equal-q5 observations must have identical complete bytes and normalized Ogg
hashes. All no-strict-match terminals select a quality-blind nearest observed
point. Decoded quality is unavailable until selection. Receipt and resume
validation bind the sequential 4..12 attempt ledger, identical fixed
configuration, attempt count, selected observation, signed byte delta, and
rate-delta percentage. `UNMATCHED_NEAREST` rows are mechanically excluded from
every equal-rate statistic or claim.

An independent AST comparison found the computation-critical inherited
functions identical after R-label normalization. The selected decoder differs
only in its ledger record label, not computation.

## Authorization boundary

GO authorizes one fresh full registered long-first R-221 run. It does not
authorize reuse of R-219 outputs, evidence admission, S13, product version
promotion, release, or a general better-than-Opus claim.
