# APA №2 | 23.10.2026 10Z | BUILD-01 | SOURCE инженерный отчёт

## Новый конкретный вклад в G2

**P0 / 100 из 100: обнаружено отсутствие отдельной санкции на вторую нативную мутацию перекрытия.** В `SceneWriter._execute_verified_plan` после `CreateSlabs` и readback вызывается `ModifySlabs` напрямую, но `approval_record.permission` остаётся `CreateSlabs`. В SQLite фиксируется `BASIC_MODIFY_ATTEMPTED`, однако отдельной проверки разрешения `ModifySlabs` нет. Это не означает, что WRITE уже выполнялась в этом исследовании. **G2 = DUAL_WRITE_APPROVAL_NOT_ENFORCED / WRITE_BLOCKED** до явной санкции на обе операции и минимальной проверки внутри существующего SceneWriter. Никакого второго writer/router.

**Почему второй шаг нужен:** закреплённый Tapir 1.5.10 `CreateSlabs` не имеет `structureType/buildingMaterialId`, а `ModifySlabs` имеет. Обход путём несуществующих CREATE-полей запрещён. На втором этаже нельзя использовать floor0-only verifier PR149.

## Три дополнительных результата

**G0 / 100:** все 14 непосредственно проверенных PR #34/#48/#74/#82/#97/#126/#131/#149/#150/#151/#154/#159/#160/#162 OPEN/UNMERGED. Pinned PR162 commit `f7c37b84b76c040c417ccd58a5543326e50f673a` — кодовый источник, не доказательство установки. Закреплённый JSON — 262 команды, `provider_version=1.5.10`, исторический PLN/порт19723; PID/loaded APX/локальная схема не прочитаны. `DynamicCommands.probe_runtime` проверяет `API.IsAddOnCommandAvailable`, но не схему.

**G1 / 99:** authored `run_project(mode='offline')` отвергается. Готовый безопасный путь — `mode='preflight'` с read-only transport, exact scratch PLN и правильным активным story. CLI допускает только два фиксированных scratch пути; `bind_authorized_saved_copy` с SHA256/authorizationRef существует, но не подключён автоматически к CLI. `evidenceKind='LIVE'` при `native_transport` возможно даже в read-only preflight: **не считать LIVE_CREATE**.

**G4 / 100:** `archicad_authored_geometry.run` вызывает `GetModelDumpV1`, отсутствующий в pinned 262 commands. `Get3DBoundingBoxes` — AABB, не BREP. Без read-only runtime BREP либо минимального адаптера G4 остаётся BLOCKED. Upstream [Tapir #681](https://github.com/ENZYME-APD/tapir-archicad-automation/issues/681) о SaveProject/3D относится к AC29 build3000, не доказан для build5101.

## Девять готовых/условных маршрутов и два контрааудита

Подробности: `research-2-integration-2026-10-23T10Z-matrix.md` (9 маршрутов, интерфейсы/поля/приоритеты/ГОТОВО), `research-2-integration-2026-10-23T10Z-audit-A.md` (Slab authorization/schema), `research-2-integration-2026-10-23T10Z-audit-B.md` (PR/source/installed, G1 и G4). 30 прямых SOURCE-проверок S01–S30 — `research-2-integration-2026-10-23T10Z-checks.md`; дополнительно прочитаны upstream Tapir issues #481/#573/#604/#681/#439. Лицензия Tapir upstream MIT, но версия установленного APX не подтверждена. Две независимые проверки проведены по разным вопросам.

## Состояние G0–G5

| Gate | Статус | Следующее безопасное доказательство |
|---|---|---|
| G0 | BLOCKED | PID→loaded APX SHA256, port/PLN, GetAddOnVersion, runtime command inventory/schema |
| G1 | SOURCE_ONLY/NOT_RUN | Реальный READ-ONLY authored preflight двух этажей, typed DAG и plan hash |
| G2 | SOURCE_ONLY/DUAL_SCOPE_BLOCKED | Две санкции Slab, host GUID, Favorites, roof/beam/column exact schema |
| G3 | NOT_AUTHORIZED | Только отдельный допуск владельца на новую scratch PLN/port/plan hash |
| G4 | NOT_RUN/BREP_BLOCKED | GuardedSave, GUI close/reopen, независимые GUID/host/material/BREP |
| G5 | NOT_RUN | Другое задание и другая scratch PLN |

**SOURCE 30 · OFFLINE 0 · BUILD 0 · INSTALLED 0 · LIVE 0 · ACCEPTED 0** (новые результаты). Ни одной новой модели, установки, запуска native WRITE, изменения main/NEXT/PLN/APX/кода, PR merge. 06Z PARTIAL_NOT_ACCEPTED. IFC/DXF/Hotlink/MEP/SAF/Publisher — вторичные направления, P0 не замещают. MODEL_MODE_NOT_VERIFIABLE.
