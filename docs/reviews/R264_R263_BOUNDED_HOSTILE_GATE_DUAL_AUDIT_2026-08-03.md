# R-264 R-263 bounded hostile-gate dual audit

Date: 2026-08-03

Status: **DUAL PRE-CODE GO FOR THE EXACT R-263 EVIDENCE REDESIGN ONLY**

## Audited identity

Both independent auditors reviewed the exact R-263 plan at:

- path:
  `docs/reviews/R263_R262_BOUNDED_TRANSACTIONAL_HOSTILE_GATE_REDESIGN_2026-08-03.md`;
- SHA-256:
  `dcb8ecc6f8936dbcc40c3e88d57ab64fcc95311f8b81c09327df396850a0ea10`;
- physical lines: `422`.

Neither auditor edited project files or executed project code, tests, codec,
audio, Opus or player work.

## Independent findings resolved before GO

The initial drafts were NO-GO. They did not define an enforceable termination
reserve or a pre-Stage-0 monitor; assigned one progress sequence to multiple
processes; repeated full loaded validation tens of times; failed to freeze
ordered mapping restoration; could have removed the independent gate-validator
witness; reused a mutable parsed authority by identity only; attempted racy
post-termination PID capture; allowed concurrent writers to one stderr stream;
and initially proposed ordinary Job completion-port messages as authoritative
despite Microsoft's non-guaranteed-delivery warning.

The final plan closes those findings with:

- one pre-execution, self-hashed inline verifier and the already bound gate as
  the sole outer monitor;
- exact 68.0/73.0/73.5/74.5/75.0-second boundaries, create-suspended,
  assignment-before-resume and kill-on-close containment;
- authoritative resize-until-complete Job process-list plus accounting queries
  while the no-breakaway Job handle remains held;
- one Stage-0 outer writer and one length-framed Stage-1 relay;
- one full loaded closure before and after the transactional matrix, with each
  row calling only its shared narrow production validator;
- exact ordered mapping, module/spec, finder, namespace and Guard restoration;
- canonical authority-content hashing immediately before and after each reuse;
- preservation of the separate production gate `_validate_authority()` positive
  witness;
- exact 82-binding closure: 14 files, 67 local imports and one inline launcher;
  and
- a cumulative maximum of 720 executable added lines, counting the launcher.

## Binary verdict and authorization

Both auditors returned **GO** with no remaining plan-level blocker. R-264
authorizes only the smallest implementation of the exact R-263 plan inside its
closed executable inventory and frozen resource budget.

It does not authorize either focused admission run. The finished source bytes,
authority, inline launcher and static proof must first receive two independent
implementation GO verdicts. Only then may Run 1 execute once. Any Run-1 failure
is terminal, suppresses Run 2 and forbids another remediation cycle, larger
deadline, reduced suite or reduced authority. Run 2 is authorized only by a
passing Run 1.

R-264 changes no codec algorithm, bitstream, decoded sample, Opus anchor,
product version or Orkela behavior. It therefore triggers no R-198 audio
comparison.

## Post-implementation static admission

After implementation, two independent auditors reviewed the same exact final
bytes without executing project code or tests. The first review exposed two
real blockers: a mutator exception was restored but not externally recorded as
a terminal harness error, and an unassigned-process branch marked termination
before `Popen.kill()` could succeed. Run 1 remained blocked.

The final candidate captures a mutator failure separately, restores the entire
transaction, emits a serialized `HARNESS_ERROR`, and then fails admission. It
also separates termination attempt from success, performs exactly one caught
unassigned-process kill plus bounded wait in `finally`, and cannot let either
error suppress Job close or the terminal receipt. Both auditors then returned
**GO** for these exact identities:

- bootstrap SHA-256:
  `463002769637422d4dc4b6de32056212d5623313779530bcc4699dd5fdb62a7f`;
- gate SHA-256:
  `c4529ffaee118d8fd51360babda6e88d7051b0c1fdeabacca200d11ff04ea908`;
- test SHA-256:
  `ab70ba0f807ec4f7f3332a852c06e1ac5a9b8462889c232ac504258dddf81ede`;
- authority SHA-256:
  `1fe9e4b8a2c1afd5b52643ecbcd76ee187e888d4220f4b8173072e2f5aad7c02`.

Static closure is exactly 82 bindings, 26 test methods, a 1,014-byte
newline-free launcher and 720 added executable lines including the launcher.
This dual GO authorizes exactly one fresh Run 1 under the frozen R-263 limits.
It does not authorize a retry after failure or any codec/audio/Opus execution.

## Terminal runtime outcome

The only authorized Run 1 returned terminal `FAIL` before tests started. Stage
1 ordinary stderr was interpreted as a framed length by Stage 0 and caused
`MemoryError`; the outer monitor then rejected Stage 0's ordinary traceback.
The receipt SHA-256 is
`9864dccc649846fceceea8c6fc7b4a7179697d4994baeb7755ef47fcd03a22f2`.
Containment ended with zero active Job processes and no matching Python
survivor. Run 2 and any further R-263 remediation are therefore forbidden.
Detailed evidence is retained in
[`../results/R263_S15_RUN1_TERMINAL_FAILURE_2026-08-03.md`](../results/R263_S15_RUN1_TERMINAL_FAILURE_2026-08-03.md).
