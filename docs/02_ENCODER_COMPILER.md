# Encoder-компилятор Resonith

Статус: pipeline — **ACCEPTED**; численные параметры — **TARGET**.

## 1. Encoder понимает музыку, decoder исполняет физику

Encoder MAY использовать:

- pitch/onset/tempo/score transcription;
- source separation и emitter tracking;
- instrument, speaker и room recognition;
- long-context music/audio foundation model;
- global motif retrieval;
- differentiable analysis-by-synthesis;
- exhaustive beam/graph search.

Результат анализа не передаётся как обязательная семантика. Encoder
компилирует гипотезы в `TIMBRE_BASIS`, atoms, parameter tracks и Innovation и
проверяет их тем же bit-exact decoder, который получит слушатель.

## 2. Не classifier switch, а соревнование кандидатов

Router предлагает top-K представлений для каждого source/time-frequency
region. Кандидаты MAY перекрываться и складываться. Итоговая функция:

\[
\begin{aligned}
J={}&R_{\mathrm{total}}
+\lambda D_{\mathrm{truth}}
+\alpha D_{\mathrm{perceptual}}\\
&+\mu C_{\mathrm{decode}}
+\nu M_{\mathrm{state}}
+\rho L_{\mathrm{latency}}
+\kappa P_{\mathrm{loss}}
+\eta S_{\mathrm{switch}}.
\end{aligned}
\]

`R_total` включает basis, adapters, events, indexes, checkpoints, entropy
headers и FEC. Proxy разрешён только для shortlist; финальный RDO считает
фактический bitstream.

Неправильная семантическая гипотеза безопасна: если «скрипичный» basis не
окупился, exact RDO выбирает lifting residual.

## 3. Analysis-by-synthesis pipeline

1. Нормализовать channel layout и sample timeline без потери исходника.
2. Найти onsets, periodic tracks, residual noise и long decay.
3. Построить source hypotheses, не требуя идеальной separation.
4. Найти reusable timbre/excitation/room bases.
5. Для каждого Basis сравнить raw/lifting и CIBS latent+correction.
6. Предложить atom tracks с absolute phase.
7. Предложить transient и stochastic predictors.
8. Синтезировать кандидата bit-exact Core decoder-ом.
9. Закодировать остаток Innovation.
10. Выполнить full RDO и temporal dynamic programming.
11. Расставить checkpoints и packet-loss boundaries.

Ошибка source separation не является ошибкой decoder: она просто повышает
Innovation и может сделать decomposition невыгодным.

## 4. Профили encoder-а

### Live

- causal или малый lookahead;
- bounded top-K;
- Realtime profile;
- low-delay lifting fallback;
- packet-loss-aware RDO.

### Studio

- полный трек/произведение;
- bidirectional analysis;
- global timbre and motif dictionary;
- точная phase tracking через паузы и re-entry;
- beam search по sections.

### Foundry

- многочасовой/многосуточный budget;
- ensemble neural teachers;
- глобальная source/score/room hypothesis;
- Pareto search и distillation в Consumer/Studio router;
- тот же bitstream и decoder.

## 5. Consumer practicality

**TARGET:** первый encoder должен запускаться на обычном PC без обязательного
облака. Основной рабочий набор тайлится по source hypotheses, frequency bands
и временным sections; долговременные bases выгружаются в RAM.

Аудио существенно легче видео по размерности. GPU полезен для neural analysis
и batched RDO, но Core prototype обязан иметь CPU path. Производительность
будет измеряться отдельно для Live, Studio и Foundry; до реализации численные
скорости не объявляются фактом.

## 6. Как не получить дёргания архитектуры

Замораживается semantic spine:

```text
continuous timeline
immutable reusable basis
fixed update-time CIBS
absolute parameter tracks
RESET / SET / END
small integer DSP ISA
objective Innovation fallback
optional non-reference Perceptual Detail
```

Новые encoder-модели, quantizers и basis synthesizers разрешены только если
они компилируются в этот spine. Новый opcode добавляется лишь после:

1. oracle ablation;
2. net gain после полного overhead;
3. decoder complexity audit;
4. conformance and corruption analysis;
5. доказательства, что существующий ISA не выражает механизм разумно.

## 7. Teacher–student moat

Foundry сохраняет не только победителя, но и Pareto-set:

- rejected basis families;
- atom lifetime и update decisions;
- битовую стоимость basis/reuse/innovation;
- phase/pitch tracking alternatives;
- packet and checkpoint decisions;
- uncertainty и причины fallback.

Компактный router учится предлагать top-K. Exact RDO сохраняет последнее
слово. Преимущество переносится в encoder/data, не в закрытый decoder.
