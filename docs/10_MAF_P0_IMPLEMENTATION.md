# MAF-P0 - the first executable audio codec

Date: 2026-07-26
Status: **IMPLEMENTED / EXPERIMENTAL**

## 1. What already works

Full path:

```text
PCM16 mono
→ period analysis
→ persistent periodic Basis
→ RAW or CIBS materialization
→ Q15 amplitude events
→ objective residual
→ compressed MAF0 container
→ independent decoder
→ PCM16
```

Sources:

- `../reference/maf_p0/` - codec, container, model, renderer, WAV I/O and CLI;
- `../reference/cibs0/` — bit-exact CIBS kernel;
- `../tests/` — round-trip, corruption, hash and quality tests;
- `../experiments/maf_p0_benchmark.py` - reproducible benchmark.

## 2. First benchmark

Corpus: synthetic harmonic sustained note, 10 s, 48 kHz mono PCM16.

| Mode | Stream | PCM saving | Quality |
|---|---:|---:|---|
| Raw Basis lossless | 55.728 B | 94.195% | exact |
| CIBS lossless | 55.971 B | 94.170% | exact |
| CIBS basis-q8/residual-q16 | 11.333 B | 98.819% | 66.13 dB, max error 8 |

Experimental CIBS model package: 3,654 B, separate from stream.

On a bank of 128 unseen harmonic bases:

| Basis representation | Compressed bytes | vs raw Basis |
|---|---:|---:|
| Raw int16 Basis | 64,866 | anchor |
| CIBS + exact correction | 67,557 | −4.15% |
| CIBS + q8 correction | 45,393 | +30.02% |

## 3. Interpretation

Positive:

- the architectural pipeline is truly executable;
- lossless round-trip bit-exact;
- CIBS q8 already reduces Basis bank by 30% on favorable unseen corpus;
- Basis is created once, CIBS does not work in the sample loop;
- corrupted section and wrong Basis hash are not committed.

Negative:

- CIBS exact still loses to raw Basis;
- on one Basis latent/correction/header are not amortized;
- residual occupies the main part of the full stream;
- synthetic periodic signal is a very light class;
- comparison with PCM does not mean victory over FLAC, Opus or xHE-AAC.

These negative results are part of the project, not hidden.

## 4. How to run on WAV

The current prototype accepts mono PCM16 WAV. Requires at least two training WAVs
for experimental CIBS model:

```text
python -m maf_p0 train-model model.npz note1.wav note2.wav note3.wav
python -m maf_p0 encode input.wav output.maf0 --mode cibs --model model.npz
python -m maf_p0 decode output.maf0 restored.wav --model model.npz
python -m maf_p0 benchmark input.wav model.npz
```

`PYTHONPATH` must include the repository-local `reference` directory before
running.

## 5. What you need before comparing with Opus

1. Several periodic segments and independent lifetimes instead of one Basis.
2. Continuous pitch/phase trajectory.
3. Transient path without pre-echo.
4. General lifting residual instead of zlib-only placeholder.
5. Stereo.
6. Real training corpus and nonlinear CIBS refinement.
7. Built-in Opus/xHE-AAC anchor runner.
8. MUSHRA-ready decoded outputs and full bit accounting.

## 6. Time estimate- limited compression test on sustained mono WAV: available now;
- real-instrument CIBS corpus and multi-Basis ablation: 2–4 days;
- first technical bitrate/quality test against Opus: 1–2 weeks;
- meaningful mixed music/classical prototype: 3–6 weeks;
- broad standard-grade conclusion will require months of corpus/listening work.

This is a timeline for continuous development, not a promise of victory by a specified date.
