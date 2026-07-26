# First Native Typed-Stream Music Diagnostic

Status: **MEASURED-DIAGNOSTIC — NOT A CODEC VICTORY CLAIM**
Date: 2026-07-26

## 1. What changed

This is the first real-music experiment in which every Resonith candidate was
a complete typed RSC1 stream and had to pass the shared C++20 Golden Core
before RDO. The earlier MAF-P1 report used the generic Python `MAF0` container;
this run uses only `CONF`, `ATOM`, `BRAW`, and `RSL1`.

The source corpus, licenses, URLs, byte counts, and SHA-256 values remain pinned
by [`../experiments/real_music_corpus.json`](../experiments/real_music_corpus.json).
Each clip is a deterministic one-second mono crop at 44.1 kHz. Resonith uses
Innovation step 64, so maximum waveform error is bounded to 32. RDO competes
constant and continuous phase laws at four gain-event granularities.

GitHub Actions run:
[30198613411](https://github.com/moshkinyevhen/resonith/actions/runs/30198613411).
The downloaded raw report SHA-256 is:

```text
371154c136a254e2ad1cce61346a6c91529bbdcef66c99b50c95b0f3211502f4
```

## 2. Measured result

| Clip | Resonith q64 | SNR | Opus 48k actual | SNR | Opus 96k actual | SNR |
|---|---:|---:|---:|---:|---:|---:|
| Corelli realization | 97.22 kbit/s | 24.09 dB | 58.60 kbit/s | 19.31 dB | 117.96 kbit/s | 26.03 dB |
| Recorded piano | 113.34 kbit/s | 47.14 dB | 62.18 kbit/s | 25.81 dB | 118.46 kbit/s | 29.04 dB |
| Recorded drums | 119.59 kbit/s | 40.10 dB | 47.56 kbit/s | 21.92 dB | 99.38 kbit/s | 22.19 dB |

All byte rates include the complete RSC1 or Ogg file. The Opus runner in this
job is the Ubuntu package selected by the workflow; its exact executable
versions and hashes are retained in the raw artifact.

These rows are not perceptually matched. Waveform SNR strongly favors a codec
that preserves objective samples and does not predict listener preference.
The only defensible conclusion is that typed Main-0 is now measurable end to
end and lies in a useful diagnostic range; it does not yet prove superiority
over Opus.

## 3. Complexity evidence

| Clip | Eight-candidate Python encode | Native decode | Host workspace |
|---|---:|---:|---:|
| Corelli realization | 1.689 s | 1.393 ms | 546,220 bytes |
| Recorded piano | 2.190 s | 1.517 ms | 546,220 bytes |
| Recorded drums | 1.801 s | 1.572 ms | 546,220 bytes |

Native timing includes stream inspection, section integrity checks, binding
allocation, and whole one-second decode. It is already hundreds of times
faster than real time on the GitHub runner. The unoptimized Python encoder
evaluates eight complete candidates in roughly 1.7–2.2 times clip duration;
this is an encouraging consumer-encoder baseline, not a Foundry result.

## 4. Architectural signal

Every clip selected `constant-gain-4096`. The winning constant law used only
three endpoint knots, while the continuous candidate used twelve. The
continuous law changed SNR by very little and cost 53–200 extra bytes at the
same gain granularity.

This is useful negative evidence. A global continuous pitch track applied to
an entire polyphonic mix is not the missing revolution. Continuous phase
belongs on isolated long-lived sources; broad mixtures next need multiple
state-local Basis/Atom records and later simultaneous source Atoms. RDO must
remain able to select the constant law.

## 5. Listening artifact

The workflow artifact contains:

- source, Resonith, Opus 48k, and Opus 96k decoded WAVs;
- an opaque `A.wav` through `D.wav` trial directory per clip;
- `manifest.json` without codec identities;
- a separate `answer-key.json`.

The locally downloaded set is under
`artifacts/main0_native_music_ci_eb11b3d/listening`. Listen before opening the
answer key. This is an informal blind set; randomized presentation, trained
listeners, anchors, statistical analysis, and a proper MUSHRA UI remain open.

## 6. State-partition kill gate

State-local multi-Basis/multi-Atom partitioning was then implemented in typed
RSC1 and verified through the same native decoder. Both one-second and
long-form runs kept the mandatory one-state fallback on every clip.

Long-form closest competitors:

| Clip | Duration | One state | Closest multi-state | Extra bytes |
|---|---:|---:|---:|---:|
| Corelli realization | 8.00 s | 86,711 | 87,460, adaptive 2-state | +749 |
| Recorded piano | 8.00 s | 107,430 | 108,214, adaptive 2-state | +784 |
| Recorded drums | 3.72 s | 42,801 | 43,495, fixed 2-state | +694 |

Run:
[30199317539](https://github.com/moshkinyevhen/resonith/actions/runs/30199317539).
Raw report SHA-256:

```text
403f1c48141ed730e66196bc9004f97a7109bc11c9b0408dd0feb192329dea4b
```

This gate failed. Sequential states remain a valid bounded syntax and the
native decoder correctly reuses maximum per-state workspace, but the encoder
must not select them on this corpus. The failure also survived Basis
amortization over eight seconds, so denser boundaries are not justified.

## 7. Next engineering gate

The next experiment is an encoder-side additive Atom oracle. It tests
simultaneous long-lived causes by matching pursuit, wide integer mixing, one
final LiftPack Innovation, and complete prospective RSC1 byte accounting.
Normative overlap/mixer syntax is added only if an extra Atom wins on at least
two declared clips.

## 8. Additive raw-Basis kill gate

The R-038 oracle searched autocorrelation fundamentals and subharmonics,
shortlisted candidates by objective residual energy, and ranked the survivors
by complete prospective RSC1 bytes. A two-period synthetic mixture selected
two Atoms and reduced 6,572 bytes to 5,198 bytes, proving that the search can
recover useful concurrent periodic causes.

The licensed one-second clips all selected one Atom:

| Clip | One Atom | Two Atoms | Four Atoms | Best residual change |
|---|---:|---:|---:|---:|
| Corelli realization | 12,042 | 12,857 | 14,340 | -150 bytes |
| Recorded piano | 14,167 | 14,960 | 16,510 | -142 bytes |
| Recorded drums | 14,964 | 15,834 | 17,504 | +92 bytes |

GitHub Actions run:
[30199790029](https://github.com/moshkinyevhen/resonith/actions/runs/30199790029).
The downloaded raw report SHA-256 is:

```text
7c6321d4b7265adfd9a62a5b8e1565a2ecd207393c288a3b916cf55927abd7de
```

This kill gate failed zero of three. Each extra full-lifetime periodic Atom
paid for a new 520-byte `BRAW`, an `ATOM` payload, and two directory records,
while barely changing LiftPack. Main-0 therefore does not gain overlapping
raw-Basis syntax from this experiment.

R-039 tests the narrower remaining explanation: useful tonal structure may
exist, but its representation must be an analytic or cached decoder Basis and
many records must share one directory entry. That experiment remains
encoder-side until its own complete-byte gate passes.

## 9. Analytic oscillator and zero-Atom result

R-039 replaced each 520-byte raw Basis with one verified fixed sine ROM and
batched all prospective oscillator records into one `HBNK` section. The
complete-byte result was:

| Clip | Raw-Basis anchor | Zero Atom | Selected analytic | Result |
|---|---:|---:|---:|---|
| Corelli realization | 12,042 | 11,402 | 11,402, 0 Atoms | oscillator rejected |
| Recorded piano | 14,167 | 13,539 | 13,535, 1 Atom | -4 bytes |
| Recorded drums | 14,964 | 14,207 | 14,207, 0 Atoms | oscillator rejected |

Run:
[30200069831](https://github.com/moshkinyevhen/resonith/actions/runs/30200069831).
Raw report SHA-256:

```text
6919c598e24cb1937617859aea6e75aee395c103ac4b58243290f17ed3d29fac
```

The analytic-bank gate failed one of three and no opcode is promoted. The
simpler result is stronger: an identically zero predictor reduced the complete
stream by 4.4% to 5.3% against the mandatory raw-Basis anchor on every clip.
R-040 therefore makes `CONF` plus `RSL1` with no `ATOM`/`BRAW` a normative
Main-0 form and a mandatory encoder candidate.

## 10. Native zero-Atom and LiftPack block-size RDO

The R-040 decoder path passed GCC, Clang, MSVC, all native conformance targets,
and the Python-to-C++ decoder-in-loop tests in
[run 30200277390](https://github.com/moshkinyevhen/resonith/actions/runs/30200277390).
It reports zero model workspace and reconstructs the q64 Truth stream through
the same native acceptance boundary.

R-041 then evaluated the existing LiftPack-1 block sizes per complete typed
candidate. It selected 32,768 samples for Corelli and piano, but 2,048 for
drums:

| Clip | Selected stream | Bitrate | Reduction vs one-state |
|---|---:|---:|---:|
| Corelli realization | 10,930 bytes | 87.44 kbit/s | 7.45% |
| Recorded piano | 12,740 bytes | 101.92 kbit/s | 6.07% |
| Recorded drums | 14,011 bytes | 112.09 kbit/s | 5.64% |

Run:
[30200401912](https://github.com/moshkinyevhen/resonith/actions/runs/30200401912).
Raw report SHA-256:

```text
85f2d8d72713d434a987e994186fb8b3a0dcbc275a4aaed0f756363578abb7af
```

Every clip selected `residual-only`; the periodic and sequential-state
candidates remain legal but lost RDO. Block-size RDO changes no decoder syntax
and is now the default unrestricted Main-0 encoder search.

## 11. Bounded LPC research gate

R-042 added one prospective integer LPC transform to the residual competition.
It retained the existing LiftPack transforms and entropy coders, fitted LPC
coefficients only in the encoder, quantized them to Q12, and verified exact
prospective decoding before counting complete RSC1 bytes. The gate required a
win beyond the already optimized RSL1 block-size anchor on at least two clips.

| Clip | RSL1 anchor | LPC candidate | Reduction | Selected block |
|---|---:|---:|---:|---:|
| Corelli realization | 10,930 bytes | 10,233 bytes | 6.38% | 16,384 |
| Recorded piano | 12,740 bytes | 11,953 bytes | 6.18% | 32,768 |
| Recorded drums | 14,011 bytes | 12,743 bytes | 9.05% | 4,096 |

Run:
[30200626416](https://github.com/moshkinyevhen/resonith/actions/runs/30200626416).
Raw report SHA-256:

```text
aa28153b943a530697df821f87e1bce05854c65416a49fb36ed8f95e2f49127d
```

The gate passed three of three. Order 16 was never selected in a winning
stream; selected blocks used orders 4, 8, or 12. This is evidence for the
bounded predictor, not for a larger maximum order. R-043 therefore promotes
the exact tested syntax as `LiftPack-2`/`RSL2`; it does not add a second
entropy coder or an open-ended predictor.

Canonical compact evidence:
[`../experiments/results/lpc_liftpack_oracle_2026-07-26_summary.json`](../experiments/results/lpc_liftpack_oracle_2026-07-26_summary.json).

R-043 then passed the independent Python/native bridge, the standalone LPC
rounding vector, and all native conformance targets on GCC, Clang, and MSVC:
[run 30201013628](https://github.com/moshkinyevhen/resonith/actions/runs/30201013628).
The full licensed production-decoder benchmark independently selected RSL2 on
all three clips:
[run 30201094754](https://github.com/moshkinyevhen/resonith/actions/runs/30201094754).
Its raw report SHA-256 is:

```text
4ca6a8f93743ea7725d5ba152f837f79c75af69a18324c599c7b8ab6c1edcb8e
```

The selected complete rates were 81.86 kbit/s for Corelli, 95.62 kbit/s for
piano, and 101.94 kbit/s for drums. Native whole-stream decode remained about
1.35–1.60 ms per one-second clip on the GitHub runner. This verifies the
implementation and earlier byte result; it remains a mono q64 waveform
diagnostic, not a matched-MUSHRA comparison with Opus.

Canonical compact native evidence:
[`../experiments/results/main0_lpc_native_2026-07-26_summary.json`](../experiments/results/main0_lpc_native_2026-07-26_summary.json).
