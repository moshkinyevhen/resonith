# R-111 Extended Heterogeneous Audio Corpus

Status: **ACQUIRED AND PREPARED; CODEC GATE PENDING**

Date: 2026-07-27

## Purpose

The pinned speech, Emotional piano, and complete Mozart references remain the
mandatory full-file regression floor. They are not broad enough to decide
whether an architecture generalizes. R-111 adds controlled and mixed-content
material that exercises the major acoustic classes used by MAF.

No compression improvement is claimed by this report. It records acquisition,
identity, preparation, and coverage before results are measured.

## Acquired sources

| Collection | Local source size | Identity | Use policy |
|---|---:|---|---|
| EBU Tech 3253 SQAM lossless FLAC package | 175,545,976 bytes | SHA-256 `7d6fcd0fc42354637291792534b61bf129612f221f8efef97b62e8942a8686aa` | Local non-commercial codec R&D under the EBU download terms |
| Xiph Sintel trailer stereo FLAC | 4,692,805 bytes | SHA-256 `171d95acdb59882b4b8fb39cc1463920a859a78d3772bca532059c9ee02d48a6` | Local codec R&D; no repository redistribution pending per-title license record |
| Xiph Elephants Dream stereo FLAC | 59,166,432 bytes | SHA-256 `fc25f3658365529c599097954fa5342c3e20333cf55648e4cbbcaea95b360f18` | Local codec R&D; no repository redistribution pending per-title license record |

The EBU package is the official 70-file lossless SQAM collection. The
repository selects controlled diagnostic classes from that package; it does
not republish source audio.

## Bounded architecture matrix

Each row uses a pinned 12-second PCM16 crop. Starts are explicit in
[`extended_audio_corpus.json`](../../experiments/extended_audio_corpus.json);
there is no automatic best-window selection.

| Clip | Primary stress |
|---|---|
| EBU 1 kHz level sequence | persistent deterministic tone and gain tracking |
| EBU band-limited pink noise | stochastic field and stereo |
| EBU vibrato gong | resonance, modulation, and long decay |
| EBU electronic tune | synthetic tonal material |
| EBU violin | solo harmonic instrument and stereo image |
| EBU claves | sparse attacks and pre-echo |
| EBU side drum | attacks plus noise-like excitation |
| EBU cymbal | stochastic transient and long decay |
| EBU grand piano | polyphonic attack/decay |
| EBU soprano | solo voice, pitch, and formants |
| EBU female English speech | female speech intelligibility |
| EBU male English speech | male speech intelligibility |
| EBU orchestra | dense classical mixture |
| EBU popular-music mix | dense voice-plus-music mixture |
| Xiph Sintel trailer | dialogue, score, effects, and ambience together |
| Xiph Elephants Dream | long-form dialogue, score, effects, and ambience |

The clean-channel matrix is supplemented by deterministic isolated,
two-packet-burst, and periodic-five-percent loss patterns on speech, dense
music, and film mixes.

## Deterministic preparation

[`prepare_extended_audio_corpus.py`](../../experiments/prepare_extended_audio_corpus.py)
downloads missing immutable sources, verifies byte counts and SHA-256 before
use, safely extracts selected EBU members, decodes lossless FLAC, applies only
the declared crop and channel policy, and writes PCM16 WAV without resampling
or loudness normalization.

Prepared identities are pinned in
[`extended_audio_corpus_prepared_2026-07-27.json`](../../experiments/results/extended_audio_corpus_prepared_2026-07-27.json).
The prepared set contains 16 clips and 192 seconds of diagnostic audio in
addition to the three complete regression references.

Local files on the project workstation:

```text
G:\Resonith\artifacts\corpus\ebu-sqam
G:\Resonith\artifacts\corpus\xiph
G:\Resonith\artifacts\corpus\prepared-r111
```

These paths are local evidence locations, not portable specification paths.

## Promotion rule

Every material architecture change:

1. runs the three complete R-102 references;
2. runs all 16 bounded R-111 clips;
3. reports wins and regressions per acoustic class;
4. expands any material bounded win or loss to the complete source item;
5. runs packet-loss profiles where the syntax is streamable;
6. publishes actual decoder output and complete container bytes.

The matrix prevents a speech-only, tonal-only, or SNR-only optimization from
being presented as a universal codec improvement.
