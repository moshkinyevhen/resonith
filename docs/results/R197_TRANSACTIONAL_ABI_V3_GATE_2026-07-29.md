# R-197 Transactional Path ABI v3 Gate

Date: 2026-07-29

Status: **FOCUSED GATE PASSED — WORK-LEDGER REMEDIATION CONTINUES**

## Decision enabled

The public path-analyzer boundary may proceed on ABI v3. ABI v2 is retired as
a no-write `UNSUPPORTED_VERSION` compatibility stub. This result admits no
predictor, bitstream, compression, quality, or product claim.

## Implemented boundary

- packed ABI v3 manifest, path, entry, and report layouts with compile-time
  sizes and offsets;
- complete preflight before semantic output publication;
- bounded path and entry staging followed by one commit phase;
- pairwise no-alias validation for every input, output, manifest, and report
  range;
- immutable input snapshots before canonical validation;
- no semantic payload write for missing/stale identity, insufficient capacity,
  invalid input, profile-bound, allocation, or internal failure;
- report publication only after its header and precedence rows one through five
  validate;
- safe no-write ABI v2 rejection;
- matching Python 3.14 `ctypes` ABI v3 layout and native bridge.

## Exact precedence evidence

The native test covers:

1. invalid report header -> `INVALID_ARGUMENT`, report unchanged;
2. checked byte-range overflow -> `PROFILE_BOUND`, report unchanged;
3. forbidden overlap -> `INVALID_ARGUMENT`, all overlapping bytes unchanged;
4. reserved-field failure -> `INVALID_ARGUMENT`, report unchanged;
5. hard-profile ceiling -> `PROFILE_BOUND`, report unchanged;
6. missing fill fingerprint -> `INVALID_ARGUMENT`, payload unchanged;
7. stale input -> `HASH_MISMATCH` with `STALE_INPUT`, payload unchanged;
8. insufficient capacity -> `OUTPUT_TOO_SMALL`, payload unchanged;
9. successful preflight/fill -> exact required/written counts and ABI v3
   records.

The remaining exact 22-event accounting and canonical ABI v3 fingerprint law
belong to the next R-197 work package and are not claimed by this gate.

## Executed validation

- LLVM/Clang C++23 warnings-as-errors build:
  `resonith_partial_graph_test` and `resonith_core_shared` passed;
- native transactional test:
  9 canonical edges, 8 paths, deterministic result;
- independent Python fixed-point/native suite:
  **40 passed in 1.87 seconds**;
- shared-library export:
  `resonith_partial_graph_paths_cpu_v3` is present;
- ABI v3 packed sizes:
  manifest 1232 bytes, path 136 bytes, entry 48 bytes, report 560 bytes.

## R-198 classification

This work changes analyzer API safety and does not alter a Resonith audio
algorithm, bitstream, or decoded PCM. Therefore the R-198 complete music gate
does not apply. Focused native and independent-oracle validation is the
declared identical-output infrastructure exception.

## Next dependency

Implement the frozen 22-event work taxonomy, exact reservation/consumption
law, canonical field-wise ABI v3 fingerprints, and corresponding golden
vectors before declaring R-197 complete.
