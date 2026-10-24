# APA №2 | 2026-10-24 10Z | BUILD-01: конфликт GH-native writes с неизменяемым inventory SceneWriter

**Объект:** [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). **Режим:** SOURCE_ONLY. Среда по заданию: Windows 11, Archicad 29 build 5101, Tapir 1.5.10, Rhino 8 (Service Release неизвестен), Grasshopper. Ни один локальный процесс не опрашивался. Нет установки, LIVE, изменения main, кода, PLN/APX, merge. MODEL_MODE_NOT_VERIFIABLE.

## 1. Новый результат P0: GH Live Connection не может незаметно стать вторым писателем в BUILD-01

Прочитаны immutable [connected_components.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L323-L425) и [фрагмент 428–551](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L428-L551).

**Доказанный на SOURCE уровне инвариант:** `native_context` читает `GetAllElements` через `inventory_guids`. В режиме `preflight/execute` `main` требует `before_context['inventory'] == record.context.inventory` (если он есть) либо `source.inventory`. Функция `verify_inventory` после записи требует точное равенство ожидаемого множества GUID (source + новые typed + зарегистрированные дочерние). `retained_geometry_signatures` включает BREP, Surface GUID, home story, type, relationships, materials. При несовпадении — `ACCEPTED_WHOLE_INVENTORY_DRIFT`, `CONNECTED_INVENTORY_HAS_UNOWNED_OR_MISSING_GUIDS` или `RETAINED_NATIVE_GEOMETRY_CHANGED_DURING_BATCH`.

**Следствие (вывод по коду, НЕ LIVE):** если Graphisoft GH Design создаёт дополнительный native Beam/Wall/Roof **в том же PLN после фиксации исходного receipt**, это добавляет GUID вне принятого inventory и блокирует следующий connected preflight. Если GH изменит геометрию уже удерживаемого GUID, проверка retained BREP также может блокировать продолжение. Даже «не трогаем APA-owned, GH пишет только свои» не является автоматически безопасным режимом для этого исполнителя. Отдельный GH-owned элемент, созданный до исходного receipt и включённый в baseline, — другой случай, но автоматическое обновление его геометрии также не проходит без проверки retained signatures. Универсальный механизм включения GH-generated GUID в APA ledger без нового writer/router/sync — **NOT_FOUND**.

**Практическое решение без кода:** на BUILD-01 PLN GH–AC Live Connection использовать как **read-only AC→GH** через `Set one/multiple Element in Archicad` → `Deconstruct [Wall/Slab/Beam/...]` → `Extract Settings` → `Send Changes`. Никаких GH Design/Document компонентов с Synchronize=True для этого PLN. Rhino Content Cache Push/Bake — запись **только в Rhino**, не в Archicad; без отдельного разрешения не запускать. Прямой GH native writer допустим лишь в отдельно санкционированном scratch-контуре, не в BUILD-01 ledger.

Источник Graphisoft AC29: [официальный GC.pdf](https://help.graphisoft.com/AC/29/INT/GC.pdf), раздел Deconstruct: Set one/multiple и Send Changes; Deconstruct Roof только Single-Plane. [Synchronize parameter](https://help.graphisoft.com/AC/29/INT/GC.pdf) TRUE=автоматическая генерация/обновление native, FALSE=Null и без генерации; FALSE не доказывает ни транзакцию, ни удаление/сохранение предыдущего элемента. Историческая [Graphisoft Teamwork](https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680): при delete/recreate теряются SEO и меняются GUID; это не испытание AC29.

## 2. Проверенные версии, лицензии и направления

| Средство | Версия / лицензия | Направление | Граница доказательства |
|---|---|---|---|
| [Graphisoft GH–AC29 Live Connection](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) | AC29 build **3000**, Windows, Rhino 7/8; опубликован 01.10.2025; add-on доступен для скачивания, Archicad/Rhino требуют лицензии | GH Design→native AC; AC element reference/Deconstruct→GH через Send Changes | НЕ полный bidirectional merge; локальная совместимость с AC29 build5101 и Rhino SR не проверена |
| [Rhino 8 Grasshopper](https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm) | входит в лицензируемый Rhino 8 | Rhino↔GH geometry; `-GrasshopperPlayer` запускает существующий GH | GH solve/Player не AC commit; side effects возможны |
| [Rhino Content Cache](https://discourse.mcneel.com/t/content-cache-updated-guide/181883) | встроен в Rhino 8, точный SR обязателен | GH Push/Pull ↔ Rhino objects | Rhino Object ID ≠ Archicad GUID; Push/Bake/Purge side effects |
| [Content Cache issue RH-84658](https://discourse.mcneel.com/t/content-cache-push-doesnt-update-material-data/194222) | баг материалов 8.13, исправлен **8.14** по сообщению McNeel | GH→Rhino material | неизвестный Rhino SR — запрет объявлять материальную идентичность доказанной |
| [Wasp MCP v0.5.2](https://github.com/liangjunglj-cpu/wasp-mcp/releases/tag/v0.5.2) | MIT для bridge/server code, knowledge data отдельные условия; Rhino8 Windows | MCP→GH discovery/solve; `gh_wait_idle` | idle ≠ AC commit; `gh_bake` отдельный Rhino writer; НЕ устанавливать |
| [EaseHee rhino-mcp v0.6.0](https://github.com/EaseHee/rhino-mcp/releases/tag/v0.6.0) | MIT, Python>=3.11, rhino3dm>=8.9, Rhino8 bridge | MCP↔Rhino/GH; `RHINO_MCP_FORCE_MODE=bridge` fail-closed | без проверки active .3dm/PLN; standalone fallback при auto; НЕ устанавливать |
| [IfcDiff](https://docs.ifcopenshell.org/ifcdiff.html) | docs 0.9.0post1, версия установленного пакета неизвестна; лицензия конкретной сборки здесь не сверена | IFC old/new→added/deleted/changed по GlobalId | только QA, не AC native writer/merge; representation false positives |
| APA PR74/SceneWriter/Tapir | immutable code ref `5a3a9201...`, ожидаемый Tapir 1.5.10, фактический runtime не проверен | typed BIM DAG→SceneWriter/SQLite→AC native | единственный исполнитель BUILD-01; no new writer |

**Важная терминология:** build3000 относится к add-on Graphisoft, build5101 — к Archicad; равенство build не требуется, но локальную работоспособность этой пары доказывает только G0.

## 3. Воспроизводимый протокол G0–G5 (пока без исполнения)

**G0 / read-only:** подтвердить активный AC port и GetProjectInfo (путь PLN), build5101, Tapir AddOnVersion 1.5.10, фактический набор команд/schema/APX SHA, native stories index/floorId/elevation, scratch PLN path/SHA, материалы и Favorites. Rhino: exact 8 SR, PID, active .3dm path/SHA/units; GH: .gh SHA, plugin list и все компоненты с write side effects; GH–AC connection build3000. Ожидаемая связка PR74/connected CLI жёстко привязана к scratch и порту **19724** для connected preflight. `IsAlive` сам по себе не идентифицирует PLN. При расхождении — `BLOCKED_RUNTIME`, никаких записей.

**G1 / offline:** одно исходное типизированное задание, 2 этажа с точными абсолютными Z, native walls/slabs, hosted doors/windows, roof, optional columns. `compile_authored_intent` + существующий `compile_graph` → DAG/order/schema/planHash; не объявлять OFFLINE_PASS до фактического запуска. Непрямоугольный BREP Rhino не является валидным authored intent автоматически.

**G2 / read-only preflight:** после подтверждённого accepted исходного receipt отдельно запустить существующий connected CLI `--source <receipt> --intent <typed.json> --mode preflight --output <новый_каталог>`; для Beam `enabled:['beam']`, `CreateBeams` с точными параметрами. Preflight должен вернуть `CONNECTED_NATIVE_PREFLIGHT_PASS`, `modelWriteAttempts=0`; если GH добавил GUID — FAIL inventory. Эта команда **не запускалась**. До наличия G0/G1 её выполнять нельзя.

**G3 / LIVE:** требуется отдельное разрешение, отдельный чистый scratch, точный confirm-plan-hash, SceneWriter и отсутствие GH-native writer. Никаких автоматических retry после неопределённой записи. В этом исследовании G3=NOT_AUTHORIZED.

**G4 / Save/Close/Reopen:** после разрешённого G3 отдельно доказать сохранение и повторное чтение native GUID, kind, floor, hostWall, materials, closed BREP, roof SEO, сравнение inventory и IFC. Наличие SQLite receipt без повторного открытия — не G4.

**G5 / независимая приёмка:** второе отличное задание, сравнение геометрии и нативной семантики; IfcDiff на двух IFC только дополнительный контроль. Нормативы — отдельные версии правил и фактические расчёты; `schema pass` не экспертиза СП.

**Откат:** до G3 — отсутствие записи. После возможного G3 — восстановление заранее проверенной копии PLN и согласованной версии .3dm/.gh/ledger; это не атомарный rollback всех программ. При неизвестном результате записи STOP+read-only reconcile.

## 4. Десять приоритетных операций BUILD-01

Стандарт маршрута: **выбор программы/готового инструмента → изменение → завершение → направление синхронизации → проверка → Save/Open/откат**. Все ниже SOURCE-проекты; не INSTALLED/LIVE.

| № | Операция и готовый инструмент | Передача / завершение | Приёмка / ограничение / статус |
|---|---|---|---|
| 01 | **Этажи:** AC29 story settings + PR74 `storyBindings` (nativeIndex/floorId/elevation); GH читает reference | AC stories→PR74 read binding→GH read-only; не создавать этаж по Z геометрии | exact label/index/elevation, Save/Open; программное native CreateStory в этом маршруте **NOT_FOUND** |
| 02 | **Стены:** PR74 `CreateWalls`; `prepare_building_parameter_edit`→`ModifyWalls` **только height** | typed authored→SceneWriter→AC; AC→GH `Deconstruct Wall`+`Send Changes` только reference | GUID/type/height/thickness/material/BREP, Save/Open; GH→APA auto-sync **NOT_FOUND** |
| 03 | **Перекрытия:** `CreateSlabs` по одному прямоугольному footprint на этаж; `level` абсолютный Z | typed→SceneWriter→AC; GH read-only `Deconstruct Slab` | story/level/thickness/material/holes/BREP; произвольный Rhino polygon, slab holes в authored входе **NOT_FOUND** |
| 04 | **Колонны:** `nativeComponents.CreateColumns` при точных floor/XYZ в outline | typed→SceneWriter→AC; GH reference/deconstruct | GUID+ColumnSegment, story/material/BREP; GH mutation той же модели запрещена |
| 05 | **Балки:** **отдельный existing connected CLI** `adapters(['beam'])`→`CreateBeams` | только после accepted source receipt; offline→preflight→разрешённый execute через тот же SceneWriter | parent Beam/BeamSegment GUID, axis/profile/material/closed BREP; one-shot authored Beam **NOT_FOUND** |
| 06 | **Простая кровля:** `nativeComponents.CreateRoofs` Basic Single-Plane, pivotLine; `MoveElements` для изменения **только level** | typed→SceneWriter→AC; AC→GH `Deconstruct Roof` | plane/pitch/level/material/SEO/BREP, Save/Open; свес >0.35 м вне outline отклоняется; auto pitch edit **NOT_FOUND** |
| 07 | **Сложная кровля:** Rhino/GH построение surfaces как исходный геометрический reference; AC29 UI native Multi-Plane | Rhino→GH geometry; **нет** доказанного native Multi-Plane writer и обратной параметризации | единый Roof GUID/стыки/SEO после Save/Open **NOT_FOUND**; не подменять Morph/Hotlink |
| 08 | **Двери/окна:** `CreateDoors/CreateWindows` с проверенным `ownerWallId`, GDL part | authored→SceneWriter→AC; `ModifyDoors/Windows` только width/height, AC→GH reference | host GUID, opening, ownUnID/material/geometry; удаление host/переустановка библиотеки — STOP |
| 09 | **Библиотеки/материалы:** штатные AC29 Favorites/LibPart, `nativeLibraryExpectations` | разрешённый native create→readback libPart.name/ownUnID.guid, material GUID; GH только read | GDL ≠ arbitrary Rhino BREP; library migration identity **NOT_FOUND** |
| 10 | **Изменение/QA/нормы:** GH filters/geometry checks → authored typed intent; AC `GetDetailsOfElements`, `GetModelDumpV1`, `GetIFCIdsOfElements`; IfcDiff/IfcTester | GH geometry→typed intent **не автоматизировано**; AC readback→GH reference, IFC diff вне PLN | GUID/GlobalId mapping, BREP/material/host/story; schema/IFC не заменяют нормативный расчёт; full 3-way sync **NOT_FOUND** |

**Правило завершения каждой операции:** записать в единственный разрешённый SceneWriter (если G3 санкционирован), дождаться ответа, прочитать native элемент и его дочерние GUID, проверить BREP/материал/этаж/host, сохранить PLN, повторно открыть и сверить; затем обновить GH reference через `Send Changes` и Rhino геометрию только после отдельного допуска. Для направлений без готового автоматического шага ставить NOT_FOUND, не рисовать двусторонние стрелки.

## 5. Конфликты, циклы, удаления, владение

- **Ownership:** APA-owned GUID изменяет только SceneWriter; GH Design для BUILD-01 не должен создавать или менять native AC. Rhino-owned объекты могут изменяться Content Cache, но только при разрешённом запуске; их ID не является native GUID.
- **Цикл:** GH AC Deconstruct→GH computation→GH Design→AC создаёт feedback loop/конкуренцию. Read-only GH output и запрет Design/Document Synchronize=True для BUILD-01 устраняют write-loop ценой отсутствия полной 3-way синхронизации.
- **Конфликт:** если Archicad изменён вручную или GH записал в PLN, inventory/retained signature drift→STOP, новый planHash без явного reconcile не создаёт разрешения.
- **Удаление:** `prepare_building_parameter_edit` запрещает add/remove/recreate, поэтому automatic delete propagation **NOT_FOUND**; delete/recreate может уничтожить SEO/host dependencies.
- **Параметры:** разрешены только Wall height, Window/Door width/height, Roof level (MoveElements). Slab footprint, Roof pitch, Beam shape, Story elevations, multi-plane topology не покрыты этим редактором.
- **Нормы:** IFC Tester/Clash/Grasshopper geometric checks могут выявлять нарушения, но версия СП, область применения, входные данные, расчёт и экспертная верификация не заменяются.

## 6. Состояние и следующий инженерный шаг

| Gate | Статус 10Z |
|---|---|
| SOURCE | 27 отдельных проверок в checks; два внутренних контрааудита |
| OFFLINE / BUILD | 0 новых / 0 |
| INSTALLED | NOT_VERIFIED |
| LIVE / ACCEPTED | 0 новых / 0 |
| G0 | BLOCKED_RUNTIME |
| G1 | NOT_RUN |
| G2 | SOURCE_ONLY; connected CLI контракт найден |
| G3 | NOT_AUTHORIZED |
| G4 / G5 | NOT_RUN / NOT_RUN |
| Full native 3-way / GUID-safe conflict merge / deletion / cross-app rollback | NOT_FOUND |

**Следующий P0:** read-only G0 manifest (AC29 port/PLN/APX/schema; Rhino8 SR/.3dm/.gh; GH connection), затем существующий G1 authored offline compiler. Не начинать GH native writes в BUILD-01, пока не решено несоответствие строгому inventory. Это не запрет Graphisoft инструмента как такового: он остаётся официальным read-only мостом и альтернативным writer в **другом** санкционированном проекте.

**Источники управления:** [NEXT_RESEARCH_PRIORITIES](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md), [TRIAD-PIVOT](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md), [матрица 61](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json), [№1 09:55Z](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261024T0955Z-TRIAD-GH-MCP-IDLE-ROUTING-GATES.md), [№3 последний найденный audit 20.10 18Z-A](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md). Исторический PROJECT_PLAN rev182 прочитан, не менялся.
