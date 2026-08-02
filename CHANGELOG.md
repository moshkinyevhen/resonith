# Resonith Changelog

All notable released changes are recorded here. Measured claims link to
reproducible evidence; targets and hypotheses are explicitly labelled.

The format follows Keep a Changelog principles and the project uses Semantic
Versioning for implementation releases. Bitstream syntax has its own declared
version.

## [Unreleased]

### Evidence and repository history

- Completed the output-identical R-218 S11 analyzer acceleration at commit
  `64521b19551d4b9688de10fe01c5302607a5beb1`; codec payload and decoded PCM
  identities are unchanged.
- Added the audited R-219 direct comparison controller for current Resonith
  versus one fixed official Opus 1.6.1 configuration. The partial long-first
  run retained complete per-file bytes and actual-decoder quality metrics, then
  failed closed when four bounded rate attempts missed the first registered
  speech item.
- Added R-220 short and 319.38-second LibriSpeech diagnostics. Resonith decoding
  is faster than real time on both; the long encoder is 11.78 times real time,
  while the short analyzer-rich path is not real time. At matched bytes,
  Resonith has higher waveform SNR but lower STOI/ESTOI and worse log-mel than
  Opus, so no speech-quality victory is claimed.
- Completed and independently admitted the R-221 S12 direct comparison in its
  narrow declared scope. All 19 registered inputs were decoded and audited;
  16 are strict complete-byte matches and three are retained diagnostic
  mismatches excluded from equal-rate claims. Resonith wins waveform SNR on
  13/16 strict rows, registered channel-0 phase MAE on 15/16, pre-echo on
  14/16, and log-mel on 9/16, while Opus wins detailed log-spectrum distance on
  11/16. This is a measured error-profile diagnosis, not a general
  better-than-Opus claim.
- Made GitHub synchronization durable: every coherent pushed change now carries
  an English changelog entry, R-number, validation record, updated all-63-step
  checkpoint, and commit identity. Experimental commits do not increment the
  product `VERSION` or imply release.
- Closed the missing preceding-Resonith column with the audited R-224 actual
  historical execution. All 19 frozen R-221 payloads and all 19 native decoded
  PCM outputs are byte-identical to the exact pre-S11 `ca87dec` direct-Truth
  producer. This proves that the registered R-221 result measured direct Truth,
  not an active persistent-partial lane; no codec improvement, syntax, version,
  Opus rerun, or release is claimed. The coherent evidence package is commit
  `434d12fa3de72aacb3a2361bf99283f2caab42d0`.
- Froze and independently audited the R-227 S13 phase-poisoned tiled-shadow
  experiment. It uses a complete four-input authority, bounded twelve-second
  target tiles, phase-free integer support and knot selection, paired existing-
  syntax carry/reset arms, actual complete-byte/native-decode accounting and a
  strict kill gate. R-228 authorizes only the smallest implementation; long
  execution, syntax, versioning and release remain blocked. The public pre-code
  checkpoint is commit `1c375d9f3ffe4f80b152e8015d0e25e9797f2ebf`.
- Implemented the bounded R-227 runner and retained the independent R-229
  NO-GO instead of hiding it. The bounded remediation replaces forgeable phase
  strings with a durable capability vault, validates and natively decodes the
  exact 600-placement periodic control, records the complete loaded-module
  inventory, and passes 17/17 focused checks. Long execution remains blocked
  until the committed bytes receive a fresh independent GO.

### Research

- Accepted the R-190 edge analyzer contract and retained the remediated R-191
  path ABI as quarantined infrastructure pending its final R-203 admission
  gate. Existing evidence proves bit-exact Python/C++23 edge/path fixtures,
  bounded transactional v3 safety, sanitizers, exhaustive allocation
  failpoints, and broad platform compilation, but it does not yet execute the
  frozen R-197 finite/10,000-case/six-tile corpus or admit R-191 output.
  Predictor, syntax, compression, Opus, release, and player claims remain
  blocked.
- Accepted R-182 through R-189 as a quarantined whole-track causal-analysis
  sequence: anonymous complex partials now precede source grouping; canonical
  spectral peaks precede half-open band allocation; continuity, local
  potential, and protected weak-line top-K families remain independent; proxy
  values are never reported as Truth bits. The audited synthetic gate passes
  clean 440.3 Hz phase, both crossing chirps, an approximately -47.6 dB weak
  line, white-noise resource pruning, and exact-small disjoint selection.
  Predictor, syntax, complete-byte, Opus, and release claims remain blocked
  pending native C++23/CUDA parity and a second audit.
- Accepted R-161 as the project priority lock. LSPF is now the only active
  compression-architecture priority until its convolutive fields, bounded
  transform laws, physical-law competition, long grammar, global
  correction-entropy RDO, native Foundry, and full R-118 gates pass or are
  explicitly rejected. Every material generation must retain original,
  encoded Resonith, actual Resonith decode, official Opus, actual Opus decode,
  preceding Resonith, metrics, hashes, and the exact tested Orkela package.
- Accepted R-162: every LSPF package now runs short diagnostic and continuous
  120-second-or-longer material simultaneously. One syntax/decoder serves all
  durations; the encoder deterministically adapts scales, convolution/search
  depth, dictionary lifetime, checkpoints, residency, and scheduling while
  publishing the complete chosen plan and retaining every fallback/quality
  invariant.
- Accepted R-163 duration-Pareto preservation: a proven long-input mode remains
  an explicit RDO candidate while short-input behavior is tuned, and vice
  versa. New tuning may add specialized candidates but cannot silently replace
  an incumbent. Per-input manifests retain all alternatives, quality
  eligibility, complete bytes, rejection reasons, and the selected winner.
- Accepted R-164 long-first testing and dual-axis success. Each generation now
  freezes continuous 120-second-or-longer evidence before short tuning. A
  candidate is retained when it either lowers complete bytes at the quality
  floor or improves quality inside the declared matched-byte tolerance;
  duration-specific wins are not erased by failure in another bucket.
- Accepted R-165: a rate-only or quality-only result now triggers immediate
  bounded optimization of the missing axis before the generation is fixed.
  Two-axis wins may close after verification; one-axis wins close only after
  the declared refinement budget is exhausted and remain retained Pareto
  points with the complete refinement trace.
- Accepted R-166 maximum-effort Opus anchoring. Every material real-audio gate
  now uses official libopus at complexity 10 plus an applicable
  application/signal/frame/VBR/bandwidth/bitrate search, official decode, full
  container accounting, and retained candidate evidence rather than a single
  convenient preset.
- Accepted R-167 through R-169: coherent complex partial bundles and the causal
  acoustic mechanism objective now separate harmonic, bounded-inharmonic,
  transient, stochastic, and phase/room/channel-route lanes. Lanes may overlap
  additively but have single rate ownership, are summed before one final Truth,
  and require no semantic source labels.
- Completed the R-165 long-first exact structural proxy. The 120-second Mozart
  candidate lost 96 bytes (0.000483%) and selected independent Truth; short
  speech found three fields and 144 placements but lost 0.485516%, while dense
  orchestra and pink noise selected Truth. R-170 therefore retains
  magnitude-CNMF only as a proposer and moves the primary path to
  phase-aware/time-domain causal lanes.
- Accepted R-171 Causal Sequence Atlas. Pattern discovery now indexes
  canonical causal event transitions rather than relying on whole-waveform
  windows. Exact suffix-automaton states cover every origin and complete
  repeated-length interval for literal, offset, first-difference, and bounded
  second-difference pitch/gain/phase/route laws before global RDO.
- Accepted R-172/R-173 all-lane factorized law atlases. Harmonic,
  bounded-inharmonic, transient, stochastic, and route events remain separate;
  timing, pitch, phase, gain, envelope, resonator, and route laws are indexed
  independently before bounded synchronized composition. This prevents an
  unrelated phase or route mismatch from erasing a reusable causal law.
- Completed the R-171–R-173 long-first discovery diagnostic. The first 120
  seconds of Mozart produced 681 transformed harmonic classes, the rejected
  all-coordinate conjunction produced zero, and the corrected factorized-law
  atlas covered 258,664 overlapping end-position classes across 64,501 lane
  events in 69.576 seconds. Speech, dense orchestra, and pink noise produced
  22,875, 12,238, and 22,511 factorized classes respectively. These are exact
  reconstruction and search-coverage results, not bitrate or Opus claims.
- Added R-174 exact byte-priced causal-law ledgers: literal, immutable token
  dictionary, and bounded acyclic hierarchical pair grammar compete by actual
  compressed payload bytes. The decoder verifies bounds, backward-only rules,
  checksum, full expansion, and exact token round-trip. Corpus names remain
  evidence labels only and never become transmitted source classes.
- Completed R-174/R-175 long-first ledger gates. Mozart factorized-law tokens
  decreased 15.761871%, then one shared timeline per causal lane reduced the
  exact event ledger from 602,415 to 471,002 bytes (-21.814364%). The same
  event-ledger selector reduced separate female-speech, dense-orchestra, and
  pink-noise inputs by 8.105210%, 9.904385%, and 14.411588%. Short transient
  and tiny harmonic lanes retained row fallback where column headers lost.
  These are metadata-ledger results, not complete Resonith or Opus gains.
- Added R-176 Causal Basis Field research transport and complete decoder-in-loop
  candidate. CBF1 stores one immutable Basis dictionary and compressed
  anonymous warp-event ledger per emitter, reconstructs a sample-identical
  native MFT1 DSP program, and adds one final lapped Truth. CBF1, direct MFT1,
  and direct Truth remain actual-byte fallbacks; native direct CBF1 execution
  and full R-118 evidence are pending.
- Completed the R-176 long-first gate. CBF1 plus Truth lost by 2,188 bytes on
  120 seconds of Mozart and fixed-block discovery covered only 2,048 samples;
  speech, dense orchestra, and pink noise also selected Truth. CBF1 itself
  remained sample-identical to native MFT1 and reduced the dense-orchestra
  predictor from 133,804 to 52,968 bytes, isolating causal coverage and final
  correction—not transport—as the blocker. R-177 therefore replaces the
  primary fixed-block proposer with unnamed clustered partial-Basis
  trajectories fitted only against their separately owned harmonic lane.
- Added R-159/R-160 Latent Source Pattern Field and its
  minimum-description anonymous field grammar. The exact research oracle now
  uses non-circular finite alignment, batched similarity evaluation,
  cross-channel occurrence reuse, one final Truth identity, global event
  ledgers, and byte-selected sparse pair or multi-step motifs whose steps may
  skip unrelated events. A perfect-reconstruction partial-spectrum wrapper
  searches independently normalized lifting bands without losing discarded
  coefficient bits. Focused tests include changing overlap, cross-channel
  routes, arbitrary gaps, affine laws, partial-spectrum contamination, exact
  CRC/decoder round-trips, and explicit uneconomic fallback.
- Measured the first R-160 synthetic structural proxy at 1,815 bytes versus
  2,491 independent proxy bytes (-27.14%) with exact PCM SHA-256; a short
  candidate costing 49 extra bytes was rejected. These are Synthetic / Proxy
  results, not full Resonith, FLAC, or Opus claims. The first real whole-band
  diagnostic on speech, dense orchestra, and pink noise admitted no component,
  correctly exposing partial-spectrum/source-field inference as the current
  blocker rather than hiding the loss behind fallback.
- The exact partial-spectrum R-160b diagnostic activated two anonymous Basis
  entries and 1,082 occurrences on 12 seconds of dense orchestra. They
  explained 55.24% of energy but reduced the exact structural proxy only 0.42%
  (1,296,657 versus 1,302,123 bytes). A phase-preserving anonymous NMF proposer
  found 40 speech occurrences but its complete candidate was 0.49% larger, so
  RDO retained independent Truth. This establishes residual entropy—not source
  discovery alone—as the next blocking metric.
- Completed the R-156/R-157 gridless warp execution loop. Native every-origin
  rolling hashes and arbitrary interval manifests now feed a C++23/CUDA
  fractional-phase, forward/reverse, constant/linear pitch-time and signed
  gain lattice. The RTX 2080 Super gate produced exact CPU/GPU parity for
  6,912/6,912 candidates in unequal tiles. An integrated exact global RDO
  diagnostic selected one Basis with eight arbitrary placements and reduced
  a favorable lossless construction from 1,156 to 704 bytes (-39.10%) while
  reconstructing PCM exactly. This is architecture evidence, not an Opus or
  real-audio compression claim; the complete R-118 gate remains mandatory.
- Added STEP M-151 Complete Pattern Field: the C++23/CUDA Foundry now searches
  every member of a declared finite multiscale/time/channel lattice, including
  forward/reverse circular Basis traversal and signed constant/linear Q1.15
  gain, with exact CPU/GPU parity. A bounded global chart prices shared Basis
  activation, placements, exact correction, actual MFT1 bytes, and independent
  Truth fallback. Orkela `0.3.0-alpha.3` directly executes the emitted MFT1
  subset on Windows and Android. This is constructive architecture evidence;
  full R-118 and standardized composite-Truth transport remain pending.
- Measured Gemini 3.6 Flash as an untrusted proposer on PCM16LE hexadecimal
  sequences. It recalled coarse synthetic targets but only 1.744% of eligible
  real-speech relations and no exact Q1.15 parameters, so it cannot prune the
  deterministic Foundry. The frozen identical GPT-5.6 Sol `max`/`pro` gate
  reached the OpenAI API but the configured project lacks model access; no Sol
  quality result or winner is claimed.
- Added the separate blind Codex `gpt-5.6-sol` / `Ultra` R-154 gate. Sol
  recalled all `24/24` synthetic and `172/172` real-speech eligible relations,
  versus Gemini `8/24` and `3/172`, but exact Q1.15 parameters remained
  `0/24` and `18/172`. Sol is admitted only as an expensive high-recall
  proposer/auditor; the native fitter, complete CUDA Foundry, and
  decoder-in-loop RDO remain authoritative.
- Added R-149/R-150 evidence-grade Foundry foundations: an optional native
  CUDA/NVRTC 13.3 C++23 backend exhaustively evaluates every declared
  block-pair, circular-phase, and signed constant/linear Q1.15 gain candidate
  in deterministic VRAM tiles with exact CPU parity. Removed the former
  seed/probe search budgets from motif discovery. Added a scale-parallel,
  non-greedy hierarchical grammar oracle that lets direct large spans,
  transformed state-increment compounds, existing Basis entries, micro-atoms,
  and Truth compete in one exact bounded minimum-description chart. These are
  architecture and synthetic-conformance results, not real-audio or Opus
  compression claims. The exact parity, 26.50% favorable synthetic saving,
  and mandatory Truth fallback on the first exhaustive real-speech diagnostic
  are published in
  [the complete GPU Foundry report](docs/results/COMPLETE_GPU_FOUNDRY_2026-07-27.md).
- Implemented R-142/R-145/R-146/R-147 immutable motif orbits: native MFT1
  Basis Instances, circular phase/counterphase alignment, exact linear gain
  trajectories, semantic-free reversible partial-spectrum dictionaries, and
  global cross-channel Basis placement. Constructive lossless diagnostics
  reduced a partial-band mixture by 42.06% versus independent Truth and a
  phase/envelope stereo transfer signal by 76.51% versus the best reversible
  stereo Truth mode. The first real speech and six whole-waveform controls
  retained exact Truth, so no real-audio, Opus, R-118, or default-codec claim
  is made. See
  [the motif-orbit evidence](docs/results/PARTIAL_SPECTRUM_ORBIT_2026-07-27.md).
- Added R-131/R-134 exact-sample semantic-boundary candidate sets and immutable
  periodic Basis lifetimes. A deliberately favorable EBU SQAM sustained-tone
  fast diagnostic reduced complete bytes by 75.15% against direct Resonith
  Truth while improving waveform SNR, but regressed log-mel error; it remains
  research evidence and makes no Opus or general-audio claim. See
  [the exact-boundary and periodic-MAF report](docs/results/PERIODIC_MAF_AND_EXACT_BOUNDARIES_2026-07-27.md).
- Completed the R-135 19-item typed-MAF gate. Zero candidates passed both
  complete-byte and multi-objective quality admission, so all selected
  artifacts remain exact preceding Resonith fallbacks. The rejected
  electronic-tune candidate exposed a large rate opportunity and an equally
  clear spectral-allocation failure. See
  [the complete R-118 report](docs/results/TYPED_MAF_R118_2026-07-27.md).
- Closed residual-budget and gain-shape reallocation as fixes for the
  full-band MAF spectral regression. R-137 found a 63,412-byte eligible
  ordinary Truth point on EBU electronic tune, while every enabled MAF family
  failed the spectral guard. This Truth saving is explicitly excluded from
  MAF claims. See
  [the frontier and ablation report](docs/results/MAF_TRUTH_FRONTIER_AND_ABLATION_2026-07-27.md).
- Adopted R-139 content-defined immutable motif memory: exact one-shot Basis
  reuse first, followed by bounded gain/phase and pitch/time-normalized
  instances with objective correction and optimized Truth fallback.
- Added R-130 prospective `MFT1`, the first executable typed MAF lifetime
  stream for stable source filters, counter-addressed stochastic fields,
  phase-continuous impulse or stochastic excitation, bounded transients, and
  persistent output mixes. The allocation-free C++23 decoder validates CRC,
  canonical records, references, lifetimes, stable filters, exact memory, and
  operation budgets before playback. Clang 22, GCC 16.1, Android NDK r29,
  C99-ABI, callback-partition, transactional-failure, and 20,003-input
  adversarial smoke gates pass. This is a decoder/syntax milestone only:
  complete R-118 encoder evidence remains pending, so no compression or
  quality improvement is claimed.
- Strengthened R-129 boundary handling: cloud timestamps are search-window
  centers only. Local original-PCM analysis produces exact sample candidates,
  and exact decoder-in-loop RDO must test their neighborhood together with the
  no-boundary alternative before any timestamp can enter a stream.
- Replaced magnitude-based Q15 rounding with the R-127 signed
  quotient/remainder rule after Windows ARM64 exposed positive saturation for
  negative transient samples. The rule retains exact ties-away-from-zero and
  the existing desktop vectors while making the sign path explicit.
- Added the R-126 strict GCC 16.1 C++23 compatibility gate and fixed one
  GCC-only narrowing diagnostic in bounded MAF filter-history traversal
  without changing fixed-point or PCM behavior.
- Added R-124/R-125 optional AI semantic arbitration. Gemini is the active
  research default; OpenAI or automatic capability selection remain explicit
  alternatives. ElevenLabs
  receives speech/speaker/timing/isolation tasks and Azure receives long-form,
  domain, diarization, role, and enterprise-metadata tasks. A deterministic
  local policy gate minimizes uploads and exact local MAF RDO remains the only
  admission authority.
- Added the R-122 bounded MAF Decoder ISA substrate before further Foundry
  encoder expansion. The portable C++23 Core now exposes hard resource
  preflight, transactional operation budgets, periodic Basis rendering,
  callback-invariant counter noise, stable source filtering, quantized
  Innovation, bounded transient injection, and Q1.15 channel-matrix mixing
  through the stable C ABI. Main-0 whole-stream and callback decoding now route
  Basis render and Truth composition through one exact transactional budget.
  Twelve native tests, a deterministic 20,003-input adversarial MAF smoke
  gate, the complete 195-test Python/native integration suite, and Android
  ARM64/x86-64 compile gates pass. The complete R-118 evidence gate remains
  pending before MAF syntax promotion.
- Added the R-120 independently decodable unified MAF research streams:
  event-driven MFC1 cells, corrected causal SFT1 source-filter state, cached
  integer filter Basis, and EPV1 adaptive/stochastic algebraic excitation.
  The pinned speech fast diagnostic reached the 10,765-byte rate checkpoint
  but failed Opus quality, so no default or release syntax changed.
- Added exact event-ledger reporting, PVQ-default maps, persistent gain state,
  band-local Basis/stochastic/transient/Truth competition, causal channel
  reuse, closed-loop adaptive excitation, corruption tests, and the
  single-item diagnostic driver. The complete R-118 gate remains pending.
- Passed the 194-test Python 3.14 regression suite after R-120 integration;
  four optional external-tool/device tests were skipped on the Windows host.
- Completed the mandatory 19-item R-117 temporal score companding gate.
  The 17,904-byte pinned speech point improved SNR, STOI, ESTOI, and log-mel
  error without syntax changes; the other 18 items retained exact R-113
  fallbacks. The parameter remains an encoder-side candidate, not a default.
- Closed global PVE2 as the next factorization after an equal-size speech
  diagnostic improved log-mel error but substantially regressed SNR, STOI,
  and ESTOI. The next PVE experiment is packet- and band-local RDO.
- Added R-116 mobile portability gates, checked-in CMake presets for Android
  ARM64/x86-64 and iOS device/simulator builds, and CI artifact production
  with stable NDK r29 and Xcode.
- Adopted C++23 as the production language baseline while retaining C++26 as
  a non-blocking forward-compatibility check. Pinned the Windows research
  workstation to stable Python 3.14.6, LLVM/Clang 22.1.8, CMake 4.4.0, and
  Ninja 1.13.2; the repository-local sync client is MinGit
  2.55.0.windows.3. Shipped artifacts remain independent of Python.
- Made MinGW builds self-contained by statically linking the C++ runtime
  through the Core target contract; strict C++23 compilation also exposed and
  removed a transitive-include dependency.
- Passed 10 native tests and the 185-test Python 3.14/native suite. All 16
  heterogeneous R-111 streams remained byte-identical under the C++23 Core
  across 192 seconds and 2,471,068 compressed bytes.
- Added prospective LPS6 bounded signed Rice/fixed-width coefficient-value
  entropy with an exact LPS5 RDO fallback. At the prior complete-byte ceiling,
  speech moved from budget 67 to 68 and improved SNR, STOI, ESTOI, and log-mel
  RMSE simultaneously; complete piano and Mozart saved 110 and 5,432 bytes
  with identical PCM. The 16-class gate selected LPS6 for three classes and
  retained LPS5 for the other 13.
- Migrated accepted LPS6 value packing and decode to the allocation-free
  C++20 Core, added Python/Core byte and PCM parity plus malformed-stream
  tests, and reused immutable transform analysis across adjacent RDO budgets.
- Corrected the R-108 PVQ compiler to use deterministic greedy integer
  direction search and projection-optimal gain. The corrected candidate
  improved speech-envelope metrics but failed the complete-stream universal
  base gate, so no PVQ decoder syntax was promoted.
- Accepted R-112 and moved the exact LAF1 adaptive arithmetic packer into the
  allocation-free C++20 Core. Complete Mozart encoding improved from 385.976
  to 155.866 seconds (2.476x) while retaining the exact 6,526,665-byte stream;
  speech, piano, and all 16 R-111 class streams were also byte-identical.
- Accepted R-110: Python remains the rapidly editable research control plane
  and independent oracle, while scaling transform, PVQ, candidate
  reconstruction, synthesis, and decode work executes in C++20/SIMD or
  optional CUDA. Shipped artifacts have no Python runtime dependency.
- Accepted and prepared the R-111 16-class heterogeneous corpus from lossless
  EBU SQAM and Xiph sources. It adds male/female speech, solo voice, sustained
  tone, noise, resonance, electronic, transient, dense, stereo, and mixed-film
  gates; no codec improvement is claimed by corpus acquisition.
- Measured R-107 on all 16 R-111 classes at nearly complete-byte-matched Opus
  sizes. Resonith led waveform SNR on 12 classes and log-mel error on six, but
  failed the universal gate on sustained tone, noise, speech envelope, and
  several mixed classes. No decoder syntax or released default changed.
- Completed the R-107 native-backed full-reference gate. Speech, Emotional
  piano, and complete Mozart improved over the preceding Resonith evidence and
  passed the admission bounds; Opus still led speech STOI/ESTOI and most
  spectral-envelope diagnostics, so R-107 remains a research fallback.
- Closed R-103 after its active-band coefficient selector failed the speech
  fast gate. The negative machine report is published; no bitstream, decoder,
  or default-encoder behavior changed.
- Closed R-104 after its recursive voiced long-term predictor improved
  log-mel detail but failed SNR, STOI, and ESTOI. No decoder syntax was added.
- Closed R-105 after sparse harmonic Basis transport approached equal size and
  improved log-mel detail but still slightly reduced STOI and ESTOI.

### Research

- Predictive and voiced Basis candidates for speech are the next measured
  encoder experiment. No improvement is claimed yet.

## [0.1.0-alpha.1] - 2026-07-26

### Added

- Portable dependency-free C++20 Golden Core and stable C ABI.
- Python analysis-by-synthesis encoder with the prospective LPS5 transport.
- Native bounded `.resonith` decoder utility.
- Cached Integer Basis Synthesis, multi-Basis lifetimes, phase trajectories,
  transient experiments, integer lifting residuals, native decoder-in-loop
  verification, packet and corruption gates.
- Continuous public-reference evidence and release protocol.

### Measured

- The pinned LibriSpeech and full-length Mozart comparison against official
  Opus is the
  [release evidence for this version](docs/results/PUBLIC_BENCHMARK_2026-07-26.md).
- At nearly identical complete file sizes, the current Resonith candidate
  preserved waveform SNR and spectral convergence better on both references,
  while Opus preserved speech intelligibility, log-mel/log-spectral detail,
  and harmonic-peak coverage better. No broad perceptual-superiority claim is
  made.

### Rejected

- A per-frame transform-coefficient floor increased bytes and degraded all
  declared speech diagnostics. It was removed instead of becoming a permanent
  encoder option.

### Compatibility

- Implementation version: `0.1.0-alpha.1`.
- Normative-draft specification version: `0.0.9`.
- The public `.resonith` extension currently carries prospective LPS5
  research transport. Stable Main-0 bitstream compatibility is not yet frozen.

[Unreleased]: https://github.com/moshkinyevhen/resonith/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/moshkinyevhen/resonith/releases/tag/v0.1.0-alpha.1
