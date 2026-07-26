# Resonith/MAF Experiments

First required experiment:

```text
integer lifting baseline
vs
TIMBRE_BASIS + absolute PHASE_TRACK + integer lifting residual
```

The report for each clip must be stored:

- input hash and PCM format;
- encoder configuration;
- full payload breakdown;
- exact decoded output hash;
- objective distortion;
- encode/decode time;
- active atoms and state bytes;
- fallback rate;
- worst-case artifacts/notes.

No aggregate gain is considered a result without a per-clip table,
reproducible command and independent decode.

## Implemented experiments

- `maf_p0_benchmark.py` — original single-Basis and CIBS amortization test.
- `maf_p1_benchmark.py` — multi-Basis lifetime, continuous phase,
  transient-RDO, and real Opus ablation.
- `opus_anchor.py` — run official external `opusenc/opusdec` on a supplied WAV.
- `results/maf_p1_opus_2026-07-26.json` — raw first MAF-P1/Opus diagnostic.
- `real_music_corpus.json` — pinned URLs, licenses, credits, hashes, and crops.
- `real_music_benchmark.py` — deterministic PCM downmix, LiftPack/zlib,
  fixed/adaptive/full-RDO, and Opus ablation.
- `results/maf_p2_real_music_2026-07-26.json` — raw real-music phase report.

The Opus runner counts the complete Ogg file and records executable version
and SHA-256. A missing external tool is reported explicitly; it is never
silently replaced by a simulation.
