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
