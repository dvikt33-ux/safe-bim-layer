# APA №2 — 2026-10-23 13Z — 30 фактических SOURCE-проверок
BUILD-01 issue #192; статус SOURCE_ONLY. Каждая строка — отдельная проверенная позиция источника, НЕ отдельный запуск или документ. Код фиксирован на commit `f7c37b84b76c040c417ccd58a5543326e50f673a`. Ссылки с путями ниже — неизменяемые.

## P0: цель, схема, существующий исполнитель
01. Issue #192 требует НОВУЮ двухэтажную scratch PLN, G0–G5, Save/Close/Reopen и второе задание; старый прототип не ACCEPTED. https://github.com/dvikt33-ux/safe-bim-layer/issues/192
02. Поручение №1 TRIAD-PIVOT 11Z сохраняет PR74/SceneWriter и запрещает новый writer/synchronizer. https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
03. Матрица priority_matrix_20261018.json: count=61, фактически items=61, уникальных ID=61; GRASSHOPPER=40 — историческая оценка ДО TRIAD-PIVOT. https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
04. PR74 документация: пример 10 Walls, 2 Slabs, 6 Windows, 2 Doors, 1 SinglePlane Roof; 21 нативный элемент, не универсальный проект. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/docs/APA_MODEL_FIRST_BUILDING.md
05. PR74 compile_candidate использует реальный nativeStoryBindings, проверяет heights/levels и компилирует BIM Graph без разрешения записи. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py
06. SceneWriter имеет SQLite журнал, разрешение точной сохранённой PLN по SHA256 и отдельный readback; это действующий контур записи. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
07. run_project создаёт typed_adapters(['roof']) при наличии CreateRoofs, но НЕ подключает beam adapter в этом маршруте. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py
08. NativeAdapter('CreateBeams') уже существует, требует точный набор полей Basic straight Beam; новый writer не нужен. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py

## Tapir pinned schema и readback
09. Pinned Tapir1.5.10 CreateSlabs.slabsData не содержит structureType/buildingMaterialId. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
10. Pinned ModifySlabs.slabsWithDetails содержит structureType/buildingMaterialId: требуется отдельная разрешённая запись после CreateSlabs. Тот же pinned schema.
11. Pinned CreateWalls.wallsData содержит floorIndex,zCoordinate,height,thickness,structureType,buildingMaterialId; это не автоматическая синхронизация с GH. Тот же pinned schema.
12. Pinned CreateColumns.columnsData содержит floorIndex,coordinates,height,width,depth,buildingMaterialId; материал нужно подтвердить native readback. Тот же pinned schema.
13. Pinned CreateBeams.beamsData содержит floorIndex,begCoordinate,endCoordinate,zCoordinate,width,height,buildingMaterialId; конкретный adapter проверяет более строгий набор. Тот же pinned schema + NativeAdapter.
14. Pinned CreateRoofs.roofsData содержит pivotLine,angle,structureType,buildingMaterialId; SinglePlane маршрут требует явных параметров. Тот же pinned schema.
15. Pinned CreateDoors/CreateWindows требуют ownerWallId и centerOffset; допускают favoriteName/libraryPartName, но эти поля не доказывают фактически выбранный GDL. Тот же pinned schema.
16. Pinned GetAvailableLibraryParts(filterByTypeId) и GetFavoritesByType(elementType) позволяют READ-only выбор GDL/Favorite до CREATE. Тот же pinned schema.
17. Pinned GetDetailsOfElements и GetGDLParametersOfElements существуют, а GetModelDumpV1 в каталоге отсутствует: BREP installed contract не подтверждён. Тот же pinned schema.
18. В archicad_authored_extension.verify_model имеется условный контроль libPart.name + libPart.ownUnID.guid при заполненном plan.nativeLibraryExpectations. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_extension.py
19. В examples/accelerator/model-first-building.json отсутствуют nativeLibraryExpectations, favoriteName и libraryPartName у перечисленных hosted проёмов; GDL-identity на этом fixture НЕ доказана. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json
20. prepare_building_parameter_edit поддерживает сохранение GUID при ограниченных Wall-height, Door/Window size, Roof-level изменениях, но отвергает глобальную смену этажей и не поддерживает произвольную форму Roof. https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_extension.py

## Официальный AC29 / Rhino / Grasshopper
21. Graphisoft: именно AC29 GH Live Connection build3000, Windows 16.8MB, Rhino7/8, дата 2025-10-01. https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
22. На той же странице AC30 GH Live Connection также build3000 (2026-10-07); build без номера AC не идентифицирует правильный инсталлятор. Тот же источник.
23. Graphisoft: GH Live Connection не совместим с Archicad Start Edition. Тот же источник.
24. Официальное руководство AC29: GH Design/Document создают реальные AC элементы, используют собственную ID-связь с GH definition, элементы первоначально locked. https://help.graphisoft.com/AC/29/INT/GC.pdf (indexed official excerpt, full PDF page audit NOT_DONE)
25. Официальное руководство AC29: после unlock ручные AC-правки возможны, но управляемые GH параметры имеют приоритет при следующем вычислении. Тот же источник.
26. Официальное руководство AC29: не заданные GH параметры нового элемента наследуют Default Settings инструмента AC в момент создания; без explicit Settings результат не детерминирован. Тот же источник.
27. Rhino8 -Grasshopper Solver Disable/Enable управляет только GH вычислением; -GrasshopperPlayer запускает .gh/.ghx без GH UI. https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
28. Rhino8 evaluation 90 дней; после истечения saving и plugins прекращают работу; это не бессрочная бесплатная лицензия. https://www.rhino3d.com/download/
29. Официальный Tapir репозиторий имеет MIT LICENSE; Tapir Grasshopper Plugin доступен как пакет 'tapir' через Rhino Package Manager, но обозначен Work in Progress. https://github.com/ENZYME-APD/tapir-archicad-automation ; https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE
30. Tapir GH coverage — статическая проверка именуемых параметров исходного кода, а НЕ доказательство работающего runtime или покрытия всех команд. https://enzyme-apd.github.io/tapir-archicad-automation/gh-coverage/

## Проверки, которые НЕ выполнены
Нет доступа к локальной Windows11, APX SHA, loaded command inventory, GH add-on binary, Rhino license и scratch PLN. Нет OFFLINE, BUILD, INSTALLED, LIVE или ACCEPTED в этом проходе. PDF AC29 22.8MB недоступен для полного постраничного аудита; SOURCE 24–26 основаны на официальном индексированном фрагменте. Исторический PROJECT_PLAN rev182 не изменялся; его текущий путь в данном проходе не установлен. Свежий отдельный №3 23.10 в доступных проверенных путях не найден. MODEL_MODE_NOT_VERIFIABLE.
