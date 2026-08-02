# R-245 R-243 Phase-A runner remediation

Date: 2026-08-02

Status: **IMPLEMENTED, EXECUTION BLOCKED PENDING DUAL RE-AUDIT**

## Scope

This document records the single runner-only remediation permitted by the
R-243 Phase-A preflight. It does not authorize an evidence execution, a codec
source edit, Phase B, an R-232/R-240 control, a long input, R-198, or a product
change.

The rejected first implementation had runner SHA-256
`1a5b357b97375e149712219a016bf232f65954def182af9b34b3849f15c37f52`
and authority SHA-256
`aefb0134d0a38a6d5334db8c4f695ed40cac7949cb86532686bab8a9a2a6f5a7`.
It was never executed.

## Blocking findings and resolutions

1. **Direct worker and concurrent-controller bypass.** The rejected worker
   accepted a public mode and arbitrary output. A losing controller could also
   remove another controller's staging directory. The remediated controller
   acquires ownership only by atomically creating the exact staging directory.
   Pre-ownership failures neither clean nor publish. Each child requires a
   controller-created, hash-bound, one-use request with a 256-bit nonce, exact
   mode/output, exact request path and actual parent PID. The worker consumes
   the request with an exclusive marker before work.

2. **Authority/source TOCTOU.** Each worker now revalidates the complete bound
   authority and source before its terminal report. The controller revalidates
   authority, Git and source after every worker, before receipt creation and at
   the final publication boundary. The failure state records the last closed
   authority/source identity.

3. **Incomplete CPU/wall closure.** The parent installs an audited Windows Job
   `JOB_OBJECT_LIMIT_PROCESS_TIME` limit before resuming each suspended child,
   in addition to the existing one-process, memory, wall, storage and log
   bounds. The worker process-time value remains labeled as a proxy; the Job
   limit is the hard whole-process CPU gate. The controller rechecks its wall
   ceiling only after manifest hashing, receipt fsync, retained-size traversal
   and final authority/source validation, immediately before atomic rename.

4. **Lossy failure receipt.** A failure receipt now retains the monitored
   child's exit/wall/memory/disk/log evidence, completed-mode resources, the
   failing phase and the last validated authority/source state before owned
   staging is safely removed.

5. **Untied profile identity.** The profile report schema and timing report
   schema are validated, and the profiled rescored stream/PCM/report/SSE/byte
   identity must equal the timing worker's rescored identity exactly before
   profile predicates can pass.

6. **Golden false PASS.** The worker asserts the exact 128-case order, unique
   IDs, integer dtypes, canonical JSON readback and all sixteen nine-law maximum
   witnesses. The controller independently reopens, rehashes and validates the
   same structure before receipt publication.

7. **Weak reconstruction closure.** The exact preflight, preclearance audit,
   remediation record and runner are committed before authority freeze. The
   authority itself is created after that commit to avoid a self-referential
   commit hash. A successful immutable artifact retains byte-identical copies
   of the runner, authority, preflight and audit records in its hashed
   provenance directory.

## Remaining gate

The compacted runner must remain at most 600 physical lines and 64 KiB, pass
AST parsing and whitespace checks, and receive two new independent binary GO
verdicts over its exact SHA-256 and the newly frozen authority SHA-256. Only
those verdicts can authorize the single Phase-A evidence execution.
