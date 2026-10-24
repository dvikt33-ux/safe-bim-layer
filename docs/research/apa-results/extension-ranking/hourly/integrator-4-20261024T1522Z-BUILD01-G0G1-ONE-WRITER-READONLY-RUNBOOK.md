# APA I4 — BUILD-01: единая исполнимая схема G0→G5, цикл 15Z

**Дата среза:** 24.10.2026, 15:22 UTC / 18:22 МСК. **Роль:** I4 — интегратор. **Цель:** [BUILD-01, issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Ветка:** `research/apa-extension-ranking-hub-20261018`. **Режим:** GitHub SOURCE/read-only + публикация только настоящего отчёта; Windows/Archicad/Rhino не подключались. **MODEL_MODE_NOT_VERIFIABLE**.

## 1. Приёмка входов текущего часа

Все три отчёта **15Z** прочитаны непосредственно через GitHub; Git blob SHA-1 независимо вычислен из полного UTF-8 содержимого (формат Git: `SHA1("blob "+byteLength+"\\0"+bytes)`) и совпал с возвращённым GitHub SHA. Это не подтверждает установленный runtime.

| Источник | Файл, время | Git blob SHA-1 | Приёмка |
|---|---|---|---|
| R1 | [research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md](research-1-20261024T1458Z-BUILD01-G0-READONLY-INVENTORY.md), 14:58Z | `5c036f238ae65afd3a0f338eb98d0884aaad7805` | FOUND / SHA_MATCH |
| R2 | [research-2-20261024T1504Z-BUILD01-SCOPED-BRIDGE-CLOSURE.md](research-2-20261024T1504Z-BUILD01-SCOPED-BRIDGE-CLOSURE.md), 15:04Z | `1407b1d013d59f73738614ed09c33e057d4b6e3b` | FOUND / SHA_MATCH |
| R3 | [research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md](research-3-20261024T15Z-BUILD01-A5-STRICT-GH-CONTRACT-QA.md), 15Z | `ac9a9b8d80def329a29915755603801fa5c98465` | FOUND / SHA_MATCH |
| A5, последнее опубликованное поручение | [audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md](audit-a5-20261024T1439Z-BUILD01-G0G1-COUNTERAUDIT.md), 14:39Z | `2b9079c78c226f4c01cb05b6957e993c6f4e0d12` | FOUND / SHA_MATCH |

**MISSING 15Z: 0/3.** Аудит A5 относится к предшествующему циклу, не подменяет новые R1/R2/R3. В качестве независимых источников повторно прочитаны [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) и код PR74 на **immutable commit** `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: `scripts/archicad_project_accelerator.py` blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`, `scripts/archicad_authored_native_plan.py` blob `f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7d`, `scripts/archicad_scene_run.py` blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`, `examples/accelerator/model-first-building.json` blob `e192fbb31bc872d751c41aa7132f0a4981755051`. Исследовательская ветка **не равна** установленной сборке PR74+PR126+PR131+PR149+PR162.

## 2. Единственный маршрут записи и граница автоматизации

```text
Rhino 8 (.3dm) → Grasshopper 1 (геометрия, параметры, QA; БЕЗ Bake/Push/Design Create)
                         │
                         ▼
              таблица проверенных параметров GH
                         │ РУЧНОЕ сопоставление с существующим контрактом
                         ▼
     apa-authored-project/1 JSON → PR74 compile_authored_intent
                         │              │
                GetStories/GetAttributes (только READ)
                         ▼
            typed BIM Graph → topological order
                         ▼
           ОДИН SceneWriter → SQLite intent/step ledger
                         ▼
              Tapir Archicad Add-On 1.5.10
                         ▼
             Archicad 29 native Wall/Slab/Roof/
                    Window/Door/Column (G3 — НЕ РАЗРЕШЁН)
                         │
             GetAllElements/GetDetails/GetModelDump
                         ▼
       read-only QA + Graphisoft GC29 Element Input/Deconstruct
                         ▼
                Grasshopper reference geometry
```

**Автоматической трёхсторонней синхронизации здесь НЕТ.** R2 ограниченно проверил 12 Python-файлов пяти PR head commits (#74/#126/#131/#149/#162) и не нашёл GH DataTree→PR74 converter. Результат `NOT_FOUND_IN_12_INSPECTED_FILES_5_PR_HEADS`, а не «не существует вообще». **Не разрабатывать второй writer/router/synchronizer.** Для первого G1 использовать имеющийся authored JSON и ручной перенос параметров; официальный GC29 только в read-only ветви. Компоненты GH Design Create/Modify, Tapir GH Push, Rhino Bake в Archicad и GDL/Morph-импорт **не включать** в нативный контур.

**Владение:** Rhino `ObjectId` — геометрический объект Rhino; GH `GH_Path`/component/source IDs — параметрическая модель; APA `projectId/stepId/sourcePlanHash/scene_id/confirmPlanHash` — задание, DAG и ledger; **Archicad GUID** — идентичность нативного элемента; IFC `GlobalId` — идентичность IFC-представления. Ни одно пространство ID не подменяет другое. `ownerWallId.guid.$createdGuid` — ссылка на шаг ранее созданной стены, фактический GUID появляется **только после G3 CREATE**. Источник истины для этажа/материала/host/геометрии после записи — Archicad, а не GH preview или SQLite.

## 3. Что должно быть на ноутбуке: минимальный набор, порядок, лицензии

| № | Компонент и точная версия | Действие после разрешения; сейчас только инвентаризация | Признак ГОТОВО / риск |
|---|---|---|---|
| 1 | **Archicad 29 build 5101**, Windows 11 | Проверить About, лицензию, активный проект, порт, имя и SHA PLN; без изменения PLN | `API.GetProductInfo.version=29`; build 5101 подтверждён отдельно; нет Teamwork/Untitled; путь = разрешённый scratch |
| 2 | **Tapir Archicad Add-On 1.5.10** | `GetAddOnVersion`, путь и SHA256 APX, зарегистрированные Create/Get схемы | Локальная 1.5.10 и поля реально совпали с frozen; upstream MIT не заменяет runtime |
| 3 | **APA PR74**, immutable `5a3a9201…` | Найти локальный checkout и точный commit; frozen schema `schemas/tapir-live-1.5.10/tapir-scene-live.json` и **соседние** `command_definitions.js/common_schema_definitions.js` с исходными SHA256 | Не использовать путь схемы из research branch: R1 подтвердил, что там её нет |
| 4 | **Rhino 8 + штатный Grasshopper** | Проверить Service Release, лицензию, `ModelUnitSystem`, абсолютный/угловой допуски, SHA .3dm/.gh | Встроенных GH-компонентов достаточно для GH-BASE; никаких обязательных новых плагинов |
| 5 | **Graphisoft Grasshopper–Archicad 29 Live Connection build 3000**, Windows, Rhino 7/8, дата 01.10.2025 | Проверить наличие; при отсутствии — НЕ устанавливать в этом цикле; для QA только Element Input/Deconstruct | Официальный [Graphisoft Toolset](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/), не совместим с Start Edition; локально NOT_VERIFIED |
| 6 | Опционально **IfcOpenShell/IfcTester** | После нативной сборки для независимого IFC/IDS QA; установка не разрешена | IFC/IDS не доказывают native BIM и соблюдение СП |
| 7 | **Не устанавливать для G1:** Tapir GH Yak 1.7.2, Rhino.Inside AC29 host, Karamba/Honeybee | Rhino8-дистрибутив Tapir GH и готовый Rhino.Inside host не доказаны; FEA/климат — P1 | Не блокируют базовое здание |

Источники: [Graphisoft](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/), [Tapir upstream](https://github.com/ENZYME-APD/tapir-archicad-automation) (MIT для исходников; Add-On и GH plugin — разные компоненты), [McNeel Rhino](https://www.rhino3d.com/), [IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell). **Ничего не установлено**. Archicad/Rhino требуют собственных лицензий; бесплатность add-on не означает бесплатность хостов.

## 4. Контракты данных и нативных операций

| Контракт | GH/JSON вход и ограничения | Единственный маршрут и readback | Gate |
|---|---|---|---|
| `PROJECT` | `schemaVersion="apa-authored-project/1"`, `projectId=brief.projectId`, `units="meters"`, `brief.targetProjectPath=RUN.EXPECTED_PATH` | PR74 strict root allowlist; чужой PLN → STOP | G0/G1 |
| `STORY` | `brief.stories[].id/label/level/existingNativeIndex/existingFloorId`; первый архитектурный `1 этаж` на 0.0; `storyHeights` 2.4–4.5 м, согласование соседних Z до 1e-5 м | `GetStories`: реальный `index/floorId/level/name`; архитектурный label не обязан равняться native label | G1/G2 |
| `SPACE` | `layout.outline{xMin,xMax,yMin,yMax}`; `rooms[].rectangle`, `axes[]` X/Y, `bearingLines[]`, `loadPaths[]`; не произвольный NURBS | `archicad_semantic_spatial` → typed candidate; комнаты не заменять bbox сложной формы | G1 |
| `CSE/MATERIAL` | `cseCandidate.native` содержит существующий BuildingMaterial GUID/имя, thickness/storyIds и provenance; `wallBasicMaterialName` отдельно | `GetAttributesByType` + `GetBuildingMaterials`; нет GUID → STOP, не создавать фиктивный материал | G0/G2 |
| `SLAB` | Authored compiler генерирует `CreateSlabs` из layout, absolute level, polygon, thickness, floorIndex | SceneWriter: `CreateSlabs→readback→ModifySlabs` при Basic material; итоговые GUID/type/story/level/material; отверстия не подтверждены | G2/G3/G4 |
| `WALL` | `bearingLines` 0.15–0.60 м, длина ≥1 м; отдельные partition через `nativeComponents.CreateWalls` с локальным floorIndex | `CreateWalls` → native GUID + geometry/material; несущие стены вдоль границ комнат | G1/G3 |
| `COLUMN` | `nativeComponents.CreateColumns`: coordinates XYZ, floorIndex, height/width/depth; local material/profile | `CreateColumns` → parent/segments GUID и размеры; optional | G2/G3 |
| `BEAM` | `CreateBeams` есть в Tapir, но **нет** в authored `nativeComponents` allowlist PR74 | **НЕ включать в G1**; не выдавать optional Tapir command за интегрированный маршрут | G2 P1 |
| `ROOF` | `nativeComponents.CreateRoofs`: SinglePlane, `pivotLine`, polygonCoordinates, level, `structureType=Basic`, buildingMaterialId, floorIndex | `CreateRoofs` → typed roof adapter verify; PolyRoof upstream ≠ PR74 support | G2/G3 |
| `OPENING` | `CreateWindows/Doors`: `ownerWallId.guid.$createdGuid`, centerOffset,width,height,sillHeight; library/Favorite локально сверить | После Wall; readback host GUID/story/size/library part/marker; frozen `libraryPartName` vs upstream 1.5.9 = SCHEMA_DRIFT_RISK | G2/G3 |
| `GH_GEOMETRY` | `W,D,originXY,Z0,Z1,H0,H1,Twall,Tslab,room rectangles,roof pivot/pitch,openings`; метры, закрытые контуры | GH только параметры/preview; передача в JSON **ручная** с проверкой полей | G1 SOURCE_SPEC |
| `IDENTITY` | `stepId/sourcePlanHash` ≠ native GUID; `GH_Path` ≠ `floorIndex`; `IfcGlobalId` ≠ AC GUID | SQLite ledger + AC `GetAllElements/GetDetails` после санкционированного CREATE | G3/G4 |
| `QA` | GH loops/planarity/normal/area/BREP; AC GUID/type/story/host/material/BREP; IFC GlobalId/storey/voids; IDS; применимый СП | Пять **раздельных** вердиктов: GH_GEOMETRY, AC_NATIVE, IFC_STRUCTURE, IDS_INFORMATION, NORMATIVE_REVIEW | G4/G5 |

**Корневой allowlist PR74:** обязательны `schemaVersion,projectId,units,brief,cseCandidate,layout,storyHeights`; допустимы лишь `wallBasicMaterialName,nativeComponents,nativeGeometryAudit,junctionPolicy,nativeRoofJunctions,structuralFunctions`. `nativeComponents` принимает только `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs`; `CreateSlabs` генерирует authored candidate. Не добавлять `GH_Path,source_key,slab_holes,roof_facets` в root. **G1 без реального local story/material/library binding нельзя объявить schema PASS.**

## 5. Grasshopper: граф, параметры, BREP и ошибки

**GH-BASE (P0, спецификация, не .gh PASS):** `W,D,originXY` → Construct Point×4 → Closed Polyline/Area → `outline`; Lines/Length → `axes` + `bearingLines`; Rectangle/Area/Region Intersection → `rooms`; Move Z → `story levels`; Line → roof pivot; Panels → контрольные численные значения. У каждого authored wall/room стабильный source ID, но не выдуманный AC GUID. Перенос в `brief/layout/storyHeights/nativeComponents` — ручной по таблице выше. Не преобразовывать кривую комнату в bbox без архитектурного решения.

**BREP QA:** `Curve.IsClosed`, `IsPlanar`, self-intersection, ориентация внешнего контура CCW/внутреннего CW, nesting/area, `Brep.IsValidWithLog`, bbox и `Intersection.BrepBrep` с проверкой **массивов пересечений**, а не только bool. `Brep.IsSolid` требуется лишь для замкнутого объёма, не для отдельной плоскости кровли. Единицы Rhino mm→m переводить **ровно один раз**; записать фактический absolute tolerance. Теоретический GH-OPT пример: 12×8 минус 2×2 = 92 м², уклон `atan(1.6/4)=21.8014°`; это OFFLINE_NUMERIC_ONLY R3, **не** native holes/PolyRoof.

**STOP до G1:** `1 этаж` не на 0; story height <2.4 или >4.5; non-rectangular room; bearingLine 0.10 м; Z0+H0≠Z1; отсутствует source Wall для окна; повторная collinear wall; Rhino mm прочитаны как m; комната меньше minAreaM2. Эти проверки — SOURCE-спецификация; фактический GH граф не исполнялся.

## 6. Контрольные ворота G0–G5 и проверяемые артефакты

| Gate | Что сделать | **ГОТОВО** — точный критерий | Текущее состояние |
|---|---|---|---|
| **G0 — READ inventory** | Подтвердить AC29 build/port/active PLN/approved scratch, Tapir APX/schema, local PR74 commit, GetStories/materials/Favorites/libraries, Rhino8 SR/units/license/GC29 | `g0-manifest` с точными путями, версиями, SHA256 PLN/APX/checkout, read-only ответами и **одним** явным STOP reason при несовпадении | **BLOCKED_RUNTIME** |
| **G1 — NO-NATIVE-WRITE PREFLIGHT** | Один новый authored двухэтажный JSON через существующий PR74 `--preflight`, **с запущенным Archicad для READ** | Реальные `plan.json,preflight.json,result.json,inventory-before.json,inventory-after.json,SHA256.json`; typed DAG/toposort/host binding, `confirmPlanHash`, `modelWriteAttempts=0`, `inventoryUnchanged=true`, статус `READY_FOR_EXPLICIT_TEST_RUN` | **NOT_RUN** |
| **G2 — LOCAL COMMAND CONTRACT** | Сопоставить frozen Tapir 1.5.10 и локально зарегистрированные schemas/JS SHA; проверить story/host/material/library/SinglePlane | Подтверждённые Create/Get параметры, один SceneWriter, no unknown fields; при drift точный BLOCKED_LOCAL_SCHEMA | **SOURCE_PARTIAL** |
| **G3 — NATIVE CREATE** | Только после отдельного разрешения на **точный** scratch PLN/port/plan hash и проверки отсутствия чужих изменений | SQLite intent-before-write; native GUID/type/story/host/material/BREP receipts, уникальность scene_id, ни одного GH writer; статус `COMPLETE_UNSAVED` ещё **не ACCEPTED** | **NOT_AUTHORIZED / NOT_RUN** |
| **G4 — SAVE/OPEN** | Только после допуска GuardedSave → GUI Close → no-open check → Reopen → независимый AC readback | Совпали GUID/type/story/host/material/library/BREP, геометрия, source PLN SHA, receipt; IFC/IDS/СП verdict отдельно | **NOT_RUN** |
| **G5 — SECOND BUILD** | Другое authored здание на другом разрешённом scratch PLN, новые footprint/высоты/проёмы | Повтор G1–G4 с новым sourcePlanHash/sceneId; без fixture reuse | **NOT_RUN** |

**Особо важно:** PR74 `run_project` строки 438–447 **запрещает** `offline` для `apa-authored-project/1`; нужен callable native READ transport. Это не разрешение LIVE-записи: в `--preflight` `EvidenceAPI` запрещает native mutations. Код может пометить evidenceKind как `LIVE` из-за реального транспорта, но административно **LIVE_CREATE=0**, пока `modelWriteAttempts=0`. SQLite — durable ledger, **не** атомарная транзакция PLN.

## 7. Практический чек-лист для ноутбука — НЕ ИСПОЛНЕН

1. В Archicad проверить **About: 29/5101**, лицензию, активный порт и `GetProjectInfo`; закрыть/не использовать пользовательский BDD. Проверить путь и SHA **разрешённой** копии, не создавать/открывать/сохранять PLN в этом исследовательском цикле. PR74 CLI принимает только заранее определённые цели: `--scratch-port` → `C:\\LocalAI\\APA_Test_House_01.pln` либо `--isolated-port` → `C:\\LocalAI\\APA_Isolated_Writer_Test_01.pln`; **не** произвольный новый PLN. Исторический `Тест MER .pln` по умолчанию не трогать.
2. Только существующие чтения: `API.GetProductInfo`, `GetProjectInfo`, `GetStories`, `GetAddOnVersion`, `GetAttributesByType` (BuildingMaterial, Composite, Profile, Surface), `GetAvailableLibraryParts` (учесть `skippedCount`), `GetAllElements`, `Get3DBoundingBoxes`, `GetDetailsOfElements`. `GetFavoritesByType` есть во frozen Tapir, но **отсутствует в `EvidenceAPI.READS` PR74**: использовать только уже существующий отдельный read-only путь/UI либо `BLOCKED_FAVORITE`; не расширять router.
3. В PowerShell для **существующих** файлов: `Get-FileHash -Algorithm SHA256 "<PATH_TO_APPROVED_SCRATCH.pln>"`, `Get-FileHash -Algorithm SHA256 "<PATH_TO_TAPIR.apx>"`; `git -C "<LOCAL_APA_CHECKOUT>" rev-parse HEAD`. Это лишь будущие команды инвентаризации, сейчас не запускались.
4. Rhino: версия 8/SR, лицензия, единицы, абсолютный/угловой допуски; наличие штатного Grasshopper. GC29 build3000 проверить через UI, не устанавливать без разрешения. Проверить, что GH Design output **физически отсоединён** от компонентов записи.
5. Подготовить **новый** `apa-authored-project/1` из структуры [PR74 example](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/examples/accelerator/model-first-building.json), не запускать исторический fixture. Сменить `projectId` в root/brief согласованно, exact `brief.targetProjectPath` = реально разрешённый `RUN.EXPECTED_PATH`, координаты в свободной проверенной зоне, `brief.stories` по GetStories, `cseCandidate.native` по локальному BuildingMaterial, библиотеку/host и `storyHeights`. До G0 поля `originXY/storyIndex/materialGuid/libraryBinding` = **UNRESOLVED**, не вставлять произвольные значения. **Нового schema-valid fixture и G1 receipt пока нет.**
6. **Только после G0 и разрешённого READ-only подключения**, из локального checkout PR74, когда каталог `<NEW_EVIDENCE_DIR>` ещё **не существует**, возможная команда (пример, НЕ выполнена):
   ```powershell
   py scripts/archicad_project_accelerator.py --intent "<NEW_APPROVED_AUTHORED.json>" --schema "schemas/tapir-live-1.5.10/tapir-scene-live.json" --output "<NEW_EVIDENCE_DIR>" --preflight --isolated-port <ACTUAL_APPROVED_PORT>
   ```
   Если используется `APA_Test_House_01.pln`, заменить **только** `--isolated-port` на `--scratch-port`, при точном совпадении target. Путь схемы должен существовать в локальном PR74 checkout с соседними JS и правильными SHA. Выходной каталог — **несуществующий**, родитель — существующий; команда создаёт **локальные evidence-файлы**, но не должна изменять PLN. Нет read-only runtime → `BLOCKED_RUNTIME`; никакого ложного `OFFLINE_PASS`.
7. После фактического G1 сверить `result.json` (`READY_FOR_EXPLICIT_TEST_RUN`, `modelWriteAttempts=0`), `preflight.json` (`sourcePlanHash`, binding, collisions), `plan.json` (typed DAG, host refs), `inventory-before/after`, `SHA256.json`, журнал dispatch. При `BLOCKED` сохранить evidence и точную причину; **не переходить к `--execute`**.
8. G3–G5 только после отдельного разрешения владельца на exact scratch/port/hash; никакого LIVE в текущем цикле.

## 8. Конфликты, независимый readback и rollback

| Событие | STOP и разрешённый следующий шаг |
|---|---|
| `CREATE` timeout/UNKNOWN | `UNKNOWN_STOP`; проверить SQLite scene_id/plan_hash, `GetAllElements/GetDetailsOfElements`, не повторять CREATE и не обходить reservation новым sceneId |
| Slab `CreateSlabs` успешен, `ModifySlabs` неизвестен | Сохранить Slab GUID; проверить фактический material; **не** повторять `CreateSlabs`; две mutations в одном SceneWriter |
| GH/AC одновременно пытаются изменить native | `SECOND_WRITER_STOP`; GH Design Create/Modify отключить; только SceneWriter владеет записью |
| Стена host удалена/изменена, окно/дверь orphan | `HOST_DRIFT_STOP`; AC GUID, ownerWallId, story и children читать обратно; не пересоздавать автоматически |
| GH reference пропал/стал Null | Это **не** команда Delete в AC; `DELETE_UNAUTHORIZED_STOP` |
| Story/material/library drift | Сверить локальный `GetStories`/attributes/parts; `skippedCount>0` = PARTIAL, не считать полный library PASS |
| BREP расхождение / Save/Open drift | `G4_FAIL`; независимый native GUID/type/story/host/material/geometry/BREP diff; Rhino preview не подтверждает AC |
| Требуется rollback | Нет доказанной атомарной AC+GH+Rhino транзакции. Только заранее санкционированный snapshot scratch, freeze writers, read-only reconciliation, затем **отдельно разрешённое** восстановление; SQLite/Undo ≠ автоматический rollback |

**Пять независимых QA-слоёв:** `GH_GEOMETRY` — NURBS/BREP/контуры/площадь/допуски; `AC_NATIVE` — GUID/type/story/host/material/BREP после Save/Open; `IFC_STRUCTURE` — IFC-типы/GlobalId/IfcBuildingStorey/RelVoids/RelFills; `IDS_INFORMATION` — атрибуты и информационные требования; `NORMATIVE_REVIEW` — конкретный СП, редакция, пункт, применимость, измерение и ответственный. Отсутствие evidence = UNKNOWN, не PASS. Полноценные узлы/конструктивные расчёты/сложные NURBS/PolyRoof/holes остаются P1, **не блокируют G1**.

## 9. Реестр точных незакрытых блокеров и передача A5

| ID | Владелец / приоритет | Проблема → безопасное действие → **ГОТОВО** |
|---|---|---|
| I4-15-B01 | Владелец ноутбука + I4 / P0 | Нет фактического G0 runtime → собрать read-only manifest с SHA PLN/APX/checkout/versions/port → `RUNTIME_READY` либо один точный `BLOCKED_<reason>` |
| I4-15-B02 | I4 / P0 | Нет нового authored fixture с проверенными story/material/target/origin → адаптировать существующий PR74 пример **после** G0, без новых полей → валидный typed candidate или `BLOCKED_LOCAL_BINDINGS` |
| I4-15-B03 | I4 / P0 | G1 не запускался → один `--preflight` при разрешённом read-only runtime → реальный `READY_FOR_EXPLICIT_TEST_RUN`, hashes, native writes=0 |
| I4-15-B04 | R1 / P0 | Frozen Tapir 1.5.10 vs local APX/schema/Favorites/libraryPartName не сверены → GetAddOnVersion/APX SHA/registered fields/library `skippedCount` → `SCHEMA_MATCH` или `BLOCKED_LOCAL_SCHEMA` |
| I4-15-B05 | R2 / P0 SOURCE_CLOSED | GH→PR74 bridge не найден в ограниченном scope; GUID/conflicts описаны → принять ручной JSON для G1, не повторять поиски без нового конкретного кандидата → `NOT_FOUND_SCOPED` документирован |
| I4-15-B06 | R3 / P0 SOURCE_CLOSED | GH-BASE не исполнен, но контракт сопоставлен → сохранить 5 QA-verdict slots, ошибки N01–N08; не обещать .gh PASS → `SOURCE_SPEC_DONE` |
| I4-15-B07 | I4 + A5 / P0 | G3/G4/G5 не разрешены и нет native receipts → хранить gate STOP/rollback; разрешение отдельно на exact scratch/port/plan hash → до разрешения `NOT_AUTHORIZED` |
| I4-15-B08 | A5 / P0 | Риск бесконечных исследований → следующий аудит сравнивает B01–B04 и **фактические** G0/G1 evidence, не число SOURCE документов → `STALLED_EXTERNAL_DEPENDENCY` при отсутствии runtime |

**Вопросы A5 для решения по доказательствам, не для немедленного ответа пользователя:** (1) принять `G1=READ_ONLY_PREFLIGHT_REQUIRES_ARCHICAD` и запретить термин «автономный offline»; (2) принять R2 ограниченный `NOT_FOUND` и R3 `SOURCE_SPEC` как завершённые исследовательские поручения, не как BUILD; (3) не требовать нового GH writer/exporter до первого G1; (4) при отсутствии G0 оставить `STALLED_EXTERNAL_DEPENDENCY`; (5) не смешивать `READY_FOR_EXPLICIT_TEST_RUN` с `LIVE_CREATED` и `ACCEPTED`; (6) согласовать отдельное разрешение на G3 только после реального G1, без изменения main/кода.

## 10. Строгие статусы и ограничения

- **SOURCE:** R1/R2/R3 15Z и A5 14:39Z — FOUND/SHA_MATCH; PR74 immutable source и официальный Graphisoft/Tapir — проверены.
- **OFFLINE:** R3 — лишь независимые арифметические примеры `OFFLINE_NUMERIC_ONLY`; **новый G1 preflight не выполнялся**.
- **BUILD:** 0 новых сборок BUILD-01.
- **INSTALLED:** NOT_VERIFIED (нет доступа к ноутбуку).
- **LIVE:** 0 новых native writes; G3 NOT_AUTHORIZED. Исторические LIVE APA не считать этим BUILD.
- **ACCEPTED:** 0.
- **NOT_FOUND (ограниченный scope):** GH→typed PR74 bridge в 12 файлах пяти PR, PR74 PolyRoof/hole verifier, Rhino.Inside AC29 host, atomic cross-app rollback.
- **G0:** BLOCKED_RUNTIME; **G1:** NOT_RUN; **G2:** SOURCE_PARTIAL; **G3:** NOT_AUTHORIZED; **G4/G5:** NOT_RUN.

**Не менялись:** main, исходники, PLN/APX, установленное ПО, merge, платные API, Work/Codex/Arena, NEXT_RESEARCH_PRIORITIES.md. Изменение в GitHub — только этот append-only русский I4 отчёт. Публикация требует отдельного GitHub readback/SHA/commit; до успешной проверки статус `WRITE_BLOCKED`. **MODEL_MODE_NOT_VERIFIABLE.**
