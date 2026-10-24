# APA R2 | 24.10.2026, 13Z | Триада AC29–Rhino8–GH: границы готовых мостов и нативной кровли

**Статус:** SOURCE_ONLY. Цель: [BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192). Исследовательская ветка: `research/apa-extension-ranking-hub-20261018`. **Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED нет.** Изменения main, кода, PLN/APX, установка, LIVE, merge, Work/Codex/Arena, платные API — не выполнялись. **MODEL_MODE_NOT_VERIFIABLE.**

## 1. Дельта этого прохода: четыре доказуемых ограничения и одна возможность

**R2-13A / ПРИОРИТЕТ 100 — многощипцовая/многоскатная кровля: Tapir API умеет больше, чем действующий APA guard.** Официальный [каталог Tapir](https://enzyme-apd.github.io/tapir-archicad-automation/archicad-addon/) описывает `CreateRoofs` (команда появилась в 1.4.0): **по умолчанию создаётся Multi-Plane Roof**, а `pivotLine` переключает создание на Single-Plane. Там же `ModifyRoofs` (1.4.0) описан как модификатор **multi-plane Roof** с `levels`, `eavesOverhang`, `polygonOutline`, `holes`, материалами. Это **SOURCE наличия функции в Tapir**, не установленный/исполненный контракт локальной 1.5.10. В существующем APA immutable code commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7`: `scripts/archicad_project_accelerator.py:294-304` требует `pivotLine` для `CreateRoofs`; `scripts/archicad_connected_components.py:184-196` принимает только `roofClass=SinglePlane` и `structureType=Basic`; `scripts/archicad_authored_extension.py:134-143` позволяет изменять только `level` кровли через `MoveElements`; `scripts/archicad_scene_run.py:94-97` не содержит `ModifyRoofs` в `ALLOWED_WRITES/EXTENDED_WRITES`. **Итог:** команда готова на уровне Tapir, но маршрут `PR74 → единственный SceneWriter → multi-plane Create/Modify → native readback` **NOT_FOUND** без расширения существующих ограничителей; прямой вызов Tapir/GH в тот же PLN стал бы вторым writer и запрещён. **Не утверждать «Tapir не умеет сложные кровли» — утверждать «текущий APA не квалифицировал их».**

**R2-13B / ПРИОРИТЕТ 96 — AC29 → Rhino .3dm является потерей BIM-семантики и иногда топологии.** [Официальный AC29 Export Model to Rhino](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm): передаётся геометрия, но **не** свойства, марки, спецификации и объёмы; режим `Surface Model` **разбивает один многоматериальный AC-элемент на несколько Rhino-объектов**; `Solid Model` сохраняет один объект, но **один цвет**; `Hybrid` переводит плоские поверхности в BREP, криволинейные — в Mesh. Значит количество Rhino объектов, Rhino Object IDs и топология экспортированного BREP **не являются** инвариантами native AC GUID/BREP. QA в Rhino — лишь геометрическая сверка с явно зафиксированным режимом экспорта; финальный native GUID/type/material/BREP readback — из Archicad.

**R2-13C / ПРИОРИТЕТ 93 — Rhino .3dm → AC29 Hotlink есть, но это GDL sidecar, не Wall/Slab/Roof.** [AC29 Open/Merge Rhino](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) помещает модель как не редактируемый GDL-объект, отдельные .gsm — в Embedded Library. Свойства `Rhino` сохраняют **исходный Rhino Layer и Rhino ID** (это provenance, **не** AC GUID mapping). [AC29 Hotlink Rhino](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm) принимает .3dm, размещает hotlink на **текущем этаже**, его параметры сегментации после размещения не редактируются. Никакой гарантии native type/host/SEO/дублирования при обновлении нет. Для BUILD-01 в основной PLN импорт/Hotlink запрещён; допустим только изолированный sidecar после разрешения.

**R2-13D / ПРИОРИТЕТ 88 — готовый Tapir Grasshopper Plugin существует, но не равен полной интеграции.** [Официальный репозиторий Tapir](https://github.com/ENZYME-APD/tapir-archicad-automation) указывает пакет Rhino Package Manager с именем `tapir`, а сам GH plugin помечает **work in progress**; AC Add-On отдельно добавляет JSON-команды. Следовательно, потенциальен GH→Tapir read-only интерфейс, но набор компонентов, Rhino 8 SR, фактическая установленность и покрытие методов **NOT_VERIFIED**. GH-компоненты Create/Modify нельзя включать в BUILD-01, иначе это конкурент SceneWriter.

**R2-13E / ПРИОРИТЕТ 87 — источник кода и рабочая ветка не совпадают.** Прямой `fetch_file` `scripts/archicad_project_accelerator.py` и `scripts/archicad_connected_components.py` на **research branch** и **main** дал 404, но оба файла успешно прочитаны с immutable commit `5a3a9201a715a5528c93bed4a5318e2acb32eea7` (blob соответственно `8e0ce2fbb5441009925f0d9199e180e8670a5eea` и `c5a99f59a90369ff622807574677cf11ca0a2225`). Это не ошибка доказанного содержания старого кода, а **непроверенный путь развёртывания на ноутбуке**. G0 должен установить реальный локальный SHA/ветку/порт/APX, не считать исследовательскую ветку исполняемым исходником.

## 2. Совместимость и лицензирование (SOURCE, не INSTALLED)

| Средство | Точный документированный контракт | Стоимость/условия | Для BUILD-01 |
|---|---|---|---|
| [Graphisoft Grasshopper–Archicad 29 Live Connection](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) | **build 3000**, Windows installer 16.8 MB, 01.10.2025; **Rhino 7/8**. Не AC30-бинарник; Start Edition не поддерживается | Публичный download add-on, отдельная цена на странице не указана; AC29 и Rhino8 требуют собственных лицензий | AC→GH reference/deconstruct; GH→AC Design — отдельный writer, **OFF** |
| [Tapir](https://github.com/ENZYME-APD/tapir-archicad-automation) | Add-On JSON commands; GH package `tapir` WIP. Документация команд обновляется независимо от установленной 1.5.10 | Исходники репозитория под MIT; не экстраполировать лицензию на Archicad/Rhino | JSON только через существующий APA SceneWriter |
| [Rhino 8 Content Cache](https://www.rhino3d.com/features/grasshopper/content-cache/) | GH↔Rhino tracked model objects, не AC-native. `Pull/Push/Bake/Purge` | Входит в лицензированный Rhino8 | `Pull`/reference допустим; `Push/Bake/Purge` OFF в BUILD-01 |
| [Rhino.Inside](https://www.rhino3d.com/features/rhino-inside/) | Технология embedding в 64-bit Windows host; документированные примеры Revit/AutoCAD; готовый Archicad29-host **не найден** | Open-source технология, но требуется Rhino license | **NOT_FOUND** как готовый AC29-host, не ставить |
| [AC29 Rhino .3dm Hotlink](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm) | Rhino→AC связанный GDL-геометрический reference, этаж — текущий | Штатный AC29 | Sidecar только, не native BIM |

**Неизвестно:** точный Rhino 8 SR, GH Live Connection APX SHA/installed, Tapir GH package installed, локальные регистрация JSON-команд и фактические лицензии. Rhino Content Cache bug RH-84658 исправлен в SR14 по [McNeel](https://discourse.mcneel.com/t/content-cache-push-doesnt-update-material-data/194222), но локальный SR не определён.

## 3. Общий контракт завершения операции (не заявленная реализация)

`G0`: зафиксировать AC29 build5101/PLN path+hash/порт/Tapir1.5.10/APX+registered commands/schema/этажи/атрибуты/Favorites/Defaults/библиотеки; Rhino8 exact SR/.3dm path+units+hash; GH .gh path+hash/один активный документ/компоненты. `G1`: typed intent/plan hash из существующего PR74. `G2`: source native schema и preflight без записи. **После отдельного допуска** `G3`: только SceneWriter в новом scratch PLN, GH Design `Synchronize=False` и без writer nodes; после любого UNKNOWN — STOP/read-only reconcile, **не повторять CREATE**. `G4`: GetAllElements/GetDetailsOfElements/GetModelDumpV1 + GUID/type/story/host/material/child GUID/BREP + GuardedSave/Close/Reopen и повторный readback. `G5`: новое независимое здание по другому заданию.

`AC→GH` через Element Input/Deconstruct/Sync Changes to GH — **связь для чтения**, но если выход подключён к GH Design Create/Modify, может образоваться write-cycle; отключение Synchronize не равно удалению и не является rollback. `Rhino→GH` через Query Model Objects/Content Cache Pull — геометрия/Model Object ID. `GH→AC` через Graphisoft Design или Tapir GH — **конкурирующие писатели**, в основной модели запрещены. `AC→Rhino` через штатный .3dm export — snapshot, не BIM roundtrip. Глобальная атомарная трёхсторонняя транзакция и GUID-preserving conflict merge **NOT_FOUND**.

## 4. Десять маршрутов и критерии ГОТОВО

| ID | Выбор → изменение → завершение → передача | Native readback и ГОТОВО | Граница |
|---|---|---|---|
| T01 Этажи | AC Story Settings / PR74 `storyBindings`; GH читает reference | native floorId/index/Z и совпадение после Save/Open | GH автоматическое создание этажей в существующем PR74 **NOT_FOUND** |
| T02 Стены | GH/Rhino контур как расчёт → PR74 `CreateWalls` → SceneWriter → AC | Wall GUID/height/thickness/story/buildingMaterial/host/BREP | произвольный NURBS→native Wall без адаптера **NOT_FOUND** |
| T03 Перекрытия | authored footprint → `CreateSlabs` → SceneWriter | Slab GUID/Z/thickness/holes/material/композит и reopen | `CreateSlabs` в текущем коде без явного `buildingMaterialId`; defaults и holes нельзя принимать по виду |
| T04 Колонны | typed coordinates → PR74 `nativeComponents.CreateColumns` | Column+ColumnSegment GUID/axis/section/material/story/BREP | GH Rhino ID не равен AC GUID |
| T05 Балки | существующий `archicad_connected_components.py` `beam→CreateBeams` после source receipt/preflight → SceneWriter | Beam+BeamSegment GUID/straight axis/profile/material/closed BREP | **не** входит в `nativeComponents` PR74; отдельный connected CLI; curved Beam **NOT_FOUND** |
| T06 Простая кровля | PR74 `CreateRoofs` с `pivotLine`, Basic → SceneWriter | Roof SinglePlane GUID/pivot/pitch/Z/material/SEO/BREP | сохранённый guard только SinglePlane |
| T07 Многоскатная кровля | Tapir `CreateRoofs` без pivotLine или `ModifyRoofs` с levels/overhang/outline | после будущей интеграции нужен native MultiPlane GUID/ridges/valleys/material/holes/SEO/reopen | **SOURCE_TOOL_EXISTS; APA_SCENEWRITER_ROUTE_NOT_FOUND**; прямой вызов запрещён |
| T08 Окна/двери | `CreateWindows/CreateDoors` с `ownerWallId` → SceneWriter | Window/Door GUID + hostWall + width/height/sill/void + reopen | generic Opening writer отдельно, не подменять окнами |
| T09 Библиотеки/3dm | AC Library Manager/Favorites; Rhino 3dm Hotlink **только отдельный reference PLN** | GDL Object + Rhino original ID property, отсутствие missing objects | GDL ≠ native Wall/Slab/Roof; import в BUILD-01 запрещён |
| T10 QA/нормы | GH геометрические constraints → typed inputs; AC IFC read-only → IfcOpenShell/IfcTester/IfcClash; Rhino export только geometry QA | native GUID/type/material/BREP из AC + отдельно геометрические/IFC проверки | нормативная экспертиза, cross-app rollback, 3-way atomic sync **NOT_FOUND** |

Для T01–T10 `ГОТОВО` — **будущий критерий**, а не результат данного запуска. При любой смене GUID/типа/host/материала после повторного открытия — STOP; откат только через отдельно сохранённые версии PLN/.gh/.3dm и квитанции. Удаление, смена владельца, массовая замена и циклические AC→GH→AC записи **не квалифицированы**.

## 5. 28 предметных SOURCE-проверок (каждая отдельное утверждение, не 28 уникальных сайтов)

| № | Проверенный факт | Доказательство |
|---|---|---|
| 01 | BUILD-01 требует новый scratch, два этажа и независимый reopen | [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 02 | PR74/SceneWriter — единственный разрешённый native writer | [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 03 | research TRIAD-PIVOT требует трёх программ и отделения SOURCE от LIVE | [TRIAD-PIVOT](research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 04 | NEXT_RESEARCH_PRIORITIES находится в `docs/research/apa-results/extension-ranking/` | [очередь](../NEXT_RESEARCH_PRIORITIES.md), blob `6f074693360231c5cb42ada815984a6b0dd504c0` |
| 05 | матрица ранжирования содержит 61 item (полнота формул здесь не пересчитывалась) | [matrix 61](../priority_matrix_20261018.json), blob `9cb5e6f2a59f80762cc77073eeb10404829af75a` |
| 06 | AC29 GH Live Connection build3000 поддерживает Rhino7/8 | [Graphisoft downloads](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 07 | AC29 Windows installer 16.8 MB и дата 01.10.2025 | [Graphisoft downloads](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 08 | Start Edition не поддерживается | [Graphisoft downloads](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 09 | Rhino.Inside — embedding technology, не готовый AC29-host в официальном списке | [McNeel Rhino.Inside](https://www.rhino3d.com/features/rhino-inside/) |
| 10 | Rhino8 Content Cache обновляет tracked objects без обязательного повторного Bake | [McNeel](https://www.rhino3d.com/features/grasshopper/content-cache/) |
| 11 | Content Cache Pull переносит Rhino Object ID в GH | [McNeel guide](https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1) |
| 12 | Content Cache Bake без ID создаёт дубликаты; Purge удаляет объекты/definitions | [McNeel guide](https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1) |
| 13 | Rhino8 SR14 исправляет RH-84658 (material cache) | [McNeel forum](https://discourse.mcneel.com/t/content-cache-push-doesnt-update-material-data/194222) |
| 14 | AC29 экспорт .3dm не переносит properties/tags/quantities | [AC29 export](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm) |
| 15 | AC29 Surface Model может разбить один элемент на несколько Rhino объектов | [AC29 export](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm) |
| 16 | AC29 Solid Model один Rhino object, но один цвет | [AC29 export](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm) |
| 17 | AC29 Hybrid: flat→BREP, curved→Mesh | [AC29 export](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-44.htm) |
| 18 | AC29 .3dm импорт превращает геометрию в GDL Object | [AC29 import](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) |
| 19 | AC29 импорт хранит original Rhino Layer/ID в свойствах | [AC29 import](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm) |
| 20 | AC29 Hotlink .3dm размещается на текущем этаже, сегментация после размещения не редактируется | [AC29 hotlink](https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-43.htm) |
| 21 | Tapir GH plugin доступен как Package Manager `tapir`, но WIP | [Tapir README](https://github.com/ENZYME-APD/tapir-archicad-automation) |
| 22 | Tapir CreateRoofs default multi-plane, pivotLine→single-plane | [Tapir commands](https://enzyme-apd.github.io/tapir-archicad-automation/archicad-addon/) |
| 23 | Tapir ModifyRoofs описывает multi-plane levels/outline/holes | [Tapir commands](https://enzyme-apd.github.io/tapir-archicad-automation/archicad-addon/) |
| 24 | PR74 authored nativeComponents не принимает CreateBeams | [immutable code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L290-L304) |
| 25 | PR74 authored CreateRoofs требует pivotLine, Basic | [immutable code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py#L295-L304) |
| 26 | Connected roof adapter проверяет SinglePlane, а beam adapter — straight basic section | [immutable code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L100-L107), [roof](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L184-L196) |
| 27 | SceneWriter allowed/extended creates не содержат ModifyRoofs | [immutable code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py#L94-L97) |
| 28 | Авторский parameter diff допускает Wall height, Door/Window size, Roof level, не roof pitch/contour | [immutable code](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py#L118-L143) |

**Отдельная repo-верификация:** `fetch_file` по исследовательской ветке и main для двух файлов `scripts/archicad_project_accelerator.py` / `scripts/archicad_connected_components.py` вернул 404; те же пути по immutable commit прочитаны успешно. Это 4 отрицательных и 2 положительных API lookup, **не** доказательство отсутствия всего APA на локальной машине. Свежий отчёт R1 за 13Z и R3 за 13Z на момент чтения этого запуска не был доступен по проверенному пути; актуальные поручения A5 этого же цикла ещё не опубликованы (A5 планируется позже), использована ранее опубликованная очередь/аудит 20.10 и R1 10:56Z. Не делать вывод, что коллеги не работают.

## 6. Два собственных контрааудита

**Контрааудит A — документация против реализации.** Проверена ловушка: `Tapir CreateRoofs` действительно документирует MultiPlane, но это не означает, что `SceneWriter` принимает и проверяет такой результат. Независимая от документации сверка `project_accelerator.py`, `connected_components.py`, `scene_run.py`, `authored_extension.py` выявила четыре отдельных ограничителя. Вывод **SOURCE_TOOL_EXISTS / APA_ROUTE_NOT_FOUND**, не `ACCEPTED`. Проверена вторая ловушка: число Rhino объектов после экспорта нельзя сравнивать 1:1 с числом AC GUID из-за Surface Model split.

**Контрааудит B — безопасность данных и дублирование.** Для трёх направлений (`AC→Rhino .3dm`, `Rhino→AC .3dm Hotlink`, `AC→GH Deconstruct`) проверено, что они не доказывают обратную native identity/host/material и атомарный commit. Для `GH Design→AC`, `Tapir GH→AC` и `Rhino Hotlink→AC` в основной PLN существует риск второго writer/внеплановых GUID. Итог: оставить только read-only/reference в BUILD-01; никакой auto-rollback/auto-retry; сохранить G0 BLOCKED.

## 7. Передача интегратору I4: четыре закрываемых задания

1. **I4-13-01 (100):** выпустить точную карту `Tapir CreateRoofs/ModifyRoofs` → существующий `SceneWriter`: перечислить какие guard/adapter не пропускают MultiPlane, и проверить наличие **уже готового** безопасного пути без правки кода. При отсутствии — `NOT_FOUND`, не запускать raw Tapir. **ГОТОВО:** таблица команда/параметры/guard/readback/разрешённый executor.
2. **I4-13-02 (96):** в схеме QA отделить `AC native BREP` от `AC→Rhino Surface/Solid/Hybrid`; зафиксировать режим экспорта и отсутствие сохранения BIM-семантики. **ГОТОВО:** критерии геометрической сверки без сравнения Rhino Object Count=AC GUID Count.
3. **I4-13-03 (93):** для .3dm Hotlink описать только **изолированный GDL sidecar** с Rhino original ID и текущим этажом; запретить в основном PLN. **ГОТОВО:** native/GDL provenance и условия отдельного разрешения.
4. **I4-13-04 (90):** собрать G0 manifest реально установленного executable commit/PLN/APX/порт/версии Rhino SR/GH build; объяснить, почему read-only GitHub исторического commit не доказывает deployed. **ГОТОВО:** immutable source→local SHA binding или явный `BLOCKED_RUNTIME`.

## 8. Итоговая матрица

| Gate | Фактический статус |
|---|---|
| G0 | BLOCKED_RUNTIME (нет локального runtime manifest) |
| G1 | NOT_RUN в этом цикле |
| G2 | SOURCE_PARTIAL (Tapir multi-plane API есть, APA guard не допускает) |
| G3 | NOT_AUTHORIZED |
| G4 / G5 | NOT_RUN |
| SOURCE | **28 предметных проверок** (не уникальных сайтов и не LIVE) |
| OFFLINE / BUILD / LIVE / ACCEPTED | **0 / 0 / 0 / 0 новых** |
| INSTALLED | NOT_VERIFIED |
| 3-way native bidirectional sync, cross-app atomic rollback | **NOT_FOUND** |
| Код, main, PLN/APX, установки, LIVE, merge | **НЕ ИЗМЕНЯЛИСЬ / НЕ ВЫПОЛНЯЛИСЬ** |
| Модельный режим | **MODEL_MODE_NOT_VERIFIABLE** |
