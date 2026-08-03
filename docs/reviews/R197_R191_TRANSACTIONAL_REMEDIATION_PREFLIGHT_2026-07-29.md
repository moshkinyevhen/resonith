# R-197 R-191 Transactional Remediation Preflight

Status: **INDEPENDENT PRE-IMPLEMENTATION GO**

Final independent verdict: **GO** on 2026-07-29. The verdict authorizes only
the frozen R-190/R-191 transactional analyzer remediation and its declared
kill gates. It does not admit predictor syntax, compression or product claims.

## Scope

This preflight covers only remediation of the quarantined R-191 anonymous
partial-path analyzer and its R-190 canonical-edge dependency. It does not
admit predictor syntax, a compression mechanism, or a performance claim.

## Frozen failure

The independent post-implementation audit rejected R-191 because:

- the work ledger omitted repeated canonical enumeration, sorting, scanning,
  state and reconstruction work;
- the R-190 C ABI used unbounded default-resource containers and could throw
  or partially write;
- the fuzz target left material fields unreachable and did not prove
  transactionality;
- resource extrema, exact-small oracle, randomized parity and platform gates
  were incomplete.

## Alternatives

| Alternative | Decision | Reason |
|---|---|---|
| Materialize one bounded canonical edge vector | Oracle/fallback | Simple and auditable, but duplicates storage |
| Shared streaming enumerator with bounded staging | Preferred | One canonical definition and transactional output |
| Hash-only supplied-edge validation | Rejected | A fingerprint cannot replace exact field comparison |
| One formula-only global work precharge | Rejected alone | It hides repeated passes and data-dependent scans |
| Per-operation ledger plus deterministic sort precharge | Preferred | Platform-independent and complete |
| Monotonic arena | Allowed fallback | Must report full reserved allocation |
| Reclaiming arena with generation-tagged indices | Preferred after proof | Reduces live state without stale references |

## Frozen implementation contract

The fill call performs complete validation and canonical field comparison with
zero semantic writes, validates every capacity and resource bound, stages all
fallible output in one bounded managed resource, and commits only after no
failure remains. Every non-success result preserves caller output and canaries
byte-for-byte.

Work is a specified deterministic ledger. Each pass is separately charged.
Sorting uses a specified algorithm or a conservative precharged comparison
bound. Overflow terminates before the affected operation and exact selector
totals never saturate.

Every project-controlled allocation uses the bounded counting PMR resource.
C-boundary functions catch all exception classes and return declared statuses.
Arena references carry checked generation identity, and reconstruction is
iterative and bounded.

## Published hard profile ceilings

Caller manifests only reduce the following ABI ceilings; values above a
ceiling are rejected before enumeration or allocation. `UINT64_MAX` is never a
valid substitute for a profile:

| Dimension | R-197 hard ceiling |
|---|---:|
| sample rate | 384,000 Hz |
| resolutions / gaps / cycle offsets / neighbours per gap | 8 / 8 / 9 / 16 |
| observations | 1,048,576 |
| canonical or supplied edge records | 4,194,304 |
| path observations / reconstruction depth | 1,048,576 |
| retained path records | 65,536 |
| total path entries | 4,194,304 |
| live frontier states | 1,048,576 |
| arena state records | 4,194,304 |
| exact-set candidates | 24 |
| work events | 281,474,976,710,655 (`2^48-1`) |
| counted host bytes | 8,589,934,592 (8 GiB) and never above `SIZE_MAX` |
| counted device bytes | 4,294,967,296 (4 GiB) |
| one CUDA launch | at most 65,535 blocks × 1,024 threads |
| one logical CUDA index domain | 4,194,304 records, addressed with checked 64-bit indices |

Output bytes are not a second unbounded dimension: they are checked products
of the path/entry ceilings and their versioned record sizes. Any future larger
profile requires a new reviewed profile version; it cannot be enabled by a
caller-only manifest change.

## Work-ledger law v1

One work unit is one emitted event from the following frozen taxonomy, not one
CPU instruction and not elapsed time. Every event increments exactly one
64-bit counter by one immediately before the named action:

1. `VALIDATE_RECORD`: once before validating one API header, manifest,
   resolution, observation, edge, path or entry record;
2. `SNAPSHOT_BYTE`: once per byte copied into the bounded normalized input
   snapshot;
3. `RADIX_BUCKET`: once per bucket cleared or prefix-updated;
4. `RADIX_CLASSIFY`: once per input record classified in one radix pass;
5. `RADIX_SCATTER`: once per record written by one radix pass;
6. `MERGE_COMPARE`: once before one total-order comparison in the non-radix
   stable merge sorter;
7. `MERGE_MOVE`: once per complete record copied to the current merge output
   or copied back to the canonical buffer;
8. `GRAPH_SOURCE`: once before processing one canonical source observation;
9. `GRAPH_GAP`: once before processing one declared gap for one locally
   resolvable source;
10. `GRAPH_TARGET`: once before testing one canonical observation as the target
    of one source/gap pair;
11. `GRAPH_CYCLE`: once before testing/emitting one cycle-offset hypothesis for
    one retained target;
12. `EDGE_FIELD`: once before comparing one declared logical edge field;
13. `LOOKUP`: once before one key comparison or one visited record in a
    deterministic table, bucket or set scan;
14. `STATE`: once before creating a state, comparing two states or testing one
    state transition;
15. `REFERENCE`: once before acquire, release or generation validation of one
    arena handle;
16. `SELECT`: once before one frontier, reservoir, conflict or final-selector
    comparison/membership test;
17. `RECONSTRUCT`: once before visiting one arena node or emitting one path
    entry during iterative reconstruction;
18. `MEMORY_PAGE`: once per logical 4,096-byte page, rounded up, reserved,
    committed, transferred, reclaimed or released in host or device storage;
19. `STAGE_RECORD`: once immediately before staging one path, entry or local
    report record;
20. `COMMIT_RECORD`: once in the atomic tail reservation for each path, entry
    or report record that will be copied to caller storage;
21. `FINGERPRINT_BYTE`: once immediately before consuming one canonical
    serialization byte;
22. `CUDA_ITEM`: once per logical candidate assigned to a kernel, once per
    4,096-byte transfer page, and once per synchronized launch completion.

`MEMORY_PAGE` counts `ceil(bytes / 4096)` for each named storage operation;
zero bytes emit zero events. `CUDA_ITEM` does not replace `MEMORY_PAGE`.

Canonical resolutions use four stable LSD 8-bit radix passes over
`resolution_id`. Canonical observations use stable LSD 8-bit radix passes in
this least-significant-key-first sequence:
`observation_id:u64` (8), `frequency_hz_q20:i64` (8),
`detector_id:i32` (4), `resolution_id:u32` (4), and
`center_sample:u64` (8), for exactly 32 passes. Signed radix keys are the
two's-complement bit pattern XOR the type's sign bit. Every pass clears 256
buckets, classifies every record, performs 256 prefix updates, and scatters
every record. Stability defines all ties.

All other production ordering uses stable bottom-up merge sort. Starting with
run width one, each pass merges adjacent runs left-to-right; one
`MERGE_COMPARE` precedes each comparison while both runs are non-empty, equal
keys select the left item, and one `MERGE_MOVE` precedes every output record.
Run width doubles with checked arithmetic. Buffers alternate; if the final
records are not in the designated canonical buffer, exactly `N` final
`MERGE_MOVE` events copy them back. No library sort participates in the
work-law trace.

The report publishes all 22 counters in the order above and a checked sum.
A conservative formula MAY reject an impossible input early, but cannot
replace events that actually execute.

Pass 1 consumes its own validation, snapshot, canonicalization and comparison
work. Before any payload write it atomically reserves the exact remaining
stage and commit event counts; if the remaining budget is insufficient, the
call fails before event `k`. Every `k-1` prefix budget is testable.

The atomic tail is exactly:

`path_count + entry_count + 1 report` `COMMIT_RECORD` events.

Every stage push charges `STAGE_RECORD` before the push. Therefore allocation,
staging and all data-dependent analysis may fail safely; only the pre-reserved
tail remains when the first caller payload byte is copied.

## Snapshot, storage and handle law

- Inputs are copied to bounded counted storage before semantic validation.
  Callers SHALL NOT mutate input storage concurrently with the call.
- Every non-empty byte range in this list SHALL be pairwise disjoint from every
  other range: `resolutions`, `observations`, `edges`, `graph_manifest`,
  `path_manifest`, `paths`, `entries`, and `report`. Thus report/input,
  report/payload, paths/entries, input/input and input/payload aliasing are all
  forbidden. Empty edge input may use null only when `edge_count == 0`;
  preflight uses null `paths` and `entries` with both capacities zero; fill
  requires both payload pointers non-null. All non-null pointers satisfy
  `alignof(pointed_type)`.
- Fingerprints are diagnostic cache identities only. Admission always compares
  every canonical field.
- Canonical fingerprints serialize named unsigned/signed integer fields in
  fixed little-endian order. They never hash C padding, object
  representation, floating point, NaNs, signed zero, or compiler-dependent
  structure bytes.
- Each arena reference is `(index, generation)`. Allocation increments a
  non-zero generation with checked wrap rejection; the deterministic free list
  cannot reuse a slot while any child, reservoir, terminal, reconstruction or
  caller-visible handle owns the old generation.
- Refcount overflow, underflow, rank inversion, stale generation and ownership
  mismatch are recoverable checked failures, never `terminate`.
- One counting resource owns every PMR allocation. A test-only global
  allocation tripwire proves that no project-controlled heap allocation occurs
  after analyzer initialization. Host, device, reserved, committed and
  peak-live bytes are reported separately.

## Exact C-ABI failure semantics

**Amended by R-199.** Rows 1 through 5 remain absolute. After the bounded
report transaction begins, rows 6 through 8 are semantic checkpoints and row
9 is a per-operation resource guard. The complete proof and test obligations
are in
[R-199 R-197 Failure-Precedence Amendment](R199_R197_PRECEDENCE_AMENDMENT_2026-07-29.md).

The exact mapping is:

1. null/count/pointer-pair, alignment, ABI size/version or invalid report header
   -> `INVALID_ARGUMENT`; invalid report header writes nothing;
2. checked pointer-range/product overflow -> `PROFILE_BOUND`,
   `PROFILE_BOUND` termination;
3. any forbidden overlap -> `INVALID_ARGUMENT`;
4. reserved-field or enum failure -> `INVALID_ARGUMENT`;
5. any hard ceiling, invalid caller resource declaration, or inability to
   reserve the diagnostic stage/commit pair -> `PROFILE_BOUND`; runtime
   exhaustion of a valid declaration is row 9;
6. malformed canonical resolution/observation/edge relation ->
   `INVALID_ARGUMENT`;
7. expected preflight identity absent on fill -> `INVALID_ARGUMENT`; present
   but stale -> `HASH_MISMATCH`, `STALE_INPUT` termination;
8. insufficient path or entry capacity -> `OUTPUT_TOO_SMALL`,
   `OUTPUT_TOO_SMALL` termination;
9. work, counted host/device memory, frontier, state, entry, path, depth or
   exact-small exhaustion -> `PROFILE_BOUND`, `PROFILE_BOUND` termination;
10. counted-resource upstream failure, `std::bad_alloc`, CUDA allocation
    failure -> `OUT_OF_MEMORY`, `ENVIRONMENTAL_OOM` termination;
11. CUDA launch/transfer/synchronization failure, checked internal arithmetic
    impossible under validated ceilings, generation/refcount/ownership/rank
    violation, other `std::exception`, or `catch (...)` ->
    `MALFORMED`, `INTERNAL_MALFORMED` termination.

Rows 1 through 5 follow this numbered order and the first failure wins. After
row 5, the first determinable failure wins: a row 6, 7 or 8 predicate wins when
it is known before resource exhaustion; row 9 wins when the declared bound is
exhausted before that predicate can be determined. Implementations MUST NOT
perform hidden work to discover a later semantic result. Within one checkpoint,
fields are examined in function-argument order, then structure declaration
order, then ascending array index. No asynchronous CUDA failure may cross the
boundary: a CUDA path synchronizes inside the call.

`paths`, `entries`, and their canaries remain byte-identical for every
non-success status. `report` is the only diagnostic output allowed to change
after its own header validates: it is written once from a local staged report,
sets both written counts to zero on failure, and may expose required counts,
termination, exact consumed work, memory peaks and fingerprints. If the report
header itself is invalid, no caller byte is written.

The R-190 edge call has the same transactional rule. Preflight is exactly
`output == NULL`, `output_capacity == 0`, and a non-null disjoint
`output_count`. Fill requires non-null aligned `output`; `output`,
`output_count`, both manifests and all input arrays are pairwise disjoint.
Canonical edges are staged completely. Before the first caller write the call
reserves exactly `edge_count` payload `COMMIT_RECORD` events plus one
`COMMIT_RECORD` for `output_count`.

- preflight-success tail is exactly one `COMMIT_RECORD` for `output_count`;
- `OUTPUT_TOO_SMALL` tail is exactly one `COMMIT_RECORD` for `output_count`;
- fill-success tail is exactly `edge_count + 1` `COMMIT_RECORD` events;
- preflight success writes the required count only;
- fill success writes all edges and then the identical required count;
- `OUTPUT_TOO_SMALL` writes the required count but leaves the edge payload
  unchanged;
- every other non-success status leaves both edge payload and `output_count`
  byte-identical;
- a null, misaligned or overlapping `output_count` produces
  `INVALID_ARGUMENT` and no write.

R-190 uses the same hard `2^48-1` internal work ceiling even though that legacy
call does not expose the event ledger.

One `STAGE_RECORD` and one `COMMIT_RECORD` token for the R-191 diagnostic
report are reserved as one rollback-safe pair immediately after the report
header, manifest hard ceiling and caller work limit validate, before semantic
analysis. Only after both reservations succeed is the stage token consumed to
initialize the local diagnostic report; the commit token remains reserved for
its one final publication. Both tokens are included in the published ledger.
If the manifest cannot reserve both tokens, the partial reservation is
cancelled, the report remains unchanged, and the call returns `PROFILE_BOUND`.
Payload commit tokens are reserved only after payload staging completes.

The reservation transition occurs after precedence row 5 above. Failures in
rows 1 through 5 leave `report` byte-identical even when its header is valid.
Failures in rows 6 through 11 commit exactly one local diagnostic report using
the already reserved token. The general failure-report rule applies only after
that transition.

## ABI migration

R-197 introduces path ABI version 3 and the new exported symbol
`resonith_partial_graph_paths_cpu_v3`. The v3 manifest replaces the former
reserved-alignment word with `work_ledger_version`, which SHALL equal one. The
v3 report adds:

- 22 `u64 work_event_counts` in the frozen event order;
- `reserved_host_bytes`, `committed_host_bytes`, `peak_live_host_bytes`;
- `reserved_device_bytes`, `committed_device_bytes`,
  `peak_live_device_bytes`;
- `INTERNAL_MALFORMED = 5` to the termination enumeration.

Record sizes and every offset receive v3 static assertions and cross-language
layout fixtures. The v3 input/output fingerprint domains described below apply
only to v3 and serialize the v3 ABI value and `work_ledger_version`; report
metrics never enter either payload fingerprint.

The existing v2 symbol and packed v2 layouts remain declared in the
experimental compatibility header for one migration cycle. The v2 symbol is
implemented as a safe rejection stub: it writes no payload or report byte and
returns `UNSUPPORTED_VERSION`. No v2 result is admitted after R-197. R-190
retains graph ABI version 1 and its existing symbol because its record layouts
do not change; only its implementation contract becomes transactional.

The complete packed v3 declarations are:

```c
#define RESONITH_PARTIAL_PATH_V3_WORK_EVENT_COUNT 22U

typedef struct resonith_partial_path_manifest_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t second_order_law_version;
    uint32_t protected_band_count;
    uint32_t k_value_per_state;
    uint32_t k_continuity_per_state;
    uint32_t top_k_value;
    uint32_t top_k_continuity;
    uint32_t top_k_protected;
    uint32_t protected_paths_per_band;
    uint32_t minimum_path_observations;
    uint32_t maximum_path_observations;
    uint32_t exact_set_candidate_limit;
    uint32_t amplitude_floor_q16;
    uint32_t amplitude_residual_weight_q8;
    uint32_t work_ledger_version;
    uint64_t frequency_sigma_floor_hz_q20;
    int64_t birth_cost_bits_q8;
    int64_t death_cost_bits_q8;
    int64_t score_saturation;
    uint64_t maximum_path_records;
    uint64_t maximum_total_entries;
    uint64_t maximum_frontier_states;
    uint64_t maximum_state_records;
    uint64_t maximum_work_units;
    uint64_t maximum_managed_bytes;
    uint64_t maximum_device_bytes;
    uint64_t expected_input_fingerprint[4];
    int64_t protected_band_upper_hz_q20[127];
    uint32_t reserved[8];
} resonith_partial_path_manifest_v3;

typedef struct resonith_partial_path_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t path_id;
    uint64_t entry_offset;
    uint32_t entry_count;
    uint32_t family_flags;
    uint64_t terminal_observation_id;
    int64_t continuity_score_q8;
    int64_t potential_node_value_q8;
    int64_t uncertainty_leakage_penalty_q8;
    int64_t provisional_program_cost_q8;
    int64_t selection_score_q8;
    uint64_t phase_error_sum_u64;
    uint32_t phase_error_count;
    uint32_t ownership_conflict_count;
    uint32_t protected_band_id;
    uint32_t value_rank;
    uint32_t continuity_rank;
    uint32_t protected_rank;
    uint32_t flags;
    uint32_t reserved[5];
} resonith_partial_path_v3;

typedef struct resonith_partial_path_entry_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint64_t observation_id;
    uint64_t incoming_edge_candidate_id;
    uint32_t ownership_component;
    int32_t second_order_cost_q8;
    uint32_t flags;
    uint32_t reserved[3];
} resonith_partial_path_entry_v3;

typedef struct resonith_partial_path_report_v3 {
    uint32_t struct_size;
    uint32_t abi_version;
    uint32_t termination;
    uint32_t solver;
    uint64_t required_path_count;
    uint64_t required_entry_count;
    uint64_t written_path_count;
    uint64_t written_entry_count;
    uint64_t raw_state_count;
    uint64_t frontier_peak;
    uint64_t work_units;
    uint64_t peak_live_managed_bytes;
    uint64_t selected_candidate_count;
    uint64_t selected_path_count;
    uint64_t internal_conflict_count;
    uint64_t cross_path_conflict_count;
    uint64_t score_saturation_count;
    uint64_t value_family_count;
    uint64_t continuity_family_count;
    uint64_t protected_family_count;
    uint64_t duplicate_state_count;
    uint64_t terminal_retained_state_count;
    uint64_t state_k_discarded_count;
    uint64_t state_arena_peak;
    uint64_t value_family_presented_count;
    uint64_t continuity_family_presented_count;
    uint64_t protected_family_presented_count;
    uint64_t value_family_discarded_count;
    uint64_t continuity_family_discarded_count;
    uint64_t protected_family_discarded_count;
    uint64_t output_deduplicated_count;
    uint64_t bound_rejected_count;
    uint64_t input_fingerprint[4];
    uint64_t output_fingerprint[4];
    uint64_t work_event_counts[22];
    uint64_t reserved_host_bytes;
    uint64_t committed_host_bytes;
    uint64_t peak_live_host_bytes;
    uint64_t reserved_device_bytes;
    uint64_t committed_device_bytes;
    uint64_t peak_live_device_bytes;
    uint32_t flags;
    uint32_t reserved[7];
} resonith_partial_path_report_v3;
```

All declarations are inside one `#pragma pack(push, 1)` /
`#pragma pack(pop)` region. Exact sizes are manifest `1232`, path `136`, entry
`48`, report `560` bytes. Manifest offsets are:
`work_ledger_version=60`, `frequency_sigma=64`, `maximum_path_records=96`,
`maximum_work_units=128`, `maximum_managed_bytes=136`,
`maximum_device_bytes=144`, `expected_fingerprint=152`,
`protected_bands=184`, `reserved=1200`.
Report offsets through `output_fingerprint=272` equal v2; then
`work_event_counts=304`, `reserved_host=480`, `committed_host=488`,
`peak_host=496`, `reserved_device=504`, `committed_device=512`,
`peak_device=520`, `flags=528`, `reserved=532`. Path and entry offsets are
identical to their v2 layouts. Every listed value is a compile-time assertion.

## Canonical fingerprint law v1

Both fingerprint domains use unsigned modulo-`2^64` arithmetic. The four
initial states are
`cbf29ce484222325`, `84222325cbf29ce4`, `9e3779b185ebca87`,
`d6e8feb86659fd93`; the lane primes are `100000001b3`,
`100000001c9`, `100000001e7`, `10000000233`. For each serialized byte `b` and
lane `i` from zero through three:

`state[i] = (state[i] XOR ((b + 53*i) mod 256)) * prime[i] mod 2^64`.

All unsigned integers serialize at their declared width, least-significant byte
first. Signed integers serialize their width-preserving two's-complement bit
pattern. Counts serialize as `u64`. Arrays serialize every declared element in
ascending index order. Reserved fields are validated zero and still serialized.

The input domain starts with the exact eight bytes `52 50 47 46 01 00 00 00`
(`RPGF`, version 1), followed by `work_ledger_version:u32`, resolution,
observation and edge counts as `u64`, then:

1. graph-manifest fields in C declaration order;
2. path-manifest fields in C declaration order, except all four
   `expected_input_fingerprint` lanes serialize as zero;
3. canonical resolutions in the radix order above, every field in declaration
   order;
4. canonical observations in the radix order above, every field in declaration
   order;
5. edges in ascending `candidate_id`, every field in declaration order.

Structure padding and host object bytes are never serialized.

The output domain starts with `52 50 4f 46 01 00 00 00` (`RPOF`, version 1),
then path and entry counts as `u64`, then paths in ascending `path_id` and
entries in path/entry order. Every logical field serializes in C declaration
order, including zero reserved fields. Fingerprint golden vectors include zero,
one, extrema, signed negative and multi-record cases.

## Allocation-tripwire scope

The global allocation tripwire is armed before the first tested C-ABI entry,
not after initialization. A thread-local permit exists only inside the supplied
counting resource's checked upstream call and inside explicitly counted CUDA
runtime allocation/transfer scopes. Lazy/static project initialization,
default allocators and repeated first-use allocation outside those scopes fail
the gate. The first call and every repeated call run under the same rule.

## Required evidence

- `limit-1` failure and `limit` success for every resource dimension;
- unchanged canaries for every non-success class;
- independent arbitrary-precision exact-small oracle;
- exhaustive small cases, ties, extrema, permutations and forged edges;
- generation-safe release/reuse at every arena boundary;
- repeat/order-invariant CPU output and exact CUDA tile parity at
  1/31/32/255/256/1024;
- deterministic reachability of every fuzz mutation plus sanitizer canary
  checks;
- structure-aware mutation that repairs dependent sizes, IDs and fingerprints,
  branch-specific seed corpora, explicit per-branch reachability counters,
  stateful preflight/fill sequences, allocator failure injection and host/device
  canaries;
- a global-allocation tripwire after initialization and separate host/device
  accounting;
- null/length, alignment, checked-range, overlap, version and status-precedence
  matrices;
- work-event golden vectors proving that budget `k-1` prevents event `k`;
- field-serialized fingerprint golden vectors across MSVC, Clang and GCC;
- one-commit Windows, Linux sanitizer, Android and iOS gates.

Quantitative campaign floors are frozen as follows:

- the pure hard-ceiling validator covers `ceiling-1`, `ceiling`, and
  `ceiling+1` for every table row, plus `0`, `1`, and every checked product;
- the independent arbitrary-precision oracle executes the exact finite
  complete-canonical-union domain in the hashed case manifest: every
  observation permutation through five observations and the first 64 distinct
  SplitMix Fisher-Yates permutations for six and seven;
- deterministic randomized CPU campaigns execute 10,000 cases with SplitMix64 state
  `0x9e3779b97f4a7c15`; CPU/CUDA parity executes 10,000 cases for every required
  tile size with seed `0xd1b54a32d192ed03`;
- each parser/API structured-fuzz target executes at least 2,000,000 inputs and
  15 minutes, whichever finishes later; stateful/fault-injection targets
  execute at least 1,000,000 sequences and 10 minutes, whichever finishes
  later; TSan shared-state campaigns execute at least 100,000 sequences;
- the fixed seed corpus contains empty, one-record, every status row, every
  event kind, every hard-ceiling boundary encoding, stale fingerprint,
  overlapping-range descriptors, maximal-depth reconstruction, every arena
  transition and every CUDA error class;
- every declared semantic reachability counter is hit at least 100 times and
  line/branch coverage for the two exported analyzer functions is at least
  95%/90%. Any sanitizer, leak, canary, nondeterminism, status-precedence,
  oracle or parity failure is an unconditional NO-GO.

The finite oracle and randomized input definitions are frozen by
`R197_CASE_GENERATOR_V1_2026-07-29.md`. Its source hash is part of this review;
changing the generator, value alphabet, distributions or rejection behavior
invalidates the audit and requires a new case-manifest version.

Frozen case-manifest SHA-256:
`10e24fa8721dfe69c2e1be82f9ffcc83e5dc7b32da0a038d29ec46b943d761bc`.

The final report may claim only bounded analyzer infrastructure. Any predictor,
syntax, compression, Opus or Orkela claim is forbidden by this work package.
