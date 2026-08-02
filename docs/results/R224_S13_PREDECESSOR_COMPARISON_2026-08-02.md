# R-224 S13 Predecessor Comparison

Date: 2026-08-02

Status: **PASS; predecessor identity closed; no codec improvement admitted**

## Question

R-221 compared the current R-215/S11 encoder path with a fixed official Opus
1.6.1 anchor, but all nineteen retained Resonith streams reported
`truth-fallback`. R-224 asks one narrow question before any phase-oracle work:
are those current streams and decoded samples actually identical to the exact
pre-S11 direct-Truth producer at historical commit
`ca87decf7d4b255bae11ce980e6f4be6fe3065f0`?

This is a required preceding-Resonith closure, not a quality, compression,
syntax, decoder, or release generation.

## Method

The audited controller exported the exact historical Git tree
`ca6b528b9024109c118aec537ce4488ceb5cd2eb`, validated and extracted its ZIP
archive into an isolated root, then ran the historical direct-Truth producer on
each of the nineteen frozen R-221 source PCM inputs. Every historical stream
was decoded through the frozen native Core and compared against the sealed
R-221 stream and decoded PCM.

Opus was not rerun. Equal historical stream and WAV duplicates were omitted
only after byte identity was established. Any payload-only or PCM-only
mismatch would have retained both historical artifacts and stopped the run
without publishing a passing aggregate.

The focused implementation suite passed `49/49` tests before the only
authorized fresh corpus execution. The tests include real historical-worker
payload-only and PCM-only mismatch paths, lexical and recursive reparse
rejection, exact process-handle lifetime accounting, full-argv binding,
authority mutation, archive traversal and alias rejection, and aggregate
publication behavior.

## Result

| Measure | Result |
|---|---:|
| Registered inputs | 19 |
| Historical executions completed | 19 |
| Historical/current payload identities | 19/19 |
| Historical/current decoded PCM identities | 19/19 |
| Skipped inputs | 0 |
| Duplicate input executions | 0 |
| Quarantined items | 0 |
| Mismatch artifacts | 0 |
| Controller wall time before aggregate | 339.6762922 s |
| Maximum child peak working set | 2,493,497,344 bytes |
| Retained bytes before aggregate | 16,389,899 bytes |
| Final retained package | 16,705,533 bytes |

The independent auditor re-derived every authority chain and confirmed that
all nineteen current R-221 Resonith payloads and all nineteen native decoded
PCM outputs are exactly identical to the historical pre-S11 direct-Truth
execution.

## Interpretation

The R-221 quality profile is a measurement of direct Truth at the tested rate,
not evidence that the persistent multi-partial S11 lane was active on the
registered corpus. This is negative but decisive evidence: adding a phase
syntax now would be unjustified. S13 must first show that a label-free,
phase-blind persistent lane is eligible and that a zero-cost exact-phase oracle
would materially reduce the final compressed Truth on long complete inputs.

The next gate is therefore analysis-only. It does not change bitstream syntax,
decoder behavior, the product version, or the fixed Opus anchor.

## Identities

- R-224 aggregate file SHA-256:
  `4f3ee90bda70b573d95250cd05fcac0cdf70b8cff6f3221f1491d46f93fa6864`
- Aggregate material SHA-256:
  `90629dfa11f20ae346ae6a11365c623c6e2eb66199f54159c0952ddc73713d12`
- Historical ZIP SHA-256:
  `6232d28b8ac4306821f58ed6be94de2db342814f0d7dc1c7f38adc94530752a6`
- Historical archive and extracted inventory: `572` entries each.
- Extracted inventory SHA-256:
  `72fd4991bae9c651e92bc5430afc11b9a67e8cc95a6a4542af9346d7876d4f7f`
- R-221 run identity:
  `470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c`
- Registered manifest SHA-256:
  `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0`
- Frozen preflight SHA-256:
  `a92b3ad2f04719c59cb1364294db1e4dc8d05a0872d1d590c85ef7920e1ca134`
- Controller SHA-256:
  `f4ed3b6197338918da381604dfc561038a6cfcdcd2cf0952929cefc3982e57c4`
- Focused-test source SHA-256:
  `5034aa835fe4aa40e4cd8e8e524163b72f240f8cbcea2f3c04adc9d241527b41`
- Local machine evidence:
  `G:\Resonith\artifacts\r224-s13-predecessor-comparison`

## Admission boundary

R-224 closes only the missing preceding-Resonith identity column. It does not
admit a phase oracle, phase anchors, a new opcode, an S13 codec generation, an
Opus rerun, a version increment, a product claim, or a release. The independent
verdict is recorded in
`docs/reviews/R226_R224_PREDECESSOR_AGGREGATE_AUDIT_2026-08-02.md`.
