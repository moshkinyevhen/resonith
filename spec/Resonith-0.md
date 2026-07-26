# Resonith-0 Bitstream and Decoding Process

Версия: 0.0.2  
Статус: **NORMATIVE-DRAFT**  
Архитектура: **MAF — Memory-oriented Acoustic Field**

Этот документ фиксирует semantic spine. Binary packing, entropy tables,
fixed-point precisions и profile limits будут заморожены после oracle и
conformance experiments.

## 1. Normative language

`MUST`, `MUST NOT`, `SHOULD`, `MAY` имеют нормативный смысл.

## 2. Scope

Resonith-0 определяет самостоятельный детерминированный audio bitstream и
bounded integer decoding process.

Resonith-0:

- MUST декодироваться без видеопотока;
- MUST иметь universal objective Innovation fallback;
- MUST поддерживать CIBS-0 cached integer Basis synthesis;
- MUST поддерживать смешение разных basis families в одно время;
- MUST NOT требовать semantic classifier или per-sample neural inference;
- MUST отделять Truth Core от Optional Perceptual Detail;
- MUST позволять Lossless profile восстановить exact PCM.

## 3. Canonical signal

\[
\hat x[n]=
Mix\left(
\sum_{i\in Active(n)}
RenderAtom_i(n)
\right)
+Innovation[n].
\]

Optional Perceptual Detail применяется только после формирования Core output
и не входит в \(\hat x[n]\) для objective/lossless conformance.

## 4. Timeline

1. Stream MUST задавать rational sample timebase и output sample rate.
2. Event time MUST быть exact integer sample index в stream timebase.
3. Atom parameter law MUST иметь absolute origin.
4. Decoder MUST NOT выводить atom через recursive reference к предыдущему
   output block.
5. Transport packet boundary MUST NOT неявно завершать atom.
6. Render block size является implementation choice и MUST NOT менять output.

## 5. State records

### 5.1 `STREAM_CONFIG`

Определяет:

- profile/level;
- sample rate и channel/output layout;
- fixed-point precision identifiers;
- entropy configuration;
- resource limits;
- capability flags.

### 5.2 `STATE_RESET(t)`

Атомарно очищает atom namespace, Basis Bank и dependent filter state.

### 5.3 `BASIS_SET(t, basis_id, family, payload)`

Создаёт immutable basis. Повторный `basis_id` до reset запрещён.
`family` MAY быть waveform/timbre basis, filter/resonator basis или
`CONTROL_BASIS`.

`payload_mode` MUST быть:

- `RAW_INT`;
- `LIFTED_INT`;
- `CIBS_LATENT`.

Main-0 decoder MUST реализовать все три mode. CIBS payload MUST содержать
`synth_model_id`, target schema, quantized latent, optional bounded adapter,
optional objective correction и expected Basis hash.

### 5.4 `ATOM_SET(t, atom_id, changed_fields, payload)`

Создаёт atom либо атомарно изменяет перечисленные fields. Неуказанные fields
сохраняют прежнее значение.

### 5.5 `ATOM_END(t, atom_id)`

Завершает atom точно перед sample `t`.

### 5.6 `INNOVATION(t, duration, payload)`

Добавляет bounded objective residual. `EXACT_REPLACE` MUST позволять полностью
определить любой интервал независимо от model atoms.

### 5.7 `CHECKPOINT(t)`

Содержит self-contained Core state или `STATE_RESET` плюс достаточный payload
для bounded random access.

### 5.8 `PERCEPTUAL(t, duration, payload)`

Является discardable enhancement и MUST NOT менять Core state.

## 6. Basis families

Один Main decoder использует общий operator ISA. Families не имеют отдельные
entropy coders или clocks.

### 6.0 CIBS Basis materialization

\[
B =
Clip_{basis}\left(
Synth^{int}_{model}(z,adapter)
+LIFT^{-1}(q_{correction})
\right).
\]

Decoder MUST:

1. проверить model/schema/resource limits;
2. выполнить fixed versioned integer graph в staging;
3. применить correction;
4. вычислить normative Basis hash;
5. commit-ить immutable Basis только при совпадении hash.

CIBS MUST выполняться только на `BASIS_SET` или materialization checkpoint.
Per-sample CIBS inference запрещён.

CIBS-0 Basis hash MUST быть SHA-256 от canonical byte sequence:

```text
u8 model_id_utf8_length
u32le basis_channels
u32le samples_per_channel
model_id_utf8
int16le basis_samples[channel-major]
```

`model_id` MUST занимать 1–255 UTF-8 bytes.

### 6.1 `PERIODIC`

\[
y[n]=A[n]\sum_k a_k[n]B_k(\phi[n]).
\]

- `B_k` MUST быть immutable bounded integer periodic tables;
- phase law MUST быть absolute fixed-point;
- interpolation и wrapping MUST иметь canonical rounding;
- atom update MUST сохранять phase continuity либо включать objective
  correction/crossfade.

### 6.2 `PREDICTIVE`

Использует bounded excitation и short stable integer FIR/IIR sections.
Разрешённые coefficients MUST принадлежать profile-defined stability domain.

### 6.3 `STOCHASTIC`

Использует counter-based normative PRNG:

\[
u[n]=PRNG(stream\_key,atom\_id,seed,n).
\]

Shaping MUST быть bounded integer operation. Random access к `n` MUST NOT
требовать генерации samples до `n`.

### 6.4 `RESONANT`

Использует bounded bank stable resonators или short convolution basis.
Unbounded convolution и неопределённый recursive state запрещены.

### 6.5 `TRANSIENT`

Использует onset-relative bounded envelope и/или short inverse integer
lifting basis. Long-window pre-echo MUST иметь отдельный conformance test.

### 6.6 `INNOVATION`

Использует inverse integer lifting, sparse coefficients и exact replacement.
Это universal fallback, а не отдельный content classifier.

### 6.7 `SPATIAL`

Задаёт source routing, gain/delay law и bounded integer mix matrix.
Immersive renderer MAY быть profile-specific, но base Core output MUST
оставаться самостоятельно определённым.

## 7. Operator ISA

Main Core MAY использовать только:

- integer add/subtract/multiply/accumulate;
- canonical shift/round/saturate;
- bounded table lookup/interpolation;
- short FIR/IIR/resonator;
- counter-based PRNG;
- inverse integer lifting;
- coefficient-law evaluation;
- gain/delay/matrix mix;
- entropy decode.

CIBS update-time kernel дополнительно MAY использовать fixed integer
matrix/1D convolution, dyadic upsample, short FIR, piecewise-linear activation
и bounded low-rank adapter. Graph topology и weights определяются
`synth_model_id`, а не bitstream.

Bitstream MUST NOT содержать executable code, arbitrary neural graph,
replacement weights или unbounded loop.

## 8. Canonical composition

1. Events с одним timestamp применяются в coded order после полной проверки.
2. Basis/atom update сначала строится в staging и затем commit-ится атомарно.
3. Active atoms группируются по profile-defined dependency level.
4. Независимые atoms MAY вычисляться параллельно.
5. Accumulation использует profile-defined wide integer accumulator.
6. Saturation/clip выполняется только в определённых mix boundaries.
7. Result MUST быть независим от implementation block size и thread order.

## 9. Parameter tracks

Main-0 MUST поддерживать bounded piecewise:

- constant;
- linear;
- quadratic.

Profile определяет maximum duration, knot count, coefficient range и
derivative. Track оценивается от absolute event origin.

Atom MAY ссылаться на immutable `CONTROL_BASIS`:

\[
\theta_i(t)=s_iQ_r(\tau_i(t))+o_i.
\]

Scale, offset и time mapping MUST быть bounded fixed-point. Reference MUST NOT
создавать cyclic dependency. Shared control evaluation использует те же
parameter-law operators и не является отдельным decoder mode.

## 10. Profiles

### 10.1 `Realtime`

Ограничивает lookahead, atom lifetime dependencies, checkpoint interval и
decoder complexity для low-delay speech/general audio.

### 10.2 `Main`

Поддерживает general mono, stereo и profile-defined multichannel output,
включая все Core families и normative `CIBS-0`.

### 10.3 `Immersive`

Добавляет emitters, listener pose, room/resonant state и profile-defined
spatial renderer.

### 10.4 `Perceptual`

Добавляет discardable learned/generative detail. Никакой Perceptual output
не является Core reference.

### 10.5 `Lossless`

Использует Core predictions, но Innovation MUST обеспечить sample-exact PCM
при declared input format.

Профили являются ограничениями одной syntax, а не независимыми подкодеками.

## 11. Resource limits

Каждый level MUST задавать:

- maximum active atoms;
- maximum basis bytes;
- maximum table taps и interpolation samples;
- maximum filter/resonator order;
- maximum MAC/sample/channel;
- maximum mix sources и channels;
- maximum parameter knots/time;
- maximum checkpoint distance;
- maximum entropy payload;
- maximum state bytes;
- maximum CIBS model ROM, latent, adapter, output elements, MAC/Basis,
  scratch bytes и creations/time;
- accumulator widths и overflow rules.

При превышении encoder MUST использовать более простой representation или
`INNOVATION`; decoder MUST отвергнуть non-conforming stream детерминированно.

## 12. Truth and Perceptual isolation

1. Только Core records MAY менять reference state.
2. `PERCEPTUAL` MUST NOT влиять на future atom, entropy context, checksum или
   checkpoint.
3. Concealment MUST NOT становиться Truth reference.
4. Lossless conformance MUST игнорировать Perceptual records.
5. Semantic labels MAY присутствовать как non-normative metadata, но MUST NOT
   менять Core output.

## 13. Random access and loss

1. Random-access point MUST начинаться с validated `CHECKPOINT` или
   `STATE_RESET`.
2. Stochastic samples MUST быть counter-addressable.
3. CIBS checkpoint MUST содержать self-contained latent+adapter+correction
   либо materialized objective Basis.
4. CIBS Basis hash failure MUST NOT commit partial state.
5. Corrupt state event MUST NOT commit partial changes.
6. После integrity failure dependent state MUST считаться invalid до
   следующего checkpoint.
7. Realtime level MUST ограничивать maximum error propagation.
8. Concealment output MUST быть помечен и не использоваться как reference.

## 14. Encoder requirements

Encoder не нормативен, но conforming bitstream:

- MAY быть создан Live, Studio или Foundry encoder-ом;
- не содержит обязательный classifier decision;
- учитывает все basis/event/checkpoint bits;
- MUST иметь Core fallback для любого input;
- MUST соблюдать resource level независимо от качества encoder-а.

Рекомендуемый final selector:

\[
J=R+\lambda D+\mu C+\nu M+\rho L+\kappa P+\eta S.
\]

## 15. Security

Decoder MUST:

- проверить все sizes/IDs/ranges до allocation и commit;
- проверять filter stability domain;
- предотвращать integer overflow;
- ограничивать entropy operations;
- не выполнять код из bitstream;
- иметь deterministic error path;
- не позволять atom ссылаться на undefined/expired basis.

## 16. Open items

- binary packing;
- entropy contexts/tables;
- exact PRNG construction;
- exact CIBS-0 graph, weights, quantizers, Basis hash и model package;
- lifting kernels;
- sample formats и channel layouts;
- fixed-point precisions;
- stability domains;
- exact profile/level limits;
- packetization/FEC;
- MUSHRA conformance corpus;
- reference encoder/decoder;
- container mappings.

Ни один open item не меняет принятый semantic spine без новой записи в
`docs/06_DECISION_LOG.md`.
