# APA A5 | Независимый аудит и диспетчеризация BUILD-01 — 24.10.2026, цикл 14Z

**Срез:** 24.10.2026, 14:39 UTC / 17:39 МСК. **Цель:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE + GitHub read-only; Windows/Archicad не подключались; `MODEL_MODE_NOT_VERIFIABLE`.

## A. Приёмка входов и происхождение доказательств

Через GitHub connector повторно прочитаны четыре входных документа **этого цикла**, каждый с фактическим Git blob SHA. Ссылки указывают на исследовательскую ветку; для аудита сохранён SHA, так как ветка подвижна.

| Исполнитель | Файл / срез | Полученный Git blob SHA | Приёмка входа |
|---|---|---|---|
| R1 | [research-1-20261024T1355Z-BUILD01-CONTRACT-DRIFT-MATRIX.md](research-1-20261024T1355Z-BUILD01-CONTRACT-DRIFT-MATRIX.md), 13:55Z | `8b4e8ffa65b096b8c27b852692ef66f8c84cf771` | FOUND / SHA_MATCH |
| R2 | [research-2-20261024T14Z-GH-BRIDGE-ID-OWNERSHIP.md](research-2-20261024T14Z-GH-BRIDGE-ID-OWNERSHIP.md), 14Z | `6c5e5d3f83cef786f79e7e5ed97eb8a9bac665cc` | FOUND / SHA_MATCH |
| R3 | [research-3-2026-10-24T14Z-GH-GRAPHS-QA-CONTRACT.md](research-3-2026-10-24T14Z-GH-GRAPHS-QA-CONTRACT.md), 14Z | `6d28049eecf832fcde60e3da92356acf1753cac1` | FOUND / SHA_MATCH |
| I4 | [integrator-4-2026-10-24T1415Z-BUILD01-RUNTIME-GATE-CORRECTION.md](integrator-4-2026-10-24T1415Z-BUILD01-RUNTIME-GATE-CORRECTION.md), 14:15Z | `634c993599aab6a5ff059a4701ec8a841fa79992` | FOUND / SHA_MATCH |

Прочитаны также [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) (OPEN) и каноническая очередь `docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md`, blob `6f074693360231c5cb42ada815984a6b0dd504c0`. Предыдущий A5 13Z использован как контекст, **не** как подмена отчётов 14Z. **MISSING: 0/4.** Это подтверждение архивного наличия, не исполнение четырёх рабочих процедур на ноутбуке.

## B. Контрааудит CA-A5-14A — первоисточники, версии, лицензии

1. Официальный [Graphisoft Rhino–Grasshopper–Archicad Toolset](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) содержит **Grasshopper–Archicad 29 Live Connection build 3000** для Windows, поддержка **Rhino 7/8**, дата **01.10.2025**; **не совместим с Start Edition**. Это SOURCE по доступной сборке, **не** доказательство INSTALLED и не подтверждение полной автоматической синхронизации. Локальная совместимость с AC29 build5101 не проверялась запуском.
2. [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation) различает Archicad Add-On (команды JSON) и Grasshopper Plugin (work in progress), репозиторий под MIT. **Лицензию конкретного Yak-пакета и работоспособность в Rhino 8 нельзя выводить только из MIT репозитория.** R2 сообщает Yak 1.7.2 `rh7_21-any` без отдельной Rhino8 сборки в проверенном каталоге: статус **RHINO8_COMPATIBILITY_NOT_VERIFIED**, а не «не работает».
3. Локально заявленный Tapir Add-On **1.5.10** не идентифицирован через `GetAddOnVersion`/SHA APX/registered schema. R1 подтвердил расхождение frozen APA schema (`libraryPartName` у окон/дверей) с upstream исходником **1.5.9**. Это **SOURCE_SCHEMA_DRIFT**, но не установленная несовместимость локального бинарника. G2 остаётся BLOCKED_LOCAL_SCHEMA.
4. Rhino 8, Grasshopper, установленный GC29, лицензии Archicad/Rhino, Windows-порты, материалы/Favorites, библиотеки, активный PLN и локальный PR74 checkout не инспектировались. **INSTALLED=NOT_VERIFIED.**
5. Перепроверен immutable PR74 commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: `scripts/archicad_project_accelerator.py` blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`; `scripts/archicad_scene_run.py` blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`; `scripts/archicad_connected_components.py` blob `c5a99f59a90369ff622807574677cf11ca0a2225`. Нельзя считать этот immutable PR74 автоматически установленным или объединённым с PR126/131/149/162.

**Вердикт CA-A5-14A:** `SOURCE_PARTIAL_PASS / RUNTIME_AND_LOCAL_SCHEMA_UNVERIFIED`. Противоречий официальной таблице GC29 не обнаружено; лицензия/совместимость Yak Rhino8 и локальная Tapir 1.5.10 не повышаются до INSTALLED.

## C. Контрааудит CA-A5-14B — воспроизводимость, конкуренция writers и транзакционные границы

**Новое подтверждение исходным кодом, P0:** PR74 `run_project`, строки 438–447, при `schemaVersion=apa-authored-project/1` запрещает режим `offline`: требуется `preflight` или `execute` с callable transport, `guarded_project` и чтением реальных этажей/атрибутов. Следовательно, **G1 — read-only runtime preflight, не автономный offline compile**. `--preflight` не даёт права на native write; доказательство `G1_PASS` возможно лишь по фактическим квитанциям. В CLI `--output` **обязателен**, но каталог по этому пути **должен отсутствовать до запуска** (`mkdir(exist_ok=False)`). Входное задание должно быть новым и иметь разрешённый scratch target; не повторять исторический fixture.

**SceneWriter:** в `archicad_scene_run.py` строки 776–787 SQLite резервирует `scene_id`/`plan_hash`, запрещая неоднозначный повтор. Строки 856–893 подтверждают, что Slab с Basic material может требовать **CreateSlabs → readback → ModifySlabs**, то есть две native mutations внутри одного writer. При timeout/UNKNOWN — STOP, ledger + native GUID/material readback, **не повторять CREATE**. SQLite ≠ транзакция PLN.

**Native/identity:** Rhino `ObjectId`, GH `GH_Path`, APA `sourcePlanHash/stepId`, IFC `GlobalId`, Archicad GUID — разные пространства идентичности. Окна/двери должны быть привязаны к фактическому GUID ранее созданной стены; storyIndex и absolute Z сверяются с GetStories. Ручное удаление/изменение host Wall требует STOP и reconciliation. Параллельный Graphisoft GH Design Create/Modify и SceneWriter нарушают правило одного writer; GC Element Input/Deconstruct использовать только для read-only QA. Автоматическое GH→typed PR74 преобразование **NOT_FOUND_IN_CHECKED_PR74**; ручной перенос подтверждённых параметров в исходный JSON допустим как временный маршрут, но это не «трёхсторонняя синхронизация».

**Геометрия и нормативы:** R3 GH-BASE и GH-OPT — **спецификации графов, не созданные/исполненные .gh**. В `archicad_connected_components.py` строки 184–196 Roof verifier требует `SinglePlane`; upstream Tapir PolyRoof не доказывает поддержку через текущий PR74. Slab/Roof holes не проходят отдельный hole-loop readback в проверенных verifier. Rhino BREP и GH preview не доказывают Archicad native type; IFC/IDS проверяют отдельные аспекты и не заменяют BREP/СП экспертизу. Cross-app atomic rollback **NOT_FOUND**. Защита: отдельная санкционированная scratch PLN, snapshot, один writer, read-only reconciliation и восстановление только после допуска.

**Вердикт CA-A5-14B:** `ONE_WRITER_SOURCE_PLAUSIBLE / WHOLE_BUILD_NOT_REPRODUCED / G1_RUNTIME_REQUIRED`. Исторические успешные тесты APA не принимаются как новое BUILD-01. **Ни одного нового G0/G1/G3/G4/G5 receipt.**

## D. G0–G5 — контрольные ворота и закрывающие доказательства

| Gate | Требование для ГОТОВО | Факт |
|---|---|---|
| **G0** | Read-only manifest: AC29 build/port/PLN+SHA, разрешённая scratch path+SHA, Tapir GetAddOnVersion/APX SHA/command schema, GetStories, materials/Favorites/library parts, Rhino8 SR/units/tolerances/license, GC29, локальный PR74 immutable commit | **BLOCKED_RUNTIME** |
| **G1** | Реально запущенный на новом `apa-authored-project/1` **read-only `--preflight`** с Archicad; typed DAG/toposort, host bindings, schema pass, collision checks, sourcePlanHash/confirmPlanHash, inventory before=after, native writes=0, output receipt+SHA | **NOT_RUN**; «чистый offline» не поддерживается этим путём |
| **G2** | Фактическая зарегистрированная схема Tapir 1.5.10 и PR74 contract, 6 основных команд, story/host/material/library, SinglePlane Roof, один SceneWriter, отказные кейсы; unknown fields STOP | **SOURCE_PARTIAL / BLOCKED_LOCAL_SCHEMA** |
| **G3** | Только после отдельного допуска на конкретную scratch PLN/port/plan hash: native Create, уникальные GUID, type/story/host/material/BREP, SQLite ledger, no duplicate writers | **NOT_AUTHORIZED / NOT_RUN** |
| **G4** | Разрешённый GuardedSave, реальный Close/Open, независимый GUID/host/material/BREP readback, SHA и без потери элементов | **NOT_RUN** |
| **G5** | Другое задание/контур/высоты/проёмы на **другой** scratch PLN, повтор G1–G4 | **NOT_RUN** |

**Нативные элементы:** для базового первого здания обязательны Wall, Slab, SinglePlane Roof, Window, Door; Column/Beam только если реальный контракт/локальная установка подтвердят; PolyRoof, holes, сложные NURBS/IFC/СП — P1, не блокируют G1. **Нативный BIM не ACCEPTED**, пока нет полного GUID/type/story/host/material/BREP + Save/Open readback.

## E. Реестр блокеров — не расширять архитектуру

| ID | Владелец | Препятствие | Единственный следующий безопасный шаг | Закрытие |
|---|---|---|---|---|
| A5-B01 | Владелец ноутбука / I4 | Нет доступа к локальному runtime | Read-only G0 manifest по существующим командам | RUNTIME_READY или точный BLOCKED_reason |
| A5-B02 | I4 | G1 ошибочно назывался автономным offline | Зафиксировать `--preflight`+read-only Archicad, новый output path и authored target | Корректный G1 runbook и позднее реальный receipt |
| A5-B03 | R1 | Локальная схема Tapir/Favorites/Window-Door неизвестна | Таблица frozen vs upstream vs local с явным UNKNOWN | G2 local schema verified либо BLOCKED_LOCAL_SCHEMA |
| A5-B04 | R2 | GH→PR74 bridge не найден; разные GUID и writers | Закрыть поиск в проверенном PR74 как scoped NOT_FOUND; матрица STOP | 1 writer, 5 ID пространств, 4+ failure guards |
| A5-B05 | R3 | GH графы не исполнены, holes/PolyRoof не verified | Проверить спецификацию GH-BASE на строгий authored contract и ошибки | Graph I/O + 3 отрицательных случая без fake PASS |
| A5-B06 | I4 | Новый G1 fixture/receipt отсутствует | Подготовить один разрешаемый authored JSON и runbook без исполнения | Fixture/spec с нерешёнными параметрами явно, без заявленного OFFLINE_PASS |
| A5-B07 | I4 | Нет G3/G4 native receipts и rollback | Сформировать матрицу будущей readback-приёмки и STOP на UNKNOWN | Проверяемые критерии без LIVE |
| A5-B08 | A5 | Исследования могут бесконечно подменять BUILD | Каждый следующий аудит сравнивает B01–B07, не число SOURCE | При отсутствии G0/G1 прогресса `STALLED_EXTERNAL_DEPENDENCY` |

## F. Адресные поручения на следующий цикл

### R1 — native BIM, P0/98
**R1-15A:** прекратить повторное описание шести команд; составить **локальный G0 read-only инвентаризационный лист** с точными именами существующих Get-команд, expected полями, типами, местом сохранения, флагами STOP. Отдельно 1.5.10 frozen schema vs upstream 1.5.9 vs runtime UNKNOWN; Window/Door `libraryPartName/favoriteName`, Slab Basic, Roof SinglePlane. **ГОТОВО:** одна матрица `command → source → expected → runtime evidence → BLOCKED`, без новых API и без фиктивного INSTALLED.

### R2 — мосты/синхронизация, P0/97
**R2-15A:** завершить поиск готового GH→PR74 adapter в **точно названных доступных ветках/файлах**; если нет, выдать `NOT_FOUND_IN_SCOPED_BRANCHES` и не искать бесконечно. **ГОТОВО:** пути+commit для положительных находок либо конечный список проверенных веток. **R2-15B:** компактная таблица `create/update/delete/UNKNOWN/partial Slab/host drift/feedback loop` с владельцем GUID, существующим readback и STOP; не создавать sync.

### R3 — GH/геометрия/QA, P0/93
**R3-15A:** сопоставить **каждое** поле GH-BASE с уже существующим `apa-authored-project/1` (не с придуманным `nativeComponents`), отметить ручной перенос, единицы/допуски/стороны контуров/absolute Z; выделить 3 ошибки входа до G1. **ГОТОВО:** schema-compatible table, не .gh PASS. **R3-15B:** пять независимых QA verdicts `GH_GEOMETRY/AC_NATIVE/IFC_STRUCTURE/IDS_INFORMATION/NORMATIVE_REVIEW` и их минимальные доказательства; holes/PolyRoof оставить P1.

### I4 — исполнимый G0→G1, P0/100
**I4-15A:** выпустить **единственный** практический read-only runbook с immutable PR74 ref, проверкой реального scratch-port/target, CLI `--output` (каталог не существует), перечнем GetStories/GetAttributes/library/schema, ожидаемыми `plan.json/preflight.json/result.json/SHA256.json`, точными STOP условиями и границей nativeWriteCalls=0. **ГОТОВО:** документ воспроизводим на ноутбуке без новых writer/router; реальный запуск только после G0. **I4-15B:** подготовить одно новое `apa-authored-project/1` двухэтажное учебное задание с пометкой UNRESOLVED для material/story/origin/library до runtime; не выдавать за одобренный объект и не запускать. **ГОТОВО:** полный schema-check по существующему PR74 либо точный BLOCKED, а не обещание автоматического GH bridge.

## G. Административное решение и статусы

1. **P0 — G0, затем G1.** Новые исследования PolyRoof/IFC/плагинов не повышают приёмку и не должны блокировать базовое двухэтажное здание.
2. **Коррекция G1 принята:** `READ_ONLY_PREFLIGHT_REQUIRES_ARCHICAD_RUNTIME`; не требовать невозможного полностью автономного authored offline.
3. **Каноническую очередь НЕ менять:** `NEXT_RESEARCH_PRIORITIES.md` прочитан, SHA сохранён; административная директива и риск перезаписи требуют отдельного согласования. Задания только в этом append-only hourly отчёте.
4. **SOURCE:** 4/4 входных отчёта найдены и SHA совпали; два контрааудита на исходниках/официальной документации. **OFFLINE:** 0 новых запусков; **BUILD:** 0; **INSTALLED:** NOT_VERIFIED; **LIVE:** 0 новых; **ACCEPTED:** 0. **NOT_FOUND (ограниченный объём):** GH→PR74 auto bridge, PR74 PolyRoof/ModifyRoofs, hole-loop verifier, атомарный cross-app sync/rollback, Rhino8 distribution Tapir GH в проверенном каталоге.
5. **Ничего не устанавливалось и не менялось:** main, код, PLN/APX, PR, merge, платные API, Work/Codex/Arena, native LIVE. Публикуется только этот исследовательский markdown в разрешённой ветке. При невозможности readback публикации — `WRITE_BLOCKED`.

**Итог:** `REPORTS_4_OF_4_FOUND / COUNTERAUDITS_2 / G0_BLOCKED_RUNTIME / G1_NOT_RUN / BUILD01_NOT_ACCEPTED / STALLED_EXTERNAL_DEPENDENCY`. **MODEL_MODE_NOT_VERIFIABLE.**
