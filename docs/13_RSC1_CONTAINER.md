# RSC1 Compact Deterministic Section Container

Status: **NORMATIVE-DRAFT / EXECUTABLE SUBSET**
Date: 2026-07-26

## 1. Why `MAF0` is not the production container

The Python oracle currently uses `MAF0`: a JSON directory followed by generic
zlib-compressed NumPy arrays. It was useful while section shapes changed every
hour, but it is the wrong trusted boundary for a final codec:

- JSON adds a large variable grammar and non-canonical parser behavior;
- generic dtype and shape records expose research implementation details;
- zlib duplicates compression around payloads such as `LiftPack-1` that
  already own their entropy syntax;
- decompression requires dynamic output storage before the typed payload can
  even be validated;
- duplicate detection normally needs an allocation or quadratic search;
- worst-case parse work is harder to communicate to mobile, DSP, and chip
  implementers.

`RSC1` deliberately does less. It is a typed section envelope, not another
codec.

## 2. Fixed layout

```text
32-byte header
80-byte directory record × section_count
stored typed payload 0
stored typed payload 1
...
```

The header identifies version, profile, level, timebase, record count, and
directory CRC-32. Every directory record contains:

| Field | Bytes | Purpose |
|---|---:|---|
| type | 4 | Uppercase ASCII/digit section code |
| schema version | 2 | Typed payload syntax version |
| flags | 2 | Criticality; other Main-0 bits are zero |
| instance ID | 4 | Namespace within a type |
| start tick | 8 | Absolute timeline origin |
| payload offset | 8 | Zero-copy random access |
| stored bytes | 8 | Exact payload extent |
| raw bytes | 8 | Equal to stored bytes in Main-0 |
| CRC-32 | 4 | Fast local corruption rejection |
| SHA-256 | 32 | Cross-implementation content identity |

The record is exactly 80 bytes and the header exactly 32 bytes.

## 3. Canonicality is a complexity tool

Records MUST be strictly sorted by `(type, instance_id)`. Payloads MUST be
tightly packed in that same order. This gives the parser three useful
properties:

1. duplicate keys are rejected by comparing only adjacent records;
2. offset overlap and holes are rejected with one running cursor;
3. the entire structural pass is \(O(section\_count)\), allocation-free, and
   deterministic.

Canonical order is therefore not cosmetic serialization policy. It replaces a
hash table in the trusted decoder.

## 4. Integrity boundary

Opening a container validates structure and the directory checksum. It does
not hash gigabytes of audio before exposing the directory. A consumer then:

1. finds the typed section;
2. verifies its CRC-32 and SHA-256;
3. passes the verified payload to the matching normative primitive.

This preserves random access and bounded corruption domains. CRC-32 provides a
fast accidental-corruption gate; SHA-256 provides the stable identity used by
cross-implementation conformance. Neither is a digital signature.

Signatures, authenticated transport, and package trust belong above `RSC1`.

## 5. Main-0 bounds

- at most 4,096 sections;
- at most 512 MiB per section;
- at most 1 GiB of raw section payloads;
- timebase from 1 through 1,000,000,000 ticks per second;
- only stored self-encoded sections;
- no generic decompressor in the Core;
- no heap allocation, I/O, locks, logging, or mutable global state.

Unknown critical types reject the profile. Unknown non-critical types may be
skipped by the typed decoder.

## 6. Executable evidence

The Python writer/parser and C++20 whole-stream decoder share one canonical
557-byte Main-0 stream. It contains typed `CONF`, `ATOM`, `BRAW`, and `RSL1`
sections and has SHA-256:

```text
32e4e7d0f8b5ff7c2d7c33ed51579c24731d57ee9c681cbc480eee23e0e3aa74
```

The native conformance test performs one allocation-free
`RSC1 -> BRAW -> ATOM -> LiftPack -> Truth PCM` decode. Python independently
parses the same embedded bytes and reproduces all 40 output samples. The native
inspection API reports exact Basis, phase, gain, output, Innovation, and
LiftPack workspace element counts before any decode call.

## 7. What remains

The mono periodic path now supports a canonical state partition with
content-deduplicated `BRAW` sections and multiple state-local `ATOM` sections.
The decoder reuses maximum per-state workspace while one stream-wide `RSL1`
preserves honest residual accounting.

Main-0 still needs typed CIBS, transients, simultaneous Atom mixing,
multi-channel output, Innovation indexing, and checkpoints. Each new syntax
must enter through the same inspect-first, caller-owned-memory decoder
boundary; no generic metadata archive is added.
