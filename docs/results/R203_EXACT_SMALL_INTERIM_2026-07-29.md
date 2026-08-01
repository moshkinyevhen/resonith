# R-203 Exact-Small and Fingerprint Interim Evidence

Date: 2026-07-29

Status: **INTERIM PASS; R-191 ADMISSION REMAINS NO-GO**

Scope: quarantined R-191/R-197 analyzer infrastructure only

## Outcome

The executable independent generator emitted all 9,024 frozen valid
exact-small presentation cases. Every case was replayed twice through the
public ABI with both Clang 22 and GCC 16 C++23 builds.

| Evidence | Value |
|---|---:|
| Frozen contract SHA-256 | `10e24fa8721dfe69c2e1be82f9ffcc83e5dc7b32da0a038d29ec46b943d761bc` |
| JSONL cases | 9,024 |
| JSONL bytes | 55,085,390 |
| JSONL SHA-256 | `1bf354dafa223f4350b79719e9e138df2262c52f22ce51a6d028eb4e56d3a306` |
| Shared semantic SHA-256 | `cf48eaa45b901934803b76c827f135f03278884ee25617995985cc3aca31ec2a` |
| Maximum work units | 33,479 |
| Maximum reserved/committed/peak host bytes | 2,104 / 2,104 / 2,104 |

Clang completed the twice-replayed corpus in 10.313 seconds; GCC completed it
in 10.420 seconds. Their DLL hashes differ, as expected, while their complete
canonical semantic hash is identical.

## Independent fingerprint correction

The Python field serializer falsified the former native lanes one through
three. The frozen law requires:

```text
(byte + 53 * lane) mod 256
```

The old C++ expression reduced `53 * lane` before integer promotion but did
not reduce the final sum. Native now performs the explicit final eight-bit
reduction. Input and output vectors match the independent serializer on all
four lanes, including boundary bytes
`0/96/97/149/150/202/203/255`.

The old token is not accepted as an alternate identity. It returns
`HASH_MISMATCH`, reports `STALE_INPUT`, and leaves caller path and entry
payload byte-identical. Fingerprint law and ABI remain version one and three
respectively because R-191 has never been admitted.

## Preserved behavior

- path and entry payloads are unchanged;
- path counts, entry counts, scores, statuses and all work-event totals are
  unchanged;
- two preflights are byte-identical;
- two fills have identical payload, report and ledger;
- Clang and GCC native and C-header gates pass;
- the combined independent/native pytest gate passes 62 tests.

The released encoder does not yet consume R-191 output. Final evidence must
still prove that fact and preserve the released bitstream/decoded-PCM goldens.
This interim identity correction therefore does not claim a codec algorithm,
compression, quality, Opus, or Orkela improvement.

## Negative evidence

The frozen exact-small corpus has **zero canonical edges, paths and entries in
all 9,024 cases**. The cyclic `detector_id` row prevents adjacent matches, and
the only same-detector gap has a frequency bound below the corresponding
template separation.

This corpus remains mandatory ABI, fingerprint, canonicalization and
permutation evidence and is not changed. It cannot, by itself, prove a
non-empty candidate-family union. A separate candidate-rich exact domain with
its own review, version and hash is therefore a blocking requirement.

## Remaining gates

R-191 remains NO-GO until the supplemental candidate-rich domain, frozen
10,000-case CPU campaign, six 10,000-case CUDA tile campaigns, boundary and
hostile corpora, complete independent status/report/ledger oracle, Step-9
sanitizer/fuzz/allocation/TSan replay, MSVC/Apple/Android hashes, released
encoder non-consumption proof, golden bitstream/PCM identity, and final
independent audit all pass.

Machine record:
[`r203_exact_small_interim_2026-07-29.json`](../../experiments/results/r203_exact_small_interim_2026-07-29.json).
