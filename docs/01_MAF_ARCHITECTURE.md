# MAF — Memory-oriented Acoustic Field

Статус: архитектурное ядро — **ACCEPTED**; конкретные precisions и tables —
**NORMATIVE-DRAFT**.

## 1. Парадокс

Звуковая волна физически должна продолжаться, но параметры устойчивого
колебания незачем передавать снова каждые 10–20 ms. Resonith отделяет:

1. долгоживущую акустическую причину;
2. редкое изменение её закона;
3. объективную innovation, которую модель не объяснила;
4. необязательную perceptual detail, не являющуюся истиной.

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+TruthInnovation_t
+OptionalPerceptualDetail_t.
\]

Transport остаётся пакетным, а DAC выдаёт samples, но neither packet nor
sample block является единицей долгоживущего codec state.

## 2. Не классификация куска, а superposition

Один и тот же интервал MAY одновременно содержать:

- `PERIODIC`: нота, voiced speech, двигатель;
- `PREDICTIVE`: excitation и короткая vocal/formant model;
- `TRANSIENT`: удар, щелчок, атака;
- `STOCHASTIC`: дыхание, дождь, тарелка, bow noise;
- `RESONANT`: струна, корпус, помещение, reverb tail;
- `SPATIAL`: emitter/listener law и mixer;
- `INNOVATION`: всё, что выгоднее передать объективным residual.

Это не семь подкодеков. Это параметры малого общего ISA, которые смешиваются
sample-accurately и используют один timeline, state grammar и entropy layer.

## 3. Универсальная запись атома

Логическая запись:

```text
Atom {
    atom_id
    basis_family
    birth_time
    death_time | open_ended
    source_id
    basis_ref | inline_basis
    changed_fields
    parameter_tracks
    routing
    truth_class
}
```

State меняют только:

```text
RESET(time)
SET(time, atom_id, changed_fields, payload)
END(time, atom_id)
```

`END` является канонической краткой формой `SET(alive=0)`. Отсутствие `SET`
означает сохранение прежнего закона. Render query читает state и не изменяет
его.

## 4. Coherent field и Timbre Basis

Передавать тысячи независимых синусоид невыгодно. Основной coherent atom
использует кэшируемый периодический basis:

\[
C_i(t)=A_i(t)\sum_{k=0}^{K_i-1}
a_{ik}(t)B_{ik}(\phi_i(t)).
\]

Где:

- \(B_{ik}\) — immutable integer wavetable/timbre basis;
- \(\phi_i(t)\) — absolute fixed-point phase law;
- \(A_i(t)\) и \(a_{ik}(t)\) — bounded continuous coefficient tracks.

Один `TIMBRE_BASIS` MAY использоваться всеми нотами партии, одним
инструментом, голосовыми сегментами или повторными появлениями источника.
Изменение pitch не требует повторной передачи waveform. Если basis перестал
объяснять исполнение, encoder обновляет coefficients или выбирает Innovation.

Нормативный decoder не знает, что basis принадлежит скрипке. Это знание
используется только encoder-компилятором.

## 5. CIBS — Cached Integer Basis Synthesis

**ACCEPTED:** `TIMBRE_BASIS`, `FILTER_BASIS` и `CONTROL_BASIS` MAY
передаваться не только raw/lifting coefficients, но и как:

\[
B=\operatorname{CIBS}_{m}(z,\Delta_m)
+LIFT^{-1}(q_{\mathrm{basis\ correction}}).
\]

Где:

- \(m\) — profile-defined versioned integer model;
- \(z\) — quantized latent;
- \(\Delta_m\) — optional bounded low-rank adapter;
- correction — objective integer поправка к synthesized Basis.

Synthesizer запускается только на `BASIS_SET`. После проверки hash результат
становится immutable и sample loop видит обычный cached Basis. Таким образом
learned compression уменьшает Basis payload, но не превращает audio renderer
в neural decoder.

Main запрещает:

- arbitrary graph из bitstream;
- device floating-point behaviour;
- внешнюю модель, необходимую для decode;
- изменение weights после profile publication;
- CIBS inference на каждом output sample.

Полная семантика:
[09_CIBS_NORMATIVE_DESIGN.md](09_CIBS_NORMATIVE_DESIGN.md).

## 6. Excitation–resonator factorization

\[
R_i(t)=\sum_m H_{im}(z;\rho_{im}(t))\,e_i(t),
\]

где \(e_i\) — excitation, а \(H_{im}\) — малые stable integer
FIR/IIR/resonator sections.

Один excitation MAY возбуждать несколько resonant modes. Один room basis MAY
обрабатывать несколько emitters. Это позволяет оплачивать долгоживущую
структуру один раз, а затем передавать редкие parameter events.

Каждый IIR section обязан иметь нормативное доказательство bounded stability
для разрешённого диапазона coefficients.

## 7. Shared Control Basis

Множество акустических atoms часто подчиняется одному изменению:

- tempo/rubato нескольких нот;
- vibrato или pitch bend группы partials;
- crescendo/dynamics ансамбля;
- движение emitter;
- изменение room/microphone law.

Повторять одинаковые knots в каждом atom не нужно. Immutable
`CONTROL_BASIS` задаёт scalar/vector parameter law один раз; atoms ссылаются на
неё с bounded scale, offset и time mapping:

\[
\theta_i(t)=s_i\,Q_r(\tau_i(t))+o_i.
\]

Decoder не обязан знать, что \(Q_r\) означает tempo или vibrato. Он вычисляет
обычную fixed-point law. Semantic score помогает encoder-у обнаружить reuse,
но не становится Truth.

## 8. Stochastic field без скрытой случайности

\[
N_i[n]=F_{\mathrm{int}}\left(
PRNG(seed_i,n),\Sigma_i(n)
\right).
\]

- PRNG является counter-based: sample \(n\) вычисляется независимо;
- seed, spectral envelope и filter law входят в bitstream;
- результат bit-exact;
- random access не требует проигрывать всю предыдущую историю;
- objective mismatch передаётся Innovation.

Stochastic atom не означает «похожий шум равен исходному». В lossy profile
такой predictor допустим только после RDO; в Lossless exact residual
восстанавливает исходный PCM.

## 9. Transient и Innovation

Transient не должен размазываться длинным окном и создавать pre-echo.
Core использует короткие integer lifting bases с независимым onset:

\[
T_i + E = LIFT^{-1}(q_{\mathrm{sparse}}).
\]

`TRANSIENT` имеет параметризованный onset/decay, когда это выгодно.
`INNOVATION` является универсальным bounded fallback и MAY быть:

- короткой sparse lifting correction;
- band-limited correction;
- full-band exact replacement.

Lossy Innovation детерминирована, но квантована. Lossless Innovation обязана
восстановить exact input PCM.

## 10. Минимальный normative DSP ISA

Main decoder строится из следующих операций:

1. periodic table lookup/interpolation с absolute phase;
2. short integer FIR/IIR/resonator;
3. counter-based integer PRNG;
4. inverse integer lifting;
5. coefficient-track evaluation;
6. gain, mix, spatial matrix, add, saturate/clip;
7. единый entropy decoder.

CIBS добавляет отдельный update-time kernel из fixed integer
matrix/filter/upsample/nonlinearity operations. Он не входит в per-sample hot
loop и имеет отдельный MAC/Basis limit.

Никакой atom не исполняет произвольный код. Никакой neural graph не обязателен
в Truth Core. Параллельность определяется dependency levels, а не порядком
случайного dynamic graph.

## 11. Непрерывные laws

Phase, amplitude, pitch, filter coefficients и spatial trajectory задаются
piecewise constant/linear/quadratic laws с absolute start time.

Обязательные инварианты:

- phase continuity;
- ограниченный derivative jump либо crossfade/Innovation;
- canonical fixed-point rounding;
- clip только в нормативных mix boundaries;
- bounded atom overlap;
- отсутствие recursive dependence на предыдущий output block.

Разные atoms обновляются с разной частотой. Устойчивая нота может жить тысячи
render quanta; transient — несколько samples; ambience law — секунды.

## 12. Truth и Perceptual

`Truth Core` включает deterministic atoms и Innovation и является единственным
источником будущего state/reference.

`Optional Perceptual Detail` MAY синтезировать незаметную микротекстуру или
верхний спектр, но:

- MUST быть discardable;
- MUST NOT менять Core state;
- MUST NOT быть predictor/reference;
- MUST иметь capability signaling;
- MUST NOT использоваться в objective/lossless claims.

## 13. Где находится преимущество

Революция возможна только если один persistent atom одновременно убирает:

- повторную передачу тембра;
- повторную оценку pitch/phase на каждом frame;
- несовместимые переключения speech/music codec;
- длинный reverb waveform;
- repeated excitation/resonance structure;
- повторную передачу общей modulation trajectory.

Если metadata и residual почти равны обычному transform codec, MAF не имеет
преимущества. Поэтому каждый basis family является RDO-кандидатом, а не
обязательным режимом.

## 14. Что сознательно не входит в Main-0

- обязательное score/MIDI representation;
- названия инструментов как декодирующая истина;
- unrestricted/per-sample neural decoder; fixed update-time CIBS разрешён;
- Turing-complete acoustic program;
- внешняя cloud dictionary, без которой stream недекодируем;
- неограниченная convolution;
- неограниченное число atoms на sample.

Repeated motif programs и shared package dictionaries остаются **RESEARCH** и
обязаны компилироваться в тот же ISA. CIBS принят решением R-014.
