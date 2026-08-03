# Causal Basis Field plus Truth R-176

Date: 2026-07-28  
Status: **Real PCM / Complete decoder-in-loop fast diagnostic / Rejected predictor**

R-176 tested the first complete `CBF1 + Truth` path. CBF1 compressed bounded
Basis-warp events, reconstructed an equivalent MFT1 program, obtained
sample-identical predictor PCM from the native C++23 decoder, and added one
lapped Truth. Corpus names are input identifiers only; no semantic source
class is used or transmitted.

This is a long-first four-input fast diagnostic, not the full R-118 or Opus
gate.

## Result

| Input | Direct Truth | CBF1 + Truth | Byte delta | Candidate/baseline SSE | Basis / instances | Covered samples | Wall time | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Mozart, 120 s | 1,883,620 B | 1,885,808 B | +2,188 B | 0.999999 | 1 / 2 | 2,048 | 351.876 s | Truth |
| Female speech, 12 s | 91,120 B | 97,837 B | +6,717 B | 1.043926 | 4 / 10 | 10,240 | 6.002 s | Truth |
| Dense orchestra, 12 s | 196,466 B | 223,784 B | +27,318 B | 1.788864 | 59 / 271 | 277,504 | 40.581 s | Truth |
| Pink noise, 12 s | 200,709 B | 201,057 B | +348 B | 1.000000 | 0 / 0 | 0 | 33.592 s | Truth |

The long Mozart result was frozen before the short inputs.

## What passed

- CBF1 reproduced every source MFT1 predictor sample for sample.
- CBF1 reduced predictor syntax where repeated instances existed. Dense
  orchestra decreased from 133,804 MFT1 bytes to 52,968 CBF1 bytes.
- Independent native decoding, final-Truth addition, corruption bounds, and
  direct Truth fallback passed.

## What failed

- The R-155 fixed-block waveform proposer found only two Mozart instances.
- Dense-orchestra prediction was not isolated by causal ownership; residual
  quality and bytes worsened despite strong command compression.
- The full Mozart run required 351.876 seconds in the old CPU pair fitter.

Therefore no CBF1 candidate was admitted and no release claim is made. The
transport is retained; the primary analyzer moves to R-177 anonymous
coherent-partial Basis states fitted only against their separately owned
harmonic lane. Inharmonic, transient, stochastic, and route laws remain
separate before one final Truth.

## Listening artifacts

Every selected file below is the direct-Truth fallback selected by exact RDO:

- [Mozart selected stream](../../experiments/artifacts/r176-cbf-truth/mozart-original-selected.resonith)
- [Mozart selected decode](../../experiments/artifacts/r176-cbf-truth/mozart-original-selected-decoded.wav)
- [Speech selected stream](../../experiments/artifacts/r176-cbf-truth/ebu-female-speech-en-selected.resonith)
- [Speech selected decode](../../experiments/artifacts/r176-cbf-truth/ebu-female-speech-en-selected-decoded.wav)
- [Dense-orchestra selected stream](../../experiments/artifacts/r176-cbf-truth/ebu-dense-orchestra-selected.resonith)
- [Dense-orchestra selected decode](../../experiments/artifacts/r176-cbf-truth/ebu-dense-orchestra-selected-decoded.wav)
- [Pink-noise selected stream](../../experiments/artifacts/r176-cbf-truth/ebu-pink-noise-selected.resonith)
- [Pink-noise selected decode](../../experiments/artifacts/r176-cbf-truth/ebu-pink-noise-selected-decoded.wav)

## Machine evidence

- [R-176 machine report](../../experiments/results/causal_basis_truth_r176_2026-07-27.json)

