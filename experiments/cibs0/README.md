# CIBS-0 experiment

Статус: reference arithmetic prototype; demo model не обучен и не нормативен.

Текущие артефакты:

- `../../reference/cibs0/cibs0.py` — integer materialization kernel;
- `../../tests/test_cibs0.py` — repeatability, hash, adapter, correction и
  type-safety tests.

Первый benchmark обязан сравнить:

```text
LIFTING_ONLY
RAW_BASIS + waveform residual
CIBS_LATENT + basis correction + waveform residual
```

Следующий шаг — training/export pipeline, который обучает analysis/synthesis
model на извлечённых periodic bases, квантует weights/latents и проверяет
export тем же reference integer kernel.

Demo weights служат только для фиксации арифметики. Compression claim по ним
запрещён.
