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
- `main0_native_music_benchmark.py` — typed RSC1 periodic RDO accepted only by
  the shared Golden Core, licensed one-second music crops, Opus anchors, timing,
  workspace accounting, and decoded WAV output.
- `listening_set.py` — deterministic opaque WAV labels plus a separate answer
  key for immediate informal blind listening.
- `additive_atom_oracle_benchmark.py` — R-038 matching-pursuit search over
  simultaneous periodic Atoms, with complete prospective RSC1 byte accounting
  and no decoder syntax change before the declared compression gate passes.
- `analytic_oscillator_oracle_benchmark.py` — R-039 fixed-ROM oscillator
  matching pursuit with one batched Atom bank, a zero-Atom residual anchor,
  and the measured raw-Basis envelope as competing full-byte baselines.
- `lpc_liftpack_oracle_benchmark.py` — R-042 exact block-local integer LPC
  with transmitted coefficient cost, independent prospective decode, and the
  R-041 block-size-RDO `RSL1` stream as the complete-byte anchor.
- `variable_block_oracle_benchmark.py` — R-044 exact-byte dynamic programming
  over variable residual lifetimes, with all fixed `RSL2` block sizes retained
  as mandatory fallbacks and no normative syntax assigned before its gate.
- `stereo_lifting_oracle_benchmark.py` — R-045 complete-byte competition
  among independent, reversible mid/side, left/side, and right/side stereo
  representations over the original licensed source channels.

The Opus runner counts the complete Ogg file and records executable version
and SHA-256. A missing external tool is reported explicitly; it is never
silently replaced by a simulation.
