# R-142/R-145 Motif and Partial-Spectrum Orbit Diagnostic

Date: 2026-07-27  
Status: **LOSSLESS ARCHITECTURE DIAGNOSTIC; NOT R-118 OR AN OPUS CLAIM**

## 1. Question

Can Resonith store an objective waveform or partial-spectrum sequence once,
place mathematically related instances, and preserve exact PCM through a
separate Truth correction without recognizing speech, instruments, notes, or
natural-sound labels?

The two tested representations were:

1. R-142 whole-waveform `BASIS_INSTANCE` with exact timing, crop, and signed
   Q1.15 gain in the native C++23 MFT1 decoder;
2. R-145 reversible integer multiband analysis with an independent dictionary
   per coefficient band, signed-gain instances, and exact RSL2 correction.

All byte totals below include the tested representation and exact correction.
Common outer-container bytes are excluded symmetrically. Every selected and
rejected candidate reconstructed the source PCM exactly.

## 2. Native executable subset

`BASIS_INSTANCE` is now record type 7 in prospective MFT1. Its 24-byte payload
resolves one immutable Basis, emitter, absolute output start, source crop,
sample count, and signed gain. The native renderer adds it before the active
mix and remains invariant under callback partitioning.

The C++ and Python tests cover:

- independent pack/parse and native decode parity;
- two exact placements of one immutable waveform;
- irregular versus regular callback partitioning;
- unresolved Basis rejection;
- operation and memory preflight;
- exact lossless Truth composition;
- a transformed-loop complete-byte win.

## 3. Whole-waveform control

The strict first control used a fixed-lattice whole-waveform proposal hash and
gain-only instances:

| Signal | Gain orbit + Truth | Independent Truth | Selected |
|---|---:|---:|---|
| Synthetic transformed loop | 143,022 | 157,485 | Gain orbit |
| EBU sustained sine | 116,840 | 116,744 | Truth fallback |
| EBU electronic tune | 213,054 | 212,958 | Truth fallback |
| EBU female speech | 492,735 | 492,639 | Truth fallback |
| EBU claves | 175,606 | 175,510 | Truth fallback |
| EBU pink noise | 462,918 | 462,822 | Truth fallback |
| EBU dense orchestra | 145,756 | 145,660 | Truth fallback |

The synthetic saving was 9.18% under the best exact Truth block selection.
All six real controls found no admitted group and paid the 96-byte empty-MFT1
overhead, which RDO rejected. This falsifies fixed-lattice whole-waveform
gain-only matching as a sufficient real-audio mechanism; it does not falsify
partial-band or transformed reuse.

## 4. Partial-spectrum constructive test

The synthetic signal was created from four exact reversible bands. Only the
finest detail band repeated; the other three bands contained independent
content. No sound label or source identity entered matching.

| Representation | Bytes | Delta vs independent Truth |
|---|---:|---:|
| Independent exact Truth | 154,512 | baseline |
| Reversible multiband Truth, no dictionary | 133,451 | -13.63% |
| Partial-spectrum dictionary + exact Truth | **89,522** | **-42.06%** |

The winning band used one 64-coefficient Basis and 1,024 placements to cover
65,536 coefficients. Dictionary metadata was 119 bytes, fixed instance
records were 12,288 bytes, and correction for that band was 8,355 bytes. The
three unrelated bands remained exact Truth.

This is a constructive proof of the requested property: a recurring spectral
part can be paid once even when the complete waveform never repeats.

## 5. First real-speech result

| Representation | Bytes | Selected |
|---|---:|---|
| Independent exact Truth | **518,431** | Yes |
| Reversible multiband Truth, no dictionary | 635,409 | No |
| Partial-spectrum dictionary + exact Truth | 635,723 | No |

The first Haar-like grid found only two Bases and four placements covering 256
coefficients. Its band split itself was less efficient than direct RSL2.
Therefore the real speech stream retained independent Truth exactly.

This negative result identifies the missing mechanisms rather than changing
the invariant:

1. phase/alignment-, pitch/time-, and envelope-normalized matching;
2. a frequency tiling aligned to audible partials rather than the first simple
   reversible Haar grid;
3. content-defined time boundaries instead of one fixed lattice;
4. batched delta-coded placements instead of one fixed 12-byte record;
5. joint RDO across transformed Basis, stochastic law, source-filter law,
   transient law, and independent Truth.

## 6. Interpretation

For a repeated region of `L` PCM16 samples placed `K` times, with `P` placement
bytes and negligible correction, the raw-domain ideal saving is approximately:

```text
1 - 1/K - P/(2L)
```

The limit approaches 100% only when repetitions are numerous, placement is
compact, and correction is small. Against Opus or optimized Resonith Truth the
available saving is much lower because those codecs already remove local
redundancy. No percentage against Opus is inferred from this lossless
diagnostic.

### 6.1 Phase and cross-channel executable extension

R-146/R-147 extend the same 24-byte MFT1 instance without an additional record:

- `CIRCULAR` plus Basis offset represents exact integer sample phase/alignment;
- signed gain represents polarity and exact counterphase;
- `LINEAR_GAIN` uses the former reserved final word as an exact end gain and
  interpolates one fade/damping trajectory;
- emitter identity and the persistent mix route one global Basis into different
  output channels.

A generated stereo signal placed one waveform under changing circular phases,
constant gains on the left, and linear decays on the right. The exact baseline
competed independent, mid/side, left/side, and right/side channel lifting:

| Representation | Complete RSC1 bytes | Exact |
|---|---:|---|
| Best reversible stereo Truth (`mid_side`) | 74,568 | Yes |
| Shared cross-channel Basis + Truth | **17,513** | Yes |

The measured lossless saving was **76.51%**. One Basis served 256 instances;
128 carried linear gain, and 32,768 samples were covered in each channel.
MFT1 occupied 8,824 bytes and exact per-channel Truth occupied 8,401 bytes.

This is a constructive transform test, not a real-audio or Opus claim. A
pinned native-stereo gate is required to measure whether phase/envelope
relations survive a real mix after the baseline has already used channel
lifting.

The next evidence gate replaces the first whole-waveform hash with
content-defined time-frequency cells and bounded affine alignment/pitch/time
transforms. It must still publish forced losses, exact fallbacks, runtime, and
the complete R-118 union before any general claim.

## 7. Reproduction

Implementations:

- `reference/maf_p0/motif_orbit.py`;
- `reference/maf_p0/partial_spectrum_orbit.py`;
- `experiments/motif_orbit_gate.py`;
- `experiments/partial_spectrum_orbit_gate.py`.

Local machine reports:

- `G:\Resonith\artifacts\r142-motif-orbit-real-2026-07-27\report.json`;
- `G:\Resonith\artifacts\r145-partial-spectrum-smoke\report.json`;
- `G:\Resonith\artifacts\r147-cross-channel-synthetic\report.json`.
