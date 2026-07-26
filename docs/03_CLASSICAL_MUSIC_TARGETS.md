# Классическая музыка: модель и цели

Статус всех чисел в этом документе: **HYPOTHESIS / TARGET**, не результат.

## 1. Почему классика одновременно удобна и трудна

Потенциал MAF:

- устойчивые pitches и harmonic relations;
- повторное использование тембра инструмента;
- score/motif structure;
- длинные resonances и room response;
- offline доступ ко всему произведению.

Трудности:

- dense polyphony и crossing partials;
- vibrato, portamento, microdynamics и expressive timing;
- changing bow/breath/noise excitation;
- атаки без точного повторения;
- длинный reverberant mix;
- microphone noise и audience;
- тембр зависит от ноты, громкости и артикуляции.

Поэтому «передать ноты вместо waveform» недостаточно. Score помогает encoder-у
найти basis и trajectories, но точность исполнения обеспечивает Innovation.

## 2. Рабочие bitrate-гипотезы

При matched MUSHRA quality относительно сильнейшего применимого
Opus/xHE-AAC/USAC anchor:

| Материал | Зрелый Resonith: гипотеза экономии | Кандидат stereo rate |
|---|---:|---:|
| Solo / чистый sustain | 35–60% | 40–72 kbit/s |
| Chamber music | 30–50% | 48–80 kbit/s |
| Orchestra, хороший hall | 20–40% | 72–112 kbit/s |
| Dense choir/percussion/noisy live | 10–30% | 80–128 kbit/s |
| Broad classical corpus | 25–45% | content-adaptive |

Первый работающий prototype, который даёт 10–20% на ограниченном classical
corpus, считается хорошим исследовательским началом. Более 50% на broad
transparent classical — stretch, а не обещание.

Экстремальный Perceptual profile MAY достигать 24–48 kbit/s stereo и большой
экономии, но он не смешивается с claims об objective transparency.

## 3. Lossless

В Lossless exact Innovation обязана вернуть исходный PCM. Для mastered
classical записи microphone/room/noise и микроскопическая непредсказуемость
доминируют в residual.

**HYPOTHESIS:** выигрыш 0–15% против сильного FLAC-подобного anchor реалистичен;
более крупный broad lossless gain маловероятен без нового результата в
универсальном entropy modeling.

## 4. Обязательный benchmark contract

Claims принимаются только если:

- anchors настроены экспертами и включают полный overhead;
- сравнение проводится отдельно с Opus и xHE-AAC/USAC;
- используются ITU-R BS.1534 MUSHRA, hidden reference и low anchors;
- слушатели не знают codec;
- corpus включает solo, chamber, orchestra, choir, percussion, organ,
  historical/noisy recordings;
- учитываются startup, seek, checkpoint и dictionary bits;
- reported confidence intervals и correction for multiple comparisons;
- отдельно проверяются pre-echo, warble, pitch/phase, stereo image, reverb и
  timbre identity;
- objective metrics являются вторичными к listening tests.

## 5. Революционная планка

- менее 15% broad gain: интересный инструмент, но не новый стандарт;
- 15–30%: сильный конкурент;
- не менее 35% broad music/classical при equal MUSHRA и малом decoder:
  революционный результат;
- более 50% broad transparent: исторический stretch, требующий независимого
  воспроизведения.
