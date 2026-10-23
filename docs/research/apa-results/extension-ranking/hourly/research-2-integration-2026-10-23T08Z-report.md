# APA №2 — BUILD-01 | 23.10.2026 08Z | Инженерный отчёт SOURCE

## Конкретный вклад в ворота BUILD-01
**B-08Z-01, G2/G4, 97/100 — потенциальный провал финальной инвентаризации BeamSegment после нативного CREATE.** Существующий `NativeAdapter('CreateBeams')` уже читает `assembly_subelements(...,'Beam')` и проверяет родителя, материал, замкнутый BREP. Однако `run_project` в финальном GUID-diff добавляет только `column_subelements`. **Если** GetAllElements включает BeamSegment, `FINAL_INVENTORY_DIFF_MISMATCH` наступит после записи. Это условный риск по исходникам, а не подтверждённая LIVE-ошибка. Минимальное исправление — использовать уже имеющийся `assembly_subelements` для Beam при final inventory; новый writer/router не нужен. Сначала отрицательный OFFLINE-кейс и установленное read-only перечисление сегментов.

**S-08Z-01, G2, 99/100 — подтверждён реальный дрейф провайдерской схемы.** Upstream Tapir `main` сейчас содержит `ADDON_VERSION 1.7.3` и поля `CreateSlabs.structureType/buildingMaterialId/compositeId`, тогда как сохранённый каталог `1.5.10` (262 команды) не содержит этих полей у `CreateSlabs`; они есть у `ModifySlabs`. Следовательно, **не** копировать схему 1.7.3 в локальный 1.5.10, не обновлять APX ради эксперимента. Существующий маршрут PR74 `CreateSlabs→GUID→ModifySlabs→readback` остаётся кандидатом, но требует двух санкционированных write scopes и установленной схемы.

## G0–G5 — состояние
| Gate | Статус | Что нужно для ГОТОВО |
|---|---|---|
| G0 | **BLOCKED** | Read-only PID→loaded APX path→SHA256, port/current PLN, GetAddOnVersion, actual command registration/schema. Provider 1.5.10 metadata и upstream 1.7.3 не являются installed contract. |
| G1 | **SOURCE_ONLY** | Новая отдельная scratch PLN с owner authorization; existing PR74 compiler, 2 storyBindings, typed DAG/hash, настоящий OFFLINE или read-only preflight. Никаких повторов 21-element fixture. |
| G2 | **SOURCE_ONLY** | Existing Wall/Slab/Beam/Column/Roof/Door/Window exact required fields, host GUID, favorite/material; Beam adapter wiring; BeamSegment final diff; CreateSlabs/ModifySlabs scopes. |
| G3 | **NOT_AUTHORIZED** | Отдельное разрешение владельца на scratch path/port/plan hash; SQLite intent-before-write; no retry on UNKNOWN. PR126/162 только после scoped runtime. |
| G4 | **NOT_RUN** | GuardedSave, GUI close, no active palette scripts, reopen, independent all-database GUID/host/material/BREP. Pinned catalog omits GetModelDumpV1; AABB не BREP. |
| G5 | **NOT_RUN** | Другая спецификация на второй новой копии, independent readback. |

## Воспроизводимый минимум
1. **G0 100/100:** на Windows11 без установки проверить загруженный APX именно в Archicad29 PID; SHA256 того же файла; сопоставить с port/PLN/version и actual command registration. [Microsoft ListDLLs](https://learn.microsoft.com/sysinternals/downloads/listdlls) — опциональная готовая утилита, **не устанавливалась**; возможен штатный `Get-Process -Module`.
2. **G1 98/100:** применить existing `bind_authorized_saved_copy(port,path,name,saved_sha256,authorization_ref)` и `compile_authored_intent`, не второй SceneWriter; при `apa-authored-project/1` `run_project(mode='offline')` отвергается, read-only `preflight` требует реального transport.
3. **G2 99/100:** fail-closed writer-required поля `width/height/sillHeight`, `Slab.floorIndex/thickness`, `Column.height/width/depth` и Beam strict 17-field recipe; hostWall GUID. Это проверки до WRITE, не пробные native CREATE.
4. **G2/G4 97/100:** добавить Beam child GUID только через уже существующий `assembly_subelements`, если read-only installed inventory показывает child GUID в `GetAllElements`. Отсутствие такого поведения не выдумывать.
5. **G4 99/100:** проверить explicit databases и `executionResultForDatabases` при инвентаризации; independent BREP только после actual `GetModelDumpV1` registration. При отсутствии — **NOT_FOUND** и минимальный read-only adapter, не объявлять ACCEPTED.

## Подтверждения и ограничения
- **SOURCE:** 30 отдельных успешных проверок: issue #192, 14 PR metadata, 15 `fetch_file` (точные refs и Git blob SHA в checks-A/B); сверх них проверены upstream Tapir MIT LICENSE, `AddOnVersion.hpp`, `ElementCreationCommands.cpp`, BIM Graph и DynamicCommands. Два самостоятельных статических контрааудита A/B; матрица 10 маршрутов.
- **OFFLINE: 0. BUILD: 0. INSTALLED: 0. LIVE: 0. ACCEPTED: 0.** Нет доступа к Windows PID/APX/PLN, поэтому ни один новый gate не закрыт.
- Архив **06Z PARTIAL_NOT_ACCEPTED**: исходный отчёт 22.10 06Z отсутствует; прямой повторный fetch = 404. Старые приложения и документы не заменялись.
- Нет нового кода, второго writer/router, CloneNativeGroupV1, установки, native WRITE, LIVE, PR merge, Work/Codex/Arena, платных API. `main`, NEXT, PLN/APX не изменялись. 0–100 — экспертный приоритет, не 100× и не benchmark.
- `MODEL_MODE_NOT_VERIFIABLE`.

## Точные первоисточники
[BUILD-01 issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [PR162 compiler](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_project_accelerator.py) · [PR162 SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_scene_run.py) · [PR162 adapters](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_connected_components.py) · [Tapir 1.5.10 pinned](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json) · [Tapir upstream version](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/AddOnVersion.hpp) · [Tapir upstream CreateSlabs](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/archicad-addon/Sources/ElementCreationCommands.cpp) · [MIT LICENSE](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/main/LICENSE).
