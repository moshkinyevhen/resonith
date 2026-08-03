# R-203 Semantic Ledger and Resource Telemetry Split Preflight

Date: 2026-07-29

Status: **REVISION 3; SECOND-AUDITOR BLOCKERS UNDER REVIEW**

Scope: remove an invalid cross-toolchain resource-identity requirement without
changing production solver, output, ABI, syntax, encoder, decoder, or player
behavior

Evidence amendment ID: `R203-EVIDENCE-SPLIT-1`

## Problem

The current Step-10 evidence plan conflates three different claims:

1. semantic output determinism;
2. logical solver-event determinism;
3. implementation-local managed-allocation telemetry.

The first claim must be identical across every admitted toolchain. Most of the
second claim can also be identical. The third claim cannot generally be
identical because conforming standard-library implementations may issue
different allocation requests while producing identical semantic results.

Requiring one cross-toolchain hash over all three creates false failures and
pressures the project toward an unrelated custom-container rewrite. Ignoring
resource telemetry would create the opposite error. This preflight separates
the claims while retaining fail-closed local resource evidence.

## Frozen production boundary

This proposal changes evidence comparison only. It does not authorize any
change to:

- native solver control flow or charge sites;
- path, entry, score, status, selection, or fingerprints;
- ABI layout or field meaning;
- successful or failing transaction behavior;
- released encoder consumption;
- bitstream bytes, decoded PCM, or Orkela.

Any such change exits this preflight and triggers the applicable R-198 and
independent-audit gates.

## Evidence classes

The frozen 288-case corpus SHA-256 and `case_index` values `0..287` define the
ordinary Class-A/Class-B fixture set before execution. Both preflight and fill
of every one of those cases use their frozen common nonbinding ceilings and no
fault injection. Every admitted toolchain must execute every ordinary call as
Class A/B. A resource failure, inability to execute, or post-result
reclassification of an ordinary fixture is unconditional NO-GO.

Tight-budget, OOM, allocation-ordinal, cleanup, release, and injected-failure
fixtures are separately enumerated by immutable ID in the hostile inventory
before execution. Only those calls use toolchain-local Class-C failure
evidence.

### Class A: cross-toolchain semantic identity

For calls whose work/resource ceilings and fault injection cannot trigger a
vendor-dependent failure, the following fields must match exactly across GCC,
Clang, MSVC, AppleClang, Android NDK, and every repeated call:

- status and termination;
- `struct_size`, `abi_version`, `solver`, `flags`, and every reserved-zero
  report field;
- required/written counts;
- every path and entry field and raw packed byte;
- every score, rank, family, conflict, and selection field;
- input and output fingerprints;
- corpus, contract, inventory, and typed/packed semantic hashes.

Any mismatch inside that non-resource-triggering domain is unconditional
NO-GO. Tight-budget, OOM, allocation-ordinal, cleanup, release, and explicit
fault-injection calls instead require their locally expected
status/termination, no-write boundary, cleanup, and repeatability. Their
vendor-specific failure point is not a Class-A cross-toolchain identity field.
They also require exact locally expected `struct_size`, `abi_version`,
`solver`, `flags`, and reserved-zero fields, or an unchanged caller report
under the applicable no-write contract.

### Class B: logical event identity

For the CPU analyzer, all event counts except `MEMORY_PAGE` must match exactly
across admitted toolchains and repeated calls when caller work/resource
ceilings cannot trigger a vendor-dependent failure. `work_units` is split in
evidence only after the replay verifies:

```text
work_units == sum(work_event_counts[0..21])
non_memory_work_units =
    sum(work_event_counts[event != MEMORY_PAGE])
```

`non_memory_work_units` and its 21-component vector are cross-toolchain
identity fields. `CUDA_ITEM` is compared only within the corresponding CPU or
CUDA execution class.

Tight work-budget prefixes, OOM, allocation ordinals, and resource-ceiling
calls are per-toolchain failure evidence. Their exact status, no-write
transaction, cleanup, and repeatability remain mandatory locally, but a
vendor-specific allocation request may legitimately move the prefix at which
resource exhaustion wins.

The independent reference authority must exactly derive the fourteen event
families whose public laws are closed:

- validation and snapshot;
- radix bucket/classify/scatter;
- graph source/gap/target/cycle and edge fields;
- stage, commit, fingerprint, and CPU `CUDA_ITEM = 0`.

For merge, lookup, state, reference, select, and reconstruct events, admission
requires:

- an independently derived conservative total and per-loop upper bound from
  canonical input and manifest ceilings;
- a versioned complete inventory of every native charge site;
- exact repeat-run and cross-toolchain identity;
- event-prefix budget rejection;
- focused mutation and branch-coverage gates;
- ledger-sum, reservation, cleanup, and zero-outstanding invariants;
- one native mutant that removes each inventoried charge site and one that
  reclassifies it, both of which the gate must reject;
- explicit honest status as implementation conformance evidence, not an
  independently proved closed-form count.

The project SHALL NOT claim independent mathematical prediction for those
seven dynamic families.

### Class C: implementation-local managed-resource telemetry

`MEMORY_PAGE`, reserved/committed/peak-live host/device bytes, and allocation
request traces are not cross-toolchain semantic identity fields. For each
toolchain independently they must:

- repeat exactly for the same binary and input;
- preserve `reserved >= committed >= peak-live`;
- remain within manifest host/device ceilings;
- bind every allocation identity from prepare through upstream outcome,
  commit or cancel/reclaim, and release;
- retain ordered transition records containing phase, pointer-independent
  allocation identity, requested size, requested alignment, outcome, and
  page count;
- reproduce `MEMORY_PAGE` from that ordered transition stream using the frozen
  4,096-byte page law;
- end with zero outstanding managed allocations and page reservations;
- preserve transactional no-write behavior under every injected pre-commit
  allocation, upstream, commit, cancel, and cleanup-reservation failure.

The frozen Step-10 no-failure-after-publication rule remains absolute. Cleanup
release events are reserved and included in the published total before the
copy tail, but post-report destruction must be proved unable to alter totals
or reach a failure. Required native mutants remove and reorder the v3 release
callback and force release-ledger consumption failure; every mutant must be
rejected. If proof requires a production cleanup reorder rather than a
test-only capture hook, it is a separately audited native change outside this
evidence-only amendment.

The report terminology remains **managed upstream-request bytes**. It does not
claim allocator metadata, virtual-address reservation, RSS, or OS physical
page commitment.

The cross-toolchain aggregate publishes each toolchain's telemetry vector and
min/max range. A difference is reported, not hidden, and is a failure only if
it violates a local invariant, ceiling, repeatability, or the frozen semantic
boundary.

For each unchanged toolchain, compiler/link input, corpus, and fixture, the
aggregate also compares allocation count, each transition-class count, and
reserved/committed/peak-live vectors with the immediately preceding accepted
artifact. This evidence-only change admits zero increase. A changed toolchain
or compiler/link input cannot borrow that zero-regression claim; it receives a
new explicitly labelled baseline while still satisfying all absolute bounds.

## Alternatives rejected

- one hash over semantic output and STL allocation requests;
- deleting resource fields from evidence;
- rewriting every solver container solely to make telemetry hashes equal;
- calling implementation-derived dynamic event counts independently proved;
- accepting semantic differences because resource bounds passed;
- changing ABI names to claim OS-level physical memory.

## Falsifiable predictions

On the frozen 288-case corpus:

- all Class-A fields and all 21 CPU non-memory event counts remain identical;
- Clang and GCC retain packed semantic hash
  `4b72967ad29a23722724b3338656dd4563d35419d35ac53ee65a7946b327da22`;
- every per-toolchain resource replay is twice-identical and locally valid;
- no native source, shared-library binary, path, entry, report, released
  bitstream, or decoded PCM changes as a consequence of this evidence split;
- the revised comparator rejects injected Class-A/Class-B mismatch and accepts
  a bounded, internally valid Class-C difference while reporting it.

## Required mutation tests

The comparator and replay must reject:

- one changed path/entry/report semantic field;
- one changed non-memory event count;
- an incorrect ledger sum;
- a missing or reclassified dynamic-family charge site;
- a missing allocation request or release;
- a reordered prepare/outcome/commit/cancel/release transition;
- a reused or mismatched allocation identity;
- an incorrect page rounding;
- telemetry over a manifest ceiling;
- nonzero outstanding allocation/page state;
- a different resource vector on the second run of the same binary;
- an omitted or falsely equalized toolchain artifact.

One test must demonstrate that two synthetic, locally valid telemetry vectors
with identical Class-A/Class-B evidence are accepted and both retained in the
aggregate.

Every inventoried dynamic charge site must have remove/reclassify mutant
coverage. A mutant that survives is unconditional NO-GO.

## Versioned supersession

`R203-EVIDENCE-SPLIT-1` explicitly supersedes:

- the R-197 requirement that complete `MEMORY_PAGE` and managed
  upstream-request vectors be platform-independent identity evidence;
- the R-203 final-admission preflight requirement that the independent Python
  authority emit complete expected reports and all 22 exact event-ledger
  counts;
- the R-203 comparator requirement for one exact cross-toolchain hash over
  semantic output, dynamic work, and vendor allocation telemetry.

The replacement field matrix is:

| Evidence class | Exact cross-toolchain fields | Local-only fields |
|---|---|---|
| A | `struct_size`, `abi_version`, status/termination, `solver`, `flags`, every reserved-zero field, required/written and every semantic report count for frozen ordinary fixtures; every path/entry byte, score, rank, family, conflict and selection field; input/output fingerprints; Class-A typed and packed-output hashes | exact locally expected header/control/reserved values and unchanged-report/no-write behavior for hostile fixtures |
| B | 21 non-`MEMORY_PAGE` counters and checked `non_memory_work_units`; CPU/CUDA classes remain separate | tight-budget and injected-failure status boundaries |
| C | none | raw `work_units`, `MEMORY_PAGE`, `peak_live_managed_bytes`, six host/device byte fields, ordered allocation transitions, allocation/release failure boundaries |

This matrix exhaustively partitions every field of
`resonith_partial_path_report_v3`; no report field may be omitted or left
unclassified by a replay or comparator.

This supersession does not alter:

- the 22 event meanings;
- ABI field layout or semantics;
- local exactness, bounds, repeatability, failure behavior, or provenance;
- cross-toolchain identity for semantic output or 21 non-memory CPU events;
- any frozen corpus, campaign floor, or final independent admission gate.

The R-197 phrase "platform-independent and complete" remains applicable to
Class A and the 21-component Class B vector. Class C is complete,
implementation-local telemetry published per toolchain.

## Admission gates

1. independent binary GO on this exact split;
2. comparator/replay implementation with focused mutation tests;
3. unchanged production sources, generated inputs, compiler flags, link
   inputs, and native object/shared-library hashes for this evidence-only
   amendment where reproducibly available;
4. frozen candidate-rich, R-197, hostile, boundary, allocation, sanitizer,
   concurrency, CUDA, and platform gates;
5. final independent R-191 analyzer-only GO.

Because this preflight changes no production behavior, it uses the focused
evidence exception only when all production sources, generated inputs,
compiler flags, and link inputs are unchanged. It cannot classify unrelated
production diffs in the same working batch. Those retain their own audited
identity or complete-comparison gates. This amendment does not waive the
complete registered-music and maximum-effort Opus gate for any later solver,
analyzer integration, encoder, syntax, decoded-output, or resource-behavior
change.

## Sources

- [R-203 complete-ledger authority audit](R203_COMPLETE_LEDGER_AUTHORITY_AUDIT_2026-07-29.md)
- [Rejected portable-ledger schedule](R203_PORTABLE_LEDGER_SCHEDULE_PREFLIGHT_2026-07-29.md)
- [C++ working draft: vector capacity](https://eel.is/c++draft/vector.capacity)
- [C++ working draft: memory-resource allocation](https://eel.is/c++draft/mem.res.private)
- [WG21 P2236R0: monotonic buffer resource implementation differences](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2020/p2236r0.html)

## Independent verdict

Revision 2 received one independent GO, then a second independent auditor
returned NO-GO on three remaining conflicts: incomplete supersession of the
Step-10 oracle clause, weakened post-publication cleanup law, and fixture-class
membership that was not frozen before execution. Revision 3 incorporates all
three findings. No implementation is admitted until both auditors confirm the
current text.
