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
- Status: **ACCEPTED / IMPLEMENTING / NORMATIVE-DRAFT**
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
