# R-203 Candidate-Rich Interim Evidence

Date: 2026-07-29

Status: **INTERIM PASS FOR THE AUDITED EVIDENCE SPLIT; R-191 NO-GO**

Source branch: `codex/maf-r193-alpha`

Evidence boundary: analyzer test and conformance infrastructure only

## Frozen corpus

| Property | Value |
|---|---:|
| Generator | `R203-CANDIDATE-RICH-EXACT-1` |
| Cases | 288 |
| Topology distribution | `36 / 144 / 36 / 36 / 36` |
| Corpus bytes | 3,111,742 |
| Edges | 936 |
| Paths | 1,620 |
| Entries | 3,924 |
| Corpus SHA-256 | `fb7966d795ddb27d26fe76e4e141cc44a131d34505b386cb9ddf7052bf3f9df7` |
| Contract SHA-256 | `572db682e345bef4f448f049674d2edd62cfe972fc58a1a2ab36c2dd2459dd73` |
| Expected semantic SHA-256 | `cef44832e75ee3eee056544e644f61e040ccd64a081a6ef11cde910be754bc5f` |
| Inventory SHA-256 | `ba120afa8b437c476b5548935b210e4406a734e09a80554f67abf615c667c957` |

The finite domain crosses five graph topologies with unique/conflicting
ownership, no/zero/nonzero phase, protected evidence, and every observation
permutation. It supplements and does not replace the frozen 9,024-case R-197
corpus.

## Independent finite authorities

Authority A generates the reference graph/path solution. Authority B does not
import the native ABI or Authority A; it independently:

- enumerates graph edges and every legal path;
- derives internal and cross-path ownership conflicts;
- enumerates every conflict-free subset;
- computes the frozen score and path-ID tie law;
- selects the exact optimum.

Generation fails closed unless the two authorities agree on every edge, path,
conflict relation, score, ordering, selected set, and permutation invariant.

## Raw typed replay

The native bridge records the frozen
[`R203-EVIDENCE-SPLIT-1`](../reviews/R203_SEMANTIC_LEDGER_TELEMETRY_SPLIT_PREFLIGHT_2026-07-29.md)
classes:

- **Class A:** every semantic path, entry, manifest, and non-resource report
  field, including headers, control words, reserved words, fingerprints, and
  raw packed output;
- **Class B:** the exact 21-event non-memory ledger after independently checking
  that the complete 22-event total equals `work_units`;
- **Class C:** toolchain-local memory-page and resource telemetry with local
  ordering, bounds, and repeatability checks.

Only Classes A and B are cross-toolchain identity evidence. Class C is retained
per native binary and is not incorrectly treated as a portable allocator
identity.

The native C++ conformance executable also runs all 288 cases twice and checks
the packed binary transcript. Zero-output fill uses a non-null marker with
zero capacity, preventing accidental reinterpretation as preflight.

## Local toolchain replay

| Field | Clang 22 | GCC 16 |
|---|---:|---:|
| Cases | 288 | 288 |
| Total paths | 1,620 | 1,620 |
| Total entries | 3,924 | 3,924 |
| Maximum non-memory work units | 573,625 | 573,625 |
| Maximum work units | 576,097 | 576,097 |
| Total memory-page events | 463,860 | 463,860 |
| Maximum reserved host bytes | 25,892 | 25,892 |
| Maximum committed host bytes | 25,892 | 25,892 |
| Maximum peak live host bytes | 25,892 | 25,892 |
| Twice replayed | yes | yes |
| Wall time | 1.497 s | 1.518 s |
| Native binary SHA-256 | `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed` | `425a58feefc34cead230dbdc838d1b8c24aa29fecc269b96e4a700c47df784e7` |

All local semantic identities match:

```text
legacy semantic:
  d8b4c3aa8e397598fd012b568e5c98772c399b1845c11b8f3e87144b9f09e92b

typed semantic:
  5899c4f324290c47c786a7a9c86f2e8a2a0c51cd258aeaf43d634b793c628b7f

packed semantic:
  4b72967ad29a23722724b3338656dd4563d35419d35ac53ee65a7946b327da22

Class-A semantic:
  eb09e5243dd12525da5f35af42c8bbc5e2731689b98fe74155e38c6c9b8ca0c4

Class-A packed output:
  968019ce7e03fcd49d71d613b771b66bd880b70c8d4ad8a99c40087e43f91401

Class-B non-memory ledger:
  1db3a5ded97c1e29c7db6233e54314b9c5d23fe2cd70060a070b7a93de3d7385
```

The local comparator admitted both distinct binaries and preserved both
Class-C telemetry records. Its complete result is
`artifacts/r203/local-cross-toolchain-comparison.json`, SHA-256
`29bce1bb53eb0be1871ff68f382566ac453546def0d3468696c6e87473781c11`.

The GitHub workflow wires the same replay into GCC, Clang, MSVC, Linux ARM64,
AppleClang, and Android jobs. A fail-closed aggregate requires at least four
distinct native binary hashes before it can publish cross-toolchain equality.
Those remote jobs have not run on the current uncommitted source and are not
claimed as passed.

## Focused validation

| Gate | Result |
|---|---:|
| Candidate generator tests | 4 passed |
| Combined R-191/R-197/R-203 Python tests | 78 passed |
| Native CTest | 20/20 passed |
| Workflow static validation | passed |
| Git diff whitespace validation | passed |
| Public-tree Cyrillic scan | 0 findings |

## Remaining blocker

Two independent auditors approved the evidence split on the exact frozen
preflight SHA-256
`c9f736288e67f69622812149c2ab86e5f54439c9778bcf57068acd8b6585aa74`.
That GO authorizes the replay/comparator evidence implementation only; it does
not admit R-191.

The remaining admission work is:

- complete charge-site inventory and negative mutants for the seven dynamic
  non-memory event families;
- ordered prepare/outcome/commit/cancel/release capture and release-failure
  mutants for Class C;
- the frozen hostile, CPU/CUDA, cross-toolchain, and platform campaigns;
- release non-consumption proof and final independent GO/NO-GO.

R-191 remains quarantined until all of those gates pass.

## R-198 boundary

No Resonith bitstream syntax, encoder RDO, released encoded bytes, decoded PCM,
or Orkela behavior changed. This interim evidence therefore uses the focused
identical-output exception and does not claim a codec quality or compression
improvement. Any production solver/resource change receives the complete
registered-music comparison against the preceding Resonith generation and the
maximum-effort official Opus anchor.

### Released-codec identity comparison

The current working tree was compared with preceding accepted revision
`69c0d341b626d29dff6d951ec3485a437d42e767` through the released prospective
LPS5 encoder and decoder:

| Input/output | Previous bytes | Current bytes | SHA-256 | Result |
|---|---:|---:|---|---|
| Speech bitstream | 17,929 | 17,929 | `a85b1308a252714298f9ac5155d29c45b7a763275a28eef88fcc38ffd3042e80` | identical |
| Speech decoded PCM WAV | 187,404 | 187,404 | `eb34cdfb899ce76bf8e20a9d8260c021f6f6ca3d300c16c535eb8b654e5e6ce5` | identical |
| Mozart 3 s bitstream | 42,115 | 42,115 | `6004642e739bf5043b25be748b0ee1feb54d04df86f98e97cafe4f79eebe449c` | identical |
| Mozart 3 s decoded PCM WAV | 576,044 | 576,044 | `c0f6dcfb0c5466b11dc2bde87b006fed3e88a7e9f2da52965849add032b111aa` | identical |

The released CLI encoder/decoder entry paths contain zero references to the
partial-graph analyzer. Therefore an Opus quality/bitrate rerun would have no
changed candidate to compare in this evidence-only batch. The complete
registered-music and maximum-effort Opus comparison remains mandatory at the
first actual MAF/RDO/bitstream/decoded-output change.

## Reproducible local artifacts

- `artifacts/r203/r203-candidate-rich-exact-v1.jsonl`
- `artifacts/r203/candidate-rich-inventory.json`
- `artifacts/r203/clang-replay.json`
- `artifacts/r203/gcc-replay.json`
- `artifacts/r203/local-cross-toolchain-comparison.json`
- `artifacts/r203/release-identity/baseline/`
- `artifacts/r203/release-identity/current/`
