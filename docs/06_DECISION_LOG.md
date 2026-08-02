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
- Status: **PASS / ACCEPTED**
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
- Result:
  - `resonith_lapped_compact_sequence_requirements` derives current,
    lookahead, overlap, and output maxima without packet bytes or allocation;
  - the frozen vector proves every header-derived field covers the tighter
    complete-stream requirement and decodes exact stateless PCM using only the
    conservative workspace;
  - the H512, stereo, 1536-frame Realtime profile needs at most 45,368 bytes of
    caller arrays under the header-only ceiling;
  - GitHub Actions run 30215434818 passed all desktop, ARM64, Android, C99,
    decoder-in-loop, and sanitizer/fuzzer gates.

## R-089 — Exact prefix salvage without lookahead

- Date: 2026-07-26
- Status: **PASS / ACCEPTED**
- Decision:
  - when a non-final current LPS4 record is valid but its immediate lookahead is
    unavailable at playout, permit decoding only the mathematically complete
    prefix of `logical_count - half_window` frames;
  - never expose the unresolved final half-window as Truth and never feed
    concealment into future reconstruction;
  - keep complete record-pair decode as the normal path and make prefix salvage
    an explicit separate API so loss policy cannot silently weaken exactness;
  - retain transactional validation and exact record framing before any prefix
    PCM write.
- Rationale:
  - single-owner lapping makes only the final half-window depend on the next
    record; discarding the whole current interval would inflate one missing
    lookahead into avoidable loss;
  - an explicit exact-prefix primitive lets the external scheduler conceal the
    smallest unresolved region while keeping the Core free of PLC policy.
- Gate:
  - every salvaged prefix is bit-identical to complete record-pair decode;
  - the advertised frame count excludes exactly one half-window;
  - corrupt current input writes no PCM; final packets and undersized outputs
    are rejected;
  - cross-platform, C99, sanitizer, and mutation gates pass.
- Result:
  - `resonith_lapped_compact_decode_record_prefix` validates and entropy-decodes
    one exact non-final record, renders only its complete prefix, and never
    writes the unresolved suffix;
  - the frozen H32 vector returns 32 exact frames from a 64-frame logical
    record and matches complete record-pair PCM sample-for-sample;
  - corrupt input is transactional, output bounds are enforced, and final
    records reject the prefix-only path;
  - at the selected H512/1536-frame Realtime point, 1024 frames or 23.22 ms are
    salvageable and only 512 frames or 11.61 ms require concealment when
    lookahead is absent;
  - run 30215434818 passed every cross-platform and hostile-input gate, with the
    fuzzer comparing the exact prefix against complete decode for each accepted
    non-final record.

## R-090 — Bounded authenticated-record playout scheduler

- Date: 2026-07-26
- Status: **PASS / ACCEPTED**
- Decision:
  - keep reordering, replay rejection, deadlines, and concealment policy outside
    the normative decoder in a bounded host-side state machine;
  - at each logical deadline choose exactly one action: complete record-pair
    decode, exact prefix salvage plus suffix concealment, or full-interval
    concealment;
  - retain a record that served as lookahead so it can become the next current
    record without retransmission or copying;
  - reject unauthenticated, duplicate, late, out-of-range, and beyond-window
    records before they enter the buffer;
  - advance timeline state independently of decoder Truth state. Concealed
    output is never inserted as a record or reference.
- Rationale:
  - network order and deadline policy vary by QUIC/SRTP/application and do not
    belong in the integer acoustic Core;
  - one explicit three-action state machine makes the loss consequences
    auditable and prevents accidental propagation of PLC state;
  - bounded future acceptance prevents adversarial packet indices from turning
    reordering into unbounded memory.
- Gate:
  - in-order, reversed arrival, missing current, missing lookahead, late
    recovery, final packet, replay, authentication, and window bounds pass;
  - a lost middle record preserves the previous exact prefix and allows the
    next valid final record to decode exactly;
  - no scheduler action mutates record payloads or creates decoder reference.
- Result:
  - `LappedTransportScheduler` retains only the bounded future window and
    reuses the next record after it served as lookahead;
  - each deadline produces one explicit `decode_pair`, `decode_prefix`, or
    `conceal` decision with exact and concealed frame counts;
  - reversed arrival, late recovery before the record's own deadline, missing
    middle input, final decode, authentication, replay, late arrival, invalid
    index, and far-future bounds pass;
  - a missing middle record salvages the preceding exact half, conceals only
    unresolved output, and leaves the later final record exactly decodable;
  - 136 reference/security/integration tests pass locally and in GitHub Actions
    run 30215591344.

## R-091 — Temporal support-state entropy oracle

- Date: 2026-07-26
- Status: **FAIL / CLOSED**
- Candidate:
  - replace repeated per-transform sparse positions with one bounded support
    state per channel;
  - encode the first support against the empty state and later supports as
    sorted XOR toggle events;
  - derive each frame's coefficient count from the resulting support while
    keeping coefficient values as independent Truth;
  - reset the support at every independently decodable record boundary.
- Rationale:
  - the selected R-084 frontier already delta-codes scale and coefficient-count
    fields, but repays every active coefficient position in every transform
    frame;
  - measured adjacent-frame support retention is 84% on piano, 73% on Corelli,
    and 56% on drums at the exact three-second R-084 operating points;
  - temporal value deltas are larger than absolute-value codes on all three
    clips, so this experiment deliberately does not add an amplitude
    predictor.
- Complexity ceiling:
  - one `half_window`-bit support field per channel;
  - integer XOR/toggle, sorted bounded Rice positions, and the existing
    scale/value entropy primitives only;
  - no classifier, learned model, cross-record dependency, search state, or
    new synthesis operation.
- Gate:
  - serialized encode/decode round-trips the selected scale and coefficient
    grids exactly and rejects malformed/trailing input;
  - all bit counts, mode metadata, reset cost, padding, and complete stream
    bytes are included;
  - the candidate must reduce complete bytes on every licensed R-084 clip and
    reduce the arithmetic mean by at least 5% at identical reconstruction;
  - failure closes the temporal-support syntax rather than adding more modes.
- Result:
  - serialized `LST1` round-trips the selected scale and coefficient grids
    exactly with strict bounds, reset state, and exact framing;
  - complete-byte reductions were 6.93% on Corelli, 5.63% on piano, and
    negative 0.56% on drums at identical reconstruction;
  - the arithmetic-mean reduction was 4.00%, below the declared 5% threshold,
    and the all-clips condition failed;
  - no temporal-support opcode or normative entropy mode is promoted.

## R-092 — Split magnitude/sign value entropy pre-gate

- Date: 2026-07-26
- Status: **FAIL / CLOSED BEFORE SYNTAX**
- Candidate:
  - encode nonzero coefficient magnitudes with bounded unsigned Rice and carry
    their signs in a separate one-bit plane.
- Gate:
  - require a positive complete-byte result on every R-084 clip before defining
    a serialized syntax.
- Result:
  - full bit accounting predicted reductions of 0.09% on piano, 0.09% on
    Corelli, and negative 2.27% on drums, including the extra sign bit count;
  - the existing signed entropy already approaches the useful bound, so no
    split-sign syntax or decoder branch is added.

## R-093 — Existing-band contextual value entropy

- Date: 2026-07-26
- Status: **FAIL / CLOSED BEFORE SYNTAX**
- Candidate:
  - retain the exact selected coefficients, positions, transform, and 24
    existing scale bands;
  - entropy-code coefficient values in band contexts instead of forcing one
    global value distribution across the spectrum;
  - use the same bounded packed/Rice primitive per populated band and no new
    synthesis operation.
- Complexity ceiling:
  - at most one entropy kind, parameter, and exact bit count per existing band;
  - no probability adaptation, tree, classifier, learned table, or
    cross-record dependency;
  - decoder routes each already decoded position to its deterministic band.
- Gate:
  - exact serialized round-trip, strict framing, and malformed-input rejection;
  - include every per-band descriptor and byte-padding cost;
  - complete bytes decrease on all three R-084 clips and the arithmetic-mean
    reduction is at least 3%;
  - otherwise close the contextual syntax.
- Result:
  - exact bit accounting, including one packed descriptor and one exact bit
    count per existing band, predicted reductions of 1.08% on piano, 0.62% on
    Corelli, and negative 0.33% on drums;
  - the candidate fails both universality and the 3% mean threshold, so no
    band-context syntax is defined.

## R-094 — Entropy-aware coefficient compiler

- Date: 2026-07-26
- Status: **FAIL / CLOSED**
- Candidate:
  - preserve the selected LSE2 bitstream and normative decoder unchanged;
  - replace the equal-cost global energy selector with an encoder-only RDO
    search that estimates each coefficient's value cost, measures the exact
    serialized candidate, and reinvests saved bytes in useful coefficients;
  - retain the existing fixed integer transform, scale grid, reconstruction,
    and complete-byte accounting.
- Rationale:
  - current adaptive density assigns coefficients globally by squared transform
    energy but treats a cheap small value and an expensive large value as if
    their rate were equal;
  - a stronger compiler may improve the quality frontier without spending one
    decoder opcode, state bit, or runtime branch.
- Gate:
  - compare against the exact R-084 energy-selected points at no greater
    complete stream bytes;
  - reconstruction remains deterministic and decodable by the unchanged
    decoder;
  - no clip loses waveform SNR and the arithmetic-mean SNR gain is at least
    0.5 dB before the selector may enter the encoder;
  - waveform evidence remains diagnostic and cannot replace blinded listening.
- Result:
  - the best measured candidates saved only 47 bytes on piano, 61 bytes on
    drums, and 121 bytes on Corelli;
  - their waveform SNR changed by negative 0.0004, negative 0.0009, and
    negative 0.0016 dB respectively, and the savings were too small to admit
    another useful coefficient at the tested operating points;
  - the proxy selector is not promoted; the unchanged energy selector remains
    the simpler choice.

## R-095 — Finite-state entropy ceiling

- Date: 2026-07-26
- Status: **PASS / NATIVE PROMOTION APPROVED**
- Candidate:
  - measure the empirical order-0 entropy of every existing LSE2 field against
    its exact bounded Rice/packed bit count;
  - count a complete, independently decodable model descriptor rather than
    reporting an unattainable fractional-bit limit;
  - define an integer finite-state coder only if the conservative serialized
    ceiling leaves a material universal margin.
- Gate:
  - no synthesis, coefficient, scale, or reconstruction change;
  - model/reset/table/padding costs are included per independent record;
  - a prospective complete-byte reduction of at least 5% on every R-084 clip
    is required before implementing a new normative entropy engine;
  - the eventual decoder, if justified, must use bounded integer state and
    fixed allocation.
- Result:
  - the implemented 32-bit arithmetic state uses deterministic Laplace
    frequencies, bounded count rescaling, no transmitted probability table,
    and an RDO-selected raw escape threshold for coefficient gaps;
  - scales, positions, and values use the adaptive state while the already
    efficient coefficient-count field retains its bounded packed/Rice path;
  - serialized encode/decode is exact, deterministic, independently reset, and
    rejects noncanonical arithmetic representations;
  - complete-byte reductions at identical reconstruction were 6.47% on piano,
    5.34% on drums, and 7.67% on Corelli, with a 6.49% arithmetic mean;
  - the research gate passes and justifies native parity, hostile-input,
    cross-compiler, and timing work before any Main-profile promotion.

## R-096 — Native LAF1 portability and resource gate

- Date: 2026-07-26
- Status: **PASS / PROSPECTIVE LAPPED PROMOTION APPROVED**
- Decision:
  - implement LAF1 behind a stable C99 inspection/decode ABI with no heap,
    global mutable state, locks, callbacks, or floating point;
  - keep the arithmetic model independently reset per entropy field and retain
    LSE2 as the mandatory fallback until transport integration is complete;
  - measure entropy decode separately from inverse transform so its sequential
    cost cannot hide inside DSP timing.
- Gate:
  - exact Python/native field parity;
  - GCC, Clang, MSVC x64 and ARM64, AppleClang ARM64, Linux ARM64, and Android
    NDK builds with warnings as errors;
  - ASan/UBSan/libFuzzer mutation coverage from a valid LAF1 seed;
  - at least 100x realtime median entropy decode on the current physical
    desktop for every three-second R-084 clip, with stable field hashes.
- Result:
  - GitHub Actions run 30216722725 passed the first cross-platform/native
    parity matrix, and run 30216803304 passed the dedicated LAF1 sanitized
    mutation gate;
  - the exact CI-built Windows x64 benchmark executable has SHA-256
    `d35d7514b4e85a41483a35e83c11308a1586f84ba4b45d3a58d834b0eba11ec5`;
  - on the physical MSI MS-7885 / Xeon E5-2650 v3 host, 500 measured passes
    after 50 warmups produced median entropy speeds of 259.49x realtime for
    piano, 356.86x for drums, and 305.56x for Corelli;
  - p99 latency was 13.06 ms, 8.90 ms, and 12.42 ms respectively for complete
    2.995-second fields, with 81.8–119.1 KB caller workspace and stable hashes;
  - native resource and portability gates pass. LAF1 may enter a prospective
    lapped transport, but Main promotion still waits for the shared blinded
    listening gate.

## R-097 — Independent-record adaptive entropy reset gate

- Date: 2026-07-26
- Status: **PASS / 278.6 MS STREAMING POINT**
- Candidate:
  - replace each compact LPS4 LSE2 record with an independently reset compact
    LAF1 field while retaining the same authenticated sequence context,
    single transform ownership, immediate lookahead, CRC, and concealment
    boundary;
  - remove LAF1 magic, version, flags, reserved, frame count, channels, and
    band count from each record because the authenticated envelope and packet
    index determine them exactly.
- Risk:
  - the monolithic LAF1 gain may depend on hundreds of transform frames of
    adaptation; resetting the probability model every 34.8 ms could erase the
    measured compression advantage;
  - carrying adaptive state across packets would violate the project's loss
    containment and random-access rules.
- Gate:
  - measure complete record bytes at 34.8, 69.7, 139.3, 278.6, and 557.3 ms
    nominal packet durations on every R-084 clip;
  - include the compact descriptor, arithmetic finish bits, byte padding, CRC,
    sequence context, final partial record, and per-record model reset;
  - do not define LPS5 syntax unless one latency point saves at least 3% on
    every clip while keeping packet duration at or below 278.6 ms;
  - if the gate fails, investigate a fixed normative prior without introducing
    cross-record state.
- Result:
  - at 34.8 ms, compact LAF1 saved 2.88% on piano, 0.66% on drums, and 2.54%
    on Corelli, so it does not replace low-latency LPS4;
  - at 69.7 ms the reductions were 4.12%, 1.78%, and 3.96%; at 139.3 ms they
    were 4.84%, 2.73%, and 5.03%;
  - the 278.6 ms point passed every condition with complete-transport
    reductions of 5.32% on piano, 3.43% on drums, and 5.95% on Corelli;
  - the 557.3 ms diagnostic reached 5.78%, 4.10%, and 6.74% but is not selected
    because it doubles the loss/seek interval for a modest additional gain;
  - LPS5 is approved as a prospective Streaming/Main transport with a 278.6 ms
    nominal record. LPS4 remains the Realtime fallback, and a fixed-prior
    experiment may target shorter records without cross-record state.

## R-098 — Native LPS5 transport integration gate

- Date: 2026-07-26
- Status: **PASS**
- Decision:
  - reuse the existing allocation-free compact streaming ABI for LPS4 and
    LPS5 instead of adding a parallel player interface;
  - retain the public structure layout and preserve the sequence parser's
    opaque transport discriminator across sequential and stateless calls;
  - decode compact LAF1 directly from inherited sequence shape, without
    materializing a synthetic 43-byte LAF1 header or allocating memory.
- Gate:
  - frozen Python-authored LPS5 vector must reconstruct byte-identical PCM in
    the native pull path and match both Python LPS5 and the LPS4 reconstruction;
  - corrupt CRC, malformed lengths, noncanonical padding, wrong inherited
    shape, and undersized workspaces must fail before PCM delivery;
  - GCC, Clang, MSVC, x64, ARM64, AppleClang, Linux ARM64, and Android builds
    must pass with warnings as errors;
  - Python/native LPS5 decoder-in-loop parity and sanitized compact-stream
    mutation tests must pass before the status changes to PASS.
- Evidence:
  - commit `6268a99` passed the complete cross-platform test matrix, native
    decoder-in-loop parity, and ASan/UBSan/libFuzzer mutation smoke suite:
    <https://github.com/moshkinyevhen/resonith/actions/runs/30219506924>;
  - the same commit passed the release native decode/analysis/RDO benchmark:
    <https://github.com/moshkinyevhen/resonith/actions/runs/30219506918>.

## R-099 — Canonical public names and filename extensions

- Date: 2026-07-26
- Status: **ACCEPTED**
- Decision:
  - the standalone audio codec is **Resonith**, pronounced `re-zo-nit`;
  - `.resonith` is the canonical filename extension for a standalone Resonith
    audio bitstream;
  - `.lps`, `.lps4`, `.lps5`, and `.rsc` remain research transport or
    container revision identifiers and MUST NOT be presented as the stable
    public media extension;
  - the standalone video codec is **SceneLith**, pronounced `seen-lit`, with
    `.scenelith` as its independent visual-bitstream extension;
  - **Orkela**, pronounced `or-ke-la`, is the standalone player;
  - `.orka` is reserved for an Orkela synchronized media package that can bind
    independent Resonith and SceneLith streams through the separate SceneLith
    AV Bridge without merging their Truth reference graphs.

## R-100 — Per-frame coefficient-floor speech kill-test

- Date: 2026-07-26
- Status: **RESEARCH — CLOSED**
- Hypothesis:
  - reserve a minimum number of selected transform coefficients in every
    channel/frame before spending the remaining global adaptive budget;
  - this might preserve low-energy consonants that a waveform-energy ranking
    could otherwise starve.
- Test:
  - LibriSpeech `1272-128104-0000`, 5.855 s, mono 16 kHz PCM16;
  - prospective LPS5, 64 average coefficients, identical transform, entropy,
    packet size, and decoder;
  - floors of 0, 4, 8, 12, 16, 24, and 32 coefficients;
  - complete bytes plus SNR, STOI, ESTOI, and log-spectral distance.
- Result:
  - floor zero produced 17,929 bytes, 19.619 dB SNR, 0.94989 STOI, 0.90297
    ESTOI, and 30.49 dB log-spectral distance;
  - every positive floor increased complete bytes and reduced all four quality
    diagnostics; floor 32 reached 18,315 bytes, 18.498 dB SNR, 0.94300 STOI,
    0.89758 ESTOI, and 31.89 dB log-spectral distance;
  - the candidate is removed rather than added as a permanent encoder option.
    The next speech experiment must change the predictive/Basis model or use
    verified perceptual RDO, not merely constrain the existing coefficient
    allocator.

## R-101 — Continuous public-reference evidence gate

- Date: 2026-07-26
- Status: **ACCEPTED**
- Decision:
  - every material encoder, decoder, entropy, transport, Basis, or allocation
    milestone MUST rerun the pinned public speech and long-form music
    references before a performance claim or release is published;
  - the initial pinned set is LibriSpeech `1272-128104-0000` and the complete
    400.773-second Mozart *Die Zauberflöte* overture performed by the Musopen
    Symphony;
  - every comparison MUST include the exact PCM16 input, complete Resonith
    file bytes, and a current official Opus anchor rate-matched by complete Ogg
    bytes, not nominal bitrate;
  - decoded PCM MUST come from the actual Resonith and Opus decoders used by
    listeners;
  - the machine report MUST include hashes, tool versions, wall time, complete
    bitrate, SNR, SI-SDR, segmental SNR, multi-resolution STFT error,
    log-spectral and log-mel error, magnitude similarity, harmonic-peak
    preservation/frequency/amplitude error, and STOI/ESTOI for speech;
  - reports and the three listening files MUST be published even when a
    candidate loses. A failed idea is removed or explicitly retained as
    research; it is never hidden by changing the corpus or metric after the
    result;
  - controlled blinded listening remains mandatory for perceptual claims
    because objective metrics are diagnostics, not a replacement for human
    hearing.
- Player coupling:
  - every Orkela release that changes decode, playback, or UI behavior MUST
    test both a short and the pinned long `.resonith` file;
  - the release gate includes real playback, responsive background decode,
    malformed-input rejection, timeline and spectrum motion, seeking, file
    association, and high-DPI visual inspection;
  - the public benchmark report MUST identify the exact Orkela build used for
    playback verification.
- Version and publication coupling:
  - every published Resonith or Orkela improvement MUST have a semantic
    version, an English `CHANGELOG.md` entry, and a link to its reproducible
    benchmark or release-evidence report;
  - the changelog entry MUST distinguish measured improvements, regressions,
    fixes, format changes, implementation-only changes, and open perceptual
    questions. Targets and hypotheses MUST NOT appear as achieved gains;
  - local release artifacts and the corresponding GitHub release MUST carry
    the same version, source commit, filenames, and SHA-256 hashes;
  - any change to normative syntax or decoder behavior requires an explicit
    bitstream or ABI compatibility statement and an appropriate version
    increment;
  - a change without versioned before/after evidence remains an experiment and
    MUST NOT be described as a released improvement.

## R-102 — Three-set listening and regression corpus

- Date: 2026-07-26
- Status: **ACCEPTED**
- Decision:
  - the permanent minimum listening corpus consists of LibriSpeech
    `1272-128104-0000`, the eight-second public Emotional piano reference, and
    the complete 400.773-second Mozart *Die Zauberflöte* overture;
  - each set MUST preserve an adjacent numbered triplet: canonical PCM16 WAV,
    native `.resonith`, and current official `.opus`;
  - fast inner-loop experiments MAY use speech plus Emotional piano first, but
    a material milestone, version, performance claim, or release does not pass
    until the complete Mozart reference and all three listening triplets are
    regenerated or verified;
  - the manifest MUST record duration, channel layout, sample rate, complete
    bytes, SHA-256, source, license, codec settings, and actual decoder output;
  - Orkela release QA MUST open the short speech and piano streams and exercise
    responsive background decode and playback on the complete Mozart stream.

## R-103 — Active-band perceptual selection oracle

- Date: 2026-07-27
- Status: **RESEARCH — CLOSED / FAST GATE FAILED**
- Hypothesis:
  - the current global squared-energy ranking can spend nearly every sparse
    coefficient on dominant components while omitting quieter but structurally
    audible bands;
  - reserve at most one already-quantized nonzero coefficient for each active
    lapped band whose peak lies within 40 dB of the frame peak, then spend the
    remaining unchanged global budget by the existing energy ranking;
  - compete the new selection with the unchanged energy selector by complete
    encoded bytes and actual decoder output.
- Constraints:
  - this is encoder-only RDO: it adds no syntax, model, decoder operation,
    memory, or normative floating-point behavior;
  - the emitted coefficient positions and values remain ordinary LPS4/LPS5
    Truth data and decode through the existing native Core;
  - the baseline selector remains the complete fallback, and a losing
    candidate is removed rather than hidden behind a classifier;
  - R-100 remains closed: this experiment may not reintroduce a blind minimum
    coefficient count per frame.
- Fast gate:
  - rerun the pinned LibriSpeech and Emotional piano references against the
    preceding selector and complete-byte-matched Opus;
  - at matched complete bytes, speech STOI and ESTOI must both improve, while
    SNR may not regress by more than 0.5 dB;
  - piano log-mel error may not regress by more than 3% and SNR may not regress
    by more than 0.5 dB.
- Promotion gate:
  - only a fast-gate pass proceeds to the complete Mozart reference, native
    decoder parity, public listening triplets, changelog, and versioned
    release evidence;
  - objective diagnostics remain insufficient for a perceptual-superiority
    claim without controlled blinded listening.
- Result:
  - the speech energy baseline produced 17,744 complete LPF1 bytes, 19.619 dB
    SNR, 0.94989 STOI, 0.90297 ESTOI, and 3.8249 log-mel RMSE;
  - the nearest active-band candidate produced 18,012 bytes, 16.973 dB SNR,
    0.94815 STOI, 0.91217 ESTOI, and 2.3883 log-mel RMSE;
  - it therefore improved ESTOI and log-mel detail but missed the byte target
    by 1.51%, lost 2.65 dB SNR, and reduced STOI, failing the declared speech
    gate;
  - on Emotional piano, the same 68-coefficient point added nine bytes,
    changed SNR by less than 0.001 dB, and improved log-mel RMSE by 0.066%;
  - the overall candidate is not promoted, the complete Mozart run is skipped
    as required, and the production/default energy selector remains
    unchanged. The explicit research backend is retained only to reproduce
    this closed negative result.

## R-104 — Bounded voiced long-term predictor oracle

- Date: 2026-07-27
- Status: **RESEARCH — CLOSED / SPEECH FAST GATE FAILED**
- Hypothesis:
  - voiced speech repeatedly pays transform coefficients for energy that is
    causally predictable from an earlier pitch period;
  - transmit one bounded pitch lag and Q7 gain per fixed acoustic interval,
    transform-code only the prediction Innovation, and reconstruct through one
    integer multiply-accumulate per sample;
  - include the complete parameter envelope, checksum, residual stream, and
    actual inverse-predictor output in RDO.
- Constraints:
  - lag is bounded to the declared speech pitch range, gain is nonnegative and
    strictly below unity, and every arithmetic operation has an explicit
    signed rounding and saturation rule;
  - low-correlation, clipped, initial, or invalid intervals use gain zero and
    become the unchanged transform fallback;
  - the first oracle is mono and research-only; no Main syntax is assigned
    before an independent parser/decoder, corruption tests, and the
    complete-byte gate pass;
  - encoder pitch analysis may use floating point, but the prospective decoder
    uses only transmitted integers.
- Fast gate:
  - compare the pinned LibriSpeech excerpt against the preceding energy
    selector and current public Opus anchor;
  - match complete candidate bytes within 0.5% of the preceding Resonith
    stream, including pitch metadata and checksum;
  - both STOI and ESTOI must improve, SNR may not regress by more than 0.5 dB,
    and log-mel RMSE may not regress by more than 5%.
- Promotion gate:
  - a speech pass proceeds to Emotional piano as the false-positive guard,
    then to the complete Mozart/native-decoder/publication gate;
  - any failure closes the candidate without adding decoder syntax.
- Result:
  - the selected 1,024-sample state used 62 coefficients per transform frame,
    marked 51.1% of intervals voiced, and produced 17,757 complete bytes
    against the 17,744-byte energy baseline, a 0.073% difference;
  - log-mel RMSE improved from 3.8249 to 2.9411, but SNR fell from 19.619 to
    17.321 dB, STOI from 0.94989 to 0.92744, and ESTOI from 0.90297 to
    0.87187;
  - every rate-near block lifetime showed the same failure pattern: quieter
    spectral detail improved while recursive reconstruction error damaged
    waveform accuracy and intelligibility;
  - the candidate is closed before the music and Mozart gates, no VPR1 syntax
    enters Main, and the ordinary transform remains the decoder fallback;
  - the next voiced experiment must use a nonrecursive excitation/harmonic
    Basis with absolute phase or a genuinely closed-loop analysis-by-synthesis
    design. Copying lossy reconstructed history is not sufficient.

## R-105 — Nonrecursive harmonic excitation Basis oracle

- Date: 2026-07-27
- Status: **RESEARCH — CLOSED / SPEECH FAST GATE FAILED**
- Hypothesis:
  - replace recursive sample-history prediction with a short immutable
    harmonic Basis rendered from an absolute local phase;
  - one pitch increment plus a small bank of signed sine/cosine amplitudes
    describes the coherent part of each voiced interval, while the unchanged
    lapped path codes only Innovation;
  - because the renderer never references degraded past PCM, reconstruction
    error cannot circulate around a pitch recurrence.
- Constraints:
  - the prospective decoder uses one frozen Q15 sine ROM, a 32-bit phase
    accumulator, bounded int16 harmonic coefficients, signed integer rounding,
    and saturation;
  - harmonic count, state size, coefficient magnitude, interval count, payload
    size, and residual configuration are preflighted;
  - intervals whose exact fixed renderer would overflow the PCM residual use
    a zero-harmonic fallback;
  - every candidate includes the complete Basis parameter envelope, checksum,
    residual stream, independent parser, and actual synthesis output.
- Fast gate:
  - RDO competes two, four, and six harmonics and 64, 128, and 256 ms-class
    lifetimes against the unchanged 17,744-byte speech transform anchor;
  - complete bytes must match within 0.5%, STOI and ESTOI must both improve,
    SNR may not regress by more than 0.5 dB, and log-mel RMSE may not regress by
    more than 5%;
  - failure adds no Main syntax and directs the next experiment toward
    excitation–resonator factorization or learned cached Basis analysis.
- Result:
  - the initial fixed-width envelope nearly passed but spent 309 bytes on 23
    blocks although only nine were active;
  - sparse active-block transport plus exact signed 12-bit sine/cosine pairs
    reduced the selected Basis envelope to 114 bytes and retained the same
    64-coefficient transform budget;
  - the final two-harmonic, 4,096-sample candidate produced 17,825 bytes,
    0.456% above the 17,744-byte baseline, with 39.1% active blocks;
  - SNR changed from 19.619 to 19.534 dB and log-mel RMSE improved from 3.8249
    to 3.7157, but STOI fell from 0.94989 to 0.94855 and ESTOI from 0.90297 to
    0.90257;
  - shorter lifetimes improved log-mel detail further but caused larger
    intelligibility losses; more harmonics did not reverse the tradeoff;
  - the strict gate therefore fails, no HBR1 syntax enters Main, and the next
    oracle must test continuous pitch, phase, and amplitude trajectories
    across voiced regions instead of restarting a static fit per block.

## R-106 — Continuous harmonic trajectory oracle

- Date: 2026-07-27
- Status: **RESEARCH — FAST GATE IN PROGRESS**
- Hypothesis:
  - R-105 lost a small amount of speech intelligibility because every active
    block restarted its harmonic phase and held pitch and amplitudes constant;
  - preserve absolute Q32 phase across each voiced run, linearly interpolate
    bounded pitch and sine/cosine amplitude knots, and code only the remaining
    lapped Innovation;
  - the continuous law should remove block-edge incoherence without copying
    degraded PCM history or introducing a neural decoder.
- Constraints:
  - the prospective decoder uses the existing frozen Q15 sine ROM, unsigned
    Q32 phase, bounded signed coefficients, integer linear interpolation,
    bounded multiply-accumulate, signed rounding, and int16 saturation;
  - every phase is derivable from a run origin and transmitted trajectory
    knots, so decode output is independent of callback or render-block size;
  - pitch analysis, voiced-run discovery, and least-squares fitting remain
    encoder-only and may use floating point; transmitted state and synthesis
    are deterministic integers;
  - inactive regions remain ordinary lapped Truth, every parameter byte and
    checksum participates in RDO, and malformed runs, knots, sizes, or
    residual configurations are rejected before allocation or synthesis;
  - no Main opcode or bitstream identifier is assigned unless the independent
    parser/decoder and declared evidence gates pass.
- Fast gate:
  - compete bounded trajectory lifetimes and harmonic counts against the
    unchanged 17,744-byte pinned speech anchor and current official Opus
    reference;
  - complete candidate bytes must match the preceding Resonith stream within
    0.5%, STOI and ESTOI must both improve, SNR may not regress by more than
    0.5 dB, and log-mel RMSE may not regress by more than 5%;
  - selection is lexicographic: pass all hard bounds first, then maximize
    STOI plus ESTOI, then SNR, then minimize complete bytes.
- Promotion gate:
  - a speech pass proceeds to Emotional piano as a false-positive guard and
    then the complete Mozart, native-decoder, current-Opus, public-triplet,
    changelog, and semantic-version gates required by R-101 and R-102;
  - stereo evidence uses one independently bounded trajectory bank per
    channel but a single joint lapped Innovation stream. A shared residual is
    required so that the experiment does not gain or lose merely by replacing
    the preceding stereo transform with two unrelated mono transforms;
  - a failure closes this exact representation without changing the current
    production syntax. The report must retain the closest candidate and guide
    the next factorization experiment.

## R-107 — Perceptual gain–shape and envelope-preserving compiler

- Date: 2026-07-27
- Status: **RESEARCH — COMPLETE ADMISSION PASSED; BREAKTHROUGH AND HETEROGENEOUS GATES FAILED**
- Problem:
  - the current global selector minimizes absolute transform energy, producing
    high waveform SNR while starving quiet frames and bands that carry speech
    formants, consonants, ambience, and log-spectral structure;
  - LPF1 already transmits one bounded power-of-two scale per critical band,
    but dropping coefficients also drops most of that band's reconstructed
    energy. The scale therefore does not yet act as a true spectral envelope;
  - the public speech anchor consequently beats matched Opus in waveform SNR
    but trails it materially in STOI, ESTOI, and log-mel error.
- Hypothesis:
  - compile each selected band as gain plus normalized sparse shape: preserve
    the analyzed band energy by adjusting the existing scale and retained
    int8 shape values, without adding metadata or a decoder operation;
  - rank shape coefficients by a bounded continuum between raw energy,
    frame-normalized energy, and band-normalized energy instead of imposing a
    blind minimum on every frame or band;
  - exact complete-byte RDO should discover the smallest amount of temporal
    and spectral whitening that protects intelligibility while retaining the
    waveform advantage.
- Constraints:
  - emitted streams remain ordinary LSE2/LPF1 and decode through the unchanged
    fixed-integer Golden Core; this experiment is encoder-only;
  - every selected position, signed value, modified existing band scale,
    entropy byte, and container byte participates in RDO;
  - normalization uses the original analyzed band energy, never decoded past
    PCM, and zero-selection bands remain zero rather than receiving generated
    content;
  - R-100 remains closed: the compiler may continuously reweight candidates
    but may not reserve a fixed coefficient floor per frame;
  - the ordinary energy selector and the R-106 trajectory stream remain exact
    fallbacks. A candidate is chosen only from actual decoder output.
- Fast admission gate:
  - on the pinned speech file at no more complete bytes than the official
    Opus 1.6.1 anchor, STOI and ESTOI must both improve over the preceding
    Resonith anchor, SNR may not regress by more than 0.5 dB, and log-mel RMSE
    must improve;
  - Emotional piano must then stay within 0.5 dB SNR and 3% log-mel RMSE of
    the preceding complete-byte-matched Resonith point.
- Breakthrough target:
  - exceed the same complete-byte Opus anchor simultaneously in speech STOI
    and ESTOI, then close the log-mel gap on the speech and complete Mozart
    evidence without surrendering Resonith's waveform-SNR lead;
  - this target is not a measured claim. Failure of the first oracle triggers
    the next simplest gain–shape representation or predictive envelope law,
    not threshold relaxation.
- Promotion gate:
  - native-decoder identity, all three R-102 references, current Opus decode,
    public listening triplets, blinded listening, changelog, and semantic
    version remain mandatory before this compiler becomes a released default.
- R-111 result:
  - the release C++20 Core completed energy and gain-shape encode/decode on all
    16 heterogeneous 12-second clips, with actual Opus 1.6.1 Ogg files selected
    by complete bytes;
  - gain-shape emitted fewer bytes than the same-budget energy path on 15 of 16
    clips, Resonith beat Opus waveform SNR on 12 of 16, and beat Opus log-mel
    error on 6 of 16;
  - sparse attacks, side drum, grand piano, and dense orchestra were strong
    simultaneous wins, while sustained sine and pink noise lost both headline
    diagnostics;
  - male/female speech retained large waveform-SNR leads but did not beat Opus
    STOI/ESTOI, confirming that the formant/envelope problem is structural;
  - the universal R-107 gate therefore fails. Gain-shape remains a fallback
    candidate and adds no syntax or released-default claim.
- Complete R-102 result:
  - speech produced 17,924 complete bytes against 17,942 Opus bytes, improved
    the preceding Resonith STOI, ESTOI, and log-mel result, and retained
    19.605 dB SNR, but Opus still led STOI 0.993172 to 0.953579 and ESTOI
    0.988045 to 0.905907;
  - Emotional piano produced 117,225 bytes against 117,091 Opus bytes and
    improved the preceding Resonith SNR from 40.4330 to 40.5364 dB and log-mel
    RMSE from 1.05526 to 0.96367;
  - complete Mozart at budget 71 produced 6,452,284 bytes, 0.8895% below the
    Opus target, so it was retained as a frontier point but failed the declared
    rate-match bound;
  - complete Mozart at budget 72 produced 6,526,665 bytes against 6,510,191
    Opus bytes, a 0.2530% difference, improved the preceding Resonith SNR from
    34.5878 to 34.8509 dB and log-mel RMSE from 2.02804 to 1.89211, and encoded
    400.773 seconds in 385.976 seconds through the native-backed research path;
  - the three-complete-file admission gate passes, but the speech breakthrough
    target and R-111 universal gate fail. R-107 remains an RDO fallback and is
    not a released universal default.

## R-108 — Compact integer PVQ with predictive log envelope

- Date: 2026-07-27
- Status: **RESEARCH — NEXT ACTIVE ARCHITECTURE GATE**
- Decision:
  - after publishing the complete R-107 scalar gain–shape evidence, test a
    bounded integer pyramid-vector shape and a time/frequency-predicted
    quantized log-energy envelope;
  - keep transform, envelope, pulse count, codebook index, arithmetic, memory,
    and corruption bounds explicit; require an independent decoder and actual
    serialized bytes before comparing quality;
  - retain R-107 and the ordinary LPF1 path as complete fallbacks. No syntax is
    promoted from an estimated-rate or encoder-reconstruction-only result.
  - R-111 requires one band-local RDO competition among coherent integer PVQ,
    transmitted-envelope counter-based stochastic detail, sparse transient
    pulses, R-107 scalar gain-shape, and ordinary energy selection;
  - these are bounded operands of one acoustic ISA and entropy layer, not
    independently framed codecs. No class label is trusted by the decoder.
- Gate:
  - first exceed R-107 at no more complete bytes on speech STOI, ESTOI, SNR,
    and log-mel RMSE;
  - the breakthrough target remains simultaneous STOI and ESTOI superiority
    over the complete-byte-matched official Opus anchor;
  - every passing speech point proceeds through the full cross-content gate
    in R-109 before a normative opcode, changelog release entry, or version.
- Pure-PVQ finding:
  - the first independently decoded PVE1 stream reduced the sustained-sine
    point from 83,061 to 23,913 complete bytes, but regressed SNR by 1.762 dB
    and log-mel RMSE by 2.398x relative to R-107;
  - on speech it produced 18,404 bytes against 17,924 for R-107, improved STOI
    from 0.953579 to 0.964781 and ESTOI from 0.905907 to 0.930657, but reduced
    SNR from 19.605 to 11.494 dB;
  - this is evidence that the compact envelope and direction preserve useful
    perceptual structure but cannot replace TruthInnovation. PVE1 remains an
    oracle and is not eligible for promotion by adding pulses indefinitely.
- PVE2 amendment:
  - couple the independently decodable PVE1 basis with a bounded sparse
    transform-domain TruthInnovation field in the same RSC1 stream;
  - reconstruct the base coefficients first, add explicit signed correction
    coefficients under transmitted per-band integer scales, then run one fixed
    integer synthesis. The correction may contain only measured source-minus-
    base error and may not generate or predict untransmitted detail;
  - select the complete-byte Pareto frontier across base pulse and correction
    budgets. PVE2 passes the fast gate only if one point is no larger than
    R-107 and simultaneously improves speech SNR, STOI, ESTOI, and log-mel
    RMSE; otherwise retain the negative result and change the factorization.
- PVQ compiler correction:
  - the initial PVE1 encoder proportionally rounded coefficient magnitudes to
    pulses and transmitted the unprojected source-band norm. That construction
    is deterministic but does not minimize squared error for the decoded PVQ
    direction and therefore is not a valid quality verdict on the syntax;
  - replace it with a bounded greedy integer search that maximizes squared
    target correlation per candidate pulse energy, followed by the
    projection-optimal gain for the selected direction. Ties are resolved by
    coefficient index, the bitstream and decoder remain unchanged, and the
    old proportional quantizer is not retained as an encoder candidate unless
    actual RDO finds a smaller complete stream at equal distortion;
  - rerun the same speech and sustained-sine frontier before changing entropy
    or adding more TruthInnovation so that directional-search gain is measured
    independently.
- Corrected fast-gate result:
  - the greedy direction plus projected gain improved the selected speech
    point from 11.494 to 12.134 dB SNR, but it still required 18,580 bytes and
    remained 7.471 dB below the 17,924-byte LPS5 baseline. Speech log-mel RMSE
    improved to 1.465 and STOI/ESTOI reached 0.961999/0.928951, demonstrating
    useful envelope structure without an acceptable Truth reconstruction;
  - the sustained-sine point was 23,926 bytes with 36.103 dB SNR and 2.035
    log-mel RMSE. LPS5 remained better in both SNR and log-mel at 83,061
    bytes, while PVQ retained its large rate advantage;
  - therefore neither proportional nor greedy pure PVQ becomes a universal
    base path. Both remain band-local RDO candidates only, and PVE2 sparse
    TruthInnovation must prove a complete-stream Pareto win before any decoder
    promotion.

## R-109 — Permanent cross-content architecture evidence gate

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - every material architecture change MUST be evaluated on the pinned speech,
    Emotional piano, and complete Mozart references, regardless of the content
    class that motivated the change;
  - extend the permanent corpus with reproducibly acquired, redistribution-
    compatible references covering at least male and female speech, solo
    voice, tonal sustain, transient percussion, dense music mix, electronic
    material, ambience/noise, stereo image, and packet loss;
  - prefer official or primary corpus sources, pin source URL, version,
    license, exact crop, PCM normalization procedure, SHA-256, and acquisition
    date, and never silently replace a reference after results exist;
  - evaluate complete files from actual decoders and report complete bytes,
    bitrate, SNR, SI-SDR, segmental SNR, multi-resolution STFT, log-spectral,
    log-mel, magnitude similarity, onset/pre-echo where applicable, STOI and
    ESTOI for speech, hashes, tool versions, source commit, and wall time;
  - negative and mixed results are first-class evidence. Perceptual
    superiority still requires controlled blinded listening in addition to
    objective diagnostics.
- Publication:
  - every completed architecture gate receives a detailed English Markdown
    report, machine-readable JSON, listening artifacts where redistribution is
    permitted, and a clearly separated conclusion, regressions, limitations,
    and next action;
  - every released improvement receives a semantic version and linked English
    `CHANGELOG.md` entry. Experiments that do not change the released default
    are recorded under the Unreleased research section without pretending to
    be a product improvement;
  - the repository index MUST make the latest benchmark, corpus manifest, and
    changelog easy to find from the project front page.

## R-110 — Research control plane and native execution boundary

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - retain Python as a thin research control plane for rapidly expressing
    hypotheses, search spaces, RDO cost functions, experiment orchestration,
    metrics, plots, reports, and independent conformance models;
  - execute every material per-sample, per-coefficient, transform, PVQ search,
    candidate reconstruction, synthesis, and decode workload in the shared
    native C++20 Core, with portable SIMD and optional CUDA acceleration where
    measurement proves a benefit;
  - a successful experiment MUST migrate its bitstream-critical behavior into
    the bounded native encoder/decoder path before promotion. A Python oracle
    may describe or verify normative behavior but may never be its only
    executable definition;
  - the shipped Resonith codec, SDK, command-line tools, embedded library, and
    Orkela playback path MUST have no Python runtime dependency;
  - keep an independently structured Python conformance model where practical
    so that exact native output is checked against a second implementation
    rather than against itself.
- Rationale:
  - banning Python would lengthen hypothesis iteration through repeated
    compile/link cycles without improving the shipped product;
  - executing heavy DSP in Python would make full-track architecture gates
    unnecessarily expensive and would obscure the performance of the intended
    implementation;
  - the split preserves interactive research speed, native throughput,
    cross-platform product portability, and independent verification at the
    same time.
- Enforcement:
  - profiling MUST identify any Python loop whose cost scales materially with
    samples, coefficients, candidates, or PVQ pulses; such a loop is a native
    migration candidate before a full-corpus gate;
  - final RDO measurements MUST decode through the native Core and require
    exact PCM equality with the independent model for every promoted syntax;
  - Python-only throughput is research telemetry and MUST NOT be presented as
    the expected speed of a production encoder;
  - native acceleration must preserve the same serialized bytes or declare a
    distinct encoder search level; it may never change normative decoding.

## R-111 — Extended heterogeneous acoustic corpus

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - the three complete R-102 references remain the mandatory regression floor,
    not the complete architecture corpus;
  - add a pinned heterogeneous matrix covering sustained deterministic tone,
    stochastic noise, vibrato/resonance, electronic material, solo tonal
    instruments, sparse attacks, drums, cymbal-like stochastic transients,
    polyphonic piano, solo voice, female speech, male speech, dense orchestra,
    dense popular music, and mixed dialogue/music/effects/ambience;
  - source the controlled material from the lossless EBU Tech 3253 SQAM
    package and lossless Xiph test-media film mixes. Keep exact collection and
    item URLs, byte counts, SHA-256 hashes, acquisition date, crop, channel
    policy, and use restrictions in a machine-readable manifest;
  - use deterministic PCM16 preparation and publish the prepared-file hashes.
    Source audio that cannot be redistributed under clearly verified terms
    remains local; the repository publishes acquisition instructions,
    provenance, and evidence only;
  - every material architecture change first passes the three complete
    references, then the heterogeneous matrix. Content-specific modes must
    report both the classes they improve and those they regress.
- Initial bounded gate:
  - use one pinned 12-second diagnostic crop per heterogeneous class so that
    broad screening remains practical on a consumer workstation;
  - any candidate promoted toward release must be rerun on the complete source
    items for every class where the bounded crop shows a material win or loss;
  - packet-loss tests apply deterministic loss patterns to the speech, dense
    mix, and film-mix streams in addition to clean-channel measurements.

## R-112 — Immediate improvement capture and measured optimization

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - when implementation or measurement exposes a concrete improvement, record
    it immediately with its affected invariant, expected benefit, regression
    risk, and measurable acceptance gate;
  - implement it at the nearest safe boundary of the active experiment. Do not
    discard an in-flight reproducible gate or mix unmeasured changes into its
    evidence, but do not leave a discovered opportunity only in chat or an
    unprioritized backlog;
  - small isolated improvements with existing coverage are applied and tested
    immediately. Architectural or bitstream changes first receive a frozen
    decision and baseline so that an apparent gain cannot erase comparability;
  - every performance claim requires wall-time evidence, exact output-byte or
    decoded-PCM identity where the algorithm is intended to be unchanged, and
    the toolchain, CPU/GPU path, input duration, and source revision.
- Current optimization gate:
  - profile the R-107 native-backed complete encode and attribute wall time
    among analysis, selection, entropy packing, container construction, and
    independent decode rather than assuming Python is the bottleneck;
  - move every material sample/coefficient/symbol loop identified by that
    profile into the C++20 Core or replace it with a measured bounded vector
    operation, while retaining Python only as the experiment controller;
  - require byte-identical `.resonith` output and PCM-identical decode before
    accepting an unchanged-algorithm optimization;
  - publish short-reference before/after timings first, then rerun complete
    Mozart. The immediate target is at least 2x end-to-end encode throughput
    over the published 385.976-second R-107 run on the same machine; this is a
    target, not a measured result.
- Measured result:
  - the allocation-free C++20 adaptive arithmetic packer is byte-identical to
    the independent Python oracle for alphabets from 2 through 512 and is now
    used for LAF1 scale, value, and gap-category fields;
  - the ordinary encode hot path no longer serializes and decodes a duplicate
    monolithic LPF1 stream. That comparison remains available as an explicit
    conformance mode and in independent streaming/native tests;
  - complete Mozart encoded in 155.866 seconds instead of the published
    385.976 seconds, a 2.476x speedup and 2.571x realtime throughput. The
    6,526,665-byte result remained byte-identical with SHA-256
    `9018223f167b21bb47be165c1b39d947b4e580f96dd8eda4315438f8d5c9ff6f`;
  - speech improved from 1.010 to 0.439 seconds (2.301x), and Emotional piano
    improved from 6.981 to 2.859 seconds (2.442x), also with exact stream
    identity;
  - all 16 R-111 class streams remained byte-identical in a 60.174-second
    regression gate, the strict warning build passed, and the complete
    Python/native suite passed 180 tests with four unavailable external-device
    or external-tool integrations skipped;
  - because every compressed byte is identical, all previously published
    objective quality and decoded-PCM results remain exactly unchanged. R-112
    changes implementation throughput, not bitstream syntax or codec quality.

## R-113 — RDO-selectable bounded value entropy

- Date: 2026-07-27
- Status: **RESEARCH — PASSED AS AN RDO-SELECTABLE MODE**
- Observation:
  - in the 17,924-byte R-107 speech stream, coefficient values consume 91,320
    of 136,640 entropy bits (66.8%), while scales consume 13.0%, position gaps
    19.2%, and counts 0.9%;
  - a packet-local bounded signed Rice/packed search reduces the budget-68
    value field by 2,179 bits. Budget 68 already improves SNR, STOI, ESTOI, and
    log-mel RMSE over budget 67, and the prospective descriptor extension
    costs 46 complete bytes across 23 packets;
  - this is only a measured field-cost opportunity. It is not a complete-file
    result until serialized and independently decoded.
- Decision:
  - add a distinct prospective LPS6/LAR1 research syntax that preserves all
    LPS5 packet, reset, transform, scale, count, gap, integrity, and bounded-
    allocation rules but permits the value field to select bounded signed
    Rice or fixed-width entropy per packet;
  - carry the value entropy ID and parameter explicitly. Never infer them from
    content, and retain ordinary LPS5 adaptive values as an exact complete
    fallback in encoder RDO;
  - first implement an independently bounded Python oracle, then migrate the
    accepted parser and decoder to the allocation-free C++20 Core before any
    release or player claim.
- Fast gate:
  - one actual LPS6 speech stream at no more than 17,924 complete bytes must
    exceed the published R-107 speech point simultaneously in SNR, STOI,
    ESTOI, and log-mel RMSE;
  - corruption, truncation, noncanonical padding, entropy parameter, packet
    reset, and exact reconstruction tests are mandatory;
  - a passing speech point proceeds to complete piano, complete Mozart, and
    all 16 R-111 classes. Per-class RDO may retain LPS5, and the chosen stream
    must be compared by complete bytes and actual decoder output.
- Preliminary measured result and immediate performance action:
  - the independently serialized budget-68 speech point is 17,904 complete
    bytes and improves all four required metrics over the 17,924-byte
    budget-67 LPS5 point: SNR 19.728 versus 19.605 dB, STOI 0.953871 versus
    0.953579, ESTOI 0.907409 versus 0.905907, and log-mel RMSE 3.6510 versus
    3.6903. This passes the first fast gate but is not yet a corpus result;
  - the first Python-oracle run required 1.897 seconds because bounded value
    serialization and independent decoding remained Python loops. Before the
    full corpus gate, migrate both accepted paths to allocation-free C++20,
    require exact Python/Core entropy bytes and PCM parity, then report the
    new wall time. This applies R-109 and R-112 rather than accepting an
    avoidable research-only throughput regression.
  - the complete-reference gate exposed a second avoidable cost: adjacent RDO
    budgets independently repeat identical fixed transform analysis. Preserve
    one immutable authenticated `LappedAnalysis` per source/configuration and
    reuse it across entropy modes and coefficient budgets. Apply this only
    after the already-running gate is captured, then require exact stream and
    PCM identity for every candidate plus a multi-budget wall-time result.
- Complete measured result:
  - speech selected budget 68 at 17,904 bytes, 20 bytes below the prior
    budget-67 LPS5 point, and improved SNR by 0.1234 dB, STOI by 0.000292,
    ESTOI by 0.001502, and log-mel RMSE by 0.03925;
  - complete Emotional piano saved 110 bytes and complete Mozart saved 5,432
    bytes at identical budgets and exact decoded PCM;
  - all 16 heterogeneous base-budget reconstructions were PCM-identical.
    RDO selected LPS6 for female speech, male speech, and dense pop, saving
    1,600 bytes across the matrix, and retained LPS5 for the other 13 classes;
  - native value entropy is byte-identical to the independent oracle, native
    LPS6 decode is PCM-identical, and parameter, padding, truncation, and CRC
    rejection gates pass;
  - native packing reduced the speech candidate from 1.897 to 0.415 seconds.
    Shared immutable analysis then reduced the measured two-budget speech
    encode phase from 0.852 to 0.622 seconds with identical candidate hashes;
  - LPS6 is not a universal replacement and does not close the Opus
    speech-intelligibility or spectral-envelope gap. It remains a prospective
    encoder-selected mode with exact LPS5 fallback.

## R-114 — Latest stable language and build-tool baseline

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - use the latest stable production releases for active development:
    Python 3.14.6 for the research control plane, C++23 for native source,
    LLVM/Clang 22.1.8 through llvm-mingw 20260616 on Windows, CMake 4.4.0,
    and Ninja 1.13.2;
  - pin downloads, versions, and hashes. Never replace a stable project
    baseline with a release candidate, nightly, or unverified binary merely
    because its version number is newer;
  - LLVM 23.1.0 RC1 and the unfinished C++26 publication cycle are therefore
    not production baselines. They may run non-blocking forward-compatibility
    jobs only;
  - use C++23 as the declared language mode but limit decoder-critical source
    to features supported by the current Clang, GCC, MSVC, Apple Clang, and
    Android NDK gates. A new library feature is not accepted until all target
    toolchains pass;
  - Python remains absent from shipped codec, SDK, embedded, CLI, and Orkela
    runtime artifacts. Updating Python affects only research orchestration,
    independent oracles, metrics, and reports;
  - every language or toolchain upgrade must pass the strict native build,
    the complete Python/native suite, and at least one exact compressed-stream
    and decoded-PCM regression before becoming the documented default.
- Owner amendment:
  - C++26 is the active native language mode now, despite the standard and
    newest LLVM line still being pre-final at this date;
  - install llvm-mingw 20260721 with LLVM 23.1.0 RC1 as the primary Windows
    C++26 toolchain and pin it separately from the retained stable LLVM 22.1.8
    baseline;
  - the primary build and CI request C++26. A secondary C++23 compatibility
    build remains mandatory for current Android, Apple, and embedded
    toolchains until their C++26 modes pass;
  - C++26-only source features require a measurable correctness, safety,
    performance, or maintainability benefit. Version novelty alone is not a
    reason to enlarge the decoder or reduce platform coverage;
  - this amendment explicitly supersedes the earlier R-114 choice to keep
    C++26 only in a non-blocking forward-compatibility job.
- Final owner amendment:
  - restore C++23 as the primary production language mode to preserve current
    mobile and embedded compatibility;
  - cancel the LLVM 23 RC toolchain adoption and retain stable llvm-mingw
    20260616 with LLVM/Clang 22.1.8;
  - C++26 returns to a non-blocking forward-compatibility gate until the
    mobile, Apple, and embedded toolchains support it without reducing target
    coverage;
  - this final amendment supersedes the immediately preceding C++26/LLVM 23 RC
    amendment. The historical record remains explicit rather than silently
    rewriting the decision sequence.
- Final evidence:
  - strict C++23 compilation completed with extensions disabled and warnings
    treated as errors; 10 of 10 native tests passed;
  - Python 3.14.6 completed 185 tests: 181 passed and four external device or
    Opus integrations were skipped;
  - all 16 R-111 streams, covering 192 seconds and 2,471,068 bytes, remained
    byte-identical. Native/Python decoder parity tests remained exact;
  - the accepted C++23 Core DLL SHA-256 is
    `a801f0192c81c57b2c97465efa637d0ea4612c6194f9f146a4c93cde6408fab0`.

## R-115 — Self-contained MinGW production artifacts

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - MinGW production libraries, tools, and tests statically link their C++
    runtime through the Resonith Core target contract;
  - a released Resonith DLL or executable must not depend on a compiler-local
    `libc++.dll`, `libstdc++-6.dll`, or equivalent C++ runtime that is absent
    from a stock target system;
  - the stable C ABI remains the integration boundary. Static runtime linkage
    does not expose a C++ ABI or permit allocation in the audio callback;
  - CI must inspect Windows binary dependencies and run tests without adding
    the compiler directory to `PATH`. A missing runtime must fail directly,
    never wait on an interactive system dialog.
- Evidence:
  - the first strict C++23 CMake/Ninja gate linked test executables against
    compiler-local `libc++.dll`; CTest consequently waited on the Windows
    loader dialog when the toolchain directory was not on `PATH`;
  - the prior direct release DLL was self-contained. The CMake contract now
    makes that property explicit and reproducible;
  - post-fix dependency inspection found only Windows system runtime imports
    in both the Core DLL and the C-header test executable; all 10 native tests
    then passed without adding the compiler directory to `PATH`.

## R-116 — Mandatory Windows, Android, and iOS portability gates

- Date: 2026-07-27
- Status: **ACCEPTED**
- Decision:
  - every promoted Resonith Core change must compile as strict C++23 for
    Windows x86-64, Android ARM64, and iOS ARM64;
  - Android x86-64 is a mandatory emulator compile target. Android ARMv7 is an
    optional compatibility target and may not constrain the Main decoder;
  - use stable Android NDK r29 and API 26 as the first mobile baseline.
    Android ARM64 artifacts expose the same stable C ABI and deterministic
    integer semantics as desktop builds;
  - iOS artifacts are built by current stable Xcode on a macOS runner for
    device ARM64 and at least one simulator architecture. A Windows host
    cannot substitute for Apple's SDK, linker, signing, or runtime;
  - iOS 15 is the initial deployment floor. Increasing either mobile floor
    requires measured necessity and an explicit owner decision;
  - codec conformance is separate from player conformance. Resonith CI proves
    library compilation, tests that can execute on the host or emulator, ABI
    visibility, and conformance-vector identity. Orkela separately proves its
    Android and iOS package, UI, audio-device, lifecycle, file-picker, and
    background-playback adapters;
  - a Windows-only Orkela feature may be merged during the migration only
    when the portable session contract is unchanged and the platform gap is
    declared. Once the first Android and iOS packages pass, every new Orkela
    release must produce Windows, Android, and iOS artifacts from one source
    revision;
  - local Android builds use a pinned JDK, command-line SDK, build tools, and
    NDK under ignored repository artifacts. iOS builds remain reproducible in
    GitHub Actions until a physical macOS build host is available.
- Rationale:
  - C++23 preserves substantially wider current Android NDK and Apple Clang
    coverage than an early C++26 baseline;
  - compile-only success is necessary but insufficient for a player. Codec
    determinism, real-time audio behavior, mobile lifecycle, thermal limits,
    and package installation require separate evidence.

## R-117 — Temporal score companding before band-local representation RDO

- Date: 2026-07-27
- Status: **RESEARCH — FAST GATE PASSED ON PINNED SPEECH**
- Observation:
  - the R-113 speech winner spends a globally fixed transform-coefficient
    budget according to raw energy. A frame-energy exponent of `0.02` preserves
    the same 17,904 complete bytes while reallocating a small number of
    coefficients from the loudest frames to quieter acoustic state;
  - on the pinned speech reference, the actual LPS6 decoder output improved
    SNR from 19.728443 to 19.730429 dB, STOI from 0.953871 to 0.954650, ESTOI
    from 0.907409 to 0.908310, and log-mel RMSE from 3.651023 to 3.644395;
  - this is an encoder-only RDO candidate. It changes neither syntax nor the
    bounded C++23 decoder.
- Decision:
  - add temporal score companding as a continuous encoder search parameter,
    with exact zero as the existing fallback;
  - evaluate the fixed `0.02` fast-gate point against the current R-113
    selected streams on all 16 R-111 classes and the complete speech, piano,
    and Mozart references before changing a default or version;
  - retain the preceding stream per item whenever complete bytes or any
    mandatory quality diagnostic regresses. A corpus aggregate may not hide
    an individual loss;
  - after this isolated encoder result, resume R-108 as a band-local
    representation competition. Global PVE2 is rejected as the factorization:
    at 17,821 bytes it improved speech log-mel RMSE from 3.651 to 2.968 but
    reduced SNR/STOI/ESTOI to 10.674 dB, 0.916774, and 0.868799 because the
    stream paid globally for both a PVQ basis and sparse correction;
  - the next PVE experiment must let each band select exactly one primary
    representation, with optional measured TruthInnovation only where the
    complete-byte RDO proves that correction is cheaper than the ordinary
    sparse-Truth fallback.
- Gate:
  - the temporal candidate is selectable only when it is no larger than the
    preceding complete stream, does not regress SNR or log-mel RMSE, and, for
    speech, does not regress STOI or ESTOI;
  - a material default requires the R-109 publication set, native decoder
    output, current Opus anchors, full Mozart, and the mandatory mobile
    compile matrix from R-116.
- Complete R-118 result:
  - all three complete references and all 16 heterogeneous classes were
    encoded and decoded, for 19 actual candidate streams;
  - the pinned LibriSpeech candidate remained exactly 17,904 bytes and
    improved all four mandatory diagnostics, so it is retained as an
    encoder-side search candidate;
  - piano added one byte and slightly reduced SNR; full Mozart added 907 bytes
    and reduced SNR by 0.010581 dB. Both retained their exact R-113 streams;
  - none of the 16 R-111 items passed the complete-byte and quality gate.
    Female and male speech improved STOI/ESTOI and log-mel slightly, but added
    23 and 14 bytes and reduced SNR. Every heterogeneous item therefore
    retained its exact R-113 fallback;
  - R-117 is not a new default and causes no version or syntax change. It
    demonstrates that file-global score parameters are too coarse; the next
    architecture gate moves the competition to bounded packets and bands.

## R-118 — Non-negotiable 19-item architecture gate

- Date: 2026-07-27
- Status: **ACCEPTED — OWNER REQUIREMENT**
- Decision:
  - no architecture change, codec milestone, default change, version, or
    compression/quality claim may be admitted from only the three complete
    references;
  - the minimum clean-channel architecture gate is the union of:
    1. the complete pinned LibriSpeech excerpt;
    2. the complete pinned Emotional piano reference;
    3. the complete pinned Mozart overture;
    4. all 16 pinned R-111 heterogeneous classes;
  - every one of these 19 items must be encoded and decoded by the actual
    candidate and preceding codec paths. A fallback selection is reported per
    item and may not be counted as a candidate improvement;
  - the 19-item gate is a floor, not a complete test universe. Affected
    mechanisms also require their dedicated packet-loss, seek/reset,
    transient/pre-echo, stereo/spatial, latency, corruption, determinism,
    memory, throughput, mobile, and listening gates;
  - new reproducible classes are added when an experiment exposes a missing
    acoustic regime. Existing pinned items are never removed or silently
    replaced to improve an aggregate score;
  - a partial run must be labelled `FAST GATE` or `DIAGNOSTIC`. It cannot
    authorize a version or a statement that Resonith improved generally;
  - reports must publish a 19-row result table, per-item pass/fallback/failure,
    aggregate counts, actual complete bytes, decoder-derived metrics, hashes,
    wall time, and the exact candidate revision.
- Rationale:
  - the three complete references detect long-stream and public-listening
    regressions, while the heterogeneous set detects content-class failures
    that a speech/piano/orchestra trio cannot represent;
  - requiring their union prevents either long-form evidence or breadth from
    being treated as optional in later development.

## R-119 — Persistent coarse log-gain memory before adding band modes

- Date: 2026-07-27
- Status: **RESEARCH — ACTIVE FAST GATE**
- Observation:
  - the corrected PVE1 speech stream spends 72,359 of 146,729 logical bits
    on gain residuals, more than its 55,700 PVQ shape bits;
  - the current predictor resets an inactive band's gain to zero every frame
    and transmits Q8 fractional log gain. Both choices contradict the MAF
    principle that stable acoustic state should persist until changed;
  - global PVE2 cannot repair this inefficiency because adding sparse Truth
    after an overpriced base duplicates representation cost.
- Decision:
  - extend the research PVE envelope with explicit, bounded persistent
    per-channel/per-band gain memory. A zero-pulse band emits no gain and does
    not erase its remembered state;
  - make log-gain fractional precision explicit in the stream and test Q3,
    Q4, Q5, and Q8. The decoder expands the transmitted code through the
    existing frozen integer Q31 log-gain materializer;
  - preserve PVE1 version 1 byte-for-byte as the fallback. The new semantics
    use an explicit research version and flags; they are never inferred from
    content;
  - test this isolated envelope change before implementing a band-mode map.
    If it does not materially reduce complete bytes without unacceptable
    quality loss, persistent gain memory remains an encoder model rather than
    decoder syntax;
  - only after the gain overhead is measured may R-108 compare one primary
    PVQ or sparse-Truth representation per band. This prevents a mode-map
    experiment from hiding a defective envelope coder.
- Fast gate:
  - serialize and independently decode the pinned speech, sustained-sine,
    pink-noise, side-drum, and grand-piano representatives;
  - report complete bytes, count/gain/shape bits, SNR, log-mel, STOI/ESTOI
    where valid, deterministic hashes, malformed-stream rejection, and
    version-1 regression identity;
  - a candidate proceeds to band-local RDO only if gain bits fall materially
    and at least one complete-stream Pareto point improves on PVE1. It does not
    become a Resonith default without the full R-118 gate.
- Fast-gate result:
  - persistent gain prediction alone was rejected: it increased the pinned
    speech candidate at both Q8 and Q4 precision. Persistence remains a state
    concept, not a mandatory gain predictor;
  - explicit Q4 log-gain precision reduced the budget-96 speech candidate from
    18,580 to 14,455 complete bytes with nearly unchanged SNR, STOI, ESTOI,
    and improved log-mel RMSE;
  - reinvesting part of the saved rate at Q4 produced a 18,376-byte
    budget-192 candidate. Relative to PVE1 it improved speech SNR by
    3.724788 dB, STOI by 0.017447, ESTOI by 0.025355, and log-mel RMSE by
    0.288789 while saving 204 complete bytes;
  - the same Q4/reinvestment search selected a complete-stream Pareto point
    on grand piano, pink noise, side drum, and sustained sine. This is a
    five-class fast gate only, not an R-118 milestone or an Opus victory;
  - the selected speech stream still spends 82,169 logical bits on PVQ shape,
    39,367 on gain, and 23,566 on pulse counts. Shape alone is therefore
    approximately the complete 10,765-byte budget required for a 40% saving
    against the pinned 17,942-byte Opus file.

## R-120 — Unified event-driven MAF representation competition

- Date: 2026-07-27
- Status: **NORMATIVE-DRAFT ARCHITECTURE / RESEARCH IMPLEMENTATION**
- Owner direction:
  - implement the defining MAF idea now rather than continuing to improve a
    transform-only codec under the MAF name;
  - develop the long-lived source/filter, band-local RDO, persistent state,
    stochastic, cached Basis/motif, transient, and channel-reuse mechanisms as
    one coordinated architecture;
  - exploit the full memory-oriented model without degrading accepted tracks.
- Decision:
  - the fundamental encoder decision unit is a bounded
    `packet × channel-group × band × lifetime` cell, not a complete frame and
    not a complete parallel substream;
  - every cell selects exactly one primary representation from `HOLD`,
    `COHERENT`, `SOURCE_FILTER`, `STOCHASTIC`, `TRANSIENT`, `PVQ`, and
    `TRUTH`. A sparse Truth correction is optional only when its complete
    incremental rate-distortion cost beats replacing the primary
    representation with Truth;
  - `HOLD` is the zero-update event: an immutable Basis, excitation law,
    filter law, seed law, gain trajectory, routing, and lifetime remain in
    force until an explicit mutation or end. The bitstream MUST NOT resend
    unchanged state merely because another transform interval elapsed;
  - source excitation and the stable filter/timbre envelope are independent
    long-lived state. Pitch/phase, gain, and sparse filter control points may
    update at different times. A block-local harmonic fit is not sufficient
    evidence for this mode;
  - stochastic state carries a deterministic counter-based generator,
    spectral/temporal envelope, and lifetime. Its realization is objective
    decoder state, but a stochastic candidate MUST NOT become a predictor for
    unrelated future Truth;
  - transient state has bounded short support and an explicit onset. It MUST
    NOT force a higher coefficient budget over an entire long window;
  - CIBS materializes an immutable Basis once. Motif reuse is a bounded,
    declarative instance sequence over existing Basis/Atom operations; neither
    mechanism adds per-sample neural inference or an unbounded program;
  - joint-channel or spatial reuse represents a common emitter once and
    transmits bounded channel differences. Independent-channel Truth remains a
    complete RDO fallback;
  - mode flags, state payloads, checkpoints, dictionaries, model packages,
    motif definitions, corrections, and container overhead all count toward
    rate. Savings from interacting mechanisms MUST NOT be added as if they
    were independent.
- Non-regression contract:
  - the current complete LPS5/LPS6 stream remains an ordinary candidate in
    every file-level RDO search;
  - a MAF candidate is admitted per item only after actual serialization,
    independent decoding, complete-byte comparison, and all applicable
    quality gates. Failure selects the exact preceding stream; a fallback is
    never reported as an improvement;
  - no track may be degraded to make an aggregate result appear better. A
    claimed milestone still requires the complete R-118 19-item gate plus
    affected transient, stochastic, stereo, loss, seek, resource, and
    subjective gates.
- Frontier contract:
  - there is no content-independent percentage called “the theoretical
    limit”. A limit is defined only for a pinned source distribution,
    decoder/profile/resource envelope, latency, and distortion contract;
  - Resonith measures three separate frontiers: exact PCM, objectively
    transparent Truth, and perceptual/generative detail. Generative results
    MUST NOT be counted as Truth compression;
  - the 40% Opus saving is a checkpoint, not an assumed ceiling. On the pinned
    speech item it means no more than 10,765 complete bytes versus the current
    17,942-byte official Opus anchor, at independently demonstrated
    non-inferior perceived quality;
  - the initial 10,765-byte engineering budget is a **TARGET**, not evidence:
    state/mode 0.60 KiB, filter/envelope 1.20 KiB, coherent excitation
    3.00 KiB, stochastic/transient 1.80 KiB, Truth 3.70 KiB, and
    container/checkpoints 0.45 KiB. The complete serialized sum, rather than
    any isolated field, decides feasibility;
  - a universal 40% saving is not required and cannot be assumed for
    entropy-like input. The primary structured-content target is at least 40%
    versus byte-matched Opus at MUSHRA non-inferiority; hostile stochastic
    material requires an honest smaller saving or exact fallback.
- Implementation order inside one architecture:
  - build one independently decodable research stream containing the complete
    mode/state competition and exact bit accounting;
  - first activate the representations already supported by measured kernels:
    Q4 PVQ, sparse Truth, persistent Basis hold/trajectory, deterministic
    stochastic fill, bounded transient events, and joint-channel lifting;
  - add the continuous source-filter analyzer and cached Basis/motif proposals
    to the same RDO, never as separately stacked full streams;
  - migrate scaling search/synthesis/decode loops to C++23 while retaining
    Python only as the replaceable oracle and experiment controller;
  - publish an ablation frontier in which each mechanism is disabled in turn.
    Only the joint candidate and its real predecessor/Opus anchors determine
    the headline result.
- Fast diagnostic implementation result:
  - prospective `MFC1` now serializes one independently decodable event field
    with `HOLD`, cached Basis set/reference/update, deterministic stochastic
    state, bounded transient, Q4 PVQ, sparse Truth, and causal channel reuse.
    A PVQ-default map and a separate coarse gain trajectory replace repeated
    per-band signalling;
  - on the pinned speech diagnostic, gain memory reduced the prospective
    complete stream from 21,483 to 19,932 bytes. PVQ-default syntax reduced it
    to 19,277 bytes at SNR 15.847947 dB, STOI 0.979699, ESTOI 0.954469, and
    log-mel RMSE 1.117839. The official Opus anchor remains smaller at 17,942
    bytes and better on STOI, ESTOI, and log-mel, so this is not a win;
  - the event ledger closes exactly: 3,066 map bits, 2,849 mode bits, 146,380
    command-payload bits, and zero unclassified bits. Packing alone therefore
    cannot reach the 10,765-byte checkpoint;
  - prospective `SFT1` corrects the causal source-filter order: the adaptive
    excitation is reconstructed before the stable LPC synthesis filter.
    Integer exact analysis/synthesis remains bit-identical before lossy
    excitation coding;
  - an immutable learned 16-entry filter Basis reduced the measured
    source-filter parameter envelope from 2,577 to 701 bytes. The Innovation
    became more expensive under the transform fallback, so the complete
    candidate did not win;
  - prospective `EPV1` adds a short algebraic PVQ excitation, counter-based
    stochastic candidate, zero event, and causal adaptive pitch state. At
    10,294 complete bytes it exceeded the 40%-saving byte checkpoint but
    produced only STOI 0.878153 and ESTOI 0.795882, so the point is rejected
    on quality;
  - closed-loop adaptive excitation improved the eight-pulse point to
    12,548 bytes, STOI 0.908976, ESTOI 0.846112, SNR 7.211959 dB, and log-mel
    RMSE 1.190511. Its pitch state still mutated in 1,134 of 1,464 subframes;
    it is therefore neither competitive with Opus nor evidence of a
    long-lived pitch law;
  - all figures above are one-item **FAST DIAGNOSTICS**. No default, release,
    bitstream promotion, R-118 milestone, or general compression claim follows.
    The next source-filter gate requires a compact continuous pitch/phase
    trajectory and perceptually weighted closed-loop multi-pulse search, with
    MFC1/LPS6 retained as complete fallbacks.

## R-121 — Cached excitation Basis before higher per-subframe pulse rate

- Status: **RESEARCH**
- Date: 2026-07-27
- Decision:
  - test the defining MAF lifetime claim directly: materialize a bounded bank
    of immutable integer excitation shapes once, then encode each eligible
    subframe as a Basis reference plus a quantized gain and optional local
    correction;
  - train or cluster the bank only in the encoder. The prospective decoder
    receives explicit bounded integer Basis vectors and performs no semantic
    classification, floating-point inference, or per-sample neural work;
  - charge dictionary definition, references, gain events, corrections,
    checkpoints, and container bytes to the complete stream ledger;
  - make cached Basis, algebraic PVQ, stochastic, transient, zero/HOLD, and
    Truth mutually exclusive primary excitation candidates under one
    decoder-in-loop RDO decision. Do not stack a Basis stream over a complete
    PVQ stream;
  - retain EPV1, MFC1, LPS6, and the official complete-byte Opus anchor as
    honest fallbacks. No cached-Basis syntax is promoted unless independent
    decoding and the R-118 evidence gate show non-regression.
- Evidence motivating the experiment:
  - increasing the learned filter bank from 16 to 64 entries improved the
    eight-pulse speech diagnostic from STOI 0.908976 and log-mel RMSE 1.190511
    to STOI 0.920973 and log-mel RMSE 1.104564, but enlarged the complete
    stream to 13,102 bytes;
  - increasing algebraic excitation to 12 pulses reached 15,852 bytes,
    STOI 0.942890, ESTOI 0.898446, and log-mel RMSE 0.984754. This remains
    materially behind the 17,942-byte Opus anchor at STOI 0.993172,
    ESTOI 0.988046, and log-mel RMSE 0.601168;
  - a direct synthesis-weighted pulse search produced no candidate that beat
    the ordinary target-domain candidate under a strict time and
    log-spectral non-regression guard. The dead search is removed rather than
    retained as unproductive complexity.
- Kill condition:
  - reject the cached excitation Basis as a Main-path mechanism if its
    complete dictionary and reference cost does not improve the measured
    rate-quality frontier against direct EPV1 on the affected classes;
  - a one-item result remains a fast diagnostic and cannot authorize a
    default, bitstream promotion, version, or general claim.

## R-122 — Bounded MAF Decoder ISA before Foundry intelligence

- Status: **NORMATIVE-DRAFT**
- Date: 2026-07-27
- Owner direction:
  - finish the deterministic MAF execution substrate before expanding the
    smart, neural, or GPU-assisted encoder;
  - make ordinary desktop and mobile decode independent of a GPU, cloud
    service, Python runtime, or per-sample neural model.
- Decision:
  - the portable C++23 Core exposes a fixed allocation-free integer DSP ISA.
    The initial operation set is periodic/cached Basis render, sparse gain,
    stable source/resonator filter, counter-addressed stochastic field,
    bounded transient injection, quantized Innovation add, channel matrix mix,
    and saturating output commit;
  - a `.resonith` stream carries only validated operation identifiers,
    immutable data, state mutations, references, and numeric parameters. It
    never carries executable native code, bytecode loops, shaders, scripts, or
    dynamically loaded decoder models;
  - the parser resolves stream IDs to prepared caller-owned state before the
    audio callback. The render path performs no allocation, file access,
    network access, logging, locking, model discovery, or global mutation;
  - every profile declares hard maxima for sample rate, output channels,
    active emitters, Basis count/elements, trajectory and gain events, filter
    order, stochastic fields, transients, PVQ/Innovation work, state bytes,
    scratch bytes, and integer operations per rendered frame;
  - preparation rejects a stream before PCM commit when a declaration,
    reference, lifetime, stable-filter domain, arithmetic bound, workspace, or
    operation budget exceeds the selected profile. Render consumes a
    monotonically decreasing operation budget and fails transactionally;
  - counter-based stochastic output is a pure function of stream seed, field
    ID, channel, and absolute sample index. Callback size, thread scheduling,
    CPU SIMD width, and seek order cannot change output;
  - the ordinary mono/stereo decoder targets one CPU thread. Optional GPU
    execution is permitted only for high-count immersive rendering,
    convolution, or non-Truth enhancement and MUST match the integer CPU Core
    for every Truth operation;
  - CIBS runs only while materializing an immutable Basis outside the callback.
    A materialized Basis is ordinary decoder memory; no neural work is
    performed for each rendered sample.
- Encoder boundary:
  - cloud or local AI may propose sources, lifetimes, Basis, trajectories, and
    top-K candidates only after this ISA is fixed enough to evaluate them;
  - exact serialization, independent integer decode, complete-byte cost, and
    distortion decide admission. Semantic confidence never overrides RDO;
  - an external AI service is optional and replaceable. Offline encoding and
    decoding MUST remain available without credentials or network access.
- Promotion gate:
  - publish C and C++ API conformance vectors for every operation and one
    composed causal pipeline;
  - pass malformed input, resource exhaustion, arithmetic edge, callback
    partition, random access, and deterministic replay tests;
  - pass Windows C++23 immediately and Android NDK/iOS compile gates before a
    mobile compatibility claim;
  - integrate stream syntax only after operation-level tests pass. The
    existing Main-0/LPS6 decoder remains the complete fallback throughout.

## R-123 — Default optional Foundry provider adapters

- Status: **ACCEPTED**
- Date: 2026-07-27
- Decision:
  - the future Foundry provider layer presents OpenAI, ElevenLabs, and Azure
    as the three first-class adapters by default;
  - OpenAI supplies general audio-semantic and structured hypothesis
    proposals; ElevenLabs supplies speech, speaker, timing, and optional
    isolation proposals; Azure supplies speech, custom-domain, diarization,
    long-form segmentation, and structured-content proposals;
  - Gemini, Anthropic, and local/open-weight providers remain supported by the
    same capability interface but are not the initial default cloud trio;
  - every cloud adapter is installed in the disabled state. It cannot upload
    audio until the user supplies credentials and grants a per-provider data
    permission;
  - credentials live only in the operating-system credential store. They MUST
    NOT enter a `.resonith` file, repository, project configuration, report,
    command line, telemetry event, crash dump, or ordinary log;
  - permissions distinguish metadata-only, speech upload, full-audio upload,
    and private-audio-denied operation. Providers receive the minimum data
    required for the selected task;
  - provider output is an untrusted time-bounded proposal. It cannot define
    Truth, bypass local decoder-in-loop RDO, become a decoding dependency, or
    prevent fully offline encode/decode.
- Order:
  - implement the adapter interface only after the R-122 bounded MAF Decoder
    ISA and its native stream integration gates are complete.

## R-124 — AI semantic arbiter and selectable generalist

- Status: **ACCEPTED**
- Date: 2026-07-27
- Decision:
  - an optional AI semantic arbiter SHALL analyze a bounded representation of
    the recording before specialist cloud calls and produce a timestamped
    routing plan;
  - the user MAY select OpenAI, Gemini, or automatic capability selection as
    the global analyst and arbiter. OpenAI remains the initial default; this
    supersedes R-123 only where it described Gemini as a non-default-class
    integration;
  - the arbiter assigns global structure, source-type, musical-section, motif,
    and causal-hypothesis work to the selected OpenAI/Gemini adapter; speech,
    speaker-lifetime, word/phoneme-timing, voiced/unvoiced, and isolation
    proposals to ElevenLabs; and long-form, domain-vocabulary, diarization,
    speaker-role, and enterprise-metadata work to Azure;
  - one recording or segment MUST NOT be uploaded to multiple providers merely
    to vote. The router sends only the minimum time span, channels, resolution,
    and metadata required by the assigned capability;
  - a deterministic local policy gate enforces user consent, private-audio
    denial, task allowlists, byte/cost/time budgets, and provider availability
    before executing the AI routing plan;
  - the arbiter and every specialist are untrusted proposal generators. Their
    timestamp/source IDs MAY seed local search, but only exact decoder-in-loop
    MAF RDO can admit a representation;
  - unavailable, rejected, contradictory, or malformed provider output falls
    back to local analysis and cannot prevent offline encoding or decoding.
- Boundary:
  - provider names and APIs are non-normative encoder integrations, not
    `.resonith` syntax or decoder dependencies;
  - the arbiter SHOULD consume a local feature summary or the least revealing
    bounded audio proxy that satisfies the selected provider capability.

## R-125 — Gemini-first Foundry arbitration

- Status: **ACCEPTED**
- Date: 2026-07-27
- Decision:
  - Gemini is the active default AI semantic arbiter and global audio analyst
    during the current research phase;
  - OpenAI remains a user-selectable, disabled-by-default alternative. The
    presence of stored OpenAI credentials MUST NOT cause an OpenAI request;
  - `Auto` MAY choose a provider only when the user explicitly enables
    automatic provider selection. It is not the initial mode;
  - ElevenLabs and Azure retain their R-124 specialist roles and receive only
    tasks and bounded regions assigned by the Gemini routing plan and admitted
    by the deterministic local policy gate;
  - free-tier availability is an operational preference, not an encoder or
    codec invariant. Quota exhaustion, provider failure, or network absence
    falls back to local analysis without changing decodability.
- Supersedes:
  - R-124 only where it named OpenAI as the initial default;
  - R-123 only where its ordering implied that Gemini was not a first-class
    initial provider.

## R-126 — Independent GCC C++23 compatibility gate

- Status: **ACCEPTED**
- Date: 2026-07-27
- Decision:
  - strict GCC is a required independent C++23 compatibility gate in addition
    to the pinned Clang production baseline, MSVC, AppleClang, and Android NDK;
  - the Windows research host uses checksum-verified portable GCC 16.1.0 to
    reproduce GCC-only diagnostics before pushing;
  - the GCC gate uses the same `-Wall -Wextra -Wconversion -Wpedantic
    -Wshadow -Werror` contract as Linux CI;
  - compiler-warning fixes MUST preserve bitstream, fixed-point, ABI, and PCM
    behavior and rerun the complete native and Python/native suites.
- Trigger:
  - commit `9f4fc74` passed Clang, MSVC, AppleClang, Android NDK, sanitizer
    fuzzing, Android, and iOS gates but exposed one GCC-only narrowing warning
    in the MAF filter-history reverse index.

## R-127 — Signed quotient/remainder for normative Q15 rounding

- Status: **NORMATIVE-DRAFT**
- Date: 2026-07-27
- Decision:
  - signed fixed-point rounding SHALL derive the truncated quotient and signed
    remainder from the positive power-of-two denominator, then move the
    quotient one unit away from zero when the remainder reaches half;
  - normative code SHALL NOT obtain the rounding magnitude by negating a
    signed input and converting it to unsigned;
  - this rule is exact ties-away-from-zero, handles positive and negative
    values symmetrically, and avoids architecture-dependent lowering of the
    former magnitude helper.
- Trigger:
  - Windows ARM64 MSVC decoded the negative half of a bounded transient as
    positive saturation while x64 MSVC, Clang, GCC, AppleClang, Android NDK,
    and the remaining MAF operations passed;
  - the ARM64 conformance vector reported status `OK`, the exact expected
    operation budget, positive samples `1000, 2000`, but negative samples
    `-1000, -500` as `32767, 32767`.
- Gate:
  - preserve all existing x64 conformance vectors;
  - require the same positive and negative transient vector on Windows ARM64,
    Android ARM64, Linux ARM64, and desktop compilers.

## R-128 — Live Gemini arbiter evidence before encoder admission

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Owner order:
  - test the configured Gemini-first semantic layer on real audio, update
    Orkela to the resulting bounded MAF Core revision, and then resume typed
    MAF lifetime syntax without replacing the MAF-first roadmap;
  - a provider result is useful only when it narrows local search without
    changing Truth or degrading an admitted reconstruction.
- Decision:
  - the first live adapter consumes a bounded mono proxy and requests only
    timestamped acoustic structure: source classes, coherent, source-filter,
    stochastic, transient, resonant, and mix hypotheses, estimated lifetimes,
    confidence, and specialist-routing needs;
  - the adapter reads its API key from the operating-system credential store.
    A key MUST NOT enter a repository file, command line, generated report,
    prompt transcript, exception, ordinary log, or subprocess environment;
  - uploaded Files API objects are deleted after the response is validated.
    The public machine report records hashes, sizes, durations, timing, model
    identifier, structural counts, and local validation only. It contains no
    credentials, transcript, lyrics, or copyrighted audio;
  - provider JSON is untrusted. A strict local schema, timestamp bounds,
    finite-value checks, enum allowlists, count limits, and overlap limits
    reject malformed or resource-amplifying proposals before Foundry can use
    them;
  - local DSP computes independent energy, onset, periodicity, and spectral
    change evidence. A proposal is labelled supported, weak, or contradicted;
    confidence alone can never admit a MAF representation;
  - the material evidence floor is the complete R-118 union: complete speech,
    complete emotional piano, complete Mozart, and all 16 heterogeneous
    classes. Partial provider availability remains a diagnostic and cannot
    support a codec version or compression claim;
  - this gate changes no bitstream and therefore cannot itself improve bytes
    or quality. Only a later exact decoder-in-loop RDO result may report an
    AI-guided compression improvement, with the preceding non-AI search as a
    complete fallback.
- Execution boundary:
  - Gemini is the only general arbiter called in this gate. OpenAI remains
    disabled; ElevenLabs and Azure receive no audio unless the validated
    routing plan requests their distinct specialist capability and the local
    policy gate separately authorizes it;
  - the research adapter is a thin Python control plane. Audio proxy creation,
    exact feature analysis, candidate synthesis, serialization, decode, and
    RDO remain local compiled or deterministic DSP work. No Python or provider
    SDK is added to the shipped decoder, SDK, or player.
- Promotion gate:
  - pass offline parser and adversarial validation tests without a credential;
  - complete the live 19-item evidence run without leaking audio or secrets
    into Git;
  - demonstrate at least one measured reduction in local candidate-search
    work or one exact-RDO admission before describing the semantic layer as an
    encoder improvement.

## R-129 — Semantic change ledger instead of whole-track labels

- Status: **RESEARCH — OWNER-DIRECTED**
- Date: 2026-07-27
- Decision:
  - a Foundry arbiter response is not useful merely because it classifies an
    entire recording correctly. It SHALL propose a bounded ordered ledger of
    material acoustic changes across time;
  - each proposal event carries its time, source identity or scene-global
    scope, change type, post-change acoustic style, candidate Basis family,
    change strength, and confidence;
  - stable regions separately carry start, end, acoustic style, candidate
    Basis, lifetime, reason, and confidence. A changing speech, music,
    percussion, synthetic, or mixed recording longer than five seconds cannot
    be represented by one undifferentiated full-file region;
  - event classes initially cover source start/stop, section, pitch regime,
    timbre, energy, rhythm, transient, spatial, speech-state, and uncertain
    changes. Acoustic style is a bounded physical/search hint, not a genre or
    copyrighted semantic label;
  - the provider merges changes closer than the declared analysis resolution
    and obeys a hard event-count limit. It is never asked to emit every sample
    fluctuation or a transcript;
  - local deterministic features align every proposed event to a nearby
    sample-accurate candidate boundary, add missed high-confidence DSP
    changes, and remove unsupported provider events;
  - exact decoder-in-loop RDO then prunes any aligned event whose additional
    state/header cost does not reduce complete rate-distortion cost. Therefore
    semantic detail may enlarge the search but cannot enlarge an admitted
    stream or degrade its reconstruction relative to the complete fallback.
- Evidence rule:
  - reports publish event and stable-region counts, styles, change families,
    local support, pruning, timing, and search reduction. Raw transcript,
    lyrics, copyrighted descriptions, and provider prose remain unrecorded;
  - a one-label response is reported as classification-only and rejected from
    encoder admission even if its label is correct.
- First complete live result:
  - revision `574c0cdff2e7c722a0732cddf804d666ac7d108e` analyzed the
    complete R-118 union in 116.057 seconds, uploaded 19 bounded proxies, and
    deleted all 19 provider objects;
  - the strict response contained 39 ordered change events and 20 stable-region
    boundaries across 19 items. Sixteen items received more than one region;
    complete Mozart received four regions/events rather than one whole-file
    label;
  - the independent coarse family audit reported 28 supported, 11 weak, and
    zero contradicted region hypotheses. Original-PCM one-millisecond
    alignment supported 24 of 39 event times; 15 require local replacement or
    removal. Provider-to-local shifts reached 249.025 ms, directly confirming
    that provider timestamps cannot be serialized;
  - the result is accepted as a useful semantic proposal diagnostic but
    rejected from encoder admission: event density remains too low for speech
    and long-form music, no search-work reduction has been measured, and no
    exact RDO candidate changed bytes or reconstruction;
  - the next gate uses per-clip and long-form chunk analysis plus dense local
    change proposals. It retains the exact non-AI search and stream as the
    complete fallback.

## R-130 — Sample-verified boundaries and typed MAF lifetimes

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Boundary decision:
  - provider timestamps are approximate search hints only. They MUST NOT be
    copied into a normative Resonith stream;
  - for every proposed acoustic change, deterministic local analysis SHALL
    inspect the original-channel PCM in a bounded neighborhood, generate exact
    source-sample candidates, and include strong locally detected candidates
    that the provider missed;
  - exact decoder-in-loop RDO SHALL test the aligned candidate and a bounded
    neighborhood, including the no-boundary alternative. It SHALL serialize a
    boundary only when its complete stream cost repays its record, state-reset,
    checkpoint, and residual consequences;
  - source starts, stops, and transients require a final sample-domain
    envelope/onset refinement after coarse spectral-change localization.
    Pitch, timbre, speech-state, spatial, and section changes use the matching
    local physical evidence. Unsupported or ambiguous provider events are
    removed;
  - the admitted boundary is therefore a property of local PCM and exact RDO,
    not the precision, confidence, wording, or availability of an AI service.
- Typed lifetime decision:
  - introduce prospective `MFT1`, an allocation-free typed MAF lifetime stream
    for stable filters, stochastic fields, source-filter emitters, bounded
    transients, and output mixes;
  - a record installs immutable parameters over an explicit half-open sample
    lifetime. Render callback partitioning does not create state changes or
    require repeated signalling;
  - every source-filter lifetime selects exactly one excitation family:
    phase-continuous impulse excitation or a referenced counter-addressed
    stochastic field. A filter and its excitation may be reused for the
    lifetime rather than retransmitted per transform frame;
  - mix matrices also have explicit lifetimes and refer to emitter identifiers.
    They are not frame headers. Transients are finite onset-addressed events;
  - canonical order, unique identifiers, resolved references, non-overlapping
    source lifetimes, full mix coverage, filter stability, exact resource
    declarations, CRC integrity, and operation budgets are validated before
    playback state or PCM can be committed;
  - the decoder executes a fixed integer ISA with caller-owned persistent and
    scratch memory. The stream contains no code, loops, recursion, shaders,
    model discovery, file access, or network references;
  - deterministic Truth Innovation remains the complete fallback. `MFT1`
    cannot be promoted merely because it renders: its encoded candidate must
    win exact complete-byte RDO without worsening an admitted reconstruction.
- First implementation gate:
  - inspect and prepare a hostile `MFT1` stream without allocation;
  - render source-filter, stochastic, transient, and mix lifetimes identically
    under different callback partitions;
  - reject truncation, checksum errors, undefined or expired references,
    overlapping lifetimes, resource amplification, unstable filters, and
    insufficient output, scratch, persistent, or operation budgets before
    affected output/state commit;
  - pass strict C++23, adversarial smoke, sanitizer, desktop, Android, and iOS
    compile/conformance gates before stream integration reaches Orkela.

## R-131 — Decoder-in-loop lifetime candidate and complete Truth fallback

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Decision:
  - the first encoder experiment after `MFT1` SHALL produce a real typed
    predictor, decode it through the C++23 Core, compute Innovation from that
    exact integer PCM, and code the remaining error through the existing
    independently decodable lapped Truth path;
  - the research candidate uses the existing authenticated `RSC1` container
    with exactly one `CONF`, one `MFT1`, and one nested residual section. This
    is an experiment envelope, not a frozen Main syntax;
  - rate means the complete outer container bytes, including both section
    integrity records and every nested residual byte. Predictor bytes cannot be
    excluded merely because a long lifetime amortizes them;
  - for each input, the unchanged preceding LPS6/Truth stream remains a
    complete candidate. A typed MAF candidate is admitted only if actual
    decode, layout, duration, metrics, full bytes, resource limits, and
    robustness pass; otherwise the exact preceding stream is emitted;
  - semantic events may narrow lifetime candidates only after R-130 local
    sample alignment. A no-AI deterministic candidate lattice remains
    complete, and the no-boundary/no-MAF candidate is always evaluated;
  - the first fitting families are stable source-filter/phase excitation for
    coherent mono regions, counter-addressed stochastic fields for locally
    noise-like regions, bounded onset transients for sparse attacks, and
    persistent identity or joint stereo mixes. No file-level semantic class
    forces a representation.
- Admission sequence:
  1. add an independent Python builder and parser for `MFT1`;
  2. add explicit ctypes bindings that inspect and render through the native
     decoder with caller-owned memory;
  3. prove Python-packed/native-decoded PCM and callback partition parity;
  4. build the combined complete-byte candidate and run a fast diagnostic;
  5. run every R-118 item before any default, version, or compression claim.

## R-132 — Per-lifetime stochastic excitation gain

- Status: **NORMATIVE-DRAFT**
- Date: 2026-07-27
- Decision:
  - an excitation-only stochastic field owns the reusable counter sequence and
    base field gain, while each consuming source-filter lifetime owns an
    independent signed Q1.15 excitation gain;
  - the decoder combines both gains once per lifetime slice using the R-127
    signed quotient/remainder rule and passes the result to the unchanged
    counter-addressed noise kernel;
  - this permits one immutable stochastic field to serve changing breath,
    frication, bow-noise, or ambience levels without retransmitting a field or
    introducing per-sample parameter work;
  - impulse excitation continues to interpret the same source gain field as
    its signed PCM16 pulse amplitude.

## R-133 — Immutable periodic Basis in the typed lifetime stream

- Status: **NORMATIVE-DRAFT**
- Date: 2026-07-27
- Trigger:
  - the first R-131 router correctly rejected every source-filter/noise
    lifetime on the sustained-sine item: `MFT1` lacked a way to reference the
    already implemented immutable periodic Basis operation, so a stable tone
    could only be approximated by an impulse through a damped LPC filter;
  - the complete fallback prevented regression, but this omission contradicted
    the MAF premise that a stable waveform is paid once and advanced by phase.
- Decision:
  - add an immutable PCM16 periodic `BASIS` record and a
    `PERIODIC_BASIS` source excitation family to prospective `MFT1`;
  - a periodic source references one Basis, carries an absolute Q32 phase
    origin and increment, a signed Q1.15 gain, an emitter, and a half-open
    lifetime. It does not require or mutate source-filter history;
  - rendering SHALL use the existing canonical Q16-interpolated periodic Basis
    kernel followed by the existing gain-law composition kernel. Callback
    partitions cannot change phase or PCM;
  - Basis count is inferred from the canonical total record count in schema 1,
    reported explicitly by inspection, bounded by Main, and included in every
    parser/fuzz/resource gate;
  - periodic Basis competes with impulse source-filter, stochastic
    source-filter, transient, and `NO_MODEL` under exact residual-rate RDO. It
    is never forced merely because a pitch detector reports a high score.

## R-134 — Provider times expand into exact-sample boundary candidate sets

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Trigger:
  - a cloud analyst can identify the correct acoustic change while placing its
    timestamp several milliseconds, or substantially more, away from the
    physical transition;
  - selecting one one-millisecond analysis-frame center is not sample-accurate
    and can move an onset, reset phase at the wrong point, or make an otherwise
    useful lifetime lose exact RDO.
- Decision:
  - an AI timestamp is only the center of a bounded local search. It SHALL
    expand into a bounded set of integer source-sample candidates derived from
    original-channel PCM, never into a serialized boundary;
  - local analysis SHALL retain multiple independently strong change peaks,
    because the nearest or strongest spectral peak need not be the
    rate-distortion optimum;
  - source starts, stops, and transients SHALL contribute exact sample-domain
    envelope and waveform-edge candidates. Pitch, timbre, speech-state, and
    section changes SHALL contribute fine spectral/change candidates;
  - each retained anchor SHALL be searched at individual-sample resolution in
    a bounded neighborhood. At 48 kHz this gives a 20.833 microsecond candidate
    lattice without claiming that the physical event itself is instantaneous;
  - exact decoder-in-loop RDO SHALL compare the complete stream cost and
    decoded error of the retained sample candidates, locally detected missed
    changes, and the explicit no-boundary candidate;
  - AI confidence, provider precision, and acoustic-score rank MAY order or
    prune search work but MUST NOT force a boundary or defeat the complete
    no-AI/no-boundary fallback.
- Resource rule:
  - Main encoder profiles SHALL declare bounds for the provider search radius,
    local anchor count, exact samples per anchor, and full-RDO finalist count;
  - candidate generation is encoder-only. It changes neither the bounded
    integer decoder nor the normative stream syntax.

## R-135 — Spectral quality guard supersedes waveform-SSE-only admission

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Trigger:
  - the corrected periodic-Basis fast candidate reduced complete bytes and
    improved waveform SSE/SNR on the EBU sustained-sine item, yet worsened
    log-mel and multiresolution spectral error;
  - a waveform-SSE-only decision can therefore select a smaller stream that
    is objectively worse in a perceptually relevant domain.
- Decision:
  - complete-byte and decoder-output checks remain mandatory, but waveform
    SSE alone SHALL NOT admit a material architecture candidate;
  - the research admission guard SHALL also compare log-mel error,
    multiresolution spectral convergence, magnitude similarity, and the
    applicable speech/intelligibility or transient diagnostics;
  - a candidate that fails any declared non-regression limit SHALL emit the
    unchanged complete Truth fallback even when it is smaller and has better
    waveform SNR;
  - the report SHALL preserve the rejected candidate and every metric so that
    its representation gain remains measurable without degrading listening
    artifacts or released defaults;
  - thresholds are research policy, not decoder syntax. Final promotion still
    requires complete-byte-matched Opus anchors and blinded listening on the
    complete R-118 union.
- First complete result:
  - revision `b86fdadc501c57c7fe635e6ad9bff1da1e5bad17` evaluated all
    three complete references and all 16 R-111 classes in 1,543.6 seconds;
  - zero of 19 candidates passed both the complete-byte and multi-objective
    quality gates, so every selected artifact is the exact preceding Resonith
    fallback;
  - the EBU electronic-tune candidate reduced complete bytes from 86,387 to
    27,318 but failed log-mel, magnitude-cosine, and all declared
    multiresolution STFT limits. This proves a representation-rate opportunity
    but also proves that the current SSE-directed residual allocator cannot be
    promoted;
  - Mozart passed the declared quality guard but remained 8.64% larger than
    the preceding stream. Speech also passed quality but remained 6.57%
    larger. These results isolate persistent record/residual overhead from
    perceptual allocation failure;
  - the next experiment SHALL search the residual frontier under the R-135
    spectral guard before adding another decoder operation.

## R-136 — Quality-constrained Truth frontier before new syntax

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Decision:
  - expose an encoder-only exact residual-budget override for the existing
    `MFT1` plus Truth candidate without changing any decoder record;
  - on the EBU electronic-tune opportunity, serialize and independently decode
    a bounded residual frontier, measure complete bytes and every R-135 metric,
    and choose the smallest point that passes the preceding-stream quality
    guard;
  - if no passing point remains smaller than the preceding 86,387-byte stream,
    close pure residual reallocation as the solution and proceed to
    band-local representation plus persistent-state merging;
  - every frontier point retains the same native predictor, complete outer
    bytes, exact fallback, and deterministic decoder path. A lower-rate failed
    point remains diagnostic only.
- Measured result:
  - the exact residual budgets 12, 16, 24, 32, 48, 64, and 71 were serialized
    and independently decoded on EBU electronic tune;
  - no point passed R-135. Log-mel error improved monotonically from 4.001 to
    2.430 but remained far above the preceding 0.459;
  - the 48-budget point remained smaller at 71,907 versus 86,387 bytes but
    failed log-mel and magnitude similarity. Budgets 64 and 71 were both
    larger and still failed those metrics;
  - pure residual-budget reallocation is therefore closed as the solution.
    The failure originates in representation selection and final-sum
    allocation rather than too little search over the existing scalar budget.

## R-137 — Final-output representation ablation before band-local syntax

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Decision:
  - expose encoder-only allowed-family masks while retaining `NO_MODEL` as a
    mandatory candidate and changing no decoder syntax;
  - ablate periodic, impulse source-filter, and stochastic source-filter
    families on the electronic-tune opportunity at an otherwise identical
    residual point;
  - a representation family is useful only when the complete native-decoded
    sum, not its isolated residual proxy, passes the R-135 spectral guard;
  - if `NO_MODEL + PERIODIC_BASIS` materially improves the frontier, full-band
    impulse/stochastic admission is disabled until closed-loop final-output
    or band-local RDO exists;
  - if no family mask passes below the preceding bytes, proceed directly to
    band-local mutual exclusion and persistent-state merging. Do not add a new
    excitation opcode to rescue this gate.
- Measured result:
  - at a fixed 48-coefficient residual budget, only `NO_MODEL` passed all
    declared limits: 63,412 bytes versus the preceding 86,387 and log-mel
    0.466 versus 0.459;
  - this is a better ordinary Truth point, not a MAF gain;
  - periodic-only improved waveform SNR from 36.181 to 43.634 dB for 64,607
    bytes, but log-mel rose to 0.512 and magnitude similarity missed the R-135
    limit;
  - every mask containing impulse or stochastic source-filter excitation
    produced a much larger spectral regression. Those full-band modes are
    disabled from promotion until final-output or band-local RDO exists.

## R-138 — Optimized Truth is the incremental MAF baseline

- Status: **RESEARCH — ACTIVE GATE**
- Date: 2026-07-27
- Decision:
  - every structural MAF result SHALL report two comparisons: the preceding
    released Resonith stream and the best eligible `NO_MODEL` Truth point from
    the same search. Only the second comparison is incremental MAF gain;
  - the 63,412-byte electronic-tune `NO_MODEL` point becomes the local
    architecture baseline. Its reduction MUST NOT be attributed to periodic,
    source-filter, stochastic, AI, or lifetime coding;
  - before adding band-local syntax, test the existing gain-shape residual
    selector and bounded whitening frontier with periodic-only MAF. This may
    preserve the periodic waveform gain while directing Truth toward spectral
    non-regression;
  - periodic MAF is admitted only if it beats or improves on optimized Truth
    under a declared complete-byte/quality tradeoff. Otherwise the next
    mechanism is band-local mutual exclusion, not a looser quality threshold.
- Measured result:
  - six periodic-only gain-shape residual variants at budget 48 tested frame
    whitening 0, 0.02, 0.10, and 0.25 plus two band-whitened combinations;
  - complete bytes ranged from 63,866 to 64,595, but log-mel ranged from 0.517
    to 0.542 versus 0.459 for the preceding stream and 0.466 for optimized
    `NO_MODEL`;
  - no periodic point passed R-135. Gain-shape residual selection is closed as
    the missing solution for this full-band periodic candidate.

## R-139 — Content-defined immutable motif dictionary

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- North-star decision:
  - MAF SHALL support paying once for a reusable acoustic motif and placing
    bounded instances over the continuous timeline. Repetition is not limited
    to periodic oscillators or transform-frame back-references;
  - the dictionary contains immutable objective PCM16 or integer-synthesized
    Basis. An instance carries an exact start sample, Basis reference, gain,
    absolute phase/time origin, bounded pitch/time law, channel/emitter
    placement, and half-open support;
  - objective per-instance correction remains Truth. A transformed instance
    that cannot repay its dictionary bytes, command bytes, and correction is
    rejected in favor of `NO_MODEL`.
- Encoder layers:
  1. exact content-defined chunking and hashing finds bit-identical motifs
     despite unknown positions;
  2. canonical matching factors gain, sample alignment, phase, modest
     pitch/time drift, and channel placement before searching near-duplicates;
  3. decoder-in-loop RDO compares immutable Basis plus all instances and their
     corrections against optimized ordinary Truth;
  4. learned or semantic models MAY propose motif families, but cannot define
     equality, correction, or admission.
- Scope and honesty:
  - exact sample, loop, percussion, game, interface, and electronic material
    may obtain very large gains. Live speech and classical stereo mixes may
    expose fewer reusable objective motifs because articulation, overlap,
    reverberation, and other sources change every occurrence;
  - raw waveform hashes alone are insufficient: a one-sample shift, gain
    change, phase change, room response, or overlapping source changes every
    byte. Canonical transformed matching plus objective correction is the
    required general mechanism;
  - this combines known dictionary, long-term prediction, sample-reuse, and
    fingerprinting principles into MAF lifetime syntax. Novelty is not claimed
    until a documented prior-art and patent search is complete.
- Decoder and security:
  - Basis and instance counts, total Basis samples, simultaneous instances,
    interpolation work, correction bytes, and random-access dependency span
    SHALL be profile-bounded;
  - the decoder executes fixed integer placement only. No search, hash,
    semantic model, arbitrary graph, or per-sample neural inference enters the
    bitstream;
  - checkpoints SHALL name every live instance and required immutable Basis.
    Missing or corrupt dictionary data cannot contaminate unrelated future
    state.
- Admission order:
  1. exact one-shot Basis reuse and exact-sample placement;
  2. signed gain and phase/alignment normalization;
  3. bounded pitch/time laws;
  4. overlapping and multichannel instances;
  5. canonical learned Basis proposals only after deterministic gates.

## R-140 — Multiscale spectral micro-Basis tiling

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Clarification:
  - dictionary identity is not a note, phoneme, letter, instrument, or long
    motif. A reusable Basis MAY be any objective waveform/time-frequency
    fragment whose shape recurs anywhere in the recording;
  - a short stable portion inside one crescendo note may be reused inside a
    different note, voice segment, instrument, ambience, or effect. Semantic
    source identity is neither required nor trusted.
- Representation:
  - the encoder searches a bounded multiscale lattice of arbitrary fragments,
    initially exact PCM16 and reversible integer-transform tiles, then
    canonical gain/alignment/phase/pitch/time variants;
  - synthesis is a bounded overlap-add sum of immutable Basis instances with
    exact sample timing, complex phase or equivalent objective alignment,
    gain/trajectory, band support, and objective Truth correction;
  - magnitude-spectrum equality alone is a proposer because different phase
    can produce a different waveform. Exact PCM, reversible complex
    coefficients, or decoder-output plus Truth defines objective equality.
- Granularity rule:
  - the encoder SHALL compete short atoms, medium fragments, long motifs, and
    independent Truth under one complete cost. It MUST NOT split every signal
    into the smallest detectable repeat;
  - an atom is retained only when its one-time Basis bytes plus all placement,
    overlap, transform, checkpoint, and correction bytes are cheaper at the
    declared quality than coding the covered cells independently;
  - placement commands themselves SHALL use persistent entropy contexts and
    delta-coded sample times so very short reuse is not defeated by fixed
    record overhead.
- Architecture:
  - a file-local global dictionary is mandatory for standalone decode. Optional
    package or application dictionaries are enhancement research and cannot be
    required;
  - Foundry MAY use matching pursuit, vector quantization, learned
    dictionaries, robust fingerprints, or AI to propose atoms. The normative
    decoder only performs fixed integer Basis placement, overlap-add, and
    Truth composition;
  - R-139 exact one-shot `BASIS_INSTANCE` is the first executable subset. Band
    support, overlap windows, transformed instances, and compact batched
    placement syntax follow only with measured incremental gain over optimized
    Truth.

## R-141 — Basis equivalence classes under bounded transforms

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Model:
  - near-repeated fragments SHALL be representable as
    `Instance_j = T(theta_j, Basis_k) + TruthCorrection_j`;
  - one immutable Basis therefore represents an equivalence class, or orbit,
    of objectively related waveform/time-frequency fragments rather than only
    bit-identical copies;
  - a magnitude-spectrum match is a proposal. The normative instance is the
    output of exact bounded integer transform `T`, and objective equality is
    established only after correction and native decode.
- Initial fixed transform set:
  - crop and exact sample alignment;
  - signed gain, polarity, and piecewise envelope;
  - absolute phase rotation or equivalent complex alignment;
  - profile-bounded pitch resampling and time stretch;
  - bounded spectral tilt/formant envelope;
  - reverse and finite loop flags;
  - short stable resonator or room-response reference.
- Constraints:
  - transformations compose only in a canonical declared order and use fixed
    integer rounding. Arbitrary formulas, bytecode, graphs, shaders, floating
    point, and per-sample neural inference are prohibited;
  - each profile bounds transform count, knots, interpolation ratio, filter
    order, overlap, operations, and correction dependency;
  - the encoder pays Basis, every transform parameter, placement, checkpoint,
    and correction. It retains the transformed instance only when complete
    RDO beats optimized Truth at the declared quality;
  - lossless remains exact because a lossless Truth correction encodes every
    integer difference between the source and the normative transformed
    Basis. Almost/lossless profiles may quantize only under their declared
    distortion and listening gates.
- Implementation order:
  - R-139 exact `BASIS_INSTANCE` already carries crop and signed gain fields;
  - add phase/alignment and bounded pitch/time only after exact dictionary
    reuse wins its real and synthetic gates;
  - add envelope and stable spectral transforms only after the simpler orbit
    cannot explain a measured residual.

## R-142 — Exact/gain Basis-orbit implementation gate

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Decision:
  - implement `BASIS_INSTANCE` as the first executable equivalence-class
    operation: one immutable mono PCM16 Basis, an exact sample-time placement,
    a bounded crop, and a signed Q1.15 gain;
  - render instances additively into an emitter before the active mix lifetime.
    Decoder output plus a separately coded Truth correction is the only
    reconstruction authority;
  - count every Basis byte, record prefix, instance parameter, mix record,
    Truth byte, checksum, operation, and persistent-memory element. A waveform
    or fingerprint match alone is not a compression result.
- First gate:
  - prove native C++23/Python parser parity, callback-partition invariance,
    hostile-input rejection, and exact source reconstruction after lossless
    correction;
  - compare an optimized independent Truth stream with complete
    `MFT1 + lossless Truth` bytes on transformed-loop synthesis and on pinned
    speech, music, deterministic, transient, and stochastic references;
  - publish forced-orbit results separately from RDO-selected results. A
    synthetic win establishes implementation correctness, not a general codec
    claim.
- Promotion:
  - phase/alignment and bounded pitch/time receive a new record only if
    exact/gain reuse reduces complete bytes on at least one real structured
    class without increasing objective distortion;
  - the complete R-118 union and current Opus anchor remain mandatory before a
    version, default, or broad quality/compression claim.

## R-143 — Multiscale minimum-description acoustic law

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Principle:
  - every region competes under the common causal description
    `X_j = T(theta_j, Basis_k) + S(phi_j, seed_j) + Truth_j`;
  - `T` is a bounded deterministic transform of reusable objective structure,
    `S` is a bounded counter-addressed stochastic law, and `Truth` is the exact
    or quality-declared difference. Any term may be absent;
  - the search is multiscale. A useful law may live for a few samples, one
    oscillation, an attack, a phrase, a room tail, or the complete stream.
- Noise:
  - rain, wind, surf, breath, applause, and analogous material are not assumed
    to repeat exact PCM. Reusable event shapes and resonances compete with
    spectral density, modulation, inter-channel correlation, event-rate, and
    seed laws;
  - the natural realization is preserved only by Truth. A seeded stochastic
    synthesis without correction is perceptual detail, not objective
    reconstruction.
- Minimum-description rule:
  - the existence of a mathematical mapping is insufficient. A representation
    wins only when its complete canonical bytes and bounded decode cost are
    lower than every admitted alternative at the declared quality;
  - arbitrary programs are excluded because a per-region program can merely
    hide the original signal. The decoder exposes only the fixed integer MAF
    ISA and bounded parameter trajectories;
  - optimized independent Truth is the universal fallback, so a failed law
    cannot worsen the selected stream.

## R-144 — Latent acoustic tomography from changing mixtures

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Observation:
  - a finished mono or stereo mix is not treated as an indivisible waveform.
    Repeated sources observed under different gains, positions, filters,
    overlaps, and surrounding sources provide multiple equations from which
    reusable latent components may be inferred;
  - the encoder MAY factor an observed channel as
    `Y_c(t) = sum_i H_ci(t) T_i(theta_it, Basis_i) + Truth_c(t)`.
    `H`, `T`, and every Basis are objective decoder operations; semantic source
    names are unnecessary.
- Compression rule:
  - physical source identity is not required. If two inseparable real sources
    are cheaper as one composite Basis, the composite is canonical for that
    stream;
  - if an inferred separation is wrong, complete native synthesis increases
    Truth or total bytes and RDO rejects it. No separated stem is trusted
    without the decoded-sum test;
  - temporal overlap therefore serves both as masking that defeats direct
    hashes and as additional evidence for encoder-side factorization.
- Complexity boundary:
  - blind source separation, non-negative/sparse factorization, neural
    separation, cross-occurrence subtraction, and multi-view matching are
    encoder-side proposers only;
  - the decoder remains the same bounded integer emitter sum, Basis transform,
    stochastic field, and Truth composition ISA. No separator model is carried
    as executable code;
  - non-identifiable mixtures fall back to a composite Basis or independent
    Truth. Identifiability is never a conformance assumption.
- Gate:
  - first validate exact/gain reuse on direct observations under R-142;
  - then compare joint latent factorization against direct-mixture Basis reuse
    and optimized Truth on stereo music, orchestra, speech-plus-noise, and
    synthetic mixtures with known ground-truth sources;
  - count model or separator ROM, encoder time, MFT1 bytes, all instance/mix
    parameters, and Truth bytes separately.

## R-145 — Semantic-free partial-spectrum sequence dictionary

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Decision:
  - normative reuse SHALL be discovered from objective waveform or
    time-frequency coefficient sequences, not from labels such as speech,
    phoneme, instrument, note, rain, or ambience;
  - one Basis MAY cover only a bounded band or coefficient support. Matching
    content in one band may be reused even while unrelated simultaneous
    content occupies other bands;
  - semantic and source-separation models MAY propose search regions but their
    labels never enter reconstruction and are not required by the encoder.
- Exact model:
  - a coefficient region is represented as
    `C_region = T(theta, DictionaryBasis) + TruthCorrection`;
  - exact/lossless profiles use a reversible integer analysis/synthesis pair
    and exact integer correction. Magnitude-only equality is insufficient:
    coefficient sign, phase-equivalent alignment, overlap state, and rounding
    are part of the objective region;
  - transformed equality is admitted only through a fixed bounded integer ISA.
    Arbitrary programs or formulas remain prohibited.
- RDO:
  - the encoder searches time scale, band support, Basis, alignment, signed
    gain, and later bounded affine phase/pitch/time laws;
  - it pays analysis mode, band/support signaling, dictionary bytes,
    placement/transform bytes, overlap/checkpoint state, and correction;
  - every coefficient cell has exactly one owner: a transformed Basis,
    stochastic law, source-filter law, transient law, or independent Truth.
    Double payment across representations is prohibited.
- First executable evidence:
  - retain R-142 whole-waveform gain reuse as a control;
  - add a reversible integer multiband oracle that performs semantic-free
    matching and lossless correction independently per band;
  - test a synthetic mixture where only one latent band repeats, then pinned
    speech, tonal music, transient, stochastic, and dense-mix material;
  - no normative opcode is promoted before the partial-band candidate beats
    optimized independent Truth by complete bytes on real evidence and passes
    native resource and R-118 gates.

## R-146 — Phase-complete Basis matching and circular alignment

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Requirement:
  - magnitude or power spectra are phase-invariant proposal keys only. They
    SHALL NOT establish waveform equality or objective reconstruction;
  - Foundry SHALL search complex cross-spectrum or equivalent exact waveform
    correlation for bounded alignment, polarity, and per-band phase relations;
  - a global integer sample shift represents the corresponding linear spectral
    phase ramp. Signed gain represents exact polarity and the 180-degree
    counterphase case. Other phase laws require separately bounded records.
- First executable transform:
  - schema-1 `BASIS_INSTANCE.flags & 1` is `CIRCULAR`;
  - with `CIRCULAR=0`, `source_offset + sample_count` SHALL remain inside the
    Basis as before;
  - with `CIRCULAR=1`, `source_offset` is an exact phase/alignment origin,
    `sample_count` SHALL NOT exceed the Basis length, and sample `n` reads
    `Basis[(source_offset + n) mod BasisLength]`;
  - no other flag is valid. Signed Q1.15 gain is applied after indexing.
- Search:
  - a phase-invariant spectral fingerprint MAY create a broad candidate bucket;
  - encoder-side FFT cross-correlation or an exact equivalent SHALL choose
    bounded top alignment/polarity candidates, followed by fixed-point
    decoder-in-loop gain fitting and complete correction RDO;
  - partial-spectrum analysis performs the same search independently for each
    objectively owned band. It does not require source or sound recognition.
- Gate:
  - native and independent tests SHALL cover arbitrary circular alignment,
    negative-gain counterphase, callback partitioning, invalid flags, exact
    correction, and corruption;
  - evidence SHALL publish the incremental byte effect over R-142/R-145
    gain-only matching. A phase match that increases complete bytes is rejected.

## R-147 — Global cross-channel Basis and transfer trajectories

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Model:
  - dictionary search SHALL span `channel x band x time`. A Basis discovered in
    one input or output channel MAY be placed into any declared emitter and
    routed to any output channel;
  - channel identity is placement/routing metadata, not part of Basis identity.
    Exact timing, phase/alignment, polarity, gain/envelope, and optional bounded
    transfer filtering describe the channel-specific observation;
  - every output channel retains its own objective Truth correction.
- Initial envelope transform:
  - schema-1 `BASIS_INSTANCE.flags & 2` is `LINEAR_GAIN`;
  - the existing gain field is the gain at the first instance sample. The final
    schema-1 `i32`, previously required to be zero, becomes `end_gain_q15`;
  - when `LINEAR_GAIN=0`, `end_gain_q15` SHALL be zero and the start gain is
    constant. When set, the decoder interpolates a canonical signed Q1.15 gain
    trajectory including both endpoints;
  - `CIRCULAR | LINEAR_GAIN` MAY be composed in that canonical order:
    circular/cropped Basis indexing, gain interpolation, then saturating
    emitter addition.
- Later transfer laws:
  - piecewise gain knots, fractional delay, short stable per-band transfer
    filters, and immutable envelope references are admitted only through
    separate complete-byte gates;
  - arbitrary per-channel formulas, unconstrained convolution, and executable
    graphs remain prohibited.
- RDO and evidence:
  - Foundry compares a shared cross-channel Basis against independent channel
    Truth, reversible mid/side or other admitted channel lifting, direct mixed
    Basis reuse, and no-reuse fallback;
  - synthetic tests SHALL cover delayed, counterphase, attenuated, fading, and
    reverberant channel copies. Real gates SHALL preserve native stereo or
    multichannel PCM rather than downmixing;
  - a shared Basis is counted once, while every placement, routing matrix,
    envelope, transfer filter, correction, and operation is counted in full.

## R-148 — Local learned pattern miner as a non-normative proposer

- Status: **HYPOTHESIS — OWNER-REQUESTED EVALUATION**
- Date: 2026-07-27
- Motivation:
  - the first fixed Haar/time-lattice matcher found too few real-speech
    candidates. This is evidence against that matcher, not evidence that speech
    lacks persistent speaker, excitation, formant, or micro-pattern structure;
  - exhaustive search over every duration, band, channel, phase, pitch/time
    law, filter, and overlap is combinatorial. A learned proposer may reduce
    that search without changing the decoder or Truth.
- Proposed pipeline:
  1. a local audio representation model reads original-rate, original-channel
     PCM and emits multiscale label-free embeddings;
  2. GPU approximate-nearest-neighbor search proposes related regions across
     `time x band x channel`;
  3. deterministic DSP fits exact alignment/phase, signed gain/envelope,
     pitch/time law, and bounded transfer filters;
  4. native decoder-in-loop RDO prices Basis, transforms, correction, memory,
     and operations against every admitted fallback.
- Speech:
  - the proposer runs jointly with the causal speaker-local excitation/filter
    model. Persistent vocal-tract/timbre state, pitch/phase trajectories, and
    residual micro-Basis reuse are complementary representations;
  - recognized text, phoneme names, speaker names, and semantic labels are not
    required and never become normative reconstruction state.
- Provider policy:
  - the primary precise proposer is local and operates on original PCM. Cloud
    providers may propose coarse states or boundaries only under the existing
    privacy and policy gate;
  - no AI confidence establishes equality. Exact fixed-point synthesis and
    Truth correction remain the authority, and encoding remains possible with
    no model.
- Gate:
  - compare deterministic spectral hashing, local learned embeddings, and their
    union under the same downstream fitter and complete-byte RDO;
  - report model identity/ROM, GPU time, candidate recall on synthetic known
    transforms, real selected bytes, fallback rate, and held-out generalization.

## R-149 — Complete Foundry search over the declared transform language

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Scope:
  - completeness is defined over an explicit finite MAF hypothesis language,
    not over the infinite set of arbitrary mathematical programs;
  - every Foundry run SHALL publish its searched duration lattice, time cells,
    frequency cells, channels, Basis candidates, representation families,
    transform parameter bounds, composition depth, and resource limits;
  - a claim of exhaustive search is valid only inside those published bounds.
- Foundry completeness:
  - Foundry SHALL evaluate every discrete candidate in the declared search
    space. Fingerprints, embeddings, approximate-nearest-neighbour indices,
    classifiers, and cloud models MAY order work but SHALL NOT remove a
    candidate from a conformance or evidence run;
  - analytically solvable continuous parameters MAY be fitted directly.
    Fixed-point neighbours required by the normative decoder SHALL then be
    evaluated explicitly;
  - every accepted representation SHALL be compared by complete-byte,
    decoder-in-loop RDO against independent Truth and all admitted fallbacks.
- GPU execution:
  - the primary Foundry backend SHOULD evaluate correlation, phase/alignment,
    gain/envelope fits, transform candidates, synthesis, and correction costs
    in deterministic GPU batches;
  - limited device memory changes tile or batch size only. It SHALL NOT change
    candidate membership or the selected result;
  - a portable CPU reference SHALL verify GPU results. Evidence requires exact
    candidate-count parity and selected-candidate parity, with declared
    numeric tolerances only for non-normative ranking scores.
- Profiles:
  - `Foundry` uses the complete declared search and is required for published
    compression claims;
  - `Fast` and `Live` MAY prune or use top-K proposal, but their artifacts and
    reports SHALL be labelled and SHALL NOT be presented as Foundry evidence;
  - normative bitstreams and decoder safety are identical for all encoder
    profiles.
- AI boundary:
  - AI MAY schedule tiles, estimate an efficient execution order, or propose a
    new transform family for a later explicitly bounded experiment;
  - AI SHALL NOT be the sole reason a declared Foundry candidate is skipped.
- Gate:
  - synthetic known-transform recall SHALL be 100% for candidates inside the
    declared lattice;
  - CPU and GPU SHALL agree on candidate counts, fitted fixed-point parameters,
    accepted candidates, decoded PCM, and complete byte totals;
  - reports SHALL include runtime, peak host/device memory, tile dimensions,
    search-space cardinality, and proof that out-of-memory fallback preserves
    the same candidate set.

## R-150 — Hierarchical Basis grammar and low-cost law composition

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Principle:
  - minimum-scale matches are not the final representation. Foundry SHALL test
    whether adjacent or overlapping accepted atoms form a cheaper longer-lived
    Basis, CompoundBasis, motif, source state, or transform trajectory;
  - analysis SHALL run independently on every declared scale from the original
    signal. Selecting or discovering a micro-atom SHALL NOT claim its samples,
    suppress an overlapping span, or prevent direct discovery of a longer
    pattern;
  - a compound MAY contain raw immutable samples, existing Basis references,
    transformed instances, or previously admitted compounds. Dictionary
    entries therefore form a bounded acyclic grammar rather than a flat table;
  - the same merge process is repeated across declared scales and grammar
    depths, so a useful larger structure may itself become part of a still
    larger structure.
- Transform-law composition:
  - Foundry SHALL test whether per-instance increments can be replaced by one
    low-cost state law: constant or piecewise gain, phase/frequency increment,
    bounded pitch/time mapping, envelope/filter trajectory, cross-channel
    transfer, repetition, crop, or another explicitly admitted MAF operation;
  - equivalent existing Basis/CompoundBasis entries SHALL be considered for
    unification before a new dictionary payload is created;
  - arbitrary executable formulas and cyclic dictionary dependencies remain
    prohibited.
- Selection:
  - the objective is complete bytes plus declared decode resources and exact
    Truth cost. A merge is accepted only when the complete independently
    decodable stream is cheaper than all unmerged alternatives at the same
    distortion;
  - Foundry SHALL use an exhaustive bounded chart/dynamic-programming search
    over the declared atom sequence, merge spans, transform families, and
    grammar depth. A greedy first-match merge is not sufficient evidence;
  - the chart receives direct large-span candidates, bottom-up compounds,
    overlapping micro-atoms, persistent physical states, and Truth at the same
    decision stage. Only the global complete cost assigns ownership;
  - admissible lower bounds MAY avoid materializing a candidate only when they
    mathematically prove it cannot beat the current complete cost. Such a
    proof preserves search completeness and SHALL be reported.
- GPU execution:
  - pair/span scoring, transform composition, correction-energy evaluation,
    and chart cells SHOULD be evaluated in deterministic GPU tiles;
  - VRAM pressure changes tile residency only. Host spill and recomputation
    preserve the same chart and selected grammar.
- Gate:
  - synthetic tests SHALL cover two micro-atoms combining into a larger exact
    motif, repeated transformed compounds, unification with an existing Basis,
    a misleading locally cheap merge rejected by the global optimum, and a
    no-merge fallback;
  - evidence SHALL publish atom, span, transform, and grammar candidate counts,
    selected hierarchy, complete bytes at every level, exact decoded PCM, and
    CPU/GPU parity for a bounded corpus.

## R-151 — STEP M-151: Complete Pattern Field

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED**
- Date: 2026-07-27
- Purpose:
  - this step converts the accepted motif-orbit discussion into one auditable
    implementation program. A research oracle, isolated opcode, synthetic
    example, or candidate-count claim does not complete a mechanism;
  - "complete" or "exhaustive" always means every candidate in a published
    finite hypothesis language. Resonith SHALL NOT claim to search the
    unbounded set of all mathematical descriptions of an arbitrary signal.
- Pattern-search contract:
  - Foundry SHALL analyze every declared time origin, duration, frequency cell,
    channel, phase/alignment, transform tuple, representation family, and
    grammar depth from the original signal;
  - exact content matches and content-defined boundaries complement the
    declared multiscale lattice. They do not replace it;
  - discoveries at one scale SHALL NOT claim samples, prune overlapping
    candidates, or suppress independent discovery at another scale;
  - deterministic hashes, learned embeddings, and cloud analysis MAY order
    work. They SHALL NOT remove candidates from a complete Foundry run;
  - GPU memory changes deterministic tile residency only. CPU and GPU
    candidate membership and fixed-point results SHALL agree.
- Required transform language:
  - exact placement, crop, integer alignment, circular phase, polarity,
    constant and piecewise gain/envelope;
  - bounded pitch resampling, bounded time mapping, fractional phase,
    spectral/formant envelope, reverse, loop, and short stable
    resonator/transfer filtering;
  - cross-band and cross-channel placement with delay, phase, decay/envelope,
    and admitted transfer laws;
  - transform parameters and compositions are bounded integer records. An
    arbitrary executable program is never a Basis transform.
- Required representation competition:
  - exact and transformed Basis, CompoundBasis, source-filter, stochastic
    field, transient, channel lifting/transfer, and independent Truth enter one
    global quality-constrained RDO;
  - repeated transform increments SHALL compete with a persistent state law;
  - adjacent and overlapping atoms SHALL compete with direct large-span
    candidates and bounded hierarchical merges;
  - dictionary activation, every instance and parameter, entropy state,
    correction, checkpoints, memory, and decode operations are priced in full;
  - lossless selection requires exact PCM. Lossy selection requires the
    declared quality floor and SHALL reject a smaller but materially degraded
    candidate. Independent Truth is always available.
- Required evidence:
  - synthetic tests prove recall for every admitted transform, cross-channel
    law, scale, overlap, hierarchy, and deliberately misleading greedy case;
  - real diagnostics publish raw PCM bytes, complete stream bytes, prediction
    quality, corrected quality, fallback bytes, candidate counts, runtime,
    peak host/device memory, and CPU/GPU parity;
  - a material milestone runs the complete R-118 union: the three full
    references and all sixteen R-111 classes. Each item compares audio decoded
    from the original, Resonith, and current official Opus artifacts;
  - reports include complete bytes plus applicable SNR, log-mel, STOI/ESTOI,
    transient/pre-echo, spatial/channel, runtime, and resource metrics. Quality
    and rate are evaluated together; byte count alone cannot admit a mode.
- Completion gate for each checklist item:
  1. bounded syntax and deterministic C++23 decoder behavior;
  2. native C++23 encoder/search implementation, with CUDA for parallel heavy
     kernels and a portable CPU reference;
  3. exact Truth correction and independent fallback;
  4. conformance, corruption, resource, CPU/GPU parity, and portability tests;
  5. Orkela backend playback of the emitted stream;
  6. full R-118 original/Resonith/Opus evidence with listening artifacts;
  7. matching version, changelog, hashes, and public repository evidence.
- Immediate order:
  - first integrate the multiscale complete search, global chart, and exact
    fallback so subsequent transform families share one honest judge;
  - then complete the transform, partial-spectrum, stochastic, source-filter,
    transient, mixture, cross-channel, learned-proposer, and persistent-law
    rows without weakening the search contract;
  - update Orkela and rerun the full evidence gate before any promotion claim.

## R-152 — Gemini byte-pattern proposer A/B gate

- Status: **HYPOTHESIS — OWNER-REQUESTED IMMEDIATE TEST**
- Date: 2026-07-27
- Question:
  - can Gemini 3.6 Flash discover reusable transformations more effectively
    from a canonical PCM16 byte/number sequence than the current deterministic
    encoder proposer?
- Fair comparison:
  - Gemini receives no audio MIME, transcript, source label, or musical
    description. It receives numbered fixed-length PCM16 blocks encoded as
    deterministic numeric or hexadecimal text and the exact finite transform
    language;
  - the native Foundry evaluates the identical blocks and every ordered
    pair/circular-phase/constant-or-linear-Q1.15-gain candidate;
  - Gemini returns structured candidate indices and parameters. The local
    fixed-point evaluator verifies every proposed candidate and rejects
    invented, out-of-range, or numerically incorrect results;
  - evidence reports exact-match precision, eligible-candidate recall, best
    per-target recall, valid-parameter rate, request bytes/tokens, latency, and
    native CPU/GPU time.
- Integration rule:
  - a positive result may add Gemini output to the proposer union or use it to
    schedule GPU tiles;
  - Gemini output SHALL NOT establish equality, replace decoder-in-loop RDO,
    remove a candidate from Foundry, or become necessary for encoding;
  - credentials remain outside the repository and uploaded test material is
    limited to owner-authorized evidence inputs.

## R-153 — GPT-5.6 Sol maximum-compute byte-pattern A/B gate

- Status: **BLOCKED BY PROVIDER MODEL ACCESS — TEST REMAINS READY**
- Date: 2026-07-27
- Configuration:
  - use the OpenAI Responses API model `gpt-5.6-sol`;
  - use the highest documented single-response quality configuration:
    `reasoning.effort=max` and `reasoning.mode=pro`;
  - the Codex product label `Ultra` is not recorded as an API reasoning-effort
    value. The evidence SHALL name the actual API configuration rather than
    relabel it.
- Fairness:
  - send the same PCM16LE hexadecimal cases, finite transform language,
    structured output schema, thresholds, and local CUDA verifier used by
    R-152;
  - compare eligible-relation precision/recall, best-target recall, exact Q15
    parameter rate, latency, and token usage against Gemini 3.6 Flash and
    native Foundry;
  - provider output remains an untrusted proposer and cannot prune Foundry.
- Execution result on 2026-07-27:
  - the configured OpenAI project returned HTTP `403 model_not_found` before
    inference because it does not have access to `gpt-5.6-sol`;
  - no Sol output, latency, token usage, precision, or recall value therefore
    exists. This access failure SHALL NOT be represented as a model loss;
  - the identical request builder, schema, cases, and local CUDA verifier are
    retained. The gate SHALL be rerun without code or prompt changes when the
    selected API project gains access;
  - available realtime models are not substituted because that would compare
    a different model class and invalidate the A/B.

## R-154 — Blind Codex GPT-5.6 Sol Ultra proposer gate

- Status: **MEASURED — HIGH-RECALL PROPOSER; NOT AN EXACT FITTER**
- Date: 2026-07-27
- Boundary:
  - because the configured Responses API project cannot access
    `gpt-5.6-sol`, an isolated Codex sub-agent using model `gpt-5.6-sol` and
    product reasoning effort `Ultra` MAY be measured as a separate execution
    surface;
  - this result SHALL NOT be labelled a Responses API `max`/`pro` result.
    R-153 remains blocked until the API project itself gains model access.
- Blindness and fairness:
  - the agent receives only the frozen R-152 provider-neutral prompt,
    PCM16LE hexadecimal blocks, finite transform language, and threshold;
  - it MUST NOT read Gemini output, CUDA/native results, the WAV source, or
    any codec report;
  - its structured candidates are scored after completion by the unchanged
    local R-152 fixed-point CUDA authority;
  - the report compares relation precision/recall, best-target recall, and
    exact Q1.15 parameter rate. No self-reported explanation is evidence.
- Integration rule:
  - as with every learned provider, a positive result may add proposals or
    scheduling hints but may never establish equality, prune Foundry, or
    become required for encoding or decoding.
- Measured result:
  - on the synthetic exact-law case, Sol Ultra recalled `24/24` eligible
    relations and every best target; Gemini recalled `8/24`;
  - on the real EBU speech-byte case, Sol Ultra recalled `172/172` eligible
    relations and every best target; Gemini recalled `3/172` and no best
    target;
  - Sol Ultra precision was `57.14%` on synthetic and `58.90%` on speech,
    versus Gemini `66.67%` and `25.00%`;
  - exact Q1.15 transform parameters remained weak: `0/24` on synthetic and
    `18/172` on speech. Therefore Sol may propose relations, but the native
    fixed-point fitter and complete CUDA search remain mandatory;
  - the frozen R-152 authority explicitly excludes later reverse-transform
    candidates because reverse was not described in the blind provider
    prompt.

## R-155 — Bounded fractional Basis warp instance

- Status: **NORMATIVE-DRAFT — STEP M-151 TRANSFORM EXPANSION**
- Date: 2026-07-27
- Purpose:
  - schema-1 integer placement cannot express fractional phase, pitch
    resampling, bounded time stretch, or a continuous pitch/time trajectory;
  - these transforms are required to test whether one objective micro-Basis
    can replace many related speech, music, and cross-channel fragments
    without semantic labels.
- New record:
  - add `BASIS_WARP_INSTANCE` as record type 8 rather than changing the
    already executable schema-1 `BASIS_INSTANCE`;
  - canonical schema-1 payload:

```text
u16 instance_id
u16 emitter_id
u16 basis_id
u16 flags: bit 0 CIRCULAR, bit 1 LINEAR_GAIN, bit 2 LINEAR_STEP
u32 output_start
u32 output_sample_count
i32 source_position_q16
i32 source_step_start_q16
i32 source_step_end_q16
i32 start_gain_q15
i32 end_gain_q15
```

- Deterministic synthesis:
  - the source coordinate is signed Q16.16. One source sample per output
    sample is `65536`; negative steps express reverse playback;
  - source step is constant unless `LINEAR_STEP` is set. A linear law is
    evaluated from the absolute instance-local output index with one closed
    integer expression, so callback partitioning cannot accumulate drift;
  - schema-1 uses fixed two-tap linear interpolation with signed
    ties-away-from-zero rounding. Integer coordinates reproduce the selected
    Basis sample exactly;
  - circular instances use Euclidean modulo. Non-circular instances require
    every source coordinate to remain inside `[0, basis_samples - 1]`;
  - constant and linear signed Q1.15 gain retain the existing normative
    rounding and saturation rules.
- Bounds:
  - `abs(source_step_q16) <= 8 * 65536`;
  - one warp instance contains at most 65535 output samples; longer laws are
    split at canonical absolute positions without decoder-state carry;
  - a linear step cannot cross zero inside one instance; a reversal is split
    into separate instances;
  - `LINEAR_STEP` requires at least three output samples and
    `LINEAR_GAIN` requires at least two;
  - warp and integer instances share the Main limit of 4096 placements and
    are preflighted against declared operation and memory bounds.
- Admission:
  - the record is not a compression claim. It must first pass native/Python
    parity, callback partition, corruption, resource, Android/iOS compile,
    exact Truth correction, Orkela playback, and the complete R-118 gate;
  - the encoder SHALL compare complete Basis, instance, correction, entropy,
    checkpoint, and operation cost against independent Truth. A warped
    prediction that is larger or worse is rejected.

## R-156 — Gridless Multiscale Pattern Field

- Status: **NORMATIVE-DRAFT — PRIMARY ENCODER STEP**
- Date: 2026-07-27
- Decision:
  - Resonith SHALL NOT make a fixed analysis block, transform frame, or CUDA
    tile the semantic unit of an acoustic pattern;
  - normative Basis instances remain events with arbitrary integer
    `output_start` and `output_sample_count`. Implementation tiles MAY batch
    analysis, entropy, checkpoints, and rendering, but their boundaries SHALL
    NOT restrict candidate onset, duration, frequency support, or composition;
  - this is the **gridless meaning, tiled execution** contract.
- Required discovery union:
  1. rolling exact fingerprints at every source-sample origin for every
     declared exact duration, followed by byte/sample verification;
  2. content-defined anchors derived from original PCM independently on every
     declared channel and perfect-reconstruction frequency cell;
  3. overlapping regular origins at every declared duration scale, with the
     hop and origin set published in the run manifest;
  4. cross-channel and cross-band candidates whose intervals may start and end
     at different implementation-tile positions;
  5. direct longer spans and bottom-up `CompoundBasis` spans, neither of which
     may be removed because shorter candidates were found first.
- Anti-blindness:
  - a pattern crossing one or many analysis-tile boundaries remains eligible;
  - discovery at one scale cannot claim samples or suppress overlapping,
    nested, shifted, longer, shorter, cross-band, or cross-channel candidates;
  - fingerprints, embeddings, Gemini, and other learned proposers MAY schedule
    work but SHALL NOT establish equality or remove a declared Foundry
    candidate;
  - only the global complete-cost interval/field selector assigns ownership.
- Evidence:
  - the R-155 fixed lattice checked 18,494 transformed pairs at 4,096 samples
    and 49,924 pairs at 1,024 samples on the complete Mozart reference but
    selected zero Basis instances at the two-percent fit limit;
  - both complete candidates therefore collapsed to a 104-byte empty MFT1
    predictor plus Truth and measured 7,003,168 bytes, versus the 6,521,233-byte
    stable reference. All R-135 quality checks passed, so the failure isolates
    discovery and complete-byte economics rather than decoder correctness;
  - these runs are retained as the fixed-grid A/B baseline, not promoted as
    the new algorithm.
- Completion gate:
  - synthetic spans beginning at every possible offset around a tile boundary
    MUST have identical recall to spans wholly inside a tile;
  - CPU results MUST be invariant to tile size and thread order;
  - at least one real speech, tonal, transient, stochastic, dense-mix, and
    multichannel item MUST emit active arbitrary-interval Basis candidates;
  - exact Truth, full-byte RDO, complete R-118 evidence, and Orkela playback
    remain mandatory before promotion.

## R-157 — Batched CUDA Warp Foundry

- Status: **NORMATIVE-DRAFT — FOLLOWS R-156 CANDIDATE GENERATION**
- Date: 2026-07-27
- Decision:
  - move the expensive R-155 transform fitter from per-candidate Python/NumPy
    calls into large C++23/CUDA batches;
  - the finite lattice includes every declared direction, integer and
    fractional phase, signed constant/linear gain, bounded constant/linear
    pitch/time step, and every explicitly declared fixed-point neighbour;
  - CUDA batching MAY change residency and evaluation order but SHALL NOT
    reduce candidate membership. Python remains only the experiment manifest,
    orchestration, and report layer.
- Required proof:
  - one portable CPU reference and the CUDA backend produce identical selected
    parameters, reconstructed PCM, squared error, and candidate cardinality;
  - results are invariant to CUDA tile size, host spill boundaries, and
    callback/render partitioning;
  - every accepted warp is decoded by the normative C++23 Core before rate or
    quality scoring;
  - GPU failure falls back to the same finite CPU search or a clearly labelled
    `Fast` profile, never to a silently pruned Foundry result.
- Implemented evidence:
  - the C++23 C ABI exposes complete warp cardinality plus portable CPU and
    CUDA execution for ordered pairs, fractional phase, both directions,
    bounded constant/linear pitch-time step, and constant/linear signed gain;
  - an RTX 2080 Super / NVRTC 13.3 gate evaluated `6,912/6,912` candidates in
    unequal `4,099 + 2,813` tiles. Every 48-byte result record was identical
    between CPU and CUDA, and a known fractional-phase, linearly changing
    pitch-time law produced zero correction;
  - the Python 3.14 layer only declares tiles and consumes fixed result
    records. It performs no per-candidate transform, gain fit, synthesis, or
    squared-error loop;
  - the first integrated gridless exact-RDO diagnostic evaluated
    `7,168/7,168` candidates, selected one immutable Basis with eight
    arbitrary placements, reconstructed PCM exactly, and measured 704 bytes
    versus 1,156 bytes for independent lossless Truth (`-39.10%`). This is a
    favorable synthetic construction and is not an Opus or real-audio claim.

## R-158 — Multiscale economic lifetime gate

- Status: **NORMATIVE-DRAFT — REQUIRED BEFORE WHOLE-FILE PROMOTION**
- Date: 2026-07-27
- Evidence that changes the next implementation:
  - the first R-157 Fast structural union evaluated
    `21,012,480/21,012,480` declared candidates on all 19 R-118 content types
    in 103.122 seconds;
  - short 64-sample search found from zero to 691,200 fit-eligible
    relationships per item, including speech, tonal, transient, stochastic,
    dense, and multichannel material, but complete byte RDO selected
    independent exact Truth for all `19/19` items;
  - therefore relationship recall is no longer the immediate limiter. Flat
    micro-Basis activation, placement, and correction cost is.
- Decision:
  - every next gate SHALL search direct original-PCM spans independently at
    64, 256, and 1,024 samples before whole-file encoding;
  - longer direct spans and bottom-up CompoundBasis candidates SHALL remain in
    the same global chart as micro-spans. Finding a short relation cannot
    remove, claim, or synthesize a longer one;
  - one persistent transform law MAY replace consecutive compatible
    placements only when its exact rendered PCM plus correction and complete
    signalling cost less than the unmerged path;
  - Fast diagnostics MAY declare fewer content/regular origins at longer
    scales to bound wall time, but SHALL publish every origin and evaluate
    100% of the resulting finite lattice. Such a run is not a whole-file
    Foundry claim;
  - whole-file lossy/Opus work begins only after a real corpus item activates
    a structured span under actual complete-byte exact RDO, or an ablation
    proves that lossy correction changes that conclusion without violating
    the R-118 quality floor.

## R-159 — Latent Source Pattern Field

- Status: **NORMATIVE-DRAFT — OWNER-DIRECTED PRIMARY R-158 MECHANISM**
- Date: 2026-07-27
- Decision:
  - the Foundry encoder SHALL search reusable patterns both in observed
    channels and in objective latent additive layers inferred from changing
    mixtures;
  - a layer is not an instrument, speaker, phoneme, note, or environmental
    label. It is only a decoder-verifiable term in
    `Y_c(t) = sum_i Route_ci(t) Transform_i(Basis_i, t) + Truth_c(t)`;
  - every inferred layer is searched independently by the same gridless,
    multiscale, phase-aware, cross-channel R-156/R-157 dictionary machinery.
- Candidate union:
  1. direct observed-channel patterns remain mandatory;
  2. complex time-frequency factorization SHALL retain magnitude, phase and
     cross-channel transfer evidence rather than separating magnitude alone;
  3. cross-occurrence robust consensus SHALL infer a recurring component from
     several differently overlapped observations;
  4. layer counts, origin sets, transform families, factorization iterations,
     and fixed-point neighbours form a published finite language;
  5. direct mixtures, composite Basis candidates, every inferred layer family,
     and independent Truth coexist in the global selector. A separator cannot
     remove a direct candidate.
- Exactness and safety:
  - source recovery is not assumed identifiable. Two physical decompositions
    may explain the same PCM, and neither semantic explanation is normative;
  - each complete candidate is rendered by the bounded MAF decoder, summed in
    its normative order, and corrected by Truth. Lossless admission requires
    exact PCM; lossy admission requires all R-118 quality floors;
  - if factorization is wrong, its dictionary, route, transform and correction
    bytes make it lose to a composite Basis or independent Truth.
- First implementation:
  - add a deterministic encoder-side latent-layer oracle using multiscale
    complex spectral signatures, bounded phase/alignment and gain fitting,
    robust cross-occurrence consensus, iterative residual peeling, and
    cross-channel routing;
  - CUDA performs the declared warp/phase/gain lattice. Python declares the
    layer language and orchestrates reports only; it is not shipped;
  - publish a synthetic changing-overlap recovery gate before making any
    bitrate claim, then run speech-plus-noise, stereo music, orchestra,
    ambience and the full R-118 union.
- Completion gate:
  - demonstrate at least one mixture where no direct mixed chunk repeats but a
    decoder-verifiable latent Basis is reused under different overlaps;
  - compare direct-mixture dictionary, latent-layer dictionary and independent
    Truth by complete bytes and decoded quality;
  - report latent candidate recall, correction energy/bytes, route bytes,
    wall time, peak CPU/GPU memory, and exact reconstruction hash.

## R-160 — Minimum-Description Anonymous Field Grammar

- Status: **NORMATIVE-DRAFT — PRIMARY LSPF INTEGRATION CONTRACT**
- Date: 2026-07-27
- Problem:
  - source separation, shift-invariant sparse coding, convolutive/NMF
    dictionaries, sinusoidal/stochastic models, long-term prediction and neural
    codebooks already demonstrate important parts of the proposed mechanism;
  - they do not by themselves define a universal codec whose decoder receives
    anonymous reusable fields, discontinuous long motifs, finite transform
    laws, cross-channel routes and one final exact correction selected by full
    serialized cost;
  - physical source recovery is non-identifiable, unrestricted sparse search is
    combinatorial, and arbitrary transform programs would merely hide a second
    codec inside each file.
- Decision:
  - Resonith SHALL optimize a minimum-description explanation of PCM, not claim
    to recover the true speaker, instrument or environmental source;
  - an anonymous field is a decoder-verifiable additive component with a
    reusable immutable Basis dictionary, persistent transform/route laws and a
    sparse event ledger;
  - a long motif MAY join non-adjacent observations. Unrelated or overlapping
    events between its steps remain independent, so `A -> gap -> B` is one
    legal motif without requiring the entire mixture between A and B to repeat;
  - a long macro SHOULD normally be a DAG/grammar of smaller Basis references
    and laws. Raw long PCM Basis payloads are admitted only when their complete
    amortized byte cost wins;
  - analysis boundaries are gridless and multiscale. CUDA tiles, entropy pages
    and checkpoints are implementation details and SHALL NOT restrict event
    onset, duration, partial-spectrum support or motif boundaries;
  - the initial finite law language is `literal`, `constant`, `affine`,
    `run-length` and `sparse-exception`. The decoder transform ISA remains
    fixed, bounded and non-Turing-complete;
  - partial-spectrum components SHALL be represented by
    perfect-reconstruction integer lifting pairs; magnitude-only subtraction is
    forbidden. Integer sample alignment is non-circular, and fractional
    phase claims require a separately tested normative transform;
  - routes MAY reuse one Basis across channels with gain, phase, delay and
    bounded filter laws. The summed rendering receives one final Truth
    correction; each hypothetical source SHALL NOT pay an independent exact
    correction.
- RDO:
  - direct channel patterns, anonymous fields, composite Basis, stochastic
    fields, source-filter atoms, transient atoms and independent Truth compete
    in one global selector;
  - admission is determined by the complete decoder-produced stream size and
    the R-118 quality contract, including dictionary, event, route, law,
    checkpoint, entropy and correction bytes;
  - event-ledger compression is evidence about grammar signalling only and
    SHALL NOT be reported as complete audio compression.
- First exact evidence:
  - a synthetic changing-overlap signal with no exactly repeated mixed block
    reused one 128-sample anonymous Basis ten times with varying gains and
    sparse contamination;
  - the exact prototype reconstructed identical PCM by SHA-256 and cost
    1,815 bytes versus a 2,491-byte independent lossless proxy, a 676-byte
    or 27.14% proxy reduction;
  - the same RDO rejected a short candidate that cost 49 bytes more than
    independent Truth;
  - the R-160 event grammar exactly round-tripped a 24-occurrence cross-channel
    `token 0 -> affine gap -> token 7` motif while preserving unrelated
    intervening events and selected it only when its actual serialized ledger
    was smaller;
  - these are **Synthetic / Proxy** results, not Opus, FLAC or full Resonith
    wins.
- First real diagnostic:
  - exact reversible partial-spectrum search on 12 seconds of EBU dense
    orchestra admitted two anonymous Basis entries with 1,082 occurrences and
    explained 55.24% of waveform energy;
  - its complete exact structural proxy cost 1,296,657 bytes versus 1,302,123
    independent proxy bytes, a 5,466-byte or 0.42% reduction;
  - a phase-preserving anonymous NMF proposer found one 40-occurrence field on
    three seconds of EBU female speech, but the structured candidate cost
    190,025 versus 189,099 bytes, so RDO selected independent Truth;
  - this is **Real PCM / Fast diagnostic / Proxy**, not a FLAC, Opus or final
    Resonith result. It proves that explained energy is not sufficient;
    correction entropy and complete overhead are the blocking quantities.
- Kill gates:
  - changing-overlap synthetic: at least 15% complete-stream reduction versus
    the best direct-dictionary/Truth path;
  - anonymous-field correction: no more than 50% of the independent covered
    cost, and the latent path must beat the direct dictionary by at least 5%;
  - blind inference: within 15% of a known-stem oracle on controlled mixtures;
  - real lossless corpus: at least 5% median complete-byte improvement over the
    best current Truth/FLAC anchor before standard promotion;
  - perceptual corpus: first gate at no more than 90% of matched-quality Opus;
    the research target remains 60%, never a guaranteed universal ratio;
  - Foundry gate: no more than 30x track duration and 7 GiB encoder VRAM for the
    declared profile; CPU-only bounded decode and seek pre-roll remain required.
- Novelty status:
  - the combination is a research candidate, not a novelty or patent claim;
    formal prior-art and freedom-to-operate searches remain mandatory before
    such a claim or a standards submission.

## R-161 — LSPF Priority Lock and Evidence-Carrying Generations

- Status: **ACCEPTED — OWNER-DIRECTED HIGHEST PRIORITY**
- Date: 2026-07-27
- Priority:
  - Latent Source Pattern Field is the only active compression-architecture
    priority until every R-161 work package has either passed its gate or been
    explicitly rejected by complete evidence;
  - unrelated player polish, container expansion, provider integration,
    marketing, and speculative syntax SHALL NOT displace an open LSPF gate;
  - Orkela work remains mandatory only where it produces the listening,
    inspection, and release artifact for the current verified codec
    generation.
- Required implementation order:
  1. convolutive anonymous fields;
  2. bounded pitch, time, phase, formant, envelope, and route laws;
  3. persistent source-filter, stochastic, transient, and cross-channel
     competition inside every observed or anonymous field;
  4. multiple sparse motif definitions, arbitrary-gap CompoundBasis DAGs, and
     persistent parameter laws;
  5. correction-entropy-driven global RDO over every dictionary, event, route,
     law, checkpoint, final Truth, and independent fallback byte;
  6. C++23/CUDA Foundry execution with portable fixed-integer CPU parity and
     the unchanged bounded decoder;
  7. the complete R-118 quality/byte frontier and only then syntax promotion.
- Non-negotiable selection rule:
  - explained energy, separation quality, semantic plausibility, or proposer
    confidence cannot promote a mechanism;
  - a candidate first satisfies exact reconstruction or the applicable R-118
    quality floors, then wins by actual complete bytes and bounded decode cost;
  - only the final mixture-domain Truth correction is authoritative.
- Evidence-carrying generation:
  - every material work package SHALL produce an English machine report,
    configuration, input/output hashes, wall time, resource use, ablation,
    previous-Resonith comparison, and current official Opus anchor where a
    perceptual comparison is meaningful;
  - every generation SHALL retain the original input, actual decoded Resonith
    PCM, encoded `.resonith`, actual decoded Opus PCM, and complete `.opus`
    anchor in a stable generation directory;
  - Orkela SHALL be updated to decode and inspect the promoted generation
    before a release may be tagged. The report SHALL link the exact local
    player executable and every listening artifact;
  - Fast diagnostics MAY use a declared subset, but are never a milestone,
    release, or general compression claim;
  - every material milestone SHALL run the complete three-reference plus
    sixteen-class R-118 union, including full-length Mozart.
- Failure policy:
  - losing candidates remain research evidence or are removed; they do not add
    normative opcodes;
  - no work package is declared complete while encoded listening files,
    released-decoder output, Orkela compatibility, or required R-118 rows are
    missing;
  - ideas discovered during implementation are recorded immediately, but do
    not interrupt the active gate unless they change its mathematical validity
    or are required to prevent irreversible syntax error.

## R-162 — Simultaneous Short- and Long-Duration Adaptation Gate

- Status: **ACCEPTED — MANDATORY FOR EVERY LSPF WORK PACKAGE**
- Date: 2026-07-27
- Decision:
  - every material LSPF mechanism SHALL be evaluated on short and long inputs
    in the same generation;
  - short inputs diagnose onset, phase, transient, boundary, local transform,
    low-latency, and parameter-fit behavior;
  - long inputs of at least 120 seconds diagnose dictionary amortization,
    persistent-law drift, long motifs, checkpoint/index cost, memory growth,
    random access, throughput, and fallback stability;
  - a short pass cannot substitute for a long pass, and a long average cannot
    hide a short transient, speech-intelligibility, or boundary failure.
- Automatic adaptation:
  - Live, Studio, and Foundry are encoder search/resource policies over one
    decoder and one syntax family;
  - the encoder SHALL derive a deterministic analysis plan from duration,
    sample rate, channels, latency target, memory limit, signal structure, and
    requested quality;
  - duration MAY change scale union, candidate residency, checkpoint cadence,
    dictionary lifetime, search depth, and parallel scheduling;
  - duration SHALL NOT disable exact fallback, quality floors, corruption
    bounds, or decoder conformance;
  - automatic decisions and every candidate family enabled or skipped SHALL be
    published in the generation manifest.
- Minimum evidence:
  - Fast development pairs each short diagnostic with at least one continuous
    input of 120 seconds or longer;
  - a material milestone still requires the complete full-length speech,
    Emotional piano, 400.773-second Mozart, and all sixteen R-111 classes under
    R-118;
  - both per-file rows and duration-bucket aggregates SHALL be published. No
    average-only result is sufficient.

## R-163 — Duration-Pareto Preservation

- Status: **ACCEPTED — MANDATORY FOR AUTOMATIC ADAPTATION**
- Date: 2026-07-27
- Decision:
  - a mechanism that wins on long material by complete bytes at the applicable
    quality floor, or by quality at an equal complete-byte budget, SHALL remain
    an available RDO candidate while short-material behavior is improved;
  - short-track tuning SHALL add or refine a duration-specialized search plan.
    It SHALL NOT remove, weaken, or silently retune a proven long-track branch;
  - the reciprocal rule applies to a proven short-track branch.
- Selection:
  - the encoder always evaluates the applicable incumbent, new specialized
    candidate, and independent Truth/fallback under the same decoder-produced
    byte and quality accounting;
  - a new default is selected per input, never by an average that hides a
    duration-bucket regression;
  - exact lossless candidates compare complete bytes. Lossy candidates first
    pass per-item quality floors and then compare complete bytes; equal-byte
    quality claims require a declared equivalence budget and the full metric
    panel.
- Evidence:
  - every generation manifest records the incumbent candidate identifier,
    duration class, all evaluated alternatives, rejection reason, and selected
    winner;
  - short, medium, and long Pareto frontiers are retained independently;
  - long-only success is a valid retained capability, not a failed experiment.
    It is not promoted as a universal win until the other declared duration
    classes pass their own gates.

## R-164 — Long-First Gate and Dual-Axis Success

- Status: **ACCEPTED — OWNER-DIRECTED TEST ORDER**
- Date: 2026-07-27
- Execution order:
  1. run every generation on the declared continuous long inputs first;
  2. freeze the long-input result, configuration, metrics, hashes, stream, and
     Pareto candidates;
  3. only then run the short corpus and tune a short-specialized search plan;
  4. rerun any affected long candidate before changing a shared default.
- Success criterion for one duration bucket:
  - **rate success:** lower decoder-produced complete bytes while every
    applicable quality floor remains satisfied; or
  - **quality success:** objectively and, for a promotion claim, subjectively
    better quality inside the declared matched-complete-byte tolerance.
- Retention:
  - either success axis makes the generation a retained successful Pareto
    candidate; improvement on both axes is preferred but not required;
  - a rate/quality trade-off outside the declared equivalence tolerance is
    retained and labelled as an alternative operating point, not silently
    installed as the universal default;
  - failure on short material cannot erase a long-material success, and
    short-material success cannot erase the frozen long incumbent.
- Reporting:
  - reports SHALL be written in actual execution order: long rows and frozen
    frontier first, short rows and tuning second, final per-duration selection
    last;
  - byte equivalence tolerance, metric deltas, quality floors, and listening
    protocol SHALL be declared before the comparison.

## R-165 — Dual-Axis Refinement Before Generation Freeze

- Status: **ACCEPTED — OWNER-DIRECTED COMPLETION RULE**
- Date: 2026-07-27
- Decision:
  - a first pass that wins only rate or only quality SHALL immediately trigger
    a bounded refinement pass targeting the missing axis before the generation
    is frozen;
  - after a rate-only win, the encoder tunes representation, allocation,
    correction, entropy, and operating point to improve quality without losing
    the rate success;
  - after a quality-only win, it tunes state reuse, signalling, correction
    entropy, allocation, and operating point to reduce complete bytes without
    losing the quality success.
- Completion:
  - a two-axis win may be frozen immediately after verification;
  - a one-axis win may be frozen only after the declared refinement lattice,
    time/resource budget, and stop conditions have been exhausted and recorded;
  - the surviving one-axis win remains a successful Pareto candidate. Failure
    to improve the second axis does not erase it.
- Evidence:
  - the generation report SHALL contain the initial winning point, every
    refinement candidate, both axis deltas, rejection reasons, selected final
    point, and whether the refinement budget was exhausted;
  - no release version or fixed generation identifier is assigned while a
    required dual-axis refinement pass is still open.

## R-166 — Maximum-Effort Official Opus Anchor

- Status: **ACCEPTED — MANDATORY EXTERNAL ANCHOR**
- Date: 2026-07-27
- Decision:
  - every real-audio material generation SHALL include the current project-
    pinned official libopus encoder and decoder at their strongest lawful
    offline settings;
  - `OPUS_SET_COMPLEXITY(10)` is mandatory. The anchor search SHALL also
    evaluate all applicable application, signal, frame-duration, bandwidth,
    VBR/constrained-VBR, channel, and file-coding controls that can improve the
    measured point without changing the source or comparison contract;
  - bitrate is searched against the declared complete-byte target or quality
    target. One convenient preset is not an adequate anchor.
- Selection:
  - every Opus candidate is decoded by the official decoder;
  - the winning Opus point is chosen by the same predeclared quality floors,
    complete-container bytes, objective panel, and listening protocol used for
    the Resonith comparison;
  - encoder delay, pre-skip, sample count, channel mapping, metadata, and
    container overhead are included consistently.
- Evidence:
  - reports retain the complete Opus search configuration, rejected points,
    winning `.opus`, decoded PCM, hashes, encoder/decoder versions, and wall
    time;
  - a lossless structural proxy MAY report Opus as contextual evidence but
    SHALL NOT rank lossy Opus bytes against lossless exact bytes as a codec
    victory;
  - if the official pinned Opus version changes, anchors are regenerated before
    any current comparative claim.

## R-167 — Coherent Partial Bundle Dictionary

- Status: **ACCEPTED — REQUIRED LSPF ANALYTIC CANDIDATE**
- Date: 2026-07-27
- Decision:
  - LSPF SHALL search repeated coherent spectral bundles in addition to direct
    waveform, transform, anonymous-field, source-filter, stochastic, transient,
    and Truth candidates;
  - a bundle is an unnamed group of partials whose frequency ratios,
    amplitude/envelope evolution, phase trajectories, and channel routes are
    jointly predictable. It is not required to be labelled as a voice or
    instrument;
  - one immutable `PartialBasis` stores normalized partial ratios, complex
    phase relations, spectral/formant envelope, and optional inharmonic offsets.
    Instances carry bounded pitch, absolute phase, gain/envelope, time, and
    route laws.
- Analysis:
  - candidate grouping uses joint temporal co-modulation, harmonic or bounded
    inharmonic ratio consistency, complex phase continuity, onset/decay
    coherence, and cross-channel covariance;
  - matching SHALL be multiscale and independent of fixed transform-frame
    boundaries. Perfect-reconstruction filterbank tiles MAY be used internally;
    they do not define event boundaries;
  - harmonicity is evidence, not a semantic classifier and not an admission
    rule.
- Exactness and fallback:
  - coherent bundles, stochastic fields, transient events, direct Basis, and
    independent Truth compete per region and may overlap additively;
  - the sum receives one final mixture-domain Truth correction;
  - a claim that arbitrary audio is reconstructed without distortion is valid
    only after the normative decoder plus final Truth reproduces the declared
    exact PCM hash. A bundle alone is never assumed complete.
- RDO:
  - dictionary partials, parameter trajectories, phase anchors, route laws,
    entropy state, checkpoints, and compressed final correction are priced;
  - a large explained-energy fraction does not admit a bundle when its complete
    bytes or applicable quality point loses;
  - an initial one-axis win follows R-165 dual-axis refinement before the
    generation may be fixed.

## R-168 — Causal Acoustic Mechanism Objective

- Status: **ACCEPTED — MAF NORTH-STAR OBJECTIVE**
- Date: 2026-07-27
- Signal model:
  - MAF treats decoded pressure as the sum of unnamed causal emitters, their
    bounded resonant dynamics, propagation/routes, and one final Truth:
    `Pressure_c(t) = sum_s Route_c,s(Resonator_s(Excitation_s, State_s)) +
    Truth_c(t)`;
  - excitation may combine coherent/quasiperiodic trajectories, sparse
    impulses, and counter-addressed stochastic innovation;
  - resonant state may contain harmonic/inharmonic partial bundles,
    source-filter/formant laws, decay, modulation, and a short stable room or
    body response;
  - routes contain bounded delay, gain, phase, channel covariance, and stable
    propagation filters.
- Representation:
  - the encoder performs multiscale system identification: micro cycles and
    attacks, meso acoustic states, and macro sparse motifs/parameter laws
    compete together;
  - a law, state, Basis, or motif is paid once and remains alive until an event
    changes or expires it;
  - semantic class names are never needed for conformance or admission.
- Search objective:
  - the preferred latent explanation is the one minimizing complete dictionary,
    state, event, route, checkpoint, entropy, final-Truth, distortion, decode,
    and seek cost;
  - neural or semantic analysis MAY propose causes and boundaries but cannot
    remove deterministic search, decoder verification, quality floors, or
    independent Truth;
  - physical plausibility and predicted continuation are useful priors, not
    proof of compression.
- Information boundary:
  - Resonith does not claim that arbitrary audio has zero conditional entropy or
    can always be compressed;
  - distortion-free reconstruction of arbitrary supported PCM is provided only
    by the complete bounded rendering plus final Truth and verified hash;
  - if causal modelling does not reduce complete bytes or improve a matched-rate
    quality point, RDO retains the simpler incumbent.

## R-169 — Separate Causal Lanes with Single Ownership

- Status: **ACCEPTED — REQUIRED MAF DECOMPOSITION**
- Date: 2026-07-27
- Lanes:
  - coherent harmonic partial bundles;
  - deterministic bounded-inharmonic partial bundles;
  - sparse onset-addressed transients;
  - counter-addressed stochastic fields;
  - phase-, delay-, decay-, room-, and cross-channel route laws;
  - direct innovation/Truth for everything not economically explained.
- Ownership:
  - these lanes MAY overlap in time and frequency because physical causes add,
    but one primary lane owns each admitted explanatory coefficient/sample
    region for rate accounting;
  - a harmonic lane SHALL NOT absorb a transient or stochastic tail merely to
    avoid signalling another representation;
  - no lane carries an independent full residual. All selected lanes are summed
    first and receive one final mixture-domain Truth correction.
- Interference:
  - linear reinforcement and cancellation are rendered by complex phase and
    channel/route laws, not encoded as a duplicate source;
  - unexplained nonlinear interaction or estimation error remains final Truth.
- Selection:
  - local lane proposals feed one global complete-byte RDO;
  - the selector prices Basis/state, partials, events, phase, routes, entropy,
    checkpoints, overlap composition, and compressed final Truth;
  - a separate lane is admitted only when it reduces complete bytes or creates
    a successful matched-rate quality point under R-164/R-165.

## R-170 — Retire Magnitude-CNMF as a Primary Coding Path

- Status: **ACCEPTED — FAST GATE REJECTION / PROPOSER RETAINED**
- Date: 2026-07-27
- Long-first evidence:
  - the first R-165 gate analyzed the first continuous 120 seconds of the pinned
    full Mozart input before any short tuning;
  - the exact structural candidate selected zero latent components and cost
    19,874,554 bytes versus 19,874,458 independent compressed-Truth proxy bytes,
    a 96-byte or 0.000483% loss;
  - exact reconstruction passed; wall time was 484.787 seconds, or 4.040 times
    source duration.
- Short-second evidence:
  - 12-second EBU female speech found three active anonymous fields and 144
    placements but cost 0.485516% more than independent Truth;
  - 12-second EBU dense orchestra and pink noise admitted no field and lost
    0.009830% and 0.009173% respectively on structural overhead;
  - all cases reconstructed exact PCM.
- Decision:
  - mixture-phase-preserving magnitude CNMF remains an encoder proposal and
    ablation, but SHALL NOT be developed as the primary MAF coding
    representation;
  - the primary refinement moves to phase-aware/time-domain convolutional
    sparse fields plus the R-167/R-169 coherent, inharmonic, transient,
    stochastic, and route lanes;
  - future CNMF use must propose onsets, masks, partial groups, or boundaries
    whose decoder-verifiable causal representation wins complete RDO. CNMF
    magnitude factors themselves are not transmitted.
- Claim boundary:
  - these are **Real PCM / Fast diagnostic / Exact structural proxy** results,
    not full Resonith, FLAC, or Opus comparisons;
  - no `.resonith` generation or Orkela release is created for this rejected
    proxy candidate.

## R-171 — Causal Sequence Atlas

- Status: **ACCEPTED — HIGHEST-PRIORITY PATTERN SEARCH**
- Date: 2026-07-27
- Decision:
  - pattern search moves from repeated whole-waveform windows to canonical
    causal event streams derived from the R-167/R-169 lanes;
  - event coordinates include anonymous Basis/partial state, arbitrary time
    gap, pitch/frequency law, complex phase law, gain/envelope, formant/spectral
    shape, decay/resonator state, and channel/route state;
  - absolute pitch, phase, gain, onset, and channel position are separated from
    their transition laws so one motif can cover transformed performances.
- Completeness:
  - for each declared finite quantization and transform family, the Foundry
    SHALL build an exact suffix automaton or equivalent compressed index over
    every event origin;
  - one automaton state represents the complete interval of repeated substring
    lengths sharing an end-position class. The candidate manifest records that
    covered interval rather than silently testing only a few preferred lengths;
  - separate canonical streams SHALL cover at least literal, constant-offset,
    first-difference, and bounded second-difference pitch/gain/phase/route laws;
  - approximate matching MAY use landmarks, LSH, DTW, learned separation, or AI
    as additional proposers, but no proposer may prune the exact declared
    canonical language.
- Grammar:
  - arbitrary gaps and unrelated intervening events remain explicit;
  - maximal repeated sequences and their shorter suffix-automaton intervals
    feed multiple motif definitions and bounded `CompoundBasis` DAG selection;
  - micro patterns may merge into longer candidates, while direct long
    candidates continue to compete independently.
- Admission:
  - discovery does not imply coding gain. Complete dictionary, transform,
    event, entropy, checkpoint, render, and final-Truth bytes are compared with
    the incumbent and maximum-effort Opus under R-164 through R-166;
  - the long-first gate is mandatory because musical amortization and motif
    structure may not appear in short clips.

## R-172 — All-Lane Causal Event Atlas

- Status: **ACCEPTED — REQUIRED R-171 COMPLETION**
- Date: 2026-07-27
- Evidence:
  - the first R-171 long-first diagnostic indexed 20,849 harmonic causal events
    from the first continuous 120 seconds of the pinned Mozart input and found
    681 repeated end-position classes in 38.693 seconds;
  - 680 classes were found by bounded second-difference laws and one by
    constant-offset/first-difference laws. The longest reported class covered
    four events and the most frequent covered six occurrences;
  - 12-second female speech produced 1,216 events and 11 repeated classes;
  - dense orchestra produced only eight harmonic events, while its
    deterministic-inharmonic, transient, and stochastic lanes owned nearly all
    coefficients. This is an event-extraction coverage failure, not evidence
    that the mixture contains no repeated causal state.
- Decision:
  - every R-169 lane SHALL expose its own strictly ordered anonymous causal
    event stream: coherent harmonic, deterministic inharmonic, sparse
    transient, stochastic law, and phase/room/channel route;
  - each lane is indexed independently so simultaneous events never overwrite
    one another and cross-lane ownership remains explicit;
  - the joint grammar may reference synchronized events from several lanes,
    but it SHALL NOT merge them into one opaque waveform token;
  - stochastic events describe repeated distributions, envelopes,
    correlations, and modulation laws. They do not require repeated random
    sample realizations;
  - one final mixture-domain Truth remains the only authoritative correction.
- Admission:
  - the all-lane atlas is a proposer until dictionary, event, transform,
    entropy, checkpoint, render, and final-Truth bytes are priced together;
  - the R-171 diagnostic is sequence-discovery evidence only and makes no
    bitrate, quality, or Opus claim.

## R-173 — Factorized Law Atlases Before Joint Composition

- Status: **ACCEPTED — CORRECTION TO R-172 SEARCH**
- Date: 2026-07-27
- Failed conjunction:
  - the first all-lane implementation required time, pitch, phase, gain,
    envelope, resonator, and route coordinates to repeat as one indivisible
    token;
  - on the first 120 seconds of Mozart this indexed 64,501 lane events but
    reported zero joint classes, even though the simpler harmonic R-171
    language had already found 681 classes;
  - this is a false-negative construction: an unrelated coordinate, especially
    stochastic realization phase or small route drift, can destroy a real
    repetition in every other causal law.
- Decision:
  - each lane SHALL maintain independent exact atlases for timing, pitch,
    phase, gain, envelope, resonator, and route laws;
  - the full joint event atlas remains an optional high-specificity proposal,
    not a prerequisite for discovering a reusable law;
  - a bounded synchronized grammar composes separately reusable laws and prices
    their shared lifetime, exceptions, and final Truth. It need not retransmit
    a combined opaque token;
  - stochastic phase realizations are excluded from predictive state. Their
    distribution and channel correlation remain eligible laws.
- Completeness boundary:
  - exact completeness is claimed separately for every declared finite
    projected event language and every event origin;
  - cross-law composition is complete only for the explicitly bounded grammar
    family declared by the evidence generation;
  - learned, approximate, and semantic proposers may add joint candidates but
    cannot prune any exact factorized-law candidate.

## R-174 — Byte-Priced Hierarchical Causal-Law Grammar

- Status: **ACCEPTED — EXECUTABLE RESEARCH LEDGER**
- Date: 2026-07-27
- Decision:
  - factorized causal-law tokens SHALL compete as an exact literal ledger, a
    token dictionary, and a bounded acyclic hierarchical pair grammar;
  - a grammar rule is a `CompoundBasis` over two literal or earlier-rule
    symbols. Repeated rules may therefore grow micro patterns into longer
    structures without fixed waveform blocks;
  - every proposed rule is packed, entropy-coded, and admitted only when it
    reduces the complete causal-law payload at that step;
  - the decoder validates vocabulary, rule direction, expansion count, token
    width, checksum, and trailing bytes before accepting the ledger.
- Scope:
  - this first executable grammar prices and reproduces canonical event tokens
    exactly. It does not yet price acoustic Basis payloads, synchronized
    cross-law composition, renderer state, checkpoints, or final audio Truth;
  - therefore a token-ledger byte win is architecture evidence only, not a
    Resonith or Opus compression claim.
- Semantic boundary:
  - input names such as speech, Mozart, orchestra, or noise identify corpus
    files in evidence reports only;
  - the term `end-position class` denotes a suffix-automaton mathematical
    equivalence family, never a classified sound, speaker, instrument, or
    content type;
  - neither R-173 discovery nor R-174 grammar requires or transmits semantic
    source classes. Admission uses anonymous numeric causal laws and bytes.

## R-175 — One Timeline per Causal Lane

- Status: **ACCEPTED — REQUIRED LEDGER DEDUPLICATION**
- Date: 2026-07-27
- R-174 evidence:
  - on the first 120 seconds of Mozart, independently packed factorized token
    ledgers decreased from 611,298 to 514,946 bytes, or 15.761871%, with exact
    token round-trip;
  - female speech, dense orchestra, and pink noise token ledgers decreased by
    10.577340%, 6.074323%, and 11.925028% respectively;
  - most Mozart savings came from immutable token dictionaries. Hierarchical
    grammar won only coherent-harmonic timing and sparse-transient timing,
    demonstrating that rule admission correctly rejects gratuitous macros.
- Correction:
  - R-174 priced every factorized law independently and therefore repeated the
    same event timeline across pitch, phase, gain, envelope, resonator, and
    route columns;
  - one causal lane SHALL encode one ordered event clock. Its numeric law
    columns reference event ordinals or shared lifetimes;
  - constant/default columns and empty mono routes SHALL be omitted and
    reconstructed from declared defaults;
  - a complete row ledger, shared-timeline column ledger, and incumbent direct
    representation compete by actual packed bytes and exact decode.
- Claim boundary:
  - the R-174 percentages apply only to canonical causal token ledgers. They
    exclude acoustic Basis, rendering, checkpoints, synchronization, and final
    Truth and are not full Resonith or Opus gains.
- R-175 result:
  - the first 120 seconds of Mozart selected the shared-timeline column form in
    every lane and reduced the exact event ledger from 602,415 to 471,002
    bytes, or 21.814364%;
  - female speech, dense orchestra, and pink noise reduced their exact event
    ledgers by 8.105210%, 9.904385%, and 14.411588%;
  - short transient and very small harmonic lanes selected complete row
    fallback, proving that column factorization is not forced when its headers
    cost more;
  - all selected ledgers reproduced every anonymous numeric event exactly, and
    all analytic lane renders plus final Truth reproduced the PCM hashes.

## R-176 — Causal Basis Field Research Transport

- Status: **ACCEPTED — DECODER-IN-LOOP INTEGRATION STEP**
- Date: 2026-07-27
- Decision:
  - the first complete integration SHALL replace repeated MFT1
    `BASIS_WARP_INSTANCE` records with one immutable Basis dictionary and one
    R-175 event ledger per anonymous emitter;
  - each event carries only bounded numeric render state: onset, Basis ID,
    source position/phase, start/end source step, start/end gain, finite
    lifetime, and flags. It carries no source class;
  - the research decoder parses and bounds this `CBF1` transport, reconstructs
    the equivalent MFT1 bounded-DSP program, executes the existing native
    decoder, and then adds one independently decoded lapped Truth;
  - direct MFT1 and direct Truth remain complete-byte fallbacks.
- Admission:
  - the `CBF1` predictor must reproduce the native MFT1 prediction sample for
    sample before any residual comparison;
  - complete `CBF1 + Truth` bytes and decoded quality compete against direct
    Truth under the same quality floor;
  - this translation transport is research-only until a native C++23 parser
    renders the same events directly with CPU parity and declared bounds.
- Long-first result:
  - the first 120 seconds of Mozart selected direct Truth at 1,883,620 bytes;
    fixed-block CBF1 plus Truth cost 1,885,808 bytes, only 2,188 bytes more,
    but the proposer found one Basis and two instances covering 2,048 samples;
  - female speech, dense orchestra, and pink noise also selected Truth.
    CBF1 compressed the dense-orchestra predictor from 133,804 to 52,968 bytes,
    but its insufficiently isolated prediction made complete Truth correction
    and quality substantially worse;
  - all CBF1 translations were sample-identical to their native MFT1
    predictors. The transport passes; R-155 fixed-block discovery is rejected
    as the primary real-audio predictor under R-177.

## R-177 — Anonymous Partial-Basis Trajectories Replace Fixed-Block Proposals

- Status: **ACCEPTED — PRIMARY R-176 ANALYZER REFINEMENT**
- Date: 2026-07-28
- Evidence:
  - on the 12-second speech smoke input, R-176 compressed the bounded predictor
    from 8,792 MFT1 bytes to 6,131 CBF1 bytes, but the fixed 1,024-sample warp
    proposer covered only 10,240 of 529,200 samples;
  - complete CBF1 plus Truth cost 97,837 bytes and had larger SSE than the
    91,120-byte direct Truth, so exact RDO selected fallback;
  - transport and native translation therefore work; inadequate causal
    coverage and residual reduction are the blocker.
- Decision:
  - fixed waveform blocks remain a direct-dictionary candidate but cease to be
    the primary CBF1 analyzer;
  - coherent observations SHALL be clustered into multiple anonymous immutable
    partial-shape Basis states using normalized amplitude ratios and relative
    complex phase, without instrument or voice labels;
  - contiguous observations are compiled into long bounded source-position,
    source-step, gain, and route trajectories at arbitrary sample boundaries;
  - each Basis count, clustering, segmentation, and trajectory refinement
    competes by complete CBF1 plus final-Truth bytes. One global median Basis is
    never assumed sufficient;
  - inharmonic, transient, stochastic, and route lanes remain separate and
    continue to compete with direct Truth.

## R-178 — Persistent Anonymous State and Decoder-Domain Admission

- Status: **ACCEPTED — REQUIRED R-177 CORRECTION**
- Date: 2026-07-28
- Failed behavior:
  - the first R-177 boundary smoother raised one Basis from zero gain to its
    fitted gain and returned it to zero across the complete lifetime;
  - this suppressed most of a long-lived cause merely to avoid a boundary
    discontinuity. On the 12-second female-speech diagnostic it improved the
    complete candidate from the earlier R-176 result, but still cost 96,067
    bytes versus 91,120 direct-Truth bytes and produced `1.007334` times the
    direct-Truth SSE;
  - analytic coherent-lane fit therefore cannot by itself admit a transported
    Basis. The actual residual transform, quantizer, entropy payload, and
    decoded reconstruction are authoritative.
- Decision:
  - an anonymous cause persists at its fitted gain and phase for its useful
    lifetime. Boundary smoothing is confined to short bounded edge ramps and
    SHALL NOT taper the entire lifetime to zero;
  - subdivision for CUDA, analysis windows, entropy pages, or checkpoints
    SHALL preserve source position, phase, gain, and law state. An internal
    chunk boundary is not an acoustic event;
  - adjacent compatible state intervals SHOULD be chained before transport.
    A new event is emitted only for an objectively measured state change;
  - candidate admission SHALL compare the actual decoder-produced
    `Basis + events + final Truth` stream with the incumbent at complete bytes
    and decoded quality. Analytic lane error is a proposer score only;
  - bounded local or beam RDO MAY use an exact affected-transform-domain
    delta before the final complete-stream decode. It SHALL retain direct
    Truth and SHALL NOT use semantic content names or classifier confidence.
- Evidence order:
  - every generation runs a long input first and freezes its Pareto point;
  - short speech, orchestra, noise, and heterogeneous diagnostics follow;
  - a rate-only or quality-only candidate receives the bounded refinement of
    the missing axis required by R-164 before it is frozen.

## R-179 — Minimum-Description Anonymous Causal Program

- Status: **ACCEPTED — PRIMARY MAF COMPILER OBJECTIVE**
- Date: 2026-07-28
- Correction:
  - tuning one waveform Basis, threshold, frame mode, or semantic source class
    at a time cannot realize MAF. The 12-second R-177 diagnostic assigned
    90.546% of signal energy to its analytic coherent lane, yet the primitive
    single-cycle trajectory language covered only a small fraction
    economically and did not beat direct Truth;
  - this is a representation failure, not evidence that the recording lacks
    causal structure. The compiler must optimize the complete anonymous
    program rather than force one representation to explain every cause.
- Objective:
  - for a declared finite program language, the Foundry minimizes
    `L(program) + L(events, routes, state | program) + L(final Truth | program)
    + lambda * distortion + mu * decode cost + nu * seek cost`;
  - the byte terms are actual packed streams from the independent decoder.
    Explained energy, separation score, semantic confidence, and analytic
    error are proposal evidence only;
  - Lossless fixes distortion to zero. Perceptual profiles retain a
    decoder-produced matched-quality Pareto frontier and direct Truth.
- Anonymous causal program:
  - a program contains unnamed additive emitters, immutable leaf Basis,
    excitation laws, resonator/state laws, deterministic inharmonic partials,
    transient events, stochastic distributions, phase-continuous parameter
    trajectories, channel/room routes, and bounded acyclic CompoundBasis;
  - these mechanisms may overlap in time but have single primary ownership in
    the perfect-reconstruction analysis domain. They are summed before one
    mixture-domain Truth; per-lane exact residuals are forbidden;
  - timing, pitch, complex phase, gain, envelope, resonator, and route remain
    independently indexed and are composed only when the complete program
    becomes shorter;
  - source, instrument, speaker, note, speech, music, and noise names are not
    program fields. Optional AI, separation, embeddings, fingerprints, and
    semantic models may add columns but cannot delete any candidate in the
    declared deterministic language.
- Search:
  - proposer union includes direct complex/time-domain patterns, anonymous
    convolutive factors, coherent partial bundles, source-filter,
    deterministic inharmonic, transient, stochastic, cross-channel route, and
    direct Truth candidates at overlapping scales and arbitrary origins;
  - a bounded exact oracle is used for small candidate families. Scalable
    encoding uses column generation plus deterministic add/remove/swap beam
    RDO and an actual final pack/decode pass;
  - short events may form long sparse gap motifs, while direct long
    candidates remain independent. CUDA tiles, transforms, and entropy pages
    never define acoustic boundaries.
- Decoder and limits:
  - the decoder executes a fixed resource-bounded integer ISA; it performs no
    search, classification, separation, or neural inference;
  - arbitrary programs, shaders, callbacks, floating-point normative state,
    and transmitted neural networks remain forbidden;
  - every program declares bounded Basis bytes, active emitters, expanded
    events, grammar depth, operations per frame, checkpoint dependency, and
    workspace before rendering.
- Falsifiable gates:
  - first prove the free-oracle bound on changing-overlap synthetic mixtures;
  - then run long real material before short tuning and report Basis, event,
    route, checkpoint, final-Truth, total-byte, quality, and wall-time budgets;
  - no architecture or Opus claim is made until the complete R-118 union and
    maximum-effort official Opus frontier pass from actual decoders.

## R-181 — Theory-Before-Syntax Research Protocol

- Status: **ACCEPTED — MANDATORY PROJECT METHOD**
- Date: 2026-07-28
- Scope:
  - before implementing any new codec mechanism, opcode, normative state, AI
    role, transform family, or material encoder heuristic, the project SHALL
    complete a written theory review;
  - ordinary defect fixes, tests for already accepted behavior, mechanical
    portability work, and measurement-only runs do not require a new review.
- Required review:
  1. state the signal model, invariant, objective, and what existing candidate
     fails;
  2. derive the information, identifiability, approximation, and worst-case
     limits. Separate possible compression from impossible universal claims;
  3. search current primary scientific and engineering sources online,
     including prior art, successful methods, negative results, and practical
     implementations. Record direct references and the date;
  4. compare at least the direct-Truth incumbent, the simplest bounded
     candidate, the strongest practical alternative, and the proposed union;
  5. define decoder ISA, fixed-point state, memory, operations, security,
     random access, packet-loss, mobile, and ASIC consequences before syntax;
  6. publish a falsifiable byte/quality budget, expected activation domain,
     ablation plan, and kill gate;
  7. declare long-first and short-second real inputs, synthetic oracle bounds,
     maximum-effort anchors, exact artifacts, and independent-decode checks;
  8. record the decision before code and update the theory if evidence
     contradicts an assumption.
- Per-file oracle:
  - manual, visual, AI-assisted, and exhaustive analysis of each evidence file
    is encouraged for discovering the best attainable anonymous program;
  - such analysis is an encoder oracle, never transmitted semantics. A useful
    manual explanation must be converted into deterministic mathematics,
    reproduced automatically, and validated on held-out files before a
    general codec claim;
  - no benchmark-specific table, hand-authored event map, filename, or content
    label may enter a released encoder default.
- Scientific basis:
  - Rissanen's minimum-description principle justifies charging the model and
    the data together;
  - McAulay-Quatieri and Serra justify time-varying sinusoidal/partial laws and
    separate deterministic/stochastic representations;
  - phase-aware complex factorization shows that magnitude-only separation is
    insufficient;
  - MixIT shows label-free latent separation is possible but not unique, while
    sparse-solution NP-hardness requires an explicitly bounded search rather
    than an unprovable claim of a universal exact optimum.

## R-182 — Whole-Track Self-Supervised Causal Foundry

- Status: **ACCEPTED — HIGHEST-PRIORITY RESEARCH ARCHITECTURE**
- Date: 2026-07-28
- Problem:
  - isolated frame, block, or locally fitted Basis candidates do not learn how
    one anonymous cause evolves, disappears, returns, routes between channels,
    or participates in a longer gapped law across the complete recording;
  - a separator optimized for human source names is neither identifiable from
    a mixture nor aligned with minimum complete codec bytes;
  - fitting a per-track neural function without charging its quantized weights
    can merely hide the waveform in an unreported second payload.
- Formal signal model:
  - for channel \(c\), the analysis hypothesis is
    \(x_c[n]=\sum_s Route_{c,s}(n)\{Resonator_s(State_s,
    Excitation_s)[n]+Transient_s[n]+Stochastic_s[n]\}+Truth_c[n]\);
  - an anonymous point-cause state is a vector rather than one pitch:
    \(f_{s,k}(n)=k f_{s,0}(n)+Delta f_{s,k}(n)\), with separately persistent
    amplitude, complex phase, waveform-shape, resonator, envelope, and route
    coordinates for each retained partial;
  - causes may overlap and need not equal physical instruments. They exist only
    when they shorten the decoded explanation.
- Authoritative objective:
  - the per-track Foundry minimizes the actual packed description
    \(L(P)+L(E,R,S,C\mid P)+L(Truth\mid P,E,R,S,C)+lambda D+mu C_{decode}
    +nu C_{seek}\);
  - learned parameters, immutable Basis samples, dictionaries, events, routes,
    checkpoints, entropy state, and the single final Truth are all charged;
  - explained energy, separator confidence, likelihood, training loss, and
    semantic plausibility are proposal diagnostics only.
- Deterministic training loop:
  1. analyze the complete input at overlapping phase-preserving resolutions
     and arbitrary content-defined origins;
  2. propose anonymous coherent-vector, bounded-inharmonic, source-filter,
     transient, stochastic, convolution/resonator, route, direct long-Basis,
     and sparse gapped-motif columns;
  3. initialize parameters from deterministic DSP, an optional local learned
     proposer, or an external AI proposer, without allowing any proposer to
     prune the declared deterministic union;
  4. alternate quantized parameter re-estimation with add, remove, split,
     merge, link, unlink, route-share, motif-grow, and Basis-deduplicate edits;
  5. pack and independently decode every frontier edit, compute the one final
     mixture Truth, and admit an edit only on the complete rate-distortion-
     resource Pareto frontier;
  6. analyze the decoder-domain residual to generate the next columns while
     preserving single ownership and preventing per-lane correction streams;
  7. stop deterministically when a complete pass produces no admitted edit or
     a declared Foundry resource bound is reached.
- Whole-track learning rule:
  - all samples and channels MAY train the file-specific model. This is not a
    generalization task: overfitting is controlled by charging every emitted
    parameter and its final correction, not by pretending weights are free;
  - long-range state, returns, gapped motifs, cross-channel transfer, and
    repeated transformations are learned before short-only refinement;
  - internal FFT windows, CUDA tiles, batches, entropy pages, and checkpoints
    are implementation units and SHALL NOT define acoustic boundaries.
- Solver:
  - bounded exact subset search remains the oracle for small column sets;
  - scalable Foundry uses deterministic column generation plus reproducible
    add/remove/swap/split/merge beam search. It MUST publish the finite
    hypothesis manifest and the gap to every available exact subproblem;
  - global optimum over unrestricted sparse programs is not claimed.
- Decoder and privacy:
  - per-track training, source separation, gradients, Python, CUDA, and cloud
    models are encoder-only. The decoder receives only bounded integer ISA
    records already permitted by the selected profile;
  - a transmitted neural network, arbitrary executable graph, content label,
    filename identity, or cloud response is forbidden as a decoding
    dependency;
  - private PCM is local by default. External AI receives data only under an
    explicit user policy and remains a non-authoritative proposer.
- Prior-art review, checked 2026-07-28:
  - Rissanen supports charging the model and data jointly through minimum
    description length;
  - McAulay-Quatieri and Serra support evolving sinusoidal partials and
    deterministic-plus-stochastic analysis;
  - phase-aware complex factorization shows that magnitude-only factors lose
    a decisive coordinate;
  - MixIT and Sparse MixIT show label-free mixture learning and the need to
    penalize over-separation, but do not make the inferred sources unique;
  - per-signal implicit neural representations demonstrate train-on-the-file
    compression, while their quantized weights and slow fitting confirm that
    a learned representation must be charged and compiled into a bounded
    decoder language;
  - sparse program selection is NP-hard in general, so the declared finite
    exact/beam split is a required honesty boundary.
- Falsifiable budgets and kill gates:
  - for every selected structure,
    `saved final-Truth bytes > added program + event + route + checkpoint
    bytes` at the admitted quality point;
  - an alternative matched-byte quality point may be retained, but receives
    the required bounded refinement of the missing rate axis before freeze;
  - synthetic mixtures with known evolving causes test parameter recovery and
    independent decoded reconstruction, but do not authorize a real-audio
    compression claim;
  - long real inputs run first. Their Pareto incumbents are frozen before short
    tuning. A family that never reaches a Pareto frontier is disabled from the
    default without being hidden from the report;
  - only actual complete files decoded by the independent Core can pass.
    R-118 plus maximum-effort official Opus remains the promotion gate.

## R-183 — Multivoice Causal Basis Ledger

- Status: **ACCEPTED — REQUIRED R-182 TRANSPORT**
- Date: 2026-07-28
- Evidence that triggered the decision:
  - the first R-180 vector-partial synthetic fit explained approximately
    99.4% of event-domain energy but represented 2 seconds with 1,620 raw MFT1
    warp records and 71,424 predictor bytes;
  - this is a signaling failure, not a compression result. Repeating the full
    record header for every partial and analysis hop prevents a useful causal
    model from repaying itself.
- Design:
  - extend the CBF research transport from one identity-routed emitter per
    output to up to 64 anonymous emitter ledgers plus one bounded static output
    mix;
  - one emitter ledger owns one time-ordered partial or Basis trajectory.
    Several ledgers may overlap and route to the same output channel;
  - all ledgers share the Basis dictionary and total timeline. Their event
    fields retain exact onset, lifetime, source position, start/end step, and
    start/end gain;
  - the transport is a lossless lowering to the already bounded MFT1 decoder
    subset. It adds no oscillator, inference, floating-point behavior, or
    arbitrary program to the decoder.
- Alternatives:
  - raw MFT1 is retained as the exact fallback;
  - collapsing all partials into one PCM Basis reduces signaling but prevents
    independent frequency, phase, amplitude, and detuning evolution;
  - a neural waveform function may be more compact on some inputs, but its
    weights require a new decoder and must be charged. It remains an encoder
    proposer, not this transport.
- Limits and security:
  - output channels remain at most 8, emitters at most 64, Basis at most 256,
    and every ledger is strictly ordered with bounded event count;
  - the static mix is validated before MFT1 construction. Dynamic routes remain
    a separate future candidate and are not smuggled into this transport;
  - parser expansion is resource-preflighted and independently decoded.
- Kill gate:
  - conversion MUST reproduce the source MFT1 program and native PCM exactly;
  - it is selected only when its complete bytes are smaller than raw MFT1;
  - vector-partial compression claims remain forbidden until this transport,
    the final Truth, and complete program bytes beat the incumbent frontier.

## R-184 — Global Complex-Partial Flow Before Cause Grouping

- Status: **ACCEPTED — REQUIRED CORRECTION TO R-182 ANALYSIS**
- Date: 2026-07-28
- Rejected shortcut:
  - greedily selecting several fundamental frequencies in each STFT frame is
    allowed only as a labeled diagnostic proposer;
  - it is not the primary Foundry architecture because it can select
    subharmonics, switch identities at crossings, duplicate leaked energy,
    discard inharmonic causes, and spend an independent phase value for every
    channel and hop.
- Signal objects:
  - a primitive observation is an anonymous complex spectral partial
    \(p=(t,f,A,phi,route,uncertainty)\), estimated at sub-bin precision from
    overlapping phase-preserving analyses;
  - a partial trajectory is a path through such observations with continuous
    or explicitly corrected integrated phase, amplitude/frequency laws,
    births, deaths, and bounded gap edges;
  - a causal field is an optional group of partial trajectories that shares
    enough frequency modulation, amplitude envelope, resonator state, event
    timing, or channel route to reduce complete description length.
- Required analysis order:
  1. generate complex partial observations at all declared resolutions,
     without first assigning fundamentals or source classes;
  2. form a global time-frequency continuation graph over the complete track.
     Edges encode frequency, phase-integration, amplitude, route, gap, and
     residual consequences;
  3. select non-duplicating partial paths using exact min-cost flow where costs
     are additive and deterministic bounded beam/column generation where
     higher-order laws break that reduction;
  4. retain every selected path as an independent fallback;
  5. propose harmonic, bounded-inharmonic, common-modulation, common-envelope,
     resonator, motif, and route groupings only after paths exist;
  6. admit a grouping only when its shared law plus corrections is cheaper
     than the independent paths and produces a complete decoded Pareto point.
- Phase and channels:
  - phase is a state coordinate, not an afterthought. A continuous path derives
    phase by integrating frequency and adds sparse phase innovations only when
    they are cheaper than a restart;
  - cross-channel phase is first proposed as a shared route law, including
    delay-induced frequency-dependent phase, gain, polarity, decay, and a
    bounded transfer correction. Independent per-channel phase remains the
    exact fallback;
  - magnitude-only tracking cannot authorize a selected field.
- Other lanes:
  - transient, stochastic, convolution/resonator, and direct long-Basis
    candidates compete separately. A partial graph never forces them into a
    sinusoidal explanation;
  - the final Truth is computed once after the native sum of all selected
    lanes. Graph confidence and path coverage are diagnostics only.
- Primary-source review, checked 2026-07-28:
  - McAulay-Quatieri established time-varying sinusoidal tracks with phase
    related to the integral of instantaneous frequency;
  - PARSHL and Serra's spectral modeling track frequency, amplitude, and phase
    of spectral lines and explicitly retain a stochastic residual;
  - phase-aware complex factorization and phase-aware harmonic/percussive
    optimization show why magnitude-only assignment is insufficient;
  - published SMS implementations also document identity switching and the
    need for track continuation rules, confirming that frame-local nearest or
    pitch-guided matches are not a complete solution.
- Solver and complexity:
  - the declared observation and edge graph is finite. Exact flow is used for
    additive first-order tracking; spline, shared-law, and route groupings use
    bounded deterministic search with the independent paths always available;
  - unrestricted joint separation, grouping, and sparse-program selection is
    not claimed tractable or uniquely identifiable.
- Falsifiable gates:
  - synthetic crossing chirps, disappearing/reappearing tracks, harmonic and
    inharmonic bundles, opposite polarity, channel delay, and transient/noise
    overlap MUST be included;
  - the global tracker MUST report observation recall, identity switches,
    phase-integration error, grouped versus independent bytes, final-Truth
    bytes, and independently decoded PCM;
  - a grouped cause is rejected unless its actual total is smaller than the
    independent-track representation at admitted quality;
  - long real material remains first. No result from a frame-local
    multi-fundamental proposer may be presented as R-182 evidence.

## R-185 — Mandatory Adversarial Design Review Before Material Changes

- Status: **ACCEPTED — MANDATORY PROJECT METHOD**
- Date: 2026-07-28
- Scope:
  - applies before every material codec improvement, correction of an
    architectural assumption, syntax or state addition, search-family change,
    model/AI role, quality objective, transport, or resource-policy change;
  - ordinary typo fixes, mechanical refactors with proven identical behavior,
    tests of an already accepted invariant, and emergency restoration of a
    previously passing decoder do not require a new review.
- Required sequence:
  1. state the observed failure and freeze the evidence that exposed it;
  2. perform a divergent brainstorm containing the direct-Truth incumbent, the
     simplest bounded fix, at least one materially different alternative, and
     the strongest plausible combined approach;
  3. attempt to reject every alternative through information limits,
     identifiability, counterexamples, adversarial signals, complexity,
     security, seek/loss behavior, mobile/ASIC consequences, and actual-byte
     accounting;
  4. review several independent sources of truth: primary theory, current
     research, working implementations or standards, negative evidence, and
     the project's measured decoder output;
  5. assign an independent red-team subagent that did not author the proposal.
     The auditor SHALL inspect the theory, code if any, assumptions, budgets,
     tests, and stopping rule and SHALL return explicit accepted, rejected, and
     unresolved claims;
  6. resolve every blocking audit item in writing, revise or reject the design,
     and record the decision and kill gates;
  7. only then implement or continue the material change.
- Draft-code boundary:
  - exploratory code written before the audit is non-admitted scratch. It
    SHALL NOT become a default, result claim, release, or basis for subsequent
    architecture until the audit is closed;
  - preserving a draft for inspection is allowed, but its status and failing
    assumptions must be explicit.
- Evidence:
  - the decision record SHALL list rejected alternatives and why they lost;
  - a material result report SHALL link the audit, primary sources, synthetic
    counterexamples, independent decode, and long-first real gate;
  - agreement by the author is not an audit. If the auditor finds no weakness,
    a second counterexample pass is required before implementation.

## R-186 — Audited Complex-Partial Analyzer Manifest and Quarantine

- Status: **ACCEPTED — ANALYZER/TEST WORK ONLY**
- Date: 2026-07-28
- Audit disposition:
  - R-185 red-team accepts R-184 observation and tracking research only after
    the restrictions below;
  - predictor integration, phase syntax, R-183 lowering, cause grouping,
    long-real compression gates, default changes, and claims remain blocked
    until a second audit after native sparse-graph parity.
- Accepted foundations:
  - anonymous complex observations precede fundamentals and source grouping;
  - independent partial paths remain available;
  - phase is required state, while the current draft is phase evidence only;
  - transient, stochastic, direct-Basis, factorization, sparse-convolution,
    learned-proposer, and direct-Truth families remain in the union;
  - an additive first-order disjoint-path subproblem may have an exact
    diagnostic solution, but it is not the codec objective.
- Rejected current claims:
  - authoritative phase, all-resolution coverage, persistent phase paths,
    cross-channel route sharing, non-duplicating ownership, actual byte RDO,
    grouping, R-183 use, and scalable global flow are not implemented;
  - energy ranking, observation coverage, or arbitrary edge benefit cannot
    select a codec program.
- Finite research manifest:
  - declared resolutions are `(512,128)`, `(2048,512)`, and `(8192,2048)`
    samples by default; a gate may publish a smaller explicit subset;
  - 24 logarithmic bands, at most 2 observations per band and 48 total per
    detector/frame; aggregate and each channel are separate detector
    hypotheses with duplicate provenance and later ownership conflicts;
  - direct complex-DTFT and reassigned/phase-derivative estimates are distinct
    hypotheses. The first implementation supports only direct DTFT and reports
    that subset;
  - every observation carries resolution, centered time origin, detector,
    complex channel values, local SNR, frequency and phase uncertainty,
    resolvability, and provenance;
  - gap hypotheses are `1, 2, 4, 8` local hops; at most 4 neighbors per gap;
    second-order state contains frequency slope/acceleration, amplitude slope,
    route change, endpoint phase error, and cycle offsets `m0 + {-2..2}`;
  - bounded K-best width is 8 per terminal state, with deterministic numeric
    tie breaks; exact diagnostics are limited to at most 512 observations and
    4,096 continuation hypotheses;
  - original PCM plus strongest-first and lowest-correction decoder-residual
    observation orders form the finite order union, with at most 2 residual
    passes per order. Original candidates are never erased by a peel;
  - an evidence run declares at most 65,536 retained path hypotheses, 7 GiB
    VRAM, and 16 GiB host RAM. Crossing those limits yields a bounded-search
    report, never silent pruning or a completeness claim.
- Phase convention:
  - direct DTFT uses a symmetric declared window and complex exponential whose
    time zero is the observation center sample;
  - low-SNR phase does not affect continuation cost;
  - endpoint phase compilation is forbidden in this generation. A future
    phase law must enumerate integer cycle counts near the integrated-frequency
    prediction and compare `CONTINUE(m)` against `RESTART`.
- Resolvability and truth:
  - perfectly symmetric crossings, sub-Rayleigh close tones, and complete
    destructive cancellation are scored modulo permutation or marked
    unidentifiable; they do not become false tracker failures;
  - direct, convolutional, factorization, and Truth alternatives remain
    available for all unresolved content.
- Ordered implementation gate:
  1. analytic resolvability oracle and counterexample tests;
  2. corrected observation records and DTFT phase;
  3. exact small first/second-order diagnostics with restart/birth/death and
     minimum length inside the state;
  4. bounded K-best sparse tracker;
  5. native C++23/CUDA sparse graph parity;
  6. stop for a second R-185 audit before any phase synthesis or transport.
- Accounting preconditions:
  - publish observation/track diagnostics on known analytic signals;
  - publish a free-oracle lower bound that charges proposed path, phase, event,
    and route records and shows whether zero-cost grouping could plausibly
    repay them;
  - failure of the lower bound blocks syntax design.

## R-187 — Audited Multi-Objective Partial-Path Hypothesis Union

- Status: **ACCEPTED — ANALYZER PROPOSER ONLY**
- Date: 2026-07-28
- Frozen failure:
  - a continuity-only R-186 draft followed stable window sidelobes through a
    two-chirp crossing because every retained observation was assigned the
    same artificial independent-observation value;
  - on the declared crossing test it emitted two long paths, but their median
    nearest-ground-truth frequency errors were approximately 125 Hz and
    186 Hz. The draft is rejected as evidence of partial identity;
  - assigning `base + scale * log(amplitude)` "saved bits" was also rejected:
    without a decoded residual experiment this is neither an entropy bound nor
    an estimate of Truth bytes.
- Brainstorm and falsification:
  - **continuity only** is retained as one hypothesis family, but rejected as
    the sole ranker because coherent leakage can be temporally smoother than a
    crossing partial;
  - **strongest energy only** is rejected because it removes the planted
    approximately -47.6 dB weak line and biases every path toward dominant
    sources;
  - **higher detection thresholds** are rejected because they hide rather than
    solve ownership and weak-line recall;
  - **semantic or neural classification** is rejected as an authority because
    it can neither prove phase identity nor suppress a mathematically valid
    anonymous candidate;
  - **a calibrated residual delta per candidate** is the future authoritative
    value, but evaluating it for the complete raw graph is too expensive for
    the present analyzer. It is required before codec admission;
  - the accepted bounded proposer is the deterministic union of three
    materially different rankings: continuity, uncertainty-aware local
    potential, and frequency-stratified protected weak lines.
- Score separation:
  - `potential_node_value_q` is a dimensionless fixed-point search heuristic,
    not bits. It is zero when the lower confidence amplitude is non-positive
    and decreases with amplitude uncertainty, frequency uncertainty, phase
    uncertainty, low prominence, and leakage risk;
  - amplitude entering that heuristic is normalized by the declared window
    coherent gain, detector channel count, and analysis resolution;
  - `program_cost_bits` separately reports the provisional birth, continuation,
    cycle, phase, gap, and death syntax estimate. It is never subtracted from a
    dimensionless value to claim byte savings;
  - each path separately reports continuity score, potential value,
    uncertainty/leakage penalty, program cost, conflict count, family, and
    phase error.
- Ownership and union:
  - duplicate observations from channel, aggregate, resolution, or sidelobe
    hypotheses remain explicit conflicts and cannot be rewarded twice inside a
    selected set;
  - the retained top-K union SHALL include value-weighted, continuity-only,
    and protected weak-line paths. Selection by one family SHALL NOT prune the
    candidates of another family;
  - weak-line protection is stratified by frequency band and confidence. It
    preserves a candidate for later exact residual testing; it does not force
    a weak line into the codec program.
- Determinism and bounds:
  - all ranking values are signed saturating fixed-point integers with
    published constants and lexicographic ties on family, observation IDs, and
    cycle counts;
  - the R-186 graph, K-best, path, host-memory, and accelerator bounds remain;
    hitting a bound is reported as pruning, never completeness;
  - partial tracking literature supports global lattice/path optimization over
    greedy continuation, but does not establish this heuristic as a codec
    objective. The full decoder-domain MDL remains authoritative.
- Kill gates:
  - both planted crossing chirps MUST occur in the emitted top-K equivalence
    set modulo permutation, and stable sidelobes MUST NOT displace them;
  - the approximately -47.6 dB line MUST survive in at least one protected
    weak-line path;
  - the 440.3 Hz clean-tone frequency, centered-phase, and path-continuity
    results MUST not regress;
  - reports MUST expose each score component and ownership conflict count;
  - no path may enter a predictor, syntax, R-183 transport, long-real claim, or
    release until a second R-185 audit and complete
    `pack -> native decode -> one final Truth -> actual bytes` comparison.

## R-188 — Canonical Spectral Peaks Before Band Allocation

- Status: **ACCEPTED — AUDITED ANALYZER CORRECTION**
- Date: 2026-07-28
- Frozen failure:
  - the R-186 detector searched each logarithmic band independently and
    inserted `argmax(band)` whenever that band had no interior local maximum;
  - a monotonic band edge is not a spectral peak. Around two planted crossing
    chirps this fallback emitted pairs near 453.1/459.6 Hz and 940.2/953.1 Hz;
  - the later Rayleigh test then treated each artifact as a second physical
    line, rejected the true observation, and left stable sidelobes for the
    path tracker.
- Alternatives and audit:
  - raising amplitude, SNR, or prominence thresholds is rejected because it
    can remove genuine weak lines without fixing the false feature;
  - choosing one representative from every sub-Rayleigh ambiguity cluster is
    rejected as the first correction because it can silently collapse two
    genuine close lines;
  - immediate multi-line deconvolution or reassignment remains a separate
    bounded observation hypothesis and is not necessary to remove this
    detector artifact;
  - the independent R-185 auditor accepts canonical full-spectrum peak
    detection as the smallest causal correction and blocks representative
    clustering until a later separately audited proposal.
- Required detector order:
  1. identify plateau-aware local maxima once over the complete positive
     spectrum, excluding DC and Nyquist;
  2. map every canonical peak bin into exactly one half-open logarithmic band.
     A peak exactly on a boundary belongs to the upper band;
  3. apply the per-band and per-detector resource caps only after this mapping.
     A band without a genuine local maximum emits no coherent partial;
  4. fit sub-bin frequency, direct DTFT, amplitude, phase, prominence, and
     uncertainty only for canonical bins;
  5. retain every genuine sub-Rayleigh member, attach an unresolved
     equivalence group, and mark no member as an authoritative resolved
     partial. Do not replace the group by a synthetic representative;
  6. preserve cross-detector and cross-resolution alternatives with ownership
     conflicts.
- Kill gates:
  - the frozen chirp frame MUST retain one canonical feature near each planted
    460 Hz and 940 Hz component and remove the band-boundary duplicates;
  - both chirps MUST then survive the R-187 top-K equivalence gate;
  - the approximately -47.6 dB weak genuine maximum and clean 440.3 Hz phase
    tests MUST not regress;
  - if canonical peaks alone do not clear the crossing failure, stop for a new
    R-185 audit before adding ambiguity representatives or deconvolution.

## R-189 — Canonical-Pool Admission and Protected Band Slots

- Status: **ACCEPTED — AUDITED ANALYZER CORRECTION**
- Date: 2026-07-28
- Frozen failure:
  - after R-188 removed false boundary features, a genuine 460 Hz chirp peak
    was still omitted because its three-bin Hann main lobe had a median of
    4,948 amplitude units. Treating that self-energy as noise and applying a
    3 dB gate rejected the 6,624-unit maximum;
  - a within-band median or percentile dominated by the candidate's own main
    lobe is not a noise estimator.
- Accepted rule:
  - every full-spectrum canonical local maximum enters the candidate pool;
    SNR, prominence, leakage, and uncertainty annotate and rank candidates but
    SHALL NOT reject them before the declared resource allocation;
  - the first band slot uses deterministic conservative salience based on
    coherent-gain-normalized peak amplitude, a lower-confidence proxy, and
    prominence;
  - the second band slot uses an independent protected-line ordering based on
    relative prominence and leakage resistance. If both slots select the same
    peak, the next deterministic candidate fills the available slot;
  - remaining configured slots use the published lexicographic salience order;
    at global allocation, one protected candidate per occupied band precedes
    second candidates whenever the global cap permits;
  - all pruning reports pool count, retained and discarded candidate IDs, and
    `resource_pruned=true`. Retained candidates are never called complete.
- Confidence:
  - an optional diagnostic noise estimate uses a window-specific annulus
    outside the declared main-lobe guard and excludes guards belonging to all
    other canonical peaks;
  - if too few unowned bins remain, SNR is unknown and phase is unusable.
    Neither outcome removes the magnitude proposal;
  - noise confidence never authorizes candidate admission.
- Kill gates:
  - both 460 Hz and 940 Hz frozen-frame peaks survive while the old boundary
    artifacts remain absent;
  - the approximately 0.30 Hz crossing-path result, the -47.6 dB weak line,
    clean 440.3 Hz phase, and white-noise resource bounds all pass;
  - every detector/frame exposes resource-allocation diagnostics.

## R-190 — Native Sparse-Graph Parity and Optional CUDA Edge Scoring

- Status: **ACCEPTED — CONDITIONAL IMPLEMENTATION MANIFEST**
- Date: 2026-07-28
- Approved milestone wording:
  - **C++23 native sparse-graph parity with optional bit-exact CUDA
    edge-score acceleration**;
  - `CUDA tracker`, `full-GPU graph`, predictor, codec, or compression claims
    are forbidden in this generation. Canonical enumeration and the dependent
    K-best frontier remain deterministic C++23 CPU work.
- Alternatives:
  - porting the full FFT/DTFT analyzer to CUDA first is rejected because
    window/FFT differences would obscure graph parity and repeat detector
    errors before the accepted graph is stable;
  - CPU-only C++23 is retained as the mandatory fallback and oracle but does
    not satisfy accelerator evidence;
  - a fully GPU-resident K-best/min-cost tracker is deferred because
    cross-frontier dependencies, atomics, reductions, and tie order create a
    larger determinism problem. Official CUDA documentation notes that
    floating-point and atomic/reduction ordering can vary;
  - the accepted first phase enumerates the complete declared fixed-point graph
    on the host, maps one canonical candidate ID to one output record, scores
    every independent edge/cycle record on CPU or optional NVRTC CUDA, and
    runs the complete bounded R-187 path-family union in C++23.
- Scalar domains:
  - sample rate is `1..384000` Hz; declared analysis frequencies are
    `0..sample_rate/2`;
  - frequency and frequency delta use signed `int64_t` Q20 Hz. Frequency
    uncertainty uses unsigned `uint64_t` Q20 Hz;
  - normalized amplitude and amplitude uncertainty use unsigned `uint32_t`
    Q16 PCM-amplitude units, inclusive range `0..0xffffffff`. Normalization is
    direct-DTFT amplitude divided by window coherent gain and aggregate
    detector amplitude divided by square root of channel count;
  - phase is `phase_turn_u32`, one turn modulo `2^32`. Wrapped subtraction is
    interpreted as `int32_t`. Endpoint error is `phase_error_u31` in
    `[0,2^31]`; phase uncertainty uses the same half-turn domain;
  - `phase_step_u32` is
    `round(frequency_hz / sample_rate * 2^32) mod 2^32` and is carried in the
    observation fixture. Phase-invalid observations set the phase-usable flag
    to zero; no sentinel phase value is interpreted;
  - potential, uncertainty/leakage penalty, protected rank, continuity, and
    provisional program cost use signed Q8. Edge fields are bounded `int32_t`;
    path accumulation uses signed saturating `int64_t`. Dimensionless value and
    provisional bits remain separate objectives.
- Multiresolution and provenance:
  - the manifest contains at most eight resolution records with
    `resolution_id`, `fft_samples`, and `hop_samples`;
  - every observation carries `uint64_t center_sample`, local frame index,
    resolution, signed detector ID, band, ambiguity identity, canonical
    ownership component, local-resolvability and phase flags, protected rank,
    neighbor priority, potential, and uncertainty penalty;
  - center-sample delta is authoritative. Frame index is a
    resolution-local index and an edge is valid only when its center delta
    equals a declared gap multiplied by that resolution's hop;
  - ownership input is the deterministic union-find transitive closure of all
    detector, resolution, sidelobe, and duplicate relations. It is a disjoint
    equivalence partition before ABI entry. Non-transitive relations MUST use
    explicit CSR adjacency in a future ABI rather than being silently merged;
  - ambiguity identity is separate and does not authorize ownership or a
    representative.
- Integer laws:
  - neighbor membership and order are fixed-point only. Rank is normalized
    frequency distance Q8, then descending precomputed anonymous neighbor
    priority, then target observation ID;
  - `log2(1+n/d)` is a published integer Q8 operation: form a saturated Q16
    ratio capped at 65535, normalize with integer leading-bit position, then
    derive eight fractional bits by repeated unsigned Q31 squaring with
    round-down at every step. No lookup table or floating point participates;
  - phase advance computes
    `round((step0+step1)*center_delta/2) mod 2^32` by quotient/remainder
    decomposition. Only low 32-bit factors are multiplied; an odd step sum
    adds `ceil(center_delta/2) mod 2^32`. CPU and CUDA use the same unsigned
    operations and never require `__int128`;
  - every addition, multiplication used for cardinality/bytes, and signed
    score accumulation is checked or saturating before allocation or launch.
- C ABI:
  - every public manifest, resolution, observation, candidate, edge, and path
    record uses exact-width fields, `struct_size`, `abi_version`, explicit
    reserved-zero storage, a fixed packed layout, and compile-time size/offset
    assertions;
  - records are an in-memory ABI, not the Resonith serialized bitstream.
    Callers provide pointer/count spans; no uninitialized padding is hashed or
    compared;
  - invalid detector is not a sentinel: aggregate is explicitly `-1`, channel
    detectors are nonnegative. `UINT32_MAX` denotes absent ambiguity identity;
    ownership component is always present.
- Execution and reporting:
  - host enumeration, host-to-device transfer, CUDA scoring, device-to-host
    transfer, and CPU frontier times are reported separately;
  - CUDA tiles cannot change candidate membership, ID, order, score, or hash.
    CUDA absence or loader failure selects the identical CPU result;
  - host memory is capped at 16 GiB and VRAM at 7 GiB. Bound hits report
    explicit pruning/stopping and never a complete-search claim;
  - if host enumeration plus frontier exceeds 50% of wall time, the only
    allowed performance claim is edge-score acceleration.
- Kill gates:
  - CPU and CUDA edge arrays are bit-exact on every R-187/R-189 fixture,
    adversarial scalar extrema, every cycle offset, randomized valid
    manifests, and CUDA tile sizes `1,31,32,255,256,1024`;
  - C++23 path-family union, conflicts, component scores, tie order, bound
    reports, and exact-small selected set are bit-exact to a separate Python
    fixed-point oracle;
  - candidate cardinality and byte products are checked in 64-bit; maximum
    sample rate, center delta, gap, frequency, amplitude, score, path length,
    and invalid-manifest cases are covered;
  - the frame-50 460/940 Hz observations, approximately 0.30 Hz crossing
    paths, -47.6 dB protected line, and clean 440.3 Hz result do not regress;
  - Windows and Linux C++23 plus Android/iOS CPU-only compile gates pass;
  - a 120-second sparse and dense graph reports peak memory and stage times;
  - no output is imported by a predictor, R-183 transport, syntax, Orkela, or
    a real-audio compression report before the mandatory second R-185 audit.

## R-191 — Separate Transactional Path ABI and Frozen Second-Order Law

- Status: **QUARANTINED — POST-IMPLEMENTATION AUDIT BLOCKED**
- Date: 2026-07-28
- Trigger:
  - the first R-190 implementation achieved bit-exact Python/C++23 parity for
    the fixed 80-byte edge records, but the edge manifest did not declare the
    complete R-187 K-best frontier policy and the edge ABI could not represent
    variable-length paths;
  - implementing an implicit C++ policy would have violated R-185 by hiding
    pruning, resource use, tie order, and path ownership behind implementation
    defaults.
- Brainstormed alternatives:
  - **A — preserve edge ABI v1 and add a separate path ABI** is accepted.
    First-order independent edge scoring and dependent path search have
    different lifetimes, storage, and resource policy. Paths use fixed records
    plus a bounded CSR entry arena;
  - **B — replace the edge manifest with ABI v2** is rejected. It would mix
    independent edge scoring with frontier policy, invalidate frozen edge
    fixtures and hashes, and still require a variable-length output arena;
  - **C — compile K and other limits into C++** is rejected. It prevents exact
    preflight, makes the search language invisible to callers, and can turn a
    bound hit into silent pruning;
  - inline fixed-length path arrays and per-path allocation are rejected.
    The former imposes an artificial maximum on causal lifetime; the latter
    prevents exact capacity checks and stable cross-language layout.
- Independent red-team result:
  - two independent auditors selected alternative A;
  - both blocked implementation until amplitude-log scaling, temporal
    extrapolation, median-band assignment, transactional capacity behavior,
    ownership conflicts, and exact-small tie order were frozen;
  - this decision resolves those blockers before path code is admitted.
- Public in-memory ABI:
  - `resonith_partial_path_manifest` is separate from and does not modify
    `resonith_partial_graph_manifest` v1;
  - `resonith_partial_path`, `resonith_partial_path_entry`, and
    `resonith_partial_path_report` use exact-width integer fields,
    `struct_size`, `abi_version`, explicit reserved-zero bytes, packed fixed
    layouts, and compile-time size and offset checks;
  - one path record names a half-open slice in one bounded entry arena.
    Entry zero uses `UINT64_MAX` as the birth edge; every later entry references
    the stable incoming R-190 edge candidate ID. Gap, cycle, and phase data are
    not duplicated;
  - path identity is the complete tuple of observation IDs followed by incoming
    edge candidate IDs. Hashes are diagnostics only and never break a tie;
  - the API is two-pass and transactional. A null-output preflight returns the
    complete required path and entry counts and an input/config fingerprint.
    A fill request supplies that expected fingerprint. Stale input,
    insufficient capacity, invalid data, or a declared bound hit writes
    neither semantic output array;
  - all count, byte, offset, and work products are checked in `uint64_t` before
    conversion to `size_t` or allocation.
- Declared resource policy:
  - the path manifest independently declares K per terminal state for the
    local-potential and continuity objectives; top-K reservations for
    local-potential, continuity, and protected-weak families; protected
    paths per frequency band; minimum and maximum observations per path;
    maximum output paths, total entries, frontier states, work units, and host
    bytes; and the exact-small candidate limit;
  - frequency bands are explicit strictly increasing Q20-Hz upper edges.
    Bands are half-open and an exact boundary belongs to the upper band. The
    last band includes the declared Nyquist endpoint;
  - bounds are checked at canonical deterministic work checkpoints. Wall time
    may cancel a run but never defines a reproducible retained subset;
  - a bound hit sets an explicit termination and pruning report and cannot be
    described as a complete search.
- Canonical graph order correction:
  - source observations are enumerated by
    `(center_sample, resolution_id, detector_id, frequency_q20,
    observation_id)`, independent of caller array order;
  - declared gaps and cycle offsets are strictly increasing; target order is
    normalized frequency distance, descending anonymous neighbor priority,
    then target observation ID;
  - changing input permutation, CPU thread count, or CUDA tile order cannot
    change candidate IDs, records, paths, or selection.
- Fixed second-order frequency law, version 1:
  - for three observations with positive center deltas
    `dt01=t1-t0` and `dt12=t2-t1`, define
    `df01=f1-f0` and `df12=f2-f1` in signed Q20 Hz;
  - `predicted_df12 = scale_nearest_even(df01, dt12, dt01)`.
    Scaling uses sign/magnitude quotient-and-remainder arithmetic and never
    evaluates a potentially overflowing wide product;
  - frequency residual is
    `abs(df12-predicted_df12)`. Its denominator is the saturating unsigned sum
    of all three Q20 frequency uncertainties, clamped to the manifest's
    positive Q20 sigma floor;
  - frequency acceleration cost is the frozen R-190 integer
    `log2(1+residual/denominator)` Q8 operation.
- Fixed second-order amplitude law, version 1:
  - replace each unsigned Q16 normalized amplitude `a` by
    `max(a, amplitude_floor_q16)`, where the declared floor is positive;
  - define `dlog01=ilog2_ratio_q8(a1,a0)` and
    `dlog12=ilog2_ratio_q8(a2,a1)`. `ilog2_ratio_q8` is the signed use of the
    frozen R-190 integer `log2(1+n/d)` law: zero for equality, positive for
    growth, and negative for decay;
  - `predicted_dlog12 =
    scale_nearest_even(dlog01,dt12,dt01)`. The amplitude residual is
    `abs(dlog12-predicted_dlog12)`;
  - with the manifest's positive `amplitude_residual_weight_q8`, amplitude
    acceleration cost is
    `ilog2_1p_q8(residual * weight_q8 / 65536)`. The multiplication is checked
    or evaluated by quotient/remainder decomposition;
  - frequency and amplitude second-order costs are separate components before
    saturating addition. No floating point participates.
- `scale_nearest_even`:
  - division rounds to nearest; an exact half selects the even magnitude;
  - an unsigned product/division is evaluated as quotient plus a bit-serial
    remainder product, so CPU, CUDA, 32-bit, and 64-bit hosts require no
    `__int128`;
  - an unrepresentable result saturates to the declared signed path score
    limit and increments the report saturation count.
- Frontier, families, and ownership:
  - local-potential and continuity states are retained independently per
    terminal `(previous,current)` state, then unioned by canonical path
    identity. Dimensionless Q8 heuristic accumulators and provisional-bit Q8
    accumulators remain separate and are never compared across domains;
  - a protected-weak path contains at least one observation carrying
    `RESONITH_PARTIAL_OBSERVATION_PROTECTED_WEAK`. It is ranked within the
    lower-median frequency band by descending protected-observation count,
    descending saturating sum of nonnegative protected rank, descending
    continuity score, then canonical identity;
  - the path's frequency is the lower median Q20 value at index `(n-1)/2`
    after integer sorting. No floating-point or averaged even median is used;
  - a repeated ownership component inside one path increments its internal
    conflict count and makes that path ineligible for selected-set output.
    Cross-path conflicts are intersections of ownership components; ambiguity
    components never confer ownership;
  - exact-small selection maximizes the sum of
    `max(0, local_potential_score, continuity_score)`. Equal totals select the
    lexicographically smaller sorted tuple of canonical path IDs. Above the
    exact limit, deterministic greedy order uses descending selection score
    then canonical identity and is reported as non-exact;
  - protected retention reserves hypotheses for later measurement; it never
    overrides ownership and never forces final selection.
- Signed half-score correction:
  - randomized Python/C++ parity exposed that language-default division differs
    for a negative odd continuity score: Python produced
    `floor(-833/2)=-417`, while C++ truncated to `-416`;
  - an independent follow-up audit selected floor toward negative infinity.
    Truncation can erase a `-1` penalty and nearest-even adds parity-dependent
    tie behavior;
  - `half_score(x)` is therefore `x/2` followed by decrement when `x<0` and
    the remainder is nonzero. Implementations SHALL NOT rely on signed right
    shift. Required vectors include `-833 -> -417`, `-1 -> -1`, `1 -> 0`,
    and the minimum stored score.
- Report requirements:
  - required and written path/entry counts; raw, retained, deduplicated and
    per-family counts; frontier peak; deterministic work units; host bytes;
    internal and cross-path conflict counts; exact-small candidates and
    selections; solver and termination enums; score-saturation count;
    pruning/bound flags; and canonical input/config/output fingerprints;
  - neither path scores nor the report are predictor bytes, Truth savings,
    compression results, or bitstream syntax.
- Kill gates:
  - edge ABI v1 sizes, existing golden bytes, hashes, and the 14 current
    analyzer/edge tests remain unchanged;
  - a separate Python fixed-point oracle and C++23 implementation produce
    identical path, entry, family, selected-set, and report records;
  - caller input permutations, CPU thread counts, and CUDA tile sizes do not
    alter canonical output;
  - constant and linear chirps, amplitude ramps, irregular positive deltas,
    phase-invalid magnitude evidence, the approximately -47.6 dB protected
    line, odd/even medians, exact band boundaries, equal-score selections,
    ownership transitive closures, internal conflicts, and cross-path
    conflicts pass;
  - minimum and maximum path lengths, every arena boundary, stale preflight,
    insufficient capacity, count/offset/byte overflow, work exhaustion, and
    scalar extrema produce the declared status with no partial semantic write;
  - exact-small output matches an independent brute-force solver;
  - Windows and Linux C++23 plus Android and iOS CPU-only compile gates pass;
  - predictor, syntax, compression, Opus, release, and Orkela integration
    remain blocked until the second R-185 audit required by R-190.
- Second R-185 post-implementation result:
  - the independent auditor returned **NO-GO** for predictor admission;
  - path ABI v1 is an experimental fixture and SHALL NOT be release-frozen;
  - the audit demonstrated that path input validation accepted backward and
    internally inconsistent edge records instead of verifying that the edge
    array was the exact output of the declared graph;
  - reported work and host bytes covered neither the cumulative copied state
    frontier nor all temporary containers, pair comparisons, fingerprint
    sorting, and edge preflight materialization;
  - second-order dimensionless curvature had been added to both continuity and
    provisional-program accumulators, contrary to the domain separation above;
  - state/family truncation did not set the pruning flag or expose the promised
    discard counts;
  - exact-small totals used silent saturation, so the selected set was not
    exact under score overflow;
  - irregular-gap frequency uncertainty omitted the extrapolation ratio. For
    `q=dt12/dt01`, a conservative independent-error bound is
    `u2 + (1+q)u1 + q*u0`, not `u0+u1+u2`;
  - the 32 randomized CPU cases and one nine-edge CUDA fixture did not satisfy
    the declared resource, overflow, selector, scalar-extrema, cross-platform,
    and randomized CPU/CUDA kill gates.
- Audited remediation direction, pending a separate pre-code review:
  - edge ABI v1 remains frozen, but path ABI advances experimentally. The path
    call receives the resolution table and validates the caller's canonical
    edge array against a shared streaming edge enumerator and scorer. Local
    delta checks or a diagnostic fingerprint alone are insufficient;
  - edge preflight becomes count-only streaming enumeration; semantic output
    is filled only after capacity succeeds. It SHALL NOT materialize the full
    edge vector merely to count it;
  - copied path vectors and cumulative historical maps are replaced by a
    fixed-record state arena with parent backpointers and indexed terminal
    ranges. A counting `pmr::memory_resource` enforces peak live allocated
    bytes; a work meter charges before scans, comparisons, sorts, pair tests,
    and state creation;
  - path ABI v2 reports raw, retained, deduplicated, and discarded states,
    per-family truncation, every bound hit, peak live bytes, and every
    authoritative saturation. Any unrepresentable selector total terminates
    with a profile bound; exact-small never uses saturating set totals;
  - second-order curvature affects only dimensionless continuity ranking until
    an independently packed coding-cost model exists;
  - irregular-gap uncertainty uses the ratio-scaled conservative law with
    checked quotient/remainder arithmetic and exact Python/C++ parity;
  - transactional canary tests, an arbitrary-precision brute-force selector,
    resource/overflow extremes, randomized CPU/CUDA cases, ABI offsets, and
    Windows/Linux/Android/iOS gates are mandatory before another predictor
    admission audit.
- Pre-code remediation audit:
  - verdict is **conditional GO for analyzer remediation only**; predictor
    admission remains NO-GO;
  - supplied edges SHALL be in canonical `candidate_id` order and SHALL match
    the shared streaming enumerator field-for-field. Observation order remains
    caller-independent. Resolutions and ordering policy enter the fingerprint;
  - fill SHALL finish enumeration, fingerprint, exact count, and capacity
    validation before the first semantic write;
  - arena nodes use checked integer parent indices, a declared sentinel,
    indexed terminal buckets, reference-counted reclamation, and collision-free
    canonical sequence equality. Reconstructed identities, medians, ownership,
    and output entries consume declared work;
  - all dynamic project-controlled temporary containers use one bounded PMR
    resource. The report states `peak_live_managed_bytes`, not process RSS or
    allocator metadata. Environmental allocation failure is distinct from a
    declared profile bound;
  - sorting receives a published implementation-independent precharge;
    all possible pair tests, bucket scans, state creation, traversal, and
    reconstruction are charged before execution;
  - path API v2 uses a new symbol and never reads a v1-sized record. It reports
    generated, duplicate, retained, K-discarded, family-presented,
    family-discarded, output-deduplicated, and bound-rejected counts. Normal
    finite K/top-K truncation sets `PRUNED`;
  - exact-small totals are checked and unsaturated. Overflow terminates at the
    profile bound; equal totals compare full sorted canonical path identities;
  - frequency uncertainty law v2 is the estimator L1 proxy
    `u2 + u1 + ceil(dt12*(u0+u1)/dt01)`. Amplitude acceleration remains a
    weighted heuristic until amplitude uncertainty has its own audited law.

## R-192 — Multi-Partial Predictor Preflight

- Status: **ACCEPTED PREFLIGHT — IMPLEMENTATION BLOCKED BY R-191**
- Date: 2026-07-28
- Decision:
  - retain independent anonymous complex-partial paths as the first candidate
    source for decoder-domain prediction;
  - compare integrated phase and explicit endpoint-locked phase as finite,
    mutually exclusive hypotheses for the same path interval;
  - quantize and render every hypothesis through the prospective bounded
    integer decoder before measuring one final mixture-domain Truth;
  - preserve direct Truth as a complete fallback and admit no predictor record
    from analyzer scores alone.
- Rejected:
  - one frame-local fundamental as a universal representation;
  - magnitude-only synthesis;
  - a normative neural waveform decoder;
  - one independently corrected residual per inferred source;
  - syntax work before the quarantined R-191 graph passes its second
    post-remediation audit.
- Evidence and counterexamples are recorded in
  `docs/reviews/R192_MULTI_PARTIAL_PREDICTOR_PREFLIGHT_2026-07-28.md`.

## R-193 — Phase-Innovation Anchor Gate for Persistent Complex Partials

- Status: **ACCEPTED FUTURE EVIDENCE GATE — NO OPCODE ADMITTED**
- Date: 2026-07-28
- Trigger:
  - the project owner proposed replacing repeated phase estimates with one
    persistent oscillator state and sparse objective phase-lock events;
  - an independent R-185 red-team audit was required before adding the idea to
    the execution plan.
- What the audit accepted:
  - a small frequency error integrates into a large phase error over a long
    coherent lifetime;
  - integrated phase and explicit phase innovation must compete by complete
    decoder-in-loop rate/distortion cost;
  - long material is the correct first amortization and drift gate.
- Corrections to the proposal:
  - transform and predictive codecs do not simply forget phase. Opus uses
    lapped MDCT, inter-frame energy prediction, pitch filtering, and SILK
    long-term prediction; FLAC reconstructs the exact sample sequence;
  - continuous sinusoidal tracking and phase-continuous interpolation are
    established prior art, including McAulay–Quatieri models and MPEG-4 HILN;
  - a spectral peak or energy maximum does not uniquely define physical phase
    under window-origin changes, overlap, cancellation, or gauge ambiguity;
  - a large Truth reduction is a falsifiable target, not an established
    consequence.
- Current implementation boundary:
  - R-029 and the existing trajectory core already provide absolute integer
    phase state and partition-independent rendering;
  - R-190/R-191 observations and edges carry phase, phase-step, uncertainty,
    and endpoint-error evidence;
  - the Python research union already names `continuous` and `phase-locked`
    columns, but it emits short absolute-position warp instances. It does not
    implement sparse phase-innovation events or prove their byte economy;
  - no audited graph path currently drives persistent native synthesis,
    phase-anchor syntax, recovery checkpoints, or Orkela playback.
- Admitted research model for partial \(k\):

  \[
  z_k[n] = a_k[n]e^{i\theta_k[n]},
  \qquad
  \theta_k[n] =
  \theta_{0,k}+\Phi_{\omega_k}(n)
  \sum_j \Delta_{k,j}G(n-\tau_{k,j})
  \pmod {2^{32}}.
  \]

  `Phi` is an absolute bounded integer frequency integral. Each transmitted
  `Delta` is an objective phase innovation. `G` is one fixed bounded causal
  correction ramp. An instantaneous hidden phase reset is forbidden: a
  discontinuity uses a declared rebirth/crossfade candidate.
- Required alternatives and ablations:
  1. direct Truth;
  2. the preceding short harmonic/event predictor;
  3. persistent amplitude/frequency knots without phase anchors;
  4. denser frequency knots;
  5. persistent state plus phase-innovation anchors;
  6. rebirth plus deterministic crossfade using existing primitives;
  7. a free exact-phase oracle as an upper-bound diagnostic;
  8. magnitude-only or randomized phase as a negative control;
  9. shared oscillator plus cross-channel route versus independent channels.
- Admission and kill gates:
  - stop before syntax if the free exact-phase oracle fails to reduce compressed
    final Truth by at least 10% in at least three long coherent classes;
  - anchor mode must beat no-anchor, dense-frequency-knot, and
    rebirth/crossfade alternatives by at least 3% complete bytes on at least
    two long real coherent classes at the declared quality floor;
  - a stationary sinusoid and exactly representable linear chirp use no phase
    anchors after onset; a ten-minute bounded-vibrato case uses no more than
    one anchor per second;
  - close tones below nominal resolution, beating, crossing chirps,
    cancellation, onset/offset, noise, impulses, reverberation, anti-phase
    stereo, and changing inter-channel delay are mandatory counterexamples;
  - IDs, births/deaths, knots, anchors, routes, checkpoints, entropy, decoder
    work/memory, and final Truth all enter the complete cost;
  - callback partition and random-access slice cannot alter decoded PCM;
    corruption recovery must be bounded by a declared checkpoint;
  - no opcode is proposed until the oracle gate, native deterministic
    synthesis, complete R-118, current maximum-effort Opus, and listening gates
    pass.
- Execution order:
  - this is appended after the current final Orkela-coupled evidence step;
  - it does not bypass the active R-191 quarantine or R-192 predictor gate;
  - successful results amend R-192 instead of creating a parallel codec
    architecture.

## R-194 — Continuous MAF-to-1.0 Completion Train

- Status: **ACCEPTED PROJECT EXECUTION CONTRACT**
- Date: 2026-07-29
- Decision:
  - a passing diagnostic, architecture gate, alpha, beta, release candidate,
    or Orkela integration checkpoint is not a project stopping condition while
    a dependency-ready Resonith 1.0 item remains;
  - continue in the dependency order recorded in
    `docs/20_LSPF_MASTER_EXECUTION_PLAN.md` until Resonith 1.0 and its native
    Orkela integration are publicly released, unless the project owner stops
    the work or a genuine external blocker prevents useful progress;
  - the active technical spine remains the anonymous causal MAF model:
    persistent multi-source partial/resonator/excitation/route states,
    gridless multiscale patterns, transformed immutable Basis instances,
    separately owned coherent, bounded-inharmonic, transient, stochastic and
    route lanes, one final Truth, global decoder-in-loop RDO, GPU proposer
    search, and a bounded integer decoder;
  - R-191 remediation remains first. R-192 prediction and R-193 phase
    innovations cannot bypass its quarantine;
  - focused tests follow each change. The complete R-118, maximum-effort Opus,
    cross-platform, listening, and Orkela matrices run at declared generation
    and release boundaries, or earlier only when a focused failure proves that
    the broad gate is necessary;
  - every test names the risk it controls and the decision its pass enables.
    Testing without a release or architecture decision is not progress.
- Completion order:
  1. publish the accepted Orkela alpha needed for listening evidence;
  2. remediate and re-audit R-191;
  3. implement and measure R-192 persistent anonymous multi-partial synthesis;
  4. run the R-193 free phase oracle before any new anchor syntax;
  5. integrate gridless patterns, transformed Basis, separated causal lanes,
     persistent entropy/state, and global byte-quality-compute RDO;
  6. move exhaustive proposer/search kernels to GPU with a complete CPU
     fallback while retaining a CPU-only bounded decoder;
  7. run long-first Pareto generations against the maximum-effort official
     Opus frontier, then refine short inputs without deleting the long
     incumbent;
  8. freeze the v1 bitstream only after conformance, corruption, random access,
     packet loss, resource, deterministic synthesis, and cross-platform gates;
  9. publish Resonith 1.0 encoder, decoder, SDK, CLI, specification,
     reproducible benchmark corpus, and Orkela integration.
- Rejected:
  - treating one successful test as completion;
  - repeatedly rerunning the full corpus after isolated implementation edits;
  - bypassing analyzer quarantine to create parallel syntax;
  - preserving a mechanism merely because implementation effort was spent;
  - stopping at a target or hypothesis without measured decoder output.

## R-195 — MAF-First Architecture Jump

- Status: **ACCEPTED PRIORITY AMENDMENT**
- Date: 2026-07-29
- Supersedes:
  - R-194 completion-order item 1 only. Publishing an existing Orkela alpha is
    no longer a prerequisite for the next Resonith architecture generation.
    R-194's continuous-completion contract remains active.
- Decision:
  - complete one integrated MAF architecture generation before returning to
    non-blocking Orkela product expansion;
  - Orkela work during this interval is limited to the exact listening,
    visualization, A/B, and conformance support required by the current codec
    generation;
  - implement the architecture as one decoder-in-loop candidate union rather
    than a sequence of isolated percentage tweaks.
- Required integrated mechanisms:
  1. remediated anonymous multi-partial graph and persistent causal
     source/resonator/excitation/route states;
  2. objective continuous and phase-locked trajectories plus the R-193 free
     phase oracle;
  3. content-defined exact motif cache at arbitrary sample starts and lengths;
  4. gridless multiscale approximate-pattern search across time, frequency,
     fixed analysis tiles, and channels;
  5. CompoundBasis and sparse gap laws that compose useful distant events;
  6. immutable transformed-Basis orbits covering bounded alignment, phase,
     pitch, time, gain, envelope, filter, crop, reverse, polarity, delay, and
     route laws;
  7. Cached Integer Basis Synthesis for encoder-learned per-file atoms,
     materialized once by the bounded decoder and then immutable;
  8. separately owned coherent, bounded-inharmonic, transient, stochastic,
     and room/channel-route lanes plus one final TruthCorrection;
  9. source-filter and resonator lifetime models for slowly changing
     excitation, vocal-tract/instrument response, room tail, and gain/envelope
     state;
  10. exact inter-channel delay, phase, polarity, attenuation, common-source,
      and route reuse;
  11. persistent entropy and allocation state;
  12. one complete-byte, decoded-quality, decoder-compute and memory RDO over
      every model candidate and direct Truth;
  13. full GPU proposer/search batching without reducing the declared
      candidate union, with deterministic CPU fallback and a CPU/DSP-only
      normative decoder;
  14. optional Gemini and local-model proposals that may expand search but
      never label the bitstream or override local RDO;
  15. Foundry decision-trace capture and distillation into a compact consumer
      top-K router, with exact local RDO retaining final authority.
- Evidence order:
  - long speech, music, stochastic ambience, transient-rich and multichannel
    material first;
  - complete R-118 union at the integrated generation boundary;
  - maximum-effort official Opus frontier, preceding Resonith and direct Truth
    anchors from the identical PCM;
  - missing-axis refinement for any rate-only or quality-only win;
  - short-input tuning only after the long frontier is frozen.
- Kill rule:
  - each mechanism remains optional in the RDO union and is rejected for an
    input when its Basis, state, events, transforms, checkpoints, entropy,
    correction, decoder work and memory cost exceed direct Truth;
  - loss on one class cannot delete a proven Pareto win on another class;
  - no semantic source name, cloud response, hidden stem, or manual annotation
    is required for decoding or default encoding.

## R-196 — Material-Step Audit and Full Improvement Acceptance

- Status: **ACCEPTED AFTER INDEPENDENT AUDIT**
- Date: 2026-07-29
- Audit verdict:
  - **NO-GO** for literal review of every source edit and a complete corpus
    and platform rerun after every commit;
  - **GO** when a step means one independently falsifiable material work
    package and an improvement becomes accepted only after its full
    comparative gate.
- Material-step boundary:
  - a material step can change normative syntax, decoded samples/state,
    compatibility, an admitted encoder candidate/search/RDO/default/quality
    floor, bounded resource/security/seek/loss/mobile/ASIC behavior, a shipped
    ABI/API/platform or observable Orkela behavior, evidence semantics, corpus,
    anchor, metric, threshold, or public claim;
  - a source file, function, commit, test case, or ordinary implementation
    phase is not automatically a material step;
  - tightly coupled edits MAY form one step only when they share one frozen
    model and evidence plan, cannot be evaluated meaningfully in isolation,
    and retain individual ablations. Unrelated changes cannot be bundled;
  - changing the reviewed signal model, admitted scope, normative behavior,
    resource bounds, risk, or kill gate starts a new material step.
- Mandatory pre-implementation protocol:
  1. freeze the observed failure, incumbent, and reproducible baseline;
  2. compare direct Truth/incumbent, the simplest bounded correction, at least
     one materially different alternative, and the strongest plausible
     combined design;
  3. attempt to falsify every alternative against theory, identifiability and
     information limits, counterexamples, prior measurements, complete bytes,
     decoder resources, security, seek, loss, latency, mobile and ASIC
     consequences as applicable;
  4. review current primary research, standards, working implementations,
     negative evidence, and project measurements;
  5. declare byte, quality, resource and compatibility budgets, stopping rule,
     focused tests, and the full promotion evidence plan;
  6. obtain a written binary GO or NO-GO from an independent auditor subagent
     that did not author the proposal.
- Audit semantics:
  - GO authorizes only the reviewed bounded implementation and declared gate;
  - every unresolved blocking finding is NO-GO until resolved or the proposal
    is rejected;
  - exploratory calculations and code may exist only as marked non-admitted
    scratch before GO;
  - audit preparation, execution, remediation, verification, and publication
    are control activities and are not recursively material steps;
  - the same auditor may close findings in one case. A new audit is required
    when the proposal materially changes, independence is lost, a prior
    decision requires post-implementation audit, or this acceptance policy
    changes.
- Codec improvement acceptance:
  - an improvement is not accepted, retained as an admitted generation or
    default, versioned, released, or publicly claimed until its full gate
    executes long inputs first, freezes the long frontier, then encodes and
    decodes the complete R-118 union;
  - identical PCM is compared against the preceding Resonith generation,
    direct Truth/fallback, and the current maximum-effort official Opus
    frontier with complete-file byte accounting;
  - the report publishes all per-item bytes, actual-decoder quality metrics,
    resource results, hashes, source revision, versions, wall times, losses,
    fallbacks and retained incumbents;
  - affected corruption, determinism, seek/reset, packet loss, transient,
    stereo/spatial, latency, memory, throughput, listening, ABI and conformance
    gates are mandatory;
  - the complete supported-platform matrix is mandatory when bitstream,
    decoder, ABI/shared runtime or portability changes, and at every
    release-candidate and release boundary.
- Player improvement acceptance:
  - an Orkela user-visible or released improvement is not accepted until the
    Player Acceptance Gate compares it with the preceding Orkela version on
    every platform claimed by that version;
  - the report includes pinned short speech, full Mozart, backward
    compatibility and affected formats; real transport, seek, visualization,
    resize/DPI/settings behavior; startup/seek latency, underruns, PCM identity
    where applicable, CPU/GPU, peak memory and A/V synchronization; malformed
    inputs, associations, screenshots/traces, binaries, hashes and
    regressions;
  - a player-only UI improvement does not rerun codec compression R-118 unless
    it changes decoding, PCM delivery, codec integration or listening
    evidence. A codec-only encoder-search change does not run the complete
    Orkela product matrix unless it changes stream, decoder, compatibility or
    the listening package.
- Exclusions:
  - mechanical refactors with proven identical stream and PCM, formatting,
    typo fixes, tests of an accepted invariant, and non-normative
    documentation receive focused validation only;
  - performance-only refactors additionally publish identical output and a
    reproducible before/after resource report;
  - a failed or unpromoted hypothesis receives a scoped negative report but
    not an automatic full matrix unless that matrix was its declared decision
    boundary;
  - a defect fix restoring already specified behavior receives focused
    regression evidence; changing specified behavior, compatibility,
    resource/security bounds, or a released claim is a material step.

## R-197 — R-191 Transactional Remediation Preflight

- Status: **INDEPENDENT PRE-IMPLEMENTATION GO**
- Date: 2026-07-29
- Final independent verdict:
  - **GO** after closure of the exact-work, ABI, alias, transaction, bounded
    memory, case-generator and quantitative-gate findings;
  - implementation authority is limited to the frozen R-190/R-191 analyzer
    remediation. Predictor, syntax, compression, Opus and product claims remain
    blocked until the post-implementation evidence closes R-197.
- Frozen incumbent:
  - R-191 predictor admission remains NO-GO;
  - current work accounting omits repeated enumeration, sorting, scanning and
    reconstruction work;
  - R-190 edge fill retains unbounded default-resource containers and an
    exception/partial-write C-ABI risk;
  - fuzz dispatch and boundary/oracle/platform evidence are incomplete.
- Independently audited alternatives:
  - bounded materialized canonical edge vector: retained as an oracle and
    fallback, not the default;
  - hash-only validation: rejected because collision or stale data cannot
    replace field-for-field canonical comparison;
  - formula-only global work precharge: rejected as the sole meter;
  - hybrid per-operation charging with deterministic sort precharge: accepted;
  - monotonic arena: permitted only when total reserved allocation is reported
    as the memory cost;
  - reclaiming arena: preferred only with checked generation-tagged lifetime
    proof.
- Transactional fill contract:
  1. validate ABI, reserved fields, input/output non-overlap, bounds and
     immutable-input ownership;
  2. regenerate and compare the complete canonical edge stream field-for-field
     while computing exact count, diagnostic fingerprint and deterministic
     work ledger, with zero semantic caller writes;
  3. validate capacities and every declared work, managed-byte, state, path,
     frontier, entry and exact-small bound;
  4. stage all fallible output in bounded managed storage;
  5. commit caller arrays only after every fallible operation succeeds.
  - an allocation-free third emission pass may replace staging only after a
    proof that no failure remains possible and the API forbids overlapping or
    concurrently mutated inputs and outputs;
  - every non-success status preserves caller output and canaries byte-for-byte.
- Work-ledger contract:
  - work units are a platform-independent specified ledger, not measured CPU
    instructions;
  - charge before every validation pass, edge enumeration pair, field
    comparison, target-list construction, bucket scan, state creation, pair
    test, traversal, reconstruction, selector comparison, staging traversal
    and commit traversal;
  - use a specified deterministic sort or precharge a published conservative
    comparison bound. Runtime `std::sort` comparison counts are not normative;
  - repeated passes are charged independently;
  - arithmetic overflow returns the declared overflow status before the
    affected operation. Exact totals never saturate.
  - work-law v1 is a versioned per-event ledger for validation, input snapshot
    and canonical serialization, every fixed-pass radix operation, graph
    enumeration and comparison, table/bucket work, state and reference work,
    selection, reconstruction, allocation/reclamation, staging/commit,
    fingerprint bytes and synchronized CUDA enqueue/transfer/completion;
  - the 22 event kinds, multiplicity, 4,096-byte page, canonical 8-bit LSD
    radix keys/passes, signed-key mapping, stable bottom-up merge order and
    tie rule are frozen in the R-197 preflight review;
  - pass 1 consumes actual work, then reserves the exact stage-and-commit tail
    atomically before any semantic caller write; every event boundary has a
    reproducible `k-1` rejection case.
- Hard analyzer ceilings:
  - at most 1,048,576 observations, 4,194,304 edges, 65,536 paths,
    4,194,304 entries, 1,048,576 frontier states, 4,194,304 arena states and
    path depth 1,048,576;
  - at most `2^48-1` work events, 8 GiB counted host storage, 4 GiB counted
    device storage and checked output products;
  - one CUDA launch is capped at 65,535 blocks by 1,024 threads and uses
    checked 64-bit logical indices over at most 4,194,304 records;
  - all caller limits only reduce these ceilings. Raising a ceiling requires a
    new reviewed profile version.
- Storage and C-ABI contract:
  - every project-controlled dynamic allocation uses one bounded counting PMR
    resource; no default-resource vector, unordered map or hidden dynamic sort
    storage is permitted inside the C boundary;
  - catch `std::bad_alloc`, `std::exception`, and all other exceptions and map
    them to declared statuses;
  - report reserved arena bytes, committed arena bytes, allocator peak-live
    bytes and peak-live state slots separately;
  - snapshot bounded caller inputs before semantic processing; input and output
    ranges cannot overlap and caller mutation during the call is forbidden;
  - fingerprints serialize named integer fields in fixed little-endian order;
    raw padding, floating object representations, NaNs, signed zero and
    toolchain-dependent bytes never enter identity or scoring;
  - parent references use checked index plus generation identity. A slot cannot
    be reused while a child, terminal bucket or reconstruction cursor can
    reference its previous generation;
  - refcount overflow/underflow, stale generation, ownership mismatch and rank
    inversion are recoverable errors; no analyzer path calls `terminate`;
  - a post-initialization global-allocation tripwire proves that every
    project-controlled allocation flows through the counted resource;
  - reconstruction is iterative and bounded.
- Failure semantics:
  - null/pair/version/size precedes alignment/range, overlap, reserved/hard
    profile, canonical input, stale identity, capacity, resource, OOM and
    internal-state errors;
  - path and entry payloads are never changed on failure. After its own valid
    header, the report may be committed once with zero written counts and
    required counts, termination, consumed work, memory and fingerprints;
  - CUDA work synchronizes before returning and maps asynchronous errors to a
    declared status.
  - the review freezes pairwise disjoint ranges for every input, output and
    report object, exact first-failure precedence, status/termination mapping
    and which report diagnostics may change;
  - fingerprint law v1 freezes domain bytes, ordered logical fields, integer
    widths, two's-complement signed encoding, little-endian byte order, hash
    states/primes and output ordering; no implementation object bytes enter it;
  - the allocation tripwire is armed before the first ABI entry and permits
    upstream allocation only from explicitly counted host/device scopes.
  - R-190 stages its complete edge stream and atomically reserves edge payload
    plus `output_count`; only success and `OUTPUT_TOO_SMALL` may publish the
    exact required count, while every other failure preserves it and payload;
  - one R-191 report-stage token and one report-commit token are reserved before
    fallible analysis; staging is consumed immediately and publication retains
    the commit token. If both cannot be reserved, the report remains unchanged;
  - R-197 introduces path ABI v3 and
    `resonith_partial_graph_paths_cpu_v3`, 22 event counters, separate
    host/device reserved/committed/peak metrics and
    `INTERNAL_MALFORMED`; v2 remains a no-write `UNSUPPORTED_VERSION` stub for
    one migration cycle. R-190 ABI/record layout remains version 1.
- Fuzz and exact kill gates:
  - every mutation opcode has an independently addressable deterministic test,
    including `candidate_id`, `gap_hops` and `flags`;
  - canaries remain unchanged for every invalid ABI/reserved field,
    stale/missing fingerprint, forged edge field, insufficient capacity,
    resource bound, injected allocation failure, overflow and corrupt-parent
    result;
  - `limit-1` fails and `limit` succeeds for work, managed bytes, states,
    entries, frontier, path length and exact-small count;
  - an independent arbitrary-precision brute-force oracle matches IDs, order
    and totals for exhaustive small graphs, randomized ties and scalar extrema;
  - observation and resolution permutations are byte-identical; missing,
    duplicate, extra, forged and permuted supplied edges fail;
  - arena release/reuse covers every boundary without stale-parent access and
    preserves truthful reserved/peak-live reporting;
  - CPU results are repeat- and order-invariant; CUDA matches for randomized
    cases and tile sizes 1, 31, 32, 255, 256 and 1024;
  - sanitizer fuzzing checks statuses and output canaries in addition to crash
    freedom;
  - structure-aware fuzz repairs dependent IDs/sizes/fingerprints, publishes
    per-branch reachability, exercises stateful preflight/fill and allocator
    faults, and guards both host and device memory;
  - exact work/fingerprint golden vectors, global-allocation tripwire,
    null/alignment/range/overlap/version/status-precedence matrices and
    cross-compiler fixed-point/serialization parity are required;
  - quantitative floors are fixed by the hashed R-197 case manifest: every
    observation permutation through five observations, 64 deterministic
    SplitMix permutations for six and seven, 10,000 seeded CPU cases, 10,000 seeded
    CPU/CUDA cases per tile, 2,000,000 inputs plus 15 minutes per structured
    parser/API target, 1,000,000 sequences plus 10 minutes per stateful fault
    target, 100,000 TSan sequences, at least 100 hits per semantic reachability
    counter and at least 95% line/90% branch coverage of both exported analyzer
    functions;
  - every hard-profile dimension is tested at ceiling-minus-one, ceiling and
    ceiling-plus-one by the pure checked ceiling validator in addition to
    end-to-end declared-profile boundaries;
  - the exact finite value alphabet, topology enumeration and deterministic
    random-case generator are frozen and hashed in the R-197 case manifest
    before admitted implementation.
  - Windows MSVC/Clang/GCC, Linux GCC/Clang ASan+UBSan, Android NDK
    ARM64/x86-64 and Apple-SDK iOS compile gates run on one exact commit.
- Claim boundary:
  - a passing R-197 result proves bounded analyzer infrastructure only;
  - predictor, bitstream, compression, Opus and product claims remain blocked.

### R-197 implementation checkpoint A

- Status: **FOCUSED GATE PASSED — R-197 REMAINS OPEN**
- Hard ceilings, checked ranges, pairwise no-alias validation and bounded input
  snapshots are active in the R-190 edge call and quarantined R-191 analyzer.
- R-190 failure count preservation, empty-input preflight, payload/report
  overlap rejection, deterministic native output and the independent
  fixed-point oracle passed.
- Focused evidence:
  - Clang 22 C++23 native conformance executable: passed;
  - independent Python suite: 39 passed in 2.27 seconds.
- Result:
  [R-197 Hard-Profile and Snapshot Gate](results/R197_HARD_PROFILE_SNAPSHOT_GATE_2026-07-29.md).
- This checkpoint admits no predictor, syntax, compression or product claim.
  The next dependency is the separately visible transactional v3
  count/stage/commit API.

## R-198 — Every Algorithm Change Runs the Complete Music Manifest

- Status: **ACCEPTED**
- Date: 2026-07-29
- Rule:
  - every codec algorithm change is a separate evidence generation;
  - before another algorithm generation begins, encode and decode every item in
    the complete versioned registered-music manifest;
  - compare per file against both the immediately preceding Resonith generation
    and the current maximum-effort official Opus anchor from identical PCM;
  - publish detailed English human- and machine-readable per-file and aggregate
    bytes, bitrate, objective quality, spectral/phase/transient/channel
    behavior, encode/decode time, CPU/GPU, memory, hashes, fallbacks, wins,
    losses and regressions;
  - retain originals, encoded alternatives, actual decoded evaluation signals,
    commands, versions and reports.
- Scope:
  - all pinned music files and duration/structure classes, not only the three
    principal references;
  - this gate is additional to the non-negotiable R-118 union;
  - only a mechanical refactor with proven bitstream and PCM identity receives
    the focused identical-output exception.

### R-197 implementation checkpoint B

- Status: **FOCUSED GATE PASSED — R-197 REMAINS OPEN**
- Transactional path ABI v3 now owns the public native and Python bridge:
  - complete preflight, bounded staging and one semantic commit;
  - exact no-write behavior for precedence rows one through five;
  - no path/entry mutation on missing or stale identity, insufficient
    capacity, profile failure, allocation failure or malformed input;
  - packed cross-language layouts and deterministic successful output;
  - ABI v2 is a no-write `UNSUPPORTED_VERSION` compatibility stub.
- Focused evidence:
  - Clang 22 C++23 warnings-as-errors native gate: passed;
  - independent Python native/oracle suite: 40 passed in 1.87 seconds.
- Result:
  [R-197 Transactional Path ABI v3 Gate](results/R197_TRANSACTIONAL_ABI_V3_GATE_2026-07-29.md).
- This checkpoint changes analyzer infrastructure only, so R-198's
  algorithm-change music gate is not triggered.
- The next dependency is the exact 22-event ledger and canonical ABI v3
  fingerprint law; no predictor or compression claim is admitted.

## R-199 — Caller-Bounded Failure Precedence

- Status: **ACCEPTED AMENDMENT — R-197 REMAINS OPEN**
- Date: 2026-07-29
- Finding:
  - the original absolute precedence of semantic rows 6 through 8 over
    resource row 9 was impossible under arbitrary caller work/memory limits;
  - discovering a later malformed, stale, or insufficient-capacity result may
    itself require more than the caller budget;
  - continuing only to discover that result would create hidden uncounted work.
- Decision:
  - rows 1 through 5 remain absolute and ordered;
  - after the report reservation transition, rows 6 through 8 are semantic
    checkpoints and row 9 is a per-operation guard;
  - a known semantic failure wins, but resource exhaustion wins if it occurs
    before that predicate is determinable;
  - no ABI, record-layout, fingerprint-domain, or bitstream change is made.
- Required implementation order:
  - bounded canonical snapshot and semantic validation;
  - missing expected identity on fill;
  - canonical fingerprint and stale identity;
  - pass-one solver and exact capacity;
  - complete staging, payload commit reservation, payload commit, report
    commit.
- Evidence boundary:
  - this is analyzer-infrastructure remediation, not a codec algorithm change,
    so R-198's full music gate is not triggered;
  - R-191 stays blocked pending exact boundary tests and independent GO/NO-GO.
- Review:
  [R-199 R-197 Failure-Precedence Amendment](reviews/R199_R197_PRECEDENCE_AMENDMENT_2026-07-29.md).
- Focused implementation evidence:
  [R-199 Exact Work-Ledger and Fingerprint Gate](results/R199_WORK_LEDGER_FINGERPRINT_GATE_2026-07-29.md).
- Independent result:
  - **GO for Step 6** on `partial_graph.cpp` SHA-256
    `B3B893D70828C6813C8B3ECD696AB648E9EF0C142051604BC8E1733123B0597D`;
  - no blocker was found in the R-199 phase order, exact typed ledger,
    canonical fingerprints, transactional publication, or focused claims;
  - Steps 7 through 10 retain arena-completeness, memory-provenance,
    broad-fuzz/platform, and final R-191 obligations.

## R-200 — Generation-Safe Arena Ownership

- Status: **ACCEPTED — IMPLEMENTED — INDEPENDENT STEP-7 GO**
- Date: 2026-07-29
- Decision:
  - only the arena may manufacture an owning path-state reference;
  - owning creation/retention use RAII and one typed release reservation per
    live reference;
  - raw handles are generation-checked non-owning borrows;
  - roots have rank two; children match parent generation, rank, first
    observation, and previous/current linkage before refcount mutation;
  - zero-ref release is iterative and uses a deterministic LIFO free list;
  - solver success requires zero live states and zero arena-owned outstanding
    reference reservations.
- Red-team additions:
  - remove public raw-handle adoption;
  - prove parent/owner/PMR failure rollback;
  - prove multi-slot ABA/LIFO and no reuse under retained/child ownership;
  - audit refcount/reservation equality and complete free-list integrity.
- Rejected:
  arena UUIDs, hazard pointers, shared ownership, lock-free reclamation, and a
  production provenance graph.
- Design:
  [R-200 Generation-Safe Arena Design](reviews/R200_GENERATION_SAFE_ARENA_DESIGN_2026-07-29.md).
- Focused evidence:
  [R-200 Generation-Safe Arena Focused Gate](results/R200_GENERATION_SAFE_ARENA_GATE_2026-07-29.md).
- This is ownership infrastructure only; it makes no predictor, bitstream,
  compression, Opus, or product claim.
- Independent result:
  - **GO, zero blockers** on `partial_graph.cpp` SHA-256
    `D5E960011F78609AE7B0FA83820DECADCB4AEDF1A9E26BA2AA6BA687E670E413`;
  - Steps 8 through 10 retain full memory provenance, broad fuzz/platform
    coverage, and final R-191 admission.

## R-201 — Exact Host/Device Memory Provenance

- Status: **ACCEPTED — IMPLEMENTED — INDEPENDENT STEP-8 GO**
- Date: 2026-07-29
- Decision:
  - reserved, committed, and live memory are independent per-call high-water
    transitions, ordered `reserved >= committed >= peak-live`;
  - admitted upstream OOM raises only reserved high-water provenance and rolls
    current state back;
  - page prepare/commit/cancel/release transitions are checked against one
    immutable work ceiling;
  - every reachable project-controlled R-190/R-191 allocation uses one
    counting PMR resource;
  - a test-only permit surrounds only its checked upstream calls;
  - the CPU path reports device bytes and CUDA work as exactly zero rather
    than estimating unavailable device activity.
- Rejected:
  fake CUDA accounting, a production-wide replacement allocator, a shared
  ownership rewrite, and deletion of unreachable legacy code without evidence.
- Preflight:
  [R-201 Memory Provenance Preflight](reviews/R201_MEMORY_PROVENANCE_PREFLIGHT_2026-07-29.md).
- Focused evidence:
  [R-201 Memory Provenance Focused Gate](results/R201_MEMORY_PROVENANCE_GATE_2026-07-29.md).
- Evidence boundary:
  this is analyzer infrastructure only; allocation-ordinal fuzzing, sanitizers,
  platform breadth, and final R-191 admission remain Steps 9 and 10.
- Independent result:
  - **GO, zero Step-8 blockers** on `partial_graph.cpp` SHA-256
    `79C66C04CA270E5942A06263AAC713B531726964BC4C80DB611BC911B522F369`;
  - tripwire SHA-256
    `42992C32EAD0A940BAB4C9E0A569084A66AAE6B4CBBCBF7F6A88936114D4FDC8`;
  - all eight individual first/repeated R-190/R-191 entries exercised the
    counted permit path; `1,904` permitted and zero forbidden allocations;
  - Step 9 retains ordinal fault campaigns, sanitizers, structured fuzzing and
    platform breadth.

## R-202 — Stateful ABI-v3 Fuzz, Coverage, and Staging-Guard Evidence

- Status: **ACCEPTED — INDEPENDENT STEP-9 GO**
- Date: 2026-07-29
- Problem:
  the output-staging managed-memory guard at the v3 publication boundary is
  defensive, but the first proposed coverage witness emitted only one
  protected path and therefore could not test whether complete legacy-plus-v3
  staging could exceed the solver's measured historical peak.
- Rejected alternatives:
  - increasing only `top_k_protected` from 1 to 128 is rejected: every
    514-observation candidate has a 440 Hz median and is truncated by the
    per-band limit before the global protected reservoir;
  - lowering the measured peak, excluding legitimate allocations, adding a
    test-only production bypass, or accepting a coverage percentage without a
    semantic witness are rejected;
  - redesigning 128 paths to have distinct median-frequency bands remains a
    valid alternative but adds unnecessary fixture complexity.
- Independently challenged decision:
  - the first corrected 128-path fixture was killed after producing exactly
    128 paths and 65,792 entries because its measured historical peak was
    12,310,952 bytes versus 6,350,848 staging bytes;
  - the failure is dominated by crossing the 65,536-entry geometric vector
    capacity boundary and does not prove the guard unreachable;
  - one final bounded witness raises both public-valid protected limits to 256,
    uses a 4,094-observation shared prefix, 16 intermediate branches and 16
    terminal neighbors per branch, and requires exactly 256 paths of length
    4,096 and 1,048,576 entries;
  - production code, ABI, algorithm, bitstream, work law, and memory
    accounting remain unchanged;
  - the fixture must prove exactly 256 output paths and 1,048,576 entries, a
    protected-family population, measured historical peak below complete
    staging, exact-peak preflight reproducibility, `PROFILE_BOUND` at fill,
    unchanged output payload, and bounded Clang/GCC runtime and memory.
- Falsifiable prediction:
  the power-boundary shared-prefix fixture either produces the declared counts
  with `historical_peak < 100,732,928` staging bytes and reaches the
  transactional staging guard, or it is rejected without further threshold
  tuning. Focused runtime must remain at most 10 seconds and process RSS at
  most 512 MiB.
- Measured falsification:
  - the fixture produced exactly 256 paths, 1,048,576 entries and 4,365 edges
    in 1.702 seconds;
  - historical peak was 116,675,808 bytes, exceeding 100,732,928 staging
    bytes by 15,942,880;
  - no larger fixture is permitted without allocation-component evidence.
- Final allocation proof:
  - at the final legacy entry-vector growth boundary, old and new buffers
    coexist and contribute at least `72E` for current supported STL growth;
  - protected and union identities add `16E + 16E`, ownership adds `4E`, and
    family/union object backing adds `272P`;
  - consequently `historical_peak >= 108E + 272P`, while the later guard
    computes `stage_bytes = 96E + 272P`;
  - successful preflight already proves
    `historical_peak <= maximum_managed_bytes`, so for every non-empty output
    the wrapper predicate `stage_bytes > maximum_managed_bytes` is impossible;
  - the independent verdict is GO for a pure checked arithmetic helper and
    strict hash-bound semantic allowlist, and NO-GO for another public witness,
    a manufactured failpoint, or allocation behavior changed only for
    coverage.
- Local implementation result:
  - the failed 256-by-4,096 witness and diagnostic trace were removed;
  - production and tests share one pure overflow/limit helper;
  - Clang 22 and GCC 16 each pass all five focused partial-graph tests;
  - strict source/helper/proof hashes and exact missing-set equality reject
    stale, new, or silently covered contract entries;
  - LLVM-MinGW 22 is rejected as an admission authority after reporting both
    false negatives and an impossible `2^63 - 1` branch counter;
  - the sole admission contract is bound to Ubuntu 24.04 and exact LLVM
    18.1.3 toolchain identity; automatic profile inference and unioned outcome
    sets are prohibited;
  - a second unchanged Ubuntu run proved that mixed profiles from separately
    linked executables are themselves unstable;
  - semantic coverage now admits only the canonical conformance executable;
    tripwire, ordinal, concurrency, and fuzz profiles are retained and hashed
    as mandatory supplemental evidence but cannot enter semantic counters;
  - the first canonical Ubuntu artifact seeds only a candidate contract; two
    independent identical canonical runs are required before freezing it;
  - the first canonical-only artifact exposed three reachable cases hidden by
    the former mixed profile: R-190 environmental OOM, invalid observations
    after a valid manifest, and entry-only v3 insufficient capacity;
  - independent review returned NO-GO for allowlisting them; focused
    transactional tests now cover all three, and Clang 22/GCC 16 each pass
    all five partial-graph gates;
  - the pre-test artifact is invalid as a contract seed; two independent
    post-test-change Ubuntu LLVM 18.1.3 canonical runs remain mandatory;
  - raw coverage is 93.3702% lines and 90.8696% branches;
  - proof-adjusted coverage is 96.1320% lines and 92.4779% branches;
  - independent post-implementation verdict is **GO with zero local design
    blockers**;
  - independent cross-toolchain audit rejected MinGW admission, then returned
    **GO with zero blockers** for the sole Ubuntu LLVM 18 contract and explicit
    version binding;
  - independent audit returned GO for canonical/supplemental separation with
    predicted canonical-only adjusted coverage of 95.79% lines and 91.59%
    branches;
  - two independent post-fix Ubuntu LLVM 18.1.3 canonical artifacts now have
    identical target totals, exact missing sets, profile identity, raw
    93.3702%/90.8696% and adjusted 96.1320%/92.4779% line/branch coverage;
  - GitHub run 30454668805 proved all sanitized CTests and all four
    500,000-input fuzz shards, but falsified the redundant two-phase schedule:
    the count shards already ran 1,938--1,971 seconds each before four
    equivalent 900-second shards caused the 45-minute timeout;
  - independent audit returned GO to retain one four-seed 2,000,000-input
    campaign, require at least 900 seconds per seed, capture exact eleven-branch
    reachability, retain the exhaustive 952-ordinal/2,864-call failpoint gate
    and the eight-thread/100,000-sequence TSan gate, and remove only the
    duplicate time phase;
  - the former `1,000,000 sequences plus 10 minutes per stateful fault target`
    requirement is revoked: no distinct stateful/fault mutation grammar
    existed. Exhaustive ordinal injection and deterministic retry prove the
    fault space directly instead of relabeling duplicate random fuzz;
  - final GitHub run
    [`30471669754`](https://github.com/moshkinyevhen/resonith/actions/runs/30471669754)
    passed all nine evidence jobs and the aggregate mobile gate on source
    revision `ecfee1a3ed4a2a62848da91c91acc098f873cbd6`;
  - the sanitizer/fuzz job completed in 32 minutes 49 seconds, 20/20 sanitized
    CTests passed, and four fixed seeds completed exactly 500,000 units each,
    at least 900 seconds each, and 2,000,000 total with zero sanitizer findings
    or crash artifacts;
  - exact reachability covered all eleven outcomes at least 100 times; all 952
    allocation ordinals and 2,864 calls reproduced trace hash
    `56204c224ae7c4c3` and terminated with zero live allocations;
  - the eight-thread/100,000-sequence TSan gate, Android, Apple, Linux,
    canonical semantic coverage, and final aggregate gates passed;
  - the sanitizer artifact's 13/13 and coverage artifact's 11/11 SHA-256
    inventories matched locally;
  - companion test run
    [`30471677677`](https://github.com/moshkinyevhen/resonith/actions/runs/30471677677)
    passed all ten repository test jobs;
  - the final independent auditor returned **GO with zero remaining Step-9
    blockers**. Step 10 remains the final R-191 conformance and admission
    decision.
- Evidence:
  [R-202 Stateful ABI and Semantic Coverage Gate](results/R202_STATEFUL_ABI_COVERAGE_GATE_2026-07-29.md).
- Evidence boundary:
  this is test and coverage infrastructure only. It does not trigger the R-198
  music/Opus gate and does not admit R-191.
- Review:
  [R-202 Stateful ABI-v3 Fuzz and Failpoint Preflight](reviews/R202_V3_FUZZ_AND_FAILPOINT_PREFLIGHT_2026-07-29.md).

## R-203 — Final R-191 Admission Remediation

- Status: **INDEPENDENT REMEDIATION GO — CURRENT ADMISSION NO-GO**
- Date: 2026-07-29
- Problem:
  Step 9 proves sanitizer, fuzz, allocation, concurrency, platform, and
  semantic-coverage properties, but the frozen R-197 final-admission corpus
  has not been executed. The current evidence therefore cannot admit R-191
  path output even as bounded analyzer infrastructure.
- Independently confirmed blockers:
  - the frozen case-generator document has the correct SHA-256
    `10e24fa8721dfe69c2e1be82f9ffcc83e5dc7b32da0a038d29ec46b943d761bc`,
    but no versioned executable generator, JSONL corpus, expected-status
    artifact, or admission runner exists;
  - exhaustive permutations through five observations, 64 deterministic
    permutations at six and seven observations, the 10,000-case SplitMix CPU
    campaign, and 10,000 identical CPU/CUDA cases on each tile
    `1/31/32/255/256/1024` have not run;
  - GitHub reference jobs use `unittest discover`, so the free pytest
    functions in `test_partial_graph_fixed.py` are not CI authority;
  - the independent oracle does not yet cover the complete ABI-v3 report,
    22-event ledger, field-wise input/output fingerprint law, and every
    precedence status;
  - the exact-small brute-force test currently selects from native-produced
    candidate paths and therefore does not independently prove completeness of
    the native family union;
  - v3 layout assertions cover only selected offsets, while the frozen
    contract requires every field across C, C++, and Python;
  - the public v2 comment describes a working analyzer although the retained
    symbol is an unconditional no-write `UNSUPPORTED_VERSION` migration stub;
  - the fixed hostile corpus does not yet cover every status, event kind,
    hard-ceiling boundary, maximal depth, arena transition, and CUDA error
    class;
  - successful payload publication still contains ledger/health failure
    branches after the first caller path byte is written;
  - no single semantic JSONL/hash has been compared across the admitted
    Clang, GCC, MSVC, Apple, and Android implementations, and the old v2 result
    remains stale without an explicit supersession.
- Alternatives rejected:
  - declaring Step 9 sufficient is rejected because R-202 explicitly excludes
    final R-191 admission;
  - adding more undirected fuzz iterations is rejected because random
    reachability does not prove the frozen finite oracle, every ABI field, or
    exact CUDA tile parity;
  - using one native implementation as generator, oracle, and comparator is
    rejected as circular;
  - reducing the frozen 10,000-case or six-tile floors is rejected because it
    would silently change the audited R-197 hypothesis.
- Accepted remediation package:
  1. create one versioned orchestrator around separate independent case
     generator/oracle, native ABI/transaction runner, CUDA runner, and
     cross-toolchain comparator;
  2. publish the exact generated JSONL and its hash, execute the complete
     frozen finite, CPU, CUDA, hostile, boundary, and two-pass campaigns, and
     retain raw outputs;
  3. make the Python oracle an explicit pytest CI authority and remove circular
     candidate reuse from exact-small proof;
  4. assert every packed v2/v3 C/C++/ctypes size and offset and exhaustively
     prove the v2 no-write stub;
  5. independently serialize every fingerprint field, compare preflight/fill
     twice, mutate every serialized field one at a time, and compare complete
     paths, entries, reports, event counts, statuses, and output hashes;
  6. before the first caller payload write, finish all staging, fingerprint,
     resource-health, report, and cleanup-reservation checks, then consume
     payload-plus-report commit tokens once. The remaining copy tail must be
     branch-free, allocation-free, ledger-free, and statically
     no-throw/trivially-copyable;
  7. publish one twice-replayed semantic hash across every admitted toolchain
     and supersede all stale v2/pending evidence.
- Falsifiable prediction and kill gate:
  Step 10 remains NO-GO on any corpus-hash mismatch, oracle/native payload or
  status difference, v2 write, v3 layout difference, fingerprint omission,
  preflight/fill mismatch, CUDA tile difference, toolchain semantic-hash
  difference, post-write failure path, sanitizer/leak/race/canary finding,
  resource-ceiling breach, or incomplete frozen campaign.
- R-198 boundary:
  this package changes analyzer safety and evidence infrastructure, not
  Resonith syntax, the released encoder default, encoded bytes, decoded PCM,
  or RDO. The structural publication refactor receives the focused
  identical-output exception only if successful analyzer paths, entries,
  reports, current encoded streams, and decoded PCM are proven identical
  before/after. Any semantic analyzer-output change or integration into
  typed-stream/RDO/codec behavior triggers the complete registered-music and
  maximum-effort Opus gate before acceptance.
- Independent verdict:
  **GO to implement this exact remediation package; NO-GO for R-191 admission
  until every gate passes.**
- Pre-implementation oracle finding:
  - the first independent field serializer reproduced native fingerprint lane
    zero but falsified lanes one through three;
  - the frozen law reduces `byte + 53 * lane` modulo 256 before XOR, while the
    C++ expression currently promotes both operands to `int` and can XOR a
    value through 510;
  - changing the frozen document is rejected because its reviewed SHA-256 is
    an admission input; accepting lane zero alone is rejected because all four
    lanes are normative;
  - the proposed correction is one explicit unsigned-eight-bit reduction in
    native code, followed by independent golden vectors, every-field mutation,
    twice-replayed identity, and cross-toolchain hashes;
  - independent R-198 audit requires correction of native code, not amendment
    of the frozen law. The explicit reduction remains fingerprint-law version
    one because ABI-v3/R-191 is quarantined and unadmitted;
  - no dual acceptance is allowed: old native vectors are retained only as
    rejected non-normative evidence, and an old expected fingerprint must
    produce `HASH_MISMATCH` without payload writes;
  - the correction does not trigger the music/Opus gate only if final evidence
    proves identical paths, entries, counts, scores, statuses, ledgers,
    released-encoder bitstreams and decoded PCM, plus no released encoder/RDO
    consumer of R-191. Any failure of that proof triggers the complete R-198
    gate;
  - required regression vectors cover bytes
    `0/96/97/149/150/202/203/255`, zero/one/extrema/signed/multi-record
    serializers, two preflights and two fills, stale old tokens, every
    serialized-field mutation, and exact cross-toolchain hashes;
  - the final R-203 revision must rerun the affected Step-9 sanitizer, fuzz,
    ordinal, allocation and TSan matrix. Until that and the complete Step-10
    campaign pass, R-191 remains NO-GO.
- Exact-small executable evidence:
  - the first complete independent corpus contains 9,024 cases and is
    twice-replayed through the public ABI;
  - Clang 22 and GCC 16 agree on corpus SHA-256
    `1bf354dafa223f4350b79719e9e138df2262c52f22ce51a6d028eb4e56d3a306`
    and semantic SHA-256
    `cf48eaa45b901934803b76c827f135f03278884ee25617995985cc3aca31ec2a`;
  - the corpus falsifies its usefulness as a candidate-union proof: every
    frozen case has zero canonical edges, paths, and entries because
    `detector_id` cycles across adjacent observations while the only
    same-detector gap has an insufficient frequency bound;
  - the frozen corpus remains mandatory ABI, fingerprint, status and
    permutation evidence and SHALL NOT be edited or relabeled;
  - a separate candidate-rich supplemental exact domain is blocked pending an
    independent design audit. It must supplement, never replace, the frozen
    corpus and must receive its own version and hash.
- Candidate-rich supplement verdict:
  - independent review returned GO for
    `R203-CANDIDATE-RICH-EXACT-1`, a separate 288-case finite corpus;
  - five topology profiles cover cycle chains, a branch/merge diamond and the
    exact `559/560/561 Hz` frequency boundary, crossed with unique/conflicting
    ownership, no/zero/nonzero phase, protected evidence and every
    observation permutation;
  - the supplement requires an independently coded graph-theoretic checker
    that cannot import the production ABI or the existing Python edge/path
    oracle and cannot receive native candidates;
  - closed-form edge/path counts, conflict, phase, protected-family, exact
    solver and permutation invariants are generator kill gates;
  - the frozen R-197 corpus and this supplement are conjunctive. Neither may
    replace the other.
- Review:
  [R-203 Candidate-Rich Exact Supplement](reviews/R203_CANDIDATE_RICH_EXACT_SUPPLEMENT_2026-07-29.md).
- Candidate-rich post-implementation audit:
  - independent review reproduced the 288-case corpus and its SHA-256 but
    returned NO-GO for admission;
  - blockers are incomplete raw ABI/report/22-event parity, an Authority B
    that does not yet independently judge the selected optimum, a
    non-fail-closed inventory/replay, and missing identical replay across all
    admitted toolchains;
  - the corpus and frozen contract remain unchanged; remediation is limited
    to evidence infrastructure and cannot waive production or R-198 gates.
- Review:
  [R-203 Candidate-Rich Post-Implementation Audit](reviews/R203_CANDIDATE_RICH_POST_IMPLEMENTATION_AUDIT_2026-07-29.md).
- Complete-ledger authority audit:
  - an independent audit rejected immediate implementation of a Python
    authority for all 22 work-event families;
  - eleven event families plus complete fingerprint/stage/commit laws are
    independently derivable, but merge-site traces, solver operations,
    arena-reference operations, selection/reconstruction, memory pages, and
    resource high-water are not fully defined by the frozen public contract;
  - copying C++ charge sites, importing native vectors, emulating one STL, or
    ignoring `MEMORY_PAGE` are explicitly rejected as circular;
  - R-191 stays NO-GO until a declarative solver-ledger schedule and a portable
    deterministic capacity/allocation law receive independent GO, are
    implemented, and are interpreted by a genuinely independent authority;
  - the resulting production resource/schedule change requires the complete
    registered-music comparison against the preceding Resonith generation and
    maximum-effort official Opus before admission.
- Review:
  [R-203 Complete-Ledger Authority Audit](reviews/R203_COMPLETE_LEDGER_AUTHORITY_AUDIT_2026-07-29.md).
- Portable-ledger proposal:
  - status is **INDEPENDENT NO-GO; SUPERSEDED BEFORE IMPLEMENTATION**;
  - the audit found that a witness trace cannot prove omitted operations,
    PMR cannot force exact vendor-independent vector capacity, allocation-site
    instances/lifetimes were incomplete, maximum reservation could change
    statuses, and the 288-case scope was unsafe for production;
  - no production implementation was started.
- Preflight:
  [R-203 Portable Ledger Schedule Preflight](reviews/R203_PORTABLE_LEDGER_SCHEDULE_PREFLIGHT_2026-07-29.md).
- Evidence-split proposal:
  - status is **TWO-AUDITOR GO; EVIDENCE-ONLY IMPLEMENTATION AUTHORIZED**;
  - cross-toolchain identity remains mandatory for all semantic output and all
    21 non-memory CPU event counts;
  - `MEMORY_PAGE` and managed upstream-request byte telemetry remain exact,
    bounded, twice-repeatable, and fail-closed per toolchain, but are reported
    rather than falsely required to equal vendor-specific STL request traces;
  - fourteen closed event laws receive independent exact derivation; seven
    dynamic solver families receive independent conservative loop/total
    bounds, complete charge-site inventory, remove/reclassify mutants,
    identity, prefix-budget, coverage, and cleanup gates without an
    unsupported exact-formula claim;
  - resource replay uses ordered pointer-independent
    prepare/outcome/commit/cancel/release identities and admits zero regression
    for unchanged toolchain inputs;
  - the no-failure-after-publication rule remains absolute. Release-callback
    removal/reorder and release-ledger-consumption mutants are mandatory; an
    invalid post-publication transition is evidence failure, not an accepted
    caller-visible failure path;
  - amendment `R203-EVIDENCE-SPLIT-1` explicitly supersedes R-197's
    cross-toolchain resource-telemetry identity clause and the conflicting
    R-203 complete-report/all-22-event independent-oracle clauses;
  - the proposal changes evidence comparison only and cannot alter production
    ABI, solver, bitstreams, decoded PCM, or player behavior.
  - the final audit required and received one last correction: Class-A
    cross-toolchain status identity applies only outside resource/fault
    triggering calls; tight-budget, OOM, allocation, cleanup, release, and
    injected-failure calls use local expected status, no-write, cleanup, and
    repeatability gates.
  - a second independent audit then returned NO-GO: Revision 3 now explicitly
    supersedes the conflicting R-203 complete-report/22-ledger oracle clauses,
    freezes all 288 ordinary fixture IDs as Class A/B before execution, and
    retains the absolute no-failure-after-publication rule with mandatory
    release-callback and release-ledger mutants;
  - evidence-split code written between the two verdicts is unadmitted scratch
    until both auditors approve the current text;
  - both auditors returned binary GO after an exhaustive field partition was
    added for every ABI-v3 report field; the approved preflight SHA-256 is
    `c9f736288e67f69622812149c2ab86e5f54439c9778bcf57068acd8b6585aa74`.
- Preflight:
  [R-203 Semantic Ledger and Resource Telemetry Split](reviews/R203_SEMANTIC_LEDGER_TELEMETRY_SPLIT_PREFLIGHT_2026-07-29.md).
- Interim evidence:
  [R-203 Candidate-Rich Interim Evidence](results/R203_CANDIDATE_RICH_INTERIM_2026-07-29.md).
- Dynamic charge-site mutation substep:
  - the first independent audit returned NO-GO for implementation because no
    reviewed AST inventory, witness map, independent bound table, native
    mutant generator, or mutation CI gate existed;
  - grep/line-number inventories, copied native logic, production site IDs and
    automatic golden regeneration are rejected;
  - the revised candidate is a pinned Clang-AST bijection plus test-only
    temporary-source remove/reclassify mutants, one immutable witness per
    helper invocation, declarative finite bounds, runtime rejection, and
    production object/bitstream/PCM identity;
  - current orientation finds 36 dynamic-family references and therefore 72
    candidate mutants, but neither count is admitted until AST extraction and
    independent audit pass;
  - production source or object changes are outside this evidence-only
    substep and trigger a separate audit and the applicable R-198 gate.
- Preflight:
  [R-203 Dynamic Charge-Site Mutation Preflight](reviews/R203_DYNAMIC_CHARGE_SITE_MUTATION_PREFLIGHT_2026-07-29.md).
- Preflight audit:
  - an independent auditor returned binary GO on exact preflight SHA-256
    `253d18a9061560ab05a4650b7b36c305f85904fed114d648462ca3cbe6cb092b`;
  - authorization is limited to the specified test-only AST inventory,
    witnesses, finite bounds, isolated mutants, and identity evidence;
  - no result, R-191 admission, production/native change, post-implementation
    audit, Step-10 campaign, or R-198 obligation is waived.
- Audit:
  [R-203 Dynamic Charge-Site Preflight Audit](reviews/R203_DYNAMIC_CHARGE_SITE_PREFLIGHT_AUDIT_2026-07-29.md).

## R-204 — Continuous Execution and Resumable 63-Step Plan

- Status: **ACCEPTED PROJECT EXECUTION CONTRACT**
- Date: 2026-07-30
- Supersedes:
  - ambiguous persistence wording in R-194 only where R-204 is stricter;
  - it does not supersede R-185, R-196, R-198, dependency order, quarantine,
    kill, safety, authority, publication, release, credential, or destructive
    action gates.
- Decision:
  - while the project owner has explicitly authorized execution of the
    continuous Resonith plan, passing a test, audit, subtask, generation,
    alpha, beta, or release candidate is a checkpoint rather than project
    completion;
  - continue with the earliest dependency-ready, safe, in-scope action while
    an authorized item remains;
  - the canonical authority is the versioned
    `docs/20_LSPF_MASTER_EXECUTION_PLAN.md`, accepted decisions, and their
    dependency and quarantine gates;
  - the complete 63-step operational panel is a derived, versioned view with
    stable step IDs. It must not be shortened, regrouped, renumbered,
    reordered, reconstructed from memory, or used to override the canonical
    plan. Its definition, hash, mapping, status, evidence, and current
    checkpoint must remain durably restorable;
  - the accepted definition is panel `R204-63-V1` at
    `docs/23_CONTINUOUS_63_STEP_EXECUTION_PANEL.md`, SHA-256
    `6b2d1e21436e22231538d1b362657375c3699892b5290d17843ae025f510684e`;
    mutable state is retained separately in
    `docs/execution/R204_CURRENT_CHECKPOINT.md`;
  - continuation never expands authority. Silence does not authorize pushes,
    publication, releases, paid services, credentials, destructive or
    irreversible actions, production or user-data mutation, or unrelated work;
  - any clear owner instruction to stop, pause, wait, reprioritize, supersede,
    or narrow the task controls in any language.
- Evidence-generation rule:
  - one materially scoped codec-algorithm hypothesis and its tightly coupled
    edits form one frozen evidence generation;
  - focused risk-based tests run after each implementation edit;
  - before accepting that generation or starting another algorithm generation,
    run the complete versioned registered-music manifest through the actual
    decoders from identical source PCM;
  - compare the candidate with the immediately preceding accepted Resonith
    generation and the frozen current maximum-effort official Opus anchor;
  - retain English machine-readable and written per-file and aggregate
    complete bytes, bitrate, quality, spectral, phase, transient, channel,
    runtime, CPU/GPU, memory, hash, fallback, win, loss, and regression
    evidence;
  - external publication remains separately authorized;
  - only a proven bitstream- and decoded-PCM-identical mechanical refactor may
    use the focused R-198 exception.
- Pause conditions:
  - an unambiguous owner stop, pause, wait, reprioritization, supersession, or
    scope reduction;
  - completion of the approved plan;
  - a safety, security, privacy, legal, integrity, host-stability, storage,
    compute, cost, or evidence-retention risk;
  - missing authority, approval, credential, artifact, platform, or external
    dependency without an authorized evidence-equivalent alternative;
  - conflicting workspace changes, baseline/corpus/tool/hash drift,
    irreproducibility, dependency or quarantine failure, mandatory audit
    NO-GO, admission kill gate, or material ambiguity;
  - a hard resource, tool, session, or execution-window limit.
- Blocker behavior:
  - never bypass authority, credentials, immutable evidence, quarantine,
    dependency, or audit gates;
  - a NO-GO blocks promotion and dependent work, but explicitly authorized
    remediation or another independently dependency-ready branch may continue;
  - a failed kill gate rejects or redirects the candidate; it does not justify
    rescuing the same failed mechanism by uncontrolled complexity.
- Resumable checkpoint:
  - on every pause, blocker, or platform-imposed yield, record the panel
    version/hash, all 63 stable step states, repository revision and worktree
    state, active step and evidence generation, incumbent Resonith and Opus
    identities, completed commands, tool versions, evidence paths and hashes,
    blocker, clearance authority, invalidation conditions, and next safe
    action;
  - a status yield is not project completion;
  - verify identities before resuming. An explicit owner pause requires an
    explicit owner resume.
- Independent audit:
  - initial wording received **NO-GO** because it treated one stop word as
    exclusive, left the panel unversioned, blurred edit and generation test
    timing, implied publication authority, and incentivized bypass attempts;
  - every blocking finding was accepted and resolved in the rule above;
  - the corrected R-204 wording received independent binary **GO** before this
    decision was recorded.

## R-205 — Family-Separated Dynamic-Bound Authority

- Status: **AUDIT CANDIDATE; PRE-IMPLEMENTATION NO-GO**
- Date: 2026-07-30
- Scope:
  - evidence-only closure of the two remaining R-203 dynamic-bound authority
    defects;
  - no production source, header, ABI, solver, bitstream, decoded PCM, codec
    algorithm, or player change;
  - R-198 is not triggered unless that boundary is violated.
- Frozen problem:
  - the rejected runner summed `selection-pair-local` and
    `exact-set-local` allowances before checking the shared native `SELECT`
    event. One family could therefore exceed its own bound while unused margin
    in the other hid the violation;
  - only candidate-rich and exact-small corpora entered bound replay. Native
    conformance, bounded greedy, allocation-ordinal, and state-arena
    contributors supplied coverage but no machine-checked bound evidence;
  - the previous hostile-greedy label replayed the ordinary greedy fixture and
    did not create a genuinely resource-constrained rejection.
- Considered alternatives:
  - keep one summed `SELECT` bound: rejected because it cannot prove either
    local family;
  - subtract exact and greedy executions: rejected because both paths share a
    `SELECT` prologue;
  - reclassify whole families into spare event IDs: retained only as an
    optional cross-check because destination events may contain unrelated
    work;
  - reproduce the production solver CFG in Python: rejected as copied,
    implementation-coupled logic rather than an independent bound authority;
  - use source coverage alone: rejected because reachability does not bind
    charge amount, family ownership, phase passes, or per-contributor input
    ceilings;
  - add fixed test-only per-site accounting to a temporary source copy:
    selected as the smallest mechanism that observes family ownership without
    changing production behavior.
- Authorized design:
  1. Freeze an amendment containing a bijective partition of all 36 dynamic
     sites, including exclusive ownership of every `SELECT` site by exactly one
     of `selection-pair-local` or `exact-set-local`.
  2. Generate a temporary instrumented `partial_graph.cpp` from the frozen
     production bytes. Production source/header/library files remain untouched.
  3. Give every site fixed-capacity checked counters for attempted, completed
     emit, reserve, cancel, and consume units. No heap allocation, exception,
     codec decision, semantic output, or caller-visible ABI may depend on this
     telemetry.
  4. Statically prove from the frozen AST that every instrumented dynamic-site
     call charges exactly one unit. Fail closed on a non-unit amount, overflow,
     duplicate site, missing site, operation mismatch, or source/hash drift.
  5. Record actual analyzer-pass counts and per-call public input ceilings.
     Check them against a versioned pass-ceiling contract instead of assuming
     the former unlabelled `1/2` multipliers.
  6. For every successful phase, require:
     - completed site units grouped by event equal the native event ledger;
     - `selection-pair-local` site units independently satisfy only their
       formula;
     - `exact-set-local` site units independently satisfy only their formula;
     - their sum equals the native `SELECT` count;
     - reserve/cancel/consume balance is valid and no telemetry overflow or
       truncation occurred.
  7. Replay and bind distinct contributor IDs for candidate-rich, native
     conformance, ordinary greedy, exact-small, every allocation ordinal,
     every state-arena subcase, and a genuinely tight-budget hostile greedy
     rejection. No contributor may be missing, empty, duplicated under another
     name, or silently replaced by a different fixture.
  8. Preserve exact Class-A semantics and ordinary Class-B native output
     between the production library and instrumented build. Telemetry is
     implementation-conformance evidence only; independent authority remains
     the frozen formulas, public input limits, AST bijection, contributor
     manifest, and negative mutants.
- Mandatory negative evidence:
  - one wrong-family mutant for every `SELECT` site;
  - missing, duplicated, wrong-unit, and wrong-operation site mutants;
  - pass-count under/over-report and contributor omission/duplication mutants;
  - ledger/site-sum disagreement and counter-overflow mutants;
  - a tight-budget hostile-greedy case that reaches the greedy lane and returns
    the declared typed rejection without partial publication.
- Frozen production identities:
  - source SHA-256:
    `ecbc3fcbbb9cd5d38d21d93375503fc05f0b188d33273f27cd0a211010e2df05`;
  - header SHA-256:
    `12733d20b54be6209455800f477bfce9b84951d74699972a646dc492b803d49e`;
  - production shared-library SHA-256:
    `f12c6ad9061089d2d4088a5bfd2e20e845148ebcd303afaecc3bb2dc6be042ed`.
- Kill gates:
  - any frozen production identity changes;
  - any site lacks exactly one local family or belongs to two local families;
  - any contributor lacks complete bound and identity evidence;
  - any telemetry path affects ordinary semantic or Class-B output;
  - any local, event, aggregate, pass, prefix, transaction, or resource bound
    is exceeded or hidden by another allowance;
  - any automatically regenerated golden value replaces independently frozen
    evidence.
- Independent audit:
  - the first orientation auditor confirmed both original defects and
    recommended the bounded evidence-only direction;
  - the frozen-document auditor returned **NO-GO** before implementation:
    audit status had been pre-recorded, pass counts were bounded rather than
    exact, the new manifest and contributor cardinalities were unfrozen,
    telemetry API/capacity/concurrency/slot placement were ambiguous,
    reservation and failure-prefix equations were incomplete, hostile-greedy
    identity and threshold were unfrozen, the negative-mutant matrix had no
    exact cardinality, and hostile production/instrumented parity was omitted;
  - no R-205 implementation code was started;
  - the current runner, the 72-mutant campaign, R-203 admission, S09 completion,
    S10, predictor work, syntax work, and any compression claim remain
    **NO-GO** until a corrected frozen design receives independent binary GO.

### R-205 V2 frozen audit candidate

- Status: **PRE-IMPLEMENTATION NO-GO; INDEPENDENT AUDIT PENDING**
- Supersedes: the R-205 V1 implementation design, while retaining its NO-GO
  findings as negative evidence.
- Frozen V2 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V2_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `481a75b3b752ca5aac1c046d1a71843f1e62dfca9dcf08abab0733b8c9f2aa94`;
  - `native/tests/r205_family_bound_authority_v1.json`, schema
    `resonith-r205-family-bound-authority-1`, SHA-256
    `d02dcdced3707b34f4902b045f5e6eb6d1e68a4d0972689236e67de9172dd509`.
- Corrections:
  - replaced arbitrary pass ceilings with exact validation/solver epoch
    anchors and finite call-kind/status prefix traces;
  - selected one private test C API, one active call, one fixed record, 36 site
    slots, 22 event slots, and explicit no-heap/no-exception behavior;
  - froze source-hook AST bijection, slot and sequencing proof, and the exact
    production compile-command delta;
  - replaced the ambiguous contributor partition with exactly 10,276 expanded
    contributor IDs and 19,596 discovery/admission call records;
  - froze the seven contributor classes, all 952 allocation ordinals, all nine
    state-arena subcases, and the deterministic hostile-greedy input and
    threshold law;
  - defined prefix reservation, event-ledger, no-write, and hostile
    production/instrumented parity equations;
  - froze an exact 285-mutant negative matrix;
  - split implementation/discovery from admission: pre-implementation GO may
    authorize only the private evidence harness, and a second binary GO on
    exact generated identities is required before admission replay.
- Boundary:
  - no R-205 implementation code exists at this checkpoint;
  - the frozen V2 hashes are now submitted to the independent auditor;
  - S09 remains active and every dependent action remains NO-GO until that
    auditor returns binary GO.

### R-205 V3 corrected audit candidate

- Status: **PRE-IMPLEMENTATION NO-GO; INDEPENDENT AUDIT PENDING**
- V2 self-red-team result: **NO-GO before external audit completed**.
  - V2 modeled only V3 path validation/solver epochs even though 26 frozen
    allocation ordinals exercise the R190 edge API;
  - R190 has an intentional no-op work sink and no V3 report, so claiming
    native-ledger equality for it would be false;
  - the nine state-arena subcases were outside every V2 epoch.
- Frozen V3 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V3_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `c49a89fb831c845e3d8d5576e68b8ab06db16cc6992a64d01ae43df00fda4ad3`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V3`, SHA-256
    `c453495e86eed7a2912d013aaf4e096cd3264f3eb3ea51cfce775cab715df692`.
- V3 corrections:
  - separate exact path-validation, path-solver, edge-validation,
    edge-enumeration, and named state-arena epoch families;
  - honest `logical-site-formula-only` evidence for R190 rather than inventing
    a native work ledger;
  - native event equality remains mandatory for ledger-bearing V3 path and
    arena evidence;
  - one arena probe record contains exactly nine named subrecords;
  - the corrected total is 19,588 discovery/admission call records;
  - the exact negative matrix is 300 mutants after adding all five epoch
    families and illegal-overlap evidence.
- Boundary:
  - no implementation code is authorized or present;
  - V3 replaces V2 for the next independent pre-implementation audit;
  - every S09-dependent action remains NO-GO until binary GO.

### R-205 V4 phase-resolved audit candidate

- Status: **INDEPENDENT PRE-IMPLEMENTATION NO-GO**
- Independent V3 result: **NO-GO**.
  - one global 36-site counter set could not identify how repeated merge sites
    divided work between edge validation and two edge enumerations;
  - V3 froze right-hand-side edge/arena limits without freezing every measured
    left-hand-side numerator.
- Frozen V4 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V4_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `54bdb12c22af946c4aef6bdaeece53e0177264d6e3adbaaa0527f23f6e3e7de8`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V4`, SHA-256
    `6ebac9d495e9daab43ae4d249bd4a89e3de2f5ab689b63c495d8227c86c7949a`.
- V4 corrections:
  - fixed `epoch[17] × site[36] × operation[5]` checked counters;
  - opening/closing `total`, `reserved`, `counts[22]`, and
    `reserved_counts[22]` for every ledger-bearing epoch/subrecord;
  - exact path, edge-validation, edge-enumeration, and arena left-hand-side
    aggregation rules;
  - canonical logical JSON serialization; raw private-struct hashing is
    forbidden;
  - a compile-time private-record upper bound of 65,536 bytes;
  - eighteen new phase-resolution, snapshot, numerator, capacity, and
    serialization mutants, for exactly 318 total.
- Boundary:
  - no implementation code is authorized or present;
  - two independent auditors rejected V4:
    - `input_fingerprint_v3` executed one frozen dynamic merge site outside
      every declared epoch;
    - the machine authority required global boundary `reserved=0` while
      production intentionally retained an unrelated `COMMIT_RECORD`
      reservation;
  - S09 remains active and S10 remains pending.

### R-205 V5 outer-fingerprint and reservation audit candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V5 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V5_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `d5f837dbdcc7df1dbc35075da984a5cbf892bfb710269e3bbf4d94d02fcf64f8`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V5`, SHA-256
    `f414c0b9437f83c48cc065405d11bd681d7e60fe1bb685c5248be2158df33036`.
- V5 corrections:
  - eighteen fixed epochs: three path-validation, two path-solver, one V3
    input-fingerprint, one edge-validation, two edge-enumeration, and nine
    named arena subcases;
  - an exact `F1` trace and a ledger-bearing local numerator for the
    `input_fingerprint_v3` merge;
  - explicit AST-falsifiable outer-region coverage: the V3 outer canonical
    snapshot and output fingerprint invoke no frozen dynamic sites;
  - zero boundary reservation for each dynamic event independently, while
    retaining and permitting unrelated wrapper reservations in the full
    snapshots;
  - exact arena equality after dynamic-event ownership;
  - a 65,536-byte fixed private-record ceiling;
  - exactly 326 typed negative mutants.
- Validation:
  - JSON parse passed;
  - epoch assignment is exactly `18/18`;
  - the negative matrix recomputes to `326/326`;
  - contributor and public-call cardinalities remain `10,276` and `19,588`;
  - the V5 authority and preflight contain zero Cyrillic text.
- Boundary:
  - no telemetry or production implementation is authorized yet;
  - the split-authority auditor accepted the runtime epoch model and arithmetic
    but rejected the stage-2 authority because the machine artifact list
    omitted both the complete epoch-record set and production/instrumented
    parity set;
  - the resource auditor rejected the full-ledger authority because it lacked
    direct mapping and conservation laws, fixed `COMMIT_RECORD` boundary
    semantics, and typed wrapper-reservation mutants;
  - S09 remains active.

### R-205 V6 immutable discovery and full-ledger audit candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V6 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V6_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `76ec68383948de20d61fb78c29f9b575b4e83cb65c20b7aac12e3adfd1eb618e`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V6`, SHA-256
    `dc73384b7433e2277e6c69aed543859fb299c2110b7e4bd7a2857c2973578a10`.
- V6 corrections:
  - direct opening/closing copies of `total`, `reserved`, all 22 counts, and
    all 22 reserved counts, enforced by AST validation;
  - full-ledger `total=sum(counts)` and `reserved=sum(reserved_counts)`
    conservation;
  - exact `COMMIT_RECORD=1` boundary semantics for every V3 path, solver, and
    input-fingerprint epoch;
  - mechanically first nonzero opening and closing `MEMORY_PAGE` witnesses;
  - exact deterministic call plan for all 19,588 records;
  - canonical 19,588-line epoch-record and parity JSONL artifacts;
  - ten-entry stage-2 payload manifest whose own root hash is published
    externally, avoiding a self-referential hash;
  - twelve new full-ledger snapshot mutants and eight immutable-freeze
    mutants, bringing the exact total to 346.
- Validation:
  - JSON parse passed;
  - epoch slots remain `18/18`;
  - negative arithmetic is `346/346`;
  - the call plan is `19,588/19,588`;
  - the authority defines ten payload artifact identities plus one external
    freeze-manifest root identity;
  - the V6 authority and preflight contain zero Cyrillic text.
- Boundary:
  - the split-authority auditor rejected the impossible inclusion of the
    post-audit admission call in the 19,588 pre-audit executed records;
  - the resource auditor rejected a `MEMORY_PAGE` witness that identified only
    a record, not one exact epoch/boundary/event cell or its selection proof;
  - S09 remains active.

### R-205 V7 stage-separated and cell-addressed audit candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V7 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V7_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `dd02bb90dfbf46adc0adb6dbf0ed9217b988593d9f4129ca8db1e5ddf0a29c1a`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V7`, SHA-256
    `270f7be5ca3bf2e2d967ea116cc99efcad892070c77c2fa4bdcaa39df6255efc`.
- V7 corrections:
  - exactly 19,587 executed discovery records before stage-2 audit;
  - one immutable expected-admission specification with exact budget,
    threshold receipt, status, site deltas, and no-write result;
  - exactly one observed post-audit admission record, kept outside and unable
    to modify the audited discovery root;
  - a total witness-cell order over record ordinal, epoch slot, opening/closing
    boundary, and fixed `MEMORY_PAGE` event index 17;
  - explicit record ordinal, slot, boundary, event, value, record hash, prefix
    count, and zero-prefix hash for opening and closing witnesses;
  - a third independent result audit before the original 72-mutant campaign,
    R-203/R-191 admission, or S10;
  - five stage-boundary and seven witness-selection mutants, bringing the
    exact negative total to 358.
- Validation:
  - JSON parse passed;
  - stage-1 call arithmetic is `19,587/19,587`;
  - stage 1 plus one admission is `19,588`;
  - negative arithmetic is `358/358`;
  - stage 2 binds eleven payload artifacts under one external root hash;
  - the V7 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors accepted the stage split and exact witness-cell proof;
  - both rejected the underidentified admission role because it did not freeze
    preflight versus fill, pointers, capacities, initial buffers, payload hash
    domains, expected fingerprint, or the exact discovery source of `B`;
  - S09 remains active.

### R-205 V8 exact fill-topology audit candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V8 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V8_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `3ee15d0fc6550699fb448dffe268c5a8c7b1d2451684448971b3a72f2d96704c`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V8`, SHA-256
    `6c47d773c4a284319af7dc7ef248e519ee226b2a6d937ab18a063ed90a16d8a3`.
- V8 corrections:
  - exact preflight and fill discovery topologies;
  - threshold source fixed to the ample discovery-fill record;
  - `B=ledger.total+ledger.reserved` at the target, plus proof that every
    earlier operation fits and the target unit does not;
  - admission fixed to a non-null fill using preflight-required capacities,
    `0xA5` path bytes, `0x5A` entry bytes, and a valid frozen report header;
  - separate exact path, entry, and report pre-call hash domains;
  - independent no-public-ABI Python derivation of the four expected
    fingerprint qwords for budget `B`, including exact byte order and modulo
    \(2^{64}\) arithmetic;
  - exact expected status, termination, flags, incomplete trace, attempted and
    completed site deltas, and unchanged path/entry hashes;
  - one additional stage-2 derivation receipt and eight topology mutants,
    bringing the payload and negative totals to 12 and 366.
- Validation:
  - JSON parse passed;
  - stage-1 call arithmetic remains 19,587 and the complete total remains
    19,588;
  - negative arithmetic is `366/366`;
  - the V8 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors rejected the undefined threshold receipt: V8 had aggregate
    epoch/site counters but no bounded ordered-operation capture, ordinal,
    canonical commitment, capacity, overflow law, or independently replayable
    prefix proof;
  - the resource auditor additionally found that the twelve-payload root did
    not bind the instrumented binary, transformer, validators, discovery and
    admission runners, commands, or oracle bytes;
  - the negative matrix could not detect a truncated, reordered, omitted, or
    falsified earlier-operation proof or drifted evidence machinery;
  - S09 remains active.

### R-205 V9 bounded operation-trace and evidence-toolchain candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V9 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V9_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `64a2172859ce42ab51196f1acf1071701e6c60bc272a693e9477e004a3486b7d`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V9`, SHA-256
    `df90d1f562356ac14da470b0d24e8236d8b8eb2441b3c0c79a7ca4f9e1d93af9`.
- V9 corrections:
  - canonical 101-byte tuples for every `emit`, `reserve`, `cancel`, and
    `consume` ledger operation in exact zero-based ordinal order;
  - fixed-state standard SHA-256 commitment and checked prefix summaries for
    every record;
  - an independently replayable, runner-owned, preallocated trace of at most
    1,048,576 tuples and 105,906,176 bytes for only the tight discovery-fill
    record;
  - a 22-field threshold receipt proving state continuity, complete successful
    prefix, `required_capacity<=B` before the target, and target
    `required_capacity=B+1`;
  - exact nested-meter/global-ledger equivalence obligations;
  - a 24-payload external root that binds the actual instrumented binary,
    transformer, validator, separate discovery/admission runners, exact
    commands, oracle bytes, operation trace, and all result authorities;
  - 36 new operation-commitment and evidence-toolchain mutants, bringing the
    exact negative total to 402.
- Validation:
  - JSON parse passed;
  - epoch assignment is `18/18`;
  - negative arithmetic is `402/402`;
  - stage-1 records remain `19,587`, followed by one separately authorized
    admission;
  - the root payload count is `24`;
  - the expected admission and threshold receipt define 26 and 22 required
    fields respectively;
  - the V9 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors rejected the false equality between every nested meter
    maximum and the then-current global remainder; the source retains a
    call-entry maximum across later direct-ledger operations;
  - the root listed 24 payloads while post-admission immutability named 23;
  - the fixed-state layout named fourteen `uint64` values although it contained
    twelve integers and two digests;
  - invalid raw events and required-capacity overflow lacked unique tuple
    encodings;
  - S09 remains active.

### R-205 V10 dominance-replay and exact-root candidate

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V10 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V10_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `8f45a64db7f4f2c666eaeb31720ccc2c0da8e50d02a42445c2a58cf8815bf985`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V10`, SHA-256
    `e26042f5be6c23b8a6112a84e6e7b1639968bf39b2b393bb9119b58b2f2d94fb`.
- V10 corrections:
  - 151-byte operation tuple V2 with full underlying-width raw event,
    canonical arithmetic-overflow sentinels, and explicit meter context;
  - correct dominance and replay laws over global footprint, report work,
    private meter reservation, origin, and the replay maximum derived from
    `B`;
  - a bounded trace of at most 1,048,576 tuples and 158,334,976 bytes;
  - exact 12-`uint64` plus two-digest fixed-state accounting;
  - 25 stage-2 payloads and 25 same-order contracts with exact IDs, paths,
    schemas, and record-count laws;
  - pre/post admission hashes for the root plus every payload, including one
    mutation per payload;
  - a non-self-referential typed external root-hash slot whose only realized
    substitution is recorded after admission;
  - 40 new typed mutants, including audited-root substitution attacks,
    bringing the exact negative total to 442.
- Validation:
  - JSON parse passed;
  - epoch assignment remains `18/18`;
  - negative arithmetic is `442/442`;
  - stage-1 records remain `19,587` plus one separate admission;
  - payload and artifact-contract identity/order is exactly `25/25`;
  - expected admission and threshold receipt define 27 and 23 fields;
  - the V10 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors accepted the meter-dominance direction but rejected the
    rooted negative-matrix contract: authority declared 442 mutants while the
    root required 437 records;
  - direct-ledger tuples fixed absent meter integers but left
    `meter_context_valid` ambiguous;
  - raw-event truncation lacked an explicit non-vacuous value above 255;
  - S09 remains active.

### R-205 V11 exact-mutant and canonical-context amendment

- Status: **PRE-IMPLEMENTATION NO-GO; ONE INDEPENDENT GO AND ONE INDEPENDENT NO-GO**
- Frozen V11 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V11_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `5eeb56c40fb59ce97812f79d18d73be03390e3a1eec161a67289bb4549d02761`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V11`, SHA-256
    `a0c5e4347d037c2b43c9adea186bd9fc4e95e79de01a7d3a6f00b57e471d828f`.
- V11 corrections:
  - the declared matrix, computed sum, rooted expansion, and future JSONL line
    count are exactly `443`;
  - direct-ledger tuples canonically require `meter_present=0`,
    `meter_context_valid=0`, and five `UINT64_MAX` meter fields;
  - a new mutant rejects the alternative absent-context flag;
  - exact private canonicalization probes include raw events 256, 511, and
    4,294,967,295, so byte-truncation mutations are non-vacuous;
  - all 25 artifact paths advance to V11 without changing their identities,
    schemas, order, or other cardinalities.
- Validation:
  - JSON parse passed;
  - negative arithmetic and root contract are `443/443`;
  - root IDs and contracts remain `25/25`;
  - V11 authority and preflight contain zero Cyrillic text.
- Boundary:
  - the split-authority auditor returned GO;
  - the resource/canonicalization auditor rejected label-only probe cases that
    did not freeze complete 25-field inputs, expected hashes, or force the
    actual instrumented encoder to process them;
  - S09 remains active.

### R-205 V12 byte-exact encoder probe amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V12 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V12_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `6185c33802a4d53b8a9a5eab8b14f886ca6909ccab25ac11d7115339ce7400d7`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V12`, SHA-256
    `4286a880adf741c3ac6284a525dd9548b08e4f72a5a2bc62b225df4d07cfa339`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V12 corrections:
  - twelve complete 25-field probe cases in exact tuple order;
  - twelve independently recomputed expected SHA-256 values over exact
    151-byte outputs;
  - raw events 256, 511, and `UINT32_MAX`, plus global/meter overflow cases;
  - a private C API that must call the same single C++ tuple encoder as the
    real ledger observer;
  - an independent Python serializer forbidden from loading the instrumented
    library;
  - AST rejection of a second, copied, or probe-only C++ encoder;
  - the probe corpus as a required-hash root payload, increasing root
    cardinality to 26;
  - eight new root/probe mutants, bringing the exact total to 451.
- Validation:
  - all 12 case vectors contain 25 fields;
  - all 12 expected hashes independently recompute;
  - authority hash and required probe SHA-256 agree;
  - negative arithmetic and root contract are `451/451`;
  - root IDs and contracts are `26/26` in identical order;
  - V12 authority, probe corpus, and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors found the same surviving implementation: the real observer
    can truncate `event` before the shared encoder while the probe injects the
    full-width value directly;
  - V12 proved the encoder but did not prove pre-encoder observer field
    construction;
  - S09 remains active.

### R-205 V13 real-ledger semantic-probe amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V13 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V13_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `134a63653c355247966b59833154b90879b6d5737a6f21377ae4192ecd259059`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V13`, SHA-256
    `2e859a00fa9386e27fdba5f22063cf988334b19e9c9efc47a97d46c6e0345d7b`;
  - `native/tests/r205_observer_semantic_probes_v1.json`, SHA-256
    `015e86ab3e96743a6ab162ef9cf5e118e3c7d91180965a1e67c6c3bad932713c`.
- V13 corrections:
  - the probe runner supplies only fourteen semantic inputs, never tuple
    fields, derived capacity, result, after state, or canonical bytes;
  - the injected C API constructs a real ledger and invokes exactly one real
    `emit`, `reserve`, `cancel_reserved`, or `emit_reserved` method;
  - the real methods and semantic probe therefore traverse the same sole
    observer field builder and the same sole encoder;
  - `event_raw` is derived only inside the builder from the complete unsigned
    enum-underlying representation, with narrow intermediates and masks
    forbidden;
  - the independent oracle derives all 25 fields from semantic state before
    serializing and checking the twelve frozen hashes;
  - fourteen observer/probe dataflow mutants bring the exact negative total to
    465.
- Validation:
  - JSON parse and two independent structural passes succeeded;
  - all 12 semantic cases independently derive the 25 expected fields and
    frozen hashes;
  - the frozen C++23 toolchain confirms a 32-bit enum underlying
    representation;
  - negative arithmetic and the root contract are `465/465`;
  - root IDs and contracts are `26/26` in identical order;
  - V13 authority, semantic corpus, and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors rejected the attempt to pass 255, 256, 511, and
    `UINT32_MAX` through real C++ ledger methods because the non-fixed enum's
    language-defined range is only 0 through 31;
  - an out-of-range cast or reconstructed object has undefined behavior, so
    its observed hashes cannot be evidence;
  - R-205 is evidence-only and does not replace the mandatory S12
    registered-music comparison after algorithm step S11;
  - S09 remains active.

### R-205 V14 defined-enum observer and typed-encoder separation

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V14 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V14_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `e0d1081b1388cdd336587b9c4ac8433ff253f7616841b774c17bfc10bf2e8f69`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V14`, SHA-256
    `813dec26c602e67b4a4cb97a369fe996011442bc582dcd5e2e5323ed3c7406d5`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V14 corrections:
  - real ledger calls use only defined enum values 0 through 31;
  - valid 0/21 and defined-invalid 22/23/24/30/31 exercise the real methods,
    observer field builder, and encoder;
  - runner and C API both reject values above 31 before enum conversion;
  - one active record produces immutable ordinals 0 through 11;
  - exact AST/dataflow laws prove the absence of narrow intermediates even
    when current defined values would make an eight-bit truncation
    behaviorally invisible;
  - a separate typed `uint64` encoder probe retains 256, 511, and
    `UINT32_MAX` without constructing an enum or claiming observer
    equivalence;
  - the second root payload and out-of-range-enum mutant bring exact root and
    negative totals to 27 and 467.
- Validation:
  - both probe authorities parse and contain 12 exact cases each;
  - all semantic cases independently derive their 25 fields and hashes;
  - machine authority, matrix, and root invariants are `467/467` and
    `27/27`;
  - every stage-2 artifact path is V14 and unique;
  - V14 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - one auditor found an impossible call-graph contract: all direct encoder
    calls were forbidden while the typed encoder probe required one;
  - the other found a value-domain hole: finite probes omitted epochs 9
    through 17, allowing a branchless encoder corruption to pass;
  - S09 remains active.

### R-205 V15 exact encoder-template and two-caller amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V15 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V15_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `6256f3b1701b7997af1764301bf0e1b97c36e3ca8f63f8e973d7954c46edbad3`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V15`, SHA-256
    `12c0afe87df77ece65e04c55e6320e5362021b65982bf64913e506708b3b73a1`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V15 corrections:
  - the sole encoder has exactly two callers: the field builder and one named
    test-only typed probe;
  - the test-only direct caller is unreachable from all production,
    discovery, admission, ledger, observer, and semantic-probe graphs;
  - the encoder tuple type, 25 direct member writes, fixed offsets, `uint8`
    copy, and eight-byte little-endian helper are closed AST templates;
  - encoder values cannot enter arithmetic, masks, aliases, lookups, branches,
    or data-dependent addresses;
  - the source-template proof covers the complete `uint8` and `uint64`
    domains, including arena epochs 9 through 17;
  - one caller mutant and 86 encoder-dataflow mutants bring the exact total to
    554.
- Validation:
  - machine authority parses with `554/554` negative arithmetic;
  - root IDs and contracts remain `27/27` with unique V15 paths;
  - both unchanged probe hashes remain bound;
  - V15 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors found that a caller-supplied output span could overlap the
    tuple only for unprobed field values, allowing early writes to corrupt
    later exact reads while the encoder template still passed;
  - one auditor's separate 544-mutant arithmetic claim was rejected because
    it counted the 11-member wrong-SELECT-family group as one; the exact V15
    sum remains 554;
  - S09 remains active.

### R-205 V16 by-value encoder-output ownership amendment

- Status: **PRE-IMPLEMENTATION NO-GO; ONE INDEPENDENT GO AND ONE INDEPENDENT NO-GO**
- Frozen V16 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V16_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `dfe750d19c61b966ccdfe8092205fcea1c0278d5876071b2623e23f686e22fe0`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V16`, SHA-256
    `f06a5ec1b13dcde4042b8435b6b0b81b87880c4b9d0a4b6ae20f3d345cf9cf53`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V16 corrections:
  - the encoder accepts only a const tuple reference and returns one
    `std::array<uint8_t,151>` by value;
  - its only output storage is one local zero-initialized array;
  - output parameters, spans, pointers, views, external storage, placement
    construction, storage selection, and reference/view returns are forbidden;
  - the builder constructs one const tuple aggregate and never mutates or
    aliases it;
  - five ownership mutants bring the exact negative total to 559.
- Validation:
  - machine authority parses with independent negative arithmetic `559/559`;
  - root IDs and contracts remain `27/27` with unique V16 paths;
  - both unchanged probe hashes remain bound;
  - V16 authority and preflight contain zero Cyrillic text.
- Boundary:
  - one auditor returned GO;
  - the other showed that the builder could mutate the returned array after
    the exact encoder and before commitment because V16 did not const-bind or
    trace that post-return dataflow;
  - S09 remains active.

### R-205 V17 immutable encoder-to-commit dataflow amendment

- Status: **PRE-IMPLEMENTATION NO-GO; ONE INDEPENDENT GO AND ONE INDEPENDENT NO-GO**
- Frozen V17 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V17_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `0df8a8710eea773c92248824c0479b759ac744df96a5620890f38afe5a375b0d`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V17`, SHA-256
    `fb5ab04397893ca0d5674c8439ade4b4074dde36a5bbf2ec88cd19dd5b1e8b05`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V17 corrections:
  - the builder binds encoder output exactly as `const auto encoded`;
  - the sole immediate next action is
    `commit_operation_tuple_bytes(encoded)`;
  - the commit function consumes a const array reference and feeds the same
    exact pointer and literal 151 bytes to SHA-256 and optional trace copy;
  - no intervening statement, mutable alias, substitution, offset, length
    drift, transform, or divergent hash/trace source is permitted;
  - four commit-dataflow mutants bring the exact negative total to 563.
- Validation:
  - machine authority parses with independent negative arithmetic `563/563`;
  - root IDs and contracts remain `27/27` with unique V17 paths;
  - both unchanged probe hashes remain bound;
  - V17 authority and preflight contain zero Cyrillic text.
- Boundary:
  - one auditor returned GO;
  - the other supplied a valid conforming counterexample containing an
    unrelated enormous fixed loop or automatic stack object inside the commit
    function while preserving every frozen byte and SHA/trace dataflow law;
  - V17 did not freeze the commit signature, body, address lifetime, or rooted
    resource envelope tightly enough;
  - S09 remains active.

### R-205 V18 closed commit and rooted resource amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V18 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V18_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `e32bd23b883a2b3dc66c7052b85e80995827ad15500db309d5b39dac75d5f3e8`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V18`, SHA-256
    `3d6a3be3743b46ca48bd6159b0377e554d6fba62bfde6a09af9262af4132c155`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V18 corrections:
  - the sole commit has an exact `void ... noexcept` signature and a closed
    body containing only the required SHA-256 update and optional trace copy;
  - additional locals, statements, calls, control flow, side effects,
    recursion, mutable access, persistence, and address escape are forbidden;
  - the complete rooted builder/encoder/commit/SHA/copy graph has a
    conservative source-declared automatic-storage ceiling of 4,096 bytes,
    at most 4,096 dynamic loop iterations per 151-byte commit, zero heap
    allocation, and no recursion;
  - eight resource and source-shape mutants bring the exact negative total to
    571.
- Validation:
  - machine authority parses with independent negative arithmetic `571/571`;
  - root IDs and contracts remain `27/27` in identical order with unique V18
    paths;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V18 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors independently showed that source-declared automatic storage
    omits actual ABI frames, return addresses, shadow space, alignment, spills,
    and stack probes;
  - a deep acyclic direct-call chain could therefore exhaust the machine stack
    without recursion, loops, heap use, or source-declared local objects;
  - a correct SHA implementation could also use arbitrarily large static
    tables or straight-line code while preserving every V18 byte and source
    law;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V19 compiled-resource receipt amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V19 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V19_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `d9c0e36fbd55325d4c7d63f6e6ef8372fb2eb261b2581cf8a88c738f6aef7f1b`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V19`, SHA-256
    `037782719ed7d59c0a4887ab2046cea45516d4a9cac0289399e21f426e86ae17`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V19 corrections:
  - the exact compiled instrumented PE, not only C++ source, becomes part of
    the resource proof;
  - complete sections, imports, relocations, reachable disassembly, and x64
    unwind/prologue data bound direct-call depth, actual ABI stack, machine
    instructions, text, static storage, file size, and `SizeOfImage`;
  - a fresh-process 100,000-commit trial binds elapsed time, peak working set,
    exit status, SHA-256, and trace identity;
  - one new resource receipt expands the ordered root to 28 payloads;
  - eleven compiled-resource mutants plus one new payload-rewrite mutant bring
    the exact negative total to 583.
- Validation:
  - machine authority parses with independent negative arithmetic `583/583`;
  - root IDs and contracts are `28/28` in identical order with unique V19
    paths;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V19 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors found that runtime inputs and independent expected hashes
    were not frozen, permitting an untested rare slow path;
  - executable hashes did not bind loaded native dependencies or retain raw
    LLVM outputs as root payload bytes;
  - stack accounting began at the telemetry suffix and omitted production
    caller ancestry already occupying the stack;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V20 closed machine-dependency and public-ancestry amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V20 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V20_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `3111c93db6c1ae7e32bd69c69c6bd5f73764b721ed6936826c09f958bb607e12`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V20`, SHA-256
    `48338e41beec1a08b8d06fe25c45a6a03f09bec8658d1e043d805d26d6a42fcf`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V20 corrections:
  - tuple values may affect arithmetic data but cannot affect machine control
    flow, loop bounds, call targets, memory addresses, allocation, stack
    adjustment, or exception paths;
  - worst-case dynamic instructions are derived from the complete finite CFG
    and fixed loop bounds rather than inferred from a sample;
  - actual stack accounting starts at all three real production public ABI
    roots and reaches every frozen observer site;
  - a canonical raw evidence bundle roots LLVM stdout/stderr/argv, Python and
    native loaded-module identities, OS loader, CPU, affinity, and timer facts;
  - the runtime stream is fixed as 12 semantic cases repeated 10,000 times,
    with independent case-index, tuple-cycle, full-stream, SHA, and trace
    hashes;
  - one evidence-bundle payload expands the ordered root to 29;
  - fourteen closure mutants plus one new payload-rewrite mutant bring the
    exact negative total to 598.
- Validation:
  - machine authority parses with independent negative arithmetic `598/598`;
  - root IDs and contracts are `29/29` in identical order with unique V20
    paths;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V20 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - V20 required one live 120,000-operation record but froze bytes whose
    ordinal reset to zero every twelve operations;
  - the independently correct continuous-ordinal stream hash differs from the
    frozen repeated-cycle hash, so no implementation could satisfy both laws;
  - V20 also permitted tuple-tainted arithmetic to enter variable-latency
    opcodes even when control flow and instruction count remained fixed;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V21 continuous ordinal and operand-latency amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V21 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V21_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `067920cd9e87560a91d2419c1d9eb3a35e36480d1b5d9048421d1d3644028101`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V21`, SHA-256
    `2f7c1e8a6088066ec999b83eaa3dd348320c4c9bbaf52abf264af943e3442d3e`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V21 corrections:
  - one active telemetry record now emits continuous ordinals zero through
    119,999 with no reset, gap, or duplicate;
  - the independently recomputed 18,120,000-byte expected SHA/trace hash is
    `d51859d69cc2200d87bdb1a534fd90466c90aae8c67eb20eb88021cccc1e8c58`;
  - tuple-tainted operands are restricted to a closed constant-latency integer
    opcode set;
  - division, multiplication, floating/vector divide or square root,
    tainted-repeat, gather/scatter, and undocumented variable-latency or
    microcoded operations are forbidden;
  - the frozen-CPU table bounds worst-case instructions and cycles per
    commitment;
  - two new mutants bring the exact negative total to 600.
- Validation:
  - machine authority parses with independent negative arithmetic `600/600`;
  - root IDs and contracts remain `29/29` in identical order with unique V21
    paths;
  - the continuous-ordinal stream hash was independently reproduced;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V21 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - both auditors confirmed the continuous ordinal stream and exact
    `d518...8c58` hash;
  - both rejected the absolute cycle-WCET claim because ordinary Windows
    cache, TLB, paging, interrupt, and scheduling latency is not bounded by the
    implementation;
  - the operand allowlist also used the ambiguous term `MOV-family` rather
    than exact decoded mnemonics and forms;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V22 implementation-owned resource boundary amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION GO VERDICTS; STAGE-1 IMPLEMENTATION AUTHORIZED**
- Frozen V22 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V22_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `6abf4b0d5a136b110bf875a3ac76908c7cf594d91799752f4643884e1804f0e8`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V22`, SHA-256
    `83d8968226b0e92860f0713ed8cbf1f902ac17ea824e8006db9e65b9e7fda823`;
  - `native/tests/r205_observer_semantic_probes_v2.json`, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - `native/tests/r205_canonical_tuple_probes_v1.json`, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V22 corrections:
  - normative bounds cover implementation-owned code, control, addresses,
    instructions, loads/stores, pages, bytes, stack, storage, heap, image,
    imports, and allocation;
  - external Windows cache, TLB, page-fault, interrupt, preemption, frequency,
    thermal, firmware, hypervisor, driver, and scheduler latency is explicitly
    outside the binary-WCET claim;
  - runtime wall time remains a recorded empirical admission observation;
  - exact decoded transfer mnemonics, operand forms, widths, prefixes, and
    opcode bytes replace the `MOV-family` wildcard;
  - implementation-owned memory operations, pages, and bytes receive static
    finite bounds;
  - two new mutants bring the exact negative total to 602.
- Validation:
  - machine authority parses with independent negative arithmetic `602/602`;
  - root IDs and contracts remain `29/29` in identical order with unique V22
    paths;
  - the continuous-ordinal stream hash remains independently reproduced;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V22 authorities and preflight contain zero Cyrillic text.
- Boundary:
  - two independent read-only auditors returned binary GO on all four exact
    V22 hashes;
  - a later read-only implementation guard found an unspecified private C ABI,
    contradictory command-artifact shapes, and a circular pre-discovery gate;
  - a preliminary tuple-encoder scaffold was removed immediately and no
    retained implementation, discovery, admission, codec, bitstream, or PCM
    change occurred;
  - V22 is superseded by V23 before retained implementation;
  - read-modify-write, implicit stack access, stack ancestry, and page-crossing
    accounting are mandatory implementation-audit checks;
  - admission, the original 72-mutant campaign, R-203 admission, and S10 remain
    forbidden until the frozen 29-payload stage-2 root receives two fresh
    independent GO verdicts;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V23 exact private ABI and non-circular execution amendment

- Status: **PRE-IMPLEMENTATION CANDIDATE; TWO INDEPENDENT AUDITS PENDING**
- Frozen V23 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V23_PREFLIGHT_2026-07-30.md`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V23`, SHA-256
    `b7d823108fb28e4923232b0c4160e78f2a828272e7f9d2f7d1dd878b3263c01d`;
  - unchanged defined-range semantic probes, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - unchanged typed encoder probes, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V23 corrections:
  - freezes every private C type, field order, status, calling convention,
    function signature, record-ID law, and trace-buffer law;
  - defines one canonical command object containing exact argv, cwd,
    allowlisted environment, executable identity, and path-sorted input hashes;
  - splits Stage 1 into pre-discovery implementation gates, exactly 19,587
    discovery calls, and post-discovery validation/root freeze;
  - adds three authority-closure mutants for a total of 605.
- Validation:
  - machine authority parses with independent negative arithmetic `605/605`;
  - root IDs and contracts are `29/29`, unique, ordered, and all use V23 paths;
  - both unchanged probe hashes and all frozen production identities remain
    bound;
  - V23 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both independent auditors returned NO-GO;
  - the blockers were unfrozen private-structure layouts, missing status
    transitions and precedence, a forbidden admission record ID, no observed
    runtime trace route, and an admission-root self-reference gap;
  - V23 is superseded by V24 before retained implementation;
  - admission, the original 72-mutant campaign, R-203 admission, and S10 remain
    forbidden;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V24 byte-exact ABI and external-root amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V24 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V24_PREFLIGHT_2026-07-30.md`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V24`, SHA-256
    `954215c985b83bf2917cd8cff86375c9a5a0dda2658967688addd4c20d99ad8d`;
  - unchanged semantic probes, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - unchanged typed probes, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V24 corrections:
  - freezes exact size, alignment, and every offset of both private C input
    structures and requires matching compile-time assertions;
  - defines a complete five-state status and error-precedence machine;
  - admits the later admission record ID without adding it to discovery;
  - adds a distinct 18,120,000-byte measured-runtime trace mode;
  - replaces the cyclic admission input with one exact out-of-band
    SHA-bound-file slot and transient argv substitution;
  - adds five closure mutants for an exact total of 610.
- Validation:
  - machine authority parses with independent arithmetic `610/610`;
  - root IDs/contracts are `29/29`, unique, ordered, and all use V24 paths;
  - unchanged probes and production identities remain bound;
  - V24 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both independent auditors returned NO-GO;
  - the blockers were the contradictory trace-retention law, a
    `r205_record_read` output-alias route, an incomplete semantic initial-state
    predicate, and command/root identity ambiguity;
  - V24 is superseded by V25 before retained implementation;
  - admission, the original 72-mutant campaign, R-203 admission, and S10 remain
    forbidden;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V25 observable-probe and rooted-execution amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION NO-GO VERDICTS**
- Frozen V25 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V25_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `483c0bab6c5356e976ac5419105121bea451760dc84355956bf586df886b0c09`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V25`, SHA-256
    `d6739d80437531a1ac936976792c26a394dc3e58b500d2ca08afb21e2d95ed8e`;
  - unchanged semantic probes, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - unchanged typed probes, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V25 corrections:
  - freezes three independently persisted trace modes with one identical
    SHA/copy byte source and dedicated non-aliasing runner spans;
  - makes the twelve real-ledger semantic tuples directly observable;
  - records exact branchless arithmetic-validity summaries `1,2` for one
    semantic cycle and `10000,20000` for the measured runtime;
  - freezes the complete valid semantic initial-state predicate;
  - rejects `required_bytes`/JSON output range aliasing before any read output;
  - binds every evidence command to the actual rooted source, interpreter,
    argv, cwd, environment, and inputs that execute it;
  - adds eight V25 input/observability mutants plus one command-executor
    closure mutant for an exact total of 619.
- Validation:
  - machine authority parses with independent arithmetic `619/619`;
  - all twelve semantic inputs pass the frozen domain predicate;
  - derived validity summaries are exactly `1,2` and `10000,20000`;
  - root IDs/contracts are `29/29`, unique, ordered, and all use V25 paths;
  - unchanged probes and production identities remain bound;
  - V25 authority and preflight contain zero Cyrillic text.
- Boundary:
  - both independent auditors returned NO-GO on the 619-versus-616 rooted
    negative-matrix contradiction;
  - one auditor additionally found that admission compared its realized argv
    against the immutable placeholder template instead of a derived realized
    vector;
  - V25 is superseded by V26 before retained implementation;
  - admission, the original 72-mutant campaign, R-203 admission, and S10 remain
    forbidden;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V26 exact matrix and realized-argv amendment

- Status: **TWO INDEPENDENT PRE-IMPLEMENTATION GO VERDICTS; EVIDENCE-ONLY
  STAGE-1 IMPLEMENTATION AUTHORIZED**
- Frozen V26 documents:
  - `docs/reviews/R205_FAMILY_SEPARATED_BOUND_AUTHORITY_V26_PREFLIGHT_2026-07-30.md`,
    SHA-256
    `12c82b89c5c21f36f1cca5ad63ba1db6664643ebbc48c1655fe4f9efc8de20a2`;
  - `native/tests/r205_family_bound_authority_v1.json`, design revision
    `R205-FAMILY-EPOCH-V26`, SHA-256
    `a31dc407a2ae6812ff0f42be023c0fe7d70a5d42307070ff0ff4a8da36603341`;
  - unchanged semantic probes, SHA-256
    `f7642e6f3ae98b2b7c767a92e1c76d64e286956dfffad181d7d479637cbb7095`;
  - unchanged typed probes, SHA-256
    `86cda87aaba7279e0d55ac1c92ef6fae4dc9083d778d2ed4c56f4eb3dd5e95bc`.
- V26 corrections:
  - the declared sum, expected total, Phase-C requirement, and rooted JSONL
    contract now all require exactly 619 negative mutants;
  - ordinary commands compare observed argv with the immutable template;
  - admission derives one exact realized argv from the unchanged template and
    supplied external root before comparing the observed process vectors;
  - every stage-2 output path advances to V26.
- Validation:
  - matrix closure is `619/619/619/619`;
  - root IDs/contracts are `29/29`, unique, ordered, and all use V26 paths;
  - the 18,120,000-byte runtime stream still hashes to `d518...8c58`;
  - unchanged probes and production identities remain bound;
  - V26 authority and preflight contain zero Cyrillic text.
- Boundary:
  - two independent binary GO verdicts cover the exact V26 hashes;
  - only evidence-only Stage-1 implementation and Phase-A gates are now
    authorized;
  - discovery remains blocked until Phase A passes;
  - admission, the original 72-mutant campaign, R-203 admission, and S10 remain
    forbidden;
  - R-205 is evidence-only and does not trigger the registered-music gate;
  - S09 remains active.

### R-205 V26 record/state-matrix V10 independent rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V10 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V10_CRASH_CLOSED_BOOTSTRAP_2026-08-01.md`;
  - 13,819 bytes;
  - SHA-256
    `b4bf3237b0b1d8a87841208d45af073f6e7a56e6f8c3c3423e14352562e7e719`.
- Accepted V10 correction:
  - controller/watchdog death no longer produced false Job-accounting or
    cleanup claims; `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` remained
    defense-in-depth only.
- Blocking findings:
  - the declared 256-byte WAL record could not contain its fields;
  - torn-tail handling contradicted crash reconciliation;
  - the plan mapping had no closed writer/publication/authorization path;
  - recovery required parent-root handles owned only by the dead process;
  - the seven-operation Python validator delta omitted substantial system
    behavior;
  - `CancelSynchronousIo` could not guarantee bounded worker completion;
  - Phase-0 residue, evolving output content, and pre/post-code freezes were
    incomplete.
- Boundary:
  - V10 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - all prior artifacts remain negative evidence;
  - all nine Phase-A gates remain unresolved and S09 remains active.

### R-205 V26 record/state-matrix V11 minimal native-controller candidate

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V11 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V11_MINIMAL_NATIVE_CONTROLLER_2026-08-01.md`;
  - 22,459 bytes;
  - SHA-256
    `b3c57025a44f0f16b30b5ab571d04a0c3274b272237080de2915c44fcf638c90`.
- Selected architecture:
  - one minimal C++23 controller is the sole lifecycle authority;
  - a broker and tool run in distinct zero-capability sibling AppContainers;
  - the existing Python validator only invokes the exact controller from its
    existing `state_matrix_gate` and validates bounded atomic output;
  - no automatic recovery runs after controller death;
  - one exact 512-byte append-only WAL and explicit short-tail law replace the
    impossible V10 record;
  - controller-owned plan publication, Phase-0 residue, output lease/content
    evolution, provisional data EOF, fixed receipt, sibling isolation, and
    stuck-I/O self-termination are explicit;
  - pre-code authority and post-implementation identity freezes are separate.
- Alternatives rejected before implementation:
  - expanding the 2,605-line Python validator into a lifecycle authority;
  - handle-escrow or path-reopening recovery processes;
  - combining hostile parsing with lifecycle authority;
  - rescuing V10 through incremental hidden behavior.
- Prediction and kill gate:
  - the smaller native trust root should close V10 ownership contradictions;
  - V11 is killed if Python must own mutation handles, controller must parse raw
    records, a worker can overlap cleanup, identity must be weakened, or the
    complete cost fails to close a proof gap.
- Boundary:
  - independent audit rejected V11 because synchronous I/O could make even
    process termination unbounded, future identity lacked a separate observed
    commitment, output and terminal states were incomplete, profile storage was
    unbounded, write/flush failures and handle ownership were open, and the
    validator/build trust chain was not closed;
  - V11 authority and inert fixtures are forbidden;
  - no implementation, build, process, profile, ACL, discovery, admission, S10,
    codec, bitstream, or PCM change is authorized;
  - the registered-music/Opus comparison remains scheduled at S12 after the
    next actual codec-algorithm change in S11.

### R-205 V26 record/state-matrix V12 overlapped-LPAC rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V12 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V12_OVERLAPPED_LPAC_CONTROLLER_2026-08-01.md`;
  - 23,940 bytes;
  - SHA-256
    `03e4a49e1057654a1fbeba8442bdf0e2320ba93f19d5e247831ea96d9ca5a0cd`.
- Selected corrections:
  - one controller thread and five `FILE_FLAG_OVERLAPPED` channels replace
    blocking workers and anonymous pipes;
  - controller passes already-open child handles, retains each OVERLAPPED/event
    until observed completion, and makes no absolute OS completion-time claim;
  - the 1 MiB structural result remains in precommitted memory until all
    child/I/O and cleanup states are terminal;
  - distinct zero-capability LPAC profiles contain copied frozen closures and
    are recursively changed to read/execute-only before launch; registry,
    network, and filesystem writes are denied and probed;
  - the 512-byte WAL adds exact observed-state and observed-identity fields and
    closes no/short/full/flush outcomes;
  - result publication occurs after cleanup and distinguishes
    `FINAL_PRESENT_UNATTESTED`;
  - an exact 1,024-byte controller receipt binds WAL head, cleanup, result,
    resources, profiles, images, run nonce, and required process exit;
  - the current 179-line `state_matrix_gate` replacement and noncircular
    pre-code/native/validator/post-manifest/root-command chain are explicit.
- Rejected alternative:
  - experimental `CreateProcessInSandbox` is not normative because Microsoft
    marks it unstable, it forbids inherited handles, has no public header, and
    still creates an AppContainer profile.
- Boundary:
  - independent audit rejected V12 because Phase 0 contradicted result timing,
    the real one-main plus four-child helper interface was incompatible,
    profile population and result publication lacked closed WAL transitions,
    the persistent-state hash was circular, LPAC registry/delete accounting and
    post-timeout monotonicity were incomplete, the broker receipt was open, and
    pre-exit resource samples were misnamed as complete process time;
  - V12 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no implementation/build/process/profile/ACL/discovery/admission/S10 action
    is authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - no codec algorithm changed, so the full music/Opus gate remains S12.

### R-205 V26 record/state-matrix V13 framed-LPAC transaction rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V13 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V13_FRAMED_LPAC_TRANSACTION_2026-08-01.md`;
  - 33,246 bytes;
  - SHA-256
    `1a18839b53e7d2ab6e761f6a590d8bd5d7cd2a242e05069ff3934bf534b22644`.
- Selected corrections:
  - an evidence-only `--output-stdio` helper delta preserves path-mode bytes
    while supporting the actual one-main plus four-child invocation graph;
  - controller frames five sequential streams for one bounded hostile-parser
    broker without parsing state-matrix rows itself;
  - Phase 0 contains only run root, plan, and journal;
  - profile create/populate/seal and result create/finalize/promote have closed
    aggregate WAL ownership and inverse rules;
  - timeout irreversibly enters `POISONED_WAIT_ONLY`, so late completion cannot
    resume persistent mutation;
  - broker and controller receipts are exact contiguous 512- and 1,024-byte
    layouts; the 256-byte frame and 512-byte WAL layouts also pass machine
    contiguity checks;
  - pre-receipt persistent-state hashing explicitly excludes receipt leaves,
    and resource cutoff samples are distinct from post-exit totals.
- Boundary:
  - independent audit rejected V13 because its structural result was not
    byte-closed, pre-receipt attestation was circularly named, profile monikers
    were underidentified, rebuild/inspection subprocesses lost an owner, deny
    canaries contradicted process accounting, partial populate rollback lacked
    terminal WAL behavior, frame hashing was ambiguous, and pre-delete resource
    closure was incomplete;
  - V13 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source, build, process, profile, ACL, discovery, admission, S10, codec,
    bitstream, or PCM change is authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the next codec algorithm remains S11 and its full registered comparison
    remains S12.

### R-205 V26 record/state-matrix V14 byte-closed transaction rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V14 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V14_BYTE_CLOSED_TRANSACTION_2026-08-01.md`;
  - 27,906 bytes;
  - SHA-256
    `b7decd83e9d1e7d6787a0e5edae6afb4bcd8ffad4a5401e924cc025db48a3f05`.
- Selected corrections:
  - exact 256-byte frame header, 256-byte structural header, 320-byte row
    header, 512-byte WAL/canary/broker receipts, and 1,024-byte controller
    receipt all pass independent contiguity arithmetic;
  - controller result state is `FINAL_PRESENT_CONTROLLER_VERIFIED`; only the
    validator derives external `ATTESTED` after final receipt and exact exit;
  - LPAC monikers are exact 60-character domain-separated lower-base32 names;
  - current rebuild and LLVM inspection work is preserved in an immediately
    preceding state-toolchain gate with existing bundle names;
  - two frozen nonmutating deny canaries raise exact child count to eight;
  - partial populate/seal rollback closes only through durable NOT_APPLIED;
  - frame length, payload, cumulative, complete-frame, and transcript hash
    domains are byte-exact;
  - a fixed ownership registry and source closure prove every profile-associated
    handle/pointer closed before public-API deletion.
- Boundary:
  - independent audit rejected V14 because row grammar admitted producer-
    impossible length 192, canary plan was not byte-closed, probe targets lacked
    immutable/WAL ownership, child-launch outcomes did not close process
    accounting, and pre-receipt hashing included mutable directory state;
  - V14 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V15 reproducible-canary candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V15 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V15_REPRODUCIBLE_CANARY_TRANSACTION_2026-08-01.md`;
  - 34,024 bytes;
  - SHA-256
    `fe58a1383e9cd39db6b187b69ab356a7ef83ee29324035f42fdeb830eb37e910`.
- Selected corrections:
  - broker row label domain is exact producer range 1..191 and 192 is a mutant;
  - canary input is an exact contiguous 2,048-byte plan;
  - probe targets are a populate/seal-owned profile file, the pre-existing
    frozen production source, pre-existing HKCU Software root, fixed loopback,
    and verified canary image; no probe creates persistent state;
  - canary emits a 384-byte raw report and controller combines post-exit Job
    observations into a separate 512-byte receipt;
  - both denied-before-create and created-then-Job-killed child tuples are
    exact; complete child process count is 8..10;
  - pre-receipt state is a domain-separated projection using exact 192-byte
    root and 320-byte object records, excluding receipt leaves and mutable
    directory metadata while independently checking the final entry set;
  - all eleven declared layouts pass machine contiguity and exact-size checks.
- Boundary:
  - independent audit returned NO-GO because the UTF-16 maximum contradicted
    the byte-count bound, primary launches lacked pre-resume Job confinement,
    canary Job accounting was not reproducible, the raw report overclaimed
    inherited-handle evidence, helper/toolchain hashes lacked owned channels,
    and path grammar ambiguously forbade required literal dots;
  - V15 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V16 pre-resume-confinement candidate

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V16 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V16_PRE_RESUME_CONFINEMENT_2026-08-01.md`;
  - 45,634 bytes;
  - SHA-256
    `72c77a927332a6fa167c0c09835699b6963502c405cdf7748c032b802078e70b`.
- Selected corrections:
  - the fixed 520-byte path fields admit even byte counts through 520, with
    exact NUL and zero-tail laws plus 518/520 boundary mutants;
  - four distinct Jobs and an exact create-suspended, assign, verify, then
    single-resume sequence forbid target execution before confinement;
  - dedicated canary Jobs freeze baseline and final process arithmetic, while
    the broker and five sequential helpers have separately identified Jobs;
  - raw canary evidence contains only token facts queryable by the canary;
    controller receipts separately bind startup capabilities, LPAC/child
    policy, HANDLE_LIST, inherit-bit audit, token observation, and Job state;
  - an exact 1,024-byte state-toolchain receipt owns source/image/tool/command/
    inspection hashes; validator-to-controller and controller-to-broker whole-
    argument channels bind helper and toolchain hashes noncircularly;
  - controller rehashes the actual helper before all five launches and verifies
    the frozen external source before/after each canary without share-deny;
  - path grammar forbids only whole `.`/`..` components and allows the required
    literal dots in fixed leaf names;
  - all twelve declared layouts pass machine contiguity and exact-size checks.
- Boundary:
  - independent audit rejected V16 because its Job outcome matrix omitted a
    documented limit-rejection counter state, five record hashes lacked exact
    domains/preimages, seventeen pipe handles lacked role-visible stdio routing,
    three image fields lacked complete producer/reconciliation channels, and
    pre-code authority ambiguously appeared to predict future source bytes;
  - V16 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V17 hash-closed-routing rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V17 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V17_HASH_CLOSED_ROUTING_TRANSACTION_2026-08-01.md`;
  - 53,537 bytes;
  - SHA-256
    `6d499280e28ef8ee413724f4800645e483a4f91b0320d97ce9a4dd5b4c5ba414`.
- Selected corrections:
  - final canary classification admits pre-association denial, false-return
    association-limit rejection, and observed created-then-limit-terminated,
    with two distinct pre-action snapshots and all final Job counters;
  - WAL genesis/record, raw canary report, canary receipt, broker receipt, and
    terminal receipt have exact domain-separated zero-field preimages;
  - all eight processes use exact STARTF_USESTDHANDLES routing and ordered
    three-handle HANDLE_LISTs; seventeen pipe clients and seven NUL handles are
    completely typed, inherited, counted, and closed;
  - the rooted state-toolchain receipt supplies all four image hashes through
    exact CLI/plan channels, while role self-checks and independent controller/
    validator rehashes reconcile actual images rather than trusting echoes;
  - pre-code authority binds existing identities, future paths/contracts/
    predicates, and hash placeholders, never nonexistent future source bytes;
  - all twelve fixed layouts and all 14 sections pass machine checks, and the
    file contains no truncation marker.
- Boundary:
  - independent audit rejected V17 because it protected the four rooted source
    images but did not bind and continuously protect the profile copies actually
    named by `lpApplicationName`; destination replacement remained possible
    between rehash, suspended creation, and role self-check;
  - V17 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V18 sealed-launch-identity rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Immutable V18 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V18_SEALED_LAUNCH_IDENTITY_TRANSACTION_2026-08-01.md`;
  - 73,617 bytes;
  - SHA-256
    `14222c6fcc7baedf9058446f9bacf45305f01d2b2472947dd24f43067fa22c17`.
- Selected corrections:
  - exact source-to-profile mapping binds four rooted images to fixed relative
    leaves under the two runtime-created profile roots without predicting a
    future absolute path in pre-code authority;
  - each WAL-owned copy uses a bounded writer, flush/seal and provisional
    identity capture, then closes the writer and reacquires the unchanged file
    as a read-only guard denying write/delete before copy COMMITTED;
  - each of eight launches uses exact nonnull `lpApplicationName`, quoted argv,
    create-suspended confinement, pre-resume `QueryFullProcessImageNameW`, held-
    guard/file-ID/hash/security/link reconciliation, and role self-check;
  - four 512-byte sealed-copy receipts, eight 512-byte launch receipts, and five
    256-byte helper attestations bind the terminal sealed-launch transcript;
  - all added link/security/path/file/guard/process/transcript hashes have exact
    domain-separated preimages, and the WAL observed-state -> committed-record
    -> copy-receipt edge is one-way rather than circular;
  - all sixteen fixed layouts pass contiguity and exact-size checks, all 14
    sections are present, and the candidate is ASCII-clean with no truncation.
- Boundary:
  - independent audit rejected V18 because immutable pre-call command-line
    bytes and exact nonambient Unicode environment/cwd were underdefined;
    identity producer APIs/flags were not fixed; an early receipt predicted a
    future guard close; canary did not attest its actual loaded copy; and no
    late full metadata readback or loader/share/drift gate closed the guard
    lifetime;
  - the source -> relative leaf -> runtime profile-copy mapping and one-way
    WAL -> receipt graph remain accepted positive evidence;
  - V18 authority, fixtures, source, build, process, profile, and ACL actions
    are forbidden;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.
- Independent result:
  [R-205 V18 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V18_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 record/state-matrix V19 exact launch-context candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V19 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V19_EXACT_LAUNCH_CONTEXT_GUARD_LIFETIME_2026-08-01.md`;
  - 87,662 bytes;
  - SHA-256
    `4fd5eb0a13e7ed83d1570753092f87a4f6b2a40c25ca8270957a8ffbd828f31e`.
- Selected coherent remediation:
  - immutable canonical pre-call application/command/argv evidence is separate
    from the disposable writable `CreateProcessW` command-line clone;
  - every primary launch supplies exact nonnull Unicode environment and current
    directory with a byte-closed ASCII ordering/duplicate/special-name law;
  - exact Win32 API/flags/bounds own final handle path, FILE_ID, volume, size,
    attributes/reparse tag, streams, hard links, security descriptor, module
    self-path, and suspended process image path;
  - early sealed-copy receipt contains only observed guard-open state; a late
    terminal guard-lifetime hash records actual post-use close;
  - canary raw report is 512 bytes and binds actual module identity, state-
    toolchain receipt, sealed-copy receipt, and launch context before any probe;
  - every launch receipt follows role exit with a fresh complete destination
    identity readback, while the threat claim is limited to ordinary share-mode
    denial plus the stated ACL boundary;
  - later Windows loader/share and metadata-drift integration behavior is an
    explicit kill fixture rather than a design assumption;
  - all sixteen fixed layouts pass exact size/contiguity checks, all 14 sections
    exist, and the candidate is ASCII-clean without a truncation marker.
- Boundary:
  - independent GO is requested only for permission to create later pre-code
    authority and inert fixtures;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V19 launch-observation rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Audited immutable V19 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V19_EXACT_LAUNCH_CONTEXT_GUARD_LIFETIME_2026-08-01.md`;
  - 87,662 bytes;
  - SHA-256
    `4fd5eb0a13e7ed83d1570753092f87a4f6b2a40c25ca8270957a8ffbd828f31e`.
- Accepted evidence:
  - immutable command-line input and disposable writable clone, exact Unicode
    environment contract, named identity APIs, one-way guard-lifetime evidence,
    512-byte canary report, complete mapping lists, and absence of a hash cycle
    are structurally retained;
  - guard/loader compatibility remains a real Windows kill fixture rather than
    an assumed design property.
- Boundary:
  - independent audit rejected V19 because it mixes parent-only launch inputs
    with role-observable context; broker/helpers cannot verify expected sealed
    destination identity before parsing; cwd has two possible textual sources;
    owner/group/DACL evidence is overstated as a complete security descriptor;
    and several Win32 in/out length states remain underdefined;
  - V19 authority, fixtures, source, build, process, profile, and ACL actions are
    forbidden;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.
- Independent result:
  [R-205 V19 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V19_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 record/state-matrix V20 parent/role identity candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V20 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V20_PARENT_ROLE_IDENTITY_HANDSHAKE_2026-08-01.md`;
  - 99,612 bytes;
  - SHA-256
    `0766904d793768cf31df36aacee5b5c222e578b14554c764c463d843423ec4bb`.
- Selected coherent remediation:
  - controller-owned application/flags/inheritance/HANDLE_LIST evidence and
    role-observed module/command/argv/cwd/environment evidence use separate
    domains and reconcile only at the launch receipt;
  - one shared `LAUNCH-TARGET-IDENTITY` domain permits exact expected-versus-
    actual executable equality without comparing differently domained hashes;
  - broker and five helpers emit a 320-byte pre-parser attestation; broker's
    first frame and each helper's one-byte GO gate are withheld until validation;
  - copied `GetAppContainerFolderPath` text is the sole cwd producer, while the
    opened volume-GUID path remains a separate handle identity and round-trip is
    a Windows kill fixture;
  - security evidence is explicitly OWNER/GROUP/DACL only; SACL-class metadata
    is excluded rather than silently claimed;
  - final-path, file-information, stream, hard-link, module-path, process-image,
    cwd, and security APIs have exact capacities, return laws, termination,
    replay, cleanup, and reconciliation rules;
  - all sixteen fixed layouts pass exact size/contiguity checks, all 14 sections
    exist, and the candidate is ASCII-clean without stale V19 magic/domains.
- Boundary:
  - independent GO is requested only for permission to create later pre-code
    authority and inert fixtures;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V20 deterministic-path rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Audited immutable V20 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V20_PARENT_ROLE_IDENTITY_HANDSHAKE_2026-08-01.md`;
  - 99,612 bytes;
  - SHA-256
    `0766904d793768cf31df36aacee5b5c222e578b14554c764c463d843423ec4bb`.
- Accepted evidence:
  - parent/role evidence split, shared launch-target equality, one-way hash graph,
    OWNER/GROUP/DACL scope, all sixteen layouts, and complete process/pipe/handle
    counts are independently retained;
  - loader/share behavior remains a future mandatory Windows kill fixture.
- Boundary:
  - V20 is rejected because helper does not observe EOF after GO, profile-root
    grammar and per-leaf bounds are open, hard-link root/name joining is not
    byte-exact, and helper source-delta scope contradicts its own handshake;
  - V20 authority, fixtures, source, build, process, profile, and ACL actions are
    forbidden;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.
- Independent result:
  [R-205 V20 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V20_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 record/state-matrix V21 deterministic path/gate candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V21 candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V21_DETERMINISTIC_PATH_GATE_CLOSURE_2026-08-01.md`;
  - 106,632 bytes;
  - SHA-256
    `8fc01af59fa916eef945019011c3a31f4da7045390a7e753b3faf387fc142d56`.
- Selected bounded remediation:
  - each helper binds the exact one-byte grant and a second terminal
    `ERROR_BROKEN_PIPE` read to a 128-byte completion record and a complete
    controller/helper gate transcript;
  - `profile_cwd_text` has one strict absolute-DOS grammar, checked root/leaf
    addition, a 259-WCHAR non-NUL ceiling, and a named pre-populate rollback
    boundary;
  - the hard-link reopen path is the exact validated volume-root prefix plus the
    exact returned link name after stripping exactly one root marker;
  - the helper-only evidence source/API delta is enumerated once and admits no
    unstated helper behavior;
  - all seventeen fixed layouts pass exact size/contiguity checks, all 14
    sections exist, and the candidate is ASCII-clean without stale V20 magic.
- Boundary:
  - independent GO is requested only for permission to create later pre-code
    authority and inert fixtures;
  - no source/build/process/profile/ACL/discovery/admission/S10/codec action is
    authorized;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V21 state/evidence rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Audited immutable identity:
  - 106,632 bytes;
  - SHA-256
    `8fc01af59fa916eef945019011c3a31f4da7045390a7e753b3faf387fc142d56`.
- Accepted evidence:
  - the two-read helper gate, controller/helper transcript, complete helper
    source delta, 17 fixed layouts, process/resource counts, and deterministic
    hard-link separator construction are retained;
  - no new hash cycle was found.
- Boundary:
  - V21 is rejected because root validation requires rollback after entering an
    irreversible poison state; the hard-link reopen bytes are not bound to a
    domain-separated serialized evidence hash; and local named-pipe EOF behavior
    lacks a mandatory real-Windows feasibility fixture;
  - V22 must also clarify backslash grammar and apply the canary 520-byte fit to
    both its profile and external source paths;
  - no authority, fixture, source, build, process, profile, ACL, discovery,
    admission, S10, or codec action is authorized;
  - all nine Phase-A gates remain open and S09 remains active.
- Independent result:
  [R-205 V21 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V21_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 record/state-matrix V22 recoverable-root/bound-reopen candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V22 identity:
  - 112,685 bytes;
  - SHA-256
    `185e42f2cb899bfedadb0c86f30a11250de47a85f4e7cfcbf2f0945cbc632f80`.
- Selected bounded remediation:
  - durable CREATE INTENT precedes profile creation, and root/path/handle checks
    precede PROFILE_CREATE COMMITTED; a failed gate uses recoverable
    uncommitted-create abort/NOT_APPLIED rather than irreversible poison;
  - actual hard-link reopen input/name/path/raw-key evidence is domain-separated
    inside runtime `LINK_STATE`; plan offset 296 contains only a static policy
    template and predicts no future profile path;
  - a mandatory pre-admission real-Windows x64/ARM64 fixture must reproduce the
    exact local named-byte-pipe grant and EOF tuples or kill the design;
  - backslash separator grammar and both 520-byte canary path fields are explicit;
  - all seventeen fixed layouts are contiguous, all 14 sections exist, and the
    candidate is ASCII-clean without stale V21 magic/domain.
- Boundary:
  - no authority, fixture, source, build, process, profile, ACL, discovery,
    admission, S10, or codec action is authorized before a separate design GO;
  - all nine Phase-A gates remain open and S09 remains active;
  - the registered music/Opus comparison remains S12 after S11.

### R-205 V26 record/state-matrix V22 commit-publication rejection

- Status: **INDEPENDENT DESIGN NO-GO; NO AUTHORITY OR IMPLEMENTATION**
- Audited immutable identity:
  - 112,685 bytes;
  - SHA-256
    `185e42f2cb899bfedadb0c86f30a11250de47a85f4e7cfcbf2f0945cbc632f80`.
- Accepted evidence:
  - pre-COMMITTED root/canary validation, hard-link evidence binding, static
    plan policy, Windows pipe feasibility gate, all 17 layouts, resource counts,
    and authority boundary are retained.
- Boundary:
  - V22 is rejected only because a torn/unreadable/unflushed COMMITTED append is
    routed through a recoverable branch that would append behind an uncertain
    WAL tail;
  - V23 must split the state at first COMMITTED issuance and make every uncertain
    publication terminal/nonmutating;
  - no authority, fixture, source, build, process, profile, ACL, discovery,
    admission, S10, or codec action is authorized;
  - all nine Phase-A gates remain open and S09 remains active.
- Independent result:
  [R-205 V22 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V22_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 record/state-matrix V23 commit-publication candidate

- Status: **DESIGN CANDIDATE; INDEPENDENT GO/NO-GO IN PROGRESS**
- Immutable V23 identity:
  - 114,421 bytes;
  - SHA-256
    `411dc72617a5c67714ec36b45ee62e99e92c556c7f8568484e485dca0466cfc6`.
- Selected sole remediation:
  - recoverable root-gate abort is reachable only before COMMITTED issuance;
  - the controller enters `COMMIT_PUBLICATION_IN_FLIGHT` before issuing the
    append;
  - only exact full write/readback/flush/readback reaches
    PROFILE_CREATE_COMMITTED;
  - every no/short/invalid/readback/flush/ambiguous outcome reaches terminal
    `UNPROVEN_COMMIT_PUBLICATION` and permits no later persistent mutation;
  - explicit transition mutants cover no-write, 1..511-byte tails, invalid full
    records, both readbacks, flush ambiguity, and chain mismatch;
  - all seventeen layouts and all prior accepted V22 mechanisms are unchanged.
- Boundary:
  - no authority, fixture, source, build, process, profile, ACL, discovery,
    admission, S10, or codec action is authorized before design GO;
  - all nine Phase-A gates remain open and S09 remains active.

### R-205 V26 record/state-matrix V23 design admission

- Status: **INDEPENDENT DESIGN GO; PRE-CODE AUTHORITY/FIXTURE DRAFT ONLY**
- Audited immutable identity:
  - 114,421 bytes;
  - SHA-256
    `411dc72617a5c67714ec36b45ee62e99e92c556c7f8568484e485dca0466cfc6`.
- Accepted evidence:
  - exact pre-issuance abort versus COMMIT_PUBLICATION_IN_FLIGHT split;
  - terminal zero-mutation state for every uncertain COMMITTED result;
  - retained root/canary, hard-link, named-pipe, layout, resource, hash-graph,
    cleanup, and authority closures.
- Authorization:
  - one pre-code authority/schema draft and inert fixture/mutant definitions may
    now be created and frozen;
  - future source/image bytes may not be predicted;
  - no implementation source edit, fixture executable, build, process, profile,
    ACL, discovery, admission, S10, codec, or publication action is authorized;
  - the frozen authority/fixture draft requires a separate independent GO;
  - all nine Phase-A gates remain open and S09 remains active.
- Independent result:
  [R-205 V23 Audit Result](reviews/R205_V26_RECORD_STATE_MATRIX_V23_AUDIT_RESULT_2026-08-01.md).

### R-205 V26 V23 pre-code authority and inert-fixture candidate

- Status: **IMMUTABLE PRE-CODE CANDIDATE; INDEPENDENT AUTHORITY AUDIT IN PROGRESS**
- Frozen inert fixture/mutant contract:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V23_INERT_FIXTURE_MUTANT_CONTRACT_2026-08-01.md`;
  - 19,506 bytes;
  - SHA-256
    `6fccb932e0a5bb5239f9298b811c19c99fe2ef3b6b77d32fb1b35b376e855692`.
- Frozen pre-code authority candidate:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V23_PRECODE_AUTHORITY_2026-08-01.md`;
  - 28,381 bytes;
  - SHA-256
    `273f29d87dcffb811f24c2a90ac126dd766e2990e2a5682593bff4af2a458d42`.
- Closed candidate surface:
  - exact 17-layout and 52-domain registries;
  - 22 closed fixture families, including all 1..511-byte COMMITTED tails,
    hard-link reopen evidence, helper terminal EOF, sealed-loader/share, and
    Windows x64/ARM64 feasibility kill gates;
  - exact existing and future source paths without any future source/image
    digest;
  - one-way V23 -> fixture -> authority -> source -> toolchain receipt ->
    post-code-manifest graph;
  - exact four-role source contracts, source/AST/dataflow predicates, 16-command
    toolchain order, 24 inspection outputs, and 32 bounded command streams.
- Boundary:
  - the same independent adversarial auditor must return a separate authority
    GO before any source/vector implementation, build, fixture process, profile,
    or ACL action;
  - no runtime/post-code/Phase-A/discovery/admission/S10/codec/player/release or
    publication authority is implied;
  - S09 remains active and all nine Phase-A gates remain open.

### R-205 V26 V23 pre-code authority rejection

- Status: **INDEPENDENT PRE-CODE NO-GO; NO IMPLEMENTATION**
- Audited immutable identities:
  - inert contract: 19,506 bytes, SHA-256
    `6fccb932e0a5bb5239f9298b811c19c99fe2ef3b6b77d32fb1b35b376e855692`;
  - authority: 28,381 bytes, SHA-256
    `273f29d87dcffb811f24c2a90ac126dd766e2990e2a5682593bff4af2a458d42`.
- Seven independent blockers:
  - the helper source closure omits the actual local stage-budget header;
  - the claimed existing helper path/stdio semantic baseline does not exist;
  - fixture families are prose-open rather than an immutable expanded oracle;
  - no frozen producer exists for the mandatory AST/CFG/dataflow proof;
  - the claimed PE import allowlist is absent;
  - Windows ARM64 role/fixture build and receipt ownership are not closed;
  - the integration fixture has no byte-exact authority-rooted plan/result
    transport.
- Boundary:
  - V23 authority, source/vector generation, build, fixture execution, profile,
    ACL, runtime, discovery, admission, S10, and codec work remain forbidden;
  - V24 is design-only and must close all seven blockers before another
    independent authority audit;
  - S09 remains active and all nine Phase-A gates remain open.
- Independent result:
  [R-205 V23 Pre-code Authority Independent Audit](reviews/R205_V26_RECORD_STATE_MATRIX_V23_PRECODE_AUTHORITY_INDEPENDENT_AUDIT_2026-08-01.md).

### R-205 V26 V24 byte-closed pre-code candidate

- Status: **IMMUTABLE DESIGN/AUTHORITY CANDIDATE; INDEPENDENT AUDIT IN PROGRESS**
- Frozen V24 design:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V24_BYTE_CLOSED_PRECODE_REMEDIATION_2026-08-01.md`;
  - 27,965 bytes;
  - SHA-256
    `8f76b8e5bd0e37e75c0084f1117410f9d82a6c80da600b0436e5a7e97b13b204`.
- Frozen inert manifest:
  - `native/tests/r205_v24_fixture_vectors_v1.json`;
  - 2,077,815 bytes;
  - SHA-256
    `c28c364ce30ed5e060833530edc67f297d1508d472bda43762e20cbbb0f4c37c`;
  - 4,896 fixed records, seven compact ranges, ten exact post-build prefix
    formulas, 7,224 known expanded IDs, ID SHA-256
    `faef90ca341ed7f53418a4b7c61007ba65b98790e501f45afdb63c9aa46cb9c6`.
- Frozen V24 pre-code authority:
  - `docs/reviews/R205_V26_RECORD_STATE_MATRIX_V24_PRECODE_AUTHORITY_2026-08-01.md`;
  - 22,046 bytes;
  - SHA-256
    `c6f58500f3f65d0a5ba6685d803762760026bab2892b86f2eec1e98f390cbb6e`.
- Selected remediation:
  - new honest five-partition helper and complete five-file local closure;
  - exact 192-row semantic commitment and no fictional path mode;
  - pinned Clang AST/CFG source-proof producer, six-source receipt, and 22
    uniquely anchored source mutants;
  - finite 20-name PE import set;
  - primary x64 plus six-image x64/ARM64 build graph;
  - fixed 4,096-byte integration plan, 512-byte native-runner record, and
    2,048-byte result through inherited pipes.
- Boundary:
  - design and authority both require independent GO before future sources,
    build, fixtures, profiles, or ACLs;
  - runtime/post-code/Phase-A/discovery/admission/S10/codec/player/release and
    publication remain closed;
  - S09 remains active and all nine Phase-A gates remain open.

### R-205 V26 V24 design and pre-code authority rejection

- Status: **INDEPENDENT DUAL NO-GO; NO IMPLEMENTATION**
- Audited immutable identities:
  - design: 27,965 bytes, SHA-256
    `8f76b8e5bd0e37e75c0084f1117410f9d82a6c80da600b0436e5a7e97b13b204`;
  - inert manifest: 2,077,815 bytes, SHA-256
    `c28c364ce30ed5e060833530edc67f297d1508d472bda43762e20cbbb0f4c37c`;
  - pre-code authority: 22,046 bytes, SHA-256
    `c6f58500f3f65d0a5ba6685d803762760026bab2892b86f2eec1e98f390cbb6e`.
- Eight independent blockers:
  - all 192 runtime rows omit concrete production-call tuples;
  - source, integration, layout, and domain operators remain symbolic rather
    than byte-exact inputs or deterministic formal transforms;
  - the modified Python validator is excluded from the source proof and the
    receipt has a temporal self-proof contradiction;
  - Clang proof flags do not match `-DNDEBUG` executable behavior and omit the
    ARM64 parsed configuration;
  - the integration plan omits path counts, exact timeout/policy preimages,
    runner transport, and a consistent named-pipe grammar;
  - the x64 sealed plan does not bind primary x64 build-receipt provenance;
  - post-build ranges enumerate artifacts rather than all four V23 mapping/copy
    operations;
  - per-case and aggregate/post-build results have no canonical serialization,
    path, ordering, hash, or ceiling contract.
- Retained positive evidence:
  - the five-file helper closure, honest new-helper baseline, physical manifest
    identities/counts, finite import commitment, real x64/ARM64 wrappers, and
    one-way absence of predicted future hashes remain useful inputs.
- Boundary:
  - V24 remains immutable negative evidence and authorizes no source edit,
    build, fixture, profile, ACL, runtime, discovery, admission, S10, codec,
    player, release, or publication action;
  - V25 must resolve B1 through B8 together and receive a fresh independent
    verdict;
  - S09 remains active and all nine Phase-A gates remain open.
- Independent result:
  [R-205 V24 Dual Independent Audit](reviews/R205_V26_RECORD_STATE_MATRIX_V24_PRECODE_DUAL_INDEPENDENT_AUDIT_2026-08-01.md).

### R-205 V26 V25-A V1 staged-authority early rejection

- Status: **EARLY INDEPENDENT NO-GO; ORACLE/AUTHORITY NOT AUTHORIZED**
- Audited V1 design:
  - 16,453 bytes;
  - SHA-256
    `44de3a408532ecb8d7a274580fc78ae261d2127a1ddbab15df8ce8a452e3c759`.
- Blocking result:
  - helper-visible expected values created a self-oracle;
  - instruction bytes and range construction were incomplete;
  - post-source mutation-manifest authority and exact source-freeze
    publication were absent;
  - the property/mutant map and Python-adapter contract were incomplete;
  - future checkers were not independently closed;
  - nominal sources remained under active build/import roots.
- Boundary:
  - V1 is immutable negative design evidence;
  - no oracle, authority, staged source, patch, import, build, or runtime action
    is authorized under it;
  - S09 remains active.
- Independent result:
  [R-205 V25-A V1 Early Red-Team](reviews/R205_V26_RECORD_STATE_MATRIX_V25A_V1_EARLY_REDTEAM_2026-08-01.md).

### R-205 V26 V25-A V2 split-oracle inert-staging candidate

- Status: **DESIGN REMEDIATION CANDIDATE; INDEPENDENT REVIEW REQUIRED**
- Immutable V2 identity:
  - 23,712 bytes;
  - SHA-256
    `bf1c062695233fa56bede7304f7a027b60b3ac47658767f33aca0bd97c46d751`.
- Selected correction:
  - helper receives stimulus bytes only; expectations remain outer-oracle-only;
  - all program/instruction headers, opcodes, operands, hashes, states, pointer,
    write, and residue registries are finite and byte-defined;
  - forty source-independent predicates and negative directions are frozen
    before source;
  - Stage A writes only `.candidate.txt` payloads under a non-build docs root;
  - exact source inventory, independent byte-patch manifest, and terminal
    inventory use an explicit FROZEN transaction;
  - Python facts come from pinned Python 3.14 built-in AST/dis tools and are
    checked with independently retained raw outputs plus a bounded native
    checker;
  - V24 B4 through B8 remain mandatory actual oracle values, not deferred
    prose.
- Boundary:
  - V2 authorizes only creation of a complete non-source oracle candidate and
    design validation receipt;
  - it authorizes no staging/source/patch/import/proof/build/runtime action;
  - S09 and all nine Phase-A gates remain open.

### R-205 V26 V25-A V2 early independent rejection

- Status: **INDEPENDENT NO-GO BEFORE ORACLE AUTHORING**
- Frozen audit identity:
  - 6,014 bytes;
  - SHA-256
    `5645dfcd0f807d45402cc5b1a1c91abe2fbbaf3f0d0687114a3107ccb6f0d033`.
- Blocking findings:
  - stimulus and expectations are logically but not physically separated, and
    helper-visible ordinal/partition/hash bytes still permit keyed imitation;
  - exact production-call and observation provenance is not proven;
  - BEGIN has a 193/192-byte contradiction, operand combinations and raw
    observation bytes are incomplete, and the fabricated pointer is unsafe;
  - typed-mutant, source-inventory, no-reference, and receipt authority is not
    closed;
  - the adapter AST delta, original-validator identity, Python runtime closure,
    and a genuinely independent semantic verifier are not frozen;
  - the oracle itself is proposed under an active test root.
- Decision:
  - V2 is immutable negative design evidence;
  - no V2 oracle may be authored;
  - create a V3 design with physically separate artifacts, no helper-visible
    case identity, post-source unpredictable challenges, exact ABI-call
    provenance, valid owned pointer cases, explicit typed/source inventories,
    complete Python closure, and inert oracle placement;
  - obtain another independent GO before oracle creation.
- Evidence:
  [R-205 V25-A V2 Early Red-Team](reviews/R205_V26_RECORD_STATE_MATRIX_V25A_V2_EARLY_REDTEAM_2026-08-01.md).

### R-206 S09 compact-conformance scope correction

- Status: **ACCEPTED EXECUTION CORRECTION; S09 REMAINS ACTIVE**
- Problem and measured baseline:
  - R-205 review/result history contains 76 files, 1,426,165 bytes, and
    24,813 lines; the decision log has also grown by 2,289 working-tree lines;
  - the LPAC, randomized-oracle, recursively checked authority branch defends
    against a deliberately colluding test author rather than the production
    behavior that S09 must admit;
  - this is disproportionate test-of-tests recursion and delays the MAF work.
- Alternatives:
  - continue V25-A V3 with a sandboxed randomized ABI VM: rejected for scope;
  - rely only on the existing replay: rejected because the record/state matrix
    and caller-buffer effects still need direct coverage;
  - use one direct bounded C++ state-matrix test plus independent review:
    selected as the smallest coherent gate;
  - make no change: rejected because it preserves the stalled recursion.
- Accepted compact gate:
  - freeze expected status, state, and write effects from the ABI contract,
    never from production output;
  - execute a generic table loop against the actual production ABI;
  - compare complete caller-owned buffers before and after every call;
  - cover every state and operation equivalence class, null/alias/capacity
    boundaries, invalid transitions, finish, reset, and failure atomicity;
  - include a deliberately wrong synthetic expectation proving comparator
    rejection;
  - run MSVC and Clang x64, ARM64 compile/run where available, sanitizer and
    repeated replay, followed by the retained R-203 exact-small,
    candidate-rich, and complete corpus gates;
  - obtain one independent source/result GO before S09 completes.
- Claims explicitly dropped:
  - no defense against a malicious or colluding test author, compromised
    compiler/OS/framework, or hostile third-party fixture execution;
  - no cryptographic function-call provenance, formal state-space completeness,
    recursive checker-independence proof, or sandbox certification.
- Hard budget from this decision forward:
  - at most five changed/new human-authored files and 1,000 non-generated lines;
  - C++ test at most 500 lines, scope records at most 200 combined, final audit
    report at most 250 lines, and one index row;
  - at most two repair iterations and no further preflight version series;
  - if the compact gate cannot pass inside the budget, leave the sub-gate
    NO-GO instead of rebuilding an oracle-authority hierarchy.
- Evidence-first result:
  - an independent scope audit concluded that this compact gate honestly
    satisfies S09/R-203 if production never generates expectations, the
    independent candidate-rich oracle is retained, and final toolchain/corpus
    replay remains mandatory.
- Boundary:
  - all R-205 V1-V25 artifacts remain immutable negative/research evidence;
  - this correction changes no production source, ABI, codec syntax, bitstream,
    or PCM and therefore does not trigger the R-198 music/Opus gate;
  - the next action is the compact C++ test, not V25-A V3.

### R-207 S09 unimplemented private-ABI withdrawal and closure

- Status: **INDEPENDENT GO; S09 COMPLETE; S10 ACTIVE**
- New falsification result:
  - the proposed `r205_record_*`, semantic-probe, typed-probe, telemetry macro,
    and operation-tuple symbols have zero definitions in compiled native C/C++
    source;
  - R-205 was evidence-only, and its preliminary scaffold was already removed
    without a retained production implementation;
  - the first compact-test proposal was rejected because it tested the
    unrelated `work_ledger_v1` bookkeeping state rather than the proposed
    private record lifecycle.
- Decision:
  - withdraw, do not implement, and do not claim passage of the entire R-205
    private telemetry ABI, record-ID grammar, operation-tuple, LPAC harness,
    randomized oracle, and recursive authority chain;
  - retain every R-205 artifact as immutable negative research evidence;
  - make no source change and proceed directly to S10 public-ABI conformance.
- Honest claim boundary:
  - no private-state, record-ID, sandbox, anti-hardcoding, hostile test-author,
    cryptographic call-provenance, or formal state-space claim is permitted;
  - S09 is complete only as an independently reviewed remediation-design and
    scope-correction step;
  - R-191/R-203 admission, public failure atomicity, determinism, portability,
    and resource claims remain blocked until S10 evidence and final audit pass;
  - no codec, syntax, bitrate, quality, bitstream, PCM, or player improvement is
    implied.
- S10 minimum:
  - freeze actual source/header/corpus/toolchain/command identities;
  - run retained exact-small, candidate-rich, finite, hostile, boundary,
    two-pass, allocation/OOM, concurrency, CPU/CUDA, public-ABI, and available
    sanitizer/platform gates;
  - retain commands, raw outputs, hashes, time, memory, cleanup, released
    bitstream and decoded-PCM identity;
  - obtain one independent final source/result GO/NO-GO.
- Independent verdict: **GO**. Implementing a private ABI solely to test it was
  rejected as disproportionate test-of-tests recursion.

### R-208 S10 structural parity correction

- Status: **INDEPENDENT NO-GO FOR S10 CLOSURE; LOCAL PASS RETAINED**
- Evidence retained:
  - two-pass exact-small and candidate-rich public-ABI replay agrees across
    Clang 22 and GCC 16;
  - focused native and Python gates pass;
  - a narrow 32-case CUDA CPU/GPU parity run passes on RTX 2080 Super;
  - retained speech and Mozart 3-second bitstreams and decoded WAVs are
    byte-identical to their frozen counterparts.
- Falsification and correction:
  - the inherited `10,000` CPU plus six `10,000` CUDA campaign has no recorded
    power analysis, coverage-convergence evidence, mutation-score relation, or
    defect-detection rationale;
  - it is superseded rather than treated as a proof obligation;
  - the 32-case CUDA result remains a narrow local result and is not relabeled
    as complete coverage.
- Replacement CUDA admission gate:
  - twice-run CPU equality to all 288 frozen canonical unions;
  - twice-run CUDA parity at all six thread values for the 252 nonzero cases,
    with expected `INVALID_ARGUMENT` for the 36 zero-edge cases;
  - CPU-produced public-valid boundary unions around each tile boundary,
    using exact reachable or deterministic nearest lower/upper counts and a
    structural cap of 2049 rather than an undefined maximum;
  - no-match, single-chain, branch/merge, ownership-conflict, phase, protected,
    threads `0/1025`, capacity-precedence, malformed-input, and valid
    candidate-permutation profiles;
  - twice-run bit-exact outputs, stable hashes, and an honest status/failure-
    mutation reachability registry;
  - the true resource maximum remains a separate resource-limit gate.
- Remaining S10 blockers:
  - current-source remote MSVC x64, Windows/Linux ARM64, Apple ARM64, Android
    ARM64, and iOS simulator public-ABI evidence;
  - Linux ASan/UBSan/TSan/libFuzzer evidence;
  - the replacement structural CUDA campaign;
  - explicit ABI-layout, v2 no-write, fingerprint-mutation, and
    publication-atomicity obligation evidence;
  - final independently audited artifact inventory and GO/NO-GO.
- Boundary:
  - no production or codec algorithm changed, so R-198 is not triggered;
  - no private R-205 ABI is authorized;
  - S10 remains active and S11 remains blocked.

### R-209 R-208 structural CUDA admission

- Status: **INDEPENDENT GO; CUDA STRUCTURAL OBLIGATION COMPLETE**
- Result:
  - the 495-line standalone evidence harness passed locally in 19.264 seconds;
  - an independent clean rerun passed in 16.557 seconds and reproduced every
    semantic hash;
  - all 288 CPU/frozen cases, 252 nonzero all-six-thread CUDA cases, 36
    zero-edge failures, 33 public-CPU boundary pairs, negative precedence,
    mutation laws, and status reachability passed as frozen by R-208;
  - batching preserved all 936 nonzero original edges without cross-case edges.
- Scope:
  - production source and codec outputs are unchanged;
  - the random `10,000 + 6 x 10,000` target remains superseded;
  - S10 remains active for remote platform, sanitizer/fuzzer, explicit ABI
    obligations, final inventory, and independent final admission.

### R-210 focused local ABI obligation admission

- Status: **INDEPENDENT GO; LOCAL S10 OBLIGATIONS COMPLETE**
- Existing coverage, without new test code, proves:
  - C/C++/Python ABI size and offset agreement;
  - all 8192 retired-v2 pointer/count/capacity no-write combinations;
  - missing/stale/changed-input fingerprint behavior;
  - failure publication atomicity and successful bit-exact replay.
- Results:
  - Clang 7/7, GCC 7/7, Python layout 1/1;
  - the earlier incomplete GCC attempt is rejected evidence.
- Remaining S10 scope:
  - current-source remote platform and Linux sanitizer/fuzzer receipts;
  - final bound artifact inventory;
  - one final independent source/result GO/NO-GO.

### R-211 minimal sufficient evidence and anti-recursion rule

- Status: **ACCEPTED OWNER REQUIREMENT; INDEPENDENT PRE-EDIT GO**
- Problem:
  - S09 expanded into recursive authority and harness validation for an
    unimplemented private ABI;
  - the resulting file, line, storage, and elapsed-time cost was not
    proportional to the production claim being tested;
  - arbitrary round case counts were retained without coverage, convergence,
    mutation, statistical, or defect-detection justification.
- Alternatives:
  - retain unrestricted evidence depth: rejected as test-of-tests recursion;
  - weaken conformance, comparison, security, release, or platform gates:
    rejected because those gates control real production risks;
  - require the minimum sufficient evidence tied to exact production identity:
    accepted.
- Rule:
  - every evidence gate requires a pre-code claim ledger mapping each test to
    an existing production claim or public behavior, controlled risk, current
    evidence, expected result, and failure consequence;
  - reuse identity-current public-ABI, conformance, comparison, security,
    release, and platform gates before creating infrastructure;
  - a new harness requires a written public-observability gap;
  - private/test-only ABI, semantic backdoors, friend hooks, patched production
    binaries, and a harness whose sole purpose is checking another harness are
    prohibited;
  - independent hashes, schema validation, and repeated public execution are
    the terminal integrity checks and do not create a new meta-gate;
  - freeze one cumulative budget for changed/generated lines and files,
    runtime, peak memory, retained storage, CI/device/cloud/API cost, and all
    remediation iterations; splitting or renaming does not reset it;
  - every numeric case/run count requires structural, boundary, mutation,
    convergence, or statistical rationale;
  - direct structural public-ABI evidence is preferred but cannot replace a
    required dynamic concurrency, runtime, security, or platform observation.
- Admission and kill rule:
  - admit only when the ledger is covered within budget, reproducibly, against
    the exact source/binary/command/input identity;
  - the first budget breach or remediation permits one bounded redesign;
  - a repeated breach or second remediation cycle for the same claim/gate
    stops that gate for independent redesign or scope reduction;
  - changing names, files, generations, or harnesses does not reset the count;
  - negative evidence blocks only explicitly dependent claims.
- Non-regression boundary:
  - R-198 comparisons and mandatory release, security, compatibility, and
    platform gates remain fully binding.

### R-214 S10 final admission and S11 authorization

- Status: **INDEPENDENT GO; S10 COMPLETE; S11 AUTHORIZED**
- Audited head: `1d0f6e86cded81fd156895574150b4f8f8e4d67b`.
- GitHub evidence:
  - Tests run `30724305949`: success;
  - Mobile Core run `30724305951`: success, all nine evidence jobs;
  - five valid R-203 replays agree on portable semantic identity;
  - 2,000,000 sanitizer-fuzz inputs completed with zero findings;
  - adjusted coverage is 96.3512% lines / 92.4779% branches;
  - TSan passed eight threads and 100,000 sequences;
  - Android, iOS, macOS, Windows and Linux obligations passed.
- Workflow integrity:
  - R-213 installs the frozen replay environment on Unix;
  - every Bash replay pipeline is fail-closed with `pipefail`;
  - Windows explicitly propagates piped native-process failures.
- Evidence root:
  `G:\Resonith\artifacts\r213-s10-final`.
- Disposition:
  - S10 has no remaining accepted blocker;
  - S11 anonymous multi-partial MAF predictor is the next active step;
  - R-185 preflight and independent red-team remain mandatory before source
    changes;
  - R-198 is not triggered by the workflow-only R-213 remediation.

### R-215 frozen S11 persistent multi-partial predictor

- Status: **FOCUSED S11 COMPLETE; INDEPENDENT GO; S12 AUTHORIZED**
- Problem and complete objective:
  - R-191/R-203 provides bounded anonymous complex-partial paths but no
    synthesis or actual-byte selection;
  - minimize complete container, one frozen Basis, independent per-channel
    lifetimes, and final Truth bytes under actual decoder quality, work,
    memory, startup, and fallback costs;
  - direct lapped Truth remains the complete incumbent.
- Sources of truth:
  - McAulay/Quatieri sinusoidal analysis-synthesis, global partial-tracking
    literature, MPEG-4 parametric audio/HILN, spectral-modeling residual
    practice, DDSP physical priors, R-180/R-183 negative byte evidence, and
    the admitted R-191/R-203 native paths;
  - sinusoidal tracking, parametric lines, and line-plus-residual synthesis are
    prior art and are not claimed as Resonith novelty.
- Alternatives:
  - no change/direct Truth: retained as fallback and RDO incumbent;
  - frame-local fundamental plus harmonics: rejected for polyphony,
    inharmonicity, crossings, and phase cancellation;
  - a new persistent oscillator opcode: rejected until existing MFT1 type-8
    and CBF1 transport prove complete-byte benefit;
  - independent anonymous persistent lanes: accepted as the smallest coherent
    test;
  - source-filter, phase anchors, stochastic/transient paths, latent
    separation, harmonic grouping, cross-channel reuse, learned proposals,
    and public syntax: deferred to their existing later panel steps.
- Frozen S11 language:
  - frozen used-only cosine family `{16,32,64,128,256}`, complete fixture
    SHA-256
    `9880c8f4ad2ac36e5af5302299a8a6dbbe7416b8243f48c786db3a375c40a87c`;
  - unchanged MFT1 type-8 piecewise-linear Q16 step and signed Q15 gain,
    arbitrary birth/death, one initial phase, continuous one-past phase carry,
    independent per-channel emitters, static one-hot mix, one final Truth, and
    direct Truth fallback;
  - one length is selected once per lane; length 16 maps the existing
    inclusive `+/-8 * 2^16` step range to the full signed Nyquist interval,
    while longer admitted lengths reduce interpolation error;
  - aggregate observations may propose paths but cannot share channel law,
    phase, gain, emitter, or record cost in S11.
- Reproducible in-language lower bound:
  - actual native decode of a 12-second changing/overlapping four-lane field;
  - complete CBF1 candidate `4,768` bytes versus direct Truth `119,854` bytes,
    ratio `3.9782%`, with bit-exact final PCM;
  - two runs produced receipt SHA-256
    `0b86b51d90e1be8c335103bdfb746ea408970706d88654c1452ea407bdd31668`;
  - this proves only bounded representational capacity, not analyzer recovery,
    real-audio gain, Opus gain, novelty, or promotion.
- Retained negative evidence:
  - a read-only 997 Hz diagnostic exposed 16-point interpolation residual RMS
    307.74 PCM and increased lapped Truth from 572 to 8,126 bytes;
  - final Truth and direct fallback price this error; the failed 16-only
    language was revised before the focused S11 gate rather than hidden by a
    threshold change.
- Falsifiable prediction and kill gates:
  - automatically recovered lanes must make a new complete Pareto point, with
    the predeclared focused synthetic threshold passing on at least two of
    crossing, birth/death overlap, and gap/reappearance cases;
  - path identity, channel phase, continuous split carry, CBF1/MFT1 PCM
    identity, final decoder loop, bounds, and direct fallback must remain
    exact and deterministic;
  - noise, transients, over-bound candidates, or uneconomic lanes must fall
    back explicitly rather than force model activation;
  - S12 must run the complete registered long-first comparison against the
    preceding Resonith generation and maximum-effort official Opus before any
    S13 algorithm work or promotion.
- Independent audit:
  - final **GO with no blockers** for the frozen S11 implementation;
  - signed `+/-Nyquist` edges, beyond-range rejection, all artifact hashes,
    byte closure, `2^20` phase modulus, exact split carry, and claim boundary
    were independently checked;
  - public syntax, S13+, promotion, release, novelty, and compression claims
    remain unauthorized until focused S11 evidence and S12.
- Dominated cycle-offset implementation rule:
  - S11 uses `cycle_offsets=(0,)`; nonzero duplicates change no phase or
    topology term and add only nonnegative offset cost;
  - frozen crossing evidence preserves the same selected 122-observation
    semantic sequence while reducing edges `4,755 -> 951` and native work
    `170,645,887 -> 26,757,175` units;
  - semantic identity means the ordered observation evidence, not candidate,
    incoming-edge, path, rank, or packed IDs across manifests;
  - universal bounded-frontier equivalence is not claimed because duplicate
    IDs can consume top-K state under ties or saturation;
  - the encoder work cap is frozen at `250,000,000` units; exhaustion is an
    explicit fallback, not authority to expand the cap silently.
- Basis-resolution remediation before the focused S11 gate:
  - the analyzer-recovered 16-only clean-tone candidate improved SSE sharply
    but lost rate at both 64 and 128 coefficients/frame, exposing material
    interpolation residual rather than a threshold problem;
  - alternatives were direct Truth only, 256 only with fallback above
    `sample_rate/32`, a frozen power-of-two family, or a new oscillator opcode;
    direct Truth remains fallback, 256 only loses high partials, and a new
    opcode remains deferred to S51;
  - independent audit returned **GO** for the smallest coherent frozen family
    `{16,32,64,128,256}` and **NO-GO** for adding 512/1024 in S11;
  - one length is selected once per lane as the longest member whose raw,
    corrected, interpolated, split, and tail endpoint steps all fit existing
    type-8 bounds; the length never changes inside that lane;
  - every phase mapping, distance, correction, modulo, one-past carry, split,
    and tail operation uses that length; a hard-coded 16 is a blocker;
  - only used tables are packed once in ascending-length order and their full
    byte/header cost participates in complete RDO;
  - native one-law evidence at 128 coefficients/frame gives length-128
    `3,719` bytes/SSE `0` versus direct Truth `4,229` bytes/SSE `15,724,667`,
    a 12.06% byte reduction with exact PCM; this is a focused lower bound, not
    analyzer recovery or a real-audio claim.
- Final decoder-coordinate phase-fit remediation:
  - the unchanged analyzer path remains authoritative; measured frequency may
    select only an unwrapped integer cycle and cannot change path identity;
  - a frozen Q12 weighted two-parameter integer solve proposes type-8 endpoint
    steps, with endpoint-prior weight one, exact ties-even division, fixed
    conditioning and signed 512-bit accumulator gates;
  - the actual half-away-rounded native type-8 coordinates rescore every
    observation and split; ambiguous aliases, insufficient data, range or
    conditioning failures retain the previous endpoint fitter or direct Truth;
  - no phase reset, interior anchor, per-knot phase record, or opcode is added;
    those remain S13/S51 scope;
  - the historical 4,412-byte/SSE-915,414 diagnostic is explicitly
    non-authoritative because its exact input, command, and artifact identities
    were not persisted; it is neither an admission baseline nor a passed gate;
  - the executable admission gate is the reproducible predeclared two-of-three
    structural Pareto threshold plus explicit noise/transient fallback,
    executed transport/decoder evidence, and deterministic repetition of an
    actually model-active candidate.
- Boundary-valid paid-lifetime rule:
  - an independent audit returned **GO** for excluding centered observations
    whose frozen FFT window extends beyond source bounds;
  - the complete native path and ordered IDs remain unchanged evidence; one
    deterministic maximal valid run defines separate retained-support IDs;
  - run selection maximizes covered sample span, then observation count, then
    earliest center, then lexicographic IDs, without bridging invalid rows;
  - rejected prefix, suffix, and gaps remain final Truth and no edge-padding
    extrapolation is allowed;
  - the rule changes paid S11 birth/death only and makes no unbiased-gain
    claim; complete decoder-domain RDO remains authoritative.
 - Exact constant-span tail fusion:
  - independent **GO** permits fusing an adjacent tail into a constant law only
    under identical emitter/Basis/circular/gain, 65,535-sample, frozen
    frequency/type-8, old-boundary one-past-phase, and support-contiguity gates;
  - it is not a PCM-identical refactor: the tail prediction, Truth, and complete
    RDO are recomputed and the fused form is never forced;
  - the focused receipt must expose before/after placements, boundary phase,
    complete bytes/SSE, executed CBF1/MFT1 identity, and model-active repeat
    hashes before S11 can close.
- Focused closeout evidence:
  - authoritative receipt
    `G:\Resonith\artifacts\r215-s11-focused-v3\r215_s11_focused_gate.json`,
    SHA-256
    `afcdea6a9277182b53f32b1c0777e904fe1a58c5a52ccdcd9f26e5cf462ecc95`;
  - predeclared structural Pareto threshold passed on birth/death and
    gap/reappearance; noise and transient explicitly selected direct Truth;
  - the model-active delayed/antiphase stereo candidate selected CBF1 + Truth
    at 14,051 bytes/SSE 132,190,200 versus direct Truth 15,813
    bytes/SSE 154,475,295, with identical repeated stream, PCM, lane evidence,
    and metric hashes;
  - all 16 evaluated subsets proved parser-derived S11-only records,
    CBF1/MFT1 predictor identity, and independent complete-decode identity;
  - independent final verdict is **GO with no blocking findings** and an
    independent 24/24 relevant-test pass in 6.61 seconds;
  - this closes focused S11 and authorizes only the complete S12 registered
    long-first comparison. S13, promotion, release, novelty, and compression
    claims remain blocked.

## R-217 — Owner-directed fixed official Opus direct anchor

- Status: **NORMATIVE EVIDENCE POLICY; INDEPENDENT CONDITIONAL GO CLOSED**
- The owner stopped the R-216 exhaustive Opus-frontier search during the first
  long item and narrowed S12 to a direct current-Resonith-versus-Opus
  comparison. The preceding Resonith generation is excluded from R-217.
- R-217 uses one official Opus 1.6.1 point at maximum `opusenc` complexity,
  true VBR, 20 ms, zero expected loss, 1000 ms maximum delay, default phase
  inversion, zero padding, discarded comments/pictures, and deterministic
  serial. The exact registered token `speech` selects `--speech`; every other
  item uses `--music`.
- R-217 is not the R-166 maximum-effort frontier and cannot support a general
  "better than Opus" claim. R-166 remains authoritative for any later broad
  Opus claim.
- Exactly four bitrate-feedback attempts are generated. Before any quality
  metric is inspected, one attempt is selected by absolute complete-byte
  delta, then smaller complete bytes, q5, and attempt index. Failure to enter
  `max(64, target_bytes // 1000)` is `UNMATCHED` and forbids equal-rate claims.
- The selected Ogg is decoded by official `opusdec`; current Resonith is
  decoded by the Golden Core. Each receives one common metric pass from
  identical PCM.
- Partial R-216 staging has diagnostic value only and cannot seed R-217.
  R-217 receives a new run identity, output schema, long-first atomic receipts,
  frozen path/process/time/RSS/disk bounds, and fresh S11 and Opus encodes.
- Independent red-team initially returned NO-GO and then authorized the
  smallest coherent implementation after the claim, selection, container, and
  authority remediations above were incorporated in
  `docs/reviews/R217_S12_FIXED_OPUS_DIRECT_PREFLIGHT_2026-08-02.md`.
- S13 remains blocked until all 19 R-217 receipts and the aggregate direct
  report pass. This is an explicit owner-directed S12 evidence amendment, not
  a silent modification of the stable 63-step panel.
- First full-run incident and sole bounded redesign:
  - full Mozart committed in 356.707504 seconds with receipt SHA-256
    `99a0fcf1624860554331dfea6119918d77636586bf2b12c1cfa9b5fbe61123ef`;
  - `ebu-claves` then failed closed at its exact 420-second S11 child ceiling,
    without a stream, receipt, RSS/disk breach, orphan, or blind retry;
  - the 2,998-byte failed staging was atomically quarantined with both file
    hashes preserved;
  - independent GO permits one change only: short S11 900 seconds and short
    worker 1,200 seconds, with every other algorithm, identity, corpus and
    resource bound unchanged;
  - the redesigned run uses a new output root and repeats Mozart; any second
    budget breach stops R-217 instead of expanding the limit again;
  - complete evidence is in
    `docs/reviews/R217_S12_SHORT_TIMEOUT_INCIDENT_2026-08-02.md`.
- Second full-run stop:
  - the new run identity
    `68ee12a3560fab4bbe16969dc85488bdddace28913d4330e08770a10f558a6c3`
    independently repeated Mozart and committed `ebu-claves` in 800.877559
    seconds;
  - `ebu-cymbal` then exceeded the redesigned exact 900-second S11 ceiling
    without an output, receipt, RSS/disk breach, orphan, or retry;
  - its 3,009-byte request-only staging was atomically quarantined with both
    hashes preserved;
  - R-211 now forbids another ceiling increase. R-217 is stopped until an
    independently audited, output-identical S11 performance redesign fits the
    existing bound, or the owner explicitly reduces scope;
  - partial Mozart/claves evidence is retained but does not close S12 or
    authorize S13/promotion;
  - exact evidence is in
    `docs/reviews/R217_S12_SECOND_TIMEOUT_STOP_2026-08-02.md`.

## R-218 — Output-identical S11 analyzer performance remediation

- Status: **INDEPENDENT GO; BASELINE FINGERPRINTING AUTHORIZED**
- Problem: the fixed R-217 direct comparison stopped twice because the frozen
  S11 analyzer used 792.173 seconds on `ebu-claves` and exceeded 900 seconds on
  `ebu-cymbal`, despite both inputs containing only 529,200 stereo frames.
- Objective: make the existing 900-second S11 ceiling sufficient without
  changing the S11 candidate language, observation values/order, native graph,
  selected payload, decoded PCM, resource/security behavior, or R-217 Opus
  anchor.
- Measured focused profile:
  - 42.579 seconds total under `cProfile`;
  - 29.592 seconds in `observe_complex_partials`;
  - 11.921 seconds in `_candidate_peaks`;
  - 8.120 seconds in `_direct_dtft`;
  - 5.488 seconds in `_assign_conflict_groups`.
- The independently reviewed remediation is sequential A, then B, then C:
  remove the tail-list copy; prove identity; hoist one immutable PCM16-to-
  float64 conversion; prove identity; then hoist only exact DTFT constants and
  the identical per-frame window product; prove identity. The generation may
  be admitted only if every checkpoint passes independently.
- The first audit returned NO-GO because selected fallback bytes alone could
  hide changed search state, stable source ownership was unstated, runtime
  admission was ambiguous, and raw-PCM/resource gates were incomplete. The
  revised preflight requires a pre-edit byte-level fingerprint of observations,
  graph inputs/edges/paths, lowered lanes/subsets and RDO ledger; stable
  non-concurrently-mutated PCM; exact <=475-second claves and <=600-second
  cymbal limits; raw PCM identity; and unchanged RSS/disk ceilings.
- No timeout increase, candidate pruning, approximate search, reordered
  floating reduction, new Opus search, or new codec algorithm is authorized.
- Implementation was blocked until the independent auditor issued binary GO
  on the revised remediation and identity gates recorded in
  `docs/reviews/R218_S11_OUTPUT_IDENTICAL_PERFORMANCE_PREFLIGHT_2026-08-02.md`.
- Final independent re-audit verdict: **GO** on preflight SHA-256
  `9900e569df3fd6f33ef637a0d4f0c525196664fb8eee756b1e4c6abb768641b7`.
  Authorization is limited to sequential A -> exact identity gate -> B ->
  exact identity gate -> C -> exact identity gate. Any mismatch kills that
  checkpoint; no tolerance, timeout increase, pruning, reordered arithmetic,
  GPU path, or comparison-scope change is authorized.
- Implementation evidence status: **INDEPENDENT FINAL CLOSEOUT GO; IMMUTABLE
  COMMIT PREPARATION**.
  - A removed only quadratic suffix-list allocation and reduced full claves
    encode from 774.105972 to 237.670336 seconds while preserving the complete
    internal SHA-256
    `79c11ca6b160d80330c30944e82d59207b8b7e4157d5984d3b7826f019a34a2b`.
  - B hoisted the stable PCM16-to-float64 snapshot and preserved every named
    internal identity; full claves fell to 220.386926 seconds.
  - C reused the identical windowed frame and immutable DTFT constants while
    retaining the same `np.exp` and axis-0 `np.sum` order; full claves fell to
    196.590282 seconds, a 3.9377x speedup over baseline.
  - full cymbal, which previously exceeded 900 seconds, completed in
    233.343736 seconds and repeated in 239.125873 seconds with identical
    internal, payload, and decoded-PCM hashes.
  - all seven focused cases, both active real prefixes, and full claves kept
    identical observation/graph/lane/subset/RDO, payload, and PCM hashes after
    each A/B/C checkpoint. No Opus point was searched or encoded by R-218.
  - detailed retained evidence is in
    `docs/results/R218_S11_OUTPUT_IDENTICAL_PERFORMANCE_2026-08-02.md`.
  - the independent closeout audit reproduced all reported hashes, all 30
    baseline/A/B/C semantic identity comparisons, both C-repeat payload/PCM
    identities and the 16-test gate, but rejected the resource-evidence
    contract: historical checkpoint JSON files omitted externally measured
    resource fields and the C-repeat helper asserted zero temporary bytes;
  - A and B are proof checkpoints rather than retained generations, so they
    will not be rerun solely for telemetry. Their resource-admission claim is
    withdrawn. Final C must instead repeat full claves and cymbal under a
    fail-closed parent monitor that creates a suspended child inside an
    active-process-limit-1 Windows Job Object, hashes authorities before and
    after, and records operating-system peak working set plus staging byte
    high-water under the unchanged 8 GiB/2 GiB/600 s limits. This supersedes
    original gate 8 only for historical A/B resource admission;
  - R-217 itself must not be bypassed: it correctly rejects the dirty changed
    analyzer, pins the pre-R-218 revision, and omits the analyzer from run
    identity. After R-218 closes, selected R-218 files require an immutable
    commit and a new independently audited direct-comparison identity that
    explicitly hashes the analyzer while preserving the single fixed official
    Opus 1.6.1 point;
  - exact remediation scope and kill gates are appended to the R-218
    preflight. S12 remains blocked until the auditor authorizes and closes both
    evidence gaps.
  - first monitor-code audit: **NO-GO for real repeats**. Job structure layouts,
    active-process enforcement and the eight focused tests passed, but four
    closeout gaps remain: the parent gate needs an externally supplied audited
    self-hash; receipt-inclusive disk bytes need a final limit check; failure
    cleanup needs checked `TerminateJobObject` plus verified child death and
    checked handles; and the receipt needs observed sample count/maximum gap,
    not only a configured interval;
  - selected smallest remediation: require and record an audited parent-gate
    SHA-256 argument; target 10 ms sampling and fail if observed start-to-start
    gap exceeds 25 ms; reject receipt-inclusive bytes above 2 GiB; check every
    monitor-owned handle operation; on any monitor failure terminate the Job,
    wait for and verify child exit, with an explicit process-kill fallback if
    Job termination itself fails. Focused mutants must cover wrong gate hash,
    receipt overflow, sampling overrun, and child cleanup before any real C
    repeat.
  - first independently authorized full-claves resource launch failed closed
    in 0.9 seconds before encoding because the helper was invoked by script
    path without `PYTHONPATH`; its absolute import of `experiments` failed.
    The fresh staging root is empty and no child survived. A no-encode `--help`
    probe reproduced the exact `ModuleNotFoundError`;
  - a non-encoding test falsified module-only launch: the existing dependency
    graph also imports top-level `cibs0` from `reference`. Retry remains
    blocked. The selected correction is pinned Python `-I -c` with a recorded
    bootstrap that inserts only the resolved repository and `reference` roots,
    then runs the same hashed module; inherited `PYTHONPATH` remains excluded.
    The new gate must also expose bounded child error evidence, pass focused
    tests, receive a fresh external parent hash and independent GO, then use a
    new empty staging root. Full evidence is in
    `docs/reviews/R218_S11_RESOURCE_GATE_LAUNCH_INCIDENT_2026-08-02.md`.
  - the remediated parent gate received independent GO at SHA-256
    `3128e5f75dc5bf1955aec9515ba35c1cd8672aced3c86137cd1a84ce9436d198`;
    its 13 focused fail-closed tests independently passed;
  - authoritative final-C resource repeats both pass with frozen internal,
    payload and PCM identities unchanged:
    - claves: 193.272769-second encode, 256.040667-second parent wall,
      782,192,640-byte peak working set, 10.6424-ms maximum observed sample
      gap, 9,995-byte receipt-inclusive disk high-water, parent receipt
      SHA-256 `d0a3193b4d3845e6dd15e9bec379902e8dc56a6c64da63a77ef373b0f867ee6b`;
    - cymbal: 229.107934-second encode, 302.371870-second parent wall,
      848,003,072-byte peak working set, 11.0230-ms maximum observed sample
      gap, 9,973-byte receipt-inclusive disk high-water, parent receipt
      SHA-256 `923f22901a173cfc01a98e7e3ad856b53794fb83adc56786c09c0a48bc5a1527`;
  - both remain below the unchanged 600-second, 8 GiB and 2 GiB ceilings;
  - independent final closeout recomputed receipt hashes and fixed-point sizes,
    every pre/post authority, frozen internal/payload/PCM identities, runtime,
    RSS, disk, sample counts/gaps, report arithmetic and the empty failed root.
    Verdict: **GO for narrow immutable-commit preparation only**. Commit scope
    requires a separate staged-index audit; pushing, old-R-217 reuse, a new
    runner, Opus and corpus work remain unauthorized at this boundary.

## R-219 — Post-R-218 fixed-Opus direct comparison identity

- Status: **PRE-CODE; INDEPENDENT GO/NO-GO REQUIRED**
- R-218 is immutable at revision
  `64521b19551d4b9688de10fe01c5302607a5beb1`, but R-217 intentionally pins the
  preceding source revision and lacks explicit analyzer identity. It must fail
  rather than be bypassed.
- Owner scope remains direct current Resonith versus one fixed official Opus
  1.6.1 maximum-complexity point. No Opus-frontier search and no preceding-
  Resonith comparison column are authorized.
- Selected smallest change: a new R-219 controller generation preserving every
  R-217 algorithm, command, metric, byte-selection, corpus, ordering, atomicity,
  time and resource rule while changing only schemas/error labels, source and
  preflight identities, and explicit analyzer authority.
- The analyzer must be hashed in controller material and worker requests before
  and during work. Old R-217 output remains diagnostic and cannot seed R-219.
- Pre-code model, alternatives, fixed authorities and kill gates are in
  `docs/reviews/R219_S12_POST_R218_DIRECT_IDENTITY_PREFLIGHT_2026-08-02.md`.
  Controller code remains blocked pending an independent verdict.
- First independent pre-code verdict: **NO-GO**. The R-217-shaped request was
  mutable after creation and `item_id` did not bind every algorithmic field;
  analyzer pre/post hashes also could not exclude change-use-restore ABA during
  the nested S11 child.
- Revised design seals exact request bytes through out-of-band argv SHA plus a
  canonical manifest-item hash, verifies both in receipt and index, and holds
  Windows deny-write/delete handles over the complete frozen imported execution
  set and current source throughout worker execution and final verification.
  First start requires a nonexistent reparse-free root; resume is explicit and
  accepts only an exact indexed R-219 tree. Old R-217 schemas/tree adoption,
  analyzer/dependency ABA and unchanged-id request mutants are mandatory
  negative tests. Code remains blocked pending re-audit.
- Second independent pre-code verdict: **NO-GO**. The allowed-diff gate had not
  been expanded to the required controls; file handles alone did not prevent
  ancestor-directory path swap; authority hashes and locks could diverge across
  hand-maintained lists; and request bytes would still have been deleted.
- Revised closure uses one canonical sorted declared project/tool/input
  authority set for hashes, locks, material, request and receipt; holds both
  file and ancestor-directory deny-delete handles; retains exact sealed request
  bytes in every completed item; and quarantines rather than adopts an
  unindexed rename-before-index crash product. Python site-packages and Windows
  remain an explicitly version-pinned frozen-host assumption, not a false
  whole-OS byte-lock claim. The allowed diff and required cross-process mutants
  now enumerate these controls. Code remains blocked pending another verdict.
- Third independent pre-code verdict: **NO-GO**. A singular authority digest
  ambiguously included a different current WAV for each item, and the stated
  hash/lock order left a mutation window between observation and lock.
- Finalized identity model separates one run-wide static
  `base_authority_set_sha256` from nineteen manifest-bound
  `item_authority_set_sha256` values formed by adding exactly one source WAV.
  Paths and ancestors are validated first; all directory/file handles are then
  acquired in sorted order; hashes and digests are computed and compared only
  while every lock is live; request creation/worker launch follows; postflight
  hashes are checked before release. A synchronized hash-before-lock mutant is
  mandatory. Code remains blocked pending re-audit.
- Fourth independent pre-code verdict: **NO-GO** solely because stale
  singular-digest wording contradicted the normative base-plus-nineteen-item
  model and did not state when run identity becomes immutable.
- The stale wording is removed. Run identity/material is computed once before
  item execution from expected static rows plus the ordered nineteen manifest
  source hashes. Under-lock observations must equal those precommitted base and
  item values before request creation and can never redefine the run. Code
  remains blocked pending final pre-code re-audit.
- Final implementation audit: **GO for the exact R-219 direct gate**.
  - runner SHA-256:
    `e5f17b7a036cf83b408eebe0b65fb8c21be6da41c3b8343b4d1f2654ab989f54`;
  - focused-test SHA-256:
    `9d441eec34cd8f4a872da26942e941f4d8a1741e679e57808a7d20dadbcbde30`;
  - 27/27 focused tests independently passed in 2.63 seconds;
  - exact prefix resume, request retention/sealing, base-plus-nineteen item
    authorities, Windows file/ancestor locking, R-217 rejection, emitted
    two-codec output and pinned host identity all passed;
  - AST comparison confirmed the computation-critical S11 and fixed-Opus
    functions remain R-217-equivalent after label normalization;
  - the authorized execution is current Resonith versus one fixed official
    Opus 1.6.1 point only. No frontier search, preceding-generation column,
    S13, promotion or release is authorized by this verdict;
  - complete verdict:
    `docs/reviews/R219_S12_DIRECT_IMPLEMENTATION_AUDIT_2026-08-02.md`.

## R-221 — Bounded rate-only matching for direct comparison

- Status: **IMPLEMENTED; COMPLETE CORPUS ADMITTED BY R-223**.
- R-219 stopped correctly on `ebu-female-speech-en`: the four fixed Opus
  attempts bracketed the 94,816-byte target but missed the 94-byte tolerance.
  Repeating them is a blind retry; searching other Opus configurations is
  outside owner scope.
- Selected remediation preserves the first four attempts and every Opus
  configuration coordinate, then permits at most eight integer-bitrate
  bisection attempts inside the observed byte bracket. Quality is unavailable
  to the controller until one point has been selected.
- If twelve attempts still do not match, the nearest actual point is retained
  with explicit `UNMATCHED_NEAREST` and byte/rate delta. It cannot support an
  equal-rate winner claim but no longer prevents reporting the rest of the
  corpus.
- No R-219 output may seed R-221. S11, metrics, decoders, corpus/order and all
  resource/time bounds remain unchanged.
- Preflight and gates:
  `docs/reviews/R221_S12_BOUNDED_RATE_MATCH_PREFLIGHT_2026-08-02.md`.
- First independent pre-code verdict: **NO-GO**. The no-bracket path was
  undefined, VBR nonmonotonicity made the bracket rule ambiguous, and unmatched
  rows were not mechanically excluded from equal-rate aggregate claims.
- Remediation forbids extrapolation. A legal bracket is an observed
  q5-ordered sign-changing pair outside the strict tolerance; the minimum-span
  pair is recomputed from every unique observation with a fixed tie order.
  Missing, duplicate or non-shrinking brackets terminate immediately to the
  quality-blind nearest point. Aggregate status/counts exclude every unmatched
  row from all equal-rate statistics and claims. Code remains blocked pending
  re-audit.
- Second independent pre-code verdict: **NO-GO** on three deterministic details:
  midpoint rounding, terminal fallback coverage and repeated-q5 handling.
- The exact midpoint is now `q_low + (q_high - q_low) // 2` and must remain
  strictly internal. Every no-match terminal condition selects nearest with no
  further encode. Equal-q5 observations must have identical bytes and
  normalized Ogg hash or fail determinism; agreeing duplicates collapse to the
  earliest attempt only for bracket construction. Code remains blocked pending
  final re-audit.
- Final independent pre-code re-audit of exact preflight SHA-256
  `a97c1da031e905e4ac55d16f13f069f12cc330a2a657951e7824eadf1ca2c755`:
  **GO with no blocking findings**. It authorizes only the exact bounded
  controller implementation and focused validation. Corpus execution still
  requires post-implementation identity audit.
- Final post-implementation audit: **GO for one fresh complete corpus run**.
  Runner SHA-256 is
  `830ed4ac12b369bcf9de7308fa18bfb5b31c0989c11aaa665f052a9d87d869a3`;
  focused-test SHA-256 is
  `76f51f610927169bbe0cb1a51b30e1d7e53c5c496f2d099d09bec2e26a2e3947`;
  the independent rerun passed 32/32 in 2.71 seconds. No R-219 reuse,
  admission, S13, version promotion, release, or general Opus claim is
  authorized. Full verdict:
  `docs/reviews/R221_S12_BOUNDED_RATE_IMPLEMENTATION_AUDIT_2026-08-02.md`.

## R-222 — Durable GitHub history and checkpoint versioning

- Status: **OWNER-ACCEPTED PROCESS REQUIREMENT**.
- Every coherent externally synchronized change must update the English
  changelog and durable all-63-step R-204 checkpoint, then use explicit-file
  staging and an immutable commit SHA. Experimental identities are R-number
  plus commit SHA; `VERSION` changes only for an admitted generation or
  release.
- A commit or push is repository synchronization only. It cannot admit an
  experiment, imply compatibility, create a release, or establish a quality or
  compression claim.

## R-223 — S12 complete direct-comparison admission

- Status: **INDEPENDENT GO; S12 COMPLETE IN THE DECLARED NARROW SCOPE**.
- The preserved R-221 run identity is
  `470603e2f8fed8957e0eade645bd78fbab1b50fd35aad624b9be473dd23dc73c`
  at source revision `1c45376eebe7daa49904acae885c47d6d571cf87`.
- Nineteen registered inputs completed. Sixteen are `STRICT_MATCH`; female EBU
  speech, male EBU speech, and sustained sine are `UNMATCHED_NEAREST` and are
  mechanically excluded from all equal-rate statistics and claims.
- The strict rows cover 570.628 seconds and total 9,602,867 Resonith bytes
  versus 9,602,500 Opus bytes, a difference of 367 bytes or about 0.0038%.
- Resonith wins waveform SNR on 13/16 strict rows, registered channel-0 phase
  MAE on 15/16, mean pre-echo on 14/16, magnitude cosine on 11/16, and log-mel
  RMSE on 9/16. Opus wins detailed log-spectrum distance on 11/16.
- The result identifies a stable split: current Resonith commonly preserves
  waveform timing, channel-0 phase and attacks much more accurately, but loses
  important low-energy spectral detail and speech-critical envelopes on
  several classes.
  Later MAF work must repair that allocation without discarding the temporal
  advantage.
- Independent audit closed all 19 authority chains, re-decoded every Opus and
  Resonith artifact, replayed every metric and q5 transition, and found zero
  blocking issues. Three ESTOI differences of `2.22e-16` through `9.99e-16`
  are non-decision-changing floating-point rounding.
- Machine evidence SHA-256 identities:
  - `aggregate.json`:
    `f8aeed2a205e7c802fd093d9de90bf1b4df9b751b1225d5b00592020889acfcf`;
  - `REPORT.md`:
    `a89dddd2f578712063973024cbcd0da2809f21189f11cf11ce8aa4fcc57ea534`;
  - `run-index.json`:
    `ed1d8e5505ccf0fe0af4b59725e1f5e1c30fefc67218aff9b3608b9046140ecd`.
- Detailed result:
  `docs/results/R221_S12_FIXED_OPUS_DIRECT_2026-08-02.md`.
- Independent verdict:
  `docs/reviews/R223_S12_COMPLETE_CORPUS_AUDIT_2026-08-02.md`.
- This admission does not authorize an Opus frontier, a full-19 equal-rate
  claim, general superiority, a release, or a `VERSION` increment. S13 is the
  next step and requires its own evidence-first preflight.

## R-224 — S13 phase-economy oracle and syntax hold

- Status: **PREDECESSOR COMPARISON PRE-CODE GO; S13 SYNTAX NO-GO**.
- The S13 objective is corrected from generic phase improvement to a narrower
  economic question: can objective phase evidence reduce complete final-Truth
  cost while preserving the incumbent decoded quality? R-221 already reports
  strong phase and transient accuracy, but all nineteen retained Resonith
  streams selected `truth-fallback`; those results do not prove that the S11
  persistent-partial model was active or that a phase-anchor law is needed.
- Prior art is explicit. McAulay--Quatieri tracks sinusoidal amplitude,
  frequency and phase with birth/death handling and cubic phase interpolation;
  MPEG-4 HILN carries phase-continuous parametric lines; PARSHL and spectral
  modeling retain sinusoidal trajectories plus residual. S13 claims no novelty
  for phase continuity, phase locking, cubic interpolation, or line-plus-
  residual synthesis.
- Frozen alternatives, all charged through actual complete bytes and one final
  decoded Truth, are:
  - no change and direct Truth;
  - the exact S11 incumbent, including its decoder-coordinate phase fit and
    endpoint phase correction through frequency steps;
  - a pure phase-blind continuous arm whose post-birth fit, thinning and knot
    selection cannot observe phase;
  - denser phase-blind frequency knots;
  - the smallest existing-syntax triangular frequency bridge;
  - split/rebirth with deterministic crossfade;
  - a sparse phase-innovation bridge; and
  - a zero-byte exact-phase oracle that is an upper bound only.
- A cubic smoothstep correction is not equivalent to existing type-8 linear
  frequency interpolation: it creates cubic phase and quadratic instantaneous-
  frequency correction, while type-8 creates quadratic phase. No new cubic
  decoder law or opcode is authorized unless it materially beats both the
  triangular existing-syntax control and the best type-8 approximation.
- Phase gauge is frozen before any experiment. The non-phase base law cannot
  change after anchor fitting; signed gain versus phase-plus-pi, shortest-turn
  half-cycle ties, analysis-window origin, amplitude nulls, beating, crossings,
  gap/reappearance and route delay remain explicit ambiguities. Phase events
  are forbidden below a frozen amplitude/confidence floor. Identity changes
  choose rebirth or fallback rather than an anchor.
- S13 cannot import S35 shared-route syntax. Experimental selection may jointly
  protect channels, but every channel remains independently paid. Evidence must
  report every channel, mid/side error, interchannel phase, delay/correlation,
  antiphase cancellation and the existing channel-0 metric.
- Existing MFT1 type-8 placements carry absolute source position. S13 therefore
  has no existing persistent phase state whose lost event would corrupt all
  future phase. Stateful anchor/checkpoint syntax remains S51 scope. S13 may
  first evaluate only an encoder-side oracle and existing-syntax experiments;
  corruption or checkpoint claims cannot exceed the current absolute-record
  container.
- Mandatory baseline closure precedes the oracle. R-221 deliberately omitted
  the preceding-Resonith column under the then-active owner scope. The current
  candidate closure is a machine proof that every retained R-221 stream selected
  the unchanged direct-Truth fallback and is bitstream/decoded-PCM identical to
  the pre-S11 direct-Truth generation. If complete recursive code/configuration,
  native-decoder, input, payload and PCM identity cannot be proven for all
  nineteen items, run the missing preceding-generation comparison instead.
- The first baseline-proof re-audit returned **NO-GO** on authority closure,
  not on the derivation principle. The proof is revised to bind the exact
  `ca87dec` `encode_lapped_stream` producer blobs and current on-disk blobs;
  every explicit/default call argument; PCM layout and registered order; the
  loaded DLL, ABI/header, dependency and stateless-call contract; pinned Python,
  NumPy, module origins, package roots and dynamic import closure; fallback
  payload/reconstruction non-mutation; every receipt/index/artifact/replay; and
  per-item derived preceding/current rows with the derivation stated. Merely
  copying a current hash into a `preceding` field is forbidden. A final binary
  GO remains mandatory before this proof tool is implemented.
- The derived static proof is rejected as unnecessarily complex after that
  audit. The selected smaller authority is an actual counterfactual execution
  of the exact pre-S11 `ca87dec` direct-Truth producer on all nineteen frozen
  R-221 inputs, followed by actual native decode and byte-for-byte/PCM-for-PCM
  comparison with sealed R-221 outputs. Opus is not rerun. Duplicate historical
  streams and WAVs are omitted only after equality; any mismatch is retained
  and terminates the gate.
- Independent re-audit returned **GO** for this actual-run replacement,
  conditional on the exact archive/extraction, isolated runtime/module origin,
  native DLL/source/ABI, per-item PCM/configuration, sealed receipt, process
  bound, mismatch-retention, nineteen-row aggregate and negative-test fields
  frozen in the R-224 preflight before implementation.
- Final independent verification bound the exact amended preflight SHA-256
  `a92b3ad2f04719c59cb1364294db1e4dc8d05a0872d1d590c85ef7920e1ca134`
  and returned **GO with no blocking findings** for implementing and executing
  only the bounded nineteen-item `ca87dec` predecessor comparison. Stage-1
  oracle code, S13 behavior, syntax, Opus reruns, promotion and release remain
  unauthorized.
- Stage-1 oracle inputs, in order, are full 400.773-second Mozart,
  319.38-second single-speaker LibriSpeech, full 658.32-second *Elephants
  Dream*, and 600-second bounded synthetic vibrato. Freeze exact S11 paths,
  supports, observations, Basis lengths, gain/frequency laws, source hashes,
  decoder, Truth settings, candidate order, time, memory and retained-storage
  budgets before the first run.
- Kill S13 before syntax unless the free exact-phase oracle reduces compressed
  final-Truth bytes by at least 10% on at least three deterministically eligible
  complete inputs and creates a decoder-domain quality Pareto point. Real-audio
  files are not silently labelled coherent; eligibility is numeric and label-
  free.
- If and only if the free oracle passes, one focused existing-syntax experiment
  compares the eight frozen arms on stationary tone, linear chirp, one known
  phase innovation, close-tone crossing with an amplitude null,
  gap/reappearance, delayed/antiphase stereo, and the strongest qualifying real
  long input. Tone and linear chirp must select zero anchors; bounded vibrato
  uses at most one anchor per second.
- A paid phase candidate is killed unless it beats exact S11, pure continuous,
  dense-frequency and rebirth/crossfade by at least 3% complete bytes at the
  frozen quality floor on at least two long real inputs, while preserving all-
  channel quality, CBF1/MFT1 decoder identity, callback partition identity,
  random-slice identity and existing bounded-resource limits.
- S14 full registered comparison remains blocked until an S13 candidate passes
  both gates. Failure is a valid S13 no-change result and advances the plan to
  source-filter S15 without adding decoder complexity.

## R-225 — R-224 controller independent minimal redesign

- Status: **INDEPENDENT REDESIGN GO; CORPUS EXECUTION NO-GO**.
- The first implementation audit rejected seven authority gaps. One bounded
  remediation closed current-artifact TOCTOU, symmetric atomic mismatch
  retention, fail-closed resource sampling, aggregate time/storage bounds,
  complete module inventory, strict receipt validation and direct production
  validators. The second audit still returned NO-GO on four residual gaps.
- R-211 therefore forbids another ad-hoc patch cycle. A second independent
  auditor designed the only authorized replacement, limited to the existing
  controller and focused test module:
  1. inspect the lexical drive-root-to-leaf path with `lstat` before any
     resolution or traversal, reject every reparse component, and recursively
     recheck the final evidence root after publication;
  2. duplicate the exact Windows child-process handle once, retain it through
     termination, and use one mandatory post-exit lifetime
     `PeakWorkingSetSize`/CPU sample as the authoritative resource value;
  3. construct one full absolute argv before request publication, execute that
     list unchanged, compare it with `sys.orig_argv`, and retain the full list
     plus canonical digest in request, receipt and aggregate;
  4. exercise payload-only and PCM-only mismatch paths through the real
     isolated historical worker, actual `ca87dec` tree, frozen native Core and
     frozen short speech source. Either mismatch must retain both historical
     artifacts atomically, publish a canonical MISMATCH receipt and terminate
     nonzero without an aggregate.
- Rejected substitutes are resolve-then-lstat, reopening by PID, faster polling
  without a final lifetime counter, recording only an argv digest, helper-only
  mismatch tests, monkeypatches, request flags, environment triggers and a
  test-only codec ABI.
- Admission remains blocked until the existing focused tests plus the lexical
  junction/final-root checks, post-exit resource checks, complete argv
  equality/mutation checks and two real mismatch executions pass, followed by
  a fresh independent implementation GO. The nineteen-item predecessor run,
  Stage-1 phase oracle, syntax, version, release and Opus rerun remain blocked.

## R-226 — R-224 predecessor aggregate admission

- Status: **INDEPENDENT AGGREGATE GO; STAGE-1 PRE-CODE GO ONLY**.
- The redesigned controller passed 49/49 focused tests and a final independent
  implementation audit. Its frozen identities are controller SHA-256
  `f4ed3b6197338918da381604dfc561038a6cfcdcd2cf0952929cefc3982e57c4`
  and test-module SHA-256
  `5034aa835fe4aa40e4cd8e8e524163b72f240f8cbcea2f3c04adc9d241527b41`.
- The only authorized fresh execution completed all nineteen registered inputs.
  Historical/current payload identity is 19/19 and native decoded-PCM identity
  is 19/19, with zero skips, duplicates, quarantines or mismatch artifacts.
- Independent recomputation confirmed aggregate file SHA-256
  `4f3ee90bda70b573d95250cd05fcac0cdf70b8cff6f3221f1491d46f93fa6864`,
  aggregate material SHA-256
  `90629dfa11f20ae346ae6a11365c623c6e2eb66199f54159c0952ddc73713d12`,
  historical archive SHA-256
  `6232d28b8ac4306821f58ed6be94de2db342814f0d7dc1c7f38adc94530752a6`,
  and identical 572-entry archive/extracted inventories with digest
  `72fd4991bae9c651e92bc5430afc11b9a67e8cc95a6a4542af9346d7876d4f7f`.
- Controller wall before aggregate was 339.6762922 seconds. Maximum child peak
  working set was 2,493,497,344 bytes, retained bytes before aggregate were
  16,389,899, and the final evidence package was 16,705,533 bytes. Every frozen
  time, memory and retention bound passed.
- R-224 therefore proves that every registered R-221 Resonith output is the
  unchanged pre-S11 direct-Truth result. The R-221 quality comparison cannot be
  attributed to an active S11 persistent-partial lane.
- The independent auditor returned GO only for Stage-1 pre-code planning and a
  bounded encoder-side free-phase oracle. Before execution, a Stage-1-specific
  record must freeze the exact four source PCM identities, S11 observations,
  paths and supports, Basis and gain/frequency laws, lane caps, decoder/Truth
  settings, entropy backend, candidate order, resource ceilings, runner and
  focused tests. A separate implementation GO is mandatory.
- Paid phase syntax, decoder or bitstream changes, Opus reruns, product/API or
  version changes, promotion and release remain **NO-GO**.
- Detailed result:
  `docs/results/R224_S13_PREDECESSOR_COMPARISON_2026-08-02.md`.
- Independent verdict:
  `docs/reviews/R226_R224_PREDECESSOR_AGGREGATE_AUDIT_2026-08-02.md`.
