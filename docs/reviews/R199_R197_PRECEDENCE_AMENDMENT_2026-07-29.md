# R-199 R-197 Failure-Precedence Amendment

- Status: **ACCEPTED AMENDMENT — IMPLEMENTATION AND RE-AUDIT OPEN**
- Date: 2026-07-29
- Scope: R-197 path ABI v3 failure rows 6 through 9 only
- ABI effect: none
- Bitstream effect: none
- Compression claim: none

## Why the frozen rule was inconsistent

R-197 originally required semantic failures in rows 6 through 8 to precede
resource exhaustion in row 9 for every caller work and memory budget. That
order cannot be implemented without violating another frozen invariant.

For some inputs, deciding whether a canonical relation is malformed, whether
an expected identity is stale, or how much output capacity is required needs
more than `k - 1` work events or bytes. If the caller declares `k - 1`, a
conforming implementation has only two choices:

1. stop at the declared resource boundary before the semantic predicate is
   known; or
2. perform hidden or uncounted work to discover the later semantic failure.

The second choice makes the ledger false and breaks caller resource authority.
Therefore absolute row 6/7/8 precedence over row 9 was rejected. The repaired
law preserves caller bounds and defines the winner at the earliest point where
a predicate is objectively decidable.

## Amended precedence law

Rows 1 through 5 remain absolute and ordered:

1. null/count/pointer-pair, alignment, ABI size/version or invalid report
   header;
2. checked pointer-range or product overflow;
3. forbidden overlap;
4. reserved-field or enum failure;
5. hard profile ceiling, invalid caller resource declaration, or inability to
   reserve the diagnostic report stage/commit tokens.

After row 5, the report transaction is active. Rows 6 through 8 are semantic
checkpoints and row 9 is a per-operation resource guard:

6. malformed canonical resolution, observation, or edge relation;
7. missing expected identity on fill, or a present but stale identity;
8. insufficient path or entry capacity after exact required counts are known;
9. declared work, counted host/device memory, frontier, state, path, entry,
   depth, or exact-small exhaustion.

The first *determinable* failure wins:

- if a row 6, 7, or 8 predicate is known before the next bounded operation
  would exceed row 9, that semantic row wins;
- if the declared resource is exhausted before the semantic predicate can be
  determined, row 9 wins;
- no implementation may exceed, borrow against, or hide work or memory merely
  to discover a later semantic result.

Rows 10 and 11 retain their previous mapping:

10. counted-resource upstream failure, `std::bad_alloc`, or CUDA allocation
    failure maps to environmental out-of-memory;
11. synchronized CUDA execution failure or a checked internal invariant
    violation maps to internal malformed.

Within one checkpoint, fields are examined in function-argument order,
structure declaration order, then ascending array index. A CUDA path
synchronizes before return.

## Required pipeline

The v3 implementation SHALL use these visible phases:

A. Validate rows 1 through 5 using stack state, snapshot the three headers, set
   the caller ledger limit, and atomically reserve one typed report
   `STAGE_RECORD` and one typed report `COMMIT_RECORD`.

B. Under the caller work and counted-memory limits, snapshot and canonicalize
   resolution/observation state and perform semantic relation validation.

C. On fill, reject an absent expected identity without running the solver.

D. Canonically serialize named fields, compute the input fingerprint, and
   reject a stale expected identity.

E. Run the exact pass-one solver, determine exact path/entry counts, then
   reject insufficient capacity.

F. Stage the payload completely, atomically reserve typed payload commit
   events, commit payload records, and publish the one diagnostic report.

No fingerprint or solver pass may run before phase B. No solver pass may run
before the missing/stale identity checks. Internal CUDA tiles, PMR pages, and
temporary sorting buffers are counted work/memory, not exemptions.

## Transactional consequences

- Rows 1 through 5 leave every caller byte unchanged.
- Rows 6 through 11 leave path and entry payloads unchanged and publish at
  most one already-reserved diagnostic report with zero written counts.
- Fill success is the only path that commits path/entry payloads.
- Preflight and fill over identical logical input must expose identical
  canonical input and output fingerprints.
- A stale-identity diagnostic contains the newly computed actual input
  fingerprint.

## Mandatory falsification cases

The post-amendment gate must include:

- every single row and every pair among rows 1 through 5;
- malformed-at-work-`k`, then caller limits `k - 1` and `k`;
- stale-at-fingerprint-`k`, then caller limits `k - 1` and `k`;
- capacity-at-solver-`k`, then caller limits `k - 1` and `k`;
- missing identity proving that neither fingerprint nor solver executes;
- canary verification for every non-success path;
- exact typed event counts and exact total work for successful preflight and
  fill;
- deterministic permutations and cross-language fingerprint parity;
- injected counted-memory and upstream allocation failures at each phase.

This amendment is not a GO for R-191. It only removes an impossible
requirement and supplies a falsifiable, caller-bounded replacement. Independent
post-implementation audit remains mandatory.
