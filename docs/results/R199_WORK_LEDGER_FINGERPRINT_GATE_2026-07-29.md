# R-199 Exact Work-Ledger and Fingerprint Gate

- Date: 2026-07-29
- Status: **FOCUSED GATE PASSED — INDEPENDENT STEP-6 GO**
- Scope: bounded analyzer infrastructure only
- Codec algorithm change: no
- Bitstream change: no
- Compression or Opus claim: none

## Implemented result

The R-191 path ABI v3 now exposes one exact deterministic ledger containing
22 typed event families. Every successful focused fixture satisfies:

```text
work_units == sum(work_event_counts[0..21])
```

Work reservations retain their event type. A report `STAGE_RECORD` and report
`COMMIT_RECORD` are reserved as one rollback-safe pair before the stage event
is consumed. Payload commit events are reserved only after complete staging
and are consumed immediately before the corresponding caller write.

The v3 input and output fingerprints serialize named integer fields in fixed
little-endian order. They do not hash structure padding or compiler object
representations. Canonical input permutations produce identical input
fingerprints, output fingerprints, exact event vectors, total work, and peak
managed memory.

## R-199 pipeline correction

The executed order is now:

1. absolute pointer/header/profile checks and typed report reservation;
2. caller-bounded resolution/observation snapshot and semantic validation;
3. missing expected-identity rejection on fill;
4. canonical edge snapshot, named-field fingerprint, and stale-identity
   rejection;
5. exact pass-one solve and output-capacity rejection;
6. complete staging, typed payload commit, and one report commit.

A missing identity emits zero `FINGERPRINT_BYTE` events. A stale identity
publishes the newly computed actual canonical fingerprint but changes no path
or entry byte. The solver does not run before the missing/stale identity
check.

R-199 replaces the impossible requirement that later semantic predicates
always beat an earlier caller-resource exhaustion. Rows 1 through 5 remain
absolute. After the reservation transition, a known semantic failure wins;
resource exhaustion wins if the declared bound is reached before the semantic
predicate can be determined. No hidden work is permitted.

## Exact focused golden vector

The registered deterministic native/Python fixture produced:

| Event | Count |
|---|---:|
| `VALIDATE_RECORD` | 60 |
| `SNAPSHOT_BYTE` | 12,760 |
| `RADIX_BUCKET` | 18,432 |
| `RADIX_CLASSIFY` | 164 |
| `RADIX_SCATTER` | 164 |
| `MERGE_COMPARE` | 298 |
| `MERGE_MOVE` | 636 |
| `GRAPH_SOURCE` | 15 |
| `GRAPH_GAP` | 30 |
| `GRAPH_TARGET` | 150 |
| `GRAPH_CYCLE` | 27 |
| `EDGE_FIELD` | 405 |
| `LOOKUP` | 2,312 |
| `STATE` | 438 |
| `REFERENCE` | 710 |
| `SELECT` | 3,538 |
| `RECONSTRUCT` | 190 |
| `MEMORY_PAGE` | 1,839 |
| `STAGE_RECORD` | 129 |
| `COMMIT_RECORD` | 33 |
| `FINGERPRINT_BYTE` | 9,632 |
| `CUDA_ITEM` | 0 |
| **Total** | **51,962** |

Peak live managed memory was 18,684 bytes.

The canonical fingerprints were:

```text
input:
  14681656237124231420
  14217794624446866229
   3318052838151244206
  15337156228999464508

output:
    533898623865692396
   9232259795300133137
   5802264844233550618
   5931678949044348120
```

## Executed checks

| Gate | Result |
|---|---|
| Clang 22, strict C++23 warnings-as-errors build | passed |
| Native transactional/conformance executable | passed |
| Independent Python/native/oracle suite | 40 passed |
| Partial-graph fuzz smoke | passed |
| `git diff --check` | passed |
| Exact 22-event sum and golden vector | passed |
| Resolution/observation permutation invariance | passed |
| Missing-identity-before-fingerprint assertion | passed |
| Stale diagnostic actual-fingerprint assertion | passed |
| Typed reservation mismatch rejection | passed |
| Report stage/commit pair rollback probe | passed |
| Generation-safe stale-handle probe | passed |

## Claim boundary

This focused result does not admit R-192 prediction, a Resonith stream opcode,
compression improvement, an Opus comparison, or a product release. It is a
mechanical analyzer-infrastructure change, so R-198's complete registered-music
gate is not triggered. Generation-safe arena completion, full memory
provenance, fuzz matrices, and final R-191 conformance remain separate
subsequent steps.

## Independent audit

The independent red-team auditor returned **GO for Step 6** on:

```text
native/src/partial_graph.cpp
SHA-256:
B3B893D70828C6813C8B3ECD696AB648E9EF0C142051604BC8E1733123B0597D
```

The audit found no blocker in the amended phase order, exact typed ledger,
canonical fingerprints, transactional publication, or focused evidence
claims. It explicitly kept arena completeness, full memory provenance, broad
fuzz/platform gates, and final R-191 admission in Steps 7 through 10.
