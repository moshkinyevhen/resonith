# R-201 Host/Device Memory Provenance Focused Gate

Date: 2026-07-29
Scope: R-190/R-191 analyzer infrastructure only
Codec algorithm or bitstream change: **no**

## Implemented law

The one counting PMR resource now tracks three independent per-call historical
high-water transitions:

```text
profile-admitted reservation
    >= successful upstream commitment
    >= analyzer-visible live storage
```

An admitted upstream OOM raises only reserved high-water bytes, rolls current
reservation back to zero, and maps to the environmental-OOM status. Profile
exhaustion occurs before reservation. Successful deallocation returns current
reserved, committed, and live counters to zero.

Page prepare, commit, cancel, and release callbacks are checked. The work meter
snapshots one immutable ceiling, so later internal passes cannot reinterpret
already consumed page work against a reduced manifest remainder.

`path_output` no longer has a default allocator. A test-only thread-local
permit surrounds only the counting resource's checked upstream
allocate/deallocate call. A separate statically linked executable overrides
global `new`, `new[]`, aligned, sized, and nothrow variants and arms the
tripwire before the first tested ABI call.

No CUDA allocator exists in the current CPU path. Device reserved, committed,
peak-live bytes, and CUDA work events remain exactly zero.

## Exact evidence

Source:

```text
native/src/partial_graph.cpp
SHA-256 79C66C04CA270E5942A06263AAC713B531726964BC4C80DB611BC911B522F369
```

Tripwire source:

```text
native/tests/partial_graph_allocation_tripwire_test.cpp
SHA-256 42992C32EAD0A940BAB4C9E0A569084A66AAE6B4CBBCBF7F6A88936114D4FDC8
```

Shared library:

```text
build/cpp23-clang22-ninja/libresonith_core_shared.dll
SHA-256 9BB7FE551C442BFA3E740C19D135619D9476AE54808B873C59657F951C3B0628
```

Strict C++23 warnings-as-errors build: passed.

Native conformance:

```json
{"schema":"resonith-r190-native-edge-cpu-1","edge_count":9,"path_count":8,"reserved_host_bytes":18684,"committed_host_bytes":18684,"peak_live_host_bytes":18684,"device_bytes":0,"deterministic":true,"predictor_integrated":false}
```

Armed first-use and repeated-use tripwire:

```json
{"schema":"resonith-r201-allocation-tripwire-1","r190_passes":2,"r191_passes":2,"permitted_allocations":1904,"forbidden_allocations":0,"device_bytes":0}
```

Additional focused results:

- internal success/profile-bound/upstream-OOM/callback-failure provenance
  probe: passed;
- v3 admitted-upstream-OOM report:
  `reserved_host_bytes > 0`, committed/live host bytes zero, all device bytes
  zero: passed;
- R-190/R-191 adversarial smoke: passed;
- native/Python exact oracle and ABI suite: **40 passed in 1.90 s**;
- CTest partial-graph conformance, allocation tripwire, and adversarial smoke:
  **3/3 passed**;
- `git diff --check`: passed.

## Non-regression

The frozen R-199 successful vector remains:

- total typed work: `51,962`;
- memory-page work: `33`;
- report commit work: `1`;
- input fingerprint:
  `CBC20C48929AFCBC C54EA97A8F9D12B5 2E0C4CFD91A734EE D4DBB44FC70C0EEC`;
- output fingerprint:
  `0768B860696B93BC 801DAAA74B3AD371 5085DFDA5814619A 525158F31ABEF638`.

The new counter assertions run in the same native and Python gate. No DSP,
syntax, entropy, reconstructed PCM, or encoded byte changed, so the R-198
complete-music recompression gate is not triggered.

## Evidence boundary

This focused gate proves the Step-8 counter law, rollback, checked page
transitions, truthful CPU device zeros, and first/repeated-call global
allocation tripwire.

Allocation-ordinal campaigns, structured ABI fuzzing, sanitizers, and broad
platform matrices remain Step 9. Final R-191 admission remains Step 10 and
requires an independent post-remediation GO.

## Independent post-implementation audit

Verdict: **GO — zero Step-8 blockers**.

The auditor confirmed on the final source and tripwire hashes:

- independent and correctly ordered reserved/committed/live high-water state;
- rollback after profile rejection, upstream OOM, and callback failure;
- upstream deallocation and page-reservation cancellation after failed commit;
- checked prepare/commit/cancel/release transitions;
- immutable work-ceiling capture;
- armed coverage of scalar/array, aligned, sized, and nothrow global allocation
  variants;
- independent counted-upstream activity for all eight first/repeated R-190 and
  R-191 preflight/fill entries;
- exact CPU device zeros and environmental-OOM report distinction;
- unchanged native, fuzz-smoke, and frozen R-199 evidence.

The audit explicitly leaves allocation-ordinal injection, sanitizers,
shared-library/platform breadth, and structured fuzzing to Step 9.
