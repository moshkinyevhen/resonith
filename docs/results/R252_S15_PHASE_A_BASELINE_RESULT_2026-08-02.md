# R-252 S15 Phase-A exact-LPC baseline result

Date: 2026-08-02

Status: **DUAL-AUDITED PASS FOR PRE-CHANGE EVIDENCE ONLY**

## Outcome

R-250 completed its only authorized invocation and atomically published one
successful evidence directory. Two independent read-only audits returned GO.
This admits the pre-change measurement needed by R-243; it does not admit a
codec algorithm generation, syntax, decoder, default, release, or quality
claim.

The exact evidence root is
`artifacts/r250-s15-short-baseline-prechange`. It contains 29 ordinary files
and four directories including the root, totalling 2,307,740 bytes. Its
canonical `receipt.json` has SHA-256
`b28f8d264d183d34a817f0523ec274cb2ac057df66413235e578d295ffedba8d`.
The 28-entry receipt manifest equals every retained non-receipt file by path,
size, and SHA-256. No staging, failure, future-summary, reparse, or competing
terminal path remains.

The local root retains the complete closure. Repository history carries the
canonical receipt, timing/profile reports, raw and deterministic text profile,
and both encoded streams. Large derived golden JSON, decoded PCM, duplicated
encoder reports, empty logs, worker requests, and provenance copies stay out
of Git because their exact identities are already closed by the published
receipt and the two audits; this is the R-211 minimal-evidence boundary, not a
different result set.

## Frozen measurements

| Metric | Legacy | Decoder-domain rescored |
|---|---:|---:|
| Complete stream bytes | 12,554 | 12,371 |
| Median process CPU | 10.578125 s | 39.031250 s |
| Median wall time | 10.6120175 s | 39.6908918 s |
| Decoded waveform SSE | 73,327,420,909 | 72,956,137,926 |

The rescored arm saves 183 bytes, or 1.45770%, and lowers waveform SSE by
371,282,983, or 0.50634%, but costs 3.68981 times the legacy median CPU. These
are short-source diagnostic facts, not an Opus comparison or general codec
claim.

The retained profile contains 648,120 calls to `_lpc_q14`, with 58.5003879
cumulative seconds inside 95.9350807 cumulative seconds for
`encode_maf_source_filter_analysis`: a ratio of 0.6097914076. All three frozen
Phase-A consistency predicates pass. This directly supports testing one
output-identical hoist of repeated reflection-to-LPC conversion.

## Exactness and resource closure

- Timing and profile runs produced byte-identical rescored streams, decoded
  PCM, and encoder reports.
- The retained golden matrix has 128 unique ordered cases: eight intervals,
  four law families, and four sample patterns. Sixteen maximum witnesses touch
  nine filter blocks.
- Candidate counters recompute to 1,464 subframes, 8,642 evaluated candidates,
  and 7,041 rejected candidates.
- Controller wall before receipt was 390.7651842 seconds under the 510-second
  bound. Timing and profile workers stayed within their CPU, wall, 512-MiB
  memory, 32-MiB retained-data, disk-high-water, and log bounds.
- The raw profile and both deterministic text views match their retained
  hashes. Re-rendering changes only the expected first-line path after the
  atomic `.staging` to final-directory rename; the statistics are otherwise
  byte-identical after that path is restored.

## Admission consequence

R-250 is accepted only as immutable Phase-A evidence. R-198 is not triggered
because no codec, oracle, bitstream, decoder, decoded sample, RDO policy, or
accepted generation changed.

The next safe action is a separate Phase-B preflight and independent binary
GO for the bounded per-subframe prepared-LPC helper described by R-243. That
change must preserve every candidate, arithmetic order, stream byte, decoded
PCM sample, report identity, and selection trace. No source edit is authorized
by this result alone.
