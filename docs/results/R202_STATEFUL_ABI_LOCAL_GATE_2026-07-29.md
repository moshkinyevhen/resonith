# R-202 Stateful ABI and Semantic Coverage Local Gate

Date: 2026-07-29

Scope: Step-9 R-190/R-191 ABI, allocation, fuzz, and coverage infrastructure

Codec algorithm or bitstream change: **no**

Status: **local gate passed; GitHub platform gate pending**

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
47EE7993E063F22A9CF18849EFA7A94538C12842FC12929BC349B8131EF0DDF6

scripts/enforce_partial_graph_coverage.py
013A87096C18CBEA4269E7BF098EA91FDA2E68D10C4FF29C263C1A9E9D3903D9

.github/workflows/mobile.yml
3F81851CA903FE6310B5280D2AB637399915869C65D020D4BAD871A7D8A37667
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

Any new miss, stale miss, source drift, helper drift, or proof-range drift
fails the gate before percentages are evaluated. Negative tests confirmed
rejection of a changed source hash and a stale uncovered-line entry.

Measured local coverage:

| Metric | Raw | Proof-adjusted | Floor |
|---|---:|---:|---:|
| Lines | 845 / 905 = 93.3702% | 845 / 879 = 96.1320% | 95% |
| Branch outcomes | 209 / 230 = 90.8696% | 209 / 226 = 92.4779% | 90% |

Exactly 26 lines and four branch outcomes are excluded as
allocation- or ledger-invariant unreachable. All remaining uncovered
locations remain in the denominator as explicit tracked gaps.

Generated gate:

```text
build/local-coverage/evidence-r202-helper/coverage-gate.json
202D4C7ECDD2E5BE86103FB6F29421E383776DB7E3A9AF926CD9CF19D71F4E34
```

`actionlint`, Python syntax validation, and `git diff --check` pass.

## Acceptance boundary

This is a focused analyzer-infrastructure gate. It changes no codec syntax,
encoded bytes, decoded samples, PCM, entropy policy, or RDO behavior, so the
complete music/Opus generation gate is not triggered.

Step 9 remains open until the same revision passes the GitHub sanitizer,
thread-sanitizer, Android, Apple, Linux, Windows, fuzz, and semantic-coverage
jobs and receives final independent post-implementation GO. Step 10 remains
the final R-191 conformance and admission audit.

## Independent post-implementation audit

Verdict: **GO — zero blocking defects for the local R-202 design**.

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

This GO applies to the local design and evidence. Step 9 still requires the
same committed revision to pass the GitHub platform and sanitizer matrix.
