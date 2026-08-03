# R-234 S15 bounded implementation audit request

Date: 2026-08-02

Status: **POST-REMEDIATION READ-ONLY AUDIT REQUIRED; EXECUTION NO-GO**

## Authorized scope

R-232 and both independent pre-code auditors authorized one narrow remediation
only. Synthetic controls compare decoder-domain rescoring against legacy SFT1;
they cannot claim accepted-S12 fallback, paid admission, or a real-audio win.
This implementation does not change the frozen DSP formula, proposal lattice,
RDO thresholds, syntax, decoder, mode family, pulse budget, or stream version.

The only changes are:

1. factor the frozen selector into a directly testable function;
2. bind pitch state, adaptive vector, ordered candidates, payload fields and
   realized vectors into one digest immediately before every choice;
3. retain per-choice digests and winner signatures so the runner proves exact
   list identity through the first winner divergence;
4. make candidate scoring read-only over committed histories and verify that
   it does not mutate the bit writer;
5. test eligibility boundaries, zero/tiny normalization, half-even rounding,
   both clipping sites, rejected candidates, causal mel scope, decoder-exact
   synthesis, determinism and first-divergence trace semantics;
6. execute legacy identity plus four 120-second controls sequentially in
   suspended one-process Windows Job Objects with hard 3 GiB process/job
   memory, 900-second wall, bounded logs and 8 GiB aggregate storage;
7. publish each worker, the incremental run index, terminal suite receipt and
   failure receipt atomically, with validated cleanup confined to the exact
   suite staging parent;
8. seal configuration, preflight, oracle, runner, test, metric helper, WAV
   helper, native Core, Python, NumPy, SciPy and Windows identities through an
   external authority file and an explicit authority hash.

Real-audio mode deliberately refuses to run. Actual-decoder S12 and Opus
comparison remains a later separately audited extension before long speech.

## Frozen identities

| Item | SHA-256 |
|---|---|
| amended R-232 preflight | `9267715a26bcc1e5ec5f5c2f0053a9ba928480ff9a2dc8f0057071475bd25d33` |
| frozen configuration | `b89cae2d09c2c45ba1488e573009a7d822e15998ad4816c7bb45d65ad3cf5d24` |
| source-filter oracle | `dfb667ff929864f1404d22c78732dbc05b1eba276297c7027ac32ebacf13969d` |
| focused test module | `1ad7b4323d22e6e719a298e0267814c6b29c980de7e9422ab7f7fc2550be2f07` |
| control runner | `10dce54eab509a701212859ab1f6aa7e17bec04b0fde60a1a7483395ae7b98da` |
| implementation authority | `3c50dfe1e1210c7d1cef3d5460b9654c1167392109f0238380bf033561500365` |

The authority additionally binds the existing metric/WAV helpers, native Core
and exact runtime. The public speech source must hash to
`799f78ed4beb4de7ceae3a809262d4ce242394342ccd1d58cef7d49dbc2def46`.
Legacy execution must reproduce the 12,548-byte R-120 stream and its frozen
stream/decoded-WAV hashes before any synthetic control begins.

## Focused evidence already permitted

The one focused test module passes 11/11 under pinned Python 3.14.6 and native
Core. `py_compile`, authority validation and `git diff --check` also pass. No
legacy-identity or 120-second control has been executed after remediation.

## Exact proposed execution

The following command is prohibited until both read-only auditors return GO on
the identities above:

```powershell
$env:PYTHONHASHSEED='0'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe `
  G:\Resonith\experiments\r232_s15_source_filter_gate.py `
  --control-suite `
  --output-directory G:\Resonith\artifacts\r234-s15-controls `
  --legacy-identity-source G:\Orkela\comparison\public-benchmark-2026-07-26\speech-original.wav `
  --authority G:\Resonith\experiments\fixtures\r234_s15_implementation_authority.json `
  --expected-authority-sha256 3c50dfe1e1210c7d1cef3d5460b9654c1167392109f0238380bf033561500365
```

The controller stops on the first failed legacy/control/resource gate. No
retry, retuning, threshold change or candidate-family change follows a result.

## Binary audit questions

Return **GO** only if all answers are yes:

1. Is the implemented selector exactly the frozen R-232 selector?
2. Does the trace prove candidate-list identity through the first functional
   winner divergence and include every causal proposal input requested?
3. Are rejected evaluations unable to mutate the writer or committed state?
4. Do the tests minimally but sufficiently cover the previously identified
   selector, clipping, causality, trace and transactional boundaries?
5. Are memory, process count, wall, logs and aggregate storage enforced while
   the child is alive, with stop-on-first-failure sequencing?
6. Are success, progress, failure and cleanup fail-closed and transactional?
7. Does the authority seal every executable dependency needed for this narrow
   control run, without representing synthetic evidence as S12 admission?

Any blocking no leaves execution at **NO-GO** and must identify the smallest
in-scope correction. This audit does not authorize real-audio execution or a
new algorithm generation.
