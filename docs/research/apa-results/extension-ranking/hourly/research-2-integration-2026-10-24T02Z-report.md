# APA №2 — 2026-10-24 02Z: BUILD-01 / граница no-code Rhino8→GH→PR74
**Статус:** SOURCE_ONLY; не выполнялись OFFLINE, INSTALLED, LIVE или ACCEPTED. MODEL_MODE_NOT_VERIFIABLE.
**Цель:** воспроизводимая нативная BIM-сборка в Archicad 29 build5101 + Tapir 1.5.10 + Rhino 8/Grasshopper, без нового writer/router/synchronizer. Исходные файлы, main, PLN/APX не менялись. Публикация только в исследовательской ветке.

## НОВЫЙ P0 — пространственный контракт PR74 не принимает произвольную Rhino-геометрию
Сверены immutable PR74 `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, `archicad_semantic_spatial.py` и `archicad_authored_native_plan.py`:
1. `layout.outline` и каждый `layout.rooms[].rectangle` — строго `xMin/xMax/yMin/yMax`; не полигоны/кривые. Компонент `layout.axes` допускает только `X` или `Y`, `bearingLines` лежат на этих осях и обязаны совпасть с краем авторского прямоугольного помещения. Толщина базовой несущей стены 0.15–0.60 м, длина ≥1 м. Это **прямоугольный, ортогональный базовый spatial compiler**, не универсальный конвертер BREP.
2. На каждый этаж `archicad_authored_native_plan.py` создаёт **один четырёхугольный Slab** по общему прямоугольному footprint, без поля holes. Slab `level` абсолютный. Базовые Walls следуют bearingLines. Свободная криволинейная/многоконтурная плита Rhino **не переносится автоматически** через этот путь.
3. `nativeComponents` добавляет `CreateColumns/CreateDoors/CreateWindows/CreateWalls/CreateRoofs` (один roof/wall на step при заданных ограничениях). **Нет** `CreateSlabs`, `CreateBeams`, `CreateOpenings`, `SetStories`, библиотечного writer. `CreateRoofs` требует `pivotLine`, `structureType=Basic`, `buildingMaterialId` — это SinglePlane route; не MultiPlane native roof. Наличие этих команд в Tapir само по себе не снимает allowlist PR74.
4. Значит обещание «любая модель Rhino → одна JSON → полная нативная BIM» **НЕ ДОКАЗАНО**. Существующий маршрут достаточен лишь для ограниченного BUILD-01 макета (прямоугольный основной контур + поддержанные отдельные компоненты), пока G1/G2/G4 не пройдены.

## Готовый GH маршрут без нового кода — 7 шагов
1. В Rhino 8 открыть конкретный `.3dm`, проверить document units, transform к метрам, source SHA, имя слоя, Rhino Object ID и атрибутный User Text; в GH открыть конкретный `.gh`, зафиксировать SHA и версии компонентов. Не путать Rhino ID с AC GUID.
2. Для каждого исходного Rhino объекта использовать атрибуты `APA_Owner`, `APA_Type`, `APA_Story`, `APA_ExternalId` как **согласованную дисциплину именования**, а не существующий штатный BIM-контракт. Значения `APA_Owner=APA`, `APA_Type=Wall/Slab/Roof/Column/Opening`; обязательны non-empty, уникальный ExternalId, известный story, whitelist type. Нельзя автоматически считать User Text достоверным.
3. Встроенный GH1/Rhino8: `Query Model Objects` с Layer/Name → `Group Content` по `Model Object → User Text → APA_Story` → `Match Text Filter` (Equals `APA_Owner=APA` и `APA_Type`) → `Filter Content`. Для атрибутов использовать `Model Object`, а не только голый Brep. Это **выбор ветви данных**, НЕ автоматический выбор приложения.
4. По геометрии разрешать только то, что понимает authored PR74: rectangular `outline/rooms`; X/Y axes и прямолинейные ортогональные bearingLines; отдельные SinglePlane Roof с pivotLine; окна/двери с host `$createdGuid`. Несоответствие геометрии — STOP/NOT_FOUND, не приближать форму незаметно.
5. Для JSON использовать существующий `examples/accelerator/model-first-building.json` как **схему-образец**, jSwan `Serialize Keys and Values` для точных `x/y` и List Access для массивов. Не подавать raw Point (`X/Y/Z`) как `{x,y}`; не включать `Lock Structure` там, где `null` недопустим. Версия jSwan на Rhino8 не проверена; готовый экспорт полного `.json` из GH в файл без дополнительных действий НЕ ДОКАЗАН.
6. Сверить `schemaVersion=apa-authored-project/1`, `units=meters`, `brief.targetProjectPath=RUN.EXPECTED_PATH`, actual `GetStories` bindings, native BuildingMaterial GUID, уникальные IDs, host references и `nativeGeometryAudit` bool. Для authored нельзя `mode=offline`; только штатный read-only `preflight` после G0.
7. Только при отдельном WRITE разрешении SceneWriter/SQLite → Tapir → Archicad. GH–AC `Synchronize=True` для APA-owned элементов запрещён (иначе второй writer). После каждой завершённой операции readback, Save/Open, IFC/BREP/материалы/хозяева и reconciliation при UNKNOWN. Сейчас **не запускать**.

## Девять операций: программа → инструмент → направление → контроль → ГОТОВО
| № | Операция и выбор программы | Конкретный путь и ограничение | Критерий ГОТОВО / текущий статус |
|---|---|---|---|
| 1 | Rhino8/GH: исходная геометрия и атрибуты | Query Model Objects → Group/Match/Filter → jSwan → authored JSON; только прямоугольная базовая layout | `.3dm/.gh/JSON` hashes, units, no missing/duplicate IDs, contract pass; SOURCE_ONLY |
| 2 | AC29: этажи | GetStories read → GH story mapping → authored existing indices; SetStories Tapir WRITE не wired | storyId/nativeIndex/floorId/level exact после reopen; EXISTS_NOT_WIRED |
| 3 | GH→AC29: базовые стены | GH X/Y bearingLines → authored CreateWalls; произвольные диагонали только отдельным nativeComponents CreateWalls внутри envelope | native Wall GUID, Z offset, thickness, material, joints; SOURCE_WIRED_NOT_RUN |
| 4 | GH→AC29: перекрытия | authored CreateSlabs — один rectangular polygon на этаж, absolute level; holes/freeform не wired в этом входе | native Slab GUID, Z, thickness, material, holes, BREP; RECT_ONLY / HOLES_NOT_WIRED |
| 5 | GH→AC29: колонны и балки | nativeComponents CreateColumns (точка и этаж), CreateBeams отсутствует в allowlist | Column GUID/dimensions; Beam route NOT_WIRED |
| 6 | GH→AC29: кровли | nativeComponents CreateRoofs Basic SinglePlane с pivotLine; MultiPlane без pivotLine не пройдёт проверку | Roof GUID/slope/polygon/SEO/BREP; SinglePlane SOURCE_ONLY; MultiPlane NOT_FOUND |
| 7 | GH→AC29: проёмы | CreateDoors/CreateWindows с host $createdGuid и доступными GDL parts; Generic Opening нет в allowlist | host GUID, sizes, sill, library parts, Save/Open; CONDITIONAL |
| 8 | AC29→GH/Rhino: обратные изменения | Graphisoft Deconstruct/Send Changes лишь для поддержанных параметров; Rhino Object ID не AC GUID | change-source+target GUID+param hash+BREP, no overwrite; PARTIAL, FULL TRIAD NOT_FOUND |
| 9 | AC29+GH: QA/нормативы/откат | Native readback → GUID/IFC/BREP; GH численные ограничения; protected PLN Save/Close/Reopen; при UNKNOWN только READ | проверены BIM тип, этаж, GUID, материалы, BREP, коллизии, нормы с редакциями; SOURCE_ONLY, NO CERTIFICATION |

## Identity / ownership / transaction
Crosswalk (read-only): `source3dmSha | rhinoObjectId | APA_ExternalId | APA_Type | APA_Story | ghDefinitionSha | authoredStepId | ACNativeGUID | IFCGlobalId | owner | geometryHash | attributesHash`. Ни одно поле не объявляется эквивалентом другого. Если `ACNativeGUID` неизвестен до CREATE, хранить `PENDING`, а не выдуманный GUID.
**Граница транзакции:** отключить GH Solver/AC Synchronize на время редактирования → стабилизировать геометрию и данные → сформировать новый JSON/planHash → проверить G0/G1/G2 → после отдельного допуска одна owned native mutation → readback → Save/Open. При удалении, смене типа, изменении этажности, конфликте writers, несоответствии ID, цикле или UNKNOWN: STOP, только read-only reconciliation. Трёхпрограммный atomic commit и rollback **NOT_FOUND**.

## Версии/лицензии/доказательства
- Graphisoft GH–AC29 Live Connection: **build3000**, Windows, Rhino7/8, официальный пакет **01.10.2025**. AC30 build3000, опубликованный **07.10.2026**, — **не** замена AC29. Бесплатное дополнение не включает коммерческие лицензии Rhino/Archicad; точный локальный установленный build не проверен.
- Rhino8 Grasshopper1: встроенные Query Model Objects/Group Content/Match Text Filter/Filter Content/Model Object; Rhino8 коммерческий, GH включён. Локальный Rhino SR не проверен.
- jSwan: MIT; готовый JSON-конструктор, Rhino8 совместимость установленной версии NOT_VERIFIED. eleFront/Hops не нужны для минимального маршрута, их риски из №1 сохраняются.
- APA PR74 immutable `5a3a9201a715a5528c93bed4a5318e2acb32eea7`, draft; Tapir pinned 1.5.10 — SOURCE, фактическая APX/command registration NOT_VERIFIED.
- 28 документарных проверок в соседнем `research-2-integration-2026-10-24T02Z-checks.md` и два контрааудита в `research-2-integration-2026-10-24T02Z-audits.md`. Это не 28 сайтов и не OFFLINE_PASS.

## Gate status
G0=BLOCKED_RUNTIME; G1=NOT_RUN; G2=SOURCE_PARTIAL; G3=NOT_AUTHORIZED; G4=NOT_RUN; G5=NOT_RUN.
SOURCE=28 проверок; OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0.
**Следующий P0:** не подменять произвольную Rhino BREP прямоугольным макетом; подготовить **явную таблицу поддерживаемой геометрии** для BUILD-01, затем разрешённый read-only G0+authored preflight. MultiPlane, native Beam, freeform Slab, полноценная трёхсторонняя sync — NOT_FOUND/NOT_WIRED.

## Первичные ссылки
- issue: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- pr: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
- next: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
- pivot: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- n1: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T02Z-TRIAD-NATIVE-RHINO8-ROUTING-HOPS-ELEFRONT.md
- n3: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md
- mat: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
- spatial: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_semantic_spatial.py
- native: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py
- accel: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py
- example: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/examples/accelerator/model-first-building.json
- prdoc: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/docs/APA_MODEL_FIRST_BUILDING.md
- mcneel: https://www.rhino3d.com/docs/guides/grasshopper/group-sort-filter/
- attr: https://www.rhino3d.com/docs/guides/grasshopper/object-attributes/
- gs: https://www.graphisoft.com/de-de/downloads/add-ons/rhino-grasshopper/
- js: https://github.com/andrewheumann/jSwan/blob/master/README.md
- lic: https://github.com/andrewheumann/jSwan/blob/master/LICENSE
