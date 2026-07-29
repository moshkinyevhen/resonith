# R-202 Stateful ABI and Semantic Coverage Gate

Date: 2026-07-29

Scope: Step-9 R-190/R-191 ABI, allocation, fuzz, and coverage infrastructure

Codec algorithm or bitstream change: **no**

Status: **ACCEPTED — INDEPENDENT STEP-9 GO**

## Corrected staging-boundary evidence

The attempted public-ABI staging witness is rejected. Its strongest permitted
fixture produced exactly 256 paths, 1,048,576 entries, and 4,365 edges in
1.702 seconds, but pre-staging historical peak was 116,675,808 bytes versus
100,732,928 bytes of complete legacy-plus-v3 staging.

Independent allocation analysis then proved the wrapper outcome unreachable
in the current 64-bit managed implementation. For path count `P` and entry
count `E`:

```text
historical_peak >= 108E + 272P
stage_bytes       =  96E + 272P
```

Successful preflight already requires historical peak no greater than the
immutable managed limit. The wrapper therefore cannot later observe staging
above that limit. No public witness, production failpoint, or
coverage-motivated allocator behavior change is admitted.

The checked overflow and limit arithmetic is now one pure internal helper used
by production and directly tested at:

- exact limit;
- one byte below the required limit;
- path-product overflow;
- entry-product overflow;
- additive overflow.

## Exact source evidence

```text
native/src/partial_graph.cpp
F7EBB9ADFA4B49B96368C189EC4A5980A7CB14EF3D1CAD08E1A08AC2E970A415

native/src/partial_graph_stage_budget.hpp
0E9250CA66A6EB884D47B20DC065804766C3FA269DF03C81665835E508A11D41

native/tests/partial_graph_test.cpp
BCB33EDE520D0605130837AEA2172328F62F35FC7C8231B5CC0CF0AEC205D3B0

native/tests/partial_graph_coverage_contract.json
D86F698B1C1052B84BD8E74E220C88C07D86F224D386B7270FD31A8BB10F315B

scripts/enforce_partial_graph_coverage.py
FC91579F5D5E35C6304F12F796D16CC3D334A600769E67F7CA71EA2DCC30E146

.github/workflows/mobile.yml
AE104082453749077BA375A9AF16937EB80AE6656D69DB5D6947EBF0EE275263
```

## Native focused gates

Warnings-as-errors C++23 results:

| Toolchain | Focused tests | Result | Wall time |
|---|---:|---|---:|
| LLVM/Clang 22.1.8 | 5/5 | pass | 9.21 s |
| GCC 16.0.1 | 5/5 | pass | 10.60 s |

Each run includes:

- public ABI conformance;
- armed global-allocation tripwire;
- allocation-ordinal injection;
- concurrent invocation;
- 100,000-case adversarial smoke.

The canonical native report is:

```json
{"schema":"resonith-r190-native-edge-cpu-1","edge_count":9,"path_count":8,"reserved_host_bytes":18684,"committed_host_bytes":18684,"peak_live_host_bytes":18684,"device_bytes":0,"work_sweep_max":51962,"stage_budget_helper":true,"deterministic":true,"predictor_integrated":false}
```

## Strict semantic coverage

All five deterministic drivers remain mandatory, but only
`resonith_partial_graph_test` writes to `profiles/canonical`. Allocation
tripwire, allocation ordinal, concurrency, and fuzz smoke write to
`profiles/supplemental`. Both inventories are retained and hashed separately.
Only non-empty canonical profiles may enter `llvm-profdata`, `llvm-cov`
report, export, or show.

The contract freezes:

- the complete source hash;
- the helper hash;
- exact proof-range hashes;
- every uncovered source line;
- every uncovered true or false branch outcome;
- a disposition and reason for every gap.

Admission remains bound to Ubuntu 24.04 and the exact
`Ubuntu LLVM version 18.1.3` identity. Any toolchain mismatch, new miss, stale
miss, source drift, helper drift, or proof-range drift fails before
percentages are evaluated.

Local single-canonical-profile diagnostic:

| Metric | Raw | Predicted proof-adjusted | Floor |
|---|---:|---:|---:|
| Lines | 842 / 905 = 93.0387% | 842 / 879 = 95.7907% | 95% |
| Branch outcomes | 207 / 230 = 90.0000% | 207 / 226 = 91.5929% | 90% |

Exactly 26 lines and four branch outcomes are excluded as
allocation- or ledger-invariant unreachable. All remaining uncovered
locations remain in the denominator as explicit tracked gaps.

These percentages are diagnostic predictions, not accepted GitHub evidence.
The first Ubuntu canonical-only artifact may seed a replacement exact
line/outcome contract. A second independent run must reproduce the complete
set and count totals before the contract can be frozen.

The first canonical-only GitHub artifact, run `30452280336` attempt 1,
correctly failed the older mixed-profile contract. Its exact candidate
identity was
`9EC256698895A2219B4DFFE01676E9CCC9B7E9A2D9DAC2483ED8B4DDC1368C55`.
It exposed three reachable canonical omissions: R-190 environmental OOM,
invalid observations after a valid manifest, and entry-only insufficient v3
capacity. Independent review returned NO-GO for recording any of them as a
tracked or unreachable gap.

The canonical conformance test now exercises all three and verifies return
status, output-count/report state, and complete caller-payload immutability.
The unchanged production source builds with warnings-as-errors and all five
focused partial-graph gates pass:

| Toolchain | Result | Focused time |
|---|---:|---:|
| Clang 22 / C++23 | 5 / 5 | 10.28 s |
| GCC 16 / C++23 | 5 / 5 | 11.89 s |

These local results do not freeze a coverage profile. Two independent
post-test-change Ubuntu LLVM 18.1.3 canonical-only artifacts with identical
target-function totals and exact missing line/outcome sets remain mandatory.

## Rejected MinGW admission evidence

LLVM-MinGW 22 remains useful for build and diagnostic coverage, but it is not
an admission authority. Its export reported both false negatives and a
corrupt counter:

```text
edges 1224:9 true = 0 despite an explicit exercised test
edges 1234:9 true = 0 despite an explicit exercised test
paths 7465:12 true = 1 for an invariant-impossible snapshot failure
paths 7466:12 true = 9,223,372,036,854,775,807
```

The independent auditor rejected both automatic dual-profile inference and a
union of outcomes. A regression must not be able to impersonate another
toolchain profile.

Two Ubuntu runs then produced different missing outcomes from mixed profiles
despite identical source and tests. Those 96.1320% line and 92.4779% branch
results are revoked as admission evidence. Their raw artifacts remain negative
evidence of cross-binary counter incompatibility.

## Acceptance boundary

This is a focused analyzer-infrastructure gate. It changes no codec syntax,
encoded bytes, decoded samples, PCM, entropy policy, or RDO behavior, so the
complete music/Opus generation gate is not triggered.

Step 9 is accepted on source revision
`ecfee1a3ed4a2a62848da91c91acc098f873cbd6`. The same revision passed the
GitHub sanitizer, thread-sanitizer, Android, Apple, Linux, Windows, fuzz, and
semantic-coverage jobs and received final independent post-implementation GO.
Step 10 remains the final R-191 conformance and admission audit.

## Independent post-implementation audit

Initial verdict: **GO — zero blocking defects for the semantic exclusions and
strict missing-set design**.

The auditor independently verified:

- the stage-budget public-wrapper proof and direct helper boundaries;
- the `peak_live` induction against the immutable allocator limit;
- the no-intervening-mutation reservation/first-emission ledger invariant;
- translation of every relevant upstream `std::bad_alloc`;
- exactly 26 excluded lines and four excluded branch outcomes;
- adjusted coverage of 96.1320% lines and 92.4779% branches;
- complete source, helper, and six proof-range hashes;
- exact missing-set equality and stale/new-miss rejection.

All other uncovered locations remain conservative tracked gaps. The audit
explicitly notes that the misaligned-pointer rejection is caller-reachable
and must not be excluded, while the R-190 managed-bound catch remains tracked
until a valid witness or complete upper-bound proof exists.

Cross-toolchain verdict: **NO-GO for LLVM-MinGW 22 admission and automatic
dual-profile selection**. The sole-acceptance Ubuntu LLVM 18 contract and
explicit version binding implement the auditor's required safe correction.

Corrected-design verdict: **GO — zero blocking defects**. The auditor verified
the workflow platform binding, exact version `re.fullmatch`, fail-closed check
ordering, exact 21-outcome and 60-line Ubuntu profiles, unchanged four-branch
and 26-line semantic exclusions, recorded toolchain identity, and canonical
96.1320%/92.4779% replay.

Profile-separation verdict: **GO**. Semantic merge/report/export/show must
consume only non-empty canonical profiles. Supplemental profiles remain
mandatory, inventoried, and hashed but cannot enter semantic counters. Two
independent identical Ubuntu LLVM 18 canonical-only runs are required before
freezing the final contract.

Final Step-9 verdict: **GO — zero remaining Step-9 blockers**.

The complete GitHub evidence run
[`30471669754`](https://github.com/moshkinyevhen/resonith/actions/runs/30471669754)
passed all nine evidence jobs and the aggregate mobile gate:

- the sanitizer/fuzz job completed in 32 minutes 49 seconds, below the
  40-minute admission ceiling;
- 20/20 sanitized CTests passed with zero ASan, UBSan, LSan, or crash findings;
- four fixed libFuzzer seeds completed exactly 500,000 units each and
  2,000,000 total, with per-seed durations of 1,701--1,748 seconds, coverage
  `4178--4179`, feature counts `14431--14475`, and peak RSS `473--478 MiB`;
- exact semantic reachability covered all eleven declared branches at least
  100 times;
- exhaustive allocation injection covered `10 + 16 + 313 + 613 = 952`
  reachable ordinals and 2,864 calls, reproduced trace hash
  `56204c224ae7c4c3`, and terminated with zero live allocations;
- TSan passed eight threads and 100,000 independent transactional sequences;
- iOS device arm64, iOS simulator arm64/x86_64, macOS, Android arm64
  compile/link, Android x86_64 API-26 runtime, Linux canonical coverage, and
  the aggregate gate all passed;
- the canonical Ubuntu LLVM 18.1.3 report measured raw
  93.37016574585635% line and 90.8695652173913% branch coverage, then exact
  proof-adjusted 96.13196814562002% line and 92.47787610619469% branch
  coverage;
- the sanitizer artifact's 13/13 SHA-256 inventory and the coverage artifact's
  11/11 SHA-256 inventory matched locally.

The companion repository test run
[`30471677677`](https://github.com/moshkinyevhen/resonith/actions/runs/30471677677)
passed all ten Windows, Linux, macOS, Android, sanitizer/libFuzzer, reference,
and decoder-in-loop jobs. The accepted GitHub merge revision is
`9e0691c88b1b07515e921060dc8f143b698299c3`.

Retained local evidence:

- `build/github-r202-final-30471669754-sanitizers-a1`;
- `build/github-r202-final-30471669754-coverage-a1`;
- `build/github-r202-final-30471669754-index-a1`.

The final independent auditor reproduced the exact count, duration,
reachability, ordinal, transactionality, sanitizer, TSan, platform, coverage,
and inventory gates and returned binary **GO** for Step 9. This verdict does
not admit R-191 codec behavior; that decision remains Step 10.
