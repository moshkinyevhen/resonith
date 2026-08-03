# R-159/R-160 Latent Source Pattern Field Gate

Date: 2026-07-27  
Status: **Synthetic + Real PCM / Exact structural proxy / Not a codec or Opus claim**

## Outcome

The architecture is constructive and exact, but the current predictor is not
yet a competitive general audio codec.

| Input | Analysis | Components / occurrences | Explained energy | Independent proxy | Structured candidate | RDO result |
|---|---|---:|---:|---:|---:|---|
| Changing-overlap synthetic | whole-field Basis | 1 / 10 | — | 2,491 B | 1,815 B | structured, -27.14% |
| EBU dense orchestra, 12.0 s | exact partial-spectrum LSPF | 2 / 1,082 | 55.2403% | 1,302,123 B | 1,296,657 B | structured, -0.4198% |
| EBU female speech, 3.0 s | anonymous NMF proposer + LSPF | 1 / 40 | 18.7253% | 189,099 B | 190,025 B | independent Truth |

All three reconstructions are sample-exact by SHA-256. The synthetic mixture
contains no exactly repeated complete mixed block. A separate short synthetic
candidate was found but rejected because it cost 49 bytes more than independent
Truth.

The 12-second whole-band diagnostic activated no component on female speech,
dense orchestra, or pink noise. Reversible partial-spectrum search activated
only the dense-orchestra low field; female speech and pink noise remained
fallbacks. The anonymous spectral factor proposer activated one speech field
on the three-second Fast diagnostic but did not amortize its Basis and events.

## Exact orchestra ledger

| Item | Bytes |
|---|---:|
| Independent PCM zlib proxy | 1,302,123 |
| Basis payloads | 267 |
| Basis-coupled event maps | 6,641 |
| One final Truth correction | 1,289,637 |
| Proxy headers | 112 |
| Complete structured proxy | 1,296,657 |
| Net saving | 5,466 (0.4198%) |

The two Basis entries explain 55.24% of waveform energy, yet the final
correction is only 12,486 bytes smaller than the independent proxy before
overhead. This is the central measured result: explained energy is not
equivalent to reduced entropy.

The first standalone global event grammar cost 9,536 bytes on the same 1,082
observations; the existing Basis-coupled delta maps cost 6,641. RDO therefore
keeps the old map. New grammar syntax is not allowed to make a stream larger.

## Exact speech ledger

| Item | Bytes |
|---|---:|
| Independent PCM zlib proxy | 189,099 |
| Basis payload | 1,009 |
| Basis-coupled events | 252 |
| One final Truth correction | 188,668 |
| Proxy headers | 96 |
| Structured candidate | 190,025 |
| Candidate loss | 926 (0.4897%) |
| RDO-selected result | 189,099, independent Truth |

The phase-preserving anonymous NMF proposer found one recurring factor with 40
placements. It did not classify a speaker or phoneme. The result proves the
proposer-to-Basis-to-final-Truth loop, not compression.

## What was implemented

- non-circular finite integer alignment and a boundary regression test;
- batched exact signature comparison without an `M x M` resident matrix;
- exact changing-overlap anonymous Basis inference;
- cross-channel occurrence union;
- global persistent per-Basis event accounting;
- exact two-step and multi-step sparse motifs that skip unrelated events;
- literal, constant, affine, run-length, and sparse-exception parameter laws;
- perfect-reconstruction integer lifting fields with one final time-domain
  Truth;
- deterministic phase-preserving shared-mask NMF as an untrusted anonymous
  factor proposer;
- exact factor-to-dictionary search with one final mixture Truth;
- explicit structured-versus-independent proxy RDO.

Ten focused tests cover synthetic overlap, uneconomic fallback, cross-channel
reuse, non-wrapping alignment, pair/path grammar, partial-spectrum hiding,
phase-preserving anonymous factors, and one-final-Truth reconstruction.

## Scientific relationship

The implementation combines mechanisms that already exist separately:

- Lewicki and Sejnowski demonstrated non-blocked shift-invariant sparse
  representations on speech;
- convolutive NMF models temporal spectral objects and monophonic mixtures;
- MixIT demonstrates unsupervised latent source estimates from mixtures;
- phase-aware separation and shared masks preserve information discarded by
  magnitude-only factorization;
- conventional codecs use local prediction and transforms, but not this
  per-track anonymous long grammar with complete-stream RDO.

The combination remains a research candidate. No novelty or patent claim is
made.

## Why the current version is not enough

1. Gain plus integer alignment cannot normalize speech pitch, formant, duration,
   phase, and coarticulation variation.
2. Haar lifting exposes only coarse bands; it does not isolate a persistent
   instrument or vocal tract.
3. Plain NMF provides stationary magnitude templates, not long
   convolutive/pitch-time trajectories.
4. Exact residual entropy remains high even when squared error energy is much
   lower.
5. Python/Numpy search is 8.3x to 13.3x realtime on these gates and is not the
   native CUDA Foundry.
6. The proxy uses zlib rather than the final Resonith/FLAC/Opus frontier and
   therefore cannot support a codec-quality claim.

## Next hard gate

The next candidate must jointly add:

1. convolutive anonymous fields rather than stationary NMF factors;
2. bounded pitch/time/formant and phase trajectories;
3. persistent source-filter and stochastic laws inside every anonymous field;
4. multiple simultaneously selected long sparse motifs and CompoundBasis DAGs;
5. native C++23/CUDA batched fitting with portable integer CPU parity;
6. one actual complete stream competing against current Truth/FLAC and matched
   official Opus quality.

The mechanism is not promoted if the real lossless median cannot beat the best
Truth/FLAC path by 5%, or if the first perceptual gate cannot reach 90% of Opus
bytes at non-inferior controlled quality.

## Reproduction

```powershell
$env:PYTHONPATH='.;reference'
python experiments/latent_source_synthetic_gate.py
python experiments/latent_source_pattern_gate.py `
  artifacts/corpus/prepared-r111/ebu-dense-orchestra.wav `
  --mode partial --maximum-seconds 12
python experiments/latent_source_pattern_gate.py `
  artifacts/corpus/prepared-r111/ebu-female-speech-en.wav `
  --mode factorized --maximum-seconds 3
```

Python: 3.14.6.

Result SHA-256:

- synthetic JSON:
  `c99eb1901c5000e3c7f07740393d887b13b6070a151d2908a3c44cf48ce8252e`;
- current orchestra JSON:
  `5b46c9677cd69eadfa45fafd907f5f22e233db35a02b85a4c3bb0ff5cdb742ad`;
- current speech JSON:
  `7c3d55c89718ff6afb9c79689dbd6ff8600ebdd9dfc3113a84bc3f8caf51a8db`.

The hashes above refer to the first generated files before this report was
added; rerunning after code or report changes intentionally produces a new
artifact hash.
