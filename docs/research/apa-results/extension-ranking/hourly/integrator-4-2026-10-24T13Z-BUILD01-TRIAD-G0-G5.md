# APA I4 — интеграция трёх программ для BUILD-01: рабочая схема и G0–G5
**Дата цикла:** 24.10.2026, 13Z (16:20 МСК). **Роль:** I4, инженер-интегратор. **Статус:** SOURCE_INTEGRATION_DESIGN / NOT_EXECUTED. **MODEL_MODE_NOT_VERIFIABLE.**

## 0. Результат, который можно передать A5
Составлена одна ограниченная архитектура: Rhino 8 / Grasshopper вычисляют геометрию и проверяют ограничения; существующий APA PR74 → BIM Graph → SceneWriter → SQLite → Tapir создаёт нативные BIM-элементы в Archicad 29; Graphisoft Live Connection используется в основном BUILD-01 **только для чтения AC→GH**. Никакой второй writer, router или собственный синхронизатор не предлагается.

**Критический пробел:** не найден существующий проверенный автоматический преобразователь произвольного GH DataTree/BREP в точный вход PR74. Поэтому сквозная автоматизация Rhino→GH→PR74→AC сейчас **NOT_FOUND**, хотя отдельные участки технически документированы. Ручная фиксация параметров в уже существующем authored intent возможна как подготовка, но **не** считается автоматической трёхсторонней связкой. Автоматическая двусторонняя BIM-синхронизация и атомарный rollback трёх приложений также **NOT_FOUND**.

**Новый конкретный результат аудита кода:** PR74 — открытый, не объединённый PR, head commit **5a3a9201a715a5528c93bed4a5318e2acb32eea7** на ветке **feature/apa-model-first-building-20261013**. Исследовательская ветка НЕ содержит его scripts/ и examples/ как единый рабочий checkout. PR126, PR131, PR149, PR162 тоже открыты и имеют отдельные head commits. Нельзя складывать возможности разных PR в «установленную единую систему» без доказанного immutable локального checkout и зависимостей. Создание нового merge/кода запрещено. Следующий обязательный шаг — read-only идентификация фактически используемого локального дерева и регистраций команд.

## 1. Входные доказательства текущего часа
| Источник | Файл / immutable blob SHA | Прочитано | Статус |
|---|---|---|---|
| R1 | research-1-20261024T13Z-BUILD01-NATIVE-ROOF-FAVORITES.md / **4be23c3371c572b09d87c80ab882eca699e2bfee** | Да, текущий 13Z | SOURCE |
| R2 | research-2-triad-2026-10-24T13Z-report.md / **e379a5341e41dec5d9d7f7c58d517f1c1acfbbb4** | Да, текущий 13Z | SOURCE |
| R3 | research-3-rhino-gh-2026-10-24T13Z.md / **6a51de7906bbdc6a454547604dbc75f9f077de06** | Да, текущий 13Z | SOURCE |
| P0 | issue #192, https://github.com/dvikt33-ux/safe-bim-layer/issues/192 | Да | Требования G0–G5 |
| Очередь | docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md / **6f074693360231c5cb42ada815984a6b0dd504c0** | Да, только чтение | Канон |
| TRIAD | hourly/research-1-20261023T11Z-TRIAD-PIVOT.md / **896fa3af0953468ca58fca710f32cb926504f582** | Да | Директива |
| Матрица | priority_matrix_20261018.json / **9cb5e6f2a59f80762cc77073eeb10404829af75a** | Да, каталог 61 | Не приемка |
| A5 текущего 13Z | Отчёт аудитора ожидается после фазы :40 | **PENDING**, не MISSING | Поручения прошлого канона действуют |

Все SHA в этой таблице — SHA Git blob из fetch_file, не SHA256 локального PLN. Ни один локальный runtime-факт из GitHub не выводится.

## 2. Фактическая совместимость и минимальный набор
| Компонент | Целевая версия / лицензия | Функция и действие на ноутбуке | Статус |
|---|---|---|---|
| Archicad | 29 build 5101, действующая лицензия | Проверить текущий executable, project path, порт, этажи и libraries; НЕ обновлять | Задано пользователем; локально NOT_VERIFIED |
| Rhino | 8, конкретный SR неизвестен; коммерческая или действующая trial/учебная лицензия | Проверить Help→About, units, absolute tolerance, открытый .3dm; НЕ менять настройки автоматически | NOT_VERIFIED |
| Grasshopper | Встроен в Rhino 8, отдельный платный плагин не требуется | Зафиксировать единственный активный .gh, путь, SHA256, версии компонентов, выключить Design write outputs | SOURCE |
| Graphisoft GH–AC29 Live Connection | **AC29 build 3000**, Windows 16.8 MB, дата 01.10.2025; Rhino 7/8, не Start Edition | При отсутствии — подготовить официальную загрузку, **не устанавливать** до разрешения; для BUILD-01 AC Reference/Deconstruct | SOURCE, INSTALLED_NOT_VERIFIED |
| Tapir Archicad Add-On | локально заявлен **1.5.10**; upstream 1.5.6/1.5.9 содержит PolyRoof | Прочитать GetAddOnVersion, реальный APX SHA, командный каталог и schema; не подменять бинарник | VERSION_PROVENANCE_NOT_VERIFIED |
| APA PR74 / SceneWriter | head **5a3a9201...** в GitHub; локальный commit не установлен | Проверить реальный checkout/SQLite journal/Schema SHA; никаких новых исполнителей | SOURCE |
| Tapir Grasshopper package | upstream WIP, отдельный от Graphisoft Connector | Для основной BUILD-01 НЕ требуется; GH→AC native writer создаёт конфликт | EXCLUDE_MAIN |
| Rhino.Inside | готовый AC29 host не найден | НЕ устанавливать как обязательную часть | NOT_FOUND |
| IfcOpenShell / IfcTester | кандидаты R3: 0.9.0.post1 / 0.9.0; LGPL | Опциональный независимый IFC read-only аудит ПОСЛЕ разрешённого экспорта | SOURCE, INSTALLED_NOT_VERIFIED |

Первоисточники: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://www.rhino3d.com/ ; https://github.com/ENZYME-APD/tapir-archicad-automation ; https://www.rhino3d.com/features/rhino-inside/ ; https://ifcopenshell.org/ .

**Порядок будущего подключения (не выполнен):** 1) read-only инвентаризация существующих Archicad/Rhino/Grasshopper/Tapir/APA; 2) подтвердить лицензии, build/SR, архитектуру и совместимость; 3) при отсутствии Graphisoft Connector — отдельно согласовать официальный AC29 build3000; 4) открыть только разрешённую scratch PLN и отдельный .gh; 5) AC→GH Reference/Deconstruct без Design write; 6) отдельный offline PR74 compile; 7) только после G0–G2 и явного допуска возможен SceneWriter dispatch. Скачивание, установка и LIVE не производились.

## 3. Владение и однонаправленный цикл
**Источник истины по BIM:** Archicad PLN после независимого native readback. **Единственный исполнитель изменения нативных элементов:** существующий SceneWriter (через существующие DynamicCommands/BIM Graph/Tapir). **Источник параметрической геометрии:** GH definition и зафиксированные Rhino объекты; они не владеют Archicad GUID. **Постоянная квитанция:** существующий SQLite ledger SceneWriter, immutable plan hash, native GUID receipts, SHA256 исходных артефактов.

Безопасный маршрут:
1. Rhino 8: исходные NURBS/BREP/контуры/оси, model units и tolerance; объект Rhino имеет Rhino Object ID, НЕ Archicad GUID.
2. GH: DataTree, планарность, замкнутость, самопересечения, топология, геометрические и нормативные ограничения; заморозить определение и входы. GH Path НЕ GUID.
3. Переход GH→PR74: только документированный **типизированный authored intent**, проверенный существующим компилятором. Автоматический GH→PR74 bridge **NOT_FOUND**. Нельзя считать JSON произвольной формы готовым native payload.
4. PR74/BIM Graph: точные story bindings, topological order, ownerWallId через $createdGuid, schema/sourcePlanHash, коллизии, привязки материалов/Favorites/библиотек.
5. SceneWriter/SQLite: intent-before-write; при UNKNOWN/timeout STOP, без повтора CREATE; никакого GH Design writer на том же PLN.
6. Archicad native readback: GUID, BIM type, этаж, host, атрибуты, BREP/связи/сегменты; затем только санкционированный GuardedSave/Close/Reopen и повторная независимая проверка.
7. AC→GH: штатные Element Input/Deconstruct/Sync Changes to GH — **чтение**. Выход не должен замыкаться на GH Create/Modify. AC→Rhino через .3dm export — лишь geometry snapshot, не BIM roundtrip. Content Cache управляет Rhino объектами, не AC BIM.

**Конфликт/цикл:** если GH Design Create/Modify подключён к выходу AC Deconstruct или Tapir GH записывает напрямую, возникает второй writer и потенциальный feedback loop. Режим BUILD-01 требует отключённых выходов GH-native write и запрета Bake/Push/Purge в основной модели. **Synchronize=False не удаляет ранее созданные AC-элементы и не является rollback.** Не делать удаления по пустому GH output. При изменении/удалении native элемента извне — inventory drift → STOP + read-only reconcile. Отсутствие доказанного 3-way GUID-preserving conflict merge = NOT_FOUND.

## 4. Точные контракты и существующий код
| Контракт | Вход → выход | Фактически найденное ограничение |
|---|---|---|
| GH source record (проектная спецификация, не существующий API) | source_key, geometry_role, geometry_kind, units, abs_tol_m, story_index, z_abs_m/z_rel_m, host_source_key, material_key, expected_bbox/area/volume, source .3dm/.gh SHA | Прямой штатный GH→PR74 parser/adapter NOT_FOUND. Не вводить новый router |
| PR74 authored intent | schemaVersion apa-authored-project/1, projectId, units=meters, brief.stories, rooms, constraints, targetProjectPath, CSE/material/geometry | Пример: examples/accelerator/model-first-building.json в PR74; исторический fixture, не копировать target/координаты в новую задачу |
| BIM Graph | graph.operations: id, command, params; $createdGuid host references; executionOrder/sourcePlanHash | Проверено в scripts/archicad_bim_graph.py PR74, blob **87fc7476c9079a189c8b8e31ae3c6beaf6712dd3** |
| SceneWriter | preflight/binding/schemaSha256/expected hash → SQLite reservation → one native call → verified GUID; без automaticRetry | scripts/archicad_scene_run.py PR74, blob **ca91c1cfc41cee763c62d1f3a70337d74fbafd53** |
| Базовые Create | CreateWalls/Slabs/Columns/Windows/Doors/Objects | ALLOWED_WRITES; реальная локальная schema/INSTALLED не проверена |
| Расширенные Create | CreateRoofs/Beams/Morphs/MEP — только opt-in NativeAdapter | EXTENDED_WRITES, не включаются одним названием; нужен typed adapter |
| Connected Roof | CreateRoofs → NativeAdapter.verify требует **roofClass=SinglePlane**, Basic, angle, pivotLine, polygon, material | scripts/archicad_connected_components.py PR74, blob **c5a99f59a90369ff622807574677cf11ca0a2225**; MultiPlane не проходит текущий verifier |
| Connected Beam | CreateBeams → NativeAdapter: explicit straight Basic, BeamSegment host/material/closed BREP | Готовый SOURCE-контракт; единый G1-компилятор здания с ним не доказан |
| Slab | CreateSlabs polygon + absolute level, floorIndex, thickness, referencePlaneLocation | scripts/archicad_authored_native_plan.py PR74, blob **f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7**; hole loops и явный Basic material CREATE через текущий путь NOT_VERIFIED |
| Уровни | GetStories nativeIndex/floorId/level ↔ authored story | CreateSlabs.level абсолютный; Wall zCoordinate при floorIndex зависит от этажа; нельзя смешивать |
| Readback | GetAllElements, GetDetailsOfElements, GetModelDumpV1, Get3DBoundingBoxes, hosted/child relations | GH Deconstruct BREP документирован только для Beam/Column/Slab/Wall/Mesh/Zone/Shell/SinglePlaneRoof; список поверхностей ≠ доказанный замкнутый solid |

**Критический P0 по кровле:** upstream Tapir 1.5.9 CreateRoofs без pivotLine способен создавать API_PolyRoofID с levels/eavesOverhang. Но существующий PR74 NativeAdapter.verify требует SinglePlane, а текущие opt-in writes не содержат ModifyRoofs. **Следовательно PolyRoof native API = SOURCE_FOUND; end-to-end through existing SceneWriter = NOT_FOUND.** Нельзя обойти SceneWriter прямым GH/Tapir вызовом или объявить готовым multi-plane writer. Проверять существующие другие approved adapter branches read-only, а не придумывать новый.

**Отдельный P0 по веткам:** PR74/126/131/149/162 имеют разные открытые head branches; нет доказанного единого immutable объединённого executable tree. Пример успешного 21-element LIVE из PR74 — историческая ограниченная квитанция, НЕ новый BUILD-01 ACCEPTED.

## 5. Десять маршрутов BUILD-01
| № | Операция / программа / готовый путь | Завершение и readback; критерий ГОТОВО | Текущий статус |
|---|---|---|---|
| 01 | Этажи: AC Story Settings + GetStories → PR74 storyBindings → GH reference | floorId/index/elevation совпадают до и после Save/Open; никаких скрытых этажей | SOURCE; программный GH Story writer в PR74 NOT_FOUND |
| 02 | Стены: Rhino/GH оси/контур → authored PR74 CreateWalls → SceneWriter | Wall GUID, native Wall, height/thickness/material/story, ненулевая длина, solid BREP, no collision | SOURCE, OFFLINE_NOT_RUN |
| 03 | Перекрытия: GH planar outer/holes → PR74 CreateSlabs только для поддержанного прямоугольного/typed контура | Slab GUID, absolute Z, floor, thickness, material/default, holes, closed BREP | SOURCE; GH holes→PR74 NOT_FOUND |
| 04 | Колонны: GH points/section → existing CreateColumns | Column GUID, story, section, material, children, BREP | SOURCE; INSTALLED_NOT_VERIFIED |
| 05 | Балки: GH axis/section → connected NativeAdapter CreateBeams через тот же SceneWriter | Beam + BeamSegment GUID, host, profile rotation, material, BREP; связка с authored compiler отдельно | SOURCE; unified G1 NOT_VERIFIED |
| 06 | Простая кровля: GH planar face → PR74 CreateRoofs с pivotLine, Basic | SinglePlane Roof GUID, pitch, elevation, pivot, material, wall-roof junctions, BREP | SOURCE, исторический PR74 bounded LIVE, новый G3 NOT_RUN |
| 07 | Многоскатная кровля: GH ridge/eave planes → upstream Tapir CreateRoofs без pivotLine | Один native PolyRoof GUID, уровни скатов, гребни/ендовы, materials, holes, Save/Open | **SOURCE_FOUND, ROUTE_NOT_FOUND** через PR74 guard |
| 08 | Окна/двери: GH host geometry + opening dimensions → CreateWindows/Doors через $createdGuid | hosted GUID, ownerWallId, ширина/высота/sill, library identity, void, BREP | SOURCE; generic Opening NOT_FOUND |
| 09 | Библиотеки/атрибуты: AC Library Manager + GetFavoritesByType/read-only attribute list | pinned library part name+ownUnID, favorites, material/composite GUID; defaults drift controlled | SOURCE; import/apply являются writes |
| 10 | QA: GH planarity/boolean/clearance → AC native inventory → опциональный IFC + IfcOpenShell/IfcTester IDS | native GUID/type/story/host/material/BREP отдельно от IFC GlobalId; IDS отдельно от геометрии/СП | SOURCE; local tools/export NOT_RUN |

**Универсальная проверка каждой будущей операции:** источник и программа → точный typed intent → frozen hash → single writer → native GUID receipt → BIM type/story/host/attrs/BREP → Save/Close/Reopen → независимое сравнение → STOP/restore scratch snapshot при ошибке. Отсутствие реального reopen запрещает ACCEPTED.

## 6. Контрольные ворота G0–G5
| Gate | Требуемый результат / критерий ГОТОВО | Фактический статус |
|---|---|---|
| **G0** | Read-only manifest: AC29 build5101, порт, активный PLN path+SHA, scratch identity, local checkout SHA, Tapir GetAddOnVersion/APX SHA/registered schema, stories, Favorites/materials/libraries, Rhino8 SR/units/tolerance/.3dm SHA, .gh SHA, Graphisoft LC build/registration. Нет незарегистрированного второго writer | **BLOCKED_RUNTIME** — нет доступа к ноутбуку/GUI/APX/PLN |
| **G1** | ОДНО новое typed задание на минимум 2 этажа с Wall/Slab/Roof/Window/Door (+ Beam/Column условно), offline compile реально запущен: DAG/toposort/host refs/schema/plan hash/collision PASS, нативных writes=0 | **NOT_RUN**; исторический fixture не засчитывать |
| **G2** | Таблица точных команд по фактической local Tapir schema, floor/story convention, material/Favorites/library, beam/roof adapters, holes/host, no duplicate GUID, ownership. Неподдержанные поля исключены или блокированы | **SOURCE_PARTIAL**; PolyRoof и Slab holes блокируют расширенную модель |
| **G3** | Только отдельное разрешение на конкретные scratch PLN+port+plan hash, один SceneWriter/SQLite; actual native GUID receipts, 0 неопознанных элементов; UNKNOWN → STOP, never retry CREATE | **NOT_AUTHORIZED / NOT_RUN** |
| **G4** | GuardedSave → GUI Close → no-open check → Open → independent inventory GUID/type/story/host/material/children/BREP + native junction/collision, immutable receipts | **NOT_RUN** |
| **G5** | Новое исходное задание и новый scratch, другие контуры/высоты/проёмы, повтор G1–G4, доказательство не-fixure | **NOT_RUN** |

**План отката:** до G3 сохранить независимую исходную scratch копию и SHA; при ошибке остановить оба канала GH→AC и APA writes, сохранить SQLite/evidence, read-only inventory/reconcile, НЕ повторять CREATE; только после отдельного разрешения восстановить scratch snapshot. Undo, Synchronize=False, GH delete и IFC import не являются подтверждённым транзакционным rollback.

## 7. Практический чек-лист для владельца ноутбука — только инструкция, НЕ выполнено
1. Проверить лицензию Archicad 29, About/build5101, активный PLN и порт; сохранить идентификаторы без изменения BDD.
2. Проверить Rhino 8 About/Service Release, действующую лицензию, Units и Absolute Tolerance; путь/хеш .3dm.
3. Открыть Grasshopper только для read-only инвентаризации одного .gh; записать SHA и список компонентов, не Bake/Push/Purge.
4. Проверить в Add-On Manager Graphisoft Grasshopper–Archicad **29** Live Connection build3000 и Tapir; если нет — оформить список официальных установщиков для отдельного разрешения, не ставить.
5. Read-only Tapir GetAddOnVersion, GetStories, GetProjectInfo, GetFavoritesByType, список команд/схема; локальные APX и PLN SHA.
6. Проверить фактический APA Git checkout commit, наличие scripts/archicad_project_accelerator.py, archicad_bim_graph.py, archicad_scene_run.py, archicad_connected_components.py, schema snapshot и ledger. **Не смешивать открытые PR вручную**.
7. Подготовить НОВЫЙ изолированный scratch и отдельное утверждённое здание; не использовать исторические пути из examples/accelerator/model-first-building.json как автоматическое разрешение.
8. G1 выполнить только существующий offline CLI PR74 (без --execute) на проверенном structured intent; сохранить stdout/plan hash/graph/schema evidence. Это будущая операция, в данном цикле не запускалась.
9. G2 составить точную матрицу native команд и типовых ограничений; до доказанного bridge GH→PR74 оставить ручной authored intent и статус PARTIAL.
10. G3/G4/G5 — только после отдельного scope/разрешения; любое автоматическое LIVE до этого запрещено.

## 8. Контрааудиты I4
**CA-I4-01: исходники и установленность.** Проверены реальные GitHub PR metadata: PR74 head 5a3a9201..., PR126 head f12aeba0..., PR131 head 75ae71dc..., PR149 head 4c119428..., PR162 head f7c37b84..., все OPEN, не merged. Исследовательская ветка содержит отчёты, но не является готовой локальной исполнимой комбинацией этих PR. Upstream Tapir 1.5.9 PolyRoof не равен локальному бинарнику с заявленной версией 1.5.10. Вывод: G0 BLOCKED; INSTALLED и LIVE не заявлять.

**CA-I4-02: инженерная воспроизводимость и семантика.** Противопроверка: GH Slab with holes ≠ подтверждённый PR74 Slab holes; GH planar roof facets ≠ единый native PolyRoof; Rhino .3dm Hotlink ≠ native Wall/Roof; IFC GlobalId ≠ доказанный Archicad internal GUID; Deconstruct BREP surfaces ≠ closed manifold; GH Sync Changes to GH ≠ трёхсторонняя запись. Существующий PR74 Roof verifier явно SinglePlane. Отсутствуют G1 offline run, G3 native receipts, G4 Save/Open. Вывод: BUILD-01 не готов; автоматическая трёхсторонняя схема NOT_FOUND.

## 9. Передача A5: адресные блокеры и поручения
| ID / приоритет | Блокер и владелец | Следующий безопасный шаг / критерий закрытия |
|---|---|---|
| I4-P0-01 / 100 | Нет runtime manifest — A5→R2/владелец ноутбука | Read-only G0: immutable checkout SHA, Tapir APX/schema, LC build, Rhino SR, GH SHA, PLN/port/story. ГОТОВО = полная таблица + hashes, без model writes |
| I4-P0-02 / 100 | Нет автоматического GH→PR74 typed input — A5→R2/R3 | Найти существующий готовый, уже допустимый GH exporter / PR74 parser. ГОТОВО = exact schema mapping + offline compiler PASS; если нет — NOT_FOUND, не писать новый router |
| I4-P0-03 / 98 | PolyRoof upstream, но PR74 SinglePlane verifier — A5→R1/R2 | Проверить готовый другой существующий SceneWriter adapter на immutable branch, локальную команду и offline schema. ГОТОВО = без изменения кода multi-plane typed verification, иначе BLOCKED |
| I4-P0-04 / 96 | Невозможно считать отдельные PR единой установкой — A5→R1/I4 | Read-only dependency map и фактический checkout; не merge. ГОТОВО = один доказанный commit/installed registry для минимального BUILD-01 |
| I4-P0-05 / 94 | G1 нового здания не запускался — A5→I4 | Подготовить реальный approved учебный intent и запустить существующий offline compile после G0. ГОТОВО = plan hash + DAG/schema/host/geometry receipts, 0 writes |
| I4-P1-06 / 90 | Slab holes/material defaults и roof/door QA — A5→R3 | Точные supported fields из локальной schema и readback; optional IFC/IDS отдельно от native BREP; ГОТОВО = доказанный контракт или NOT_FOUND |
| I4-P1-07 / 88 | Ownership conflicts / rollback — A5→R2 | Проверить GH Design writer disabled, AC→GH read-only, SQLite unknown reconcile; ГОТОВО = не возникает дубликатов и write cycles на схеме, LIVE только с допуском |

**Статусы:** SOURCE — интеграционная карта по 3 отчётам и исходникам; OFFLINE (новый) = 0; BUILD (новый) = 0; INSTALLED = NOT_VERIFIED; LIVE (новый) = 0; ACCEPTED (новый) = 0; 3-way native sync = NOT_FOUND; cross-app atomic rollback = NOT_FOUND. Исторические PR74 21-element LIVE и прочие receipts не перенесены в новую приёмку. **MODEL_MODE_NOT_VERIFIABLE**.

**Границы:** только исследовательская документация. Не изменялись main, исходный код, PLN/APX, библиотеки, установки, платные API, Work/Codex/Arena, merge; LIVE не выполнялся. NEXT_RESEARCH_PRIORITIES.md и PROJECT_PLAN rev182 только читались.
