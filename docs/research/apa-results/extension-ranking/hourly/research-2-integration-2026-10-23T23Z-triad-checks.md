# APA №2 — 23Z / 30 документарных SOURCE-проверок
Проверки сделаны по реально прочитанным исходным контрактам. Это 30 утверждений, НЕ 30 независимых сайтов, НЕ локальные тесты.

**Ключи первоисточников:**
[S] https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json (Git blob e8ad53b6ea7c19dc34cbdcb723a79be995639cd7).
[A] https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py .
[R] https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py .
[B] https://github.com/dvikt33-ux/safe-bim-layer/issues/192 .
[N] https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md .
[X] https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T2156Z-TRIAD-ZONES-MARKERS-RELATIONS.md .
[M] https://developer.rhino3d.com/en/guides/grasshopper/gh-algorithms-and-data-structures/algorithms-data/ .
[J] https://github.com/andrewheumann/jSwan/blob/main/README.md .
[G] https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ .

| № | Сверенное утверждение | Источник |
|---:|---|---|
| 01 | BUILD-01 требует G0–G5 и новое здание, не повтор старого fixture | B |
| 02 | NEXT запрещает подмену результата SOURCE-исследованием и изменение main | N |
| 03 | Исследователь №1 поручил №2 read-only карту Zone→Wall→Opening | X |
| 04 | Закреплённая схема Tapir 1.5.10 — отдельный Git blob, не локальный APX | S |
| 05 | GetZoneBoundaries v1.2.3 существует | S |
| 06 | GetZoneBoundaries допускает zoneElementId ИЛИ zones, но не оба | S |
| 07 | Batch GetZoneBoundaries.zoneBoundariesOfZones выровнен по порядку входа | S |
| 08 | Zone boundary содержит connectedElementId, isExternal, neighbouringZoneElementId | S |
| 09 | Boundary.area — площадь boundary polygon, polygonOutline — Coordinate3D, не floor area | S |
| 10 | GetRelationsOfElements v1.5.7 требует elements, otherElementType необязателен | S |
| 11 | ZoneRelations содержит elementsGroupedByType, wallParts, beamParts, curtainWallSegmentParts | S |
| 12 | Opening relations для Door/Window содержат fromRoom/toRoom | S |
| 13 | Roof/Shell relations содержат connectedRooms | S |
| 14 | GetConnectedElements v1.1.4 требует elements и connectedElementType | S |
| 15 | GetConnectedElements возвращает connectedElements[].elements либо error | S |
| 16 | GetStories v1.1.5: index/floorId/level/name/height; нет ifcId | S |
| 17 | GetIFCIdsOfElements v1.5.1 требует elements | S |
| 18 | GetElementsByIFCIds v1.5.1 требует ifcIds | S |
| 19 | GetAvailableLibraryParts v1.5.0 возвращает skippedCount/skippedSample | S |
| 20 | GetBuildingMaterials v1.5.4 требует attributeIds | S |
| 21 | GetDetailsOfElements v1.5.7 имеет необязательное fields | S |
| 22 | CreateRoofs v1.4.0 без pivotLine допускает MultiPlane, levels максимум 16 | S |
| 23 | CreateSlabs v1.0.3 принимает holes/favoriteName, но не buildingMaterialId | S |
| 24 | GetModelDumpV1 отсутствует в commands закреплённой Tapir 1.5.10 | S |
| 25 | Get3DGeometryOfElements отсутствует в commands закреплённой Tapir 1.5.10 | S |
| 26 | PR74 EvidenceAPI.READs не включает GetZoneBoundaries/GetRelations/GetConnected/GetIFCIds | A |
| 27 | PR74 authored nativeComponents не принимает Beams/Zones; Roof требует Basic+pivotLine+material | A |
| 28 | SceneWriter обращается к GetModelDumpV1 условно при некорректных bbox, а не обязательно всегда | R |
| 29 | McNeel требует .3dm вместе с .gh при referenced geometry; internal data хранится в .gh | M |
| 30 | jSwan README: Item/List Access, default Point X/Y/Z, Lock Structure/null, Serialize Keys and Values; Graphisoft GH–AC29 build3000 официально Rhino7/8 | J, G |

Контекст вне счётчика: официальный Archicad ассоциативный SEO/Trim — внутри Archicad https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-269.htm ; upstream zone-overlap PR827 остаётся OPEN https://github.com/ENZYME-APD/tapir-archicad-automation/pull/827 ; Rhino/GH Panel Stream Contents перезаписывает файл при пересчёте https://discourse.mcneel.com/t/grasshopper-colleting-all-panel-to-one-txt-file/92782 .

**Счётчик:** SOURCE=30 отдельных утверждений; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
