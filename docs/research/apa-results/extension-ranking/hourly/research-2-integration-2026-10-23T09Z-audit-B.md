# Контрааудит B — Beam opt-in и G4 BREP полнота | 09Z

**Независимый предмет:** командная маршрутизация до CREATE, нативные дочерние GUID и независимый геометрический контроль. Источники: project accelerator (blob `439f6d26ce097cdfdfc33a2b5a245352073151f2`), SceneWriter (blob `484c600a205192d5737e124f8d47c8583e07a9f3`), connected components (blob `c5a99f59a90369ff622807574677cf11ca0a2225`).

1. `NativeAdapter('CreateBeams')` **существует** и требует строго straight/basic payload; `adapters(['beam'])` возвращает `{'CreateBeams':NativeAdapter(...)}`.
2. `run_project` строки 765–769 создаёт `typed_adapters={}` и добавляет **только** `CONNECTED.adapters(['roof'])` при наличии Roof. Следовательно Beam **не** входит в `typed_adapters` даже при наличии операции `CreateBeams`.
3. `SceneWriter.__init__` строки 598–602: `allowed_writes = ALLOWED_WRITES | self.adapters.keys()`; `CreateBeams` находится в `EXTENDED_WRITES`, **не** в `ALLOWED_WRITES`. `_execute_verified_plan` проверяет `if command not in self.allowed_writes: raise ValueError('UNSUPPORTED_WRITE_RECIPE')`. Это **детерминированный статический барьер маршрута Beam до CREATE**, если Beam реально включён в graph.
4. После безопасного opt-in возникает второй **условный** барьер: `run_project` final GUID diff добавляет только `column_subelements`, хотя `assembly_subelements(...,'Beam')` уже реализован. Будет ли `BeamSegment` в `GetAllElements`, неизвестно. Не объявлять это LIVE-ошибкой.
5. G4: pinned schema из 262 команд **не** содержит `GetModelDumpV1`. `Get3DBoundingBoxes` — AABB, не замкнутый BREP. Существование Python-кода `normalize_dump` не доказывает установленный native readback.
6. `DynamicCommands.probe_runtime` (PR126) проверяет `API.IsAddOnCommandAvailable`, но **не** подтверждает входную schema, binary SHA или содержимое BREP. Требуются три независимые проверки.

**Контргипотеза:** в минимальном BUILD-01 Beam необязателен согласно issue #192 («если команды реально доступны»), поэтому можно получить минимальное здание без Beam. **Принимается:** не блокировать G1/G3 базового здания из-за optional Beam; блокировать лишь расширенный Beam-маршрут.

**Результат:** STATIC_ROUTE_BLOCKER_FOR_OPTIONAL_BEAM; не LIVE failure. **Приоритет 98/100**. Исправление только в существующем `run_project`: выбрать имеющийся `adapters(['beam'])` при наличии Beam в DAG, затем OFFLINE negative/positive tests и установленный read-only preflight. Никакого нового writer/router.
