# R-237 S15 closed implementation audit request

Date: 2026-08-02

Status: **SUPERSEDED AFTER FAIL-CLOSED BOOTSTRAP REJECTION**

## Outcome

Both independent auditors returned GO, but the exact command stopped before
suite creation because a direct Python 3.14 script launch did not expose
`importlib.util` after importing only `importlib`. Earlier validation had
accidentally primed that attribute in its wrapper. No legacy identity or
synthetic audio ran and no output, failure receipt or staging directory was
created. R-238 binds the one-line explicit stdlib import correction.

## Scope

This request closes only the remaining R-236 evidence-controller findings. It
does not change DSP, candidate proposal, eligibility, quality scalar, tie
order, syntax, decoder, stream version, corpus or claim scope.

The authority now binds all 66 statically reachable local sources, all 84
existing local `.pyc`/`.pyo` files that the frozen interpreter could select,
the complete pinned Python `Lib` and `DLLs` trees including bytecode, runtime
binaries and package versions. `PYTHONDONTWRITEBYTECODE=1` is mandatory.

After every bounded child exits, the parent revalidates the same authority
before reading the worker transaction. One shared production helper validates
the receipt, exact retained-file manifest and report. Any missing or corrupt
post-worker record raises a structured failure that preserves the already
measured request, wall, process/job memory, disk high-water and bounded log
hashes/excerpts. Suite staging creation is inside the guarded transaction and
partial setup is cleaned through the same confined cleanup.

Candidate scoring snapshots every mutable `_BitWriter` field and hashes the
current live causal history reachable by the next decision. The direct witness
mutates every writer field and mutates committed state through a pre-existing
writable alias, proving that reachable changes are detected while unreachable
old history is intentionally excluded.

## Exact identities

| Item | SHA-256 |
|---|---|
| amended R-232 preflight | `9267715a26bcc1e5ec5f5c2f0053a9ba928480ff9a2dc8f0057071475bd25d33` |
| frozen configuration | `b89cae2d09c2c45ba1488e573009a7d822e15998ad4816c7bb45d65ad3cf5d24` |
| source-filter oracle | `8a2f27e4357146edd0c1840268ec74bee3b59e43e6ca75a2d18902ef7d325007` |
| focused test module | `75e394bf1e6da57ce692a7747735c51c80559bb3acacb70be88226e057624483` |
| control runner | `b54296130d9eaf9ca1a5d8f132c291f9dda2dfdee87b1d4c974a680dedbf0bac` |
| implementation authority v2 | `29031312ad0c76c49cc2057d7dc31ac7787b33b282f9013612384d9ef855cf2e` |

## Focused evidence

- `py_compile`: PASS;
- `git diff --check`: PASS;
- fresh-process authority validation followed by runtime load: PASS with 66
  source modules, 84 local bytecode files and four frozen files;
- focused module: 16/16 PASS in 21.75 seconds;
- real child then missing-receipt witness: PASS, preserving complete measured
  resources in the external failure receipt, publishing no final suite and
  leaving no staging orphan;
- all earlier normal, timeout, second-process, memory, log, storage, authority
  drift and stop-on-first-failure witnesses remain PASS.

No legacy-identity or 120-second audio control has executed after remediation.

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
  --output-directory G:\Resonith\artifacts\r237-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 29031312ad0c76c49cc2057d7dc31ac7787b33b282f9013612384d9ef855cf2e
```

Return binary **GO** only if this exact command may run legacy identity followed
by the four synthetic controls. This does not authorize real-audio execution,
comparison with S12/Opus, S15 admission, release or publication. Any blocker
must identify the smallest in-scope controller/evidence defect.
