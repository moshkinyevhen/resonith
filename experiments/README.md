# Эксперименты Resonith / MAF

Первый обязательный эксперимент:

```text
integer lifting baseline
vs
TIMBRE_BASIS + absolute PHASE_TRACK + integer lifting residual
```

Отчёт для каждого clip обязан хранить:

- input hash и PCM format;
- encoder configuration;
- полный payload breakdown;
- exact decoded output hash;
- objective distortion;
- encode/decode time;
- active atoms и state bytes;
- fallback rate;
- worst-case artifacts/notes.

Никакой aggregate gain не считается результатом без per-clip table,
reproducible command и independent decode.
