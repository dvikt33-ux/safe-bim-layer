# APA №2 — BUILD-01: 9 способов подключения (19Z)

Баллы 0–100 — **экспертный приоритет, не ускорение и не benchmark**. Источник: PR74/126/131/149/150/159/162 (точные Git SHA в checks-B); pinned Tapir provider 1.5.10, upstream MIT; лицензия APA NOT_VERIFIED. Общий путь: SOURCE → OFFLINE → BUILD → INSTALLED → LIVE → ACCEPTED. Здесь подтверждён только SOURCE.

| Gate/балл | Барьер → готовый интерфейс → минимальный путь → ГОТОВО |
|---|---|
| G0 / 100 | Неизвестны APX и реальные команды. PR162 `archicad_runtime_version_probe`: `GetProductInfo`, `GetProjectInfo`, `GetAddOnVersion`, `GetStories`; официальный `IsAddOnCommandAvailable(AddOnCommandId)`. Только READ: путь/порт/build5101, SHA256 загруженного APX, список registered command IDs и их schemas; **RUNTIME_READY** лишь при полном совпадении. |
| G1 / 99 | Этажи/высоты. PR74 `archicad_authored_native_plan`: `nativeStoryBindings`, `GetStories`, `floorIndex`, абсолютный `level`; проверить высоты обоих этажей и новый plan hash в существующем BIM Graph. **OFFLINE_PASS** после фактического прогона нового DAG. |
| G2 / 100 | Slab материал. `CreateSlabs.slabsData` требует `level,polygonCoordinates`, принимает `favoriteName,floorIndex,thickness`, **НЕ принимает** `structureType,buildingMaterialId`. PR131 qualified Favorite (`settingsHash`); альтернатива: подтверждённый `ModifySlabs.slabsWithDetails` после CREATE и независимый readback. Без этого **BLOCKED**. |
| G2 / 98 | Wall/Column/Roof. `CreateWalls.wallsData` beg/end/height/thickness, floorIndex/structureType/material; `CreateColumns.columnsData` coordinates/floorIndex; `CreateRoofs.roofsData` level/polygonCoordinates, pivotLine/angle/material. Использовать PR74 + PR149 scoped verifiers; **ГОТОВО** по native GUID/типу/этажу/BREP/материалу. |
| G2 / 99 | Host проёмов. `CreateWindows.windowsData`, `CreateDoors.doorsData`: `ownerWallId` + `centerOffset` обязательны; qualified libraryPartName/Favorite, размеры, ориентация, коллизии. PR131 hostContext + PR74 BIM dependencies; **ГОТОВО** при readback host GUID/геометрии. |
| G3 / 80 | Batch: PR126 `DynamicCommands.execute_batch` 1–200 за один SceneWriter intent; PR74 `created_guid` требует один GUID. Для первого здания single-create; packed только с детерминированным mapping GUID→DAG. **ГОТОВО** при receipt на каждый элемент и без повторного CREATE. |
| G3 / 65 | Группы: PR162 `CreateNativeGroupV1`→`CloneNativeGroupV1`, `$result:/groupId`, sourceRef; уже существующий writer. Применять после базовой модели. **ГОТОВО** при source/target GUID, независимом BREP и отсутствии дубликатов. |
| G3 / 55 | Beam: PR162 BIM Graph знает `CreateBeams`, SceneWriter требует opt-in adapter из `connected_components`; `beamsData` beg/end/zCoordinate. **OPTIONAL_UNSUPPORTED**, пока не доказан установленный adapter. |
| G4–G5 / 100 | Неполный readback. `GetAllElements({})` не доказывает оба этажа; использовать Navigator database IDs, отдельную инвентаризацию этажей, `GetModelDumpV1` только после проверки registration и 3D-фильтров. GuardedSave→Close→Reopen→сверка GUID/BREP; затем другое задание/новая scratch. **ACCEPTED** только после независимого протокола. |

**Минимум внешних звеньев:** Graphisoft JSON API + уже установленный Tapir + существующий APA DynamicCommands/BIM Graph/SceneWriter/SQLite. Никакого второго writer/router, платного MCP или нового engine. Внешние skill-файлы — только необязательная документация.
