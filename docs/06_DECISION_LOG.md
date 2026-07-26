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
