# R-203 Portable Ledger Schedule Preflight

Date: 2026-07-29

Status: **INDEPENDENT NO-GO; SUPERSEDED BEFORE IMPLEMENTATION**

Scope: the smallest production-law change that makes every R-191 work and
resource field independently verifiable across admitted toolchains

## Problem and frozen baseline

The current candidate-rich replay proves exact path, entry, fingerprint,
selection, transaction, and packed-output identity for 288 cases. It does not
independently predict every work and memory field because:

- solver charge sites are distributed across implementation control flow;
- the public contract does not enumerate every sort, lookup, state, arena,
  selection, or reconstruction transition;
- physical allocation requests inherit implementation-defined container
  capacity growth.

The frozen baseline is the current candidate-rich corpus and its SHA-256
`fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7`,
the exact packed semantic hash
`4b72967ad29a23722724b3338656dd4563d35419d35ac53ee65a7946b327da22`,
the R-199 golden vector, all current paths/entries/fingerprints/statuses, and
zero released-encoder consumption of R-191.

## Complete objective

For every accepted case and admitted toolchain:

1. a separate verifier derives every one of the 22 event counts;
2. the verifier derives all report, fingerprint, path, and entry fields;
3. the native implementation and verifier agree exactly;
4. physical host/device use remains bounded and truthfully reported;
5. no successful path, entry, status, score, fingerprint, released bitstream,
   or decoded PCM changes;
6. release builds retain no trace-storage or Python dependency.

## Alternatives considered

### A. Copy native charge sites into Python

Rejected. This is circular and can preserve the same omission in two
languages.

### B. Report only closed-form upper budgets

Rejected as the primary ledger. It is independently predictable, but it no
longer proves that the implementation emitted one event immediately before
each named operation. Upper bounds may remain a separate denial-of-service
guard.

### C. Ignore physical allocation differences

Rejected. Exact semantic output does not excuse an unbounded or inaccurately
reported working set.

### D. Replace every solver container immediately

Rejected as the first experiment. A full custom-container rewrite has a large
regression surface before the evidence mechanism itself is proven.

### E. Proof-carrying schedule plus explicit allocation sites

Selected for independent audit.

## Proposed schedule law

### Declarative operation sites

Assign a stable integer site ID to every solver operation family:

- canonical radix pass;
- stable merge sort and its ordered input;
- deterministic table lookup/probe;
- state create/compare/transition;
- arena acquire/release/generation validation;
- reservoir/frontier/conflict/final selection;
- iterative reconstruction visit/emit;
- staging, fingerprint, commit, and CUDA operation;
- host/device allocation, commit, transfer, reclaim, and release.

One checked-in English schedule table defines, per site:

- legal predecessor and successor states;
- the event family and multiplicity law;
- the typed operands required to validate the transition;
- the canonical ordering/tie rule;
- whether the site may repeat and its hard maximum;
- the associated allocation site, if any.

The table is normative evidence input. C++ does not generate the Python
verifier, and Python does not import or call the native implementation.

### Conformance trace

In conformance builds only, the production state machine emits a bounded
fixed-record trace:

```text
site_id, event, phase, object_id, operand_a, operand_b, result
```

The trace is not accepted as truth. The independent verifier:

1. begins from the original canonical input, not native candidates;
2. checks every trace transition against the schedule table;
3. independently reconstructs radix and merge ordering, graph state, arena
   generations, reservoirs, conflicts, selected paths, and reconstruction;
4. rejects a missing, extra, reordered, illegal, or inconsistent record;
5. derives the 22 counters and output records from the verified transitions.

The native report is compared only after this replay. Test traces are bounded
by the manifest's declared event ceiling and are absent from release ABI and
artifacts.

### Portable allocation-site law

Every solver-owned dynamic container receives:

- a stable allocation-site ID;
- a checked exact maximum element count derived from canonical input and
  manifest fields before first mutation;
- an exact byte-capacity formula including element size and declared
  alignment;
- one explicit reserve/commit transition;
- a prohibition on implicit growth after reservation.

The managed resource allocates the declared site capacity, not a vendor
container's preferred growth capacity. A request greater than the declared
site capacity is a deterministic internal failure; unused site bytes remain
counted because they are physically reserved by the site. Release uses the
site record rather than the deallocator's requested byte count.

The first coherent prototype covers only the containers reached by the frozen
288-case corpus. Admission remains blocked until the same law covers every
R-191 solver allocation and hostile/boundary corpus.

## Why this is independently checkable

- native control flow cannot choose an unlisted operation without producing an
  illegal or missing transition;
- the verifier derives state and outputs from original inputs and a public
  state-transition law;
- allocation bytes come from explicit site formulas rather than hidden
  `vector` growth;
- the final ledger is a consequence of verified transitions, not a copied
  native vector;
- release behavior uses the same state machine but does not retain the trace.

## Falsifiable predictions

The 288-case prototype must:

- retain the corpus and packed semantic hashes exactly;
- retain every path, entry, score, status, input/output fingerprint, and
  selection result;
- produce one complete valid schedule trace per preflight and fill;
- reproduce all 22 event counts and every report field independently;
- report the same managed allocation-site bytes on Clang, GCC, MSVC,
  AppleClang, Android NDK, and the reference interpreter;
- add at most 20% focused-test wall time with tracing disabled and at most 2x
  with bounded tracing enabled;
- add zero trace-storage bytes and zero Python dependency to release builds.

## Kill gates

Return NO-GO on any:

- circular verifier dependency;
- operation that cannot be expressed by the schedule table;
- implicit post-reserve growth;
- vendor-specific allocation size in a semantic or resource field;
- changed path, entry, score, status, fingerprint, released bitstream, or
  decoded PCM;
- missing/extra/invalid transition accepted by the verifier;
- counter, report, resource, toolchain, or repeat-run mismatch;
- unbounded trace or release-build trace dependency;
- registered-music or maximum-effort Opus regression outside the frozen
  acceptance policy.

## Verification order

1. independent binary audit of this preflight;
2. one tiny trace/table prototype over the 288-case corpus;
3. focused native/Python/toolchain replay;
4. explicit allocation-site coverage audit;
5. hostile, boundary, allocation, sanitizer, concurrency, and CUDA campaigns;
6. released-encoder non-consumption and bitstream/PCM identity proof;
7. complete registered-music manifest against the preceding Resonith
   generation and maximum-effort official Opus;
8. final independent R-191 GO/NO-GO.

## Sources

- [R-203 complete-ledger authority audit](R203_COMPLETE_LEDGER_AUTHORITY_AUDIT_2026-07-29.md)
- [C++ working draft: vector capacity](https://eel.is/c++draft/vector)
- [WG21 P2236R0: monotonic buffer resource implementation differences](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2020/p2236r0.html)
- [WG21 P3002R1: allocator policies and deterministic execution](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p3002r1.html)
- [libc++ ABI guarantees](https://libcxx.llvm.org/ABIGuarantees.html)

## Independent audit outcome

The proposal was rejected before production implementation:

- a witness trace cannot prove that native omitted neither an operation nor
  its corresponding trace record;
- the English table is not a complete executable transition law;
- PMR cannot reduce or otherwise control a vendor-selected allocation request;
- allocation sites require dynamic instance and lifetime identity;
- reserving site maxima can change resource-failure statuses;
- the ABI reports managed upstream-request bytes, not OS physical pages;
- release-finalization and bounded trace laws were incomplete;
- a 288-case production remediation would not cover hostile solver paths.

The simpler semantic-ledger/resource-telemetry split is reviewed separately.
