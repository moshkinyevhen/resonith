# Resonith

**Resonith** is a standalone continuous-time acoustic-field audio codec. Its
internal architecture is **MAF — Memory-oriented Acoustic Field**.

> **Resonith — encode acoustic causes, not repeated waveform blocks.**

The canonical formula is:

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+ TruthInnovation_t
+ OptionalPerceptualDetail_t.
\]

Resonith represents long-lived coherent, stochastic, resonant, and transient
acoustic atoms. The encoder may use score transcription, source separation,
instrument recognition, and large neural teacher models. The normative
decoder executes only a small, bounded, deterministic integer acoustic ISA.

**ACCEPTED:** Main-0 includes **CIBS — Cached Integer Basis Synthesis**. A
compact latent is materialized once by a fixed integer synthesis graph into an
immutable timbre, filter, or control Basis. The real-time sample loop then uses
that cached Basis without per-sample neural inference.

Resonith is independent of SceneLith Video and always supports standalone
decoding. Their optional specialized integration is defined separately by the
SceneLith AV Bridge.

Current implementation version: **0.1.0-alpha.1**. The bitstream specification
is an independently versioned normative draft.

## Executable status

The repository contains:

- MAF-P0 single-Basis baseline;
- MAF-P1 immutable multi-Basis Bank with validated lifetimes and reuse;
- absolute continuous Q32 pitch/phase trajectories with random access;
- bounded reversible integer-lifting transient events;
- RAW and CIBS Basis banks plus bounded `LiftPack-1`/`LiftPack-2` objective
  residuals with exact block-local integer LPC;
- the compact deterministic `RSC1` typed section-container candidate;
- a dependency-free C++23 whole-RSC1 Golden Core behind a stable C99 ABI;
- allocation-free block indexing, random block decode, linear residual
  cursors, and callback-oriented zero-Atom/model-bearing PCM playback;
- registry-backed latent-only `BCIB` Basis transport with preflighted
  materialized hashes and shared non-overlapping CIBS/LiftPack staging;
- one-through-eight-channel residual-only Main-0 transport with aligned
  per-channel RSL2 partitions, bounded interleaved whole decode, and
  allocation-free push and transactional pull playback;
- an optional source-bound `RSI1` seek sidecar whose rejection never affects
  sequential Truth decode;
- an explicit shared-Core Python bridge that gates typed-stream RDO on the
  production decoder and exact cross-decoder PCM equality;
- independently authenticated `LPS1` source-context, `LPS2` independent
  transform-boundary, `LPS3` single-owner transform packets, and compact
  transport-framed `LPS4` records for bounded-memory, parallel, random-access,
  and loss-contained lapped research, including exact stateless record-pair
  decode under an authenticated sequence context and packet index;
- a bounded allocation-free native `LAF1` adaptive integer entropy candidate
  that preserves the selected lapped reconstruction while reducing complete
  three-second R-084 bytes by 5.34% to 7.67% on all three licensed clips;
- an allocation-free C++23 LAF1 encoder that preserves every published R-107
  stream byte and improves complete-Mozart encode throughput by 2.476x to
  2.571x realtime on the measured Windows x64 host;
- prospective `LPS5` independently reset adaptive records, which preserve LPS4
  loss containment and reduce complete 278.6 ms transport bytes by 3.43% to
  5.95% on the three R-084 clips;
- prospective `LPS6` packet-local bounded Rice/fixed-width value entropy with
  an exact LPS5 RDO fallback; it improved all four declared speech metrics
  inside the previous complete-byte ceiling and retained LPS5 on 13 of 16
  heterogeneous classes where the new representation was larger;
- prospective R-120 unified MAF research streams with event-driven band cells,
  cached integer vocal-tract Basis, causal source-filter order, and
  independently decoded adaptive/stochastic algebraic excitation; the first
  speech byte-checkpoint point failed Opus quality and remains rejected;
- the R-122 portable bounded MAF DSP substrate: explicit stream-resource and
  operation budgets plus allocation-free integer Basis, noise, source-filter,
  Innovation, transient, and channel-mix primitives behind the stable C ABI;
- prospective `MFT1`, the first allocation-free typed MAF execution path for
  long-lived source-filter, stochastic, transient, and mix records, with exact
  lifetime splitting and callback-partition-invariant PCM;
- acoustic change-point proposals guarded by complete-stream boundary RDO;
- a reproducible external Opus anchor with full Ogg byte accounting and tool
  provenance;
- a pinned licensed real-music corpus and deterministic PCM downmix;
- a pinned 16-class EBU SQAM/Xiph heterogeneous gate spanning speech, solo
  voice, sustained tones, noise, electronic, transient, dense, stereo, and
  film-mix material;
- 195 Python reference/security/integration tests, including native
  decoder-in-loop coverage, twelve native conformance targets, native x64/ARM64
  coverage across Linux, Windows, and macOS, an Android arm64-v8a build, and
  separate sanitized LiftPack/Main-0/RSI1/LPF1/LAF1 mutation targets.

All current MAF-P1/Opus results are deliberately labeled diagnostics, not
general codec claims. See
[MAF-P0 and MAF-P1 Executable Prototypes](docs/10_MAF_P0_IMPLEMENTATION.md)
and
[LiftPack-1 and Full-Stream Acoustic-State RDO](docs/12_LIFTPACK_AND_STATE_RDO.md).
The first portable decoder subset is documented in
[the native Golden Core README](native/README.md).

## Documentation

- [Documentation index](docs/INDEX.md)
- [Charter and North Star](docs/00_CHARTER_AND_NORTH_STAR.md)
- [MAF architecture](docs/01_MAF_ARCHITECTURE.md)
- [Encoder compiler](docs/02_ENCODER_COMPILER.md)
- [Classical-music targets](docs/03_CLASSICAL_MUSIC_TARGETS.md)
- [Risks and kill gates](docs/04_RISKS_AND_KILL_GATES.md)
- [Naming and IP](docs/05_NAMING_AND_IP.md)
- [Decision log](docs/06_DECISION_LOG.md)
- [Implementation roadmap](docs/07_IMPLEMENTATION_ROADMAP.md)
- [Research directions and codec targets](docs/08_RESEARCH_DIRECTIONS_AND_CODEC_TARGETS.md)
- [CIBS normative design](docs/09_CIBS_NORMATIVE_DESIGN.md)
- [MAF-P0/P1 executable prototypes and measured results](docs/10_MAF_P0_IMPLEMENTATION.md)
- [Implementation language and runtime](docs/11_IMPLEMENTATION_LANGUAGE.md)
- [LiftPack-1 and full-stream state RDO](docs/12_LIFTPACK_AND_STATE_RDO.md)
- [RSC1 compact deterministic section container](docs/13_RSC1_CONTAINER.md)
- [First native typed-stream music diagnostic](docs/14_MAIN0_NATIVE_MUSIC.md)
- [Continuous evidence and immediate-improvement protocol](docs/15_CONTINUOUS_EVIDENCE.md)
- [C++23 production toolchain baseline](docs/16_TOOLCHAIN_BASELINE.md)
- [Unified MAF rate-distortion frontier](docs/17_MAF_RATE_DISTORTION_FRONTIER.md)
- [R-120 unified MAF speech fast diagnostic](docs/results/R120_UNIFIED_MAF_SPEECH_FAST_2026-07-27.md)
- [C++23 migration and exact regression evidence](docs/results/CPP23_TOOLCHAIN_GATE_2026-07-27.md)
- [Android and iOS Core portability evidence](docs/results/MOBILE_CORE_GATE_2026-07-27.md)
- [Bounded MAF DSP and stream-integration evidence](docs/results/BOUNDED_MAF_DSP_2026-07-27.md)
- [Gemini semantic change-ledger and local alignment evidence](docs/results/GEMINI_SEMANTIC_ARBITER_2026-07-27.md)
- [Latest bounded-value entropy result](docs/results/BOUNDED_VALUE_ENTROPY_2026-07-27.md)
- [Corrected PVQ envelope fast gate](docs/results/PVQ_ENVELOPE_FAST_GATE_2026-07-27.md)
- [Primary sources](docs/REFERENCES.md)
- [Resonith-0 normative draft](spec/Resonith-0.md)

All unverified compression, complexity, quality, and schedule figures are
explicitly marked as **TARGET** or **HYPOTHESIS**. They are not codec claims.

Public repository:
[github.com/moshkinyevhen/resonith](https://github.com/moshkinyevhen/resonith).

## Main-0 WAV quick start

The reference CLI accepts uncompressed PCM16 WAV with one through eight
channels. Lossless mode uses `innovation_step=1`:

```sh
PYTHONPATH=reference python -m maf_p0 encode-main0 \
  input.wav output.rsc --innovation-step 1
PYTHONPATH=reference python -m maf_p0 decode-main0 \
  output.rsc decoded.wav
```

The encoder RDO selects one aligned RSL2 block size by complete aggregate RSC1
bytes. The decoder independently validates the container, channel instances,
frame counts, and common block partition before emitting PCM.

## Prospective lapped WAV listening

The fixed-integer, bounded-entropy, adaptive-density research path is
immediately testable on one-through-eight-channel PCM16 WAV:

```sh
PYTHONPATH=reference python -m maf_p0 encode-lapped \
  input.wav output.rsc --average-coefficients 64
PYTHONPATH=reference python -m maf_p0 decode-lapped \
  output.rsc decoded.wav
```

The encoder prints complete RSC1 bytes, waveform diagnostics, selected
coefficient-count range, table identity, and wall time. This path has passed
objective and native portability gates but remains prospective until blinded
listening and real-device timing pass.

The canonical filename path uses independently reset prospective LPS5 records:

```sh
PYTHONPATH=reference python -m maf_p0 encode-resonith \
  input.wav output.resonith --average-coefficients 64
PYTHONPATH=reference python -m maf_p0 decode-lapped \
  output.resonith decoded.wav
```

When `--packet-frames` is omitted, the encoder selects a transform-aligned
record duration near 256 ms. The public `.resonith` extension is stable; the
embedded LPS5 research transport remains prospective.

The native build also provides a bounded streaming decoder that writes PCM16
WAV without allocating the complete reconstruction:

```sh
resonith_decode input.resonith output.wav
```

The first physical Windows x64 callback gate has passed 26,100 observations
with zero deadline misses, 9.81x–12.33x realtime decode, and 29.5–37.8 KB
caller workspace. This is desktop feasibility only; Android thermal and energy
evidence remains open.

The real-music experiment also emits a self-contained offline blind-listening
application. It uses one Web Audio clock for the named reference, hidden
reference, Resonith, Opus, and low-pass anchor, verifies every WAV hash, and
exports manifest-bound JSON without uploading data. From the generated
`listening` directory:

```sh
python -m http.server 8765
```

Open `http://127.0.0.1:8765/`, export all blinded results, and only then use
`experiments/listening_results.py` with the separate answer key. The harness
does not turn an informal or undersized panel into a MUSHRA claim.

## Continuous public evidence

Every material Resonith milestone must be tested on the pinned LibriSpeech
speech excerpt, Emotional piano reference, and complete Mozart
*Die Zauberflöte* overture. The released Resonith file is compared with both
the preceding Resonith version and a current official Opus encode matched by
complete container bytes. Reports use PCM from the real decoders and publish
complete sizes, hashes, timings, waveform and multi-resolution spectral
diagnostics, speech intelligibility, and any regressions.

An improvement is not released until its semantic version and English
[`CHANGELOG.md`](CHANGELOG.md) entry link to reproducible evidence. The exact
protocol is in
[Continuous Evidence and Release Protocol](docs/15_CONTINUOUS_EVIDENCE.md).

Every coherent synchronized development change is also recoverable before it
is pushed: its English changelog entry, R-number, validation evidence, affected
stable step, and all-63-step durable checkpoint are committed together. The
commit SHA identifies experimental checkpoints. `VERSION` changes only when a
generation is admitted or released, so a GitHub push never masquerades as a
product release.

An explicit shared Golden Core can replace Python forward analysis without
changing the selected bitstream:

```sh
PYTHONPATH=reference python -m maf_p0 encode-lapped \
  input.wav output.rsc --average-coefficients 64 \
  --native-core build/native/libresonith_core_shared.so
```

For bounded packet research, choose a logical packet size aligned to the
half-window:

```sh
PYTHONPATH=reference python -m maf_p0 encode-lapped \
  input.wav output.lps --average-coefficients 64 \
  --packet-frames 44032
PYTHONPATH=reference python -m maf_p0 decode-lapped \
  output.lps decoded.wav
```

## Implementation stack

- portable dependency-free C++23 bit-exact Golden Core;
- stable C ABI for applications, bindings, and hardware test benches;
- Rust for secure parsing, streaming, scheduling, and player services;
- Python/PyTorch as a thin research control plane for hypotheses, RDO policy,
  metrics, and CIBS training, never as a shipped runtime dependency;
- C++23/SIMD and optional CUDA kernels for scaling transform, search,
  reconstruction, synthesis, and Studio/Foundry encoding work;
- scalar, x86 SIMD, ARM NEON/SVE2, WASM SIMD, and vendor-DSP decode paths.
- mandatory CMake compile gates for Windows x86-64, Android ARM64/x86-64, and
  iOS device ARM64/simulator x86-64.

See
[Implementation Language and Runtime Architecture](docs/11_IMPLEMENTATION_LANGUAGE.md)
for the portability and real-time contract.

The permanent heterogeneous corpus is defined by
[R-111 acquisition and preparation evidence](docs/results/EXTENDED_AUDIO_CORPUS_2026-07-27.md).

## GitHub synchronization

A repository-local `post-commit` hook automatically pushes every explicitly
created local commit to `origin`. It never stages files and never creates
commits.

Enable the hook after a fresh clone:

```powershell
.\scripts\enable-auto-sync.ps1
```

Run an explicit `fetch + pull --rebase + push`:

```powershell
.\scripts\sync.ps1
```
