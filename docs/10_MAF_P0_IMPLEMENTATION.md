# MAF-P0 and MAF-P1 Executable Prototypes

Date: 2026-07-26
Status: **IMPLEMENTED / EXPERIMENTAL RESULT**

## 1. MAF-P0 baseline

The original executable path remains available as the falsification baseline:

```text
PCM16 mono
→ one periodic Basis
→ RAW or CIBS materialization
→ constant Q32 phase increment
→ Q15 block gains
→ objective residual
→ self-checking MAF0 container
→ independent decode
```

MAF-P0 is intentionally retained. Every MAF-P1 gain must be measured against
this simpler path rather than attributed to unrelated changes.

## 2. MAF-P1 stateful path

MAF-P1 adds the four requested engineering mechanisms:

```text
immutable content-addressed Basis Bank
→ multiple Atom lifetimes
→ absolute piecewise-linear Q32 pitch/phase trajectories
→ optional bounded transient replacement
→ universal objective residual
```

Implemented invariants:

- repeated materialized Basis content is stored once and reused by several
  Atoms;
- every Atom lifetime is half-open and fully contained by its Basis lifetime;
- malformed streams in which an Atom outlives its Basis are rejected;
- each phase trajectory includes its endpoint knots and is evaluated from an
  absolute polynomial, never from the previous render block;
- arbitrary output slices match full sequential rendering bit-for-bit;
- transient events use reversible integer Haar lifting in bounded,
  non-overlapping windows;
- transient reconstruction is identically zero outside declared windows, so
  the path cannot create pre-echo before its support;
- `transient=auto` compares coefficient, event, and remaining-residual cost and
  rejects an unprofitable transient representation;
- `residual_step=1` reconstructs exact PCM for RAW and CIBS Basis banks.

The experimental container is self-describing and not the final binary syntax.
The Python implementation is an oracle; the portable C++20 Golden Core remains
the production target.

## 3. Real Opus anchor

`reference/maf_p0/opus_anchor.py` executes real external `opusenc` and
`opusdec`, then reports:

- complete Ogg Opus bytes, including headers and container overhead;
- requested and effective bitrate;
- decoded PCM quality and exact sample count;
- deterministic normalized Ogg hash that zeroes the random logical-stream
  serial and dependent page CRC fields;
- encoder and decoder version strings;
- SHA-256 of both executables;
- mode, application, frame duration, sample rate, and sample count.

The checked-in installer downloads the official Xiph/Mozilla Windows package:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\install-opus-anchor.ps1
$env:RESONITH_OPUS_TOOLS = `
  "$env:USERPROFILE\.local\tools\resonith-opus-tools-0.2-opus-1.3"
```

The pinned archive SHA-256 is:

```text
a1ae3c806adee9b008348166251f938dd7774ba6987d392187202b11d1152e90
```

This package contains opus-tools 0.2 linked with libopus 1.3. It is a real,
reproducible reference anchor, but it is not the newest libopus 1.6.1 anchor.
The version is therefore printed in every report and no result is described as
a comparison with current best Opus until the 1.6.1 runner is added.

## 4. Reproducible MAF-P1/Opus experiment

Command:

```powershell
$env:PYTHONPATH = "$PWD\reference"
python experiments\maf_p1_benchmark.py `
  --opus-tools $env:RESONITH_OPUS_TOOLS `
  --output experiments\results\maf_p1_opus_2026-07-26.json
```

Corpus: deterministic 3-second, 48 kHz mono synthetic signal containing three
harmonic segments, continuous pitch changes, amplitude modulation, and four
detected attacks.

### MAF ablation

| Configuration | Effective kbit/s | SNR | Max error |
|---|---:|---:|---:|
| P0 single Basis, residual q16 | 455.55 | 60.96 dB | 8 |
| P1 multi-Basis, q16, transient off | 349.16 | 60.99 dB | 8 |
| P1 multi-Basis, q16, transient forced | 351.67 | 61.00 dB | 8 |
| P1 multi-Basis, q16, transient auto | 349.16 | 60.99 dB | 8 |
| P1 multi-Basis, q64, transient auto | 161.33 | 48.97 dB | 32 |
| P1 multi-Basis, q256, transient auto | 74.33 | 36.93 dB | 128 |
| P1 multi-Basis, q1024, transient auto | 37.18 | 24.83 dB | 512 |

At equal q16, P1 reduced bytes by 23.35% relative to P0 on this declared
synthetic class. Forced transient coding cost 0.72% more bytes; `auto`
correctly rejected it. The negative transient result is retained.

### Official Opus anchor

| Requested mode | Effective kbit/s | SNR | Max error |
|---|---:|---:|---:|
| 32k VBR music | 59.42 | 26.77 dB | 14,394 |
| 48k VBR music | 86.80 | 27.78 dB | 13,965 |
| 64k VBR music | 114.25 | 28.27 dB | 13,866 |
| 96k VBR music | 169.47 | 29.25 dB | 13,944 |

On this favorable synthetic signal, P1 q256 has a lower effective bitrate and
higher waveform SNR than the measured 48k Opus run. This is not a perceptual
codec victory: SNR does not predict MUSHRA, the corpus is synthetic and highly
structured, Opus is optimized for perceptual quality, and the anchor version
is libopus 1.3. The result only proves that the new state mechanisms are
executable and can improve the declared class.

Canonical raw report:
[`../experiments/results/maf_p1_opus_2026-07-26.json`](../experiments/results/maf_p1_opus_2026-07-26.json).

## 5. Test coverage

The reference suite now covers:

- P0 RAW and CIBS lossless/lossy paths;
- CIBS atomic materialization and hash rejection;
- multi-Basis lifetime validation and content reuse;
- RAW and CIBS MAF-P1 Basis banks;
- absolute phase-law slice and block-size independence;
- reversible transient lifting, non-overlap, and zero outside support;
- corruption rejection;
- a real Opus encode/decode integration test when the tool is configured.

Run:

```powershell
$env:PYTHONPATH = "$PWD\reference"
python -m unittest discover -s tests -v
```

## 6. Next falsification gates

1. Replace the zlib residual placeholder with the general integer-lifting and
   entropy baseline.
2. Add automatic change-point segmentation instead of fixed Atom intervals.
3. Fit phase trajectories from real vibrato, glissando, and polyphonic
   recordings.
4. Make transient RDO win on a predeclared attack-heavy corpus without
   introducing pre-echo.
5. Add stereo and multi-Atom overlap.
6. Build or package current libopus 1.6.1 and xHE-AAC anchors.
7. Run per-clip objective and MUSHRA-ready tests on licensed real music,
   speech, ambience, and hostile noise.

No broad compression claim is accepted before these gates and independent
listening tests.
