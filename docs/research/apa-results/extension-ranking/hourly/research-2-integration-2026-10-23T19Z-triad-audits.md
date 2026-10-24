# APA №2 — два независимых контрааудита SOURCE / 2026-10-23 19Z

## Контрааудит A: «Tapir 1.7.2 закрыл G2 и G4?»

**Проверяемое оптимистическое утверждение:** новый upstream Tapir решает материал Slab одной операцией и независимый BREP, поэтому BUILD-01 готов.

**Контрпроверка 1 (схемы):** pinned 1.5.10 `CreateSlabs` не содержит `structureType/buildingMaterialId/compositeId` (Git blob e8ad53b6...); PR785 + release 1.7.1 добавляют эти поля только в новую версию. `Get3DGeometryOfElements` в pinned 262 commands отсутствует. Следовательно, локальный payload/command не квалифицирован.

**Контрпроверка 2 (геометрия):** PR865 описывает polygon vertices/face holes и Rhino Mesh, не BREP. Более того, геометрию предоставляет тот же Tapir provider; это не независимый reader. Исторический PR82 MultiPlane roof и PR74 Save/Open не доказывают нового BUILD-01 G4.

**Вердикт A:** `G2_UPGRADE_CANDIDATE_SOURCE_ONLY`, `G4_INDEPENDENT_BREP_NOT_FOUND`. Следующий безопасный шаг: read-only installed APX/command inventory; не менять версию и не выполнять write. Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785 ; https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865 ; https://github.com/dvikt33-ux/safe-bim-layer/pull/149 .

## Контрааудит B: «GH metadata/ReplaceExisting дают настоящую 3-way sync?»

**Проверяемое оптимистическое утверждение:** Tapir GH `Component Guid` гарантирует стабильный native GUID и `ReplaceExisting` безопасно синхронизирует Rhino/GH/Archicad.

**Контрпроверка 1 (идентичность):** PR615 хранит путь GH definition, локальное время, GH `InstanceGuid` компонента. Это не native GUID каждого элемента. `ReplaceExisting=true` делает новый Create и удаляет старые GUID, включая host walls с зависимыми проёмами. `ReplaceExisting=false` дублирует объекты. Предупреждение при ошибке metadata не откатывает native Create.

**Контрпроверка 2 (ownership):** GH Create* идёт мимо APA SceneWriter/SQLite; Graphisoft GH Live Connection имеет отдельный механизм Synchronize и не останавливает Tapir GH Create*. PR866 даёт удобные поля Details→Create, но при mixed Basic/Composite возможны null; создание нового элемента не эквивалентно Modify существующего GUID. Наличие McNeel MCP не даёт транзакций или единого owner.

**Вердикт B:** `FULL_THREE_WAY_SYNC=NOT_FOUND`. Для APA-owned GUID: GH только параметры/JSON staging, native mutation только SceneWriter, конфликт STOP+read-only reconciliation. Для не-APA-owned GH элементов допускается отдельная область/PLN и отдельная приёмка, но не смешивание в BUILD-01. Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/pull/615 ; https://github.com/ENZYME-APD/tapir-archicad-automation/pull/866 ; https://mcneel.github.io/RhinoAI/docs/troubleshooting/ .

Оба аудита — самостоятельные сопоставления исходных контрактов, **не** независимые LIVE испытания. SOURCE_ONLY; новых ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
