# R-256 R-253 implementation dual audit

Date: 2026-08-02

Status: **SUPERSEDED NO-GO AFTER REPRODUCTION FOUND STALE BYTECODE AUTHORITY**

## Audited implementation

The audit covered exactly four implementation-evidence files:

- `reference/maf_p0/maf_source_filter_oracle.py`, SHA-256
  `736292ac28b5a3dcb7ca33db6a4be0c451909a67b96dab0c393b435b5656382e`;
- `tests/test_maf_source_filter_oracle.py`, SHA-256
  `bf409eb3f5f700937f7d31ca8ccdcbc0c3f615794dba412e7a0f763b34bdba2b`;
- `tests/fixtures/r250_s15_lpc_golden.json.gz`, SHA-256
  `793bff4e748435c079668920a5a2a6cc97b932250bb1bca1df69ed2c6958cc35`;
- `experiments/fixtures/r255_s15_implementation_authority.json`, SHA-256
  `d275e280f5d1a44048c97e7e6fca42e7e2ecd3a16bdcba7f68d75954c60a8aa3`.

The gzip fixture is 56,229 bytes and decompresses to the independently frozen
R-250 golden payload SHA-256
`8fe390457f9baf5226207f2d3c3ebb71c6ba5ac968921cb7e6e145f9b4e8ccf6`.
R-234 remains immutable at SHA-256
`bb14ad62772a7fe71530fe2a99ddbf127cd6a095b84a7aa1fc8006e7295cc29e`.

## Implemented change

The new private `_prepare_short_filter_lpc` helper validates one exact
subframe interval and prepares the immutable Q14 LPC tuples for only the
FilterLaw blocks touched by that interval. The prepared value is reused by:

- Basis-training desired-excitation collection;
- main-loop desired-excitation construction; and
- every realized candidate synthesized for the same main-loop subframe.

The helper admits block sizes from 64 through 8192 samples and region lengths
from 1 through 512 samples, requires the complete exact FilterLaw count, and
can touch at most nine laws. It creates no cache, global state, public ABI,
syntax, decoder, trace, report, counter, or cross-encode lifetime.

Coefficient order, accumulator order, integer rounding, clipping, FFT and RDO
ordering, candidate ordering, tie breaks, stream serialization, and commit
order remain unchanged.

## Focused evidence

The complete focused module passed:

```text
18 passed in 22.48s
```

The test set includes all 128 frozen scalar cases, the nine-law maximum,
invalid interval and profile bounds, insufficient and excess law counts,
both desired-target callers, escaped candidate mappings, repeated equal but
distinct helper results, nonzero-Basis training, transactional synthesis, and
fresh validation of R-255's complete import and runtime closure.

The first full-module run retained two authority failures rather than hiding
them: R-234 correctly rejected the changed oracle and test. R-255 was then
created as a fresh implementation authority; the historical drift test still
uses immutable R-234, while only the two current-closure tests use R-255.

## Independent findings

Two independent auditors returned GO. They found:

- exact coverage of every production caller authorized by R-253;
- no hidden cache, retained observer state, or report/trace mutation;
- complete and schema-compatible R-255 project, import, runtime, native, and
  configuration closure;
- unchanged R-234 historical authority;
- compliance with the file, line, byte, helper-lifetime, and nine-law budgets;
- adequate adversarial and transactional focused coverage.

Both auditors independently require the next evidence transaction to
distinguish Basis-training and main-loop helper observations, retain process
peak working-set evidence, and prove complete pre/post stream, decoded PCM,
semantic report, and candidate-trace identity.

## Verdict and boundary

**GO** to freeze this exact implementation and create, but not execute, one
bounded post-change evidence runner plus one separate execution authority.

Any edit to the four audited files invalidates this verdict. The new runner
must preserve the R-250 workload, candidate lattice, metrics, time and memory
budgets, stop-on-first-failure law, and atomic publication behavior. It must be
at most 700 physical lines and 72 KiB, use external non-timed observation, and
receive a separate read-only dual-audit GO before its single invocation.

No algorithm generation, compression result, R-198 corpus exception, syntax,
decoder, product, version, Opus rerun, promotion, or release is admitted by
this audit.

## Post-audit falsification

Before commit, the focused module was rerun without exporting
`PYTHONDONTWRITEBYTECODE=1` before interpreter startup. CPython 3.14.6
legitimately regenerated
`reference/maf_p0/__pycache__/maf_source_filter_oracle.cpython-314.pyc` from
the unchanged audited source. Its SHA-256 changed from R-255's stale
`8759a513a5b44e1f4eda85123f9fb47b2bd956e8e2d8d4da6ebe65750662e51f`
to the current-source cache SHA-256
`777551dd2abe9517d68d202c29929635a9f079a93e0e262abc8dcfb9c6e036fe`.
The authority then failed closed in 2 of 18 tests; the other 16 passed.

Inspection found that all 84 R-255 bytecode entries use timestamp
invalidation. Sixty-six have the selectable `cpython-314` tag and eighteen
have the foreign `cpython-312` tag. Binding all existing cache files therefore
both included bytecode the frozen interpreter cannot select and treated
ordinary source-cache regeneration as executable drift.

The implementation source, test source, golden fixture and R-255 JSON bytes
were unchanged. This finding does not show an LPC arithmetic mismatch, but it
does invalidate R-255's claimed executable closure and therefore supersedes
the preceding GO. No commit or post-change benchmark execution occurred.
R-257 defines the required remediation; implementation remains frozen and
execution remains NO-GO.
