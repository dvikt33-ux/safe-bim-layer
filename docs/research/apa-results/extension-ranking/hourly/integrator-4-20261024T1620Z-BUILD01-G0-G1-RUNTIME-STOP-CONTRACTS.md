# APA I4 — BUILD-01 #192: исполнимая интеграция, цикл 16Z (24.10.2026)

**Срез:** 2026-10-24 16:20 UTC / 19:20 МСК. **Роль:** I4, интегратор. **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** SOURCE_ONLY, без доступа к ноутбуку/локальному AC29/Rhino. **MODEL_MODE_NOT_VERIFIABLE.** Отчёт описывает будущие операции, а не их выполнение.

## 1. Входы текущего часа: наличие и независимый SHA

Все файлы прочитаны непосредственно из указанной ветки через GitHub connector; SHA вычислен как Git blob SHA-1 от фактически прочитанных UTF-8 байтов и совпал с SHA GitHub.

| Источник | UTC | Файл в hourly/ | Git blob SHA-1 | Статус |
|---|---|---|---|---|
| R1 | 16:03 | [G0 Runtime Decision Gates](research-1-20261024T1603Z-BUILD01-G0-RUNTIME-DECISION-GATES.md) | `10173bf788344de8a85a926c98cac44a6f6053c9` | FOUND / SHA_MATCH |
| R2 | 16:03 | [Conflict Ownership Ledger](research-2-20261024T1603Z-BUILD01-CONFLICT-OWNERSHIP-LEDGER.md) | `fd551db40d8d690a79a786aaa62bfe090c3e41b7` | FOUND / SHA_MATCH |
| R3 | 16:02 | [GH-BASE P0 Checklist](research-3-20261024T1602Z-BUILD01-GH-BASE-P0-CHECKLIST.md) | `9d04949b908b7d786172efbe290dcf2b2b7d606b` | FOUND / SHA_MATCH |
| A5 (последний доступный) | 15:43 | [A5 G0/G1 Strict Counteraudit](audit-a5-20261024T1543Z-BUILD01-G0G1-STRICT-COUNTERAUDIT.md) | `af0ab17e54b556001a47572a5d858e8c9eda76a8` | FOUND / SHA_MATCH |
| I4 (предыдущий) | 15:22 | [I4 One Writer Runbook](integrator-4-20261024T1522Z-BUILD01-G0G1-ONE-WRITER-READONLY-RUNBOOK.md) | `702bb038a8078297ee9a0ddb4ee1d07b98e7461b` | FOUND / SHA_MATCH |

Проверен первичный [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) и неизменяемый PR74 commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, включая `scripts/archicad_project_accelerator.py` (blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`) и [исходный пример authored JSON](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/examples/accelerator/model-first-building.json) (blob `e192fbb31bc872d751c41aa7132f0a4981755051`). Это SOURCE, не установленный локальный checkout.

## 2. Решение: один контур нативной записи

```text
Rhino 8 (.3dm, RhinoCommon, NURBS/BREP, единицы/допуски)
     ↓ параметрическая геометрия / исходные числа
Grasshopper (GH-BASE: W,D,Z,H,контуры,опирание,кровля,проёмы; QA)
     ↓ ПОКА РУЧНОЙ перенос в существующий контракт (auto adapter не доказан)
apa-authored-project/1 JSON (PR74, immutable schema + G0 story/material bindings)
     ↓ compile_authored_intent + typed DAG/topological order
BIM Graph → единственный SceneWriter + существующий SQLite ledger
     ↓ только после отдельного разрешения G3
Tapir 1.5.10 → Archicad 29 build 5101: native Wall/Slab/Column/SinglePlane Roof/Window/Door
     ↑ native GUID/type/story/host/material/geometry/BREP readback
Archicad API / штатный GC29 Element Input+Deconstruct (ТОЛЬКО READ)
     ↑ GH QA; отдельно IFC/IDS/СП review
```

**Ограничение:** это не доказанная автоматическая трёхсторонняя синхронизация. R2 не обнаружил GH DataTree→PR74 адаптер **только в 12 проверенных Python-файлах пяти PR (#74/#126/#131/#149/#162)**. Нового writer/router/synchronizer не создавать. GC29 Design Create/Modify, Tapir GH Push, Rhino Bake→Morph/GDL запрещены как второй канал записи в том же BUILD-01. Обратное чтение не является командой UPDATE. Изменение GH-параметра после G3 требует нового утверждённого плана и существующей подтверждённой команды; универсальный native UPDATE не доказан.

**Владение:** Rhino ObjectId — Rhino; GH component/path — Grasshopper; `projectId/stepId/sourcePlanHash/scene_id/operationHash` — APA и SQLite; `native GUID` выдаёт только Archicad после CREATE; `ownerWallId.guid.$createdGuid` разрешается после подтверждённого создания родительской стены; `floorIndex/floorId/level` — исключительно из фактического `GetStories`; IFC GlobalId — отдельная IFC-идентичность. Не выводить GUID из GH Path, не подставлять этажи 0/1 без G0.

## 3. Что должно быть установлено / проверено (без установки сейчас)

| Порядок | Компонент | Версия/лицензия/проверка | Роль и STOP |
|---|---|---|---|
| 1 | Archicad для Windows | **29 build 5101** — локальный About + `API.GetProductInfo`; действующая лицензия, точный port/PLN | native authority; `BLOCKED_PRODUCT_OR_BUILD_UNVERIFIED` |
| 2 | Tapir Archicad Add-On | **локальная 1.5.10 заявлена, но не измерена**; `GetAddOnVersion`, Add-On Manager, APX path/SHA256, command registration | API native; frozen `schemas/tapir-live-1.5.10/tapir-scene-live.json` ≠ local schema |
| 3 | APA PR74 + BIM Graph/SceneWriter/SQLite | immutable PR74 `5a3a9201…` для SOURCE; локальный commit, состояние дерева, наличие соседних schema definitions проверить | только существующий writer; нельзя считать несколько PR автоматически объединёнными |
| 4 | Rhino 8 + штатный Grasshopper | Rhino 8 Service Release/лицензия, `RhinoDoc.ModelUnitSystem`, абсолютный/угловой допуски, SHA `.3dm/.gh` | GH параметрика и геометрия; не обязательный runtime G1 без GH-графа |
| 5 | Graphisoft Grasshopper–Archicad **29** Live Connection | официальный **build 3000**, Windows, поддержка Rhino 7/8; дата 01.10.2025; локальный INSTALLED неизвестен | для read-only AC→GH; для G1 не обязателен; не включать GH Design writer |
| 6 | Опционально IfcOpenShell/IfcTester | версия/лицензия отдельно при G4; сейчас не устанавливать | независимый IFC/IDS QA, не native writer |

**Официальный источник GC29:** https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/ . **Tapir upstream:** https://www.archicad-api.com/ (сайт заявляет open-source/MIT; лицензию локального APX и конкретной сборки сверять отдельно). Не требовать для G1 Rhino.Inside AC29 host, Tapir GH Yak, Karamba, Honeybee, GDL/LCF converter. Программное обеспечение, расширения и платные API в этом цикле не устанавливались и не запускались.

## 4. Точные контракты GH → authored PR74 → native readback

| Контракт | Вход GH / поле существующего JSON | Guard до G1 | Native/readback после отдельного G3 |
|---|---|---|---|
| PROJECT | `schemaVersion=apa-authored-project/1`, root `projectId=brief.projectId`, `units=meters`, `brief.targetProjectPath` | exact `RUN.EXPECTED_PATH`, запрещён пользовательский BDD; strict root allowlist | `GetProjectInfo` и SHA scratch; project binding |
| STORY | `brief.stories[].id/label/level`, `storyHeights[id]`; в ADAPT_EXISTING: `existingNativeIndex/existingFloorId/existingNativeLabel` | первая архитектурная метка `1 этаж`, Z0=0; высота 2.4–4.5 м; `abs(Z0+H0-Z1)≤1e-5`; два реально существующих native stories | `GetStories`, activeIndex, nativeIndex/floorId/level |
| GEOMETRY | `layout.outline`, `rooms[].rectangle`, `axes[]`, `bearingLines[]`, `loadPaths[]` | прямоугольные комнаты, оси X/Y, Wall 0.15–0.60 м, длина ≥1 м, без подмены NURBS bbox | тип Wall, геометрия, floor, bbox/BREP |
| MATERIAL | `cseCandidate.native`, `wallBasicMaterialName` | GUID/имя/attributeId из фактического PLN; не из PR74 example | material readback, отдельно инженерная/нормативная приёмка |
| SLAB | authored compiler генерирует `CreateSlabs`; Basic material | frozen `CreateSlabs` не гарантирует material при CREATE; typed schema и реальный material | **тот же SceneWriter**: CreateSlabs→GUID/readback→ModifySlabs→readback; при PARTIAL не повторять CREATE |
| COLUMN | `nativeComponents.CreateColumns` (если локальная schema совпадает) | native floor/height/profile/material, segment child GUID | колонна + дочерние GUID/размеры |
| BEAM | Tapir `CreateBeams` есть, но **вне** authored `nativeComponents` allowlist PR74 | исключить из обязательного G1, пока нет доказанного existing route | NOT_IN_AUTHORED_G1 |
| ROOF | `nativeComponents.CreateRoofs`: Basic SinglePlane, `pivotLine`, polygon, angle, level, floorIndex, material | не PolyRoof, не произвольный NURBS; local schema + story/material | typed Roof SinglePlane, angle/pivot/level/material/contour |
| WINDOW/DOOR | `CreateWindows/Doors`, `ownerWallId.guid.$createdGuid`, centerOffset/width/height/sillHeight | host Wall step существует в DAG; libraryPartName/Favorites и skippedCount локально проверить | native Window/Door GUID, host Wall GUID, story, размеры |
| IDENTITY | GH tree ≠ native GUID; scene/step/plan hash → SQLite | один исполнитель, stable ledger, отсутствие неизвестного предыдущего CREATE | GUID map + independent `GetDetailsOfElements` |

**BREP:** GH/Rhino замкнутость, ориентация, самопересечения, плоскостность, допуски и площади — отдельная проверка входной геометрии. Native BREP/bbox после CREATE и после Save/Open проверяется независимо; совпадение Rhino preview не означает совпадение Archicad. Отверстия в перекрытиях, сложные кровли/узлы, универсальные Stair/GenericOpening, конструктивная несущая способность и автоматическое соблюдение СП **не подтверждены** как P0.

## 5. G0–G5: ворота, доказательства ГОТОВО и статус

| Gate | Критерий ГОТОВО | Фактически на 16:20Z |
|---|---|---|
| **G0** read-only | реальный manifest: AC29 29/5101, порт/активный scratch PLN SHA256, два native stories, local Tapir 1.5.10 APX/schema SHA, Favorites, materials, library `skippedCount`, spatial inventory, локальный APA commit, Rhino/GC29 installed state | **BLOCKED_RUNTIME_NOT_OBSERVED** |
| **G1** read-only preflight | **реальный** `--preflight` нового authored JSON, точные target/story/material/origin, typed DAG, topological host refs, collision check, `confirmPlanHash`, `result.json`, `preflight.json`, `plan.json`, before/after inventory, SHA256, `modelWriteAttempts=0` | **NOT_RUN**; автономный authored offline запрещён PR74 |
| **G2** schema gate | local 1.5.10 vs frozen/PR74 fields, Window/Door/Slab/Roof, native materials/Favorites/library; drift→STOP | **SOURCE_PARTIAL / BLOCKED_LOCAL_SCHEMA** |
| **G3** native CREATE | отдельное разрешение на exact scratch PLN/port/planHash, intent-before-write SQLite, один SceneWriter, GUID/type/story/host/material/BREP receipts, no duplicate | **NOT_AUTHORIZED / NOT_RUN** |
| **G4** Save/Open | отдельно разрешённый GuardedSave, Close, no-open check, Reopen, independent native GUID/type/story/host/material/BREP diff + hashes | **NOT_RUN** |
| **G5** second model | другой approved scratch PLN и другое здание, новый plan/scene, повтор G1–G4 без старого fixture | **NOT_RUN** |

**Ключевая проверка исходника:** `scripts/archicad_project_accelerator.py` строки 438–447: authored `apa-authored-project/1` требует `preflight/execute` и callable transport, делает `RUN.guarded_project(api)`; полностью автономный offline запрещён. CLI строки 609–650: `--intent`, `--schema`, `--output`, `--preflight`, `--scratch-port` или `--isolated-port`. `--output` создаётся с `exist_ok=False`. G1 создаёт локальные evidence-файлы и может использовать SQLite preflight, но **не должен писать BIM**; `evidenceKind=LIVE` по транспорту означает LIVE_READ, не native CREATE.

## 6. Практический чек-лист ноутбука (инструкция, НЕ выполнено)

1. **Ничего не устанавливать/не открывать/не сохранять сейчас.** После отдельного разрешения: локально проверить AC29 About 5101, лицензию, активный порт, `GetProjectInfo`; BDD/исходный PLN не использовать. Разрешённый кодом PR74 target: `--isolated-port` только `C:\LocalAI\APA_Isolated_Writer_Test_01.pln`, либо `--scratch-port` только `C:\LocalAI\APA_Test_House_01.pln`. Эти пути — кодовые bindings, а не доказательство наличия файлов.
2. G0 только READ: `API.GetProductInfo`, `GetProjectInfo`, `GetStories`, `GetAddOnVersion`, `GetAttributesByType` / `GetBuildingMaterials`, `GetAvailableLibraryParts` (+ `skippedCount`), `GetAllElements`, `Get3DBoundingBoxes`, `GetDetailsOfElements`. Favorites через существующий отдельный READ/UI: `GetFavoritesByType` есть во frozen Tapir, но **не в `EvidenceAPI.READS` PR74**; без локального доказательства `BLOCKED_FAVORITE_READ`.
3. Локальные хеши: `Get-FileHash -Algorithm SHA256 "<APPROVED_SCRATCH.pln>"`, `Get-FileHash -Algorithm SHA256 "<TAPIR.apx>"`, `git -C "<APA_CHECKOUT>" rev-parse HEAD`, `git -C "<APA_CHECKOUT>" status --porcelain`; сохранить evidence отдельно от защищённых файлов. Зафиксировать APX schema и два native story.
4. Проверить Rhino 8 SR/license, GH и единицы/допуски. Если исходная модель в мм, GH→JSON в метрах с коэффициентом 0.001 **один раз**. GC29 build 3000 — проверить installed, не устанавливать; GH Design Create/Modify физически отсоединить от writer.
5. **После G0:** взять PR74 `examples/accelerator/model-first-building.json` как структуру, но **не запускать исторический fixture**; новый `projectId`, точный `brief.targetProjectPath=RUN.EXPECTED_PATH`, G0 native stories/material/host/library, согласованные высоты и свободный origin. До G0 значения `originXY, floorId, nativeIndex, materialGuid, libraryBinding` = **UNRESOLVED**, не подставлять выдуманные и не выдавать placeholder за schema-valid intent.
6. **Только после разрешённого READ-only G0:** из локального PR74 checkout, с НОВЫМ отсутствующим output directory и проверенным портом выполнить пример (НЕ выполнен):
   ```powershell
   py scripts/archicad_project_accelerator.py --intent "<NEW_APPROVED_AUTHORED.json>" --schema "schemas/tapir-live-1.5.10/tapir-scene-live.json" --output "<NEW_UNUSED_EVIDENCE_DIR>" --preflight --isolated-port <ACTUAL_APPROVED_PORT>
   ```
   Для второго code-bound scratch заменить только `--isolated-port` на `--scratch-port` при exact target match. **Не** использовать `--execute` в текущем цикле.
7. Проверить `result.json` (`status=READY_FOR_EXPLICIT_TEST_RUN`, `modelWriteAttempts=0`, `inventoryUnchanged=true`), `preflight.json`, `plan.json`, `inventory-before.json`, `inventory-after.json`, `SHA256.json`; при любом drift/UNKNOWN остановиться. Если локального runtime нет — честный `BLOCKED_RUNTIME_NOT_OBSERVED`.

## 7. Конфликты, независимая проверка, rollback

| Событие | STOP / только допустимое действие |
|---|---|
| CREATE timeout/UNKNOWN | `UNKNOWN_STOP`; сверить existing SQLite scene_id/plan_hash/stepId + native GUID inventory; **не повторять CREATE** и не обходить новым scene_id |
| UPDATE / FEEDBACK_LOOP | только доказанная native Modify-команда внутри SceneWriter; GH Design writer отключён; `SECOND_WRITER_STOP` |
| DELETE / GH reference lost | `DELETE_UNAUTHORIZED_STOP`; отсутствие GH объекта не разрешает удалять AC |
| PARTIAL_SLAB | сохранять существующий Slab GUID, readback material; не делать второй CreateSlabs |
| HOST_DRIFT | `HOST_DRIFT_STOP`; сверить Wall GUID, Window/Door ownerWallId/story, без автоматического rehost |
| STORY/MATERIAL/LIBRARY drift | `BLOCKED_LOCAL_SCHEMA`/`BLOCKED_ATTRIBUTE_BINDING`/`PARTIAL_LIBRARY_INVENTORY` |
| Save/Open / BREP drift | `G4_FAIL`, read-only reconciliation, не ACCEPTED |
| rollback | **нет доказанной атомарной транзакции Rhino+GH+AC+SQLite**; freeze writers → snapshot/inventory comparison → только отдельно санкционированное восстановление из scratch backup; SQLite ledger не откатывать как замену PLN |

**Пять независимых вердиктов:** `GH_GEOMETRY` (NURBS/BREP/units), `AC_NATIVE` (GUID/type/story/host/material/BREP), `IFC_STRUCTURE` (IfcWall/Slab/Roof/Window/Door, storeys, GlobalId, voids/fills), `IDS_INFORMATION` (IfcTester), `NORMATIVE_REVIEW` (СП/редакция/пункт/применимость/измерение). Каждый UNKNOWN до реального evidence. R3 NEG-Z / NEG-HOST / NEG-UNIT — **спецификации**, не исполненные тесты.

## 8. Точные открытые блокеры и вопросы A5

| ID | Блокер | Владелец / закрывающее доказательство |
|---|---|---|
| I4-16-B01 P0 | Нет runtime-доступа к ноутбуку и read-only G0 manifest | владелец среды + I4: реальные AC29 build/port/PLN SHA, 2 stories, APX/schema, materials/Favorites/library, APA checkout |
| I4-16-B02 P0 | `GENERATE_FROM_ZERO` не создаёт native stories; нет доказательства двух этажей scratch | R1/I4: `GetStories` + exact bindings, либо STOP |
| I4-16-B03 P0 | Нет локальной Tapir 1.5.10 command schema/APX SHA и Favorite/Library evidence | R1/I4: local-vs-frozen Window/Door/Slab/Roof, `skippedCount` |
| I4-16-B04 P0 | Нет нового двухэтажного authored JSON с реальными G0 значениями | I4: schema-valid intent после G0; до этого `BLOCKED_LOCAL_BINDINGS` |
| I4-16-B05 P0 | G1 `--preflight` и нулевая native запись не подтверждены | I4: receipt `READY_FOR_EXPLICIT_TEST_RUN`, `inventoryUnchanged`, `modelWriteAttempts=0`, SHA |
| I4-16-B06 P1 | Нет доказанного GH DataTree→PR74 auto adapter | R2: `NOT_FOUND_IN_SCOPED_PR_HEADS`, ручной JSON для G1; не создавать writer |
| I4-16-B07 P1 | GH-BASE .gh/BREP/нормативный QA не исполнялись | R3: спецификация готова; не считать G1 blocker, если G1 authored JSON корректен |
| I4-16-B08 P0 | G3/G4/G5 без разрешения и native receipts | владелец/A5: явный допуск на exact scratch/port/hash; до этого STOP |

**Вопросы A5:** (1) Считать ли SOURCE R1/R2/R3 текущего 16Z достаточными и остановить дальнейшее расширение плагинов до фактического G0? (2) Подтвердить, что G1 должен выполняться только на уже существующей утверждённой scratch PLN с двумя native stories, без создания этажей? (3) Разрешать ли G3 только после отдельной явной санкции exact PLN/port/confirmPlanHash, при неизменном одном SceneWriter? (4) Достаточно ли для будущего G4 native readback+Save/Open, оставив IFC/IDS/нормативы отдельными вердиктами, не скрывая UNKNOWN?

**Передача A5:** входы 3/3 FOUND и SHA_MATCH; источник PR74 проверен; I4 runbook и таблица контрактов обновлены без изменения кода. Главный измеримый следующий результат — **фактический G0 manifest**, затем **один G1 read-only preflight**. При отсутствии доступа: `STALLED_EXTERNAL_DEPENDENCY`, не повторять бессрочные SOURCE-исследования.

## 9. Строгая классификация и запреты

- **SOURCE:** R1/R2/R3/A5/предыдущий I4 прочитаны; SHA_MATCH; официальный Graphisoft GC29 build 3000/Rhino8; PR74 исходник/пример проверены.
- **OFFLINE:** новых запусков GH/PR74 нет; численные примеры R3 прошлых циклов не G1.
- **BUILD:** новых BUILD-01 зданий не подтверждено.
- **INSTALLED:** NOT_VERIFIED (нет доступа к локальной среде).
- **LIVE:** новых операций записи не проводилось; G1 LIVE_READ тоже NOT_RUN.
- **ACCEPTED:** 0 новых.
- **NOT_FOUND:** GH→PR74 adapter только в ограниченно проверенных PR; атомарный cross-app rollback не подтверждён.
- **G0/G1/G2/G3/G4/G5:** `BLOCKED_RUNTIME_NOT_OBSERVED / NOT_RUN / SOURCE_PARTIAL / NOT_AUTHORIZED / NOT_RUN / NOT_RUN`.
- **Ограничения:** main, код, PLN/APX, merge, установки, LIVE, платные API, Work/Codex/Arena не затронуты. `NEXT_RESEARCH_PRIORITIES.md` не менялся. **MODEL_MODE_NOT_VERIFIABLE.**

**Публикация этого отчёта требует отдельного GitHub create → readback по commit и ветке → независимого Git blob SHA-1; до проверки нельзя писать PUBLISHED_VERIFIED.**
