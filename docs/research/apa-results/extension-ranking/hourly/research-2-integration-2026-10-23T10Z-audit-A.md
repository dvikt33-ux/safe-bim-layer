# APA №2 | 10Z | Контрааудит A — двойная WRITE Slab

**Вопрос:** действительно ли текущий SceneWriter реализует два самостоятельных разрешения на `CreateSlabs` и `ModifySlabs`?

**SOURCE:** [archicad_scene_run.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py), Git blob `484c600a205192d5737e124f8d47c8583e07a9f3`; [archicad_project_accelerator.py](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py), blob `439f6d26ce097cdfdfc33a2b5a245352073151f2`; pinned schema blob `e8ad53b6ea7c19dc34cbdcb723a79be995639cd7`.

**Проверка:** `SceneWriter.allowed_writes=ALLOWED_WRITES|adapters.keys()`; `ALLOWED_WRITES` содержит `CreateSlabs`, но не `ModifySlabs`. На строках 948–956 `approval_record.permission=command`, то есть `CreateSlabs`. После GUID и промежуточного readback на 975–1007 формируется `modify_intent` с вложенным старым approval и `BASIC_MODIFY_ATTEMPTED`, затем вызывается `self.api('ModifySlabs',modify)`. Нет отдельной проверки `permission='ModifySlabs'`. `EvidenceAPI(execute=True)` разрешает обе мутации на уровне общего набора команд, но это не два независимых approval.

**Контрпроверка схемы:** pinned `CreateSlabs` поля `favoriteName,level,thickness,referencePlaneLocation,polygonCoordinates,polygonArcs,holes,floorIndex`; `structureType/buildingMaterialId` отсутствуют. `ModifySlabs` оба поля имеет. Нельзя подменить второй шаг добавлением несуществующих CREATE-полей.

**Результат:** технический маршрут существует, но **политика двух отдельных санкций в коде не обеспечена**. Новое обозначение `DUAL_WRITE_APPROVAL_NOT_ENFORCED`, G2 `WRITE_BLOCKED`. Готового отдельного guard в проверенном пути не найдено — `NOT_FOUND`; требуется минимальная проверка внутри существующего SceneWriter (не новый writer/router), отдельный readback, разрешение владельца. Ни одного native WRITE не выполнено.
