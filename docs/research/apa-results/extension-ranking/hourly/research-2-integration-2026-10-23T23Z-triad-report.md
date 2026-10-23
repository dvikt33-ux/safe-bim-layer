# APA №2 — 23 октября 2026, 23Z — BUILD-01 / воспроизводимость и QA связей
Статус: SOURCE_ONLY. OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.

## Четыре результата P0

**P0-23-01 — GH без Rhino-файла не воспроизводим.** Официальный McNeel: если Grasshopper использует referenced geometry из Rhino, вместе с .gh необходимо сохранять и передавать исходный .3dm. Внутренние данные хранятся в .gh. Источник: https://developer.rhino3d.com/en/guides/grasshopper/gh-algorithms-and-data-structures/algorithms-data/. Для BUILD-01 G1 требовать снимок .gh + .3dm (или доказанное internalized-only), SHA256 обоих, идентификаторы Rhino-объектов, версии плагинов и SHA256 конечного JSON. Не писать синхронизатор.

**P0-23-02 — нативная проверка отношений зон уже имеется в Tapir 1.5.10, но не подключена к EvidenceAPI PR74.** В закреплённой схеме есть GetZoneBoundaries v1.2.3, GetRelationsOfElements v1.5.7, GetConnectedElements v1.1.4, GetIFCIdsOfElements v1.5.1. В READS исходного archicad_project_accelerator.py этих команд нет. Можно документировать отдельную READ-only инвентаризацию через существующий Tapir; нельзя называть её уже автоматизированным PR74 preflight. Если Zone не создана, результат проверки зон NOT_APPLICABLE, а не PASS.

**P0-23-03 — площадь границы зоны НЕ площадь помещения.** Tapir ZoneBoundariesWrapper определяет area как площадь 3D polygon участка границы; polygonOutline содержит Coordinate3D. Запрещено складывать boundary.area и выдавать результат за площадь пола зоны или нормативную полезную площадь. Потребуется отдельный квалифицированный параметр площади и его проверка.

**P0-23-04 — GetModelDumpV1 не принадлежит pinned Tapir 1.5.10.** Имени нет среди commands закреплённого JSON, но archicad_scene_run.py условно вызывает GetModelDumpV1 при аномальных 3D bbox, а archicad_project_accelerator.py использует его в дополнительных roof/structural receipts. G0 должен отдельно проверить фактическую регистрацию и провайдера команды. Это не доказательство её отсутствия в установленном другом add-on. Не утверждать, что любой preflight обязательно её вызывает.

## Подтверждённые версии и источники
- BUILD-01 issue #192: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- NEXT: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
- TRIAD PIVOT №1: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
- №1 21:56Z, поручение read-only zone QA: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T2156Z-TRIAD-ZONES-MARKERS-RELATIONS.md
- №3 audit-2026-10-20-18-A/B: docs/research/apa-results/extension-ranking/hourly/; более свежий №3 не подтверждён.
- Tapir pinned 1.5.10: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json ; blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7, это SOURCE, не runtime.
- PR74 immutable compiler: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py ; SceneWriter: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py
- Graphisoft GH–AC29 Live Connection build3000, Windows Rhino7/8, 01.10.2025: https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ ; бесплатный add-on, Archicad29/Rhino8 лицензируются отдельно; build5101 compatibility INSTALLED_NOT_VERIFIED.
- jSwan MIT, Serialize Keys and Values, Item/List Access, Lock Structure/null: https://github.com/andrewheumann/jSwan/blob/main/README.md ; Rhino8 plugin load NOT_VERIFIED.
- Матрица 61: docs/research/apa-results/extension-ranking/priority_matrix_20261018.json ; blob 9cb5e6f2a59f80762cc77073eeb10404829af75a. Исторический PROJECT_PLAN rev182 не менялся и в этом проходе не извлекался.

## Готовая READ-only QA-карта этаж → зона → ограждение → проём
1. GetStories: native index/floorId/name/level; pinned 1.5.10 НЕ возвращает stories[].ifcId.
2. GetAllElements с фильтром Zone: зафиксировать реальные Zone GUID; при отсутствии зон статус NOT_APPLICABLE, без CreateZones.
3. GetZoneBoundaries с массивом zones: ответ zoneBoundariesOfZones выровнен по входу; каждая граница содержит connectedElementId, isExternal, neighbouringZoneElementId, area, polygonOutline; учитывать ErrorItem.
4. GetRelationsOfElements для Zone GUID: zoneRelations.elementsGroupedByType, wallParts, beamParts, curtainWallSegmentParts; сверять со стенами BIM Graph.
5. GetConnectedElements с обязательными elements=[Wall GUID] и connectedElementType=Door, отдельно Window: nested connectedElements[].elements; сверять hostWall GUID.
6. GetRelationsOfElements для Door/Window GUID: openingRelations.fromRoom/toRoom; наружное окно может не иметь зоны с одной стороны — решать по заданию, не автоматически считать ошибкой.
7. GetRelationsOfElements для Roof/Shell GUID: roofOrShellRelations.connectedRooms; отсутствие зон не дефект кровли.
8. GetIFCIdsOfElements и GetElementsByIFCIds: отдельная сверка Archicad element GUID и IFC GlobalId; не смешивать их с Rhino object GUID, GH component ID и floorId.

**Ограничение:** команды пунктов 3–8 НЕ включены в PR74 EvidenceAPI.READs. Это документированный план read-only QA, не результат выполненного preflight.

## Воспроизводимый маршрут без второго writer
G0 READ: AC29 build5101, Tapir APX SHA/версия/команды, порт, открытый PLN, этажи/floorId, Favorites/библиотеки/материалы; Rhino8 SR, GH Connection build3000, jSwan версия. G0 BLOCKED_RUNTIME.
G1 GH: сохранить .gh + .3dm, единицы/координаты/ссылки; заморозить Solver, выключить Panel Stream Contents после создания JSON, исключить null и GH list-matching drift; затем PR74 authored mode=preflight с реальным read-only transport и точным targetProjectPath. Автоматический atomic handoff GH→PR74 готовыми компонентами пока NOT_FOUND.
G2: стены/перекрытия/колонны/SinglePlane Roof/окна/двери через PR74; балки и MultiPlane Roof существуют в Tapir, но не подключены в authored whitelist. Relative wall Z и absolute slab level не смешивать; Slab holes сохранять при Modify; GDL libPart name/ownUnID проверять.
G3: только после отдельного разрешения, один SceneWriter/SQLite; GH direct Synchronize на APA-owned GUID запрещён. При UNKNOWN STOP, read-only reconciliation, no retry CREATE. CreateZones и GH ReplaceExisting на чужом PLN запрещены.
G4: GuardedSave → GUI Close → no-open → Reopen → native GUID/type/floor/host/material/holes/SEO/BREP readback; IFC Publisher с проверенными visibility, translator и Hotlink Preferences; IFC GlobalId↔native GUID и IfcOpenShell/IfcTester независимый контроль. IFC mesh/3dm Object не доказывает native BREP.
G5: другой brief и отдельная scratch PLN; без этого BOUNDED_DEMO. Откат из защищённой копии PLN и соответствующих .gh/.3dm/JSON/библиотек, а не только Undo.

**Вывод:** полная автоматическая Rhino↔GH↔AC синхронизация с сохранением GUID, циклическими изменениями, удалениями и разрешением конфликтов NOT_FOUND. Нормативные GH constraints/IFC IDS не заменяют экспертизу СП. SOURCE_ONLY, не повышать G0–G5. MODEL_MODE_NOT_VERIFIABLE.
