# R-203 Evidence-Split Final Audit

Date: 2026-07-29

Status: **TWO-AUDITOR GO**

Audited contract:
[`R203-EVIDENCE-SPLIT-1`](R203_SEMANTIC_LEDGER_TELEMETRY_SPLIT_PREFLIGHT_2026-07-29.md)

Audited contract SHA-256:
`c9f736288e67f69622812149c2ab86e5f54439c9778bcf57068acd8b6585aa74`

## Audit history

The first proposal received NO-GO because it conflated semantic identity,
logical work events, and vendor-specific allocation requests. Revision 2
separated those evidence classes but initially left contradictory status
domains and insufficient cleanup/resource requirements.

The first independent auditor required:

- conservative independent bounds and remove/reclassify mutants for the seven
  dynamic event families;
- a checked full-ledger sum before deriving non-memory work;
- per-toolchain treatment of tight-budget and resource-failure prefixes;
- ordered allocation-transition evidence;
- exact preceding-toolchain resource regression checks;
- explicit R-197 supersession;
- a strict production-identity boundary for the focused exception.

Revision 2 incorporated those findings and received GO.

A second independent auditor then found:

- conflict with the earlier R-203 complete-report/22-ledger oracle clause;
- an impermissible weakening of the no-failure-after-publication cleanup law;
- fixture classes that were not frozen before toolchain execution;
- unclassified ABI-v3 report header/control/reserved fields.

Revision 3 explicitly superseded the conflicting evidence clauses, froze
ordinary `case_index` values `0..287` as Class A/B, retained the absolute
post-publication cleanup rule with required release mutants, and exhaustively
partitioned every `resonith_partial_path_report_v3` field.

Both independent auditors returned binary **GO** on the exact hash above.

## Authorization boundary

GO authorizes only:

- replay and comparator evidence classification;
- focused mutation tests for that evidence;
- test-only capture/inventory work that leaves production behavior unchanged.

It does not admit R-191, alter the ABI or solver, integrate the analyzer into
the encoder, waive frozen campaigns, or waive any applicable R-198 music/Opus
gate. A production cleanup reorder or other native behavior change requires a
separate preflight and independent GO.
