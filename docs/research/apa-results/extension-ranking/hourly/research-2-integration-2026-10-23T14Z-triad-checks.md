# APA №2 — 23.10.2026 14Z — 28 реально выполненных SOURCE-проверок
**Метод:** прочитаны конкретные файлы и официальные страницы; каждая строка — отдельное утверждение, не тест Archicad. Результаты предыдущего 13Z проверены повторно. PR74 immutable commit f7c37b84b76c040c417ccd58a5543326e50f673a. OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.

01. Issue #192 требует новую scratch PLN, G0–G5, не повтор 21-element fixture: https://github.com/dvikt33-ux/safe-bim-layer/issues/192
02. №1 TRIAD-PIVOT 11Z требует AC29/Rhino8/GH и запрещает второй writer: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/research-1-20261023T11Z-TRIAD-PIVOT.md
03. NEXT 20.10 фиксирует приоритет BUILD-01 и исторический rev182 read-only: https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/NEXT_RESEARCH_PRIORITIES.md
04. Реестр priority_matrix_20261018.json имеет `count=61`, `items=61`, `GRASSHOPPER priority=40` (до triad): https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/priority_matrix_20261018.json
05. PR74 исторически создавал 10 Walls/2 Slabs/6 Windows/2 Doors/1 Roof, не универсальный BUILD-01: https://github.com/dvikt33-ux/safe-bim-layer/pull/74
06. PR162 group-first использует существующий SceneWriter и пока SOURCE_INTEGRATED_PENDING...: https://github.com/dvikt33-ux/safe-bim-layer/pull/162
07. PR149 подтверждает ограничение Basic Slab CREATE и отдельный MODIFY: https://github.com/dvikt33-ux/safe-bim-layer/pull/149
08. Fixture PR74 имеет `schemaVersion=apa-authored-project/1`, `units=meters`: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json
09. Fixture имеет `brief.stories` с этажами 0 и +3 м, native index 0/1: тот же fixture.
10. Fixture содержит `brief.mode=ADAPT_EXISTING` и `targetProjectPath`, а не универсальный new-story creator: тот же fixture.
11. Fixture содержит `layout.outline`, bearingLines, `storyHeights`, `nativeComponents`: тот же fixture.
12. Hosted Door/Window используют `ownerWallId.guid.$createdGuid`: тот же fixture.
13. `compile_authored_intent` требует ровно основные поля projectId/units/brief/cseCandidate/layout/storyHeights: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py
14. `compile_authored_intent` сравнивает `brief.targetProjectPath == RUN.EXPECTED_PATH`: тот же compiler.
15. `run_project` отвергает authored `mode=offline` без native read transport: тот же compiler.
16. `evidenceKind=LIVE` при native_transport может маркировать даже read-only preflight; это НЕ CREATE: тот же compiler.
17. CLI поддерживает `--preflight`, `--execute`, `--intent`, `--schema`, `--isolated-port`, `--confirm-plan-hash`: тот же compiler.
18. `compile_candidate` разрешает только READ GetProjectInfo/GetStories/GetAttributesByType и проверяет высоты/уровни: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_native_plan.py
19. `compile_candidate` требует точный `nativeStoryBindings` и совпадение material GUID: тот же native plan.
20. `SceneWriter.ALLOWED_WRITES` включает CreateWalls/Slabs/Columns/Windows/Doors, а CreateBeams/Roofs требуют typed adapter: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py
21. SceneWriter записывает `BASIC_MODIFY_ATTEMPTED` в SQLite **перед** ModifySlabs; журнал есть, но отдельное разрешение на WRITE всё ещё требуется: тот же SceneWriter.
22. Pinned Tapir 1.5.10 `CreateSlabs.slabsData` не имеет structureType/buildingMaterialId: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json
23. Pinned `ModifySlabs.slabsWithDetails` имеет structureType/buildingMaterialId: тот же pinned schema.
24. Existing `nativeLibraryExpectations` проверяет `libPart.name/ownUnID.guid`, только при заполнении: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_extension.py
25. Graphisoft AC29 GH Live Connection build3000, Windows16.8MB, Rhino7/8, 01.10.2025; AC30 другой installer с тем же build: https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/
26. Rhino8 `-GrasshopperPlayer` выполняет GH definition без окна; `-Grasshopper Solver Disable` лишь останавливает GH solver: https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm
27. jSwan MIT имеет Serialize/Deserialize JSON, List Access/Lock Structure; версия 1.2.1 от 2020 (Rhino8 compatibility NOT_VERIFIED): https://github.com/andrewheumann/jSwan ; https://grasshopperdocs.com/addons/jswan.html
28. GH Panel имеет Stream Contents/Stream Destination, записывает при обновлении (риск overwrite, не транзакция): https://smorgasbord.cdp.arch.columbia.edu/modules/5-computational-design-modeling-in-grasshopper/5-7_design-space/ ; https://gdocu.upv.es/alfresco/service/api/node/content/workspace/SpacesStore/9e7ef2af-c4da-4fdb-b4ca-0d2a5fe970f2/TOC_0270_03_01.pdf?guest=true

**Отрицательные проверки:** новый отдельный №3 за 23.10 по опробованному пути не найден; `PROJECT_PLAN.json` в корне и docs/ не найден; исходный код на исследовательской ветке отсутствует, поэтому проверялся immutable PR74 commit. Эти 404 не считаются успешными SOURCE-проверками. Не подтверждены Rhino8+jSwan runtime, локальный Tapir1.5.10 binary, APX, GDL, BREP, любое native WRITE.
