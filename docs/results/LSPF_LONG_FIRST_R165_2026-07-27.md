# R-165 Long-First Convolutive LSPF Gate

Status: **Real PCM / Fast diagnostic / Exact structural proxy**  
Date: 2026-07-27  
Claim boundary: not a full Resonith, FLAC, or Opus comparison

## Protocol

The generation followed the mandatory order:

1. analyze continuous long material first;
2. write and freeze its configuration, hashes, metrics, and selection;
3. only then analyze the short corpus;
4. retain independent Truth whenever the structured candidate loses.

Long material was the first 120 continuous seconds of the pinned complete
400.773-second Mozart overture. Short material used the 12-second prepared EBU
female-speech, dense-orchestra, and pink-noise references.

The candidate combined finite non-circular CNMF/NMFD anonymous fields, shared
cross-channel mixture-phase masks, per-factor exact LSPF Basis search, sparse
event maps, and one final mixture-domain Truth. The byte comparison is an
explicit zlib structural proxy:

```text
structured =
    proxy header
  + compressed Basis
  + event maps
  + compressed final Truth
```

It is not a Resonith container or an Opus-comparable lossy point.

## Results

| Input | Duration | Active fields | Basis placements | Independent proxy | Structured proxy | Delta | Wall time |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mozart overture | 120.000 s | 0 | 0 | 19,874,458 B | 19,874,554 B | +96 B / +0.000483% | 484.787 s |
| EBU female speech | 12.000 s | 3 | 144 | 189,099 B | 190,017 B | +918 B / +0.485516% | 148.061 s |
| EBU dense orchestra | 12.000 s | 0 | 0 | 1,302,123 B | 1,302,251 B | +128 B / +0.009830% | 76.820 s |
| EBU pink noise | 12.000 s | 0 | 0 | 1,395,427 B | 1,395,555 B | +128 B / +0.009173% | 506.595 s |

Every case reconstructed exact PCM and matched the declared SHA-256.

## Interpretation

The long result was frozen before short analysis and RDO correctly retained
independent Truth. Short speech proves that the current proposer can expose
repeated fields, but the compressed correction plus dictionary/signalling
costs more than the regions it replaces. Orchestra and pink noise admit no
economic waveform Basis.

Magnitude-CNMF is therefore rejected as a primary coding representation. It
remains useful only as an encoder-side onset, mask, partial-group, or boundary
proposer. The next primary path is phase-aware/time-domain convolutional sparse
coding plus separately owned coherent harmonic, bounded-inharmonic, transient,
stochastic, and route lanes under one final Truth.

## Reproduction

- Machine report:
  [`experiments/results/lspf_r165_long_first_2026-07-27.json`](../../experiments/results/lspf_r165_long_first_2026-07-27.json)
- Runner:
  [`experiments/lspf_duration_gate.py`](../../experiments/lspf_duration_gate.py)
- Convolutive proposer:
  [`reference/maf_p0/convolutive_anonymous_field.py`](../../reference/maf_p0/convolutive_anonymous_field.py)
- Exact factor/Basis wrapper:
  [`reference/maf_p0/convolutive_factorized_latent_field.py`](../../reference/maf_p0/convolutive_factorized_latent_field.py)
- Automatic duration policy:
  [`reference/maf_p0/lspf_analysis_policy.py`](../../reference/maf_p0/lspf_analysis_policy.py)
- Duration Pareto selector:
  [`reference/maf_p0/lspf_duration_rdo.py`](../../reference/maf_p0/lspf_duration_rdo.py)
