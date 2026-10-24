# APA №2 — 2026-10-23 13Z — два самостоятельных контрааудита

## Контрааудит A — GH identity, владение, конфликты, удаление
**Проверяемая гипотеза:** Graphisoft GH Live Connection автоматически превращает Archicad29+Rhino8+GH+APA в симметричный трёхсторонний редактор, который сохраняет GUID и устраняет конфликты.

1. Официальный AC29 GC.pdf подтверждает ID-based association между GH definition и элементами, которые СОЗДАЛ GH. Это не доказательство привязки к произвольным APA-owned GUID. 
2. GH Design/Document генерируют реальные locked Archicad элементы. После unlock правки AC разрешены, но значения входов GH применяются повторно при пересчёте. Это конкретный риск silent overwrite: AC ручная правка ≠ гарантированно авторитетная.
3. Неуправляемые GH параметры наследуют текущие Archicad Tool Defaults при CREATE; одна и та же GH definition при разных Defaults может давать разные BIM materials/settings. Нужно explicit settings и readback.
4. GH native writes обходят существующий SceneWriter/SQLite ledger, а значит не удовлетворяют single-writer invariant BUILD-01. GH Synchronize FALSE, Rhino Solver Disable и GrasshopperPlayer не являются distributed commit/undo.
5. Возможные GH-created element deletion/recreation, GUID drift, feedback loops и связь native SEO/host не доказаны на установленной связке; запретить auto-replay после UNKNOWN.

**Контрвывод A:** FULL_AUTO_TRIAD_SAME_GUID=NOT_FOUND; строгий маршрут — GH READ/reference/preview, только SceneWriter нативно пишет APA-owned. GH-owned и APA-owned могут сосуществовать в непересекающихся областях, но это второй native writer и не соответствует строгому P0. До независимого Save/Open+BREP статус SOURCE_ONLY.

Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf (официальный индексированный фрагмент), https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/, https://docs.mcneel.com/rhino/8/help/en-us/commands/grasshopper.htm, https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py

## Контрааудит B — исправление GDL-утверждения и нативной полноты
**Проверяемая гипотеза:** отсутствие универсального GDL-identity readback означает, что готового способа проверить библиотечную часть в APA вообще нет; pinned schema и старый BUILD prototype достаточны для G2–G4.

1. Прямой SOURCE аудит archicad_authored_extension.verify_model показывает существующий условный код: `nativeLibraryExpectations[sid]` → `GetDetailsOfElements.details.libPart.name` и `libPart.ownUnID.guid` → ошибка при несовпадении. Следовательно прежнее безусловное «GDL readback NOT_FOUND» было слишком сильным. Исправление: `EXISTS_CONDITIONAL_NOT_WIRED_FOR_FIXTURE`.
2. Прямой SOURCE аудит examples/accelerator/model-first-building.json показывает отсутствие `nativeLibraryExpectations`, `favoriteName` и `libraryPartName` в sample openings. Следовательно sample не доказывает проверку фактической GDL identity. GetAvailableLibraryParts/GetFavoritesByType позволяют READ-only подготовить binding, но автоматическая вставка expectations в компилятор не подтверждена.
3. Tapir CreateSlabs не имеет structureType/buildingMaterialId; ModifySlabs имеет. SceneWriter сохраняет intent перед ModifySlabs, но отдельная человеческая авторизация и граница ошибки должны быть явно квалифицированы. Считать CREATE Slab материально готовым нельзя.
4. NativeAdapter(CreateBeams) существует, но run_project wires only roof. Отсутствие Beam в конкретном run не означает отсутствия API, но BUILD-01 Beam пока BLOCKED_ADAPTER_WIRING.
5. Pinned GetModelDumpV1 отсутствует; независимый installed BREP неизвестен. Исторические 21 native elements, Save/Open и native geometry — полезный исходный факт, но не новый BUILD-01.
6. Graphisoft .3dm import/export встроен с AC25, но перенос NURBS как reference/object не доказывает native Wall/Roof/BIM type; старый GDL converter описывает Rhino5 и не даёт подтверждённой AC29/Rhino8 схемы.
7. Tapir MIT и GH plugin package 'tapir' существуют, но upstream называет plugin WIP; статическая coverage page явно не runtime PASS. Нельзя считать plugin заменой SceneWriter.
8. Точная версия GH add-on AC29 build3000 от 2025-10-01 не доказывает, что она установлена на AC29 build5101. AC30 build3000 от 2026-10-07 — другой инсталлятор. Rhino8 trial не бессрочна.

**Контрвывод B:** G0 BLOCKED_RUNTIME, G1 NOT_RUN, G2 SOURCE_ONLY (GDL условный readback уже есть, wiring требует проверки), G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Нет ни одного нового OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED. Нового кода не требуется для чтения GDL identity, но готовая автоматическая привязка expectations к fixture НЕ подтверждена.

Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_authored_extension.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/examples/accelerator/model-first-building.json ; https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json ; https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://github.com/ENZYME-APD/tapir-archicad-automation ; https://enzyme-apd.github.io/tapir-archicad-automation/gh-coverage/

**Независимость:** это два разных теста гипотез по разным источникам и инвариантам, проведённые данным исследователем; НЕ независимый аудит №3, НЕ две LIVE-проверки, НЕ строительная экспертиза. MODEL_MODE_NOT_VERIFIABLE.
