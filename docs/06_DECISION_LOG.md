# Журнал решений Resonith

Этот файл является каноническим источником принятых решений. Более новое
решение ссылается на заменяемое и помечает его **SUPERSEDED**.

## R-001 — Рабочее имя самостоятельного аудиокодека

- Дата: 2026-07-26
- Статус: **RESEARCH / OPEN**
- Решение:
  - ведущий кандидат рабочего имени аудиокодека — **Resonith**;
  - имя не является финально выбранным до отдельного решения владельца и
    trademark clearance;
  - имя папки и документов используется как удобный временный namespace и
    не означает утверждения бренда;
  - Resonith не является `QINTRA Audio` и не требует QINTRA;
  - QINTRA остаётся самостоятельным видеокодеком;
  - оптимизированная связь двух кодеков описывается отдельным
    `SceneLith AV Bridge`.

## R-001A — Имя архитектуры

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - внутренняя архитектура самостоятельного аудиокодека —
    **MAF: Memory-oriented Acoustic Field**;
  - смена публичного имени кодека не меняет MAF и bitstream design.

## R-002 — Один acoustic ISA вместо набора подкодеков

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - Resonith имеет одну state grammar, один timeline, один entropy layer и
    малый bounded integer acoustic ISA;
  - speech, music, noise и ambience не являются взаимоисключающими режимами
    временного кадра;
  - coherent, predictive, transient, stochastic, resonant, spatial и
    objective innovation atoms MAY одновременно действовать в одном
    time-frequency участке;
  - профили ограничивают разрешённое подмножество единой syntax, но не
    являются вложенными независимыми кодеками.

## R-003 — Выбор представления через decoder-in-the-loop RDO

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - classifier/router только предлагает top-K кандидатов;
  - окончательный выбор делает точный RDO по полному битрейту, distortion,
    decoder compute, state memory, latency, resilience и switching stability;
  - semantic label инструмента, ноты или речи никогда не является
    достаточным основанием для нормативной реконструкции;
  - универсальный Truth Innovation является обязательным fallback.

## R-004 — Непрерывное состояние вместо coding frames

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - параметр атома передаётся при рождении или действительном изменении;
  - отсутствие события означает продолжение предыдущего закона;
  - transport packets и внутренние render quanta разрешены, но не являются
    единицей акустического состояния;
  - phase, envelope и trajectory задаются от абсолютного sample/time origin;
  - любое переключение обязано быть phase-/energy-continuous либо закрываться
    objective innovation.

## R-005 — Timbre Basis, excitation и room response оплачиваются один раз

- Дата: 2026-07-26
- Статус: **ACCEPTED / NORMATIVE-DRAFT**
- Решение:
  - повторяющийся тембр хранится как immutable `TIMBRE_BASIS`;
  - periodic/coherent atoms ссылаются на basis и передают phase, pitch,
    amplitude и малые coefficient trajectories;
  - excitation MAY быть отделён от resonator, чтобы один excitation law
    возбуждал несколько мод и источников;
  - room/resonator basis MAY переиспользоваться многими emitters;
  - все basis payloads, adapters и dictionary references учитываются в
    полном битрейте;
  - скрытая внешняя модель не требуется для standalone decode.

## R-006 — Детерминированные stochastic fields

- Дата: 2026-07-26
- Статус: **ACCEPTED / NORMATIVE-DRAFT**
- Решение:
  - stochastic atom использует counter-based PRNG, абсолютный sample index,
    seed и bounded integer spectral/resonant shaping;
  - recursive PRNG state не должен быть обязательным для random access;
  - stochastic reconstruction в Truth Core детерминирована;
  - её несовпадение с исходником закрывается Truth Innovation;
  - Optional Perceptual Detail никогда не становится reference.

## R-007 — Профили единого стандарта

- Дата: 2026-07-26
- Статус: **ACCEPTED / NORMATIVE-DRAFT**
- Профили:
  - `Realtime`: speech/general low delay, packet-loss constraints;
  - `Main`: general mono/stereo/multichannel audio;
  - `Immersive`: emitters, room and spatial rendering;
  - `Perceptual`: discardable learned/generative detail, не reference;
  - `Lossless`: exact PCM reconstruction тем же Core плюс exact innovation.

## R-008 — Численные цели не являются результатом

- Дата: 2026-07-26
- Статус: **TARGET / HYPOTHESIS**
- Решение:
  - любой compression claim отчётен отдельно против Opus, xHE-AAC/USAC,
    EVS/IVAS и lossless anchor там, где они применимы;
  - matched-quality определяется MUSHRA/ABX с hidden anchors;
  - broad classical target зрелого поколения: 25–45% меньший bitrate
    относительно сильнейшего применимого anchor при равном субъективном
    качестве;
  - революционная планка: не менее 35% на broad music/classical corpus при
    малом software decoder и без систематических phase/timbre artifacts;
  - эти числа являются гипотезами до воспроизводимого эксперимента.

## R-009 — Повторяющиеся acoustic programs

- Дата: 2026-07-26
- Статус: **RESEARCH**
- Решение:
  - repeated motif, accompaniment pattern или emitter program MAY быть
    content-addressed macro, создающим обычные Core atoms с time/pitch/gain
    transform;
  - Main-0 не получает отдельный музыкальный язык, score VM или
    Turing-complete scripting;
  - механизм принимается в Main только при net gain не менее 5% на broad
    music после учёта dictionary и seek overhead.

## R-010 — Первый путь разработки

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - разработка начинается с standalone Resonith, не с AV Bridge;
  - первый oracle сравнивает универсальный lifting residual с
    `TIMBRE_BASIS + PHASE_TRACK + residual`;
  - затем добавляются transient и stochastic candidates;
  - spatial/room и Perceptual profile не блокируют первый codec loop;
  - каждое расширение обязано пройти отдельный ablation и kill-gate.

## R-011 — Shared Control Basis

- Дата: 2026-07-26
- Статус: **NORMATIVE-DRAFT / HYPOTHESIS**
- Решение:
  - общая modulation trajectory MAY храниться один раз как immutable
    `CONTROL_BASIS`;
  - несколько atoms MAY ссылаться на неё с bounded scale/offset/time mapping;
  - механизм покрывает общие tempo/rubato, vibrato, dynamics, pitch bend,
    emitter trajectory и room change без semantic labels;
  - `CONTROL_BASIS` использует те же fixed-point parameter-law operations и не
    добавляет новый DSP opcode;
  - механизм остаётся optional, если full-RDO не окупает reference metadata.

## R-012 — Статус трёх оставшихся направлений

- Дата: 2026-07-26
- Статус: **RESEARCH / HYPOTHESIS**
- Решение:
  - cached learned Basis synthesis рассматривается как optional способ кодирования
    `BASIS_SET`, а не per-sample neural renderer; inclusion gate — не менее 5%
    broad net bitrate reduction либо не менее 12% на заранее заявленном
    существенном классе при bounded startup;
  - motif macro MAY только детерминированно разворачивать уже существующие
    atoms; отдельная musical VM запрещена; inclusion gate остаётся не менее 5%
    на broad music после seek/checkpoint overhead;
  - generative detail допускается только в `Perceptual` profile, не меняет
    Truth state и не участвует в objective/lossless claims;
  - ориентировочные выигрыши этих направлений нельзя складывать: они
    перекрываются и конкурируют в одном полном RDO;
  - таблицы в `08_RESEARCH_DIRECTIONS_AND_CODEC_TARGETS.md` являются
    архитектурными прогнозами, не измеренными результатами.

## R-013 — Контракт сравнения с лучшими audio anchors

- Дата: 2026-07-26
- Статус: **ACCEPTED / TARGET**
- Решение:
  - speech/realtime сравнивается отдельно с Opus, EVS и LC3plus;
  - general/music streaming сравнивается отдельно с Opus и xHE-AAC/USAC;
  - immersive сравнивается отдельно с IVAS и применимым MPEG-H/object anchor;
  - lossless сравнивается с FLAC и применимым современным lossless anchor;
  - frontier neural papers отчётны отдельной research table и не называются
    production anchors до независимого воспроизведения;
  - равенство качества определяется MUSHRA/ABX при одинаковых latency,
    resilience, channel, random-access и complexity constraints;
  - отрицательные и worst-decile результаты публикуются наряду со средним.

## R-014 — Cached Integer Basis Synthesis входит в Main-0

- Дата: 2026-07-26
- Статус: **ACCEPTED / NORMATIVE-DRAFT**
- Решение владельца:
  - cached learned Basis synthesis реализуется с первой версии, а не
    откладывается как research extension;
  - нормативное имя механизма —
    **CIBS: Cached Integer Basis Synthesis**;
  - `BASIS_SET` MUST поддерживать `CIBS_LATENT` наряду с objective raw/lifting
    fallback;
  - fixed versioned integer synthesis graph запускается только при создании
    Basis и выдаёт immutable cached `TIMBRE/FILTER/CONTROL_BASIS`;
  - arbitrary graph, floating-point dependency, external mandatory model и
    per-sample neural inference запрещены;
  - optional adapter и objective basis correction входят в bitstream и полный
    bitrate;
  - synthesized Basis MUST иметь normative hash и bit-exact output;
  - Main profile MUST реализовать базовый `CIBS-0`; Realtime profile MAY
    ограничить создание новых bases startup/checkpoint intervals;
  - R-012 переводится в **SUPERSEDED** только в части research-статуса CIBS;
    motif macros и Generative Detail сохраняют прежние статусы.

## R-015 — CIBS-first implementation order

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - первый periodic oracle сразу сравнивает три пути:
    `LIFTING_ONLY`, `RAW_BASIS + residual`,
    `CIBS_LATENT + correction + residual`;
  - reference integer synthesis kernel создаётся до training pipeline;
  - training/export ненормативны, decoder kernel и model package проходят
    отдельные bit-exact tests;
  - первый CIBS model MAY быть слабым: architecture correctness отделяется от
    последующего качества обучения.

## R-016 — MAF-P0 end-to-end prototype

- Дата: 2026-07-26
- Статус: **IMPLEMENTED / EXPERIMENTAL RESULT**
- Реализовано:
  - mono PCM16 WAV I/O;
  - encoder-side period detection и periodic Basis extraction;
  - Q32 phase renderer и Q15 block amplitude law;
  - `RAW_BASIS` и `CIBS_LATENT + correction`;
  - quantized/exact objective residual;
  - self-checking compressed container;
  - independent decoder, CLI и corruption tests.
- Первый synthetic harmonic benchmark, 10 s / 48 kHz:
  - raw-Basis lossless: 55,728 bytes против 960,000 bytes PCM;
  - CIBS lossless: 55,971 bytes, то есть на одном Basis пока хуже raw на
    243 bytes;
  - CIBS lossy `basis_q=8`, `residual_q=16`: 11,333 bytes, SNR 66.13 dB,
    maximum absolute error 8;
  - на bank из 128 unseen harmonic bases CIBS exact correction проиграла raw
    Basis 4.15%, а CIBS q8 correction выиграла 30.02%;
  - experimental model package: 3,654 bytes, отчётен отдельно.
- Ограничение:
  - это synthetic favourable class и сравнение с PCM/raw Basis, не с
    Opus/xHE-AAC;
  - zlib является временным entropy baseline;
  - цифры не являются codec claim.

## R-017 — Имя Resonith утверждено окончательно

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение владельца:
  - окончательное продуктовое имя самостоятельного аудиокодека —
    **Resonith**;
  - R-001 в части открытого статуса имени становится **SUPERSEDED**;
  - архитектура сохраняет имя
    **MAF — Memory-oriented Acoustic Field**;
  - рекомендуемое имя публичного GitHub repository — `resonith`;
  - trademark/FTO clearance остаётся отдельной юридической задачей и не
    отменяет внутренний выбор имени.

## R-018 — Имя связанного видеокодека изменено на SceneLith

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение владельца:
  - standalone video codec окончательно называется **SceneLith Video**;
  - бывшее имя QINTRA выведено из актуального брендинга;
  - Resonith остаётся полностью самостоятельным аудиокодеком;
  - специализированная совместная оптимизация по-прежнему определяется
    отдельной спецификацией SceneLith AV Bridge.

## R-019 — Публичный GitHub и безопасная автосинхронизация

- Дата: 2026-07-26
- Статус: **ACCEPTED**
- Решение:
  - рекомендуемое имя отдельного public repository — `resonith`;
  - каждый явно созданный local commit автоматически отправляется в `origin`
    repo-local hook-ом;
  - hook никогда сам не выполняет `git add` и не создаёт commit;
  - перед первым public push обязательны tests, secret/PII scan и проверка
    tracked files;
  - CI запускает reference tests на каждом push и pull request.
