# APA №2 — 23Z / два независимых документарных контрааудита

## Контрааудит A — идентичность, ownership, циклы и конфликтные изменения
1. Rhino object GUID, GH source component ID, Archicad element GUID, IFC GlobalId и floorId — разные идентификаторы; нельзя отождествлять их по равенству строк. Для каждого требуется явная карта.
2. Graphisoft GH→AC Synchronize — отдельный native writer; GH→JSON→PR74→SceneWriter/SQLite — существующий APA writer. Нет доказанного общего transaction lease и conflict resolver. Запрещено двойное владение APA-owned GUID.
3. Graphisoft AC→GH Sync Changes to GH обновляет параметры, но не гарантирует обратный roundtrip native BREP и не обеспечивает единую запись Rhino↔GH↔AC.
4. GetZoneBoundaries/GetRelations/GetConnected/GetIFCIds есть в pinned Tapir, но их нет в EvidenceAPI.READs PR74; нельзя заявлять, что они автоматически выполнены в preflight.
5. GH referenced geometry без .3dm может не разрешиться при открытии .gh; один .gh SHA недостаточен. Установить provenance пары .gh/.3dm/JSON и plugins.
6. Удаление GH-компонента, GH ReplaceExisting, циклический solver и повтор CREATE после UNKNOWN могут разрушить идентичность. Применять STOP и read-only reconciliation, а не auto-retry.
**Вердикт A:** FULL_AUTOMATIC_GUID_PRESERVING_THREE_WAY_SYNC=NOT_FOUND; все проверки SOURCE_ONLY. Никаких LIVE.

## Контрааудит B — BIM-семантика, геометрия, версии и ложный PASS
1. ZoneBoundary.area — площадь 3D boundary polygon, не полезная/нормируемая площадь комнаты. GetZoneBoundaries не является проверкой СП по площадям.
2. В PR74 authored нет CreateZones: если зоны не созданы и не существовали, zone QA NOT_APPLICABLE, а не PASS. Не создавать зоны ради улучшения метрики.
3. Pinned Tapir 1.5.10 не содержит GetModelDumpV1/Get3DGeometryOfElements. SceneWriter условно вызывает GetModelDumpV1; возможный отдельный локальный provider надо квалифицировать в G0, отсутствие в pinned не доказывает отсутствие в runtime.
4. MultiPlane Roof поддержан Tapir CreateRoofs, но PR74 authored принимает только Basic SinglePlane с pivotLine. CreateBeams существует в Tapir, но PR74 nativeComponents его исключает. Это NOT_WIRED, не «нативная сборка готова».
5. Graphisoft AC29 GH Live Connection build3000 официально поддерживает Rhino8, но фактическая установка/совместимость с AC29 build5101 не доказана; jSwan Rhino8 load не доказан; APX SHA не прочитан с локальной машины.
6. IFC GlobalId↔native GUID требуется проверять отдельно. Mesh, 3dm Object, bounding box или отсутствие clash не доказывают независимый native BREP. Save/Close/Reopen нового BUILD-01 не выполнялись.
7. GH numerical constraints и IFC IDS могут проверять выбранные формальные условия, но не заменяют инженерную и нормативную экспертизу.
**Вердикт B:** G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. SOURCE=30 утверждений не превращаются в OFFLINE_PASS. PROJECT_PLAN rev182 только чтение, не менялся. MODEL_MODE_NOT_VERIFIABLE.

## Основания
- BUILD-01 https://github.com/dvikt33-ux/safe-bim-layer/issues/192
- pinned schema https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
- PR74 compiler https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py
- SceneWriter https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py
- McNeel https://developer.rhino3d.com/en/guides/grasshopper/gh-algorithms-and-data-structures/algorithms-data/
- Graphisoft https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/
