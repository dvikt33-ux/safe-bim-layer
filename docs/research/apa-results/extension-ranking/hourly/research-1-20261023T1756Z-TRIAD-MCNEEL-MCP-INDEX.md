# APA №1 — 23.10.2026 17:56Z — Rhino MCP Platform: новый готовый инструмент для BUILD-01

## Влияние на BUILD-01 / конкретный результат
**НОВОЕ P0 SOURCE:** найден официальный бесплатный [McNeel Rhino MCP Platform](https://mcneel.github.io/RhinoAI/) — готовый AI/MCP-мост для Rhino 8 и Grasshopper 1 без разработки собственного Rhino bridge. [Yak v0.3.0 от 29.09.2026](https://rhinopackages.github.io/package/Rhino-MCP-Platform) поддерживает Windows Rhino 8 с пакетной меткой `rh8_19-win`. [MIT-репозиторий](https://github.com/mcneel/RhinoAI) и [официальная документация](https://mcneel.github.io/RhinoAI/docs/) подтверждают создание Rhino geometry и построение GH definitions через MCP. **В матрице 61 это решение отсутствовало** (там есть Graphisoft Grasshopper, но нет Rhino-MCP-Platform). Это потенциально снимает необходимость создавать собственный Rhino/GH AI bridge, но не решает автоматический native Archicad write.

**P0-контрааудит:** [McNeel прямо предупреждает](https://mcneel.github.io/RhinoAI/docs/troubleshooting/), что при нескольких окнах Rhino агент может изменить не тот документ; [privacy](https://github.com/mcneel/RhinoAI/blob/rhino-9.x/PRIVACY.md) указывает доступ к run_command/run_python/run_csharp/open_doc/save_doc и передачу результатов AI-клиенту. Поэтому до G0 read-only проверка точного Rhino window/.3dm и allowlist обязательны. Запретить новый writer; для APA-owned элементов использовать уже документированный №2 GH→jSwan→typed JSON→PR74→SceneWriter.

## Новые карточки
1. **C1756-01 P0**: McNeel Rhino MCP — AI→Rhino commands/geometry, без собственного моста. Важно: Windows Rhino8 package `rh8_19`, локальная версия неизвестна.
2. **C1756-02 P0**: McNeel MCP → создание/редактирование GH1 canvas; output только в существующий APA JSON compiler, без второго native writer.
3. **C1756-03 P0**: Rhino `-Grasshopper Solver Disable/Enable` + Graphisoft `Synchronize Boolean Toggle` — штатный gate против частичной отправки; не атомарная транзакция.
4. **C1756-04 P0**: McNeel target-window и privacy preflight — исключить неверный .3dm и непредусмотренный запуск кода/запись файлов.
5. **C1756-05 P1 HOLD**: [Elephant](https://dfma.tools/products/elephant/) — free Rhino identity/lineage/JSON diff, но заявляет **автоматический git add/commit при сохранении в tracked repo**. Не устанавливать и не включать без изоляции; Elephant UUID не равен Archicad GUID.
6. **C1756-06 P2 EXCLUDE_FREE_P0**: [ggRhinoIFC](https://technical.geometrygym.com/getting-started/licencing) — IFC fallback, но trial 30 дней/академическая или коммерческая лицензия, не постоянный бесплатный стек. IFC обмен не native same-GUID sync.

## BUILD-01 status (новый маршрут, не исторический PR74)
| Gate | Результат |
|---|---|
| G0 runtime: Rhino8 build/MCP/APX/PLN/GH link/target | **BLOCKED_RUNTIME** |
| G1 offline whole-building compiler + GH→JSON | **NOT_RUN** |
| G2 exact local native command schema | **SOURCE_ONLY** |
| G3 native CREATE/MODIFY | **NOT_AUTHORIZED** |
| G4 Save/Close/Reopen + GUID/BREP/library | **NOT_RUN** |
| G5 second distinct building | **NOT_RUN** |

SOURCE=30 предметных утверждений, 6 карточек, 2 контрааудита; **OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0**. FULL_THREE_WAY_SYNC=NOT_FOUND_IN_CHECKED_SOURCES. Никакого 100× benchmark.

## Архив и SHA (create_file → fetch_file → exact content readback)
| Файл | Git commit | Git blob SHA | Символов | Точное совпадение |
|---|---|---|---:|---|
| [research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-SOURCE.md](research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-SOURCE.md) | `1e467cdf3f1fc1a237abe30359898ac98fdecf84` | `19f21f3a75ba8bd267d9f282a96a3266856a7cd1` | 8488 | true |
| [research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-CARDS.md](research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-CARDS.md) | `2008625400810959939b19252423ff4ba397fbdf` | `4c6ae0d957160ebddd1e158ef988b31a18a59001` | 7161 | true |
| [research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-AUDITS.md](research-1-20261023T1756Z-TRIAD-MCNEEL-MCP-AUDITS.md) | `82a23accb726ec0dd0685cc4d75c0f0974517ad4` | `df7f558cad30f82d51beef1c083ea52ec29de835` | 3996 | true |

## Прочитанные внутренние материалы
- [NEXT_RESEARCH_PRIORITIES.md](../NEXT_RESEARCH_PRIORITIES.md), blob `6f074693360231c5cb42ada815984a6b0dd504c0`.
- [TRIAD-PIVOT](research-1-20261023T11Z-TRIAD-PIVOT.md), blob `896fa3af0953468ca58fca710f32cb926504f582`.
- [№1 17:23Z](research-1-20261023T1723Z-TRIAD-OWNERSHIP-INDEX.md), blob `972c7597e241d0f41a2492011e7ede6b7a42311e`.
- [№2 17Z](research-2-integration-2026-10-23T17Z-triad-report.md), blob `3d7326bcbfe08359efedc0d62615277e289e2b9d`.
- [Матрица 61](../priority_matrix_20261018.json), blob `9cb5e6f2a59f80762cc77073eeb10404829af75a`, count=items.length=61.
- [Последний непосредственно прочитанный №3 — 20.10 07Z](audit-2026-10-20-07.md), blob `40742adbf7ec945b31d125aac6912d95e5f07920`. Более свежий №3 не установлен.
- [Issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) и [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) прочитаны; исторический PROJECT_PLAN rev182 только чтение косвенно через NEXT, сам файл не извлечён.

## Адресное поручение №2
В следующем инженерном SOURCE-проходе документировать совместимость локальной сборки Rhino 8 с Rhino-MCP-Platform 0.3.0 (`rh8_19-win`), MCPConnect, read-only tool inventory, ограничения на arbitrary-code/file tools, точный target window/.3dm и путь GH1→jSwan→PR74. Показать, какие операции полностью заменяют самописный мост, а какие остаются NOT_FOUND. Не запускать установки, Work/Codex/Arena, платные API или LIVE.

Никаких изменений main/PLN/APX/кода/установленных расширений, NEXT и canonical PROJECT_PLAN. Исследование SOURCE_ONLY; MODEL_MODE_NOT_VERIFIABLE.
