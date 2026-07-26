# Инструкции для агентов Resonith

## Каноническая область

`Resonith` является окончательно принятым именем самостоятельного аудиокодека.
Кодек не является профилем SceneLith и не требует видеопотока для декодирования.
Внутренняя архитектура — MAF.

Совместная оптимизация Resonith и SceneLith Video описывается только отдельной
спецификацией `G:\SceneLith-AV-Bridge`.

## Статусы

- **ACCEPTED** — принято владельцем.
- **NORMATIVE-DRAFT** — предполагаемое нормативное требование.
- **HYPOTHESIS** — проверяемая техническая гипотеза.
- **TARGET** — цель, а не измеренный результат.
- **RESEARCH** — идея вне обязательного Main.
- **SUPERSEDED** — заменённое решение.

## Инварианты

1. Truth Core детерминирован, bounded и пригоден для integer DSP/GPU/ASIC.
2. Optional Perceptual Detail никогда не является reference.
3. Semantic/music understanding разрешён encoder-у, но не считается истиной.
4. Нормативный bitstream передаёт физически проверяемые acoustic fields,
   trajectories и innovation, а не обязательные названия нот и инструментов.
5. Lossless profile должен восстанавливать точный PCM.
6. Один decoder/bitstream обслуживает Live, Studio и Foundry encoders.
7. Отсутствие видео не должно влиять на standalone decode.
8. Любая новая идея сначала фиксируется в `docs/06_DECISION_LOG.md`.
9. Main-0 включает CIBS: fixed integer synthesis выполняется только при
   `BASIS_SET`, а synthesized Basis после этого immutable.
10. CIBS не разрешает arbitrary graph, floating point или per-sample neural
    inference.

## Проверка

После изменения документации проверить:

1. относительные ссылки;
2. статусы всех численных утверждений;
3. отсутствие смешения standalone Resonith и AV Bridge;
4. наличие первичных источников;
5. отсутствие персональных данных и секретов.
