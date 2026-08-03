# R-235 S15 final controller remediation

Date: 2026-08-02

Status: **IMPLEMENTATION AUTHORIZED; CONTROL EXECUTION REMAINS NO-GO**

## Problem and frozen objective

Both independent R-234 audits rejected the exact control command while
accepting the frozen selector, decoder recurrence, RDO formula, trace scope and
synthetic-only claim boundary. The remaining defect is evidentiary: executable
identity is not closed before imports, some terminal limit races and failure
records are incomplete, and the new controller lacks direct bounded witnesses.

The objective is to remove only those blockers. The DSP, candidate proposal,
eligibility thresholds, quality scalar, tie order, syntax, decoder, stream
version and source corpus remain unchanged.

## Considered alternatives

1. **No change:** rejected because the exact R-234 command remains NO-GO.
2. **Version strings plus top-level file hashes:** rejected because executable
   transitive modules and binary package contents can drift.
3. **Import first, enumerate `sys.modules`, then hash:** rejected because
   unauthorized import-time code would already have executed.
4. **Selected: stdlib-only bootstrap plus static local closure and runtime-tree
   hashes before imports.** The bootstrap parses local imports, requires an
   exact authority set, hashes the pinned Python `Lib` and `DLLs` trees plus
   runtime binaries, and only then imports NumPy, SciPy and project modules.
5. **Full control-suite as controller test:** rejected because it is the
   prohibited experiment. Short non-codec micro-workers test the same resource
   and transaction machinery within the focused-test budget.

## Authorized corrections

- move every third-party/project import behind successful stdlib-only
  authority validation;
- discover the local transitive import closure statically and require its exact
  authority mapping;
- hash the pinned Python runtime and complete `Lib`/`DLLs` contents, including
  executable bytecode/cache files, and bind every existing local `.pyc`/`.pyo`
  that the frozen interpreter could select;
- revalidate the identical closure after each worker;
- compare full `_BitWriter` state and a freshly computed authenticated identity
  of the live causally reachable excitation/output history during candidate
  evaluation;
- add the missing adaptive-vector, candidate-order/payload, later-prefix mel,
  tiny-floor and writer/state witnesses;
- recompute wall, logs and aggregate storage after process exit before any
  success is accepted;
- retain structured failing task/request, elapsed time, process/job memory,
  storage high-water, bounded log hashes/excerpts, authority/runner and last
  run-index hash in the external atomic failure receipt;
- put confined cleanup in `finally` and reject any matching orphan staging on
  startup;
- repeat authority validation in the parent immediately after child exit and
  retain measured resources when receipt/report validation fails;
- use bounded micro-workers to prove normal execution, timeout, child-spawn
  rejection, log/storage rejection, authority drift and stop-on-first-failure
  transaction behavior.

## Falsifiable gate

Focused tests, compile checks, authority validation and diff checks must pass
inside 120 seconds, 2 GiB and 256 MiB. The two prior auditors must then return
GO on the new exact hashes. Until that point the legacy-identity and four
120-second controls remain prohibited. Any requested DSP/RDO/threshold change
closes R-232 rather than expanding this remediation.
