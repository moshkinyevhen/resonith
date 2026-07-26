# Resonith Solution Log

This file is the canonical source of accepted decisions. Newer
the solution references the one it is replacing and marks it **SUPERSEDED**.

## R-001 - Working name of a stand-alone audio codec

- Date: 2026-07-26
- Status: **RESEARCH / OPEN**
- Solution:
  - the leading candidate for the working name of the audio codec is **Resonith**;
  - the name is not finally chosen until a separate decision of the owner and
    trademark clearance;
  - the name of the folder and documents is used as a convenient temporary namespace and
    does not constitute a brand endorsement;
  - Resonith is not `QINTRA Audio` and does not require QINTRA;
  - QINTRA remains an independent video codec;
  - optimized communication between two codecs is described separately
    `SceneLith AV Bridge`.

## R-001A - Architecture name

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - internal architecture of a stand-alone audio codec -
    **MAF: Memory-oriented Acoustic Field**;
  - changing the public name of the codec does not change the MAF and bitstream design.

## R-002 - One acoustic ISA instead of a set of subcodecs

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - Resonith has one state grammar, one timeline, one entropy layer and
    small bounded integer acoustic ISA;
  - speech, music, noise and ambience are not mutually exclusive modes
    temporary frame;
  - coherent, predictive, transient, stochastic, resonant, spatial and
    objective innovation atoms MAY act simultaneously in one
    time-frequency plot;
  - profiles limit the allowed subset of a single syntax, but not
    are nested independent codecs.

## R-003 - Representation selection via decoder-in-the-loop RDO

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - classifier/router only offers top-K candidates;
  - the final choice is made by the exact RDO based on the full bitrate, distortion,
    decoder compute, state memory, latency, resilience and switching stability;
  - the semantic label of an instrument, note or speech is never
    sufficient basis for normative reconstruction;
  - universal Truth Innovation is a mandatory fallback.

## R-004 - Continuous state instead of coding frames

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - the atom parameter is transmitted at birth or actual change;
  - the absence of an event means the continuation of the previous law;
  - transport packets and internal render quanta are allowed, but are not
    unit of acoustic state;
  - phase, envelope and trajectory are set from absolute sample/time origin;- any switching must be phase-/energy-continuous or closed
    objective innovation.

## R-005 — Timbre Basis, excitation and room response are paid once

- Date: 2026-07-26
- Status: **ACCEPTED / NORMATIVE-DRAFT**
- Solution:
  - repeating timbre is stored as immutable `TIMBRE_BASIS`;
  - periodic/coherent atoms refer to basis and transmit phase, pitch,
    amplitude and small coefficient trajectories;
  - excitation MAY be separated from the resonator to make one excitation law
    excited several modes and sources;
  - room/resonator basis MAY be reused by many emitters;
  - all basis payloads, adapters and dictionary references are taken into account in
    full bitrate;
  - hidden external model is not required for standalone decode.

## R-006 — Deterministic stochastic fields

- Date: 2026-07-26
- Status: **ACCEPTED / NORMATIVE-DRAFT**
- Solution:
  - stochastic atom uses counter-based PRNG, absolute sample index,
    seed and bounded integer spectral/resonant shaping;
  - recursive PRNG state should not be mandatory for random access;
  - stochastic reconstruction in Truth Core is deterministic;
  - its discrepancy with the source code is closed by Truth Innovation;
  - Optional Perceptual Detail never becomes reference.

## R-007 – Profiles of a single standard

- Date: 2026-07-26
- Status: **ACCEPTED / NORMATIVE-DRAFT**
- Profiles:
  - `Realtime`: speech/general low delay, packet-loss constraints;
  - `Main`: general mono/stereo/multichannel audio;
  - `Immersive`: emitters, room and spatial rendering;
  - `Perceptual`: discardable learned/generative detail, not reference;
  - `Lossless`: exact PCM reconstruction with the same Core plus exact innovation.

## R-008 - Numerical goals are not results

- Date: 2026-07-26
- Status: **TARGET / HYPOTHESIS**
- Solution:
  - any compression claim is reported separately against Opus, xHE-AAC/USAC,
    EVS/IVAS and lossless anchor where applicable;
  - matched-quality is determined by MUSHRA/ABX with hidden anchors;
  - broad classical target mature generation: 25–45% lower bitrate
    relative to the strongest applicable anchor with equal subjective
    quality;
  - revolutionary level: no less than 35% for broad music/classical corpus with
    with a small software decoder and without systematic phase or timbre
    artifacts;
  - these numbers are hypotheses pending a reproducible experiment.

## R-009 – Repetitive acoustic programs

- Date: 2026-07-26
- Status: **RESEARCH**
- Solution:
  - a repeated motif, accompaniment pattern, or emitter program MAY be a
    content-addressed macro that creates regular Core atoms with time, pitch,
    and gain
    transform;
  - Main-0 does not receive a separate music language, score VM or
    Turing-complete scripting;
  - the mechanism is accepted into Main only with net gain of at least 5% on broad
    music after taking into account dictionary and seek overhead.

## R-010 - First development path

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - development starts with standalone Resonith, not with AV Bridge;
  - the first oracle compares the universal lifting residual with
    `TIMBRE_BASIS + PHASE_TRACK + residual`;
  - then transient and stochastic candidates are added;
  - spatial/room and Perceptual profile do not block the first codec loop;
  - each extension must undergo a separate ablation and kill-gate.

## R-011 - Shared Control Basis

- Date: 2026-07-26
- Status: **NORMATIVE-DRAFT / HYPOTHESIS**
- Solution:
  - a general modulation trajectory MAY be stored once as an immutable
    `CONTROL_BASIS`;
  - several atoms MAY refer to it with bounded scale/offset/time mapping;
  - the mechanism covers general tempo/rubato, vibrato, dynamics, pitch bend,
    emitter trajectory and room change without semantic labels;
  - `CONTROL_BASIS` uses the same fixed-point parameter-law operations and
    adds no DSP opcode;
  - the mechanism remains optional if full-RDO does not pay for the reference metadata.

## R-012 — Status of the three remaining directions

- Date: 2026-07-26
- Status: **RESEARCH / HYPOTHESIS**
- Solution:
  - cached learned Basis synthesis is considered as an optional coding method
    `BASIS_SET`, not per-sample neural renderer; inclusion gate - at least 5%
    broad net bitrate reduction or at least 12% on the pre-declared
    essential class with bounded startup;
  - a motif macro MAY only deploy existing Atoms deterministically; a separate
    musical VM is prohibited; the inclusion gate remains at least 5%
    on broad music after seek/checkpoint overhead;
  - generative detail is allowed only in the `Perceptual` profile, does not change
    Truth state and does not participate in objective/lossless claims;
  - the estimated gains of these directions cannot be added up: they
    overlap and compete in one complete RDO;
  - tables in `08_RESEARCH_DIRECTIONS_AND_CODEC_TARGETS.md` are
    architectural predictions not measured by results.

## R-013 – Comparison contract with the best audio anchors

- Date: 2026-07-26
- Status: **ACCEPTED / TARGET**
- Solution:
  - speech/realtime is compared separately with Opus, EVS and LC3plus;
  - general/music streaming is compared separately with Opus and xHE-AAC/USAC;- immersive is compared separately with IVAS and the applicable MPEG-H/object anchor;
  - lossless is compared with FLAC and applicable modern lossless anchor;
  - frontier neural papers are reported in a separate research table and are not named
    production anchors before independent playback;
  - equal quality is determined by MUSHRA/ABX with the same latency,
    resilience, channel, random-access and complexity constraints;
  - negative and worst-decile results are published along with the average.

## R-014 - Cached Integer Basis Synthesis included in Main-0

- Date: 2026-07-26
- Status: **ACCEPTED / NORMATIVE-DRAFT**
- Owner's decision:
  - cached learned Basis synthesis is implemented from the first version, and not
    deferred as research extension;
  - normative name of the mechanism -
    **CIBS: Cached Integer Basis Synthesis**;
  - `BASIS_SET` MUST support `CIBS_LATENT` along with objective raw/lifting
    fallback;
  - fixed versioned integer synthesis graph runs only when created
    Basis and produces immutable cached `TIMBRE/FILTER/CONTROL_BASIS`;
  - arbitrary graph, floating-point dependency, external mandatory model and
    per-sample neural inference is prohibited;
  - optional adapter and objective basis correction are included in bitstream and full
    bitrate;
  - synthesized Basis MUST have normative hash and bit-exact output;
  - Main profile MUST implement the basic `CIBS-0`; Realtime profile MAY
    limit the creation of new bases startup/checkpoint intervals;
  - R-012 is transferred to **SUPERSEDED** only in terms of CIBS research status;
    motif macros and Generative Detail retain their previous statuses.

## R-015 — CIBS-first implementation order

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - the first periodic oracle immediately compares three paths:
    `LIFTING_ONLY`, `RAW_BASIS + residual`,
    `CIBS_LATENT + correction + residual`;
  - reference integer synthesis kernel is created before the training pipeline;
  - training/export are non-standard, decoder kernel and model package pass
    separate bit-exact tests;
  - the first CIBS model MAY be weak: architecture correctness is separated from
    subsequent quality of education.

## R-016 – MAF-P0 end-to-end prototype

- Date: 2026-07-26
- Status: **IMPLEMENTED / EXPERIMENTAL RESULT**
- Implemented:
  - mono PCM16 WAV I/O;
  - encoder-side period detection and periodic Basis extraction;
  - Q32 phase renderer and Q15 block amplitude law;
  - `RAW_BASIS` and `CIBS_LATENT + correction`;
  - quantized/exact objective residual;
  - self-checking compressed container;
  - independent decoder, CLI and corruption tests.
- First synthetic harmonic benchmark, 10 s / 48 kHz:- raw-Basis lossless: 55,728 bytes versus 960,000 bytes PCM;
  - CIBS lossless: 55,971 bytes, that is, on Basis alone it’s still worse than raw on
    243 bytes;
  - CIBS lossy `basis_q=8`, `residual_q=16`: 11,333 bytes, SNR 66.13 dB,
    maximum absolute error 8;
  - on bank of 128 unseen harmonic bases CIBS exact correction lost raw
    Basis 4.15%, and CIBS q8 correction won 30.02%;
  - experimental model package: 3,654 bytes, reported separately.
- Limitation:
  - this is a synthetic favorite class and comparison with PCM/raw Basis, not with
    Opus/xHE-AAC;
  - zlib is a temporary entropy baseline;
  - the numbers are not a codec claim.

## R-017 — Resonith name is finally approved

- Date: 2026-07-26
- Status: **ACCEPTED**
- Owner's decision:
  - final product name of the stand-alone audio codec -
    **Resonith**;
  - R-001 in terms of the open name status becomes **SUPERSEDED**;
  - architecture retains name
    **MAF—Memory-oriented Acoustic Field**;
  - the recommended name for the public GitHub repository is `resonith`;
  - trademark/FTO clearance remains a separate legal task and is not
    cancels internal name selection.

## R-018 - Linked video codec name changed to SceneLith

- Date: 2026-07-26
- Status: **ACCEPTED**
- Owner's decision:
  - standalone video codec is finally called **SceneLith Video**;
  - the former QINTRA name has been removed from the current branding;
  - Resonith remains a completely independent audio codec;
  - specialized joint optimization is still defined
    separate SceneLith AV Bridge specification.

## R-019 - Public GitHub and secure auto-sync

- Date: 2026-07-26
- Status: **ACCEPTED**
- Solution:
  - the recommended name for a separate public repository is `resonith`;
  - every explicitly created local commit is automatically sent to `origin`
    repo-local hook;
  - hook itself never executes `git add` and does not create a commit;
  - tests, secret/PII scan and verification are required before the first public push
    tracked files;
  - CI runs reference tests on every push and pull request.

## R-020 — Public repository Resonith created

- Date: 2026-07-26
- Status: **IMPLEMENTED**
- Result:
  - public repository:
    `https://github.com/moshkinyevhen/resonith`;
  - default branch: `main`;
  - initial public commit: `68073e5`;
  - CI runs nine reference tests;
  - repo-local `post-commit` auto-push is enabled and subject to verification by this
    subsequent commit.

## R-021 — English is the sole public repository language

- Date: 2026-07-26
- Status: **ACCEPTED / IMPLEMENTED**
- Decision:
  - all public specifications, documentation, code comments, commit messages,
    issue and pull-request templates, and GitHub metadata use English;
  - conversation with the project owner may use another language, but the
    repository is the international canonical record;
  - historical material in another language remains outside the public
    repository or receives a complete English record;
  - the existing public working tree is migrated to English without rewriting
    published Git history.

## R-022 — Native Golden Core and cross-platform runtime

- Date: 2026-07-26
- Status: **ACCEPTED / ENGINEERING DECISION**
- Decision:
  - Resonith uses a restricted, dependency-free C++20 Golden Core behind a
    stable versioned C ABI;
  - Python/PyTorch remain the research encoder, RDO, CIBS training, and corpus
    environment;
  - optional C++/CUDA kernels accelerate Studio/Foundry encoding but are never
    a format dependency;
  - Rust owns untrusted package/network parsing, streaming, scheduling,
    capability negotiation, and player services, and later supplies an
    independent decoder;
  - the mandatory scalar Core and exactly equivalent x86, ARM, WASM, and
    vendor-DSP paths target Windows, Linux, macOS, iOS, Android, browsers,
    embedded systems, and future ASICs;
  - no allocation, I/O, logging, blocking lock, or lazy model loading is
    permitted in the audio render callback;
  - cross-compiler conformance hashes, sanitizers, fuzzing, static analysis,
    reproducible builds, ABI tests, and real-time deadline tests are release
    gates.
- Canonical engineering document:
  `11_IMPLEMENTATION_LANGUAGE.md`.

## R-023 — High-signal commenting and deterministic debug visibility

- Date: 2026-07-26
- Status: **ACCEPTED / ENGINEERING DECISION**
- Decision:
  - source comments are a maintained engineering interface for human and AI
    debugging;
  - public APIs, normative DSP kernels, Atom/Basis transitions, fixed-point
    and phase rules, security boundaries, concurrency, and real-time behavior
    require concise contract comments;
  - complex functions use a few named logical phases when this makes the
    pipeline visibly easier to inspect;
  - comments that merely restate code, line-by-line narration, decorative
    banners, duplicated specifications, and dead commented-out code are
    prohibited;
  - every `TODO`, `FIXME`, approximation, and unexplained constant carries a
    tracked issue or decision identifier and a removal gate;
  - deterministic structured traces expose parse, validate, stage, synthesize,
    render, commit, fallback, and reject phases, but are disabled by default in
    the audio callback;
  - stale comments fail review and must be updated with behavior in the same
    commit.
- Canonical contract:
  section 11 of `11_IMPLEMENTATION_LANGUAGE.md`.

## R-024 — MAF-P1 lifetimes, phase trajectories, transients, and Opus anchor

- Date: 2026-07-26
- Status: **IMPLEMENTED / EXPERIMENTAL RESULT**
- Implemented:
  - immutable content-addressed multi-Basis Bank with explicit half-open
    lifetimes, reuse, and rejection when an Atom outlives its Basis;
  - absolute piecewise-linear Q32 pitch/phase law with canonical signed
    rounding, bounded knot spans, random access, and block-size-independent
    output;
  - bounded non-overlapping transient events using reversible integer Haar
    lifting and exact zero contribution outside declared support;
  - residual-aware transient RDO with `off`, `on`, and `auto` modes;
  - RAW and CIBS MAF-P1 Basis banks with exact PCM reconstruction when
    quantization steps equal one;
  - external official `opusenc/opusdec` runner with complete Ogg byte
    accounting, decoded PCM, tool versions, and executable SHA-256;
  - official Windows opus-tools installer with a pinned archive hash and Linux
    CI integration.
- Measured deterministic three-second synthetic experiment:
  - P0 single-Basis q16: 455.55 kbit/s, 60.96 dB SNR;
  - P1 multi-Basis q16: 349.16 kbit/s, 60.99 dB SNR;
  - reduction against P0 on this declared class: 23.35%;
  - forced transient path was 0.72% larger, and `auto` correctly rejected it;
  - P1 q256: 74.33 kbit/s, 36.93 dB SNR;
  - official libopus 1.3 anchor at requested 48k VBR: actual 86.80 kbit/s,
    27.78 dB SNR.
- Limitations:
  - this is a synthetic, highly structured, waveform-SNR diagnostic;
  - it is not a MUSHRA result or a broad music claim;
  - the official binary uses libopus 1.3, not current libopus 1.6.1;
  - zlib remains the residual entropy placeholder;
  - transient coding has not yet demonstrated a net win.
- Canonical implementation and report:
  - `10_MAF_P0_IMPLEMENTATION.md`;
  - `../experiments/results/maf_p1_opus_2026-07-26.json`.

## R-025 — LiftPack-1, full-stream state-boundary RDO, and real music

- Date: 2026-07-26
- Status: **IMPLEMENTED / EXPERIMENTAL RESULT**
- Decision:
  - replace the MAF-P1 zlib-array Truth residual with `LiftPack-1`, an
    independently bounded reversible residual stream;
  - split the residual into independently decodable blocks and compete
    `IDENTITY`, first-difference, second-difference, and reversible integer
    Haar lifting by exact coded size;
  - use bounded escaped Rice or fixed-width zigzag packing per block;
  - store the already entropy-coded residual without a second zlib layer;
  - treat acoustic feature segmentation only as a candidate generator;
  - make the final boundary decision by complete stream bytes, including
    Basis, Atom, phase, gain, container, and residual cost;
  - retain fixed-lifetime candidates so the compiler can prove that no
    proposed acoustic boundary is profitable.
- Real-music corpus:
  - three pinned Wikimedia Commons PCM sources;
  - CC0 recorded piano, CC BY-SA 4.0 recorded drum pattern, and one
    public-domain Corelli score realization;
  - deterministic PCM16 mono downmix with source and derived PCM hashes;
  - 19.72 seconds total after declared crops.
- Measured q64 results:
  - LiftPack versus the previous zlib residual at identical fixed
    segmentation and reconstruction:
    - Corelli: 27.08% fewer complete-stream bytes;
    - piano: 59.01% fewer;
    - drums: 31.06% fewer;
  - feature-only adaptive segmentation was inconsistent: −0.82%, +1.12%,
    and −5.77% against the one-second fixed baseline;
  - complete-stream boundary RDO improved on the fixed LiftPack baseline by
    2.22%, 2.38%, and 2.04%, respectively;
  - selected candidates were a two-second fixed lifetime for Corelli and
    piano, and a high-penalty adaptive partition for drums.
  - two independent full runs produced identical canonical report SHA-256
    `5996c5591210f041ecd14542bd08453d82ad4f863759e1237a4beccc03981578`.
- Interpretation:
  - LiftPack passes this phase's kill-test on every declared real clip;
  - feature confidence alone does not justify bitstream state;
  - automatic segmentation remains accepted only behind full-stream RDO;
  - the measured Opus anchor still uses libopus 1.3, and waveform SNR is not a
    perceptual listening result.
- Canonical implementation and evidence:
  - `12_LIFTPACK_AND_STATE_RDO.md`;
  - `../reference/maf_p0/residual.py`;
  - `../reference/maf_p0/segmentation.py`;
  - `../experiments/real_music_corpus.json`;
  - `../experiments/results/maf_p2_real_music_2026-07-26.json`.

## R-026 — Allocation-free native LiftPack Golden Core

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED**
- Decision:
  - expose the first frozen decoder primitive through a C99-compatible,
    versionable ABI implemented in dependency-free portable C++20;
  - keep all buffers caller-owned and forbid allocation, I/O, logging, locks,
    exceptions across the ABI, and global mutable state;
  - validate the complete `LiftPack-1` envelope and CRC before exposing sizes
    or reconstructing coefficients;
  - provide an explicit worst-case scratch query in `int64_t` elements;
  - compile the public header from a C99 translation unit;
  - require the embedded native conformance stream to equal the Python Golden
    Encoder byte-for-byte;
  - build and test with GCC, Clang, and MSVC with warnings treated as errors.
- Scope:
  - this phase decodes only the objective residual primitive;
  - the MAF container, CIBS Basis materialization, Atom state, trajectories,
    gain laws, and channel renderer remain later native parity stages.
- Canonical implementation:
  - `../native/include/resonith/liftpack.h`;
  - `../native/src/liftpack.cpp`;
  - `../native/tests/liftpack_test.cpp`;
  - `../native/README.md`.

## R-027 — RSC1 compact deterministic section container

- Date: 2026-07-26
- Status: **IMPLEMENTED / NORMATIVE-DRAFT**
- Decision:
  - do not port the experimental JSON/zlib `MAF0` research container into the
    Golden Core;
  - define `RSC1` as a compact fixed-record Resonith Section Container with a
    32-byte header and sorted 80-byte directory records;
  - keep Main-0 section payloads stored and self-encoded rather than wrapping
    every section in a generic compression layer;
  - require canonical `(type, instance_id)` ordering, unique keys, tightly
    packed payload offsets, explicit profile bounds, a directory CRC-32, and
    both CRC-32 and SHA-256 for every section;
  - expose immutable zero-copy section views through the C ABI;
  - validate structure in one bounded linear pass with no allocation;
  - verify section content explicitly before a payload reaches a normative
    decoder primitive;
  - retain `MAF0` only as an encoder-research artifact until all executable
    sections migrate to `RSC1`.
- Rationale:
  - a general JSON parser and zlib inflater would enlarge the trusted decoder,
    obscure worst-case work and memory, and preserve array metadata that the
    final typed section syntaxes do not need;
  - sorted fixed records eliminate duplicate detection tables and allow a
    deterministic allocation-free parser;
  - independently hashed self-encoded sections support random access and
    bounded corruption domains.

## R-028 — Registry-backed native CIBS materialization

- Date: 2026-07-26
- Status: **IMPLEMENTED / NORMATIVE-DRAFT**
- Decision:
  - port the complete bounded CIBS-0 integer synthesis operator to the native
    Golden Core before freezing a production model package;
  - keep normative synthesis models in a versioned decoder registry rather
    than repeating projection weights in every stream;
  - let a typed Basis payload reference a registered model and carry only its
    latent, optional bounded adapter/correction, lifetime, and expected
    materialized-Basis hash;
  - expose model tables as immutable caller-owned descriptors in the C ABI so
    conformance models and future firmware registries use the same kernel;
  - use two caller-owned `int64` work planes plus bounded adapter scratch;
  - compute the canonical Basis SHA-256 incrementally and commit samples to
    output only after an expected hash matches;
  - preserve the Python rules exactly: signed round-to-nearest with ties away
    from zero, negative one-eighth activation, per-stage int16 saturation,
    periodic refinement boundaries, and channel-major sample order.
- Scope:
  - the current demo model remains explicitly non-normative and serves only as
    the first cross-language conformance vector;
  - model selection and training remain encoder-side research until measured
    corpus evidence justifies freezing Main-0 registry entries.

## R-029 — Prepared absolute phase trajectories

- Date: 2026-07-26
- Status: **IMPLEMENTED / NORMATIVE-DRAFT**
- Decision:
  - represent periodic Atom motion as absolute piecewise-linear unsigned Q32
    phase increments over strictly increasing sample positions;
  - cap every knot span at 32,768 samples and the trajectory bank at one
    million knots;
  - prepare and validate knot phase origins once into caller-owned memory
    outside the real-time callback;
  - render arbitrary slices by binary-searching the prepared trajectory and
    evaluating the absolute polynomial, never by advancing prior callback
    state;
  - use Q16 linear Basis interpolation with explicit floor-division semantics
    for negative values;
  - require identical output for every callback partition and random-access
    slice;
  - keep the scalar kernel allocation-free and make future SIMD paths exactly
    equivalent.
- Rationale:
  - the prepared origin table makes random access logarithmic in knot count
    without storing per-sample phase;
  - absolute evaluation removes callback size, seek history, and scheduling
    from normative output.

## R-030 — Sparse gain events and one-pass Truth composition

- Date: 2026-07-26
- Status: **IMPLEMENTED / NORMATIVE-DRAFT**
- Decision:
  - replace the conceptual requirement for fixed gain blocks with a sparse
    absolute event law: one signed Q17.15 gain remains active until the next
    declared position;
  - permit an encoder to reproduce the current block-gain experiment by
    placing events at block starts, but charge every redundant event in RDO;
  - evaluate arbitrary slices by binary search and event scanning, without
    state inherited from an earlier callback;
  - combine scaled periodic prediction and dequantized objective Innovation in
    one saturating int64 pass;
  - define negative Q15 division by explicit floor semantics, not signed right
    shift.
- Rationale:
  - a static or slowly varying Atom pays no per-frame gain syntax;
  - the same small mechanism handles abrupt amplitude events and long-lived
    constants while preserving exact compatibility with the P1 diagnostic
    when needed.

## R-031 — Minimal typed raw Basis payload

- Date: 2026-07-26
- Status: **IMPLEMENTED / NORMATIVE-DRAFT**
- Decision:
  - define RSC1 section type `BRAW`, schema version 1, as an eight-byte typed
    header followed by channel-major little-endian int16 Basis samples;
  - carry only `u16 channels`, zero `u16 flags`, and
    `u32 samples_per_channel` before sample data;
  - use the RSC1 directory for type, schema, instance ID, lifetime origin,
    extent, CRC, and hash rather than duplicating those fields inside payload;
  - decode into caller-owned aligned host-endian memory instead of exposing an
    unsafe cast into unaligned little-endian bytes;
  - cap total Basis elements at 16,384.
- Rationale:
  - the final decoder needs typed acoustic objects, not generic dtype/shape
    arrays;
  - the eight-byte header is sufficient for exact materialization on
    little-endian, big-endian, desktop, mobile, and embedded targets.

## R-032 — First complete native causal pipeline vector

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED**
- Implemented chain:
  - decode one typed `BRAW` immutable Basis;
  - prepare an absolute Q32 phase law;
  - render periodic prediction;
  - decode quantized objective Innovation from `LiftPack-1`;
  - prepare sparse Q17.15 gain events;
  - compose and saturate final int16 Truth PCM.
- Evidence:
  - Python and C++ reproduce all 40 PCM samples exactly;
  - output PCM SHA-256 is
    `5c065cb48f1d7581ff2c7160b5ff0cb7923ff0f1377b7c3e314b494a64e933fd`;
  - GCC, Clang, MSVC, and the complete Python/Opus workflow pass.
- Remaining boundary:
  - the vector calls typed primitives directly;
  - compact `ATOM`/configuration payload parsing and whole-RSC1 decoder
    orchestration are the next stage.

## R-033 — Typed Main-0 stream state and whole-container decoding

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - define `CONF` schema 1 as one fixed 16-byte stream contract carrying
    sample count, objective-Innovation step, output-channel count, and zero
    flags/reserved fields;
  - define `ATOM` schema 1 as one bounded periodic Atom header followed by
    absolute Q32 phase knots and sparse signed Q17.15 gain events;
  - use the RSC1 record start tick as the Atom lifetime origin and use the
    `BRAW` instance ID as its immutable Basis reference;
  - make the first executable Main-0 subset exactly mono and require one
    `CONF`, one `ATOM`, one `BRAW`, and one `RSL1`, all with instance ID zero;
  - permit unknown non-critical sections but reject every unknown critical
    section in this profile;
  - expose a two-stage allocation-free native API: inspect computes exact
    caller-owned workspace requirements, then decode verifies every required
    payload before rendering or committing PCM;
  - orchestrate the already verified Basis, trajectory, gain, LiftPack, and
    Truth-composition kernels rather than introduce another DSP path.
- Rationale:
  - a complete container-to-PCM function is the minimum decoder-in-loop
    boundary needed by encoder RDO, fuzzing, players, mobile bindings, and
    independent implementations;
  - fixed typed state removes the generic array archive from the normative
    format while preserving the causal model and a small embedded decoder;
  - exact workspace discovery keeps the decoder deterministic and free of
    hidden allocation.

## R-034 — Native decoder-in-loop is an encoder acceptance gate

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - build a shared-library form of the exact same Golden Core sources and C
    ABI used by native conformance tests;
  - load that library from Python only by an explicit path or environment
    variable, never by silently substituting another decoder;
  - inspect exact native workspace requirements before allocating binding
    buffers and apply a host-side memory ceiling before allocation;
  - require every new typed-RSC1 encoder candidate to decode successfully in
    the native Core and match the Python reference PCM sample-for-sample before
    it may participate in RDO;
  - reject a candidate on native status failure or cross-decoder mismatch
    rather than assigning it an optimistic proxy cost;
  - exercise this boundary in CI against the shared Core, in addition to
    keeping pure-Python reference tests independently runnable.
- Rationale:
  - encoder RDO must optimize the format that production devices execute, not
    an accidentally more permissive research decoder;
  - one source set for static and shared builds prevents binding-specific DSP
    drift;
  - explicit loading and resource ceilings keep experiment provenance and
    hostile-input behavior auditable.

## R-035 — Licensed typed-stream evidence and blinded listening artifacts

- Date: 2026-07-26
- Status: **IMPLEMENTED FIRST RUN / MEASURED-DIAGNOSTIC**
- Decision:
  - run the executable typed Main-0 encoder only through the R-034 native
    decoder gate on the existing pinned and licensed real-music corpus;
  - report complete RSC1 bytes, measured encode/decode time, waveform quality,
    selected candidate, workspace, hashes, and exact tool provenance;
  - compare with complete Ogg Opus anchors while clearly retaining the current
    warning that bitrate and waveform SNR are not perceptually matched;
  - write source, Resonith, and anchor PCM16 WAV files outside Git so a human
    can listen to exactly the samples measured by the report;
  - create a deterministic blinded trial manifest and opaque file names from
    those WAVs while keeping the answer key separate;
  - begin with bounded one-second crops for the first native typed-stream
    diagnostic, then expand duration only after profiling removes Python
    encoder bottlenecks.
- Rationale:
  - conformance without listening can preserve the wrong sound perfectly;
  - a bounded first run gives rapid, reproducible architectural feedback
    without presenting a tiny corpus or waveform metric as a codec victory;
  - separation of the blinded manifest and key makes informal listening useful
    now and leaves a clean path to a later MUSHRA front end.

## R-036 — State-partitioned typed RSC1 before simultaneous mixing

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - extend the executable profile from one global periodic Atom to a canonical
    sequence of one or more `ATOM` sections whose half-open lifetimes exactly
    partition the configured sample timeline;
  - assign consecutive instance IDs independently to `ATOM` and `BRAW`
    sections and permit any number of Atoms to reference one immutable Basis;
  - carry the absolute Atom birth in the RSC1 start tick and keep every
    trajectory/gain position local to that Atom;
  - require a referenced Basis start tick to be no later than the Atom birth;
  - keep one stream-wide LiftPack Innovation so state selection cannot hide
    residual or entropy overhead;
  - discover maximum per-Atom Basis, phase, gain, and render workspace during
    inspection, then reuse those bounded buffers while decoding the partition;
  - retain the one-Atom stream as the zero-complexity RDO candidate;
  - defer simultaneous overlapping Atoms until state-local partitioning proves
    a complete-byte gain on licensed music.
- Rationale:
  - the first native music result showed that a richer global pitch law loses
    to a constant law on whole mixtures;
  - local states can change timbre and phase without adding a mixer, object
    separator, or unbounded live-state bank;
  - Basis instance reuse tests the central memory hypothesis directly: timbre
    bytes are paid once even when multiple state-local Atoms invoke them.

## R-037 — Native full-byte RDO owns every state boundary

- Date: 2026-07-26
- Status: **MEASURED KILL-GATE FAILED / EXPERIMENTAL**
- Decision:
  - keep the one-Atom typed stream as a mandatory candidate;
  - propose additional fixed-duration and acoustic-change partitions;
  - fit one local Basis, constant phase law, and sparse gain law per state in
    the first partition experiment;
  - content-deduplicate all resulting Basis payloads before costing;
  - compute one stream-wide quantized Innovation from the assembled prediction
    and encode it once with LiftPack;
  - pack, native-decode, and cross-check every complete candidate before
    ranking by total RSC1 bytes at one Innovation step;
  - accept multi-state syntax as a compression mechanism only if it beats the
    one-state candidate on at least two declared pitched/music clips; otherwise
    retain it solely as a representation capability and move to source overlap.
- Rationale:
  - a feature boundary is only a search proposal and may cost more Basis,
    Atom, directory, phase, gain, hash, and residual bytes than it saves;
  - the one-state fallback prevents semantic confidence from forcing syntax;
  - local constant laws test whether state separation itself helps, without
    confounding the result with the already losing global continuous law.

## R-038 — Additive Atom oracle before overlap syntax

- Date: 2026-07-26
- Status: **MEASURED KILL-GATE FAILED / RESEARCH**
- Decision:
  - retain state-partitioned decoding as a bounded representation capability,
    but stop treating sequential replacement of the whole mix as a compression
    mechanism after its one-second and long-form kill-gates both failed;
  - test simultaneous full-lifetime periodic Atoms first in an encoder-side
    matching-pursuit oracle;
  - fit each additional Atom against the remaining objective residual, mix
    Atom predictions in a wide integer accumulator, and keep one final
    LiftPack Innovation;
  - count prospective `BRAW`, `ATOM`, directory, hash, configuration, and
    residual bytes by packing a complete canonical RSC1 envelope;
  - compare one through four Atoms at one Innovation step on the pinned music
    clips;
  - add normative overlap/mixer syntax and native kernels only if at least one
    extra Atom reduces complete bytes on two declared clips.
- Rationale:
  - real mixtures contain concurrent causes; replacing one model for the whole
    mix cannot preserve a continuing source across another source's event;
  - an oracle can falsify additive structure before increasing decoder attack
    surface or hardware complexity;
  - complete envelope accounting prevents a visually convincing source
    decomposition from hiding Basis and Atom overhead.

The licensed one-second run selected one Atom on all three clips. Additional
Atoms changed LiftPack by between +54 and -150 bytes while adding roughly 800
bytes of Basis, Atom, and directory cost each. This rejects simultaneous
full-lifetime arbitrary raw Bases as the next normative mechanism; it does not
reject cheaper analytic or cached Basis families.

## R-039 — Batched analytic oscillator oracle before new Core syntax

- Date: 2026-07-26
- Status: **MEASURED KILL-GATE FAILED / RESEARCH**
- Decision:
  - test a fixed decoder-ROM sinusoidal Basis with no per-stream `BRAW`;
  - derive a bounded spectral frequency shortlist and estimate phase
    encoder-side, while the prospective renderer remains deterministic integer
    Basis lookup, absolute Q32 phase, sparse Q17.15 gain, and wide mixing;
  - batch all oscillator records into one prospective bank section so
    directory overhead is paid once rather than once per Atom;
  - compare zero through a bounded number of oscillator Atoms with one final
    LiftPack Innovation and complete RSC1 envelope accounting;
  - compare the winning analytic envelope with the measured raw-Basis oracle;
  - add a normative oscillator bank only if it beats the best raw-Basis
    envelope on at least two declared licensed clips.
- Rationale:
  - R-038 showed that the residual saving of concurrent causes is smaller than
    the metadata of an arbitrary 256-sample Basis;
  - a shared analytic Basis turns the same hypothesis into a much cheaper
    decoder operation and batched syntax removes repeated 80-byte directory
    records;
  - this isolates whether the failure was caused by metadata granularity or by
    an absence of useful stable tonal structure.

The licensed one-second run selected zero oscillators for Corelli and drums.
Piano selected one oscillator but reduced the complete stream by only four
bytes. The gate therefore failed one of three. The zero-Atom envelope beat the
best raw-Basis envelope on all three clips, which triggered R-040 instead of a
new oscillator opcode.

## R-040 — Zero-Atom Truth stream is a mandatory Main-0 candidate

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - permit a canonical Main-0 stream containing `CONF` and `RSL1` with no
    `ATOM` or `BRAW` sections;
  - define the absent prediction as mathematical zero, so output is the
    saturated dequantized Innovation;
  - require `ATOM` and `BRAW` to be either both absent or both present and
    cross-valid;
  - report zero Basis, phase, gain, render, Atom, and Basis-bank workspace for
    the residual-only stream;
  - make residual-only a mandatory full-byte RDO candidate for every Main-0
    encoder invocation;
  - retain all existing state and raw-Basis paths only when they beat this
    simpler complete stream.
- Rationale:
  - the preliminary R-039 licensed run showed that a mandatory periodic
    predictor can increase total bytes on heterogeneous music;
  - optional modeling preserves the universal Truth fallback and makes a
    failed semantic or acoustic hypothesis cost zero decoder complexity;
  - this is both a compression improvement and a simplification of resource
    requirements.

## R-041 — Full-byte LiftPack block-size RDO

- Date: 2026-07-26
- Status: **IMPLEMENTED / NATIVE-GATED / MEASURED**
- Decision:
  - permit the encoder to evaluate a bounded set of existing LiftPack-1 block
    sizes for every complete Main-0 candidate;
  - pack and native-decode every surviving stream exactly as before;
  - select by complete RSC1 bytes, including the changed block-header count;
  - keep the decoder syntax and arithmetic unchanged because block size is
    already an explicit bounded LiftPack-1 field;
  - retain a single integer block-size argument as a deterministic restricted
    encoder configuration.
- Rationale:
  - one-second residual-only diagnostics show that tonal clips prefer very
    large blocks while the drum clip prefers a smaller 2,048-sample block;
  - no universal fixed choice is best, and encoder-only RDO improves
    compression without increasing decoder ISA, state, or attack surface.

## R-042 — Bounded integer LPC oracle before LiftPack-2 syntax

- Date: 2026-07-26
- Status: **MEASURED 3/3 PASSED / PROMOTED BY R-043**
- Decision:
  - test block-local finite-order linear prediction as an additional exact
    Truth transform before assigning a new LiftPack transform ID;
  - derive predictor coefficients encoder-side, quantize them to a fixed
    signed integer precision, and transmit the first samples plus exact
    prediction residual;
  - cap order, coefficient magnitude, coefficient-sum magnitude, block size,
    intermediate arithmetic, and decoded sample magnitude;
  - compete zero, fixed first/second difference, Haar, and LPC by actual block
    payload bytes including predictor coefficients;
  - wrap the prospective residual in a complete research RSC1 envelope and
    verify exact inverse reconstruction;
  - add native syntax only if LPC reduces complete bytes on at least two
    licensed clips beyond R-041 block-size RDO.
- Rationale:
  - R-041 diagnostics show second difference winning almost every tonal block,
    which is direct evidence that a slightly richer local predictor may reduce
    the dominant `RSL1` payload;
  - LPC is bounded sequential integer DSP with small metadata, not a neural or
    semantic decoder dependency;
  - an oracle prevents a familiar lossless-audio technique from entering the
    Core merely because it is conventional.

## R-043 — LiftPack-2 exact LPC block syntax

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-COMPILER VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - define critical section `RSL2` with payload magic `RSL2`, retaining the
    bounded LiftPack stream and block headers;
  - retain transform IDs 0 through 3 unchanged and assign transform ID 4 to
    block-local integer LPC;
  - place `u8 order`, `u8 precision`, then `order` little-endian signed int16
    coefficients between the block header and entropy payload;
  - freeze Main-0 LPC precision at Q12, order at 1 through 16, and absolute
    coefficient sum at no more than \(8\cdot2^{12}\);
  - copy the first `order` entropy-decoded values as seed samples, then predict
    from already reconstructed samples with nearest, ties-away signed Q12
    rounding and add the exact residual;
  - accept exactly one of `RSL1` or `RSL2` in a Main-0 stream;
  - keep scratch asymptotics and allocation ownership unchanged;
  - make both residual versions compete in native-decoder-gated complete-byte
    RDO.
- Rationale:
  - the licensed R-042 gate reduced complete block-size-optimized streams by
    6.18% to 9.05% and won all three declared clips;
  - orders 4, 8, and 12 were selected while order 16 was never selected,
    validating a small bounded decoder kernel;
  - a separate section/version preserves rejection by older Main-0 decoders
    instead of silently extending `RSL1` semantics.

## R-044 — Transient localization through variable residual lifetimes

- Date: 2026-07-26
- Status: **MEASURED 3/3 WON / GATE FAILED / RESEARCH-ONLY**
- Decision:
  - test attack and acoustic-state localization first as exact byte-RDO over
    variable LiftPack-2 block lifetimes, not as a separate transient codec;
  - use the already decoded block length as the only prospective per-boundary
    syntax and retain the same transforms, LPC kernel, entropy paths, checksum,
    and objective Innovation;
  - let encoder-only dynamic programming place boundaries from complete
    encoded block bytes; no onset classifier output enters the bitstream;
  - include every fixed-block RSL2 stream as a fallback and reject variable
    partitioning unless it reduces complete bytes by at least 3% on average
    across the declared licensed corpus and wins on at least two clips;
  - use a research-only magic and section type until the gate passes; assign no
    normative version or opcode in advance.
- Rationale:
  - the earlier separate exact-replacement transient payload lost its gate,
    while LiftPack already expresses short lifting and predictive blocks;
  - variable lifetimes can isolate attacks and state changes without another
    renderer, entropy coder, overlap rule, or sample-domain mixing path;
  - exact byte dynamic programming directly implements the simplicity rule:
    a boundary exists only when its saved residual bytes pay for its header.
- Result:
  - a 512-sample encoder lattice reduced the complete RSL2 anchor by 0.28%,
    2.39%, and 4.58% on Corelli, piano, and drums respectively;
  - the arithmetic mean was 2.42%, below the declared 3% promotion threshold;
  - variable blocks remain a research encoder/bitstream experiment and no new
    normative residual version is assigned.

## R-045 — Reversible stereo lifting before spatial syntax

- Date: 2026-07-26
- Status: **MEASURED 1/3 WON / GATE FAILED / RESEARCH-ONLY**
- Decision:
  - test stereo first as one bounded reversible two-channel lifting choice
    followed by two unchanged independent RSL2 streams;
  - compete independent left/right, reversible mid/side, left/side, and
    right/side representations by complete prospective RSC1 bytes;
  - use the exact integer mapping
    \(side=right-left,\ mid=left+\lfloor side/2\rfloor\) and its exact inverse;
  - quantize source channels before the reversible mapping so every candidate
    reconstructs the same channel-local objective Truth;
  - allow floating-point correlation or source understanding only to shortlist
    encoder candidates; the final decision remains full-byte RDO;
  - assign no Main stereo opcode until the representation reduces complete
    bytes by at least 10% on two declared stereo clips and 12% on average.
- Rationale:
  - stereo correlation is a much larger available redundancy source than the
    failed broad variable-block syntax;
  - the decoder cost is one add and one exact floor divide per sample pair,
    while entropy, prediction, checksums, and bounded memory stay unchanged;
  - starting with a whole-stream lift creates a falsifiable lower bound before
    considering time-varying or frequency-selective stereo state.
- Result:
  - independent channels remained optimal for Corelli and piano;
  - left/side saved 0.42% on drums;
  - the mean was 0.14%, so no whole-stream stereo-lift syntax is promoted.

## R-046 — One-MAC cross-channel gain-delay predictor

- Date: 2026-07-26
- Status: **MEASURED 0/3 WON / GATE FAILED / CLOSED**
- Decision:
  - test one decoded channel as an immutable Truth reference for the other;
  - predict the target with one signed Q12 gain and one bounded integer sample
    delay, then code the exact target residual with unchanged RSL2;
  - compete both channel directions and delays from -32 through +32 samples;
  - use encoder-only residual energy to shortlist at most four gain-delay
    candidates per direction, then select only by complete RSC1 bytes;
  - retain the full R-045 winner as a mandatory fallback;
  - promote only if the cross-channel predictor saves at least 3% on two clips
    and at least 5% on the arithmetic mean.
- Rationale:
  - fixed mid/side assumes equal gain and zero delay, which the licensed stereo
    recordings demonstrably do not satisfy;
  - gain-delay prediction adds only one MAC per target sample, a tiny header,
    and bounded lookahead/state while leaving both RSL2 kernels unchanged;
  - failure closes the simple waveform-domain stereo family before considering
    more expensive time-varying or frequency-selective spatial models.
- Result:
  - the best cross-channel candidates were 3.06%, 6.99%, and 0.02% larger than
    the R-045 fallback on Corelli, piano, and drums respectively;
  - no cross-channel candidate was selected, so global waveform-domain stereo
    lifting and gain-delay prediction are closed for Main.

## R-047 — Two-band reversible spatial lifting

- Date: 2026-07-26
- Status: **MEASURED 0/3 WON / GATE FAILED / CLOSED**
- Decision:
  - apply one exact temporal Haar lifting stage to each quantized channel,
    yielding low and high coefficient bands;
  - choose independent, mid/side, left/side, or right/side lifting separately
    for each band;
  - concatenate like components and transport them through only two unchanged
    RSL2 streams, with one bounded band/mode header;
  - compete all sixteen band-mode pairs by complete bytes and retain the full
    R-045 winner as fallback;
  - promote only if the two-band form saves at least 5% on two clips and 8% on
    the arithmetic mean.
- Rationale:
  - the failed global predictors imply that stereo dependence varies with
    acoustic component rather than one waveform-wide law;
  - one reversible split is the smallest frequency-local experiment and
    reuses the existing integer Haar kernel;
  - two residual streams avoid multiplying section-directory and entropy state
    overhead as the number of bands grows.
- Result:
  - the best subband candidates were 26.20%, 43.73%, and 18.94% larger than
    R-045 on Corelli, piano, and drums respectively;
  - temporal Haar separation destroyed more long-range LPC predictability than
    band-local channel modes recovered;
  - whole-stream, gain-delay, and two-band waveform stereo tools are closed;
    future spatial work must operate on accepted source/Basis representations
    or pass a new oracle without weakening the RSL2 anchor.

## R-048 — Production streaming hardening before new Main opcodes

- Date: 2026-07-26
- Status: **IMPLEMENTED CORE / CROSS-COMPILER VERIFIED / HARDENING CONTINUES**
- Decision:
  - stop assigning compression syntax after the failed R-044 through R-047
    gates and harden the winning `CONF` plus `RSL2` Truth path;
  - add bounded block indexing, checkpoint/random-access contracts, malformed
    stream fuzz targets, and a callback-oriented player API;
  - preserve the allocation-free C ABI, caller-owned memory, deterministic
    output, and exact Python/C++ cross-decoder boundary;
  - require checkpoint tables to be independently integrity-checked and
    optional: their absence affects seek cost, never decodability;
  - resume new normative coding tools only from a declared complete-byte or
    matched-listening gate.
- Rationale:
  - robustness and usable random access are now higher-value than preserving
    failed research modes in Main;
  - a small auditable Core is the project's accepted differentiator and is
    necessary before mobile/player integration or a public standard proposal.
- Result:
  - the allocation-free C ABI now validates and exports every LiftPack block
    byte/sample interval and independently decodes any block;
  - a mutable caller-owned cursor verifies the outer residual envelope once,
    then parses and decodes each block in one linear forward pass;
  - the zero-Atom Main-0 player opens an immutable RSC1 view, supports bounded
    block seek, and emits canonical PCM16 blocks through an application
    callback using only one-block work memory;
  - separate ASan/UBSan/libFuzzer targets now exercise LiftPack internals and
    the complete RSC1-to-PCM pipeline from valid RSL1, RSL2, zero-Atom, and
    periodic-Atom seeds;
  - GCC, Clang, MSVC, the Python/native decoder bridge, and both 5,000-mutation
    smoke targets passed in runs 30202809934, 30203095386, and 30203223428;
  - complete callback playback now also supports model-bearing state
    partitions: it retains only one residual block plus the maximum live
    Basis/trajectory/gain state, splits prediction internally when a residual
    block crosses an Atom boundary, and emits the same canonical PCM as
    whole-stream decode;
  - zero-Atom and model-bearing callback playback, including a deliberately
    cross-boundary state transition, passed every x64/ARM64/Android target,
    the Python/native bridge, and sanitized fuzzing in run 30204031294;
  - no compression opcode or mandatory index syntax was added. A serialized
    seek/checkpoint table remains optional future work and must bind itself to
    the verified residual identity before a decoder may trust its offsets.

## R-049 — Optional residual seek sidecar

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - define `RSI1` as an optional, non-Truth seek sidecar for one exact RSL1 or
    RSL2 payload;
  - bind the table to the complete source byte length and SHA-256, and protect
    the sidecar header plus entries with its own CRC-32 and SHA-256;
  - store canonical byte/sample intervals and the already normative transform,
    entropy, and LPC metadata in fixed 32-byte entries;
  - validate the source checksum, source identity, every source block
    envelope, exact entry equality, and final byte/sample coverage before
    exposing O(1) entry lookup;
  - permit a decoder to reconstruct a selected independently seeded block in
    time proportional to that block only after the verified view is open;
  - make rejection or absence of `RSI1` fall back to linear scan or sequential
    cursor decode without changing reconstructed Truth;
  - cap Main-0 sidecars at 1,000,000 entries and require caller-owned output;
    the Core performs no heap allocation.
- Rationale:
  - the LiftPack checksum authenticates accidental integrity only after
    scanning the residual, while repeated seeks should not rescan all earlier
    block envelopes;
  - binding offsets to the exact residual digest prevents stale indexes from
    silently targeting another stream;
  - keeping the table outside mandatory Truth avoids adding bitrate to
    sequential files and lets containers, HTTP manifests, and players choose
    their own caching policy.
- Result:
  - the C99 ABI reports exact sidecar size, builds RSI1 without allocation,
    verifies both byte arrays and every entry, exposes bounded lookup, and
    decodes a selected block without parsing earlier envelopes;
  - the conformance vector produces a 228-byte table for four source blocks,
    rejects a damaged entry atomically, and reproduces the direct decoder's
    exact selected PCM;
  - Linux x64/ARM64, Windows x64/ARM64, macOS ARM64, Android arm64-v8a, GCC,
    Clang, MSVC, and the native bridge passed in run 30203602697;
  - a dedicated ASan/UBSan/libFuzzer target passed 5,000 bounded canonical-XOR
    and raw-sidecar mutations in run 30203691322.

## R-050 — Typed cached CIBS Basis before reopening source overlap

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - define critical `BCIB` schema 1 as a compact cached-Basis payload carrying
    a registered CIBS model ID, bounded int8 latent, declared mono Basis shape,
    and expected materialized-Basis SHA-256;
  - keep schema 1 latent-only: adapters and objective Basis corrections require
    later schemas and their own complete-byte evidence;
  - place `BCIB` and `BRAW` in one consecutive Basis instance namespace, with
    exactly one representation for each referenced instance ID;
  - resolve models through immutable caller-owned registry descriptors rather
    than global state or stream-carried weights;
  - inspect exact materialization scratch before decode, stage synthesis in
    caller-owned memory, verify the expected Basis hash, and commit no samples
    on failure;
  - add explicit registry-aware inspect, whole-decode, player-open, and
    complete-callback entry points while preserving the existing BRAW ABI;
  - require Python/native sample equality and full cross-platform/fuzz gates
    before a `BCIB` stream may enter encoder RDO;
  - only after this transport is executable, rerun simultaneous-source
    complete-byte experiments with cached Basis reuse and the zero-Atom RSL2
    winner as mandatory fallback.
- Rationale:
  - R-038 rejected extra simultaneous raw Atoms mainly because each paid for
    another transmitted 520-byte Basis and directory record;
  - CIBS already has accepted deterministic integer synthesis and native
    conformance kernels, but without typed RSC1 integration it cannot remove
    that measured overhead in the production decoder path;
  - latent-only schema 1 is the smallest falsifiable bridge from cached learned
    synthesis to source overlap and adds no per-sample neural execution.
- Result:
  - Python and native primitives validate the fixed 48-byte header, canonical
    UTF-8 model ID, latent and shape bounds, unique registry resolution, exact
    staging size, and atomic expected-Basis hash;
  - Main-0 accepts one consecutive mixed `BRAW`/`BCIB` Basis namespace through
    explicit registry-aware inspect, whole-decode, player-open, and callback
    functions while legacy BRAW entry points retain their ABI;
  - CIBS materialization and LiftPack reuse one int64 staging region because
    their lifetimes never overlap; inspection reports their exact maximum
    rather than summing both buffers;
  - every `BCIB` hash is preflighted before the first PCM write or callback,
    and the last materialized Basis remains cached for immediate rendering;
  - whole native decode, callback decode, and the Python reference agree
    sample-for-sample on a generated registry-backed stream;
  - primitive conformance passed run 30204417294; integrated Linux, Windows,
    macOS, Android, x64/ARM64, GCC, Clang, MSVC, native-bridge, and sanitizer
    gates passed run 30204865673;
  - no simultaneous-Atom syntax is promoted by implementation alone. The next
    step remains a held-out complete-byte gate with model-ROM accounting.

## R-051 — Held-out cached-Basis simultaneous-source gate

- Date: 2026-07-26
- Status: **MEASURED FAIL / CLOSED FOR MAIN-0 / RESEARCH**
- Decision:
  - train one fixed mono CIBS-0 development registry model only from source
    intervals after the declared evaluation crops; never fit registry weights
    on an evaluated PCM interval;
  - freeze and hash the model package before ranking overlap candidates;
  - use the existing bounded matching-pursuit period proposals, but project
    every proposed raw Basis into the frozen model, materialize it through the
    normative CIBS-0 rules, then refit gain against that decoded Basis;
  - compete zero through four simultaneous full-lifetime periodic causes with
    one final LiftPack-2 Innovation and complete prospective RSC1 bytes;
  - make the canonical zero-Atom RSL2 stream a mandatory fallback, rather than
    comparing only against a mandatory one-Atom model;
  - batch no unimplemented decoder operation other than wide additive mixing;
    each candidate otherwise uses executable `CONF`, `BCIB`, `ATOM`, and
    `RSL2` payloads;
  - report fixed registry bytes separately and show one-, ten-, hundred-, and
    thousand-stream amortization. Registry weights are neither hidden in the
    stream result nor charged repeatedly as if Opus/VVC fixed tables were
    per-file payload;
  - promote simultaneous periodic mixing only if cached Atoms reduce complete
    stream bytes by at least 3% on two declared clips and by at least 5% on the
    arithmetic mean; otherwise retain the zero-Atom RSL2 decoder unchanged.
- Rationale:
  - R-038 isolated repeated raw Basis transport as the dominant extra-Atom
    cost, and R-050 now makes the smallest cached replacement executable;
  - held-out model training prevents the registry from becoming an uncounted
    copy of the test audio;
  - the zero-Atom fallback and a non-trivial promotion margin enforce the
    project's simplicity rule: a mixer enters Main only for measured net gain.
- Result:
  - the deterministic development model used 120 held-out Basis examples,
    occupied 5,160 serialized registry bytes, and was frozen as SHA-256
    `80db262673b348baa6752aa3268c60a0bae2f675883b0de123f6404756a0f20e`;
  - complete one-second candidates were evaluated on the three pinned music
    crops with zero through four full-lifetime cached periodic Atoms, three
    residual block sizes, and the previously accepted RSL2 fallback;
  - complete-byte RDO selected zero Atoms on every clip. One Atom changed the
    stream from 10,233 to 10,560 bytes on Corelli, 11,953 to 12,227 bytes on
    piano, and 12,743 to 13,115 bytes on drums;
  - the first cached Atom reduced RSL2 by only 57, 78, and 12 bytes
    respectively, while `BCIB`, `ATOM`, and added directory records cost
    384, 352, and 384 bytes. Further Atoms increased total size;
  - the gate therefore produced zero winning clips and 0% selected mean
    reduction. Simultaneous periodic mixing is not promoted to Main-0;
  - `BCIB` remains useful executable infrastructure for future single-cause
    or longer-lived Basis tests, but cached synthesis alone is not evidence
    for an additive mixer opcode.

## R-052 — Independent-channel Main-0 transport

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - extend the residual-only Main-0 subset to one through eight output channels
    without adding a second container, codec dispatch layer, or coupled DSP
    transform;
  - retain one `CONF` record and store exactly one critical `RSL2` instance per
    output channel. Instance IDs are consecutive canonical channel indices;
  - require every channel to share the RSC1 sample rate, frame count,
    Innovation step, LiftPack block size, and block count so callback playback
    can emit aligned interleaved frames with bounded memory;
  - derive the base speaker order from `output_channels`; custom objects and
    arbitrary layouts remain outside Main-0 rather than adding metadata to the
    minimum fallback;
  - keep existing mono APIs and ABI unchanged. Add explicit multichannel
    inspect, interleaved whole-decode, player-open, and callback functions;
  - use one channel-sized int64 Innovation buffer, one maximum LiftPack scratch
    region, and one interleaved output block. Channel residuals decode
    sequentially, so workspace does not scale by the full programme duration;
  - make the encoder choose one common residual block partition by complete
    aggregate bytes across all channels and independently verify the packed
    stream;
  - treat independent channels as the mandatory functional fallback. Coupled
    stereo or spatial coding may replace it only after a separate
    complete-byte or matched-listening gate.
- Rationale:
  - the codec cannot become deployable while the executable Core is mono-only;
  - earlier waveform stereo transforms lost their gates, but that does not
    justify delaying correct stereo transport or embedding another codec;
  - independent channel residuals reuse the winning RSL2 kernel, preserve
    exact isolation and random block boundaries, and add only directory
    records plus interleaving;
  - aligned partitions make the real-time contract simple enough for desktop,
    mobile, embedded, and later hardware decoders.
- Result:
  - the Python encoder performs complete aggregate-byte RDO over common RSL2
    block sizes, independently parses its winning RSC1, and reconstructs
    canonical frame-major PCM;
  - the native Core validates one consecutive residual instance per channel,
    exact frame/partition equality, and bounded output-size arithmetic;
  - whole decode preflights every entropy path before its first PCM write while
    reusing one channel-sized Innovation and one maximum scratch region;
  - player decode uses one channel block plus one interleaved output block and
    calls the application only after all channels reconstruct the same frame
    interval;
  - a generated stereo stream is bit-exact across Python, native whole decode,
    and native callback playback;
  - GCC, Clang, MSVC, Linux ARM64, Windows ARM64, macOS ARM64, Android
    arm64-v8a, the Python/native bridge, and ASan/UBSan/libFuzzer passed in
    run 30205820034;
  - the reference CLI now accepts ordinary one-through-eight-channel PCM16 WAV
    for `encode-main0` and writes validated PCM16 WAV through `decode-main0`.

## R-053 — Pull-oriented realtime player session

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / NORMATIVE-DRAFT**
- Decision:
  - add a mutable caller-owned multichannel session that borrows the immutable
    verified player view and retains one forward LiftPack cursor per channel;
  - expose one `decode_next` operation that reconstructs exactly one aligned
    interleaved PCM block and reports its frame offset and length;
  - perform no allocation, I/O, logging, locking, clock access, or global
    mutation in session initialization or the block decode path;
  - stage cursor advances in local copies and commit session state only after
    every channel reconstructs the same frame interval. A failed block leaves
    the session retryable and reports zero frames;
  - return `NOT_FOUND` after the canonical final block without changing
    session state;
  - leave device APIs outside the Core. WASAPI, AAudio/Oboe, CoreAudio, ALSA,
    WebAudio, and embedded DMA adapters consume the same pull contract;
  - require pull output to equal whole decode and push-callback output before
    the API is considered executable.
- Rationale:
  - a push function that decodes the entire stream is useful for tests and
    conversion but cannot directly feed a device callback or bounded ring
    buffer;
  - a small cursor session is the minimum cross-platform player primitive and
    avoids placing platform threads, locks, or device ownership in normative
    codec code;
  - transactional cursor commit prevents one damaged channel from advancing
    ahead of the others and preserves deterministic retry/concealment policy
    for the application.
- Result:
  - the native session retains eight fixed cursor slots, commits only the
    declared active channels, and returns one canonical interleaved block per
    call;
  - an undersized output rejection reports zero frames and leaves
    `next_block` unchanged; canonical exhaustion returns `NOT_FOUND`;
  - native pull output equals both whole decode and push-callback output on the
    generated stereo conformance stream;
  - GCC, Clang, MSVC, Linux ARM64, Windows ARM64, macOS ARM64, Android
    arm64-v8a, Python/native parity, and sanitized fuzzing passed in run
    30206070812.

## R-054 — Block-local packet-loss containment simulator

- Date: 2026-07-26
- Status: **MEASURED / CONTAINMENT PASSED / RESEARCH**
- Decision:
  - expose independently verified RSL2 block indexing and single-block decode
    in the Python reference, mirroring the native LiftPack API;
  - simulate loss at aligned multichannel block granularity without modifying
    the intact source stream or pretending that container checksums survived a
    truncated file;
  - conceal only the missing frame interval with a deterministic bounded fade
    from the last available interleaved frame toward zero;
  - decode every received block from its own transmitted seeds and require the
    first block after a loss run to match undamaged Truth exactly;
  - report affected frames, lost payload bytes, loss-run boundaries, objective
    concealment error, and exact equality outside lost intervals;
  - keep concealment an application policy, not normative Truth and not a
    reference state. Future packet framing/FEC must receive its own transport
    syntax and overhead gate.
- Rationale:
  - block-local LPC seeds should bound damage naturally, but the property must
    be executed and measured rather than inferred;
  - mutating an RSC1 section and ignoring its SHA-256 would test a non-conformant
    file decoder, not realistic packet loss;
  - a simple poor-but-bounded concealment baseline makes recovery behavior
    falsifiable before spending decoder complexity on neural PLC or FEC.
- Result:
  - single-block Python decode equals full RSL2 decode for first, middle, and
    final blocks, matching the already executable native independent-block
    property;
  - on all three one-second stereo music crops, losing one internal aligned
    block changed only its declared frames and the first following block
    returned to exact Truth;
  - unrestricted complete-byte RDO selected 4,096-frame blocks. One loss then
    affected 92.88 ms at 44.1 kHz, which is contained but too long for the
    Realtime target;
  - a 512-frame ceiling reduced the affected interval to 11.61 ms. Complete
    stream size increased by 12.95% on Corelli, 13.37% on piano, and 9.59% on
    drums relative to the 4,096-frame winners;
  - simple fade concealment remained audibly risky on exposed piano and is
    retained only as a bounded baseline. No concealment output becomes Truth
    or future prediction state.

## R-055 — Realtime residual block ceiling candidate

- Date: 2026-07-26
- Status: **TARGET / NORMATIVE-DRAFT**
- Decision:
  - cap the initial Realtime profile at 512 PCM frames per independently seeded
    residual block for 44.1 and 48 kHz material;
  - permit Main/Studio encoders to choose longer blocks by complete-byte RDO;
  - count the measured rate penalty explicitly rather than presenting the
    latency profile as a compression win;
  - require a later native timing gate to show worst-case one-block decode
    below the device callback budget on reference mobile hardware;
  - revisit the ceiling only with packet-loss listening evidence, not with
    bitrate alone.
- Rationale:
  - 512 frames bounds coded loss and algorithmic block recovery to 11.61 ms at
    44.1 kHz and 10.67 ms at 48 kHz;
  - the measured 9.59% to 13.37% byte cost is material but acceptable as an
    explicit Realtime trade-off, while a 4,096-frame loss is too long for a
    credible low-latency profile.

## R-056 — Stereo rate frontier and blinded Opus comparison

- Date: 2026-07-26
- Status: **MEASURED / BASELINE LOSES / LISTENING PENDING / RESEARCH**
- Decision:
  - extend the existing official `opusenc`/`opusdec` anchor from mono to
    canonical one-through-eight-channel PCM while retaining complete Ogg byte
    accounting and executable hashes;
  - evaluate the pinned one-second stereo music crops over explicit Resonith
    Innovation steps and Opus VBR rates;
  - report every rate/quality point, then select nearest-complete-byte pairs
    without interpolating or hiding container overhead;
  - label waveform SNR and maximum error as diagnostics, not perceptual
    equivalence, because Opus is optimized for listening rather than exact
    waveform reconstruction;
  - create deterministic opaque WAV trials containing source, rate-matched
    Resonith, and Opus. No listening win may be claimed before scores exist;
  - preserve source channel order and sample count exactly throughout the
    benchmark.
- Rationale:
  - the project now has executable stereo transport, so mono/downmix anchors
    are no longer sufficient;
  - same-rate objective tables reveal gross failures, while blinded listening
    is required to judge timbre, attacks, stereo stability, and noise;
  - separating measured files from subjective conclusions prevents a
    residual-only prototype from appearing competitive merely because scalar
    quantization retains high sample-domain SNR.
- Result:
  - official `opusenc`/`opusdec` stereo operation is reproducible with complete
    Ogg bytes, normalized stream hashes, exact frame shape, and executable
    provenance;
  - at the closest complete bytes to the Opus 96 kbit/s request, Resonith used
    14,984 versus 15,356 bytes on Corelli, 14,881 versus 15,552 bytes on piano,
    and 12,430 versus 12,599 bytes on drums;
  - the corresponding waveform SNR diagnostics were 13.08 versus 21.20 dB,
    24.78 versus 26.46 dB, and 17.49 versus 21.80 dB respectively. The
    residual-only Resonith baseline lost this objective sanity check on all
    three clips;
  - deterministic three-way blind trials containing source, rate-matched
    Resonith, and Opus were generated locally. No perceptual conclusion is
    recorded until listening scores exist;
  - uniform waveform-domain Innovation quantization is therefore identified as
    the next compression bottleneck. More Atom syntax will not hide it.

## R-057 — Lapped perceptual Innovation oracle

- Date: 2026-07-26
- Status: **OBJECTIVE SANITY GATE PASSED / LISTENING AND INTEGER GATES PENDING / RESEARCH**
- Decision:
  - add an encoder-side lapped transform Innovation candidate for lossy Main,
    while retaining RSL2 as the exact Lossless and mandatory RDO fallback;
  - use 50% overlap, perfect-reconstruction analysis/synthesis windows,
    frequency-band quantization, transmitted bounded scale laws, and sparse
    signed coefficient entropy;
  - keep the first oracle floating-point and explicitly non-normative to test
    the representation quickly. No opcode is assigned until a winning design
    is converted to fixed integer arithmetic and independently decoded;
  - count every frame header, band scale, coefficient payload, alignment byte,
    and outer container byte;
  - bound the future decoder to one lapped block, one overlap tail, fixed
    tables, and no neural inference;
  - add short-window/transient switching only after the long-window candidate
    wins a complete-byte gate;
  - compare against both RSL2 and official Opus at nearest complete bytes. A
    waveform metric is only a sanity gate; blinded listening remains required
    for promotion.
- Rationale:
  - R-056 shows that causal state machinery cannot compensate for inefficient
    coding of the remaining mixed Innovation;
  - modern perceptual codecs spend error by frequency and masking, whereas the
    current scalar waveform step spends the same error budget everywhere;
  - a single regular lapped kernel plus scale/entropy metadata is compatible
    with SIMD, GPU, DSP, mobile, and later ASIC implementation without turning
    the decoder into a collection of subcodecs.
- Result:
  - the prospective `LPF1` oracle uses a 50%-overlapped sine-window MDCT,
    low-frequency-dense band scales, sparse signed coefficients, complete
    `RSC1` byte accounting, and an independent decoder;
  - at nearest complete bytes to the official Opus 96 kbit/s anchor, LPF1 used
    15,959 versus 15,356 bytes on Corelli, 16,768 versus 15,552 bytes on piano,
    and 12,714 versus 12,599 bytes on drums;
  - the corresponding waveform SNR diagnostics were 22.38 versus 21.20 dB,
    38.32 versus 26.46 dB, and 25.90 versus 21.80 dB. All three objective
    sanity comparisons passed, with a mean diagnostic delta of +5.71 dB;
  - this is not a listening win or a syntax promotion. The current oracle uses
    floating-point transform arithmetic and zlib as a non-normative entropy
    proxy. Fixed-integer parity, bounded native entropy, resource timing, and
    blinded listening remain mandatory gates.

## R-058 — One bounded sparse entropy path for lapped Innovation

- Date: 2026-07-26
- Status: **OBJECTIVE GATE PASSED / NATIVE AND LISTENING GATES PENDING / RESEARCH**
- Decision:
  - replace the R-057 zlib proxy with a prospective independently decoded
    sparse syntax before changing transform arithmetic or adding perceptual
    tools;
  - transmit band-scale temporal deltas and signed nonzero values through the
    existing bounded escaped-Rice/fixed-width entropy primitive;
  - transmit sorted coefficient-position gaps through one bounded unsigned
    escaped-Rice path, resetting the position predictor at every transform
    frame;
  - declare one fixed coefficient count per transform frame so no bitmap,
    per-coefficient tag, adaptive probability table, or general-purpose
    decompressor is required;
  - select all entropy parameters by exact complete-byte RDO, validate zero
    padding and complete bit consumption, and bound every count before
    allocation;
  - retain the R-057 zlib stream only as a research comparator. A bounded
    result must preserve the nearest-byte Opus sanity gate before the design
    advances to fixed-integer conversion.
- Rationale:
  - the sparse transform already identifies the data structure directly:
    slowly changing band scales, sorted positions, and small signed values;
  - coding those three fields explicitly tests whether the measured result
    belongs to the representation rather than to a heavyweight external
    compressor;
  - reusing one Rice/packed primitive keeps the future hardware surface small
    and preserves the project's single-entropy-layer rule.
- Result:
  - the bounded syntax independently reconstructs the exact scale, position,
    and signed-value grids without zlib or another general decompressor;
  - combined with the fixed kernel from R-059, it passes the same nearest-byte
    gate on all three clips at 0.950x to 1.068x the complete Opus bytes;
  - the remaining promotion blockers are native cross-decoder parity, measured
    resource bounds, and blinded listening rather than entropy feasibility.

## R-059 — Deterministic fixed-integer lapped kernel

- Date: 2026-07-26
- Status: **PYTHON BIT-EXACT GATE PASSED / NATIVE AND LISTENING GATES PENDING / RESEARCH**
- Decision:
  - freeze one prospective sine window in Q15 and one cosine transform table in
    Q14 for each permitted power-of-two half-window;
  - execute analysis, inverse transform, windowing, and overlap accumulation
    with bounded int64 intermediates and one explicitly defined symmetric
    rounding rule;
  - identify the exact fixed table bytes by SHA-256 in every experiment and
    eventually generate compiled ROM from reviewed repository data rather than
    evaluating trigonometric functions in a production decoder;
  - keep floating transform arithmetic only as the R-057 comparator and require
    the fixed path to pass independent decode, overflow-bound, deterministic
    hash, complete-byte, and real-music gates;
  - do not require mathematically lossless MDCT inversion in the lossy path.
    Exact PCM remains the separate RSL2 fallback; the lapped decoder must be
    deterministic and bounded.
- Rationale:
  - integer table MACs map directly to scalar C++, SIMD, GPU integer dot
    products, DSPs, and fixed-function silicon;
  - accumulating both overlapping contributions before the final rounding
    avoids platform-dependent floating state and prevents repeated rounding
    from becoming an audible block-boundary mechanism;
  - validating the transform before adding masking or window switching keeps
    the next compression conclusion attributable to one change.
- Result:
  - Q15 window and Q14 cosine table MACs reconstruct deterministically through
    the independent Python decoder and retain the R-057 compression result;
  - at nearest complete bytes to Opus 96 kbit/s, the fixed bounded path used
    16,395 versus 15,356 bytes on Corelli, 14,780 versus 15,552 bytes on piano,
    and 12,842 versus 12,599 bytes on drums;
  - waveform SNR diagnostic deltas were +4.63, +11.87, and +6.23 dB, for a
    +7.58 dB mean. This is still not a perceptual quality claim;
  - compiled ROM, native independent decode, overflow proofs, timing, and
    listening remain required before any syntax promotion.

## R-060 — Allocation-explicit native LPF1 decoder gate

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / RESEARCH**
- Decision:
  - add a standalone C99 ABI for prospective fixed/bounded LPF1 inspection and
    whole-stream decode without merging the research syntax into Main-0;
  - require caller-owned scale, position, coefficient, overlap, and output
    storage with exact element counts returned before decode;
  - validate the complete container, section hashes, entropy envelopes,
    canonical padding, decoded positions, scale range, and conservative int64
    synthesis bounds before the first PCM write;
  - represent every supported power-of-two window through two reviewed
    quarter-wave ROMs sampled at the 1,024-half-window grid. Symmetry and
    integer stride recover the exact Q14 cosine and Q15 window values;
  - gate the implementation with a Python-authored native conformance vector,
    Python/native PCM equality, workspace atomicity, cross-compiler warnings
    as errors, ARM64/Android builds, and sanitizers.
- Rationale:
  - a Python-only integer result does not prove portable decoder feasibility;
  - caller-owned memory and preflighted arithmetic make real device costs
    visible before syntax promotion;
  - quarter-wave symmetry reduces compiled table storage from a full transform
    matrix to 4,098 int32 ROM values while preserving exact coefficients.
- Result:
  - the Python-authored conformance vector and dynamic native bridge reproduce
    fixed/bounded LPF1 PCM sample-for-sample;
  - inspection reports exact caller-owned scale, position, coefficient,
    overlap, and output capacities; undersized workspace is rejected before
    PCM changes;
  - GCC, Clang, MSVC, Linux ARM64, Windows ARM64, macOS ARM64, Android
    arm64-v8a, reference tests, native bridge, and sanitized builds pass in
    GitHub Actions run 30207598669;
  - real-device thermal/deadline measurements and blinded listening remain
    promotion blockers.

## R-061 — Implicit acoustic-state boundaries through sparse density

- Date: 2026-07-26
- Status: **OBJECTIVE GATE PASSED / NATIVE AND LISTENING GATES PENDING / RESEARCH**
- Decision:
  - test variable transform-frame coefficient counts before adding explicit
    acoustic-state records, short-window opcodes, or a transient classifier;
  - treat the existing `coefficients_per_frame` input as an average complete
    budget and select the globally strongest quantized coefficients across
    channel, time, and frequency;
  - transmit one bounded count trajectory plus the existing scale, position,
    and signed-value fields. Position prediction still resets per transform
    frame, including zero-count frames;
  - let sustained regions and attacks emerge as low/high sparse-density runs.
    A classifier may later accelerate search but must not define decoder truth;
  - compare fixed and variable density at nearest complete Opus bytes on the
    same corpus. No native syntax is added unless variable density improves the
    declared complete-byte quality gate.
- Rationale:
  - an explicit boundary is redundant when the coded resource field already
    says where acoustic complexity changes;
  - global allocation removes the artificial rule that silence, sustain, and
    attack receive the same coefficient count;
  - one count law is simpler than a separate segmentation model and can later
    drive window switching only where listening proves it necessary.
- Result:
  - a bounded `LSE2` research payload reconstructs temporal scale deltas,
    coefficient-count deltas, reset position gaps, and signed values exactly,
    including zero-count transform frames;
  - closest fixed/adaptive complete-byte pairs improved waveform SNR by
    +0.56 dB with 76 fewer adaptive bytes on Corelli, +0.79 dB with 28 more
    bytes on piano, and +1.34 dB with 64 more bytes on drums;
  - around the Opus-size point, adaptive drums used 12,514 versus 12,623 fixed
    bytes while improving the diagnostic by +0.93 dB;
  - observed per-frame counts ranged from 0 to 98 on Corelli, 48 to 96 on
    piano, and 5 to 125 on drums at the original selected average budgets.
    This is evidence that one resource law locates changing acoustic
    complexity without a separate classifier;
  - native LSE2 parity and blinded listening remain mandatory before the count
    law can enter prospective syntax.

## R-062 — Native LSE2 count-law extension

- Date: 2026-07-26
- Status: **IMPLEMENTED / CROSS-PLATFORM VERIFIED / RESEARCH**
- Decision:
  - extend the existing LPF1 native ABI with an optional caller-owned uint16
    transform-frame count array; fixed-density streams report zero count
    elements and remain unchanged;
  - decode bounded temporal count deltas before positions, require their sum to
    equal the declared sparse coefficient total, and reject any frame count
    above the half-window;
  - reuse the exact Q14/Q15 synthesis kernel, scale law, position Rice path,
    value entropy, overlap memory, and arithmetic preflight from R-060;
  - require fixed and variable streams from one Python source to match the
    independent native output exactly on every cross-compiler target.
- Rationale:
  - R-061 earned the count law through a complete-byte gate, so implementing it
    now tests the actual incremental decoder cost;
  - one optional count array and one existing signed entropy field are smaller
    and easier to verify than explicit acoustic-state or transient syntax.
- Result:
  - fixed LSE1 and variable LSE2 streams share one native parser, arithmetic
    preflight, quarter-wave transform, and overlap renderer;
  - Python/native exact PCM parity passes for both density modes, including the
    dynamic 8,192-frame stereo bridge vector;
  - all ten cross-platform jobs pass in GitHub Actions run 30208161776 after
    retaining warnings-as-errors and the existing sanitizer build;
  - explicit state and transient opcodes remain unjustified. Blinded listening
    and real-device timing are still required.

## R-063 — Reproducible native lapped timing gate

- Date: 2026-07-26
- Status: **MEASURED HOST PASS / PHYSICAL DEVICE PENDING / RESEARCH**
- Decision:
  - benchmark the release C++ decoder on the same pinned one-second stereo
    music crops and selected adaptive-density budgets used by the compression
    gate;
  - verify Python/native PCM equality before accepting any timing sample;
  - report complete stream bytes, exact caller-owned workspace, minimum,
    median, and maximum end-to-end decode wall time, and real-time factor;
  - initially include ctypes call and caller-array construction in the timing.
    This is a conservative host integration measurement, not an isolated
    optimized kernel claim;
  - automate the run on a pinned GitHub Linux x64 environment and retain its
    JSON artifact. Android and ARM64 builds establish portability, while
    physical phone thermal/battery testing remains a separate release gate.
- Rationale:
  - operation counts and successful cross-compilation do not prove deadline
    margin;
  - using real selected streams reveals parser, entropy, sparse-density, ROM
    lookup, overlap, interleave, and host binding costs together.
- Result:
  - GitHub Actions run 30208323632 decoded each one-second stereo crop in a
    median 48.91-58.15 ms, or 0.049-0.058 times real time;
  - the measured scope includes the ctypes call, caller-array allocation,
    stream inspection and verification, entropy decode, synthesis, interleave,
    and a NumPy copy rather than timing only an isolated kernel;
  - exact caller-owned workspace was 389,528-399,968 bytes for the selected
    one-second streams;
  - this establishes ample x64 host deadline margin, not mobile energy,
    concurrent-stream capacity, or worst-case hostile-stream performance.
    Physical Android/ARM64 thermal and battery measurements remain open.

## R-064 — Short-window transient oracle before window-switch syntax

- Date: 2026-07-26
- Status: **MEASURED FAIL / MIXED-WINDOW SYNTAX CLOSED / RESEARCH**
- Decision:
  - add deterministic multi-resolution spectral and onset-local pre-echo
    diagnostics that operate on source/reconstruction PCM without changing the
    decoder;
  - compare the accepted 512-sample half-window against an all-short
    128-sample half-window at nearest complete Opus bytes on the pinned corpus;
  - treat waveform SNR, spectral error, and pre-echo as diagnostics with
    different failure modes; none is a listening conclusion;
  - add mixed long/short window syntax only if the all-short oracle materially
    improves attack-local error on transient material while long windows retain
    a clear efficiency advantage elsewhere.
- Rationale:
  - variable density locates attacks but cannot shorten a transform's temporal
    support;
  - an all-short comparison isolates whether window duration is still a real
    artifact source before introducing switching transitions and new state.
- Result:
  - at nearest Opus bytes, the 512 half-window beat the 128 half-window in
    waveform SNR, multi-resolution spectral convergence, and mean onset-local
    pre-echo error on all three clips;
  - mean long/short pre-echo diagnostics were -27.60/-22.70 dB on Corelli,
    -40.23/-36.38 dB on piano, and -25.46/-23.13 dB on drums, where lower is
    better;
  - on drums, the long path also beat Opus in this diagnostic (-25.46 versus
    -19.36 dB) while using 12,514 versus 12,599 complete bytes;
  - no short-window or window-switch state is added. The density law remains
    the only automatic acoustic-complexity mechanism until blinded listening
    supplies contrary evidence.

## R-065 — Sanitized LPF1 hostile-stream gate

- Date: 2026-07-26
- Status: **SANITIZED SMOKE PASS / CONTINUOUS**
- Decision:
  - fuzz the complete native LPF1 inspect/decode boundary with fixed- and
    adaptive-density valid seeds;
  - run libFuzzer with AddressSanitizer and UndefinedBehaviorSanitizer on every
    repository test workflow;
  - cap harness allocations and estimated synthesis work independently of the
    normative parser bounds so mutation throughput cannot be dominated by one
    valid but expensive stream;
  - assert the public write-count contract: success writes exactly the declared
    frame count and every failure reports zero frames.
- Rationale:
  - exact conformance vectors cover known streams but not adversarial section,
    entropy, count, position, or arithmetic combinations;
  - LPF1 is the first prospective public path that combines persistent parser
    state, variable symbol counts, bounded entropy, and integer synthesis.
- Result:
  - GitHub Actions run 30208736366 compiled the new harness with Clang,
    AddressSanitizer, UndefinedBehaviorSanitizer, and libFuzzer;
  - 5,000 bounded mutations completed for LPF1 in addition to the existing
    LiftPack, Main-0, and seek-sidecar targets;
  - the complete ten-job repository workflow passed. This is a smoke gate, not
    a substitute for a continuously growing corpus or long fuzz campaigns.

## R-066 — Reusable immutable encoder analysis

- Date: 2026-07-26
- Status: **MEASURED DEVELOPMENT PASS / RESEARCH**
- Decision:
  - split lapped encoding into immutable transform analysis and exact-byte
    selection/packing stages;
  - allow one analysis to serve many bitrate, density, and entropy candidates;
  - require every reused-analysis candidate to be byte-identical to the
    original one-shot encoder;
  - keep the one-shot API as a convenience wrapper, so CLI and applications do
    not need to manage analysis lifetime.
- Rationale:
  - RDO searches a frontier, not one guessed bitrate. Repeating the same
    O(N-squared) research transform for every budget wastes work without
    improving a decision;
  - immutable analysis makes parallel candidate evaluation safe and is the
    natural boundary for a future C++/CUDA encoder backend.
- Result:
  - all six fixed-integer adaptive-density candidates remained exactly
    byte-identical on all three pinned clips;
  - on one local Windows/Python development pass, the six-point frontier fell
    from 6.49-6.99 seconds to 4.21-4.47 seconds, a 1.54x-1.59x speedup;
  - this single-pass developer timing is directional, not a production encoder
    throughput claim. Native batched analysis and synthesis remain the next
    performance step.

## R-067 — Allocation-explicit native forward analysis

- Date: 2026-07-26
- Status: **EXACT PARITY PASS / PORTABLE**
- Decision:
  - expose the fixed Q15-window/Q14-cosine forward transform through the stable
    C99 ABI without adding encoder policy to the decoder;
  - preflight transform-frame, scale, coefficient, and score counts before any
    output write;
  - emit channel-major band scales, quantized coefficients, and exact unsigned
    squared scores into caller-owned arrays;
  - require exact parity with the Python Golden Encoder on both a frozen small
    vector and a dynamic 8,192-frame stereo integration vector.
- Rationale:
  - R-066 identifies immutable analysis as the correct acceleration boundary;
  - keeping selection and RDO outside the kernel permits CPU, CUDA, and future
    teacher encoders to compete without changing the bitstream or decoder;
  - an allocation-free scalar C ABI supplies a portable correctness anchor
    before SIMD or GPU specialization.
- Result:
  - the frozen Python-authored vector matches native scales, all quantized
    coefficients, and every squared score exactly;
  - the dynamic 8,192-frame stereo decoder-in-loop test matches Python analysis
    exactly and produces a byte-identical adaptive-density stream when selected
    through the native backend;
  - GitHub Actions run 30209156633 passed all ten jobs across GCC, Clang, MSVC,
    Linux ARM64, Windows ARM64, macOS ARM64, and Android arm64-v8a;
  - the CLI exposes native analysis only through an explicit `--native-core`
    path. Python remains the fallback until optimized native throughput is
    measured.

## R-068 — Native analysis timing before specialization

- Date: 2026-07-26
- Status: **MEASURED BASELINE / OPTIMIZATION REQUIRED / RESEARCH**
- Decision:
  - measure the release scalar C++ forward-analysis ABI on the three pinned
    one-second stereo crops;
  - verify exact Python/native arrays before accepting any timing sample;
  - include ctypes, caller-array allocation, transform, quantization, score
    generation, and NumPy reshape in the native timing scope;
  - compare native medians with the existing NumPy/Python fixed oracle, then
    choose SIMD-first or CUDA-first work from evidence rather than assumption.
- Rationale:
  - a portable scalar anchor can be slower than optimized matrix operations
    despite using a compiled language;
  - the correct specialization target depends on measured transform cost and
    the intended consumer/studio encoder split.
- Result:
  - exact array parity passed before every accepted timing set in GitHub
    Actions run 30209344885;
  - scalar native analysis took a median 269.80-270.27 ms per one-second stereo
    crop, or 0.270 times real time;
  - the NumPy fixed oracle took 137.08-145.28 ms, making the scalar native path
    1.86x-1.97x slower despite its compiled implementation;
  - profiling by inspection identifies repeated padding tests, window lookup,
    and window multiplication inside every coefficient/sample MAC. The next
    kernel must hoist those operations once per transform frame, preserve exact
    arrays, and be remeasured before adding explicit SIMD or CUDA code.

## R-069 — Hoist invariant forward-window work

- Date: 2026-07-26
- Status: **EXACT PARITY PASS / 2.19X KERNEL SPEEDUP**
- Decision:
  - materialize one signed Q15 windowed PCM block per channel and transform
    frame on the stack;
  - reuse that block for every coefficient dot product, removing repeated
    padding branches, source indexing, window phase lookup, and window
    multiplication from the inner MAC loop;
  - preserve multiplication order and the Q29 accumulator exactly;
  - require frozen-vector, dynamic Python/native parity, sanitizer, and timing
    gates before accepting the rewrite.
- Rationale:
  - the same input sample and window value were recomputed `half_window` times;
  - hoisting a mathematical invariant is simpler and more portable than adding
    architecture intrinsics before the scalar dataflow is clean.
- Result:
  - every compiler, sanitizer, frozen-vector, and dynamic Python/native parity
    gate passed in GitHub Actions run 30209438911;
  - the automated timing run 30209438939 reduced median native analysis from
    269.80-270.27 ms to 123.17-123.37 ms per one-second stereo crop;
  - the rewrite is 2.19x faster than the preserved scalar baseline, 8.1x real
    time, and 1.16x-1.19x faster than NumPy on the same hosted runner;
  - explicit SIMD/CUDA is not the next bottleneck. Candidate reconstruction
    still uses the slower Python synthesis and should move through the already
    verified native decoder before adding architecture-specific code.

## R-070 — Native candidate reconstruction in encoder RDO

- Date: 2026-07-26
- Status: **EXACT PARITY PASS / 3.60X-5.17X FRONTIER SPEEDUP**
- Decision:
  - allow exact-byte candidate packing to request reconstruction from the
    independent native Golden Decoder;
  - retain Python decode as the portable fallback and require payload and PCM
    parity between both paths;
  - when the CLI is given `--native-core`, use that same explicit library for
    forward analysis and every candidate reconstruction;
  - keep coefficient selection and bounded entropy encoder-side in Python until
    timing identifies either as the next bottleneck.
- Rationale:
  - native decode already measures 17x-20x real time while Python synthesis is
    repeated for every RDO candidate;
  - using the production decoder inside RDO accelerates search and strengthens
    acceptance: distortion is measured from the implementation users run.
- Result:
  - all six candidate payloads and reconstructed PCM arrays matched the Python
    path exactly on all three clips;
  - GitHub Actions run 30209590542 reduced a six-budget one-second stereo
    frontier from 2.21-2.74 seconds to 0.53-0.61 seconds;
  - end-to-end frontier speedup was 3.60x on drums, 4.48x on Corelli, and 5.17x
    on piano;
  - the ordinary CPU path can now evaluate six exact candidates faster than
    real time on the hosted x64 runner. GPU work is reserved for deeper RDO,
    source analysis, and teacher search rather than basic encoding viability.

## R-071 — Independent-context bounded LPF1 packets

- Date: 2026-07-26
- Status: **MEASURED PASS / NATIVE SESSION PENDING / RESEARCH**
- Decision:
  - test an `LPS1` packet sequence whose children are complete independently
    verifiable LPF1/RSC1 streams;
  - give each logical packet exactly one half-window of source context on both
    sides, then discard that context after child reconstruction;
  - align packet duration to the half-window and require contiguous canonical
    logical offsets;
  - authenticate the fixed header and every packet independently with SHA-256,
    while retaining every child's existing section integrity;
  - admit streaming syntax only if approximately one-second packets cost no
    more than 8% complete bytes and lose no more than 0.5 dB waveform SNR on
    every pinned clip.
- Rationale:
  - current LPF1 scale, sparse, and overlap workspaces grow with track length;
  - one-window context makes fixed-density packet interiors exactly equal to
    monolithic reconstruction while avoiding cross-packet decoder state;
  - slight context retransmission is a deliberate simplicity trade for bounded
    memory, random access, packet-loss containment, and parallel decode.
- Result:
  - the Python reference packet encoder/decoder rejects non-canonical coverage,
    child-parameter mismatch, digest corruption, and unaligned packet sizes;
  - fixed-density packet reconstruction is exactly equal to monolithic LPF1 on
    a multi-boundary conformance vector;
  - on three-second adaptive-density music crops, complete-byte overhead was
    6.80%-7.31% and waveform-SNR delta was -0.26 to +2.64 dB, so all three
    clips passed the declared gate;
  - packet-local SHA-256 permits progressive authentication without waiting for
    an end-of-file digest. The native envelope parser, pull session, packet-loss
    behavior, and listening gate remain pending.

## R-072 — Allocation-explicit native `LPS1` pull session

- Date: 2026-07-26
- Status: **EXACT PULL/FUZZ PASS / PORTABLE**
- Decision:
  - preflight the complete packet sequence, authenticating the header and every
    child and reporting maximum child plus logical-output storage;
  - retain only immutable input pointers, the next byte offset, packet index,
    and logical frame offset in the caller-owned session;
  - decode one complete child into caller-owned temporary PCM, trim context,
    then atomically commit the logical interval and session cursor;
  - return end-of-stream explicitly and leave the cursor/output count unchanged
    on every rejected packet.
- Rationale:
  - the Python gate proves the representation, but bounded-memory playback
    requires a native pull API rather than whole-file NumPy allocation;
  - independent children let the implementation reuse the existing verified
    LPF1 parser and decoder instead of adding a second transform path.
- Result:
  - the allocation-free C99 pull session reports exact maximum child and
    logical-output capacities before decode and commits its cursor only after
    a complete authenticated child succeeds;
  - a frozen two-packet C++ vector reconstructs exactly the same PCM as the
    monolithic fixed-density LPF1 stream;
  - the Python/native bridge generated and decoded an adaptive 8,192-frame
    packet stream with exact PCM parity;
  - GitHub Actions run 30210231145 passed GCC, Clang, MSVC, C99-header,
    sanitizer, Python/native, and 5,000-mutation dedicated LPS1 fuzz gates;
  - the session retains only an immutable input view and four scalar cursors.
    Child PCM, transform workspace, and delivered PCM remain caller-owned.

## R-073 — Hosted native `LPS1` resource gate

- Date: 2026-07-26
- Status: **PASS / 16.59X-21.55X REAL TIME / 754-765 KB**
- Decision:
  - benchmark the release native packet pull path on every pinned music crop;
  - include open/preflight time, per-packet pull time, complete sequence time,
    exact Python/native parity, and all caller-owned workspace in the record;
  - require at least 4x real-time decode, less than 2 MiB bounded workspace,
    and exact PCM parity on the hosted x64 runner;
  - preserve packet duration and density policy from R-071 so this measures
    implementation cost rather than a newly tuned representation.
- Rationale:
  - a bounded API is not sufficient evidence that its constants are practical;
  - packet-local authentication and repeated child inspection may create a
    hidden throughput cost that monolithic LPF1 timing does not measure;
  - a reproducible CI artifact is more useful than a development-machine
    timing anecdote, while physical mobile energy remains a later gate.
- Result:
  - GitHub Actions run 30210498613 passed all three pinned three-second music
    crops with exact Python/native PCM equality;
  - median complete-sequence decode speed was 16.59x real time on Corelli,
    18.51x on piano, and 21.55x on drums;
  - complete caller-owned workspace was 762,194, 764,864, and 754,184 bytes,
    respectively, below the declared 2 MiB ceiling;
  - timing includes complete-sequence preflight, repeated packet and child
    validation, allocation of caller arrays, entropy decode, integer
    synthesis, context trim, interleave, and NumPy copy;
  - physical-device power, thermal throttling, and transport I/O remain open.

## R-074 — Packet loss never mutates lapped Truth

- Date: 2026-07-26
- Status: **TRUTH CONTAINMENT PASS / SHORT-PACKET RATE FAIL**
- Decision:
  - expose one independently authenticated LPS1 packet view after envelope
    demultiplexing and decode each available child without earlier children;
  - model loss only after authentication/demultiplexing, as a transport packet
    that did not arrive, rather than weakening corruption rejection;
  - fill a missing logical interval with deterministic bounded integer
    concealment in the player output layer;
  - never feed concealed PCM, inferred coefficients, or generative detail into
    Truth state;
  - require exact PCM equality to uninterrupted decode at every frame outside
    lost packet intervals and at the first later available packet.
- Rationale:
  - independent context is valuable only if the decoder does not propagate a
    missing packet through overlap, entropy, phase, or prediction state;
  - transport loss and authenticated corruption are different conditions:
    corruption must remain a hard error, while absence may be concealed;
  - a simple exact containment gate should precede FEC or learned concealment,
    both of which can improve missing audio without changing codec Truth.
- Result:
  - GitHub Actions run 30210723866 dropped one authenticated 243.81 ms packet
    after demultiplexing on each pinned three-second music crop;
  - every non-lost frame and the first later packet matched uninterrupted Truth
    exactly on all three clips;
  - deterministic integer fade remained output-only and never entered a codec
    reference;
  - complete-byte overhead versus monolithic LPF1 was 23.80%, 27.10%, and
    28.26%, much higher than the 6.80%-7.31% measured near one second;
  - therefore the construction is retained for file, parallel, and coarse
    random-access packets but rejected as the current Realtime packet profile.
    A shorter-packet design must reuse global analysis and pay only for the
    minimum boundary state.

## R-075 — Transform-boundary packets replace repeated source context

- Date: 2026-07-26
- Status: **EXACT PASS / 7.53%-7.75% SHORT-PACKET OVERHEAD**
- Decision:
  - analyze and select the complete lapped coefficient field exactly once;
  - form an independent packet from only the transform frames that overlap its
    logical output interval;
  - duplicate exactly one selected boundary transform frame between adjacent
    half-window-aligned packets, rather than source context on both sides;
  - retain complete independently authenticated LPF1 children and output-only
    loss concealment;
  - promote the construction over LPS1 short packets only if reconstruction is
    exactly equal to the monolithic selected field and 243.81 ms packet
    overhead is no more than 10% on every pinned clip.
- Rationale:
  - an interval of \(m\) half-windows is determined by \(m+1\) overlapping
    transform frames; the neighboring interval shares only the last frame;
  - current source-context packets independently analyze \(m+3\) frames and
    also make a new local allocation decision, which explains much of the
    measured 23.80%-28.26% short-packet cost;
  - moving the boundary into transform space removes redundant work and bytes
    without a new DSP kernel, predictor, or persistent decoder dependency.
- Result:
  - the Python oracle packetizes one globally selected LPF1 field as direct
    authenticated LSE2 children and duplicates one boundary transform frame;
  - every LPS2 packet sequence reconstructed exactly the monolithic selected
    LPF1 PCM, including after loss from the first later packet onward;
  - GitHub Actions run 30211189623 measured 7.53%, 7.75%, and 7.68% complete
    byte overhead for 243.81 ms packets, passing the 10% gate on every clip;
  - the corresponding source-context LPS1 overheads were 23.80%, 27.10%, and
    28.26%, so the same decoder transform with a smaller packet grammar removed
    roughly two thirds of the short-packet tax;
  - LPS2 remains prospective until its direct LSE2 path passes native parity,
    bounded-resource, and hostile-input gates.

## R-076 — Direct bounded LSE2 native packet primitive

- Date: 2026-07-26
- Status: **EXACT NATIVE/FUZZ PASS / PORTABLE**
- Decision:
  - factor the existing native variable-density parser and fixed synthesis
    kernel so they can decode either a complete LPF1/RSC1 stream or one direct
    LSE2 payload under authenticated caller-supplied stream parameters;
  - extend the same allocation-explicit packet session to distinguish LPS1
    source-context and LPS2 transform-boundary records;
  - preserve one workspace contract, one integer synthesis kernel, one status
    model, and transactional session commit for both packet forms;
  - require frozen-vector, dynamic Python/native, C99-header, cross-compiler,
    sanitizer, and dedicated mutated-LPS2 corpus gates.
- Rationale:
  - wrapping every LSE2 packet back into an artificial container would restore
    the header cost R-075 removed and would require hidden temporary storage;
  - duplicating an LSE2 decoder inside the packet module would create two
    security and arithmetic implementations;
  - a parameterized selected-field primitive is the smallest reusable native
    boundary and keeps the player allocation-free.
- Result:
  - the native Core now exposes allocation-explicit direct-LSE2 inspect/decode
    calls and shares the same sparse parser, bound checks, entropy decode, and
    fixed synthesis functions with complete LPF1;
  - the existing transactional packet session accepts both LPS1 and LPS2 and
    selects context trim or direct logical output without persistent transform
    state;
  - a frozen two-packet LPS2 vector equals monolithic adaptive LPF1 PCM, and a
    dynamic 8,192-frame Python-authored sequence matches native output exactly;
  - GitHub Actions run 30211517931 passed GCC, Clang, MSVC, Windows ARM64,
    Linux ARM64, macOS ARM64, Android ARM64, C99-header, sanitizer, and 5,000
    packet-fuzzer mutations seeded with valid LPS1 and LPS2 streams.

## R-077 — Hosted native LPS2 resource gate

- Date: 2026-07-26
- Status: **PASS / 16.74X-21.33X REAL TIME / 191-195 KB**
- Decision:
  - run the same release native timing and complete caller-owned workspace gate
    as R-073 using 243.81 ms LPS2 transform-boundary packets;
  - retain exact Python/native parity and the 2 MiB workspace ceiling;
  - require at least 4x real-time decode on every pinned three-second clip;
  - record this separately from LPS1 so shorter packet duration cannot hide a
    resource regression behind the earlier one-second measurement.
- Rationale:
  - LPS2 removes bytes and nested parsing, but increases packet count from four
    to thirteen in the chosen three-second sequence;
  - only a complete host measurement can show whether repeated authentication,
    entropy setup, and overlap clearing remain practical.
- Result:
  - GitHub Actions run 30211619214 decoded all three pinned three-second clips
    with exact Python/native PCM equality;
  - median speed was 16.74x real time on Corelli, 18.76x on piano, and 21.33x
    on drums, effectively preserving the prior packet/monolithic throughput;
  - complete caller-owned workspace was 190,767, 191,565, and 195,345 bytes;
  - compared with the 754-765 KB one-second LPS1 measurements, direct short
    transform packets reduce the largest live packet storage by approximately
    four times while also lowering complete bytes;
  - physical mobile energy, thermal behavior, and transport I/O remain open.

## R-078 — Single-owner transform boundaries for Realtime

- Date: 2026-07-26
- Status: **ORACLE PASS / 2.98%-3.67% OVERHEAD**
- Decision:
  - test an `LPS3` research packet sequence in which every globally selected
    transform frame belongs to exactly one packet;
  - let packet \(k\) own the transform frames beginning in its logical
    interval, while its final half-window becomes decodable when the first
    transform frame of packet \(k+1\) arrives;
  - let the final packet also own the terminal transform frame;
  - on loss, permit output-only concealment of the missing logical interval
    plus at most the preceding half-window that awaited its boundary frame;
  - require every later packet to reconstruct exactly and require complete
    243.81 ms packet overhead below 4% on every pinned clip before native work.
- Rationale:
  - LPS2 duplicates exactly one boundary transform frame to make every packet
    independently complete; this is the remaining dominant rate cost;
  - normal transform playback already has half-window lookahead. Assigning the
    shared frame once converts duplicate bytes into bounded lookahead without
    predictive Truth state;
  - a lost packet cannot contaminate future coefficient or overlap state:
    only output that explicitly depended on the absent boundary is concealed.
- Result:
  - the LPS3 oracle assigns every selected transform frame once, reconstructs
    uninterrupted PCM exactly equal to monolithic adaptive LPF1, and requires
    one half-window of boundary lookahead;
  - GitHub Actions run 30211915964 measured 2.98%, 3.67%, and 3.10% complete
    byte overhead for 243.81 ms packets, passing the 4% gate on every clip;
  - the first packet after a simulated missing record decoded exactly without
    the lost packet;
  - loss extension is bounded to the preceding 512-frame half-window
    (11.61 ms at 44.1 kHz), whose final output awaited the missing packet's
    first transform frame;
  - native scheduling is deferred until a packet-duration/half-window frontier
    identifies viable Realtime latency and rate points.

## R-079 — Measured Realtime latency/rate frontier

- Date: 2026-07-26
- Status: **NO COMMON LPS3 POINT / ADMINISTRATIVE RATE BLOCKER**
- Decision:
  - sweep fixed half-windows 128, 256, and 512 with approximately 20, 40, and
    80 ms LPS3 packet intervals on every pinned music clip;
  - scale coefficient budget with half-window duration so the first comparison
    keeps approximately equal selected coefficients per second;
  - report complete LPS3 bytes, overhead against same-transform monolithic
    LPF1, estimated packet-plus-half-window algorithmic latency, waveform SNR,
    multi-resolution spectral error, and transient pre-echo diagnostics;
  - use the current 512-half-window monolithic candidate as the declared
    internal quality/rate anchor;
  - identify a Realtime candidate only if estimated latency is at most 50 ms,
    complete bytes are no more than 15% above the anchor, waveform SNR loses no
    more than 1 dB, and mean spectral error loses no more than 1 dB on every
    clip.
- Rationale:
  - packet overhead alone cannot select a Realtime profile because a shorter
    transform changes temporal resolution, scale metadata, and coefficient
    efficiency;
  - a joint frontier exposes whether low latency is paid in packet headers,
    transform inefficiency, or objective quality before any native LPS3 state
    machine is frozen;
  - the metrics remain diagnostics. A passing point still requires listening.
- Result:
  - GitHub Actions run 30212188173 found no configuration passing all four
    limits on all clips;
  - H128 at approximately 40 ms packets reached 43.54 ms estimated latency and
    acceptable rate on some clips, but lost 1.08-6.37 dB waveform SNR and
    1.13-6.95 dB mean spectral convergence;
  - H256 at approximately 40 ms reached 46.44 ms, but still lost 0.60-3.36 dB
    SNR and 0.70-3.79 dB spectral convergence;
  - H512 at approximately 40 ms preserved anchor PCM and all diagnostics
    exactly, but repeated packet metadata raised complete bytes by
    20.63%-25.96%;
  - therefore shorter transforms are not selected merely for latency. R-080
    attacks the isolated administrative rate cost while retaining H512.

## R-080 — Compact transport-framed LPS4 records

- Date: 2026-07-26
- Status: **REALTIME DIAGNOSTIC PASS / 46.44 MS / 10.56%-13.22%**
- Decision:
  - test an `LPS4` Realtime sequence with the same globally selected
    single-owner transform fields and lookahead semantics as LPS3;
  - make packet index, nominal logical duration, channel count, transform
    shape, and child length implicit from the authenticated sequence header,
    transport record boundary, and entropy bit counts;
  - replace each repeated 42-byte LSE2 header, 12-byte logical packet header,
    and 32-byte packet SHA-256 with a 27-byte compact entropy descriptor and a
    4-byte CRC-32;
  - retain the header SHA-256 and require corruption rejection, canonical
    packet coverage, exact monolithic PCM, and exact later-packet recovery;
  - rerun the R-079 frontier unchanged and admit a diagnostic Realtime
    candidate only under the same 50 ms, 15%, 1 dB, and 1 dB limits.
- Rationale:
  - R-079 isolates repeated packet administration, not transform DSP, as the
    rate blocker for the quality-preserving H512 points;
  - authenticated transports such as QUIC/SRTP already frame and
    cryptographically protect datagrams. A codec-level SHA-256 and repeated
    global shape in every short packet are redundant;
  - CRC-32 preserves standalone accidental-corruption detection while the
    transport profile requires external cryptographic authentication.
- Result:
  - the Python LPS4 encoder removes repeated logical and transform-shape
    fields, carries a 27-byte entropy descriptor, derives each record length
    from entropy bit counts, and protects the compact record with CRC-32;
  - compact-to-canonical LSE2 expansion is exact, malformed or corrupted
    records are rejected, and decoded PCM equals the monolithic transform
    anchor exactly;
  - GitHub Actions run 30212427356 found one common passing point: H512 with
    1536-frame, 34.83 ms records;
  - one 512-frame lookahead raises estimated algorithmic latency to 46.44 ms;
    complete-byte overhead was 10.56%, 12.37%, and 13.22% on the three pinned
    clips, with zero SNR or spectral delta from the anchor;
  - native compact parsing and scheduling, authenticated transport integration,
    physical-device measurements, and listening remain prospective. CRC-32 is
    not adversarial authentication.

## R-081 — Separate bounded native LPS4 pull ABI

- Date: 2026-07-26
- Status: **PASS / ACCEPTED**
- Decision:
  - add a separate C99-compatible LPS4 session API instead of changing the
    established LPS1/LPS2 packet-session layout or semantics;
  - make `open` validate the sequence-header SHA-256, every derived record
    length, every CRC-32, inherited transform shape, bounded arithmetic, exact
    record coverage, and maximum caller-owned resources before exposing a
    session;
  - expose the current-record and one-record-lookahead requirements explicitly;
    the eventual pull decoder receives two caller-owned field workspaces and
    one caller-owned overlap/output workspace;
  - keep `open` allocation-free and transactional. A failed pull writes no PCM
    and does not advance the session;
  - retain CRC-32 only as accidental-corruption detection. Transport
    authentication and replay protection remain mandatory for adversarial
    network input.
- Rationale:
  - LPS4 single ownership deliberately moves one transform boundary into the
    following record. Hiding that dependency behind an internal allocation
    would violate the real-time and embedded contract;
  - a separate ABI keeps existing LPS1/LPS2 users source- and behavior-stable
    while making the different LPS4 lookahead lifetime visible to hosts;
  - full preflight converts hostile bit counts and record lengths into bounded
    resource declarations before the audio callback.
- Gate:
  - frozen Python-authored LPS4 vectors, malformed-header and CRC rejection,
    C-header compilation, x64/ARM64 cross-platform builds, and a sanitized
    sequence-parser mutation target;
  - exact cross-decoder PCM and transactional two-record pulls are a subsequent
    gate, not implied by parser acceptance.
- Result:
  - `resonith_lapped_compact_open` exposes bounded maximum current,
    one-record-lookahead, overlap, and output resources without allocation;
  - `resonith_lapped_compact_decode_next` decodes two independent compact
    entropy records into caller-owned workspaces and renders their shared
    transform boundary with the unchanged integer kernel;
  - the frozen Python-authored two-record vector equals monolithic adaptive
    LPF1 PCM exactly; a corrupt lookahead writes no PCM and does not advance the
    session;
  - GitHub Actions run 30213319134 passed GCC, Clang, AppleClang, MSVC,
    Linux/Windows ARM64, Android arm64-v8a, C99 header compilation, and the
    sanitized compact parser/entropy/synthesis mutation gate;
  - long-stream Python/native parity and hosted resource timing are tracked by
    R-082.

## R-082 — Hosted native LPS4 resource and parity gate

- Date: 2026-07-26
- Status: **HOSTED PASS / 12.83x-16.39x / 29.8-38.0 KB**
- Decision:
  - decode 3-second pinned real-music crops through the complete native LPS4
    pull API with H512 and the R-080 approximately 40 ms record point;
  - require exact Python/native PCM, at least 4x real-time hosted x64 decode,
    and at most 2 MiB of complete current, lookahead, overlap, logical-output,
    and host-wrapper workspace on every clip;
  - time sequence preflight, every CRC and entropy revalidation, caller-array
    creation, two-record field decode, integer synthesis, interleave, and NumPy
    copy rather than timing an isolated kernel;
  - record median, minimum, and maximum wall time and complete workspace bytes;
    do not treat hosted x64 wall time as mobile energy or thermal evidence.
- Rationale:
  - R-080 establishes a rate/latency point and R-081 establishes bounded exact
    semantics, but neither measures the complete native host path on real
    music;
  - the two-workspace design is accepted only if its explicit lookahead memory
    remains small and throughput retains substantial realtime margin.
- Result:
  - GitHub Actions run 30213445729 decoded 3-second H512 LPS4 crops as 87
    records of 1536 frames each and passed every declared limit;
  - complete median hosted speed was 12.83x, 14.39x, and 16.39x real-time for
    Corelli, piano, and drums respectively;
  - complete caller-owned workspace was 29,810, 30,218, and 37,976 bytes;
  - every native output equaled the Python LPS4 output bit-for-bit;
  - timing includes full sequence preflight, per-record CRC and entropy
    validation, two field workspaces, overlap synthesis, output arrays,
    interleave, allocation, and NumPy copy;
  - physical-device energy, thermal behavior, authenticated transport I/O, and
    listening remain open.

## R-083 — Stateless authenticated-transport LPS4 record mapping

- Date: 2026-07-26
- Status: **ACCEPTED / IMPLEMENTING**
- Decision:
  - expose an allocation-free native sequence-context parser for the exact
    60-byte LPS4 header plus SHA-256;
  - expose a stateless record-pair decoder keyed by explicit packet index. It
    receives one transport-framed current record and, except for the final
    packet, one following boundary record;
  - derive logical start, logical count, transform ownership, and expected
    record shape solely from the authenticated sequence context and packet
    index; reject trailing bytes, wrong index, missing lookahead, CRC failure,
    and non-canonical compact fields before PCM write;
  - keep cryptographic authentication, replay protection, stream identity, and
    packet ordering in the transport profile. The codec API MUST be called only
    after those checks, and CRC-32 MUST NOT be represented as adversarial
    authentication;
  - make record-pair decode stateless so a lost record cannot contaminate later
    Truth. Concealment remains output-only and is never fed into reference
    fields.
- Rationale:
  - a full-file byte offset is not available when QUIC datagrams or SRTP
    packets arrive independently;
  - embedding keys, ciphers, replay windows, or network ordering inside the
    codec Core would duplicate mature transports and expand the normative
    decoder;
  - explicit current-plus-next ownership makes the one-half-window dependency
    visible while permitting parallel, random-access, and post-loss decode.
- Gate:
  - stateless and sequential native outputs are bit-identical;
  - missing or corrupt lookahead writes no PCM, and a later valid record pair
    still decodes exactly;
  - exact framing, C99 compilation, cross-platform builds, and sanitized
    mutation coverage pass before the mapping is recorded as accepted.
- Result:
  - `resonith_lapped_compact_sequence_open` validates exactly the immutable
    60-byte sequence context without scanning records or allocating memory;
  - `resonith_lapped_compact_decode_record_pair` accepts only exact current
    and immediate-lookahead record frames under an explicit packet index;
  - the frozen vector proves sequential/stateless/monolithic PCM identity,
    rejects missing, corrupt, and trailing-byte lookahead transactionally, and
    decodes a later valid packet after the simulated earlier loss;
  - the compact mutation target executes both sequential and stateless paths
    and compares their PCM for every accepted input;
  - GitHub Actions run 30213950494 passed GCC, Clang, AppleClang, MSVC,
    Linux/Windows/macOS ARM64, Android arm64-v8a, the C99 header test, native
    decoder-in-loop parity, and ASan/UBSan/libFuzzer;
  - cryptographic transport integration, real packet reordering tests,
    physical-device measurements, and blinded listening remain open.

## R-084 — Offline synchronized blinded-listening harness

- Date: 2026-07-26
- Status: **HARNESS PASS / LISTENING PENDING**
- Decision:
  - ship a dependency-free static Web Audio harness inside the repository and
    copy it into every generated listening set;
  - expose the source as a named reference while retaining an independently
    copied hidden reference among opaque randomized candidates;
  - start every decoded candidate on one shared audio clock, preserve playback
    position while switching, and loop the same excerpt so condition changes
    do not introduce timing bias;
  - collect one mandatory 0–100 quality score per candidate, audition time,
    switch count, optional artifact tags, and optional notes;
  - bind exported results to the exact public manifest SHA-256 and keep the
    answer key in a separate file that the browser never requests;
  - validate and aggregate exported results with a separate deterministic
    Python tool. Do not automatically exclude listeners or claim MUSHRA
    significance from an informal or undersized panel.
- Rationale:
  - waveform SNR can prefer a reconstruction that listeners reject for
    pre-echo, timbre drift, unstable stereo image, or structured noise;
  - separate audio elements do not guarantee sample-synchronous switching and
    can bias short comparisons;
  - a static offline harness is auditable, portable, host-independent, and
    cannot silently send listening data to a service.
- Gate:
  - the public manifest contains no candidate identities and the application
    never loads the answer key;
  - candidates begin on a shared Web Audio clock and condition switching does
    not restart playback;
  - incomplete or out-of-range results are rejected;
  - deterministic generation, manifest binding, unblinding, and summary logic
    pass automated tests before real scores are interpreted.
- Result:
  - every generated set now includes a dependency-free static application,
    named reference, opaque hidden reference, WAV hashes, separate answer key,
    local run instructions, and manifest-bound JSON export;
  - all conditions run from one Web Audio clock and switch by gain without
    restarting the excerpt;
  - the result validator rejects wrong manifests, missing scores, audition
    times below the declared floor, invalid annotations, and duplicate listener
    IDs; the unblinder emits descriptive summaries without automatic listener
    exclusion or significance claims;
  - a deterministic 3.5 kHz linear-phase low-pass condition provides an
    explicit impaired anchor but is excluded from codec-rate accounting;
  - the three 3-second real-music trials rate-match the selected Resonith
    candidate to complete Opus bytes within 1.10%, 0.86%, and 0.83%;
  - Resonith's waveform SNR diagnostic is 3.41, 11.22, and 9.47 dB above the
    rate-matched Opus decode, but this is not perceptual evidence;
  - the public manifest SHA-256 is
    `a9573bd53b88796663796e46eb3924f2a08dda0fe29072db193088d6b140ffcb`;
  - 128 reference/security/integration tests, four subtests, and JavaScript
    syntax validation pass. Real listener scores remain pending.

## R-085 — Standalone physical-device callback benchmark

- Date: 2026-07-26
- Status: **HARNESS PASS / PHYSICAL RUN PENDING**
- Decision:
  - add one dependency-free native executable that reads an LPS4 sequence,
    preflights it once, allocates exactly the reported caller workspaces, and
    then measures every transactional pull;
  - keep file I/O, preflight, allocation, and JSON reporting outside the timed
    callback interval;
  - report per-pull minimum, median, p95, p99, maximum, deadline misses,
    realtime speed, complete workspace bytes, and a deterministic PCM hash;
  - repeat complete decode passes and require the same PCM hash and frame count
    on every pass;
  - compile the same source on desktop, ARM64, and Android. Platform-specific
    battery, temperature, frequency, and process-affinity collection belongs
    in an external runner, not the codec Core or timed callback.
- Rationale:
  - hosted Python/ctypes wall time includes allocation and wrapper work but does
    not reveal callback-tail latency;
  - a physical-device gate must execute the production C ABI directly and
    remain usable on an Android shell, embedded Linux board, desktop, or CI
    runner without a language runtime;
  - separating telemetry from the decoder prevents platform APIs and thermal
    policy from entering normative code.
- Gate:
  - the executable builds with warning-as-error on all existing native targets;
  - the frozen LPS4 vector produces the same PCM hash across repeated passes;
  - malformed input exits without timing or partial success;
  - actual mobile energy and sustained thermal results remain pending until run
    on named physical hardware.
- Result:
  - `resonith_lapped_device_bench` executes the public LPS4 pull ABI directly,
    allocates only the preflighted workspaces, excludes I/O and allocation from
    callback timing, and emits machine-readable JSON;
  - a Python-authored deterministic LPS4 vector passes two measured decodes
    with one warmup, stable PCM hash, exact frame count, and valid callback
    observation count; a CRC-corrupt variant exits before timing;
  - GitHub Actions run 30214660610 passed the tool and its integration test on
    GCC, Clang, AppleClang, MSVC, Linux/Windows/macOS ARM64, Android arm64-v8a,
    C99, decoder-in-loop, and sanitizer/fuzzer jobs;
  - actual phone temperature, power, frequency, and sustained callback-tail
    measurements remain pending.

## R-086 — External Android sustained-run telemetry

- Date: 2026-07-26
- Status: **ACCEPTED / IMPLEMENTING**
- Decision:
  - keep ADB, Android properties, thermal zones, CPU frequencies, and battery
    telemetry in a Python experiment runner outside the native Core;
  - bind each report to local and device-side SHA-256 of the exact LPS4 stream
    and benchmark executable;
  - run multiple complete native benchmark sessions, preserving every raw JSON
    result and pre/post telemetry snapshot;
  - summarize worst p99/max callback, total deadline misses, minimum realtime
    speed, and observed thermal delta without inventing unavailable power data;
  - require an explicit device serial when more than one authorized device is
    connected and never select an unauthorized or offline device.
- Rationale:
  - one short callback run can hide warm-up, DVFS, and thermal throttling;
  - vendor thermal-zone names and permissions vary, so missing sensors must be
    represented as missing evidence rather than zero temperature;
  - reproducible stream and executable hashes are necessary before comparing
    devices or builds.
- Gate:
  - telemetry parsing and sustained-summary arithmetic pass deterministic tests;
  - the runner refuses ambiguous device selection and hash mismatch;
  - a named physical phone report is required before any mobile energy or
    thermal claim.

## R-087 — Reproducible physical-host benchmark artifacts

- Date: 2026-07-26
- Status: **PHYSICAL WINDOWS PASS / MOBILE PENDING**
- Decision:
  - publish the warning-clean Windows x64 and Android arm64 callback benchmark
    executables as immutable artifacts of the same GitHub commit;
  - generate named LPS4 device streams from the pinned licensed corpus with
    explicit codec parameters and record their hashes;
  - download the Windows artifact to the current physical host and run sustained
    callback timing on all three streams without requiring a local compiler;
  - record CPU, OS, executable hash, input hashes, raw JSON, and the worst
    callback tails separately from CI-hosted results.
- Rationale:
  - a CI compile proves portability but not the user's actual machine;
  - distributing the exact Android executable also removes local NDK/toolchain
    ambiguity when a phone becomes available;
  - commit-bound binary artifacts and stream hashes make later device
    comparisons reproducible.
- Gate:
  - artifact publication succeeds from warning-as-error jobs;
  - all physical-host runs have zero deadline misses and stable PCM hashes;
  - desktop results MUST NOT be presented as phone energy or thermal evidence.
- Result:
  - GitHub Actions run 30214923144 published commit-bound Windows x64 and
    Android arm64 executables; the Windows executable SHA-256 is
    `7ca930346a5d4480cdb5a7dcae797147106610bedcaac05b5e02a24716cd3f38`;
  - the current physical Windows host is an MSI MS-7885 with a 10-core,
    20-thread Intel Xeon E5-2650 v3 and 34,254,712,832 bytes of RAM;
  - three 3-second LPS4 streams each ran 100 measured passes after ten warmups,
    producing 8,700 callback observations per clip and stable PCM hashes;
  - complete decode speed was 9.81x through 12.33x realtime and caller
    workspace was 29,516 through 37,754 bytes;
  - all 26,100 callback observations met their individual logical deadline;
    the worst p99 was 15.90 ms and the worst single callback was 20.71 ms;
  - these figures establish physical Windows feasibility only. Android
    temperature, sustained timing, power, and energy remain unmeasured.

## R-088 — Header-only receiver workspace contract

- Date: 2026-07-26
- Status: **ACCEPTED / IMPLEMENTING**
- Decision:
  - expose conservative maximum current, lookahead, and logical-output
    requirements derived only from the authenticated LPS4 sequence context;
  - require no packet record, complete stream, heap allocation, or entropy
    inspection to establish the receiver memory ceiling;
  - preserve the existing complete-stream preflight as the tighter
    content-dependent allocation option for files;
  - use the same public requirement structures and arithmetic bounds for both
    paths.
- Rationale:
  - a QUIC datagram or SRTP receiver must allocate before arbitrary records
    arrive and cannot depend on a complete-file scan;
  - leaving allocation to undocumented profile arithmetic would make the C ABI
    easy to misuse and undermine the bounded-decoder claim;
  - a small conservative difference is preferable to per-packet allocation or
    trusting unverified record metadata.
- Gate:
  - header-only maxima cover every exact requirement from complete preflight;
  - frozen stateless decode succeeds using only header-derived workspace;
  - overflow, invalid context, C99, cross-platform, and hostile-input gates pass.
