# APA №2 — матрица 9 готовых маршрутов подключения | 09Z

**Общее:** Archicad 29 build5101 / Windows11 / заявленный локальный Tapir1.5.10; фактический PID/APX/PLN не прочитан. Источник APA — pinned PR162 `f7c37b84b76c040c417ccd58a5543326e50f673a`; Tapir — MIT, upstream provider 1.7.3 НЕ равен installed 1.5.10. Баллы 0–100 — экспертный приоритет, не ускорение. Все строки SOURCE_ONLY до runtime.

| ID / приоритет | Барьер BUILD-01 | Готовая функция / интерфейс | Минимальная цепочка | ГОТОВО и статус |
|---|---|---|---|---|
| I09-01 / **100** | G0: неизвестен loaded APX | Windows `Get-Process -Module` + `Get-FileHash -Algorithm SHA256`; existing `GetAddOnVersion`, `GetProjectInfo` | PID→APX path/hash→port/PLN/version; **без установки** | Один PID, immutable APX hash, фактическая версия и runtime command list; **BLOCKED_NO_WINDOWS** |
| I09-02 / **100** | G0/G2: команда в каталоге, но не runtime | `DynamicCommands.probe_runtime(api,command)` → `API.IsAddOnCommandAvailable` | existing router→Archicad JSON | Регистрация каждой нужной команды, schema source отдельно; **SOURCE_ONLY** |
| I09-03 / **99** | G1: 2 story bindings | PR74 `compile_candidate`, `GetStories`, `GetAttributesByType` | brief/layout→existing BIM DAG→SceneWriter preflight | Совпадают `nativeStoryBindings`, elevations, material GUID, plan hash; **SOURCE_ONLY** |
| I09-04 / **99** | G2: материал перекрытия верхнего этажа | PR74 SceneWriter `CreateSlabs`→`ModifySlabs`, `slabsWithDetails[].elementId/structureType/thickness/buildingMaterialId` | один writer, 2 последовательные native mutations | Явно разрешены обе операции, floorIndex 0/1, GUID/материал/BREP readback; **SOURCE_ONLY** |
| I09-05 / **97** | G2: PR149 slab verifier floor0 | **Не** использовать `VerifiedBasicSlabMaterial` для story1; PR74 already handles all stories | существующий SceneWriter, без второго verifier | Negative OFFLINE story1 for PR149; positive full SceneWriter path; **SOURCE_ONLY** |
| I09-06 / **98** | G2: Beam command не подключён | `archicad_connected_components.adapters(['beam'])` + `SceneWriter(adapters=...)` | existing adapter→existing writer | В preflight `CreateBeams` в `allowed_writes`, typed Beam readback; **STATIC_BLOCKER** |
| I09-07 / **97** | G2: Walls/hosted openings | PR34/74 `CreateWalls` + `CreateDoors/CreateWindows`, `ownerWallId.guid.$createdGuid` | typed DAG→GUID binding→SceneWriter | Реальный host GUID, floorIndex/width/height/sillHeight; **SOURCE_ONLY** |
| I09-08 / **97** | G2/G4: BeamSegment inventory | existing `assembly_subelements(api,created,'Beam')` + `GetAllElements` | existing graph→read-only reconciliation | Условный child GUID diff доказан установленным read-only перечислением; **NOT_VERIFIED** |
| I09-09 / **100** | G4: независимый BREP и Save/Open | existing `GetModelDumpV1` path only if runtime registered; `GuardedSave` + GUI close/reopen | saved copy→read-only inventory→BREP | Runtime BREP available, GUID/host/material/bodies unchanged; **BLOCKED_UNPROVEN_RUNTIME** |

**Лицензии:** Tapir upstream MIT; Microsoft PowerShell штатная ОС, лицензия Windows11; исходники APA — собственный репозиторий, лицензия APA из лицензии Tapir не следует. Дополнительные платные пакеты и новый writer не требуются по выбранным маршрутам. **I09-06** — минимальная интеграция в существующий вызов, не готовый установленный wiring.
