# Устав и North Star Resonith

Статус: основные принципы — **ACCEPTED**; численные цели — **TARGET**.

## 1. Миссия

Resonith должен стандартизовать не очередную последовательность
психоакустически квантованных waveform frames, а ограниченный компиляторный
контракт для непрерывного акустического поля.

Encoder ищет компактные причины сигнала:

- устойчивые periodic/quasi-periodic компоненты;
- изменяющийся тембр;
- excitation и resonant response;
- stochastic texture;
- transients;
- emitters, spatial trajectories и room response;
- объективную innovation, не объяснённую моделью.

Decoder не обязан понимать слова «скрипка», «нота» или «симфония». Он обязан
bit-exact исполнить физические integer-параметры.

## 2. Каноническая формула

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+TruthInnovation_t
+OptionalPerceptualDetail_t.
\]

Для source \(e\):

\[
s_e(t)=C_e(t)+N_e(t)+T_e(t)+E_e(t),
\]

где:

- \(C_e\) — coherent low-rank periodic field;
- \(N_e\) — deterministic stochastic field;
- \(T_e\) — sparse transient field;
- \(E_e\) — objective exact/quantized innovation.

## 3. Главный принцип

Resonith передаёт не «тип куска: speech/music/noise», а одновременно выбирает
лучшее представление для каждого source/time-frequency atom.

В одном интервале могут сосуществовать:

- голосовой predictive/coherent atom;
- атака барабана как transient;
- тарелка как stochastic field;
- reverb как room/resonant field;
- Truth Innovation для оставшейся ошибки.

Router предлагает кандидатов. Окончательный выбор делает полный RDO:

\[
J=\sum_i R_i+\lambda D(x,\hat x)+\mu C_{\mathrm{decode}}.
\]

## 4. Что означает «понимать музыку»

Encoder MAY:

- транскрибировать score;
- выделять stems и emitters;
- узнавать инструменты и исполнителей;
- отслеживать pitch, onset, articulation, tempo и motifs;
- оценивать room impulse response;
- строить per-instrument timbre manifold;
- использовать foundation models и offline global optimization.

Но semantic label MUST NOT заменять objective evidence. Нота `A4` не
определяет тембр, фазу, микродинамику, bow noise, room или интерпретацию.
Любая semantic reconstruction проверяется exact decoder-in-the-loop RDO, а
ошибка кодируется Truth Innovation.

## 5. Отдельность продуктов

- Resonith — самостоятельный аудиокодек.
- SceneLith — самостоятельный видеокодек.
- SceneLith AV Bridge — отдельный binding, который MAY объединять timeline,
  entity mapping, trajectories и room/geometry hints.

Ни один standalone bitstream не требует другой modality.

## 6. North Star

**TARGET:**

- materially beat Opus, xHE-AAC/USAC и EVS отдельно в применимых режимах;
- perceptually transparent classical stereo при существенно меньшем bitrate;
- exact PCM lossless path;
- live latency не выше 20 ms для Realtime profile;
- Main decoder с bounded update-time CIBS, но без per-sample neural inference;
- один bounded atom grammar вместо набора независимых подкодеков;
- software decode на обычном mobile CPU/DSP.
