# R-238 S15 bootstrap import-closure audit request

Date: 2026-08-02

Status: **SUPERSEDED AFTER FAIL-CLOSED STALE-BASELINE REJECTION**

## Outcome

Both independent auditors returned GO. The exact suite then stopped on its
first task because the frozen stream identity described historical EPV1-v2,
while the pre-S15 incumbent already emitted the six-byte-larger bounded
EPV1-v3 header. The decoded WAV was bit-identical. No synthetic control ran;
the atomic failure receipt is retained at
`artifacts/r238-s15-controls-failure.json`. R-239 audits the corrected
pre-S15 incumbent identity.

## Failure and correction

The independently approved R-237 command stopped before suite creation with
`AttributeError: module 'importlib' has no attribute 'util'`. The prior
fresh-process wrapper imported `importlib.util` itself and therefore masked the
direct-script bootstrap defect.

The only implementation correction is one explicit stdlib import:
`import importlib.util`. No DSP, RDO, threshold, candidate, syntax, decoder,
stream, control, duration, corpus, resource or claim setting changed. The
authority was regenerated after `py_compile`; focused tests remain 16/16 PASS
in 22.06 seconds and direct `--help` bootstrap now passes.

## Exact changed identities

| Item | SHA-256 |
|---|---|
| control runner | `53af4e1f85341b6d29661003d7e18144d40cc2cf64679463c2da9f20f738670e` |
| implementation authority v2 | `0e6d99f39bc1a8743e477524a5c14c1375bb45ecc5fdaa78561c0ddde2c6b2a0` |

All other R-237 identities remain unchanged. Authority still binds 66 local
sources and 84 local bytecode files.

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
  --output-directory G:\Resonith\artifacts\r238-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 0e6d99f39bc1a8743e477524a5c14c1375bb45ecc5fdaa78561c0ddde2c6b2a0
```

Return binary **GO** only if the one-line bootstrap correction and regenerated
authority preserve the complete R-237 conclusions and this exact command may
run legacy identity plus four synthetic controls. Do not run the suite or edit
files. Real audio, Opus comparison and S15 admission remain unauthorized.
