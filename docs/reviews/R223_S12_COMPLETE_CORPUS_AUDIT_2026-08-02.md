# R-223 S12 Complete-Corpus Independent Audit

Date: 2026-08-02

Verdict: **GO FOR S12 COMPLETION IN THE DECLARED DIRECT-COMPARISON SCOPE**

Blocking findings: **0**

## Audited boundary

The audit covers the preserved R-221 run at
`G:\Resonith\artifacts\r221-s12-bounded-rate-direct`, run identity
`470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c`,
and source revision `1c45376eebe7daa49904acae885c47d6d571cf87`.

It authorizes only acceptance of the saved S12 evidence for current S11
Resonith versus one fixed official Opus 1.6.1 maximum-complexity configuration.
It does not authorize an Opus frontier, quality-aware rate selection, a general
superiority claim, a release, or a version promotion.

## Independent checks

- Closed all 19 `run-index -> receipt -> retained file -> source` authority
  chains and rechecked the run identity, source revision, and actual hashes.
- Confirmed 16 `STRICT_MATCH` rows and exactly three
  `UNMATCHED_NEAREST` rows: `ebu-female-speech-en`,
  `ebu-male-speech-en`, and `ebu-sustained-sine`.
- Confirmed the three unmatched rows are absent from every equal-rate count,
  average, win, and claim.
- Re-decoded all 19 retained Opus files with the pinned official Opus 1.6.1
  decoder and obtained the exact retained PCM bytes and hashes.
- Re-decoded all 19 Resonith payloads with `NativeMain0Decoder` and obtained
  the exact retained PCM bytes and hashes.
- Replayed the complete objective metric set. Every result matched; three
  ESTOI differences from `2.22e-16` through `9.99e-16` are ordinary
  floating-point rounding and do not change any reported digit or decision.
- Reconstructed every requested-bitrate q5 transition. Attempts zero through
  three reproduce the frozen R-219 initial/feedback law; attempts four through
  eleven, where present, are exact midpoints of the current tightest observed
  bracket. No extrapolation, quality leakage, premature stop, or ledger drift
  was found.
- Confirmed a single fixed Opus configuration, official Opus 1.6.1, maximum
  complexity, and integer requested bitrate as the only calibrated coordinate.
- Independently recomputed aggregate and Markdown-report arithmetic from the
  item receipts.

## Admission decision

S12 is complete under the owner's explicit direct-comparison amendment. The
R-221 corpus is accepted as measured evidence, not as proof that Resonith is
generally better than Opus. The next architecture step may begin only under its
own evidence-first preflight and independent challenge.

`VERSION` remains unchanged because this is evidence admission, not a product
generation or release.
