# R-200 Generation-Safe Arena Focused Gate

- Date: 2026-07-29
- Status: **FOCUSED GATE PASSED — INDEPENDENT STEP-7 GO**
- Scope: analyzer ownership infrastructure
- Codec algorithm change: no
- Bitstream change: no
- Compression or Opus claim: none

## Implemented

- Public raw-handle `adopt` ownership was removed.
- Only the arena can create or retain an owning RAII reference.
- Root and child rank/link/generation invariants are checked before parent
  refcount mutation.
- Each live reference has one locally tracked typed release reservation.
- Create/acquire failure rolls back slot, parent ownership, and reservations.
- Reclamation is iterative and deterministic LIFO.
- Borrowed output-union handles are destroyed before their owner reservoirs.
- Every successful solver pass requires an empty healthy arena at return.
- Test-only invariant audit proves refcount/reservation equality and free-list
  integrity.

## Focused probes

| Counterexample | Result |
|---|---|
| multi-slot ABA reuse | rejected |
| stale old generation after reuse | rejected |
| reuse while retained owner exists | rejected |
| reuse while child owns parent | rejected |
| deterministic two-slot LIFO | passed |
| parent-child cascade release | passed |
| invalid root rank | rejected transactionally |
| invalid child rank/link | rejected transactionally |
| forged second owner via raw adopt | API removed |
| RAII move | one owner retained |
| owner reservation exhaustion | rolled back |
| parent charge exhaustion | rolled back |
| parent reservation exhaustion | rolled back |
| PMR insertion allocation failure | no ownership mutation |
| refcount overflow | rejected |
| generation exhaustion | rejected without alias |
| double release | rejected and arena marked unhealthy |
| real solver teardown | empty arena required |

## Executed gates

| Gate | Result |
|---|---|
| Clang 22 strict C++23 warnings-as-errors build | passed |
| native partial-graph executable | passed |
| independent Python/native/oracle suite | 40 passed |
| partial-graph fuzz smoke | passed |
| exact Step-6 work/fingerprint golden vector | unchanged and passed |
| `git diff --check` | passed |

## Claim boundary

This is a mechanical ownership change. R-198's complete music manifest is not
triggered because encoded bytes, decoded PCM, candidate selection, and the
successful exact work/fingerprint vector are unchanged. Full allocator
provenance, broad ABI fuzzing, platform sanitizers, and final R-191 admission
remain Steps 8 through 10.

## Independent audit

The independent post-implementation audit returned **GO with zero blockers**
for Step 7. The audited `native/src/partial_graph.cpp` SHA-256 is:

```text
D5E960011F78609AE7B0FA83820DECADCB4AEDF1A9E26BA2AA6BA687E670E413
```

The auditor independently reran the strict C++23 native test successfully.
