# APA №2 — 2026-10-24 00Z — BUILD-01: готовая интеграция и идентичность документов
**Только SOURCE.** Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED нет. MODEL_MODE_NOT_VERIFIABLE.

## Новый инженерный результат
Вместо установки двух новых alpha MCP предлагается использовать уже существующий контур: **Rhino 8 штатный Query Model Objects / Model Object → Grasshopper → замороженный JSON (jSwan лишь SOURCE_CANDIDATE) → PR74 authored preflight → BIM Graph → единственный SceneWriter/SQLite → Tapir → Archicad 29 → GuardedSave/Close/Reopen → независимый IFC/BREP readback.** Это воспроизводимый документарный маршрут, а НЕ выполненная сборка и НЕ автоматическая трёхсторонняя синхронизация.

## G0: две независимые идентичности, одна проверка проекта
1. **Archicad:** явный порт 127.0.0.1:19723–19727; фактические product/build/lang; GetProjectInfo path/name/isUntitled/isTeamwork; GetStories index/floorId/level; GetAddOnVersion; фактические registered commands/schema и SHA APX; SHA защищённой scratch PLN; expected project path/name/hash и SceneWriter ledger/runId. Совпадение порта или имени файла НЕ доказывает идентичность PLN. Если путь не возвращён, STOP.
2. **Rhino/GH:** точный .3dm path/name/SHA; active Rhino document; Rhino8 SR, units, origin, Rhino object GUID; точный .gh path/SHA; referenced geometry или internalized-only; GH component versions, выбранное GH definition, Solver state, GH Synchronize=false. Rhino GUID не равен Archicad GUID.
3. **Межпрограммная геометрия:** meters, local origin, survey/map conversion (orientation and scale), native story floorId/index/level, Wall relative zCoordinate против Slab absolute level, hostWall, materials/Favorites/library IDs. При неизвестной геопривязке STOP; north не заменяет XAxisAbscissa/XAxisOrdinate.
4. **Ownership:** APA-owned элементы изменяет только SceneWriter; GH-owned — только Graphisoft Live Connection в изолированной области после отдельного разрешения; Rhino/GH только источник параметрической геометрии для APA. При двух writers, изменении после freeze, удалении, UNKNOWN или timeout — STOP, read-only reconciliation, без повторного CREATE.

## Новые инструменты №1: решение №2
- **ArchBench Rhino MCP v0.1.0-alpha.3, MIT:** привязывает мост к Rhino-документу запуска; статус/контекст READ. Rhino8 Python3 и Node22+; 16 fixture tests, native qualification pending. Опциональные скрипты unsandboxed, требуют host opt-in, env flag и confirm:true. Решение: НЕ УСТАНАВЛИВАТЬ; штатные Rhino8 GH Query/Model Object и контроль .3dm достаточны для G1 READ.
- **ArchBench Archicad MCP v0.1.0-alpha.3, MIT:** явный ARCHICAD_MCP_PORT 19723–19743, no port scanning/retry; status/selection READ; 7 fixture tests, native qualification pending. Верный порт не идентифицирует PLN, нет rollback. Решение: НЕ УСТАНАВЛИВАТЬ, существующий APA guard лучше соответствует G0. Не включать arbitrary archicad_call_command.
- **Graphisoft GH–AC29 Live Connection build3000:** официальный бесплатный add-on, Windows Rhino7/8, датирован 01.10.2025; лицензии AC29/Rhino8 отдельно. Build3000 add-on НЕ равен AC29 build5101. GH Synchronize=TRUE — прямая запись GH→AC, FALSE — Null/нет генерации. Частичное AC→GH чтение не даёт общую транзакцию с APA. INSTALLED_NOT_VERIFIED.
- **Tapir pinned 1.5.10 MIT:** 262 SOURCE-команды; runtime APX и command inventory не подтверждены. Не обновлять на 1.7.x без разрешения. Rhino8 GH Model Object позволяет работать с атрибутами и материалами, но Bake пишет в Rhino, не нативный Archicad.

## G0–G5, воспроизводимая последовательность
**G0 READ:** actual port/PLN/stories/APX SHA/commands + .3dm/.gh identity, libraries/materials. При любом неизвестном критичном поле BLOCKED_RUNTIME.
**G1 PREPARE:** GH Synchronize=false; сохранить .gh+.3dm; freeze Solver; сформировать JSON с lowercase x/y, meters, правильными массивами и типами без null; проверить story bindings, hostWall и материалы. Запустить существующий PR74 --preflight с реальным READ-only Archicad и точным targetProjectPath; нужен фактический typed DAG/planHash, иначе OFFLINE=0.
**G2 CONTRACT:** CreateWalls/Slabs/Columns/SinglePlane Roof/Windows/Doors по существующему PR74; Beam и MultiPlane Roof есть в Tapir, но authored binding не доказан. SetStories — WRITE и запрещён. Проверять GUID/type/floor/material/holes/host/SEO/BREP.
**G3:** только по отдельному разрешению для новой scratch PLN, порта, planHash и ledger. Единственный SceneWriter; UNKNOWN STOP, no retry CREATE.
**G4:** GuardedSave → GUI Close → no-open → Reopen → GUID/type/story/material/host/BREP/SEO; IFC Publisher с фиксированными view/translator/Hotlink Preferences → IfcOpenShell independent QA. IFC GlobalId, Rhino GUID, native Archicad GUID не взаимозаменяемы. Откат защищённой PLN+.gh+.3dm+JSON+библиотекой, не только Undo.
**G5:** другое исходное задание и другая изолированная модель, иначе BOUNDED_DEMO.

## Четыре конкретных блокера
I00-01 BLOCKED_RUNTIME: нет живого G0 identity receipt. ГОТОВО = реальный read-only manifest с портом/PLN/build/APX SHA/командами.
I00-02 GH_HANDOFF_NOT_PROVEN: не выполнен JSON→PR74 preflight. ГОТОВО = фактический typed DAG/planHash, zero writes.
I00-03 MULTIPLANE_NOT_WIRED: Tapir CreateRoofs MultiPlane есть, PR74 authored поддерживает только ограниченный SinglePlane. ГОТОВО = existing writer + native readback; сейчас NOT_FOUND.
I00-04 TRIAD_SYNC_NOT_FOUND: нет общего owner/version/conflict/rollback. ГОТОВО = native GUID-preserving bidirectional LIVE, delete/loop/conflict и Save/Open; сейчас NOT_FOUND.

## Проверенные источники
BUILD-01 https://github.com/dvikt33-ux/safe-bim-layer/issues/192
PR74 immutable https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/APA_MODEL_FIRST_BUILDING.md
Tapir pinned https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
NEXT https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
TRIAD PIVOT https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
№1 00Z https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T00Z-TRIAD-DOCUMENT-BOUND-MCP-GATES.md
№3 20.10 18Z https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md
Матрица61: blob 9cb5e6f2a59f80762cc77073eeb10404829af75a; PROJECT_PLAN rev182 не извлекался, не менялся.
