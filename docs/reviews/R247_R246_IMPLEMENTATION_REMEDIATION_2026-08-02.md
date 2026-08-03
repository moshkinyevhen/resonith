# R-247 R-246 implementation remediation

Date: 2026-08-02

Status: **RECORDED BEFORE CODE REMEDIATION; EXECUTION NO-GO**

## Frozen problem and objective

Two independent read-only audits rejected runner SHA-256
`2a0aa4381a3f7913d776c8e9cb022b0fe8925172d73f5bac79c811ff62674673`.
R-247 changes neither codec, oracle, decoder nor bitstream. Its sole objective is
to make the already selected R-246 evidence transaction satisfy its frozen
fail-closed contract without expanding the workload.

## Blocking findings

1. A source rehash and state construction followed staging ownership but
   preceded the protected `try`.
2. Predicate observations were recorded after the branch that could fail.
3. A worker request was hashed and parsed through separate reads, while the
   controller did not close request and consumed-marker identities.
4. Retained PCM/report sizes, raw profile identity and profile text identities
   were not fully declared and revalidated.
5. Timing/profile reports did not enforce exact keys, finite values, frozen
   pair/trial order, recomputed medians and recomputed profile ratio. Golden
   metadata validation was incomplete.
6. Post-receipt verification compared selected fields rather than exact
   canonical bytes and object equality.
7. Failure-receipt size was not guaranteed after traceback truncation.
8. The controller deadline was not checked before and between workers.
9. The literal R-246 authority path and exact outer controller invocation were
   not both enforced and retained.

## Selected minimal correction

The runner will move every fallible postownership action under the existing
transaction, record observations before their kill gate, consume each request
from one immutable byte read, and bind request/marker bytes into the receipt.
It will add exact structural and finite-number validation, recompute timing and
profile aggregates, bind every retained payload size/hash including `.prof`
and profile text, validate expanded golden metadata, require exact canonical
receipt readback, enforce the controller deadline at every phase boundary, and
emit a size-bounded failure record. The literal authority path and exact
controller argument vector will be enforced and retained.

The source bound remains 640 physical lines and 64 KiB. Existing code may be
compacted mechanically to fit; complexity may not be moved to an unaudited
helper. No workload may run until the new exact runner and authority receive
two independent implementation GO verdicts.

## Rejected alternatives and kill gate

- Weakening the R-246 design, omitting malformed-report checks, or trusting the
  worker because it is hash-bound is rejected.
- Adding another workload, long control, Opus run or codec modification is
  rejected as scope expansion.
- R-246 remains execution NO-GO if either re-auditor finds any false PASS,
  unbounded postownership path, incomplete retained-byte reconstruction or
  source-bound violation.

