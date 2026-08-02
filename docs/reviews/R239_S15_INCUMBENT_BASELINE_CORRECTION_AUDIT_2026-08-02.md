# R-239 S15 incumbent-baseline correction audit

Date: 2026-08-02

Status: **NO-GO; SUPERSEDED BY R-240 METADATA CLOSURE**

The baseline evidence passed, but an auditor found that the amended R-232
preflight still printed the old configuration SHA-256. R-240 corrects only
that self-reference and regenerates authority.

## Falsified baseline and root cause

The R-238 suite stopped on `legacy-identity` before any synthetic control.
Observed and frozen decoded WAV SHA-256 both equal
`b105da972c12a373c826a1fee4a6911a1dc63cb08bcfe4b87851b7d3da50d873`,
but the historical stream was 12,548 bytes while the current stream is 12,554
bytes.

Section inspection identified the complete cause:

- historical artifact: EPV1 version 2, 11,942-byte residual;
- pre-S15 incumbent: EPV1 version 3, 11,948-byte residual;
- event payload is unchanged at 366 bytes;
- the six bytes are the three bounded uint16 Basis header fields introduced
  before S15;
- decoded PCM and decoded WAV remain bit-identical.

To distinguish a stale fixture from S15 drift, a clean `git archive` of
pre-S15 commit `5aff74dbce41d7dece102a10f7ff326d7a700dda` was extracted outside the
worktree and run with the frozen configuration, native Core and input. Without
any S15 code it independently produced:

- stream bytes: 12,554;
- stream SHA-256:
  `f0c3abf0a71ee7d40bdd4f5c022291264b8e39a40c2e9bdc58f14fd23f87a8a6`;
- decoded WAV SHA-256:
  `b105da972c12a373c826a1fee4a6911a1dc63cb08bcfe4b87851b7d3da50d873`.

The correction therefore replaces only stale baseline metadata. It does not
waive a mismatch, derive the baseline from the candidate arm, or change code,
DSP, RDO, syntax, decoder, controls, durations, resources or claim scope.

## Exact identities

| Item | SHA-256 |
|---|---|
| frozen configuration | `5fea557eb517f0e02f318e87f205ba116b0032e61b852a0dd3a8fe06a194e0fc` |
| amended R-232 preflight | `132e984378b13d325b83f1ea8c03f1aa225f1fe5a4060a0e29117cbf23dfbf8e` |
| control runner, unchanged from R-238 | `53af4e1f85341b6d29661003d7e18144d40cc2cf64679463c2da9f20f738670e` |
| source-filter oracle, unchanged | `8a2f27e4357146edd0c1840268ec74bee3b59e43e6ca75a2d18902ef7d325007` |
| focused tests, unchanged | `75e394bf1e6da57ce692a7747735c51c80559bb3acacb70be88226e057624483` |
| corrected implementation authority | `61482ba309782f1fba0e2f40dbd47186f6b9902219ac1d7fd00b0694e19e4446` |

The configuration now calls the record `frozen_incumbent_reference` and omits
the obsolete report hash. The authority binds the corrected stream identity,
configuration and preflight. Focused tests pass 16/16 in 23.00 seconds and
`git diff --check` passes.

## Exact proposed command

```powershell
$env:PYTHONHASHSEED='0'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe `
  G:\Resonith\experiments\r232_s15_source_filter_gate.py `
  --control-suite `
  --output-directory G:\Resonith\artifacts\r239-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 61482ba309782f1fba0e2f40dbd47186f6b9902219ac1d7fd00b0694e19e4446
```

Return binary **GO** only if the independent pre-S15 reproduction proves the
baseline correction and the exact command may run incumbent identity plus the
four synthetic controls. Do not run it or edit files. Real audio, Opus
comparison and S15 admission remain unauthorized.
