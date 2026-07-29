# R-202 Stateful ABI and Semantic Coverage Gate

Date: 2026-07-29

Scope: Step-9 R-190/R-191 ABI, allocation, fuzz, and coverage infrastructure

Codec algorithm or bitstream change: **no**

Status: **canonical Ubuntu LLVM 18 replay passed; replacement CI run pending**

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
196FD48B0BE99190BA5FE4CED0A3780EA8D5A6247DB30F2554FEA0334B376AAD

native/tests/partial_graph_coverage_contract.json
D86F698B1C1052B84BD8E74E220C88C07D86F224D386B7270FD31A8BB10F315B

scripts/enforce_partial_graph_coverage.py
FC91579F5D5E35C6304F12F796D16CC3D334A600769E67F7CA71EA2DCC30E146

.github/workflows/mobile.yml
B52A1569C48C27B0DD61C61CA7EDE3067E94C08B7AB4D3CC04B31C04C4FF04D6
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

All five deterministic drivers produce profile data, but `llvm-cov` receives
one canonical instrumented executable as the sole coverage mapping. This
prevents duplicate static-library mappings from selecting incompatible
counter layouts.

The contract freezes:

- the complete source hash;
- the helper hash;
- exact proof-range hashes;
- every uncovered source line;
- every uncovered true or false branch outcome;
- a disposition and reason for every gap.

Admission is bound to Ubuntu 24.04 and the exact
`Ubuntu LLVM version 18.1.3` identity. Any toolchain mismatch, new miss, stale
miss, source drift, helper drift, or proof-range drift fails before
percentages are evaluated. Negative tests confirmed rejection of a changed
source hash, a stale uncovered-line entry, and a non-admission toolchain.

Canonical Ubuntu LLVM 18 artifact replay:

| Metric | Raw | Proof-adjusted | Floor |
|---|---:|---:|---:|
| Lines | 845 / 905 = 93.3702% | 845 / 879 = 96.1320% | 95% |
| Branch outcomes | 209 / 230 = 90.8696% | 209 / 226 = 92.4779% | 90% |

Exactly 26 lines and four branch outcomes are excluded as
allocation- or ledger-invariant unreachable. All remaining uncovered
locations remain in the denominator as explicit tracked gaps.

Generated gate:

```text
build/github-r202-coverage-30450722814/coverage-gate-corrected.json
A25BEDFE50174D780E51AFDF43B8D86996811D7C89A06413046AACA7557F8BDD
```

`actionlint`, Python syntax validation, and `git diff --check` pass.

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
toolchain profile. The exact Ubuntu LLVM 18 set is therefore the sole
admission contract; MinGW results are non-admission diagnostics.

## Acceptance boundary

This is a focused analyzer-infrastructure gate. It changes no codec syntax,
encoded bytes, decoded samples, PCM, entropy policy, or RDO behavior, so the
complete music/Opus generation gate is not triggered.

Step 9 remains open until the same revision passes the GitHub sanitizer,
thread-sanitizer, Android, Apple, Linux, Windows, fuzz, and semantic-coverage
jobs and receives final independent post-implementation GO. Step 10 remains
the final R-191 conformance and admission audit.

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

Step 9 still requires the corrected committed revision to pass the GitHub
platform, sanitizer, and canonical coverage jobs.
