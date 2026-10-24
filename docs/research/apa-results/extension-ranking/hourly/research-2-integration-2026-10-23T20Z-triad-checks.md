# APA №2 — 30 предметных SOURCE-проверок / 2026-10-23 20Z
Счёт = конкретные проверенные утверждения, не 30 разных репозиториев и не 30 программных испытаний. Все SOURCE_ONLY; использованы GitHub fetch_issue/fetch_pr/fetch_file и официальные страницы. Для pinned schema hash=e8ad53b6ea7c19dc34cbdcb723a79be995639cd7, PR74 commit=5a3a9201a715a5528c93bed4a5318e2acb32eea7.

| № | Реально сверенное утверждение | Первоисточник |
|---|---|---|
| 01 | BUILD-01 G0–G5 требует новое двухэтажное здание, не старый demo | https://github.com/dvikt33-ux/safe-bim-layer/issues/192 |
| 02 | NEXT P0 запрещает второй writer и изменение main/PLN | ../NEXT_RESEARCH_PRIORITIES.md |
| 03 | TRIAD-PIVOT определяет задачи №2 по AC/Rhino/GH | research-1-20261023T11Z-TRIAD-PIVOT.md |
| 04 | Матрица 61 существует в указанном архиве | ../priority_matrix_20261018.json |
| 05 | PR34 строит 25 native operations через один SceneWriter | https://github.com/dvikt33-ux/safe-bim-layer/pull/34 |
| 06 | PR48 добавляет authored model + проверяемые hosted edits | https://github.com/dvikt33-ux/safe-bim-layer/pull/48 |
| 07 | PR74 21-элементный исторический прототип, не BUILD-01 | https://github.com/dvikt33-ux/safe-bim-layer/pull/74 |
| 08 | PR82 MultiPlane Roof уже существует, authored путь иной | https://github.com/dvikt33-ux/safe-bim-layer/pull/82 |
| 09 | PR126 packed create 1..200 переиспользует DynamicCommands | https://github.com/dvikt33-ux/safe-bim-layer/pull/126 |
| 10 | PR131 qualified Slab Favorite, hosted doors/windows | https://github.com/dvikt33-ux/safe-bim-layer/pull/131 |
| 11 | PR149 pinned CreateSlabs не содержит direct buildingMaterialId | https://github.com/dvikt33-ux/safe-bim-layer/pull/149 |
| 12 | PR162 group-first уже существует, не клонировать CloneNativeGroupV1 | https://github.com/dvikt33-ux/safe-bim-layer/pull/162 |
| 13 | PR74 compile_authored_intent требует typed schema и targetProjectPath | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py |
| 14 | PR74 пример уже содержит floorPlans/2 stories/roof, но старый PLN path | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/examples/accelerator/model-first-building.json |
| 15 | PR74 native plan Slab level absolute, story bindings обязательны | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py |
| 16 | PR74 extension поддерживает nativeLibraryExpectations и host checks | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py |
| 17 | PR74 guard bind_authorized_saved_copy требует saved SHA256 и authorization | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py |
| 18 | PR74 documentation adapter включает PublishPublisherSet и требует selected IDs 1..4, empty output | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_bim_documentation.py |
| 19 | PR74 SceneWriter.execute_bound_operation проводит PublishPublisherSet через SQLite и GetModelDumpV1 before | https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py |
| 20 | Tapir1.5.10 IFCFileOperation v1.2.6 save+translatorName+EntireProject, отдельная файловая WRITE | https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json |
| 21 | Tapir1.5.10 GetIFCExportTranslators v1.5.10 READ | https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json |
| 22 | Tapir1.5.10 GetIFCIdsOfElements/GetElementsByIFCIds v1.5.1, externalIFCId может быть неоднозначным | https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json |
| 23 | Tapir1.5.10 PublishPublisherSet v0.1.0, GetNavigatorItemTree PublisherSets | https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json |
| 24 | Graphisoft AC29 IFC export поддерживает Publisher и translator per item | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-4.htm |
| 25 | Graphisoft AC29 IFC BREP retains junctions, parametric attributes can be lost, collision-only and gross geometry filters affect result | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-37.htm |
| 26 | Graphisoft AC29 Publisher IFC exports visible elements only, независимо от translator filter | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-45.htm |
| 27 | Graphisoft AC29 Archicad IFC ID = GlobalId; External IFC ID for imported model | https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-12.htm |
| 28 | Graphisoft AC29 GH guide Synchronize TRUE auto writes, FALSE Null; Deconstruct Roof SinglePlane only | https://help.graphisoft.com/AC/29/INT/GC.pdf |
| 29 | Graphisoft AC29 GH guide deleting GH Object Settings deletes generated Embedded Library Part; AC29 connection build3000 supports Rhino8 | https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/ |
| 30 | IfcOpenShell 0.9.0post1 supports OpenCASCADE BRep with explicit OCC configuration, LGPL | https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html |

**Не засчитаны как PASS:** installed APX, Rhino/GH installed, standalone OFFLINE, BUILD, LIVE, Save/Open, IFC export, OCC BRep readback, IFC ID equality, automatic 3-way sync. SOURCE 30; OFFLINE 0; BUILD 0; INSTALLED 0; LIVE 0; ACCEPTED 0. №3 20.10 18Z прочитан, свежие 23.10 по точным путям не обнаружены; PROJECT_PLAN rev182 не извлечён.
