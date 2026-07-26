# MAF-P0 — первый исполнимый аудиокодек

Дата: 2026-07-26  
Статус: **IMPLEMENTED / EXPERIMENTAL**

## 1. Что уже работает

Полный путь:

```text
PCM16 mono
→ period analysis
→ persistent periodic Basis
→ RAW или CIBS materialization
→ Q15 amplitude events
→ objective residual
→ compressed MAF0 container
→ independent decoder
→ PCM16
```

Исходники:

- `../reference/maf_p0/` — codec, container, model, renderer, WAV I/O и CLI;
- `../reference/cibs0/` — bit-exact CIBS kernel;
- `../tests/` — round-trip, corruption, hash и quality tests;
- `../experiments/maf_p0_benchmark.py` — воспроизводимый benchmark.

## 2. Первый benchmark

Corpus: synthetic harmonic sustained note, 10 s, 48 kHz mono PCM16.

| Режим | Stream | PCM saving | Качество |
|---|---:|---:|---|
| Raw Basis lossless | 55,728 B | 94.195% | exact |
| CIBS lossless | 55,971 B | 94.170% | exact |
| CIBS basis-q8/residual-q16 | 11,333 B | 98.819% | 66.13 dB, max error 8 |

Experimental CIBS model package: 3,654 B, отдельно от stream.

На bank из 128 unseen harmonic bases:

| Basis representation | Compressed bytes | против raw Basis |
|---|---:|---:|
| Raw int16 Basis | 64,866 | anchor |
| CIBS + exact correction | 67,557 | −4.15% |
| CIBS + q8 correction | 45,393 | +30.02% |

## 3. Интерпретация

Положительное:

- архитектурный pipeline действительно исполним;
- lossless round-trip bit-exact;
- CIBS q8 уже уменьшает Basis bank на 30% на favourable unseen corpus;
- Basis создаётся один раз, CIBS не работает в sample loop;
- corrupted section и wrong Basis hash не commit-ятся.

Отрицательное:

- CIBS exact пока проигрывает raw Basis;
- на одном Basis latent/correction/header не амортизируются;
- residual занимает основную часть full stream;
- synthetic periodic signal является очень лёгким классом;
- сравнение с PCM не говорит о победе над FLAC, Opus или xHE-AAC.

Эти отрицательные результаты являются частью проекта, а не скрываются.

## 4. Как запустить на WAV

Текущий prototype принимает mono PCM16 WAV. Нужны минимум два training WAV
для experimental CIBS model:

```text
python -m maf_p0 train-model model.npz note1.wav note2.wav note3.wav
python -m maf_p0 encode input.wav output.maf0 --mode cibs --model model.npz
python -m maf_p0 decode output.maf0 restored.wav --model model.npz
python -m maf_p0 benchmark input.wav model.npz
```

Перед запуском `PYTHONPATH` должен включать `G:\Resonith\reference`.

## 5. Что нужно до сравнения с Opus

1. Несколько periodic segments и независимые lifetimes вместо одного Basis.
2. Continuous pitch/phase trajectory.
3. Transient path без pre-echo.
4. General lifting residual вместо zlib-only placeholder.
5. Stereo.
6. Real training corpus и nonlinear CIBS refinement.
7. Встроенный Opus/xHE-AAC anchor runner.
8. MUSHRA-ready decoded outputs и полное bit accounting.

## 6. Временная оценка

- ограниченный compression test на sustained mono WAV: доступен сейчас;
- real-instrument CIBS corpus и multi-Basis ablation: 2–4 дня;
- первый технический bitrate/quality test против Opus: 1–2 недели;
- meaningful mixed music/classical prototype: 3–6 недель;
- broad standard-grade conclusion потребует месяцев corpus/listening work.

Это сроки непрерывной разработки, а не обещание победы к указанной дате.
