# APA №2 — BUILD-01 | 23.10.2026 09Z | инженерный отчёт SOURCE

## Конкретный вклад в G0–G5

**S09-01 / G2 / 99/100:** найден готовый **сквозной путь материала перекрытия двух этажей без нового writer**: `SceneWriter._execute_verified_plan` уже выполняет `CreateSlabs → GUID → readback → journal BASIC_MODIFY_ATTEMPTED → ModifySlabs → readback`. Этот путь использует `floorIndex` из исходного шага и не ограничен этажом 0. Отдельный PR149 `VerifiedBasicSlabMaterial` жёстко ограничен `floorIndex==0`; подменять им BUILD-01 на втором этаже нельзя. **Вторая WRITE требует отдельного разрешения**, журнал — не разрешение.

**S09-02 / G2 / 98/100:** `NativeAdapter('CreateBeams')` реализован, но в `run_project` подключается только roof adapter. Поэтому optional Beam в authored DAG попадёт в `SceneWriter` без права `CreateBeams` и будет отклонён как `UNSUPPORTED_WRITE_RECIPE` до native CREATE. Минимальный путь — existing `adapters(['beam'])` внутри существующего `run_project`, не новый router/writer. Это **статический** вывод, не воспроизведённый OFFLINE тест.

**S09-03 / G4 / 97/100:** после будущего Beam opt-in условный риск BeamSegment в final GUID diff остаётся. `GetModelDumpV1` отсутствует в закреплённом каталоге 262 команд Tapir 1.5.10; независимый BREP пока не подтверждён runtime.

## Статусы ворот
| Gate | Установленный статус | Критерий ГОТОВО |
|---|---|---|
| G0 | **BLOCKED** | Windows PID→loaded APX path/SHA256, current port/PLN, `GetAddOnVersion`, actual `API.IsAddOnCommandAvailable` и схема. |
| G1 | **SOURCE_ONLY** | Реальный read-only preflight PR74 для нового двухэтажного задания: story bindings, typed DAG, collision, plan hash. |
| G2 | **SOURCE_ONLY** | HostWall GUID, native Roof/Wall/Slab/Door/Window contracts, double-scope Slab, optional Beam opt-in, installed registration/schema. |
| G3 | **NOT_AUTHORIZED** | Отдельная санкция владельца на новую scratch PLN, порт и plan hash, затем один guarded SceneWriter; никаких повторов при UNKNOWN. |
| G4 | **NOT_RUN** | GuardedSave, GUI Close/Open, independent all-database GUID/host/material/BREP, palette scripts остановлены. |
| G5 | **NOT_RUN** | Другое структурированное задание, другая scratch PLN, новая приёмка. |

## Конкретная безопасная последовательность подключения

1. **G0:** без установки проверить `Get-Process -Module` или Microsoft ListDLLs для точного Archicad PID, `Get-FileHash` загруженного APX, `GetProjectInfo`, `GetStories`, `GetAddOnVersion`; existing `DynamicCommands.probe_runtime` проверяет регистрацию команд, но **не** их фактическую схему.
2. **G1:** `compile_authored_intent` / `compile_candidate` с двумя `nativeStoryBindings`, материалами `GetAttributesByType`, `apa-authored-project/1`. Режим `run_project(mode='offline')` для authored запрещён исходным кодом: нужен настоящий read-only `preflight`, иначе `NOT_RUN`.
3. **G2:** `CreateWalls` (host GUID), `CreateSlabs` (поля level/polygonCoordinates/floorIndex/thickness), `ModifySlabs` (elementId/structureType/thickness/buildingMaterialId), `CreateDoors/CreateWindows` (`ownerWallId.guid`); `CreateRoofs` только SinglePlane Basic через существующий adapter. `CreateColumns` через PR149 verifier только floor0; верхний этаж требует другой доказанный контракт, не обход.
4. **G3:** ни одной WRITE в этом исследовании. Не трогать BDD, оригиналы, main; no retry Create после UNKNOWN.
5. **G4:** pinned `GetModelDumpV1` не найден, поэтому G4 нельзя объявлять BREP_PASS по `Get3DBoundingBoxes`; требуется фактическая runtime регистрация/минимальный read-only adapter при `NOT_FOUND`.

## Доказательства и контрааудиты

- **30 фактических SOURCE-проверок:** 14 GitHub `fetch_pr` + 16 `fetch_file`, точные HEAD/blob SHA в приложениях A/B; дополнительно прочитаны фрагменты SceneWriter, upstream Tapir MIT LICENSE и version header. Это **не** 30 нативных тестов.
- **Контрааудит A:** сравнение Tapir `CreateSlabs/ModifySlabs` ↔ SceneWriter ↔ PR149 floor0; результат S09-01.
- **Контрааудит B:** сравнение `run_project` ↔ SceneWriter `allowed_writes` ↔ Beam adapter ↔ inventory/BREP; результат S09-02/03.
- **Матрица:** 9 конкретных маршрутов, экспертные приоритеты 97–100, не benchmark.
- **06Z:** первоначальный основной текст отсутствует; частичное восстановление остаётся PARTIAL_NOT_ACCEPTED, никакого псевдооригинала.
- **SOURCE: 30; OFFLINE: 0; BUILD: 0; INSTALLED: 0; LIVE: 0; ACCEPTED: 0.** Никаких native write, новых code engines, установки, изменения NEXT/PROJECT_PLAN/main, PR merge, платных API. `MODEL_MODE_NOT_VERIFIABLE`.

## Закреплённые первоисточники

[BUILD-01 #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) · [PR149](https://github.com/dvikt33-ux/safe-bim-layer/pull/149) · [PR162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) · [SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py) · [Accelerator](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py) · [Beam adapter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py) · [pinned Tapir schema](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) · [Tapir MIT LICENSE](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE) · [historical PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/control/PROJECT_PLAN.json).
