# CIBS — Cached Integer Basis Synthesis

Дата: 2026-07-26  
Статус semantic contract: **ACCEPTED**  
Exact graph/weights/precisions: **NORMATIVE-DRAFT**

## 1. Назначение

CIBS уменьшает стоимость immutable acoustic Basis. Encoder передаёт
quantized latent и optional small adapter; fixed integer graph один раз
синтезирует Basis, после чего обычный MAF renderer многократно её использует.

\[
B^\star =
\operatorname{Clip}_{16}\left(
\operatorname{Synth}_{m}^{int}(z,A)
+LIFT^{-1}(q_c)
\right).
\]

CIBS сжимает representation, а не генерирует output audio. Objective
correction \(q_c\) и universal waveform Innovation остаются обязательными
fallbacks.

## 2. `CIBS_LATENT` payload

Логические fields:

```text
synth_model_id
target_basis_schema
latent_shape
latent_quantizer_id
latent_payload
adapter_present
adapter_descriptor
adapter_payload
correction_mode
correction_payload
expected_basis_hash
```

Все payload bits учитываются в bitrate. `expected_basis_hash` вычисляется
после correction и до commit в Basis Bank.

### 2.1 CIBS-0 Basis hash

Первый исполнимый contract использует SHA-256 над:

```text
u8 model_id_utf8_length
u32le basis_channels
u32le samples_per_channel
model_id_utf8
int16le basis_samples[channel-major]
```

`model_id` не превышает 255 UTF-8 bytes. Hash не заменяет transport integrity;
он доказывает, что normative materialization дала ожидаемый Basis.

## 3. Normative decoding

1. Проверить model ID, target shape и level limits.
2. Entropy-decode latent, adapter и correction в staging.
3. Выполнить fixed integer `Synth_model_id`.
4. Применить normative inverse-lifting correction.
5. Saturate в target Basis precision.
6. Вычислить normative Basis hash.
7. При совпадении hash атомарно commit-ить immutable Basis.
8. При несовпадении не менять state и ждать objective recovery/reset.

Atoms не имеют доступа к latent, intermediate activations или adapter после
commit. Они видят только готовый Basis.

## 4. Integer graph envelope

Разрешены только:

- int8/int16 constants и latents;
- profile-defined int32/int64 accumulators;
- fixed matrix/1D convolution;
- dyadic upsample;
- short FIR;
- fixed piecewise-linear activation;
- canonical right shift/round;
- saturate/clip;
- bounded low-rank adapter;
- inverse integer lifting correction.

Запрещены:

- произвольный graph из bitstream;
- floating point;
- dynamic loop/recursion;
- attention с data-dependent unbounded memory;
- external/downloaded model;
- device-specific approximate math;
- per-sample CIBS execution.

## 5. Versioning

`synth_model_id` однозначно определяет:

- graph topology;
- normative weights/biases;
- tensor shapes;
- quantization scales;
- rounding/saturation;
- output Basis schema;
- maximum operations и scratch memory.

Main-0 decoder MUST поддерживать `CIBS-0`. Новая модель требует новой
capability/version entry; bitstream не может незаметно заменить weights.

## 6. Adapter

Adapter MAY задавать только profile-bounded low-rank delta:

\[
W'=W+UV^\top.
\]

Rank, matrices, scale и target layers ограничены level. Adapter:

- входит в bitrate;
- действует только во время одного `BASIS_SET`;
- не меняет глобальную model;
- уничтожается после materialization Basis;
- не может изменить graph topology.

## 7. Correction и exactness

`correction_mode`:

- `NONE`;
- `LOSSY_LIFTING`;
- `EXACT_LIFTING`.

`EXACT_LIFTING` MUST позволять bit-exact target Basis. Даже exact Basis не
обеспечивает lossless waveform без обычной waveform Innovation.

RDO выбирает CIBS только если:

\[
R_z+R_A+R_c+R_{events}
<
R_{\mathrm{raw/lifted\ basis}}
+\Delta R_{\mathrm{waveform\ residual}}.
\]

## 8. Resource envelope

Каждый level задаёт:

- maximum models;
- model ROM bytes;
- latent elements;
- adapter rank/bytes;
- output Basis elements;
- MAC/Basis;
- scratch bytes;
- correction bytes;
- CIBS creations/time interval;
- startup/checkpoint CIBS budget.

Первый experimental target, не нормативный final:

| Параметр | **TARGET** |
|---|---:|
| Model ROM | не более 256 KiB |
| Latent | 32–128 int8 elements |
| Output | 1–8 basis channels, 256–2048 int16 samples/channel |
| Graph depth | не более 4 synthesis stages |
| Kernel width | не более 7 |
| Compute | 0.25–2 M integer MAC/Basis |
| Adapter | rank не более 4 |

## 9. Random access

Checkpoint MUST либо:

- повторить self-contained CIBS payload и materialize Basis; либо
- содержать objective materialized Basis payload.

Reference decoder не обязан сохранять CIBS activations между checkpoints.
Realtime profile MAY запрещать CIBS creation между разрешёнными setup
boundaries.

## 10. Training и export

Training pipeline ненормативен и MAY использовать float, GPUs, large teachers
и arbitrary losses. Export обязан:

1. quantize graph;
2. выполнить range analysis;
3. подтвердить integer kernel;
4. сгенерировать model hash;
5. пройти cross-platform bit-exact vectors;
6. измерить full bit cost с corrections.

Качество training можно улучшать без изменения bitstream только пока
normative `CIBS-0` weights не заморожены. После freeze новые weights получают
новый model ID.

## 11. Kill conditions конкретной модели

Syntax CIBS остаётся, но конкретная model версия отклоняется, если:

- broad net gain меньше 5%;
- заранее заявленный specialised gain меньше 12%;
- correction систематически возвращает более 70% raw Basis bits;
- CIBS повышает waveform residual сильнее, чем экономит Basis;
- model не даёт bit-exact output;
- startup/ROM/scratch превышают level;
- OOD worst decile существенно хуже raw/lifting Basis.
