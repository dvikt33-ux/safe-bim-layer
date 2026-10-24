# APA I4 — интеграционный протокол BUILD-01: исправление G1, контракты и практический маршрут
**Срез:** 24.10.2026, 14:15 UTC / 17:15 МСК. **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Issue:** #192. **Роль:** I4. **Режим:** SOURCE_ONLY, без доступа к ноутбуку. **MODEL_MODE_NOT_VERIFIABLE.**

## 0. Входы и достоверность
Фактически повторно прочитаны через GitHub connector:
- **R1 13:55Z:** `research-1-20261024T1355Z-BUILD01-CONTRACT-DRIFT-MATRIX.md`, blob `8b4e8ffa65b096b8c27b852692ef66f8c84cf771`; 15 SOURCE-единиц, матрица 6 native commands.
- **R2 14Z:** `research-2-20261024T14Z-GH-BRIDGE-ID-OWNERSHIP.md`, blob `6c5e5d3f83cef786f79e7e5ed97eb8a9bac665cc`; 10 маршрутов, ownership/unknown/partial mutation.
- **R3 14Z:** `research-3-2026-10-24T14Z-GH-GRAPHS-QA-CONTRACT.md`, blob `6d28049eecf832fcde60e3da92356acf1753cac1`; GH-BASE, GH-OPT и QA.
- **A5 13Z:** `audit-a5-2026-10-24T13Z-BUILD01-TRIAD-DISPATCH.md`, blob `71e752a11e8324086d9ac2d9cec98de01bed8204`. Это последний уже опубликованный аудит, доступный на момент среза; **A5 14Z PENDING**, а не подменён старым.
- **Issue #192:** https://github.com/dvikt33-ux/safe-bim-layer/issues/192 (OPEN). **Каноническая очередь:** `docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md`, blob `6f074693360231c5cb42ada815984a6b0dd504c0` (READ_ONLY).
- **PR74 immutable commit** `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: лично перечитаны `scripts/archicad_project_accelerator.py` (blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`), `scripts/archicad_authored_native_plan.py` (blob `f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7`), `scripts/archicad_scene_run.py` (blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`) и `examples/accelerator/model-first-building.json` (blob `e192fbb31bc872d751c41aa7132f0a4981755051`).
- Внешние первоисточники: Graphisoft https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ (29 Live Connection build 3000, Rhino 7/8, 01.10.2025); McNeel https://developer.rhino3d.com/en/guides/yak/the-anatomy-of-a-package/ ; каталог https://rhinopackages.github.io/package/tapir (GH Yak 1.7.2, 19.10.2026, rh7_21-only, no Rhino8+ build). Эти SOURCE не доказывают локальную установку.

## 1. P0 НОВОЕ уточнение из исходного кода: G1 не является полностью автономным offline для authored intent
**Критическая коррекция к предыдущим формулировкам I4/A5.** `run_project` в PR74, строки 438–447: при `schemaVersion="apa-authored-project/1"` режим `offline` **явно запрещён**; требуется `mode in {"preflight","execute"}`, callable transport, `RUN.guarded_project(api)`, затем `compile_authored_intent(...,api)`. `compile_authored_intent` (стр. 262–282) требует targetProjectPath == `RUN.EXPECTED_PATH`, реальных `GetStories`, `GetAttributesByType`, привязок CSE/материалов. `archicad_authored_native_plan.compile_candidate` (стр. 24–72) также вызывает READ-only API для этажей/материалов и проверяет неизменность project identity. Следовательно:
1. **G1 = NO_NATIVE_WRITE_PREFLIGHT, но с доступным Archicad и живым READ-only API.** Без G0 он не запускается как реальный `OFFLINE_PASS`.
2. У PR74 есть `offline` режим для *другого* `archicad-project-intent/1` (pavilion/building-shell), но это **не эквивалент** нового authored двухэтажного BUILD-01. Нельзя переименовать fixture pass в G1.
3. `--preflight` фиксирует локальные evidence файлы, но `EvidenceAPI` (стр. 345–374) запрещает native mutation при `execute=False`; в `run_project` (стр. 522–523) read-only инвентаризация должна оставаться неизменной. Это **проектная гарантия кода**, не результат локального прогона.
4. CLI `--output` создаёт **новый несуществующий каталог** (`mkdir(...,exist_ok=False)`), поэтому нельзя переиспользовать старый output. `--scratch-port` и `--isolated-port` привязывают только заранее закодированные test PLN; произвольный путь нельзя подменять CLI.
**Вердикт:** `G1_AUTHORED_REQUIRES_READONLY_RUNTIME`, `G1=NOT_RUN`, `G0=BLOCKED_RUNTIME`. Это важнее очередной SOURCE-инвентаризации плагинов. A5 должен исправить формулировку «полностью офлайн» на «без нативной записи, с обязательным read-only runtime».

## 2. Единственная исполнимая архитектура без второго writer
`Rhino 8` → `Grasshopper 1` (геометрия/ограничения/preview; **без GH Design Create, Bake, Push, Purge**) → **ручное утверждение и перенос проверенных параметров в уже существующий** `apa-authored-project/1` → `PR74 compile_authored_intent` + `archicad_authored_native_plan` + `BIM Graph.compile_graph` → **один** `SceneWriter` + `SQLite durable ledger` → `Tapir Archicad Add-On` → `Archicad 29 native BIM`.

**Обратный путь:** Archicad `GetDetailsOfElements / GetAllElements / GetStories / GetModelDumpV1` → read-only QA + официальный `Grasshopper–Archicad Live Connection 29` (Element Input / Deconstruct / Story reference; не подключать выход к Design writer) → Rhino/GH reference. **Это не автоматическая трёхсторонняя синхронизация.** GH→typed JSON exporter в проверенном PR74 **NOT_FOUND**; ручной перенос не выдавать за готовый мост. Rhino.Inside Archicad host **NOT_FOUND в подтверждённом scope**; не включать в установочный минимум.

**Ownership:** Archicad владеет нативной BIM-геометрией и internal GUID; APA `sourcePlanHash`/`sceneId`/`stepId` владеют идентичностью задания и журналом, **не** native GUID; GH `GH_Path` и Rhino `ObjectId` — отдельные идентификаторы; IFC `GlobalId` не приравнивать к Archicad internal GUID. Нативная запись только SceneWriter после отдельного разрешения G3.

## 3. Версии, установка и проверка: точный порядок (НЕ ВЫПОЛНЕН)
| Порядок | Компонент | Что действительно нужно | Gate / блокер |
|---|---|---|---|
| 1 | Archicad 29 build 5101, Windows 11 | Установленная действующая лицензия, `About`, порт/активный PLN; только read-only snapshot | G0, **не подтверждено** |
| 2 | Tapir Add-On, локально заявленный 1.5.10 | Проверить `GetAddOnVersion`, зарегистрированные команды/схемы, SHA APX; frozen schema не считать равной бинарнику | G0/G2, **не подтверждено** |
| 3 | APA checkout PR74 + существующие зависимости | Зафиксировать immutable commit локального дерева; `archicad_project_accelerator.py`, `archicad_bim_graph.py`, `archicad_scene_run.py`, schema и ledger; отдельные PR126/131/149/162 не считать автоматически установленными | G0, **не подтверждено** |
| 4 | Rhino 8 + встроенный Grasshopper | Проверить Rhino 8 Service Release, лицензию, units/absolute/angle tolerance, исходные `.3dm/.gh` и SHA | G0, **не подтверждено** |
| 5 | Graphisoft Grasshopper–Archicad **29** Live Connection **build 3000** | Официальная Windows-сборка для Rhino 7/8; при отсутствии установить **только после отдельного разрешения**; для BUILD-01 read-only GH branch | G0/G2, SOURCE подтвержден |
| 6 | Дополнительные GH плагины | **Не обязательны**: встроенных GH компонентов достаточно для GH-BASE. Tapir GH Yak 1.7.2 имеет только `rh7_21-any` в проверенном каталоге; совместимый Rhino8 distribution **NOT_FOUND**. Rhino.Inside Archicad не доказан | Исключены из обязательного комплекта |
| 7 | IfcOpenShell/IfcTester | Опциональный независимый IFC/IDS QA **после** native модели; IDS ≠ геометрия и ≠ полный СП-аудит | G4 optional; не блокирует G1 |

Порядок *инвентаризации* обязателен; фактическую установку не выполняли. Сохранить локальные лицензии, сборки, SHA, не запускать обновления Archicad 30 параллельно с AC29.

## 4. Контракты операций и точки проверки
| Операция / ввод | Native command / existing route | Обязательные инварианты и readback | Статус |
|---|---|---|---|
| Stories | `GetStories` → `storyBindings` | `nativeIndex, floorId, level, label`; authored story heights 2.4–4.5 м и непротиворечивый абсолютный Z | SOURCE, runtime unknown |
| Wall | `CreateWalls` → SceneWriter | XY begin/end ненулевые, floorIndex, height/thickness, Basic/material при запросе; GUID/type/story/geometry | SOURCE |
| Slab | `CreateSlabs` → SceneWriter; при material binding **отдельный `ModifySlabs`** | absolute level, polygon outer, floorIndex, thickness; GUID/Basic/material; holes verifier не доказывает | SOURCE_PARTIAL |
| Column | `CreateColumns` через `nativeComponents` | координаты XYZ, floorIndex, явные height/width/depth для verifier; GUID/segments/material | SOURCE_PARTIAL |
| Beam | `CreateBeams` opt-in connected adapter | typed beam + segment/host/BREP; не входит в allowlist authored nativeComponents PR74 | SOURCE_OPTIONAL |
| SinglePlane Roof | `CreateRoofs` c `pivotLine`, Basic, material; opt-in roof adapter | floorIndex, XY outline, level/angle/pivot/thickness, native SinglePlane readback | SOURCE_PARTIAL |
| MultiPlane Roof | upstream Tapir `CreateRoofs` без `pivotLine` / `ModifyRoofs` | upstream API_PolyRoofID есть, но PR74 требует pivotLine, verifier SinglePlane, ModifyRoofs не разрешён в SceneWriter | **PR74_ROUTE_NOT_FOUND** |
| Window/Door | `CreateWindows/CreateDoors` после Wall через `$createdGuid` | ownerWallId, centerOffset, width/height/sillHeight, libpart/Favorite/marker; host GUID + story readback | SOURCE_PARTIAL; local schema drift |
| GH parameters | `GH-BASE` → существующий `apa-authored-project/1` | units meters, abs origin, story levels, roof pivot, hosted refs; **только ручное сопоставление** | AUTO_BRIDGE_NOT_FOUND |
| Rhino/IFC QA | GH BREP/AC readback/IFC export | геометрические инварианты, native GUID и IFC GlobalId отдельно; IDS только информация | SOURCE; no LIVE |

**Точная граница authored JSON:** `compile_authored_intent` требует `schemaVersion, projectId, units, brief, cseCandidate, layout, storyHeights`; дополнительные ключи только `wallBasicMaterialName,nativeComponents,nativeGeometryAudit,junctionPolicy,nativeRoofJunctions,structuralFunctions`. `nativeComponents` разрешает `CreateColumns,CreateDoors,CreateWindows,CreateWalls,CreateRoofs` (НЕ CreateBeams/Slabs). Не вводить `source_key`, `slab_holes`, `roof_facets` как новые top-level поля. `CreateSlabs` компилируется из layout через `archicad_authored_native_plan`. Для окна/двери четыре поля явно, host только `$createdGuid` созданной стены. Frozen schema Window/Door `libraryPartName` не доказана upstream Tapir 1.5.9 — G2 local runtime gate.

## 5. GH-BASE / GH-OPT: что реально передавать I4
**GH-BASE (P0):** вход `W,D,Z0,Z1,H0,H1,Twall,Tslab,originXY,storyIndex,materialGuid,libraryBinding,units,tolerances`; штатные `Construct Point → Polyline → Area/Boundary Surfaces → Move → Line/Length`. Выход — проверенные `story_levels, bearing_lines, slab_outer_polygons, roof_single_outline_pivot_angle, hosted_openings, geometry_checks`. Условия: замкнутые контуры, положительные толщины/длины, конечные XYZ, точные этажные отметки. Размеры 12×8×(3.2+3.2) м — **учебный пример**, НЕ утверждённый проект и НЕ допустимый origin. До G0 `originXY,storyIndex,materialGuid,libraryBinding` = UNRESOLVED. `.gh` **не создан и не исполнен**.
**GH-OPT (P1):** outer slab 12×8, inner 2×2 → теоретически 92 м²; два roof facets с `eaveZ=6.4,ridgeZ=8.0` → теоретический pitch 21.8014°. Это только geometry QA: GH Slab holes/две фасеты НЕ превращаются автоматически в native Slab holes/PolyRoof через PR74. Оставить optional. Отрицательные N1–N8 из R3 пока **НЕ ИСПОЛНЕНЫ**.

## 6. G0–G5: точные критерии ГОТОВО, без ложного повышения
| Gate | Критерий ГОТОВО | Факт 14:15Z |
|---|---|---|
| **G0 READ** | Manifest: AC29 build/port/current PLN path+SHA, scratch path+SHA, Tapir Add-On/APX SHA/GetAddOnVersion/registered schema, GetStories, Favorites/library/material GUID, Rhino8 SR/license/units/tolerances, `.gh/.3dm` SHA, GC29 build, local APA checkout commit | **BLOCKED_RUNTIME** |
| **G1 NO-WRITE PREFLIGHT** | На **новом** approved `apa-authored-project/1` реально выполнен PR74 `--preflight` с доступным READ-only AC; typed DAG/toposort, host refs, schema, collisions, `sourcePlanHash`, `confirmPlanHash`, before/after inventory unchanged, nativeWriteCalls=0 | **NOT_RUN; G0 REQUIRED** |
| **G2 SCHEMA** | Фактическая локальная Tapir schema и APX сверены с PR74; story/host/material/library/roof/slab контракт зафиксирован, single SceneWriter/SQLite; все неизвестные поля STOP | **SOURCE_PARTIAL** |
| **G3 CREATE** | Отдельное письменное разрешение на exact scratch PLN/port/plan hash; SceneWriter SQLite intent-before-write, actual native GUID/type/story/host/material/BREP receipts, no duplicates; не делать GH Create | **NOT_AUTHORIZED / NOT_RUN** |
| **G4 SAVE/REOPEN** | Отдельно санкционированный GuardedSave → GUI Close → no-open check → Open → независимый native inventory/GUID/host/material/geometry/BREP diff + immutable receipts; IFC/IDS при необходимости отдельно | **NOT_RUN** |
| **G5 GENERALIZE** | Второй иной `apa-authored-project/1`, новый scratch, другой footprint/высоты/проёмы, повтор G1–G4, без replay прежнего sceneId | **NOT_RUN** |

**Безопасная будущая команда G1** (ПРИМЕР, **НЕ ВЫПОЛНЯТЬ до G0**; в PowerShell подставить реальные, утверждённые пути и порт; `--output` должен отсутствовать до запуска):
```powershell
py scripts/archicad_project_accelerator.py --intent "<NEW_APPROVED_INTENT.json>" --schema "schemas/tapir-live-1.5.10/tapir-scene-live.json" --output "<NEW_EMPTY_EVIDENCE_DIRECTORY>" --preflight --scratch-port <APPROVED_PORT>
```
`--preflight` делает только разрешённые чтения, но требует доступного Archicad и точно совпадающего `brief.targetProjectPath` с `RUN.EXPECTED_PATH` для выбранной scratch; исторический `examples/accelerator/model-first-building.json` нельзя запускать на чужом target без адаптации и допуска. Примерная команда **не доказывает** runtime и не выдаётся за выполненную. `--execute` здесь сознательно не приводится.

## 7. Конфликты, rollback и независимый QA
- **Writer ownership:** GH Design Create/Modify/Synchronize не подключать к native записи; AC→GH read-only. `Synchronize=False` и Null не гарантируют удаление ранее созданного native элемента.
- **Unknown CREATE:** SQLite `ATTEMPTED` перед API, уникальность `scene_id/plan_hash` (`archicad_scene_run.py:776–787`). Timeout/UNKNOWN → STOP, read-only native GUID inventory и ledger reconciliation, **не повторять CREATE** и не генерировать новый sceneId для обхода.
- **Partial Slab:** `CreateSlabs → GetDetailsOfElements → ModifySlabs` (стр. 856–893) — **две** native mutations. Если ModifySlabs UNKNOWN, сохранить исходный Slab GUID и material status, запретить повтор CreateSlabs.
- **Host drift/delete:** при ручном удалении/перемещении стены проверить host для Window/Door; не восстанавливать автоматически.
- **Feedback cycle:** GH Element Input/Deconstruct → Design output = потенциальный цикл; write branch разорван.
- **Rollback:** нет подтверждённой атомарной транзакции Rhino+GH+Archicad. Только санкционированная отдельная scratch-копия до G3, freeze всех writers, read-only reconcile и отдельно утверждённое восстановление. SQLite ledger ≠ AC Undo.
- **QA независимые verdicts:** `GH_GEOMETRY` (planarity, loops, tolerances, normals, BREP solids only when applicable), `AC_NATIVE` (GUID/type/story/host/material/BREP), `IFC_STRUCTURE` (IfcWall/Slab/Roof/Window/Door, storeys, voids/fills, GlobalId отдельно), `IDS_INFORMATION` (информационные правила), `NORMATIVE_REVIEW` (применимый СП/редакция/пункт/ответственный). Нельзя ставить COMPLIANT по одному IFC или GH preview.

## 8. Точные блокеры и адресные действия A5
| ID | Приоритет / владелец | Блокер → следующее действие → ГОТОВО |
|---|---|---|
| **I4-B01** | 100 / A5→владелец ноутбука | G0 runtime неизвестен → read-only manifest + exact hashes → `RUNTIME_READY` или `BLOCKED_<reason>` |
| **I4-B02** | 100 / A5→I4 | Неверное представление о «чистом offline authored» → закрепить G1 как `READ_ONLY_PREFLIGHT_REQUIRES_RUNTIME` → согласованная gate-формулировка и фактический G1 receipt после G0 |
| **I4-B03** | 99 / A5→R1 | `libraryPartName` frozen schema vs upstream 1.5.9 → локальный GetAddOnVersion/schema/APX SHA → exact allowed fields, иначе `BLOCKED_LOCAL_SCHEMA` |
| **I4-B04** | 98 / A5→R2 | GH→typed PR74 automatic bridge не найден в проверенных файлах → ограничить до ручного approved JSON → `NOT_FOUND_SCOPED`, не новый writer |
| **I4-B05** | 97 / A5→I4 | Нет нового authored G1 run → подготовить утверждённый новый intent/target/story/CSE; после G0 запустить только `--preflight` → receipt, 0 writes |
| **I4-B06** | 95 / A5→R1 | PolyRoof upstream, PR74 verifier SinglePlane → исключить из первого G1, документировать existing route или `NOT_FOUND` |
| **I4-B07** | 94 / A5→R2 | Slab Create→Modify partial + GH concurrent writer → ledger readback, ownership lock, no retry → сценарий STOP и reconciliation без LIVE |
| **I4-B08** | 91 / A5→R3 | Slab holes, roof facets, QA/IFC/СП → сохранить P1, доказать GH outputs и local native readback отдельно; не блокировать базовый G1 |

**Вопросы аудитору A5 (не требуют ответа пользователя):** (1) принять исправление G1 «read-only runtime обязателен»; (2) при отсутствии ноутбука зафиксировать `STALLED_EXTERNAL_DEPENDENCY`, не требовать фиктивного offline PASS; (3) приоритизировать G0 и новый G1 перед очередными исследованиями PolyRoof; (4) не менять `NEXT_RESEARCH_PRIORITIES.md` до административного согласования; (5) не повышать G2 из SOURCE в INSTALLED по чужим PR.

## 9. Статусы и границы выполнения
**SOURCE:** R1/R2/R3 и A5 реально прочитаны, PR74 source-контракт и CLI независимо проверены, официальная совместимость Graphisoft подтверждена. **OFFLINE:** новых фактических G1 запусков 0. **BUILD:** 0. **INSTALLED:** NOT_VERIFIED. **LIVE:** новых 0. **ACCEPTED:** 0. **NOT_FOUND:** готовый GH→PR74 converter в проверенном PR74; PR74 PolyRoof/ModifyRoofs native route; PR74 slab holes; автоматическая атомарная трёхсторонняя синхронизация и rollback; Rhino8 Yak Tapir GH compatible distribution. **G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4/G5=NOT_RUN.**

**Ничего не устанавливалось и не запускалось на ноутбуке.** Не менялись main, исходники, PLN/APX, ветки PR, лицензии, Work/Codex/Arena, платные API; merge/LIVE не выполнялись. Каноническая очередь прочитана, но не изменена. Исторические APA LIVE receipts не перенесены в приёмку нового BUILD-01.

**MODEL_MODE_NOT_VERIFIABLE.**
