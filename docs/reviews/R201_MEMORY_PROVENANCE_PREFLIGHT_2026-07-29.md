# R-201 Host/Device Memory Provenance Preflight

Date: 2026-07-29
Status: **NO-GO before remediation; implementation authorized**

## Question

Does the R-190/R-191 implementation prove that every project-controlled
allocation is admitted by a bounded resource and report host/device memory
without conflating reservation, successful allocation, and live storage?

## Independent audit

The pre-implementation red-team found five blocking gaps:

1. no armed global-allocation tripwire proved that the exported C ABI avoids
   hidden default allocations and unreachable legacy containers;
2. `reserved_host_bytes`, `committed_host_bytes`, and
   `peak_live_host_bytes` were all aliases of one peak counter;
3. page-accounting callback failures were ignored;
4. the long-lived page meter referenced a manifest whose work ceiling was
   mutated between passes;
5. the single environmental-OOM probe did not prove allocation ordinals,
   rollback, first/repeated-call behavior, or truthful CPU device zeros.

The auditor explicitly rejected a fake CUDA allocator, a production-wide
replacement allocator, and an analyzer rewrite. Device use remains exactly
zero until this API actually allocates device storage.

## Stress-tested metric law

All three byte fields are historical high-water marks over one ABI call:

- **reserved host bytes**: maximum admitted outstanding byte count after the
  profile bound is checked and before the upstream allocation outcome is
  known;
- **committed host bytes**: maximum outstanding byte count backed by
  successful upstream allocations;
- **peak live host bytes**: maximum outstanding byte count made available to
  the analyzer.

Therefore:

```text
reserved_host_bytes >= committed_host_bytes >= peak_live_host_bytes
```

For the current synchronous `new_delete_resource` path, committed and live
normally rise together. They remain separate state transitions so an admitted
upstream allocation that fails can increase the reserved high-water mark
without increasing committed or live high-water marks.

Current outstanding reservation, commitment, and live counters must all return
to zero after the owning containers are destroyed. Underflow, failed page
transition, or a non-zero terminal counter is an internal provenance failure.

The device fields have the same future meaning. The CPU implementation does
not allocate CUDA, pinned, managed, or other device storage, so all three
device fields and every CUDA work event must remain exactly zero even when the
caller declares a non-zero device ceiling.

## Minimal implementation

1. Track current and high-water reserved, committed, and live host bytes with
   checked arithmetic inside the one counting PMR resource.
2. Wrap only checked upstream allocate/deallocate calls in a test-observable
   thread-local permit.
3. Make page commit/cancel/release callbacks return checked success and reject
   an unhealthy transition.
4. Snapshot the work ceiling in `bounded_work_meter`; never retain a mutable
   manifest ceiling.
5. Remove the default allocator argument from `path_output`.
6. Add an internal deterministic provenance probe for successful allocation,
   admitted upstream OOM, profile-bound rejection, callback failure, and clean
   rollback.
7. Add a dedicated statically linked allocation-tripwire executable that
   overrides global `new`/`new[]`, arms before the first R-190/R-191 ABI call,
   and repeats preflight/fill.
8. Assert exact CPU device zeros and the host ordering law in native and Python
   conformance tests.

Allocation-ordinal campaigns, structure-aware ABI fuzzing, and sanitizer
platform breadth remain the explicit scope of Step 9; Step 8 establishes the
counter semantics and the first/repeated-call tripwire proof they consume.

## Primary evidence

- The C++ working draft requires `memory_resource::do_deallocate` to receive
  storage returned by a prior equal-resource allocation with the matching
  allocation contract:
  <https://eel.is/c++draft/mem.res>
- NVIDIA documents device, pinned-host, managed, and stream-ordered allocation
  as distinct CUDA runtime operations; none is called by the current CPU path:
  <https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__MEMORY.html>
- Microsoft Application Verifier documents heap and low-resource verification
  as independent runtime evidence, supporting the later platform gate rather
  than replacing the in-process tripwire:
  <https://learn.microsoft.com/windows-hardware/drivers/devtest/application-verifier-testing-applications>

## Admission condition

R-201 may become GO only when:

- the independent counters and rollback probe pass;
- the global tripwire passes first and repeated R-190 and R-191 calls;
- report host fields satisfy the frozen law;
- device fields and CUDA events are exactly zero;
- the Step-6 work/fingerprint golden vector remains byte-for-byte unchanged;
- the post-implementation independent audit reports zero blockers.
