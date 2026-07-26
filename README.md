# Resonith

**Resonith** — утверждённое имя самостоятельного аудиокодека непрерывного
акустического поля. Внутренняя архитектура называется
**MAF — Memory-oriented Acoustic Field**.

> **Resonith — encode acoustic causes, not repeated waveform blocks.**

Каноническая формула:

\[
Audio(t)=
RenderAcoustic(Emitters_t,Trajectories_t,RoomState_t)
+TruthInnovation_t
+OptionalPerceptualDetail_t.
\]

Resonith кодирует долгоживущие coherent, stochastic и transient acoustic
atoms. Encoder может использовать score transcription, source separation,
instrument recognition и огромные neural teachers, но нормативный decoder
исполняет только малую bounded integer acoustic ISA.

**ACCEPTED:** Main-0 включает
**CIBS — Cached Integer Basis Synthesis**. Компактный latent один раз
синтезируется fixed integer graph-ом в immutable timbre/filter basis и затем
обслуживает обычный лёгкий sample loop.

Resonith не зависит от SceneLith Video и декодируется самостоятельно. Их
специализированная связь описана отдельно в
`G:\SceneLith-AV-Bridge`.

## Документы

- [Индекс](docs/INDEX.md)
- [Устав и инварианты](docs/00_CHARTER_AND_NORTH_STAR.md)
- [Архитектура MAF](docs/01_MAF_ARCHITECTURE.md)
- [Encoder-компилятор](docs/02_ENCODER_COMPILER.md)
- [Классическая музыка и цели](docs/03_CLASSICAL_MUSIC_TARGETS.md)
- [Риски и kill-gates](docs/04_RISKS_AND_KILL_GATES.md)
- [Название и IP](docs/05_NAMING_AND_IP.md)
- [Журнал решений](docs/06_DECISION_LOG.md)
- [План первой реализации](docs/07_IMPLEMENTATION_ROADMAP.md)
- [Оставшиеся направления и прогноз против codecs](docs/08_RESEARCH_DIRECTIONS_AND_CODEC_TARGETS.md)
- [Нормативный дизайн CIBS](docs/09_CIBS_NORMATIVE_DESIGN.md)
- [MAF-P0: первый исполнимый codec](docs/10_MAF_P0_IMPLEMENTATION.md)
- [Источники](docs/REFERENCES.md)
- [Нормативный черновик Resonith-0](spec/Resonith-0.md)

Все показатели compression и complexity являются целями или гипотезами,
пока не подтверждены воспроизводимыми тестами и MUSHRA.

## GitHub-синхронизация

Репозиторий использует безопасный `post-commit` hook: каждый явно созданный
локальный commit автоматически отправляется в `origin`. Hook никогда сам не
добавляет файлы и не создаёт commits. После нового clone режим включается
командой:

```powershell
.\scripts\enable-auto-sync.ps1
```

Для явного `fetch + pull --rebase + push` используется:

```powershell
.\scripts\sync.ps1
```
