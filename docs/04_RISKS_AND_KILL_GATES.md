# Риски и kill-gates Resonith

Статус: критерии — **ACCEPTED**; пороги — **TARGET**.

## 1. Главные способы провала

1. Basis metadata съедает экономию waveform.
2. Реальный тембр меняется быстрее, чем предполагает persistent basis.
3. Source separation создаёт остаток почти исходной сложности.
4. Sinusoidal tracks дают phasiness/warble.
5. Stochastic predictor меняет узнаваемую фактуру.
6. Resonator state усложняет seek и packet-loss recovery.
7. Dense polyphony превышает bounded atom count.
8. Переключения basis слышны.
9. Decoder оказывается больше и тяжелее Opus/xHE-AAC без достаточного gain.
10. Learned Perceptual layer ошибочно принимают за objective fidelity.

## 2. Последовательность falsification

### Gate A — periodic oracle

Сравнить:

```text
universal integer lifting residual
vs
TIMBRE_BASIS + absolute PHASE_TRACK + remaining lifting residual
```

Если на isolated pitched material net rate не снижается минимум на 20% при
равной objective error, coherent hypothesis замораживается.

### Gate B — broad classical

Добавить multiple bases и Studio global tracking. Если matched-MUSHRA gain
ниже 15% на broad classical после полного overhead, не строить musical VM.

### Gate C — transient/stochastic ablation

Каждая family должна дать:

- минимум 3% broad net gain, либо
- минимум 10% на заранее определённом значимом классе,

при отсутствии statistically significant artifact penalty.

### Gate D — small decoder

Main decoder должен иметь bounded state, bounded atoms/sample и predictable
integer DSP workload. Если worst-case profile нельзя реализовать на mobile
CPU/DSP без neural accelerator, сложность режется до следующего gate.

### Gate E — revolution

Продолжать стандартный proposal как frontier codec только при:

- не менее 35% bitrate reduction на broad music/classical против сильнейшего
  применимого anchor при matched MUSHRA;
- конкурентном результате на speech/general audio;
- отсутствии систематического phase, timbre и transient degradation;
- independent decoder и conformance vectors.

## 3. Метрики, которые нельзя маскировать

Отчёт обязан показывать:

- долю basis/event/innovation/checkpoint/FEC bits;
- active atoms per sample P50/P95/P99/max;
- MAC/sample и state bytes;
- random access cost;
- packet loss propagation;
- algorithmic delay;
- objective и subjective quality;
- каждый anchor отдельно;
- failed clips и worst decile, не только mean.

## 4. Правило простоты

Новый mechanism не входит в Main, если он:

- требует отдельного entropy coder;
- создаёт новую несовместимую state machine;
- не компилируется в существующий acoustic ISA;
- даёт только косметический gain;
- не имеет универсального Innovation fallback;
- ухудшает deterministic random access.

Неудачную идею закрывают, а не спасают дополнительными режимами.
