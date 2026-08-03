# R-263 S15 Run 1 terminal failure

Date: 2026-08-03

Status: **TERMINAL FAIL; RUN 2 AND R-263 REMEDIATION FORBIDDEN**

## Frozen identities

- bootstrap SHA-256:
  `463002769637422d4dc4b6de32056212d5623313779530bcc4699dd5fdb62a7f`;
- gate SHA-256:
  `c4529ffaee118d8fd51360babda6e88d7051b0c1fdeabacca200d11ff04ea908`;
- test SHA-256:
  `ab70ba0f807ec4f7f3332a852c06e1ac5a9b8462889c232ac504258dddf81ede`;
- authority SHA-256:
  `1fe9e4b8a2c1afd5b52643ecbcd76ee187e888d4220f4b8173072e2f5aad7c02`;
- immutable R-263 plan SHA-256:
  `dcb8ecc6f8936dbcc40c3e88d57ab64fcc95311f8b81c09327df396850a0ea10`.

Two independent static auditors returned GO for these exact bytes before the
only authorized execution.

## Run 1 evidence

The one fresh Run 1 used
`artifacts/r263-s15-focused-admission-v1`. It terminated after
`7.207277399982559` seconds with status `FAIL`.

- stage-minus-one receipt SHA-256:
  `9864dccc649846fceceea8c6fc7b4a7179697d4994baeb7755ef47fcd03a22f2`;
- stderr SHA-256:
  `53c31f1bf1148b81536ae02915dcc96212f71258c6a9331d7ddf42c44b9d3d29`;
- empty stdout SHA-256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
- peak Job memory: `77,963,264` bytes;
- retained-evidence high-water mark: `1,624` bytes.

Only the authenticated `stage0_preflight` progress record completed. Tests did
not start and no Stage 1 or Stage 0 final receipt was produced.

Stage 1 emitted ordinary stderr instead of a length-framed record. Stage 0
interpreted the first four bytes of that traceback as a frame size and raised
`MemoryError` in `_relay_frames` before applying the payload bound. The outer
monitor then rejected Stage 0's ordinary traceback with
`R-263 outer progress stream contained ordinary bytes`. The originating Stage
1 traceback was not separately retained, so no stronger cause is claimed.

## Containment

Containment passed despite admission failure:

- assignment occurred before resume;
- exactly one termination attempt occurred and succeeded;
- the final Job observation reports `active_processes = 0` and an empty PID
  list;
- total observed Job processes were `2`;
- Job close succeeded;
- Stage 0 and Stage 1 prefixes are absent;
- the outer monitor prefix remains empty; and
- a separate read-only process query found no matching Python survivor.

## Admission consequence

The frozen R-263 rule makes any Run-1 failure terminal. Run 2, a retry, a larger
deadline, a reduced suite, reduced authority, and another R-263 remediation
cycle are prohibited. R-253 through R-263 remain unadmitted negative evidence
and cannot support codec, performance, release, or comparison claims.

The lawful continuation is to preserve this evidence immutably, restore the
active codec/oracle/test surface to the accepted S12 identities, and define a
genuinely new evidence-first S15 source-filter hypothesis against S12. That
hypothesis must not be described as an R-263 retry or inherit its failed
evidence mechanism.
