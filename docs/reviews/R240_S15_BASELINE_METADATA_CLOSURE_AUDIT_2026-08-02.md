# R-240 S15 baseline metadata-closure audit

Date: 2026-08-02

Status: **INDEPENDENT GO; EXECUTED ONCE AND STOPPED AT FROZEN TIME LIMIT**

Both auditors returned GO. The incumbent identity passed, then the first
synthetic control reached its unchanged 900-second ceiling and was terminated
by the bounded controller. R-241 retains the terminal result; no retry or
limit increase is authorized.

R-239's substantive baseline proof passed independent hostile review. Its only
blocking defect was one stale printed configuration SHA-256 in the amended
R-232 preflight. That line now names the actual corrected configuration
`5fea557eb517f0e02f318e87f205ba116b0032e61b852a0dd3a8fe06a194e0fc`.
No code or executable configuration changed after the 16/16 R-239 focused
PASS. Authority validation was rerun in a fresh process and passes.

Exact new identities:

- amended R-232 preflight:
  `09aa603306ad581973b636a637d4daa4fa499fde043040ef4bd577d43fad4326`;
- implementation authority:
  `bb14ad62772a7fe71530fe2a99ddbf127cd6a095b84a7aa1fc8006e7295cc29e`.

Every other R-239 identity and conclusion is unchanged.

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
  --output-directory G:\Resonith\artifacts\r240-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 bb14ad62772a7fe71530fe2a99ddbf127cd6a095b84a7aa1fc8006e7295cc29e
```

Return binary **GO** only if the single metadata correction closes R-239 and
the exact command may run incumbent identity plus four synthetic controls.
Do not run it or edit files. Real audio, Opus comparison and S15 admission
remain unauthorized.
