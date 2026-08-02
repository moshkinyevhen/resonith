# R-236 S15 final implementation audit request

Date: 2026-08-02

Status: **FINAL READ-ONLY AUDIT; CONTROL EXECUTION NO-GO**

## Scope

This is the single R-235 correction of the two independent R-234 NO-GO
findings. No DSP, proposal, candidate, RDO, threshold, syntax, decoder, stream
version or corpus setting changed.

The runner now validates a 66-file statically discovered local import closure,
the complete pinned Python `Lib` and `DLLs` trees, runtime binaries and package
versions before importing any third-party or project module. It repeats the
same validation after every worker. Candidate scoring snapshots every mutable
bit-writer field and a rolling authenticated identity of the read-only
committed excitation/output prefixes.

The controller recomputes wall, logs and aggregate storage after child exit,
retains structured failure resources in the external atomic receipt, cleans in
`finally`, rejects orphan staging, and uses the same transaction function in
focused stop-on-first-failure evidence.

## Exact identities

| Item | SHA-256 |
|---|---|
| amended R-232 preflight | `9267715a26bcc1e5ec5f5c2f0053a9ba928480ff9a2dc8f0057071475bd25d33` |
| frozen configuration | `b89cae2d09c2c45ba1488e573009a7d822e15998ad4816c7bb45d65ad3cf5d24` |
| source-filter oracle | `5ba6a7fa1897bd2ca1a63d0dfc264134458476dec08191696985f6a62f461f47` |
| focused test module | `16c82b5cf5e3a9e392634a3bc93e297dccd16f3c6bdfe76f11fa71b7f5f258fa` |
| control runner | `45d6cb59f153d7309eaa7a5e5c0211bccaf7d32866acfbd8506c6e37c845724d` |
| implementation authority v2 | `8e8fc0997e5ae89317a8be4d9f916e70322ee73dec6d01ad0abf72c5a2e8ce2f` |

Authority v2 records all 66 local module hashes, five Python/runtime binary
hashes, complete cache-independent `Lib`/`DLLs` tree hashes, Python 3.14.6,
Windows 10.0.22631, NumPy 2.5.1, SciPy 1.18.0, SoundFile 0.14.0, pystoi 0.4.1
and cffi 2.1.0.

## Focused evidence

- `py_compile`: PASS;
- `git diff --check`: PASS;
- one fresh-process authority validation followed by runtime load: PASS, 66
  authorized local modules and no unauthorized local Python module;
- focused module: 14/14 PASS in 13.98 seconds;
- executable micro-witnesses: normal child, wall timeout, second-process
  rejection, 64 MiB Job memory rejection, log ceiling, storage ceiling,
  authority drift, and atomic stop-on-first-failure with no final output,
  no orphan staging and no later task.

No R-120 identity or 120-second audio control has executed after remediation.

## Exact proposed command

```powershell
$env:PYTHONHASHSEED='0'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe `
  G:\Resonith\experiments\r232_s15_source_filter_gate.py `
  --control-suite `
  --output-directory G:\Resonith\artifacts\r236-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 8e8fc0997e5ae89317a8be4d9f916e70322ee73dec6d01ad0abf72c5a2e8ce2f
```

Return binary **GO** only if the exact command may run legacy identity then the
four synthetic controls. This does not authorize long/short real speech,
accepted-S12 claims, Opus comparison or S15 admission. Any blocker must be a
smallest in-scope controller/evidence defect; an algorithm change closes R-232.
