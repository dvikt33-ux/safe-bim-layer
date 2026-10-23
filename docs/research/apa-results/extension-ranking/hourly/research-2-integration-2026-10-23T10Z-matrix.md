# APA №2 | 10Z | Матрица 9 маршрутов BUILD-01

Источник: immutable PR162 f7c37b84b76c040c417ccd58a5543326e50f673a, pinned Tapir 1.5.10 JSON 262 commands, GitHub issue #192. Баллы — экспертная важность, НЕ benchmark. Все SOURCE_ONLY, installed contract неизвестен. Tapir upstream MIT; собственный APA не наследует эту лицензию автоматически.

| ID / балл | G0–G5: барьер → готовый контракт | Минимальный маршрут и критерий ГОТОВО |
|---|---|---|
| I10-01 / **100** | **G2: DUAL_WRITE_APPROVAL_NOT_ENFORCED.** `SceneWriter._execute_verified_plan`: `CreateSlabs` approved, затем `ModifySlabs` напрямую, без второй `permission`. | Existing SceneWriter+SQLite; нужна отдельная санкция и readback ModifySlabs. **WRITE_BLOCKED**, минимальный guard внутри существующего writer, не второй writer. |
| I10-02 / **100** | G0: loaded APX ≠ `provider_version`. Windows `Get-Process -Module`, `Get-FileHash -Algorithm SHA256`, `GetAddOnVersion`. | PID→loaded APX path/hash→port/PLN/version; **BLOCKED_NO_WINDOWS**. ГОТОВО: runtime identity-квитанция. |
| I10-03 / **99** | G0: pinned schema ≠ runtime. `DynamicCommands.probe_runtime` → `API.IsAddOnCommandAvailable`. | Existing DynamicCommands/JSON; проверка регистрации, затем отдельная read-only проверка точной схемы. **SOURCE_ONLY**. |
| I10-04 / **99** | G1: authored `run_project(mode='offline')` запрещён; `GetStories`, `nativeStoryBindings`, `compile_candidate`. | READ-ONLY `preflight` с exact scratch PLN и активным story, typed DAG/hash. **NOT_RUN**. |
| I10-05 / **99** | G2: pinned `CreateSlabs` не содержит `structureType/buildingMaterialId`, `ModifySlabs` содержит. | CreateSlabs→GUID→readback→санкционированный ModifySlabs→readback; floorIndex 0/1, материал, толщина, holes. **DUAL_SCOPE_BLOCKED**. |
| I10-06 / **98** | G2: `NativeAdapter('CreateBeams')` есть, `run_project` подключает только `adapters(['roof'])`. | Existing adapter opt-in внутри текущего `run_project`; без второго router. ГОТОВО: `CreateBeams` allowed + Beam/segment GUID readback. **STATIC_BLOCKER**. |
| I10-07 / **99** | G2: `CreateWindows/CreateDoors` + `ownerWallId.guid`; upstream Tapir issue #481 показывает возможный GUID без элемента. | PR74 DAG hostWall→поэлементный CREATE→GetElementsByType + GetDetailsOfElements host. ГОТОВО: GUID, native type, wall host, физический проём. **SOURCE_ONLY**. |
| I10-08 / **97** | G2: PR126 packed create 1–200 через `DynamicCommands` с independent pre/post verify; не wired автоматически в authored loop. | Existing DynamicCommands→SceneWriter/SQLite, только после отдельного допуска. ГОТОВО: реальные batch receipts; **не** обязательный барьер первой модели. |
| I10-09 / **100** | G4: `archicad_authored_geometry.run` требует `GetModelDumpV1`, которого **нет** в pinned 262 commands; AABB ≠ BREP. | Runtime read-only registration → независимый BREP, GuardedSave/GUI close/reopen, GUID/host/material. Если runtime нет: **NOT_FOUND**, минимальный read-only BREP adapter или G4 BLOCKED. |

**Обязательные типы первой модели:** Walls/Slabs/Roof/Doors/Windows; Columns/Beams только при подтверждённом native contract. `CreateRoofs` через существующий typed adapter ограничен SinglePlane Basic. `CreateColumns` в pinned схеме имеет `floorIndex`, но PR149 verifier floor0 не годится как общий двухэтажный путь. `GetFavoritesByType`/`GetAvailableLibraryParts` доступны в pinned schema для READ-only выбора дверей/окон; фактические библиотечные части неизвестны.

**Отдельные направления:** IFC/DXF/Hotlink/MEP/SAF/Publisher — сохраняются, но не подменяют BUILD-01. G0 BLOCKED; G1 SOURCE_ONLY; G2 SOURCE_ONLY+DUAL_SCOPE_BLOCKED; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. SOURCE 30 / OFFLINE 0 / BUILD 0 / INSTALLED 0 / LIVE 0 / ACCEPTED 0.
