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
- `cross_channel_oracle_benchmark.py` — R-046 bounded one-MAC Q12 gain-delay
  prediction in both channel directions, shortlisted by energy and selected
  against the full R-045 fallback only by complete bytes.
- `subband_stereo_oracle_benchmark.py` — R-047 exact temporal Haar split with
  independently selected reversible channel lifting in low/high bands and
  only two unchanged RSL2 component streams.
- `cached_cibs_additive_benchmark.py` — R-051 held-out CIBS registry training,
  zero-through-four simultaneous cached periodic Atoms, complete prospective
  RSC1 accounting, mandatory zero-Atom RSL2 fallback, and explicit model-ROM
  amortization.
- `results/cached_cibs_additive_2026-07-26_summary.json` — the reproducible
  R-051 negative result that keeps simultaneous mixing out of Main-0.
- `packet_loss_benchmark.py` — R-054 aligned multichannel block-loss
  simulation on the pinned music corpus, with deterministic bounded
  concealment and exact post-loss Truth recovery checks.
- `results/packet_loss_2026-07-26_summary.json` — unrestricted and
  512-frame-ceiling containment results plus the measured Realtime byte cost.
- `stereo_opus_frontier.py` — R-056 complete-byte stereo sweep against official
  `opusenc/opusdec`, plus deterministic rate-matched blind WAV trials.
- `results/stereo_opus_frontier_2026-07-26_summary.json` — closest-byte
  diagnostic pairs and the explicit residual-only baseline loss.
- `lapped_opus_gate.py` — R-057 band-adaptive lapped sparse-grid sweep,
  nearest-byte Opus sanity gate, and deterministic blind listening trials.
- `results/lapped_density_2026-07-26_summary.json` — R-061 closest-byte
  fixed/variable-density comparison showing implicit acoustic-state
  localization without a separate classifier.
- `native_lapped_timing.py` — R-063 release C++ decode timing, exact
  Python/native parity, and caller-owned workspace accounting on the pinned
  real-music crops.

The Opus runner counts the complete Ogg file and records executable version
and SHA-256. A missing external tool is reported explicitly; it is never
silently replaced by a simulation.
