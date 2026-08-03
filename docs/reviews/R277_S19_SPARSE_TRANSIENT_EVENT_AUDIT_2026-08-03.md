# R-277 S19 Sparse Transient Event Audit

Date: 2026-08-03

Status: **INDEPENDENT IMPLEMENTATION GO; REAL AUDIO REMAINS BLOCKED**

## Audited package

- preflight SHA-256:
  `402a05ecefaa5867870c9825f77c528dac11e3a35094b80a0b065cd2eb870023`;
- authority SHA-256:
  `873c2e1d8f11288816ab3f1f7af39b8ed81ac903c5296a0238d8bf01e3f2b862`;
- synthetic-vector SHA-256:
  `44740bc5dc8fa38ebe8eac178392079c75179ad5d9f75c24e16bd891fd551503`.

The independent auditor rehashed all 29 declared authorities, parsed the long
speech and drum incumbents, and independently decoded the retained 44,247-byte
drum incumbent to the expected PCM16 SHA-256
`70a8b5a14bcfa1b071098580fc9ef37b9ec05076ce040700e9e49d4c7b163620`.

## Blockers closed before code

The initial package received NO-GO. Remediation made the following executable
and falsifiable before implementation:

- exact TSE1 header, record, position, ZigZag ULEB128, CRC, ordering, and outer
  RSC1 syntax;
- checked signed Haar arithmetic, PCM16 residual domain, and sole final
  saturation;
- bounded compressed payload, expanded persistent event bank, index, scratch,
  seek, callback, and canonical `K + 12*N` resource score;
- exact detector domain, threshold, neighborhood, one-frame fallback,
  enumeration, deduplication, Pareto axes, heuristic local cost, DP objective,
  and complete-stream selector;
- retained exact long-speech and drum incumbents, immutable baseline Core, and
  a distinct S19 build directory;
- complete-quality guards including circular coherence and the exact frozen
  3-ms/10-ms pre-echo metric;
- exact rational byte-saving arithmetic, byte-identical no-event fallback,
  overflow mutants, and inner-parser mutants with valid outer integrity.

## Authorization boundary

GO authorizes only the allowlisted reference/native implementation and focused
synthetic conformance tests. It does not admit syntax, change the accepted
codec generation, authorize real-audio execution, or trigger a complete corpus
or Opus comparison.

Before any real audio, the implementation sources, baseline and candidate
binaries, commands, dependencies, fixtures, and expected outcomes must be
sealed in a new execution manifest and receive a separate independent GO.

