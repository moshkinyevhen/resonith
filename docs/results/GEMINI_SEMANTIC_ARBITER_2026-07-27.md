# R-128/R-129 Gemini Semantic Arbiter Gate

Date: **2026-07-27**
Status: **LIVE PROPOSAL PASS; ENCODER ADMISSION PENDING**

## Result

Gemini 3.6 Flash analyzed the complete R-118 union through full-duration mono
16 kHz proxies. The response passed strict local schema/resource validation,
all provider files were deleted, and no credential, transcript, lyrics,
provider prose, or source audio entered the repository.

This result does **not** change the Resonith bitstream, bitrate, decoded PCM, or
player. It evaluates only whether an optional semantic model can propose
useful MAF search regions.

Machine report:
[`gemini_semantic_arbiter_r118_2026-07-27.json`](../../experiments/results/gemini_semantic_arbiter_r118_2026-07-27.json).

Source revision:
`574c0cdff2e7c722a0732cddf804d666ac7d108e`.

## Complete gate

| Property | Result |
|---|---:|
| Complete references | 3 |
| Heterogeneous R-111 items | 16 |
| Total files | 19 |
| Uploaded provider objects | 19 |
| Deleted provider objects | 19 |
| Proxy bytes | 19,412,922 |
| Proxy/local-DSP wall time | 5.631 s |
| Upload, analysis, deletion wall time | 108.404 s |
| Total wall time | 116.057 s |
| Input tokens | 15,931 |
| Output tokens | 10,023 |
| Thought tokens | 1,484 |
| Total tokens | 27,438 |

The provider returned 39 ordered events and 20 stable-region boundaries.
Sixteen of 19 clips received nontrivial multi-region proposals. Complete
Mozart received four events/regions instead of one label.

## What Gemini got right

The proposal separated the broad physical regimes required by MAF:

- stationary sine as coherent/steady tonal;
- pink noise as stochastic/stationary noise;
- speech as voiced source-filter state;
- claves, drum, and cymbal attacks as transient/decay state;
- solo tonal instruments as coherent or resonant state;
- dense music and film material as polyphonic/dense-mix state;
- speech specialists were requested only for speech-bearing inputs.

The independent family audit classified 28 proposed regions as supported,
11 as weak, and zero as contradicted. This is evidence that the model can
produce a useful top-level search map, not evidence that its representation
beats the local codec.

## Millisecond boundary correction

Provider timestamps are not trusted. Each proposed event is searched again on
the original PCM using a bounded local 20 ms energy/spectral analysis moving
at approximately 1 ms. Attack edges receive a final one-millisecond envelope
edge search. The result is an exact source-sample candidate; encoder RDO still
tests neighboring samples or deletes the event.

| Alignment property | Result |
|---|---:|
| Provider events | 39 |
| Locally supported | 24 |
| Locally unsupported | 15 |
| Largest absolute correction | 249.025 ms |
| Provider timestamp serialized directly | **No** |

The large observed corrections prove why cloud timestamps cannot be treated
as millisecond truth. Start/end endpoint events also exposed a local gate edge
case; the next revision recognizes exact stream endpoints before searching.

## Honest assessment

The current AI layer is **promising but not yet an encoder improvement**.
Thirty-nine events across roughly ten minutes of heterogeneous audio are too
coarse to describe every important speech or musical state. Four events for
complete Mozart are materially better than one whole-track label, but not
enough to drive detailed Basis lifetimes.

Therefore:

- no compression or quality gain is claimed;
- no provider event is admitted to a stream;
- no provider is required for offline encoding or decoding;
- the exact non-AI Foundry search and existing LPS6 stream remain complete
  fallbacks.

The next experiment performs per-clip analysis and divides long material into
bounded overlapping windows. Gemini supplies an explicit change ledger per
window; dense local DSP adds missed candidates and aligns every boundary; exact
decoder-in-loop RDO measures search reduction and prunes all non-paying state.
