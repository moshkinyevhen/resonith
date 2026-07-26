# План первой реализации MAF

Статус: порядок — **ACCEPTED**; сроки и gain — **TARGET / HYPOTHESIS**.

Цель первой ветки — не сразу реализовать все families, а получить
falsifiable codec loop, в котором каждый новый механизм доказывает собственный
net gain.

## Milestone 0 — Golden Core

Артефакты:

- canonical PCM reader/writer;
- exact rational sample timeline;
- integer lifting baseline;
- deterministic rounding/saturation library;
- bit-exact CIBS integer synthesis kernel;
- versioned CIBS model package parser и Basis hash;
- bit counter с полным overhead;
- Core checksum;
- first conformance vectors.

Критерий: encode/decode exact в Lossless и bit-identical на двух независимых
decoder paths.

## Milestone 1 — Periodic + CIBS oracle

Минимальная grammar:

```text
STREAM_CONFIG
STATE_RESET
BASIS_SET(TIMBRE)
ATOM_SET(PERIODIC)
INNOVATION
CHECKPOINT
```

Encoder:

1. находит isolated stable pitch tracks;
2. строит один integer `TIMBRE_BASIS`;
3. кодирует Basis двумя конкурирующими способами:
   `RAW/LIFTED` и `CIBS_LATENT + basis correction`;
4. оптимизирует absolute phase/amplitude law;
5. декодирует candidate;
6. кодирует оставшийся lifting residual;
7. сравнивает три полных bitstreams с lifting-only baseline.

Kill-gate: минимум 20% net gain на isolated pitched material при равной
objective error.

## Milestone 2 — Train/export CIBS and shared structure

Добавить:

- `CONTROL_BASIS`;
- CIBS analysis model, quantization-aware export и fixed model package;
- repeated timbre across multiple notes;
- excitation–resonator factorization;
- content-addressed Basis reuse;
- Studio whole-track dynamic programming.

Отдельный ablation показывает вклад каждого механизма.

## Milestone 3 — Transient and stochastic

Добавить по одному:

- short transient basis без pre-echo;
- counter-based stochastic atom;
- switching continuity tests;
- packet loss/checkpoint tests.

Каждая family проходит свой kill-gate и может быть выключена без изменения
остального bitstream.

## Milestone 4 — Broad codec

- speech/predictive candidate;
- stereo/spatial mixer;
- Realtime latency path;
- MUSHRA harness;
- Opus и xHE-AAC/USAC anchors;
- general/classical corpus;
- independent decoder.

Immersive room model и Perceptual profile начинаются только после победы Core
на broad objective/perceptual tests.

## Code architecture target

```text
reference/
  decoder-core/       bit-exact integer Core
  bitstream/          parser, entropy, validation
encoder/
  oracle/             медленный analysis-by-synthesis
  consumer/           позднее: distilled top-K router
experiments/
  cibs0/
  periodic_oracle/
  transient_ablation/
  stochastic_ablation/
tests/
  conformance/
  corruption/
  listening/
```

Первый oracle MAY быть быстрым исследовательским кодом, но normative arithmetic
с самого начала выделяется в маленький independently testable Core. Это
предотвращает ситуацию, когда красивый Python experiment невозможно сделать
bit-exact decoder-ом.
