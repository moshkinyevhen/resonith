# R-216 S12 implementation narrow audit

Date: 2026-08-02
Status: **INDEPENDENT GO — MOZART EXECUTION AUTHORIZED**

## Scope

This is the final implementation audit before the mandatory long-first Mozart
execution. It audits the smallest implementation authorized by the V4
preflight. It does not audit or change the codec algorithm, bitstream, native
Golden Core, registered corpus, or maximum-effort Opus policy.

Owner-directed comparator scope is R-215 S11 against official maximum-effort
Opus only. No preceding Resonith stream or score enters this run.

## Frozen reviewed inputs

- V4 preflight:
  `docs/reviews/R216_S12_REGISTERED_COMPARISON_PREFLIGHT_2026-08-02.md`,
  SHA-256
  `5e87d450ca17699884eb4a66bbc95ff7a8b59c16c8efed754d614f6f24679201`;
- registered manifest:
  `experiments/fixtures/r216_s12_registered_manifest.json`, SHA-256
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`;
- runner: `experiments/r216_s12_opus_comparison.py`, SHA-256
  `316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3`;
- metric helper: `experiments/r216_s12_metrics.py`, SHA-256
  `ab9f4a3e755d031f14fa7e6df88e4b11e65c44c5f6feb236ff4045be0f84f3e3`;
- focused tests: `tests/test_opus_max_effort.py`, SHA-256
  `a466820c8a1f47e9ee9c30213e727023e2f4e174e4b18d0a63e37fe2e2a7ecc6`.

The two new Python source files contain 1,398 nonblank lines against the
authorized maximum of 1,400. The focused test file contains 293 nonblank
lines against 450. No third Python source file was added.

## Executed evidence

Exact environment:

- Python 3.14.6;
- NumPy 2.5.1;
- SciPy 1.18.0;
- pystoi 0.4.1;
- official opus-tools `0.2-39-g9b1ca51`, libopus
  `1.6.1-8-g475cbc5`;
- Golden Core SHA-256
  `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed`.

Focused command:

```powershell
$env:PYTHONPATH='G:\Resonith;G:\Resonith\reference'
$env:RESONITH_NATIVE_CORE='G:\Resonith\build\cpp23-clang22-ninja\libresonith_core_shared.dll'
G:\Resonith\artifacts\tools\python-3.14.6-amd64\python.exe -m pytest -q G:\Resonith\tests\test_opus_max_effort.py
```

Result after process-tree remediation: **12 passed in 5.12 seconds**.

The exact frozen 19-item manifest was also read from the three explicit local
roots. Every source file hash, canonical PCM16 payload hash, rate, shape,
count, uniqueness constraint, and long-first order passed. No encode was
started by that validation.

## First independent audit and remediation

The first exact implementation audit returned NO-GO with five blockers. This
revision closes them without changing S11 or the Opus policy:

1. the controller now requires the audited runner digest on its exact command,
   validates helper, tests and V4 digests internally, and rejects relevant
   dirty or untracked imported code;
2. feedback and strict records are appended and fsynced before temporary Ogg
   or WAV deletion; retained Pareto Oggs are explicitly fsynced;
3. S11 runs in a separately killable bounded process, every Opus subprocess
   receives remaining time, staging is monitored while the worker runs, the
   output is restricted to G:, and the 12-hour origin survives resume;
4. circular coherence remains diagnostic but no longer votes in dominance;
5. successful subprocess stdout and stderr are never persisted.

The exact controller invocation must include:

```text
--audited-runner-sha256 316152b579fcc8d3896b36abb66d665d2ee088e5c95fecd15018b5387e633ba3
```

The second audit found one remaining outer-supervisor race: killing a worker
did not prove termination of its active S11 or Opus descendant. The final
runner uses an explicit Windows process-tree termination command, waits for
the tree, and uses a POSIX process group elsewhere. The focused nested-child
fixture forces a grandchild to append a heartbeat, triggers the outer timeout,
then proves the file no longer grows after the exception.

The final independent re-audit returned **GO** on the exact frozen hashes. It
independently repeated the focused suite (`12 passed in 4.99 seconds`) and
found no new blocker. The exact audited invocation may therefore start the
mandatory long-first Mozart item.

## Required adversarial review

The independent auditor must try to falsify all of these claims:

1. the analyzer bound is identical to the frozen analyzer and Mozart cannot
   accidentally invoke it;
2. S11 is scored only after actual byte decode and a reconstruction mismatch
   is hard;
3. q5 uses integer round-half-even, the serial domain is byte-canonical, all
   feedback attempts are retained, and strict matching has no escape;
4. 108/54 base configurations and the bounded 21/10 CTL expansion match V4;
5. CTL seeds and the listening artifact use the frozen axis order without an
   SNR-only shortcut;
6. each strict Opus point is raw-byte revalidated and decoded alone, with no
   collection of decoded PCM retained in memory;
7. phase, channel, transient, speech, silence, and null applicability metrics
   match V4 and cannot make a codec-dependent missing axis disappear;
8. Pareto dominance and the single lower S11 budget obey V4;
9. file-set/hash verification, staging quarantine, same-volume rename, run
   index, disk, RSS, and wall ceilings fail closed;
10. receipts and reports contain enough machine evidence for replay without
    publishing personal absolute paths.

Any blocking finding is **NO-GO**. Mozart may start only after every blocking
finding is resolved in writing and these exact hashes receive GO.
