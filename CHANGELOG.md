# Resonith Changelog

All notable released changes are recorded here. Measured claims link to
reproducible evidence; targets and hypotheses are explicitly labelled.

The format follows Keep a Changelog principles and the project uses Semantic
Versioning for implementation releases. Bitstream syntax has its own declared
version.

## [Unreleased]

### Research

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
