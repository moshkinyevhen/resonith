# R-272 S17 Inharmonic Modal-Field V5 Audit

Date: 2026-08-03  
Status: **INDEPENDENT GO; BOUNDED S17 IMPLEMENTATION AUTHORIZED**

## Exact audited identities

- preflight SHA-256:
  `a44ba1781d176577e713bc78f8ea859b11917625a0d600e3ad56cba7ff286dc4`;
- control freezer SHA-256:
  `ff61a3055864f28273d5c2728f3650c9099138562d0b9ec180af7e4a558da826`;
- tracked control manifest SHA-256:
  `5c1146171d290b021e5ae73f2be282818ee402ac433a2c82b803fabaacc27300`.

## Verdict

The independent adversarial review returned **GO** after five bounded
pre-code revisions. The final delta audit confirms that Q20 frequency has an
exact Q32 phase-step derivation, the inclusive Q31 decay search has complete
endpoint behavior, and two-run IMF1 and mechanically expanded IMU1 pack
stability is global for every model-on input.

Earlier rounds rejected incomplete parser extents, mixed Q16/Q15 amplitude
arithmetic, ambiguous phase unwrap and decay factoring, circular controls,
silent holdout clipping/truncation, incomplete decoder-identity predicates,
an unfrozen metric scalar, and an imprecise executable budget. Those defects
were removed before codec code or audio comparison.

R-272 authorizes only the exact V5 implementation allowlist and its bounded
long-first focused gate. It does not authorize syntax/default promotion,
versioning, release, an improvement claim, or S18. A failed long predicate
terminates S17 without short controls, EBU execution, registered corpus, or
Opus execution. A focused pass authorizes exactly one S18 full comparison.
