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
- `extended_audio_corpus.json` — R-111 EBU SQAM and Xiph heterogeneous
  acoustic matrix, exact source identities, crops, channel policies, and use
  restrictions.
- `gemini_semantic_arbiter_gate.py` — R-128 secret-safe Gemini Files API
  adapter, strict proposal validation, upload deletion, and independent local
  DSP audit across the complete R-118 union.
- `prepare_extended_audio_corpus.py` — verified acquisition and deterministic
  lossless-FLAC-to-PCM16 preparation for the R-111 matrix.
- `results/extended_audio_corpus_prepared_2026-07-27.json` — exact hashes and
  signal configurations of the first prepared 16-clip matrix.
- `heterogeneous_gain_shape_gate.py` — R-107 energy/gain-shape/Opus
  complete-byte comparison across all prepared R-111 classes.
- `results/heterogeneous_gain_shape_2026-07-27.json` — complete machine report
  and per-artifact identities for the first 16-class architecture gate.
- `perceptual_gain_shape_gate.py` — complete speech, Emotional piano, and
  full-Mozart R-107 admission/breakthrough gate through the native Core.
- `results/perceptual_gain_shape_2026-07-27.json` — selected complete-file
  budget-72 report.
- `results/perceptual_gain_shape_b71_2026-07-27.json` — retained lower-rate
  complete-reference R-107 point.
- `bounded_value_entropy_gate.py` — R-113 complete-byte-constrained
  LPS5/LPS6 RDO with shared immutable analysis, native decoder verification,
  objective metrics, and exact fallback.
- `results/bounded_value_entropy_mandatory_2026-07-27.json` — speech,
  complete piano, and complete Mozart LPS6 gate.
- `results/bounded_value_entropy_r111_2026-07-27.json` — all 16 heterogeneous
  classes with per-class LPS5 fallback.
- `pvq_envelope_fast_gate.py` — R-108 integer PVQ envelope compiler and
  speech/sustained-tone fast gate.
- `results/pvq_envelope_greedy_projection_2026-07-27.json` — corrected greedy
  direction and projected-gain negative universal-base result.
  full-Mozart frontier point.
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
- `active_band_selection_gate.py` — R-103 closed encoder-only attempt to
  preserve quiet active bands before global energy allocation.
- `results/active_band_selection_2026-07-27.json` — the R-103 negative
  speech/piano fast-gate report; the complete Mozart run was correctly skipped.
- `voiced_predictive_gate.py` — R-104 bounded pitch/gain Innovation oracle
  with an independently parsed prospective decoder and complete-byte RDO.
- `results/voiced_predictive_2026-07-27.json` — the R-104 negative speech
  result that keeps recursive long-term prediction out of Main.
- `harmonic_basis_gate.py` — R-105 fixed-ROM, sparse-event, nonrecursive
  harmonic Basis RDO over lifetime and harmonic-count candidates.
- `results/harmonic_basis_2026-07-27.json` — the R-105 near-equal-byte
  negative result that requires continuous trajectories before reconsideration.
- `results/lapped_density_2026-07-26_summary.json` — R-061 closest-byte
  fixed/variable-density comparison showing implicit acoustic-state
  localization without a separate classifier.
- `native_lapped_timing.py` — R-063 release C++ decode timing, exact
  Python/native parity, and caller-owned workspace accounting on the pinned
  real-music crops.
- `native_lapped_analysis_timing.py` — R-068 scalar C++ forward-analysis
  timing and exact array parity against the fixed Python oracle.
- `native_lapped_frontier_timing.py` — R-070 six-budget end-to-end RDO timing
  with native analysis and candidate reconstruction.
- `native_lapped_packet_timing.py` — R-073 release C++ LPS1 pull timing,
  R-077 LPS2 transform-packet timing, and R-082 LPS4 two-workspace timing with
  exact Python/native parity and complete caller-owned workspace gates.
- `results/native_lapped_packet_timing_2026-07-26_summary.json` — the R-073
  hosted x64 pass; physical-device energy and transport I/O remain open.
- `results/native_lapped_transform_packet_timing_2026-07-26_summary.json` —
  the R-077 LPS2 16.74x-21.33x real-time and 191-195 KB hosted x64 pass.
- `results/native_lapped_compact_packet_timing_2026-07-26_summary.json` — the
  R-082 LPS4 12.83x-16.39x real-time and 29.8-38.0 KB hosted x64 pass.
- `lapped_packet_loss_gate.py` — R-074 authenticated-packet absence,
  deterministic output-only concealment, and exact later-Truth recovery on
  pinned real music.
- `results/lapped_packet_loss_2026-07-26_summary.json` — exact containment
  pass and the measured short independent-context packet rate failure.
- `results/lapped_transform_packet_2026-07-26_summary.json` — the R-075 LPS2
  exact-monolithic pass and 7.53%-7.75% short-packet overhead result.
- `lapped_chained_packet_gate.py` — R-078 single-owner transform-frame
  packetization, bounded one-half-window loss extension, and exact later
  packet recovery.
- `results/lapped_chained_packet_2026-07-26_summary.json` — the R-078 exact
  LPS3 pass with 2.98%-3.67% complete-byte overhead.
- `lapped_realtime_frontier.py` — R-079 joint half-window, packet-duration,
  complete-rate, spectral, pre-echo, and estimated-latency sweep.
- `results/lapped_realtime_frontier_lps3_2026-07-26_summary.json` — the R-079
  negative LPS3 frontier that isolates repeated packet metadata as the blocker.
- `results/lapped_realtime_frontier_lps4_2026-07-26_summary.json` — the R-080
  compact-record diagnostic pass at 46.44 ms estimated latency and
  10.56%-13.22% complete-byte overhead.
- `results/native_lapped_frontier_timing_2026-07-26_summary.json` — the R-070
  exact native-RDO speedup over the shared-analysis Python path.
- `results/native_lapped_analysis_timing_2026-07-26_summary.json` — the R-068
  exact-but-slower scalar baseline that directs kernel optimization.
- `results/native_lapped_analysis_hoisted_2026-07-26_summary.json` — the R-069
  exact hoisted-window result, measured against the preserved scalar baseline.
- `results/native_lapped_timing_2026-07-26_summary.json` — the R-063 hosted
  x64 timing result; physical-device energy and thermal gates remain open.
- `lapped_frontier_timing.py` — R-066 exact-stream comparison and development
  timing for repeated versus shared immutable transform analysis.
- `results/lapped_frontier_timing_2026-07-26_summary.json` — the R-066 local
  six-budget frontier timing; it is not a production throughput claim.
- `window_transient_gate.py` — R-064 all-long/all-short nearest-byte
  comparison using waveform, multi-resolution spectral, and onset-local
  pre-echo diagnostics before any mixed-window syntax.
- `results/window_transient_2026-07-26_summary.json` — the R-064 negative
  result that keeps short-window switching out of prospective LPF1.
- `lapped_streaming_gate.py` — R-071 independent-context packet overhead,
  quality, and seam-local diagnostic gate on pinned real music.
- `results/lapped_streaming_2026-07-26_summary.json` — the R-071 complete-byte
  pass; native envelope/session implementation remains a separate gate.

The Opus runner counts the complete Ogg file and records executable version
and SHA-256. A missing external tool is reported explicitly; it is never
silently replaced by a simulation.
