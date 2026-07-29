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
