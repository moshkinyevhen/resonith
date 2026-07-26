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

## Executable status

The repository contains:

- MAF-P0 single-Basis baseline;
- MAF-P1 immutable multi-Basis Bank with validated lifetimes and reuse;
- absolute continuous Q32 pitch/phase trajectories with random access;
- bounded reversible integer-lifting transient events;
- RAW and CIBS Basis banks plus bounded `LiftPack-1`/`LiftPack-2` objective
  residuals with exact block-local integer LPC;
- the compact deterministic `RSC1` typed section-container candidate;
- a dependency-free C++20 whole-RSC1 Golden Core behind a stable C99 ABI;
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
- acoustic change-point proposals guarded by complete-stream boundary RDO;
- a reproducible external Opus anchor with full Ogg byte accounting and tool
  provenance;
- a pinned licensed real-music corpus and deterministic PCM downmix;
- 113 pure reference/security/integration tests, eight native decoder-in-loop
  integration tests, ten native conformance targets, native x64/ARM64
  coverage across Linux, Windows, and macOS, an Android arm64-v8a build, and
  separate sanitized LiftPack/Main-0/RSI1 mutation targets.

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

## Implementation stack

- portable dependency-free C++20 bit-exact Golden Core;
- stable C ABI for applications, bindings, and hardware test benches;
- Rust for secure parsing, streaming, scheduling, and player services;
- Python/PyTorch for encoder research, RDO, and CIBS training;
- optional C++/CUDA acceleration for Studio and Foundry encoding;
- scalar, x86 SIMD, ARM NEON/SVE2, WASM SIMD, and vendor-DSP decode paths.

See
[Implementation Language and Runtime Architecture](docs/11_IMPLEMENTATION_LANGUAGE.md)
for the portability and real-time contract.

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
