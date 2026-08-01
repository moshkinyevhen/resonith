# R-203 Complete-Ledger Authority Audit

Date: 2026-07-29

Status: **INDEPENDENT NO-GO; PRODUCTION LAW IS UNDER-SPECIFIED**

Scope: complete independent prediction of every ABI-v3 work-ledger and
resource-report field for the 288-case candidate-rich corpus

## Binary verdict

Do not implement a purportedly independent Python authority for all 22 event
families yet. The frozen R-197/R-199 law specifies the public event meanings,
but it does not completely specify every solver schedule or the capacity and
allocation policy of the C++ containers. Translating the current C++ charge
sites into Python would be a second copy of the implementation, not an
independent authority.

## Independently derivable events

For `F = 0` in preflight and `F = 1` in fill, define:

```text
L = 2 + F
S = 1 + F
R = 1
```

For `N` observations, `E` edges, `G` declared gaps, `P` output paths, `Q`
output entries, canonical input byte count `B_in`, and canonical output byte
count `B_out`, the auditor independently derived:

```text
VALIDATE_RECORD  = 3 + L(4 + R + N + E)
SNAPSHOT_BYTE    = 1972 + 32R + 128N + 80E
                   + L(1740 + 32R + 128N + 80E)
RADIX_BUCKET     = 18432
RADIX_CLASSIFY   = 4R + 32N
RADIX_SCATTER    = 4R + 32N
GRAPH_SOURCE     = LN
GRAPH_GAP        = LNG
GRAPH_TARGET     = LN^2G
GRAPH_CYCLE      = LE
EDGE_FIELD       = 15LE
STAGE_RECORD     = 1 + (1 + 3F)(P + Q)
COMMIT_RECORD    = 1 for preflight, P + Q + 1 for fill
FINGERPRINT_BYTE = B_in + (S + F)B_out
B_in             = 1448 + 32R + 128N + 80E
B_out            = 24 + 136P + 48Q
CUDA_ITEM        = 0
```

The complete `work_units` field must equal the checked sum of the 22 event
counters. These formulas reproduce the corresponding R-199 golden values,
including `VALIDATE_RECORD = 60`, `SNAPSHOT_BYTE = 12760`,
`STAGE_RECORD = 129`, `COMMIT_RECORD = 33`, and
`FINGERPRINT_BYTE = 9632`.

## Unresolved independent laws

The following event families cannot yet be predicted independently from the
frozen public contract:

- `MERGE_COMPARE` and `MERGE_MOVE`: the merge algorithm is specified, but the
  complete list of solver sort sites and their input key traces is not;
- `LOOKUP`, `STATE`, `REFERENCE`, `SELECT`, and `RECONSTRUCT`: counts depend on
  the exact sequence of solver operations, arena handles, reservoirs,
  frontiers, selection, and reconstruction;
- `MEMORY_PAGE` and the resource high-water fields: they depend on allocation
  request sizes produced by container capacity growth that the public contract
  does not define.

For one merge of `m` records, moves can be derived as
`m * (q + (q mod 2))`, where `q = ceil(log2(m))`; comparisons additionally
require the ordered key trace. `MEMORY_PAGE` is three logical page events per
allocation request in the present transaction design, but the request
sequence itself is not portable while it depends on an implementation's
container-growth policy.

The C++ standard guarantees only that `vector::reserve(n)` provides capacity
of at least `n`; it does not freeze a cross-library growth schedule. WG21
history also records materially different permitted
`monotonic_buffer_resource` release/reuse behavior among libc++, Boost, and
MSVC. Exact MSVC, libstdc++, libc++, Android, and Apple resource vectors
therefore cannot be treated as a single independently specified value until
Resonith owns the allocation law.

## Rejected shortcuts

- copying production charge sites into Python;
- accepting native ledger vectors as the oracle;
- emulating one STL implementation's growth policy;
- excluding `MEMORY_PAGE` or comparing only the total work sum;
- labelling cross-toolchain equality as independent prediction.

All five shortcuts are circular or non-portable.

## Required remediation before a new authority

1. Freeze a declarative R-203 solver ledger schedule: every sort site, table
   probe, state/reference/select/reconstruct operation, and arena transition.
2. Replace implementation-dependent capacity growth in the admitted path with
   a portable deterministic capacity/allocation law.
3. Obtain an independent binary GO for that law before production changes.
4. Implement the authority as an interpreter of the declarative law, not as a
   translation of C++ charge sites.
5. Compare the complete 22-event vector, every v3 report field, fingerprints,
   preflight/fill, repeated calls, all 288 permutations, and every admitted
   toolchain.
6. Because the remediation changes production resource and solver behavior,
   execute the complete registered-music manifest against the preceding
   accepted Resonith generation and the maximum-effort official Opus anchor
   before admission.

## Admission boundary

The existing candidate-rich corpus remains valid finite input evidence. Its
JSONL, schema, case count, and SHA-256 remain frozen. The newly added complete
typed replay, independent selection judge, fail-closed inventory, twice-run
packed hash, and cross-toolchain jobs close the earlier evidence defects, but
they do not resolve the missing independent ledger law.

R-191 therefore remains **NO-GO**.

## Sources

- [R-197 transactional remediation preflight](R197_R191_TRANSACTIONAL_REMEDIATION_PREFLIGHT_2026-07-29.md)
- [R-199 work-ledger and fingerprint gate](../results/R199_WORK_LEDGER_FINGERPRINT_GATE_2026-07-29.md)
- [C++ working draft: vector capacity](https://eel.is/c++draft/vector)
- [WG21 P2236R0: monotonic buffer resource implementation differences](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2020/p2236r0.html)
- [libc++ ABI guarantees and vector layouts](https://libcxx.llvm.org/ABIGuarantees.html)
