# APA №2 — 30 реально выполненных SOURCE-сверок, 2026-10-23 19Z

Сверка = прочтение конкретного первичного источника/закреплённого файла и проверка конкретного утверждения. Это **30 утверждений**, а не 30 локальных тестов или 30 независимых сайтов. GitHub connector fetch_file/fetch_pr; официальные страницы Graphisoft/McNeel и upstream releases. Все — SOURCE_ONLY.

| № | Проверенное утверждение | Источник |
|---|---|---|
| 01 | BUILD-01 требует новые G0..G5 и единственный SceneWriter, старый 21-element demo не ACCEPTED | [issue192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) |
| 02 | TRIAD-PIVOT требует GH/Rhino и честного направления синхронизации | [pivot](research-1-20261023T11Z-TRIAD-PIVOT.md) |
| 03 | NEXT запрещает менять main/PLN/APX и считает новый OFFLINE=0 | [NEXT](../NEXT_RESEARCH_PRIORITIES.md) |
| 04 | Матрица содержит 61 кандидат, Tapir1.5.10 и Graphisoft Python как существующие | [61](../priority_matrix_20261018.json) |
| 05 | PR74 — draft, исторический 10 Wall/2 Slab/6 Window/2 Door/1 Roof прототип | [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) |
| 06 | `compile_authored_intent` проверяет `apa-authored-project/1` и targetProjectPath | [PR74 compiler](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py) |
| 07 | Исходный пример PR74 привязан к конкретной `APA_Isolated_Writer_Test_01.pln`, не к новой scratch | [PR74 example](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/examples/accelerator/model-first-building.json) |
| 08 | `bind_authorized_saved_copy` требует путь, name, saved SHA256, authorization_ref | [PR74 guard](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py) |
| 09 | PR74 native plan передаёт Slab `level` как абсолютную Z | [PR74 native](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_native_plan.py) |
| 10 | PR74 extension связывает host Wall GUID при создании проёмов | [PR74 extension](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_authored_extension.py) |
| 11 | PR126 `execute_batch` существует в DynamicCommands, не второй writer | [PR126](https://github.com/dvikt33-ux/safe-bim-layer/pull/126) |
| 12 | PR131 предлагает source-qualified Walls/Slabs/hosted openings, но не universal create | [PR131](https://github.com/dvikt33-ux/safe-bim-layer/pull/131) |
| 13 | PR149 фиксирует CreateSlabs material gap pinned 1.5.10 | [PR149](https://github.com/dvikt33-ux/safe-bim-layer/pull/149) |
| 14 | Pinned schema содержит **262** команды, Get3DGeometryOfElements в ней нет | [pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) |
| 15 | Pinned CreateSlabs v1.0.3: `favoriteName,level,thickness,referencePlaneLocation,polygonCoordinates,polygonArcs,holes,floorIndex`, нет трёх structure/material полей | [pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) |
| 16 | Pinned ModifySlabs v1.4.0: `polygonOutline` без `holes` удаляет отверстия | [pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) |
| 17 | Pinned CreateWalls: при floorIndex zCoordinate — offset, без floorIndex — absolute Z | [pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) |
| 18 | Pinned CreateRoofs: pivotLine → SinglePlane, без него → MultiPlane, levels max16 | [pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) |
| 19 | PR82 имеет bounded MultiPlane Roof, но не универсальный authored PR74 path | [PR82](https://github.com/dvikt33-ux/safe-bim-layer/pull/82) |
| 20 | PR162 group-first использует `CloneNativeGroupV1` / `CreateNativeGroupV1`, SOURCE_PENDING | [PR162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) |
| 21 | Upstream PR785 добавляет direct CreateSlabs `structureType/buildingMaterialId/compositeId`, не в pinned 1.5.10 | [PR785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785) |
| 22 | Tapir 1.7.1 release прямо перечисляет PR785, 1.7.2 от 19.10.2026 | [releases](https://github.com/ENZYME-APD/tapir-archicad-automation/releases) |
| 23 | Upstream PR865: `Get3DGeometryOfElements` возвращает polygon/vertex/holes; GH Element3DGeometry = Mesh, не BREP | [PR865](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865) |
| 24 | Upstream PR866 GH Details→Create field alignment имеет null несовместимости для смешанных структур | [PR866](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/866) |
| 25 | PR615 Tapir GH EmbedMetadata default true, ReplaceExisting false; true удаляет прежние элементы/hosted openings | [PR615](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/615) |
| 26 | PR861 исправляет возможный ложный success Move/Rotate на locked/hidden; pinned 1.5.10 нельзя считать исправленным | [PR861](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/861) |
| 27 | Graphisoft AC29 GH Live Connection build3000 01.10.2025 Windows Rhino7/8, не universal 3-way | [Graphisoft](https://www.graphisoft.com/en-aw/downloads/add-ons/rhino-grasshopper/) |
| 28 | McNeel Rhino MCP Platform v0.3.0 Rhino8 Windows rh8_19-win, инструмент управления Rhino/GH, не native BIM writer | [Yak](https://rhinopackages.github.io/package/Rhino-MCP-Platform) |
| 29 | McNeel предупреждает о неверном целевом окне при нескольких Rhino и требует проверки | [troubleshooting](https://mcneel.github.io/RhinoAI/docs/troubleshooting/) |
| 30 | Аудитор №3 20.10 18Z: IsAlive не identity PLN, runtime guard и installed schema требуют отдельного G0 receipt | [№3 A](audit-2026-10-20-18-A.md), [№3 B](audit-2026-10-20-18-B.md) |

**Контроль версий:** Tapir pinned schema Git blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`; PR74 compiler blob `8e0ce2fbb5441009925f0d9199e180e8670a5eea`; PR74 native blob `f57812f29c826bc48ce3c6ffd0f9b6a7dc628a7`; PR74 extension blob `e6d5bbf760c82e934b194205edd0fb133d2212fa`; PR74 guard blob `ca91c1cfc41cee763c62d1f3a70337d74fbafd53`. Это **SOURCE hashes**, не локальные APX SHA.

**Не считались проверками:** любые невыполненные Rhino/GH/Archicad тесты, установки, OFFLINE/LIVE, BREP независимая приёмка, новые лицензии, запись в PLN. Итог SOURCE=30 утверждений; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0/0/0/0/0.
