# R-226 R-224 predecessor aggregate independent post-run audit

Date: 2026-08-02

Status: **R-224 PREDECESSOR AGGREGATE GO; STAGE-1 PRE-CODE PLANNING AND BOUNDED IMPLEMENTATION ONLY; ALL PRODUCT AND SYNTAX ACTIONS NO-GO**

## Audit scope

This record independently audits the completed one-shot R-224 predecessor
execution at:

`G:\Resonith\artifacts\r224-s13-predecessor-comparison`

The audit is read-only. It does not rerun the historical producer, change an
artifact, authorize S13 syntax, or modify codec or product behavior. It checks
the completed evidence package against the frozen R-224 preflight and the exact
authorized runner.

## Frozen authorities

The independently recomputed authorities are:

| Authority | SHA-256 or identity |
|---|---|
| R-224 frozen preflight | `a92b3ad2f04719c59cb1364294db1e4dc8d05a0872d1d590c85ef7920e1ca134` |
| Authorized R-224 runner | `f4ed3b6197338918da381604dfc561038a6cfcdcd2cf0952929cefc3982e57c4` |
| Focused R-224 test module | `5034aa835fe4aa40e4cd8e8e524163b72f240f8cbcea2f3c04adc9d241527b41` |
| Registered manifest | `551a9462e4f0e253e58576e5252eaeb2115e1a667ec3d904822a3c3ede1b95a0` |
| R-221 run index | `ed1d8e5505ccf0fe0af4b59725e1f5e1c30fefc67218aff9b3608b9046140ecd` |
| R-221 aggregate | `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf` |
| Native Core DLL | `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed` |
| Pinned Python executable | `03168c01b7b7491423350e82c26fee71f35b43694d1319d3c668bda6903a0c38` |
| Pinned Git executable | `7b7971dd13f0c3a284e538601f2f9770b3a87dfaccb5fb52d68141c67ed22364` |
| Historical commit | `ca87decf7d4b255bae11ce980e6f4be6fe3065f0` |
| Historical tree | `ca6b528b9024109c118aec537ce4488ceb5cd2eb` |

The aggregate's `authorities_before` and `authorities_after` objects are equal
to each other and to the independently recomputed current frozen authorities.
The five declared unchanged producer/ABI files also match between the extracted
historical tree and the current authority snapshot.

## Aggregate and archive recomputation

| Evidence | Independently recomputed result |
|---|---|
| Aggregate file SHA-256 | `4f3ee90bda70b573d95250cd05fcac0cdf70b8cff6f3221f1491d46f93fa6864` |
| Aggregate material SHA-256 | `90629dfa11f20ae346ae6a11365c623c6e2eb66199f54159c0952ddc73713d12` |
| Deterministic `ca87dec` Git archive SHA-256 | `6232d28b8ac4306821f58ed6be94de2db342814f0d7dc1c7f38adc94530752a6` |
| Archive member count | `572` |
| Extracted-tree entry count | `572` |
| Extracted-tree inventory SHA-256 | `72fd4991bae9c651e92bc5430afc11b9a67e8cc95a6a4542af9346d7876d4f7f` |

A new in-memory `git archive` of the exact historical commit was byte-identical
to the retained ZIP. Every ZIP member type, path, mode, byte count, CRC-32 and
payload SHA-256 matched the aggregate inventory. Every extracted member matched
the corresponding archive payload, and the independently walked extracted tree
matched the retained extracted inventory and its canonical digest. The complete
evidence root passed the lexical ancestry, recursive reparse and hardlink
checks.

## Nineteen-item evidence graph

The registered order is complete and exact: 19 expected items, 19 aggregate
rows, 19 unique identifiers, and orders 1 through 19. The aggregate reports and
the audit confirms:

- payload identity: `19/19`;
- decoded PCM identity: `19/19`;
- skipped items: `0`;
- duplicate items: `0`;
- quarantined items: `0`;
- unexpected or missing item directories: `0`;
- retained mismatch artifacts: `0`;
- temporary publication residue: `0`.

For every item, the audit independently recomputed the R-221 receipt and work-
request hashes, source-file and source-PCM tuple, current stream bytes and hash,
decoded-WAV and decoded-PCM identities, and the two retained-file bindings. It
then reconstructed the complete R-224 work request from those authorities.
Every retained request was identical to the reconstruction.

All 19 canonical receipt material hashes validate. Each receipt is `PASS`, is
bound to the exact source/configuration/current comparator, records equal
historical/current payload bytes and SHA-256, records equal historical/current
decoded PCM SHA-256 and dimensions, and contains no mismatch artifact entry.
The aggregate row hashes, paths, payload/PCM fields, order and historical-tree
before/after digests match their request and receipt files.

Every worker receipt's historical module inventory resolves to regular files
inside the extracted `ca87dec` tree with matching SHA-256. Before/after module
inventories are equal. The loaded native library path and SHA-256 match the
frozen Native Core. The request argv, launched argv, worker `sys.orig_argv`,
receipt argv and aggregate-row argv have identical full lists and canonical
digests. Every child records `process_scope=exact-duplicated-popen-handle` and
one mandatory post-exit lifetime resource sample.

## Resource and retention results

| Bound or measurement | Result |
|---|---:|
| Controller wall before aggregate | `339.6762921999907 s` |
| Claimed outer run wall | approximately `340.3 s` |
| Sum of child wall times | `310.84087870000803 s` |
| Maximum child wall time | `187.2928161000018 s` |
| Sum of child CPU times | `302.375 s` |
| Maximum child CPU time | `184.421875 s` |
| Maximum child peak RSS | `2,493,497,344 bytes` |
| Per-child peak RSS ceiling | `< 4 GiB` |
| Maximum recorded disk high-water | `16,389,899 bytes` |
| Retained bytes before aggregate | `16,389,899 bytes` |
| Aggregate file bytes | `315,634 bytes` |
| Final evidence-tree bytes | `16,705,533 bytes` |
| Successful retained-package ceiling | `< 256 MiB` |
| Aggregate deadline | `< 30 minutes` |

Every item stayed within its frozen per-item wall limit, the 4 GiB RSS and work-
storage bounds, and the complete controller stayed within the aggregate time
and final-retention bounds. The retained-before-aggregate value plus the exact
aggregate file size equals the independently measured final tree size.

## Binary decisions

### A. R-224 predecessor aggregate

**GO.**

The actual `ca87dec` predecessor execution is complete, internally consistent,
and byte/PCM identical to all 19 sealed R-221 direct-Truth fallbacks. It closes
the preceding-generation comparison required before the S13 Stage-1 oracle.

### B. Stage-1 free-oracle boundary

**GO only for Stage-1 pre-code planning and the bounded encoder-side oracle
implementation described by the frozen R-224 preflight.**

Before Stage-1 execution, a Stage-1-specific frozen record must bind the exact
four source PCM identities, S11 observation/path/support identities, Basis
lengths, gain and frequency laws, lane caps, decoder and direct-Truth settings,
entropy backend, candidate order, resource ceilings, runner and focused tests.
The resulting implementation and focused tests require a separate independent
implementation audit before any Stage-1 machine run. Those are the remaining
admission blockers to execution, not permission to broaden S13.

## Explicit NO-GO boundaries

This audit does **not** authorize:

- paid phase syntax or an anchor opcode;
- decoder or bitstream behavior changes;
- an Opus rerun or search;
- product or public-API changes;
- a version change;
- promotion or release.

Stage 1 remains an encoder-side, free-phase oracle only. A failed Stage-1 gate
is a valid S13 no-change result. Any later existing-syntax experiment requires
the Stage-1 admission gate to pass; any new syntax, decoder, product, promotion
or release action requires its own later authorization.
