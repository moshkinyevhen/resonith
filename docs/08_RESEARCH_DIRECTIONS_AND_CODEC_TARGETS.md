# Оставшиеся направления и прогноз против audio anchors

Дата: 2026-07-26  
Статус всех процентов: **HYPOTHESIS / TARGET**, не измеренный результат.

## 1. Как читать проценты

\[
Saving=\frac{R_{\mathrm{anchor}}-R_{\mathrm{MAF}}}
{R_{\mathrm{anchor}}}.
\]

Сравнение допустимо только при:

- одинаковом исходнике и channel layout;
- matched MUSHRA/ABX quality;
- одинаковой algorithmic latency;
- одинаковых packet-loss, random-access и checkpoint constraints;
- полном учёте basis, model, macro, index, FEC и startup bits;
- отдельном результате против каждого anchor.

Диапазоны ниже — paper forecast архитектуры. Они нужны для выбора
экспериментов и не являются заявлением о достигнутом качестве.

## 2. Cached learned Basis synthesis — **ACCEPTED как CIBS**

### Механизм

Вместо прямой передачи всех samples `TIMBRE_BASIS` encoder передаёт:

```text
quantized latent
+ optional small adapter
+ exact/quantized basis correction
```

Один fixed versioned integer synthesizer запускается только на `BASIS_SET`,
строит immutable basis и кэширует её. Hot sample loop остаётся table lookup,
filter и mix.

### Потенциальный выигрыш

| Сценарий | Дополнительная экономия поверх MAF Core |
|---|---:|
| Broad general audio | 2–8% |
| Длинный solo/chamber, устойчивый источник | 8–18% |
| Повторяющиеся тембры/electronic stems | 5–15% |
| Короткие clips | 0–3% |
| Шум, applause, dense stochastic mix | 0–2%; возможен проигрыш |

Это не экономия всего waveform. Механизм сжимает только долю потока,
занятую Basis. Когда basis уже хорошо амортизирована на длинном track, эффект
на total bitrate быстро уменьшается.

### Недостатки

- фиксированный synthesis model стареет вместе со стандартом;
- требуется bit-exact integer inference и conformance на всех устройствах;
- startup latency, RAM и silicon area;
- out-of-distribution тембр возвращает большую basis correction;
- weights и adapters обязательно входят в bitrate/IP analysis;
- новый model version дробит decoder ecosystem.

### Решение

Решением R-014 механизм включён в Main-0 под именем
**CIBS — Cached Integer Basis Synthesis**. Он является coding mode для
`BASIS_SET`, а не neural rendering каждого sample. Процентные gates теперь
определяют не наличие syntax, а принятие конкретной CIBS model версии.

## 3. Motif macros / Acoustic Programs

### Механизм

Macro хранит не готовый waveform, а recipe повторного создания уже
существующих atoms:

```text
PROGRAM_INSTANCE(
    program_ref,
    start_time,
    time_scale,
    pitch_scale,
    gain,
    bounded_overrides
)
```

Ostinato, drum pattern, accompaniment, chorus или game cue передаются один
раз. Decoder либо parser детерминированно разворачивает macro в обычные
`ATOM_SET/END`; новых DSP-операций не появляется.

### Потенциальный выигрыш

| Сценарий | Дополнительная экономия поверх MAF Core |
|---|---:|
| Broad music | 1–5% |
| Классика с повторяющимися motifs | 2–8% |
| Pop/electronic/loop-based | 5–20% |
| Game stems, library cues, почти symbolic production | 15–35% |
| Речь, ambience, crowd/noise | около 0% |

MAF уже переиспользует timbre и Control Basis, поэтому macro экономит только
оставшиеся group events, coefficients и repeated innovation patterns. Проценты
нельзя прибавлять к выигрышу Basis synthesis.

### Недостатки

- живое исполнение почти никогда не повторяется sample-exact;
- microtiming, articulation и mix variation требуют overrides/Innovation;
- macro усложняет seek, editing, packet recovery и dependency graph;
- неограниченный recipe language превращается в musical VM;
- ошибки program lifetime способны повредить длинный интервал;
- на broad audio служебные IDs могут стоить больше сэкономленных events.

### Решение

Не запрещать, но держать вне Main-0. Допустим только bounded declarative macro,
который разворачивается в существующие atoms. Никаких циклов, ветвлений и
исполняемого score language.

## 4. Generative Detail

### Механизм

Низкобитрейтная conditioning track управляет neural vocoder/generator,
восстанавливающим:

- breath/noise и ambience;
- high-frequency texture;
- reverb microdetail;
- speech excitation;
- часть музыкального timbre.

### Потенциальный выигрыш

| Сценарий | Дополнительная perceptual-экономия |
|---|---:|
| Speech при экстремально низком bitrate | 40–80% |
| Ambience/noise/foley | 30–70% |
| General music | 20–45% |
| Dense music с важной timbre identity | 10–35% |
| Objective/lossless reconstruction | 0% допустимого выигрыша |

Здесь `matched quality` означает субъективную похожесть/полезность, а не ту же
waveform truth. Современные neural papers показывают, что очень низкие rates
возможны, но используют иные модели, corpora и quality contracts; их нельзя
непосредственно считать победой над transparent waveform codecs.

### Недостатки

- возможны hallucination и изменение голоса/инструмента;
- неизвестный язык, жанр, тембр или шум могут разрушить качество;
- тяжёлый decoder, model storage, energy и startup;
- model licensing, обновление и долговременная декодируемость;
- generative output не может быть lossless или objective reference;
- MUSHRA может скрыть редкие, но критические semantic errors.

### Решение

Generative Detail полезен и будет исследоваться, но только как discardable
`Perceptual` layer. Он никогда не меняет Core state и никогда не используется
в headline Truth-compression percentages.

## 5. Полный прогноз MAF против лучших стандартизованных anchors

Проценты включают принятый MAF Core. Cached synthesis и motifs учитываются
только в подходящих строках и не суммируются отдельно.

| Сценарий | Основной сильный anchor | Против Opus | Против сильнейшего указанного standard anchor |
|---|---|---:|---:|
| Realtime speech, mono | Opus / EVS | 15–35% | 5–20% против EVS |
| Clean speech/podcast, offline | Opus / xHE-AAC / EVS | 25–50% | 10–30% против лучшего xHE-AAC/EVS |
| General mixed stereo | Opus / xHE-AAC | 20–35% | 10–25% против xHE-AAC |
| Dense pop/rock | Opus / xHE-AAC | 15–30% | 5–20% против xHE-AAC |
| Solo/chamber classical | Opus / xHE-AAC | 35–55% | 20–40% против xHE-AAC |
| Orchestra/choir/reverberant classical | Opus / xHE-AAC | 25–45% | 15–30% против xHE-AAC |
| Loop-based electronic/game stems | Opus / xHE-AAC | 35–60% | 20–45% против xHE-AAC |
| Objective ambience/rain/crowd | Opus / xHE-AAC | 0–20% | от −5% до +10% против xHE-AAC |
| Immersive persistent emitters/room | Opus multistream / IVAS / MPEG-H | 20–40% | 5–20% против IVAS/MPEG-H |
| Lossless PCM | FLAC | неприменимо | 0–15% против FLAC |

Минус в строке ambience означает, что MAF MAY потребовать больше битов. Это
важный hostile class, который нельзя прятать средним результатом.

## 6. Frontier neural codecs — отдельная лига

В 2025–2026 появились research codecs с очень низкими заявленными rates:

- FocalCodec сообщает speech tokens 0.16–0.65 kbit/s;
- LDCodec сообщает преимущество 6 kbit/s над Opus 12 kbit/s в тестах авторов;
- TQCodec исследует high-fidelity music 32–128 kbit/s;
- другие universal neural codecs оптимизируются также для generation/token
  usefulness, а не только waveform transparency.

Прямой процент MAF против них сейчас был бы выдумкой: отличаются corpora,
latency, model size, packet loss, stereo, metrics и definition of quality.

Правильные цели:

- **TARGET:** MAF Core превосходит стандартизованные anchors при существенно
  меньшем decoder и лучшей долговременной state semantics;
- **TARGET:** против frontier neural codec достигается comparable MUSHRA при
  меньшем model/state/energy либо более высокой objective fidelity;
- ultra-low generative режим сравнивается только как отдельный Perceptual
  profile.

## 7. Мой приоритет

1. Реализовать `TIMBRE_BASIS` oracle и CIBS integer kernel одновременно.
2. Сравнить `LIFTING_ONLY`, `RAW_BASIS` и `CIBS_LATENT` полными bitstreams.
3. Измерить долю total bitrate, реально занятую Basis: если она занимает 5%
   потока, даже идеальное её сжатие не даст революции.
4. Добавить motif macro после появления стабильных multi-atom tracks.
5. Generative layer разрабатывать параллельно, но никогда не смешивать с
   Truth benchmarks.

Это сохраняет максимальный потенциальный выигрыш. Решение R-014 принимает
малый bounded CIBS kernel заранее; эксперимент выбирает конкретную model и
доказывает её реальную ценность.
