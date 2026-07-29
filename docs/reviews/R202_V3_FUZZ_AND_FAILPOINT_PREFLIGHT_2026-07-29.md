# R-202 Stateful ABI-v3 Fuzz and Failpoint Preflight

Date: 2026-07-29
Status: **DESIGN GO; implementation required**

## Independent red-team finding

The existing partial-graph fuzzer is not evidence for R-191:

- it sends path mutations to the retired v2 no-write rejection stub;
- it has no v3 preflight/fill state machine;
- it does not repair dependent counts, IDs, canonical edges, and fingerprints
  before injecting one intended fault;
- its smoke executable proves dispatcher execution, not semantic branch
  consumption;
- it has no exhaustive fail-at-allocation-ordinal campaign;
- Android symbol evidence still names v2 without requiring v3.

The reviewer approved a bounded remediation that changes test infrastructure
only. It does not change R-190/R-191 algorithms, ABI, work law, fingerprints,
arena ownership, memory semantics, or bitstream syntax.

## Required architecture

### One shared structured v3 driver

A descriptor-driven driver SHALL serve both the libFuzzer entry and the
portable deterministic smoke executable. It SHALL:

1. construct a valid canonical R-190 fixture;
2. regenerate canonical edges after every valid input mutation;
3. run v3 preflight;
4. install the returned canonical fingerprint before fill;
5. inject missing/stale/forged/capacity/resource faults only after dependent
   repair;
6. assert exact status, termination, report phase, typed-ledger sum,
   host-memory ordering, CPU device zeros, and payload/report canaries;
7. increment a branch counter only after the expected downstream outcome is
   observed.

The retired v2 symbol receives one directed compatibility case proving
`UNSUPPORTED_VERSION` and no writes. It is excluded from mutation fuzzing.

### Structured mutation families

- canonical first/repeated preflight/fill, reordered logical input, and exact
  output/fingerprint/ledger determinism;
- every ABI pointer/count/alignment/range/alias/header/reserved/hard-ceiling
  row;
- every logical resolution, observation, graph-manifest, and v3-manifest
  field in repaired-valid and exactly-one-invalid forms;
- every presented edge field plus missing, duplicate, extra, reordered, and
  forged candidate streams;
- missing/stale identity and path/entry capacity boundaries;
- work, host bytes, path, entry, frontier, state, depth, and exact-set
  `limit-1/limit` boundaries;
- preflight/fill, stale-after-preflight, capacity-failure retry, OOM retry,
  repeated call, and independent concurrent-call sequences.

Every deterministic branch seed SHALL reach its intended branch at least 100
times in the final campaign. Coverage is an independent backstop: at least 95%
line and 90% branch coverage for the two public R-190/v3 entries.

## Allocation-ordinal law

A private failing PMR upstream uses the existing thread-local test hook. For
each successful allocation trace:

1. record `(ordinal, bytes, alignment)` for a no-failure baseline;
2. fail exactly ordinal `1..N`;
3. run ordinal `N+1` as the success control;
4. repeat the series and require identical JSONL and hash.

Fixtures cover empty, one-record, R-199 exact-small, and bounded-greedy/reclaim
paths for R-190 preflight/fill and v3 preflight/fill.

Every injected failure SHALL prove:

- exact environmental-OOM status at an allocation-reachable checkpoint;
- no R-190 output/count publication;
- unchanged v3 path/entry payload and canaries;
- environmental-OOM report, zero written counts, exact typed-ledger sum;
- exact trace-derived reserved/committed/live high-water values;
- zero terminal upstream allocations/bytes;
- exact CPU device zeros and zero CUDA work;
- a subsequent uninjected retry equal to the baseline.

Capacity and deterministic resource boundaries are tested separately at
`exact-1/exact`.

## Platform evidence

- Linux Clang: ASan+UBSan+LSan CTest; structured fuzz for both 2,000,000 inputs
  and 15 minutes; stateful/fault fuzz for both 1,000,000 sequences and 10
  minutes; exhaustive ordinal campaign.
- Linux Clang TSan: 100,000 independent concurrent-call sequences with no
  shared caller buffers.
- Windows x64 MSVC: warnings-as-errors, ASan CTest, v3 corpus, and exhaustive
  ordinal campaign; no false UBSan claim.
- macOS ARM64 AppleClang: ASan+UBSan CTest, deterministic stateful corpus, and
  ordinal campaign.
- Android x86-64 API 26: emulator execution of conformance, v3 smoke, and
  ordinal campaign under supported NDK sanitizers.
- Android ARM64 and iOS device/simulator variants: strict compile/link,
  layout/symbol checks, and runtime claims only where the runner actually
  executes them.

Only authoritative Linux jobs repeat the quantitative long fuzz floors.

## Kill gates

Step 9 is NO-GO on any sanitizer/leak/race/canary finding, unreachable branch,
coverage miss, nondeterministic seed/output/fingerprint/ledger/ordinal trace,
wrong status precedence or report phase, memory mismatch, non-zero CPU device
metric, non-zero terminal allocation, or missing R-190/v3 export.

Step 9 publishes source/toolchain/corpus hashes, branch-hit JSON, coverage,
sanitizer logs, ordinal JSONL/hash, and platform results from one source
revision. It does not admit R-191; final admission remains Step 10.

## Independent staging-guard witness re-audit

The first checkpoint proposed changing only `top_k_protected` from 1 to 128.
The independent reviewer returned **NO-GO**.

Every proposed terminal path contains a 512-observation 440 Hz prefix. Its
median frequency is therefore 440 Hz, so all protected candidates occupy one
protected band. `protected_paths_per_band = 1` discards 127 candidates before
the later global protected reservoir can apply `top_k_protected`.

The unchanged fixture can emit at most one value, one continuity, and one
protected path: three paths and 1,542 entries. Complete legacy-plus-v3 staging
is at most 148,848 bytes. Two 648-observation snapshots and one 647-edge
snapshot already require at least 212,472 managed bytes before maps, arena
state, identities, and output. The proposed single-field change therefore
cannot satisfy `historical_peak < staging_bytes`.

The reviewer initially permitted a corrected, test-only adversarial fixture
with both protected limits set to 128. It produced the exact 128 paths and
65,792 entries, but its measured historical peak was 12,310,952 bytes versus
6,350,848 staging bytes. That candidate is killed.

The failure does not prove the staging guard unreachable. At output
materialization, the approximate persistent core is:

```text
legacy output                         136P + 48E
protected-family and union identities       32E
ownership arrays                              4E
historical core                       136P + 84E
complete legacy-plus-v3 staging       272P + 96E
```

Staging retains an asymptotic margin of `136P + 12E`. A fully shared prefix
keeps arena/input growth near path length plus output count rather than
`P × path_length`. The 65,792-entry candidate also crossed the 65,536 vector
capacity boundary and paid for a 131,072-entry internal capacity.

The independent reviewer returned **GO for one final bounded experiment only**:

- 4,094 shared-prefix observations;
- 16 intermediate branches and 16 terminal neighbors each;
- exactly 256 protected output paths of length 4,096;
- exactly 1,048,576 serialized entries;
- minimum and maximum path length both 4,096;
- value/continuity state and output limits of one;
- protected per-band and global limits of 256;
- common ownership to keep selection/conflict storage empty;
- sufficient bounded frequency jump/slope to retain all terminal groups.

The exact staging target is:

```text
2 × (256 × 136 + 1,048,576 × 48) = 100,732,928 bytes
```

The entry count is an exact libstdc++ power-of-two capacity and only 1,293
entries below the corresponding MSVC-like 1.5-growth capacity. The predicted
historical peak was 91–94 MB. The measured experiment produced the exact
counts and 4,365 edges in 1.702 seconds, but historical peak was 116,675,808
bytes: 15,942,880 bytes above staging. The candidate is killed.

The final independent allocation audit identified the missing peak component
and proved the wrapper branch unreachable in the current 64-bit managed
implementation. During the final geometric growth of the 48-byte legacy entry
vector, old and new buffers coexist. Current supported STL growth is at most
2x, so that boundary contributes at least `72E`. Family identities, copied
union identities, and ownership arrays contribute `16E + 16E + 4E`, while
family-entry and union-candidate backing contributes `272P`. Therefore:

```text
historical_peak >= 108E + 272P
stage_bytes       =  96E + 272P
```

For every non-empty output, `historical_peak >= stage_bytes + 12E`; for an
empty output, staging is zero. Successful preflight already requires
`historical_peak <= maximum_managed_bytes`, so the later predicate
`stage_bytes > maximum_managed_bytes` cannot be true.

The independent verdict is:

- **NO-GO** for any further public-ABI witness;
- **NO-GO** for a production failpoint that manufactures reachability;
- **NO-GO** for allocator lifetime or reserve changes made solely for
  coverage because they alter observable peak/work/page accounting;
- **GO** to retain the defense-in-depth guard, factor its overflow and limit
  arithmetic into a pure internal helper, and test synthetic overflow,
  exact-limit, and over-limit boundaries directly;
- exact semantic allowlisting is permitted only for the unreachable wrapper
  outcome and its body, bound to the current source hash, guard hash, proof,
  and stale-entry rejection.

The failed large fixture must be removed. No report may claim that a public
R-191 input reached the wrapper guard.

## Cross-toolchain coverage correction

The first local strict contract used LLVM-MinGW 22 branch counters. The
canonical GitHub Ubuntu LLVM 18 artifact falsified their reliability:

- two explicitly exercised edge outcomes were falsely reported as zero;
- one invariant-impossible snapshot failure was falsely reported as covered;
- another invariant-impossible outcome had count `2^63 - 1`.

The independent auditor returned **NO-GO** for treating MinGW as an alternate
admission profile or selecting a profile from the observed miss set. The safe
correction is one exact Ubuntu LLVM 18 admission contract bound to verified
toolchain identity. MinGW coverage remains diagnostic only. Unioning both
sets, automatic profile inference, or accepting the corrupt non-zero counters
is prohibited.

A second Ubuntu run then falsified the remaining assumption: merging profiles
from five separately linked executables produced a different miss set despite
identical source and tests. Mapping that mixed profdata through one executable
does not make the counters compatible.

The independently approved correction separates evidence:

- `profiles/canonical` contains only
  `resonith_partial_graph_test` and is the sole semantic coverage input;
- `profiles/supplemental` contains allocation-tripwire, allocation-ordinal,
  concurrency, and fuzz-smoke executions;
- both inventories are non-empty, retained, and hashed separately;
- supplemental profiles remain mandatory behavior gates but never enter
  semantic merge, report, export, or show;
- misleading `all-linked` artifact names are prohibited;
- one Ubuntu LLVM 18 canonical run may seed a candidate contract, but two
  independent runs must have identical missing line/outcome sets and count
  totals before that contract is frozen.

Local single-profile evidence predicts 95.79% adjusted lines and 91.59%
adjusted branches. Cross-binary normalization and a monolithic-runner rewrite
are rejected.
